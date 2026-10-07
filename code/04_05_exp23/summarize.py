"""Write results/exp2/SUMMARY.md and results/exp3/SUMMARY.md from whatever runs have completed."""
import glob, json, os
import numpy as np
from common23 import RES, CLS

RARE = ["SQL_Injection", "Brute_Force_XSS", "Brute_Force_Web"]


def ms(v, d=4):
    v = [x for x in v if x is not None]
    if not v:
        return "-"
    return f"{np.mean(v):.{d}f}" if len(v) == 1 else f"{np.mean(v):.{d}f} ± {np.std(v, ddof=1):.{d}f}"


# ---------------- exp2 ----------------
e2 = [json.load(open(f)) for f in sorted(glob.glob(f"{RES}/exp2/*.json"))]
if e2:
    L = ["# Experiment 2: timestamp-only baseline", "",
         "Single feature t = smallest leaked IAT value in the row (0 if none).", "",
         "| split | model | acc (all) | macro-F1 (all) | acc (leaked) | macro-F1 (leaked) | n test | n leaked |",
         "|---|---|---|---|---|---|---|---|"]
    for r in e2:
        a, l = r["all"], r["leaked_rows"]
        L.append(f"| {r['split']} | {r['model']} | {a['accuracy']:.4f} | {a['macro_f1']:.4f} | "
                 f"{l.get('accuracy', float('nan')):.4f} | {l.get('macro_f1', float('nan')):.4f} | {a['n']} | {l['n']} |")
    L += ["", "Per-class recall (all test rows):", "",
          "| split | model | " + " | ".join(CLS) + " |", "|---|---|" + "---|" * len(CLS)]
    for r in e2:
        L.append(f"| {r['split']} | {r['model']} | " + " | ".join(f"{r['all']['per_class'][c]['recall']:.3f}" for c in CLS) + " |")
    open(f"{RES}/exp2/SUMMARY.md", "w").write("\n".join(L) + "\n")

