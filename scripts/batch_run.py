"""Run the pipeline over a folder of clips and print a verdict table.

Labels come from the labeling tool's JSON (or a legacy {"<file name>": label} map);
clips without a label are listed as "?". Example:

    uv run python scripts/batch_run.py data/raw --labels data/labels.json --rois config/rois.full_frame.json

Each clip gets its own folder under outputs/<batch-name>/. This is a dev check, not an evaluation:
it reports per-clip outcomes and makes no accuracy claim.
"""

from __future__ import annotations

import argparse
import contextlib
import io
import json
import statistics
from datetime import datetime
from pathlib import Path

from core import labels as L
from core.config import resolve
from core.main import main as run_clip

VIDEO_EXT = {".mp4", ".mov", ".m4v", ".webm"}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("folder")
    ap.add_argument("--labels", help="JSON mapping file name -> positive/negative/uncertain")
    ap.add_argument("--rois", required=True)
    ap.add_argument("--name", default=datetime.now().strftime("batch_%Y%m%d_%H%M%S"))
    ap.add_argument("--vlm", help="judge backend passed to mcam (mlx | probe | either)")
    ap.add_argument("--frames", type=int, help="frames per judgement passed to mcam")
    args = ap.parse_args()

    lab_data = L.load(args.labels) if args.labels else L.empty()
    clips = sorted(p for p in Path(args.folder).rglob("*") if p.suffix.lower() in VIDEO_EXT)
    rows = []
    for clip in clips:
        run_name = f"{args.name}/{clip.stem}"
        with contextlib.redirect_stdout(io.StringIO()):
            extra = (["--vlm", args.vlm] if args.vlm else []) + (["--frames", str(args.frames)] if args.frames else [])
            run_clip(["--video", str(clip), "--rois", args.rois, "--run-name", run_name, "--annotate"] + extra)
        run_dir = resolve("outputs") / run_name
        events = [json.loads(l) for l in (run_dir / "events.jsonl").read_text(encoding="utf-8").splitlines()]
        verdicts = [f"{e['pts_s']:.1f}s:{e['decision'] or e['kind']}" for e in events
                    if e["kind"] in ("alert", "insufficient", "error", "dropped")
                    or (e["kind"] == "episode_closed")]
        verdicts = [v for v in verdicts if not v.endswith("episode_closed")]
        alerted = any(e["kind"] == "alert" for e in events)
        first_alert = next((e["pts_s"] for e in events if e["kind"] == "alert"), None)
        rel = clip.relative_to(args.folder).as_posix()
        entry = lab_data["clips"].get(rel) or lab_data["clips"].get(clip.name)
        label = (L.clip_label(entry) if entry else None) or "?"
        outcome = {("positive", True): "TP", ("positive", False): "FN",
                   ("negative", True): "FP", ("negative", False): "TN"}.get((label, alerted), "-")
        chew_start = first_positive_start(entry) if entry else None
        delay = round(first_alert - chew_start, 2) if outcome == "TP" and chew_start is not None else None
        rows.append({"clip": str(clip.relative_to(args.folder)), "label": label, "alert": alerted,
                     "first_alert_s": first_alert, "chew_start_s": chew_start, "alert_delay_s": delay,
                     "outcome": outcome, "verdicts": verdicts})

    out = resolve("outputs") / args.name / "batch_summary.json"
    out.write_text(json.dumps(rows, indent=2, ensure_ascii=False), encoding="utf-8")
    w = max(len(r["clip"]) for r in rows) if rows else 10
    print(f"{'clip':<{w}}  label      alert  first   outcome  verdicts")
    for r in rows:
        fa = f"{r['first_alert_s']:.1f}s" if r["first_alert_s"] is not None else "-"
        print(f"{r['clip']:<{w}}  {r['label']:<9}  {str(r['alert']):<5}  {fa:<6}  {r['outcome']:<7}  {' '.join(r['verdicts'])}")
    totals = {k: sum(r["outcome"] == k for r in rows) for k in ("TP", "FN", "FP", "TN")}
    totals["unlabeled"] = sum(r["outcome"] == "-" for r in rows)
    delays = [r["alert_delay_s"] for r in rows if r["alert_delay_s"] is not None]
    totals["alert_delay_s"] = {"n": len(delays), "p50": _pct(delays, 50), "p95": _pct(delays, 95)}
    (out.parent / "batch_totals.json").write_text(json.dumps(totals, indent=2), encoding="utf-8")
    pos, neg = totals["TP"] + totals["FN"], totals["FP"] + totals["TN"]
    print(f"\ncaught {totals['TP']}/{pos}  missed {totals['FN']}/{pos}  false alerts {totals['FP']}/{neg}"
          + (f"  unlabeled {totals['unlabeled']}" if totals["unlabeled"] else ""))
    if delays:
        print(f"chewing start -> first alert (media time, s): P50 {totals['alert_delay_s']['p50']}  "
              f"P95 {totals['alert_delay_s']['p95']}  (n={len(delays)}; add judge latency for wall-clock)")
    print(f"\nsummary: {out}")
    return 0


def first_positive_start(entry: dict) -> float | None:
    """When chewing starts in the labels (earliest positive segment), or None."""
    starts = [s["start_s"] for s in entry.get("segments", []) if s["label"] == "positive"]
    return min(starts) if starts else None


def _pct(values: list[float], q: int) -> float | None:
    if not values:
        return None
    if len(values) == 1:
        return round(values[0], 2)
    return round(statistics.quantiles(values, n=100, method="inclusive")[q - 1], 2)


if __name__ == "__main__":
    raise SystemExit(main())
