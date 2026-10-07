"""Experiment 1b worker: score ONE (model, condition) in a fresh process, then exit (frees all ORT memory).
Usage: exp1b_score.py <model: knn|ensemble> <condition>"""
import json, os, sys, time, resource
import numpy as np, onnxruntime as ort

OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "exp1b")
MODELS = {"knn": "/home/USER/trained_models/knn_model.onnx", "ensemble": "/home/USER/trained_models/ensemble_model.onnx"}
BATCH, THREADS = 50, 2
model, cond = sys.argv[1], sys.argv[2]
dst = f"{OUT}/pred_{model}_{cond}.npy"
so = ort.SessionOptions(); so.enable_cpu_mem_arena = False; so.intra_op_num_threads = THREADS
sess = ort.InferenceSession(MODELS[model], so, providers=["CPUExecutionProvider"])
Z = np.load(f"{OUT}/cond_{cond}.npy")
t0, out, rss = time.time(), [], []
for i in range(0, len(Z), BATCH):
    out.append(sess.run(None, {"input": Z[i:i + BATCH]})[0])
    if (i // BATCH) % 20 == 0:
        rss.append(int(open("/proc/self/statm").read().split()[1]) * 4096 / 1e9)
        print(f"{model} {cond} {i + BATCH}/{len(Z)} {time.time() - t0:.0f}s rss={rss[-1]:.2f}GB", flush=True)
np.save(dst + ".tmp.npy", np.concatenate(out).astype(np.int64)); os.replace(dst + ".tmp.npy", dst)
json.dump({"model": model, "cond": cond, "rows": len(Z), "seconds": round(time.time() - t0, 1),
           "peak_rss_gb": resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / 1e6, "rss_samples_gb": rss},
          open(dst.replace(".npy", ".meta.json"), "w"))