# ---------------- exp3 ----------------
runs = [json.load(open(f)) for f in sorted(glob.glob(f"{RES}/exp3/runs/*.json")) if not f.endswith(".worker.json")]
if runs:
    groups = {}
    for r in runs:
        groups.setdefault((r["split"], r["variant"]), []).append(r)
    order = [(s, v) for s in ("temporal", "random") for v in ("leaky", "fixA", "fixB") if (s, v) in groups]
    L = ["# Experiment 3: RF retrained with and without the leak", "",
         "RandomForestClassifier(n_estimators=200, max_depth=30, min_samples_leaf=10, class_weight='balanced', n_jobs=2, "
         "random_state=seed), 313 features. Mean ± std over completed seeds.", "",
         "fixA = leaked IAT cells set to 0 in train and test. fixB = fixA + rows with packets_count == 1 dropped "
         "(the test set shrinks too, so fixB is scored on a different row set).", ""]
    flags = [f"{r['split']}_{r['variant']}_s{r['seed']}: {r['leak_check']['thresholds_above_1e9']} "
             f"({r['leak_check']['of_which_on_IAT_features']} on IAT features)"
             for r in runs if r["leak_check"]["FLAG"]]
    iat_flags = [r for r in runs if r["leak_check"]["FLAG"] and r["leak_check"]["of_which_on_IAT_features"]]
    if flags:
        L += [f"**LEAK CHECK FLAGGED (split thresholds > 1e9 in a fixed model): {flags}**", ""]
        L += ["**Of these, on IAT features: " + (f"{len(iat_flags)} run(s) - TIMESTAMP LEAK NOT REMOVED**" if iat_flags else
              "none.** The flagged thresholds are on non-IAT columns. The census column scan found genuine non-timestamp "
              "values above 1e9 only in avg_bwd_bulk_rate, avg_fwd_bulk_rate, bytes_rate, fwd/bwd_bytes_rate and "
              "variance_*_delta_len (implausible rates, not capture times), so these are not leaks."), ""]
    else:
        L += ["Leak check: 0 split thresholds > 1e9 in every fixA/fixB model.", ""]
    hdr = ["split", "variant", "seeds", "acc", "macro-F1"] + [f"R {c}" for c in CLS]
    L += ["## All test rows", "", "| " + " | ".join(hdr) + " |", "|" + "---|" * len(hdr)]
    for k in order:
        g = groups[k]
        L.append(f"| {k[0]} | {k[1]} | {','.join(str(r['seed']) for r in sorted(g, key=lambda r: r['seed']))} | "
                 f"{ms([r['all']['accuracy'] for r in g])} | {ms([r['all']['macro_f1'] for r in g])} | " +
                 " | ".join(ms([r['all']['per_class'][c]['recall'] for r in g], 3) for c in CLS) + " |")
    L += ["", "## Leaked test rows (rows leaked in the unmodified data)", "", "| " + " | ".join(hdr) + " |", "|" + "---|" * len(hdr)]
    for k in order:
        g = groups[k]
        L.append(f"| {k[0]} | {k[1]} | {len(g)} | {ms([r['leaked_rows'].get('accuracy') for r in g])} | "
                 f"{ms([r['leaked_rows'].get('macro_f1') for r in g])} | " +
                 " | ".join(ms([r['leaked_rows']['per_class'][c]['recall'] if r['leaked_rows']['n'] and r['leaked_rows']['per_class'][c]['support'] else None for r in g], 3) for c in CLS) + " |")
    L += ["", "## Rare classes: exact counts (correct / support per seed, all test rows)", "",
          "| split | variant | " + " | ".join(RARE) + " |", "|---|---|" + "---|" * len(RARE)]
    for k in order:
        g = sorted(groups[k], key=lambda r: r["seed"])
        L.append(f"| {k[0]} | {k[1]} | " + " | ".join(
            ", ".join(f"{r['all']['per_class'][c]['correct']}/{r['all']['per_class'][c]['support']}" for r in g) for c in RARE) + " |")
    L += ["", "## Differences (mean leaky − mean fixed)", "", "| split | comparison | Δ acc | Δ macro-F1 | " +
          " | ".join(f"Δ R {c}" for c in CLS) + " |", "|---|---|---|---|" + "---|" * len(CLS)]
    for s in ("temporal", "random"):
        if (s, "leaky") not in groups:
            continue
        base = groups[(s, "leaky")]
        for v in ("fixA", "fixB"):
            if (s, v) not in groups:
                continue
            g = groups[(s, v)]
            d = lambda f: np.mean([f(r) for r in base]) - np.mean([f(r) for r in g])
            L.append(f"| {s} | leaky − {v} | {d(lambda r: r['all']['accuracy']):+.4f} | {d(lambda r: r['all']['macro_f1']):+.4f} | " +
                     " | ".join(f"{d(lambda r, c=c: r['all']['per_class'][c]['recall']):+.3f}" for c in CLS) + " |")
    L += ["", "## Runs", "", "| run | n train | n test | fit s | peak RSS GB | thresholds > 1e9 (on IAT) |", "|---|---|---|---|---|---|"]
    for r in sorted(runs, key=lambda r: (r["split"], r["variant"], r["seed"])):
        L.append(f"| {r['split']}_{r['variant']}_s{r['seed']} | {r['n_train']} | {r['n_test']} | {r['fit_seconds']:.0f} | "
                 f"{r.get('time_v', {}).get('max_rss_gb', r['worker_peak_rss_gb']):.2f} | {r['leak_check']['thresholds_above_1e9']} ({r['leak_check']['of_which_on_IAT_features']}) |")
    failed = sorted(glob.glob(f"{RES}/exp3/runs/*.FAILED"))
    if failed:
        L += ["", "Failed runs: " + ", ".join(os.path.basename(f)[:-7] for f in failed)]
    open(f"{RES}/exp3/SUMMARY.md", "w").write("\n".join(L) + "\n")
print("summaries written")
