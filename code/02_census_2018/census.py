"""Step 2 census: leaked epoch timestamps in IAT features of BCCC-CSE-CIC-IDS2018.

One chunked pass over every original per-day file computes:
  - per (file, label): n, 1-packet rows, fwd/bwd/combined/any leak, leak beyond ghosts, rule checks
  - per (file, label): min/max leaked value and an hourly (UTC) histogram of leaked values
  - offset between leaked fwd value and the row's `timestamp` column (is the leak the flow start time?)
  - per column: count of values in [1.4e9, 2.2e9] (second-leak-path scan) and non-numeric column samples
Results are written per file to out/parts/ so an interrupted run can resume.
"""
import os, sys, json, time, multiprocessing as mp
import numpy as np, pandas as pd
from common import list_files, open_csv, header, name

OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "out")
PARTS = os.path.join(OUT, "parts")
LEAK = 1e9
LO, HI = 1.4e9, 2.2e9
CHUNK = 100_000


def classify(cols):
    iat = [c for c in cols if "iat" in c.lower()]
    fwd = [c for c in iat if c.lower().startswith("fwd")]
    bwd = [c for c in iat if c.lower().startswith("bwd")]
    comb = [c for c in iat if c not in fwd and c not in bwd]
    return iat, fwd, bwd, comb


SCRATCH = "/tmp/claude-1000/-home-nik-pew/9491c7c3-7c6d-4932-9590-b57cabbbfdb0/scratchpad/fallback"


def fallback_copy(path):
    """Inner zip for a CSV, pulled from its day's outer zip onto the NVMe scratch dir."""
    import glob, subprocess
    want = name(path) + ".zip"
    for outer in glob.glob("/home/USER/pew/Dataset/*.zip") + glob.glob("/home/USER/Downloads/*.zip"):
        entries = subprocess.run(["unzip", "-Z1", outer], capture_output=True, text=True).stdout.split()
        hit = [e for e in entries if e.endswith("/" + want)]
        if hit:
            os.makedirs(SCRATCH, exist_ok=True)
            subprocess.run(["unzip", "-o", "-j", "-q", outer, hit[0], "-d", SCRATCH], check=True)
            return os.path.join(SCRATCH, want), outer
    raise FileNotFoundError(f"no zip copy of {want}")


def process(path):
    tag = name(path)
    part = os.path.join(PARTS, tag + ".json")
    if os.path.exists(part):
        return tag, "cached"
    try:
        return scan(path, tag, part, source=path)
    except OSError as e:
        err = f"{type(e).__name__}: {e}"
    try:
        alt, outer = fallback_copy(path)
        try:
            return scan(alt, tag, part, source=f"{outer} -> {name(path)}.zip (primary failed: {err})")
        finally:
            os.remove(alt)
    except Exception as e2:
        with open(os.path.join(PARTS, tag + ".FAILED"), "w") as f:
            f.write(f"primary: {err}\nfallback: {type(e2).__name__}: {e2}\n")
        return tag, "FAILED"


def scan(path, tag, part, source):
    t0 = time.time()
    cols = header(path)
    iat, fwd, bwd, comb = classify(cols)
    census, rng, hours, offs = {}, {}, {}, {}
    range_hits = {}
    nonnum = {}
    with open_csv(path, check=True) as fh:
        for ch in pd.read_csv(fh, chunksize=CHUNK, low_memory=False):
            # second-leak-path scan over every numeric column
            for c in ch.columns:
                s = ch[c]
                if pd.api.types.is_numeric_dtype(s):
                    k = int(((s >= LO) & (s <= HI)).sum())
                    if k:
                        range_hits[c] = range_hits.get(c, 0) + k
                elif c not in nonnum:
                    nonnum[c] = [str(v) for v in s.dropna().unique()[:5]]
            x = ch[iat].apply(pd.to_numeric, errors="coerce")
            pc, fc, bc = (pd.to_numeric(ch[c], errors="coerce") for c in
                          ("packets_count", "fwd_packets_count", "bwd_packets_count"))
            fl = (x[fwd] > LEAK).any(axis=1)
            bl = (x[bwd] > LEAK).any(axis=1)
            cl = (x[comb] > LEAK).any(axis=1)
            al = (x > LEAK).any(axis=1)
            d = pd.DataFrame({
                "label": ch["label"].astype(str),
                "one_pkt": pc == 1,
                "fwd_leak": fl, "bwd_leak": bl, "comb_leak": cl, "any_leak": al,
                "beyond": al & (pc > 1),
                "fwd_rule_ok": fl == (fc == 1),
                "bwd_rule_ok": bl == (bc == 1),
                "comb_rule_ok": cl == (pc == 1),
            })
            g = d.groupby("label")
            agg = g.sum()
            agg["n"] = g.size()
            for lab, row in agg.iterrows():
                acc = census.setdefault(lab, {})
                for k, v in row.items():
                    acc[k] = acc.get(k, 0) + int(v)

            # leaked values: range and UTC-hour histogram (max over IAT cols = the leaked epoch)
            lv = x.where(x > LEAK).max(axis=1)
            m = lv.notna()
            if m.any():
                lab_l, v_l = d.loc[m, "label"], lv[m]
                for lab, vv in v_l.groupby(lab_l):
                    r = rng.setdefault(lab, [np.inf, -np.inf])
                    r[0], r[1] = min(r[0], float(vv.min())), max(r[1], float(vv.max()))
                    hh = pd.to_datetime(vv, unit="s", utc=True).dt.strftime("%Y-%m-%d %H")
                    h = hours.setdefault(lab, {})
                    for k, v in hh.value_counts().items():
                        h[k] = h.get(k, 0) + int(v)

            # leaked fwd value vs the row's timestamp column (naive, read as if UTC)
            fv = x[fwd].where(x[fwd] > LEAK).max(axis=1)
            mf = fv.notna()
            if mf.any():
                ts = pd.to_datetime(ch.loc[mf, "timestamp"], format="ISO8601", errors="coerce")
                ts_epoch = (ts - pd.Timestamp("1970-01-01")) / pd.Timedelta(seconds=1)
                off = (fv[mf] - ts_epoch).round(3)
                for k, v in off.value_counts(dropna=False).items():
                    key = "nan" if pd.isna(k) else repr(float(k))
                    offs[key] = offs.get(key, 0) + int(v)

    res = {"file": tag, "path": path, "source": source, "seconds": round(time.time() - t0, 1),
           "census": census, "range": {k: list(v) for k, v in rng.items()}, "hours": hours,
           "fwd_offset_vs_timestamp": offs, "range_hits": range_hits, "non_numeric": nonnum}
    tmp = part + ".tmp"
    with open(tmp, "w") as f:
        json.dump(res, f)
    os.replace(tmp, part)
    return tag, res["seconds"]


if __name__ == "__main__":
    os.makedirs(PARTS, exist_ok=True)
    files = list_files()
    with open(os.path.join(OUT, "file_list.txt"), "w") as f:
        for p in files:
            f.write(f"{os.path.getsize(p)}\t{p}\n")
    files.sort(key=os.path.getsize, reverse=True)  # big ones first for better packing
    workers = int(sys.argv[1]) if len(sys.argv) > 1 else 2
    with mp.Pool(workers, maxtasksperchild=1) as pool:
        for tag, sec in pool.imap_unordered(process, files):
            print(f"done {tag} ({sec}s)", flush=True)
    print("ALL DONE", flush=True)
