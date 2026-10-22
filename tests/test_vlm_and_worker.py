import time

from PIL import Image

from core.types import VLMRequest
from core.vlm import FakeVLMBackend, build_prompt, parse_decision
from core.worker import VLMWorker


def test_parse_plain_json():
    assert parse_decision('{"decision": "suspect", "reason": "biting the sofa"}') == ("suspect", "biting the sofa")


def test_parse_json_with_surrounding_text():
    assert parse_decision('Sure! {"decision":"normal","reason":"sleeping"} done')[0] == "normal"


def test_parse_garbage_is_insufficient_not_normal():
    assert parse_decision("the dog is cute") == ("insufficient", "unparseable output")


def test_parse_bare_label():
    assert parse_decision("suspect") == ("suspect", "")
    assert parse_decision("  Normal.\n") == ("normal", "")


def test_parse_label_inside_sentence_is_not_accepted():
    assert parse_decision("I think it is suspect maybe") == ("insufficient", "unparseable output")


def test_parse_unknown_label_is_insufficient():
    assert parse_decision('{"decision": "maybe"}')[0] == "insufficient"


def test_prompt_mentions_target():
    assert "sofa" in build_prompt("sofa")


def _req():
    return VLMRequest(images=(Image.new("RGB", (8, 8)),), prompt="x")


def test_worker_returns_result():
    w = VLMWorker(FakeVLMBackend(), queue_size=2)
    w.submit("ep1", 1.0, _req())
    assert w.wait_idle(5)
    out = w.outcomes.get_nowait()
    assert out.result.decision == "suspect" and out.error is None
    w.close()


def test_worker_drops_oldest_when_full():
    w = VLMWorker(FakeVLMBackend(delay_s=0.3), queue_size=1)
    w.submit("ep1", 1.0, _req())
    time.sleep(0.05)  # ep1 is now running
    w.submit("ep2", 2.0, _req())
    w.submit("ep3", 3.0, _req())  # queue full -> ep2 dropped
    assert w.wait_idle(5)
    outs = []
    while not w.outcomes.empty():
        outs.append(w.outcomes.get_nowait())
    by_ep = {o.job.episode_id: o for o in outs}
    assert by_ep["ep2"].error == "dropped:queue_full"
    assert by_ep["ep1"].result and by_ep["ep3"].result
    w.close()


def test_worker_reports_backend_errors():
    class Boom(FakeVLMBackend):
        def infer(self, request):
            raise RuntimeError("device lost")

    w = VLMWorker(Boom())
    w.submit("ep1", 1.0, _req())
    assert w.wait_idle(5)
    out = w.outcomes.get_nowait()
    assert out.result is None and "device lost" in out.error
    w.close()


# ---------------------------------------------------------------- multi-frame + either
def test_multi_frame_prompt_mentions_count_and_floor():
    p = build_prompt("sofa", 4, 0.5)
    assert "4 frames" in p and "floor" in p and "sofa" in p
    assert build_prompt("sofa") == build_prompt("sofa", 1)


def test_either_backend_short_circuits_on_probe():
    from core.vlm import EitherBackend
    probe = FakeVLMBackend('{"decision": "suspect"}')
    vlm = FakeVLMBackend('{"decision": "normal"}')
    r = EitherBackend(probe, vlm).infer(_req())
    assert r.decision == "suspect" and vlm.calls == 0


def test_either_backend_uses_vlm_when_probe_normal():
    from core.vlm import EitherBackend
    probe = FakeVLMBackend('{"decision": "normal"}')
    vlm = FakeVLMBackend('{"decision": "suspect", "reason": "biting"}')
    r = EitherBackend(probe, vlm).infer(_req())
    assert r.decision == "suspect" and vlm.calls == 1 and "vlm" in r.raw_text



def _drain(w):
    outs = []
    while not w.outcomes.empty():
        outs.append(w.outcomes.get_nowait())
    return {(o.job.episode_id, o.job.kind): o for o in outs}


def test_explain_jobs_go_to_the_explainer():
    explainer = FakeVLMBackend('{"assessment": "suspect", "contact": "sofa", "observation": "teeth on cushion"}')
    w = VLMWorker(FakeVLMBackend('{"decision": "normal"}'), queue_size=2, explainer=explainer)
    w.submit("ep1", 1.0, _req())
    w.submit("ep1", 1.0, _req(), kind="explain")  # same episode, different kind: not merged
    assert w.wait_idle(5)
    by = _drain(w)
    assert by[("ep1", "judge")].result.decision == "normal"
    assert "teeth on cushion" in by[("ep1", "explain")].result.raw_text
    w.close()


def test_explain_never_evicts_a_judge_job():
    w = VLMWorker(FakeVLMBackend(delay_s=0.3), queue_size=1, explainer=FakeVLMBackend())
    w.submit("ep1", 1.0, _req())
    time.sleep(0.05)  # ep1 running
    w.submit("ep2", 2.0, _req())                  # fills the queue
    w.submit("ep1", 1.0, _req(), kind="explain")  # full: the explanation is the one dropped
    w.submit("ep3", 3.0, _req(), kind="explain")
    assert w.wait_idle(5)
    by = _drain(w)
    assert by[("ep2", "judge")].result is not None
    assert by[("ep1", "explain")].error == "dropped:queue_full"
    w.close()


def test_judge_evicts_a_pending_explanation_first():
    w = VLMWorker(FakeVLMBackend(delay_s=0.3), queue_size=1, explainer=FakeVLMBackend())
    w.submit("ep1", 1.0, _req())
    time.sleep(0.05)
    w.submit("ep1", 1.0, _req(), kind="explain")
    w.submit("ep2", 2.0, _req())  # judge job: the pending explanation makes room
    assert w.wait_idle(5)
    by = _drain(w)
    assert by[("ep1", "explain")].error == "dropped:queue_full"
    assert by[("ep2", "judge")].result is not None
    w.close()


def test_parse_explanation_validates_fields():
    from core.vlm import parse_explanation

    e = parse_explanation('{"assessment": "SUSPECT", "contact": "pizza", "mouth_visibility": "clear", '
                          '"observation": "one two three four five six seven eight nine ten eleven twelve thirteen"}')
    assert e["ok"] and e["assessment"] == "suspect" and e["contact"] == "unclear"
    assert len(e["observation"].split()) == 12
    assert parse_explanation("no json here")["ok"] is False


def test_judge_jobs_run_before_queued_explanations():
    order = []

    class Rec(FakeVLMBackend):
        def __init__(self, tag):
            super().__init__(delay_s=0.1)
            self.tag = tag

        def infer(self, request):
            order.append(self.tag)
            return super().infer(request)

    w = VLMWorker(Rec("judge"), queue_size=3, explainer=Rec("explain"))
    w.submit("ep0", 0.0, _req())
    time.sleep(0.03)  # ep0 running
    w.submit("ep1", 1.0, _req(), kind="explain")
    w.submit("ep2", 2.0, _req())
    assert w.wait_idle(5)
    assert order == ["judge", "judge", "explain"]
    w.close()
