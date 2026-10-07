# NTLFlowLyzer timestamp leak in BCCC-CSE-CIC-IDS2018: full findings

Final, 2026-10-02. All steps complete. Experiment 3 uses **seeds 0-3** for all six split × variant combinations
(24 runs); the seed-4 tier was stopped by decision, and its two completed runs are kept aside in
`results/exp3/excluded_seed4/` and not used.

---

## 0. Summary

1. **Bug (Step 1).** Upstream NTLFlowLyzer writes the flow's absolute start time (Unix epoch) into the IAT features of
   any direction that contains exactly one packet. Reproduced from a 21-packet synthetic pcap on unmodified upstream
   code; the author's fork gives byte-identical output. A second bug splits the closing ACK of a FIN exchange into
   its own 1-packet "ghost" flow, which then also leaks.
2. **Dataset (Step 2).** 17,108,403 of 48,182,782 rows (35.5%) in the published BCCC-CSE-CIC-IDS2018 CSVs carry an
   epoch timestamp in their IAT columns; every class is affected (0.07% to 100%). The leak follows the code's rule
   with **0 violations in 48.2M rows**, so the dataset was built with the same buggy code. Every leaked value is the
   flow's true UTC start time and falls inside that class's capture window.
3. **Existing models (Experiment 1).** Changing only the leaked timestamps changes predictions. The RF loses 20,381
   correct attack detections that depended only on the timestamp; KNN and the soft-voting ensemble fall from
   **0.993 to 0.871** accuracy, i.e. their whole advantage over the RF comes from the leak.
4. **Timestamp alone (Experiment 2).** A pre-specified decision tree on the single timestamp feature identifies the
   leaked attack rows under a random split (mean attack-class recall 0.80, pooled attack-row recall 1.000;
   95.2% of all leaked test rows correct; 61.1% under the temporal split).
5. **Retraining (Experiment 3, 4 seeds).** Random split: leaky 0.9976 vs fixed 0.9533, so the leak **inflates**
   accuracy by 4.4 points (Bot recall 1.00 vs 0.50). Temporal split: leaky 0.8919 vs fixed 0.9645, so the leak
   **hurts** by 7.3 points. On the same multi-packet rows all variants score ~0.999-1.000: the entire effect sits in
   the 1-packet (ghost-type) flows, ~29-32% of the test set.
6. **Other datasets (§9).** BCCC-CIC-IDS-2017 (38.5% of rows leaked) and BCCC-cPacket-Cloud-DDoS-2024 (65.4%) show the same defect with 0 rule violations and every leaked value on its capture day. With the pre-specified timestamp-only tree on a random split, the timestamp alone identifies the leaked attack rows in all three datasets (pre-specified balanced tree: mean attack-class recall 0.80 / 0.90 / 0.98 for 2018 / 2017 / cPacket; pooled attack-row recall 1.000 / 0.997 / 0.990). Outside two probe-type classes (2017 Port_Scan, Botnet_ARES) and one SYN attack (cPacket BYPass-V1), the leaked attack rows are fragments or generic SYN/RST shapes without attack content. BCCC-DLLayer-IDS-2025 is not NTLFlowLyzer output and carries no timestamps.
7. **Replication retrain on 2017 (§11, seed 0).** Random split: leaky 0.9915 vs fixed 0.8753, the leak inflates accuracy by **11.6 points** (2018: 4.4). Multi-packet rows: no difference again. Temporal split: unlike 2018 the leaky model is better overall (0.940 vs 0.833) although it still loses several attack classes on leaked rows; see §11.7.

---

## 1. Step 1: minimal reproducer

**Setup.** Upstream `ahlashkari/NTLFlowLyzer` at commit `d99cd5377faaed53b39450ce262652902501188d` (2026-05-28),
clean clone (`~/Desktop/NTLFlowLyzer`), version 0.1.0 (setup.py; the CLI has no `--version`), own venv,
Python 3.12.3, Linux. Thresholds set to 1 so every flow is written
(`feature_extractor_min_flows`, `writer_min_rows`, `check_flows_ending_min_flows`, `capturer_updating_flows_min_value`).

**Test pcap** (`repro.pcap`, sha256 `61ea9c3ed384b17f1048a8546496660105882ed598079ca683a71bc4df8a3e87`, 21 packets,
classic pcap, T0 = 1519308000 = 2018-02-22 14:00:00 UTC).

| Flow | Port | Packets (fwd/bwd) | Epoch-valued IAT columns | Value | = packet time? |
|---|---|---|---|---|---|
| A, lone SYN | 40001 | 1 (1/0) | combined + fwd | 1519308000.0 | yes (T0) |
| B, SYN / SYN-ACK / RST | 40002 | 3 (1/2) | fwd only | 1519308010.0 | yes (T0+10) |
| C, main flow | 40003 | 7 (4/3) | none | 0.01-0.04 | - |
| C, ghost (trailing ACK) | 40003 | 1 (1/0) | combined + fwd | 1519308020.08 | yes |
| D, control | 40004 | 8 (4/4) | none | 0.01-0.02 | - |
| E, lone SYN +1 year | 40005 | 1 (1/0) | combined + fwd | 1550844000.0 | yes, exactly A + 31,536,000 |

- Affected statistics per direction: mean, max, min, total, median, mode (std/variance/cov = 0, skewness = NaN).
  A direction with 0 packets gets IAT 0, not a timestamp: the leak is exactly "one packet in that direction".
- **Root cause:** `NTLFlowLyzer/features/utils.py:20-27`, `calculate_IAT`: when `len(times) == 1` the raw timestamp
  list is returned instead of differences.
- **Ghost flow:** 5 conversations produced 6 flows. A flow ends as soon as both sides have sent FIN
  (`network_flow_capturer/network_flow_capturer.py:305-311`, `has_two_FIN_flags`), so the final ACK opens a new flow.
- No flows dropped (both lone SYNs present).
- The `timestamp` column and the time inside `flow_id` are rendered in local time (machine TZ); IAT values are true epoch.
- **Fork check:** `Nmakitan/NTLFlowLyzer` @ `31c677c` (upstream + 2 commits touching only continuous-batch polling in
  `network_flow_capturer.py`) gives byte-identical output (`cmp`). The fork neither causes nor changes the bug.

Files: `~/Desktop/ntl_repro_step1/` (make_pcap.py, repro.pcap + sha256, repro_config.json, repro_out.csv,
repro_out_fork.csv, run logs, env.txt, RESULTS.md).

---

## 2. Step 2: census of the published dataset

**Data.** 34 original per-day files, 10 capture days, 48,182,782 rows, one identical 323-column header. Inner files
dated 2023-07..2023-11, archive entries 2024-02-23, downloaded 2026-09-04. Wed 28-02 has no attack file in the published
zip. Days 14-02, 15-02, 01-03 read from their inner zips (Deflate64, streamed with `unzip -p`). 0 files failed.
Leak = IAT value > 1e9. Column names: 30 IAT columns (10 combined `packets_IAT_*`/`packet_IAT_*`, 10 `fwd_packets_IAT_*`,
10 `bwd_packets_IAT_*`), `packets_count`, `fwd_packets_count`, `bwd_packets_count`, `label`, `timestamp`.

### 2.1 Per class

