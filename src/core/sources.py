"""Frame sources. Stage I reads local video files; RTSP is a second implementation later."""

from __future__ import annotations

from collections.abc import Iterator
from pathlib import Path
from typing import Protocol

import cv2

from .types import Frame


class FrameSource(Protocol):
    def frames(self) -> Iterator[Frame]: ...

    @property
    def size(self) -> tuple[int, int]: ...  # (width, height)


class VideoFileSource:
    """Reads a video file and samples it at target_fps using media timestamps."""

    def __init__(self, path: Path | str, target_fps: float = 5.0):
        self.path = str(path)
        self.target_fps = target_fps
        cap = cv2.VideoCapture(self.path)
        if not cap.isOpened():
            raise FileNotFoundError(f"Cannot open video: {self.path}")
        self._size = (int(cap.get(cv2.CAP_PROP_FRAME_WIDTH)), int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT)))
        self.native_fps = cap.get(cv2.CAP_PROP_FPS) or 30.0
        cap.release()

    @property
    def size(self) -> tuple[int, int]:
        return self._size

    def frames(self) -> Iterator[Frame]:
        cap = cv2.VideoCapture(self.path)
        step = 1.0 / self.target_fps
        next_pts = 0.0
        index = 0
        try:
            while True:
                ok, image = cap.read()
                if not ok:
                    break
                pts = cap.get(cv2.CAP_PROP_POS_MSEC) / 1000.0
                if pts <= 0 and index > 0:  # some containers report 0; fall back to frame count
                    pts = index / self.native_fps
                index += 1
                if pts + 1e-6 < next_pts:
                    continue
                next_pts = pts + step
                yield Frame(image=image, pts_s=pts, index=index - 1)
        finally:
            cap.release()
