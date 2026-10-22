import json
import threading
import urllib.error
import urllib.request

import numpy as np
import pytest

from core import labels as L
from core.label_tool import LabelState, make_server
from core.probe import (ClipFrames, LogisticProbe, ProbeBackend, build_dataset, clip_alert, group_folds,
                        pick_threshold, save_classifier, train_and_evaluate)
from core.types import VLMRequest


# ---------------------------------------------------------------- labels
def test_clip_label_priority():
    seg = lambda lab: {"start_s": 0, "end_s": 1, "label": lab}
    assert L.clip_label({"segments": [seg("negative"), seg("positive")]}) == "positive"
    assert L.clip_label({"segments": [seg("uncertain"), seg("negative")]}) == "negative"
    assert L.clip_label({"segments": []}) is None


def test_label_at_open_ended_segment():
    e = {"segments": [{"start_s": 2.0, "end_s": -1, "label": "positive"}]}
    assert L.label_at(e, 1.0, 8.0) is None and L.label_at(e, 7.5, 8.0) == "positive"


def test_validate_rejects_bad_segment():
    with pytest.raises(ValueError):
        L.validate_clip({"segments": [{"start_s": 3, "end_s": 1, "label": "positive"}]})
    with pytest.raises(ValueError):
        L.validate_clip({"segments": [{"start_s": 0, "end_s": 1, "label": "maybe"}]})


def test_legacy_map_is_converted(tmp_path):
    p = tmp_path / "labels.json"
    p.write_text(json.dumps({"a.mp4": "negative"}))
    assert L.clip_label(L.load(p)["clips"]["a.mp4"]) == "negative"


# ---------------------------------------------------------------- labeling server
@pytest.fixture
def label_server(tmp_path):
    folder = tmp_path / "raw"
    (folder / "sub").mkdir(parents=True)
    (folder / "V001_pos_chewing_furniture.mp4").write_bytes(b"0123456789" * 100)
    (folder / "sub" / "clip_b.mp4").write_bytes(b"x" * 50)
    prompts = tmp_path / "prompts.json"
    prompts.write_text(json.dumps({"prompts": [{"id": "V001", "label": "positive", "behavior": "chewing_furniture",
                                                "target": "sofa armrest", "prompt": "..."}]}))
    state = LabelState(folder, tmp_path / "labels.json", prompts)
    srv = make_server(state, 0)
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    yield f"http://127.0.0.1:{srv.server_address[1]}", state
    srv.shutdown(); srv.server_close()


def test_listing_has_hint_from_prompt_id(label_server):
    base, _ = label_server
    clips = json.loads(urllib.request.urlopen(base + "/api/clips").read())["clips"]
    by = {c["path"]: c for c in clips}
    assert by["V001_pos_chewing_furniture.mp4"]["hint"]["label"] == "positive"
    assert "sub/clip_b.mp4" in by


def test_video_range_request(label_server):
    base, _ = label_server
    req = urllib.request.Request(base + "/video/0", headers={"Range": "bytes=10-19"})
    resp = urllib.request.urlopen(req)
    assert resp.status == 206 and resp.headers["Content-Range"] == "bytes 10-19/1000"
    assert resp.read() == b"0123456789"


def test_save_and_reload_segments(label_server):
    base, state = label_server
    body = {"segments": [{"start_s": 1, "end_s": 5, "label": "positive", "behavior": "chewing_furniture"}], "simulated": True}
    req = urllib.request.Request(base + "/api/clips/0", json.dumps(body).encode(), {"Content-Type": "application/json"})
    assert json.loads(urllib.request.urlopen(req).read())["label"] == "positive"
    saved = json.loads(state.labels_path.read_text())
    assert saved["clips"]["V001_pos_chewing_furniture.mp4"]["simulated"] is True


def test_invalid_segment_is_422(label_server):
    base, _ = label_server
    body = {"segments": [{"start_s": 5, "end_s": 1, "label": "positive"}]}
    req = urllib.request.Request(base + "/api/clips/0", json.dumps(body).encode(), {"Content-Type": "application/json"})
    with pytest.raises(urllib.error.HTTPError) as err:
        urllib.request.urlopen(req)
    assert err.value.code == 422


