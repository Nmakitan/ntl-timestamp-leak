"""Summaries for the three-dataset model comparison -> results/SUMMARY.md (regenerated from whatever results exist).
Reads results/runs/*.json, results/bootstrap/*.json (mc_bootstrap.py), results/ZERO_CHECK.json (mc_zerocheck.py)
and the queue status files (which machine ran what)."""
import glob, json, os, re

HERE = os.path.dirname(os.path.abspath(__file__))
RES = f"{HERE}/results"
DS = {"d2018": "BCCC-CSE-CIC-IDS2018 (9 classes)", "d2017": "BCCC-CIC-IDS-2017 (14 classes)",
      "cpacket": "BCCC-cPacket-Cloud-DDoS-2024 (26 subtypes)"}
MODELS = ["gnb", "dt", "lr", "xgb", "rf", "mlp", "knn", "xgbfull", "rffull"]
NAMES = {"gnb": "GaussianNB", "dt": "DecisionTree", "lr": "LogReg (std)", "xgb": "XGBoost", "rf": "RandomForest",
         "mlp": "MLP (std)", "knn": "KNN (std, k=5)", "xgbfull": "XGBoost, full train (2018)", "rffull": "RandomForest, full train (2018)"}
COND = ["leaky", "leaky_plus8y", "leaky_zero", "fixA", "dropIAT"]
CSHORT = {"leaky": "leaky", "leaky_plus8y": "+8y", "leaky_zero": "zero", "fixA": "fixA", "dropIAT": "dropIAT"}
VARIANT = {"leaky": "leaky", "leaky_plus8y": "leaky", "leaky_zero": "leaky", "fixA": "fixA", "dropIAT": "dropIAT"}
SPLITS = ("random", "temporal")

runs = {}
for f in glob.glob(f"{RES}/runs/*.json"):
    r = json.load(open(f))
    t = f"{RES}/logs/{r['dataset']}_{r['split']}_{r['model']}_{r['variant']}.time.txt"
    m = re.search(r"Maximum resident set size \(kbytes\): (\d+)", open(t).read()) if os.path.exists(t) else None
    r["peak_gb"] = int(m.group(1)) / 1e6 if m else r.get("peak_rss_gb_self")
    runs[(r["dataset"], r["split"], r["model"], r["variant"])] = r
boot = {}
for f in glob.glob(f"{RES}/bootstrap/*.json"):
    b = json.load(open(f)); boot[(b["dataset"], b["split"], b["model"])] = b
zc = json.load(open(f"{RES}/ZERO_CHECK.json")) if os.path.exists(f"{RES}/ZERO_CHECK.json") else {}
machine = {}  # last successful "end" line per run; untagged lines predate the laptop (all PC)
for f in (f"{RES}/QUEUE_STATUS.txt", f"{RES}/QUEUE_STATUS_laptop.txt"):
    for line in open(f) if os.path.exists(f) else []:
        m = re.search(r"(?:\[(\S+)\] )?end (\S+) rc=0", line)
        if m:
            machine[m.group(2)] = "laptop" if m.group(1) == "nik-G5-5587" else "PC"
        m = re.search(r"\d (\S+) finished under the old queue", line)
        if m:
            machine[m.group(1)] = "PC"


def run(ds, sp, m, c):
    return runs.get((ds, sp, m, VARIANT[c]))


def val(ds, sp, m, c, part="all", key="accuracy"):
    r = run(ds, sp, m, c)
    return r["conditions"][c][part].get(key) if r and c in r["conditions"] else None


fmt = lambda v, d=3: "-" if v is None else f"{v:.{d}f}"


def bci(ds, sp, m, name, part, key):
    """Bootstrap difference as '+0.123 [+0.120, +0.126]*' (* = 95% CI excludes 0); '-' if not available."""
    b = boot.get((ds, sp, m))
    d = b and b["diff"].get(name, {}).get(part, {}).get(key)
    if not d or d["point"] is None or d["ci95"][0] != d["ci95"][0]:
        return "-"
    lo, hi = d["ci95"]
    return f"{d['point']:+.3f} [{lo:+.3f}, {hi:+.3f}]" + ("*" if lo > 0 or hi < 0 else "")


