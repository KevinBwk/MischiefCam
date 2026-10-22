import argparse
import json

import numpy as np

from core.demo import FULL_FRAME, _judge_name, draw_overlay, item_rois, load_items
from core.types import Detection


def _args(**kw):
    base = dict(playlist=None, video=None, camera=None, caption=None, rois=None)
    base.update(kw)
    return argparse.Namespace(**base)


def test_playlist_defaults(tmp_path):
    p = tmp_path / "pl.json"
    p.write_text(json.dumps({"items": [{"video": "a.mp4", "caption": "x"}, {"camera": "0"}]}))
    items = load_items(_args(playlist=str(p)))
    assert items[0]["synthetic"] is True and items[1]["synthetic"] is False


def test_video_items_and_full_frame_zone():
    items = load_items(_args(video=["a.mp4", "b.mp4"]))
    assert [i["caption"] for i in items] == ["a.mp4", "b.mp4"]
    assert item_rois(items[0]) == [FULL_FRAME]


def test_overlay_draws_without_error():
    img = np.zeros((360, 640, 3), dtype=np.uint8)
    det = Detection((100, 100, 300, 300), 0.9, "dog", track_id=1)
    info = {"dogs": {1: {"zones": ["sofa"], "state": "cooldown", "verdict": {"decision": "suspect", "reason": "", "raw": "probe: p=0.9"}}}}
    out = draw_overlay(img, [FULL_FRAME], [det], info, 2.0, {"synthetic": True})
    assert out.shape == img.shape and out.sum() > 0


def test_judge_name():
    assert _judge_name("probe: p=0.1 | vlm: suspect") == "classifier + VLM"
    assert _judge_name("probe: p=0.9") == "classifier" and _judge_name('{"decision":"suspect"}') == "VLM"