# ---------------------------------------------------------------- probe
def _synthetic_clips(n_pos=6, n_neg=8, frames=8, d=16, seed=0):
    rng = np.random.default_rng(seed)
    clips = []
    for i in range(n_pos + n_neg):
        lab = 1 if i < n_pos else 0
        center = np.ones(d) if lab else -np.ones(d)
        X = center * 0.5 + rng.normal(0, 0.6, (frames, d))
        X /= np.linalg.norm(X, axis=1, keepdims=True)
        clips.append(ClipFrames(f"c{i}", lab, np.arange(frames) * 0.5, np.full(frames, lab), X.astype(np.float32)))
    return clips


def test_probe_learns_separable_data():
    clips = _synthetic_clips()
    X = np.vstack([c.X for c in clips]); y = np.concatenate([c.frame_labels for c in clips])
    p = LogisticProbe.fit(X, y).proba(X)
    assert ((p >= 0.5) == y).mean() > 0.95


def test_group_folds_keep_clips_whole_and_mixed():
    labels = {f"p{i}": 1 for i in range(4)} | {f"n{i}": 0 for i in range(6)}
    folds = group_folds(list(labels), labels, 3)
    assert sorted(c for f in folds for c in f) == sorted(labels)
    assert all(any(labels[c] for c in f) and any(not labels[c] for c in f) for f in folds)


def test_clip_alert_rule():
    assert clip_alert([0.1, 0.9, 0.2, 0.8], 0.5, k=2, m=4) is True
    assert clip_alert([0.9, 0.1, 0.1, 0.1, 0.1, 0.9], 0.5, k=2, m=4) is False


def test_pick_threshold_limits_false_positives():
    probs = np.array([0.1, 0.2, 0.3, 0.9, 0.95]); y = np.array([0, 0, 0, 1, 1])
    thr = pick_threshold(probs, y, max_fp_rate=0.0)
    assert (probs[y == 0] >= thr).sum() == 0 and (probs[y == 1] >= thr).all()


def test_train_and_evaluate_reports_grouped_cv(tmp_path):
    report = train_and_evaluate(_synthetic_clips(), folds=3)
    cv = report["cross_validation"]
    assert cv["clip_level"]["TP"] + cv["clip_level"]["FN"] == 6
    assert cv["clip_level"]["TP"] >= 5 and cv["clip_level"]["FP"] <= 1
    data = save_classifier(tmp_path / "clf.json", report, "fake", 2.0, "animal", 0.15, 336, 2, 4)
    assert len(data["weights"]) == 16


def test_too_little_data_trains_without_claiming_accuracy():
    report = train_and_evaluate(_synthetic_clips(n_pos=1, n_neg=1))
    assert report["cross_validation"] is None and "warning" in report


def test_probe_backend_is_a_judge(tmp_path):
    class Emb:
        model_id = "fake"
        def embed(self, images):
            return np.ones((len(images), 16), dtype=np.float32) / 4.0
    report = train_and_evaluate(_synthetic_clips(), folds=3)
    save_classifier(tmp_path / "clf.json", report, "fake", 2.0, "animal", 0.15, 336, 2, 4)
    r = ProbeBackend(tmp_path / "clf.json", embedder=Emb()).infer(VLMRequest(images=(object(),), prompt=""))
    assert r.decision == "suspect" and r.raw_text.startswith("p=")


def test_build_dataset_uses_segments_and_cache(tmp_path):
    folder = tmp_path / "raw"; folder.mkdir()
    for n in ("pos.mp4", "neg.mp4"):
        (folder / n).write_bytes(b"v")
    labels = {"clips": {"pos.mp4": {"segments": [{"start_s": 1.0, "end_s": 3.0, "label": "positive"}]},
                        "neg.mp4": {"segments": [{"start_s": 0.0, "end_s": -1, "label": "negative"}]}}}
    calls = {"n": 0}
    def sampler(path, fps):
        calls["n"] += 1
        return [(t, "img") for t in (0.25, 1.25, 2.25, 3.25)]
    class Emb:
        model_id = "fake"
        def embed(self, images):
            return np.ones((len(images), 4), dtype=np.float32)
    clips = build_dataset(folder, labels, Emb(), sampler, 2.0, tmp_path / "cache", log=lambda *_: None)
    by = {c.clip: c for c in clips}
    assert len(by["pos.mp4"].X) == 2  # only frames inside 1.0–3.0 s are used
    assert len(by["neg.mp4"].X) == 4
    build_dataset(folder, labels, Emb(), sampler, 2.0, tmp_path / "cache", log=lambda *_: None)
    assert calls["n"] == 2  # second run hits the embedding cache