n_main = sum(1 for k in runs if k[3] in ("leaky", "fixA") and k[2] in MODELS)
n_drop = sum(1 for k in runs if k[3] == "dropIAT")
L = ["# Timestamp-leak susceptibility across ML models and three BCCC datasets", "",
     "Spec: fixed model list and configurations, seed 0, no per-condition tuning. Leaked cell = IAT column value > 1e9 "
     "(judged on the unmodified data). Conditions:",
     "- **leaky**: train and test as is.",
     "- **+8y**: same leaky model; leaked test cells + 252,460,800 s (8 years).",
     "- **zero**: same leaky model; leaked test cells set to 0.",
     "- **fixA**: retrain and test with every leaked IAT cell set to 0.",
     "- **dropIAT**: retrain and test with every IAT column removed (30 of 313 features on 2018 and cPacket, 15 of 114 on 2017). "
     "No IAT information at all, so it is a leak-free reference for fixA: if fixA still carried the leak through its zeros, "
     "fixA would beat dropIAT by more than the legitimate IAT information is worth.",
     "",
     "Training: 600k stratified subsample per dataset × split (every row of classes with < 1,000 training rows; all rows "
     "if < 600k); test = the full test split, identical across models and conditions (comparisons are paired). "
     "Mean attack recall = unweighted mean recall over attack classes with >= 10 rows in the subset (cPacket: `Attack` subtypes). "
     "95% CIs: paired bootstrap over test rows, B = 1,000, seed 0 (`mc_bootstrap.py`); `*` = CI excludes 0. "
     "The CIs cover test-set sampling only, not training randomness (single seed).",
     "",
     f"Runs: {n_main} of {7 * 12 + 2 * 4} leaky/fixA runs (7 models × 3 datasets × 2 splits × 2, plus RF and XGBoost "
     f"trained on the full 2018 training split × 2 splits × 2), {n_drop} of {6 * 6 + 2 * 2} dropIAT runs (all models except LogReg). "
     "The full-train runs (`rffull`, `xgbfull`) answer whether the 600k subsample changes the 2018 leak effect. LinearSVC was dropped (> 2.5 h per run, single-threaded, ~6 GB on 2018). "
     "LogReg has no dropIAT run (user decision: slowest model, and it hits the iteration limit in most runs; see caveats). "
     f"Bootstrap results available for {len(boot)} dataset × split × model triples. "
     "All data files and per-class detail: `ALL_RUNS_pooled.csv` (`mc_pool.py`), `BOOTSTRAP_CI.csv`."]
fails = sorted(os.path.basename(f)[:-4] for f in glob.glob(f"{RES}/logs/*.log")
               if not os.path.exists(f"{RES}/runs/{os.path.basename(f)[:-4]}.json")
               and "linsvc" not in f and "bootstrap" not in f and "zerocheck" not in f)
if fails:
    L.append(f"\nRuns without a result (failed or in progress): {', '.join(fails)}")


# ---------------------------------------------------------------- headline differences with CIs
def diff_table(name, part, key, title):
    out = ["", f"### {title}", "", "| model | " + " | ".join(f"{ds} {sp}" for ds in DS for sp in SPLITS) + " |",
           "|---|" + "---:|" * (len(DS) * 2)]
    for m in MODELS:
        cells = [bci(ds, sp, m, name, part, key) for ds in DS for sp in SPLITS]
        if any(c != "-" for c in cells):
            out.append(f"| {NAMES[m]} | " + " | ".join(cells) + " |")
    return out


L += ["", "## 1. Headline differences (point estimate [95% bootstrap CI])", "",
      "Positive leaky−X = the leaky model loses that much when the leak is broken or removed. "
      "fixA−dropIAT is how much more fixA gets than a model with no IAT columns at all: small or negative means fixA's "
      "zeros carry no leak signal beyond legitimate IAT information."]
