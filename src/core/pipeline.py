"""Stage I pipeline: video -> detector -> zone overlap -> episode state machine -> VLM worker -> events."""

from __future__ import annotations

import time
from collections import deque
from collections.abc import Callable
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
from .vlm import build_explain_prompt, build_prompt, parse_explanation
from .worker import VLMWorker


@dataclass
class PipelineConfig:
    bbox_expand: float = 0.15
    min_overlap: float = 0.10
    vlm_input_size: int = 336
    crop_mode: str = "animal"  # "animal" | "union" | "contact" (zoom on where the dog meets the zone/couch)
    probe_crop_mode: str | None = None  # classifier's crop when it differs from crop_mode (from classifier.json)
    context_classes: tuple[str, ...] = ()  # detector classes used only as context (e.g. couch), never tracked as pets
    auto_zone_hold_s: float = 3.0  # keep an auto zone's last boxes this long when the object is not detected
    max_new_tokens: int = 48
    explain_max_new_tokens: int = 96  # the visual-assessment JSON is longer than a verdict
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
    judge_ms: dict[str, list[float]] = field(default_factory=dict)  # raw ms per judge: clip / qwen / qwen_explain
    max_detector_gap_s: float = 0.0

    def add_timings(self, timings: dict, suffix: str = "") -> None:
        for name, ms in timings.items():
            self.judge_ms.setdefault(name + suffix, []).append(round(float(ms), 2))


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
        on_frame: Callable[[object, list[Detection], dict], None] | None = None,
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
        self.on_frame = on_frame  # called after every processed frame (live displays)
        self.last_verdict: dict[int, dict] = {}  # track_id -> latest judgement shown on screen
        self._last_det: dict[int, Detection] = {}
        self._context: list[Detection] = []  # latest context detections (e.g. couches)
        # auto zones (ROI.auto = a detector class): current boxes and when they were last seen
        self.auto_zones: dict[str, list[tuple[float, float, float, float]]] = {}
        self._auto_seen: dict[str, float] = {}
        missing = {r.auto for r in self.rois.values() if r.auto} - set(cfg.context_classes)
        if missing:
            raise ValueError(f"auto zones need these detector context classes: {sorted(missing)} "
                             "(add them to detector.context_classes)")
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
                self._context = [d for d in dets if d.class_name in self.cfg.context_classes]
                dets = [d for d in dets if d.class_name not in self.cfg.context_classes]
                self.stats.detector_ms.append((time.perf_counter() - t0) * 1000)
                self.stats.frames += 1
                self.stats.detections += len(dets)

                self._update_auto_zones(frame.pts_s)
                present: set[tuple[int, str]] = set()
                for det in dets:
                    tid = det.track_id if det.track_id is not None else -1
                    self._last_det[tid] = det
                    box = expand_box(det.bbox, self.cfg.bbox_expand, width, height)
                    for roi in self.rois.values():
                        if self._overlap(box, roi, width, height) >= self.cfg.min_overlap:
                            present.add((tid, roi.id))

                if self.cfg.frames > 1:
                    self._remember_crops(frame.image, frame.pts_s, {tid for tid, _ in present})

                transition = self.tracker.update(frame.pts_s, present)
                for req in transition.reviews:
                    self._submit_review(frame.image, req.episode_id, req.track_id, req.roi_id, frame.pts_s)
                for ep in transition.closed:
                    self._publish("episode_closed", ep.episode_id, ep.track_id, ep.roi_id, frame.pts_s,
                                  extra={"verdicts": ep.verdicts, "duration_s": round(ep.last_seen - ep.first_seen, 2)})

                if self.on_frame is not None:  # before draining: an alert's snapshot frame must already be shown
                    self.on_frame(frame, dets, self.frame_info(present))
                self._drain_outcomes()
                if writer is not None:
                    writer.write(self._annotate(frame.image, dets, frame.pts_s))
                last_pts = frame.pts_s

            for _ in range(2):  # a last alert can queue its explanation while draining: wait once more for it
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
            crop = self._crop(image, det, any_roi, self.cfg.crop_mode)
            hist = self._history.setdefault(tid, deque(maxlen=max(8, self.cfg.frames * 6)))
            hist.append((pts, crop))
        for tid in list(self._history):
            if tid not in track_ids and self._history[tid] and pts - self._history[tid][-1][0] > 3.0:
                del self._history[tid]

    def _crop(self, image: np.ndarray, det: Detection, roi: ROI, mode: str):
        """A judge's input. "contact" zooms on the dog's overlap with the couch it touches most, else the zone."""
        zone_box = None
        if roi.auto and mode == "union":
            mode = "contact"  # an auto zone has no polygon; its boxes are what contact already aims at
        if mode == "contact":
            best = max(self._context, key=lambda c: _inter(det.bbox, c.bbox), default=None)  # sampler's rule
            if best is not None and _inter(det.bbox, best.bbox) > 0:
                zone_box = best.bbox
            else:
                mode = "animal"  # no touching couch: training (whole-frame zone) fell back to the animal crop too
        return interaction_crop(image, det.bbox, roi, self.cfg.vlm_input_size, self.cfg.bbox_expand, mode,
                                zone_box=zone_box)

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
        crop = self._crop(image, det, roi, self.cfg.crop_mode)
        images = self._select_frames(track_id, (pts, crop)) if self.cfg.frames > 1 else [crop]
        probe_mode = self.cfg.probe_crop_mode
        probe_images = (self._crop(image, det, roi, probe_mode),) if probe_mode and probe_mode != self.cfg.crop_mode else ()
        if self.cfg.save_crops:
            crop_dir = self.cfg.output_dir / "crops"
            crop_dir.mkdir(parents=True, exist_ok=True)
            for i, im in enumerate(images):
                im.save(crop_dir / f"{episode_id}_{int(pts * 1000)}_{i}.jpg")
        request = VLMRequest(images=tuple(images), prompt=build_prompt(roi.name, len(images), self.cfg.frame_gap_s),
                             max_new_tokens=self.cfg.max_new_tokens, probe_images=probe_images)
        self._episode_meta[episode_id] = (track_id, roi_id)
        self.worker.submit(episode_id, pts, request, owner=self)
        self.stats.reviews_requested += 1
        self._publish("review", episode_id, track_id, roi_id, pts)

    def _drain_outcomes(self, final_pts: float | None = None) -> None:
        while not self.worker.outcomes.empty():
            out = self.worker.outcomes.get_nowait()
            job = out.job
            if job.owner is not None and job.owner is not self:
                continue  # late result from an earlier clip on a shared worker
            track_id, roi_id = self._episode_meta[job.episode_id]
            if job.kind == "explain":  # assessment for an alert that already fired: never a verdict
                if out.result:
                    self.stats.add_timings(out.result.timings, "_explain")
                expl = parse_explanation(out.result.raw_text) if out.result else None
                self._publish("explained", job.episode_id, track_id, roi_id, job.pts_s,
                              expl["assessment"] if expl else None, (expl or {}).get("observation", ""),
                              {"alert_key": _alert_key(job.episode_id, job.pts_s), "explanation": expl,
                               "error": out.error, "raw": out.result.raw_text if out.result else "",
                               "vlm_ms": round(out.result.elapsed_ms, 1) if out.result else None})
                continue
            if out.error:
                kind = "dropped" if out.error.startswith("dropped") else "error"
                self.stats.dropped += kind == "dropped"
                self.stats.errors += kind == "error"
                self.tracker.on_verdict(job.episode_id, roi_id, None, job.pts_s)
                self._publish(kind, job.episode_id, track_id, roi_id, job.pts_s, reason=out.error)
                continue
            res = out.result
            self.stats.vlm_ms.append(res.elapsed_ms)
            self.stats.add_timings(res.timings)
            self.last_verdict[track_id] = {"decision": res.decision, "pts": job.pts_s, "reason": res.reason,
                                           "ms": round(res.elapsed_ms), "raw": res.raw_text}
            need = self.tracker.cfg.vlm_confirmations if res.source == "vlm" else 1
            alert = self.tracker.on_verdict(job.episode_id, roi_id, res.decision, job.pts_s, required=need)
            if res.decision == "suspect" and not alert:
                self._publish("confirming", job.episode_id, track_id, roi_id, job.pts_s, res.decision, res.reason,
                              {"raw": res.raw_text, "vlm_ms": round(res.elapsed_ms, 1)})
            extra = {"raw": res.raw_text, "vlm_ms": round(res.elapsed_ms, 1)}
            if alert:
                self.stats.alerts += 1
                extra["alert_key"] = _alert_key(job.episode_id, job.pts_s)
                extra["judge_source"] = res.source
                # Classifier alerts go out at once; the VLM's visual assessment follows as an "explained" event.
                extra["explaining"] = res.source == "probe" and self.worker.explainer is not None
                self._publish("alert", job.episode_id, track_id, roi_id, job.pts_s, res.decision, res.reason, extra)
                if extra["explaining"]:
                    self._request_explanation(job.episode_id, roi_id, job.pts_s, job.request.images)
            elif res.decision == "insufficient":
                self.stats.insufficient += 1
                self._publish("insufficient", job.episode_id, track_id, roi_id, job.pts_s, res.decision, res.reason, extra)

    def _request_explanation(self, episode_id: str, roi_id: str, pts: float, images: tuple) -> None:
        roi = self.rois[roi_id]
        req = VLMRequest(images=images[-1:], prompt=build_explain_prompt(roi.name),
                         max_new_tokens=self.cfg.explain_max_new_tokens)
        self.worker.submit(episode_id, pts, req, kind="explain", owner=self)

    def _update_auto_zones(self, pts: float) -> None:
        for roi in self.rois.values():
            if not roi.auto:
                continue
            boxes = [d.bbox for d in self._context if d.class_name == roi.auto]
            if boxes:
                self.auto_zones[roi.id], self._auto_seen[roi.id] = boxes, pts
            elif pts - self._auto_seen.get(roi.id, -1e9) > self.cfg.auto_zone_hold_s:
                self.auto_zones[roi.id] = []  # e.g. a dog lying on the sofa hides it briefly: hold, then drop

    def _overlap(self, box, roi: ROI, width: float, height: float) -> float:
        """Fraction of the (expanded) dog box inside the zone: a drawn polygon or the auto zone's boxes."""
        if not roi.auto:
            return box_overlap_fraction(box, roi, width, height)
        area = max(1e-6, (box[2] - box[0]) * (box[3] - box[1]))
        return max((_inter(box, b) / area for b in self.auto_zones.get(roi.id, [])), default=0.0)

    def frame_info(self, present: set) -> dict:
        """Per-dog state for live displays: {track_id: {"zones": [...], "state": str, "verdict": {...}}}."""
        dogs: dict[int, dict] = {}
        for (tid, roi_id), ep in self.tracker.episodes.items():
            d = dogs.setdefault(tid, {"zones": [], "state": "", "verdict": self.last_verdict.get(tid)})
            d["zones"].append(self.rois[roi_id].name if roi_id in self.rois else roi_id)
            d["state"] = ep.state.value
        return {"dogs": dogs, "in_zone": sorted({tid for tid, _ in present}),
                "auto_zones": {rid: list(boxes) for rid, boxes in self.auto_zones.items()}}

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
            if roi.auto:
                for b in self.auto_zones.get(roi.id, []):
                    x1, y1, x2, y2 = map(int, b)
                    cv2.rectangle(canvas, (x1, y1), (x2, y2), (0, 0, 255), 2)
                    cv2.putText(canvas, f"{roi.name} (auto)", (x1, max(20, y1 - 6)), cv2.FONT_HERSHEY_SIMPLEX, 0.8,
                                (0, 0, 255), 2)
                continue
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


def _inter(a, b) -> float:
    return max(0.0, min(a[2], b[2]) - max(a[0], b[0])) * max(0.0, min(a[3], b[3]) - max(a[1], b[1]))


def _alert_key(episode_id: str, pts: float) -> str:
    """Links an alert to its later "explained" event (and to the reviewed frame)."""
    return f"{episode_id}@{pts:.3f}"
