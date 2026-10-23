"""Cross-validate the CLIP linear probe over several labeled folders at once.

    uv run python scripts/eval_probe.py data/Videos:data/labels_videos.json data/Medium-Videos:data/labels_ai_medium.json

Each argument is FOLDER:LABELS. Folds are grouped by scene (a clip, or both clips of a contrast pair,
never sit in both train and test). Results are reported overall and per folder. This only evaluates; it does not
overwrite models/classifier.json.
"""

from __future__ import annotations

import argparse
import json

import numpy as np

from core import labels as L
from core.config import resolve
from core.probe import (DEFAULT_EMBED_MODEL, CLIPEmbedder, LogisticProbe, build_dataset, clip_alert, group_folds,
                        make_sampler, pick_threshold)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("sets", nargs="+", help="FOLDER:LABELS pairs")
    ap.add_argument("--fps", type=float, default=2.0)
    ap.add_argument("--folds", type=int, default=5)
    ap.add_argument("--max-fp-rate", type=float, default=0.02)
    ap.add_argument("--k", type=int, default=2)
    ap.add_argument("--m", type=int, default=4)
    ap.add_argument("--out", default="outputs/eval_probe.json")
    args = ap.parse_args()

    from core.detector import UltralyticsDetector

    detector = UltralyticsDetector(str(resolve("models/yolov8m.pt")), "mps", ["dog", "couch"])
    embedder = CLIPEmbedder(DEFAULT_EMBED_MODEL)
    sampler = make_sampler(detector)
    clips, origin = [], {}
    for pair in args.sets:
        folder, lab = pair.split(":", 1)
        got = build_dataset(resolve(folder), L.load(resolve(lab)), embedder, sampler, args.fps,
                            resolve("outputs/cache/embeddings"), log=lambda *_: None)
        for c in got:
            c.clip = f"{folder}/{c.clip}"
            origin[c.clip] = folder
        clips += got
        print(f"{folder}: {len(got)} clips ({sum(c.label for c in got)} positive) from {lab}")

    labels = {c.clip: c.label for c in clips}
    folds = group_folds(list(labels), labels, args.folds)
    oof = {}
    for fs in folds:
        tr = [c for c in clips if c.clip not in fs]
        probe = LogisticProbe.fit(np.vstack([c.X for c in tr]), np.concatenate([c.frame_labels for c in tr]))
        for c in clips:
            if c.clip in fs:
                oof[c.clip] = probe.proba(c.X)
    P = np.concatenate([oof[c.clip] for c in clips])
    Y = np.concatenate([c.frame_labels for c in clips])
    thr = pick_threshold(P, Y, args.max_fp_rate)

    rows = []
    for c in clips:
        alert = clip_alert(oof[c.clip], thr, args.k, args.m)
        outcome = {(1, True): "TP", (1, False): "FN", (0, True): "FP", (0, False): "TN"}[(c.label, alert)]
        rows.append({"clip": c.clip, "folder": origin[c.clip], "label": c.label, "outcome": outcome,
                     "max_p": round(float(oof[c.clip].max()), 3)})

    def summary(rs):
        o = {k: sum(r["outcome"] == k for r in rs) for k in ("TP", "FN", "FP", "TN")}
        return o
    print(f"\nthreshold={thr:.3f} (frame FP rate <= {args.max_fp_rate}), rule: >= {args.k} of {args.m} frames")
    print(f"frame recall={float((P[Y == 1] >= thr).mean()):.2f}  frame FP rate={float((P[Y == 0] >= thr).mean()):.3f}")
    print("overall:", summary(rows))
    for folder in dict.fromkeys(origin.values()):
        print(f"  {folder}:", summary([r for r in rows if r["folder"] == folder]))
    for r in rows:
        if r["outcome"] in ("FN", "FP"):
            print(f"  {r['outcome']}  max_p={r['max_p']:.3f}  {r['clip']}")
    resolve(args.out).write_text(json.dumps({"threshold": thr, "rows": rows}, indent=1), encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
