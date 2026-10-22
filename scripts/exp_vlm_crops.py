"""Experiment: which crop lets Qwen2-VL-2B (336 px, as on Hailo-10H) see chewing best?

Samples labeled frames at 1 fps from every labeled clip, builds several crops of the same frame and
asks the VLM once per crop. Reports frame-level suspect / insufficient rates and clip-level
recall / false alerts ("alert if any judged frame is suspect", all frames vs the first 3).

    uv run python scripts/exp_vlm_crops.py --out outputs/exp/vlm_crops.json
"""

from __future__ import annotations

import argparse
import json
import time
from collections import defaultdict

import cv2

from core import labels as L
from core.config import resolve
from core.crop import interaction_crop
from core.detector import UltralyticsDetector
from core.probe import pick_dog_and_couch
from core.types import ROI, VLMRequest
from core.vlm import MLXVLMBackend, build_prompt

SETS = [("close", "data/Videos", "data/labels_videos.json"), ("medium", "data/Medium-Videos", "data/labels_medium.json"),
        ("wide", "data/Wide-Videos", "data/labels_wide.json"), ("hardneg", "data/HardNeg-Videos", "data/labels_hardneg.json")]
VARIANTS = {"animal": ("animal", 0.15), "tight": ("animal", 0.0), "contact": ("contact", 0.15)}
WHOLE = ROI("frame", "frame", "forbidden", ((0, 0), (1, 0), (1, 1), (0, 1)))


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default="outputs/exp/vlm_crops.json")
    ap.add_argument("--fps", type=float, default=1.0)
    args = ap.parse_args()

    det = UltralyticsDetector(str(resolve("models/yolov8m.pt")), "mps", ["dog", "couch"])
    vlm = MLXVLMBackend("mlx-community/Qwen2-VL-2B-Instruct-4bit")
    prompt = build_prompt("sofa")
    rows = []
    t_start = time.time()
    for view, folder, lab in SETS:
        clips = L.load(resolve(lab))["clips"]
        for name, entry in sorted(clips.items()):
            clip_lab = L.clip_label(entry)
            if clip_lab not in ("positive", "negative"):
                continue
            cap = cv2.VideoCapture(str(resolve(folder) / name))
            dur = (cap.get(cv2.CAP_PROP_FRAME_COUNT) or 0) / (cap.get(cv2.CAP_PROP_FPS) or 30)
            t = 0.5
            while t < dur:
                fl = L.label_at(entry, t, dur)
                if fl in ("positive", "negative"):
                    cap.set(cv2.CAP_PROP_POS_MSEC, t * 1000)
                    ok, frame = cap.read()
                    if ok:
                        dog, couch = pick_dog_and_couch(det.detect_once(frame))
                        if dog is not None:
                            row = {"view": view, "clip": f"{view}/{name}", "clip_label": clip_lab, "frame_label": fl,
                                   "t": round(t, 2), "has_couch": couch is not None}
                            for v, (mode, expand) in VARIANTS.items():
                                img = interaction_crop(frame, dog, WHOLE, 336, expand, mode, zone_box=couch)
                                row[v] = vlm.infer(VLMRequest(images=(img,), prompt=prompt, max_new_tokens=48)).decision
                            rows.append(row)
                t += 1.0 / args.fps
            cap.release()
        print(f"{view}: done ({len(rows)} frames so far, {time.time() - t_start:.0f}s)", flush=True)
    out = resolve(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(rows, indent=1), encoding="utf-8")
    report(rows)
    return 0


def report(rows) -> None:
    print(f"\n{len(rows)} judged frames")
    print(f"{'crop':8s} | {'pos frames: suspect / insufficient':>34s} | {'neg frames: suspect':>20s} | "
          f"{'clips (all frames) TP/FP':>25s} | {'clips (first 3) TP/FP':>22s}")
    for v in VARIANTS:
        pf = [r for r in rows if r["frame_label"] == "positive"]
        nf = [r for r in rows if r["frame_label"] == "negative"]
        by_clip = defaultdict(list)
        for r in rows:
            by_clip[(r["clip"], r["clip_label"])].append(r)
        def clip_counts(first):
            tp = fp = 0
            for (c, lab), rs in by_clip.items():
                rs = rs[:first] if first else rs
                hit = any(r[v] == "suspect" for r in rs)
                tp += lab == "positive" and hit
                fp += lab == "negative" and hit
            return tp, fp
        npos = sum(1 for (c, lab) in by_clip if lab == "positive")
        nneg = sum(1 for (c, lab) in by_clip if lab == "negative")
        a, b = clip_counts(None), clip_counts(3)
        rate = lambda xs, d: f"{sum(r[v] == d for r in xs) / max(1, len(xs)):.0%}"
        print(f"{v:8s} | {rate(pf, 'suspect'):>16s} / {rate(pf, 'insufficient'):>15s} | {rate(nf, 'suspect'):>20s} | "
              f"{a[0]:>3d}/{npos} {a[1]:>3d}/{nneg:<12d} | {b[0]:>3d}/{npos} {b[1]:>3d}/{nneg}")


if __name__ == "__main__":
    raise SystemExit(main())
