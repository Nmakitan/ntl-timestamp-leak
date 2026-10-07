"""Leave-one-day-out report for d2017: binary attack-vs-benign scoring from the saved predictions.

Every 2017 attack class is captured on one day, so the held-out day's attack classes are absent from training and
multiclass recall on them is 0 by construction. Scored instead: detection rate (attack rows predicted as ANY attack
class) and false-positive rate (benign rows predicted as any attack class), on all rows and on leaked rows.
Writes results/LODO_2017.md and results/LODO_2017.csv.
"""
import glob, json, os
import numpy as np, pandas as pd
from mc_common import *

D = Data("d2017")
att = np.array([D.is_attack(c) for c in D.classes])
FOLDS = ("lodo_0703", "lodo_0704", "lodo_0705", "lodo_0706", "lodo_0707")
COND = [("leaky", "leaky", "leaky"), ("leaky", "leaky_plus8y", "leaky +8y"), ("leaky", "leaky_zero", "leaky, zeroed"),
        ("fixA", "fixA", "fixA")]
rows = []
for f in FOLDS:
    te = np.sort(D.split(f)[1]); y = D.y[te]; lk = D.leaked[te]; ya = att[y]
    for m in ("dt", "rf", "gnb"):
        for variant, key, name in COND:
            p = f"{RES}/runs/d2017_{f}_{m}_{variant}.pred.npz"
            if not os.path.exists(p):
                continue
            pa = att[np.load(p)[key]]
            assert len(pa) == len(te)
            r = {"fold": f, "model": m, "condition": name}
            for part, mask in (("all", np.ones(len(te), bool)), ("leaked", lk)):
                a, b = mask & ya, mask & ~ya
                r[f"{part}_n_attack"], r[f"{part}_n_benign"] = int(a.sum()), int(b.sum())
                r[f"{part}_detect"] = float(pa[a].mean()) if a.any() else np.nan
                r[f"{part}_fpr"] = float(pa[b].mean()) if b.any() else np.nan
            for k in np.unique(y[ya]):  # per held-out attack class, all rows
                r[f"det_{D.classes[k]}"] = float(pa[y == k].mean())
            rows.append(r)
T = pd.DataFrame(rows)
T.to_csv(f"{RES}/LODO_2017.csv", index=False)


def fmt(v):
    return "–" if pd.isna(v) else f"{v:.3f}"


L = ["# Leave-one-day-out, BCCC-CIC-IDS-2017 (DT, RF, GNB)", "",
     "Train on four capture days (600k stratified subsample), test on the whole fifth day. The held-out day's attack "
     "classes never appear in training, so scoring is binary: **detect** = share of attack rows predicted as any attack "
     "class; **FPR** = share of benign rows predicted as any attack class. Conditions: leaky model as is; same model "
     "with leaked timestamps +8 years or zeroed (no retrain); fixA = retrained with leaked IAT cells zeroed in train and test.", ""]
for part, title in (("all", "All test rows"), ("leaked", "Leaked test rows only")):
    L += [f"## {title}", "", "| held-out day | model | condition | attack rows | detect | benign rows | FPR |", "|---|---|---|---|---|---|---|"]
    for d in T.to_dict("records"):
        L.append(f"| {d['fold'][5:]} | {d['model']} | {d['condition']} | {d[f'{part}_n_attack']:,} | {fmt(d[f'{part}_detect'])} | "
                 f"{d[f'{part}_n_benign']:,} | {fmt(d[f'{part}_fpr'])} |")
    L.append("")
det = [c for c in T.columns if c.startswith("det_")]
L += ["## Detection rate per held-out attack class (all rows)", "", "| held-out day | model | condition | " + " | ".join(c[4:] for c in det) + " |",
      "|---|---|---|" + "---|" * len(det)]
for d in T.to_dict("records"):
    L.append(f"| {d['fold'][5:]} | {d['model']} | {d['condition']} | " + " | ".join(fmt(d[c]) for c in det) + " |")
open(f"{RES}/LODO_2017.md", "w").write("\n".join(L) + "\n")
print("\n".join(L))
