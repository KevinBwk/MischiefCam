# Stage II: porting to the ASUS UGen300 (Hailo-10H)

The Stage I prototype runs on a Mac (Apple M4 Pro, 24 GB). The UGen300 is a USB accelerator
(Hailo-10H, 8 GB LPDDR4, 40 TOPS INT4 / 20 TOPS INT8) that plugs into a host. ASUS lists Windows,
Linux and Android hosts, not macOS ([spec](https://www.asus.com/motherboards-components/ai-accelerator/ugen/ugen300-usb-8g/techspec/)),
so Stage II runs on a Windows or Linux host; bring-up starts on Linux (Ubuntu x86_64 is supported by
[hailo-apps](https://github.com/hailo-ai/hailo-apps)). Facts below are from vendor pages
(2026-10-24); our own on-device numbers do not exist yet.

## What moves where

| Stage I component (Mac) | Stage II target | Work |
|---|---|---|
| YOLOv8m + ByteTrack (`UltralyticsDetector`) | `yolov8m` HEF from the Hailo Model Zoo on the NPU; ByteTrack stays on the host CPU | new `DetectorBackend` (`detector.backend = "hailo"`), same `Detection` output incl. `couch` context boxes |
| CLIP ViT-B/16 image encoder (`CLIPEmbedder`) | `clip_vit_b_16` image-encoder HEF on the NPU | new `Embedder`; **re-train / re-threshold the logistic head on HEF embeddings** (hardware top-1 drops 68.6% → 64.6% on CIFAR-100, so Mac thresholds will not transfer) |
| Logistic-regression head, crops, state machine, events | host CPU, unchanged | none |
| Qwen2-VL-2B-Instruct, MLX 4-bit (`MLXVLMBackend`) | Hailo GenAI `Qwen2-VL-2B-Instruct` HEF (A8W4, 336×336) via the HailoRT GenAI Python API (`hailo_platform.genai`) | new `VLMBackend`; MLX is Apple-only. Official sample: hailo-apps `gen_ai_apps` (VLM Chat) |

The seams already exist: `DetectorBackend`, `Embedder`, `VLMBackend` and `FrameSource` are
protocols (`src/core/detector.py`, `probe.py`, `vlm.py`, `sources.py`); `config/default.toml`
already selects the judge backend by name (`vlm.backend`); Stage II wires `detector.backend` and
the embedder the same way. Porting adds backends; the pipeline, state machine, crops and alert
flow do not change.

## Expected timing (vendor single-model figures, not measured together)

| Stage | Mac prototype (measured) | Hailo-10H (vendor figure) | Implication |
|---|---|---|---|
| Detector per frame | see results table | yolov8m 76.2 FPS ≈ 13 ms | fine at 5–10 FPS |
| Classifier per review | see results table | clip_vit_b_16 51.5 FPS ≈ 19 ms | fine |
| VLM verdict (~20–30 tokens) | see results table | 1.02 s first token + 7.04 tokens/s ≈ 4–5 s | slower than the Mac (~0.5 s); alerts from the classifier stay fast, VLM-only alerts arrive seconds later |
| VLM visual assessment (~60–80 tokens) | see results table | ≈ 10–12 s | the card updates later; acceptable because the alert itself is not delayed |

All three models share one NPU. Whether they can stay resident together and how HailoRT
schedules them is **unverified**; Qwen2-VL alone is 2.18 GB of the 8 GB.

## Plan

1. **Bring-up** (Linux host + UGen300): run hailo-apps samples for detection, CLIP and VLM Chat.
2. **Backends**: `HailoDetector`, `HailoCLIPEmbedder`, `HailoVLMBackend` behind the existing protocols.
3. **Memory and scheduling**: load all three, measure device memory, and if they do not fit,
   keep YOLO + CLIP resident and load the VLM on demand (the classifier already gives the alert;
   the VLM only adds a second opinion and the assessment).
4. **Re-calibrate** the classifier head on HEF embeddings with the same labelled clips and the
   same 5% frame false-alert budget; re-run the frozen test-set protocol.
5. **Measure on device** with the same scripts (`scripts/batch_run.py`, `scripts/latency_report.py`):
   per-stage P50/P95, chewing-to-alert delay, false alerts per hour on real footage.
6. **Licensing**: decide between an Ultralytics Enterprise license and a permissive detector
   (YOLOX HEFs exist for Hailo-10H) before any commercial release.
