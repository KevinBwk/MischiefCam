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
