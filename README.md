# MischiefCam

> On-device AI that spots pet mischief before it spreads.
> Mascot / reminder: **Michelle** — she is the voice of every notification.

*Product name is provisional.* All user-facing names live in [`config/branding.toml`](config/branding.toml);
the Python package is intentionally called `core`. To rename across docs:
`uv run python scripts/rename_product.py "MischiefCam" "NewName" --dry-run`.

Built for the ASUS UGen AI League (Battlefield Lightning — ASUS UGen300 / Hailo-10H).
Stage I runs on a MacBook (Apple Silicon); Stage II ports the same pipeline to UGen300.

## What it does (Stage I scope)

Single camera, single dog, owner-defined protected zones. When a dog stays in a *forbidden* zone,
a vision-language model looks at an interaction crop and answers `suspect / normal / insufficient`.
Only `suspect` produces an alert; `insufficient`, parse errors and timeouts are logged, never shown as "normal".
Everything runs locally; no frame leaves the machine.

```
video file ─► YOLO (dog) + ByteTrack ─► zone overlap ─► episode state machine
                                                        │ (dwell, re-observe, cooldown)
                                                        ▼
                                        crop 336×336 ─► VLM worker (bounded queue)
                                                        ▼
                                        events.jsonl + Michelle notification
```

## Setup (macOS, Apple Silicon)

```bash
brew install ffmpeg
uv sync
source scripts/env.sh
uv run pytest -q
uv run python scripts/smoke_models.py
```

`scripts/env.sh` keeps model caches inside the project (`.hf_cache/`, `.yolo_config/`) and disables telemetry.
After models are downloaded, `source scripts/env.sh --offline` makes any Hugging Face network access an error.

## Draw protected zones

```bash
uv run mcam-roi --video data/raw/your_clip.mp4 --at 2
```

Opens a local page (http://127.0.0.1:8765, localhost only) showing a snapshot of the clip.
Click **New zone**, click around the sofa / shoe rack / cable area, click the first point to close,
name it, choose **Forbidden** (alert) or **Allowed** (ignore), and **Save**. Corners can be dragged;
the slider picks a different snapshot time. Zones are saved to `config/rois.json` (git-ignored, it is your home layout)
in normalized coordinates, which the pipeline reads by default.

## Generate, label and train

| Step | Command | What it does |
|---|---|---|
| Prompts | `prompts/training_video_prompts.*` (close, 60), `prompts/medium_prompts.*` (medium, 20), `prompts/wide_trial_prompts.*` (wide, 20) | Curated CCTV-style prompts, about 1 positive : 2 negatives per view. `scripts/gen_video_prompts.py` regenerates the original 120-prompt close-up pool (overwrites the curated file) |
| Label | `uv run mcam-label` | Local page (blind: no prompt hints for id-only file names): mark time segments in `data/Videos` as positive / negative / uncertain → `data/labels_videos.json` |
| Check | `uv run python scripts/label_report.py` | After labeling: lists clips whose label differs from what the prompt asked for |
| AI-assisted | `uv run mcam-label --suggest data/labels_ai.json` | Shows AI pre-labels as suggestions (press G to apply, then review and save; saved with `ai_assisted: true`). Keep test sets blind by omitting `--suggest` |
| Agreement | `uv run python scripts/compare_labels.py data/labels_videos.json data/labels_ai.json` | Clip- and time-level agreement between two label files, with every disagreement listed |
| Train | `uv run mcam-train` | CLIP embeddings of animal crops → logistic-regression probe, cross-validated by clip → `models/classifier.json` |
| Use | `uv run mcam --video clip.mp4 --vlm probe` | The trained classifier replaces the VLM as the judge |

## Demo view (for the video)

```bash
uv run mcam-demo --playlist demo/playlist.json      # scenes with captions, real-time playback
uv run mcam-demo --camera 0                         # live camera: device index, or rtsp/http URL
```

Local page (127.0.0.1:8768) with the camera view, zone / dog / state overlay, the judge's reason,
and Michelle's notification cards with snapshots. It opens paused: start the screen recording, then
press Start or Space. Recorded clips are labelled "synthetic clip — pre-recorded video, live inference".
Default judge: classifier OR VLM (`--vlm either`). List cameras: `ffmpeg -f avfoundation -list_devices true -i ""`.

## Run

```bash
uv run mcam --video data/your_clip.mp4 --annotate
```

Dry run without a dog (exercises every stage with people instead; uses the example zones):

```bash
uv run python scripts/make_dryrun_video.py --out data/dryrun.mp4
uv run mcam --video data/dryrun.mp4 --target-class person --rois config/rois.example.json --annotate
```

Outputs go to `outputs/run_*/`: `events.jsonl`, `summary.json` (counts, detector/VLM latency P50/P95,
max detector gap), `crops/`, and `annotated.mp4` with `--annotate`.

## Configuration

| File | Purpose |
|---|---|
| `config/default.toml` | detector, zones, state-machine timings, VLM backend, outputs |
| `config/rois.example.json` | protected zones as normalized polygons, each `forbidden` or `allowed` |
| `config/branding.toml` | product name, mascot name, notification copy |

## Implemented / measured / planned

| Item | Status |
|---|---|
| Local video source, YOLO dog detection + tracking (MPS) | implemented |
| Zone overlap (expanded box ∩ polygon), episode state machine keyed by (track, zone) | implemented, unit-tested |
| Qwen2-VL-2B (MLX, 4-bit) verdicts with strict JSON parsing | implemented |
| Background VLM worker, bounded queue, stale/full drops reported | implemented, unit-tested |
| Event log + mascot notifications | implemented |
| Latency / detector-gap numbers on real dog footage | **to be measured** |
| ROI-only vs ROI+VLM evaluation on held-out clips | planned |
| Zone editor web page (draw / drag / name / policy / save, localhost only) | implemented, tested |
| Labeling tool, prompt generator, CLIP linear-probe training with clip-grouped CV | implemented, unit-tested (real training needs labeled clips) |
| Live camera source (device index or rtsp/http URL), demo view | implemented (camera not yet tested on hardware) |
| Tap-to-select zones (FastSAM) | planned |
| Hailo backends (`hailo_platform.genai.VLM`, Hailo YOLO HEF) on UGen300 | planned (Stage II) |

## Repository layout

```
config/    runtime, zones, branding
scripts/   env setup, smoke tests, dry-run video, product rename
src/core/  pipeline (types, sources, detector, roi, state, vlm, worker, crop, events, pipeline, main)
tests/     unit tests (no models needed)
notes/     private planning notes (git-ignored)
```
