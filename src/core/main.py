"""CLI entry point: run the Stage I pipeline on a local video file."""

from __future__ import annotations

import argparse
import json
import statistics
from datetime import datetime
from pathlib import Path

from .branding import load_branding
from .config import load_config, resolve
from .detector import UltralyticsDetector
from .events import EventBus, JsonlSink, MascotNotifier
from .pipeline import Pipeline, PipelineConfig
from .roi import load_rois
from .sources import make_source
from .state import StateConfig
from .vlm import make_backend, probe_crop
from .worker import VLMWorker


def _pct(values: list[float], q: float) -> float | None:
    if not values:
        return None
    if len(values) == 1:
        return round(values[0], 1)
    return round(statistics.quantiles(values, n=100, method="inclusive")[int(q) - 1], 1)


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="Run the pet-mischief pipeline on a video file.")
    src = ap.add_mutually_exclusive_group(required=True)
    src.add_argument("--video", help="Path to a local video file")
    src.add_argument("--camera", help="Live camera: device index (0, 1, …) or rtsp/http stream URL")
    ap.add_argument("--config", help="Optional TOML file overriding config/default.toml")
    ap.add_argument("--rois", help="ROI JSON (default: [roi].file in config)")
    ap.add_argument("--vlm", choices=["mlx", "fake", "probe", "either"],
                    help="Override judge backend (probe = trained classifier, either = probe OR VLM)")
    ap.add_argument("--frames", type=int, help="Frames per judgement (multi-frame when > 1)")
    ap.add_argument("--target-class", action="append", help="Override detector classes (repeatable), e.g. person for dry runs")
    ap.add_argument("--annotate", action="store_true", help="Write an annotated video next to the run outputs")
    ap.add_argument("--run-name", help="Output folder name under [output].dir (default: run_<timestamp>)")
    args = ap.parse_args(argv)

    cfg = load_config(args.config)
    branding = load_branding()
    if args.vlm:
        cfg["vlm"]["backend"] = args.vlm
    if args.target_class:
        cfg["detector"]["target_classes"] = args.target_class
    if args.frames:
        cfg["vlm"]["frames"] = args.frames

    run_dir = resolve(cfg["output"]["dir"]) / (args.run_name or datetime.now().strftime("run_%Y%m%d_%H%M%S"))
    run_dir.mkdir(parents=True, exist_ok=True)

    source = make_source(args.video, args.camera, cfg["source"]["target_fps"])
    det_cfg = cfg["detector"]
    detector = UltralyticsDetector(str(resolve(det_cfg["model"])), det_cfg["device"], det_cfg["target_classes"],
                                   det_cfg["min_score"], det_cfg["tracker"],
                                   det_cfg.get("context_classes", []))
    roi_path = resolve(args.rois or cfg["roi"]["file"])
    if not roi_path.exists() and not args.rois:
        roi_path = resolve("config/rois.example.json")
        print(f"[warn] no zones drawn yet — using example zones ({roi_path}). Draw yours with: uv run mcam-roi --video <clip>")
    rois = load_rois(roi_path)
    vcfg = cfg["vlm"]
    worker = VLMWorker(make_backend(vcfg), vcfg["queue_size"], vcfg["max_age_s"])

    bus = EventBus()
    sink = JsonlSink(run_dir / "events.jsonl")
    bus.subscribe(sink)
    bus.subscribe(MascotNotifier(branding, notify_insufficient=cfg["output"].get("notify_insufficient", False)))

    pipe = Pipeline(
        source, detector, rois, worker, bus,
        StateConfig(**cfg["state"]),
        PipelineConfig(bbox_expand=cfg["roi"]["bbox_expand"], min_overlap=cfg["roi"]["min_overlap"],
                       vlm_input_size=vcfg["input_size"], crop_mode=vcfg.get("crop", "animal"), probe_crop_mode=probe_crop(vcfg),
                       context_classes=tuple(det_cfg.get("context_classes", [])),
                       max_new_tokens=vcfg["max_new_tokens"], frames=vcfg.get("frames", 1),
                       frame_gap_s=vcfg.get("frame_gap_s", 0.5), save_crops=cfg["output"]["save_crops"],
                       output_dir=run_dir),
        annotate_path=run_dir / "annotated.mp4" if args.annotate else None,
    )
    print(f"[{branding.product_name}] running on {args.video or 'camera ' + str(args.camera)} (VLM: {vcfg['backend']}, mascot: {branding.mascot_name})")
    try:
        stats = pipe.run()
    finally:
        worker.close()
        sink.close()

    summary = {
        "product": branding.product_name,
        "video": str(args.video or f"camera:{args.camera}"),
        "frames": stats.frames,
        "detections": stats.detections,
        "reviews_requested": stats.reviews_requested,
        "alerts": stats.alerts,
        "insufficient": stats.insufficient,
        "errors": stats.errors,
        "dropped": stats.dropped,
        "detector_ms_p50": _pct(stats.detector_ms, 50),
        "detector_ms_p95": _pct(stats.detector_ms, 95),
        "vlm_ms_p50": _pct(stats.vlm_ms, 50),
        "vlm_ms_p95": _pct(stats.vlm_ms, 95),
        "max_detector_gap_s": round(stats.max_detector_gap_s, 3),
        "config": cfg,
    }
    (run_dir / "summary.json").write_text(json.dumps(summary, indent=2, ensure_ascii=False), encoding="utf-8")
    print(json.dumps({k: v for k, v in summary.items() if k != "config"}, indent=2, ensure_ascii=False))
    print(f"outputs: {run_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
