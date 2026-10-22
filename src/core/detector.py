"""Detector backends. Stage I: Ultralytics YOLO (+ ByteTrack, CPU-side) on Apple MPS."""

from __future__ import annotations

from typing import Protocol

import numpy as np

from .types import Detection


class DetectorBackend(Protocol):
    def detect(self, image_bgr: np.ndarray) -> list[Detection]: ...


class UltralyticsDetector:
    def __init__(
        self,
        model: str = "yolov8m.pt",
        device: str = "mps",
        target_classes: list[str] | None = None,
        min_score: float = 0.35,
        tracker: str = "bytetrack.yaml",
    ):
        from ultralytics import YOLO

        self.model = YOLO(model)
        self.device = device
        self.min_score = min_score
        self.tracker = tracker
        names = self.model.names  # {id: name}
        wanted = set(target_classes or ["dog"])
        unknown = wanted - set(names.values())
        if unknown:
            raise ValueError(f"Classes not in model: {sorted(unknown)}")
        self.class_ids = [i for i, n in names.items() if n in wanted]
        self.names = names

    def reset_tracks(self) -> None:
        """Forget tracker state (call between unrelated videos)."""
        self.model.predictor = None  # the tracker lives on the predictor; it is rebuilt on the next track() call

    def detect_once(self, image_bgr: np.ndarray) -> list[Detection]:
        """Detection without tracking (for offline sampling of single frames)."""
        res = self.model.predict(image_bgr, classes=self.class_ids, conf=self.min_score, device=self.device, verbose=False)[0]
        boxes = res.boxes
        if boxes is None or len(boxes) == 0:
            return []
        return [Detection(bbox=tuple(float(v) for v in b), score=float(s), class_name=self.names[int(c)])
                for b, s, c in zip(boxes.xyxy.cpu().numpy(), boxes.conf.cpu().numpy(), boxes.cls.cpu().numpy())]

    def detect(self, image_bgr: np.ndarray) -> list[Detection]:
        results = self.model.track(
            image_bgr,
            persist=True,
            tracker=self.tracker,
            classes=self.class_ids,
            conf=self.min_score,
            device=self.device,
            verbose=False,
        )
        boxes = results[0].boxes
        if boxes is None or len(boxes) == 0:
            return []
        xyxy = boxes.xyxy.cpu().numpy()
        conf = boxes.conf.cpu().numpy()
        cls = boxes.cls.cpu().numpy().astype(int)
        ids = boxes.id.cpu().numpy().astype(int) if boxes.id is not None else [None] * len(xyxy)
        return [
            Detection(
                bbox=tuple(float(v) for v in xyxy[i]),
                score=float(conf[i]),
                class_name=self.names[int(cls[i])],
                track_id=None if ids[i] is None else int(ids[i]),
            )
            for i in range(len(xyxy))
        ]
