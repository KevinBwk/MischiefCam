"""Score VLM, CLIP probe and VLM-OR-probe per view on human labels (20 random clip-grouped 5-fold splits).

Needs the VLM batch summaries in outputs/eval_<view><suffix> and cached embeddings (scripts/exp_embed.py or eval_probe.py).

    uv run python scripts/eval_combined.py _ct _ct2 _ct3 --crop contact --fpr 0.04   # VLM numbers = mean of the runs
"""
import argparse, json, random, numpy as np, collections
from core import labels as L
from core.config import resolve
from core.probe import DEFAULT_EMBED_MODEL, SAMPLER_VERSION, LogisticProbe, build_dataset, clip_alert, pick_threshold
class CacheOnly:
    model_id = DEFAULT_EMBED_MODEL
    def embed(self, images): raise RuntimeError("cache miss")
ap = argparse.ArgumentParser()
ap.add_argument("suffixes", nargs="*", default=[""], help='VLM batch suffixes, e.g. "_ct _ct2 _ct3" (results averaged)')
ap.add_argument("--crop", default="animal", help="classifier crop the embeddings were cached with")
ap.add_argument("--fpr", type=float, default=0.02, help="classifier frame FP budget for the threshold")
args = ap.parse_args()
SETS = [("close", "data/Videos", "data/labels_videos.json", "eval_close"),
        ("medium", "data/Medium-Videos", "data/labels_medium.json", "eval_medium"),
        ("wide", "data/Wide-Videos", "data/labels_wide.json", "eval_wide"),
        ("hardneg", "data/HardNeg-Videos", "data/labels_hardneg.json", "eval_hardneg")]
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
vlm = vlm_runs[0]
assert all(set(truth) <= set(vr) for vr in vlm_runs), [set(truth) - set(vr) for vr in vlm_runs]

def probe_alerts(seed):
    rng = random.Random(seed); pos = [c.clip for c in clips if c.label]; neg = [c.clip for c in clips if not c.label]
    rng.shuffle(pos); rng.shuffle(neg); folds = [set() for _ in range(5)]
    for i, c in enumerate(pos): folds[i % 5].add(c)
    for i, c in enumerate(neg): folds[(i + len(pos)) % 5].add(c)
    oof = {}
    for fs in folds:
        tr = [c for c in clips if c.clip not in fs]
        p = LogisticProbe.fit(np.vstack([c.X for c in tr]), np.concatenate([c.frame_labels for c in tr]))
        for c in clips:
            if c.clip in fs: oof[c.clip] = p.proba(c.X)
    P = np.concatenate([oof[c.clip] for c in clips]); Y = np.concatenate([c.frame_labels for c in clips])
    thr = pick_threshold(P, Y, args.fpr)
    return {c.clip: clip_alert(oof[c.clip], thr) for c in clips}

runs = [probe_alerts(s) for s in range(20)]
def score(alerts, keys):
    tp = sum(truth[k] == "positive" and alerts.get(k, False) for k in keys)
    fp = sum(truth[k] == "negative" and alerts.get(k, False) for k in keys)
    return tp, fp
print(f"classifier crop={args.crop} fpr={args.fpr}; VLM runs: {args.suffixes} (mean)")
print(f"{'view':7s} {'pos/neg':8s} | {'VLM':>15s} | {'classifier (mean of 20)':>24s} | {'VLM OR classifier':>20s}")
for v in ("close", "medium", "wide", "hardneg", "all"):
    keys = [k for k in truth if v == "all" or view.get(k) == v or (k not in view and k.split('/')[1] == {'close':'Videos','medium':'Medium-Videos','wide':'Wide-Videos','hardneg':'HardNeg-Videos'}.get(v))]
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
