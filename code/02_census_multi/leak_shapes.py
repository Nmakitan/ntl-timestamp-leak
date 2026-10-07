"""What are the leaked rows? Classify every row of an NTLFlowLyzer dataset into a flow-shape category and count, per class,
how the leaked rows (any IAT > 1e9) split across categories.
Usage: leak_shapes.py <dataset_dir> <out_dir> <class_mode: label|activity>

Categories (f = fwd packets, b = bwd packets, flags summed over both directions, payload = total_payload_bytes):
  1 packet:  lone SYN | lone SYN-ACK | lone RST | lone FIN | lone ACK, no payload (ghost ACK) | lone data packet | lone other
  1 + 1:     SYN -> RST (probe / refused) | SYN -> SYN-ACK | FIN/RST teardown pair | 1+1 with payload | 1+1 other
  > 2 packets (one direction has exactly 1 packet):
             multi-packet with payload (real session) | repeated SYNs, no payload | multi-packet, no payload
  not leaked rows are counted as "not leaked" (shape irrelevant).
"""
import glob, json, os, sys
import numpy as np, pandas as pd

SRC, OUT, MODE = sys.argv[1], sys.argv[2], sys.argv[3]
os.makedirs(OUT, exist_ok=True)
FL = ["syn_flag_counts", "ack_flag_counts", "fin_flag_counts", "rst_flag_counts", "psh_flag_counts"]
CATS = ["lone SYN", "lone SYN-ACK", "lone RST", "lone FIN", "lone ACK, no payload (ghost ACK)", "lone data packet", "lone other",
        "SYN -> RST pair (probe/refused)", "SYN -> SYN-ACK pair", "FIN/RST teardown pair", "1+1 with payload", "1+1 other",
        "multi-packet with payload (session)", "repeated SYNs, no payload", "multi-packet, no payload"]


def categorise(f, b, syn, ack, fin, rst, pay):
    one, two = (f + b) == 1, (f == 1) & (b == 1)
    multi = ~one & ~two
    conds = [one & (syn > 0) & (ack == 0), one & (syn > 0) & (ack > 0), one & (rst > 0) & (syn == 0), one & (fin > 0) & (syn == 0) & (rst == 0),
             one & (ack > 0) & (syn + fin + rst == 0) & (pay == 0), one & (pay > 0) & (syn + fin + rst == 0), one,
             two & (syn > 0) & (rst > 0), two & (syn >= 2), two & (syn == 0) & ((fin > 0) | (rst > 0)) & (pay == 0), two & (pay > 0), two,
             multi & (pay > 0), multi & (syn >= 2) & (pay == 0), multi]
    return np.select(conds, CATS, default="?")


acc = {}
for path in sorted(glob.glob(f"{SRC}/**/*.csv", recursive=True)):
    if os.path.getsize(path) == 0:
        continue
    hdr = list(pd.read_csv(path, nrows=0).columns)
    iat = [c for c in hdr if "IAT" in c]
    cols = iat + FL + ["fwd_packets_count", "bwd_packets_count", "total_payload_bytes", "label"] + (["activity"] if MODE == "activity" else [])
    for ch in pd.read_csv(path, usecols=cols, chunksize=200_000):
        leak = (ch[iat].apply(pd.to_numeric, errors="coerce") > 1e9).any(axis=1).to_numpy()
        n = lambda c: pd.to_numeric(ch[c], errors="coerce").fillna(0).to_numpy()
        cat = categorise(n("fwd_packets_count"), n("bwd_packets_count"), *(n(c) for c in FL[:4]), n("total_payload_bytes"))
        cat = np.where(leak, cat, "not leaked")
        cls = ch["label"].astype(str) if MODE == "label" else ch["label"].astype(str) + " / " + ch["activity"].astype(str)
        for (k, c), v in pd.Series(1, index=pd.MultiIndex.from_arrays([cls.to_numpy(), cat])).groupby(level=[0, 1]).sum().items():
            acc[(k, c)] = acc.get((k, c), 0) + int(v)

T = pd.Series(acc).unstack(fill_value=0)
T = T.reindex(columns=[c for c in CATS + ["not leaked"] if c in T.columns], fill_value=0)
T.loc["ALL"] = T.sum()
T.to_csv(f"{OUT}/leak_shapes_counts.csv")
leaked = T.drop(columns="not leaked", errors="ignore")
share = leaked.div(leaked.sum(axis=1).replace(0, np.nan), axis=0) * 100
share.round(1).to_csv(f"{OUT}/leak_shapes_share_of_leaked.csv")

# coarse grouping for the argument "the leak sits on rows without attack behaviour"
G = {"ghost / fragment (ACK, RST, FIN, teardown)": ["lone ACK, no payload (ghost ACK)", "lone RST", "lone FIN", "FIN/RST teardown pair"],
     "connection attempt (SYN, SYN->RST, SYN->SYN-ACK)": ["lone SYN", "lone SYN-ACK", "SYN -> RST pair (probe/refused)", "SYN -> SYN-ACK pair", "repeated SYNs, no payload"],
     "carries payload (data packet or session)": ["lone data packet", "1+1 with payload", "multi-packet with payload (session)"],
     "other, no payload": ["lone other", "1+1 other", "multi-packet, no payload"]}
coarse = pd.DataFrame({g: leaked[[c for c in cs if c in leaked]].sum(axis=1) for g, cs in G.items()})
coarse_pct = coarse.div(coarse.sum(axis=1).replace(0, np.nan), axis=0) * 100
tot = T.sum(axis=1); lk = leaked.sum(axis=1)

L = [f"# What the leaked rows are: {os.path.basename(SRC.rstrip('/'))}", "",
     "Every leaked row (any IAT > 1e9) classified by packet counts, TCP flags (summed over both directions) and payload. "
     "Script `leak_shapes.py`; full counts `leak_shapes_counts.csv`, shares `leak_shapes_share_of_leaked.csv`.", "",
     "## Coarse view: share of each class's leaked rows", "",
     "| class | rows | leaked | % leaked | " + " | ".join(G) + " |", "|---|---:|---:|---:|" + "---:|" * len(G)]
for k in T.index:
    b = "**" if k == "ALL" else ""
    L.append(f"| {b}{k}{b} | {int(tot[k]):,} | {int(lk[k]):,} | {100 * lk[k] / tot[k]:.1f} | " +
             " | ".join("-" if pd.isna(coarse_pct.loc[k, g]) else f"{coarse_pct.loc[k, g]:.1f}" for g in G) + " |")
L += ["", "## Detailed categories: share of each class's leaked rows (%; categories under 0.5% everywhere omitted)", ""]
keep = [c for c in share.columns if (share[c] >= 0.5).any()]
L += ["| class | " + " | ".join(keep) + " |", "|---|" + "---:|" * len(keep)]
for k in share.index:
    L.append(f"| {k} | " + " | ".join("-" if pd.isna(share.loc[k, c]) else (f"{share.loc[k, c]:.1f}" if share.loc[k, c] else "") for c in keep) + " |")
open(f"{OUT}/LEAK_SHAPES.md", "w").write("\n".join(L) + "\n")
print("\n".join(L[:len(T) + 8]))
