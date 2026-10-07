"""Every metric of every run in the NTLFlowLyzer timestamp-leak project -> ~/Desktop/NTL_all_metrics.md.
Reads the result JSONs of experiments 1, 1b, 2, 3 and the section-12 model comparison (incl. bootstrap CIs).
Re-run any time; runs that do not exist yet are simply absent."""
import datetime, glob, json, os

D = os.path.expanduser("~/Desktop")
OUT = f"{D}/NTL_all_metrics.md"
M12 = f"{D}/ntl_models/results"
f3 = lambda v: "-" if v is None else f"{v:.3f}"
L = []


def rp(pc):
    """'recall / precision' of one per-class entry (precision key differs between experiments)."""
    if not pc:
        return "-"
    p = pc.get("precision", pc.get("precision_popw"))
    return f"{f3(pc.get('recall'))} / {f3(p)}"


def per_class_table(title, cols, getters, classes, support_from):
    """Rows = classes; one 'recall / precision' column per (label, per_class dict)."""
    out = [f"\n{title}\n", "| class | support | " + " | ".join(cols) + " |", "|---|---:|" + "---|" * len(cols)]
    for c in classes:
        sup = (support_from or {}).get(c, {}).get("support")
        out.append(f"| {c} | {'-' if sup is None else f'{sup:,}'} | " + " | ".join(rp((g or {}).get(c)) for g in getters) + " |")
    return out


