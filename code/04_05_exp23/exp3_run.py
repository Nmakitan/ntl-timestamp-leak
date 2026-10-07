"""Experiment 3: retrain the RF with and without the leak.
Usage: exp3_run.py <split: temporal|random> <variant: leaky|fixA|fixB> <seed>
leaky = data as is; fixA = leaked IAT cells set to 0 (train and test); fixB = fixA + rows with packets_count == 1 dropped.
"Leaked test rows" = this run's test rows that are leaked in the unmodified data.
No ONNX export; sklearn predicts directly. Writes <RES>/exp3/runs/<split>_<variant>_s<seed>.worker.json.
"""
import gc, os, sys, time
import numpy as np
from sklearn.ensemble import RandomForestClassifier
from common23 import *

split, variant, seed = sys.argv[1], sys.argv[2], int(sys.argv[3])
name = f"{split}_{variant}_s{seed}"
out = f"{RES}/exp3/runs/{name}.worker.json"
if os.path.exists(out) or os.path.exists(out.replace(".worker", "")):
    sys.exit(f"exists: {name}")
fix = variant in ("fixA", "fixB")
meta = pool_meta()
y, leaked, pc, ntr = meta["y"], meta["leaked"], meta["pc"], int(meta["ntr"])
tr, te = split_indices(split, meta)
dropped = {}
if variant == "fixB":
    dropped = {"train": int((pc[tr] == 1).sum()), "test": int((pc[te] == 1).sum())}
    tr, te = tr[pc[tr] != 1], te[pc[te] != 1]
print(f"{name}: train {len(tr)} test {len(te)} dropped {dropped}", flush=True)

t0 = time.time()
X = assemble(tr, ntr, fix)
ytr = y[tr]
if fix:
    assert not (X[:, IAT] > LEAK).any()
assemble_s = time.time() - t0
rf = RandomForestClassifier(n_estimators=200, max_depth=30, min_samples_leaf=10, class_weight="balanced",
                            n_jobs=2, random_state=seed)
t0 = time.time()
rf.fit(X, ytr)
fit_s = time.time() - t0
del X, ytr; gc.collect()
print(f"{name}: fit {fit_s:.0f}s, rss peak {peak_rss_gb():.2f}GB", flush=True)

# leak check: split thresholds above 1e9 anywhere in the forest
thr_all = thr_iat = n_splits = 0
iat_set = set(IAT.tolist())
for est in rf.estimators_:
    tt = est.tree_; internal = tt.feature >= 0
    big = internal & (tt.threshold > LEAK)
    n_splits += int(internal.sum()); thr_all += int(big.sum())
    thr_iat += int(sum(1 for f in tt.feature[big] if f in iat_set))
nodes = int(sum(e.tree_.node_count for e in rf.estimators_))
importances = {FEAT[i]: float(v) for i, v in sorted(enumerate(rf.feature_importances_), key=lambda kv: -kv[1])[:25]}

t0 = time.time()
pred = np.empty(len(te), dtype=np.int64)
for i in range(0, len(te), CHUNK):
    blk = assemble(te[i:i + CHUNK], ntr, fix)
    pred[i:i + len(blk)] = rf.predict(blk)
    del blk
pred_s = time.time() - t0
yte = y[te]
res = {"experiment": 3, "split": split, "variant": variant, "seed": seed,
       "params": {k: v for k, v in rf.get_params().items() if k != "estimator"},
       "n_train": int(len(tr)), "n_test": int(len(te)), "fixB_dropped_rows": dropped,
       "fixB_rule": "packets_count == 1 (column present in feature_order.json)" if variant == "fixB" else None,
       "assemble_seconds": round(assemble_s, 1), "fit_seconds": round(fit_s, 1), "predict_seconds": round(pred_s, 1),
       "worker_peak_rss_gb": peak_rss_gb(),
       "leak_check": {"thresholds_above_1e9": thr_all, "of_which_on_IAT_features": thr_iat,
                      "total_split_nodes": n_splits, "total_nodes": nodes,
                      "FLAG": bool(fix and thr_all > 0)},
       "top25_importances": importances,
       "all": metrics(yte, pred), "leaked_rows": metrics(yte, pred, leaked[te])}
os.makedirs(os.path.dirname(out), exist_ok=True)
np.save(f"{RES}/exp3/runs/{name}.pred.npy", pred)
write_new(out, res)
print(f"{name}: acc={res['all']['accuracy']:.4f} mF1={res['all']['macro_f1']:.4f} | leaked acc="
      f"{res['leaked_rows'].get('accuracy', float('nan')):.4f} | thresholds>1e9: {thr_all}", flush=True)
