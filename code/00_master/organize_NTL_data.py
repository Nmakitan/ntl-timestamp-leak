"""Gather every result of the NTLFlowLyzer timestamp-leak project into ~/Desktop/NTL_leak_research/.
Files <= 5 MB are copied; larger files (prediction arrays, feature caches, split indices) are symlinked to their
original location, so nothing big is duplicated on the nearly full system drive. Source folders are not modified.
Re-run any time: the target tree is rebuilt from scratch (only this script's output directory is removed)."""
import os, shutil

D = os.path.expanduser("~/Desktop")
OUT = f"{D}/NTL_leak_research"
BIG = 5_000_000
SKIP_DIRS = {"__pycache__", ".git"}
CODE_EXT = (".py", ".sh")
log = []


def skip(name):
    return name.startswith("venv") or name in SKIP_DIRS or ".bak" in name


def place(src, dst):
    os.makedirs(os.path.dirname(dst), exist_ok=True)
    if os.path.getsize(src) > BIG:
        os.symlink(src, dst); log.append(("link", src, dst))
    else:
        shutil.copy2(src, dst); log.append(("copy", src, dst))


def tree(src, dst, exclude=(), code_dst=None, top_only_code=True):
    """Copy a source tree; .py/.sh files go to code_dst instead (if given); `exclude` = subdir names to leave out."""
    for root, dirs, files in os.walk(src):
        dirs[:] = sorted(d for d in dirs if not skip(d) and os.path.relpath(f"{root}/{d}", src) not in exclude)
        rel = os.path.relpath(root, src)
        for f in sorted(files):
            if skip(f):
                continue
            s = f"{root}/{f}"
            if code_dst and f.endswith(CODE_EXT):
                place(s, f"{code_dst}/{'' if rel == '.' else rel + '/'}{f}")
            else:
                place(s, f"{dst}/{'' if rel == '.' else rel + '/'}{f}")


import subprocess  # refresh the all-metrics file first, so the copy below is current
if os.path.exists(f"{D}/build_NTL_metrics.py"):
    subprocess.run(["python3", f"{D}/build_NTL_metrics.py"], check=True)
if os.path.islink(OUT) or os.path.isfile(OUT):
    raise SystemExit(f"{OUT} exists and is not a directory")
KEEP = ("06_wireshark_figure",)  # hand-made material that lives only here: kept across rebuilds
kept = {}
for k in KEEP:
    if os.path.isdir(f"{OUT}/{k}"):
        kept[k] = f"{D}/.NTL_keep_{k}"
        if os.path.exists(kept[k]):
            raise SystemExit(f"{kept[k]} exists from an interrupted run; move it back into {OUT} first")
        shutil.move(f"{OUT}/{k}", kept[k])
if os.path.isdir(OUT):
    shutil.rmtree(OUT)
os.makedirs(OUT)
for k, tmp in kept.items():
    shutil.move(tmp, f"{OUT}/{k}")

M = f"{D}/ntl_census_multi"
D17, DCP, DDL = f"{M}/BCCC-CIC-IDS-2017", f"{M}/BCCC-cPacket-Cloud-DDoS-2024", f"{M}/BCCC-DLLayer-IDS-2025"
C = f"{OUT}/code"

# 01 reproducer
tree(f"{D}/ntl_repro_step1", f"{OUT}/01_reproducer", code_dst=f"{C}/01_reproducer")
# 02 censuses
tree(f"{D}/ntl_census_step2", f"{OUT}/02_census/2018_BCCC-CSE-CIC-IDS2018", code_dst=f"{C}/02_census_2018")
tree(D17, f"{OUT}/02_census/2017_BCCC-CIC-IDS-2017", exclude=("exp2_label", "exp2_lodo", "exp3", "cache", "lodo"), code_dst=f"{C}/02_census_multi")
tree(DCP, f"{OUT}/02_census/cpacket_BCCC-cPacket-Cloud-DDoS-2024", exclude=("exp2_label", "exp2_activity", "cache"), code_dst=f"{C}/02_census_multi")
tree(DDL, f"{OUT}/02_census/dllayer_BCCC-DLLayer-IDS-2025", code_dst=f"{C}/02_census_multi")
for f in sorted(os.listdir(M)):
    s = f"{M}/{f}"
    if os.path.isfile(s) and not skip(f):
        place(s, f"{C}/02_census_multi/{f}" if f.endswith(CODE_EXT) else f"{OUT}/02_census/combined/{f}")
