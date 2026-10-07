# Timestamp leakage in NTLFlowLyzer-built intrusion detection datasets

Draft, 2026-10-03 (revised after review). Local copy of the shared doc (https://claude.ai/code/artifact/82dd330c-302a-4860-b4a1-449f60190331); Figure 1 is a live chart there and a data table here.

## Abstract

NTLFlowLyzer, the flow-feature extractor behind the BCCC family of intrusion detection datasets, writes each flow's absolute start time (a Unix timestamp) into its inter-arrival-time (IAT) features whenever a flow direction contains exactly one packet. We reproduce the defect on the current upstream code with a 21-packet synthetic capture and trace it to a single function. A census of three published datasets finds it in 35.5% of BCCC-CSE-CIC-IDS2018 rows, 38.5% of BCCC-CIC-IDS-2017 rows and 65.4% of BCCC-cPacket-Cloud-DDoS-2024 rows, with no exception to the one-packet rule in 51.3 million rows. The leak is exploitable: under a random train/test split, the timestamp alone recovers 80-98% of the leaked attack rows. Across seven model families retrained with and without the leak, it shifts accuracy by up to 18 points. It inflates results under random splits and makes them split-dependent; distance-based KNN is inflated on every dataset and split. Setting the leaked cells to zero, or dropping the IAT features, removes the leak; both give the same results within 0.02 accuracy for six of seven model families. At least 20 studies from 2024-2026 report experiments on these datasets, several with accuracy or F1 at or above 99%. Those that kept the IAT features, particularly under random splits, may report inflated or split-dependent results and warrant re-examination.

## 1 Introduction and research argument

We claim that a defect in NTLFlowLyzer leaks capture time into three public intrusion detection datasets, that the leak changes model results, and that published work on these datasets may therefore warrant re-examination. The argument has five steps, each backed by its own evidence.

| Step | Claim | Evidence | Section |
|---|---|---|---|
| 1 | The tool writes absolute timestamps into IAT features | Minimal 21-packet pcap on upstream commit d99cd53; root cause in `calculate_IAT`; our own fork (two commits changing only continuous-batch polling) gives byte-identical output | 3 |
| 2 | The published datasets were built with this behaviour | 35-65% of rows leaked; 0 violations of the one-packet rule in 51.3M rows; every leaked value is the flow's true UTC start time on its documented capture day | 3 |
| 3 | The leak is exploitable | A decision tree on the timestamp alone recovers 80-98% of leaked attack rows under a random split | 5.1 |
| 4 | The leak changes results | Across seven model families (GaussianNB excluded from interpretation), accuracy shifts by up to 18 points between leaky and fixed data; our own KNN's 0.993 accuracy falls to 0.871 when only timestamps change | 5.2-5.4 |
| 5 | The fixed baseline is clean | Zeroing leaked cells (fixA) matches dropping all IAT columns (dropIAT) within 0.02 accuracy, except RF on 2018 (5.5); units check confirms the 1e9 threshold | 5.5 |

The claim about other research is deliberately limited. We show that the conditions for an inflated result exist in these datasets and are met by common practice (random splits, all features kept). We do not reproduce or assess individual published studies; section 6 counts how many studies use these datasets and states which setups are exposed.

## 2 Background

NTLFlowLyzer is presented by its authors as a flow-feature extractor that resolves the anomalies of earlier tools such as CICFlowMeter. The BCCC group re-extracted several benchmark captures with it and published them as BCCC-CSE-CIC-IDS2018, BCCC-CIC-IDS-2017 and BCCC-cPacket-Cloud-DDoS-2024. The original CICFlowMeter versions of CIC-IDS2017 and CSE-CIC-IDS2018 are a different release and are not examined here.

- **IAT features.** Each flow carries up to 30 inter-arrival-time statistics (mean, std, max, min, total, median, mode and others) per direction and combined. Legitimate values are seconds between packets: in these datasets the largest is about 3.2e4 s.
- **Why capture time leaks labels.** Each attack in these captures ran in its own time window. A model that sees the flow's start time can map time windows to classes without learning anything about the traffic.
- **Why the split matters.** A random split puts training and test flows from the same windows side by side, so time identifies the class. A temporal split puts test flows after the training windows, where learned time thresholds may not reach.
- **Why the model matters.** Trees can split on exact time ranges. After standard scaling, a ~1.5e9 value dominates Euclidean distance, so KNN's nearest neighbours become the flows nearest in time.

## 3 The defect

When a direction holds exactly one packet, `calculate_IAT` (`NTLFlowLyzer/features/utils.py`, lines 20-27) returns the raw timestamp list instead of the differences between timestamps. Every IAT statistic of that direction then equals the packet's epoch time.

- **Reproducer.** A 21-packet synthetic pcap (T0 = 2018-02-22 14:00:00 UTC) on upstream commit `d99cd53` yields epoch values exactly where a direction has one packet: lone SYNs, a SYN/SYN-ACK/RST probe and a trailing-ACK ghost flow. A direction with zero packets gets 0, not a timestamp.
- **Second, known bug.** A flow closes as soon as both sides send FIN, so the final ACK opens a new one-packet "ghost" flow, which then leaks. This is upstream issue #29 (open since 2025-04-07); we found no report of the IAT leak in the issue tracker or in the literature we searched (section 6).

**Table 1. Leak census of the published datasets** (leak = IAT value > 1e9)

| Dataset | Rows | Leaked rows | % leaked | Rule violations | Leaked values on capture day | IAT columns |
|---|---:|---:|---:|---:|---|---:|
| BCCC-CSE-CIC-IDS2018 | 48,182,782 | 17,108,403 | 35.5 | 0 | yes, each attack in its own window | 30 |
| BCCC-CIC-IDS-2017 | 2,438,052 | 939,324 | 38.5 | 0 | 100.00% | 15 |
| BCCC-cPacket-Cloud-DDoS-2024 | 700,774 | 458,427 | 65.4 | 0 | 100.00% | 30 |
| BCCC-DLLayer-IDS-2025 | not NTLFlowLyzer output | - | - | - | no timestamps | 0 |

The leak rate depends strongly on class, from 0.05% (2017 DDoS_LOIT) and 0.07% (2018 DDoS_LOIC_HTTP) to 100% (2018 DoS_SlowHTTP and Brute_Force_FTP) and 99.9% (2017 Port_Scan). Most leaked attack rows are fragments split off real sessions (lone RST or ACK packets, ghost ACKs) with no attack content. The exceptions, where the leaked rows are the attack itself, are 2017 Port_Scan and Botnet_ARES (SYN-RST probes) and cPacket BYPass-V1 (lone SYNs).

Every leaked value is the flow's true UTC start time: it equals the dataset's local `timestamp` column plus 4 h (July 2017) or 5 h (Feb 2018, Dec 2023).

## 4 Data and methods

All experiments use the published CSVs of the three NTLFlowLyzer datasets, with identity columns and the `timestamp` column removed (313 features for 2018 and cPacket, 114 for 2017).

- **Splits.** Random: stratified 75/25 by class, seed 0. Temporal: the latest 25% of each (file, class) by flow time (for 2018, the original pipeline's split).
- **Leaked cell.** Any IAT value > 1e9, judged on the unmodified data.
- **Conditions.**
    - *leaky*: train and test as published.
    - *+8y*: the leaky model, with leaked test cells shifted by 252,460,800 s (8 years); no retraining.
    - *zero*: the leaky model, with leaked test cells set to 0; no retraining.
    - *fixA*: retrained and tested with every leaked cell set to 0 (equivalent to the code fix, given 0 rule violations).
    - *dropIAT*: retrained and tested with every IAT column removed; a leak-free reference for fixA.
- **Models.** Our own 2018 models from a separate IDS study (ONNX RF, KNN, soft-voting ensemble, trained on the published BCCC-CSE-CIC-IDS2018 CSVs) for the timestamp-change test. For the comparison: GaussianNB, DecisionTree, LogisticRegression, XGBoost, RandomForest, MLP and KNN (k = 5, distance-weighted, as shipped), fixed configurations, seed 0, trained on a 600k-row stratified subsample and scored on the full test split. Trees, LogReg and XGBoost use balanced class weights; GaussianNB, MLP and KNN do not.
- **Uncertainty.** Paired bootstrap over test rows (B = 1,000), all conditions of a model scored on the same resample. The 2018 RF retrain also used 4 seeds (seed-to-seed accuracy std <= 0.002).
- **Scale.** 120 model runs in the comparison, plus 24 RF retrains (2018), 6 (2017) and the timestamp-only baselines.

## 5 Results

The leak is exploitable, it changes the results of every leak-sensitive model, and the fixed baseline is clean.

### 5.1 The timestamp alone identifies leaked attack rows

**Table 2. Timestamp-only decision tree** (pre-specified: depth 20, balanced weights), scored on leaked test rows

| Dataset | Mean attack-class recall, random | Pooled attack-row recall, random | Mean attack-class recall, temporal |
|---|---:|---:|---:|
| BCCC-CSE-CIC-IDS2018 | 0.80 | 1.000 | 0.22 |
| BCCC-CIC-IDS-2017 | 0.90 | 0.997 | 0.13 |
| BCCC-cPacket-Cloud-DDoS-2024 | 0.98 | 0.990 | 0.23 |

Under a random split one feature, the timestamp, recovers almost every leaked attack row. Under a temporal split it mostly fails, because test flows fall after the learned time windows.

### 5.2 Our 2018 models from a separate IDS study depend on the timestamp

**Table 3. Accuracy when only the leaked timestamps change** (original temporal test split; KNN and ensemble on a 20,001-row stratified sample, population-weighted)

| Condition | RF | KNN | Ensemble |
|---|---:|---:|---:|
| As published | 0.893 | 0.993 | 0.993 |
| +8 years | 0.875 | 0.871 | 0.871 |
| +1 day | 0.838 | 0.904 | 0.904 |
| Leaked cells = 0 | 0.875 | 0.871 | 0.871 |

The KNN and ensemble owe their whole advantage over the RF to the leak. The RF loses 20,381 correct attack detections that depended only on the timestamp.

### 5.3 Retraining with and without the leak (RandomForest)

**Table 4. RF accuracy, all test rows** (2018: mean of 4 seeds; 2017: seed 0)

| Dataset, split | Leaky | Fixed (fixA) | Leaky - fixA |
|---|---:|---:|---:|
| 2018 random | 0.998 | 0.953 | +0.044 |
| 2018 temporal | 0.892 | 0.965 | -0.073 |
| 2017 random | 0.992 | 0.875 | +0.116 |
| 2017 temporal | 0.940 | 0.833 | +0.107 |

On multi-packet flows all variants score 0.99-1.00 on both datasets: the whole effect, in either direction, sits in the one-packet rows.

### 5.4 Seven model families

**Figure 1. The leak inflates trees and KNN on random splits, and KNN on every split.** Accuracy, leaky minus fixed (fixA), all test rows (120 runs, seed 0, full test sets; 95% bootstrap CIs at most +/-0.003). GaussianNB omitted as a near-chance baseline; LogReg and MLP are under-trained and not interpreted.

| Model | 2018 random | 2018 temporal | 2017 random | 2017 temporal | cPacket random | cPacket temporal |
|---|---:|---:|---:|---:|---:|---:|
| KNN | +0.116 | +0.090 | +0.100 | +0.056 | +0.183 | +0.011 |
| RandomForest | +0.165 | +0.023 | +0.098 | +0.093 | +0.144 | -0.016 |
| XGBoost | +0.048 | +0.048 | +0.063 | +0.091 | +0.083 | +0.018 |
| DecisionTree | +0.045 | -0.028 | +0.061 | +0.043 | +0.090 | -0.057 |
| LogReg* | +0.115 | +0.002 | +0.003 | +0.004 | +0.000 | +0.001 |
| MLP* | +0.000 | +0.000 | +0.000 | +0.000 | +0.003 | +0.006 |

Every random-split dot of the tree models and KNN sits right of zero (+0.045 to +0.183). On temporal splits the trees go both ways, while KNN stays inflated (+0.011 to +0.090), because "nearest in time" still reaches test flows just after the training window. Moving leaked timestamps 8 years without retraining costs the trees up to 0.44 accuracy on cPacket, so they rely on exact capture times.

### 5.5 The fixed baseline does not leak

Zeroing leaked cells could itself act as a leak flag, since leaking is class-dependent. Two checks rule this out.

**Table 5. Fixed-baseline checks**

| Check | 2018 | 2017 | cPacket |
|---|---|---|---|
| Leaked values (epoch band) | 1.519-1.520e9 (Feb 2018) | 1.499e9 (Jul 2017) | 1.703e9 (Dec 2023) |
| Largest legitimate IAT (s) | 3.2e4 | 2.9e4 | 2.9e4 |
| Legitimate cells in (1e6, 1e9] | 0 | 0 | 0 |
| Zero-mask-only tree, macro F1: legitimate zeros vs fixA zeros | 0.333 vs 0.334 | 0.117 vs 0.129 | 0.108 vs 0.112 |

Retraining with every IAT column removed (dropIAT) matches fixA within 0.02 accuracy and +/-0.01 mean attack recall for DecisionTree, XGBoost, MLP and GaussianNB, and within 0.001 accuracy for KNN, on every dataset and split. The one exception, RF on 2018 (+0.047 random, -0.033 temporal), flips sign between splits; it traces to how that RF assigns one-packet rows that are identical across HOIC, Bot and Benign once the timestamp is gone.

## 6 Potential impact on published research

At least 20 works from 2024-2026 report experiments on a BCCC NTLFlowLyzer dataset in their abstracts, and several report accuracy or F1 at or above 99%. We did not reproduce any of them, so we make no claim about any single result.

- **Search.** OpenAlex full-text search for the exact dataset names (BCCC-cPacket-Cloud-DDoS-2024, BCCC-CIC-IDS2017, BCCC-CIC-IDS-2017, BCCC-CSE-CIC-IDS2018) on 2026-10-03 returned 47 works. Removing the three source papers and duplicate versions leaves about 40 distinct works that name a dataset.
- **Counting rule.** A work counts only if its abstract states experiments on a BCCC dataset. Abstracts were read through OpenAlex with automated screening and a manual spot-check; one candidate was dropped because its abstract names no BCCC dataset, and one non-ML study was excluded.
- **Citations (upper bound).** The cPacket dataset paper has 48 citing works and the 2025 NTLFlowLyzer paper 12 in Semantic Scholar.

**Table 6. Works whose abstracts report experiments on a BCCC dataset** (abstract figures as stated; task and split differ across works)

| Work | Year | Dataset | Abstract-reported result |
|---|---|---|---|
| [LLM-Based Cyberattack Detection Using Network Flow Statistics](https://doi.org/10.3390/app15126529) | 2025 | BCCC-CIC-IDS-2017 | all metrics > 99.90% |
| [Z-Shield: hybrid browser-based IDS](https://doi.org/10.51584/ijrias.2026.11070014) | 2026 | BCCC-CSE-CIC-IDS2018 | 99.13% accuracy, 99.58% F1 |
| [Two-stage hybrid IDS, hierarchical attack mapping, pruned CNN-GRU](https://doi.org/10.48084/etasr.16210) | 2026 | BCCC-cPacket-Cloud-DDoS-2024 | up to 99.99% accuracy |
| [DDoS detection optimized by Bayesian and PSO techniques](https://doi.org/10.59796/jcst.v16n3.2026.204) | 2026 | BCCC-cPacket-Cloud-DDoS-2024 | 99.29% accuracy, 98.91% F1 |
| [SCDF-CNN-BiGRU multi-dataset hierarchical IDS](https://doi.org/10.31026/j.eng.2026.09.12) | 2026 | BCCC-cPacket-Cloud-DDoS-2024 | up to 0.999 accuracy |
| [PU learning for cloud DDoS detection](https://doi.org/10.48550/arxiv.2410.18380) | 2024 | BCCC-cPacket-Cloud-DDoS-2024 | F1 > 98% (XGBoost, RF) |
| [AutoML random forests for cloud DDoS](https://doi.org/10.14445/23488549/ijece-v13i4p124) | 2026 | BCCC-cPacket-Cloud-DDoS-2024 | ~98% accuracy |
| [Hybrid CNN-RNN with multi-head attention](https://doi.org/10.3390/app152111567) | 2025 | BCCC-cPacket-Cloud-DDoS-2024 | 97.78% accuracy |
| [Parallel CNN-BiLSTM with Nelder-Mead calibration](https://doi.org/10.51483/ijaiml.6.10s.2026.1874-1896) | 2026 | BCCC-cPacket-Cloud-DDoS-2024 | 95-97% accuracy (k-fold) |
| [Real-time network health monitoring, OpenStack](https://doi.org/10.1109/iconecct67014.2025.11470261) | 2025 | BCCC-cPacket-Cloud-DDoS-2024 | 94.84% accuracy |
| [Optimized RF pipeline, multi-class cloud DDoS](https://doi.org/10.1109/ickecs70176.2026.11527811) | 2026 | BCCC-cPacket-Cloud-DDoS-2024 | 94.52% accuracy |
| [Contrastive AI and LLMs against DDoS](https://doi.org/10.5281/zenodo.21387306) | 2026 | BCCC-cPacket-Cloud-DDoS-2024 | 93.5% F1 |
| [Feature-selected ML/DL for cloud DDoS](https://doi.org/10.32628/ijsrst26131163) | 2026 | BCCC-cPacket-Cloud-DDoS-2024 | 87.4% accuracy (stratified split) |
| [Optimising DDoS attack detection over cloud](https://doi.org/10.1109/icass69550.2026.11547587) | 2026 | BCCC-cPacket-Cloud-DDoS-2024 | not stated as accuracy |
| [Two-stage FWSC feature selection](https://doi.org/10.62527/joiv.10.3.5572) | 2026 | BCCC-cPacket-Cloud-DDoS-2024 | not stated |
| [Adaptive ML pipelines for cloud DDoS](https://doi.org/10.36227/techrxiv.175037203.37181551/v1) | 2025 | BCCC-cPacket-Cloud-DDoS-2024 | not stated |
| [Comparative study: CIC-IDS-2017 vs BCCC-CIC-IDS-2017](https://doi.org/10.1109/ids69480.2026.00027) | 2026 | BCCC-CIC-IDS-2017 | not stated |
| [ARTEMIS: zero-query evasion of NIDS](https://doi.org/10.1109/icnp65844.2025.11192405) | 2025 | BCCC-CIC-IDS2017 / 2018 | not stated |
| [Evaluating DL and traditional ML for NIDS (thesis)](https://doi.org/10.14457/tu.the.2025.519) | 2026 | BCCC-CIC-IDS-2017 | not stated |
| Automatic cyberattack management system (dissertation) | 2026 | BCCC-CIC-IDS-2017 | 99.90% |

**Which setups are exposed.** A study is exposed when it keeps the IAT features, uses a random or stratified split or k-fold cross-validation, and uses a model that can exploit extreme values (trees, boosting, KNN, unclipped neural inputs). Studies that drop IAT features, clip or log-transform them, or split by time or capture day are much less exposed. The abstracts above rarely state these details, so exposure cannot be judged from them; that is the re-examination this report recommends.

Sources: [OpenAlex works API](https://api.openalex.org/works?search=%22BCCC-cPacket-Cloud-DDoS-2024%22), searched 2026-10-03; [Semantic Scholar citations of the cPacket paper](https://api.semanticscholar.org/graph/v1/paper/DOI:10.3390/info15040195/citations) and [of the NTLFlowLyzer paper](https://api.semanticscholar.org/graph/v1/paper/DOI:10.1007/s10922-025-09917-0/citations).

## 7 Limitations

The defect and its prevalence are established without qualification; the size of its effect on results depends on setup, and its effect on published work is not measured.

- **Published work.** We count studies; we do not reproduce them. The literature screen read abstracts only, partly by automated classification, so the count of 20 is a floor, not a census.
- **Direction of the effect.** The leak inflates results under random splits but can lower them under temporal splits (2018 RF: -7.3 points). The safe claim is "unreliable and split-dependent", not "always inflated".
- **Statistical significance.** Test sets of 0.2-1.1 million rows make accuracy intervals at most 0.006 wide, so tiny differences exclude zero; mean-attack-recall intervals are wider (up to about 0.08). Effects are judged by size.
- **Seeds.** The seven-model comparison and the 2017 RF retrain use one training seed; the 2018 RF retrain used four (accuracy std <= 0.002).
- **Model configurations.** LogisticRegression hit its iteration limit in 9 of 12 runs, MLP stopped after 14-47 epochs without class weights, and GaussianNB is near chance on cPacket; their leak effects are not interpreted.
- **Subsampling.** The comparison trains on 600k-row stratified subsamples; the 2018 RF there scores below the full-data RF (fixA random 0.831 vs 0.953), and its leak effect differs too (leaky - fixA +0.165 random, +0.023 temporal, against +0.044 and -0.073 on full data). On 2017 the subsample RF matches the full-data RF (+0.098 and +0.093 against +0.116 and +0.107). For RF on 2018, the full-data results of section 5.3 are the reference.
- **Tiny classes.** Several classes have fewer than 60 test rows (2017 Heartbleed 3, Web_SQL_Injection 6; 2018 SQL_Injection 26, XSS 58); their per-class results are anecdotal.
- **Leaked rows' content.** Most leaked attack rows are packet fragments without attack content, so their labels are themselves questionable; this is a related dataset-quality issue, not measured here.

## 8 Conclusion and recommendations

NTLFlowLyzer leaks each flow's capture time into the IAT features of one-packet directions, three published BCCC datasets carry the leak in 35-65% of rows, and models exploit it. Results on these datasets that keep the IAT features, particularly under random splits, may be inflated or split-dependent and warrant re-examination.

1. **Tool maintainers.** Fix `calculate_IAT` so that a single-packet direction returns 0 (or no IAT), and fix the FIN handling behind the ghost flows (issue #29). A report with the 21-packet reproducer is ready to file.
2. **Dataset maintainers.** Publish corrected CSVs or a correction notice, and document which rows were affected.
3. **Users of the current CSVs.** Set every IAT value > 1e9 to 0 (equivalent to the code fix) or drop the IAT columns; both give nearly the same results in our tests (section 5.5). Report the split type, and prefer a temporal or per-capture-day split.
4. **Authors of existing studies.** Check whether IAT features were used and how the data was split; if both apply, re-running with the remedy above shows how much of the result depended on the leak.

## Data availability

All results, scripts and the compiled master report are in `~/Desktop/NTL_leak_research/` (944 files copied, 48 large arrays symlinked); `MANIFEST.tsv` maps every file to its original location.

| Folder | Contents |
|---|---|
| 00_MASTER | `NTL_timestamp_leak_MASTER.md` (every finding and table), this draft, the executive summary |
| 01_reproducer | 21-packet pcap, configs and outputs reproducing the bug |
| 02_census | Per-class, per-file, calendar and flow-shape census of each dataset |
| 03_exp1_shipped_models_timestamp_change | Shipped 2018 RF, KNN and ensemble with timestamps changed |
| 04_exp2_timestamp_only | Timestamp-only decision tree, three datasets, two splits |
| 05_exp3_rf_retrain | RandomForest leaky / fixA / fixB retrains, 2018 and 2017 |
| 06_model_comparison | 120-run seven-model comparison, bootstrap CIs, validity checks |
| 07_literature | Literature screen: 20 counted, 20 excluded with reasons |
| code | Every script, by stage |

The published CSVs and large feature caches stay on the data drive; `EXTERNAL_DATA.md` lists where.