| Class | n | 1-packet | fwd leak | bwd leak | **any leak** | **%** | leak, >1 packet | % of leaked |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| Benign | 43,092,133 | 13,651,434 | 10,073,077 | 6,668,739 | 15,465,054 | 35.89 | 1,813,620 | 11.7 |
| Bot | 286,099 | 142,915 | 199 | 143,113 | 143,114 | 50.02 | 199 | 0.1 |
| Brute_Force_FTP | 193,360 | 0 | 193,360 | 193,360 | 193,360 | 100.00 | 193,360 | 100 |
| Brute_Force_SSH | 188,444 | 93,841 | 161 | 93,740 | 93,871 | 49.81 | 30 | 0.03 |
| Brute_Force_Web | 536 | 264 | 72 | 192 | 264 | 49.25 | 0 | 0 |
| Brute_Force_XSS | 232 | 115 | 3 | 112 | 115 | 49.57 | 0 | 0 |
| DDoS_HOIC | 2,164,586 | 1,082,292 | 1 | 1,082,292 | 1,082,293 | 50.00 | 1 | 0 |
| DDoS_LOIC_HTTP | 289,527 | 199 | 199 | 0 | 199 | 0.07 | 0 | 0 |
| DoS_Golden_Eye | 29,485 | 2,624 | 2,625 | 1 | 2,625 | 8.90 | 1 | 0.04 |
| DoS_HULK | 1,824,450 | 15,477 | 10,576 | 12,334 | 21,140 | 1.16 | 5,663 | 26.8 |
| DoS_SlowHTTP | 105,550 | 0 | 105,550 | 105,550 | 105,550 | 100.00 | 105,550 | 100 |
| DoS_Slowloris | 8,269 | 765 | 508 | 257 | 765 | 9.25 | 0 | 0 |
| Infiltration | 5 | 1 | 0 | 1 | 1 | 20.00 | 0 | 0 |
| SQL_Injection | 106 | 52 | 23 | 29 | 52 | 49.06 | 0 | 0 |
| **All** | **48,182,782** | 14,989,979 | 10,386,354 | 8,299,720 | **17,108,403** | **35.51** | 2,118,424 | 12.4 |

- FTP and SlowHTTP flows are 2-packet flows (1 fwd + 1 bwd), so both directions leak in every row.
- HOIC, Bot, SSH, Web, XSS, SQLi: ~50%, nearly all backward. Half of their flows are 1-packet ghost flows.
- Benign in the four largest single-file days: 28.8-36.2%, stable across days (all files: `out/per_file.csv`).

### 2.2 Rule check and value check

- fwd leak <=> `fwd_packets_count == 1`, bwd leak <=> `bwd_packets_count == 1`, combined leak <=> `packets_count == 1`:
  **0 violations in 48,182,782 rows** for all three.
- Leaked fwd value − `timestamp` column = exactly **+18,000 s** in 96-100% of rows per file (100% in most attack files);
  the rest within ~5 s. The `timestamp` column (and `flow_id` time) is local UTC−5; the leaked IAT is the true UTC epoch
  of the flow start.

### 2.3 Calendar of leaked values (UTC)

Each attack file's leaked values fall on its own capture day in a narrow window:
FTP 14-02 14:33-16:10 · SSH 14-02 18:01-19:32 · GoldenEye 15-02 13:27-14:11 · Slowloris 15-02 15:41-15:42 ·
SlowHTTP 16-02 14:12-15:05 · HULK 16-02 17:45-17:58 · LOIC 20-02 14:24-14:33 · HOIC 21-02 18:11-19:05 ·
Web 22-02 14:13-15:23 and 23-02 14:04-15:03 · XSS 22-02 17:51-18:29 and 23-02 17:01-18:10 ·
SQLi 22-02 20:14-20:27 and 23-02 19:05-19:17 · Infiltration 01-03 19:37 · Bot 02-03 14:13-19:54.
Benign spans each day ~12:20 UTC to ~00:40 the next day.

**Anomaly (not yet checked):** some benign files contain leaked values from other days (fri_23_02 benign: 3,250 rows from
21-22 Feb; fri_02_03 benign: 6,849 rows incl. 27-28 Feb); wed_28_02 and fri_02_03 benign share an identical minimum leaked
value (2018-02-27 12:18:27.392139), wed_28_02 and thu_01_03 an identical maximum. Possibly duplicated rows across day files.

### 2.4 Other columns

- Values in 1.4e9-2.2e9 occur systematically only in the 18 IAT mean/max/min/total/median/mode columns.
- Non-IAT hits: `avg_bwd_bulk_rate` 360,968; `avg_fwd_bulk_rate` 405; `bytes_rate` 336; `fwd_bytes_rate` 279;
  `bwd_bytes_rate` 95; `variance_packets_delta_len` / `variance_payload_bytes_delta_len` 71. Hand check: spread
  uniformly over the range, none within a day of the flow start: **not timestamps**. The bulk rates are implausible
  (1.6e9 B/s on flows with `bytes_rate` ~42 B/s), a separate artifact. The variance hits (Bot, ~486 KB payloads) are genuine.
- Placeholder columns `delta_start` (e.g. −0.0004, −4.3) and `handshake_duration` (e.g. 0.0002) are durations, not timestamps.

Files: `~/Desktop/ntl_census_step2/` (common.py, census.py, report.py, file_list.txt, RESULTS.md, out/ with
per_class.csv, per_file.csv, leak_date_ranges.csv, leak_hours.csv, fwd_leak_offset_vs_timestamp.csv,
column_scan.csv, non_numeric_samples.json).

---

## 3. The models under test

From `~/trained_models/` (`IDS_MODELS_SUMMARY.txt`, `train_ml_module.py`):
- **Training set:** 3,261,675 rows; **test set:** 1,087,223 rows (the temporally latest 25% of each per-day file,
  capped per class and day), 313 numeric features (identity columns, `timestamp`, `delta_start`, `handshake_duration`
  dropped), 9 classes (Benign, Bot, Brute_Force_Web, Brute_Force_XSS, DDoS_HOIC, DDoS_LOIC_HTTP, DoS_HULK,
  DoS_SlowHTTP, SQL_Injection). All features stored as float32, so leaked timestamps are on a 128 s grid.
- **RF** (`rf_model.onnx`): 200 trees, max_depth 30, min_samples_leaf 10, class_weight balanced, random_state 42,
  trained on the full training set, no scaling.
- **KNN** (`knn_model.onnx`): StandardScaler → KNeighborsClassifier(weights="distance"), 600k-row stratified subsample.
- **Ensemble** (`ensemble_model.onnx`): soft voting of an RF and the KNN, both fit on the same 600k subsample.
- Test counts: Benign 587,523 · Bot 71,525 · Web 134 · XSS 58 · HOIC 250,175 · LOIC 72,382 · HULK 79,013 · SlowHTTP 26,387 · SQLi 26.

---

## 4. Experiment 1: change only the timestamps in the test set (existing models)

Leaked test rows: 359,693 of 1,087,223 (33.1%): Benign 197,191 · Bot 35,830 (50.1%) · HOIC 97,477 (39.0%) ·
SlowHTTP 26,387 (100%) · HULK 2,698 (3.4%) · Web 66 · XSS 30 · SQLi 14 · LOIC 0.
Conditions: **+8 years** (+252,460,800 s), **+1 day**, **shuffle** (each leaked row takes another leaked row's
timestamp, one offset applied to all its leaked cells; 5 seeds), **zero** (leaked cells = 0: bug-fixed data fed to the
leaky model, not a retrain). Arithmetic in float64, cast to float32 for scoring. Sanity check: predictions on
non-leaked rows unchanged in every condition (passed everywhere).

