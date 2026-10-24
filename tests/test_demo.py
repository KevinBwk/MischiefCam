import argparse
import json

import numpy as np

from core.demo import AUTO_SOFA, _judge_name, draw_overlay, item_rois, load_items
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


def test_video_items_use_the_auto_sofa_zone():
    items = load_items(_args(video=["a.mp4", "b.mp4"]))
    assert [i["caption"] for i in items] == ["a.mp4", "b.mp4"]
    assert item_rois(items[0]) == [AUTO_SOFA] and AUTO_SOFA.auto == "couch"


def test_overlay_draws_without_error():
    img = np.zeros((360, 640, 3), dtype=np.uint8)
    det = Detection((100, 100, 300, 300), 0.9, "dog", track_id=1)
    info = {"dogs": {1: {"zones": ["sofa"], "state": "cooldown", "verdict": {"decision": "suspect", "reason": "", "raw": "probe: p=0.9"}}},
            "auto_zones": {"sofa": [(50.0, 150.0, 600.0, 350.0)]}}
    out = draw_overlay(img, [AUTO_SOFA], [det], info, 2.0, {"synthetic": True})
    assert out.shape == img.shape and out.sum() > 0
    assert out[340, 590].sum() > 0  # the auto zone's box is drawn (inside the box, away from the dog)


def test_judge_name():
    assert _judge_name("probe: p=0.1 | vlm: suspect") == "classifier + VLM"
    assert _judge_name("probe: p=0.9") == "classifier" and _judge_name('{"decision":"suspect"}') == "VLM"


def test_assessment_line_tiers():
    from core.demo import assessment_line

    base = {"ok": True, "mouth_visibility": "clear", "contact": "sofa", "limitation": "none", "observation": ""}
    assert assessment_line({**base, "assessment": "suspect", "observation": "teeth on the armrest"}) == (
        "ok", "Visual check: teeth on the armrest")
    tone, text = assessment_line({**base, "assessment": "normal", "contact": "toy"})
    assert tone == "warn" and "toy" in text            # contradicting evidence stays visible
    assert assessment_line({**base, "assessment": "insufficient"})[0] == "muted"  # contact alone is not support
    assert assessment_line({**base, "assessment": "suspect", "contact": "unclear", "observation": "x"})[0] == "muted"
    assert assessment_line({**base, "assessment": "suspect", "observation": ""})[0] == "muted"
    assert assessment_line({**base, "assessment": "insufficient", "contact": "unclear", "mouth_visibility": "hidden"}) == (
        "muted", "Mouth hidden from camera — check the snapshot")
    assert assessment_line({**base, "assessment": "insufficient", "contact": "unclear",
                            "mouth_visibility": "partial"})[1].startswith("Limited")
    assert assessment_line(None) == ("muted", "Visual assessment unavailable")
    assert assessment_line({**base, "assessment": "suspect", "ok": False})[0] == "muted"  # never a yes when unparsed


def test_only_the_dog_that_alerted_is_drawn_as_alert():
    from core.demo import C_ALERT, C_WATCH

    img = np.zeros((360, 640, 3), dtype=np.uint8)
    dets = [Detection((40, 100, 200, 300), 0.9, "dog", track_id=1), Detection((400, 100, 560, 300), 0.9, "dog", track_id=2)]
    info = {"dogs": {1: {"state": "cooldown", "alerted": True}, 2: {"state": "cooldown", "alerted": False}}}
    out = draw_overlay(img, [], dets, info, 2.0, {"synthetic": True})
    assert tuple(int(v) for v in out[250, 40]) == C_ALERT    # left edge of dog 1's box
    assert tuple(int(v) for v in out[250, 400]) == C_WATCH   # dog 2: in the zone, not an alert
