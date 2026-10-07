"""Experiment 2: timestamp-only baseline.
Usage: exp2_run.py prep                 -> pool metadata + random split indices (exp3/random_split_idx.npz)
       exp2_run.py <split> <model>      -> one run; split in {temporal, random}, model in {most_frequent, stratified, tree}
Feature: t = smallest leaked IAT value in the row (original data), 0 if no leaked cell.
"""
import os, sys, time
import numpy as np
from sklearn.dummy import DummyClassifier
from sklearn.model_selection import train_test_split
from sklearn.tree import DecisionTreeClassifier
from common23 import *

if sys.argv[1] == "prep":
    meta = pool_meta()
    if not os.path.exists(SPLIT_IDX):
        idx = np.arange(len(meta["y"]))
        tr, te = train_test_split(idx, test_size=0.25, stratify=meta["y"], random_state=0)
        os.makedirs(os.path.dirname(SPLIT_IDX), exist_ok=True)
        np.savez(SPLIT_IDX + ".tmp.npz", train_idx=np.sort(tr), test_idx=np.sort(te),
                 note="pooled index: [0,ntr)=original train, [ntr,ntr+nte)=original test; "
                      "train_test_split(test_size=0.25, stratify=label, random_state=0); indices sorted")
        os.replace(SPLIT_IDX + ".tmp.npz", SPLIT_IDX)
    s = np.load(SPLIT_IDX)
    print(f"pool {len(meta['y'])} rows (train {int(meta['ntr'])}, test {int(meta['nte'])}), "
          f"leaked {int(meta['leaked'].sum())}; random split train {len(s['train_idx'])} test {len(s['test_idx'])}")
    sys.exit(0)

split, model = sys.argv[1], sys.argv[2]
out = f"{RES}/exp2/{split}_{model}.json"
if os.path.exists(out):
    sys.exit(f"exists: {out}")
meta = pool_meta()
tr, te = split_indices(split, meta)
y, t, leaked = meta["y"], meta["t"].reshape(-1, 1), meta["leaked"]
clf = {"most_frequent": DummyClassifier(strategy="most_frequent"),
       "stratified": DummyClassifier(strategy="stratified", random_state=0),
       "tree": DecisionTreeClassifier(max_depth=20, min_samples_leaf=10, class_weight="balanced", random_state=0)}[model]
t0 = time.time()
clf.fit(t[tr], y[tr])
fit_s = time.time() - t0
p = clf.predict(t[te])
res = {"experiment": 2, "split": split, "model": model, "params": clf.get_params(), "feature": "t (smallest leaked IAT, 0 if none)",
       "n_train": int(len(tr)), "n_test": int(len(te)), "fit_seconds": round(fit_s, 2),
       "all": metrics(y[te], p), "leaked_rows": metrics(y[te], p, leaked[te]),
       "worker_peak_rss_gb": peak_rss_gb()}
if model == "tree":
    res["tree_depth"], res["tree_leaves"] = int(clf.get_depth()), int(clf.get_n_leaves())
write_new(out, res)
print(f"{split} {model}: acc={res['all']['accuracy']:.4f} mF1={res['all']['macro_f1']:.4f} | "
      f"leaked acc={res['leaked_rows']['accuracy']:.4f} mF1={res['leaked_rows']['macro_f1']:.4f}")
