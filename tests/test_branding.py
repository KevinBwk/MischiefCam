from core.branding import load_branding
from core.events import MascotNotifier
from core.types import Event


def test_branding_loads_names():
    b = load_branding()
    assert b.product_name and b.mascot_name == "Michelle"


def test_notifier_speaks_as_mascot():
    lines = []
    n = MascotNotifier(load_branding(), printer=lines.append)
    n(Event("alert", "ep", 1, "sofa", "sofa", "forbidden", 65.0, "suspect", "biting"))
    n(Event("review", "ep", 1, "sofa", "sofa", "forbidden", 65.0))  # not user-facing
    assert len(lines) == 1
    assert lines[0].startswith("Michelle:") and "sofa" in lines[0] and "01:05" in lines[0]


def test_insufficient_is_not_pushed_by_default():
    lines = []
    n = MascotNotifier(load_branding(), printer=lines.append)
    n(Event("insufficient", "ep", 1, "sofa", "sofa", "forbidden", 3.0, "insufficient", "blurry"))
    assert lines == []
    MascotNotifier(load_branding(), printer=lines.append, notify_insufficient=True)(
        Event("insufficient", "ep", 1, "sofa", "sofa", "forbidden", 3.0, "insufficient", "blurry"))
    assert len(lines) == 1 and lines[0].startswith("Michelle:")
