"""Build timestamped frame sheets for clips that still need an AI pre-label.

    uv run python scripts/make_label_sheets.py data/Videos --ai data/labels_ai.json
    uv run python scripts/make_label_sheets.py data/Medium-Videos --ai data/labels_ai_medium.json

Each sheet is a 4x4 grid of frames every 0.5 s (0.25 s, 0.75 s, ...), written to
outputs/ai_label/<folder>/<clip>.jpg. Clips already present in the --ai file are skipped,
so the script can be re-run after each new batch. It never reads the human label files.
"""

from __future__ import annotations

import argparse
from pathlib import Path

import cv2
import numpy as np

from core import labels as L
from core.config import resolve

VIDEO_EXT = {".mp4", ".mov", ".m4v", ".webm"}


def sheet(path: Path, out: Path, step: float = 0.5, cols: int = 4, tile=(400, 225)) -> int:
    cap = cv2.VideoCapture(str(path))
    dur = (cap.get(cv2.CAP_PROP_FRAME_COUNT) or 0) / (cap.get(cv2.CAP_PROP_FPS) or 30.0)
    tiles, t = [], step / 2
    while t < dur:
        cap.set(cv2.CAP_PROP_POS_MSEC, t * 1000)
        ok, fr = cap.read()
        fr = cv2.resize(fr, tile) if ok else np.zeros((tile[1], tile[0], 3), np.uint8)
        cv2.rectangle(fr, (0, 0), (70, 24), (0, 0, 0), -1)
        cv2.putText(fr, f"{t:.2f}", (4, 18), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 255), 2)
        tiles.append(fr)
        t += step
    cap.release()
    while len(tiles) % cols:
        tiles.append(np.zeros_like(tiles[0]))
    grid = np.vstack([np.hstack(tiles[r:r + cols]) for r in range(0, len(tiles), cols)])
    out.parent.mkdir(parents=True, exist_ok=True)
    cv2.imwrite(str(out), grid, [cv2.IMWRITE_JPEG_QUALITY, 80])
    return len(tiles)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("folder")
    ap.add_argument("--ai", required=True, help="AI pre-label file; clips already in it are skipped")
    ap.add_argument("--step", type=float, default=0.5)
    args = ap.parse_args()

    folder = resolve(args.folder)
    done = set(L.load(resolve(args.ai))["clips"])
    clips = sorted((p for p in folder.rglob("*") if p.suffix.lower() in VIDEO_EXT),
                   key=lambda p: (len(p.stem), p.stem))
    todo = [p for p in clips if p.relative_to(folder).as_posix() not in done and p.name not in done]
    out_dir = resolve("outputs/ai_label") / folder.name
    for p in todo:
        n = sheet(p, out_dir / f"{p.stem}.jpg", args.step)
        print(f"{p.relative_to(folder)}: {n} frames -> {out_dir / (p.stem + '.jpg')}")
    print(f"{len(todo)} sheet(s) written, {len(clips) - len(todo)} clip(s) already pre-labeled")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