L += diff_table("leaky-leaky_plus8y", "all", "accuracy", "Accuracy, all test rows: leaky − (+8y)")
L += diff_table("leaky-fixA", "all", "accuracy", "Accuracy, all test rows: leaky − fixA")
L += diff_table("fixA-dropIAT", "all", "accuracy", "Accuracy, all test rows: fixA − dropIAT")
L += ["", "**fixA − dropIAT, result.** For DecisionTree, XGBoost, MLP and GaussianNB, fixA and dropIAT agree within 0.02 "
      "accuracy and ±0.01 mean attack recall on every dataset and split, and KNN within 0.001 accuracy (mean attack recall "
      "+0.03 on 2017, ±0.002 elsewhere): fixA's zeros carry no measurable leak, and fixA is a valid leak-free baseline. One exception: RandomForest on 2018 (+0.047 random, −0.033 temporal). "
      "Its sign flips between splits, which a leak through the zeros would not do (a leak would favour fixA on both). "
      "Per class, the gap sits in how the RF assigns 1-packet fragment rows that are identical across HOIC, Bot and "
      "Benign once the timestamp is gone (RF fixA/dropIAT: HOIC recall 0.50, Bot precision 0.29-0.36, Benign recall "
      "0.82-0.90, where DT and XGBoost keep HOIC at 1.00 and Bot at 0.50): a tie-break among indistinguishable rows, "
      "not a leak channel. The same 600k subsample also leaves this RF well below the full-training-set RF of "
      "Experiment 3 (fixA random 0.831 here vs 0.953 there), so 2018 RF numbers in this section should be read with that in mind."]
L += diff_table("leaky-fixA", "all", "mean_attack_recall", "Mean attack recall, all test rows: leaky − fixA")
L += diff_table("fixA-dropIAT", "all", "mean_attack_recall", "Mean attack recall, all test rows: fixA − dropIAT")
L += diff_table("fixA-dropIAT", "all", "macro_f1", "Macro F1, all test rows: fixA − dropIAT")

# ---------------------------------------------------------------- validity checks
L += ["", "## 2. Validity checks"]
if zc:
    L += ["", "### 2a. IAT units and the 1e9 threshold", "",
          "Leaked values should all be epoch seconds near capture time; legitimate IATs should sit far below 1e9 "
          "(a ms or µs column would put legitimate long gaps near or above 1e9). Random-split training sample.", "",
          "| dataset | IAT columns / features | leaked cells: min – max | legit nonzero: median / p99.99 / max (s) | legit cells in (1e6, 1e9] |",
          "|---|---|---|---|---:|"]
    for ds in DS:
        z = zc.get(ds)
        if z:
            u = z["units"]
            L.append(f"| {ds} | {z['n_iat_cols']} / {z['n_features']} | {u['leaked_min']:.4g} – {u['leaked_max']:.4g} | "
                     f"{u['legit_nonzero_median']:.3g} / {u['legit_nonzero_p9999']:.4g} / {u['legit_max']:.4g} | {u['cells_in_1e6_1e9']} |")
    L += ["", "Result: every leaked cell is a single epoch-second band (2017: Jul 2017; 2018: Feb 2018; cPacket: Dec 2023); "
          "legitimate IATs top out around 3e4 s and no cell lies between 1e6 and 1e9, so the threshold separates them cleanly.",
          "", "### 2b. Does fixA's zero still carry the leak?", "",
          "Leaked rows are strongly class-dependent (table 2c), so after fixA, 'IAT cell == 0' could act as a leak flag. "
          "Test: a balanced decision tree (study DT settings) trained on binary masks only (random split, scored on the full test split). "
          "If fixA's zero pattern were a leak channel, it would beat the legitimate zero pattern clearly.", "",
          "| features (binary) | " + " | ".join(f"{ds}: macro F1 / mean att. recall" for ds in DS if ds in zc) + " |",
          "|---|" + "---|" * sum(ds in zc for ds in DS)]
    labs = next(iter(zc.values()))["mask_models"].keys()
    for lab in labs:
        L.append(f"| {lab} | " + " | ".join(f"{zc[ds]['mask_models'][lab]['macro_f1']:.3f} / {zc[ds]['mask_models'][lab]['mean_attack_recall']:.3f}"
                                            for ds in DS if ds in zc) + " |")
    L += ["", "Result: fixA's zero mask adds at most ~0.01 macro F1 over legitimate zeros alone (2017 +0.012, cPacket +0.004, "
          "2018 +0.001), and mean attack recall changes by -0.03 to +0.01 (lower on 2017 and 2018). Legitimate exact zeros "
          "are common (table 2c), so the leak flag is mostly hidden among them. Section 1 (fixA − dropIAT) is the "
          "full-model check of the same question.",
          "", "### 2c. Leak rate and legitimate zeros by class (random-split training sample)", "",
          "Rows leaked = share of rows with any leaked IAT cell. Legit zeros = share of IAT cells exactly 0 in non-leaked rows. "
          "Because leak rates differ so much by class, the leaked-row subset has a different class mix from the full test set: "
          "compare leaked-row results via mean attack recall, not accuracy, and only within a dataset × split "
          "(the classes entering the mean can differ between splits; see the n in table 3)."]
    for ds in DS:
        if ds in zc:
            L += ["", f"{ds}:", "", "| class | train rows | rows leaked % | legit zeros % |", "|---|---:|---:|---:|"]
            for cn, v in zc[ds]["per_class"].items():
                lz = "n/a (no non-leaked rows)" if v["legit_zero_cell_pct"] is None else f"{v['legit_zero_cell_pct']:.1f}"
                L.append(f"| {cn} | {v['n_train']:,} | {v['row_leak_pct']:.1f} | {lz} |")
    if "d2018" in zc:
        L += ["", "Note: d2018 DoS_SlowHTTP is 100% leaked, so under fixA all its leaked IAT cells are 0 by construction "
              "and there is no legitimate zero pattern to compare with."]
