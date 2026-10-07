"""Shared helpers for experiments 2 and 3.

Pool index space: rows [0, NTR) are the existing train set, rows [NTR, NTR+NTE) the existing (temporal) test set.
Leaked cell = IAT column (name contains "IAT") with value > 1e9, always judged on the UNMODIFIED data.
"""
import gc, json, os, resource, time
import numpy as np
from sklearn.metrics import accuracy_score, f1_score, precision_recall_fscore_support, confusion_matrix

D = os.environ.get("NTL23_DATA", "/home/USER/pew/Dataset/ml_module_output/_intermediate")
M = "/home/USER/trained_models"
HERE = os.environ.get("NTL23_OUT", os.path.dirname(os.path.abspath(__file__)))
CACHE = f"{HERE}/cache"
RES = f"{HERE}/results"
SPLIT_IDX = f"{HERE}/exp3/random_split_idx.npz"
LEAK = 1e9
CHUNK = 100_000

FEAT = json.load(open(f"{M}/feature_order.json"))
_lm = json.load(open(f"{M}/label_mapping.json"))
CLS = [_lm[str(i)] for i in range(len(_lm))]
LABELS = list(range(len(CLS)))
IAT = np.array([i for i, n in enumerate(FEAT) if "IAT" in n])
PC = FEAT.index("packets_count")


def arrays():
    TrX = np.load(f"{D}/train_X.npy", mmap_mode="r"); TrY = np.load(f"{D}/train_y.npy", mmap_mode="r")
    TeX = np.load(f"{D}/test_X.npy", mmap_mode="r"); TeY = np.load(f"{D}/test_y.npy", mmap_mode="r")
    assert TrX.shape[1] == TeX.shape[1] == len(FEAT)
    return TrX, TrY, TeX, TeY


def pool_meta():
    """Per pooled row: label, leaked (original data), t = smallest leaked IAT value (0 if none), packets_count."""
    f = f"{CACHE}/pool_meta.npz"
    if os.path.exists(f):
        return dict(np.load(f))
    TrX, TrY, TeX, TeY = arrays()
    ntr, nte = len(TrY), len(TeY)
    y = np.concatenate([np.asarray(TrY), np.asarray(TeY)]).astype(np.int64)
    leaked = np.zeros(ntr + nte, bool); t = np.zeros(ntr + nte); pc = np.zeros(ntr + nte)
    for src, base in ((TrX, 0), (TeX, ntr)):
        for i in range(0, len(src), CHUNK):
            blk = np.asarray(src[i:i + CHUNK])
            I = blk[:, IAT].astype(np.float64); m = I > LEAK
            sl = slice(base + i, base + i + len(blk))
            leaked[sl] = m.any(1)
            t[sl] = np.where(m.any(1), np.where(m, I, np.inf).min(1), 0.0)
            pc[sl] = blk[:, PC]
    os.makedirs(CACHE, exist_ok=True)
    np.savez(f + ".tmp.npz", y=y, leaked=leaked, t=t, pc=pc, ntr=ntr, nte=nte)
    os.replace(f + ".tmp.npz", f)
    return dict(np.load(f))


def split_indices(split, meta):
    ntr, nte = int(meta["ntr"]), int(meta["nte"])
    if split == "temporal":
        return np.arange(ntr), np.arange(ntr, ntr + nte)
    if split == "random":
        s = np.load(SPLIT_IDX)
        return s["train_idx"], s["test_idx"]
    raise ValueError(split)


def assemble(idx, ntr, fix):
    """Gather pooled rows `idx` (sorted) into one preallocated float32 array, chunk by chunk; zero leaked cells if fix."""
    TrX, _, TeX, _ = arrays()
    out = np.empty((len(idx), len(FEAT)), dtype=np.float32)
    for i in range(0, len(idx), CHUNK):
        part = idx[i:i + CHUNK]
        a, b = part[part < ntr], part[part >= ntr] - ntr
        blk = np.empty((len(part), len(FEAT)), dtype=np.float32)
        if len(a): blk[:len(a)] = TrX[a]
        if len(b): blk[len(a):] = TeX[b]
        if fix:
            I = blk[:, IAT]; I[I > LEAK] = 0.0; blk[:, IAT] = I
        out[i:i + len(part)] = blk
        del blk
    return out


def metrics(y, p, mask=None):
    if mask is not None:
        y, p = y[mask], p[mask]
    if len(y) == 0:
        return {"n": 0}
    pr, rc, f1, sup = precision_recall_fscore_support(y, p, labels=LABELS, zero_division=0)
    return {"n": int(len(y)), "accuracy": float(accuracy_score(y, p)),
            "macro_f1": float(f1_score(y, p, labels=LABELS, average="macro", zero_division=0)),
            "per_class": {c: {"precision": float(pr[i]), "recall": float(rc[i]), "f1": float(f1[i]),
                              "support": int(sup[i]), "correct": int(((y == i) & (p == i)).sum())}
                          for i, c in enumerate(CLS)},
            "confusion": confusion_matrix(y, p, labels=LABELS).tolist()}


def peak_rss_gb():
    return resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / 1e6


def write_new(path, obj):
    """Write JSON atomically; never overwrite an existing result."""
    if os.path.exists(path):
        raise FileExistsError(path)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path + ".tmp", "w") as f:
        json.dump(obj, f, indent=1)
    os.replace(path + ".tmp", path)
