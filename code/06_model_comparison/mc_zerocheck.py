"""Validity checks for fixA (random split; train = cached 600k subsample, test = full test split) -> results/ZERO_CHECK.json.
1. Units: leaked IAT cells should all be epoch seconds; legitimate IATs should stay far below the 1e9 threshold.
2. Does fixA's 'IAT cell == 0' pattern carry class information beyond legitimate zeros? A balanced decision tree
   (same settings as the study's DT) is trained on binary masks only and scored on the test split.
Usage: mc_zerocheck.py [datasets...]"""
import sys, os, json, numpy as np
import mc_common as c
from sklearn.tree import DecisionTreeClassifier
from sklearn.metrics import accuracy_score, f1_score, recall_score

def score(d, y, p):
    att = [k for k, n in enumerate(d.classes) if d.is_attack(n) and (y == k).sum() >= 10]
    r = recall_score(y, p, labels=att, average=None, zero_division=0)
    return {"accuracy": accuracy_score(y, p), "macro_f1": f1_score(y, p, labels=range(len(d.classes)), average="macro", zero_division=0),
            "mean_attack_recall": float(r.mean())}

fmt = lambda s: f"acc={s['accuracy']:.3f} macroF1={s['macro_f1']:.3f} meanAttRecall={s['mean_attack_recall']:.3f}"

OUT = f"{c.RES}/ZERO_CHECK.json"
out = json.load(open(OUT)) if os.path.exists(OUT) else {}
for name in sys.argv[1:] or ["d2018", "d2017", "cpacket"]:
    d = c.Data(name); iat = d.iat
    print(f"\n===== {name}: {len(iat)} IAT columns of {len(d.features)} features", flush=True)
    print("IAT cols:", [d.features[i] for i in iat][:40])
    itr, Xtr = c.get_xy(d, "random", "train"); Rtr = Xtr[:, iat].astype(np.float64); del Xtr
    ite, Xte = c.get_xy(d, "random", "test"); Rte = Xte[:, iat].astype(np.float64); del Xte
    ytr, yte = d.y[itr], d.y[ite]
    # units: leaked values should all sit in the epoch range (~1.48e9-1.73e9 s for 2017-2024)
    L = Rtr > c.LEAK; lv = Rtr[L]; nl = Rtr[~L & (Rtr != 0)]
    o = out[name] = {"n_iat_cols": len(iat), "n_features": len(d.features), "units": {
        "leaked_min": float(lv.min()), "leaked_max": float(lv.max()), "legit_nonzero_median": float(np.median(nl)),
        "legit_nonzero_p9999": float(np.percentile(nl, 99.99)), "legit_max": float(nl.max()),
        "cells_in_1e6_1e9": int(((Rtr > 1e6) & (Rtr <= 1e9)).sum())}, "per_class": {}, "mask_models": {}}
    print(f"leaked cells: n={L.sum()} min={lv.min():.4g} p1={np.percentile(lv,1):.4g} max={lv.max():.4g}")
    print(f"non-leaked nonzero cells: p50={np.median(nl):.4g} p99={np.percentile(nl,99):.4g} p99.99={np.percentile(nl,99.99):.4g} max={nl.max():.4g}")
    print(f"non-leaked cells in (1e6,1e9]: {((Rtr>1e6)&(Rtr<=1e9)).sum()}  in (1e8,1e9]: {((Rtr>1e8)&(Rtr<=1e9)).sum()}")
    # zero rates, per class: leaked-row rate, legit exact-zero rate in IAT cells of non-leaked rows
    rowL = L.any(1)
    print(f"{'class':38s} {'n':>8s} {'rowLeak%':>8s} {'legit0% (cells, nonleaked rows)':>32s} {'rows all-IAT=0 (nonleaked)%':>28s}")
    for k, cn in enumerate(d.classes):
        m = ytr == k
        if not m.any(): continue
        nlr = Rtr[m & ~rowL]
        z = (nlr == 0).mean() * 100 if len(nlr) else float("nan")
        za = (nlr == 0).all(1).mean() * 100 if len(nlr) else float("nan")
        print(f"{cn[:38]:38s} {m.sum():8d} {rowL[m].mean()*100:8.1f} {z:32.1f} {za:28.1f}")
        o["per_class"][cn] = {"n_train": int(m.sum()), "row_leak_pct": float(rowL[m].mean() * 100),
                              "legit_zero_cell_pct": None if np.isnan(z) else float(z)}
    # signal tests: train DT (balanced, same as study) on binary features only, eval on full random test split
    feats = {
        "row leaked flag (1 bit)": (rowL[:, None], (Rte > c.LEAK).any(1)[:, None]),
        "per-col leaked mask": (L, Rte > c.LEAK),
        "zero mask, raw data (legit zeros only)": (Rtr == 0, Rte == 0),
        "zero mask, after fixA (legit + leaked)": ((Rtr == 0) | L, (Rte == 0) | (Rte > c.LEAK)),
    }
    maj = np.bincount(ytr).argmax()
    o["mask_models"]["majority baseline"] = score(d, yte, np.full_like(yte, maj))
    print("majority baseline:", fmt(o["mask_models"]["majority baseline"]))
    for lab, (a, b) in feats.items():
        m = DecisionTreeClassifier(class_weight="balanced", max_depth=30, min_samples_leaf=10, random_state=0).fit(a.astype(np.uint8), ytr)
        o["mask_models"][lab] = score(d, yte, m.predict(b.astype(np.uint8)))
        print(f"{lab:42s}", fmt(o["mask_models"][lab]), flush=True)
    del Rtr, Rte
    json.dump(out, open(OUT + ".tmp", "w"), indent=1); os.replace(OUT + ".tmp", OUT)
