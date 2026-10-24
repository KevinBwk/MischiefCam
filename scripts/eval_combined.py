"""Score VLM, CLIP probe and VLM-OR-probe per view on human labels (20 random clip-grouped 5-fold splits).

Needs the VLM batch summaries in outputs/eval_<view><suffix> and cached embeddings (scripts/exp_embed.py or eval_probe.py).

    uv run python scripts/eval_combined.py _ct _ct2 _ct3 --crop contact --fpr 0.04   # VLM numbers = mean of the runs
    uv run python scripts/eval_combined.py _az _az2 _az3 --crop contact --fpr 0.05 --zone couch

--zone couch applies the auto protected zone to the classifier as the pipeline does: a sampled frame
can only count toward an alert if the dog's expanded box overlaps the locked couch zone (grow-only,
built from the clip's sampled frames so far, as core.roi.merge_zone_boxes) by >= 10% (the threshold
is still picked on all frames, as mcam-train does). The VLM batches must have been run
with --rois config/rois.auto.json for the same setting.
"""
import argparse, json, random, numpy as np, collections
from core import labels as L
from core.config import resolve
from core.probe import (DEFAULT_EMBED_MODEL, SAMPLER_VERSION, LogisticProbe, build_dataset, clip_alert, pick_threshold,
                        random_group_folds)
class CacheOnly:
    model_id = DEFAULT_EMBED_MODEL
    def embed(self, images): raise RuntimeError("cache miss")
ap = argparse.ArgumentParser()
ap.add_argument("suffixes", nargs="*", default=[""], help='VLM batch suffixes, e.g. "_ct _ct2 _ct3" (results averaged)')
ap.add_argument("--crop", default="animal", help="classifier crop the embeddings were cached with")
ap.add_argument("--fpr", type=float, default=0.02, help="classifier frame FP budget for the threshold")
ap.add_argument("--zone", choices=["couch"], help="apply the auto protected zone (detected couch) to the classifier")
args = ap.parse_args()
SETS = [("close", "data/Videos", "data/labels_videos.json", "eval_close"),
        ("medium", "data/Medium-Videos", "data/labels_medium.json", "eval_medium"),
        ("wide", "data/Wide-Videos", "data/labels_wide.json", "eval_wide"),
        ("hardneg", "data/HardNeg-Videos", "data/labels_hardneg.json", "eval_hardneg"),
        ("pairs", "data/Pairs-Videos", "data/labels_pairs.json", "eval_pairs")]
clips, view, truth = [], {}, {}
vlm_runs = [{} for _ in args.suffixes]
for v, folder, lab, batch in SETS:
    d = L.load(resolve(lab))
    for k, e in d["clips"].items():
        truth[f"{folder}/{k}"] = L.clip_label(e)
    for vr, suf in zip(vlm_runs, args.suffixes):
        for r in json.load(open(resolve(f"outputs/{batch}{suf}/batch_summary.json"))):
            vr[f"{folder}/{r['clip']}"] = r["alert"]
    for c in build_dataset(resolve(folder), d, CacheOnly(), lambda p, f: 1 / 0, 2.0, resolve("outputs/cache/embeddings"),
                           crop=f"{args.crop}-{SAMPLER_VERSION}", log=lambda *_: None):
        c.clip = f"{folder}/{c.clip}"; clips.append(c); view[c.clip] = v
gate = {}  # (clip, t) -> dog in the couch zone
if args.zone:
    import cv2
    from core.probe import _area, _inter, pick_dog_and_couch
    from core.roi import merge_zone_boxes
    cache = resolve("outputs/cache/zone_gate_couch_locked.json")
    known = json.loads(cache.read_text()) if cache.exists() else {}
    det = None
    for c in clips:
        need = [t for t in c.times if f"{c.clip}|{t:.3f}" not in known]
        if need:
            if det is None:
                from core.detector import UltralyticsDetector
                det = UltralyticsDetector(str(resolve("models/yolov8m.pt")), "mps", ["dog", "couch"])
            cap = cv2.VideoCapture(str(resolve(c.clip)))
            zone = []  # locked, grow-only couch zone for this clip, in time order
            for t in sorted(c.times):
                cap.set(cv2.CAP_PROP_POS_MSEC, float(t) * 1000); ok, fr = cap.read()
                passed = False
                if ok:
                    dets = det.detect_once(fr)
                    zone = merge_zone_boxes(zone, [(d.bbox, d.score) for d in dets if d.class_name == "couch"])
                    dog, _ = pick_dog_and_couch(dets)
                    if dog is not None:
                        dx, dy = (dog[2] - dog[0]) * 0.15, (dog[3] - dog[1]) * 0.15
                        g = (dog[0] - dx, dog[1] - dy, dog[2] + dx, dog[3] + dy)
                        passed = max((_inter(g, z) for z in zone), default=0) / max(_area(g), 1e-6) >= 0.10
                known[f"{c.clip}|{t:.3f}"] = passed
            cap.release()
    cache.parent.mkdir(parents=True, exist_ok=True); cache.write_text(json.dumps(known))
    gate = {c.clip: np.array([known[f"{c.clip}|{t:.3f}"] for t in c.times]) for c in clips}
    n = sum(len(g) for g in gate.values()); print(f"zone gate: {sum(int(g.sum()) for g in gate.values())}/{n} sampled frames in the couch zone")
