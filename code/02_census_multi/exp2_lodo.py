"""Experiment 2 (timestamp-only baseline) on the leave-one-day-out splits of BCCC-CIC-IDS-2017, plus a binary
attack-vs-benign table of every timestamp-only result (random / temporal from the existing JSONs, nothing rerun).
Usage: exp2_lodo.py            -> BCCC-CIC-IDS-2017/exp2_lodo/

Feature, models and metrics as exp2_multi.py (t = smallest IAT value > 1e9 in the row, 0 if none, read in float64 from
the CSVs; balanced tree pre-specified, unweighted tree secondary; dummies as baselines). Splits: lodo/splits.npz
(mc_lodo_splits.py), same row order (CSVs in sorted path order, rows in file order) - checked against the cache labels.
Each held-out day's attack classes are absent from training, so the headline is binary: detect = attack rows predicted
as any attack class; FPR = benign rows predicted as any attack class (cPacket: Suspicious counted as neither).
"""
import glob, json, os, time
import numpy as np, pandas as pd
from sklearn.dummy import DummyClassifier
from sklearn.metrics import accuracy_score, f1_score, precision_recall_fscore_support, confusion_matrix
from sklearn.tree import DecisionTreeClassifier

HERE = os.path.dirname(os.path.abspath(__file__))
D17 = f"{HERE}/BCCC-CIC-IDS-2017"
SRC = "/home/USER/Downloads/BCCC-CIC-IDS-2017"
OUT = f"{D17}/exp2_lodo"
os.makedirs(OUT, exist_ok=True)
LEAK = 1e9

# ---- t and class per row, exactly as exp2_multi.py (label mode); cached -------------------
fc = f"{OUT}/t_cls.npz"
if os.path.exists(fc):
    z = np.load(fc, allow_pickle=False); t, leaked = z["t"], z["leaked"]; cls = z["classes"][z["y"]]
else:
    T, LK, C = [], [], []
    for f in sorted(glob.glob(f"{SRC}/**/*.csv", recursive=True)):
        if os.path.getsize(f) == 0:
            continue
        iat = [c for c in pd.read_csv(f, nrows=0).columns if "IAT" in c]
        for ch in pd.read_csv(f, usecols=iat + ["label"], chunksize=200_000):
            I = ch[iat].apply(pd.to_numeric, errors="coerce").to_numpy(dtype=np.float64)
            m = I > LEAK
            T.append(np.where(m.any(1), np.where(m, I, np.inf).min(1), 0.0)); LK.append(m.any(1))
            C.append(ch["label"].astype(str).to_numpy())
    t, leaked, cls = np.concatenate(T), np.concatenate(LK), np.concatenate(C).astype("U32")
    cn, yc = np.unique(cls, return_inverse=True)  # class codes, not strings (2.4M x U32 would be 330 MB)
    np.savez(fc, t=t, leaked=leaked, y=yc.astype(np.int8), classes=cn)
classes = sorted(set(cls)); L = list(range(len(classes)))
y = pd.Series(cls).map({c: i for i, c in enumerate(classes)}).to_numpy()
X = t.reshape(-1, 1)

# same rows as the cache the LODO splits were built on
cm = json.load(open(f"{D17}/exp3/cache/meta.json")); cz = np.load(f"{D17}/exp3/cache/meta.npz")
assert cm["classes"] == classes and np.array_equal(cz["y"], y) and np.array_equal(cz["leaked"], leaked), "row order differs"
print(f"{len(y)} rows, {len(classes)} classes, leaked {leaked.sum()} - matches the cache", flush=True)

att = np.array([c != "Benign" for c in classes])
S = np.load(f"{D17}/lodo/splits.npz")
FOLDS = sorted(k[:-6] for k in S if k.endswith("_train"))


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


def binary(yt, p):
    a, b = att[yt], ~att[yt]
    return {"n_attack": int(a.sum()), "n_benign": int(b.sum()),
            "detect": float(att[p][a].mean()) if a.any() else None, "fpr": float(att[p][b].mean()) if b.any() else None}


for fold in FOLDS:
    tr, te = S[f"{fold}_train"], S[f"{fold}_test"]
    for name, clf in [("most_frequent", DummyClassifier(strategy="most_frequent")),
                      ("stratified", DummyClassifier(strategy="stratified", random_state=0)),
                      ("tree", DecisionTreeClassifier(max_depth=20, min_samples_leaf=10, class_weight="balanced", random_state=0)),
                      ("tree_unweighted", DecisionTreeClassifier(max_depth=20, min_samples_leaf=10, random_state=0))]:
        out = f"{OUT}/{fold}_{name}.json"
        if os.path.exists(out):
            continue
        t0 = time.time(); clf.fit(X[tr], y[tr]); p = clf.predict(X[te])
        yt, lk = y[te], leaked[te]
        res = {"dataset": "BCCC-CIC-IDS-2017", "class_mode": "label", "split": fold, "model": name,
               "n_train": int(len(tr)), "n_test": int(len(te)), "seconds": round(time.time() - t0, 2),
               "all": metrics(yt, p), "leaked_rows": metrics(yt, p, lk),
               "binary_all": binary(yt, p), "binary_leaked": binary(yt[lk], p[lk])}
        json.dump(res, open(out, "w"), indent=1)
        b = res["binary_leaked"]
        print(f"{fold} {name:15s} leaked rows: detect={b['detect']} fpr={b['fpr']:.4f} (attack {b['n_attack']}, benign {b['n_benign']})", flush=True)