else:
    L += ["", "(ZERO_CHECK.json not found: run mc_zerocheck.py)"]

# ---------------------------------------------------------------- per-dataset detail
L += ["", "## 3. Per-dataset detail"]
for ds, title in DS.items():
    L += ["", f"### {title}", "",
          "Accuracy and mean attack recall on all test rows, mean attack recall on leaked test rows "
          "(n = attack classes in that mean), per condition: " + " / ".join(CSHORT[c] for c in COND) + ".", "",
          "| model | split | accuracy (all) | mean att. recall (all) | mean att. recall (leaked rows) | n | machine | fit s (leaky, fixA, dropIAT) | peak GB | warnings |",
          "|---|---|---|---|---|---:|---|---|---:|---:|"]
    for m in MODELS:
        for sp in SPLITS:
            rr = [runs.get((ds, sp, m, v)) for v in ("leaky", "fixA", "dropIAT")]
            if not any(rr):
                continue
            acc = " / ".join(fmt(val(ds, sp, m, c)) for c in COND)
            mar = " / ".join(fmt(val(ds, sp, m, c, "all", "mean_attack_recall"), 2) for c in COND)
            marl = " / ".join(fmt(val(ds, sp, m, c, "leaked_rows", "mean_attack_recall"), 2) for c in COND)
            ns = sorted({x["conditions"][c]["leaked_rows"]["n_attack_classes_in_mean"] for x in rr if x for c in x["conditions"]})
            mach = sorted({machine.get(f"{ds}_{sp}_{m}_{v}", "PC") for v, x in zip(("leaky", "fixA", "dropIAT"), rr) if x})
            peaks = [x["peak_gb"] for x in rr if x and x.get("peak_gb")]
            L.append(f"| {NAMES[m]} | {sp} | {acc} | {mar} | {marl} | {'/'.join(map(str, ns))} | {'+'.join(mach)} | "
                     + ", ".join(fmt(x and x["fit_seconds"], 0) for x in rr) +
                     f" | {fmt(max(peaks) if peaks else None, 2)} | {sum(x['n_warnings'] for x in rr if x)} |")
    any_r = next((r for k, r in runs.items() if k[0] == ds), None)
    if any_r:
        first = next(iter(any_r["conditions"]))
        small = [c for c, v in any_r["conditions"][first]["all"]["per_class"].items() if v["support"] < 100]
        if small:
            L += ["", "Exact counts for classes with < 100 test rows (correct/support, all test rows; "
                  + " / ".join(CSHORT[c] for c in COND) + "). Anecdotal only: with single-digit supports, one row is "
                  "a large swing in recall, and these classes support no claims on their own.", ""]
            for m in MODELS:
                for sp in SPLITS:
                    if not any(runs.get((ds, sp, m, v)) for v in ("leaky", "fixA", "dropIAT")):
                        continue
                    parts = []
                    for c in small:
                        vals = []
                        for co in COND:
                            r = run(ds, sp, m, co)
                            pc = r["conditions"][co]["all"]["per_class"][c] if r and co in r["conditions"] else None
                            vals.append(f"{pc['correct']}/{pc['support']}" if pc else "-")
                        parts.append(f"{c} " + " / ".join(vals))
                    L.append(f"- {NAMES[m]} {sp}: " + "; ".join(parts))

