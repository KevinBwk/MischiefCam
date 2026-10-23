"""Linear probe on frozen image embeddings ("is the dog chewing a forbidden object?").

Training (mcam-train): labeled clips -> crops (--crop, default "contact"; recorded in the JSON so the
pipeline feeds the same crop) -> frozen CLIP embeddings -> logistic regression. Evaluation is grouped by
scene: frames of one clip, or both clips of a contrast pair, never sit in both train and test.
The result is a small JSON file the pipeline can load as a judge backend.

Why this design: little data is needed, it trains in seconds on a Mac, and on UGen300 the image
encoder can be a Hailo model-zoo CLIP HEF while this classifier (a few KB) runs on the host CPU.
"""

from __future__ import annotations

import hashlib
import json
import os
import re
import time
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Callable, Protocol

import numpy as np

from .types import VLMRequest, VLMResult

DEFAULT_EMBED_MODEL = "openai/clip-vit-base-patch16"  # same family as Hailo zoo clip_vit_b_16 (HEF equivalence to verify)


# --------------------------------------------------------------------------- embeddings
class Embedder(Protocol):
    model_id: str

    def embed(self, images: list) -> np.ndarray: ...  # (N, D) float32, L2-normalised


class CLIPEmbedder:
    def __init__(self, model_id: str = DEFAULT_EMBED_MODEL, device: str = "mps"):
        import torch
        from transformers import AutoImageProcessor, AutoModel

        self.model_id = model_id  # any CLIP or SigLIP checkpoint (both expose get_image_features)
        self.torch = torch
        self.device = device if (device != "mps" or torch.backends.mps.is_available()) else "cpu"
        self.model = AutoModel.from_pretrained(model_id).to(self.device).eval()
        self.processor = AutoImageProcessor.from_pretrained(model_id)  # images only: no tokenizer deps

    def embed(self, images: list) -> np.ndarray:
        if not images:
            return np.zeros((0, 0), dtype=np.float32)
        from .device import torch_gpu_lock

        with torch_gpu_lock, self.torch.no_grad():
            inputs = self.processor(images=images, return_tensors="pt").to(self.device)
            out = self.model.get_image_features(**inputs)
            if isinstance(out, self.torch.Tensor):
                feats = out
            elif getattr(out, "image_embeds", None) is not None:
                feats = out.image_embeds
            else:  # some transformers versions return a model output object
                feats = out.pooler_output
            feats = feats.float().cpu().numpy()
        return feats / np.linalg.norm(feats, axis=1, keepdims=True).clip(min=1e-8)


# --------------------------------------------------------------------------- classifier
@dataclass
class LogisticProbe:
    weights: np.ndarray
    bias: float

    @staticmethod
    def fit(X: np.ndarray, y: np.ndarray, l2: float = 1e-2, epochs: int = 2000, lr: float = 0.5) -> "LogisticProbe":
        """Class-balanced L2-regularised logistic regression (full-batch gradient descent, deterministic)."""
        n, d = X.shape
        pos = max(1, int(y.sum()))
        neg = max(1, n - pos)
        sw = np.where(y == 1, n / (2 * pos), n / (2 * neg))
        w = np.zeros(d)
        b = 0.0
        for _ in range(epochs):
            z = X @ w + b
            p = 1.0 / (1.0 + np.exp(-np.clip(z, -30, 30)))
            g = sw * (p - y)
            w -= lr * (X.T @ g / n + l2 * w)
            b -= lr * g.mean()
        return LogisticProbe(w.astype(np.float32), float(b))

    def proba(self, X: np.ndarray) -> np.ndarray:
        z = X @ self.weights + self.bias
        return 1.0 / (1.0 + np.exp(-np.clip(z, -30, 30)))


def clip_alert(probs: np.ndarray, threshold: float, k: int = 2, m: int = 4) -> bool:
    """Episode rule: alert if at least k of any m consecutive frames are at or above threshold."""
    hits = (np.asarray(probs) >= threshold).astype(int)
    if len(hits) < k:
        return False
    window = min(m, len(hits))
    return any(hits[i:i + window].sum() >= k for i in range(len(hits) - window + 1))


_PAIR = re.compile(r"(p\d+)[ab](\.\w+)?$", re.IGNORECASE)


def scene_group(clip_id: str) -> str:
    """Clips that share a scene must sit on the same side of a split: contrast pairs p01a/p01b -> p01."""
    head, _, name = clip_id.rpartition("/")
    m = _PAIR.match(name)
    return f"{head}/{m.group(1).lower()}" if m else clip_id


