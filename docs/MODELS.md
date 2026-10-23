# Models

What MischiefCam runs today (Stage I prototype on a Mac) and what each piece maps to on the
ASUS UGen300 (Hailo-10H). Sources checked 2026-10-24; sizes marked *local* were measured on the
dev machine. Anything we could not confirm is marked **unverified**.

| Role | Model | Version / source | Size | Precision | License | Hailo-10H counterpart |
|---|---|---|---|---|---|---|
| Detector (dog + couch, COCO-80) | Ultralytics YOLOv8m | `models/yolov8m.pt`, [ultralytics](https://github.com/ultralytics/ultralytics) | 25.9 M params; 52.1 MB file (*local*) | PyTorch checkpoint (stored precision **unverified**) | **AGPL-3.0** or Ultralytics Enterprise ([docs](https://docs.ultralytics.com/models/yolov8/)) | `yolov8m` HEF, 640×640, Model Zoo |
| Tracker | ByteTrack (Ultralytics implementation) | bundled with ultralytics | no weights | – | follows ultralytics (AGPL-3.0); original [ByteTrack](https://github.com/ifzhang/ByteTrack) is MIT | stays on host CPU |
| Classifier backbone | OpenAI CLIP ViT-B/16 image encoder, frozen | [`openai/clip-vit-base-patch16`](https://huggingface.co/openai/clip-vit-base-patch16) @ `57c2164` | ~600 MB checkpoint incl. text tower (*local*) | fp32 | code MIT ([openai/CLIP](https://github.com/openai/CLIP)); **weights license unverified** (HF card has none) | `clip_vit_b_16` image encoder HEF, 224×224, Model Zoo |
| Classifier head | Logistic regression (ours) | `models/classifier.json`, trained by `mcam-train` | 23 KB (*local*) | fp32 | this repo | stays on host CPU |
| VLM (verdict + visual assessment) | Qwen2-VL-2B-Instruct | [`mlx-community/Qwen2-VL-2B-Instruct-4bit`](https://huggingface.co/mlx-community/Qwen2-VL-2B-Instruct-4bit) @ `01af461`, converted from [`Qwen/Qwen2-VL-2B-Instruct`](https://huggingface.co/Qwen/Qwen2-VL-2B-Instruct) | 2 B params; 1.25 GB weights (*local*) | MLX 4-bit | Apache-2.0 | Hailo GenAI `Qwen2-VL-2B-Instruct` HEF, 336×336, A8W4 |

Experiment-only checkpoints in the local cache (CLIP ViT-L/14, SigLIP-B/16, SigLIP-L/16) are not
part of the pipeline; see the recall experiments for why CLIP ViT-B/16 was kept.

## Hailo-10H figures (vendor pages, single model, not measured by us)

| Model | Input | Hailo accuracy | Throughput | Source |
|---|---|---|---|---|
| yolov8m | 640×640×3 | COCO mAP 49.9 float → 49.2 on hardware | 76.2 FPS (batch 1) | [Model Zoo, object detection](https://github.com/hailo-ai/hailo_model_zoo/blob/master/docs/public_models/HAILO10H/HAILO10H_object_detection.rst) |
| clip_vit_b_16 | 224×224×3 | CIFAR-100 top-1 68.6% float → 64.6% on hardware | 51.5 FPS (batch 1) | [Model Zoo, zero-shot classification](https://github.com/hailo-ai/hailo_model_zoo/blob/master/docs/public_models/HAILO10H/HAILO10H_zero_shot_classification.rst) |
| Qwen2-VL-2B-Instruct | 336×336×3 | – | 7.04 tokens/s; time to first token 1.02 s; 2.18 GB; C++/Python API | [Hailo Model Explorer](https://hailo.ai/products/hailo-software/model-explorer/generative-ai/qwen2-vl-2b/) |

The CLIP accuracy drop on hardware is why the classifier head must be re-trained (or at least
re-thresholded) on embeddings produced by the HEF itself; see [STAGE2_PORT.md](STAGE2_PORT.md).

## Licensing note

YOLOv8 (and the Ultralytics tracker) are AGPL-3.0. Publishing this repo as open source under a
compatible license is fine; a closed commercial product would need an Ultralytics Enterprise
license or a permissively licensed detector. The Hailo-10H Model Zoo also ships YOLOX
(Apache-2.0: `yolox_s_leaky`, `yolox_l_leaky`, `yolox_s_wide_leaky`, `yolox_tiny`), a candidate
replacement whose accuracy on our clips is **unverified**. Whether the Hailo `yolov8m` HEF carries
the same terms as upstream is **unverified** (it lists Ultralytics as its source).

## Open items

1. CLIP ViT-B/16 weights license.
2. Precision and file size of the Hailo `yolov8m` and `clip_vit_b_16` HEFs.
3. How many HEFs can stay resident together in the UGen300's 8 GB (no official guidance found).
