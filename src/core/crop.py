"""Build the VLM input image: animal box + zone, letterboxed to the VLM input size."""

from __future__ import annotations

import cv2
import numpy as np
from PIL import Image

from .roi import expand_box, roi_bbox_px
from .types import ROI


def interaction_crop(
    frame_bgr: np.ndarray,
    animal_box: tuple[float, float, float, float],
    roi: ROI,
    size: int = 336,
    expand: float = 0.15,
    mode: str = "animal",
    zone_box: tuple[float, float, float, float] | None = None,
) -> Image.Image:
    """Build the VLM input and letterbox it (no distortion) to size x size (RGB PIL).

    mode="animal": the expanded animal box only. Keeps the mouth large enough to read
                   after downscaling to 336 px; the default.
    mode="union":  expanded animal box ∪ zone bounding box. More context, but a large
                   zone (a whole sofa) shrinks the dog to a few dozen pixels.
    mode="contact": where the dog meets the zone — the overlap of the expanded animal box and
                   the zone box (zone_box, or the ROI's bounding box), grown by a margin. Zooms in on
                   mouth-on-sofa contact; falls back to "animal" when they do not overlap.
    """
    h, w = frame_bgr.shape[:2]
    ax1, ay1, ax2, ay2 = expand_box(animal_box, expand, w, h)
    if mode == "animal":
        x1, y1, x2, y2 = int(ax1), int(ay1), int(ax2), int(ay2)
    elif mode == "contact":
        zx1, zy1, zx2, zy2 = zone_box if zone_box is not None else roi_bbox_px(roi, w, h)
        ix1, iy1, ix2, iy2 = max(ax1, zx1), max(ay1, zy1), min(ax2, zx2), min(ay2, zy2)
        bw, bh = ax2 - ax1, ay2 - ay1
        if ix2 <= ix1 or iy2 <= iy1 or (zone_box is None and (zx2 - zx1) * (zy2 - zy1) >= 0.95 * w * h):
            x1, y1, x2, y2 = int(ax1), int(ay1), int(ax2), int(ay2)  # no contact area (or zone = whole frame)
        else:
            cx, cy = (ix1 + ix2) / 2, (iy1 + iy2) / 2
            # square around the contact area: a little margin, never larger than ~3/4 of the dog box
            side = min(max(max(ix2 - ix1, iy2 - iy1) * 1.1, 0.5 * min(bw, bh)), 0.75 * max(bw, bh))
            half = side / 2
            x1, y1 = int(max(0, cx - half)), int(max(0, cy - half))
            x2, y2 = int(min(w, cx + half)), int(min(h, cy + half))
    elif mode == "union":
        rx1, ry1, rx2, ry2 = roi_bbox_px(roi, w, h)
        x1, y1 = int(max(0, min(ax1, rx1))), int(max(0, min(ay1, ry1)))
        x2, y2 = int(min(w, max(ax2, rx2))), int(min(h, max(ay2, ry2)))
    else:
        raise ValueError(f"Unknown crop mode {mode!r}")
    region = frame_bgr[y1:y2, x1:x2]
    if region.size == 0:
        region = frame_bgr
    return letterbox(region, size)


def letterbox(image_bgr: np.ndarray, size: int) -> Image.Image:
    h, w = image_bgr.shape[:2]
    scale = size / max(h, w)
    nw, nh = max(1, round(w * scale)), max(1, round(h * scale))
    resized = cv2.resize(image_bgr, (nw, nh), interpolation=cv2.INTER_AREA)
    canvas = np.zeros((size, size, 3), dtype=np.uint8)
    top, left = (size - nh) // 2, (size - nw) // 2
    canvas[top : top + nh, left : left + nw] = resized
    return Image.fromarray(cv2.cvtColor(canvas, cv2.COLOR_BGR2RGB))