vlm = vlm_runs[0]
assert all(set(truth) <= set(vr) for vr in vlm_runs), [set(truth) - set(vr) for vr in vlm_runs]

def probe_alerts(seed):
    folds = random_group_folds([c.clip for c in clips], {c.clip: c.label for c in clips}, 5, random.Random(seed))
    oof = {}
    for fs in folds:
        tr = [c for c in clips if c.clip not in fs]
        p = LogisticProbe.fit(np.vstack([c.X for c in tr]), np.concatenate([c.frame_labels for c in tr]))
        for c in clips:
            if c.clip in fs: oof[c.clip] = p.proba(c.X)
    P = np.concatenate([oof[c.clip] for c in clips]); Y = np.concatenate([c.frame_labels for c in clips])
    thr = pick_threshold(P, Y, args.fpr)
    if gate:  # frames outside the protected zone are never judged
        oof = {k: np.where(gate[k], v, 0.0) for k, v in oof.items()}
    return {c.clip: clip_alert(oof[c.clip], thr) for c in clips}

runs = [probe_alerts(s) for s in range(20)]
def score(alerts, keys):
    tp = sum(truth[k] == "positive" and alerts.get(k, False) for k in keys)
    fp = sum(truth[k] == "negative" and alerts.get(k, False) for k in keys)
    return tp, fp
print(f"classifier crop={args.crop} fpr={args.fpr} zone={args.zone or 'whole frame'}; VLM runs: {args.suffixes} (mean)")
print(f"{'view':7s} {'pos/neg':8s} | {'VLM':>15s} | {'classifier (mean of 20)':>24s} | {'VLM OR classifier':>20s}")
for v in ("close", "medium", "wide", "hardneg", "pairs", "all"):
    keys = [k for k in truth if v == "all" or view.get(k) == v or (k not in view and k.split('/')[1] == {'close':'Videos','medium':'Medium-Videos','wide':'Wide-Videos','hardneg':'HardNeg-Videos','pairs':'Pairs-Videos'}.get(v))]
    npos = sum(truth[k] == "positive" for k in keys); nneg = sum(truth[k] == "negative" for k in keys)
    m = lambda xs, i: np.mean([x[i] for x in xs])
    vs = [score(vr, keys) for vr in vlm_runs]; vt, vf = m(vs, 0), m(vs, 1)
    pr = [score(r, keys) for r in runs]
    un = [score({k: vr[k] or r.get(k, False) for k in keys}, keys) for vr in vlm_runs for r in runs]
    print(f"{v:7s} {npos:>3d}/{nneg:<4d} | TP {vt:4.1f} FP {vf:4.1f} | TP {m(pr,0):4.1f} FP {m(pr,1):3.1f} (TP range {min(x[0] for x in pr)}-{max(x[0] for x in pr)}) | TP {m(un,0):4.1f} FP {m(un,1):3.1f}")
vlm_tp = sorted(k for k in truth if truth[k] == "positive" and vlm[k]); print("\nVLM true positives:", [k.split('/')[-1] for k in vlm_tp])
freq = collections.Counter(k for r in runs for k in truth if truth[k] == "positive" and not r.get(k) and not vlm[k])
print("missed by both in most splits:", [k.split('/')[-1] for k, n in freq.items() if n >= 15])
fps = collections.Counter(k for r in runs for k in truth if truth[k] == "negative" and (r.get(k) or vlm[k]))
print("false alerts (count over 20 splits):", {k.split('/')[-1]: n for k, n in fps.most_common()})