# ------------------------------------------------------------------ header and legend
L += ["# NTLFlowLyzer timestamp leak: all metrics of all runs", "",
      f"Generated {datetime.datetime.now():%Y-%m-%d %H:%M} by `~/Desktop/build_NTL_metrics.py` from the result files. "
      "Every number below is copied from a run's result JSON (or computed from it where stated); nothing is retyped.", "",
      "**Contents:** Legend · Part 1 Experiment 1/1b (our 2018 models, timestamps changed) · Part 2 Experiment 2 "
      "(timestamp-only baseline) · Part 3 Experiment 3 (RandomForest retrain, 2018 and 2017) · Part 4 Section 12 "
      "(seven model families × three datasets, plus full-training-set RF/XGBoost on 2018).", "",
      "## Legend", "",
      "### The leak in one paragraph", "",
      "NTLFlowLyzer writes a flow's absolute start time (Unix epoch seconds, ~1.5e9-1.7e9) into every inter-arrival-time "
      "(IAT) feature of a flow direction that holds exactly one packet. A **leaked cell** is an IAT value > 1e9 in the "
      "unmodified data; a **leaked row** has at least one leaked cell. Capture time identifies the attack window, so a "
      "model can learn the class from the timestamp instead of from the traffic.", "",
      "### Datasets", "",
      "| short name | dataset | classes | features used |", "|---|---|---|---|",
      "| 2018 / d2018 | BCCC-CSE-CIC-IDS2018 (published CSVs) | 9 (Benign + 8 attacks, after the original pipeline's class selection) | 313 (30 IAT) |",
      "| 2017 / d2017 | BCCC-CIC-IDS-2017 | 14 (Benign + 13 attacks) | 114 (15 IAT) |",
      "| cPacket / cpacket | BCCC-cPacket-Cloud-DDoS-2024 | 26 subtypes: 17 `Attack / …`, 8 `Benign / …`, `Suspicious` (Experiment 2 also uses the 3 top-level labels) | 313 (30 IAT) |", "",
      "### Splits", "",
      "| split | meaning |", "|---|---|",
      "| random | stratified 75 % train / 25 % test by class, seed 0. Train and test flows come from the same capture windows, so the timestamp can identify the class. |",
      "| temporal | the latest 25 % of each (file, class) by flow time is the test set (2018: the original training pipeline's split, with its class caps). Test flows come after the training flows, so learned time ranges often do not reach them. |", "",
      "### Training variants (what the model was trained on)", "",
      "| variant | meaning |", "|---|---|",
      "| leaky | trained on the data as published (leak present). |",
      "| fixA | every leaked IAT cell set to 0 in train and test. Equivalent to the code fix (a one-packet direction gets IAT 0), because the leak rule has no exceptions. The main leak-free baseline. |",
      "| fixB | fixA, plus every row with `packets_count == 1` removed from train and test (Experiment 3 only). Scored on a smaller, different test set. |",
      "| dropIAT | every IAT column removed from train and test (Section 12 only). No IAT information at all: a check that fixA's zeros do not leak. |",
      "| subsample vs full | Section 12 models train on a 600k-row stratified subsample of the training split (all rows of classes with < 1,000 rows). `rffull` / `xgbfull` train on the full 2018 training split (3.26M rows), as Experiment 3 did. |", "",
      "### Test conditions (what the trained model was scored on)", "",
      "| condition | applies to | meaning |", "|---|---|---|",
      "| leaky / baseline | leaky models | test data as published. |",
      "| +8y | leaky models, no retraining | every leaked test cell + 252,460,800 s (8 years). Breaks the timestamp, keeps everything else. |",
      "| +1d | leaky models (Exp. 1) | every leaked test cell + 86,400 s (1 day). |",
      "| shuffle | leaky models (Exp. 1) | each leaked row gets another leaked row's timestamp (5 seeds; per-class values here are seed s0, overall values the 5-seed mean). |",
      "| zero | leaky models, no retraining | every leaked test cell set to 0: fixed data fed to the leaky model. |",
      "| fixA / dropIAT / fixB | models trained on that variant | scored on test data prepared the same way. |", "",
      "### Row subsets", "",
      "| subset | meaning |", "|---|---|",
      "| all rows | the whole test split. |",
      "| leaked rows | test rows leaked in the unmodified data (the same rows for every condition of a split). Its class mix differs from all rows, so compare it via recall / mean attack recall, not accuracy. |",
      "| multi-packet rows | test rows with `packets_count != 1` (2017 Experiment 3 only). |", "",
      "### Metrics", "",
      "| metric | meaning |", "|---|---|",
      "| accuracy | share of test rows predicted correctly. |",
      "| macro F1 | unweighted mean F1 over all classes (a class with no support and no predictions counts as 0). |",
      "| mean attack recall (MAR) | unweighted mean recall over attack classes with >= 10 rows in the subset (cPacket: the 17 `Attack / …` subtypes; `Suspicious` is not an attack). |",
      "| recall / precision | per class: recall = correct / support (how many of the class were found); precision = correct / predicted as that class (how many alarms were right). Shown as `recall / precision`. |",
      "| support | number of test rows of that class in the subset. |",
      "| 95% CI | paired bootstrap over test rows, B = 1,000, seed 0 (Section 12 only). Covers test sampling, not training randomness. |",
      "| popw | Experiment 1b scores a 20,001-row stratified sample; accuracy, macro F1 and precision are population-weighted back to the full test set. |", "",
      "### Models", "",
      "| model | configuration | class weighting | where |", "|---|---|---|---|",
      "| RF (our 2018 model) | ONNX RandomForest, 200 trees, depth 30, min_samples_leaf 10, trained on the full 2018 training set, seed 42 | balanced | Exp. 1 |",
      "| KNN, ensemble (our 2018 models) | ONNX StandardScaler + distance-weighted 5-NN (600k subsample); soft-voting RF + KNN | none (KNN) | Exp. 1b |",
      "| timestamp-only tree | DecisionTree on one feature t = smallest leaked IAT in the row (0 if none), depth 20, min_samples_leaf 10; `tree` balanced (pre-specified), `tree_unweighted` added afterwards; baselines `most_frequent`, `stratified` | as named | Exp. 2 |",
      "| RF retrain | RandomForest, 200 trees, depth 30, min_samples_leaf 10, balanced, n_jobs 2 | balanced | Exp. 3 (2018 seeds 0-3, 2017 seed 0), Section 12 (`rf`, `rffull`) |",
      "| gnb | GaussianNB, defaults. Near chance on cPacket: a broken baseline, not interpreted. | none | Section 12 |",
      "| dt | DecisionTree, depth 30, min_samples_leaf 10 | balanced | Section 12 |",
      "| lr | StandardScaler + LogisticRegression (lbfgs, max_iter 1000). Hit the iteration limit in most runs: not interpreted. | balanced | Section 12 |",
      "| xgb | XGBoost, 200 trees, depth 8, learning rate 0.1, hist | balanced (sample weights) | Section 12 (`xgb`, `xgbfull`) |",
      "| mlp | StandardScaler + MLP (128, 64), max_iter 50, early stopping. Under-trained: not interpreted. | none | Section 12 |",
      "| knn | StandardScaler + distance-weighted 5-NN (as our 2018 model) | none | Section 12 |", ""]