# 03 experiment 1 / 1b: shipped 2018 models, timestamps changed
tree(f"{D}/ntl_exp1", f"{OUT}/03_exp1_shipped_models_timestamp_change", code_dst=f"{C}/03_exp1")
# 04 experiment 2: timestamp-only baseline, three datasets
tree(f"{D}/ntl_exp23/results/exp2", f"{OUT}/04_exp2_timestamp_only/2018")
tree(f"{D17}/exp2_label", f"{OUT}/04_exp2_timestamp_only/2017")
tree(f"{D17}/exp2_lodo", f"{OUT}/04_exp2_timestamp_only/2017_lodo")  # leave-one-day-out + binary table of all splits
tree(f"{DCP}/exp2_activity", f"{OUT}/04_exp2_timestamp_only/cpacket_26_subtypes")
tree(f"{DCP}/exp2_label", f"{OUT}/04_exp2_timestamp_only/cpacket_3_labels")
# 05 experiment 3: RF retrain leaky / fixA / fixB
tree(f"{D}/ntl_exp23/results/exp3", f"{OUT}/05_exp3_rf_retrain/2018")
tree(f"{D}/ntl_exp23/results/logs", f"{OUT}/05_exp3_rf_retrain/2018/logs")
for f in ("QUEUE_STATUS.txt",):
    place(f"{D}/ntl_exp23/results/{f}", f"{OUT}/05_exp3_rf_retrain/2018/{f}")
place(f"{D}/ntl_exp23/exp3/random_split_idx.npz", f"{OUT}/05_exp3_rf_retrain/2018/random_split_idx.npz")
tree(f"{D17}/exp3", f"{OUT}/05_exp3_rf_retrain/2017", exclude=("cache",), code_dst=f"{C}/05_exp3_2017")
for f in sorted(os.listdir(f"{D}/ntl_exp23")):
    s = f"{D}/ntl_exp23/{f}"
    if os.path.isfile(s) and not skip(f):
        place(s, f"{C}/04_05_exp23/{f}" if f.endswith(CODE_EXT) else f"{OUT}/05_exp3_rf_retrain/2018/{f}")
# 06 seven-model comparison (section 12)
tree(f"{D}/ntl_models/results", f"{OUT}/06_model_comparison")
place(f"{D17}/lodo/splits.npz", f"{OUT}/06_model_comparison/lodo_2017_splits.npz")  # leave-one-day-out, 2017
for f in sorted(os.listdir(f"{D}/ntl_models")):
    s = f"{D}/ntl_models/{f}"
    if os.path.isfile(s) and not skip(f):
        place(s, f"{C}/06_model_comparison/{f}")
# 07 literature screen
lit = f"{D}/NTL_literature_screen.csv"
if os.path.exists(lit):
    place(lit, f"{OUT}/07_literature/literature_screen.csv")
# 00 master documents
for f in ("NTL_timestamp_leak_MASTER.md", "NTL_timestamp_leak_REPORT.md", "NTL_master_summary.md", "NTL_paper_draft.md", "NTL_all_metrics.md"):
    if os.path.exists(f"{D}/{f}"):
        place(f"{D}/{f}", f"{OUT}/00_MASTER/{f}")
for f in ("build_NTL_master.py", "organize_NTL_data.py", "build_NTL_metrics.py"):
    place(f"{D}/{f}", f"{C}/00_master/{f}")