def _split(groups: dict[str, list[str]], group_label: dict[str, int], k: int, order) -> list[set[str]]:
    pos = order([g for g in groups if group_label[g] == 1])
    neg = order([g for g in groups if group_label[g] == 0])
    folds = [set() for _ in range(k)]
    for i, g in enumerate(pos + neg):
        folds[i % k].update(groups[g])
    return [f for f in folds if f]


def _groups(clip_ids, clip_labels):
    groups: dict[str, list[str]] = {}
    for c in clip_ids:
        groups.setdefault(scene_group(c), []).append(c)
    return groups, {g: max(clip_labels[c] for c in cs) for g, cs in groups.items()}


def group_folds(clip_ids: list[str], clip_labels: dict[str, int], k: int) -> list[set[str]]:
    """Split clip ids into k folds by scene group (see scene_group), alternating positive and negative
    groups so each fold gets both."""
    groups, glab = _groups(clip_ids, clip_labels)
    return _split(groups, glab, k, sorted)


def random_group_folds(clip_ids: list[str], clip_labels: dict[str, int], k: int, rng) -> list[set[str]]:
    """Like group_folds but with shuffled group order (for repeated random splits)."""
    groups, glab = _groups(clip_ids, clip_labels)

    def shuffled(xs):
        xs = sorted(xs)
        rng.shuffle(xs)
        return xs
    return _split(groups, glab, k, shuffled)


def pick_threshold(probs: np.ndarray, y: np.ndarray, max_fp_rate: float = 0.02) -> float:
    """Lowest threshold whose frame-level false-positive rate on negatives stays <= max_fp_rate."""
    negs = np.sort(probs[y == 0])
    if len(negs) == 0:
        return 0.5
    allowed = int(np.floor(max_fp_rate * len(negs)))
    idx = len(negs) - allowed - 1
    return float(min(0.99, negs[idx] + 1e-6)) if idx >= 0 else 0.0


# --------------------------------------------------------------------------- dataset
@dataclass
class ClipFrames:
    clip: str
    label: int                 # clip-level: 1 positive, 0 negative
    times: np.ndarray          # sample times (s)
    frame_labels: np.ndarray   # per-frame 1/0 (frames inside labeled segments only)
    X: np.ndarray              # (n, D) embeddings


def cache_key(path: Path, model_id: str, fps: float, crop: str, expand: float) -> str:
    st = path.stat()
    raw = f"{path.resolve()}|{st.st_size}|{int(st.st_mtime)}|{model_id}|{fps}|{crop}|{expand}"
    return hashlib.sha1(raw.encode()).hexdigest()[:16]


FrameSampler = Callable[[Path, float], list[tuple[float, object]]]  # -> [(t, PIL crop or None)]


SAMPLER_VERSION = "couchpref-v2"  # part of the embedding cache key; bump when frame/dog selection changes


def _area(b) -> float:
    return max(0.0, b[2] - b[0]) * max(0.0, b[3] - b[1])


def _inter(a, b) -> float:
    return _area((max(a[0], b[0]), max(a[1], b[1]), min(a[2], b[2]), min(a[3], b[3])))


def pick_dog_and_couch(dets, expand: float = 0.15):
    """Like pick_dog, but also returns the couch box the chosen dog overlaps most (or None)."""
    dog = pick_dog(dets, expand)
    if dog is None:
        return None, None
    couches = [d.bbox for d in dets if d.class_name == "couch"]
    best = max(couches, key=lambda c: _inter(dog, c), default=None)
    return dog, (best if best is not None and _inter(dog, best) > 0 else None)


def pick_dog(dets, expand: float = 0.15):
    """Choose which dog to crop when several are visible.

    Prefer the dog whose (expanded) box overlaps a detected couch the most, because the
    question is whether a dog is chewing the sofa; fall back to the largest dog when no
    couch is detected or no dog touches one. Returns the bbox or None.
    """
    dogs = [d.bbox for d in dets if d.class_name == "dog"]
    couches = [d.bbox for d in dets if d.class_name == "couch"]
    if not dogs:
        return None

    def grow(b):
        dx, dy = (b[2] - b[0]) * expand, (b[3] - b[1]) * expand
        return (b[0] - dx, b[1] - dy, b[2] + dx, b[3] + dy)

    if couches:
        scored = [(max(_inter(grow(d), c) for c in couches) / max(_area(grow(d)), 1e-6), d) for d in dogs]
        best_overlap, best = max(scored, key=lambda s: s[0])
        if best_overlap > 0:
            return best
    return max(dogs, key=_area)