### 4.1 RF on the full test set

Baseline 0.8919 on all rows (the previously quoted 0.8928 was on a 200k sample).

| Condition | Acc all | Macro-F1 all | Acc leaked | Macro-F1 leaked | Predictions changed |
|---|---|---|---|---|---|
| Baseline | 0.8919 | 0.7560 | 0.6736 | 0.2995 | - |
| +8 years | 0.8749 | 0.7916 | 0.6220 | 0.2074 | 22,226 |
| +1 day | 0.8381 | 0.7346 | 0.5110 | 0.2065 | 121,075 |
| Shuffle (5 seeds) | 0.8763 ± 0.0000 | 0.7340 ± 0.0004 | 0.6264 ± 0.0001 | 0.2192 ± 0.0001 | 32,526 ± 68 |
| Zero | 0.8749 | 0.7916 | 0.6220 | 0.2074 | 22,226 |

- 20,381 correct detections exist only because of the timestamp (HOIC 19,992, Bot 306, HULK 61, SQLi 14 of 26,
  XSS 6, Web 2); all flip to Benign under +8y / zero. HOIC recall 0.690 → 0.610, SQLi 0.96 → 0.42.
- The leak also causes false alarms: 1,845 leaked Benign rows predicted SQL_Injection at baseline (SQLi precision 0.013;
  0.69 without the timestamp). That is why macro-F1 rises under +8y.
- +1 day: 100,689 Benign rows become SQL_Injection. The model keys on day and hour, not just "2018".
- +8y and zero give identical predictions: outside the trained windows the trees fall back to Benign.
- Controls: LOIC (0 leaked rows) unchanged; HULK −61 rows; SlowHTTP (100% leaked) stays at recall 1.0.
- At baseline the RF already misses most leaked attack rows (Bot leaked recall 0.0085): the temporal test set lies after
  the training windows, which blunts the leak for threshold-based models.

### 4.2 KNN and ensemble (stratified 20,001-row sample)

ONNX KNN runs at ~4 rows/s here, so a sample: stratified by (class, leaked), with all SQLi/XSS/Web rows; 6,654 leaked.
Only leaked rows + 200 sanity rows rescored per condition (sanity rows unchanged in all 16 runs). Identical inputs to
4.1 (same construction, same shuffle seeds). Population-weighted accuracy; the RF on this sample reproduces its
full-test numbers within 0.001.

| Condition | RF | KNN | Ensemble |
|---|---|---|---|
| Baseline | 0.8930 | **0.9934** | **0.9934** |
| +8 years | 0.8750 | 0.8713 | 0.8714 |
| +1 day | 0.8384 | 0.9036 | 0.9036 |
| Shuffle (5 seeds) | 0.8764 ± 0.0006 | 0.9195 ± 0.0023 | 0.9192 ± 0.0023 |
| Zero | 0.8750 | 0.8709 | 0.8709 |
| Leaked rows, baseline → +8y | 0.669 → 0.612 | 0.990 → 0.614 | 0.991 → 0.614 |

Recall baseline → +8y (KNN / ensemble): Bot 0.935/0.933 → 0.446 · HOIC 1.000 → 0.610 · Web 0.978/0.918 → 0.485 ·
XSS 0.966 → 0.483 · LOIC, SlowHTTP, Benign unchanged, HULK 0.969 → 0.969.

- KNN/ensemble owe their ~0.99 to the timestamp: without it they equal the RF (0.87).
- Mechanism: after standard scaling a ~1.5e9 IAT dominates the Euclidean distance, so the nearest neighbours are the
  training flows closest in time = same capture window = same class. Unlike the RF's fixed thresholds, "nearest in time"
  still works for test flows just after the training window, so the temporal split does not protect KNN.
- +1 day: all 1,774 leaked HOIC rows (21 Feb) become Brute_Force_Web (22 Feb); Web precision 0.001.
- SQLi for KNN: recall 0.19 at baseline and in every condition (26 rows).

Files: `~/Desktop/ntl_exp1/` (exp1.py, exp1_results.json, pred_*.npy, RESULTS.md, RESULTS_exp1b.md, exp1b_*.py,
exp1b/report.txt, exp1b/exp1b_results.json).

---

## 5. Experiment 2: timestamp as the only feature

Feature `t` = smallest leaked IAT in the row (0 if none). Random split = original train + test pooled (4,348,898 rows),
stratified 75/25 by label, `random_state=0` (indices in `~/Desktop/ntl_exp23/exp3/random_split_idx.npz`).

| Split | Model | Acc all | Macro-F1 all | **Acc leaked** | Macro-F1 leaked | n test | n leaked |
|---|---|---|---|---|---|---|---|
| random | most_frequent | 0.5404 | 0.0780 | 0.5262 | 0.0766 | 1,087,225 | 398,418 |
| random | stratified | 0.3598 | 0.1113 | 0.3648 | 0.1019 | 1,087,225 | 398,418 |
| random | tree (depth 20) | 0.4153 | 0.3688 | **0.9517** | 0.5462 | 1,087,225 | 398,418 |
| temporal | most_frequent | 0.5404 | 0.0780 | 0.5482 | 0.0787 | 1,087,223 | 359,693 |
| temporal | stratified | 0.3600 | 0.1115 | 0.3678 | 0.1030 | 1,087,223 | 359,693 |
| temporal | tree (depth 20) | 0.2687 | 0.1327 | 0.6109 | 0.1898 | 1,087,223 | 359,693 |

- Under a random split the timestamp alone identifies the class of 95% of leaked rows.
- Overall accuracy of the tree is low only because all non-leaked rows share t = 0 and fall into one balanced-weighted leaf.
- Under the temporal split the timestamp alone barely beats always-Benign on leaked rows (0.611 vs 0.548).
- Post-hoc check (added later, not pre-specified): the same tree without class weighting gives 0.955 (random) and 0.610 (temporal) on leaked rows; see §9 for both models across all three datasets.

---

## 6. Experiment 3: retrain with and without the leak

**Variants.** `leaky` = data as is; `fixA` = every leaked IAT cell set to 0 in train and test (equals the per-direction
code fix, given 0 rule violations); `fixB` = fixA + all rows with `packets_count == 1` dropped from train and test.
**Splits.** `temporal` = existing split; `random` = Experiment 2's saved indices. Split fixed across seeds.
**Model.** `RandomForestClassifier(n_estimators=200, max_depth=30, min_samples_leaf=10, class_weight="balanced",
n_jobs=2, random_state=seed)`, 313 features, sklearn predict (no ONNX). Each run ~15-27 min, peak RSS 5.3-6.7 GB.
**Pipeline check:** temporal-leaky s0 = 0.8919, identical to the original model.
**Leak check:** split thresholds > 1e9: leaky models 17,741-22,657 per forest (~40% of all split nodes, all on IAT
features); fixA/fixB models 0, except `random_fixA_s2` with 1 threshold on a **non-IAT** feature (one of the rate
columns in §2.4; not a timestamp).

### 6.1 All test rows (mean ± std, seeds 0-3)