# ---------------------------------------------------------------- AI suggestions
def test_suggestions_only_when_requested(tmp_path):
    folder = tmp_path / "raw"; folder.mkdir()
    (folder / "v1.mp4").write_bytes(b"x")
    sug = tmp_path / "ai.json"
    sug.write_text(json.dumps({"clips": {"v1.mp4": {"segments": [{"start_s": 0, "end_s": -1, "label": "negative"}]}}}))
    blind = LabelState(folder, tmp_path / "labels.json", tmp_path / "none.json")
    assert blind.listing()[0]["suggestion"] is None
    helped = LabelState(folder, tmp_path / "labels.json", tmp_path / "none.json", sug)
    assert helped.listing()[0]["suggestion"][0]["label"] == "negative"


def test_ai_assisted_flag_is_saved(tmp_path):
    folder = tmp_path / "raw"; folder.mkdir()
    (folder / "v1.mp4").write_bytes(b"x")
    state = LabelState(folder, tmp_path / "labels.json", tmp_path / "none.json")
    state.save_clip(0, {"segments": [{"start_s": 0, "end_s": -1, "label": "positive"}], "ai_assisted": True})
    saved = json.loads((tmp_path / "labels.json").read_text())["clips"]["v1.mp4"]
    assert saved["ai_assisted"] is True and state.listing()[0]["ai_assisted"] is True


# ---------------------------------------------------------------- dog selection
def test_pick_dog_prefers_dog_at_couch_over_bigger_dog():
    from core.probe import pick_dog
    from core.types import Detection
    big_far = Detection((800, 400, 1200, 700), 0.9, "dog")       # big dog lying in a bed, away from the sofa
    small_at_sofa = Detection((100, 300, 250, 420), 0.8, "dog")  # smaller dog chewing the sofa
    couch = Detection((0, 200, 400, 450), 0.9, "couch")
    assert pick_dog([big_far, small_at_sofa, couch]) == small_at_sofa.bbox


def test_pick_dog_falls_back_to_largest_without_couch():
    from core.probe import pick_dog
    from core.types import Detection
    a, b = Detection((0, 0, 10, 10), 0.9, "dog"), Detection((0, 0, 50, 50), 0.9, "dog")
    assert pick_dog([a, b]) == b.bbox and pick_dog([]) is None


def test_probe_backend_k_of_n(tmp_path):
    import numpy as np
    from core.probe import ProbeBackend
    clf = tmp_path / "clf.json"
    clf.write_text(json.dumps({"threshold": 0.5, "episode_rule": {"k": 2, "m": 4}, "bias": 0.0,
                               "weights": [1.0], "embedding_model": "fake"}))
    class Emb:
        model_id = "fake"
        def __init__(self, vals): self.vals = vals
        def embed(self, images): return np.array([[v] for v in self.vals[:len(images)]], dtype=np.float32)
    one_hit = ProbeBackend(clf, embedder=Emb([5, -5, -5, -5])).infer(VLMRequest(images=(1, 2, 3, 4), prompt=""))
    two_hits = ProbeBackend(clf, embedder=Emb([5, -5, 5, -5])).infer(VLMRequest(images=(1, 2, 3, 4), prompt=""))
    single = ProbeBackend(clf, embedder=Emb([5])).infer(VLMRequest(images=(1,), prompt=""))
    assert one_hit.decision == "normal" and two_hits.decision == "suspect" and single.decision == "suspect"


def test_build_dataset_refuses_held_out_test_set(tmp_path):
    import pytest

    from core.probe import build_dataset

    with pytest.raises(ValueError, match="held-out test set"):
        build_dataset(tmp_path / "Test-Videos", {"clips": {}}, None, None, 2.0, None)
