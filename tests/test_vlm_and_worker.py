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
