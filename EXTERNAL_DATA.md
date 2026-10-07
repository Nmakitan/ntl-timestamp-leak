# Large data kept outside this directory

| what | where |
|---|---|
| 2018 published CSVs (34 per-day files) | `<data drive>/Dataset (see 02_census/2018*/file_list.txt)` |
| 2018 train/test arrays used by experiments 1-3 | `<data drive>/Dataset/ml_module_output/_intermediate` |
| 2018 model-comparison matrices | `/home/nik/pew2/ntl_models_cache` |
| 2017 feature cache (X.npy + meta) | `/home/nik/Desktop/ntl_census_multi/BCCC-CIC-IDS-2017/exp3/cache` |
| cPacket feature cache (X.npy + meta) | `/home/nik/Desktop/ntl_census_multi/BCCC-cPacket-Cloud-DDoS-2024/cache` |

## Excluded from this public repository (and how to regenerate)

To keep the repository small and reviewable, the following are **not committed**. All are derived
artifacts regenerable from the published datasets with the scripts in `code/`.

| excluded | size | regenerate with |
|---|---|---|
| Prediction arrays `*.npy` (exp1/exp3) | ~26 MB | `code/03_exp1/*.py`, `code/04_05_exp23/exp3_run.py` |
| Split / subsample caches `*.npz` (exp2, model-comparison) | ~110 MB | `code/04_05_exp23/*.py`, `code/06_model_comparison/mc_*.py` |
| Symlinked feature/prediction arrays (567 MB) | 567 MB | re-run the stage that produced them (see per-stage RESULTS.md) |
| `06_wireshark_figure/UCAP172.31.69.28_22-02.pcap` | 25 MB | official CIC-IDS2018 capture; stream via `06_wireshark_figure/s3zip.py` |
| `06_wireshark_figure/cic2018_sqli_port59823.pcap` | 4 KB | extracted from the CIC-IDS2018 capture above |

The committed `*.csv` / `*.json` / `RESULTS.md` summaries contain every reported number; the excluded
binaries are only needed to re-derive them. The published PNG figures in `06_wireshark_figure/` are kept.

The minimal reproducer (`01_reproducer/repro.pcap`) is **synthetic and self-contained** — it is committed and
regenerates bit-for-bit via `code/01_reproducer/make_pcap.py` (sha256 in `01_reproducer/repro.pcap.sha256`).
