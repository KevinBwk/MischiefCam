import numpy as np
import pytest

from core.crop import interaction_crop
from core.types import ROI

BIG_ZONE = ROI("sofa", "sofa", "forbidden", ((0.0, 0.0), (1.0, 0.0), (1.0, 1.0), (0.0, 1.0)))


def _frame():
    f = np.zeros((720, 1280, 3), dtype=np.uint8)
    f[300:400, 600:700] = 255  # a white "dog" square
    return f


def _white_fraction(img):
    a = np.asarray(img)
    return (a > 200).all(axis=2).mean()


def test_animal_crop_keeps_animal_large():
    img = interaction_crop(_frame(), (600, 300, 700, 400), BIG_ZONE, 336, 0.15, mode="animal")
    assert img.size == (336, 336)
    assert _white_fraction(img) > 0.5


def test_union_crop_with_big_zone_shrinks_animal():
    img = interaction_crop(_frame(), (600, 300, 700, 400), BIG_ZONE, 336, 0.15, mode="union")
    assert _white_fraction(img) < 0.05


def test_unknown_mode_rejected():
    with pytest.raises(ValueError):
        interaction_crop(_frame(), (600, 300, 700, 400), BIG_ZONE, mode="nope")


def test_contact_crop_zooms_on_overlap():
    f = np.zeros((720, 1280, 3), dtype=np.uint8)
    f[300:340, 640:700] = 255                       # bright "mouth on sofa" patch inside the overlap
    dog = (500, 250, 700, 450)
    sofa = (640, 200, 1200, 600)
    zoom = interaction_crop(f, dog, BIG_ZONE, 336, 0.15, mode="contact", zone_box=sofa)
    whole = interaction_crop(f, dog, BIG_ZONE, 336, 0.15, mode="animal")
    assert _white_fraction(zoom) > _white_fraction(whole)


def test_contact_crop_falls_back_without_overlap():
    f = _frame()
    a = interaction_crop(f, (600, 300, 700, 400), BIG_ZONE, 336, 0.15, mode="contact", zone_box=(0, 0, 50, 50))
    b = interaction_crop(f, (600, 300, 700, 400), BIG_ZONE, 336, 0.15, mode="animal")
    assert np.array_equal(np.asarray(a), np.asarray(b))
