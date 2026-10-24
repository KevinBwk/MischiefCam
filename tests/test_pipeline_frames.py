from collections import deque

from PIL import Image

from core.pipeline import Pipeline, PipelineConfig


def _pipe(frames=4, gap=0.5):
    p = Pipeline.__new__(Pipeline)
    p.cfg = PipelineConfig(frames=frames, frame_gap_s=gap)
    p._history = {}
    return p


def test_select_frames_spacing_and_order():
    p = _pipe()
    img = lambda: Image.new("RGB", (4, 4))
    p._history[1] = deque([(t / 5, img()) for t in range(0, 15)])  # 0.0 .. 2.8 s at 5 fps
    latest = (3.0, img())
    out = p._select_frames(1, latest)
    assert len(out) == 4 and out[-1] is latest[1]
    pts = [t for t, im in list(p._history[1]) + [latest] if any(im is o for o in out)]
    assert pts == sorted(pts) and all(b - a >= 0.5 - 1e-6 for a, b in zip(pts, pts[1:]))


def test_select_frames_with_short_history():
    p = _pipe()
    latest = (0.2, Image.new("RGB", (4, 4)))
    assert p._select_frames(7, latest) == [latest[1]]


def test_contact_crop_uses_touching_couch():
    import numpy as np

    from core.crop import interaction_crop
    from core.types import ROI, Detection

    img = np.zeros((400, 600, 3), np.uint8)
    img[200:300, 250:350] = 255  # bright patch where dog and couch meet
    whole = ROI("z", "sofa", "forbidden", ((0, 0), (1, 0), (1, 1), (0, 1)))
    dog = Detection((150, 100, 350, 300), 0.9, "dog", 1)
    couch = Detection((250, 200, 600, 400), 0.8, "couch")
    p = Pipeline.__new__(Pipeline)
    p.cfg = PipelineConfig(crop_mode="contact", context_classes=("couch",))
    p._context = [couch]
    got = p._crop(img, dog, whole, "contact")
    want = interaction_crop(img, dog.bbox, whole, 336, 0.15, "contact", zone_box=couch.bbox)
    assert list(got.getdata()) == list(want.getdata())
    p._context = []  # no couch: full-frame zone -> plain animal crop
    assert list(p._crop(img, dog, whole, "contact").getdata()) == list(
        interaction_crop(img, dog.bbox, whole, 336, 0.15, "animal").getdata())


def test_probe_gets_its_own_crop(tmp_path):
    import json

    from core.vlm import probe_crop

    clf = tmp_path / "c.json"
    clf.write_text(json.dumps({"input": {"crop": "contact"}}))
    assert probe_crop({"backend": "either", "classifier": str(clf)}) == "contact"
    assert probe_crop({"backend": "mlx", "classifier": str(clf)}) is None


def test_probe_alert_queues_explanation_and_explained_event():
    from core.events import EventBus
    from core.pipeline import RunStats
    from core.state import EpisodeTracker, StateConfig
    from core.types import ROI, VLMRequest, VLMResult
    from core.worker import Job, Outcome

    class StubWorker:
        def __init__(self):
            import queue
            self.outcomes, self.explainer, self.submitted = queue.Queue(), object(), []

        def submit(self, episode_id, pts, request, kind="judge", owner=None):
            self.submitted.append((episode_id, pts, request, kind))

    p = Pipeline.__new__(Pipeline)
    p.cfg = PipelineConfig()
    p.worker, p.bus, p.stats, p.last_verdict = StubWorker(), EventBus(), RunStats(), {}
    p.tracker = EpisodeTracker(StateConfig())
    p.rois = {"z": ROI("z", "sofa", "forbidden", ((0, 0), (1, 0), (1, 1), (0, 1)))}
    p._episode_meta = {"ep": (1, "z")}
    seen = []
    p.bus.subscribe(seen.append)
    crop = Image.new("RGB", (4, 4))
    req = VLMRequest(images=(crop,), prompt="judge")
    p.worker.outcomes.put(Outcome(Job("ep", 3.0, req, 0.0), VLMResult("suspect", "probe: p=0.9", 5.0, "", "probe",
                                                                  {"clip": 5.0})))
    p._drain_outcomes()
    alert = next(e for e in seen if e.kind == "alert")
    assert alert.extra["explaining"] and alert.extra["alert_key"] == "ep@3.000"
    (ep_id, pts, ereq, kind), = p.worker.submitted
    assert kind == "explain" and ereq.images == (crop,) and "Describe only what is visible" in ereq.prompt

    raw = '{"assessment": "suspect", "mouth_visibility": "clear", "contact": "sofa", "limitation": "none", "observation": "teeth on cushion"}'
    p.worker.outcomes.put(Outcome(Job("ep", 3.0, ereq, 0.0, "explain"), VLMResult("suspect", raw, 900.0, "", "vlm",
                                                                                {"qwen": 900.0})))
    p._drain_outcomes()
    expl = next(e for e in seen if e.kind == "explained")
    assert expl.extra["alert_key"] == "ep@3.000" and expl.extra["explanation"]["observation"] == "teeth on cushion"
    assert p.stats.alerts == 1  # the explanation is not a second verdict
    assert p.stats.judge_ms == {"clip": [5.0], "qwen_explain": [900.0]}  # explain latency kept apart


