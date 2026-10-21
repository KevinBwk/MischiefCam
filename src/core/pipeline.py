"""Stage I pipeline: video -> detector -> zone overlap -> episode state machine -> VLM worker -> events."""

from __future__ import annotations

import time
from collections import deque
from dataclasses import dataclass, field
from pathlib import Path

import cv2
import numpy as np

from .crop import interaction_crop
from .detector import DetectorBackend
from .events import EventBus
from .roi import box_overlap_fraction, expand_box
from .sources import FrameSource
from .state import EpisodeTracker, StateConfig
from .types import ROI, Detection, Event, VLMRequest
from .vlm import build_prompt
from .worker import VLMWorker


@dataclass
class PipelineConfig:
    bbox_expand: float = 0.15
    min_overlap: float = 0.10
    vlm_input_size: int = 336
    crop_mode: str = "animal"
    max_new_tokens: int = 48
    frames: int = 1            # frames per judgement (multi-frame when > 1)
    frame_gap_s: float = 0.5   # minimum media-time gap between the frames sent together
    save_crops: bool = True
    output_dir: Path = Path("outputs")


@dataclass
class RunStats:
    frames: int = 0
    detections: int = 0
    reviews_requested: int = 0
    alerts: int = 0
    insufficient: int = 0
    errors: int = 0
    dropped: int = 0
    detector_ms: list[float] = field(default_factory=list)
    vlm_ms: list[float] = field(default_factory=list)
    max_detector_gap_s: float = 0.0


