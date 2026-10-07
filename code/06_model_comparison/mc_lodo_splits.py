"""Leave-one-day-out splits for d2017 -> <MULTI>/BCCC-CIC-IDS-2017/lodo/splits.npz (keys lodo_<MMDD>_train / _test).

Row -> day from row order: the cache holds the CSVs in sorted path order, rows in file order (exp3_2017.py), so file
row counts (per_file.csv) give contiguous row ranges, and leak_calendar.csv gives each file's capture day.
Check: every attack file's rows carry exactly that file's class in the cache labels.
"""
import json, os
import numpy as np, pandas as pd
from mc_common import MULTI

B = f"{MULTI}/BCCC-CIC-IDS-2017"
y = np.load(f"{B}/exp3/cache/meta.npz")["y"]
classes = json.load(open(f"{B}/exp3/cache/meta.json"))["classes"]
pf = pd.read_csv(f"{B}/per_file.csv")[["file", "cls", "n"]]
cal = pd.read_csv(f"{B}/leak_calendar.csv")[["file", "documented_day"]]
pf = pf.merge(cal, on="file", how="left")
assert pf.documented_day.notna().all(), pf[pf.documented_day.isna()]
pf = pf.iloc[sorted(range(len(pf)), key=lambda i: pf.file[i] + ".csv")].reset_index(drop=True)  # sorted path order
assert pf.n.sum() == len(y), (pf.n.sum(), len(y))

day = np.empty(len(y), dtype="U10")
off = 0
for r in pf.itertuples():
    seg = y[off:off + r.n]
    got = {classes[k] for k in np.unique(seg)}
    assert got == {r.cls}, f"{r.file}: rows {off}-{off + r.n} have labels {got}, expected {r.cls}"
    day[off:off + r.n] = r.documented_day
    off += r.n

idx = np.arange(len(y))
out = {}
for d in sorted(set(day)):
    k = "lodo_" + d[5:7] + d[8:10]
    out[f"{k}_train"], out[f"{k}_test"] = idx[day != d], idx[day == d]
    te_cls = sorted({classes[c] for c in np.unique(y[day == d])})
    print(f"{k}: train {(day != d).sum():>9,}  test {(day == d).sum():>9,}  test classes {te_cls}")
os.makedirs(f"{B}/lodo", exist_ok=True)
np.savez(f"{B}/lodo/splits.npz", **out)
print(f"wrote {B}/lodo/splits.npz")