def test_late_outcome_from_another_run_is_ignored():
    import queue

    from core.pipeline import RunStats
    from core.types import VLMRequest, VLMResult
    from core.worker import Job, Outcome

    p = Pipeline.__new__(Pipeline)
    p.worker = type("W", (), {"outcomes": queue.Queue(), "explainer": None})()
    p._episode_meta, p.stats = {}, RunStats()
    p.worker.outcomes.put(Outcome(Job("old-ep", 1.0, VLMRequest((), ""), 0.0, owner=object()),
                                  VLMResult("suspect", "", 1.0)))
    p._drain_outcomes()  # would KeyError on the unknown episode if not filtered
    assert p.stats.alerts == 0


def test_auto_zone_locks_and_never_shrinks():
    import pytest

    from core.types import ROI, Detection

    sofa = ROI("sofa", "sofa", "forbidden", (), auto="couch")
    p = Pipeline.__new__(Pipeline)
    p.cfg = PipelineConfig(context_classes=("couch",))
    p.rois = {"sofa": sofa}
    p.auto_zones = {}
    p._context = [Detection((100, 100, 300, 200), 0.9, "couch")]
    p._update_auto_zones(1.0)
    assert p._overlap((250, 150, 350, 250), sofa, 640, 360) == pytest.approx(0.25)  # 50x50 of a 100x100 box
    assert p._overlap((400, 250, 500, 350), sofa, 640, 360) == 0.0                   # beside, not touching
    p._context = [Detection((180, 100, 300, 200), 0.9, "couch")]  # the dog now hides the left half
    p._update_auto_zones(2.0)
    assert p.auto_zones["sofa"] == [(100, 100, 300, 200)]          # the zone does not shrink
    p._context = []                                                # sofa fully hidden
    p._update_auto_zones(30.0)
    assert p.auto_zones["sofa"] == [(100, 100, 300, 200)]          # still locked


def test_merge_zone_boxes_grows_and_filters_weak_new_boxes():
    from core.roi import merge_zone_boxes

    z = merge_zone_boxes([], [((0, 0, 10, 10), 0.9)])
    z = merge_zone_boxes(z, [((5, 5, 20, 12), 0.4)])               # overlaps: merged even if weak
    assert z == [(0, 0, 20, 12)]
    z = merge_zone_boxes(z, [((50, 50, 60, 60), 0.4)])             # new, weak: ignored
    assert z == [(0, 0, 20, 12)]
    z = merge_zone_boxes(z, [((50, 50, 60, 60), 0.8)])             # new, confident: second sofa
    assert len(z) == 2
    z = merge_zone_boxes(z, [((15, 8, 55, 55), 0.9)])              # bridges both: all merged
    assert z == [(0, 0, 60, 60)]


def test_auto_zone_requires_its_class_in_context_classes():
    import pytest

    from core.types import ROI

    with pytest.raises(ValueError, match="context classes"):
        Pipeline(None, None, [ROI("sofa", "sofa", "forbidden", (), auto="couch")], None, None, None,
                 PipelineConfig(context_classes=()))
