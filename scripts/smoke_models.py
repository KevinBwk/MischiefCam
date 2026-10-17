"""Smoke test: load YOLO and Qwen2-VL-2B (MLX), run each once, print timings.

Uses an image bundled with Ultralytics (no dog in it) — this proves the stack works,
not that dog behaviour is recognised. Run with your own frames via --image.

    source scripts/env.sh && uv run python scripts/smoke_models.py [--image path.jpg]
"""

from __future__ import annotations

import argparse
import time
from pathlib import Path

import cv2

from core.config import resolve


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--image", help="Image to test (default: Ultralytics bundled bus.jpg)")
    ap.add_argument("--skip-vlm", action="store_true")
    args = ap.parse_args()

    import ultralytics
    from ultralytics import YOLO

    image_path = Path(args.image) if args.image else Path(ultralytics.__file__).parent / "assets" / "bus.jpg"
    frame = cv2.imread(str(image_path))
    assert frame is not None, f"cannot read {image_path}"
    print(f"image: {image_path} {frame.shape}")

    model = YOLO(str(resolve("models/yolov8m.pt")))
    for device in ("cpu", "mps"):
        model.predict(frame, device=device, verbose=False)  # warm-up
        t0 = time.perf_counter()
        res = model.predict(frame, device=device, verbose=False)[0]
        ms = (time.perf_counter() - t0) * 1000
        names = [res.names[int(c)] for c in res.boxes.cls.tolist()]
        print(f"YOLO {device}: {ms:.1f} ms, {len(names)} boxes: {sorted(set(names))}")

    if args.skip_vlm:
        return 0

    from PIL import Image

    from core.crop import letterbox
    from core.types import VLMRequest
    from core.vlm import MLXVLMBackend

    t0 = time.perf_counter()
    backend = MLXVLMBackend("mlx-community/Qwen2-VL-2B-Instruct-4bit")
    print(f"VLM load: {time.perf_counter() - t0:.1f} s")
    img: Image.Image = letterbox(frame, 336)
    prompt = (
        "Describe this image for a home camera log. Reply with JSON only: "
        '{"decision": "normal" | "suspect" | "insufficient", "reason": "<at most 12 words>"} '
        "where suspect means a dog is chewing furniture."
    )
    for i in range(2):
        r = backend.infer(VLMRequest(images=(img,), prompt=prompt, max_new_tokens=48))
        print(f"VLM run {i + 1}: {r.elapsed_ms:.0f} ms -> decision={r.decision!r} reason={r.reason!r}")
        print(f"   raw: {r.raw_text.strip()[:200]!r}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
