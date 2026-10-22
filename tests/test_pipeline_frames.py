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