# ---- binary table over every timestamp-only result ------------------------------------------
def from_conf(r, is_att, is_ben):
    """Binary detect / FPR on leaked rows from a stored confusion matrix (rows = true, cols = predicted)."""
    cn = list(r["leaked_rows"]["per_class"]); M = np.array(r["leaked_rows"]["confusion"])
    a = np.array([is_att(c) for c in cn]); b = np.array([is_ben(c) for c in cn])
    na, nb = M[a].sum(), M[b].sum()
    return na, (M[a][:, a].sum() / na if na else np.nan), nb, (M[b][:, a].sum() / nb if nb else np.nan)


SRCS = [("CSE-CIC-IDS2018", "/home/USER/Desktop/ntl_exp23/results/exp2", lambda c: c != "Benign", lambda c: c == "Benign"),
        ("CIC-IDS-2017", f"{D17}/exp2_label", lambda c: c != "Benign", lambda c: c == "Benign"),
        ("cPacket (26 subtypes)", f"{HERE}/BCCC-cPacket-Cloud-DDoS-2024/exp2_activity",
         lambda c: c.startswith("Attack"), lambda c: c.startswith("Benign"))]
rows = []
for ds, d, ia, ib in SRCS:
    for sp in ("random", "temporal"):
        for mdl in ("tree", "tree_unweighted"):
            na, det, nb, fpr = from_conf(json.load(open(f"{d}/{sp}_{mdl}.json")), ia, ib)
            rows.append((ds, sp, mdl, na, det, nb, fpr))
for mdl in ("tree", "tree_unweighted"):  # LODO: pooled over the five held-out days
    na = nb = da = fb = 0
    for fold in FOLDS:
        b = json.load(open(f"{OUT}/{fold}_{mdl}.json"))["binary_leaked"]
        na += b["n_attack"]; nb += b["n_benign"]
        da += (b["detect"] or 0) * b["n_attack"]; fb += b["fpr"] * b["n_benign"]
    rows.append(("CIC-IDS-2017", "leave-one-day-out (5 days pooled)", mdl, na, da / na, nb, fb / nb))

f3 = lambda v: "–" if v is None or np.isnan(v) else f"{v:.3f}"
lbl = {"tree": "balanced (pre-specified)", "tree_unweighted": "unweighted (added afterwards)"}
Ltxt = ["# Timestamp-only tree: binary attack-vs-benign on leaked test rows", "",
        "Single feature t (smallest leaked IAT value). **detect** = leaked attack rows predicted as any attack class; "
        "**FPR** = leaked benign rows predicted as any attack class. Random / temporal rows are recomputed from the stored "
        "confusion matrices of Experiment 2 (no rerun); leave-one-day-out from this directory. cPacket: Suspicious counted "
        "as neither attack nor benign.", "",
        "| dataset | split | tree | leaked attack rows | detect | leaked benign rows | FPR |", "|---|---|---|---:|---:|---:|---:|"]
Ltxt += [f"| {ds} | {sp} | {lbl[m]} | {na:,} | {f3(det)} | {nb:,} | {f3(fpr)} |" for ds, sp, m, na, det, nb, fpr in rows]
Ltxt += ["", "## Leave-one-day-out per held-out day (CIC-IDS-2017, leaked test rows)", "",
         "| held-out day | tree | leaked attack rows | detect | leaked benign rows | FPR | majority-guess FPR |", "|---|---|---:|---:|---:|---:|---:|"]
for fold in FOLDS:
    mf = json.load(open(f"{OUT}/{fold}_most_frequent.json"))["binary_leaked"]
    for m in ("tree", "tree_unweighted"):
        b = json.load(open(f"{OUT}/{fold}_{m}.json"))["binary_leaked"]
        Ltxt.append(f"| {fold[5:]} | {lbl[m]} | {b['n_attack']:,} | {f3(b['detect'])} | {b['n_benign']:,} | {f3(b['fpr'])} | {f3(mf['fpr'])} |")
open(f"{OUT}/RESULTS.md", "w").write("\n".join(Ltxt) + "\n")
print("\n".join(Ltxt))
