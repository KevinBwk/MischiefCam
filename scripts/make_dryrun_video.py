"""Build a short synthetic video from an Ultralytics sample image for end-to-end dry runs.

There is no dog in it — run the pipeline with `--target-class person` to exercise
every stage (detection, zone overlap, state machine, VLM worker, events).

    uv run python scripts/make_dryrun_video.py --out data/dryrun.mp4
"""

from __future__ import annotations

import argparse
from pathlib import Path

import cv2
import numpy as np


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default="data/dryrun.mp4")
    ap.add_argument("--seconds", type=float, default=12.0)
    ap.add_argument("--fps", type=float, default=15.0)
    args = ap.parse_args()

    import ultralytics

    src = cv2.imread(str(Path(ultralytics.__file__).parent / "assets" / "bus.jpg"))
    h, w = src.shape[:2]
    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    writer = cv2.VideoWriter(str(out), cv2.VideoWriter_fourcc(*"mp4v"), args.fps, (w, h))
    n = int(args.seconds * args.fps)
    for i in range(n):
        shift = int(10 * np.sin(2 * np.pi * i / n))  # slight pan so frames are not identical
        frame = np.roll(src, shift, axis=1)
        writer.write(frame)
    writer.release()
    print(f"wrote {out} ({n} frames, {w}x{h} @ {args.fps} fps)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
