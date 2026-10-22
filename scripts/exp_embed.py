"""Experiment: which image encoder (all available in the Hailo-10H model zoo) and which crop
gives the linear probe the best clip-level recall at a fixed false-alert budget?

    uv run python scripts/exp_embed.py --models openai/clip-vit-base-patch16 openai/clip-vit-large-patch14 \
        --crops animal contact

For every (model, crop) the 91 human-labeled clips are embedded once (cached), then 20 random
clip-grouped 5-fold splits are run. Threshold = 2% frame FP rate on out-of-fold negatives, alert
rule 2 of 4 frames. Reports the mean / min / max clip TP and FP over the splits.
"""

from __future__ import annotations

import argparse
import json
import random

import numpy as np

from core import labels as L
from core.config import resolve
from core.detector import UltralyticsDetector
from core.probe import (SAMPLER_VERSION, CLIPEmbedder, LogisticProbe, build_dataset, clip_alert, make_sampler,
                        pick_threshold)

SETS = [("data/Videos", "data/labels_videos.json"), ("data/Medium-Videos", "data/labels_medium.json"),
        ("data/Wide-Videos", "data/labels_wide.json"), ("data/HardNeg-Videos", "data/labels_hardneg.json")]


def random_folds(clips, k, rng):
    pos = [c.clip for c in clips if c.label == 1]
    neg = [c.clip for c in clips if c.label == 0]
    rng.shuffle(pos)
    rng.shuffle(neg)
    folds = [set() for _ in range(k)]
    for i, c in enumerate(pos + neg):
        folds[i % k].add(c)
    return folds


def evaluate(clips, splits, max_fp_rate, k, m, seed=0):
    rng = random.Random(seed)
    tps, fps_, frame_rec = [], [], []
    for _ in range(splits):
        oof = {}
        for fs in random_folds(clips, 5, rng):
            tr = [c for c in clips if c.clip not in fs]
            probe = LogisticProbe.fit(np.vstack([c.X for c in tr]), np.concatenate([c.frame_labels for c in tr]))
            for c in clips:
                if c.clip in fs:
                    oof[c.clip] = probe.proba(c.X)
        P = np.concatenate([oof[c.clip] for c in clips])
        Y = np.concatenate([c.frame_labels for c in clips])
        thr = pick_threshold(P, Y, max_fp_rate)
        alerts = {c.clip: clip_alert(oof[c.clip], thr, k, m) for c in clips}
        tps.append(sum(alerts[c.clip] for c in clips if c.label == 1))
        fps_.append(sum(alerts[c.clip] for c in clips if c.label == 0))
        frame_rec.append(float((P[Y == 1] >= thr).mean()))
    return np.array(tps), np.array(fps_), float(np.mean(frame_rec))


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--models", nargs="+", default=["openai/clip-vit-base-patch16"])
    ap.add_argument("--crops", nargs="+", default=["animal", "contact"])
    ap.add_argument("--fps", type=float, default=2.0)
    ap.add_argument("--splits", type=int, default=20)
    ap.add_argument("--max-fp-rate", type=float, nargs="+", default=[0.02, 0.04])
    ap.add_argument("--out", default="outputs/exp/embed.json")
    args = ap.parse_args()

    detector = UltralyticsDetector(str(resolve("models/yolov8m.pt")), "mps", ["dog", "couch"])
    results = []
    for model in args.models:
        embedder = CLIPEmbedder(model)
        for crop in args.crops:
            sampler = make_sampler(detector, crop=crop)
            clips = []
            for folder, lab in SETS:
                got = build_dataset(resolve(folder), L.load(resolve(lab)), embedder, sampler, args.fps,
                                    resolve("outputs/cache/embeddings"), crop=f"{crop}-{SAMPLER_VERSION}",
                                    log=lambda *_: None)
                for c in got:
                    c.clip = f"{folder}/{c.clip}"
                clips += got
            npos = sum(c.label for c in clips)
            for fpr in args.max_fp_rate:
                tp, fp, frec = evaluate(clips, args.splits, fpr, 2, 4)
                row = {"model": model, "crop": crop, "max_fp_rate": fpr, "pos": npos, "neg": len(clips) - npos,
                       "tp_mean": float(tp.mean()), "tp_min": int(tp.min()), "tp_max": int(tp.max()),
                       "fp_mean": float(fp.mean()), "fp_min": int(fp.min()), "fp_max": int(fp.max()),
                       "frame_recall": round(frec, 3)}
                results.append(row)
                print(f"{model:40s} {crop:8s} fpr={fpr:.2f}  TP {tp.mean():5.1f}/{npos} [{tp.min()}-{tp.max()}]  "
                      f"FP {fp.mean():4.1f}/{len(clips) - npos} [{fp.min()}-{fp.max()}]  frame recall {frec:.2f}",
                      flush=True)
        del embedder
    out = resolve(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(results, indent=1), encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
