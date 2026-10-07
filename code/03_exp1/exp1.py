"""Experiment 1: change only the leaked IAT timestamps in the held-out test set and re-score the existing RF.

Conditions: baseline, +8y, +1d, shuffle (seeds 0-4), zero.  Leaked cell = IAT column value > 1e9.
Arithmetic on leaked cells is done in float64; the matrix is cast back to float32 only for scoring.
Every condition is scored on all rows so the "non-leaked rows unchanged" sanity check is real.
"""
import json, os, time
import numpy as np, onnxruntime as ort
from sklearn.metrics import accuracy_score, f1_score, precision_recall_fscore_support, confusion_matrix

D = "/home/USER/pew/Dataset/ml_module_output/_intermediate"
MODEL_DIR = "/home/USER/trained_models"
OUT = os.path.dirname(os.path.abspath(__file__))
LEAK = 1e9
EIGHT_YEARS = 8 * 365.25 * 86400  # 252,460,800 s, a multiple of the 128 s float32 step at ~1.5e9
BATCH = 100_000

names = json.load(open(f"{MODEL_DIR}/feature_order.json"))
classes = json.load(open(f"{MODEL_DIR}/label_mapping.json"))
cls = [classes[str(i)] for i in range(len(classes))]
L = list(range(len(cls)))
iat = [i for i, n in enumerate(names) if "IAT" in n]

X = np.load(f"{D}/test_X.npy")          # float32, as used in training/eval
y = np.load(f"{D}/test_y.npy")
assert X.shape == (len(y), len(names)) and X.dtype == np.float32
XI = X[:, iat].astype(np.float64)       # IAT block in float64 for modifications
MI = XI > LEAK                          # leaked cells within the IAT block
leaked = MI.any(axis=1)
t_row = np.where(MI, XI, np.inf).min(axis=1)  # smallest leaked value per row

sess = ort.InferenceSession(f"{MODEL_DIR}/rf_model.onnx", providers=["CPUExecutionProvider"])
inp = sess.get_inputs()[0].name


def pred(Z):
    return np.concatenate([sess.run(None, {inp: Z[i:i + BATCH]})[0] for i in range(0, len(Z), BATCH)]).astype(np.int64)


def with_iat(new_iat64):
    Z = X.copy()
    Z[:, iat] = new_iat64.astype(np.float32)
    return Z


def shifted(off_row):
    Zi = XI.copy()
    Zi[MI] += np.broadcast_to(off_row, (len(X),))[:, None].repeat(len(iat), 1)[MI]
    return with_iat(Zi)


def metrics(p, mask=None):
    yy, pp = (y, p) if mask is None else (y[mask], p[mask])
    pr, rc, f1, sup = precision_recall_fscore_support(yy, pp, labels=L, zero_division=0)
    return {"n": int(len(yy)), "accuracy": float(accuracy_score(yy, pp)),
            "macro_f1": float(f1_score(yy, pp, labels=L, average="macro", zero_division=0)),
            "per_class": {c: {"precision": float(pr[i]), "recall": float(rc[i]), "f1": float(f1[i]), "support": int(sup[i])}
                          for i, c in enumerate(cls)}}


results = {"n_test": int(len(y)), "n_features": len(names), "iat_columns": [names[i] for i in iat],
           "leaked_rows_per_class": {c: {"n": int((y == i).sum()), "leaked": int((leaked & (y == i)).sum())}
                                     for i, c in enumerate(cls)},
           "leaked_rows_total": int(leaked.sum()), "conditions": {}}

t0 = time.time()
base = pred(X)
print(f"baseline scored in {time.time() - t0:.0f}s", flush=True)
np.save(f"{OUT}/pred_baseline.npy", base)


def record(name, p):
    if name != "baseline":
        ok = bool((p[~leaked] == base[~leaked]).all())
        assert ok, f"{name}: predictions changed on non-leaked rows - something besides timestamps changed"
    ch = p != base
    results["conditions"][name] = {
        "all": metrics(p), "leaked_rows": metrics(p, leaked),
        "changed_predictions": int(ch.sum()),
        "confusion": confusion_matrix(y, p, labels=L).tolist(),
        "confusion_leaked": confusion_matrix(y[leaked], p[leaked], labels=L).tolist(),
        # where changed predictions went: rows = baseline prediction, cols = new prediction
        "transitions": confusion_matrix(base[ch], p[ch], labels=L).tolist() if ch.any() else None,
    }
    np.save(f"{OUT}/pred_{name}.npy", p)
    a, l = results["conditions"][name]["all"], results["conditions"][name]["leaked_rows"]
    print(f"{name:10s} acc={a['accuracy']:.4f} mF1={a['macro_f1']:.4f} | leaked acc={l['accuracy']:.4f} "
          f"mF1={l['macro_f1']:.4f} | changed={int(ch.sum())}", flush=True)
    json.dump(results, open(f"{OUT}/exp1_results.json", "w"), indent=1)


record("baseline", base)
record("plus_8y", pred(shifted(EIGHT_YEARS)))
record("plus_1d", pred(shifted(86400.0)))
idx = np.flatnonzero(leaked)
for seed in range(5):
    perm = np.random.default_rng(seed).permutation(idx)
    off = np.zeros(len(X)); off[idx] = t_row[perm] - t_row[idx]
    record(f"shuffle_s{seed}", pred(shifted(off)))
Zi = XI.copy(); Zi[MI] = 0.0
record("zero_fixed_data_leaky_model", pred(with_iat(Zi)))
print("ALL DONE", flush=True)
