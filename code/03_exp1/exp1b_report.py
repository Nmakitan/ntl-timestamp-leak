"""Experiment 1b report: RF vs KNN vs ensemble on the same stratified sample and identical condition inputs.

Per condition, a model's sample predictions = its baseline predictions with the rescored rows (leaked + sanity) replaced.
Metrics are given unweighted (sample) and population-weighted (weight = test class count / sample class count),
since the rare classes are over-represented in the sample. Recall is unaffected by the weighting; accuracy,
precision and macro-F1 are not.
"""
import json, os
import numpy as np
from sklearn.metrics import accuracy_score, f1_score, precision_recall_fscore_support, confusion_matrix

HERE = os.path.dirname(os.path.abspath(__file__))
B = f"{HERE}/exp1b"
classes = json.load(open("/home/USER/trained_models/label_mapping.json"))
cls = [classes[str(i)] for i in range(len(classes))]
L = list(range(len(cls)))
s = np.load(f"{B}/sample.npz")
S, y, leaked, sanity_pos = s["idx"], s["y"], s["leaked"], s["sanity_pos"]
rows = np.load(f"{B}/cond_rows.npy")
n_cls_S = np.bincount(y, minlength=len(cls))
w = (s["class_counts_test"] / np.maximum(n_cls_S, 1))[y]
conds = ["baseline", "plus_8y", "plus_1d", "zero_fixed_data_leaky_model"] + [f"shuffle_s{k}" for k in range(5)]


def load(model, cond):
    if model == "rf":
        return np.load(f"{HERE}/pred_{cond}.npy")[S]
    if cond == "baseline":
        f = f"{B}/pred_{model}_baseline.npy"
        return np.load(f) if os.path.exists(f) else None
    f = f"{B}/pred_{model}_{cond}.npy"
    base = load(model, "baseline")
    if base is None or not os.path.exists(f):
        return None
    p = base.copy(); p[rows] = np.load(f)
    return p


def metrics(p, mask):
    yy, pp, ww = y[mask], p[mask], w[mask]
    pr_w, rc, f1_w, sup = precision_recall_fscore_support(yy, pp, labels=L, zero_division=0, sample_weight=ww)
    pr, _, _, _ = precision_recall_fscore_support(yy, pp, labels=L, zero_division=0)
    return {"n": int(mask.sum()),
            "accuracy": float(accuracy_score(yy, pp)), "accuracy_popw": float(accuracy_score(yy, pp, sample_weight=ww)),
            "macro_f1": float(f1_score(yy, pp, labels=L, average="macro", zero_division=0)),
            "macro_f1_popw": float(f1_score(yy, pp, labels=L, average="macro", zero_division=0, sample_weight=ww)),
            "per_class": {c: {"recall": float(rc[i]), "precision_popw": float(pr_w[i]), "precision_sample": float(pr[i]),
                              "support": int(sup[i])} for i, c in enumerate(cls)}}


res, allm = {}, np.ones(len(y), bool)
for model in ["rf", "knn", "ensemble"]:
    base = load(model, "baseline")
    if base is None:
        continue
    for cond in conds:
        p = load(model, cond)
        if p is None:
            continue
        sanity_ok = bool((p[sanity_pos] == base[sanity_pos]).all())
        ch = p != base
        res.setdefault(model, {})[cond] = {
            "sanity_nonleaked_unchanged": sanity_ok, "all": metrics(p, allm), "leaked_rows": metrics(p, leaked),
            "changed_predictions": int(ch.sum()),
            "transitions": confusion_matrix(base[ch], p[ch], labels=L).tolist() if ch.any() else None,
            "confusion_leaked": confusion_matrix(y[leaked], p[leaked], labels=L).tolist()}
json.dump(res, open(f"{B}/exp1b_results.json", "w"), indent=1)

# ---- console summary ------------------------------------------------------------------------
for model, R in res.items():
    print(f"\n=== {model.upper()} (sample n={len(y)}, leaked {int(leaked.sum())}) ===")
    print(f"{'condition':30s} {'acc':>7s} {'acc_pw':>7s} {'mF1':>7s} {'mF1_pw':>7s} | {'L_acc':>7s} {'L_mF1':>7s} | changed sanity")
    for cond, r in R.items():
        a, l = r["all"], r["leaked_rows"]
        print(f"{cond:30s} {a['accuracy']:7.4f} {a['accuracy_popw']:7.4f} {a['macro_f1']:7.4f} {a['macro_f1_popw']:7.4f} | "
              f"{l['accuracy']:7.4f} {l['macro_f1']:7.4f} | {r['changed_predictions']:7d} {r['sanity_nonleaked_unchanged']}")
    sh = [R[c] for c in R if c.startswith("shuffle")]
    if len(sh) > 1:
        for part, key in [("all", "accuracy_popw"), ("all", "macro_f1_popw"), ("leaked_rows", "accuracy"), ("leaked_rows", "macro_f1")]:
            v = [x[part][key] for x in sh]
            print(f"  shuffle x{len(sh)} {part}.{key}: {np.mean(v):.4f} ± {np.std(v, ddof=1):.4f}")
    show = [c for c in ["baseline", "plus_8y", "plus_1d", "zero_fixed_data_leaky_model", "shuffle_s0"] if c in R]
    print(f"  recall (all rows) {'':4s}" + "".join(f"{c[:10]:>11s}" for c in show))
    for c in cls:
        print(f"  {c:20s}" + "".join(f"{R[k]['all']['per_class'][c]['recall']:11.4f}" for k in show))
    print(f"  precision (pop-weighted)" + "".join(f"{c[:10]:>11s}" for c in show))
    for c in cls:
        print(f"  {c:20s}" + "".join(f"{R[k]['all']['per_class'][c]['precision_popw']:11.4f}" for k in show))
    for k in show[1:]:
        T = R[k]["transitions"]
        if T:
            T = np.array(T); top = np.dstack(np.unravel_index(np.argsort(-T.ravel())[:5], T.shape))[0]
            print(f"  {k} top base->new:", [(cls[a][:9], cls[b][:9], int(T[a, b])) for a, b in top if T[a, b]])
