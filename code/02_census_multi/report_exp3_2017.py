"""Build the 2017 retrain section (markdown) from BCCC-CIC-IDS-2017/exp3/*.json -> exp3/RESULTS_exp3_2017.md"""
import glob, json, os
import numpy as np

B = "/home/USER/Desktop/ntl_census_multi/BCCC-CIC-IDS-2017/exp3"
R = {(r["split"], r["variant"]): r for r in (json.load(open(f)) for f in glob.glob(f"{B}/*_s0.json"))}
M = json.load(open(f"{B}/cache/meta.json"))
CLS = M["classes"]
order = [k for k in [(s, v) for s in ("random", "temporal") for v in ("leaky", "fixA", "fixB")] if k in R]
f3 = lambda x: "-" if x is None else f"{x:.3f}"

L = ["## 11. Replication on BCCC-CIC-IDS-2017: single-seed 2 × 2 retrain", "",
     f"All 18 CSVs, {R[order[0]]['n_train'] + R[order[0]]['n_test']:,} rows, **{M['features'].__len__()} features**: every numeric column except "
     "`flow_id`, `src_ip`, `src_port`, `dst_ip`, `dst_port`, `timestamp`, `protocol` (text) and `label`; inf/NaN -> 0, float32 "
     "(full list: `BCCC-CIC-IDS-2017/exp3/cache/meta.json`). No class capping (memory estimate: 1.1 GB full matrix, "
     "0.83 GB training subset). Splits = the Experiment 2 splits for 2017 (`exp2_label/splits.npz`): random = stratified "
     "75/25, random_state=0; temporal = latest 25% by `timestamp` per (file, class). Variants: leaky; fixA (every IAT cell "
     "> 1e9 set to 0 in train and test); fixB (fixA + rows with `packets_count == 1` dropped from train and test). Model: "
     "RandomForestClassifier(n_estimators=200, max_depth=30, min_samples_leaf=10, class_weight='balanced', n_jobs=2, "
     "random_state=0), one process per run under `systemd-run --scope -p MemoryMax=6.5G -p MemorySwapMax=0`. Seed 0 only.", "",
     "### 11.1 Overall", "",
     "| split | variant | n train | n test | acc (all) | macro-F1 (all) | acc (leaked rows) | macro-F1 (leaked) | split thresholds > 1e9 (on IAT) | fit s | peak RSS GB |",
     "|---|---|---:|---:|---:|---:|---:|---:|---|---:|---:|"]
for k in order:
    r = R[k]; a, l, lc = r["all"], r["leaked_rows"], r["leak_check"]
    L.append(f"| {k[0]} | {k[1]} | {r['n_train']:,} | {r['n_test']:,} | {a['accuracy']:.4f} | {a['macro_f1']:.4f} | {l['accuracy']:.4f} | "
             f"{l['macro_f1']:.4f} | {lc['thresholds_above_1e9']} ({lc['of_which_on_IAT_features']}) | {r['fit_seconds']:.0f} | {r['peak_rss_gb']:.2f} |")
flags = [f"{k[0]}_{k[1]}" for k in order if R[k]["leak_check"].get("FLAG_IAT")]
L += ["", ("**LEAK CHECK FAILED on IAT features: " + ", ".join(flags) + "**") if flags else
      "Leak check: 0 split thresholds > 1e9 on IAT features in every fixA/fixB forest" +
      ("" if not any(R[k]["leak_check"]["thresholds_above_1e9"] for k in order if k[1] != "leaky") else
       " (any thresholds > 1e9 in fixed forests are on non-IAT columns: multi-GB payload totals or rates, see §9 hand check)") + ".", ""]
L += ["### 11.2 Per-class recall / precision, all test rows", "",
      "| class | n test | " + " | ".join(f"{s} {v} R / P" for s, v in order) + " |", "|---|---:|" + "---|" * len(order)]
for c in CLS:
    sup = R[order[0]]["all"]["per_class"][c]["support"]
    L.append(f"| {c} | {sup:,} | " + " | ".join(f"{R[k]['all']['per_class'][c]['recall']:.3f} / {R[k]['all']['per_class'][c]['precision']:.3f}" for k in order) + " |")
L += ["", "### 11.3 Per-class recall, leaked test rows (leaked in the unmodified data)", "",
      "| class | " + " | ".join(f"{s} {v} (n)" for s, v in order) + " |", "|---|" + "---|" * len(order)]
for c in CLS:
    cells = []
    for k in order:
        pc = R[k]["leaked_rows"]["per_class"][c]
        cells.append("-" if not pc["support"] else f"{pc['recall']:.3f} ({pc['support']:,})")
    L.append(f"| {c} | " + " | ".join(cells) + " |")
small = [c for c in CLS if any(R[k]["all"]["per_class"][c]["support"] < 100 for k in order)]
L += ["", "### 11.4 Exact counts for classes with < 100 test rows (correct / support, all test rows)", "",
      "| class | " + " | ".join(f"{s} {v}" for s, v in order) + " |", "|---|" + "---|" * len(order)]
for c in small:
    L.append(f"| {c} | " + " | ".join(f"{R[k]['all']['per_class'][c]['correct']}/{R[k]['all']['per_class'][c]['support']}" for k in order) + " |")
L += ["", "### 11.5 Same rows: multi-packet test rows (packets_count != 1)", "",
      "| split | variant | rows | acc | macro-F1 |", "|---|---|---:|---:|---:|"]
for k in order:
    m = R[k]["multi_packet_rows"]
    L.append(f"| {k[0]} | {k[1]} | {m['n']:,} | {m['accuracy']:.4f} | {m['macro_f1']:.4f} |")
L += ["", "(fixB's test set *is* the multi-packet rows, so its row equals its all-rows result.)", "",
      "### 11.6 Differences, leaky − fixA", "",
      "| split | Δ acc (all) | Δ macro-F1 | Δ acc (leaked rows) | Δ acc (multi-packet rows) | Δ recall per class (|Δ| ≥ 0.01) |", "|---|---:|---:|---:|---:|---|"]
for s in ("random", "temporal"):
    if (s, "leaky") in R and (s, "fixA") in R:
        a, b = R[(s, "leaky")], R[(s, "fixA")]
        d = lambda part, key: a[part][key] - b[part][key]
        cls_d = [(c, a["all"]["per_class"][c]["recall"] - b["all"]["per_class"][c]["recall"]) for c in CLS]
        L.append(f"| {s} | {d('all', 'accuracy'):+.4f} | {d('all', 'macro_f1'):+.4f} | {d('leaked_rows', 'accuracy'):+.4f} | "
                 f"{d('multi_packet_rows', 'accuracy'):+.4f} | " + ", ".join(f"{c} {v:+.3f}" for c, v in cls_d if abs(v) >= 0.01) + " |")
open(f"{B}/RESULTS_exp3_2017.md", "w").write("\n".join(L) + "\n")
print("\n".join(L))