# ------------------------------------------------------------------ Part 1: Experiment 1 / 1b
e1 = json.load(open(f"{D}/ntl_exp1/exp1_results.json"))
C1 = [("baseline", "leaky"), ("plus_8y", "+8y"), ("plus_1d", "+1d"), ("shuffle_s0", "shuffle (s0)"), ("zero_fixed_data_leaky_model", "zero")]
cls18 = list(e1["conditions"]["baseline"]["all"]["per_class"])
L += ["", "---", "", "## Part 1. Experiment 1: our 2018 models, only the leaked timestamps changed", "",
      "Original temporal test split of 2018 (1,087,223 rows, 359,693 leaked). No retraining: the same trained model scores "
      "the test set with only the leaked IAT cells changed. Non-leaked rows' predictions were checked to be unchanged in every condition.", "",
      "### 1.1 RandomForest (full test set)", "",
      "| condition | accuracy (all) | macro F1 (all) | accuracy (leaked) | macro F1 (leaked) | predictions changed |", "|---|---:|---:|---:|---:|---:|"]
sh = [e1["conditions"][f"shuffle_s{i}"] for i in range(5) if f"shuffle_s{i}" in e1["conditions"]]
for k, lab in C1:
    c = e1["conditions"][k]
    if k == "shuffle_s0" and sh:
        m = lambda p, key: sum(x[p][key] for x in sh) / len(sh)
        L.append(f"| shuffle (mean of {len(sh)} seeds) | {f3(m('all', 'accuracy'))} | {f3(m('all', 'macro_f1'))} | "
                 f"{f3(m('leaked_rows', 'accuracy'))} | {f3(m('leaked_rows', 'macro_f1'))} | {sum(x['changed_predictions'] for x in sh) / len(sh):,.0f} |")
    else:
        L.append(f"| {lab} | {f3(c['all']['accuracy'])} | {f3(c['all']['macro_f1'])} | {f3(c['leaked_rows']['accuracy'])} | "
                 f"{f3(c['leaked_rows']['macro_f1'])} | {'-' if k == 'baseline' or c.get('changed_predictions') is None else f"{c['changed_predictions']:,}"} |")
for sub, sl in (("all", "all test rows"), ("leaked_rows", "leaked test rows")):
    L += per_class_table(f"RandomForest, per class, {sl} (recall / precision):", [lab for _, lab in C1],
                         [e1["conditions"][k][sub]["per_class"] for k, _ in C1], cls18, e1["conditions"]["baseline"][sub]["per_class"])

