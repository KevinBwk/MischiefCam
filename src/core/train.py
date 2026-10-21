"""Train and evaluate the chewing classifier from labeled clips.

    uv run mcam-train --folder data/raw --labels data/labels.json --out models/classifier.json

Prints a grouped-by-clip cross-validation report and writes the classifier JSON
(weights, threshold, embedding model, crop settings, and the report itself).
"""

from __future__ import annotations

import argparse
import json

from . import labels as L
from .config import resolve
from .probe import DEFAULT_EMBED_MODEL, CLIPEmbedder, build_dataset, make_sampler, save_classifier, train_and_evaluate


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="Train the chewing classifier (linear probe on CLIP embeddings).")
    ap.add_argument("--folder", default="data/Videos")
    ap.add_argument("--labels", default="data/labels_videos.json")
    ap.add_argument("--out", default="models/classifier.json")
    ap.add_argument("--embed-model", default=DEFAULT_EMBED_MODEL)
    ap.add_argument("--fps", type=float, default=2.0, help="frames sampled per second inside labeled segments")
    ap.add_argument("--folds", type=int, default=5)
    ap.add_argument("--max-fp-rate", type=float, default=0.02, help="frame-level FP rate allowed when picking the threshold")
    ap.add_argument("--k", type=int, default=2)
    ap.add_argument("--m", type=int, default=4)
    args = ap.parse_args(argv)

    from .detector import UltralyticsDetector

    labels = L.load(resolve(args.labels))
    print(f"labels: {len(labels['clips'])} clips in {resolve(args.labels)}")
    detector = UltralyticsDetector(str(resolve("models/yolov8m.pt")), "mps", ["dog", "couch"])
    embedder = CLIPEmbedder(args.embed_model)
    clips = build_dataset(resolve(args.folder), labels, embedder, make_sampler(detector), args.fps,
                          resolve("outputs/cache/embeddings"))
    report = train_and_evaluate(clips, args.folds, args.max_fp_rate, args.k, args.m)
    data = save_classifier(resolve(args.out), report, args.embed_model, args.fps, "animal", 0.15, 336, args.k, args.m)

    tr = data["training"]
    print(json.dumps({k: tr[k] for k in ("clips", "frames")}, ensure_ascii=False))
    cv = tr.get("cross_validation")
    if cv:
        print(f"cross-validation ({cv['method']}): threshold={cv['threshold']}  frame recall={cv['frame_level']['recall']}"
              f"  frame FP rate={cv['frame_level']['fp_rate']}  clips={cv['clip_level']}")
        for r in cv["per_clip"]:
            print(f"  {r['outcome']}  max_p={r['max_p']:.3f}  {r['clip']}")
    else:
        print("WARNING:", tr.get("warning"))
    print(f"classifier written to {resolve(args.out)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
