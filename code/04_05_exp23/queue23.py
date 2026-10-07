"""Queue for experiments 2 and 3. Starts after the exp1b scoring run and its report are finished and the train
arrays are built. Each run: own process inside `systemd-run --user --scope -p MemoryMax=6.5G -p MemorySwapMax=0`
(falls back to `ulimit -v`), under `/usr/bin/time -v`. Resumable; never overwrites results; logs failures and moves on.
Status: results/QUEUE_STATUS.txt
"""
import json, os, re, subprocess, sys, time
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
RES = f"{HERE}/results"
LOGS = f"{RES}/logs"
os.makedirs(LOGS, exist_ok=True)
STATUS = f"{RES}/QUEUE_STATUS.txt"
EXP1B = "/home/USER/Desktop/ntl_exp1/exp1b"
BUILD_LOG = f"{HERE}/build_train.log"
PY = sys.executable


def status(msg):
    line = f"{time.strftime('%F %T')} {msg}"
    print(line, flush=True)
    open(STATUS, "a").write(line + "\n")


def running(pattern):
    return subprocess.run(["pgrep", "-f", pattern], capture_output=True).returncode == 0


def stop(reason):
    status(f"QUEUE STOPPED: {reason}")
    subprocess.run([PY, f"{HERE}/summarize.py"], cwd=HERE)
    sys.exit(1)


# ---- wait for exp1b (scoring + report) and for the train build -------------------------------
status("queue started; waiting for exp1b run + report and train build")
while running("^python3 exp1b_run") or running("^/bin/bash ./exp1b_after") or running("^python3 build_train_npy"):
    time.sleep(60)
build = open(BUILD_LOG).read() if os.path.exists(BUILD_LOG) else ""
if "BUILD OK" not in build:
    stop(f"train build did not finish OK; tail of build_train.log: {build[-500:]!r}")
status("prerequisites done (exp1b finished; train arrays built and test-verified)")

# ---- memory cap wrapper -------------------------------------------------------------------
CAP = ["systemd-run", "--user", "--scope", "--quiet", "-p", "MemoryMax=6.5G", "-p", "MemorySwapMax=0"]
if subprocess.run(CAP + ["true"], capture_output=True).returncode != 0:
    status("systemd-run scope unavailable; falling back to ulimit -v 6.5 GiB")
    CAP = None


def run(tag, args):
    tlog, olog = f"{LOGS}/{tag}.time.txt", f"{LOGS}/{tag}.log"
    cmd = ["/usr/bin/time", "-v", "-o", tlog, PY] + args
    if CAP:
        cmd = CAP + cmd
    else:
        cmd = ["bash", "-c", "ulimit -v 6815744; exec \"$@\"", "_"] + cmd
    status(f"start {tag}")
    t0 = time.time()
    with open(olog, "a") as f:
        rc = subprocess.run(cmd, cwd=HERE, stdout=f, stderr=subprocess.STDOUT).returncode
    tv = {}
    if os.path.exists(tlog):
        txt = open(tlog).read()
        m = re.search(r"Maximum resident set size \(kbytes\): (\d+)", txt)
        w = re.search(r"Elapsed \(wall clock\) time .*?: ([\d:.]+)", txt)
        tv = {"max_rss_gb": int(m.group(1)) / 1e6 if m else None, "wall": w.group(1) if w else None,
              "signal": re.search(r"Command terminated by signal (\d+)", txt).group(1) if "terminated by signal" in txt else None}
    status(f"end {tag} rc={rc} wall={time.time() - t0:.0f}s peak_rss={tv.get('max_rss_gb')}GB"
           + (f" signal={tv['signal']}" if tv.get("signal") else ""))
    return rc, tv


# ---- experiment 2 ---------------------------------------------------------------------------
if not os.path.exists(f"{HERE}/exp3/random_split_idx.npz") or not os.path.exists(f"{HERE}/cache/pool_meta.npz"):
    rc, _ = run("exp2_prep", [f"{HERE}/exp2_run.py", "prep"])
    if rc != 0:
        stop("exp2 prep (pool metadata / random split) failed; see results/logs/exp2_prep.log")
for split in ("temporal", "random"):
    for model in ("most_frequent", "stratified", "tree"):
        if os.path.exists(f"{RES}/exp2/{split}_{model}.json"):
            continue
        rc, _ = run(f"exp2_{split}_{model}", [f"{HERE}/exp2_run.py", split, model])
        if rc != 0:
            status(f"FAILED exp2_{split}_{model} (rc={rc}); continuing")
subprocess.run([PY, f"{HERE}/summarize.py"], cwd=HERE)

# ---- experiment 3 ---------------------------------------------------------------------------
core = [("temporal", "leaky"), ("temporal", "fixA"), ("random", "leaky"), ("random", "fixA")]
tiers = [
    ("tier1", [(s, v, 0) for s, v in core]),
    ("tier2", [(s, v, k) for k in (1, 2) for s, v in core]),
    ("tier3", [(s, "fixB", k) for k in (0, 1, 2) for s in ("temporal", "random")]),
    ("tier4", [(s, v, k) for k in (3, 4) for s, v in core + [("temporal", "fixB"), ("random", "fixB")]]),
]
RUNS = f"{RES}/exp3/runs"
os.makedirs(RUNS, exist_ok=True)
from common23 import write_new

for tier, jobs in tiers:
    status(f"=== {tier} ===")
    for split, variant, seed in jobs:
        name = f"{split}_{variant}_s{seed}"
        final, worker = f"{RUNS}/{name}.json", f"{RUNS}/{name}.worker.json"
        if not os.path.exists(final):
            if not os.path.exists(worker):
                rc, tv = run(f"exp3_{name}", [f"{HERE}/exp3_run.py", split, variant, str(seed)])
            else:
                rc, tv = 0, {}
            if os.path.exists(worker):
                r = json.load(open(worker))
                r["time_v"] = tv
                write_new(final, r)
                if r["leak_check"]["FLAG"]:
                    status(f"!!! LEAK CHECK FAILED for {name}: {r['leak_check']['thresholds_above_1e9']} thresholds > 1e9")
            else:
                open(f"{RUNS}/{name}.FAILED", "w").write(json.dumps({"rc": rc, "time_v": tv}) + "\n")
                status(f"FAILED {name} (rc={rc}, signal={tv.get('signal')}); continuing")
        subprocess.run([PY, f"{HERE}/summarize.py"], cwd=HERE)
        if name == "temporal_leaky_s0":
            if not os.path.exists(final):
                stop("pipeline check run temporal_leaky_s0 failed")
            acc = json.load(open(final))["all"]["accuracy"]
            if abs(acc - 0.8919) > 0.015:
                stop(f"pipeline check: temporal_leaky_s0 accuracy {acc:.4f} is not ≈0.89")
            status(f"pipeline check OK: temporal_leaky_s0 accuracy {acc:.4f}")
    status(f"{tier} complete")
status("ALL TIERS DONE")
