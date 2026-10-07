"""Pass 2 leak census for an NTLFlowLyzer-built dataset (generalised from ~/Desktop/ntl_census_step2/census.py).

Usage: census_multi.py <dataset_dir> <out_dir> [--shapes] [--workers N]
Columns are detected by pattern: IAT = name contains "IAT"; fwd/bwd = IAT names starting with fwd/bwd; combined = the rest.
Class key = `label`, plus `activity` when that column exists ("label | activity").
Per (file, class): n, 1-packet, fwd/bwd/combined/any leak, leak with >1 packet, rule checks, leaked-value range and UTC
hours, leaked-fwd-minus-timestamp offsets, epoch-range hits in every numeric non-IAT column, non-numeric samples.
--shapes: flow-shape breakdown per class by (fwd, bwd) packet counts capped at 3, with leak share and mean flags/payload.
"""
import glob, json, os, sys, time, multiprocessing as mp
import numpy as np, pandas as pd

LEAK, LO, HI, CHUNK = 1e9, 1.4e9, 2.2e9, 100_000
FLAGS = ["syn_flag_counts", "ack_flag_counts", "fin_flag_counts", "rst_flag_counts", "psh_flag_counts"]
args = [a for a in sys.argv[1:] if not a.startswith("--")]
SRC, OUT = args[0], args[1]
SHAPES = "--shapes" in sys.argv
WORKERS = int(sys.argv[sys.argv.index("--workers") + 1]) if "--workers" in sys.argv else 2
PARTS = f"{OUT}/parts"


def columns(header):
    iat = [c for c in header if "IAT" in c]
    fwd = [c for c in iat if c.lower().startswith("fwd")]
    bwd = [c for c in iat if c.lower().startswith("bwd")]
    comb = [c for c in iat if c not in fwd and c not in bwd]
    return iat, fwd, bwd, comb


def add(d, k, v):
    d[k] = d.get(k, 0) + v


def process(path):
    tag = os.path.splitext(os.path.basename(path))[0]
    part = f"{PARTS}/{tag}.json"
    if os.path.exists(part):
        return tag, "cached"
    t0 = time.time()
    header = list(pd.read_csv(path, nrows=0).columns)
    iat, fwd, bwd, comb = columns(header)
    has_act = "activity" in header
    census, rng, hours, offs, range_hits, nonnum, shapes = {}, {}, {}, {}, {}, {}, {}
    for ch in pd.read_csv(path, chunksize=CHUNK, low_memory=False):
        for c in ch.columns:
            s = ch[c]
            if pd.api.types.is_numeric_dtype(s):
                if c not in iat:
                    k = int(((s >= LO) & (s <= HI)).sum())
                    if k: add(range_hits, c, k)
            elif c not in nonnum:
                nonnum[c] = [str(v) for v in s.dropna().unique()[:5]]
        key = ch["label"].astype(str)
        if has_act:
            key = key + " | " + ch["activity"].astype(str)
        x = ch[iat].apply(pd.to_numeric, errors="coerce")
        pc, fc, bc = (pd.to_numeric(ch[c], errors="coerce") for c in ("packets_count", "fwd_packets_count", "bwd_packets_count"))
        fl, bl, cl, al = ((x[cols] > LEAK).any(axis=1) for cols in (fwd, bwd, comb, iat))
        d = pd.DataFrame({"key": key, "one_pkt": pc == 1, "fwd_leak": fl, "bwd_leak": bl, "comb_leak": cl,
                          "any_leak": al, "beyond": al & (pc > 1), "fwd_rule_ok": fl == (fc == 1),
                          "bwd_rule_ok": bl == (bc == 1), "comb_rule_ok": cl == (pc == 1)})
        g = d.groupby("key"); agg = g.sum(); agg["n"] = g.size()
        for k, row in agg.iterrows():
            acc = census.setdefault(k, {})
            for col, v in row.items(): add(acc, col, int(v))
        lv = x.where(x > LEAK).max(axis=1); m = lv.notna()
        if m.any():
            for k, vv in lv[m].groupby(key[m]):
                r = rng.setdefault(k, [np.inf, -np.inf]); r[0], r[1] = min(r[0], float(vv.min())), max(r[1], float(vv.max()))
                h = hours.setdefault(k, {})
                for hh, v in pd.to_datetime(vv, unit="s", utc=True).dt.strftime("%Y-%m-%d %H").value_counts().items(): add(h, hh, int(v))
        fv = x[fwd].where(x[fwd] > LEAK).max(axis=1); mf = fv.notna()
        if mf.any():
            ts = pd.to_datetime(ch.loc[mf, "timestamp"], format="ISO8601", errors="coerce")
            off = (fv[mf] - (ts - pd.Timestamp("1970-01-01")) / pd.Timedelta(seconds=1)).round(3)
            for k, v in off.value_counts(dropna=False).items(): add(offs, "nan" if pd.isna(k) else repr(float(k)), int(v))
        if SHAPES:
            sh = pd.DataFrame({"key": key, "f": fc.clip(upper=3).astype("Int64").astype(str).replace("3", "3+"),
                               "b": bc.clip(upper=3).astype("Int64").astype(str).replace("3", "3+"), "leak": al,
                               "payload": pd.to_numeric(ch["total_payload_bytes"], errors="coerce"),
                               **{fl_: pd.to_numeric(ch[fl_], errors="coerce") for fl_ in FLAGS if fl_ in ch}})
            for (k, f_, b_), grp in sh.groupby(["key", "f", "b"]):
                s_ = shapes.setdefault(f"{k}||{f_}||{b_}", {"n": 0, "leaked": 0, "payload_sum": 0.0, **{fl_: 0.0 for fl_ in FLAGS}})
                s_["n"] += len(grp); s_["leaked"] += int(grp["leak"].sum()); s_["payload_sum"] += float(grp["payload"].sum())
                for fl_ in FLAGS:
                    if fl_ in grp: s_[fl_] += float(grp[fl_].sum())
    res = {"file": tag, "path": path, "seconds": round(time.time() - t0, 1), "n_columns": len(header),
           "iat_columns": {"fwd": fwd, "bwd": bwd, "combined": comb}, "has_activity": has_act,
           "census": census, "range": {k: list(v) for k, v in rng.items()}, "hours": hours,
           "fwd_offset_vs_timestamp": offs, "range_hits": range_hits, "non_numeric": nonnum, "shapes": shapes}
    with open(part + ".tmp", "w") as f: json.dump(res, f)
    os.replace(part + ".tmp", part)
    return tag, res["seconds"]


if __name__ == "__main__":
    os.makedirs(PARTS, exist_ok=True)
    files = sorted((f for f in glob.glob(f"{SRC}/**/*.csv", recursive=True) if os.path.getsize(f) > 0), key=os.path.getsize, reverse=True)
    with open(f"{OUT}/file_list.txt", "w") as f:
        for p in sorted(glob.glob(f"{SRC}/**/*.csv", recursive=True)):
            f.write(f"{os.path.getsize(p)}\t{p}\n")
    with mp.Pool(WORKERS, maxtasksperchild=1) as pool:
        for tag, sec in pool.imap_unordered(process, files):
            print(f"done {tag} ({sec}s)", flush=True)
    print("ALL DONE", flush=True)
