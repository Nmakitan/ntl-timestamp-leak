"""Build RESULTS.md for one census_multi.py output folder, and refresh COMBINED.md across datasets.
Usage: report_multi.py <out_dir> <dataset_name>
"""
import glob, json, os, sys
import numpy as np, pandas as pd

OUT, NAME = sys.argv[1], sys.argv[2]
ROOT = os.path.dirname(os.path.abspath(__file__))
parts = [json.load(open(p)) for p in sorted(glob.glob(f"{OUT}/parts/*.json"))]

# documented capture day per file (local date)
CIC17 = {"monday": "2017-07-03", "tuesday": "2017-07-04", "wednesday": "2017-07-05", "thursday": "2017-07-06",
         "friday": "2017-07-07", "ftp_patator": "2017-07-04", "ssh_patator": "2017-07-04", "dos_": "2017-07-05",
         "heartbleed": "2017-07-05", "web_": "2017-07-06", "botnet_ares": "2017-07-07", "portscan": "2017-07-07",
         "ddos_loit": "2017-07-07"}


def capture_day(tag):
    if NAME == "BCCC-CIC-IDS-2017":
        return next((d for k, d in CIC17.items() if tag.lower().startswith(k)), None)
    if NAME == "BCCC-cPacket-Cloud-DDoS-2024":
        return pd.to_datetime(tag.split("_", 1)[1].replace("_", " "), format="%d %b %Y").strftime("%Y-%m-%d")
    return None


order = ["n", "one_pkt", "fwd_leak", "bwd_leak", "comb_leak", "any_leak", "beyond", "fwd_rule_ok", "bwd_rule_ok", "comb_rule_ok"]
rows = [dict(file=p["file"], cls=k, **v) for p in parts for k, v in p["census"].items()]
pf = pd.DataFrame(rows).set_index(["file", "cls"]).sort_index()[order]
pf = pf.rename(index=lambda k: k.replace(" | ", " / "), level="cls")
pc = pf.groupby(level="cls").sum()
pc.loc["ALL"] = pc.sum()
for t in (pf, pc):
    for c in ("fwd", "bwd", "comb"):
        t[f"{c}_viol"] = t["n"] - t[f"{c}_rule_ok"]
    t["any_%"] = (100 * t["any_leak"] / t["n"]).round(2)
    t["beyond_%_of_leaked"] = (100 * t["beyond"] / t["any_leak"].where(t["any_leak"] > 0)).round(1)
pf.to_csv(f"{OUT}/per_file.csv"); pc.to_csv(f"{OUT}/per_class.csv")
viol = int(pc.loc["ALL", ["fwd_viol", "bwd_viol", "comb_viol"]].sum())

# dominant offset leaked - timestamp (gives local timezone)
offs = {}
for p in parts:
    for k, v in p["fwd_offset_vs_timestamp"].items():
        offs[k] = offs.get(k, 0) + v
off_s = pd.Series(offs, dtype="int64").sort_values(ascending=False)
dom = float(off_s.index[0]) if len(off_s) and off_s.index[0] != "nan" else 0.0
tz_h = round(dom / 3600)

# calendar: leaked values in local time vs documented capture day
cal, on_day, total = [], 0, 0
for p in parts:
    day = capture_day(p["file"])
    for k, hh in p["hours"].items():
        loc = pd.Series(hh)
        loc.index = (pd.to_datetime(loc.index, format="%Y-%m-%d %H") - pd.Timedelta(hours=tz_h)).strftime("%Y-%m-%d %H")
        days = loc.groupby(loc.index.str[:10]).sum()
        ok = int(days.get(day, 0)) if day else None
        lo, hi = p["range"][k]
        cal.append({"file": p["file"], "class": k.replace(" | ", " / "), "documented_day": day, "leaked_rows": int(loc.sum()),
                    "on_documented_day": ok, "local_days": " ".join(f"{d}:{int(v)}" for d, v in days.items()),
                    "local_first": (pd.to_datetime(lo, unit="s") - pd.Timedelta(hours=tz_h)).strftime("%Y-%m-%d %H:%M"),
                    "local_last": (pd.to_datetime(hi, unit="s") - pd.Timedelta(hours=tz_h)).strftime("%Y-%m-%d %H:%M")})
        if day:
            on_day += ok; total += int(loc.sum())
cal = pd.DataFrame(cal).sort_values(["local_first"]) if cal else pd.DataFrame()
cal.to_csv(f"{OUT}/leak_calendar.csv", index=False)

hits, nonnum = {}, {}
for p in parts:
    for c, k in p["range_hits"].items(): hits[c] = hits.get(c, 0) + k
    for c, v in p["non_numeric"].items(): nonnum.setdefault(c, v)

# ---------------- RESULTS.md ----------------
iatc = parts[0]["iat_columns"]
n_rows = int(pc.loc["ALL", "n"])
L = [f"# Leak census: {NAME}", "",
     f"NTLFlowLyzer output: **yes**. {len(parts)} non-empty CSV files, {parts[0]['n_columns']} columns, {n_rows:,} rows "
     f"(file list with sizes: `file_list.txt`). Class key: `label`" + (" + `activity`" if parts[0]["has_activity"] else "") + ".",
     f"IAT columns ({sum(len(v) for v in iatc.values())}): combined {iatc['combined']}; fwd {iatc['fwd']}; bwd {iatc['bwd']}.",
     "Counts: `packets_count`, `fwd_packets_count`, `bwd_packets_count`. Leak = IAT value > 1e9.", "",
     "## Per class", "",
     "| class | n | 1-packet | fwd leak | bwd leak | any leak | % | leak, >1 packet | % of leaked |", "|---|---:|---:|---:|---:|---:|---:|---:|---:|"]