def make_sampler(detector, size: int = 336, expand: float = 0.15, crop: str = "animal") -> FrameSampler:
    """Sample frames at `fps` and return the crop of the dog most likely to be at the sofa (or None).

    The detector should include the "couch" class (see pick_dog); with dogs only it picks the largest dog.
    """
    import cv2

    from .crop import interaction_crop
    from .types import ROI

    whole = ROI("frame", "frame", "forbidden", ((0, 0), (1, 0), (1, 1), (0, 1)))

    def sample(path: Path, fps: float):
        cap = cv2.VideoCapture(str(path))
        duration = (cap.get(cv2.CAP_PROP_FRAME_COUNT) or 0) / (cap.get(cv2.CAP_PROP_FPS) or 30.0)
        out = []
        t = 0.25
        while t < duration:
            cap.set(cv2.CAP_PROP_POS_MSEC, t * 1000)
            ok, frame = cap.read()
            if not ok:
                break
            box, couch = pick_dog_and_couch(detector.detect_once(frame), expand)
            if box is not None:
                out.append((t, interaction_crop(frame, box, whole, size, expand, crop, zone_box=couch)))
            else:
                out.append((t, None))
            t += 1.0 / fps
        cap.release()
        return out

    return sample


def build_dataset(
    folder: Path, labels: dict, embedder: Embedder, sampler: FrameSampler, fps: float,
    cache_dir: Path | None, crop: str = "animal-" + SAMPLER_VERSION, expand: float = 0.15, log=print,
) -> list[ClipFrames]:
    from . import labels as L

    if "Test-Videos" in Path(folder).parts and os.environ.get("MCAM_ALLOW_TEST_SET") != "1":
        raise ValueError(f"{folder} is the held-out test set: it must not be used for training or tuning "
                         "(see prompts/test_set_prompts.md). Evaluate it once with the full pipeline instead.")
    clips = []
    for rel, entry in sorted(labels["clips"].items()):
        lab = L.clip_label(entry)
        if lab not in ("positive", "negative"):
            continue  # uncertain clips are not used for training
        path = folder / rel
        if not path.exists():
            matches = list(folder.rglob(Path(rel).name))
            if not matches:
                log(f"  skip (missing file): {rel}")
                continue
            path = matches[0]
        cached = None
        if cache_dir is not None:
            cache_dir.mkdir(parents=True, exist_ok=True)
            cached = cache_dir / f"{cache_key(path, embedder.model_id, fps, crop, expand)}.npz"
        if cached is not None and cached.exists():
            z = np.load(cached)
            times, X = z["times"], z["X"]
        else:
            samples = [(t, img) for t, img in sampler(path, fps) if img is not None]
            times = np.array([t for t, _ in samples], dtype=np.float32)
            X = embedder.embed([img for _, img in samples]) if samples else np.zeros((0, 1), np.float32)
            if cached is not None:
                np.savez(cached, times=times, X=X)
        duration = float(times.max()) + 1.0 if len(times) else 0.0
        keep, ys = [], []
        for i, t in enumerate(times):
            fl = L.label_at(entry, float(t), duration)
            if fl in ("positive", "negative"):
                keep.append(i)
                ys.append(1 if fl == "positive" else 0)
        if not keep:
            log(f"  skip (no labeled frames with a dog): {rel}")
            continue
        clips.append(ClipFrames(rel, 1 if lab == "positive" else 0, times[keep], np.array(ys), X[keep]))
        log(f"  {rel}: {len(keep)} frames ({lab})")
    return clips


