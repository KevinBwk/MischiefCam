"""Compare blind labels with what each generation prompt asked for. Run AFTER labeling.

    uv run python scripts/label_report.py --labels data/labels_videos.json --map data/video_prompt_map.json

Shows counts, unlabeled clips, and every clip whose label differs from the prompt's expected label.
A mismatch is not automatically a labeling error: generators often ignore parts of the prompt.
Keep the label that matches what is visible; use the list to re-check doubtful clips and to see
which prompt types the generator fails on.
"""

from __future__ import annotations

import argparse
import json
from collections import Counter
from pathlib import Path

from core import labels as L
from core.config import resolve


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--labels", default="data/labels_videos.json")
    ap.add_argument("--map", default="data/video_prompt_map.json")
    ap.add_argument("--prompts", default="prompts/training_video_prompts.json")
    ap.add_argument("--folder", default="data/Videos")
    args = ap.parse_args()

    labels = L.load(resolve(args.labels))["clips"]
    vmap = json.loads(resolve(args.map).read_text(encoding="utf-8"))["videos"]
    prompts = {p["id"]: p for p in json.loads(resolve(args.prompts).read_text(encoding="utf-8"))["prompts"]}
    clips = sorted(p.name for p in resolve(args.folder).glob("*") if p.suffix.lower() in (".mp4", ".mov", ".m4v", ".webm"))

    counts, unlabeled, rows = Counter(), [], []
    for name in clips:
        entry = labels.get(name)
        got = L.clip_label(entry) if entry else None
        if got is None:
            unlabeled.append(name)
            continue
        counts[got] += 1
        pid = (vmap.get(name) or {}).get("prompt_id")
        if not pid or pid not in prompts:
            continue
        exp = prompts[pid]
        behaviors = sorted({s.get("behavior", "") for s in entry["segments"]})
        if got != exp["label"]:
            rows.append((name, pid, exp["label"], exp["behavior"], got, ", ".join(behaviors)))

    print(f"clips: {len(clips)}  labeled: {sum(counts.values())}  {dict(counts)}")
    if unlabeled:
        print(f"unlabeled ({len(unlabeled)}): {', '.join(unlabeled)}")
    print(f"\nlabel differs from prompt ({len(rows)}):")
    if not rows:
        print("  none")
    for name, pid, el, eb, got, beh in rows:
        print(f"  {name:10s} {pid}  prompt expected {el:9s} ({eb})  ->  labeled {got:9s} [{beh}]")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
