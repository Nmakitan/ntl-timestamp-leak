# NTLFlowLyzer timestamp leak

A reproducible data-leak finding in [NTLFlowLyzer](https://github.com/ahlashkari/NTLFlowLyzer) and the BCCC
intrusion-detection datasets built with it: when a flow direction contains exactly one packet, `calculate_IAT`
returns the packet's **absolute Unix epoch timestamp** instead of an inter-arrival time, writing the capture
time into the IAT features. The leak affects 35–65% of rows across three published datasets and inflates model
accuracy on random splits. See `00_MASTER/` for the full write-up and `01_reproducer/` for a 21-packet
minimal reproducer.

**Start here:** `00_MASTER/NTL_master_summary.md` (executive summary) → `01_reproducer/RESULTS.md` (reproduce the
bug) → `02_census/` (how much data is affected) → `03`–`06` (does it change model results).

Every result is organised by stage below. This repository contains the code, write-ups, figures, and the small
result tables (`.csv`/`.json`/`RESULTS.md`). Large regenerable binary arrays and the raw third-party capture are
**not committed** — they are listed in `EXTERNAL_DATA.md` with instructions to regenerate them from the published
datasets. `MANIFEST.tsv` records every file's origin.

| folder | what it holds | key files |
|---|---|---|
| 00_MASTER | the compiled findings | NTL_timestamp_leak_MASTER.md (everything), NTL_all_metrics.md (every metric of every run, with legend), NTL_paper_draft.md (abstract, argument, key tables), NTL_master_summary.md (executive summary), NTL_timestamp_leak_REPORT.md (sections 0-11) |
| 01_reproducer | minimal 21-packet pcap reproducing the bug on upstream NTLFlowLyzer | RESULTS.md, repro.pcap, repro_out.csv, repro_out_fork.csv |
| 02_census | leak census of each dataset: per class, per file, rule check, calendar, flow shapes | */RESULTS.md, */per_class.csv, */LEAK_SHAPES.md, combined/COMBINED.md |
| 03_exp1_shipped_models_timestamp_change | shipped 2018 RF / KNN / ensemble re-scored with only the timestamps changed | RESULTS.md, RESULTS_exp1b.md, exp1_results.json, exp1b/exp1b_results.json |
| 04_exp2_timestamp_only | decision tree on the timestamp alone, three datasets, random and temporal splits; 2017 also leave-one-day-out | */*_tree.json, 2018/SUMMARY.md, 2017_lodo/RESULTS.md (binary table, all splits) — split arrays external, see EXTERNAL_DATA.md |
| 05_exp3_rf_retrain | RandomForest retrained leaky / fixA / fixB: 2018 (4 seeds), 2017 (seed 0) | 2018/SUMMARY.md, 2018/runs/*.json, 2017/RESULTS_exp3_2017.md |
| 06_model_comparison | seven model families x three datasets x two splits x five conditions (120 runs); plus leave-one-day-out on 2017 (DT / RF / GNB x 5 held-out days x leaky / fixA, 30 runs, binary attack-vs-benign scoring) | SUMMARY.md, ALL_RUNS_pooled.csv, BOOTSTRAP_CI.csv, ZERO_CHECK.json, runs/*.json, LODO_2017.md, LODO_2017.csv, runs/d2017_lodo_*.json |
| 07_literature | works naming the BCCC datasets, counted / excluded with reasons | literature_screen.csv |
| code | every script, by stage | |

## Licensing

- **Code** (`code/`, `*.py`, `*.sh`): MIT — see `LICENSE`.
- **Documentation, figures, result tables** (`*.md`, `*.png`, `*.csv`, `*.json`): CC BY 4.0 — see `LICENSE-docs.md`.
- **Datasets and upstream NTLFlowLyzer** are not redistributed here; they keep their own licenses (see `EXTERNAL_DATA.md`).