# --------------------------------------------------------------------------- training + evaluation
def train_and_evaluate(clips: list[ClipFrames], folds: int = 5, max_fp_rate: float = 0.02,
                       k: int = 2, m: int = 4) -> dict:
    n_pos = sum(c.label == 1 for c in clips)
    n_neg = sum(c.label == 0 for c in clips)
    if n_pos == 0 or n_neg == 0:
        raise ValueError(f"need both positive and negative clips (have {n_pos} positive, {n_neg} negative)")
    X = np.vstack([c.X for c in clips])
    y = np.concatenate([c.frame_labels for c in clips])

    report: dict = {"clips": {"positive": n_pos, "negative": n_neg}, "frames": {"positive": int(y.sum()), "negative": int((1 - y).sum())}}
    evaluable = min(n_pos, n_neg) >= 2
    if evaluable:
        ids = [c.clip for c in clips]
        fold_sets = group_folds(ids, {c.clip: c.label for c in clips}, min(folds, min(n_pos, n_neg)))
        oof: dict[str, np.ndarray] = {}
        for fs in fold_sets:
            tr = [c for c in clips if c.clip not in fs]
            te = [c for c in clips if c.clip in fs]
            ytr = np.concatenate([c.frame_labels for c in tr])
            if ytr.min() == ytr.max():
                continue
            probe = LogisticProbe.fit(np.vstack([c.X for c in tr]), ytr)
            for c in te:
                oof[c.clip] = probe.proba(c.X)
        all_p = np.concatenate([oof[c.clip] for c in clips if c.clip in oof])
        all_y = np.concatenate([c.frame_labels for c in clips if c.clip in oof])
        thr = pick_threshold(all_p, all_y, max_fp_rate)
        per_clip = []
        tp = fn = fp = tn = 0
        for c in clips:
            if c.clip not in oof:
                continue
            alert = clip_alert(oof[c.clip], thr, k, m)
            outcome = {(1, True): "TP", (1, False): "FN", (0, True): "FP", (0, False): "TN"}[(c.label, alert)]
            tp += outcome == "TP"; fn += outcome == "FN"; fp += outcome == "FP"; tn += outcome == "TN"
            per_clip.append({"clip": c.clip, "label": "positive" if c.label else "negative", "alert": alert,
                             "outcome": outcome, "max_p": round(float(oof[c.clip].max()), 3)})
        fpos = all_p[all_y == 1] >= thr
        fneg = all_p[all_y == 0] >= thr
        report["cross_validation"] = {
            "method": f"{len(fold_sets)}-fold, grouped by scene (clip, or contrast pair)",
            "threshold": round(thr, 4), "threshold_rule": f"frame FP rate <= {max_fp_rate}",
            "episode_rule": f"alert if >= {k} of {m} consecutive frames >= threshold",
            "frame_level": {"recall": round(float(fpos.mean()), 3) if len(fpos) else None,
                            "fp_rate": round(float(fneg.mean()), 3) if len(fneg) else None},
            "clip_level": {"TP": tp, "FN": fn, "FP": fp, "TN": tn},
            "per_clip": per_clip,
        }
    else:
        thr = 0.5
        report["cross_validation"] = None
        report["warning"] = "Fewer than 2 clips in a class: trained without evaluation. Do not report any accuracy."

    final = LogisticProbe.fit(X, y)
    report["threshold"] = thr
    report["probe"] = final
    return report


def save_classifier(path: Path, report: dict, embed_model: str, fps: float, crop: str, expand: float,
                    size: int, k: int, m: int) -> dict:
    probe: LogisticProbe = report["probe"]
    data = {
        "type": "logistic_probe",
        "version": 1,
        "created": datetime.now().isoformat(timespec="seconds"),
        "embedding_model": embed_model,
        "input": {"crop": crop, "bbox_expand": expand, "size": size, "sample_fps": fps},
        "threshold": report["threshold"],
        "episode_rule": {"k": k, "m": m},
        "bias": probe.bias,
        "weights": [round(float(v), 6) for v in probe.weights],
        "training": {k2: v for k2, v in report.items() if k2 not in ("probe", "threshold")},
    }
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=1, ensure_ascii=False) + "\n", encoding="utf-8")
    return data


# --------------------------------------------------------------------------- runtime judge
def classifier_crop(path: Path | str) -> str:
    """The crop a saved classifier was trained on; the pipeline must feed it the same crop."""
    return json.loads(Path(path).read_text(encoding="utf-8")).get("input", {}).get("crop", "animal")


class ProbeBackend:
    """Drop-in judge for the pipeline (same interface as the VLM backends): vlm.backend = "probe"."""

    def __init__(self, classifier_path: Path | str, embedder: Embedder | None = None):
        data = json.loads(Path(classifier_path).read_text(encoding="utf-8"))
        self.threshold = float(data["threshold"])
        self.k = int(data.get("episode_rule", {}).get("k", 2))
        self.probe = LogisticProbe(np.array(data["weights"], dtype=np.float32), float(data["bias"]))
        self.embedder = embedder or CLIPEmbedder(data["embedding_model"])

    def infer(self, request: VLMRequest) -> VLMResult:
        """One frame: p >= threshold. Several frames: at least k of them (k from training, capped at n)."""
        t0 = time.perf_counter()
        ps = self.probe.proba(self.embedder.embed(list(request.probe_images or request.images)))
        hits = int((ps >= self.threshold).sum())
        need = min(self.k, len(ps)) if len(ps) > 1 else 1
        decision = "suspect" if hits >= need else "normal"
        raw = "p=" + ",".join(f"{p:.3f}" for p in ps)
        return VLMResult(decision, raw, (time.perf_counter() - t0) * 1000, f"probe {hits}/{len(ps)} frames >= {self.threshold:.2f}",
                         source="probe")

    def close(self) -> None:
        pass
