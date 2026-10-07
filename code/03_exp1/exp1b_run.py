"""Experiment 1b driver: one subprocess per (model, condition), at most PAR at a time; skips finished jobs."""
import os, subprocess, sys, time
HERE = os.path.dirname(os.path.abspath(__file__))
PAR = int(sys.argv[1]) if len(sys.argv) > 1 else 2
conds = ["baseline", "plus_8y", "plus_1d", "zero_fixed_data_leaky_model"] + [f"shuffle_s{s}" for s in range(5)]
jobs = [(m, c) for c in conds for m in ("knn", "ensemble")
        if not os.path.exists(f"{HERE}/exp1b/pred_{m}_{c}.npy")]
running, tries = [], {}
MAX_TRIES = 3
while jobs or running:
    while jobs and len(running) < PAR:
        m, c = jobs.pop(0)
        log = open(f"{HERE}/exp1b/log_{m}_{c}.txt", "w")
        running.append(((m, c), subprocess.Popen([sys.executable, f"{HERE}/exp1b_score.py", m, c], stdout=log, stderr=log)))
        print(time.strftime("%H:%M:%S"), "start", m, c, flush=True)
    for job in list(running):
        if job[1].poll() is not None:
            running.remove(job)
            print(time.strftime("%H:%M:%S"), "exit", job[0], "rc", job[1].returncode, flush=True)
            if job[1].returncode != 0:
                tries[job[0]] = tries.get(job[0], 1) + 1
                if tries[job[0]] <= MAX_TRIES:
                    print(time.strftime("%H:%M:%S"), "retry", job[0], "attempt", tries[job[0]], flush=True)
                    jobs.insert(0, job[0])
    time.sleep(5)
print("ALL DONE", flush=True)