e1b = json.load(open(f"{D}/ntl_exp1/exp1b/exp1b_results.json"))
C1b = [("baseline", "leaky"), ("plus_8y", "+8y"), ("plus_1d", "+1d"), ("shuffle_s0", "shuffle (s0)"), ("zero_fixed_data_leaky_model", "zero")]
L += ["", "### 1.2 RF, KNN and soft-voting ensemble on a 20,001-row stratified sample (Experiment 1b)", "",
      "Sample stratified by (class, leaked), all SQL_Injection / XSS / Web rows included; values population-weighted (popw).", "",
      "| model | condition | accuracy popw (all) | macro F1 popw (all) | accuracy popw (leaked) | non-leaked rows unchanged |", "|---|---|---:|---:|---:|---|"]
for mdl in ("rf", "knn", "ensemble"):
    for k, lab in C1b:
        c = e1b[mdl].get(k)
        if c:
            L.append(f"| {mdl} | {lab} | {f3(c['all'].get('accuracy_popw'))} | {f3(c['all'].get('macro_f1_popw'))} | "
                     f"{f3(c['leaked_rows'].get('accuracy_popw'))} | {c.get('sanity_nonleaked_unchanged')} |")
for mdl in ("knn", "ensemble", "rf"):
    L += per_class_table(f"{mdl}, per class, all sample rows (recall / precision popw):", [lab for _, lab in C1b],
                         [e1b[mdl][k]["all"]["per_class"] if k in e1b[mdl] else None for k, _ in C1b], cls18,
                         e1b[mdl]["baseline"]["all"]["per_class"])

# ------------------------------------------------------------------ Part 2: Experiment 2
L += ["", "---", "", "## Part 2. Experiment 2: the timestamp as the only feature", "",
      "One feature t = smallest leaked IAT value in the row (0 if none). The claim tested: the timestamp alone identifies "
      "the attack rows that carry it, so the main metrics are on **leaked test rows**. Overall accuracy on all rows is low "
      "by construction (all non-leaked rows share t = 0)."]
E2 = [("2018", f"{D}/ntl_exp23/results/exp2"), ("2017", f"{D}/ntl_census_multi/BCCC-CIC-IDS-2017/exp2_label"),
      ("cPacket, 26 subtypes", f"{D}/ntl_census_multi/BCCC-cPacket-Cloud-DDoS-2024/exp2_activity"),
      ("cPacket, 3 labels", f"{D}/ntl_census_multi/BCCC-cPacket-Cloud-DDoS-2024/exp2_label")]
MOD2 = ["most_frequent", "stratified", "tree", "tree_unweighted"]
for name, folder in E2:
    L += ["", f"### 2.{E2.index((name, folder)) + 1} {name}", "",
          "| split | model | accuracy (all) | macro F1 (all) | accuracy (leaked) | macro F1 (leaked) | n test | n leaked |", "|---|---|---:|---:|---:|---:|---:|---:|"]
    runs = {}
    for sp in ("random", "temporal"):
        for m in MOD2:
            f = f"{folder}/{sp}_{m}.json"
            if os.path.exists(f):
                r = runs[(sp, m)] = json.load(open(f))
                L.append(f"| {sp} | {m} | {f3(r['all']['accuracy'])} | {f3(r['all']['macro_f1'])} | {f3(r['leaked_rows']['accuracy'])} | "
                         f"{f3(r['leaked_rows']['macro_f1'])} | {r['all']['n']:,} | {r['leaked_rows']['n']:,} |")
    trees = [(sp, m) for sp in ("random", "temporal") for m in ("tree", "tree_unweighted") if (sp, m) in runs]
    if trees:
        cls = list(runs[trees[0]]["leaked_rows"]["per_class"])
        for sp in ("random", "temporal"):
            tt = [(s, m) for s, m in trees if s == sp]
            if tt:
                L += per_class_table(f"{name}, {sp} split, per class on **leaked test rows** (recall / precision):",
                                     [m for _, m in tt], [runs[t]["leaked_rows"]["per_class"] for t in tt], cls,
                                     runs[tt[0]]["leaked_rows"]["per_class"])

