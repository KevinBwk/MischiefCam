import json

import pytest

from core.roi import box_overlap_fraction, clip_polygon_to_box, expand_box, load_rois, polygon_area
from core.types import ROI

W, H = 1000.0, 1000.0
LEFT_HALF = ROI("left", "left half", "forbidden", ((0, 0), (0.5, 0), (0.5, 1), (0, 1)))


def test_polygon_area_square():
    assert polygon_area([(0, 0), (2, 0), (2, 2), (0, 2)]) == pytest.approx(4.0)


def test_box_fully_inside():
    assert box_overlap_fraction((100, 100, 200, 200), LEFT_HALF, W, H) == pytest.approx(1.0)


def test_box_half_inside():
    assert box_overlap_fraction((400, 100, 600, 200), LEFT_HALF, W, H) == pytest.approx(0.5)


def test_box_outside():
    assert box_overlap_fraction((600, 100, 700, 200), LEFT_HALF, W, H) == 0.0


def test_triangle_clip():
    tri = ROI("tri", "tri", "forbidden", ((0, 0), (1, 0), (0, 1)))
    # box covering the whole image: overlap = triangle area / image area = 0.5
    assert box_overlap_fraction((0, 0, 1000, 1000), tri, W, H) == pytest.approx(0.5)


def test_clip_returns_empty_when_disjoint():
    assert clip_polygon_to_box([(0, 0), (1, 0), (1, 1)], (5, 5, 6, 6)) == []


def test_expand_box_is_clamped():
    assert expand_box((0, 0, 100, 100), 0.5, 120, 120) == (0.0, 0.0, 120, 120)


def test_load_rois_validates_policy(tmp_path):
    p = tmp_path / "rois.json"
    p.write_text(json.dumps({"rois": [{"id": "a", "policy": "maybe", "polygon": [[0, 0], [1, 0], [1, 1]]}]}))
    with pytest.raises(ValueError):
        load_rois(p)


def test_example_rois_load():
    from core.config import resolve

    rois = load_rois(resolve("config/rois.example.json"))
    assert {r.policy for r in rois} == {"forbidden", "allowed"}


def test_load_auto_zone(tmp_path):
    import json

    from core.roi import load_rois

    f = tmp_path / "r.json"
    f.write_text(json.dumps({"rois": [{"id": "sofa", "name": "sofa", "policy": "forbidden", "auto": "couch"}]}))
    (roi,) = load_rois(f)
    assert roi.auto == "couch" and roi.polygon == ()
