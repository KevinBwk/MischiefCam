"""Protected zones (ROIs): loading and animal-box / zone overlap.

Overlap is measured as the fraction of the (expanded) animal bounding box that
falls inside the zone. Bottom-center tests (as used by NVRs for people) miss
chewing, where the body is next to the furniture and only the head is on it.
"""

from __future__ import annotations

import json
from pathlib import Path

from .types import ROI

Point = tuple[float, float]


def load_rois(path: Path | str) -> list[ROI]:
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    if data.get("coordinate_space", "normalized") != "normalized":
        raise ValueError("Only normalized ROI coordinates are supported")
    rois = []
    for item in data["rois"]:
        policy = item.get("policy", "forbidden")
        if policy not in ("forbidden", "allowed"):
            raise ValueError(f"ROI {item['id']}: unknown policy {policy!r}")
        if item.get("auto"):  # zone = whatever the detector finds of that class, every frame
            rois.append(ROI(id=item["id"], name=item.get("name", item["id"]), policy=policy, polygon=(),
                            auto=str(item["auto"])))
            continue
        polygon = tuple((float(x), float(y)) for x, y in item["polygon"])
        if len(polygon) < 3:
            raise ValueError(f"ROI {item['id']}: polygon needs at least 3 points")
        rois.append(ROI(id=item["id"], name=item.get("name", item["id"]), policy=policy, polygon=polygon))
    return rois


def polygon_area(points: list[Point] | tuple[Point, ...]) -> float:
    n = len(points)
    if n < 3:
        return 0.0
    s = 0.0
    for i in range(n):
        x1, y1 = points[i]
        x2, y2 = points[(i + 1) % n]
        s += x1 * y2 - x2 * y1
    return abs(s) / 2.0


def _clip(subject: list[Point], inside, intersect) -> list[Point]:
    out: list[Point] = []
    if not subject:
        return out
    prev = subject[-1]
    for cur in subject:
        if inside(cur):
            if not inside(prev):
                out.append(intersect(prev, cur))
            out.append(cur)
        elif inside(prev):
            out.append(intersect(prev, cur))
        prev = cur
    return out


def clip_polygon_to_box(polygon: list[Point], box: tuple[float, float, float, float]) -> list[Point]:
    """Sutherland–Hodgman clip of an arbitrary polygon against an axis-aligned box."""
    x1, y1, x2, y2 = box
    pts = list(polygon)

    def ix(a: Point, b: Point, x: float) -> Point:
        t = (x - a[0]) / (b[0] - a[0])
        return (x, a[1] + t * (b[1] - a[1]))

    def iy(a: Point, b: Point, y: float) -> Point:
        t = (y - a[1]) / (b[1] - a[1])
        return (a[0] + t * (b[0] - a[0]), y)

    pts = _clip(pts, lambda p: p[0] >= x1, lambda a, b: ix(a, b, x1))
    pts = _clip(pts, lambda p: p[0] <= x2, lambda a, b: ix(a, b, x2))
    pts = _clip(pts, lambda p: p[1] >= y1, lambda a, b: iy(a, b, y1))
    pts = _clip(pts, lambda p: p[1] <= y2, lambda a, b: iy(a, b, y2))
    return pts


def expand_box(
    box: tuple[float, float, float, float], frac: float, width: float, height: float
) -> tuple[float, float, float, float]:
    x1, y1, x2, y2 = box
    dx, dy = (x2 - x1) * frac, (y2 - y1) * frac
    return (max(0.0, x1 - dx), max(0.0, y1 - dy), min(width, x2 + dx), min(height, y2 + dy))


def box_overlap_fraction(
    box_px: tuple[float, float, float, float], roi: ROI, width: float, height: float
) -> float:
    """Fraction of the pixel box area that lies inside the ROI polygon."""
    x1, y1, x2, y2 = box_px
    box_area = max(0.0, x2 - x1) * max(0.0, y2 - y1)
    if box_area <= 0:
        return 0.0
    poly_px = [(x * width, y * height) for x, y in roi.polygon]
    inter = polygon_area(clip_polygon_to_box(poly_px, box_px))
    return min(1.0, inter / box_area)


def roi_bbox_px(roi: ROI, width: float, height: float) -> tuple[float, float, float, float]:
    xs = [x * width for x, _ in roi.polygon]
    ys = [y * height for _, y in roi.polygon]
    return (min(xs), min(ys), max(xs), max(ys))
