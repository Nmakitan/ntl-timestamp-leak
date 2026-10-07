"""Shared data access for the three-dataset model comparison (spec: timestamp-leak susceptibility across ML models).

Datasets: d2018 (BCCC-CSE-CIC-IDS2018), d2017 (BCCC-CIC-IDS-2017), cpacket (BCCC-cPacket-Cloud-DDoS-2024, 26-subtype target).
Leaked cell = IAT column value > 1e9, judged on the unmodified data.
"""
import json, os, sys
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
RES = f"{HERE}/results"
LEAK, SHIFT, CHUNK, SUB_N, SMALL = 1e9, 252_460_800.0, 100_000, 600_000, 1000
DATASETS = ("d2018", "d2017", "cpacket")
MULTI = os.environ.get("NTL_MULTI", "/home/USER/Desktop/ntl_census_multi")  # override on machines with another user
# The USB data drive has been mounted at both ~/pew and ~/pew2; use whichever is live (override with NTL_DRIVE).
DRIVE = os.environ.get("NTL_DRIVE") or next(
    (d for d in ("/home/USER/pew", "/home/USER/pew2") if os.path.isdir(f"{d}/Dataset/ml_module_output/_intermediate")), None)
if DRIVE:  # only the 2018 data lives on the drive; 2017/cPacket runs work without it (e.g. on a second machine)
    os.environ.setdefault("NTL23_DATA", f"{DRIVE}/Dataset/ml_module_output/_intermediate")


class Data:
    """X rows are addressed by a dataset-wide index; take(idx) returns float32 rows."""

    def __init__(self, name):
        self.name = name
        if name == "d2018":
            assert DRIVE, "USB data drive not mounted"
            sys.path.insert(0, "/home/USER/Desktop/ntl_exp23")
            import common23 as c
            self.c = c
            self.meta = c.pool_meta()
            self.y, self.leaked, self.pc = self.meta["y"], self.meta["leaked"], self.meta["pc"]
            self.ntr = int(self.meta["ntr"])
            self.features = c.FEAT
            self.classes = c.CLS
            self.iat = np.asarray(c.IAT)
            self.TrX, _, self.TeX, _ = c.arrays()
        else:
            base = f"{MULTI}/BCCC-CIC-IDS-2017" if name == "d2017" else f"{MULTI}/BCCC-cPacket-Cloud-DDoS-2024"
            cache = f"{base}/exp3/cache" if name == "d2017" else f"{base}/cache"
            m = json.load(open(f"{cache}/meta.json")); z = np.load(f"{cache}/meta.npz")
            self.X = np.load(f"{cache}/X.npy", mmap_mode="r")
            self.y, self.leaked, self.pc = z["y"], z["leaked"], z["pc"]
            self.features, self.classes, self.iat = m["features"], m["classes"], np.asarray(m["iat"])
            self.splitfile = f"{base}/exp2_label/splits.npz" if name == "d2017" else f"{base}/exp2_activity/splits.npz"

    def split(self, split):
        if self.name == "d2018":
            return self.c.split_indices(split, self.meta)
        # lodo_<MMDD>: leave-one-day-out (d2017 only), built by mc_lodo_splits.py
        s = np.load(f"{MULTI}/BCCC-CIC-IDS-2017/lodo/splits.npz" if split.startswith("lodo_") else self.splitfile)
        return s[f"{split}_train"], s[f"{split}_test"]

    def take(self, idx):
        idx = np.sort(idx) if not np.all(np.diff(idx) >= 0) else idx
        if self.name == "d2018":
            # The 2018 arrays sit on a USB NTFS (FUSE) drive: fancy indexing a memmap there becomes 4 KB random reads
            # (~28 MB/s). Read large sequential blocks instead and keep the wanted rows.
            a, b = idx[idx < self.ntr], idx[idx >= self.ntr] - self.ntr
            return np.concatenate([self._blocks(self.TrX, a), self._blocks(self.TeX, b)])
        return np.asarray(self.X[idx], dtype=np.float32)

    def take_modified(self, idx, how, B=262_144):
        """take(idx) with modify(..., how) applied block by block, so the unmodified full matrix never sits beside a
        modified copy (full 2018 training split: 3.26M x 313 float32 = 4.1 GB; two of those exceed the 6.5 GB cap)."""
        idx = np.sort(idx)
        ncol = len(self.features) - (len(self.iat) if how == "drop" else 0)
        out = np.empty((len(idx), ncol), dtype=np.float32)
        srcs = ([(self.TrX, idx[idx < self.ntr]), (self.TeX, idx[idx >= self.ntr] - self.ntr)]
                if self.name == "d2018" else [(self.X, idx)])
        k = 0
        for src, rows in srcs:
            for start in range(0, len(src), B):
                sel = rows[(rows >= start) & (rows < start + B)]
                if len(sel):
                    out[k:k + len(sel)] = modify(np.asarray(src[start:start + B], dtype=np.float32)[sel - start], self.iat, how)
                    k += len(sel)
        assert k == len(idx)
        return out

    @staticmethod
    def _blocks(src, rows, B=262_144):
        out = np.empty((len(rows), src.shape[1]), dtype=np.float32)
        k = 0
        for start in range(0, len(src), B):
            sel = rows[(rows >= start) & (rows < start + B)]
            if len(sel):
                blk = np.asarray(src[start:start + B])
                out[k:k + len(sel)] = blk[sel - start]; k += len(sel)
                del blk
        assert k == len(rows)
        return out

    def is_attack(self, c):
        return c.startswith("Attack") if self.name == "cpacket" else c != "Benign"


