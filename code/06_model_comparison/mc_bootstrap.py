"""Paired bootstrap CIs on the fixed test sets -> results/bootstrap/<ds>_<split>_<model>.json + results/BOOTSTRAP_CI.csv.
Resamples test rows with replacement (B=1000, seed 0); every condition of one model is scored on the same resample,
so differences are paired. Identical (true label, leaked flag, predictions) rows are collapsed into weighted tuples and
resampled with a multinomial over tuple counts, which is exactly a row bootstrap. Metrics follow mc_run.py: accuracy,
macro F1 and mean attack recall (attack classes with >= 10 rows in the subset), on all rows and on leaked rows.
Usage: mc_bootstrap.py [B]   (re-runs a triple only when its set of conditions changed)"""
import csv, glob, json, os, sys
import numpy as np
from mc_common import Data, RES

B = int(sys.argv[1]) if len(sys.argv) > 1 else 1000
OUT = f"{RES}/bootstrap"
CONDS = ["leaky", "leaky_plus8y", "leaky_zero", "fixA", "dropIAT"]
DIFFS = [("leaky", "leaky_plus8y"), ("leaky", "leaky_zero"), ("leaky", "fixA"), ("leaky", "dropIAT"), ("fixA", "dropIAT")]
METRICS = [("all", "accuracy"), ("all", "macro_f1"), ("all", "mean_attack_recall"),
           ("leaked_rows", "accuracy"), ("leaked_rows", "macro_f1"), ("leaked_rows", "mean_attack_recall")]
os.makedirs(OUT, exist_ok=True)


def scores(W, y, p, sub, ncls, att_cls):
    """W: (b, U) tuple weights; y, p: (U,) labels; sub: (U,) bool subset. Returns {metric: (b,) array}."""
    Ws = W * sub
    n = Ws.sum(1)
    out = {"accuracy": (Ws * (y == p)).sum(1) / n}
    f1s, rec = [], {}
    for k in range(ncls):
        tp = (Ws * ((y == k) & (p == k))).sum(1)
        sup = (Ws * (y == k)).sum(1)
        pp = (Ws * (p == k)).sum(1)
        rec[k] = np.divide(tp, sup, out=np.zeros_like(tp, dtype=float), where=sup > 0)
        f1s.append(np.divide(2 * tp, sup + pp, out=np.zeros_like(tp, dtype=float), where=(sup + pp) > 0))
    out["macro_f1"] = np.mean(f1s, axis=0)  # matches f1_score(labels=all classes, zero_division=0)
    out["mean_attack_recall"] = np.mean([rec[k] for k in att_cls], axis=0) if att_cls else np.full(len(W), np.nan)
    return out


