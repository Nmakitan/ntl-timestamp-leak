"""Shared file discovery / reading for the Step 2 census of BCCC-CSE-CIC-IDS2018."""
import glob, os, subprocess, contextlib
import pandas as pd

ROOT = "/home/USER/pew/Dataset"

def list_files():
    """Original per-day files. Extracted CSV preferred; inner zip used only if no CSV twin exists."""
    fs = [f for f in glob.glob(f"{ROOT}/*/**/*.csv", recursive=True) + glob.glob(f"{ROOT}/*/**/*.zip", recursive=True)
          if "/ml_module_output/" not in f]
    csvs = {f[:-4] for f in fs if f.endswith(".csv")}
    return sorted((f for f in fs if f.endswith(".csv") or f[:-4] not in csvs), key=os.path.basename)

@contextlib.contextmanager
def open_csv(path, check=False):
    """Text stream of the CSV; inner zips are Deflate64, so stream them through `unzip -p`."""
    if path.endswith(".zip"):
        p = subprocess.Popen(["unzip", "-p", path], stdout=subprocess.PIPE)
        ok = False
        try:
            yield p.stdout
            ok = True
        finally:
            if ok and check:  # full scans only: stream must have ended cleanly
                if p.stdout.read(1) or p.wait() != 0:
                    raise OSError(f"unzip -p {path} failed (exit {p.returncode}); stream truncated or unread")
            p.stdout.close(); p.kill(); p.wait()
    else:
        with open(path, "rb") as fh:
            yield fh

def header(path):
    with open_csv(path) as fh:
        return list(pd.read_csv(fh, nrows=0).columns)

def name(path):
    return os.path.basename(path).removesuffix(".zip").removesuffix(".csv")