def subsample(data, split):
    """600k stratified by class; every row of classes with < 1,000 training rows; all rows if train < 600k.
    Cached per dataset x split so every model uses the same rows."""
    f = f"{RES}/subsamples/{data.name}_{split}.npz"
    if os.path.exists(f):
        return np.load(f)["idx"]
    tr, _ = data.split(split)
    if len(tr) <= SUB_N:
        idx = np.sort(tr)
    else:
        rng = np.random.default_rng(0)
        ytr = data.y[tr]
        cls, cnt = np.unique(ytr, return_counts=True)
        small = cls[cnt < SMALL]
        forced = tr[np.isin(ytr, small)]
        rest_mask = ~np.isin(ytr, small)
        budget = SUB_N - len(forced)
        rest_total = rest_mask.sum()
        parts = [forced]
        for k in cls[cnt >= SMALL]:
            pool = tr[ytr == k]
            q = int(round(budget * len(pool) / rest_total))
            parts.append(rng.choice(pool, size=min(q, len(pool)), replace=False))
        idx = np.sort(np.concatenate(parts))
    os.makedirs(os.path.dirname(f), exist_ok=True)
    yc = data.y[idx]
    counts = {data.classes[k]: int((yc == k).sum()) for k in range(len(data.classes))}
    np.savez(f, idx=idx)
    json.dump({"dataset": data.name, "split": split, "n": int(len(idx)), "train_rows": int(len(tr)),
               "class_counts": counts}, open(f.replace(".npz", ".json"), "w"), indent=1)
    return idx


def modify(Z, iat, how):
    """how: None | 'fix' / 'zero' (leaked IAT cells -> 0) | 'shift' (+8 years) | 'drop' (remove every IAT column).
    Arithmetic in float64, back to float32."""
    if how is None:
        return Z
    if how == "drop":
        return np.delete(Z, iat, axis=1)
    I = Z[:, iat].astype(np.float64)
    m = I > LEAK
    I[m] = 0.0 if how in ("fix", "zero") else I[m] + SHIFT
    Z = Z.copy(); Z[:, iat] = I.astype(np.float32)
    return Z


CACHE2018 = f"{DRIVE}/ntl_models_cache"  # on the USB drive (81 GB free); the NVMe is nearly full


def get_xy(data, split, which):
    """which = 'train' (the cached subsample) or 'test' (full test split). Returns (sorted row index, float32 X).
    For 2018 the matrices are materialised once as contiguous .npy files so each run reads them sequentially."""
    idx = subsample(data, split) if which == "train" else np.sort(data.split(split)[1])
    if data.name != "d2018":
        return idx, data.take(idx)
    f = f"{CACHE2018}/d2018_{split}_{which}.npy"
    if not os.path.exists(f):
        os.makedirs(CACHE2018, exist_ok=True)
        X = data.take(idx)
        np.save(f + ".part.npy", X); os.replace(f + ".part.npy", f)
        np.save(f.replace(".npy", "_idx.npy"), idx)
        return idx, X
    assert np.array_equal(np.load(f.replace(".npy", "_idx.npy")), idx), f"stale cache {f}"
    return idx, np.load(f)