rows = []
for ds in ("d2018", "d2017", "cpacket"):
    D = None
    for split in ("random", "temporal"):
        models = sorted({os.path.basename(f).split("_")[2] for f in glob.glob(f"{RES}/runs/{ds}_{split}_*.pred.npz")})
        for model in models:
            f_out = f"{OUT}/{ds}_{split}_{model}.json"
            preds = {}
            for v in ("leaky", "fixA", "dropIAT"):
                f = f"{RES}/runs/{ds}_{split}_{model}_{v}.pred.npz"
                if os.path.exists(f) and os.path.exists(f.replace(".pred.npz", ".json")):
                    z = np.load(f); preds.update({k: z[k] for k in z.files})
            conds = [c for c in CONDS if c in preds]
            if os.path.exists(f_out) and json.load(open(f_out))["conditions"] == conds and json.load(open(f_out))["B"] == B:
                res = json.load(open(f_out))
            else:
                if D is None:
                    D = Data(ds)
                te = np.sort(D.split(split)[1])
                y, lk = D.y[te].astype(np.int64), D.leaked[te].astype(bool)
                ncls = len(D.classes)
                M = np.column_stack([y, lk] + [preds[c].astype(np.int64) for c in conds])
                assert all(len(preds[c]) == len(y) for c in conds)
                T, cnt = np.unique(M, axis=0, return_counts=True)
                ty, tl = T[:, 0], T[:, 1].astype(bool)
                tp = {c: T[:, 2 + i] for i, c in enumerate(conds)}
                subs = {"all": np.ones(len(T), bool), "leaked_rows": tl}
                att = {s: [k for k in range(ncls) if D.is_attack(D.classes[k]) and cnt[(ty == k) & m].sum() >= 10]
                       for s, m in subs.items()}
                point = {c: {s: {k: float(v[0]) for k, v in scores(cnt[None, :].astype(float), ty, tp[c], m, ncls, att[s]).items()}
                             for s, m in subs.items()} for c in conds}
                rng = np.random.default_rng(0)
                draws = {(c, s, k): [] for c in conds for s in subs for k in ("accuracy", "macro_f1", "mean_attack_recall")}
                for b0 in range(0, B, 50):  # batches keep the (b, U) weight matrix small
                    W = rng.multinomial(len(y), cnt / cnt.sum(), size=min(50, B - b0)).astype(float)
                    for c in conds:
                        for s, m in subs.items():
                            for k, v in scores(W, ty, tp[c], m, ncls, att[s]).items():
                                draws[(c, s, k)].append(v)
                draws = {key: np.concatenate(v) for key, v in draws.items()}
                ci = lambda a: [float(np.nanpercentile(a, 2.5)), float(np.nanpercentile(a, 97.5))]
                res = {"dataset": ds, "split": split, "model": model, "B": B, "conditions": conds, "n_tuples": int(len(T)),
                       "attack_classes_in_mean": {s: [D.classes[k] for k in a] for s, a in att.items()},
                       "cond": {c: {s: {k: {"point": point[c][s][k], "ci95": ci(draws[(c, s, k)])}
                                        for k in ("accuracy", "macro_f1", "mean_attack_recall")} for s in subs} for c in conds},
                       "diff": {}}
                for a, b in DIFFS:
                    if a in conds and b in conds:
                        res["diff"][f"{a}-{b}"] = {s: {k: {"point": point[a][s][k] - point[b][s][k],
                                                           "ci95": ci(draws[(a, s, k)] - draws[(b, s, k)])}
                                                       for k in ("accuracy", "macro_f1", "mean_attack_recall")} for s in subs}
                # the bootstrap's point estimates must reproduce the run JSONs exactly
                for c in conds:
                    v = "leaky" if c.startswith("leaky") else c
                    rj = json.load(open(f"{RES}/runs/{ds}_{split}_{model}_{v}.json"))["conditions"][c]
                    for s in subs:
                        for k in ("accuracy", "macro_f1"):
                            assert abs(rj[s][k] - point[c][s][k]) < 1e-9, (ds, split, model, c, s, k)
                        if rj[s]["mean_attack_recall"] is not None:
                            assert abs(rj[s]["mean_attack_recall"] - point[c][s]["mean_attack_recall"]) < 1e-9, (ds, split, model, c, s)
                json.dump(res, open(f_out + ".tmp", "w"), indent=1); os.replace(f_out + ".tmp", f_out)
                print(f"{ds} {split} {model}: {len(conds)} conditions, {len(T)} tuples", flush=True)
            for kind, block in (("condition", res["cond"]), ("difference", res["diff"])):
                for name, per in block.items():
                    for s, mm in per.items():
                        for k, v in mm.items():
                            rows.append({"dataset": ds, "split": split, "model": model, "kind": kind, "name": name,
                                         "subset": s, "metric": k, "point": v["point"], "ci_lo": v["ci95"][0],
                                         "ci_hi": v["ci95"][1], "B": B})

with open(f"{RES}/BOOTSTRAP_CI.csv", "w", newline="") as fh:
    w = csv.DictWriter(fh, list(rows[0]))
    w.writeheader(); w.writerows(rows)
print(f"{len(rows)} rows -> {RES}/BOOTSTRAP_CI.csv")
