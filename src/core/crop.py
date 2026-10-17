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
) -> Image.Image:
    """Build the VLM input and letterbox it (no distortion) to size x size (RGB PIL).

    mode="animal": the expanded animal box only. Keeps the mouth large enough to read
                   after downscaling to 336 px; the default.
    mode="union":  expanded animal box ∪ zone bounding box. More context, but a large
                   zone (a whole sofa) shrinks the dog to a few dozen pixels.
    """
    h, w = frame_bgr.shape[:2]
    ax1, ay1, ax2, ay2 = expand_box(animal_box, expand, w, h)
    if mode == "animal":
        x1, y1, x2, y2 = int(ax1), int(ay1), int(ax2), int(ay2)
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