# ------------------------------------------------------------------ Part 3: Experiment 3
L += ["", "---", "", "## Part 3. Experiment 3: RandomForest retrained with and without the leak", "",
      "Full training split (2018: 3.26M rows; 2017: 1.83M rows). fixB rows are scored on a smaller test set (1-packet rows removed)."]
X3 = f"{D}/ntl_exp23/results/exp3/runs"
L += ["", "### 3.1 2018, four seeds (0-3)", "",
      "| split | variant | seed | n test | accuracy (all) | macro F1 (all) | accuracy (leaked) | macro F1 (leaked) | split thresholds > 1e9 |",
      "|---|---|---:|---:|---:|---:|---:|---:|---:|"]
r3 = {}
for sp in ("random", "temporal"):
    for v in ("leaky", "fixA", "fixB"):
        for s in range(4):
            f = f"{X3}/{sp}_{v}_s{s}.json"
            if os.path.exists(f):
                r = r3[(sp, v, s)] = json.load(open(f))
                L.append(f"| {sp} | {v} | {s} | {r['all']['n']:,} | {f3(r['all']['accuracy'])} | {f3(r['all']['macro_f1'])} | "
                         f"{f3(r['leaked_rows']['accuracy'])} | {f3(r['leaked_rows']['macro_f1'])} | {r['leak_check'].get('thresholds_above_1e9', '-')} |")


def seedmean(pcs):
    """Per-class mean over seeds (recall, precision) and support of the first seed."""
    out = {}
    for c in pcs[0]:
        out[c] = {"recall": sum(p[c]["recall"] for p in pcs) / len(pcs),
                  "precision": sum(p[c]["precision"] for p in pcs) / len(pcs), "support": pcs[0][c]["support"]}
    return out


for sp in ("random", "temporal"):
    for sub, sl in (("all", "all test rows"), ("leaked_rows", "leaked test rows")):
        cols, gets = [], []
        for v in ("leaky", "fixA", "fixB"):
            pcs = [r3[(sp, v, s)][sub]["per_class"] for s in range(4) if (sp, v, s) in r3]
            if pcs:
                cols.append(f"{v} (mean of {len(pcs)} seeds)"); gets.append(seedmean(pcs))
        L += per_class_table(f"2018 {sp}, per class, {sl} (recall / precision; support = leaky/fixA test set, fixB differs):",
                             cols, gets, list(gets[0]), gets[0])
X17 = f"{D}/ntl_census_multi/BCCC-CIC-IDS-2017/exp3"
L += ["", "### 3.2 2017, seed 0", "",
      "| split | variant | n test | accuracy (all) | macro F1 (all) | accuracy (leaked) | accuracy (multi-packet rows) | split thresholds > 1e9 on IAT |",
      "|---|---|---:|---:|---:|---:|---:|---:|"]
r17 = {}
for sp in ("random", "temporal"):
    for v in ("leaky", "fixA", "fixB"):
        f = f"{X17}/{sp}_{v}_s0.json"
        if os.path.exists(f):
            r = r17[(sp, v)] = json.load(open(f))
            L.append(f"| {sp} | {v} | {r['all']['n']:,} | {f3(r['all']['accuracy'])} | {f3(r['all']['macro_f1'])} | "
                     f"{f3(r['leaked_rows']['accuracy'])} | {f3(r['multi_packet_rows']['accuracy'])} | {r['leak_check'].get('of_which_on_IAT_features', '-')} |")
for sp in ("random", "temporal"):
    for sub, sl in (("all", "all test rows"), ("leaked_rows", "leaked test rows"), ("multi_packet_rows", "multi-packet test rows")):
        vv = [v for v in ("leaky", "fixA", "fixB") if (sp, v) in r17]
        if vv:
            pcs = [r17[(sp, v)][sub]["per_class"] for v in vv]
            L += per_class_table(f"2017 {sp}, per class, {sl} (recall / precision):", vv, pcs, list(pcs[0]), pcs[0])