for k, r in pc.iterrows():
    b = "**" if k == "ALL" else ""
    L.append(f"| {b}{k}{b} | {int(r.n):,} | {int(r.one_pkt):,} | {int(r.fwd_leak):,} | {int(r.bwd_leak):,} | {b}{int(r.any_leak):,}{b} | "
             f"{b}{r['any_%']:.2f}{b} | {int(r.beyond):,} | {'-' if pd.isna(r['beyond_%_of_leaked']) else r['beyond_%_of_leaked']} |")
L += ["", "## Rule check", "",
      f"fwd leak <=> fwd_packets_count == 1: {int(pc.loc['ALL', 'fwd_viol'])} violations; "
      f"bwd leak <=> bwd_packets_count == 1: {int(pc.loc['ALL', 'bwd_viol'])}; "
      f"combined leak <=> packets_count == 1: {int(pc.loc['ALL', 'comb_viol'])} (of {n_rows:,} rows).", "",
      "## Leaked value vs `timestamp` column", "",
      f"Most common offset (leaked fwd value − timestamp): **{off_s.index[0]} s** = {tz_h:+d} h, in "
      f"{100 * off_s.iloc[0] / off_s.sum():.2f}% of {int(off_s.sum()):,} leaked-fwd rows; top 5: "
      + ", ".join(f"{k}: {v:,}" for k, v in off_s.head(5).items()) + ".",
      f"So the `timestamp` column is local time (UTC{-tz_h:+d}) and the leaked IAT is the UTC epoch of the flow start.", "",
      "## Calendar (local time = UTC" + f"{-tz_h:+d}" + ") vs documented capture days", ""]
if total:
    L.append(f"Leaked rows on their file's documented capture day: **{on_day:,} of {total:,} ({100 * on_day / total:.2f}%)**.")
L += ["", "| file | class | documented day | leaked rows | on that day | first (local) | last (local) | local days |", "|---|---|---|---:|---:|---|---|---|"]
for _, r in cal.iterrows():
    L.append(f"| {r.file} | {r['class']} | {r.documented_day} | {r.leaked_rows:,} | {r.on_documented_day if r.on_documented_day is not None else '-'} | "
             f"{r.local_first} | {r.local_last} | {r.local_days} |")
L += ["", "## Non-IAT columns with values in 1.4e9..2.2e9", ""]
L += [f"- `{c}`: {v:,}" for c, v in sorted(hits.items(), key=lambda kv: -kv[1])] or ["- none"]
L += ["", "Non-numeric columns (samples): " + "; ".join(f"`{c}`: {v[:3]}" for c, v in nonnum.items() if c not in ("flow_id", "src_ip", "dst_ip"))]

shp = [dict(zip(["cls", "f", "b"], k.replace(" | ", " / ").split("||")), **v) for p in parts for k, v in p.get("shapes", {}).items()]
if shp:
    S = pd.DataFrame(shp).groupby(["cls", "f", "b"]).sum().reset_index()
    flags = [c for c in S.columns if c.endswith("_flag_counts")]
    S.to_csv(f"{OUT}/flow_shapes.csv", index=False)
    L += ["", "## Flow shapes per class (fwd/bwd packet counts capped at 3)", "",
          "Rows per (fwd, bwd) shape, share of the class, share leaked, and mean SYN/ACK/FIN/RST/PSH flag counts and total payload bytes per flow.", "",
          "| class | fwd | bwd | rows | % of class | % leaked | SYN | ACK | FIN | RST | PSH | payload B |", "|---|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|"]
    tot = S.groupby("cls")["n"].sum()
    for _, r in S.sort_values(["cls", "n"], ascending=[True, False]).iterrows():
        if r.n / tot[r.cls] < 0.005 and r.n < 50:
            continue
        L.append(f"| {r.cls} | {r.f} | {r.b} | {int(r.n):,} | {100 * r.n / tot[r.cls]:.1f} | {100 * r.leaked / r.n:.1f} | " +
                 " | ".join(f"{r[c] / r.n:.2f}" for c in ["syn_flag_counts", "ack_flag_counts", "fin_flag_counts", "rst_flag_counts", "psh_flag_counts"]) +
                 f" | {r.payload_sum / r.n:.0f} |")
    L += ["", "(Shapes with < 0.5% of a class and < 50 rows omitted; full table in `flow_shapes.csv`.)"]
open(f"{OUT}/RESULTS.md", "w").write("\n".join(L) + "\n")

# ---------------- combined row ----------------
row = {"dataset": NAME, "ntlflowlyzer": "yes", "columns": parts[0]["n_columns"], "rows": n_rows,
       "leaked_rows": int(pc.loc["ALL", "any_leak"]), "leaked_%": round(float(pc.loc["ALL", "any_%"]), 2),
       "rule_violations": viol, "timestamp_offset_h": tz_h,
       "on_capture_days": f"{100 * on_day / total:.2f}% of leaked rows" if total else "n/a"}
json.dump(row, open(f"{OUT}/combined_row.json", "w"), indent=1)
print("\n".join(L[:40]))