# large arrays that stay on the data drive / in the caches: listed, not copied
EXTERNAL = [
    ("2018 published CSVs (34 per-day files)", "<data drive>/Dataset (see 02_census/2018*/file_list.txt)"),
    ("2018 train/test arrays used by experiments 1-3", "<data drive>/Dataset/ml_module_output/_intermediate"),
    ("2018 model-comparison matrices", "/home/USER/pew2/ntl_models_cache"),
    ("2017 feature cache (X.npy + meta)", f"{D17}/exp3/cache"),
    ("cPacket feature cache (X.npy + meta)", f"{DCP}/cache"),
]

n_copy = sum(1 for k, *_ in log if k == "copy"); n_link = sum(1 for k, *_ in log if k == "link")
size_copy = sum(os.path.getsize(d) for k, s, d in log if k == "copy")
with open(f"{OUT}/MANIFEST.tsv", "w") as fh:
    fh.write("action\tsize_bytes\tpath_in_this_directory\toriginal_path\n")
    for k, s, d in log:
        fh.write(f"{k}\t{os.path.getsize(s)}\t{os.path.relpath(d, OUT)}\t{s}\n")
with open(f"{OUT}/EXTERNAL_DATA.md", "w") as fh:
    fh.write("# Large data kept outside this directory\n\n| what | where |\n|---|---|\n")
    fh.writelines(f"| {a} | `{b}` |\n" for a, b in EXTERNAL)
README = """# NTLFlowLyzer timestamp leak: all project data

Every result of the project, organised by stage. Small files are copies; files over 5 MB are symlinks to their
original location (see MANIFEST.tsv: action, size, path here, original path). Data too large to keep here is listed
in EXTERNAL_DATA.md. Rebuild this directory with `code/00_master/organize_NTL_data.py`.

| folder | what it holds | key files |
|---|---|---|
| 00_MASTER | the compiled findings | NTL_timestamp_leak_MASTER.md (everything), NTL_all_metrics.md (every metric of every run, with legend), NTL_paper_draft.md (abstract, argument, key tables), NTL_master_summary.md (executive summary), NTL_timestamp_leak_REPORT.md (sections 0-11) |
| 01_reproducer | minimal 21-packet pcap reproducing the bug on upstream NTLFlowLyzer | RESULTS.md, repro.pcap, repro_out.csv, repro_out_fork.csv |
| 02_census | leak census of each dataset: per class, per file, rule check, calendar, flow shapes | */RESULTS.md, */per_class.csv, */LEAK_SHAPES.md, combined/COMBINED.md |
| 03_exp1_shipped_models_timestamp_change | shipped 2018 RF / KNN / ensemble re-scored with only the timestamps changed | RESULTS.md, RESULTS_exp1b.md, exp1_results.json, exp1b/exp1b_results.json |
| 04_exp2_timestamp_only | decision tree on the timestamp alone, three datasets, random and temporal splits; 2017 also leave-one-day-out | */*_tree.json, 2018/SUMMARY.md, 2017_lodo/RESULTS.md (binary table, all splits), splits.npz (symlinks) |
| 05_exp3_rf_retrain | RandomForest retrained leaky / fixA / fixB: 2018 (4 seeds), 2017 (seed 0) | 2018/SUMMARY.md, 2018/runs/*.json, 2017/RESULTS_exp3_2017.md |
| 06_model_comparison | seven model families x three datasets x two splits x five conditions (120 runs); plus leave-one-day-out on 2017 (DT / RF / GNB x 5 held-out days x leaky / fixA, 30 runs, binary attack-vs-benign scoring) | SUMMARY.md, ALL_RUNS_pooled.csv, BOOTSTRAP_CI.csv, ZERO_CHECK.json, runs/*.json, LODO_2017.md, LODO_2017.csv, runs/d2017_lodo_*.json |
| 07_literature | works naming the BCCC datasets, counted / excluded with reasons | literature_screen.csv |
| code | every script, by stage | |
"""
open(f"{OUT}/README.md", "w").write(README)
print(f"{OUT}: {n_copy} files copied ({size_copy / 1e6:.1f} MB), {n_link} large files symlinked")
