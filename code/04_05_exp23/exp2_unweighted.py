"""Post-hoc addition to Experiment 2 (not in the original spec): the same tree WITHOUT class weighting, on 2018,
so both tree variants exist for all three datasets. Same feature, splits and metrics as exp2_run.py."""
import sys, time
from sklearn.tree import DecisionTreeClassifier
from common23 import *
meta = pool_meta()
y, t, leaked = meta["y"], meta["t"].reshape(-1, 1), meta["leaked"]
for split in ("temporal", "random"):
    out = f"{RES}/exp2/{split}_tree_unweighted.json"
    tr, te = split_indices(split, meta)
    clf = DecisionTreeClassifier(max_depth=20, min_samples_leaf=10, random_state=0)
    t0 = time.time(); clf.fit(t[tr], y[tr]); p = clf.predict(t[te])
    res = {"experiment": "2 (post-hoc addition)", "split": split, "model": "tree_unweighted", "params": clf.get_params(),
           "n_train": int(len(tr)), "n_test": int(len(te)), "fit_seconds": round(time.time() - t0, 2),
           "all": metrics(y[te], p), "leaked_rows": metrics(y[te], p, leaked[te])}
    write_new(out, res)
    print(f"{split}: acc={res['all']['accuracy']:.4f} | leaked acc={res['leaked_rows']['accuracy']:.4f} mF1={res['leaked_rows']['macro_f1']:.4f}")
