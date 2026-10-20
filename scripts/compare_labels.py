"""Compare two label files (e.g. human vs AI pre-labels) on the clips they share.

    uv run python scripts/compare_labels.py data/labels_videos.json data/labels_ai.json

Reports clip-level agreement (positive / negative / uncertain), time-level agreement on a
0.25 s grid (only where both files have a label), a confusion table, and every disagreement.
"""

from __future__ import annotations

import argparse
from collections import Counter

import cv2

from core import labels as L
from core.config import resolve

CLASSES = ("positive", "negative", "uncertain")


def duration(path) -> float:
    cap = cv2.VideoCapture(str(path))
    fps = cap.get(cv2.CAP_PROP_FPS) or 0
    n = cap.get(cv2.CAP_PROP_FRAME_COUNT) or 0
    cap.release()
    return n / fps if fps else 8.0


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("reference", help="labels treated as ground truth (usually the human file)")
    ap.add_argument("candidate", help="labels to check (e.g. AI pre-labels)")
    ap.add_argument("--folder", default="data/Videos")
    ap.add_argument("--step", type=float, default=0.25)
    args = ap.parse_args()

    ref = L.load(resolve(args.reference))["clips"]
    cand = L.load(resolve(args.candidate))["clips"]
    shared = sorted(set(ref) & set(cand), key=lambda k: (len(k), k))
    if not shared:
        print("no clips in common")
        return 1

    clip_conf, time_conf = Counter(), Counter()
    clip_rows, time_rows = [], []
    for name in shared:
        r_lab, c_lab = L.clip_label(ref[name]), L.clip_label(cand[name])
        clip_conf[(r_lab, c_lab)] += 1
        if r_lab != c_lab:
            clip_rows.append((name, r_lab, c_lab))
        dur = duration(resolve(args.folder) / name)
        t, run = 0.0, None
        while t < dur:
            a, b = L.label_at(ref[name], t, dur), L.label_at(cand[name], t, dur)
            if a and b:
                time_conf[(a, b)] += 1
                if a != b:
                    run = (run[0], t, a, b) if run and run[2:] == (a, b) else (t, t, a, b)
                    if not time_rows or time_rows[-1][0] != name or time_rows[-1][1] != run[0]:
                        time_rows.append([name, run[0], t, a, b])
                    else:
                        time_rows[-1][2] = t
                else:
                    run = None
            t += args.step

    def table(conf, title):
        total = sum(conf.values())
        agree = sum(v for (a, b), v in conf.items() if a == b)
        print(f"\n{title}: {agree}/{total} agree ({100 * agree / total:.0f}%)")
        print(f"{'reference \\ candidate':>22} " + " ".join(f"{c:>10}" for c in CLASSES))
        for a in CLASSES:
            print(f"{a:>22} " + " ".join(f"{conf.get((a, b), 0):>10}" for b in CLASSES))

    print(f"clips compared: {len(shared)}  ({args.reference} vs {args.candidate})")
    table(clip_conf, "clip level")
    table(time_conf, f"time level ({args.step}s steps, labeled in both)")
    print("\nclip-level disagreements:")
    for name, a, b in clip_rows or [("none", "", "")]:
        print(f"  {name:9s} reference={a}  candidate={b}" if a or b else "  none")
    print("\ntime ranges that disagree (>= 0.5 s):")
    shown = [r for r in time_rows if r[2] - r[1] >= 0.5 - 1e-9]
    for name, s, e, a, b in shown or [["none", 0, 0, "", ""]]:
        print(f"  {name:9s} {s:4.2f}-{e + args.step:4.2f}s  reference={a}  candidate={b}" if a else "  none")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
