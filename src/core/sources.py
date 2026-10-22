"""Frame sources: local video files and live cameras (device index or rtsp/http stream URL)."""

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


class CameraSource:
    """Live camera: a device index (USB webcam, iPhone Continuity Camera, Android in USB-webcam mode)
    or a stream URL (rtsp://… or http://… from an IP-camera app on the local network).

    Media time is wall-clock seconds since the source started, so the state machine behaves as
    in recorded clips. Frames are sampled at target_fps; older frames are skipped, never queued.
    """

    def __init__(self, device: int | str = 0, target_fps: float = 10.0, max_seconds: float | None = None):
        self.device = int(device) if isinstance(device, str) and device.isdigit() else device
        self.target_fps = target_fps
        self.max_seconds = max_seconds
        self.stopped = False
        self._cap = self._open()
        ok, frame = self._read_first_frame()
        if not ok:
            self._cap.release()
            raise RuntimeError(
                f"Camera {self.device!r} opened but returned no frame within 4 s. On macOS, allow camera access for the "
                "app that runs this terminal (System Settings > Privacy & Security > Camera; for the Claude app's "
                "terminal that is Claude) and try again, or try another --camera index.")
        h, w = frame.shape[:2]
        self._size = (w, h)

    def _read_first_frame(self, timeout_s: float = 4.0):
        """macOS cameras often return nothing for the first reads while they warm up; retry briefly."""
        import time

        deadline = time.monotonic() + timeout_s
        while True:
            ok, frame = self._cap.read()
            if ok and frame is not None:
                return ok, frame
            if time.monotonic() > deadline:
                return False, None
            time.sleep(0.1)

    def _open(self):
        if isinstance(self.device, int):
            cap = cv2.VideoCapture(self.device, cv2.CAP_AVFOUNDATION)
        else:
            cap = cv2.VideoCapture(self.device, cv2.CAP_FFMPEG)
        if not cap.isOpened():
            raise RuntimeError(f"Cannot open camera {self.device!r} (list devices: ffmpeg -f avfoundation -list_devices true -i \"\")")
        return cap

    @property
    def size(self) -> tuple[int, int]:
        return self._size

    def stop(self) -> None:
        self.stopped = True

    def frames(self) -> Iterator[Frame]:
        import time

        start = time.monotonic()
        step = 1.0 / self.target_fps
        next_t = 0.0
        index = 0
        try:
            while not self.stopped:
                ok, image = self._cap.read()
                if not ok:
                    break
                t = time.monotonic() - start
                if self.max_seconds is not None and t > self.max_seconds:
                    break
                if t + 1e-6 < next_t:
                    continue
                next_t = t + step
                yield Frame(image=image, pts_s=t, index=index)
                index += 1
        finally:
            self._cap.release()


def make_source(video: str | None = None, camera: str | None = None, target_fps: float = 5.0):
    if camera is not None:
        return CameraSource(camera, target_fps)
    return VideoFileSource(video, target_fps)