# ------------------------------------------------------------------ Part 4: Section 12
runs = {}
for f in glob.glob(f"{M12}/runs/*.json"):
    r = json.load(open(f)); runs[(r["dataset"], r["split"], r["model"], r["variant"])] = r
boot = {}
for f in glob.glob(f"{M12}/bootstrap/*.json"):
    b = json.load(open(f)); boot[(b["dataset"], b["split"], b["model"])] = b
MODELS = ["gnb", "dt", "lr", "xgb", "xgbfull", "rf", "rffull", "mlp", "knn"]
COND = [("leaky", "leaky", "leaky"), ("leaky_plus8y", "leaky", "+8y"), ("leaky_zero", "leaky", "zero"),
        ("fixA", "fixA", "fixA"), ("dropIAT", "dropIAT", "dropIAT")]
DS = [("d2018", "BCCC-CSE-CIC-IDS2018"), ("d2017", "BCCC-CIC-IDS-2017"), ("cpacket", "BCCC-cPacket-Cloud-DDoS-2024")]


def ci(ds, sp, m, c, sub, key):
    b = boot.get((ds, sp, m))
    x = b and b["cond"].get(c, {}).get(sub, {}).get(key)
    return f" [{x['ci95'][0]:.3f}, {x['ci95'][1]:.3f}]" if x and x["ci95"][0] == x["ci95"][0] else ""


L += ["", "---", "", "## Part 4. Section 12: seven model families × three datasets × two splits × five conditions", "",
      f"{len(runs)} runs. Seed 0, 600k-row training subsample (except `rffull`, `xgbfull`: full 2018 training split), "
      "full test split. Overall values carry 95% bootstrap CIs in brackets where available. "
      "`rffull` / `xgbfull` rows only exist for 2018."]
for ds, dsl in DS:
    L += ["", f"### 4.{DS.index((ds, dsl)) + 1} {dsl}", "", "**Overall** (all test rows, then leaked test rows):", "",
          "| model | split | condition | accuracy (all) [95% CI] | macro F1 (all) | MAR (all) [95% CI] | accuracy (leaked) | MAR (leaked) | n attack classes in MAR (leaked) |",
          "|---|---|---|---|---:|---|---:|---:|---:|"]
    for m in MODELS:
        for sp in ("random", "temporal"):
            for c, v, lab in COND:
                r = runs.get((ds, sp, m, v))
                if not r or c not in r["conditions"]:
                    continue
                a, lk = r["conditions"][c]["all"], r["conditions"][c]["leaked_rows"]
                L.append(f"| {m} | {sp} | {lab} | {f3(a['accuracy'])}{ci(ds, sp, m, c, 'all', 'accuracy')} | {f3(a['macro_f1'])} | "
                         f"{f3(a['mean_attack_recall'])}{ci(ds, sp, m, c, 'all', 'mean_attack_recall')} | {f3(lk['accuracy'])} | "
                         f"{f3(lk['mean_attack_recall'])} | {lk['n_attack_classes_in_mean']} |")
    for m in MODELS:
        for sp in ("random", "temporal"):
            cc = [(c, v, lab) for c, v, lab in COND if (ds, sp, m, v) in runs and c in runs[(ds, sp, m, v)]["conditions"]]
            if not cc:
                continue
            for sub, sl in (("all", "all test rows"), ("leaked_rows", "leaked test rows")):
                pcs = [runs[(ds, sp, m, v)]["conditions"][c][sub]["per_class"] for c, v, _ in cc]
                L += per_class_table(f"**{m}, {sp} split, per class, {sl}** (recall / precision):", [lab for _, _, lab in cc],
                                     pcs, list(pcs[0]), pcs[0])

open(OUT, "w").write("\n".join(L) + "\n")
print(f"{OUT}: {os.path.getsize(OUT) / 1e3:.0f} KB, {len(L):,} lines, section-12 runs: {len(runs)}")
