"""One run = one dataset x split x model x training variant, in its own process.
Usage: mc_run.py <dataset> <split> <model> <leaky|fixA|dropIAT>
A model name ending in "full" (rffull, xgbfull) trains on the FULL training split instead of the 600k subsample.
leaky -> evaluates conditions leaky, leaky_plus8y, leaky_zero (same model, no retrain); fixA -> retrain + evaluate fixA; dropIAT -> retrain + evaluate with every IAT column removed.
Writes results/runs/<dataset>_<split>_<model>_<variant>.json (+ .pred.npz). Convergence warnings are recorded, not suppressed.
"""
import json, os, sys, time, resource, warnings
import numpy as np
from sklearn.metrics import accuracy_score, f1_score, precision_recall_fscore_support, confusion_matrix
from mc_common import *

ds, split, model, variant = sys.argv[1:5]
out = f"{RES}/runs/{ds}_{split}_{model}_{variant}.json"
if os.path.exists(out):
    sys.exit(f"exists: {out}")


def build(name):
    from sklearn.pipeline import make_pipeline
    from sklearn.preprocessing import StandardScaler, MinMaxScaler
    if name == "gnb":
        from sklearn.naive_bayes import GaussianNB; return GaussianNB()
    if name == "dt":
        from sklearn.tree import DecisionTreeClassifier
        return DecisionTreeClassifier(max_depth=30, min_samples_leaf=10, class_weight="balanced", random_state=0)
    if name == "lr":
        from sklearn.linear_model import LogisticRegression
        return make_pipeline(StandardScaler(), LogisticRegression(max_iter=1000, class_weight="balanced"))
    if name == "xgb":
        from xgboost import XGBClassifier
        return XGBClassifier(n_estimators=200, max_depth=8, learning_rate=0.1, tree_method="hist", n_jobs=4, random_state=0)
    if name == "rf":
        from sklearn.ensemble import RandomForestClassifier
        return RandomForestClassifier(n_estimators=200, max_depth=30, min_samples_leaf=10, class_weight="balanced", n_jobs=2, random_state=0)
    if name == "linsvc":
        from sklearn.svm import LinearSVC
        return make_pipeline(StandardScaler(), LinearSVC(class_weight="balanced", dual=False, max_iter=2000))
    if name == "mlp":
        from sklearn.neural_network import MLPClassifier
        return make_pipeline(StandardScaler(), MLPClassifier(hidden_layer_sizes=(128, 64), max_iter=50, early_stopping=True, random_state=0))
    if name == "knn":  # as the shipped knn_model.onnx: StandardScaler + distance-weighted 5-NN
        from sklearn.neighbors import KNeighborsClassifier
        return make_pipeline(StandardScaler(), KNeighborsClassifier(weights="distance", n_jobs=int(os.environ.get("KNN_JOBS", os.cpu_count()))))
    if name == "lgbm":
        from lightgbm import LGBMClassifier
        return LGBMClassifier(n_estimators=200, num_leaves=63, learning_rate=0.1, class_weight="balanced", random_state=0)
    if name == "mlp_minmax":
        from sklearn.neural_network import MLPClassifier
        return make_pipeline(MinMaxScaler(), MLPClassifier(hidden_layer_sizes=(128, 64), max_iter=50, early_stopping=True, random_state=0))
    raise ValueError(name)


full = model.endswith("full")  # rffull / xgbfull: full training split, same model configuration
base = model[:-4] if full else model
D = Data(ds)
L = list(range(len(D.classes)))
fix = {"leaky": None, "fixA": "fix", "dropIAT": "drop"}[variant]
if full:
    tr = np.sort(D.split(split)[0])
    Xtr = D.take_modified(tr, fix)  # modified while reading: no second full-size copy
else:
    tr, Xtr_raw = get_xy(D, split, "train")

caught = []
def show(message, category, filename, lineno, file=None, line=None):
    caught.append(f"{category.__name__}: {message}")
    print(f"WARNING {category.__name__}: {message}", flush=True)
warnings.showwarning = show
warnings.simplefilter("always")
warnings.simplefilter("ignore", ResourceWarning)  # Python file-handle noise, not model warnings

if not full:
    Xtr = modify(Xtr_raw, D.iat, fix); del Xtr_raw
