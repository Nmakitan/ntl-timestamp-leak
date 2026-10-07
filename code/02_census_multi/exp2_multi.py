"""Experiment 2 (timestamp-only baseline) on other NTLFlowLyzer datasets.
Usage: exp2_multi.py <dataset_dir> <out_dir> <class_mode: label|activity>
Feature t = smallest leaked IAT value in the row (IAT > 1e9), 0 if none.
Splits: random = stratified 75/25 by class, random_state=0;
        temporal = within each (file, class), the latest 25% by `timestamp` is test (as the 2018 pipeline did per day file).
Models: DummyClassifier most_frequent / stratified(random_state=0), DecisionTree(max_depth=20, min_samples_leaf=10,
class_weight="balanced", random_state=0). Metrics on all test rows and on leaked test rows.
"""
import glob, json, os, sys, time
import numpy as np, pandas as pd
from sklearn.dummy import DummyClassifier
from sklearn.metrics import accuracy_score, f1_score, precision_recall_fscore_support, confusion_matrix
from sklearn.model_selection import train_test_split
from sklearn.tree import DecisionTreeClassifier

SRC, OUT, MODE = sys.argv[1], sys.argv[2], sys.argv[3]
os.makedirs(OUT, exist_ok=True)
LEAK = 1e9

# ---- load t, class, timestamp, file -------------------------------------------------------
frames = []
for f in sorted(glob.glob(f"{SRC}/**/*.csv", recursive=True)):
    if os.path.getsize(f) == 0:
        continue
    hdr = list(pd.read_csv(f, nrows=0).columns)
    iat = [c for c in hdr if "IAT" in c]
    cls_cols = ["label"] + (["activity"] if MODE == "activity" else [])
    for ch in pd.read_csv(f, usecols=iat + cls_cols + ["timestamp"], chunksize=200_000):
        I = ch[iat].apply(pd.to_numeric, errors="coerce").to_numpy(dtype=np.float64)
        m = I > LEAK
        t = np.where(m.any(1), np.where(m, I, np.inf).min(1), 0.0)
        cls = ch["label"].astype(str) if MODE == "label" else ch["label"].astype(str) + " / " + ch["activity"].astype(str)
        frames.append(pd.DataFrame({"t": t, "leaked": m.any(1), "cls": cls.to_numpy(), "file": os.path.basename(f),
                                    "ts": pd.to_datetime(ch["timestamp"], format="ISO8601", errors="coerce").to_numpy()}))
D = pd.concat(frames, ignore_index=True)
classes = sorted(D.cls.unique()); L = list(range(len(classes)))
y = D.cls.map({c: i for i, c in enumerate(classes)}).to_numpy()
X = D[["t"]].to_numpy()
leaked = D.leaked.to_numpy()
print(f"{len(D)} rows, {len(classes)} classes, leaked {leaked.sum()} ({100 * leaked.mean():.2f}%)", flush=True)

# ---- splits --------------------------------------------------------------------------------
idx = np.arange(len(D))
r_tr, r_te = train_test_split(idx, test_size=0.25, stratify=y, random_state=0)
te_mask = np.zeros(len(D), bool)
for _, g in D.groupby(["file", "cls"]):
    order = g.sort_values("ts", kind="mergesort").index.to_numpy()
    te_mask[order[int(round(len(order) * 0.75)):]] = True
splits = {"random": (np.sort(r_tr), np.sort(r_te)), "temporal": (idx[~te_mask], idx[te_mask])}
np.savez(f"{OUT}/splits.npz", random_train=splits["random"][0], random_test=splits["random"][1],
         temporal_train=splits["temporal"][0], temporal_test=splits["temporal"][1])


def metrics(yt, p, mask=None):
    if mask is not None:
        yt, p = yt[mask], p[mask]
    if len(yt) == 0:
        return {"n": 0}
    pr, rc, f1, sup = precision_recall_fscore_support(yt, p, labels=L, zero_division=0)
    return {"n": int(len(yt)), "accuracy": float(accuracy_score(yt, p)),
            "macro_f1": float(f1_score(yt, p, labels=L, average="macro", zero_division=0)),
            "per_class": {c: {"precision": float(pr[i]), "recall": float(rc[i]), "support": int(sup[i])} for i, c in enumerate(classes)},
            "confusion": confusion_matrix(yt, p, labels=L).tolist()}


rows = []
for split, (tr, te) in splits.items():
    for name, clf in [("most_frequent", DummyClassifier(strategy="most_frequent")),
                      ("stratified", DummyClassifier(strategy="stratified", random_state=0)),
                      ("tree", DecisionTreeClassifier(max_depth=20, min_samples_leaf=10, class_weight="balanced", random_state=0)),
                      # extra, not in the 2018 spec: same tree without class weighting (shows the gain in plain accuracy)
                      ("tree_unweighted", DecisionTreeClassifier(max_depth=20, min_samples_leaf=10, random_state=0))]:
        out = f"{OUT}/{split}_{name}.json"
        if os.path.exists(out) and name != "tree_unweighted":
            res = json.load(open(out)); a, l = res["all"], res["leaked_rows"]
            rows.append((split, name, a["accuracy"], a["macro_f1"], l.get("accuracy", np.nan), l.get("macro_f1", np.nan), a["n"], l["n"]))
            continue
        t0 = time.time(); clf.fit(X[tr], y[tr]); p = clf.predict(X[te])
        res = {"dataset": os.path.basename(SRC.rstrip("/")), "class_mode": MODE, "split": split, "model": name,
               "n_train": int(len(tr)), "n_test": int(len(te)), "seconds": round(time.time() - t0, 2),
               "all": metrics(y[te], p), "leaked_rows": metrics(y[te], p, leaked[te])}
        json.dump(res, open(out, "w"), indent=1)
        a, l = res["all"], res["leaked_rows"]
        rows.append((split, name, a["accuracy"], a["macro_f1"], l.get("accuracy", np.nan), l.get("macro_f1", np.nan), a["n"], l["n"]))
        print(f"{split:8s} {name:13s} acc={a['accuracy']:.4f} mF1={a['macro_f1']:.4f} | leaked acc={l.get('accuracy', np.nan):.4f} "
              f"mF1={l.get('macro_f1', np.nan):.4f} (n={l['n']})", flush=True)
json.dump({"rows": rows, "classes": classes, "n": int(len(D)), "leaked": int(leaked.sum())}, open(f"{OUT}/summary.json", "w"))
