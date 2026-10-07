import sys, pandas as pd
pd.set_option("display.float_format", "{:.6f}".format); pd.set_option("display.max_rows", 200)
df = pd.read_csv(sys.argv[1])
key = [c for c in ["src_ip","dst_ip","src_port","dst_port","packets_count","fwd_packets_count","bwd_packets_count"] if c in df.columns]
iat = [c for c in df.columns if "iat" in c.lower()]
sel = df if len(sys.argv) < 3 else df[df.src_port.astype(str) == sys.argv[2]]
print(sel[key + iat].T.to_string())
