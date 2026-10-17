"""Run the pipeline over a folder of clips and print a verdict table.

Labels come from a JSON file {"<file name>": "positive" | "negative" | "uncertain"};
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
from datetime import datetime
from pathlib import Path

from core.config import resolve
from core.main import main as run_clip

VIDEO_EXT = {".mp4", ".mov", ".m4v", ".webm"}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("folder")
    ap.add_argument("--labels", help="JSON mapping file name -> positive/negative/uncertain")
    ap.add_argument("--rois", required=True)
    ap.add_argument("--name", default=datetime.now().strftime("batch_%Y%m%d_%H%M%S"))
    args = ap.parse_args()

    labels = json.loads(Path(args.labels).read_text(encoding="utf-8")) if args.labels else {}
    clips = sorted(p for p in Path(args.folder).rglob("*") if p.suffix.lower() in VIDEO_EXT)
    rows = []
    for clip in clips:
        run_name = f"{args.name}/{clip.stem}"
        with contextlib.redirect_stdout(io.StringIO()):
            run_clip(["--video", str(clip), "--rois", args.rois, "--run-name", run_name, "--annotate"])
        run_dir = resolve("outputs") / run_name
        events = [json.loads(l) for l in (run_dir / "events.jsonl").read_text(encoding="utf-8").splitlines()]
        verdicts = [f"{e['pts_s']:.1f}s:{e['decision'] or e['kind']}" for e in events
                    if e["kind"] in ("alert", "insufficient", "error", "dropped")
                    or (e["kind"] == "episode_closed")]
        verdicts = [v for v in verdicts if not v.endswith("episode_closed")]
        alerted = any(e["kind"] == "alert" for e in events)
        first_alert = next((e["pts_s"] for e in events if e["kind"] == "alert"), None)
        label = labels.get(clip.name, "?")
        outcome = {("positive", True): "TP", ("positive", False): "FN",
                   ("negative", True): "FP", ("negative", False): "TN"}.get((label, alerted), "-")
        rows.append({"clip": str(clip.relative_to(args.folder)), "label": label, "alert": alerted,
                     "first_alert_s": first_alert, "outcome": outcome, "verdicts": verdicts})

    out = resolve("outputs") / args.name / "batch_summary.json"
    out.write_text(json.dumps(rows, indent=2, ensure_ascii=False), encoding="utf-8")
    w = max(len(r["clip"]) for r in rows) if rows else 10
    print(f"{'clip':<{w}}  label      alert  first   outcome  verdicts")
    for r in rows:
        fa = f"{r['first_alert_s']:.1f}s" if r["first_alert_s"] is not None else "-"
        print(f"{r['clip']:<{w}}  {r['label']:<9}  {str(r['alert']):<5}  {fa:<6}  {r['outcome']:<7}  {' '.join(r['verdicts'])}")
    print(f"\nsummary: {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