class Pipeline:
    def __init__(
        self,
        source: FrameSource,
        detector: DetectorBackend,
        rois: list[ROI],
        worker: VLMWorker,
        bus: EventBus,
        state_cfg: StateConfig,
        cfg: PipelineConfig,
        annotate_path: Path | None = None,
    ):
        self.source = source
        self.detector = detector
        # Stage I monitors forbidden zones only; "allowed" zones are kept for policy-swap tests later.
        self.rois = {r.id: r for r in rois if r.policy == "forbidden"}
        self.worker = worker
        self.bus = bus
        self.tracker = EpisodeTracker(state_cfg)
        self.cfg = cfg
        self.stats = RunStats()
        self.annotate_path = annotate_path
        self._last_det: dict[int, Detection] = {}
        self._episode_meta: dict[str, tuple[int, str]] = {}  # episode_id -> (track_id, roi_id)
        self._history: dict[int, deque] = {}  # track_id -> recent (pts, crop) while the dog is in a zone

    # ---------------------------------------------------------------------
    def run(self, drain_timeout_s: float = 120.0) -> RunStats:
        width, height = self.source.size
        writer = None
        if self.annotate_path:
            self.annotate_path.parent.mkdir(parents=True, exist_ok=True)
            writer = cv2.VideoWriter(str(self.annotate_path), cv2.VideoWriter_fourcc(*"mp4v"), 5.0, (width, height))
        last_pts = None
        last_wall = None
        try:
            for frame in self.source.frames():
                now = time.monotonic()
                if last_wall is not None:
                    self.stats.max_detector_gap_s = max(self.stats.max_detector_gap_s, now - last_wall)
                last_wall = now

                t0 = time.perf_counter()
                dets = self.detector.detect(frame.image)
                self.stats.detector_ms.append((time.perf_counter() - t0) * 1000)
                self.stats.frames += 1
                self.stats.detections += len(dets)

                present: set[tuple[int, str]] = set()
                for det in dets:
                    tid = det.track_id if det.track_id is not None else -1
                    self._last_det[tid] = det
                    box = expand_box(det.bbox, self.cfg.bbox_expand, width, height)
                    for roi in self.rois.values():
                        if box_overlap_fraction(box, roi, width, height) >= self.cfg.min_overlap:
                            present.add((tid, roi.id))

                if self.cfg.frames > 1:
                    self._remember_crops(frame.image, frame.pts_s, {tid for tid, _ in present})

                transition = self.tracker.update(frame.pts_s, present)
                for req in transition.reviews:
                    self._submit_review(frame.image, req.episode_id, req.track_id, req.roi_id, frame.pts_s)
                for ep in transition.closed:
                    self._publish("episode_closed", ep.episode_id, ep.track_id, ep.roi_id, frame.pts_s,
                                  extra={"verdicts": ep.verdicts, "duration_s": round(ep.last_seen - ep.first_seen, 2)})

                self._drain_outcomes()
                if writer is not None:
                    writer.write(self._annotate(frame.image, dets, frame.pts_s))
                last_pts = frame.pts_s

            self.worker.wait_idle(drain_timeout_s)
            self._drain_outcomes(final_pts=last_pts)
        finally:
            if writer is not None:
                writer.release()
        return self.stats

    # ---------------------------------------------------------------------
    def _remember_crops(self, image: np.ndarray, pts: float, track_ids: set[int]) -> None:
        """Keep a short history of crops for dogs that are in a zone (needed for multi-frame judgements)."""
        any_roi = next(iter(self.rois.values()), None)
        for tid in track_ids:
            det = self._last_det.get(tid)
            if det is None or any_roi is None:
                continue
            crop = interaction_crop(image, det.bbox, any_roi, self.cfg.vlm_input_size, self.cfg.bbox_expand, "animal")
            hist = self._history.setdefault(tid, deque(maxlen=max(8, self.cfg.frames * 6)))
            hist.append((pts, crop))
        for tid in list(self._history):
            if tid not in track_ids and self._history[tid] and pts - self._history[tid][-1][0] > 3.0:
                del self._history[tid]

    def _select_frames(self, track_id: int, latest) -> list:
        """Newest crop plus older ones spaced at least frame_gap_s apart, returned oldest first."""
        chosen = [latest]
        last_pts = latest[0]
        for pts, crop in reversed(self._history.get(track_id, ())):
            if len(chosen) >= self.cfg.frames:
                break
            if last_pts - pts >= self.cfg.frame_gap_s - 1e-6:
                chosen.append((pts, crop))
                last_pts = pts
        return [c for _, c in reversed(chosen)]

    def _submit_review(self, image: np.ndarray, episode_id: str, track_id: int, roi_id: str, pts: float) -> None:
        det = self._last_det.get(track_id)
        roi = self.rois[roi_id]
        if det is None:
            return
        crop = interaction_crop(image, det.bbox, roi, self.cfg.vlm_input_size, self.cfg.bbox_expand, self.cfg.crop_mode)
        images = self._select_frames(track_id, (pts, crop)) if self.cfg.frames > 1 else [crop]
        if self.cfg.save_crops:
            crop_dir = self.cfg.output_dir / "crops"
            crop_dir.mkdir(parents=True, exist_ok=True)
            for i, im in enumerate(images):
                im.save(crop_dir / f"{episode_id}_{int(pts * 1000)}_{i}.jpg")
        request = VLMRequest(images=tuple(images), prompt=build_prompt(roi.name, len(images), self.cfg.frame_gap_s),
                             max_new_tokens=self.cfg.max_new_tokens)
        self._episode_meta[episode_id] = (track_id, roi_id)
        self.worker.submit(episode_id, pts, request)
        self.stats.reviews_requested += 1
        self._publish("review", episode_id, track_id, roi_id, pts)

    def _drain_outcomes(self, final_pts: float | None = None) -> None:
        while not self.worker.outcomes.empty():
            out = self.worker.outcomes.get_nowait()
            job = out.job
            track_id, roi_id = self._episode_meta[job.episode_id]
            if out.error:
                kind = "dropped" if out.error.startswith("dropped") else "error"
                self.stats.dropped += kind == "dropped"
                self.stats.errors += kind == "error"
                self.tracker.on_verdict(job.episode_id, roi_id, None, job.pts_s)
                self._publish(kind, job.episode_id, track_id, roi_id, job.pts_s, reason=out.error)
                continue
            res = out.result
            self.stats.vlm_ms.append(res.elapsed_ms)
            alert = self.tracker.on_verdict(job.episode_id, roi_id, res.decision, job.pts_s)
            extra = {"raw": res.raw_text, "vlm_ms": round(res.elapsed_ms, 1)}
            if alert:
                self.stats.alerts += 1
                self._publish("alert", job.episode_id, track_id, roi_id, job.pts_s, res.decision, res.reason, extra)
            elif res.decision == "insufficient":
                self.stats.insufficient += 1
                self._publish("insufficient", job.episode_id, track_id, roi_id, job.pts_s, res.decision, res.reason, extra)

    def _publish(self, kind, episode_id, track_id, roi_id, pts, decision=None, reason="", extra=None) -> None:
        roi = self.rois.get(roi_id)
        self.bus.publish(Event(
            kind=kind, episode_id=episode_id, track_id=track_id, roi_id=roi_id,
            roi_name=roi.name if roi else roi_id, policy=roi.policy if roi else "forbidden",
            pts_s=round(pts, 3), decision=decision, reason=reason, extra=extra or {},
        ))

    def _annotate(self, image: np.ndarray, dets: list[Detection], pts: float) -> np.ndarray:
        h, w = image.shape[:2]
        canvas = image.copy()
        for roi in self.rois.values():
            pts_px = np.array([[int(x * w), int(y * h)] for x, y in roi.polygon], dtype=np.int32)
            cv2.polylines(canvas, [pts_px], True, (0, 0, 255), 2)
            cv2.putText(canvas, roi.name, tuple(pts_px[0]), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 0, 255), 2)
        for det in dets:
            x1, y1, x2, y2 = map(int, det.bbox)
            cv2.rectangle(canvas, (x1, y1), (x2, y2), (0, 200, 0), 2)
            cv2.putText(canvas, f"{det.class_name} #{det.track_id}", (x1, max(20, y1 - 6)),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 200, 0), 2)
        cv2.putText(canvas, f"t={pts:6.2f}s", (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.9, (255, 255, 255), 2)
        return canvas
