"""Single-seed 2x2 retrain (leaky / fixA x random / temporal) on BCCC-CIC-IDS-2017.
Usage: exp3_2017.py build                     -> cache X (float32), y, leaked, packets_count in exp3/cache/
       exp3_2017.py <random|temporal> <leaky|fixA|fixB> [seed]
Features: every numeric column except identity / time / label (flow_id, src_ip, src_port, dst_ip, dst_port, timestamp,
protocol, label), inf -> NaN -> 0, float32 (as the 2018 pipeline's clean_features). Splits: exp2_label/splits.npz
(same row order as exp2_multi.py: files in sorted path order, rows in file order). Model: the 2018 configuration.
"""
import gc, glob, json, os, sys, time, resource
import numpy as np, pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score, f1_score, precision_recall_fscore_support, confusion_matrix

SRC = "/home/USER/Downloads/BCCC-CIC-IDS-2017"
BASE = "/home/USER/Desktop/ntl_census_multi/BCCC-CIC-IDS-2017"
C, OUT = f"{BASE}/exp3/cache", f"{BASE}/exp3"
DROP = ["flow_id", "src_ip", "src_port", "dst_ip", "dst_port", "timestamp", "protocol", "label"]

if sys.argv[1] == "build":
    os.makedirs(C, exist_ok=True)
    files = [f for f in sorted(glob.glob(f"{SRC}/**/*.csv", recursive=True)) if os.path.getsize(f) > 0]
    hdr = list(pd.read_csv(files[0], nrows=0).columns)
    feat = [c for c in hdr if c not in DROP]
    n = sum(sum(1 for _ in open(f, "rb")) - 1 for f in files)
    X = np.lib.format.open_memmap(f"{C}/X.npy.part", mode="w+", dtype=np.float32, shape=(n, len(feat)))
    labels, off = [], 0
    for f in files:
        assert list(pd.read_csv(f, nrows=0).columns) == hdr
        for ch in pd.read_csv(f, chunksize=200_000, low_memory=False):
            F = ch[feat].apply(pd.to_numeric, errors="coerce").replace([np.inf, -np.inf], np.nan).fillna(0)
            X[off:off + len(ch)] = F.to_numpy(dtype=np.float32); labels += ch["label"].astype(str).tolist(); off += len(ch)
    assert off == n
    X.flush(); del X; os.replace(f"{C}/X.npy.part", f"{C}/X.npy")
    classes = sorted(set(labels)); y = np.array([classes.index(l) for l in labels])
    X = np.load(f"{C}/X.npy", mmap_mode="r")
    iat = [i for i, c in enumerate(feat) if "IAT" in c]
    leaked = np.zeros(n, bool)
    for i in range(0, n, 500_000):
        leaked[i:i + 500_000] = (np.asarray(X[i:i + 500_000][:, iat], dtype=np.float64) > 1e9).any(1)
    pc = np.asarray(X[:, feat.index("packets_count")])
    np.savez(f"{C}/meta.npz", y=y, leaked=leaked, pc=pc)
    json.dump({"features": feat, "classes": classes, "iat": iat}, open(f"{C}/meta.json", "w"))
    print(f"built X {n} x {len(feat)}, leaked {leaked.sum()} ({100 * leaked.mean():.2f}%), classes {classes}")
    sys.exit(0)

split, variant = sys.argv[1], sys.argv[2]
seed = int(sys.argv[3]) if len(sys.argv) > 3 else 0
out = f"{OUT}/{split}_{variant}_s{seed}.json"
if os.path.exists(out):
    sys.exit(f"exists: {out}")
M = json.load(open(f"{C}/meta.json")); meta = np.load(f"{C}/meta.npz")
y, leaked, pc = meta["y"], meta["leaked"], meta["pc"]
classes, iat, feat = M["classes"], np.array(M["iat"]), M["features"]
L = list(range(len(classes)))
sp = np.load(f"{BASE}/exp2_label/splits.npz")
tr, te = sp[f"{split}_train"], sp[f"{split}_test"]
X = np.load(f"{C}/X.npy", mmap_mode="r")


def take(idx, fix):
    Z = np.asarray(X[idx], dtype=np.float32)
    if fix:
        I = Z[:, iat]; I[I > 1e9] = 0.0; Z[:, iat] = I
    return Z


def metrics(yt, p, mask=None):
    if mask is not None:
        yt, p = yt[mask], p[mask]
    pr, rc, f1, sup = precision_recall_fscore_support(yt, p, labels=L, zero_division=0)
    return {"n": int(len(yt)), "accuracy": float(accuracy_score(yt, p)),
            "macro_f1": float(f1_score(yt, p, labels=L, average="macro", zero_division=0)),
            "per_class": {c: {"precision": float(pr[i]), "recall": float(rc[i]), "support": int(sup[i]),
                              "correct": int(((yt == i) & (p == i)).sum())} for i, c in enumerate(classes)},
            "confusion": confusion_matrix(yt, p, labels=L).tolist()}


fix = variant in ("fixA", "fixB")
dropped = {}
if variant == "fixB":  # fixA + drop rows with packets_count == 1 from train and test
    dropped = {"train": int((pc[tr] == 1).sum()), "test": int((pc[te] == 1).sum())}
    tr, te = tr[pc[tr] != 1], te[pc[te] != 1]
Xtr = take(tr, fix)
if fix:
    assert not (Xtr[:, iat] > 1e9).any()
rf = RandomForestClassifier(n_estimators=200, max_depth=30, min_samples_leaf=10, class_weight="balanced", n_jobs=2, random_state=seed)
t0 = time.time(); rf.fit(Xtr, y[tr]); fit_s = time.time() - t0
del Xtr; gc.collect()
big = [(est.tree_.feature[(est.tree_.feature >= 0) & (est.tree_.threshold > 1e9)]) for est in rf.estimators_]
thr_all = int(sum(len(b) for b in big)); thr_iat = int(sum(np.isin(b, iat).sum() for b in big))
p = np.concatenate([rf.predict(take(te[i:i + 100_000], fix)) for i in range(0, len(te), 100_000)])
yt, lt, multi = y[te], leaked[te], pc[te] != 1
res = {"dataset": "BCCC-CIC-IDS-2017", "split": split, "variant": variant, "seed": seed, "n_features": len(feat),
       "n_train": int(len(tr)), "n_test": int(len(te)), "fixB_dropped_rows": dropped, "fit_seconds": round(fit_s, 1),
       "peak_rss_gb": resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / 1e6,
       "leak_check": {"thresholds_above_1e9": thr_all, "of_which_on_IAT_features": thr_iat,
                      "FLAG": bool(fix and thr_all > 0), "FLAG_IAT": bool(fix and thr_iat > 0)},
       "top15_importances": {feat[i]: float(v) for i, v in sorted(enumerate(rf.feature_importances_), key=lambda kv: -kv[1])[:15]},
       "all": metrics(yt, p), "leaked_rows": metrics(yt, p, lt), "multi_packet_rows": metrics(yt, p, multi)}
np.save(out.replace(".json", ".pred.npy"), p)
json.dump(res, open(out + ".tmp", "w"), indent=1); os.replace(out + ".tmp", out)
print(f"{split} {variant} s{seed}: acc={res['all']['accuracy']:.4f} mF1={res['all']['macro_f1']:.4f} | leaked acc="
      f"{res['leaked_rows']['accuracy']:.4f} | multi-packet acc={res['multi_packet_rows']['accuracy']:.4f} | "
      f"thr>1e9 {thr_all} (IAT {thr_iat}) | fit {fit_s:.0f}s", flush=True)
