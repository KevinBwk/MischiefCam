# Evaluation

How the numbers in the README were produced, and how to reproduce them.

## Data

All clips are AI-generated video (prompts in `prompts/`), 8 s, single fixed camera. The videos are
not in the repo; the human labels are (`data/labels_*.json`, written by `mcam-label`).
A clip or time span is **positive** from the first moment a dog's mouth bites, chews or tugs the
sofa (cushions and throw pillows count as sofa). Chewing a toy, a scrap or other furniture (e.g. a
table) is negative in Stage I, where only the sofa is protected.

| Set | Folder | Labels | Clips (pos / neg) | Use |
|---|---|---|---|---|
| Close-up | `data/Videos` | `labels_videos.json` | 41 (16 / 25) | development |
| Medium | `data/Medium-Videos` | `labels_medium.json` | 20 (7 / 13) | development |
| Wide | `data/Wide-Videos` | `labels_wide.json` | 20 (6 / 14) | development |
| Hard negatives | `data/HardNeg-Videos` | `labels_hardneg.json` | 10 (0 / 10) | development |
| Contrast pairs | `data/Pairs-Videos` | `labels_pairs.json` | 20 (10 / 10) | development (scored blind first, see below) |
| **Held-out test** | `data/Test-Videos` | `labels_test.json` | 50 of T01–T60 + D01–D05 | **evaluated once**, never trained or tuned on |

## Protected zone in evaluation

Clips come from many different rooms, so instead of drawing a zone per clip, evaluation uses the
**auto zone** (`config/rois.auto.json`): the protected zone is every couch the detector finds in the
frame, held for 3 s when the dog briefly hides it. A dog counts as "in the zone" when at least 10%
of its box (grown by 15%) overlaps a couch box; only then is it judged. Measured on the
development set: a couch was detected in 100% of positive and 99% of negative frames with a dog,
and every positive frame (214 / 214) passed the zone test, so the zone never hid a chewing dog
there. Whether each couch box is placed correctly was not checked frame by frame. A fixed home
camera uses a zone drawn once with `mcam-roi` instead.

## Two kinds of numbers

- **Development set (111 clips)**: every setting (crop, encoder, threshold, prompt) was chosen on
  these clips, so these numbers are optimistic. They are reported as the mean of 20 random
  scene-grouped 5-fold splits for the classifier × 3 runs of the VLM (`scripts/eval_combined.py`);
  both clips of a contrast pair always sit on the same side of a split.
- **Held-out test set**: prompts written to differ from all training prompts (unseen breeds,
  sofas, rooms, camera placements and wording; `scripts/gen_test_prompts.py`). The code commit and
  `models/classifier.json` are frozen first, then the set is labelled blind and run once with
  `batch_run.py --vlm either`. `build_dataset` refuses `data/Test-Videos`, so it cannot leak into
  training. These are the numbers to quote.
  - 50 of the 60 prompts are used (trimmed 2026-10-24 for generation time, keeping the 60's mix:
    20 positive, 20 hard negative, 10 ordinary negative; 19 close, 18 medium, 13 wide).
  - D01–D05 (`prompts/test_damaged_sofa_prompts.md`): the sofa is already torn and the dog does not
    chew it. Positive training clips almost always show damage appearing, so these check that the
    model alerts on chewing, not on visible damage.

## Development results (2026-10-23)

Judge "either" = CLIP linear probe (contact crop, 5% frame false-alert budget) OR Qwen2-VL-2B.

| Judge | Caught (positives) | False alerts (negatives) |
|---|---|---|
| Qwen2-VL-2B alone | 13.0 / 39 | 1.3 / 72 |
| CLIP classifier alone | 29.1 / 39 | 4.4 / 72 |
| **Either** | **29.9 / 39 (77%)** | **5.7 / 72 (8%)** |

Contrast pairs scored **blind** before they were added to training (classifier trained on the
other 91 clips, full pipeline): 8 / 10 caught, 1 / 10 false alerts.

## Reproduce

```bash
source scripts/env.sh --offline
# full pipeline over one folder, with totals and chewing-to-alert delay
uv run python scripts/batch_run.py data/Pairs-Videos --labels data/labels_pairs.json \
    --rois config/rois.auto.json --name eval_pairs_either --vlm either
# zone-only baseline: alert whenever a dog stays 2 s in the protected zone (every review says "suspect")
uv run python scripts/batch_run.py data/Pairs-Videos --labels data/labels_pairs.json \
    --rois config/rois.auto.json --name eval_pairs_zone_only --vlm fake
# latency P50 / P95 per stage (warm-up excluded), pooled over runs
uv run python scripts/latency_report.py outputs/eval_pairs_either
# development cross-validation (needs VLM batch runs named eval_<set><suffix>)
uv run python scripts/eval_combined.py "" _r2 _r3 --crop contact --fpr 0.05
```

## Results files

- `results/latency_mac_realtime_either.json`, `results/latency_mac_realtime_vlm_only.json`:
  per-stage P50 / P95 from `scripts/latency_report.py` (2026-10-24, MacBook Pro M4 Pro 24 GB,
  `mcam-demo` real-time playback of the 20 contrast-pair clips, judge "either" vs VLM only).
- Held-out test results go here once the frozen run is done.
