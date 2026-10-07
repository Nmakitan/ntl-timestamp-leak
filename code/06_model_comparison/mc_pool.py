"""Pool every finished run (both machines) into one long-format CSV -> results/ALL_RUNS_pooled.csv.
One row per run x condition x subset x class; class == "ALL" carries the overall metrics. Confusion matrices stay in the run JSONs."""
import csv, glob, json, os, re

HERE = os.path.dirname(os.path.abspath(__file__))
RES = f"{HERE}/results"

machine = {}  # last successful "end" line per run decides which machine produced it
for f in (f"{RES}/QUEUE_STATUS.txt", f"{RES}/QUEUE_STATUS_laptop.txt"):
    for line in open(f):
        m = re.search(r"(?:\[(\S+)\] )?end (\S+) rc=0", line)
        if m:
            machine[m.group(2)] = "laptop" if m.group(1) == "nik-G5-5587" else "pc"  # untagged lines predate the laptop: all PC
        m = re.search(r"\d (\S+) finished under the old queue", line)  # PC queue restart, no end line
        if m:
            machine[m.group(1)] = "pc"

RUN = ["dataset", "split", "model", "variant", "machine", "n_train", "n_test", "n_features", "n_iter",
       "fit_seconds", "predict_seconds", "peak_rss_gb", "n_warnings", "params"]
COLS = RUN + ["condition", "subset", "class", "n", "accuracy", "macro_f1", "mean_attack_recall",
              "n_attack_classes_in_mean", "recall", "precision", "correct"]
rows = []
for f in sorted(glob.glob(f"{RES}/runs/*.json")):
    r = json.load(open(f))
    key = os.path.basename(f)[:-5]
    t = f"{RES}/logs/{key}.time.txt"
    m = re.search(r"Maximum resident set size \(kbytes\): (\d+)", open(t).read()) if os.path.exists(t) else None
    base = {k: r.get(k) for k in RUN}
    base.update(machine=machine.get(key, "unknown"), params=" ".join(r["params"].split()),
                peak_rss_gb=round(int(m.group(1)) / 1e6, 3) if m else r.get("peak_rss_gb_self"))
    for cond, subsets in r["conditions"].items():
        for sub, s in subsets.items():
            rows.append({**base, "condition": cond, "subset": sub, "class": "ALL",
                         **{k: s[k] for k in ("n", "accuracy", "macro_f1", "mean_attack_recall", "n_attack_classes_in_mean")}})
            for cls, p in s["per_class"].items():
                rows.append({**base, "condition": cond, "subset": sub, "class": cls, "n": p["support"],
                             "recall": p["recall"], "precision": p["precision"], "correct": p["correct"]})

out = f"{RES}/ALL_RUNS_pooled.csv"
with open(out, "w", newline="") as fh:
    w = csv.DictWriter(fh, COLS)
    w.writeheader()
    w.writerows(rows)
print(f"{len(glob.glob(f'{RES}/runs/*.json'))} runs, {len(rows)} rows -> {out}")
print("machines:", {v: list(machine.get(os.path.basename(f)[:-5], 'unknown') for f in glob.glob(f'{RES}/runs/*.json')).count(v) for v in ('pc', 'laptop', 'unknown')})
