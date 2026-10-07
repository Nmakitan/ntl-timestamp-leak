"""Rebuild train_X.npy / train_y.npy from combined_train.csv with the same logic as train_ml_module.load_xy
(float32 features in feature_order.json order, labels via label_mapping.json), written to a memmap.
First verifies the method by re-deriving test_X/test_y from combined_test.csv and comparing to the existing .npy.
Never overwrites: refuses to run if the targets already exist.
"""
import json, os, sys, time
import numpy as np, pandas as pd

D = "/home/USER/pew/Dataset/ml_module_output/_intermediate"
M = "/home/USER/trained_models"
CHUNK = 100_000
feat = json.load(open(f"{M}/feature_order.json"))
lab = {v: int(k) for k, v in json.load(open(f"{M}/label_mapping.json")).items()}
dtype_map = {c: "float32" for c in feat}; dtype_map["label"] = "str"


def chunks(path):
    for ch in pd.read_csv(path, dtype=dtype_map, chunksize=CHUNK, usecols=feat + ["label"]):
        X = ch[feat].to_numpy(dtype=np.float32, copy=False)
        y = ch["label"].map(lab)
        if y.isna().any():
            sys.exit(f"unmapped labels in {path}: {set(ch['label'][y.isna()])}")
        yield X, y.to_numpy(dtype=np.int64)


# 1) verify method against existing test arrays
t0 = time.time()
TX, Ty = np.load(f"{D}/test_X.npy", mmap_mode="r"), np.load(f"{D}/test_y.npy", mmap_mode="r")
off = 0
for X, y in chunks(f"{D}/combined_test.csv"):
    n = len(y)
    same_x = np.array_equal(X, TX[off:off + n], equal_nan=True)
    if not (same_x and np.array_equal(y, Ty[off:off + n])):
        sys.exit(f"TEST VERIFY FAILED at rows {off}-{off + n}: X equal={same_x}")
    off += n
if off != len(Ty):
    sys.exit(f"TEST VERIFY FAILED: {off} rows vs {len(Ty)}")
print(f"test verify OK: {off} rows identical ({time.time() - t0:.0f}s)", flush=True)

# 2) build train arrays
out_X, out_y = f"{D}/train_X.npy", f"{D}/train_y.npy"
if os.path.exists(out_X) or os.path.exists(out_y):
    sys.exit("train_X.npy / train_y.npy already exist - not overwriting")
n_rows = sum(1 for _ in open(f"{D}/combined_train.csv", "rb")) - 1
print(f"train rows: {n_rows}", flush=True)
Xm = np.lib.format.open_memmap(out_X + ".part", mode="w+", dtype=np.float32, shape=(n_rows, len(feat)))
ym = np.empty(n_rows, dtype=np.int64)
off = 0
for X, y in chunks(f"{D}/combined_train.csv"):
    Xm[off:off + len(y)] = X; ym[off:off + len(y)] = y; off += len(y)
    if (off // CHUNK) % 5 == 0:
        print(f"  {off}/{n_rows} {time.time() - t0:.0f}s", flush=True)
assert off == n_rows, (off, n_rows)
Xm.flush(); del Xm
np.save(out_y + ".part.npy", ym)
os.replace(out_X + ".part", out_X); os.replace(out_y + ".part.npy", out_y)
print("class counts:", {k: int((ym == v).sum()) for k, v in lab.items()})
print(f"BUILD OK {n_rows} rows ({time.time() - t0:.0f}s)", flush=True)
