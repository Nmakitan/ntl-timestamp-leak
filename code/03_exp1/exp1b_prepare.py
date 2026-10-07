"""Experiment 1b, step 1: build the stratified test sample and every condition's input matrix.

Conditions are constructed exactly as in exp1.py on the FULL test set (same shuffle seeds and donor permutation),
then subset to the sample, so RF predictions from exp1 (pred_*.npy) apply to identical inputs.
Writes exp1b/sample.npz and exp1b/cond_<name>.npy (float32, only the rows each job must score).
"""
import json, os
import numpy as np

D = "/home/USER/pew/Dataset/ml_module_output/_intermediate"
MODEL_DIR = "/home/USER/trained_models"
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "exp1b")
LEAK, EIGHT_YEARS = 1e9, 8 * 365.25 * 86400
SAMPLE_N, SANITY_N = 20_000, 200
KEEP_ALL = ["SQL_Injection", "Brute_Force_XSS", "Brute_Force_Web"]
os.makedirs(OUT, exist_ok=True)

names = json.load(open(f"{MODEL_DIR}/feature_order.json"))
classes = json.load(open(f"{MODEL_DIR}/label_mapping.json"))
cls = [classes[str(i)] for i in range(len(classes))]
iat = [i for i, n in enumerate(names) if "IAT" in n]
X = np.load(f"{D}/test_X.npy", mmap_mode="r")
y = np.load(f"{D}/test_y.npy")
XI = np.asarray(X[:, iat], dtype=np.float64)
MI = XI > LEAK
leaked = MI.any(axis=1)
t_row = np.where(MI, XI, np.inf).min(axis=1)

# --- stratified sample over (class, leaked); rare classes kept whole ----------------------
rng = np.random.default_rng(12345)
keep = [i for i, c in enumerate(cls) if c in KEEP_ALL]
forced = np.flatnonzero(np.isin(y, keep))
rest = np.flatnonzero(~np.isin(y, keep))
budget = SAMPLE_N - len(forced)
key = y[rest] * 2 + leaked[rest]
picked = []
for k in np.unique(key):
    pool = rest[key == k]
    n_k = int(round(budget * len(pool) / len(rest)))
    picked.append(rng.choice(pool, size=min(n_k, len(pool)), replace=False))
S = np.sort(np.concatenate([forced] + picked))
yS, lS = y[S], leaked[S]
print(f"sample {len(S)} rows, leaked {lS.sum()}")
for i, c in enumerate(cls):
    print(f"  {c:16s} n={int((yS == i).sum()):6d} leaked={int((lS & (yS == i)).sum()):5d} (test total {int((y == i).sum())})")

nonleak_S = np.flatnonzero(~lS)
sanity = np.sort(rng.choice(nonleak_S, size=min(SANITY_N, len(nonleak_S)), replace=False))  # positions within S
leak_pos = np.flatnonzero(lS)                                                               # positions within S
np.savez(f"{OUT}/sample.npz", idx=S, y=yS, leaked=lS, sanity_pos=sanity, leak_pos=leak_pos,
         class_counts_test=np.bincount(y, minlength=len(cls)))

# --- condition matrices -----------------------------------------------------------------
XS = np.asarray(X[S], dtype=np.float32)
XIS, MIS = XI[S], MI[S]


def with_iat(new_iat64, rows):
    Z = XS[rows].copy()
    Z[:, iat] = new_iat64[rows].astype(np.float32)
    return Z


def shifted(off_full):
    Zi = XIS.copy()
    off = np.broadcast_to(off_full, (len(X),))[S] if np.ndim(off_full) else np.full(len(S), off_full)
    Zi[MIS] += np.repeat(off[:, None], len(iat), 1)[MIS]
    return Zi


rows_cond = np.sort(np.concatenate([leak_pos, sanity]))  # leaked rows + sanity rows
np.save(f"{OUT}/cond_baseline.npy", XS)
conds = {"plus_8y": shifted(EIGHT_YEARS), "plus_1d": shifted(86400.0)}
idx_full = np.flatnonzero(leaked)
for seed in range(5):  # identical construction to exp1.py
    perm = np.random.default_rng(seed).permutation(idx_full)
    off = np.zeros(len(X)); off[idx_full] = t_row[perm] - t_row[idx_full]
    conds[f"shuffle_s{seed}"] = shifted(off)
Zi = XIS.copy(); Zi[MIS] = 0.0
conds["zero_fixed_data_leaky_model"] = Zi
for k, Zi in conds.items():
    Z = with_iat(Zi, rows_cond)
    assert np.array_equal(Z[np.isin(rows_cond, sanity)], XS[sanity]), "sanity rows must be unmodified"
    np.save(f"{OUT}/cond_{k}.npy", Z)
np.save(f"{OUT}/cond_rows.npy", rows_cond)
print("conditions:", ["baseline"] + list(conds), "| rows per modified condition:", len(rows_cond))
