"""Feature cache for BCCC-cPacket-Cloud-DDoS-2024 (26-subtype `activity` target), row-aligned with exp2_activity/splits.npz.
Features: every numeric column except flow_id, src_ip, src_port, dst_ip, dst_port, timestamp, label, activity
(non-numeric columns such as protocol, delta_start, handshake_duration are excluded automatically); inf/NaN -> 0, float32."""
import glob, json, os
import numpy as np, pandas as pd
SRC = "/home/USER/Downloads/BCCC-cPacket-Cloud-DDoS-2024"
C = "/home/USER/Desktop/ntl_census_multi/BCCC-cPacket-Cloud-DDoS-2024/cache"
DROP = {"flow_id", "src_ip", "src_port", "dst_ip", "dst_port", "timestamp", "label", "activity"}
os.makedirs(C, exist_ok=True)
files = [f for f in sorted(glob.glob(f"{SRC}/**/*.csv", recursive=True)) if os.path.getsize(f) > 0]
hdr = list(pd.read_csv(files[0], nrows=0).columns)
probe = pd.read_csv(files[0], nrows=50_000, low_memory=False)
numeric = [c for c in hdr if c not in DROP and pd.api.types.is_numeric_dtype(probe[c])]
excluded_nonnum = [c for c in hdr if c not in DROP and c not in numeric]
n = sum(sum(1 for _ in open(f, "rb")) - 1 for f in files)
X = np.lib.format.open_memmap(f"{C}/X.npy.part", mode="w+", dtype=np.float32, shape=(n, len(numeric)))
lab, off = [], 0
for f in files:
    assert list(pd.read_csv(f, nrows=0).columns) == hdr
    for ch in pd.read_csv(f, chunksize=200_000, low_memory=False):
        F = ch[numeric].apply(pd.to_numeric, errors="coerce").replace([np.inf, -np.inf], np.nan).fillna(0)
        X[off:off + len(ch)] = F.to_numpy(dtype=np.float32)
        lab += (ch["label"].astype(str) + " / " + ch["activity"].astype(str)).tolist(); off += len(ch)
X.flush(); del X; os.replace(f"{C}/X.npy.part", f"{C}/X.npy")
classes = sorted(set(lab)); y = np.array([classes.index(l) for l in lab])
X = np.load(f"{C}/X.npy", mmap_mode="r")
iat = [i for i, c in enumerate(numeric) if "IAT" in c]
leaked = (np.asarray(X[:, iat], dtype=np.float64) > 1e9).any(1)
np.savez(f"{C}/meta.npz", y=y, leaked=leaked, pc=np.asarray(X[:, numeric.index("packets_count")]))
json.dump({"features": numeric, "excluded_non_numeric": excluded_nonnum, "classes": classes, "iat": iat}, open(f"{C}/meta.json", "w"))
sp = np.load("/home/USER/Desktop/ntl_census_multi/BCCC-cPacket-Cloud-DDoS-2024/exp2_activity/splits.npz")
assert max(sp[k].max() for k in sp.files) == n - 1 and len(sp["random_train"]) + len(sp["random_test"]) == n
print(f"cPacket cache: {n} x {len(numeric)} features, {len(classes)} classes, leaked {leaked.mean():.4f}; non-numeric excluded: {excluded_nonnum}")
