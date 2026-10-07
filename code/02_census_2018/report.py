"""Aggregate out/parts/*.json into the Step 2 tables (written to out/)."""
import glob, json, os
import pandas as pd

OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "out")
parts = [json.load(open(p)) for p in sorted(glob.glob(f"{OUT}/parts/*.json"))]
failed = sorted(glob.glob(f"{OUT}/parts/*.FAILED"))

# --- per-file and per-class census -------------------------------------------------------
rows = [dict(file=p["file"], label=lab, **v) for p in parts for lab, v in p["census"].items()]
pf = pd.DataFrame(rows).set_index(["file", "label"]).sort_index()
order = ["n", "one_pkt", "fwd_leak", "bwd_leak", "comb_leak", "any_leak", "beyond",
         "fwd_rule_ok", "bwd_rule_ok", "comb_rule_ok"]
pf = pf[order]


def finish(t):
    t = t.copy()
    for c in ["fwd_rule_ok", "bwd_rule_ok", "comb_rule_ok"]:
        t[c.replace("_ok", "_viol")] = t["n"] - t[c]
    for c in ["one_pkt", "fwd_leak", "bwd_leak", "any_leak", "beyond"]:
        t[c + "_%"] = (100 * t[c] / t["n"]).round(2)
    t["beyond_share_of_leak_%"] = (100 * t["beyond"] / t["any_leak"].where(t["any_leak"] > 0)).round(2)
    return t


pf = finish(pf)
pc = finish(pf[order].groupby(level="label").sum())
tot = finish(pf[order].sum().to_frame("ALL").T)
pf.to_csv(f"{OUT}/per_file.csv")
pd.concat([pc, tot]).to_csv(f"{OUT}/per_class.csv")

# --- leaked value ranges vs capture calendar --------------------------------------------
rr = []
for p in parts:
    for lab, (lo, hi) in p["range"].items():
        hrs = p["hours"].get(lab, {})
        days = sorted({h[:10] for h in hrs})
        rr.append(dict(file=p["file"], label=lab,
                       min_utc=pd.to_datetime(lo, unit="s", utc=True), max_utc=pd.to_datetime(hi, unit="s", utc=True),
                       leaked_rows=sum(hrs.values()), utc_days=" ".join(days),
                       rows_off_main_day=sum(v for h, v in hrs.items() if days and h[:10] != max(
                           days, key=lambda d: sum(c for k, c in hrs.items() if k[:10] == d))),
                       first_hour=min(hrs) if hrs else "", last_hour=max(hrs) if hrs else ""))
ranges = pd.DataFrame(rr).sort_values(["min_utc"])
ranges.to_csv(f"{OUT}/leak_date_ranges.csv", index=False)
hours = pd.DataFrame([dict(file=p["file"], label=lab, utc_hour=h, rows=v)
                      for p in parts for lab, hh in p["hours"].items() for h, v in hh.items()])
hours.sort_values(["file", "label", "utc_hour"]).to_csv(f"{OUT}/leak_hours.csv", index=False)

# --- leaked fwd value minus `timestamp` column ------------------------------------------
oo = []
for p in parts:
    s = pd.Series(p["fwd_offset_vs_timestamp"], dtype="int64")
    if s.empty:
        continue
    top = s.sort_values(ascending=False)
    oo.append(dict(file=p["file"], rows=int(s.sum()),
                   top_offset_s=top.index[0], top_offset_rows=int(top.iloc[0]),
                   top_share_pct=round(100 * top.iloc[0] / s.sum(), 3),
                   distinct_offsets=len(s), top5=", ".join(f"{k}:{v}" for k, v in top.head(5).items())))
pd.DataFrame(oo).to_csv(f"{OUT}/fwd_leak_offset_vs_timestamp.csv", index=False)

# --- full-column scan -------------------------------------------------------------------
hits = {}
for p in parts:
    for c, k in p["range_hits"].items():
        hits[c] = hits.get(c, 0) + k
scan = pd.DataFrame(sorted(hits.items(), key=lambda kv: -kv[1]), columns=["column", "values_in_1.4e9_2.2e9"])
scan["is_IAT"] = scan.column.str.contains("iat", case=False)
scan.to_csv(f"{OUT}/column_scan.csv", index=False)
nonnum = {}
for p in parts:
    for c, vals in p["non_numeric"].items():
        nonnum.setdefault(c, set()).update(vals)
json.dump({c: sorted(v)[:15] for c, v in nonnum.items()}, open(f"{OUT}/non_numeric_samples.json", "w"), indent=1)

# --- console summary --------------------------------------------------------------------
pd.set_option("display.width", 250); pd.set_option("display.max_columns", 40); pd.set_option("display.max_rows", 200)
print(f"{len(parts)} files scanned, {len(failed)} failed: {[os.path.basename(f) for f in failed]}")
print("fallback used:", [p["file"] for p in parts if p["source"] != p["path"]])
show = ["n", "one_pkt", "one_pkt_%", "fwd_leak", "fwd_leak_%", "bwd_leak", "bwd_leak_%", "any_leak", "any_leak_%",
        "beyond", "beyond_%", "beyond_share_of_leak_%", "fwd_rule_viol", "bwd_rule_viol", "comb_rule_viol"]
print("\nPER CLASS\n", pd.concat([pc, tot])[show].to_string())
print("\nLEAK DATE RANGES\n", ranges.to_string(index=False))
print("\nFWD LEAK - timestamp\n", pd.DataFrame(oo).to_string(index=False))
print("\nCOLUMN SCAN\n", scan.to_string(index=False))
print("\nNON-NUMERIC\n", json.dumps({c: sorted(v)[:6] for c, v in nonnum.items()}, indent=1))
