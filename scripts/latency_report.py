"""Pool raw timings from many runs and report P50 / P95 per stage (warm-up excluded).

    uv run python scripts/latency_report.py outputs/eval_close_either_ct outputs/demo_20261024_101500
    uv run python scripts/latency_report.py outputs/<batch> --json outputs/latency.json

Each argument is a batch folder (outputs/<name>/, one sub-folder per clip) or a demo/run folder;
every timings.json under it is read. Stages: detector (YOLO + tracker, per frame), clip
(CLIP embedding + linear probe), qwen (Qwen2-VL verdict), qwen_explain (visual assessment after a
classifier alert), and alert_delay (labelled chewing start -> first alert, media time, from
batch_summary.json; the wall-clock delay adds the judge latency of that review).
P95: sort the samples from fast to slow; the value 95% of samples stay under.
"""

from __future__ import annotations

import argparse
import json
import statistics
from pathlib import Path

from core.metrics import machine_info


def pct(values: list[float], q: int) -> float | None:
    if not values:
        return None
    if len(values) == 1:
        return round(values[0], 1)
    return round(statistics.quantiles(values, n=100, method="inclusive")[q - 1], 1)


def collect(folders: list[Path]) -> tuple[dict[str, list[float]], dict[str, int], set[str]]:
    pooled: dict[str, list[float]] = {}
    dropped: dict[str, int] = {}
    modes: set[str] = set()
    for folder in folders:
        for path in sorted(folder.rglob("timings.json")):
            t = json.loads(path.read_text(encoding="utf-8"))
            modes.add(t.get("mode", "?"))
            wd, wj = t["warmup"]["detector_frames"], t["warmup"]["judge_calls"]
            pooled.setdefault("detector", []).extend(t["detector_ms"][wd:])
            dropped["detector"] = dropped.get("detector", 0) + min(wd, len(t["detector_ms"]))
            for name, values in t["judge_ms"].items():
                w = wj.get(name, 0) if isinstance(wj, dict) else wj  # per-judge counts (older files: one int)
                pooled.setdefault(name, []).extend(values[w:])
                dropped[name] = dropped.get(name, 0) + min(w, len(values))
        for summary in sorted(folder.rglob("batch_summary.json")):
            delays = [r["alert_delay_s"] for r in json.loads(summary.read_text(encoding="utf-8"))
                      if r.get("alert_delay_s") is not None]
            pooled.setdefault("alert_delay_s", []).extend(delays)
    return pooled, dropped, modes


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("folders", nargs="+", type=Path)
    ap.add_argument("--json", type=Path, help="also write the report here")
    args = ap.parse_args()

    pooled, dropped, modes = collect(args.folders)
    machine = machine_info()
    report = {"machine": machine, "modes": sorted(modes), "folders": [str(f) for f in args.folders], "stages": {}}
    print(f"machine: {machine.get('model', '?')} · {machine.get('chip', machine['machine'])} · "
          f"{machine.get('ram_gb', '?')} GB RAM · runs: {', '.join(sorted(modes)) or '-'}")
    print(f"{'stage':14s} {'n':>6s} {'P50':>9s} {'P95':>9s}  unit   warm-up dropped")
    order = ["detector", "clip", "qwen", "qwen_explain", "fake", "alert_delay_s"]
    for name in sorted(pooled, key=lambda n: (order.index(n) if n in order else 99, n)):
        values = pooled[name]
        unit = "s" if name == "alert_delay_s" else "ms"
        p50, p95 = pct(values, 50), pct(values, 95)
        report["stages"][name] = {"n": len(values), "p50": p50, "p95": p95, "unit": unit,
                                  "warmup_dropped": dropped.get(name, 0)}
        print(f"{name:14s} {len(values):>6d} {p50 if p50 is not None else '-':>9} {p95 if p95 is not None else '-':>9}  "
              f"{unit:<5s}  {dropped.get(name, 0)}")
    if args.json:
        args.json.parent.mkdir(parents=True, exist_ok=True)
        args.json.write_text(json.dumps(report, indent=2), encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
