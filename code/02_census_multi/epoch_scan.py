"""Pass-1 epoch scan for a non-NTLFlowLyzer dataset: count values in the epoch range at s / ms / us scale per numeric column."""
import sys, json, pandas as pd, numpy as np
f = sys.argv[1]
R = {"s": (1.4e9, 2.2e9), "ms": (1.4e12, 2.2e12), "us": (1.4e15, 2.2e15)}
hits, ex, n, nonnum, labels = {}, {}, 0, {}, {}
for ch in pd.read_csv(f, chunksize=200_000, low_memory=False):
    n += len(ch)
    if "label" in ch: 
        for k, v in ch["label"].value_counts().items(): labels[str(k)] = labels.get(str(k), 0) + int(v)
    for c in ch.columns:
        s = ch[c]
        if not pd.api.types.is_numeric_dtype(s):
            nonnum.setdefault(c, [str(v) for v in s.dropna().unique()[:4]]); continue
        for k, (lo, hi) in R.items():
            m = (s >= lo) & (s <= hi)
            if m.any():
                hits[(c, k)] = hits.get((c, k), 0) + int(m.sum())
                ex.setdefault((c, k), [float(v) for v in s[m].head(3)])
print(f"rows {n}; labels {labels}")
print("epoch-range hits:" if hits else "epoch-range hits: NONE")
for (c, k), v in sorted(hits.items(), key=lambda kv: -kv[1]):
    e = ex[(c, k)]; div = {"s": 1, "ms": 1e3, "us": 1e6}[k]
    print(f"  {c} [{k}]: {v} rows, e.g. {e} -> {[str(pd.to_datetime(x / div, unit='s')) for x in e]}")
print("non-numeric columns:", {c: v for c, v in nonnum.items()})