| Split | Variant | Accuracy | Macro-F1 | Benign | Bot | Web | XSS | HOIC | LOIC | HULK | SlowHTTP | SQLi |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| temporal | leaky | 0.8919 ± 0.0000 | 0.7566 ± 0.0032 | 0.997 | 0.502 | 0.507 | 0.603 | 0.690 | 1.000 | 0.968 | 1.000 | 0.962 |
| temporal | fixA | 0.9645 ± 0.0001 | 0.7770 ± 0.0100 | 0.999 | 0.502 | 0.978 | 0.966 | 1.000 | 1.000 | 0.968 | 1.000 | 0.615 |
| temporal | fixB* | 0.9991 ± 0.0000 | 0.9694 ± 0.0039 | 1.000 | 0.993 | 0.985 | 1.000 | 1.000 | 0.999 | 0.996 | 1.000 | 0.917 |
| random | leaky | 0.9976 ± 0.0008 | 0.8229 ± 0.0010 | 0.996 | 1.000 | 0.993 | 0.966 | 1.000 | 1.000 | 1.000 | 1.000 | 0.894 |
| random | fixA | 0.9533 ± 0.0020 | 0.7635 ± 0.0225 | 0.974 | 0.503 | 0.978 | 0.966 | 1.000 | 0.999 | 0.998 | 1.000 | 0.731 |
| random | fixB* | 1.0000 ± 0.0000 | 0.9859 ± 0.0006 | 1.000 | 1.000 | 1.000 | 0.972 | 1.000 | 1.000 | 1.000 | 1.000 | 0.933 |

\* fixB is scored on a smaller, different test set (1-packet rows removed): temporal 776,198 rows, random 738,622.
Class columns are recall (std ≤ 0.004 except XSS temporal-leaky 0.034, Web temporal-fixB 0.017, SQLi random-leaky 0.019).

### 6.2 Leaked test rows (rows leaked in the unmodified data, seeds 0-3)

| Split | Variant | Accuracy | Macro-F1 | Benign | Bot | Web | XSS | HOIC | HULK | SQLi |
|---|---|---|---|---|---|---|---|---|---|---|
| temporal | leaky | 0.6736 | 0.304 | 0.991 | 0.009 | 0.030 | 0.233 | 0.205 | 0.088 | 1.000 |
| temporal | fixA | 0.8933 | 0.443 | 0.998 | 0.010 | 0.955 | 0.933 | 1.000 | 0.066 | 0.357 |
| random | leaky | 0.9935 | 0.727 | 0.988 | 1.000 | 0.984 | 0.955 | 1.000 | 0.994 | 0.818 |
| random | fixA | 0.8727 | 0.508 | 0.929 | 0.007 | 0.952 | 0.955 | 1.000 | 0.825 | 0.455 |

### 6.3 Rare classes, exact counts (correct / support, seeds 0, 1, 2, 3)

| Split | Variant | SQL_Injection | Brute_Force_XSS | Brute_Force_Web |
|---|---|---|---|---|
| temporal | leaky | 25/26 ×4 | 34, 38, 34, 34 /58 | 68/134 ×4 |
| temporal | fixA | 16/26 ×4 | 56/58 ×4 | 131/134 ×4 |
| temporal | fixB | 11/12 ×4 | 28/28 ×4 | 68, 66, 66, 68 /68 |
| random | leaky | 24, 23, 23, 23 /26 | 56/58 ×4 | 133/134 ×4 |
| random | fixA | 19/26 ×4 | 56/58 ×4 | 131/134 ×4 |
| random | fixB | 14/15 ×4 | 35/36 ×4 | 72/72 ×4 |

### 6.4 Differences (mean leaky − mean fixed)

| Split | Comparison | Δ accuracy | Δ macro-F1 | Main per-class Δ recall |
|---|---|---|---|---|
| temporal | leaky − fixA | **−0.0726** | −0.020 | Web −0.470, XSS −0.362, HOIC −0.310, SQLi +0.346 |
| random | leaky − fixA | **+0.0443** | +0.059 | Bot +0.497, Benign +0.021, SQLi +0.163 |
| temporal | leaky − fixB* | −0.1072 | −0.213 | (different test rows) |
| random | leaky − fixB* | −0.0024 | −0.163 | (different test rows) |

### 6.5 Same rows: all variants on the multi-packet test rows (seeds 0-2)

| Split | Multi-packet test rows (leaked) | leaky acc / mF1 | fixA acc / mF1 | fixB acc / mF1 |
|---|---|---|---|---|
| temporal | 776,198 of 1,087,223 (48,668) | 0.9992 / 0.966 | 0.9991 / 0.967 | 0.9991 / 0.968 |
| random | 738,622 of 1,087,225 (49,815) | 1.0000 / 0.990 | 1.0000 / 0.981 | 1.0000 / 0.986 |

### 6.6 Interpretation

- **Random split (common protocol): the leak inflates results** (+4.4 accuracy, +5.9 macro-F1). Nearly all of it is Bot:
  its leaked half (1-packet backward ghost flows) is recognised only through the timestamp (recall 1.00 → 0.50).
- **Temporal split: the leak hurts** (−7.3). The leaky RF learns capture windows that do not carry over to the later test
  period. Removing the timestamp fixes HOIC (0.69 → 1.00), Web (68 → 131 of 134) and XSS (34-38 → 56 of 58); SQLi falls
  (25 → 16 of 26) because its detection depended on the timestamp.
- **Everything happens in the 1-packet flows.** On multi-packet rows all variants are equal (~0.999-1.000), and the ~49k
  leaked multi-packet rows per split do not measurably change accuracy. For this RF, dropping 1-packet flows removes the
  effect entirely; but it also removes about half of every rare class (SQLi 12-15 of 26, XSS 28-36 of 58, Web 68-72 of 134).
- **Clean ceiling with 1-packet flows kept:** ~0.95-0.96 on both splits, limited by 1-packet flows that carry no
  information besides the timestamp (Bot recall ~0.50 in every fixed model).