# ---------------------------------------------------------------- caveats
L += ["", "## 4. Model configuration caveats", "",
      "| model | configuration | class weighting | notes |", "|---|---|---|---|",
      "| GaussianNB | defaults | none | Near or below chance on cPacket (fixA 0.02 accuracy, 26 classes). `var_smoothing` scales with the largest "
      "feature variance, and the features have extreme magnitudes. Treat as a broken baseline, not as evidence about the leak. |",
      "| DecisionTree | max_depth 30, min_samples_leaf 10 | balanced (`class_weight`) | |",
      "| LogReg | StandardScaler + lbfgs, max_iter 1000 | balanced (`class_weight`) | Stopped at the iteration limit in most runs "
      "(list below): its results reflect where the optimiser stopped, so leak effects for LogReg are indicative only. No dropIAT run. |",
      "| XGBoost | 200 trees, depth 8, lr 0.1, hist | balanced (`sample_weight` at fit; not visible in the saved params) | |",
      "| RandomForest | 200 trees, depth 30, min_samples_leaf 10 | balanced (`class_weight`) | |",
      "| MLP | StandardScaler, (128, 64), max_iter 50, early stopping | none | Stopped after 14–47 epochs; mostly predicts the large classes "
      "(very low attack recall on cPacket). Its flat leaky ≈ fixA ≈ +8y numbers more likely reflect under-training than robustness; "
      "the zero condition still hurts it, so it does use the IAT features. Do not read it as 'MLPs are immune'. |",
      "| KNN | StandardScaler, k = 5, distance-weighted (as the shipped knn_model.onnx) | none | Added later (overnight run); "
      "scored on the full test sets like every other model. +8y / zero predictions are computed for leaked rows only and "
      "copied from leaky for the rest (identical by construction; verified on 3,000 rows). |", ""]
iters = []
for (ds, sp, m, v), r in sorted(runs.items()):
    if m in ("lr", "mlp") and "n_iter" in r:
        n = r["n_iter"][0] if isinstance(r["n_iter"], list) else r["n_iter"]
        iters.append(f"{ds} {sp} {m} {v}: {n}" + (" (limit hit)" if m == "lr" and n >= 1000 else ""))
lr_hit = sum(1 for x in iters if "limit hit" in x)
lr_n = sum(1 for x in iters if " lr " in x)
L += [f"Iterations / epochs (LogReg hit the 1,000 limit in {lr_hit} of {lr_n} runs):", ""] + [f"- {x}" for x in iters]
L += ["", "Other caveats:",
      "- Fit time and peak memory come from two machines (PC: 8 threads; laptop: i7-8750H, 12 threads); the `machine` column "
      "in table 3 says which. Compare timings only between runs on the same machine.",
      "- Feature counts differ: 313 features (30 IAT) on 2018 and cPacket, 114 (15 IAT) on 2017. Leak sensitivity across datasets "
      "is therefore not a like-for-like comparison of feature sets.",
      "- Cross-machine reproducibility (checked 2026-10-02): a laptop XGBoost run recomputed on the PC gives identical "
      "predictions; a laptop MLP run gives 791 of 609,513 different predictions (accuracy 0.9468 vs 0.9469), i.e. "
      "floating-point differences between the two CPUs' maths libraries in MLP training, far below any effect reported here.",
      "- Laptop disk incident: on 2026-10-02 evening, 60 scikit-learn files in the laptop's Python environment were found "
      "corrupted on disk (identical garbage blocks; noticed because KNN failed to import). They were restored from the PC "
      "(checksums identical after repair); the laptop's data caches, splits and subsamples were checksum-identical to the PC's, "
      "and import failures are loud, so earlier laptop results are unaffected (see the XGBoost check above).",
      "- Single training seed (0). The CIs cover test-set sampling only.",
      "- Leaked-row accuracy is not comparable to all-row accuracy (different class mix; see 2c); use mean attack recall."]

# ---------------------------------------------------------------- warnings
L += ["", "## 5. Warnings recorded (not suppressed), by run", ""]
byw = {}
for (ds, sp, m, v), r in sorted(runs.items()):
    for w in r["warnings"]:
        byw.setdefault(" ".join(w.split()), []).append(f"{ds}_{sp}_{m}_{v}")
L += [f"- {w}\n  Runs ({len(rs)}): {', '.join(rs)}" for w, rs in byw.items()] or ["- none"]

with open(f"{RES}/SUMMARY.md", "w") as fh:
    fh.write("\n".join(L) + "\n")
print("\n".join(L))