ytr = D.y[tr]
clf = build(base)
t0 = time.time()
if base == "xgb" and full:
    # The sklearn wrapper would keep the 4 GB float matrix alive during training; build the quantised matrix
    # (~1 byte per cell) first, free the floats, then train natively with the wrapper's own parameters.
    import gc, xgboost as xgb
    from sklearn.utils.class_weight import compute_sample_weight
    dtrain = xgb.QuantileDMatrix(Xtr, label=ytr, weight=compute_sample_weight("balanced", ytr), max_bin=clf.max_bin or 256)
    Xtr = None; gc.collect()
    params = {**{k: v for k, v in clf.get_xgb_params().items() if v is not None}, "objective": "multi:softprob", "num_class": len(L)}
    booster = xgb.train(params, dtrain, num_boost_round=clf.n_estimators)
    del dtrain

    class BoosterClf:  # predict() like XGBClassifier: argmax of class probabilities
        def __init__(self, b, p, n): self.b, self.p, self.n = b, p, n
        def predict(self, Z): return self.b.inplace_predict(Z).argmax(1)
        def __repr__(self): return f"xgboost.train({self.p}, num_boost_round={self.n}) on QuantileDMatrix"
    clf = BoosterClf(booster, params, clf.n_estimators)
elif base == "xgb":
    from sklearn.utils.class_weight import compute_sample_weight
    clf.fit(Xtr, ytr, sample_weight=compute_sample_weight("balanced", ytr))
else:
    clf.fit(Xtr, ytr)
fit_s = time.time() - t0
del Xtr

te, Xte = get_xy(D, split, "test")  # whole test split once; predict in chunks from memory
conds = {"leaky": None, "leaky_plus8y": "shift", "leaky_zero": "zero"} if variant == "leaky" else {variant: fix}
preds = {k: np.empty(len(te), dtype=np.int64) for k in conds}
t0 = time.time()
for i in range(0, len(te), CHUNK):
    Z = Xte[i:i + CHUNK]
    for k, how in conds.items():
        if model == "knn" and how in ("shift", "zero"):
            # +8y / zero change only leaked rows; every other row keeps its leaky prediction (KNN is the slow model)
            preds[k][i:i + len(Z)] = preds["leaky"][i:i + len(Z)]
            lk = (Z[:, D.iat] > LEAK).any(1)
            if lk.any():
                preds[k][i:i + len(Z)][lk] = clf.predict(modify(Z[lk], D.iat, how))
        else:
            preds[k][i:i + len(Z)] = clf.predict(modify(Z, D.iat, how))
    if model == "knn":
        print(f"{time.strftime('%H:%M:%S')} predicted {i + len(Z):,} of {len(te):,} rows", flush=True)
pred_s = time.time() - t0
yte, lte = D.y[te], D.leaked[te]


def metrics(p, mask=None):
    yt, pp = (yte, p) if mask is None else (yte[mask], p[mask])
    pr, rc, f1, sup = precision_recall_fscore_support(yt, pp, labels=L, zero_division=0)
    pc = {c: {"recall": float(rc[i]), "precision": float(pr[i]), "support": int(sup[i]),
              "correct": int(((yt == i) & (pp == i)).sum())} for i, c in enumerate(D.classes)}
    att = [v["recall"] for c, v in pc.items() if D.is_attack(c) and v["support"] >= 10]
    return {"n": int(len(yt)), "accuracy": float(accuracy_score(yt, pp)),
            "macro_f1": float(f1_score(yt, pp, labels=L, average="macro", zero_division=0)),
            "mean_attack_recall": float(np.mean(att)) if att else None, "n_attack_classes_in_mean": len(att),
            "per_class": pc, "confusion": confusion_matrix(yt, pp, labels=L).tolist()}


res = {"dataset": ds, "split": split, "model": model, "variant": variant, "params": str(clf),
       "n_train": int(len(tr)), "n_test": int(len(te)), "n_features": len(D.features) - (len(D.iat) if variant == "dropIAT" else 0),
       "fit_seconds": round(fit_s, 1), "predict_seconds": round(pred_s, 1),
       "peak_rss_gb_self": resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / 1e6,
       "warnings": sorted(set(caught)), "n_warnings": len(caught),
       "conditions": {k: {"all": metrics(p), "leaked_rows": metrics(p, lte)} for k, p in preds.items()}}
if hasattr(clf, "n_iter_") or (hasattr(clf, "steps") and hasattr(clf.steps[-1][1], "n_iter_")):
    est = clf.steps[-1][1] if hasattr(clf, "steps") else clf
    res["n_iter"] = np.asarray(est.n_iter_).tolist()
os.makedirs(os.path.dirname(out), exist_ok=True)
np.savez_compressed(out.replace(".json", ".pred.npz"), **preds)
with open(out + ".tmp", "w") as fh:
    json.dump(res, fh, indent=1)
os.replace(out + ".tmp", out)
print(f"{ds} {split} {model} {variant}: " + " | ".join(
    f"{k} acc={v['all']['accuracy']:.4f} leaked={v['leaked_rows']['accuracy']:.4f}" for k, v in res["conditions"].items())
      + f" | fit {fit_s:.0f}s, warnings {len(caught)}", flush=True)