Files: `~/Desktop/ntl_exp23/` (common23.py, build_train_npy.py, exp2_run.py, exp3_run.py, summarize.py, queue23.py;
results/exp2/*.json + SUMMARY.md; results/exp3/runs/*.json + *.pred.npy, results/exp3/SUMMARY.md,
results/exp3/same_rows_analysis.md; results/QUEUE_STATUS.txt; results/logs/).

---

## 7. Methods notes and deviations

- **Training arrays rebuilt.** `train_X.npy`/`train_y.npy` did not exist (the original pipeline trained straight from
  `combined_train.csv`). Rebuilt with the original `load_xy` logic (float32, feature_order.json, label_mapping.json);
  the same method re-derived the test set from `combined_test.csv` identical to `test_X.npy`/`test_y.npy` in all
  1,087,223 rows. Train class counts match `row_counts.json` exactly.
- **"Leaked test rows"** = that run's test rows leaked in the unmodified data (same subset for leaky and fixA within a
  split; fixB has fewer).
- **Memory cap** per run: `systemd-run --user --scope -p MemoryMax=6.5G` plus `-p MemorySwapMax=0` (added so a run over
  the cap is killed rather than swapping). No run was killed.
- **Seeds:** Experiment 3 uses seeds 0-3 (the spec planned 0-4; seed 4 dropped); the original model used 42.
- **KNN/ensemble** evaluated on a stratified sample because ONNX KNN inference runs at ~4 rows/s on this machine.
- **Bad disk sector:** the external dataset drive (WD My Passport, 1 TB) has 1 pending sector (SMART PASSED,
  0 reallocated). The census read every file fully. The original training build's `stream_csv_resilient` skips 5,000
  rows after a read error, so the training set may be missing up to 5,000 rows from one file; worth a line in methods.
- Float32 storage puts leaked timestamps on a 128 s grid; the +1 day and +8 year shifts are exact multiples of 128 s.

---

## 8. Open items

1. **Gate 1:** compare the per-class census (§2.1) with the threshold written down before Step 2.
2. **Seeds:** Experiment 3 final with seeds 0-3 (seed-to-seed std ≤ 0.002 in accuracy); seed 4 dropped.
3. **Possible duplicate benign rows** across day files (§2.3): a targeted `flow_id` check (~20 min).
4. **Bulk-rate artifact** (§2.4): implausible `avg_bwd_bulk_rate` values; separate from the timestamp bug.
5. **Upstream issue:** Step 1 material (pcap, config, output, commit) is ready to attach; root cause
   `features/utils.py:20-27` and `network_flow_capturer.py:305-311`.
6. **Generality:** census and timestamp-only baseline on 2017 / 2018 / 2023 (§9) and a single-seed 2×2 retrain on 2017 (§11): random-split inflation and the 1-packet locus replicate; the temporal-split harm does not replicate overall (§11.7).
7. **Disk:** run `sudo smartctl -t long /dev/sda` and back up irreplaceable files on that drive.

---

## 9. Other BCCC datasets: census, flow shapes and exploitability

Census (pass 1 triage + pass 2 full census, same measures as §2) on BCCC-CIC-IDS-2017, BCCC-cPacket-Cloud-DDoS-2024 and BCCC-DLLayer-IDS-2025; flow-shape classification of the leaked rows; timestamp-only baseline on all three NTLFlowLyzer datasets. Details: `~/Desktop/ntl_census_multi/`.

| dataset | NTLFlowLyzer | columns | rows | leaked rows | % leaked | rule-check violations | timestamp column | leaked values on capture days |
|---|---|---:|---:|---:|---:|---:|---|---|
| BCCC-CSE-CIC-IDS2018 | yes | 323 | 48,182,782 | 17,108,403 | 35.51 | 0 | local, UTC-5 | yes: every attack file within its own day/window; some benign rows on adjacent days (see 2018 report §2.3) |
| BCCC-CIC-IDS-2017 | yes | 122 | 2,438,052 | 939,324 | 38.53 | 0 | local, UTC-4 | 100.00% of leaked rows |
| BCCC-cPacket-Cloud-DDoS-2024 | yes | 324 | 700,774 | 458,427 | 65.42 | 0 | local, UTC-5 | 100.00% of leaked rows |
| BCCC-DLLayer-IDS-2025 | no (layer-2 frame features) | 277 | not counted (pass 1 only) | - | none (no IAT columns; epoch scan: no timestamps) | n/a | n/a | n/a |

- Three NTLFlowLyzer-built datasets from three capture years (2017, 2018, 2023) show the same defect: IAT = absolute
  epoch whenever a direction has exactly one packet, with **0 rule violations** in all 51.3M rows checked.
- In every NTLFlowLyzer dataset the leaked value is the flow's true UTC start time (timestamp column + 4 h in July 2017,
  + 5 h in Feb 2018 and Dec 2023, consistent with a capture clock on Eastern time with daylight saving), and every leaked value falls on its file's
  documented capture day (2017 and 2023: 100.00%).
- 2017 uses an older 122-column NTLFlowLyzer layout (15 IAT columns: mean/std/max/min/total); 2018 and 2023 the full
  30-IAT layout (cPacket adds an `activity` column).
- No second timestamp path in any dataset: non-IAT values in the epoch range are genuine multi-GB payload totals or
  rates of ~0 s flows (2017, 2023) or rates/ratios/transaction IDs (2018, DLLayer), none near the flow start.
- BCCC-DLLayer-IDS-2025 is not NTLFlowLyzer output and carries no timestamps (pass 1 only).

Per-dataset details: `<dataset>/RESULTS.md`. 2018: `~/Desktop/ntl_census_step2/RESULTS.md`.

### What the leaked rows are (flow shapes)

Leaked rows classified by packet counts, flags and payload (`leak_shapes.py`, per dataset `LEAK_SHAPES.md`).

| dataset / group | leaked rows | fragments (lone ACK/RST/FIN, teardown) | connection attempts (SYN, SYN->RST) | with payload |
|---|---:|---:|---:|---:|
| 2017 attacks excl. Port_Scan, Botnet_ARES (12 classes) | 146,259 | 98.9% | 0.0% | 1.0% |
| 2017 Port_Scan + Botnet_ARES | 165,722 | 1.0% | 98.8% | 0.0% |
| 2017 Benign | 627,343 | 65.3% | 0.9% | 28.9% |
| cPacket attacks excl. BYPass-V1 (16 subtypes) | 21,565 | 49.0% | 50.3% | 0.4% |
| cPacket Attack-TCP-BYPass-V1 | 132,732 | 0.8% | 99.2% | 0.0% |
| cPacket Benign (all subtypes) | 288,597 | 32.7% | 66.5% | 0.3% |

- In 2017 the leaked attack rows of 12 of 14 classes are fragments split off real sessions (lone RSTs, ghost ACKs,
  teardown pairs) with no attack content; the attack sessions themselves are never leaked.
- In cPacket the leaked rows of 16 of 17 attack subtypes share one generic SYN/RST mix that does not follow the attack
  type and resembles benign traffic; they are distinguishable mainly by time.
- Exceptions where the leaked rows are the attack behaviour itself: 2017 Port_Scan and Botnet_ARES (SYN -> RST probes)
  and cPacket BYPass-V1 (lone SYNs).

### Is the leak exploitable? Timestamp-only baseline (Experiment 2) on all three datasets

**Claim: the timestamp alone identifies the attack rows that carry it** (not: the timestamp classifies all rows).
Single feature t = smallest leaked IAT value (0 if none). Random split = stratified 75/25 by class (random_state=0);
temporal = latest 25% by `timestamp` of each (file, class) (2018: the original pipeline's split, with class caps;
2017 / cPacket: same rule, no caps). Scored on **leaked test rows**. Attack classes = all non-Benign classes
(cPacket: the 17 `Attack / ...` subtypes; Suspicious is not counted as attack).

**Primary model, pre-specified:** DecisionTree(max_depth=20, min_samples_leaf=10, class_weight="balanced", random_state=0).
**Secondary model, added afterwards** (after the first 2017/cPacket results, not in the original spec): the same tree
without class weighting. Both are now run on all three datasets with the same feature and splits.
**Headline metric: mean attack-class recall** on leaked test rows.

#### random split, leaked test rows

| dataset | model | **mean attack-class recall** | attack classes with recall >= 0.90 | pooled attack-row recall | accuracy (majority guess) | macro-F1 |
|---|---|---:|---|---:|---|---:|
| CSE-CIC-IDS2018 | balanced tree (pre-specified) | **0.801** | 5 of 8 | 1.000 | 0.952 (0.526) | 0.546 |
| CSE-CIC-IDS2018 | unweighted tree (added afterwards) | **0.461** | 3 of 8 | 0.997 | 0.955 (0.526) | 0.504 |
| CIC-IDS-2017 | balanced tree (pre-specified) | **0.903** | 10 of 11 | 0.997 | 0.786 (0.668) | 0.319 |
| CIC-IDS-2017 | unweighted tree (added afterwards) | **0.223** | 2 of 11 | 0.939 | 0.969 (0.668) | 0.249 |
| cPacket (26 subtypes) | balanced tree (pre-specified) | **0.981** | 17 of 17 | 0.990 | 0.510 (0.534) | 0.412 |
| cPacket (26 subtypes) | unweighted tree (added afterwards) | **0.288** | 1 of 17 | 0.896 | 0.826 (0.534) | 0.239 |

#### temporal split, leaked test rows

| dataset | model | **mean attack-class recall** | attack classes with recall >= 0.90 | pooled attack-row recall | accuracy (majority guess) | macro-F1 |
|---|---|---:|---|---:|---|---:|
| CSE-CIC-IDS2018 | balanced tree (pre-specified) | **0.222** | 1 of 7 | 0.157 | 0.611 (0.548) | 0.190 |
| CSE-CIC-IDS2018 | unweighted tree (added afterwards) | **0.201** | 1 of 7 | 0.157 | 0.610 (0.548) | 0.159 |
| CIC-IDS-2017 | balanced tree (pre-specified) | **0.126** | 0 of 11 | 0.354 | 0.639 (0.673) | 0.246 |
| CIC-IDS-2017 | unweighted tree (added afterwards) | **0.066** | 0 of 11 | 0.350 | 0.788 (0.673) | 0.136 |
| cPacket (26 subtypes) | balanced tree (pre-specified) | **0.232** | 1 of 17 | 0.884 | 0.341 (0.538) | 0.156 |
| cPacket (26 subtypes) | unweighted tree (added afterwards) | **0.145** | 1 of 17 | 0.873 | 0.342 (0.538) | 0.077 |

Mean and the >= 0.90 count use attack classes with >= 10 leaked test rows; pooled recall uses all attack rows.
Balanced tree, classes below 0.90 and classes with < 10 leaked test rows:
- random CSE-CIC-IDS2018: below 0.90 Brute_Force_XSS 0.77 (n=22), DDoS_LOIC_HTTP 0.00 (n=50), SQL_Injection 0.64 (n=11); < 10 leaked rows: none
- random CIC-IDS-2017: below 0.90 DDoS_LOIT 0.00 (n=11); < 10 leaked rows: Heartbleed 1.00 (n=2), Web_SQL_Injection 1.00 (n=3)
- random cPacket (26 subtypes): below 0.90 ; < 10 leaked rows: none
- temporal CSE-CIC-IDS2018: below 0.90 Bot 0.01 (n=35830), Brute_Force_Web 0.03 (n=66), Brute_Force_XSS 0.07 (n=30), DDoS_HOIC 0.21 (n=97477), DoS_HULK 0.05 (n=2698), DoS_SlowHTTP 0.19 (n=26387); < 10 leaked rows: none
- temporal CIC-IDS-2017: below 0.90 Botnet_ARES 0.01 (n=1218), DDoS_LOIT 0.00 (n=42), DoS_GoldenEye 0.06 (n=289), DoS_Hulk 0.23 (n=32764), DoS_Slowhttptest 0.04 (n=555), DoS_Slowloris 0.10 (n=615), FTP-Patator 0.09 (n=1357), Port_Scan 0.49 (n=40175), SSH-Patator 0.06 (n=738), Web_Brute_Force 0.06 (n=344), Web_XSS 0.22 (n=172); < 10 leaked rows: Heartbleed 1.00 (n=1), Web_SQL_Injection 0.33 (n=3)
- temporal cPacket (26 subtypes): below 0.90 Attack / Attack-Killall-v2 0.00 (n=342), Attack / Attack-Killer-TCP 0.03 (n=373), Attack / Attack-TCP-Control 0.14 (n=341), Attack / Attack-TCP-Flag-ACK 0.18 (n=374), Attack / Attack-TCP-Flag-ACK-PSH 0.70 (n=406), Attack / Attack-TCP-Flag-MIX 0.00 (n=321), Attack / Attack-TCP-Flag-OSYN 0.15 (n=163), Attack / Attack-TCP-Flag-OSYNP 0.02 (n=196), Attack / Attack-TCP-Flag-RST-ACK 0.05 (n=60), Attack / Attack-TCP-Flag-SYN 0.09 (n=498), Attack / Attack-TCP-Flag-SYN-ACK 0.77 (n=494), Attack / Attack-TCP-Flag-SYN-TFO 0.05 (n=184), Attack / Attack-TCP-Flag-SYN-TIME 0.45 (n=183), Attack / Attack-TCP-IGMP 0.11 (n=421), Attack / Attack-TCP-SYN 0.10 (n=388), Attack / Attack-TCP-Valid-SYN 0.12 (n=378); < 10 leaked rows: none

- **Random split, pre-specified tree:** mean attack-class recall **0.80 (2018), 0.90 (2017), 0.98 (cPacket)**; pooled
  attack-row recall 1.000 / 0.997 / 0.990; 5 of 8, 10 of 11 and 17 of 17 attack classes reach recall >= 0.90. The 2018
  mean is pulled down by DDoS_LOIC_HTTP (0.00, 50 rows), SQL_Injection (0.64, 11) and Brute_Force_XSS (0.77, 22);
  2017's by DDoS_LOIT (0.00, 11 rows).
- **Not "classifies all rows":** balanced weighting pulls benign rows from the same hours into the attack classes, so
  small attack classes have low precision and overall accuracy can be modest. In cPacket the balanced tree's accuracy
  on leaked rows (0.510) is slightly *below* majority guessing (0.534) although attack recall is 0.93-1.00.
- **Unweighted tree (added afterwards):** higher accuracy (0.955 / 0.969 / 0.826) but it sends small attack classes to
  the majority class (mean attack-class recall 0.46 / 0.22 / 0.29). It is a secondary check; the claim rests on the
  pre-specified model.
- **Temporal split:** much weaker everywhere (mean attack-class recall 0.22 / 0.13 / 0.23). Test flows come after the
  training flows of the same capture session, so time thresholds learned on training times do not reach them; the
  high pooled value in cPacket (0.884) comes from one long single-session attack (BYPass-V1).

Files: 2018 `~/Desktop/ntl_exp23/results/exp2/` (unweighted: `*_tree_unweighted.json`, script `exp2_unweighted.py`);
2017 / cPacket `<dataset>/exp2_<label|activity>/`, script `exp2_multi.py`; table `exp2_consistent_table.txt`.

---

## 10. Novelty check (partial, 2026-10-02)

**GitHub, `ahlashkari/NTLFlowLyzer`:** all 32 issues and PRs (#1-#35) and their comments were read via the public API.
- **The ghost-flow bug is already known.** Issue **#29** (opened 2025-04-07, still open) reports that the final ACK of
  the four-way close is split into a new flow. The maintainer confirmed it ("the flow is being closed immediately after
  seeing the second FIN... This ACK is currently being treated as the beginning of a new flow") and promised a fix,
  which has not landed: Step 1 reproduces it at the current commit `d99cd53`. The paper should cite #29, not claim
  this bug as new.
- **The IAT timestamp leak has not been reported.** No issue, PR or comment mentions absolute timestamps in IAT
  features, single-packet directions or `calculate_IAT`. (Keyword hits on "iat" were substrings such as "appreciate".)
  `features/utils.py` has a single commit in its history ("Update the naming.").
- PR #31 ("Fix idle time statistics calculation", 2026-03-30) touched only idle-time statistics and was closed without
  merging. Unrelated.

**Literature (two quick web searches only):** no publication found that reports the IAT timestamp leak in NTLFlowLyzer
or the BCCC datasets. Both tool papers ([Computers & Security 148, 2024](https://www.sciencedirect.com/science/article/abs/pii/S0167404824004656);
[J. Netw. Syst. Manage., 2025](https://link.springer.com/article/10.1007/s10922-025-09917-0)) and the
[BCCC dataset pages](https://www.yorku.ca/research/bccc/tag/large-scale-intrusion-detection-dataset-bccc-cse-cic-ids2018/)
present NTLFlowLyzer as the tool that resolves feature anomalies of earlier extractors. **Still to do:** a systematic
pass over papers citing those two articles and over papers using the BCCC datasets (Google Scholar "cited by",
Kaggle notebooks), and a check of the forks' commit messages.

---

## 11. Replication on BCCC-CIC-IDS-2017: single-seed 2 × 2 retrain

All 18 CSVs, 2,438,052 rows, **114 features**: every numeric column except `flow_id`, `src_ip`, `src_port`, `dst_ip`, `dst_port`, `timestamp`, `protocol` (text) and `label`; inf/NaN -> 0, float32 (full list: `BCCC-CIC-IDS-2017/exp3/cache/meta.json`). No class capping (memory estimate: 1.1 GB full matrix, 0.83 GB training subset). Splits = the Experiment 2 splits for 2017 (`exp2_label/splits.npz`): random = stratified 75/25, random_state=0; temporal = latest 25% by `timestamp` per (file, class). Variants: leaky; fixA (every IAT cell > 1e9 set to 0 in train and test); fixB (fixA + rows with `packets_count == 1` dropped from train and test). Model: RandomForestClassifier(n_estimators=200, max_depth=30, min_samples_leaf=10, class_weight='balanced', n_jobs=2, random_state=0), one process per run under `systemd-run --scope -p MemoryMax=6.5G -p MemorySwapMax=0`. Seed 0 only.

### 11.1 Overall

| split | variant | n train | n test | acc (all) | macro-F1 (all) | acc (leaked rows) | macro-F1 (leaked) | split thresholds > 1e9 (on IAT) | fit s | peak RSS GB |
|---|---|---:|---:|---:|---:|---:|---:|---|---:|---:|
| random | leaky | 1,828,539 | 609,513 | 0.9915 | 0.7400 | 0.9850 | 0.6540 | 41107 (41107) | 245 | 2.44 |
| random | fixA | 1,828,539 | 609,513 | 0.8753 | 0.5343 | 0.6844 | 0.2313 | 0 (0) | 235 | 2.42 |
| random | fixB | 1,421,552 | 473,541 | 0.9939 | 0.7485 | 0.9940 | 0.4073 | 0 (0) | 204 | 2.28 |
| temporal | leaky | 1,828,539 | 609,513 | 0.9397 | 0.6327 | 0.8590 | 0.3882 | 33854 (33854) | 260 | 2.32 |
| temporal | fixA | 1,828,539 | 609,513 | 0.8326 | 0.4763 | 0.5870 | 0.1894 | 0 (0) | 236 | 2.32 |
| temporal | fixB | 1,419,623 | 475,470 | 0.9923 | 0.7422 | 0.9962 | 0.4155 | 0 (0) | 222 | 2.06 |

Leak check: 0 split thresholds > 1e9 on IAT features in every fixA/fixB forest.

### 11.2 Per-class recall / precision, all test rows

| class | n test | random leaky R / P | random fixA R / P | random fixB R / P | temporal leaky R / P | temporal fixA R / P | temporal fixB R / P |
|---|---:|---|---|---|---|---|---|
| Benign | 446,560 | 0.989 / 1.000 | 0.846 / 0.999 | 0.993 / 1.000 | 0.985 / 0.940 | 0.851 / 0.998 | 0.994 / 0.999 |
| Botnet_ARES | 1,377 | 1.000 / 0.635 | 1.000 / 0.072 | 1.000 / 0.773 | 0.105 / 1.000 | 0.877 / 0.069 | 0.876 / 1.000 |
| DDoS_LOIT | 23,933 | 1.000 / 0.999 | 1.000 / 1.000 | 1.000 / 1.000 | 0.999 / 0.924 | 0.997 / 1.000 | 0.999 / 1.000 |
| DoS_GoldenEye | 2,091 | 0.982 / 0.897 | 0.921 / 0.960 | 0.978 / 0.969 | 0.824 / 0.887 | 0.813 / 0.885 | 0.938 / 0.893 |
| DoS_Hulk | 87,310 | 0.999 / 0.993 | 0.940 / 0.832 | 0.999 / 0.990 | 0.717 / 0.993 | 0.632 / 0.994 | 0.989 / 0.993 |
| DoS_Slowhttptest | 1,715 | 0.967 / 0.784 | 0.699 / 0.855 | 0.975 / 0.854 | 0.758 / 0.593 | 0.725 / 0.564 | 0.987 / 0.573 |
| DoS_Slowloris | 1,294 | 0.971 / 0.808 | 0.804 / 0.876 | 0.966 / 0.926 | 0.783 / 0.935 | 0.339 / 0.814 | 0.601 / 0.872 |
| FTP-Patator | 2,383 | 0.997 / 0.788 | 0.832 / 0.147 | 0.998 / 0.808 | 0.520 / 0.986 | 0.861 / 0.145 | 0.998 / 0.853 |
| Heartbleed | 3 | 0.667 / 0.026 | 0.000 / 0.000 | 0.000 / 0.000 | 0.667 / 0.001 | 0.667 / 0.000 | 0.000 / 0.000 |
| Port_Scan | 40,331 | 1.000 / 0.997 | 0.993 / 1.000 | 1.000 / 1.000 | 0.987 / 0.974 | 0.990 / 1.000 | 0.998 / 1.000 |
| SSH-Patator | 1,487 | 0.995 / 0.800 | 0.989 / 0.295 | 0.989 / 0.875 | 0.508 / 0.995 | 0.949 / 0.261 | 0.936 / 0.931 |
| Web_Brute_Force | 683 | 0.777 / 0.367 | 0.262 / 0.275 | 0.533 / 0.271 | 0.270 / 0.279 | 0.237 / 0.186 | 0.474 / 0.239 |
| Web_SQL_Injection | 6 | 0.667 / 0.049 | 0.500 / 0.000 | 0.333 / 0.333 | 0.667 / 0.667 | 0.833 / 0.001 | 1.000 / 0.600 |
| Web_XSS | 340 | 0.859 / 0.356 | 0.835 / 0.015 | 0.735 / 0.168 | 0.412 / 0.194 | 0.779 / 0.014 | 0.607 / 0.119 |

### 11.3 Per-class recall, leaked test rows (leaked in the unmodified data)

| class | random leaky (n) | random fixA (n) | random fixB (n) | temporal leaky (n) | temporal fixA (n) | temporal fixB (n) |
|---|---|---|---|---|---|---|
| Benign | 0.978 (156,946) | 0.572 (156,946) | 0.990 (56,650) | 0.968 (161,365) | 0.598 (161,365) | 0.995 (62,937) |
| Botnet_ARES | 1.000 (1,154) | 1.000 (1,154) | 1.000 (952) | 0.119 (1,218) | 0.991 (1,218) | 0.990 (1,218) |
| DDoS_LOIT | 0.818 (11) | 0.000 (11) | 0.000 (1) | 0.976 (42) | 0.000 (42) | 0.000 (1) |
| DoS_GoldenEye | 1.000 (129) | 0.000 (129) | - | 0.062 (289) | 0.000 (289) | - |
| DoS_Hulk | 1.000 (32,978) | 0.844 (32,978) | 0.995 (1,014) | 0.265 (32,764) | 0.036 (32,764) | 0.967 (1,227) |
| DoS_Slowhttptest | 0.968 (527) | 0.097 (527) | 1.000 (51) | 0.283 (555) | 0.180 (555) | 1.000 (100) |
| DoS_Slowloris | 0.996 (225) | 0.022 (225) | - | 0.945 (615) | 0.005 (615) | 0.000 (1) |
| FTP-Patator | 0.998 (1,375) | 0.711 (1,375) | 1.000 (585) | 0.158 (1,357) | 0.757 (1,357) | 1.000 (699) |
| Heartbleed | 1.000 (2) | 0.000 (2) | - | 1.000 (1) | 1.000 (1) | - |
| Port_Scan | 1.000 (40,275) | 0.993 (40,275) | 1.000 (39,681) | 0.989 (40,175) | 0.992 (40,175) | 1.000 (39,401) |
| SSH-Patator | 1.000 (769) | 0.986 (769) | 0.333 (3) | 0.062 (738) | 0.951 (738) | 0.091 (11) |
| Web_Brute_Force | 1.000 (345) | 0.000 (345) | - | 0.061 (344) | 0.000 (344) | - |
| Web_SQL_Injection | 1.000 (3) | 0.667 (3) | - | 0.333 (3) | 0.667 (3) | - |
| Web_XSS | 1.000 (170) | 0.965 (170) | - | 0.221 (172) | 0.953 (172) | - |

### 11.4 Exact counts for classes with < 100 test rows (correct / support, all test rows)

| class | random leaky | random fixA | random fixB | temporal leaky | temporal fixA | temporal fixB |
|---|---|---|---|---|---|---|
| Heartbleed | 2/3 | 0/3 | 0/1 | 2/3 | 2/3 | 0/2 |
| Web_SQL_Injection | 4/6 | 3/6 | 1/3 | 4/6 | 5/6 | 3/3 |

### 11.5 Same rows: multi-packet test rows (packets_count != 1)

| split | variant | rows | acc | macro-F1 |
|---|---|---:|---:|---:|
| random | leaky | 473,541 | 0.9964 | 0.7716 |
| random | fixA | 473,541 | 0.9948 | 0.7599 |
| random | fixB | 473,541 | 0.9939 | 0.7485 |
| temporal | leaky | 475,470 | 0.9902 | 0.7368 |
| temporal | fixA | 475,470 | 0.9928 | 0.8030 |
| temporal | fixB | 475,470 | 0.9923 | 0.7422 |

(fixB's test set *is* the multi-packet rows, so its row equals its all-rows result.)

### 11.6 Differences, leaky − fixA

| split | Δ acc (all) | Δ macro-F1 | Δ acc (leaked rows) | Δ acc (multi-packet rows) | Δ recall per class (|Δ| ≥ 0.01) |
|---|---:|---:|---:|---:|---|
| random | +0.1162 | +0.2057 | +0.3006 | +0.0016 | Benign +0.143, DoS_GoldenEye +0.061, DoS_Hulk +0.059, DoS_Slowhttptest +0.268, DoS_Slowloris +0.168, FTP-Patator +0.165, Heartbleed +0.667, Web_Brute_Force +0.515, Web_SQL_Injection +0.167, Web_XSS +0.024 |
| temporal | +0.1070 | +0.1564 | +0.2720 | -0.0026 | Benign +0.134, Botnet_ARES -0.771, DoS_GoldenEye +0.010, DoS_Hulk +0.086, DoS_Slowhttptest +0.033, DoS_Slowloris +0.444, FTP-Patator -0.341, SSH-Patator -0.440, Web_Brute_Force +0.034, Web_SQL_Injection -0.167, Web_XSS -0.368 |

### 11.7 Comparison with 2018 (§6): does the random split inflate and the temporal split hurt again?

| | 2018 (4 seeds) | 2017 (seed 0) | replicated? |
|---|---|---|---|
| Random split, leaky − fixA accuracy | +0.044 | **+0.116** | **yes, larger** |
| Temporal split, leaky − fixA accuracy | −0.073 | **+0.107** | **no, sign reversed overall** |
| Multi-packet rows, leaky vs fixA | equal (≤ 0.001 apart) | equal (≤ 0.003 apart) | **yes** |
| Leak removed + 1-packet rows dropped (fixB) | ~0.999 / 1.000 | 0.992 / 0.994 | yes |
| Thresholds > 1e9 in leaky / fixed forests | 17.7-22.7k / 0 on IAT | 33.9-41.1k / 0 | yes |

- **Random split: the leak inflates results again, more than in 2018** (+11.6 points accuracy, +0.21 macro-F1; +30.1 points on
  leaked rows). The fixed model loses mainly where leaked rows are fragments without attack content: Web_Brute_Force
  recall 0.78 -> 0.26, Slowhttptest 0.97 -> 0.70, FTP-Patator 1.00 -> 0.83, Slowloris 0.97 -> 0.80, and Benign
  0.99 -> 0.85 (its leaked fragments get confused with attack fragments of the same shape). Port_Scan and DDoS_LOIT
  stay at ~1.00 either way.
- **Temporal split: the 2018 mechanism appears per class, but the overall sign reverses.** As in 2018, the leaky model
  mislearns capture windows for several attack classes: on leaked test rows, Botnet_ARES recall 0.99 (fixA) vs 0.12
  (leaky), SSH-Patator 0.95 vs 0.06, Web_XSS 0.95 vs 0.22, FTP-Patator 0.76 vs 0.16. But Benign (73% of the test set)
  goes the other way: without the timestamp, benign fragment rows (lone RSTs / ACKs, recall 0.60 on leaked benign rows)
  are pulled into the small attack classes, whose fixA precision collapses (ARES 0.07, FTP 0.15, SSH 0.26, XSS 0.01).
  With the timestamp, benign fragments are separated by time of day (benign recall 0.985). Net: +10.7 points for
  the leaky model. A likely reason this differs from 2018: in 2017 the 1-packet fragments of benign and attack traffic
  share shapes and are only separable by time, and class_weight="balanced" favours assigning them to the small
  attack classes; in 2018 the fixed model assigned such rows to Benign (Bot recall ~0.50). This is an interpretation,
  not tested.
- **Robust across both datasets:** on multi-packet flows the leak makes no difference (2017: 0.9964 vs 0.9948 random,
  0.9902 vs 0.9928 temporal), and dropping 1-packet flows brings both splits to ~0.99. The leak's whole effect, in
  either direction, sits in the 1-packet rows.
- Caveats: single seed (2018's seed-to-seed std was <= 0.002 in accuracy, so the ~11-point effects are far outside
  seed noise, but per-class values for small classes are not); Heartbleed has 3 test rows and Web_SQL_Injection 6
  (exact counts in 11.4).
