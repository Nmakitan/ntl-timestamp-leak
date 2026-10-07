# NTLFlowLyzer timestamp leak: master report (all findings and data)

Built 2026-10-03 17:22 by `~/Desktop/build_NTL_master.py` from the project's result folders. Everything below is copied or generated from those sources; nothing is retyped by hand except Part A.

**Contents**

- **0. Paper draft**: abstract, research argument, key tables (export of the shared doc).
- **A. Executive summary**: every finding in one place, with the key numbers.
- **B. Main report** (sections 0-11): bug, census of three datasets, experiments 1-3, replication on 2017, novelty check.
- **C. Model comparison** (section 12): seven model families × three datasets × two splits × five conditions, with bootstrap CIs, the drop-IAT control and validity checks.
- **D. Source write-ups, verbatim**: reproducer, all censuses, flow shapes, experiment write-ups, hand checks.
- **E. Data-file index**: where every data file lives, with sizes and row counts.
- **F. Literature screen**: works that use the BCCC datasets (counted and excluded, with reasons).

All raw data, organised by stage: `~/Desktop/NTL_leak_research/` (see its README.md and MANIFEST.tsv).


---

# 0. Paper draft

Source: the shared doc, exported to `~/Desktop/NTL_paper_draft.md`. Figure 1 is a live chart in the doc; its numbers are in Part C, section 12.1.


Draft, 2026-10-03 (revised after review). Local copy of the shared doc (https://claude.ai/code/artifact/82dd330c-302a-4860-b4a1-449f60190331); Figure 1 is a live chart there and a data table here.

### Abstract

NTLFlowLyzer, the flow-feature extractor behind the BCCC family of intrusion detection datasets, writes each flow's absolute start time (a Unix timestamp) into its inter-arrival-time (IAT) features whenever a flow direction contains exactly one packet. We reproduce the defect on the current upstream code with a 21-packet synthetic capture and trace it to a single function. A census of three published datasets finds it in 35.5% of BCCC-CSE-CIC-IDS2018 rows, 38.5% of BCCC-CIC-IDS-2017 rows and 65.4% of BCCC-cPacket-Cloud-DDoS-2024 rows, with no exception to the one-packet rule in 51.3 million rows. The leak is exploitable: under a random train/test split, the timestamp alone recovers 80-98% of the leaked attack rows. Across seven model families retrained with and without the leak, it shifts accuracy by up to 18 points. It inflates results under random splits and makes them split-dependent; distance-based KNN is inflated on every dataset and split. Setting the leaked cells to zero, or dropping the IAT features, removes the leak; both give the same results within 0.02 accuracy for six of seven model families. At least 20 studies from 2024-2026 report experiments on these datasets, several with accuracy or F1 at or above 99%. Those that kept the IAT features, particularly under random splits, may report inflated or split-dependent results and warrant re-examination.

### 1 Introduction and research argument

We claim that a defect in NTLFlowLyzer leaks capture time into three public intrusion detection datasets, that the leak changes model results, and that published work on these datasets may therefore warrant re-examination. The argument has five steps, each backed by its own evidence.

| Step | Claim | Evidence | Section |
|---|---|---|---|
| 1 | The tool writes absolute timestamps into IAT features | Minimal 21-packet pcap on upstream commit d99cd53; root cause in `calculate_IAT`; our own fork (two commits changing only continuous-batch polling) gives byte-identical output | 3 |
| 2 | The published datasets were built with this behaviour | 35-65% of rows leaked; 0 violations of the one-packet rule in 51.3M rows; every leaked value is the flow's true UTC start time on its documented capture day | 3 |
| 3 | The leak is exploitable | A decision tree on the timestamp alone recovers 80-98% of leaked attack rows under a random split | 5.1 |
| 4 | The leak changes results | Across seven model families (GaussianNB excluded from interpretation), accuracy shifts by up to 18 points between leaky and fixed data; our own KNN's 0.993 accuracy falls to 0.871 when only timestamps change | 5.2-5.4 |
| 5 | The fixed baseline is clean | Zeroing leaked cells (fixA) matches dropping all IAT columns (dropIAT) within 0.02 accuracy, except RF on 2018 (5.5); units check confirms the 1e9 threshold | 5.5 |

The claim about other research is deliberately limited. We show that the conditions for an inflated result exist in these datasets and are met by common practice (random splits, all features kept). We do not reproduce or assess individual published studies; section 6 counts how many studies use these datasets and states which setups are exposed.

### 2 Background

NTLFlowLyzer is presented by its authors as a flow-feature extractor that resolves the anomalies of earlier tools such as CICFlowMeter. The BCCC group re-extracted several benchmark captures with it and published them as BCCC-CSE-CIC-IDS2018, BCCC-CIC-IDS-2017 and BCCC-cPacket-Cloud-DDoS-2024. The original CICFlowMeter versions of CIC-IDS2017 and CSE-CIC-IDS2018 are a different release and are not examined here.

- **IAT features.** Each flow carries up to 30 inter-arrival-time statistics (mean, std, max, min, total, median, mode and others) per direction and combined. Legitimate values are seconds between packets: in these datasets the largest is about 3.2e4 s.
- **Why capture time leaks labels.** Each attack in these captures ran in its own time window. A model that sees the flow's start time can map time windows to classes without learning anything about the traffic.
- **Why the split matters.** A random split puts training and test flows from the same windows side by side, so time identifies the class. A temporal split puts test flows after the training windows, where learned time thresholds may not reach.
- **Why the model matters.** Trees can split on exact time ranges. After standard scaling, a ~1.5e9 value dominates Euclidean distance, so KNN's nearest neighbours become the flows nearest in time.

### 3 The defect

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

### 4 Data and methods

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

### 5 Results

The leak is exploitable, it changes the results of every leak-sensitive model, and the fixed baseline is clean.

#### 5.1 The timestamp alone identifies leaked attack rows

**Table 2. Timestamp-only decision tree** (pre-specified: depth 20, balanced weights), scored on leaked test rows

| Dataset | Mean attack-class recall, random | Pooled attack-row recall, random | Mean attack-class recall, temporal |
|---|---:|---:|---:|
| BCCC-CSE-CIC-IDS2018 | 0.80 | 1.000 | 0.22 |
| BCCC-CIC-IDS-2017 | 0.90 | 0.997 | 0.13 |
| BCCC-cPacket-Cloud-DDoS-2024 | 0.98 | 0.990 | 0.23 |

Under a random split one feature, the timestamp, recovers almost every leaked attack row. Under a temporal split it mostly fails, because test flows fall after the learned time windows.

#### 5.2 Our 2018 models from a separate IDS study depend on the timestamp

**Table 3. Accuracy when only the leaked timestamps change** (original temporal test split; KNN and ensemble on a 20,001-row stratified sample, population-weighted)

| Condition | RF | KNN | Ensemble |
|---|---:|---:|---:|
| As published | 0.893 | 0.993 | 0.993 |
| +8 years | 0.875 | 0.871 | 0.871 |
| +1 day | 0.838 | 0.904 | 0.904 |
| Leaked cells = 0 | 0.875 | 0.871 | 0.871 |

The KNN and ensemble owe their whole advantage over the RF to the leak. The RF loses 20,381 correct attack detections that depended only on the timestamp.

#### 5.3 Retraining with and without the leak (RandomForest)

**Table 4. RF accuracy, all test rows** (2018: mean of 4 seeds; 2017: seed 0)

| Dataset, split | Leaky | Fixed (fixA) | Leaky - fixA |
|---|---:|---:|---:|
| 2018 random | 0.998 | 0.953 | +0.044 |
| 2018 temporal | 0.892 | 0.965 | -0.073 |
| 2017 random | 0.992 | 0.875 | +0.116 |
| 2017 temporal | 0.940 | 0.833 | +0.107 |

On multi-packet flows all variants score 0.99-1.00 on both datasets: the whole effect, in either direction, sits in the one-packet rows.

#### 5.4 Seven model families

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

#### 5.5 The fixed baseline does not leak

Zeroing leaked cells could itself act as a leak flag, since leaking is class-dependent. Two checks rule this out.

**Table 5. Fixed-baseline checks**

| Check | 2018 | 2017 | cPacket |
|---|---|---|---|
| Leaked values (epoch band) | 1.519-1.520e9 (Feb 2018) | 1.499e9 (Jul 2017) | 1.703e9 (Dec 2023) |
| Largest legitimate IAT (s) | 3.2e4 | 2.9e4 | 2.9e4 |
| Legitimate cells in (1e6, 1e9] | 0 | 0 | 0 |
| Zero-mask-only tree, macro F1: legitimate zeros vs fixA zeros | 0.333 vs 0.334 | 0.117 vs 0.129 | 0.108 vs 0.112 |

Retraining with every IAT column removed (dropIAT) matches fixA within 0.02 accuracy and +/-0.01 mean attack recall for DecisionTree, XGBoost, MLP and GaussianNB, and within 0.001 accuracy for KNN, on every dataset and split. The one exception, RF on 2018 (+0.047 random, -0.033 temporal), flips sign between splits; it traces to how that RF assigns one-packet rows that are identical across HOIC, Bot and Benign once the timestamp is gone.

### 6 Potential impact on published research

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

### 7 Limitations

The defect and its prevalence are established without qualification; the size of its effect on results depends on setup, and its effect on published work is not measured.

- **Published work.** We count studies; we do not reproduce them. The literature screen read abstracts only, partly by automated classification, so the count of 20 is a floor, not a census.
- **Direction of the effect.** The leak inflates results under random splits but can lower them under temporal splits (2018 RF: -7.3 points). The safe claim is "unreliable and split-dependent", not "always inflated".
- **Statistical significance.** Test sets of 0.2-1.1 million rows make accuracy intervals at most 0.006 wide, so tiny differences exclude zero; mean-attack-recall intervals are wider (up to about 0.08). Effects are judged by size.
- **Seeds.** The seven-model comparison and the 2017 RF retrain use one training seed; the 2018 RF retrain used four (accuracy std <= 0.002).
- **Model configurations.** LogisticRegression hit its iteration limit in 9 of 12 runs, MLP stopped after 14-47 epochs without class weights, and GaussianNB is near chance on cPacket; their leak effects are not interpreted.
- **Subsampling.** The comparison trains on 600k-row stratified subsamples; the 2018 RF there scores below the full-data RF (fixA random 0.831 vs 0.953), and its leak effect differs too (leaky - fixA +0.165 random, +0.023 temporal, against +0.044 and -0.073 on full data). On 2017 the subsample RF matches the full-data RF (+0.098 and +0.093 against +0.116 and +0.107). For RF on 2018, the full-data results of section 5.3 are the reference.
- **Tiny classes.** Several classes have fewer than 60 test rows (2017 Heartbleed 3, Web_SQL_Injection 6; 2018 SQL_Injection 26, XSS 58); their per-class results are anecdotal.
- **Leaked rows' content.** Most leaked attack rows are packet fragments without attack content, so their labels are themselves questionable; this is a related dataset-quality issue, not measured here.

### 8 Conclusion and recommendations

NTLFlowLyzer leaks each flow's capture time into the IAT features of one-packet directions, three published BCCC datasets carry the leak in 35-65% of rows, and models exploit it. Results on these datasets that keep the IAT features, particularly under random splits, may be inflated or split-dependent and warrant re-examination.

1. **Tool maintainers.** Fix `calculate_IAT` so that a single-packet direction returns 0 (or no IAT), and fix the FIN handling behind the ghost flows (issue #29). A report with the 21-packet reproducer is ready to file.
2. **Dataset maintainers.** Publish corrected CSVs or a correction notice, and document which rows were affected.
3. **Users of the current CSVs.** Set every IAT value > 1e9 to 0 (equivalent to the code fix) or drop the IAT columns; both give nearly the same results in our tests (section 5.5). Report the split type, and prefer a temporal or per-capture-day split.
4. **Authors of existing studies.** Check whether IAT features were used and how the data was split; if both apply, re-running with the remedy above shows how much of the result depended on the leak.

### Data availability

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


---

# A. Executive summary


Status 2026-10-03, 09:15 (all runs finished, including the overnight KNN runs). Sections refer to Parts B (sections 0-11) and C (section 12) of this file.

### The defect

1. **Bug (section 1).** NTLFlowLyzer writes the flow's absolute start time (Unix epoch, seconds) into every IAT
   statistic of a direction that holds exactly one packet (`features/utils.py:20-27`, `calculate_IAT`). Reproduced
   from a 21-packet synthetic pcap on upstream commit `d99cd53`; the author's fork gives byte-identical output.
   A second, already-reported bug (upstream issue #29) splits the closing ACK of a FIN exchange into its own
   1-packet "ghost" flow, which then also leaks.
2. **Not reported before (section 10).** No upstream issue, PR or publication found mentions the IAT timestamp leak
   (GitHub fully checked; literature check partial).

### How much of the published data is affected

| dataset | rows | leaked rows | % | rule violations | leaked values on capture day |
|---|---:|---:|---:|---:|---|
| BCCC-CSE-CIC-IDS2018 | 48,182,782 | 17,108,403 | 35.5 | 0 | yes (per attack file, own window) |
| BCCC-CIC-IDS-2017 | 2,438,052 | 939,324 | 38.5 | 0 | 100.00% |
| BCCC-cPacket-Cloud-DDoS-2024 | 700,774 | 458,427 | 65.4 | 0 | 100.00% |
| BCCC-DLLayer-IDS-2025 | not NTLFlowLyzer output | - | - | - | no timestamps |

- 0 violations of the rule "leak ⇔ exactly one packet in that direction" in 51.3M rows: the datasets were built with
  the buggy code. Every leaked value is the flow's true UTC start time (sections 2, 9; D2-D7).
- **Leak rate depends strongly on class**: from 0.05% (2017 DDoS_LOIT) or 0.07% (2018 LOIC) to 100% (2018 FTP and
  SlowHTTP, 2017 Port_Scan 99.9%). Most leaked attack rows are fragments split off real sessions (lone RST/ACK,
  ghost ACKs) with no attack content; exceptions where the leaked rows are the attack itself: 2017 Port_Scan,
  Botnet_ARES and cPacket BYPass-V1 (section 9, D4, D6).
- Units check (12.2a): every leaked cell sits in one narrow epoch band per dataset (Jul 2017, Feb 2018, Dec 2023);
  legitimate IATs top out near 3e4 s and no cell lies between 1e6 and 1e9, so the 1e9 threshold is clean.

### Is the leak exploitable?

- **Timestamp alone (section 9, Experiment 2).** On a random split, a pre-specified decision tree on the timestamp
  alone recovers the attack rows that carry it: mean attack-class recall 0.80 (2018), 0.90 (2017), 0.98 (cPacket) on
  leaked test rows. On a temporal split it mostly fails (0.13-0.23).
- **Existing 2018 models (section 4, Experiment 1).** Changing only the leaked timestamps in the test set:
  the shipped RF loses 20,381 correct attack detections that depended only on the timestamp; **KNN and the
  soft-voting ensemble fall from 0.993 to 0.871**, i.e. their whole advantage over the RF came from the leak
  (scaled ~1.5e9 values dominate the distance, so "nearest neighbour" becomes "nearest in time").

### Does it change results? Retraining with and without the leak

- **RF, 2018, 4 seeds (section 6).** Random split: the leak inflates accuracy by 4.4 points (0.998 vs 0.953).
  Temporal split: it *hurts* by 7.3 points (0.892 vs 0.965), because learned capture windows do not carry over.
- **RF, 2017 replication (section 11).** Random split inflation replicates and is larger (+11.6 points). The temporal
  sign reverses overall (+10.7 for the leaky model): benign fragments are only separable by time of day.
- **Where it happens.** On multi-packet flows all variants are equal (~0.99-1.00) on both datasets: the whole
  effect, in either direction, sits in the 1-packet rows.
- **Seven model families × three datasets (section 12).** Accuracy, leaky − fixA, all test rows:

  | model | 2018 random | 2018 temporal | 2017 random | 2017 temporal | cPacket random | cPacket temporal |
  |---|---:|---:|---:|---:|---:|---:|
  | DecisionTree | +0.045 | −0.028 | +0.061 | +0.043 | +0.090 | −0.057 |
  | XGBoost | +0.048 | +0.048 | +0.063 | +0.091 | +0.083 | +0.018 |
  | RandomForest | +0.165 | +0.023 | +0.098 | +0.093 | +0.144 | −0.016 |
  | LogReg | +0.115 | +0.002 | +0.003 | +0.004 | +0.000 | +0.001 |
  | MLP | −0.000 | −0.000 | +0.000 | +0.000 | +0.003 | +0.006 |
  | **KNN** | **+0.116** | **+0.090** | **+0.100** | **+0.056** | **+0.183** | **+0.011** |
  | GaussianNB (broken baseline) | +0.032 | −0.005 | −0.007 | +0.055 | +0.192 | +0.190 |

  - All three tree models (DT, XGBoost, RF) are inflated by the leak on every random split (+0.045 to +0.165); on
    temporal splits the sign is mixed, as in sections 6 and 11. Mean attack recall shows the same pattern (inflation up to +0.26 on cPacket).
  - **KNN is inflated on every dataset and both splits, temporal included** (+0.011 to +0.183 accuracy; mean attack
    recall +0.04 to +0.20), unlike the trees, whose temporal-split sign is mixed. This is the section 4.2 mechanism
    at scale: after scaling, a ~1.5e9 IAT dominates the distance, so the nearest neighbours are the flows nearest in
    time, and "nearest in time" still works for test flows just after the training window. On leaked test rows
    (2018 both splits, 2017 random), leaky KNN's mean attack recall is 0.85-0.91; with timestamps moved 8 years it
    falls to 0.15-0.20, below the retrained fixA model (0.37-0.64): it recognises leaked attack rows almost only by time.
  - **The retrained KNN reproduces the shipped one.** 2018 temporal split (the original pipeline's split): leaky
    0.993, +8y 0.871; the shipped ONNX KNN in section 4.2 gave 0.993 and 0.871 on a 20k sample.
  - Moving leaked timestamps 8 years (no retrain) costs the trees up to 0.44 accuracy on cPacket and 0.12-0.15 on
    2018 random: they rely on exact capture times.
  - Paired bootstrap 95% CIs (B = 1,000): for the five models other than GaussianNB and KNN, 49 of 60 leaky − fixA
    differences (accuracy and mean attack recall) exclude 0; for KNN, all 12 do. Accuracy CIs are at most 0.006 wide because the test sets are large, so even
    tiny differences come out "significant": judge them by size, not by the star. They cover test sampling only, not training randomness (single seed).
  - MLP and LogReg show little leaky−fixA difference, but both are under-trained (MLP early-stopped after 14-47
    epochs, no class weights; LogReg at the iteration limit in 9 of 12 runs), and setting leaked cells to 0 still costs
    MLP 0.04-0.08 accuracy, so it does use those features. Do not read them as immune.

### Possible impact on published work (Part F)

- OpenAlex full-text search (2026-10-03) for the exact dataset names: about 40 distinct works name a BCCC
  NTLFlowLyzer dataset; **at least 20 report experiments on one in their abstracts** (2024-2026), several with
  accuracy or F1 at or above 99% (e.g. 99.90% on BCCC-CIC-IDS-2017, 99.58% F1 on BCCC-CSE-CIC-IDS2018, up to
  99.99% on cPacket). The cPacket dataset paper has 48 citing works in Semantic Scholar.
- No study was reproduced. The claim is that the conditions for inflated results exist and are met by common
  practice (IAT features kept, random split or k-fold CV), so these results warrant re-examination.

### Validity of the fixed baseline (fixA)

A reviewer's main concern: fixA sets leaked cells to 0, and since leaking is class-dependent, "cell = 0" could
itself be a leak flag. Two checks (sections 12.1 and 12.2b):

- **Mask-only models:** a tree trained only on fixA's zero pattern beats one trained on legitimate zeros alone by at
  most 0.012 macro F1, and mean attack recall moves by −0.03 to +0.01. Legitimate exact zeros are common (up to 65% of
  IAT cells, depending on class), which hides the flag.
- **Drop-IAT control (36 new runs):** retraining with every IAT column removed gives the same results as fixA for
  DT, XGBoost, MLP and GaussianNB on every dataset and split (within 0.02 accuracy, ±0.01 mean attack recall; 31 of 48 such differences have CIs excluding 0, i.e. detectable
  but tiny). KNN (6 more runs) agrees within 0.001 accuracy everywhere; its mean attack recall is +0.03 higher
  with fixA on 2017 only (both splits), within ±0.002 elsewhere.
  Only RF on 2018 differs (+0.047 random, −0.033 temporal); the sign flips between splits and the gap traces to how
  that RF assigns 1-packet rows that are identical across HOIC, Bot and Benign: a tie-break, not a leak.
- **Conclusion: fixA is a valid leak-free baseline.**

### Model coverage

| model | where | datasets | conditions |
|---|---|---|---|
| RF (shipped ONNX) | section 4 | 2018 | timestamp changes only (no retrain) |
| KNN, soft-voting ensemble (shipped ONNX) | section 4.2 | 2018 | timestamp changes only, 20,001-row stratified sample |
| RF retrain | sections 6, 11 | 2018 (4 seeds), 2017 (1 seed) | leaky, fixA, fixB (+ 1-packet rows dropped) |
| Timestamp-only tree | sections 5, 9 | 2018, 2017, cPacket | balanced (pre-specified) and unweighted |
| GaussianNB, DT, LogReg, XGBoost, RF, MLP, KNN | section 12 | 2018, 2017, cPacket | leaky, +8y, zero, fixA; dropIAT (all but LogReg); full test sets |

KNN in section 12 is retrained (StandardScaler + distance-weighted 5-NN, as the shipped model) and scored on the full
test sets (overnight, 2026-10-02/03; up to 1 h 51 min per run on 2018). Not covered: the soft-voting ensemble was
not retrained. LinearSVC was dropped from section 12 (> 2.5 h per run). LightGBM and MinMax-scaled MLP were
planned as optional and not run.

### Caveats

- Single training seed in sections 11 and 12 (2018 RF seed-to-seed std was ≤ 0.002 accuracy in section 6).
- Tiny classes (2017 Heartbleed 3 test rows, Web_SQL_Injection 6; 2018 SQL_Injection 26, XSS 58): per-class
  counts for them are anecdotal.
- Accuracy on leaked rows is not comparable to all-row accuracy (different class mix); use mean attack recall.
- Section 12 trains on 600k-row stratified subsamples; the 2018 RF there scores below the full-training-set RF of
  section 6 (fixA random 0.831 vs 0.953).
- Timings in section 12 come from two machines; compare only within one machine.
- Laptop disk incident (2026-10-02): 60 scikit-learn files on the laptop were corrupted on disk and repaired from
  the PC; its data caches were checksum-identical, a laptop XGBoost run reproduced exactly on the PC, and a recheck
  after the overnight runs found everything still identical. Results are unaffected; the laptop's hard disk
  (Seagate ST1000LM035) should be checked (`smartctl`).
- Feature sets differ: 313 features (30 IAT) on 2018 and cPacket, 114 (15 IAT) on 2017.

### Open items (updates to section 8)

- Section 8 items 1 (Gate 1 comparison), 3 (possible duplicate benign rows), 4 (bulk-rate artifact),
  5 (upstream issue), 7 (disk check): status not recorded since the main report; check before publishing.
- Item 6 (generality): done for three datasets (sections 9, 11) and extended to six model families (section 12).
- KNN retrain: done (section 12). New: LogReg with more iterations if it is to be reported; MLP with class weights
  and more epochs if MLP robustness is to be claimed; systematic literature check (section 10).


---

# B. Main report: bug, censuses, experiments 1-3, 2017 replication (sections 0-11)

Source: `~/Desktop/NTL_timestamp_leak_REPORT.md` (written before the model comparison; its section 8 open items are updated in Part A).


Final, 2026-10-02. All steps complete. Experiment 3 uses **seeds 0-3** for all six split × variant combinations
(24 runs); the seed-4 tier was stopped by decision, and its two completed runs are kept aside in
`results/exp3/excluded_seed4/` and not used.

---

### 0. Summary

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

### 1. Step 1: minimal reproducer

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

### 2. Step 2: census of the published dataset

**Data.** 34 original per-day files, 10 capture days, 48,182,782 rows, one identical 323-column header. Inner files
dated 2023-07..2023-11, archive entries 2024-02-23, downloaded 2026-09-04. Wed 28-02 has no attack file in the published
zip. Days 14-02, 15-02, 01-03 read from their inner zips (Deflate64, streamed with `unzip -p`). 0 files failed.
Leak = IAT value > 1e9. Column names: 30 IAT columns (10 combined `packets_IAT_*`/`packet_IAT_*`, 10 `fwd_packets_IAT_*`,
10 `bwd_packets_IAT_*`), `packets_count`, `fwd_packets_count`, `bwd_packets_count`, `label`, `timestamp`.

#### 2.1 Per class

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

#### 2.2 Rule check and value check

- fwd leak <=> `fwd_packets_count == 1`, bwd leak <=> `bwd_packets_count == 1`, combined leak <=> `packets_count == 1`:
  **0 violations in 48,182,782 rows** for all three.
- Leaked fwd value − `timestamp` column = exactly **+18,000 s** in 96-100% of rows per file (100% in most attack files);
  the rest within ~5 s. The `timestamp` column (and `flow_id` time) is local UTC−5; the leaked IAT is the true UTC epoch
  of the flow start.

#### 2.3 Calendar of leaked values (UTC)

Each attack file's leaked values fall on its own capture day in a narrow window:
FTP 14-02 14:33-16:10 · SSH 14-02 18:01-19:32 · GoldenEye 15-02 13:27-14:11 · Slowloris 15-02 15:41-15:42 ·
SlowHTTP 16-02 14:12-15:05 · HULK 16-02 17:45-17:58 · LOIC 20-02 14:24-14:33 · HOIC 21-02 18:11-19:05 ·
Web 22-02 14:13-15:23 and 23-02 14:04-15:03 · XSS 22-02 17:51-18:29 and 23-02 17:01-18:10 ·
SQLi 22-02 20:14-20:27 and 23-02 19:05-19:17 · Infiltration 01-03 19:37 · Bot 02-03 14:13-19:54.
Benign spans each day ~12:20 UTC to ~00:40 the next day.

**Anomaly (not yet checked):** some benign files contain leaked values from other days (fri_23_02 benign: 3,250 rows from
21-22 Feb; fri_02_03 benign: 6,849 rows incl. 27-28 Feb); wed_28_02 and fri_02_03 benign share an identical minimum leaked
value (2018-02-27 12:18:27.392139), wed_28_02 and thu_01_03 an identical maximum. Possibly duplicated rows across day files.

#### 2.4 Other columns

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

### 3. The models under test

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

### 4. Experiment 1: change only the timestamps in the test set (existing models)

Leaked test rows: 359,693 of 1,087,223 (33.1%): Benign 197,191 · Bot 35,830 (50.1%) · HOIC 97,477 (39.0%) ·
SlowHTTP 26,387 (100%) · HULK 2,698 (3.4%) · Web 66 · XSS 30 · SQLi 14 · LOIC 0.
Conditions: **+8 years** (+252,460,800 s), **+1 day**, **shuffle** (each leaked row takes another leaked row's
timestamp, one offset applied to all its leaked cells; 5 seeds), **zero** (leaked cells = 0: bug-fixed data fed to the
leaky model, not a retrain). Arithmetic in float64, cast to float32 for scoring. Sanity check: predictions on
non-leaked rows unchanged in every condition (passed everywhere).

#### 4.1 RF on the full test set

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

#### 4.2 KNN and ensemble (stratified 20,001-row sample)

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

### 5. Experiment 2: timestamp as the only feature

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

### 6. Experiment 3: retrain with and without the leak

**Variants.** `leaky` = data as is; `fixA` = every leaked IAT cell set to 0 in train and test (equals the per-direction
code fix, given 0 rule violations); `fixB` = fixA + all rows with `packets_count == 1` dropped from train and test.
**Splits.** `temporal` = existing split; `random` = Experiment 2's saved indices. Split fixed across seeds.
**Model.** `RandomForestClassifier(n_estimators=200, max_depth=30, min_samples_leaf=10, class_weight="balanced",
n_jobs=2, random_state=seed)`, 313 features, sklearn predict (no ONNX). Each run ~15-27 min, peak RSS 5.3-6.7 GB.
**Pipeline check:** temporal-leaky s0 = 0.8919, identical to the original model.
**Leak check:** split thresholds > 1e9: leaky models 17,741-22,657 per forest (~40% of all split nodes, all on IAT
features); fixA/fixB models 0, except `random_fixA_s2` with 1 threshold on a **non-IAT** feature (one of the rate
columns in §2.4; not a timestamp).

#### 6.1 All test rows (mean ± std, seeds 0-3)

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

#### 6.2 Leaked test rows (rows leaked in the unmodified data, seeds 0-3)

| Split | Variant | Accuracy | Macro-F1 | Benign | Bot | Web | XSS | HOIC | HULK | SQLi |
|---|---|---|---|---|---|---|---|---|---|---|
| temporal | leaky | 0.6736 | 0.304 | 0.991 | 0.009 | 0.030 | 0.233 | 0.205 | 0.088 | 1.000 |
| temporal | fixA | 0.8933 | 0.443 | 0.998 | 0.010 | 0.955 | 0.933 | 1.000 | 0.066 | 0.357 |
| random | leaky | 0.9935 | 0.727 | 0.988 | 1.000 | 0.984 | 0.955 | 1.000 | 0.994 | 0.818 |
| random | fixA | 0.8727 | 0.508 | 0.929 | 0.007 | 0.952 | 0.955 | 1.000 | 0.825 | 0.455 |

#### 6.3 Rare classes, exact counts (correct / support, seeds 0, 1, 2, 3)

| Split | Variant | SQL_Injection | Brute_Force_XSS | Brute_Force_Web |
|---|---|---|---|---|
| temporal | leaky | 25/26 ×4 | 34, 38, 34, 34 /58 | 68/134 ×4 |
| temporal | fixA | 16/26 ×4 | 56/58 ×4 | 131/134 ×4 |
| temporal | fixB | 11/12 ×4 | 28/28 ×4 | 68, 66, 66, 68 /68 |
| random | leaky | 24, 23, 23, 23 /26 | 56/58 ×4 | 133/134 ×4 |
| random | fixA | 19/26 ×4 | 56/58 ×4 | 131/134 ×4 |
| random | fixB | 14/15 ×4 | 35/36 ×4 | 72/72 ×4 |

#### 6.4 Differences (mean leaky − mean fixed)

| Split | Comparison | Δ accuracy | Δ macro-F1 | Main per-class Δ recall |
|---|---|---|---|---|
| temporal | leaky − fixA | **−0.0726** | −0.020 | Web −0.470, XSS −0.362, HOIC −0.310, SQLi +0.346 |
| random | leaky − fixA | **+0.0443** | +0.059 | Bot +0.497, Benign +0.021, SQLi +0.163 |
| temporal | leaky − fixB* | −0.1072 | −0.213 | (different test rows) |
| random | leaky − fixB* | −0.0024 | −0.163 | (different test rows) |

#### 6.5 Same rows: all variants on the multi-packet test rows (seeds 0-2)

| Split | Multi-packet test rows (leaked) | leaky acc / mF1 | fixA acc / mF1 | fixB acc / mF1 |
|---|---|---|---|---|
| temporal | 776,198 of 1,087,223 (48,668) | 0.9992 / 0.966 | 0.9991 / 0.967 | 0.9991 / 0.968 |
| random | 738,622 of 1,087,225 (49,815) | 1.0000 / 0.990 | 1.0000 / 0.981 | 1.0000 / 0.986 |

#### 6.6 Interpretation

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

### 7. Methods notes and deviations

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

### 8. Open items

1. **Gate 1:** compare the per-class census (§2.1) with the threshold written down before Step 2.
2. **Seeds:** Experiment 3 final with seeds 0-3 (seed-to-seed std ≤ 0.002 in accuracy); seed 4 dropped.
3. **Possible duplicate benign rows** across day files (§2.3): a targeted `flow_id` check (~20 min).
4. **Bulk-rate artifact** (§2.4): implausible `avg_bwd_bulk_rate` values; separate from the timestamp bug.
5. **Upstream issue:** Step 1 material (pcap, config, output, commit) is ready to attach; root cause
   `features/utils.py:20-27` and `network_flow_capturer.py:305-311`.
6. **Generality:** census and timestamp-only baseline on 2017 / 2018 / 2023 (§9) and a single-seed 2×2 retrain on 2017 (§11): random-split inflation and the 1-packet locus replicate; the temporal-split harm does not replicate overall (§11.7).
7. **Disk:** run `sudo smartctl -t long /dev/sda` and back up irreplaceable files on that drive.

---

### 9. Other BCCC datasets: census, flow shapes and exploitability

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

#### What the leaked rows are (flow shapes)

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

#### Is the leak exploitable? Timestamp-only baseline (Experiment 2) on all three datasets

**Claim: the timestamp alone identifies the attack rows that carry it** (not: the timestamp classifies all rows).
Single feature t = smallest leaked IAT value (0 if none). Random split = stratified 75/25 by class (random_state=0);
temporal = latest 25% by `timestamp` of each (file, class) (2018: the original pipeline's split, with class caps;
2017 / cPacket: same rule, no caps). Scored on **leaked test rows**. Attack classes = all non-Benign classes
(cPacket: the 17 `Attack / ...` subtypes; Suspicious is not counted as attack).

**Primary model, pre-specified:** DecisionTree(max_depth=20, min_samples_leaf=10, class_weight="balanced", random_state=0).
**Secondary model, added afterwards** (after the first 2017/cPacket results, not in the original spec): the same tree
without class weighting. Both are now run on all three datasets with the same feature and splits.
**Headline metric: mean attack-class recall** on leaked test rows.

##### random split, leaked test rows

| dataset | model | **mean attack-class recall** | attack classes with recall >= 0.90 | pooled attack-row recall | accuracy (majority guess) | macro-F1 |
|---|---|---:|---|---:|---|---:|
| CSE-CIC-IDS2018 | balanced tree (pre-specified) | **0.801** | 5 of 8 | 1.000 | 0.952 (0.526) | 0.546 |
| CSE-CIC-IDS2018 | unweighted tree (added afterwards) | **0.461** | 3 of 8 | 0.997 | 0.955 (0.526) | 0.504 |
| CIC-IDS-2017 | balanced tree (pre-specified) | **0.903** | 10 of 11 | 0.997 | 0.786 (0.668) | 0.319 |
| CIC-IDS-2017 | unweighted tree (added afterwards) | **0.223** | 2 of 11 | 0.939 | 0.969 (0.668) | 0.249 |
| cPacket (26 subtypes) | balanced tree (pre-specified) | **0.981** | 17 of 17 | 0.990 | 0.510 (0.534) | 0.412 |
| cPacket (26 subtypes) | unweighted tree (added afterwards) | **0.288** | 1 of 17 | 0.896 | 0.826 (0.534) | 0.239 |

##### temporal split, leaked test rows

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

### 10. Novelty check (partial, 2026-10-02)

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

### 11. Replication on BCCC-CIC-IDS-2017: single-seed 2 × 2 retrain

All 18 CSVs, 2,438,052 rows, **114 features**: every numeric column except `flow_id`, `src_ip`, `src_port`, `dst_ip`, `dst_port`, `timestamp`, `protocol` (text) and `label`; inf/NaN -> 0, float32 (full list: `BCCC-CIC-IDS-2017/exp3/cache/meta.json`). No class capping (memory estimate: 1.1 GB full matrix, 0.83 GB training subset). Splits = the Experiment 2 splits for 2017 (`exp2_label/splits.npz`): random = stratified 75/25, random_state=0; temporal = latest 25% by `timestamp` per (file, class). Variants: leaky; fixA (every IAT cell > 1e9 set to 0 in train and test); fixB (fixA + rows with `packets_count == 1` dropped from train and test). Model: RandomForestClassifier(n_estimators=200, max_depth=30, min_samples_leaf=10, class_weight='balanced', n_jobs=2, random_state=0), one process per run under `systemd-run --scope -p MemoryMax=6.5G -p MemorySwapMax=0`. Seed 0 only.

#### 11.1 Overall

| split | variant | n train | n test | acc (all) | macro-F1 (all) | acc (leaked rows) | macro-F1 (leaked) | split thresholds > 1e9 (on IAT) | fit s | peak RSS GB |
|---|---|---:|---:|---:|---:|---:|---:|---|---:|---:|
| random | leaky | 1,828,539 | 609,513 | 0.9915 | 0.7400 | 0.9850 | 0.6540 | 41107 (41107) | 245 | 2.44 |
| random | fixA | 1,828,539 | 609,513 | 0.8753 | 0.5343 | 0.6844 | 0.2313 | 0 (0) | 235 | 2.42 |
| random | fixB | 1,421,552 | 473,541 | 0.9939 | 0.7485 | 0.9940 | 0.4073 | 0 (0) | 204 | 2.28 |
| temporal | leaky | 1,828,539 | 609,513 | 0.9397 | 0.6327 | 0.8590 | 0.3882 | 33854 (33854) | 260 | 2.32 |
| temporal | fixA | 1,828,539 | 609,513 | 0.8326 | 0.4763 | 0.5870 | 0.1894 | 0 (0) | 236 | 2.32 |
| temporal | fixB | 1,419,623 | 475,470 | 0.9923 | 0.7422 | 0.9962 | 0.4155 | 0 (0) | 222 | 2.06 |

Leak check: 0 split thresholds > 1e9 on IAT features in every fixA/fixB forest.

#### 11.2 Per-class recall / precision, all test rows

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

#### 11.3 Per-class recall, leaked test rows (leaked in the unmodified data)

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

#### 11.4 Exact counts for classes with < 100 test rows (correct / support, all test rows)

| class | random leaky | random fixA | random fixB | temporal leaky | temporal fixA | temporal fixB |
|---|---|---|---|---|---|---|
| Heartbleed | 2/3 | 0/3 | 0/1 | 2/3 | 2/3 | 0/2 |
| Web_SQL_Injection | 4/6 | 3/6 | 1/3 | 4/6 | 5/6 | 3/3 |

#### 11.5 Same rows: multi-packet test rows (packets_count != 1)

| split | variant | rows | acc | macro-F1 |
|---|---|---:|---:|---:|
| random | leaky | 473,541 | 0.9964 | 0.7716 |
| random | fixA | 473,541 | 0.9948 | 0.7599 |
| random | fixB | 473,541 | 0.9939 | 0.7485 |
| temporal | leaky | 475,470 | 0.9902 | 0.7368 |
| temporal | fixA | 475,470 | 0.9928 | 0.8030 |
| temporal | fixB | 475,470 | 0.9923 | 0.7422 |

(fixB's test set *is* the multi-packet rows, so its row equals its all-rows result.)

#### 11.6 Differences, leaky − fixA

| split | Δ acc (all) | Δ macro-F1 | Δ acc (leaked rows) | Δ acc (multi-packet rows) | Δ recall per class (|Δ| ≥ 0.01) |
|---|---:|---:|---:|---:|---|
| random | +0.1162 | +0.2057 | +0.3006 | +0.0016 | Benign +0.143, DoS_GoldenEye +0.061, DoS_Hulk +0.059, DoS_Slowhttptest +0.268, DoS_Slowloris +0.168, FTP-Patator +0.165, Heartbleed +0.667, Web_Brute_Force +0.515, Web_SQL_Injection +0.167, Web_XSS +0.024 |
| temporal | +0.1070 | +0.1564 | +0.2720 | -0.0026 | Benign +0.134, Botnet_ARES -0.771, DoS_GoldenEye +0.010, DoS_Hulk +0.086, DoS_Slowhttptest +0.033, DoS_Slowloris +0.444, FTP-Patator -0.341, SSH-Patator -0.440, Web_Brute_Force +0.034, Web_SQL_Injection -0.167, Web_XSS -0.368 |

#### 11.7 Comparison with 2018 (§6): does the random split inflate and the temporal split hurt again?

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


---

# C. Section 12: model comparison across seven model families, three datasets, five conditions

Source: `~/Desktop/ntl_models/results/SUMMARY.md` (generated by `mc_report.py`). Code: `~/Desktop/ntl_models/` (mc_common.py, mc_run.py, mc_queue.sh, mc_bootstrap.py, mc_zerocheck.py, mc_pool.py).


Spec: fixed model list and configurations, seed 0, no per-condition tuning. Leaked cell = IAT column value > 1e9 (judged on the unmodified data). Conditions:
- **leaky**: train and test as is.
- **+8y**: same leaky model; leaked test cells + 252,460,800 s (8 years).
- **zero**: same leaky model; leaked test cells set to 0.
- **fixA**: retrain and test with every leaked IAT cell set to 0.
- **dropIAT**: retrain and test with every IAT column removed (30 of 313 features on 2018 and cPacket, 15 of 114 on 2017). No IAT information at all, so it is a leak-free reference for fixA: if fixA still carried the leak through its zeros, fixA would beat dropIAT by more than the legitimate IAT information is worth.

Training: 600k stratified subsample per dataset × split (every row of classes with < 1,000 training rows; all rows if < 600k); test = the full test split, identical across models and conditions (comparisons are paired). Mean attack recall = unweighted mean recall over attack classes with >= 10 rows in the subset (cPacket: `Attack` subtypes). 95% CIs: paired bootstrap over test rows, B = 1,000, seed 0 (`mc_bootstrap.py`); `*` = CI excludes 0. The CIs cover test-set sampling only, not training randomness (single seed).

Runs: 92 of 92 leaky/fixA runs (7 models × 3 datasets × 2 splits × 2, plus RF and XGBoost trained on the full 2018 training split × 2 splits × 2), 40 of 40 dropIAT runs (all models except LogReg). The full-train runs (`rffull`, `xgbfull`) answer whether the 600k subsample changes the 2018 leak effect. LinearSVC was dropped (> 2.5 h per run, single-threaded, ~6 GB on 2018). LogReg has no dropIAT run (user decision: slowest model, and it hits the iteration limit in most runs; see caveats). Bootstrap results available for 46 dataset × split × model triples. All data files and per-class detail: `ALL_RUNS_pooled.csv` (`mc_pool.py`), `BOOTSTRAP_CI.csv`.

Runs without a result (failed or in progress): finish_full, finish_knn

### 12.1 Headline differences (point estimate [95% bootstrap CI])

Positive leaky−X = the leaky model loses that much when the leak is broken or removed. fixA−dropIAT is how much more fixA gets than a model with no IAT columns at all: small or negative means fixA's zeros carry no leak signal beyond legitimate IAT information.

#### Accuracy, all test rows: leaky − (+8y)

| model | d2018 random | d2018 temporal | d2017 random | d2017 temporal | cpacket random | cpacket temporal |
|---|---:|---:|---:|---:|---:|---:|
| GaussianNB | +0.024 [+0.023, +0.024]* | +0.024 [+0.023, +0.024]* | +0.000 [-0.000, +0.000] | +0.000 [+0.000, +0.000]* | +0.000 [+0.000, +0.000] | +0.000 [+0.000, +0.000] |
| DecisionTree | +0.149 [+0.148, +0.150]* | +0.018 [+0.018, +0.018]* | +0.058 [+0.058, +0.059]* | +0.059 [+0.058, +0.059]* | +0.409 [+0.407, +0.412]* | +0.241 [+0.239, +0.243]* |
| LogReg (std) | +0.166 [+0.165, +0.167]* | +0.084 [+0.083, +0.085]* | +0.054 [+0.053, +0.054]* | +0.015 [+0.015, +0.015]* | +0.051 [+0.050, +0.052]* | +0.076 [+0.074, +0.077]* |
| XGBoost | +0.117 [+0.116, +0.118]* | +0.089 [+0.088, +0.090]* | +0.073 [+0.073, +0.074]* | +0.054 [+0.054, +0.055]* | +0.367 [+0.365, +0.370]* | +0.279 [+0.277, +0.282]* |
| RandomForest | +0.151 [+0.150, +0.152]* | +0.017 [+0.017, +0.017]* | +0.055 [+0.055, +0.056]* | +0.009 [+0.009, +0.009]* | +0.444 [+0.442, +0.447]* | +0.303 [+0.301, +0.305]* |
| MLP (std) | +0.000 [+0.000, +0.000]* | +0.000 [+0.000, +0.000] | -0.000 [-0.000, +0.000] | +0.000 [-0.000, +0.000] | +0.001 [+0.000, +0.001]* | +0.003 [+0.002, +0.003]* |
| KNN (std, k=5) | +0.149 [+0.149, +0.150]* | +0.122 [+0.122, +0.123]* | +0.055 [+0.055, +0.056]* | +0.048 [+0.048, +0.049]* | +0.388 [+0.386, +0.390]* | +0.255 [+0.253, +0.257]* |
| XGBoost, full train (2018) | +0.121 [+0.120, +0.122]* | +0.073 [+0.073, +0.074]* | - | - | - | - |
| RandomForest, full train (2018) | +0.147 [+0.147, +0.148]* | +0.017 [+0.017, +0.017]* | - | - | - | - |

#### Accuracy, all test rows: leaky − fixA

| model | d2018 random | d2018 temporal | d2017 random | d2017 temporal | cpacket random | cpacket temporal |
|---|---:|---:|---:|---:|---:|---:|
| GaussianNB | +0.032 [+0.031, +0.032]* | -0.005 [-0.006, -0.004]* | -0.007 [-0.008, -0.006]* | +0.055 [+0.054, +0.056]* | +0.192 [+0.190, +0.194]* | +0.190 [+0.188, +0.192]* |
| DecisionTree | +0.045 [+0.045, +0.045]* | -0.028 [-0.028, -0.027]* | +0.061 [+0.061, +0.062]* | +0.043 [+0.043, +0.044]* | +0.090 [+0.088, +0.092]* | -0.057 [-0.059, -0.055]* |
| LogReg (std) | +0.115 [+0.115, +0.116]* | +0.002 [+0.002, +0.002]* | +0.003 [+0.002, +0.003]* | +0.004 [+0.004, +0.004]* | +0.000 [-0.000, +0.001] | +0.001 [+0.000, +0.001]* |
| XGBoost | +0.048 [+0.048, +0.049]* | +0.048 [+0.048, +0.048]* | +0.063 [+0.062, +0.063]* | +0.091 [+0.091, +0.092]* | +0.083 [+0.081, +0.085]* | +0.018 [+0.017, +0.021]* |
| RandomForest | +0.165 [+0.164, +0.165]* | +0.023 [+0.022, +0.023]* | +0.098 [+0.097, +0.099]* | +0.093 [+0.092, +0.094]* | +0.144 [+0.142, +0.146]* | -0.016 [-0.018, -0.014]* |
| MLP (std) | -0.000 [-0.000, -0.000]* | -0.000 [-0.000, -0.000]* | +0.000 [-0.000, +0.000] | +0.000 [-0.000, +0.000] | +0.003 [+0.002, +0.004]* | +0.006 [+0.006, +0.007]* |
| KNN (std, k=5) | +0.116 [+0.115, +0.116]* | +0.090 [+0.089, +0.090]* | +0.100 [+0.099, +0.101]* | +0.056 [+0.056, +0.057]* | +0.183 [+0.181, +0.185]* | +0.011 [+0.009, +0.012]* |
| XGBoost, full train (2018) | +0.048 [+0.048, +0.049]* | +0.029 [+0.029, +0.030]* | - | - | - | - |
| RandomForest, full train (2018) | +0.048 [+0.047, +0.048]* | -0.073 [-0.073, -0.072]* | - | - | - | - |

#### Accuracy, all test rows: fixA − dropIAT

| model | d2018 random | d2018 temporal | d2017 random | d2017 temporal | cpacket random | cpacket temporal |
|---|---:|---:|---:|---:|---:|---:|
| GaussianNB | +0.000 [+0.000, +0.000]* | +0.000 [+0.000, +0.000]* | -0.000 [-0.000, -0.000]* | -0.000 [-0.000, -0.000]* | -0.000 [-0.000, +0.000] | -0.000 [-0.000, -0.000]* |
| DecisionTree | +0.000 [-0.000, +0.000] | +0.000 [-0.000, +0.000] | +0.002 [+0.002, +0.003]* | +0.003 [+0.002, +0.003]* | +0.000 [-0.001, +0.001] | +0.001 [+0.000, +0.002]* |
| XGBoost | +0.000 [-0.000, +0.000] | +0.000 [+0.000, +0.000]* | +0.002 [+0.002, +0.002]* | +0.002 [+0.002, +0.002]* | +0.018 [+0.017, +0.019]* | +0.001 [-0.000, +0.001] |
| RandomForest | +0.047 [+0.046, +0.047]* | -0.033 [-0.034, -0.033]* | +0.012 [+0.012, +0.012]* | +0.008 [+0.008, +0.009]* | -0.001 [-0.001, -0.000]* | -0.003 [-0.004, -0.002]* |
| MLP (std) | +0.000 [+0.000, +0.000]* | +0.000 [+0.000, +0.000]* | +0.000 [+0.000, +0.000]* | +0.000 [-0.000, +0.000] | -0.002 [-0.003, -0.001]* | -0.010 [-0.010, -0.009]* |
| KNN (std, k=5) | -0.000 [-0.000, -0.000]* | -0.000 [-0.000, +0.000] | +0.001 [+0.001, +0.001]* | +0.001 [+0.001, +0.001]* | +0.000 [-0.000, +0.000] | -0.000 [-0.001, +0.000] |
| XGBoost, full train (2018) | +0.000 [+0.000, +0.000] | +0.000 [+0.000, +0.000]* | - | - | - | - |
| RandomForest, full train (2018) | -0.004 [-0.004, -0.004]* | +0.004 [+0.004, +0.004]* | - | - | - | - |

**fixA − dropIAT, result.** For DecisionTree, XGBoost, MLP and GaussianNB, fixA and dropIAT agree within 0.02 accuracy and ±0.01 mean attack recall on every dataset and split, and KNN within 0.001 accuracy (mean attack recall +0.03 on 2017, ±0.002 elsewhere): fixA's zeros carry no measurable leak, and fixA is a valid leak-free baseline. One exception: RandomForest on 2018 (+0.047 random, −0.033 temporal). Its sign flips between splits, which a leak through the zeros would not do (a leak would favour fixA on both). Per class, the gap sits in how the RF assigns 1-packet fragment rows that are identical across HOIC, Bot and Benign once the timestamp is gone (RF fixA/dropIAT: HOIC recall 0.50, Bot precision 0.29-0.36, Benign recall 0.82-0.90, where DT and XGBoost keep HOIC at 1.00 and Bot at 0.50): a tie-break among indistinguishable rows, not a leak channel. The same 600k subsample also leaves this RF well below the full-training-set RF of Experiment 3 (fixA random 0.831 here vs 0.953 there), so 2018 RF numbers in this section should be read with that in mind.

#### Mean attack recall, all test rows: leaky − fixA

| model | d2018 random | d2018 temporal | d2017 random | d2017 temporal | cpacket random | cpacket temporal |
|---|---:|---:|---:|---:|---:|---:|
| GaussianNB | -0.013 [-0.044, +0.020] | -0.015 [-0.044, +0.015] | -0.052 [-0.059, -0.045]* | -0.079 [-0.085, -0.073]* | +0.051 [+0.048, +0.054]* | +0.066 [+0.064, +0.067]* |
| DecisionTree | +0.066 [+0.037, +0.092]* | +0.018 [-0.001, +0.039] | +0.112 [+0.105, +0.120]* | -0.163 [-0.171, -0.156]* | +0.256 [+0.246, +0.264]* | +0.023 [+0.017, +0.030]* |
| LogReg (std) | +0.062 [+0.060, +0.063]* | -0.001 [-0.003, +0.000] | +0.001 [-0.001, +0.002] | -0.001 [-0.002, -0.000]* | -0.000 [-0.002, +0.002] | +0.000 [-0.002, +0.002] |
| XGBoost | +0.075 [+0.057, +0.096]* | +0.066 [+0.063, +0.069]* | +0.107 [+0.102, +0.113]* | +0.069 [+0.062, +0.076]* | +0.256 [+0.247, +0.264]* | +0.115 [+0.108, +0.123]* |
| RandomForest | +0.113 [+0.092, +0.138]* | -0.008 [-0.031, +0.019] | +0.113 [+0.109, +0.118]* | -0.084 [-0.091, -0.077]* | +0.251 [+0.243, +0.260]* | +0.070 [+0.064, +0.076]* |
| MLP (std) | +0.005 [-0.000, +0.017] | +0.005 [+0.000, +0.015]* | +0.002 [+0.001, +0.004]* | -0.006 [-0.007, -0.005]* | +0.002 [-0.001, +0.004] | -0.004 [-0.006, -0.003]* |
| KNN (std, k=5) | +0.105 [+0.083, +0.129]* | +0.083 [+0.062, +0.106]* | +0.202 [+0.195, +0.209]* | +0.056 [+0.052, +0.060]* | +0.151 [+0.144, +0.158]* | +0.043 [+0.038, +0.047]* |
| XGBoost, full train (2018) | +0.080 [+0.065, +0.098]* | +0.055 [+0.051, +0.057]* | - | - | - | - |
| RandomForest, full train (2018) | +0.088 [+0.070, +0.110]* | -0.102 [-0.133, -0.072]* | - | - | - | - |

#### Mean attack recall, all test rows: fixA − dropIAT

| model | d2018 random | d2018 temporal | d2017 random | d2017 temporal | cpacket random | cpacket temporal |
|---|---:|---:|---:|---:|---:|---:|
| GaussianNB | +0.000 [+0.000, +0.000] | -0.000 [-0.000, +0.000] | -0.000 [-0.000, +0.000] | +0.000 [+0.000, +0.000]* | +0.000 [+0.000, +0.000] | +0.000 [+0.000, +0.000] |
| DecisionTree | +0.000 [-0.000, +0.000] | -0.010 [-0.024, -0.000]* | +0.001 [-0.004, +0.006] | -0.001 [-0.007, +0.004] | -0.000 [-0.005, +0.005] | +0.008 [+0.003, +0.012]* |
| XGBoost | +0.000 [+0.000, +0.000] | +0.001 [+0.001, +0.001]* | -0.003 [-0.007, +0.002] | -0.002 [-0.007, +0.002] | -0.004 [-0.009, +0.001] | -0.001 [-0.005, +0.003] |
| RandomForest | +0.005 [+0.000, +0.016]* | -0.014 [-0.022, -0.008]* | -0.003 [-0.006, -0.000]* | +0.001 [-0.001, +0.003] | +0.005 [+0.001, +0.009]* | -0.002 [-0.006, +0.002] |
| MLP (std) | +0.005 [+0.000, +0.016]* | -0.005 [-0.015, -0.000]* | -0.003 [-0.004, -0.002]* | +0.001 [+0.000, +0.002]* | -0.003 [-0.005, -0.000]* | +0.006 [+0.005, +0.008]* |
| KNN (std, k=5) | +0.000 [+0.000, +0.000] | +0.001 [+0.000, +0.003] | +0.030 [+0.025, +0.034]* | +0.030 [+0.025, +0.035]* | +0.002 [+0.000, +0.004]* | +0.002 [-0.000, +0.003] |
| XGBoost, full train (2018) | +0.000 [+0.000, +0.000] | +0.000 [+0.000, +0.000]* | - | - | - | - |
| RandomForest, full train (2018) | +0.000 [+0.000, +0.000] | +0.007 [+0.007, +0.007]* | - | - | - | - |

#### Macro F1, all test rows: fixA − dropIAT

| model | d2018 random | d2018 temporal | d2017 random | d2017 temporal | cpacket random | cpacket temporal |
|---|---:|---:|---:|---:|---:|---:|
| GaussianNB | +0.000 [-0.000, +0.000] | +0.000 [-0.000, +0.000] | -0.000 [-0.000, -0.000]* | -0.000 [-0.000, +0.000] | -0.000 [-0.000, +0.000] | -0.000 [-0.000, -0.000]* |
| DecisionTree | -0.002 [-0.007, +0.003] | +0.001 [-0.000, +0.002] | +0.014 [+0.011, +0.016]* | +0.012 [+0.010, +0.014]* | +0.000 [-0.002, +0.003] | +0.002 [+0.000, +0.005]* |
| XGBoost | +0.000 [-0.000, +0.000] | +0.001 [+0.000, +0.001]* | +0.010 [+0.008, +0.012]* | +0.008 [+0.006, +0.010]* | +0.002 [-0.000, +0.004] | +0.002 [-0.000, +0.004] |
| RandomForest | +0.080 [+0.073, +0.087]* | +0.023 [+0.017, +0.030]* | +0.009 [+0.008, +0.010]* | +0.008 [+0.007, +0.009]* | -0.000 [-0.002, +0.001] | -0.002 [-0.004, -0.001]* |
| MLP (std) | +0.009 [-0.001, +0.022] | -0.008 [-0.022, -0.001]* | -0.001 [-0.002, -0.000]* | -0.005 [-0.007, -0.004]* | -0.014 [-0.017, -0.010]* | -0.019 [-0.022, -0.016]* |
| KNN (std, k=5) | -0.001 [-0.005, -0.000]* | -0.000 [-0.003, +0.003] | +0.028 [+0.024, +0.032]* | +0.036 [+0.028, +0.047]* | +0.002 [+0.000, +0.004]* | +0.002 [-0.000, +0.004] |
| XGBoost, full train (2018) | +0.000 [-0.000, +0.000] | +0.000 [+0.000, +0.000]* | - | - | - | - |
| RandomForest, full train (2018) | +0.008 [+0.004, +0.014]* | +0.006 [+0.005, +0.007]* | - | - | - | - |

### 12.2 Validity checks

#### 12.2a IAT units and the 1e9 threshold

Leaked values should all be epoch seconds near capture time; legitimate IATs should sit far below 1e9 (a ms or µs column would put legitimate long gaps near or above 1e9). Random-split training sample.

| dataset | IAT columns / features | leaked cells: min – max | legit nonzero: median / p99.99 / max (s) | legit cells in (1e6, 1e9] |
|---|---|---|---|---:|
| d2018 | 30 / 313 | 1.519e+09 – 1.52e+09 | 0.296 / 1671 / 3.242e+04 | 0 |
| d2017 | 15 / 114 | 1.499e+09 – 1.499e+09 | 0.0133 / 1261 / 2.892e+04 | 0 |
| cpacket | 30 / 313 | 1.703e+09 – 1.703e+09 | 0.112 / 3601 / 2.882e+04 | 0 |

Result: every leaked cell is a single epoch-second band (2017: Jul 2017; 2018: Feb 2018; cPacket: Dec 2023); legitimate IATs top out around 3e4 s and no cell lies between 1e6 and 1e9, so the threshold separates them cleanly.

#### 12.2b Does fixA's zero still carry the leak?

Leaked rows are strongly class-dependent (table 12.2c), so after fixA, 'IAT cell == 0' could act as a leak flag. Test: a balanced decision tree (study DT settings) trained on binary masks only (random split, scored on the full test split). If fixA's zero pattern were a leak channel, it would beat the legitimate zero pattern clearly.

| features (binary) | d2018: macro F1 / mean att. recall | d2017: macro F1 / mean att. recall | cpacket: macro F1 / mean att. recall |
|---|---|---|---|
| majority baseline | 0.078 / 0.000 | 0.060 / 0.000 | 0.023 / 0.000 |
| row leaked flag (1 bit) | 0.035 / 0.250 | 0.029 / 0.182 | 0.020 / 0.105 |
| per-col leaked mask | 0.107 / 0.321 | 0.057 / 0.273 | 0.029 / 0.126 |
| zero mask, raw data (legit zeros only) | 0.333 / 0.597 | 0.117 / 0.349 | 0.108 / 0.143 |
| zero mask, after fixA (legit + leaked) | 0.334 / 0.573 | 0.129 / 0.322 | 0.112 / 0.156 |

Result: fixA's zero mask adds at most ~0.01 macro F1 over legitimate zeros alone (2017 +0.012, cPacket +0.004, 2018 +0.001), and mean attack recall changes by -0.03 to +0.01 (lower on 2017 and 2018). Legitimate exact zeros are common (table 12.2c), so the leak flag is mostly hidden among them. Section 12.1 (fixA − dropIAT) is the full-model check of the same question.

#### 12.2c Leak rate and legitimate zeros by class (random-split training sample)

Rows leaked = share of rows with any leaked IAT cell. Legit zeros = share of IAT cells exactly 0 in non-leaked rows. Because leak rates differ so much by class, the leaked-row subset has a different class mix from the full test set: compare leaked-row results via mean attack recall, not accuracy, and only within a dataset × split (the classes entering the mean can differ between splits; see the n in table 12.3).

d2018:

| class | train rows | rows leaked % | legit zeros % |
|---|---:|---:|---:|
| Benign | 323,943 | 35.6 | 9.2 |
| Bot | 39,437 | 50.1 | 16.9 |
| Brute_Force_Web | 402 | 50.2 | 5.3 |
| Brute_Force_XSS | 174 | 53.4 | 2.9 |
| DDoS_HOIC | 137,940 | 49.8 | 12.5 |
| DDoS_LOIC_HTTP | 39,909 | 0.1 | 9.0 |
| DoS_HULK | 43,566 | 1.1 | 6.2 |
| DoS_SlowHTTP | 14,549 | 100.0 | n/a (no non-leaked rows) |
| SQL_Injection | 80 | 51.2 | 7.8 |

d2017:

| class | train rows | rows leaked % | legit zeros % |
|---|---:|---:|---:|
| Benign | 439,577 | 35.1 | 9.4 |
| Botnet_ARES | 1,355 | 82.4 | 6.2 |
| DDoS_LOIT | 23,559 | 0.1 | 0.9 |
| DoS_GoldenEye | 2,058 | 6.0 | 0.9 |
| DoS_Hulk | 85,945 | 37.7 | 13.4 |
| DoS_Slowhttptest | 1,688 | 27.1 | 19.7 |
| DoS_Slowloris | 1,274 | 20.6 | 13.9 |
| FTP-Patator | 2,345 | 59.7 | 0.4 |
| Heartbleed | 9 | 22.2 | 1.0 |
| Port_Scan | 39,700 | 99.9 | 0.0 |
| SSH-Patator | 1,464 | 51.2 | 0.0 |
| Web_Brute_Force | 673 | 51.9 | 5.6 |
| Web_SQL_Injection | 18 | 44.4 | 4.7 |
| Web_XSS | 334 | 48.2 | 6.3 |

cpacket:

| class | train rows | rows leaked % | legit zeros % |
|---|---:|---:|---:|
| Attack / Attack-Killall-v2 | 4,525 | 24.4 | 22.2 |
| Attack / Attack-Killer-TCP | 4,691 | 28.2 | 22.0 |
| Attack / Attack-TCP-BYPass-V1 | 103,776 | 95.9 | 19.6 |
| Attack / Attack-TCP-Control | 4,308 | 25.3 | 17.5 |
| Attack / Attack-TCP-Flag-ACK | 8,012 | 16.1 | 12.4 |
| Attack / Attack-TCP-Flag-ACK-PSH | 5,611 | 21.9 | 19.5 |
| Attack / Attack-TCP-Flag-MIX | 5,562 | 23.6 | 17.5 |
| Attack / Attack-TCP-Flag-OSYN | 650 | 82.0 | 15.8 |
| Attack / Attack-TCP-Flag-OSYNP | 668 | 83.4 | 12.0 |
| Attack / Attack-TCP-Flag-RST-ACK | 1,084 | 42.1 | 4.7 |
| Attack / Attack-TCP-Flag-SYN | 5,884 | 22.7 | 18.7 |
| Attack / Attack-TCP-Flag-SYN-ACK | 6,153 | 20.0 | 16.4 |
| Attack / Attack-TCP-Flag-SYN-TFO | 2,723 | 22.4 | 2.7 |
| Attack / Attack-TCP-Flag-SYN-TIME | 1,020 | 67.5 | 14.3 |
| Attack / Attack-TCP-IGMP | 5,438 | 22.5 | 19.3 |
| Attack / Attack-TCP-SYN | 5,215 | 20.8 | 19.3 |
| Attack / Attack-TCP-Valid-SYN | 6,032 | 17.6 | 19.3 |
| Benign / Benign | 226,713 | 81.0 | 56.3 |
| Benign / Benign-Email-Receive | 1,046 | 66.8 | 35.5 |
| Benign / Benign-Email-Send | 1,454 | 59.6 | 27.4 |
| Benign / Benign-FTP | 362 | 64.9 | 30.5 |
| Benign / Benign-SSH | 2,239 | 47.6 | 20.4 |
| Benign / Benign-Systemic | 36,055 | 17.1 | 8.2 |
| Benign / Benign-Telnet | 3,576 | 84.0 | 65.5 |
| Benign / Benign-Web_Browsing_HTTP-S | 38,454 | 54.2 | 19.7 |
| Suspicious / Suspicious | 44,329 | 26.3 | 11.7 |

Note: d2018 DoS_SlowHTTP is 100% leaked, so under fixA all its leaked IAT cells are 0 by construction and there is no legitimate zero pattern to compare with.

### 12.3 Per-dataset detail

#### BCCC-CSE-CIC-IDS2018 (9 classes)

Accuracy and mean attack recall on all test rows, mean attack recall on leaked test rows (n = attack classes in that mean), per condition: leaky / +8y / zero / fixA / dropIAT.

| model | split | accuracy (all) | mean att. recall (all) | mean att. recall (leaked rows) | n | machine | fit s (leaky, fixA, dropIAT) | peak GB | warnings |
|---|---|---|---|---|---:|---|---|---:|---:|
| GaussianNB | random | 0.329 / 0.306 / 0.305 / 0.298 / 0.298 | 0.57 / 0.45 / 0.42 / 0.59 / 0.59 | 0.31 / 0.18 / 0.12 / 0.13 / 0.13 | 8 | PC | 3, 2, 2 | 2.05 | 0 |
| GaussianNB | temporal | 0.314 / 0.290 / 0.290 / 0.319 / 0.319 | 0.57 / 0.44 / 0.41 / 0.58 / 0.58 | 0.35 / 0.20 / 0.14 / 0.14 / 0.14 | 7 | PC | 2, 2, 2 | 2.07 | 0 |
| DecisionTree | random | 0.999 / 0.850 / 0.839 / 0.954 / 0.954 | 0.96 / 0.70 / 0.74 / 0.90 / 0.90 | 0.94 / 0.13 / 0.31 / 0.65 / 0.65 | 8 | PC | 61, 64, 48 | 1.98 | 0 |
| DecisionTree | temporal | 0.925 / 0.907 / 0.864 / 0.952 / 0.952 | 0.92 / 0.76 / 0.71 / 0.90 / 0.91 | 0.71 / 0.35 / 0.23 / 0.69 / 0.69 | 7 | PC | 65, 62, 38 | 1.98 | 0 |
| LogReg (std) | random | 0.900 / 0.735 / 0.802 / 0.785 / - | 0.90 / 0.75 / 0.77 / 0.84 / - | 0.65 / 0.46 / 0.29 / 0.53 / - | 8 | PC | 820, 668, - | 2.68 | 2 |
| LogReg (std) | temporal | 0.870 / 0.786 / 0.824 / 0.868 / - | 0.80 / 0.73 / 0.73 / 0.80 / - | 0.49 / 0.31 / 0.30 / 0.49 / - | 7 | PC | 696, 557, - | 2.68 | 2 |
| XGBoost | random | 1.000 / 0.883 / 0.851 / 0.952 / 0.952 | 0.99 / 0.77 / 0.71 / 0.92 / 0.92 | 0.87 / 0.28 / 0.23 / 0.68 / 0.68 | 8 | PC | 274, 294, 244 | 1.98 | 0 |
| XGBoost | temporal | 0.995 / 0.906 / 0.874 / 0.947 / 0.947 | 0.98 / 0.82 / 0.68 / 0.91 / 0.91 | 0.86 / 0.48 / 0.15 / 0.71 / 0.71 | 7 | PC | 278, 291, 233 | 1.98 | 0 |
| RandomForest | random | 0.995 / 0.844 / 0.851 / 0.831 / 0.784 | 1.00 / 0.71 / 0.71 / 0.89 / 0.88 | 0.99 / 0.15 / 0.23 / 0.61 / 0.61 | 8 | PC | 154, 136, 85 | 1.98 | 0 |
| RandomForest | temporal | 0.892 / 0.875 / 0.875 / 0.869 / 0.903 | 0.85 / 0.68 / 0.68 / 0.85 / 0.87 | 0.51 / 0.15 / 0.15 / 0.56 / 0.59 | 7 | PC | 146, 130, 82 | 1.98 | 0 |
| MLP (std) | random | 0.919 / 0.919 / 0.851 / 0.920 / 0.919 | 0.74 / 0.74 / 0.67 / 0.73 / 0.73 | 0.35 / 0.35 / 0.16 / 0.35 / 0.35 | 8 | PC | 95, 181, 88 | 2.68 | 0 |
| MLP (std) | temporal | 0.915 / 0.915 / 0.870 / 0.916 / 0.915 | 0.70 / 0.70 / 0.65 / 0.69 / 0.70 | 0.30 / 0.30 / 0.15 / 0.30 / 0.30 | 7 | PC | 129, 166, 73 | 2.68 | 0 |
| KNN (std, k=5) | random | 1.000 / 0.850 / 0.799 / 0.884 / 0.884 | 0.99 / 0.70 / 0.74 / 0.88 / 0.88 | 0.87 / 0.16 / 0.26 / 0.63 / 0.63 | 8 | PC | 3, 3, 3 | 2.69 | 0 |
| KNN (std, k=5) | temporal | 0.993 / 0.871 / 0.824 / 0.904 / 0.904 | 0.96 / 0.66 / 0.70 / 0.87 / 0.87 | 0.85 / 0.15 / 0.26 / 0.64 / 0.64 | 7 | PC | 3, 3, 3 | 2.69 | 0 |
| XGBoost, full train (2018) | random | 1.000 / 0.879 / 0.851 / 0.952 / 0.952 | 0.99 / 0.76 / 0.71 / 0.92 / 0.92 | 0.87 / 0.26 / 0.23 / 0.68 / 0.68 | 8 | PC | 1555, 1602, 1296 | 6.79 | 0 |
| XGBoost, full train (2018) | temporal | 0.976 / 0.903 / 0.873 / 0.947 / 0.947 | 0.96 / 0.78 / 0.68 / 0.91 / 0.91 | 0.83 / 0.40 / 0.15 / 0.71 / 0.71 | 7 | PC | 1440, 1498, 1280 | 6.80 | 0 |
| RandomForest, full train (2018) | random | 0.998 / 0.851 / 0.851 / 0.950 / 0.954 | 0.99 / 0.71 / 0.71 / 0.90 / 0.90 | 0.96 / 0.15 / 0.18 / 0.65 / 0.65 | 8 | PC | 1349, 1248, 1060 | 6.72 | 0 |
| RandomForest, full train (2018) | temporal | 0.892 / 0.875 / 0.875 / 0.965 / 0.961 | 0.78 / 0.68 / 0.68 / 0.88 / 0.87 | 0.36 / 0.15 / 0.15 / 0.62 / 0.62 | 7 | PC | 1205, 1144, 1000 | 6.75 | 0 |

Exact counts for classes with < 100 test rows (correct/support, all test rows; leaky / +8y / zero / fixA / dropIAT). Anecdotal only: with single-digit supports, one row is a large swing in recall, and these classes support no claims on their own.

- GaussianNB random: Brute_Force_XSS 32/58 / 32/58 / 32/58 / 32/58 / 32/58; SQL_Injection 11/26 / 11/26 / 6/26 / 11/26 / 11/26
- GaussianNB temporal: Brute_Force_XSS 28/58 / 28/58 / 28/58 / 28/58 / 28/58; SQL_Injection 13/26 / 13/26 / 7/26 / 10/26 / 10/26
- DecisionTree random: Brute_Force_XSS 55/58 / 34/58 / 34/58 / 56/58 / 56/58; SQL_Injection 20/26 / 13/26 / 13/26 / 19/26 / 19/26
- DecisionTree temporal: Brute_Force_XSS 53/58 / 24/58 / 24/58 / 56/58 / 56/58; SQL_Injection 24/26 / 15/26 / 18/26 / 21/26 / 23/26
- LogReg (std) random: Brute_Force_XSS 56/58 / 35/58 / 35/58 / 56/58 / -; SQL_Injection 19/26 / 14/26 / 20/26 / 19/26 / -
- LogReg (std) temporal: Brute_Force_XSS 56/58 / 30/58 / 28/58 / 56/58 / -; SQL_Injection 14/26 / 8/26 / 16/26 / 14/26 / -
- XGBoost random: Brute_Force_XSS 56/58 / 35/58 / 35/58 / 56/58 / 56/58; SQL_Injection 25/26 / 14/26 / 14/26 / 23/26 / 23/26
- XGBoost temporal: Brute_Force_XSS 56/58 / 56/58 / 28/58 / 56/58 / 56/58; SQL_Injection 24/26 / 15/26 / 10/26 / 24/26 / 24/26
- RandomForest random: Brute_Force_XSS 57/58 / 35/58 / 35/58 / 56/58 / 56/58; SQL_Injection 26/26 / 15/26 / 15/26 / 20/26 / 19/26
- RandomForest temporal: Brute_Force_XSS 53/58 / 28/58 / 28/58 / 56/58 / 56/58; SQL_Injection 25/26 / 11/26 / 11/26 / 17/26 / 17/26
- MLP (std) random: Brute_Force_XSS 34/58 / 34/58 / 34/58 / 34/58 / 34/58; SQL_Injection 7/26 / 7/26 / 7/26 / 6/26 / 5/26
- MLP (std) temporal: Brute_Force_XSS 28/58 / 28/58 / 28/58 / 28/58 / 28/58; SQL_Injection 5/26 / 5/26 / 5/26 / 4/26 / 5/26
- KNN (std, k=5) random: Brute_Force_XSS 57/58 / 35/58 / 35/58 / 56/58 / 56/58; SQL_Injection 24/26 / 13/26 / 13/26 / 16/26 / 16/26
- KNN (std, k=5) temporal: Brute_Force_XSS 56/58 / 28/58 / 28/58 / 56/58 / 56/58; SQL_Injection 21/26 / 7/26 / 7/26 / 14/26 / 14/26
- XGBoost, full train (2018) random: Brute_Force_XSS 56/58 / 35/58 / 35/58 / 56/58 / 56/58; SQL_Injection 26/26 / 15/26 / 15/26 / 23/26 / 23/26
- XGBoost, full train (2018) temporal: Brute_Force_XSS 56/58 / 42/58 / 28/58 / 56/58 / 56/58; SQL_Injection 24/26 / 15/26 / 10/26 / 24/26 / 24/26
- RandomForest, full train (2018) random: Brute_Force_XSS 56/58 / 35/58 / 35/58 / 56/58 / 56/58; SQL_Injection 24/26 / 15/26 / 15/26 / 19/26 / 19/26
- RandomForest, full train (2018) temporal: Brute_Force_XSS 34/58 / 28/58 / 28/58 / 56/58 / 56/58; SQL_Injection 25/26 / 11/26 / 11/26 / 16/26 / 16/26

#### BCCC-CIC-IDS-2017 (14 classes)

Accuracy and mean attack recall on all test rows, mean attack recall on leaked test rows (n = attack classes in that mean), per condition: leaky / +8y / zero / fixA / dropIAT.

| model | split | accuracy (all) | mean att. recall (all) | mean att. recall (leaked rows) | n | machine | fit s (leaky, fixA, dropIAT) | peak GB | warnings |
|---|---|---|---|---|---:|---|---|---:|---:|
| GaussianNB | random | 0.196 / 0.196 / 0.130 / 0.203 / 0.203 | 0.24 / 0.24 / 0.10 / 0.29 / 0.29 | 0.18 / 0.18 / 0.09 / 0.13 / 0.13 | 11 | PC | 1, 1, 1 | 1.97 | 0 |
| GaussianNB | temporal | 0.242 / 0.242 / 0.177 / 0.186 / 0.187 | 0.23 / 0.23 / 0.10 / 0.31 / 0.31 | 0.18 / 0.18 / 0.09 / 0.14 / 0.14 | 11 | PC | 1, 1, 1 | 1.78 | 0 |
| DecisionTree | random | 0.994 / 0.936 / 0.867 / 0.933 / 0.930 | 0.95 / 0.66 / 0.51 / 0.84 / 0.84 | 0.98 / 0.17 / 0.01 / 0.52 / 0.52 | 11 | PC | 22, 23, 15 | 1.95 | 0 |
| DecisionTree | temporal | 0.932 / 0.874 / 0.866 / 0.889 / 0.887 | 0.57 / 0.52 / 0.44 / 0.74 / 0.74 | 0.29 / 0.18 / 0.02 / 0.45 / 0.45 | 11 | PC | 23, 19, 15 | 1.76 | 0 |
| LogReg (std) | random | 0.826 / 0.772 / 0.799 / 0.823 / - | 0.84 / 0.81 / 0.54 / 0.84 / - | 0.52 / 0.44 / 0.10 / 0.52 / - | 11 | laptop | 365, 308, - | 2.13 | 1 |
| LogReg (std) | temporal | 0.785 / 0.770 / 0.797 / 0.781 / - | 0.74 / 0.74 / 0.48 / 0.75 / - | 0.44 / 0.43 / 0.11 / 0.44 / - | 11 | laptop | 379, 333, - | 1.97 | 0 |
| XGBoost | random | 0.987 / 0.913 / 0.871 / 0.924 / 0.922 | 0.95 / 0.67 / 0.52 / 0.84 / 0.84 | 0.97 / 0.26 / 0.02 / 0.52 / 0.52 | 11 | laptop | 168, 172, 146 | 2.05 | 0 |
| XGBoost | temporal | 0.977 / 0.922 / 0.870 / 0.885 / 0.883 | 0.81 / 0.56 / 0.47 / 0.74 / 0.75 | 0.75 / 0.15 / 0.06 / 0.45 / 0.45 | 11 | laptop | 163, 174, 138 | 1.90 | 0 |
| RandomForest | random | 0.987 / 0.932 / 0.867 / 0.889 / 0.878 | 0.95 / 0.67 / 0.52 / 0.84 / 0.84 | 0.98 / 0.17 / 0.02 / 0.51 / 0.51 | 11 | PC | 63, 59, 43 | 1.95 | 0 |
| RandomForest | temporal | 0.938 / 0.929 / 0.865 / 0.846 / 0.837 | 0.66 / 0.53 / 0.45 / 0.74 / 0.74 | 0.39 / 0.09 / 0.02 / 0.44 / 0.44 | 11 | PC | 65, 59, 43 | 1.82 | 0 |
| MLP (std) | random | 0.947 / 0.947 / 0.872 / 0.947 / 0.947 | 0.66 / 0.66 / 0.46 / 0.66 / 0.66 | 0.29 / 0.29 / 0.00 / 0.28 / 0.29 | 11 | laptop | 122, 102, 84 | 2.15 | 0 |
| MLP (std) | temporal | 0.945 / 0.945 / 0.868 / 0.945 / 0.945 | 0.62 / 0.62 / 0.40 / 0.62 / 0.62 | 0.32 / 0.32 / 0.02 / 0.32 / 0.32 | 11 | laptop | 209, 84, 83 | 2.00 | 0 |
| KNN (std, k=5) | random | 0.995 / 0.940 / 0.871 / 0.895 / 0.895 | 0.90 / 0.67 / 0.50 / 0.70 / 0.67 | 0.91 / 0.20 / 0.01 / 0.37 / 0.37 | 11 | laptop | 1, 1, 1 | 2.12 | 0 |
| KNN (std, k=5) | temporal | 0.951 / 0.903 / 0.869 / 0.895 / 0.894 | 0.71 / 0.63 / 0.45 / 0.65 / 0.62 | 0.48 / 0.30 / 0.02 / 0.39 / 0.39 | 11 | laptop | 1, 1, 1 | 1.74 | 0 |

Exact counts for classes with < 100 test rows (correct/support, all test rows; leaky / +8y / zero / fixA / dropIAT). Anecdotal only: with single-digit supports, one row is a large swing in recall, and these classes support no claims on their own.

- GaussianNB random: Heartbleed 2/3 / 2/3 / 0/3 / 0/3 / 0/3; Web_SQL_Injection 0/6 / 0/6 / 0/6 / 2/6 / 2/6
- GaussianNB temporal: Heartbleed 1/3 / 1/3 / 0/3 / 0/3 / 0/3; Web_SQL_Injection 0/6 / 0/6 / 0/6 / 3/6 / 3/6
- DecisionTree random: Heartbleed 2/3 / 0/3 / 0/3 / 0/3 / 0/3; Web_SQL_Injection 3/6 / 0/6 / 0/6 / 2/6 / 2/6
- DecisionTree temporal: Heartbleed 1/3 / 0/3 / 0/3 / 2/3 / 2/3; Web_SQL_Injection 3/6 / 2/6 / 2/6 / 5/6 / 5/6
- LogReg (std) random: Heartbleed 0/3 / 2/3 / 0/3 / 0/3 / -; Web_SQL_Injection 3/6 / 3/6 / 5/6 / 3/6 / -
- LogReg (std) temporal: Heartbleed 2/3 / 2/3 / 1/3 / 2/3 / -; Web_SQL_Injection 3/6 / 3/6 / 5/6 / 3/6 / -
- XGBoost random: Heartbleed 2/3 / 0/3 / 0/3 / 0/3 / 0/3; Web_SQL_Injection 3/6 / 0/6 / 0/6 / 2/6 / 2/6
- XGBoost temporal: Heartbleed 2/3 / 1/3 / 1/3 / 2/3 / 2/3; Web_SQL_Injection 6/6 / 3/6 / 3/6 / 5/6 / 5/6
- RandomForest random: Heartbleed 2/3 / 0/3 / 0/3 / 0/3 / 0/3; Web_SQL_Injection 5/6 / 2/6 / 2/6 / 4/6 / 4/6
- RandomForest temporal: Heartbleed 2/3 / 1/3 / 1/3 / 2/3 / 2/3; Web_SQL_Injection 6/6 / 3/6 / 3/6 / 5/6 / 5/6
- MLP (std) random: Heartbleed 0/3 / 0/3 / 0/3 / 0/3 / 0/3; Web_SQL_Injection 0/6 / 0/6 / 0/6 / 0/6 / 0/6
- MLP (std) temporal: Heartbleed 1/3 / 1/3 / 1/3 / 1/3 / 1/3; Web_SQL_Injection 0/6 / 0/6 / 0/6 / 0/6 / 0/6
- KNN (std, k=5) random: Heartbleed 0/3 / 0/3 / 0/3 / 0/3 / 0/3; Web_SQL_Injection 3/6 / 1/6 / 1/6 / 1/6 / 1/6
- KNN (std, k=5) temporal: Heartbleed 1/3 / 1/3 / 1/3 / 1/3 / 1/3; Web_SQL_Injection 5/6 / 3/6 / 3/6 / 3/6 / 3/6

#### BCCC-cPacket-Cloud-DDoS-2024 (26 subtypes)

Accuracy and mean attack recall on all test rows, mean attack recall on leaked test rows (n = attack classes in that mean), per condition: leaky / +8y / zero / fixA / dropIAT.

| model | split | accuracy (all) | mean att. recall (all) | mean att. recall (leaked rows) | n | machine | fit s (leaky, fixA, dropIAT) | peak GB | warnings |
|---|---|---|---|---|---:|---|---|---:|---:|
| GaussianNB | random | 0.207 / 0.207 / 0.019 / 0.016 / 0.016 | 0.11 / 0.11 / 0.06 / 0.06 / 0.06 | 0.06 / 0.06 / 0.05 / 0.00 / 0.00 | 17 | PC | 2, 2, 2 | 2.53 | 0 |
| GaussianNB | temporal | 0.207 / 0.207 / 0.018 / 0.017 / 0.017 | 0.10 / 0.10 / 0.06 / 0.04 / 0.04 | 0.06 / 0.06 / 0.05 / 0.00 / 0.00 | 17 | PC | 2, 2, 2 | 2.39 | 0 |
| DecisionTree | random | 0.748 / 0.339 / 0.494 / 0.658 / 0.658 | 0.56 / 0.21 / 0.21 / 0.30 / 0.30 | 0.93 / 0.00 / 0.00 / 0.13 / 0.13 | 17 | PC | 56, 44, 24 | 2.53 | 0 |
| DecisionTree | temporal | 0.539 / 0.298 / 0.450 / 0.596 / 0.595 | 0.29 / 0.19 / 0.19 / 0.27 / 0.26 | 0.23 / 0.00 / 0.00 / 0.12 / 0.12 | 17 | PC | 53, 44, 25 | 2.39 | 0 |
| LogReg (std) | random | 0.583 / 0.532 / 0.410 / 0.583 / - | 0.26 / 0.26 / 0.25 / 0.26 / - | 0.11 / 0.13 / 0.12 / 0.11 / - | 17 | laptop | 560, 561, - | 3.09 | 2 |
| LogReg (std) | temporal | 0.556 / 0.481 / 0.399 / 0.556 / - | 0.22 / 0.21 / 0.21 / 0.22 / - | 0.11 / 0.09 / 0.10 / 0.11 / - | 17 | laptop | 564, 558, - | 3.01 | 2 |
| XGBoost | random | 0.760 / 0.393 / 0.562 / 0.677 / 0.659 | 0.59 / 0.24 / 0.24 / 0.33 / 0.33 | 0.91 / 0.00 / 0.00 / 0.14 / 0.14 | 17 | laptop | 757, 759, 630 | 2.78 | 0 |
| XGBoost | temporal | 0.634 / 0.355 / 0.506 / 0.615 / 0.615 | 0.39 / 0.19 / 0.19 / 0.27 / 0.27 | 0.54 / 0.00 / 0.00 / 0.12 / 0.12 | 17 | laptop | 782, 764, 647 | 2.71 | 0 |
| RandomForest | random | 0.759 / 0.314 / 0.444 / 0.615 / 0.616 | 0.60 / 0.24 / 0.24 / 0.35 / 0.34 | 0.94 / 0.00 / 0.00 / 0.14 / 0.14 | 17 | PC | 144, 130, 98 | 2.53 | 0 |
| RandomForest | temporal | 0.591 / 0.288 / 0.409 / 0.607 / 0.610 | 0.35 / 0.19 / 0.19 / 0.28 / 0.28 | 0.46 / 0.00 / 0.00 / 0.12 / 0.12 | 17 | PC | 149, 130, 97 | 2.39 | 0 |
| MLP (std) | random | 0.823 / 0.822 / 0.758 / 0.820 / 0.822 | 0.17 / 0.17 / 0.17 / 0.17 / 0.17 | 0.06 / 0.06 / 0.06 / 0.06 / 0.06 | 17 | laptop | 234, 87, 126 | 3.08 | 0 |
| MLP (std) | temporal | 0.809 / 0.806 / 0.772 / 0.802 / 0.812 | 0.15 / 0.15 / 0.15 / 0.15 / 0.15 | 0.06 / 0.06 / 0.06 / 0.06 / 0.06 | 17 | laptop | 188, 99, 221 | 3.01 | 0 |
| KNN (std, k=5) | random | 0.841 / 0.453 / 0.736 / 0.658 / 0.658 | 0.39 / 0.17 / 0.22 / 0.24 / 0.23 | 0.60 / 0.01 / 0.07 / 0.12 / 0.12 | 17 | laptop | 2, 2, 2 | 2.47 | 0 |
| KNN (std, k=5) | temporal | 0.654 / 0.399 / 0.727 / 0.643 / 0.644 | 0.23 / 0.12 / 0.18 / 0.19 / 0.19 | 0.26 / 0.00 / 0.06 / 0.10 / 0.10 | 17 | laptop | 2, 2, 2 | 2.40 | 0 |

### 12.4 Model configuration caveats

| model | configuration | class weighting | notes |
|---|---|---|---|
| GaussianNB | defaults | none | Near or below chance on cPacket (fixA 0.02 accuracy, 26 classes). `var_smoothing` scales with the largest feature variance, and the features have extreme magnitudes. Treat as a broken baseline, not as evidence about the leak. |
| DecisionTree | max_depth 30, min_samples_leaf 10 | balanced (`class_weight`) | |
| LogReg | StandardScaler + lbfgs, max_iter 1000 | balanced (`class_weight`) | Stopped at the iteration limit in most runs (list below): its results reflect where the optimiser stopped, so leak effects for LogReg are indicative only. No dropIAT run. |
| XGBoost | 200 trees, depth 8, lr 0.1, hist | balanced (`sample_weight` at fit; not visible in the saved params) | |
| RandomForest | 200 trees, depth 30, min_samples_leaf 10 | balanced (`class_weight`) | |
| MLP | StandardScaler, (128, 64), max_iter 50, early stopping | none | Stopped after 14–47 epochs; mostly predicts the large classes (very low attack recall on cPacket). Its flat leaky ≈ fixA ≈ +8y numbers more likely reflect under-training than robustness; the zero condition still hurts it, so it does use the IAT features. Do not read it as 'MLPs are immune'. |
| KNN | StandardScaler, k = 5, distance-weighted (as the shipped knn_model.onnx) | none | Added later (overnight run); scored on the full test sets like every other model. +8y / zero predictions are computed for leaked rows only and copied from leaky for the rest (identical by construction; verified on 3,000 rows). |

Iterations / epochs (LogReg hit the 1,000 limit in 9 of 12 runs):

- cpacket random lr fixA: 1000 (limit hit)
- cpacket random lr leaky: 1000 (limit hit)
- cpacket random mlp dropIAT: 27
- cpacket random mlp fixA: 20
- cpacket random mlp leaky: 47
- cpacket temporal lr fixA: 1000 (limit hit)
- cpacket temporal lr leaky: 1000 (limit hit)
- cpacket temporal mlp dropIAT: 48
- cpacket temporal mlp fixA: 21
- cpacket temporal mlp leaky: 44
- d2017 random lr fixA: 834
- d2017 random lr leaky: 1000 (limit hit)
- d2017 random mlp dropIAT: 21
- d2017 random mlp fixA: 25
- d2017 random mlp leaky: 26
- d2017 temporal lr fixA: 858
- d2017 temporal lr leaky: 947
- d2017 temporal mlp dropIAT: 20
- d2017 temporal mlp fixA: 21
- d2017 temporal mlp leaky: 39
- d2018 random lr fixA: 1000 (limit hit)
- d2018 random lr leaky: 1000 (limit hit)
- d2018 random mlp dropIAT: 14
- d2018 random mlp fixA: 26
- d2018 random mlp leaky: 14
- d2018 temporal lr fixA: 1000 (limit hit)
- d2018 temporal lr leaky: 1000 (limit hit)
- d2018 temporal mlp dropIAT: 12
- d2018 temporal mlp fixA: 26
- d2018 temporal mlp leaky: 19

Other caveats:
- Fit time and peak memory come from two machines (PC: 8 threads; laptop: i7-8750H, 12 threads); the `machine` column in table 12.3 says which. Compare timings only between runs on the same machine.
- Feature counts differ: 313 features (30 IAT) on 2018 and cPacket, 114 (15 IAT) on 2017. Leak sensitivity across datasets is therefore not a like-for-like comparison of feature sets.
- Cross-machine reproducibility (checked 2026-10-02): a laptop XGBoost run recomputed on the PC gives identical predictions; a laptop MLP run gives 791 of 609,513 different predictions (accuracy 0.9468 vs 0.9469), i.e. floating-point differences between the two CPUs' maths libraries in MLP training, far below any effect reported here.
- Laptop disk incident: on 2026-10-02 evening, 60 scikit-learn files in the laptop's Python environment were found corrupted on disk (identical garbage blocks; noticed because KNN failed to import). They were restored from the PC (checksums identical after repair); the laptop's data caches, splits and subsamples were checksum-identical to the PC's, and import failures are loud, so earlier laptop results are unaffected (see the XGBoost check above).
- Single training seed (0). The CIs cover test-set sampling only.
- Leaked-row accuracy is not comparable to all-row accuracy (different class mix; see 2c); use mean attack recall.

### 12.5 Warnings recorded (not suppressed), by run

- ConvergenceWarning: lbfgs failed to converge after 1000 iteration(s) (status=1): STOP: TOTAL NO. OF ITERATIONS REACHED LIMIT Increase the number of iterations to improve the convergence (max_iter=1000). You might also want to scale the data as shown in: https://scikit-learn.org/stable/modules/preprocessing.html Please also refer to the documentation for alternative solver options: https://scikit-learn.org/stable/modules/linear_model.html#logistic-regression
  Runs (9): cpacket_random_lr_fixA, cpacket_random_lr_leaky, cpacket_temporal_lr_fixA, cpacket_temporal_lr_leaky, d2017_random_lr_leaky, d2018_random_lr_fixA, d2018_random_lr_leaky, d2018_temporal_lr_fixA, d2018_temporal_lr_leaky


## Section 12 training subsamples (class counts)

- cpacket random: 525,580 training rows of 525,580 (Attack / Attack-Killall-v2 4,525, Attack / Attack-Killer-TCP 4,691, Attack / Attack-TCP-BYPass-V1 103,776, Attack / Attack-TCP-Control 4,308, Attack / Attack-TCP-Flag-ACK 8,012, Attack / Attack-TCP-Flag-ACK-PSH 5,611, Attack / Attack-TCP-Flag-MIX 5,562, Attack / Attack-TCP-Flag-OSYN 650, Attack / Attack-TCP-Flag-OSYNP 668, Attack / Attack-TCP-Flag-RST-ACK 1,084, Attack / Attack-TCP-Flag-SYN 5,884, Attack / Attack-TCP-Flag-SYN-ACK 6,153, Attack / Attack-TCP-Flag-SYN-TFO 2,723, Attack / Attack-TCP-Flag-SYN-TIME 1,020, Attack / Attack-TCP-IGMP 5,438, Attack / Attack-TCP-SYN 5,215, Attack / Attack-TCP-Valid-SYN 6,032, Benign / Benign 226,713, Benign / Benign-Email-Receive 1,046, Benign / Benign-Email-Send 1,454, Benign / Benign-FTP 362, Benign / Benign-SSH 2,239, Benign / Benign-Systemic 36,055, Benign / Benign-Telnet 3,576, Benign / Benign-Web_Browsing_HTTP-S 38,454, Suspicious / Suspicious 44,329)
- cpacket temporal: 525,583 training rows of 525,583 (Attack / Attack-Killall-v2 4,525, Attack / Attack-Killer-TCP 4,690, Attack / Attack-TCP-BYPass-V1 103,776, Attack / Attack-TCP-Control 4,308, Attack / Attack-TCP-Flag-ACK 8,012, Attack / Attack-TCP-Flag-ACK-PSH 5,612, Attack / Attack-TCP-Flag-MIX 5,562, Attack / Attack-TCP-Flag-OSYN 650, Attack / Attack-TCP-Flag-OSYNP 668, Attack / Attack-TCP-Flag-RST-ACK 1,084, Attack / Attack-TCP-Flag-SYN 5,884, Attack / Attack-TCP-Flag-SYN-ACK 6,153, Attack / Attack-TCP-Flag-SYN-TFO 2,723, Attack / Attack-TCP-Flag-SYN-TIME 1,020, Attack / Attack-TCP-IGMP 5,438, Attack / Attack-TCP-SYN 5,215, Attack / Attack-TCP-Valid-SYN 6,032, Benign / Benign 226,713, Benign / Benign-Email-Receive 1,047, Benign / Benign-Email-Send 1,453, Benign / Benign-FTP 363, Benign / Benign-SSH 2,240, Benign / Benign-Systemic 36,055, Benign / Benign-Telnet 3,576, Benign / Benign-Web_Browsing_HTTP-S 38,454, Suspicious / Suspicious 44,330)
- d2017 random: 599,999 training rows of 1,828,539 (Benign 439,577, Botnet_ARES 1,355, DDoS_LOIT 23,559, DoS_GoldenEye 2,058, DoS_Hulk 85,945, DoS_Slowhttptest 1,688, DoS_Slowloris 1,274, FTP-Patator 2,345, Heartbleed 9, Port_Scan 39,700, SSH-Patator 1,464, Web_Brute_Force 673, Web_SQL_Injection 18, Web_XSS 334)
- d2017 temporal: 599,999 training rows of 1,828,539 (Benign 439,577, Botnet_ARES 1,355, DDoS_LOIT 23,559, DoS_GoldenEye 2,058, DoS_Hulk 85,945, DoS_Slowhttptest 1,688, DoS_Slowloris 1,274, FTP-Patator 2,345, Heartbleed 9, Port_Scan 39,700, SSH-Patator 1,464, Web_Brute_Force 673, Web_SQL_Injection 18, Web_XSS 334)
- d2018 random: 600,000 training rows of 3,261,673 (Benign 323,943, Bot 39,437, Brute_Force_Web 402, Brute_Force_XSS 174, DDoS_HOIC 137,940, DDoS_LOIC_HTTP 39,909, DoS_HULK 43,566, DoS_SlowHTTP 14,549, SQL_Injection 80)
- d2018 temporal: 600,000 training rows of 3,261,675 (Benign 323,943, Bot 39,437, Brute_Force_Web 402, Brute_Force_XSS 174, DDoS_HOIC 137,940, DDoS_LOIC_HTTP 39,909, DoS_HULK 43,566, DoS_SlowHTTP 14,549, SQL_Injection 80)


---

# D. Source write-ups, verbatim

These overlap with Parts B and C in places; they are kept whole because they carry detail the main report summarises (full per-class census tables, capture calendars, flow shapes, per-seed runs).


### D1. Step 1: minimal reproducer

Source: `~/Desktop/ntl_repro_step1/RESULTS.md`

### NTLFlowLyzer Step 1: minimal reproducer

Upstream `ahlashkari/NTLFlowLyzer` @ `d99cd5377faaed53b39450ce262652902501188d`, unmodified. Python 3.12.3, Linux.
pcap sha256: `61ea9c3ed384b17f1048a8546496660105882ed598079ca683a71bc4df8a3e87` (21 packets, 5 TCP conversations, T0 = 1519308000)

Reproduce: `python make_pcap.py && ntlflowlyzer -c repro_config.json`

| Flow | Port | pkts (fwd/bwd) | Epoch-valued IAT columns | Value | = packet timestamp? |
|---|---|---|---|---|---|
| A lone SYN | 40001 | 1 (1/0) | `packets_IAT_*`, `fwd_packets_IAT_*` | 1519308000.0 | yes (T0) |
| B SYN/SYN-ACK/RST | 40002 | 3 (1/2) | `fwd_packets_IAT_*` only | 1519308010.0 | yes (T0+10) |
| C main | 40003 | 7 (4/3) | none | 0.01-0.04 | n/a |
| C ghost (trailing ACK) | 40003 | 1 (1/0) | `packets_IAT_*`, `fwd_packets_IAT_*` | 1519308020.08 | yes (T0+20.08) |
| D control | 40004 | 8 (4/4) | none | 0.01-0.02 | n/a |
| E lone SYN +1 yr | 40005 | 1 (1/0) | `packets_IAT_*`, `fwd_packets_IAT_*` | 1550844000.0 | yes (T0+31536000; E-A exactly 1 year) |

Affected columns per direction: mean, max, min, total, median, mode (std/variance/cov = 0, skewness = NaN).
A direction with 0 packets gets IAT = 0, not epoch, so the leak is specifically "exactly one packet in that direction".

#### Findings
1. **IAT leak.** Any direction (or whole flow) with exactly one packet gets its absolute epoch timestamp as IAT.
   Root cause `NTLFlowLyzer/features/utils.py:20-27` (`calculate_IAT`): when `len(times) == 1` the list of raw timestamps is returned unchanged.
2. **Ghost flow.** Flow C is split in two (5 conversations -> 6 flows). The flow is closed as soon as both directions have sent FIN
   (`network_flow_capturer/network_flow_capturer.py:305-311`, `has_two_FIN_flags`), so the final ACK of the close starts a new 1-packet flow, which then also shows the leak.
3. **No dropped flows.** Both lone SYNs (A, E) appear in the output.
4. **Local-time rendering.** `timestamp` and the time in `flow_id` show 15:00 for 14:00 UTC (machine TZ Europe/Zagreb, CET in Feb). IAT values are true epoch seconds, unaffected.
5. Control flow D is fully clean.

#### Fork comparison
Fork `Nmakitan/NTLFlowLyzer` @ `31c677cfb5982999410d728260995807102c4533` (upstream d99cd53 + 2 commits touching only
`network_flow_capturer.py` for continuous-batch polling), installed in a separate venv (`venv_fork`), run on the same pcap
(`repro_config_fork.json` -> `repro_out_fork.csv`, `run_fork.log`).
Result: same 6 flows, 347 columns, **byte-identical output to upstream** (`cmp` reports no difference).
The fork neither causes nor changes the IAT leak or the ghost flow.


### D2. Census: BCCC-CSE-CIC-IDS2018

Source: `~/Desktop/ntl_census_step2/RESULTS.md`

### Step 2: leak census of BCCC-CSE-CIC-IDS2018 (original per-day files)

Data: 34 original per-day files, 10 capture days, 48,182,782 rows, one 323-column header (list with sizes: `file_list.txt`).
Inner files dated 2023-07..2023-11, archive entries 2024-02-23, downloaded 2026-09-04. Wed 28-02 has no attack file in the
published zip. 14-02, 15-02 and 01-03 were read straight from their inner zips (Deflate64, streamed via `unzip -p`).
Scripts: `common.py`, `census.py` (one chunked pass), `report.py`. Full tables in `out/`. 0 files failed, no fallback needed.
Leak = IAT value > 1e9.

#### Per class

| Class | n | 1-pkt | fwd leak | bwd leak | **any leak** | **any %** | leak beyond ghosts | beyond % of leaked |
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
| **All** | 48,182,782 | 14,989,979 | 10,386,354 | 8,299,720 | 17,108,403 | 35.51 | 2,118,424 | 12.4 |

#### Rule check
fwd leak <=> fwd_packets_count == 1, bwd leak <=> bwd_packets_count == 1, combined leak <=> packets_count == 1:
**0 violations in 48,182,782 rows** for all three. The dataset was built with the same `calculate_IAT` behaviour reproduced in Step 1.

#### Leaked values = flow start time
Leaked fwd value minus the `timestamp` column is exactly +18000 s in 96-100% of rows per file (100% in most attack files);
the rest are within ~5 s (+18001, +18000.001, +18004.97). So the `timestamp` column (and the time in `flow_id`) is
local UTC-5, and the leaked IAT is the flow's true UTC start epoch.

#### Calendar (`out/leak_date_ranges.csv`, hourly: `out/leak_hours.csv`)
Every attack file's leaked values fall on its own capture day, inside a narrow window, e.g. FTP 14-02 14:33-16:10 UTC,
SSH 14-02 18:01-19:32, GoldenEye 15-02 13:27-14:11, HULK 16-02 17:45-17:58, HOIC 21-02 18:11-19:05,
SQLi 22-02 20:14-20:27 and 23-02 19:05-19:17, Bot 02-03 14:13-19:54, Infiltration 01-03 19:37.
Benign spans each day ~12:20 UTC to ~00:40 the next day. The day is identifiable from the leaked value alone,
and within a day attack and benign windows overlap only partly.
Anomaly: some benign files contain leaked values from other days (fri_23_02 benign: 3,250 rows from 21-22 Feb;
fri_02_03 benign: 6,849 rows incl. 27-28 Feb; wed_28_02 and fri_02_03 benign share the identical minimum value
2018-02-27 12:18:27.392139, wed_28_02 and thu_01_03 the identical maximum). Possibly duplicated rows across day files; not yet checked.

#### Full-column scan (values in 1.4e9..2.2e9)
Only the 18 IAT mean/max/min/total/median/mode columns hit systematically (std/var/cov/skew never do).
Non-IAT hits: avg_bwd_bulk_rate 360,968, avg_fwd_bulk_rate 405, bytes_rate 336, fwd_bytes_rate 279, bwd_bytes_rate 95,
variance_*_delta_len 71. Hand check: values spread uniformly over the range, none within a day of the flow start, so
**not a second timestamp leak**. The bulk-rate values are implausible, though (1.6e9 B/s bulk rate on flows with
bytes_rate ~42 B/s): a separate artifact. The variance hits (Bot) are genuine (~486 KB payloads).
Non-numeric placeholder columns: `delta_start` (small signed seconds, e.g. -0.0004, -4.3) and `handshake_duration`
(e.g. 0.0002): durations, not timestamps.


### D3. Census: BCCC-CIC-IDS-2017

Source: `~/Desktop/ntl_census_multi/BCCC-CIC-IDS-2017/RESULTS.md`

### Leak census: BCCC-CIC-IDS-2017

NTLFlowLyzer output: **yes**. 18 non-empty CSV files, 122 columns, 2,438,052 rows (file list with sizes: `file_list.txt`). Class key: `label`.
IAT columns (15): combined ['packets_IAT_mean', 'packet_IAT_std', 'packet_IAT_max', 'packet_IAT_min', 'packet_IAT_total']; fwd ['fwd_packets_IAT_mean', 'fwd_packets_IAT_std', 'fwd_packets_IAT_max', 'fwd_packets_IAT_min', 'fwd_packets_IAT_total']; bwd ['bwd_packets_IAT_mean', 'bwd_packets_IAT_std', 'bwd_packets_IAT_max', 'bwd_packets_IAT_min', 'bwd_packets_IAT_total'].
Counts: `packets_count`, `fwd_packets_count`, `bwd_packets_count`. Leak = IAT value > 1e9.

#### Per class

| class | n | 1-packet | fwd leak | bwd leak | any leak | % | leak, >1 packet | % of leaked |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| Benign | 1,786,239 | 400,644 | 471,883 | 354,666 | 627,343 | 35.12 | 226,699 | 36.1 |
| Botnet_ARES | 5,508 | 705 | 4,611 | 3,908 | 4,613 | 83.75 | 3,908 | 84.7 |
| DDoS_LOIT | 95,733 | 49 | 50 | 0 | 50 | 0.05 | 1 | 2.0 |
| DoS_GoldenEye | 8,364 | 521 | 259 | 265 | 523 | 6.25 | 2 | 0.4 |
| DoS_Hulk | 349,240 | 127,983 | 111,228 | 24,994 | 132,146 | 37.84 | 4,163 | 3.2 |
| DoS_Slowhttptest | 6,860 | 1,782 | 1,455 | 527 | 1,981 | 28.88 | 199 | 10.0 |
| DoS_Slowloris | 5,177 | 1,016 | 762 | 256 | 1,017 | 19.64 | 1 | 0.1 |
| FTP-Patator | 9,531 | 3,084 | 3,944 | 4,021 | 5,527 | 57.99 | 2,443 | 44.2 |
| Heartbleed | 12 | 4 | 4 | 0 | 4 | 33.33 | 0 | 0.0 |
| Port_Scan | 161,323 | 2,178 | 159,322 | 159,757 | 161,109 | 99.87 | 158,931 | 98.6 |
| SSH-Patator | 5,949 | 2,937 | 36 | 2,934 | 2,955 | 49.67 | 18 | 0.6 |
| Web_Brute_Force | 2,734 | 1,366 | 1,222 | 144 | 1,366 | 49.96 | 0 | 0.0 |
| Web_SQL_Injection | 24 | 11 | 3 | 8 | 11 | 45.83 | 0 | 0.0 |
| Web_XSS | 1,358 | 679 | 656 | 23 | 679 | 50.00 | 0 | 0.0 |
| **ALL** | 2,438,052 | 542,959 | 755,435 | 551,503 | **939,324** | **38.53** | 396,365 | 42.2 |

#### Rule check

fwd leak <=> fwd_packets_count == 1: 0 violations; bwd leak <=> bwd_packets_count == 1: 0; combined leak <=> packets_count == 1: 0 (of 2,438,052 rows).

#### Leaked value vs `timestamp` column

Most common offset (leaked fwd value − timestamp): **14400.0 s** = +4 h, in 98.49% of 755,435 leaked-fwd rows; top 5: 14400.0: 744,052, 14400.001: 1,532, 14401.0: 1,115, 14400.002: 756, 14400.003: 602.
So the `timestamp` column is local time (UTC-4) and the leaked IAT is the UTC epoch of the flow start.

#### Calendar (local time = UTC-4) vs documented capture days

Leaked rows on their file's documented capture day: **939,324 of 939,324 (100.00%)**.

| file | class | documented day | leaked rows | on that day | first (local) | last (local) | local days |
|---|---|---|---:|---:|---|---|---|
| monday_benign | Benign | 2017-07-03 | 176,234 | 176234 | 2017-07-03 07:56 | 2017-07-03 16:01 | 2017-07-03:176234 |
| tuesday_benign | Benign | 2017-07-04 | 137,504 | 137504 | 2017-07-04 07:54 | 2017-07-04 16:00 | 2017-07-04:137504 |
| ftp_patator | FTP-Patator | 2017-07-04 | 5,527 | 5527 | 2017-07-04 08:19 | 2017-07-04 09:20 | 2017-07-04:5527 |
| ssh_patator-new | SSH-Patator | 2017-07-04 | 2,955 | 2955 | 2017-07-04 13:09 | 2017-07-04 14:11 | 2017-07-04:2955 |
| wednesday_benign | Benign | 2017-07-05 | 138,719 | 138719 | 2017-07-05 07:42 | 2017-07-05 16:08 | 2017-07-05:138719 |
| dos_slowloris | DoS_Slowloris | 2017-07-05 | 1,017 | 1017 | 2017-07-05 08:48 | 2017-07-05 09:13 | 2017-07-05:1017 |
| dos_slowhttptest | DoS_Slowhttptest | 2017-07-05 | 1,981 | 1981 | 2017-07-05 09:14 | 2017-07-05 09:42 | 2017-07-05:1981 |
| dos_hulk | DoS_Hulk | 2017-07-05 | 132,146 | 132146 | 2017-07-05 09:43 | 2017-07-05 10:06 | 2017-07-05:132146 |
| dos_golden_eye | DoS_GoldenEye | 2017-07-05 | 523 | 523 | 2017-07-05 10:10 | 2017-07-05 10:29 | 2017-07-05:523 |
| heartbleed | Heartbleed | 2017-07-05 | 4 | 4 | 2017-07-05 13:53 | 2017-07-05 14:10 | 2017-07-05:4 |
| thursday_benign | Benign | 2017-07-06 | 45,672 | 45672 | 2017-07-06 07:59 | 2017-07-06 10:59 | 2017-07-06:45672 |
| web_brute_force | Web_Brute_Force | 2017-07-06 | 1,366 | 1366 | 2017-07-06 08:16 | 2017-07-06 09:00 | 2017-07-06:1366 |
| web_xss | Web_XSS | 2017-07-06 | 679 | 679 | 2017-07-06 09:15 | 2017-07-06 09:35 | 2017-07-06:679 |
| web_sql_injection | Web_SQL_Injection | 2017-07-06 | 11 | 11 | 2017-07-06 09:40 | 2017-07-06 09:42 | 2017-07-06:11 |
| friday_benign | Benign | 2017-07-07 | 129,214 | 129214 | 2017-07-07 08:00 | 2017-07-07 16:02 | 2017-07-07:129214 |
| botnet_ares | Botnet_ARES | 2017-07-07 | 4,613 | 4613 | 2017-07-07 09:04 | 2017-07-07 15:16 | 2017-07-07:4613 |
| portscan | Port_Scan | 2017-07-07 | 161,109 | 161109 | 2017-07-07 12:55 | 2017-07-07 14:24 | 2017-07-07:161109 |
| ddos_loit | DDoS_LOIT | 2017-07-07 | 50 | 50 | 2017-07-07 15:00 | 2017-07-07 15:16 | 2017-07-07:50 |

#### Non-IAT columns with values in 1.4e9..2.2e9

- `bytes_rate`: 32
- `fwd_bytes_rate`: 24
- `bwd_bytes_rate`: 7
- `total_payload_bytes`: 1
- `bwd_total_payload_bytes`: 1
- `bwd_bulk_total_size`: 1

Non-numeric columns (samples): `timestamp`: ['2017-07-07 09:04:13.990571', '2017-07-07 09:04:24.131090', '2017-07-07 09:04:34.262355']; `protocol`: ['TCP']; `label`: ['Botnet_ARES']

#### Flow shapes per class (fwd/bwd packet counts capped at 3)

Rows per (fwd, bwd) shape, share of the class, share leaked, and mean SYN/ACK/FIN/RST/PSH flag counts and total payload bytes per flow.

| class | fwd | bwd | rows | % of class | % leaked | SYN | ACK | FIN | RST | PSH | payload B |
|---|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| Benign | 2 | 2 | 568,778 | 31.8 | 0.0 | 0.00 | 0.01 | 0.00 | 0.00 | 0.00 | 310 |
| Benign | 3+ | 3+ | 461,910 | 25.9 | 0.0 | 1.91 | 92.79 | 1.69 | 0.12 | 11.14 | 90106 |
| Benign | 1 | 0 | 261,613 | 14.6 | 100.0 | 0.00 | 0.77 | 0.00 | 0.34 | 0.00 | 1 |
| Benign | 1 | 1 | 199,206 | 11.2 | 100.0 | 0.02 | 0.29 | 0.05 | 0.09 | 0.02 | 211 |
| Benign | 0 | 1 | 139,031 | 7.8 | 100.0 | 0.00 | 0.83 | 0.05 | 0.21 | 0.00 | 0 |
| Benign | 3+ | 2 | 72,829 | 4.1 | 0.0 | 0.82 | 1.74 | 0.82 | 0.01 | 0.05 | 265 |
| Benign | 0 | 2 | 30,152 | 1.7 | 0.0 | 0.00 | 1.22 | 0.34 | 0.80 | 0.07 | 110 |
| Benign | 2 | 1 | 13,795 | 0.8 | 100.0 | 0.03 | 2.72 | 0.76 | 0.28 | 0.22 | 891 |
| Benign | 0 | 3+ | 13,348 | 0.7 | 0.0 | 0.00 | 2.96 | 1.01 | 0.05 | 0.00 | 1 |
| Benign | 3+ | 0 | 9,033 | 0.5 | 0.0 | 0.74 | 1.84 | 1.46 | 0.12 | 1.07 | 1561 |
| Benign | 1 | 2 | 8,439 | 0.5 | 100.0 | 0.01 | 2.61 | 0.81 | 0.39 | 0.18 | 302 |
| Benign | 2 | 0 | 2,719 | 0.2 | 0.0 | 0.07 | 0.43 | 0.20 | 0.21 | 0.01 | 111 |
| Benign | 3+ | 1 | 2,634 | 0.1 | 100.0 | 0.26 | 9.57 | 0.85 | 0.44 | 2.02 | 12912 |
| Benign | 1 | 3+ | 2,625 | 0.1 | 100.0 | 1.20 | 4.60 | 1.24 | 0.05 | 0.15 | 6 |
| Benign | 2 | 3+ | 127 | 0.0 | 0.0 | 0.04 | 4.88 | 1.39 | 0.44 | 0.50 | 63 |
| Botnet_ARES | 1 | 1 | 3,906 | 70.9 | 100.0 | 1.00 | 1.00 | 0.00 | 1.00 | 0.00 | 0 |
| Botnet_ARES | 3+ | 3+ | 736 | 13.4 | 0.0 | 2.00 | 11.45 | 2.00 | 0.00 | 2.10 | 7176 |
| Botnet_ARES | 1 | 0 | 705 | 12.8 | 100.0 | 0.00 | 1.00 | 0.00 | 0.00 | 0.00 | 0 |
| Botnet_ARES | 3+ | 0 | 159 | 2.9 | 0.0 | 3.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0 |
| DDoS_LOIT | 3+ | 3+ | 95,660 | 99.9 | 0.0 | 2.00 | 12.38 | 1.27 | 1.00 | 2.05 | 11685 |
| DoS_GoldenEye | 3+ | 3+ | 7,762 | 92.8 | 0.0 | 2.18 | 14.09 | 1.02 | 0.39 | 3.13 | 10979 |
| DoS_GoldenEye | 0 | 1 | 263 | 3.1 | 100.0 | 0.00 | 0.02 | 0.00 | 0.98 | 0.00 | 0 |
| DoS_GoldenEye | 1 | 0 | 258 | 3.1 | 100.0 | 0.00 | 0.00 | 0.00 | 1.00 | 0.00 | 0 |
| DoS_GoldenEye | 0 | 2 | 78 | 0.9 | 0.0 | 0.00 | 2.00 | 1.00 | 0.00 | 0.00 | 0 |
| DoS_Hulk | 3+ | 3+ | 158,650 | 45.4 | 0.0 | 2.12 | 11.45 | 1.37 | 0.63 | 2.20 | 12001 |
| DoS_Hulk | 1 | 0 | 107,098 | 30.7 | 100.0 | 0.00 | 0.00 | 0.00 | 1.00 | 0.00 | 0 |
| DoS_Hulk | 0 | 2 | 58,117 | 16.6 | 0.0 | 0.00 | 1.00 | 0.01 | 1.00 | 0.01 | 1 |
| DoS_Hulk | 0 | 1 | 20,885 | 6.0 | 100.0 | 0.00 | 0.00 | 0.00 | 1.00 | 0.00 | 0 |
| DoS_Hulk | 1 | 1 | 4,076 | 1.2 | 100.0 | 0.00 | 1.00 | 0.98 | 1.00 | 0.29 | 12 |
| DoS_Hulk | 3+ | 2 | 201 | 0.1 | 0.0 | 4.31 | 3.89 | 0.04 | 0.00 | 0.00 | 0 |
| DoS_Hulk | 3+ | 0 | 109 | 0.0 | 0.0 | 2.94 | 0.07 | 0.02 | 0.00 | 0.02 | 80 |
| DoS_Hulk | 1 | 2 | 53 | 0.0 | 100.0 | 0.00 | 2.00 | 1.00 | 1.00 | 0.91 | 10 |
| DoS_Slowhttptest | 3+ | 0 | 2,824 | 41.2 | 0.0 | 6.92 | 0.07 | 0.06 | 0.00 | 0.06 | 40 |
| DoS_Slowhttptest | 3+ | 3+ | 1,816 | 26.5 | 0.0 | 2.82 | 14.05 | 1.53 | 0.14 | 6.39 | 5445 |
| DoS_Slowhttptest | 1 | 0 | 1,260 | 18.4 | 100.0 | 0.00 | 0.01 | 0.00 | 0.99 | 0.00 | 0 |
| DoS_Slowhttptest | 0 | 1 | 522 | 7.6 | 100.0 | 0.00 | 0.01 | 0.00 | 0.99 | 0.00 | 0 |
| DoS_Slowhttptest | 1 | 2 | 194 | 2.8 | 100.0 | 0.00 | 2.00 | 0.99 | 1.00 | 1.00 | 1983 |
| DoS_Slowhttptest | 3+ | 2 | 151 | 2.2 | 0.0 | 3.14 | 14.56 | 5.99 | 0.00 | 9.46 | 2852 |
| DoS_Slowhttptest | 2 | 2 | 82 | 1.2 | 0.0 | 0.00 | 3.00 | 1.00 | 1.00 | 1.00 | 1983 |
| DoS_Slowloris | 3+ | 3+ | 2,492 | 48.1 | 0.0 | 3.30 | 17.77 | 0.67 | 0.69 | 11.05 | 4352 |
| DoS_Slowloris | 3+ | 0 | 1,642 | 31.7 | 0.0 | 2.98 | 0.07 | 0.07 | 0.00 | 0.07 | 23 |
| DoS_Slowloris | 1 | 0 | 761 | 14.7 | 100.0 | 0.03 | 0.00 | 0.00 | 0.97 | 0.00 | 0 |
| DoS_Slowloris | 0 | 1 | 255 | 4.9 | 100.0 | 0.00 | 0.04 | 0.00 | 0.96 | 0.00 | 0 |
| FTP-Patator | 3+ | 3+ | 3,992 | 41.9 | 0.0 | 2.00 | 24.33 | 1.37 | 0.62 | 13.96 | 308 |
| FTP-Patator | 1 | 1 | 2,438 | 25.6 | 100.0 | 0.00 | 1.01 | 1.00 | 0.99 | 0.01 | 0 |
| FTP-Patator | 0 | 1 | 1,578 | 16.6 | 100.0 | 0.00 | 0.03 | 0.02 | 0.97 | 0.00 | 0 |
| FTP-Patator | 1 | 0 | 1,506 | 15.8 | 100.0 | 0.00 | 0.01 | 0.01 | 0.99 | 0.00 | 0 |
| Heartbleed | 3+ | 3+ | 8 | 66.7 | 0.0 | 2.00 | 6169.50 | 1.50 | 0.50 | 359.88 | 10024923 |
| Heartbleed | 1 | 0 | 4 | 33.3 | 100.0 | 0.00 | 0.00 | 0.00 | 1.00 | 0.00 | 0 |
| Port_Scan | 1 | 1 | 157,970 | 97.9 | 100.0 | 1.00 | 1.00 | 0.00 | 1.00 | 0.00 | 0 |
| Port_Scan | 1 | 0 | 1,349 | 0.8 | 100.0 | 0.09 | 0.71 | 0.00 | 0.61 | 0.00 | 0 |
| Port_Scan | 0 | 1 | 829 | 0.5 | 100.0 | 1.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0 |
| Port_Scan | 2 | 1 | 484 | 0.3 | 100.0 | 2.00 | 1.00 | 0.00 | 1.00 | 0.00 | 0 |
| Port_Scan | 3+ | 1 | 474 | 0.3 | 100.0 | 2.00 | 3.00 | 0.00 | 1.00 | 0.00 | 0 |
| Port_Scan | 3+ | 3+ | 208 | 0.1 | 0.0 | 2.00 | 8.97 | 1.46 | 0.41 | 1.61 | 4879 |
| SSH-Patator | 3+ | 3+ | 2,980 | 50.1 | 0.0 | 2.00 | 52.79 | 2.00 | 0.01 | 30.74 | 4732 |
| SSH-Patator | 0 | 1 | 2,916 | 49.0 | 100.0 | 0.00 | 1.00 | 0.00 | 0.00 | 0.00 | 0 |
| Web_Brute_Force | 1 | 0 | 1,222 | 44.7 | 100.0 | 0.00 | 1.00 | 0.00 | 0.00 | 0.00 | 0 |
| Web_Brute_Force | 3+ | 2 | 1,180 | 43.2 | 0.0 | 2.00 | 4.00 | 2.00 | 0.00 | 0.00 | 0 |
| Web_Brute_Force | 3+ | 3+ | 185 | 6.8 | 0.0 | 2.00 | 123.26 | 2.00 | 0.00 | 79.04 | 45600 |
| Web_Brute_Force | 0 | 1 | 144 | 5.3 | 100.0 | 0.00 | 1.00 | 0.00 | 0.00 | 0.00 | 0 |
| Web_SQL_Injection | 3+ | 3+ | 12 | 50.0 | 0.0 | 2.00 | 8.42 | 2.00 | 0.00 | 2.00 | 2804 |
| Web_SQL_Injection | 0 | 1 | 8 | 33.3 | 100.0 | 0.00 | 1.00 | 0.00 | 0.00 | 0.00 | 0 |
| Web_SQL_Injection | 1 | 0 | 3 | 12.5 | 100.0 | 0.00 | 1.00 | 0.00 | 0.00 | 0.00 | 0 |
| Web_SQL_Injection | 0 | 2 | 1 | 4.2 | 0.0 | 0.00 | 2.00 | 0.00 | 0.00 | 0.00 | 0 |
| Web_XSS | 1 | 0 | 656 | 48.3 | 100.0 | 0.00 | 1.00 | 0.00 | 0.00 | 0.00 | 0 |
| Web_XSS | 3+ | 2 | 633 | 46.6 | 0.0 | 2.00 | 4.00 | 2.00 | 0.00 | 0.00 | 0 |
| Web_XSS | 3+ | 3+ | 43 | 3.2 | 0.0 | 2.00 | 133.40 | 2.00 | 0.00 | 84.84 | 97539 |
| Web_XSS | 0 | 1 | 23 | 1.7 | 100.0 | 0.00 | 1.00 | 0.00 | 0.00 | 0.00 | 0 |

(Shapes with < 0.5% of a class and < 50 rows omitted; full table in `flow_shapes.csv`.)

#### Notes (hand checks, added after generation)

**Non-IAT epoch-range values are not timestamps** (`../nonIAT_handcheck.txt`): none lies within a day of its flow's
start. `bytes_rate`-type hits are ~0 s flows (2-3 packets) where dividing by a tiny duration gives a huge rate;
the one `total_payload_bytes` / `bwd_bulk_total_size` hit is a genuine 1.87 GB transfer (1.5M packets, 576 s).

**What the leaked rows are** (flow-shape table above):
- Web_Brute_Force / Web_XSS / Web_SQL_Injection: ~45-48% of each class are lone forward ACKs with no payload: the
  trailing-ACK ghost flow reproduced in Step 1. The real attack sessions (3+/2, 3+/3+) are never leaked.
- SSH-Patator: 49% are lone backward ACKs (the same ghost in the other direction).
- DoS_Hulk / Slowloris / Slowhttptest / GoldenEye, FTP-Patator, Heartbleed: leaked rows are lone RST packets or
  FIN/RST teardown fragments split off from the real session.
- Port_Scan (97.9%: 1 fwd SYN + 1 bwd RST/ACK) and Botnet_ARES (70.9%: SYN + RST/ACK, no payload): probes and
  refused connections. Here the leaked rows are the attack's own signature, not fragments; Port_Scan is 99.87% leaked.
- Benign: 14.6% 1/0 (ACK/RST fragments), 11.2% 1/1, 7.8% 0/1.
- Shapes with 0 forward packets (0/1, 0/2, 0/3+) exist although a flow's first packet defines "forward": a further
  flow-splitting artifact (traffic arriving after a flow was closed).


### D4. Flow shapes of leaked rows: BCCC-CIC-IDS-2017

Source: `~/Desktop/ntl_census_multi/BCCC-CIC-IDS-2017/LEAK_SHAPES.md`

### What the leaked rows are: BCCC-CIC-IDS-2017

Every leaked row (any IAT > 1e9) classified by packet counts, TCP flags (summed over both directions) and payload. Script `leak_shapes.py`; full counts `leak_shapes_counts.csv`, shares `leak_shapes_share_of_leaked.csv`.

#### Coarse view: share of each class's leaked rows

| class | rows | leaked | % leaked | ghost / fragment (ACK, RST, FIN, teardown) | connection attempt (SYN, SYN->RST, SYN->SYN-ACK) | carries payload (data packet or session) | other, no payload |
|---|---:|---:|---:|---:|---:|---:|---:|
| Benign | 1,786,239 | 627,343 | 35.1 | 65.3 | 0.9 | 28.9 | 4.8 |
| Botnet_ARES | 5,508 | 4,613 | 83.8 | 15.3 | 84.7 | 0.0 | 0.0 |
| DDoS_LOIT | 95,733 | 50 | 0.1 | 98.0 | 0.0 | 2.0 | 0.0 |
| DoS_GoldenEye | 8,364 | 523 | 6.3 | 99.6 | 0.2 | 0.0 | 0.2 |
| DoS_Hulk | 349,240 | 132,146 | 37.8 | 99.0 | 0.0 | 1.0 | 0.0 |
| DoS_Slowhttptest | 6,860 | 1,981 | 28.9 | 90.0 | 0.0 | 10.0 | 0.0 |
| DoS_Slowloris | 5,177 | 1,017 | 19.6 | 97.5 | 2.5 | 0.0 | 0.0 |
| FTP-Patator | 9,531 | 5,527 | 58.0 | 99.4 | 0.0 | 0.6 | 0.0 |
| Heartbleed | 12 | 4 | 33.3 | 100.0 | 0.0 | 0.0 | 0.0 |
| Port_Scan | 161,323 | 161,109 | 99.9 | 0.6 | 99.2 | 0.0 | 0.2 |
| SSH-Patator | 5,949 | 2,955 | 49.7 | 99.8 | 0.0 | 0.0 | 0.2 |
| Web_Brute_Force | 2,734 | 1,366 | 50.0 | 100.0 | 0.0 | 0.0 | 0.0 |
| Web_SQL_Injection | 24 | 11 | 45.8 | 100.0 | 0.0 | 0.0 | 0.0 |
| Web_XSS | 1,358 | 679 | 50.0 | 100.0 | 0.0 | 0.0 | 0.0 |
| **ALL** | 2,438,052 | 939,324 | 38.5 | 59.2 | 18.0 | 19.5 | 3.3 |

#### Detailed categories: share of each class's leaked rows (%; categories under 0.5% everywhere omitted)

| class | lone SYN | lone RST | lone FIN | lone ACK, no payload (ghost ACK) | SYN -> RST pair (probe/refused) | FIN/RST teardown pair | 1+1 with payload | 1+1 other | multi-packet with payload (session) | repeated SYNs, no payload | multi-packet, no payload |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| Benign | 0.0 | 18.7 | 1.1 | 44.0 | 0.7 | 1.5 | 27.4 | 2.1 | 1.4 | 0.2 | 2.8 |
| Botnet_ARES |  |  |  | 15.3 | 84.7 |  |  |  |  | 0.0 |  |
| DDoS_LOIT |  | 98.0 |  |  |  |  |  |  | 2.0 |  |  |
| DoS_GoldenEye |  | 98.5 |  | 1.1 |  |  |  | 0.2 |  | 0.2 |  |
| DoS_Hulk |  | 96.8 |  |  |  | 2.2 | 0.9 |  | 0.0 | 0.0 | 0.0 |
| DoS_Slowhttptest |  | 89.3 | 0.1 | 0.6 |  |  | 0.1 |  | 10.0 |  |  |
| DoS_Slowloris | 2.5 | 96.5 |  | 1.0 |  | 0.1 |  |  |  |  |  |
| FTP-Patator |  | 54.8 | 0.9 | 0.2 |  | 43.6 | 0.5 |  | 0.1 |  |  |
| Heartbleed |  | 100.0 |  |  |  |  |  |  |  |  |  |
| Port_Scan | 0.6 | 0.5 |  | 0.1 | 98.1 |  | 0.0 |  |  | 0.6 |  |
| SSH-Patator |  | 0.1 |  | 99.3 |  | 0.4 |  | 0.1 |  |  | 0.1 |
| Web_Brute_Force |  | 0.1 |  | 99.9 |  |  |  |  |  |  |  |
| Web_SQL_Injection |  |  |  | 100.0 |  |  |  |  |  |  |  |
| Web_XSS |  | 0.1 |  | 99.9 |  |  |  |  |  |  |  |
| ALL | 0.1 | 26.9 | 0.8 | 30.0 | 17.7 | 1.6 | 18.5 | 1.4 | 1.0 | 0.2 | 1.9 |

#### Interpretation
- Pooled over the 12 attack classes other than Port_Scan and Botnet_ARES (146,259 leaked rows): **98.9% fragments**
  (lone RST 27-100% for DoS / Heartbleed / FTP, ghost ACKs 99-100% for SSH-Patator and the three web attacks,
  FIN/RST teardown pairs 44% for FTP-Patator), **0.0% connection attempts, 1.0% with payload**. These rows carry no
  attack content; the attack sessions themselves (multi-packet, with payload) are never leaked.
- **Exceptions: Port_Scan and Botnet_ARES** (165,722 leaked rows): 98.8% are single SYN -> RST/ACK pairs (probes,
  refused connections). For a port scan that *is* the attack behaviour, so here the leak sits on genuinely
  attack-specific rows, not on fragments.
- Benign leaked rows differ: 65.3% fragments, but 28.9% carry payload (mostly "1+1 with payload").


### D5. Census: BCCC-cPacket-Cloud-DDoS-2024

Source: `~/Desktop/ntl_census_multi/BCCC-cPacket-Cloud-DDoS-2024/RESULTS.md`

### Leak census: BCCC-cPacket-Cloud-DDoS-2024

NTLFlowLyzer output: **yes**. 4 non-empty CSV files, 324 columns, 700,774 rows (file list with sizes: `file_list.txt`). Class key: `label` + `activity`.
IAT columns (30): combined ['packets_IAT_mean', 'packet_IAT_std', 'packet_IAT_max', 'packet_IAT_min', 'packet_IAT_total', 'packets_IAT_median', 'packets_IAT_skewness', 'packets_IAT_cov', 'packets_IAT_mode', 'packets_IAT_variance']; fwd ['fwd_packets_IAT_mean', 'fwd_packets_IAT_std', 'fwd_packets_IAT_max', 'fwd_packets_IAT_min', 'fwd_packets_IAT_total', 'fwd_packets_IAT_median', 'fwd_packets_IAT_skewness', 'fwd_packets_IAT_cov', 'fwd_packets_IAT_mode', 'fwd_packets_IAT_variance']; bwd ['bwd_packets_IAT_mean', 'bwd_packets_IAT_std', 'bwd_packets_IAT_max', 'bwd_packets_IAT_min', 'bwd_packets_IAT_total', 'bwd_packets_IAT_median', 'bwd_packets_IAT_skewness', 'bwd_packets_IAT_cov', 'bwd_packets_IAT_mode', 'bwd_packets_IAT_variance'].
Counts: `packets_count`, `fwd_packets_count`, `bwd_packets_count`. Leak = IAT value > 1e9.

#### Per class

| class | n | 1-packet | fwd leak | bwd leak | any leak | % | leak, >1 packet | % of leaked |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| Attack / Attack-Killall-v2 | 6,033 | 1,134 | 1,418 | 331 | 1,453 | 24.08 | 319 | 22.0 |
| Attack / Attack-Killer-TCP | 6,254 | 1,114 | 1,764 | 677 | 1,788 | 28.59 | 674 | 37.7 |
| Attack / Attack-TCP-BYPass-V1 | 138,368 | 132,330 | 132,682 | 437 | 132,732 | 95.93 | 402 | 0.3 |
| Attack / Attack-TCP-Control | 5,744 | 1,052 | 1,461 | 454 | 1,502 | 26.15 | 450 | 30.0 |
| Attack / Attack-TCP-Flag-ACK | 10,683 | 1,318 | 1,724 | 433 | 1,741 | 16.30 | 423 | 24.3 |
| Attack / Attack-TCP-Flag-ACK-PSH | 7,482 | 1,231 | 1,635 | 451 | 1,666 | 22.27 | 435 | 26.1 |
| Attack / Attack-TCP-Flag-MIX | 7,416 | 1,150 | 1,704 | 581 | 1,724 | 23.25 | 574 | 33.3 |
| Attack / Attack-TCP-Flag-OSYN | 867 | 430 | 688 | 305 | 722 | 83.28 | 292 | 40.4 |
| Attack / Attack-TCP-Flag-OSYNP | 890 | 359 | 724 | 374 | 740 | 83.15 | 381 | 51.5 |
| Attack / Attack-TCP-Flag-RST-ACK | 1,445 | 314 | 584 | 278 | 596 | 41.25 | 282 | 47.3 |
| Attack / Attack-TCP-Flag-SYN | 7,845 | 1,275 | 1,738 | 509 | 1,765 | 22.50 | 490 | 27.8 |
| Attack / Attack-TCP-Flag-SYN-ACK | 8,204 | 1,105 | 1,582 | 494 | 1,595 | 19.44 | 490 | 30.7 |
| Attack / Attack-TCP-Flag-SYN-TFO | 3,631 | 518 | 766 | 301 | 807 | 22.23 | 289 | 35.8 |
| Attack / Attack-TCP-Flag-SYN-TIME | 1,360 | 557 | 852 | 413 | 923 | 67.87 | 366 | 39.7 |
| Attack / Attack-TCP-IGMP | 7,251 | 1,173 | 1,608 | 467 | 1,634 | 22.53 | 461 | 28.2 |
| Attack / Attack-TCP-SYN | 6,953 | 1,028 | 1,414 | 448 | 1,450 | 20.85 | 422 | 29.1 |
| Attack / Attack-TCP-Valid-SYN | 8,043 | 1,153 | 1,442 | 315 | 1,459 | 18.14 | 306 | 21.0 |
| Benign / Benign | 302,284 | 139,284 | 193,962 | 115,416 | 244,792 | 80.98 | 105,508 | 43.1 |
| Benign / Benign-Email-Receive | 1,395 | 477 | 578 | 640 | 935 | 67.03 | 458 | 49.0 |
| Benign / Benign-Email-Send | 1,938 | 889 | 640 | 626 | 1,151 | 59.39 | 262 | 22.8 |
| Benign / Benign-FTP | 483 | 204 | 170 | 191 | 307 | 63.56 | 103 | 33.6 |
| Benign / Benign-SSH | 2,985 | 1,097 | 1,350 | 346 | 1,443 | 48.34 | 346 | 24.0 |
| Benign / Benign-Systemic | 48,074 | 5,033 | 6,146 | 3,600 | 8,163 | 16.98 | 3,130 | 38.3 |
| Benign / Benign-Telnet | 4,768 | 1,663 | 1,818 | 2,799 | 3,996 | 83.81 | 2,333 | 58.4 |
| Benign / Benign-Web_Browsing_HTTP-S | 51,272 | 24,319 | 22,264 | 6,929 | 27,810 | 54.24 | 3,491 | 12.6 |
| Suspicious / Suspicious | 59,106 | 10,048 | 15,163 | 5,609 | 15,533 | 26.28 | 5,485 | 35.3 |
| **ALL** | 700,774 | 330,255 | 395,877 | 143,424 | **458,427** | **65.42** | 128,172 | 28.0 |

#### Rule check

fwd leak <=> fwd_packets_count == 1: 0 violations; bwd leak <=> bwd_packets_count == 1: 0; combined leak <=> packets_count == 1: 0 (of 700,774 rows).

#### Leaked value vs `timestamp` column

Most common offset (leaked fwd value − timestamp): **18000.0 s** = +5 h, in 99.59% of 395,877 leaked-fwd rows; top 5: 18000.0: 394,258, 18006.0: 155, 18006.004: 95, 18000.209: 74, 18000.206: 64.
So the `timestamp` column is local time (UTC-5) and the leaked IAT is the UTC epoch of the flow start.

#### Calendar (local time = UTC-5) vs documented capture days

Leaked rows on their file's documented capture day: **458,427 of 458,427 (100.00%)**.

| file | class | documented day | leaked rows | on that day | first (local) | last (local) | local days |
|---|---|---|---:|---:|---|---|---|
| Thursday_14_Dec_2023 | Benign / Benign | 2023-12-14 | 63,760 | 63760 | 2023-12-14 09:01 | 2023-12-14 17:00 | 2023-12-14:63760 |
| Thursday_14_Dec_2023 | Benign / Benign-Email-Receive | 2023-12-14 | 322 | 322 | 2023-12-14 09:01 | 2023-12-14 16:55 | 2023-12-14:322 |
| Thursday_14_Dec_2023 | Benign / Benign-Systemic | 2023-12-14 | 1,967 | 1967 | 2023-12-14 09:01 | 2023-12-14 17:00 | 2023-12-14:1967 |
| Thursday_14_Dec_2023 | Benign / Benign-Telnet | 2023-12-14 | 2,727 | 2727 | 2023-12-14 09:01 | 2023-12-14 17:00 | 2023-12-14:2727 |
| Thursday_14_Dec_2023 | Benign / Benign-Web_Browsing_HTTP-S | 2023-12-14 | 5,573 | 5573 | 2023-12-14 09:01 | 2023-12-14 16:59 | 2023-12-14:5573 |
| Thursday_14_Dec_2023 | Benign / Benign-Email-Send | 2023-12-14 | 360 | 360 | 2023-12-14 09:07 | 2023-12-14 16:55 | 2023-12-14:360 |
| Thursday_14_Dec_2023 | Benign / Benign-FTP | 2023-12-14 | 193 | 193 | 2023-12-14 09:10 | 2023-12-14 16:48 | 2023-12-14:193 |
| Thursday_14_Dec_2023 | Benign / Benign-SSH | 2023-12-14 | 577 | 577 | 2023-12-14 09:11 | 2023-12-14 16:58 | 2023-12-14:577 |
| Saturday_16_Dec_2023 | Benign / Benign | 2023-12-16 | 124,716 | 124716 | 2023-12-16 09:00 | 2023-12-16 17:00 | 2023-12-16:124716 |
| Saturday_16_Dec_2023 | Benign / Benign-SSH | 2023-12-16 | 637 | 637 | 2023-12-16 09:00 | 2023-12-16 16:54 | 2023-12-16:637 |
| Saturday_16_Dec_2023 | Benign / Benign-Telnet | 2023-12-16 | 924 | 924 | 2023-12-16 09:00 | 2023-12-16 16:58 | 2023-12-16:924 |
| Saturday_16_Dec_2023 | Benign / Benign-Web_Browsing_HTTP-S | 2023-12-16 | 7,267 | 7267 | 2023-12-16 09:00 | 2023-12-16 17:00 | 2023-12-16:7267 |
| Saturday_16_Dec_2023 | Benign / Benign-Systemic | 2023-12-16 | 4,099 | 4099 | 2023-12-16 09:01 | 2023-12-16 17:00 | 2023-12-16:4099 |
| Saturday_16_Dec_2023 | Benign / Benign-Email-Receive | 2023-12-16 | 324 | 324 | 2023-12-16 09:02 | 2023-12-16 16:58 | 2023-12-16:324 |
| Saturday_16_Dec_2023 | Benign / Benign-Email-Send | 2023-12-16 | 356 | 356 | 2023-12-16 09:08 | 2023-12-16 16:58 | 2023-12-16:356 |
| Saturday_16_Dec_2023 | Benign / Benign-FTP | 2023-12-16 | 66 | 66 | 2023-12-16 09:33 | 2023-12-16 16:54 | 2023-12-16:66 |
| Monday_18_Dec_2023 | Attack / Attack-TCP-Valid-SYN | 2023-12-18 | 1,459 | 1459 | 2023-12-18 08:56 | 2023-12-18 09:29 | 2023-12-18:1459 |
| Monday_18_Dec_2023 | Benign / Benign | 2023-12-18 | 28,348 | 28348 | 2023-12-18 08:56 | 2023-12-18 17:00 | 2023-12-18:28348 |
| Monday_18_Dec_2023 | Benign / Benign-Systemic | 2023-12-18 | 1,139 | 1139 | 2023-12-18 08:56 | 2023-12-18 17:00 | 2023-12-18:1139 |
| Monday_18_Dec_2023 | Benign / Benign-Telnet | 2023-12-18 | 159 | 159 | 2023-12-18 08:56 | 2023-12-18 16:54 | 2023-12-18:159 |
| Monday_18_Dec_2023 | Benign / Benign-Web_Browsing_HTTP-S | 2023-12-18 | 10,871 | 10871 | 2023-12-18 08:56 | 2023-12-18 17:00 | 2023-12-18:10871 |
| Monday_18_Dec_2023 | Benign / Benign-Email-Receive | 2023-12-18 | 152 | 152 | 2023-12-18 08:57 | 2023-12-18 16:53 | 2023-12-18:152 |
| Monday_18_Dec_2023 | Benign / Benign-FTP | 2023-12-18 | 24 | 24 | 2023-12-18 08:59 | 2023-12-18 16:23 | 2023-12-18:24 |
| Monday_18_Dec_2023 | Benign / Benign-SSH | 2023-12-18 | 115 | 115 | 2023-12-18 08:59 | 2023-12-18 16:56 | 2023-12-18:115 |
| Monday_18_Dec_2023 | Benign / Benign-Email-Send | 2023-12-18 | 243 | 243 | 2023-12-18 09:00 | 2023-12-18 16:55 | 2023-12-18:243 |
| Monday_18_Dec_2023 | Attack / Attack-TCP-BYPass-V1 | 2023-12-18 | 132,732 | 132732 | 2023-12-18 09:30 | 2023-12-18 09:59 | 2023-12-18:132732 |
| Monday_18_Dec_2023 | Suspicious / Suspicious | 2023-12-18 | 6,137 | 6137 | 2023-12-18 09:50 | 2023-12-18 17:00 | 2023-12-18:6137 |
| Monday_18_Dec_2023 | Attack / Attack-Killall-v2 | 2023-12-18 | 1,453 | 1453 | 2023-12-18 10:00 | 2023-12-18 10:29 | 2023-12-18:1453 |
| Monday_18_Dec_2023 | Attack / Attack-TCP-IGMP | 2023-12-18 | 1,634 | 1634 | 2023-12-18 10:30 | 2023-12-18 10:59 | 2023-12-18:1634 |
| Monday_18_Dec_2023 | Attack / Attack-TCP-SYN | 2023-12-18 | 1,450 | 1450 | 2023-12-18 11:00 | 2023-12-18 11:29 | 2023-12-18:1450 |
| Monday_18_Dec_2023 | Attack / Attack-Killer-TCP | 2023-12-18 | 1,788 | 1788 | 2023-12-18 11:30 | 2023-12-18 11:59 | 2023-12-18:1788 |
| Monday_18_Dec_2023 | Attack / Attack-TCP-Control | 2023-12-18 | 1,502 | 1502 | 2023-12-18 13:00 | 2023-12-18 13:29 | 2023-12-18:1502 |
| Monday_18_Dec_2023 | Attack / Attack-TCP-Flag-MIX | 2023-12-18 | 1,724 | 1724 | 2023-12-18 13:30 | 2023-12-18 13:59 | 2023-12-18:1724 |
| Monday_18_Dec_2023 | Attack / Attack-TCP-Flag-SYN | 2023-12-18 | 1,765 | 1765 | 2023-12-18 14:00 | 2023-12-18 14:29 | 2023-12-18:1765 |
| Monday_18_Dec_2023 | Attack / Attack-TCP-Flag-ACK | 2023-12-18 | 1,741 | 1741 | 2023-12-18 14:30 | 2023-12-18 14:59 | 2023-12-18:1741 |
| Monday_18_Dec_2023 | Attack / Attack-TCP-Flag-SYN-ACK | 2023-12-18 | 1,595 | 1595 | 2023-12-18 15:00 | 2023-12-18 15:29 | 2023-12-18:1595 |
| Monday_18_Dec_2023 | Attack / Attack-TCP-Flag-ACK-PSH | 2023-12-18 | 1,666 | 1666 | 2023-12-18 15:30 | 2023-12-18 15:59 | 2023-12-18:1666 |
| Tuesday_19_Dec_2023 | Benign / Benign | 2023-12-19 | 27,968 | 27968 | 2023-12-19 08:59 | 2023-12-19 17:00 | 2023-12-19:27968 |
| Tuesday_19_Dec_2023 | Benign / Benign-Web_Browsing_HTTP-S | 2023-12-19 | 4,099 | 4099 | 2023-12-19 08:59 | 2023-12-19 16:58 | 2023-12-19:4099 |
| Tuesday_19_Dec_2023 | Suspicious / Suspicious | 2023-12-19 | 9,396 | 9396 | 2023-12-19 08:59 | 2023-12-19 17:00 | 2023-12-19:9396 |
| Tuesday_19_Dec_2023 | Attack / Attack-TCP-Flag-RST-ACK | 2023-12-19 | 596 | 596 | 2023-12-19 09:00 | 2023-12-19 09:29 | 2023-12-19:596 |
| Tuesday_19_Dec_2023 | Benign / Benign-Email-Send | 2023-12-19 | 192 | 192 | 2023-12-19 09:00 | 2023-12-19 16:59 | 2023-12-19:192 |
| Tuesday_19_Dec_2023 | Benign / Benign-Telnet | 2023-12-19 | 186 | 186 | 2023-12-19 09:00 | 2023-12-19 16:55 | 2023-12-19:186 |
| Tuesday_19_Dec_2023 | Benign / Benign-Systemic | 2023-12-19 | 958 | 958 | 2023-12-19 09:01 | 2023-12-19 16:59 | 2023-12-19:958 |
| Tuesday_19_Dec_2023 | Benign / Benign-Email-Receive | 2023-12-19 | 137 | 137 | 2023-12-19 09:08 | 2023-12-19 16:56 | 2023-12-19:137 |
| Tuesday_19_Dec_2023 | Benign / Benign-SSH | 2023-12-19 | 114 | 114 | 2023-12-19 09:11 | 2023-12-19 16:56 | 2023-12-19:114 |
| Tuesday_19_Dec_2023 | Attack / Attack-TCP-Flag-SYN-TFO | 2023-12-19 | 807 | 807 | 2023-12-19 09:30 | 2023-12-19 09:59 | 2023-12-19:807 |
| Tuesday_19_Dec_2023 | Attack / Attack-TCP-Flag-SYN-TIME | 2023-12-19 | 923 | 923 | 2023-12-19 10:00 | 2023-12-19 10:29 | 2023-12-19:923 |
| Tuesday_19_Dec_2023 | Benign / Benign-FTP | 2023-12-19 | 24 | 24 | 2023-12-19 10:03 | 2023-12-19 16:59 | 2023-12-19:24 |
| Tuesday_19_Dec_2023 | Attack / Attack-TCP-Flag-OSYN | 2023-12-19 | 722 | 722 | 2023-12-19 10:30 | 2023-12-19 10:59 | 2023-12-19:722 |
| Tuesday_19_Dec_2023 | Attack / Attack-TCP-Flag-OSYNP | 2023-12-19 | 740 | 740 | 2023-12-19 11:00 | 2023-12-19 11:29 | 2023-12-19:740 |

#### Non-IAT columns with values in 1.4e9..2.2e9

- `total_payload_bytes`: 19
- `bwd_total_payload_bytes`: 14
- `fwd_total_payload_bytes`: 5
- `fwd_bulk_total_size`: 5
- `avg_fwd_bulk_rate`: 2
- `bytes_rate`: 1
- `fwd_bytes_rate`: 1
- `bwd_bytes_rate`: 1

Non-numeric columns (samples): `timestamp`: ['2023-12-18 08:56:39.743361', '2023-12-18 08:56:40.409563', '2023-12-18 08:56:39.214012']; `protocol`: ['TCP']; `delta_start`: ['not a complete handshake', '0.0000', '0.0013']; `handshake_duration`: ['not a complete handshake', '0.1111', '0.1080']; `label`: ['Attack', 'Benign', 'Suspicious']; `activity`: ['Attack-TCP-Valid-SYN', 'Benign', 'Benign-Web_Browsing_HTTP-S']

#### Notes (hand checks, added after generation)

**Non-IAT epoch-range values are not timestamps** (`../nonIAT_handcheck.txt`): none lies within a day of its flow's
start. `total_payload_bytes` / `bulk_total_size` hits are genuine 1.5-2.2 GB transfers (1.2-1.6M packets, 50-300 s);
rate hits are ~0 s flows.
`label` has three values (Attack, Benign, Suspicious); `activity` gives the subtype, so classes are reported as
"label / activity". `delta_start` / `handshake_duration` use the string "not a complete handshake" as a placeholder.
Attack-TCP-BYPass-V1 is 95.6% 1-packet flows (132,330 of 138,368) and 95.93% leaked.


### D6. Flow shapes of leaked rows: BCCC-cPacket-Cloud-DDoS-2024

Source: `~/Desktop/ntl_census_multi/BCCC-cPacket-Cloud-DDoS-2024/LEAK_SHAPES.md`

### What the leaked rows are: BCCC-cPacket-Cloud-DDoS-2024

Every leaked row (any IAT > 1e9) classified by packet counts, TCP flags (summed over both directions) and payload. Script `leak_shapes.py`; full counts `leak_shapes_counts.csv`, shares `leak_shapes_share_of_leaked.csv`.

#### Coarse view: share of each class's leaked rows

| class | rows | leaked | % leaked | ghost / fragment (ACK, RST, FIN, teardown) | connection attempt (SYN, SYN->RST, SYN->SYN-ACK) | carries payload (data packet or session) | other, no payload |
|---|---:|---:|---:|---:|---:|---:|---:|
| Attack / Attack-Killall-v2 | 6,033 | 1,453 | 24.1 | 61.9 | 35.9 | 2.1 | 0.2 |
| Attack / Attack-Killer-TCP | 6,254 | 1,788 | 28.6 | 47.3 | 52.6 | 0.0 | 0.1 |
| Attack / Attack-TCP-BYPass-V1 | 138,368 | 132,732 | 95.9 | 0.8 | 99.2 | 0.0 | 0.0 |
| Attack / Attack-TCP-Control | 5,744 | 1,502 | 26.1 | 46.9 | 50.7 | 1.3 | 1.1 |
| Attack / Attack-TCP-Flag-ACK | 10,683 | 1,741 | 16.3 | 55.7 | 44.1 | 0.0 | 0.2 |
| Attack / Attack-TCP-Flag-ACK-PSH | 7,482 | 1,666 | 22.3 | 49.5 | 49.9 | 0.1 | 0.5 |
| Attack / Attack-TCP-Flag-MIX | 7,416 | 1,724 | 23.2 | 42.3 | 57.2 | 0.3 | 0.2 |
| Attack / Attack-TCP-Flag-OSYN | 867 | 722 | 83.3 | 28.4 | 70.6 | 0.3 | 0.7 |
| Attack / Attack-TCP-Flag-OSYNP | 890 | 740 | 83.1 | 18.9 | 80.8 | 0.0 | 0.3 |
| Attack / Attack-TCP-Flag-RST-ACK | 1,445 | 596 | 41.2 | 20.5 | 79.4 | 0.2 | 0.0 |
| Attack / Attack-TCP-Flag-SYN | 7,845 | 1,765 | 22.5 | 57.1 | 42.9 | 0.0 | 0.0 |
| Attack / Attack-TCP-Flag-SYN-ACK | 8,204 | 1,595 | 19.4 | 48.3 | 51.5 | 0.0 | 0.2 |
| Attack / Attack-TCP-Flag-SYN-TFO | 3,631 | 807 | 22.2 | 32.5 | 66.5 | 0.6 | 0.4 |
| Attack / Attack-TCP-Flag-SYN-TIME | 1,360 | 923 | 67.9 | 37.6 | 61.1 | 0.8 | 0.5 |
| Attack / Attack-TCP-IGMP | 7,251 | 1,634 | 22.5 | 59.6 | 39.3 | 0.7 | 0.4 |
| Attack / Attack-TCP-SYN | 6,953 | 1,450 | 20.9 | 60.0 | 39.8 | 0.1 | 0.1 |
| Attack / Attack-TCP-Valid-SYN | 8,043 | 1,459 | 18.1 | 61.3 | 38.5 | 0.2 | 0.0 |
| Benign / Benign | 302,284 | 244,792 | 81.0 | 25.4 | 74.5 | 0.0 | 0.0 |
| Benign / Benign-Email-Receive | 1,395 | 935 | 67.0 | 31.2 | 56.8 | 0.0 | 12.0 |
| Benign / Benign-Email-Send | 1,938 | 1,151 | 59.4 | 65.2 | 34.2 | 0.1 | 0.5 |
| Benign / Benign-FTP | 483 | 307 | 63.6 | 61.6 | 34.5 | 3.6 | 0.3 |
| Benign / Benign-SSH | 2,985 | 1,443 | 48.3 | 69.7 | 28.5 | 1.7 | 0.1 |
| Benign / Benign-Systemic | 48,074 | 8,163 | 17.0 | 56.6 | 41.4 | 1.0 | 1.0 |
| Benign / Benign-Telnet | 4,768 | 3,996 | 83.8 | 31.1 | 68.9 | 0.0 | 0.0 |
| Benign / Benign-Web_Browsing_HTTP-S | 51,272 | 27,810 | 54.2 | 86.2 | 6.9 | 2.5 | 4.3 |
| Suspicious / Suspicious | 59,106 | 15,533 | 26.3 | 32.0 | 67.4 | 0.2 | 0.4 |
| **ALL** | 700,774 | 458,427 | 65.4 | 24.2 | 75.2 | 0.2 | 0.3 |

#### Detailed categories: share of each class's leaked rows (%; categories under 0.5% everywhere omitted)

| class | lone SYN | lone RST | lone FIN | lone ACK, no payload (ghost ACK) | SYN -> RST pair (probe/refused) | SYN -> SYN-ACK pair | FIN/RST teardown pair | 1+1 with payload | 1+1 other | multi-packet with payload (session) | repeated SYNs, no payload | multi-packet, no payload |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| Attack / Attack-Killall-v2 | 16.2 | 54.1 |  | 7.2 | 19.1 |  | 0.6 | 0.6 | 0.1 | 1.1 | 0.4 | 0.1 |
| Attack / Attack-Killer-TCP | 15.0 | 45.7 |  | 1.6 | 36.5 |  |  |  |  |  | 1.1 | 0.1 |
| Attack / Attack-TCP-BYPass-V1 | 98.9 | 0.7 |  | 0.0 | 0.3 |  | 0.0 |  |  | 0.0 | 0.0 |  |
| Attack / Attack-TCP-Control | 24.2 | 39.3 |  | 6.4 | 25.8 | 0.3 | 1.2 |  | 0.1 | 1.2 | 0.3 | 1.0 |
| Attack / Attack-TCP-Flag-ACK | 21.7 | 51.9 |  | 2.1 | 21.9 | 0.1 | 1.7 |  | 0.1 |  | 0.3 | 0.1 |
| Attack / Attack-TCP-Flag-ACK-PSH | 24.4 | 47.4 |  | 2.0 | 24.9 |  | 0.1 |  | 0.2 | 0.1 | 0.6 | 0.2 |
| Attack / Attack-TCP-Flag-MIX | 25.1 | 39.1 |  | 2.5 | 31.4 | 0.2 | 0.7 | 0.1 | 0.2 | 0.2 | 0.5 | 0.1 |
| Attack / Attack-TCP-Flag-OSYN | 31.3 | 20.1 |  | 8.0 | 37.1 |  | 0.3 | 0.1 |  | 0.1 | 2.1 | 0.7 |
| Attack / Attack-TCP-Flag-OSYNP | 29.3 | 15.1 |  | 3.8 | 48.2 |  |  |  | 0.1 |  | 3.0 | 0.1 |
| Attack / Attack-TCP-Flag-RST-ACK | 31.7 | 18.8 |  | 1.7 | 44.6 |  |  |  |  |  | 2.7 |  |
| Attack / Attack-TCP-Flag-SYN | 18.8 | 50.7 |  | 2.5 | 23.5 |  | 3.9 |  |  |  | 0.5 |  |
| Attack / Attack-TCP-Flag-SYN-ACK | 21.1 | 46.8 |  | 1.4 | 30.0 |  | 0.1 |  | 0.1 |  | 0.4 | 0.1 |
| Attack / Attack-TCP-Flag-SYN-TFO | 31.7 | 26.4 |  | 5.9 | 31.6 |  | 0.1 | 0.5 |  | 0.1 | 3.1 | 0.4 |
| Attack / Attack-TCP-Flag-SYN-TIME | 22.9 | 28.8 |  | 8.7 | 33.8 | 2.4 | 0.1 | 0.5 | 0.2 | 0.2 | 2.1 | 0.3 |
| Attack / Attack-TCP-IGMP | 16.6 | 51.0 |  | 4.0 | 22.2 |  | 4.6 |  | 0.2 | 0.7 | 0.4 | 0.2 |
| Attack / Attack-TCP-SYN | 14.1 | 53.9 |  | 2.7 | 25.0 |  | 3.4 | 0.1 |  | 0.1 | 0.6 |  |
| Attack / Attack-TCP-Valid-SYN | 17.6 | 60.6 |  | 0.8 | 20.3 |  |  | 0.1 |  |  | 0.5 |  |
| Benign / Benign | 31.4 | 25.4 |  | 0.0 | 26.4 | 0.0 | 0.0 | 0.0 |  | 0.0 | 16.7 | 0.0 |
| Benign / Benign-Email-Receive | 19.8 | 13.6 |  | 17.6 | 18.7 |  |  |  | 11.6 |  | 18.3 | 0.4 |
| Benign / Benign-Email-Send | 12.1 | 9.2 |  | 56.0 | 9.7 |  |  |  | 0.3 | 0.1 | 12.4 | 0.3 |
| Benign / Benign-FTP | 8.1 | 27.4 | 1.0 | 30.0 | 14.0 |  | 3.3 | 0.3 |  | 3.3 | 12.4 | 0.3 |
| Benign / Benign-SSH | 7.6 | 11.2 | 0.2 | 56.4 | 14.9 | 0.5 | 1.9 | 0.3 |  | 1.0 | 5.3 | 0.1 |
| Benign / Benign-Systemic | 10.6 | 48.2 | 0.5 | 2.2 | 13.0 |  | 5.6 | 0.7 | 0.0 | 0.2 | 17.8 | 1.0 |
| Benign / Benign-Telnet | 10.5 | 31.1 |  | 0.1 | 15.5 | 0.0 |  |  |  |  | 42.8 |  |
| Benign / Benign-Web_Browsing_HTTP-S | 1.8 | 36.3 | 0.5 | 48.6 | 2.6 | 0.0 | 0.8 | 0.4 | 1.2 | 2.0 | 2.4 | 3.2 |
| Suspicious / Suspicious | 33.8 | 27.7 | 0.0 | 3.1 | 32.2 | 0.1 | 1.2 | 0.1 | 0.1 | 0.1 | 1.2 | 0.3 |
| ALL | 48.1 | 20.2 | 0.0 | 3.7 | 17.2 | 0.0 | 0.3 | 0.1 | 0.1 | 0.1 | 9.9 | 0.2 |

#### Interpretation
- Leaked attack rows carry almost no payload (0.1% over all attack subtypes).
- The 16 attack subtypes other than BYPass-V1 (21,565 leaked rows) all show the **same generic mix**: lone RST 39-61%,
  lone SYN 14-32%, SYN -> RST pairs 19-48%, ghost ACKs 1-9%; pooled 49.0% fragments, 50.3% connection attempts,
  0.4% payload. The mix does not follow the attack type: the leaked rows of the ACK, ACK-PSH and RST-ACK floods are
  not ACK or RST-ACK packets but the same SYN / RST shapes. Total-variation distance between the subtypes' category
  mixes: median 0.18; to Benign 0.26, to Suspicious 0.20. Benign and Suspicious leaked rows look alike too
  (~33% fragments, ~67% connection attempts, 0.2-0.3% payload). So the leaked rows carry no subtype-specific
  behaviour; what separates them is mainly when they occurred.
- **Exception: Attack-TCP-BYPass-V1** (132,732 leaked rows, 87% of all leaked attack rows): 98.9% lone SYNs. For a
  SYN-based attack the lone SYN may be the attack packet itself, so this class does not support the "no attack
  behaviour" reading.


### D7. Census: BCCC-DLLayer-IDS-2025 (not NTLFlowLyzer)

Source: `~/Desktop/ntl_census_multi/BCCC-DLLayer-IDS-2025/RESULTS.md`

### Leak census: BCCC-DLLayer-IDS-2025 (pass 1 only)

**NTLFlowLyzer output: no.** 17 CSV files in 11 class folders, 7.5 GB; 3 Benign files are empty (0 bytes:
Jul7, Jul8, Jul11). The 14 non-empty files share one 277-column header of layer-2 / frame features: `connection`,
`tcp_stream`, `protocol`, MAC address + vendor/OUI fields, `eth_type`, `time_delta`, `num_frame`, `sum_frame_len`,
per-protocol counters and ratios (ARP, DHCP, STP, CDP, 802.1Q), `label`. No IAT, `packets_count` or
`fwd/bwd_packets_count` columns. The extractor is not identifiable from the files (file names end in
`_features_combined_<date>`, which suggests a custom frame-level extractor run in Oct 2025).

#### Epoch scan (one file, as the brief specifies)
File `STP_attack/Aug1-STP_features_combined_20251013_155048.csv`: 153,486 rows (Benign 136,843, STP attack 16,643).
Every numeric column scanned at three scales: seconds (1.4e9-2.2e9), milliseconds (1.4e12-2.2e12), microseconds
(1.4e15-2.2e15). Millisecond and microsecond scale: **no hits**. Second scale hits:

| column | rows in range | distinct values | in capture period (Jul-Aug 2025) | what it is |
|---|---:|---:|---:|---|
| arp_over_dhcp_ratio | 375 | 9 | 0 | ratio; round values (1.4e9, 1.5e9, 2.0e9) |
| stp_over_cdp_ratio | 160 | 8 | 0 | ratio; round values |
| dhcp_mean_transaction_id | 148 | 134 | 0 | random 32-bit DHCP transaction IDs |
| dhcp_min_transaction_id | 144 | 127 | 0 | same |
| dhcp_max_transaction_id | 136 | 121 | 0 | same |
| sum_frame_len_div_time | 67 | 33 | 0 | rate (bytes / time) |
| dhcp_sum_transaction_id | 51 | 51 | 0 | sum of transaction IDs |
| cdp_over_stp_ratio | 17 | 6 | 0 | ratio; round values |

None of the values lie in the capture period, and they decode to dates spread over 2014-2038.
**No timestamp leak.** Per the brief, this dataset stops at pass 1. (The round-valued ratios, 6-9 distinct values,
look like division by a tiny epsilon: a separate quality issue, not a leak.)

Script: `epoch_scan.py`; output: `epoch_scan_STP.txt`.


### D8. Hand check: non-IAT values in the epoch range

Source: `~/Desktop/ntl_census_multi/nonIAT_handcheck.txt`

```
== BCCC-CIC-IDS-2017
  friday_benign: bytes_rate n=24 range 1.465e+09..2.024e+09, within 1 day of flow start: 0; median packets 2, median duration 0.0s
  friday_benign: fwd_bytes_rate n=23 range 1.465e+09..2.024e+09, within 1 day of flow start: 0; median packets 2, median duration 0.0s
  friday_benign: bwd_bytes_rate n=1 range 1.518e+09..1.518e+09, within 1 day of flow start: 0; median packets 2, median duration 0.0s
  tuesday_benign: total_payload_bytes n=1 range 1.868e+09..1.868e+09, within 1 day of flow start: 0; median packets 1526795, median duration 576.4s
  tuesday_benign: bwd_total_payload_bytes n=1 range 1.868e+09..1.868e+09, within 1 day of flow start: 0; median packets 1526795, median duration 576.4s
  tuesday_benign: bytes_rate n=2 range 1.445e+09..1.884e+09, within 1 day of flow start: 0; median packets 2, median duration 0.0s
  tuesday_benign: bwd_bytes_rate n=1 range 1.884e+09..1.884e+09, within 1 day of flow start: 0; median packets 2, median duration 0.0s
  tuesday_benign: bwd_bulk_total_size n=1 range 1.737e+09..1.737e+09, within 1 day of flow start: 0; median packets 1526795, median duration 576.4s
  wednesday_benign: bytes_rate n=3 range 1.469e+09..1.531e+09, within 1 day of flow start: 0; median packets 2, median duration 0.0s
  wednesday_benign: bwd_bytes_rate n=3 range 1.469e+09..1.531e+09, within 1 day of flow start: 0; median packets 2, median duration 0.0s
  monday_benign: bytes_rate n=3 range 1.518e+09..1.823e+09, within 1 day of flow start: 0; median packets 2, median duration 0.0s
  monday_benign: bwd_bytes_rate n=2 range 1.598e+09..1.823e+09, within 1 day of flow start: 0; median packets 2, median duration 0.0s
  monday_benign: fwd_bytes_rate n=1 range 1.518e+09..1.518e+09, within 1 day of flow start: 0; median packets 3, median duration 0.0s
== BCCC-cPacket-Cloud-DDoS-2024
  Thursday_14_Dec_2023: total_payload_bytes n=5 range 1.473e+09..2.092e+09, within 1 day of flow start: 0; median packets 1245708, median duration 65.0s
  Thursday_14_Dec_2023: fwd_total_payload_bytes n=3 range 1.481e+09..1.683e+09, within 1 day of flow start: 0; median packets 1245708, median duration 65.0s
  Thursday_14_Dec_2023: bwd_total_payload_bytes n=2 range 1.473e+09..2.092e+09, within 1 day of flow start: 0; median packets 1457826, median duration 51.5s
  Thursday_14_Dec_2023: fwd_bulk_total_size n=3 range 1.481e+09..1.683e+09, within 1 day of flow start: 0; median packets 1245708, median duration 65.0s
  Saturday_16_Dec_2023: total_payload_bytes n=8 range 1.465e+09..2.189e+09, within 1 day of flow start: 0; median packets 1369476, median duration 93.7s
  Saturday_16_Dec_2023: fwd_total_payload_bytes n=2 range 1.465e+09..1.741e+09, within 1 day of flow start: 0; median packets 1270464, median duration 75.4s
  Saturday_16_Dec_2023: bwd_total_payload_bytes n=6 range 1.594e+09..2.189e+09, within 1 day of flow start: 0; median packets 1381042, median duration 126.7s
  Saturday_16_Dec_2023: fwd_bulk_total_size n=2 range 1.465e+09..1.74e+09, within 1 day of flow start: 0; median packets 1270464, median duration 75.4s
  Saturday_16_Dec_2023: bytes_rate n=1 range 1.735e+09..1.735e+09, within 1 day of flow start: 0; median packets 7, median duration 0.0s
  Saturday_16_Dec_2023: fwd_bytes_rate n=1 range 1.735e+09..1.735e+09, within 1 day of flow start: 0; median packets 7, median duration 0.0s
  Saturday_16_Dec_2023: bwd_bytes_rate n=1 range 1.518e+09..1.518e+09, within 1 day of flow start: 0; median packets 4, median duration 0.0s
  Saturday_16_Dec_2023: avg_fwd_bulk_rate n=2 range 1.46e+09..1.735e+09, within 1 day of flow start: 0; median packets 8, median duration 0.0s
  Monday_18_Dec_2023: total_payload_bytes n=4 range 1.579e+09..1.896e+09, within 1 day of flow start: 0; median packets 1415504, median duration 153.0s
  Monday_18_Dec_2023: bwd_total_payload_bytes n=4 range 1.579e+09..1.896e+09, within 1 day of flow start: 0; median packets 1415504, median duration 153.0s
  Tuesday_19_Dec_2023: total_payload_bytes n=2 range 1.967e+09..2.097e+09, within 1 day of flow start: 0; median packets 1642070, median duration 305.5s
  Tuesday_19_Dec_2023: bwd_total_payload_bytes n=2 range 1.967e+09..2.097e+09, within 1 day of flow start: 0; median packets 1642070, median duration 305.5s
```


### D9. Experiment 2 (2018): timestamp-only baseline

Source: `~/Desktop/ntl_exp23/results/exp2/SUMMARY.md`

### Experiment 2: timestamp-only baseline

Single feature t = smallest leaked IAT value in the row (0 if none).

| split | model | acc (all) | macro-F1 (all) | acc (leaked) | macro-F1 (leaked) | n test | n leaked |
|---|---|---|---|---|---|---|---|
| random | most_frequent | 0.5404 | 0.0780 | 0.5262 | 0.0766 | 1087225 | 398418 |
| random | stratified | 0.3598 | 0.1113 | 0.3648 | 0.1019 | 1087225 | 398418 |
| random | tree | 0.4153 | 0.3688 | 0.9517 | 0.5462 | 1087225 | 398418 |
| temporal | most_frequent | 0.5404 | 0.0780 | 0.5482 | 0.0787 | 1087223 | 359693 |
| temporal | stratified | 0.3600 | 0.1115 | 0.3678 | 0.1030 | 1087223 | 359693 |
| temporal | tree | 0.2687 | 0.1327 | 0.6109 | 0.1898 | 1087223 | 359693 |

Per-class recall (all test rows):

| split | model | Benign | Bot | Brute_Force_Web | Brute_Force_XSS | DDoS_HOIC | DDoS_LOIC_HTTP | DoS_HULK | DoS_SlowHTTP | SQL_Injection |
|---|---|---|---|---|---|---|---|---|---|---|
| random | most_frequent | 1.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 |
| random | stratified | 0.541 | 0.067 | 0.000 | 0.000 | 0.230 | 0.065 | 0.073 | 0.025 | 0.000 |
| random | tree | 0.324 | 0.500 | 0.463 | 0.293 | 0.502 | 0.999 | 0.011 | 1.000 | 0.269 |
| temporal | most_frequent | 1.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 |
| temporal | stratified | 0.540 | 0.067 | 0.000 | 0.000 | 0.231 | 0.067 | 0.073 | 0.025 | 0.000 |
| temporal | tree | 0.330 | 0.004 | 0.015 | 0.034 | 0.080 | 1.000 | 0.002 | 0.195 | 0.538 |


### D10. Experiment 2 on all three datasets: consistent table

Source: `~/Desktop/ntl_census_multi/exp2_consistent_table.txt`

```

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
```


### D11. Experiment 1: existing RF, timestamps changed

Source: `~/Desktop/ntl_exp1/RESULTS.md`

### Experiment 1: change only the leaked timestamps, re-score the existing RF

Model `~/trained_models/rf_model.onnx` (md5 19e98628...), `feature_order.json` (313 features, 30 IAT), test set
`ml_module_output/_intermediate/test_{X,y}.npy` (1,087,223 rows, 9 classes, temporally latest 25% per file).
Leaked cell = IAT column > 1e9. Modifications in float64 on the IAT block, cast to float32 for scoring.
Note: test_X was already float32 (pipeline read CSVs as float32), so timestamps were already on a 128 s grid;
+1d (86,400 s) and +8y (252,460,800 s) are exact multiples of 128, so no shift is lost to rounding.
Sanity check (non-leaked rows' predictions unchanged) passed in all 8 conditions.
Baseline 0.8919 on all rows; the earlier 0.8928 was on a 200k sample (IDS_MODELS_SUMMARY.txt:363).
Script `exp1.py`; full metrics, confusion matrices and transition matrices in `exp1_results.json`; predictions `pred_*.npy`.

#### Leaked test rows
359,693 of 1,087,223 (33.1%). Benign 197,191 (33.6%), Bot 35,830 (50.1%), HOIC 97,477 (39.0%), SlowHTTP 26,387 (100%),
HULK 2,698 (3.4%), Web 66, XSS 30, SQLi 14, LOIC 0.

#### Headline
| Condition | Acc all | Macro-F1 all | Acc leaked | Macro-F1 leaked | Predictions changed |
|---|---|---|---|---|---|
| Baseline | 0.8919 | 0.7560 | 0.6736 | 0.2995 | - |
| +8 years | 0.8749 | 0.7916 | 0.6220 | 0.2074 | 22,226 |
| +1 day | 0.8381 | 0.7346 | 0.5110 | 0.2065 | 121,075 |
| Shuffle (5 seeds) | 0.8763 ± 0.0000 | 0.7340 ± 0.0004 | 0.6264 ± 0.0001 | 0.2192 ± 0.0001 | 32,526 ± 68 |
| Zero (fixed data -> leaky model, NOT a retrain) | 0.8749 | 0.7916 | 0.6220 | 0.2074 | 22,226 |

#### Per-class recall (all rows) / precision
| Class | Base R | +8y R | +1d R | Shuffle R | Base P | +8y P | +1d P | Shuffle P |
|---|---|---|---|---|---|---|---|---|
| Benign | 0.9968 | 1.0000 | 0.9320 | 0.9933 | 0.8351 | 0.8120 | 0.8817 | 0.8211 |
| Bot | 0.5024 | 0.4981 | 0.4981 | 0.4986 | 1.0000 | 1.0000 | 1.0000 | 0.9965 |
| Brute_Force_Web | 0.5075 | 0.4925 | 0.4925 | 0.4925 | 0.9444 | 0.9429 | 0.9429 | 0.9270 |
| Brute_Force_XSS | 0.5862 | 0.4828 | 0.4828 | 0.4828 | 1.0000 | 1.0000 | 1.0000 | 0.9526 |
| DDoS_HOIC | 0.6903 | 0.6104 | 0.6104 | 0.6322 | 1.0000 | 1.0000 | 1.0000 | 0.9701 |
| DDoS_LOIC_HTTP | 1.0000 | 1.0000 | 1.0000 | 1.0000 | 1.0000 | 1.0000 | 1.0000 | 1.0000 |
| DoS_HULK | 0.9684 | 0.9676 | 0.9676 | 0.9676 | 1.0000 | 1.0000 | 1.0000 | 1.0000 |
| DoS_SlowHTTP | 1.0000 | 1.0000 | 1.0000 | 1.0000 | 0.9997 | 0.9997 | 0.9997 | 0.9997 |
| SQL_Injection | 0.9615 | 0.4231 | 0.9615 | 0.4231 | 0.0133 | 0.6875 | 0.0002 | 0.0047 |

#### Findings
1. Correct attack detections that exist only because of the timestamp: 20,381 leaked rows
   (HOIC 19,992, Bot 306, HULK 61, SQLi 14 of 26 test rows, XSS 6, Web 2). Under +8y/zero every one of them flips to Benign.
   HOIC recall 0.690 -> 0.610; SQLi recall 0.96 -> 0.42.
2. The leak also causes false positives: at baseline 1,845 leaked Benign rows are predicted SQL_Injection (SQLi precision 0.013).
   Removing the timestamp lifts SQLi precision to 0.69, which is why macro-F1 *rises* under +8y/zero.
3. +1 day is the most damaging condition: 100,689 Benign rows move to SQL_Injection. Shifting benign traffic by one day
   lands it in another day's attack window, so the model keys on the specific day and hour, not just "2018 vs not".
4. Shuffle (timestamps kept in range, class link broken): HOIC recall on leaked rows 0.205 -> 0.057, plus ~9,200
   Benign -> HOIC and ~2,100 Benign -> SQLi false positives.
5. +8y and zero give identical predictions: once a timestamp leaves the trained windows in either direction the trees
   fall back to Benign.
6. Controls behave as expected: LOIC (0 leaked rows) does not move, HULK moves by 61 rows. SlowHTTP is 100% leaked
   but stays at recall 1.0 in every condition, so it is identified by other features.
7. Important context: at baseline the model already misses most leaked attack rows (Bot leaked recall 0.0085,
   HOIC 0.205; 35,524 of 35,830 leaked Bot rows -> Benign). Because the test set is the latest 25% in time, its
   timestamps mostly fall outside the training windows, so this split already blunts the leak. The measured
   dependence is therefore a lower bound for this model; a random split would likely show far more. That is a
   hypothesis for experiments 2/3, not a result here.

#### Caveat
This measures how much this model depends on the timestamp, not what a model trained without the leak would score
(experiments 2 and 3).


### D12. Experiment 1b: KNN and ensemble

Source: `~/Desktop/ntl_exp1/RESULTS_exp1b.md`

### Experiment 1b: KNN and ensemble under timestamp-only changes (vs RF)

Same conditions as Experiment 1, scored with `knn_model.onnx` and `ensemble_model.onnx` (scaler is inside each graph;
raw features passed). ONNX KNN inference runs at ~4 rows/s on this machine (each query scans the 600k x 313 stored
training rows), so this uses a stratified sample: 20,001 test rows stratified by (class, leaked), with every
SQL_Injection (26), Brute_Force_XSS (58) and Brute_Force_Web (134) row; 6,654 leaked. A KNN/ensemble prediction depends
only on the row's own features, so per condition only the 6,654 leaked rows plus 200 random non-leaked sanity rows were
rescored; the sanity rows were unchanged in all 16 modified runs. Conditions were built on the full test set with
exp1.py's exact construction (same shuffle seeds and donors) and then subset, so the RF numbers are on identical inputs.
`acc_pw` / `mF1_pw` = population-weighted (weight = test class count / sample class count); the RF's pop-weighted sample
results reproduce its full-test results to within 0.001 (0.8930 vs 0.8919 baseline, 0.8750 vs 0.8749 +8y), so the sample is
representative. Each (model, condition) ran in a fresh process; peak memory stayed ~0.9 GB.
Scripts: exp1b_prepare.py, exp1b_score.py, exp1b_run.py, exp1b_report.py. Full output: exp1b/report.txt, exp1b/exp1b_results.json.

#### Accuracy (population-weighted) / accuracy on leaked rows

| Condition | RF | KNN | Ensemble |
|---|---|---|---|
| Baseline | 0.8930 / 0.669 | **0.9934 / 0.990** | **0.9934 / 0.991** |
| +8 years | 0.8750 / 0.612 | 0.8713 / 0.614 | 0.8714 / 0.614 |
| +1 day | 0.8384 / 0.506 | 0.9036 / 0.724 | 0.9036 / 0.722 |
| Shuffle (5 seeds) | 0.8764 ± 0.0006 / 0.617 | 0.9195 ± 0.0023 / 0.760 | 0.9192 ± 0.0023 / 0.756 |
| Zero (fixed data, leaky model) | 0.8750 / 0.612 | 0.8709 / 0.612 | 0.8709 / 0.612 |

Macro-F1 (pop-weighted), baseline -> +8y: RF 0.758 -> 0.799, KNN 0.908 -> 0.763, ensemble 0.953 -> 0.769.

#### Recall, baseline -> +8y (all sample rows)

| Class | RF | KNN | Ensemble |
|---|---|---|---|
| Bot | 0.502 -> 0.499 | 0.935 -> 0.446 | 0.933 -> 0.446 |
| DDoS_HOIC | 0.695 -> 0.610 | 1.000 -> 0.610 | 1.000 -> 0.610 |
| Brute_Force_Web | 0.508 -> 0.493 | 0.978 -> 0.485 | 0.918 -> 0.485 |
| Brute_Force_XSS | 0.586 -> 0.483 | 0.966 -> 0.483 | 0.966 -> 0.483 |
| SQL_Injection | 0.962 -> 0.423 | 0.192 -> 0.192 | 0.731 -> 0.231 |
| DoS_HULK | 0.969 -> 0.969 | 0.969 -> 0.969 | 0.969 -> 0.969 |
| DDoS_LOIC_HTTP | 1.000 -> 1.000 | 1.000 -> 1.000 | 1.000 -> 1.000 |
| DoS_SlowHTTP | 1.000 -> 1.000 | 1.000 -> 1.000 | 1.000 -> 1.000 |
| Benign | 0.997 -> 1.000 | 1.000 -> 1.000 | 1.000 -> 1.000 |

#### Findings
1. KNN and the ensemble owe their ~0.99 accuracy to the leaked timestamps. Moving the timestamps out of 2018 (+8y) or
   zeroing them drops both to 0.871, the same level as the RF (0.875). On leaked rows they fall from 0.99 to 0.61.
   The whole 0.89 -> 0.99 advantage over the RF disappears.
2. What is lost, per class (+8y): every leaked HOIC row (1,774 -> Benign; recall 1.00 -> 0.61), about half of Bot
   (0.93 -> 0.45), Web (0.98 -> 0.49) and XSS (0.97 -> 0.48). In each case recall falls to roughly the class's
   non-leaked share, i.e. those classes are detected only through the timestamp.
3. Why KNN depends on it more than the RF: after standard scaling, a leaked IAT (~1.5e9) dominates the Euclidean
   distance, so the nearest neighbours are the training flows closest in *time*, which come from the same capture
   window and so the same class. The temporal split does not protect KNN the way it partly protected the RF
   (Experiment 1): test timestamps lie just after the training window, and nearness still picks the right window,
   whereas the RF's fixed thresholds no longer fit.
4. +1 day: all 1,774 leaked HOIC rows (21 Feb, ~18:00-19:00 UTC) become Brute_Force_Web, the class captured on
   22 Feb; Brute_Force_Web precision collapses to 0.001. The models map time-of-capture to class.
5. Shuffle keeps timestamps in range but breaks the link: KNN/ensemble 0.993 -> 0.919, with new cross-class errors
   (Bot -> HOIC 311, HOIC -> Bot 226, Benign -> Web).
6. Controls behave: LOIC, SlowHTTP and Benign do not move; HULK loses 1 row.
7. SQL_Injection is anomalous for KNN: recall 0.19 at baseline, unchanged by every condition (only 26 rows; precision 1.0).

#### Caveat
As in Experiment 1, this measures how much these trained models depend on the timestamp, not what models trained without
the leak would score (Experiment 3).


### D13. Experiment 3 (2018): RF retrain, per-seed detail

Source: `~/Desktop/ntl_exp23/results/exp3/SUMMARY.md`

### Experiment 3: RF retrained with and without the leak

RandomForestClassifier(n_estimators=200, max_depth=30, min_samples_leaf=10, class_weight='balanced', n_jobs=2, random_state=seed), 313 features. Mean ± std over completed seeds.

fixA = leaked IAT cells set to 0 in train and test. fixB = fixA + rows with packets_count == 1 dropped (the test set shrinks too, so fixB is scored on a different row set).

**LEAK CHECK FLAGGED (split thresholds > 1e9 in a fixed model): ['random_fixA_s2: 1 (0 on IAT features)']**

**Of these, on IAT features: none.** The flagged thresholds are on non-IAT columns. The census column scan found genuine non-timestamp values above 1e9 only in avg_bwd_bulk_rate, avg_fwd_bulk_rate, bytes_rate, fwd/bwd_bytes_rate and variance_*_delta_len (implausible rates, not capture times), so these are not leaks.

#### All test rows

| split | variant | seeds | acc | macro-F1 | R Benign | R Bot | R Brute_Force_Web | R Brute_Force_XSS | R DDoS_HOIC | R DDoS_LOIC_HTTP | R DoS_HULK | R DoS_SlowHTTP | R SQL_Injection |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| temporal | leaky | 0,1,2,3 | 0.8919 ± 0.0000 | 0.7566 ± 0.0032 | 0.997 ± 0.000 | 0.502 ± 0.000 | 0.507 ± 0.000 | 0.603 ± 0.034 | 0.690 ± 0.000 | 1.000 ± 0.000 | 0.968 ± 0.000 | 1.000 ± 0.000 | 0.962 ± 0.000 |
| temporal | fixA | 0,1,2,3 | 0.9645 ± 0.0001 | 0.7770 ± 0.0100 | 0.999 ± 0.000 | 0.502 ± 0.002 | 0.978 ± 0.000 | 0.966 ± 0.000 | 1.000 ± 0.000 | 1.000 ± 0.000 | 0.968 ± 0.000 | 1.000 ± 0.000 | 0.615 ± 0.000 |
| temporal | fixB | 0,1,2,3 | 0.9991 ± 0.0000 | 0.9694 ± 0.0039 | 1.000 ± 0.000 | 0.993 ± 0.000 | 0.985 ± 0.017 | 1.000 ± 0.000 | 1.000 ± 0.000 | 0.999 ± 0.000 | 0.996 ± 0.000 | 1.000 ± 0.000 | 0.917 ± 0.000 |
| random | leaky | 0,1,2,3 | 0.9976 ± 0.0008 | 0.8229 ± 0.0010 | 0.996 ± 0.001 | 1.000 ± 0.000 | 0.993 ± 0.000 | 0.966 ± 0.000 | 1.000 ± 0.000 | 1.000 ± 0.000 | 1.000 ± 0.000 | 1.000 ± 0.000 | 0.894 ± 0.019 |
| random | fixA | 0,1,2,3 | 0.9533 ± 0.0020 | 0.7635 ± 0.0225 | 0.974 ± 0.004 | 0.503 ± 0.000 | 0.978 ± 0.000 | 0.966 ± 0.000 | 1.000 ± 0.000 | 0.999 ± 0.000 | 0.998 ± 0.000 | 1.000 ± 0.000 | 0.731 ± 0.000 |
| random | fixB | 0,1,2,3 | 1.0000 ± 0.0000 | 0.9859 ± 0.0006 | 1.000 ± 0.000 | 1.000 ± 0.000 | 1.000 ± 0.000 | 0.972 ± 0.000 | 1.000 ± 0.000 | 1.000 ± 0.000 | 1.000 ± 0.000 | 1.000 ± 0.000 | 0.933 ± 0.000 |

#### Leaked test rows (rows leaked in the unmodified data)

| split | variant | seeds | acc | macro-F1 | R Benign | R Bot | R Brute_Force_Web | R Brute_Force_XSS | R DDoS_HOIC | R DDoS_LOIC_HTTP | R DoS_HULK | R DoS_SlowHTTP | R SQL_Injection |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| temporal | leaky | 4 | 0.6736 ± 0.0000 | 0.3041 ± 0.0092 | 0.991 ± 0.000 | 0.009 ± 0.000 | 0.030 ± 0.000 | 0.233 ± 0.067 | 0.205 ± 0.000 | - | 0.088 ± 0.000 | 1.000 ± 0.000 | 1.000 ± 0.000 |
| temporal | fixA | 4 | 0.8933 ± 0.0001 | 0.4432 ± 0.0097 | 0.998 ± 0.000 | 0.010 ± 0.000 | 0.955 ± 0.000 | 0.933 ± 0.000 | 1.000 ± 0.000 | - | 0.066 ± 0.000 | 1.000 ± 0.000 | 0.357 ± 0.000 |
| temporal | fixB | 4 | 0.9895 ± 0.0000 | 0.2809 ± 0.0000 | 1.000 ± 0.000 | 0.000 ± 0.000 | - | - | - | - | 0.370 ± 0.000 | 1.000 ± 0.000 | - |
| random | leaky | 4 | 0.9935 ± 0.0021 | 0.7265 ± 0.0013 | 0.988 ± 0.004 | 1.000 ± 0.000 | 0.984 ± 0.000 | 0.955 ± 0.000 | 1.000 ± 0.000 | 0.900 ± 0.000 | 0.994 ± 0.000 | 1.000 ± 0.000 | 0.818 ± 0.000 |
| random | fixA | 4 | 0.8727 ± 0.0055 | 0.5075 ± 0.0306 | 0.929 ± 0.010 | 0.007 ± 0.000 | 0.952 ± 0.000 | 0.955 ± 0.000 | 1.000 ± 0.000 | 0.000 ± 0.000 | 0.825 ± 0.000 | 1.000 ± 0.000 | 0.455 ± 0.000 |
| random | fixB | 4 | 0.9998 ± 0.0000 | 0.4432 ± 0.0000 | 1.000 ± 0.000 | 0.983 ± 0.000 | - | - | - | - | 1.000 ± 0.000 | 1.000 ± 0.000 | - |

#### Rare classes: exact counts (correct / support per seed, all test rows)

| split | variant | SQL_Injection | Brute_Force_XSS | Brute_Force_Web |
|---|---|---|---|---|
| temporal | leaky | 25/26, 25/26, 25/26, 25/26 | 34/58, 38/58, 34/58, 34/58 | 68/134, 68/134, 68/134, 68/134 |
| temporal | fixA | 16/26, 16/26, 16/26, 16/26 | 56/58, 56/58, 56/58, 56/58 | 131/134, 131/134, 131/134, 131/134 |
| temporal | fixB | 11/12, 11/12, 11/12, 11/12 | 28/28, 28/28, 28/28, 28/28 | 68/68, 66/68, 66/68, 68/68 |
| random | leaky | 24/26, 23/26, 23/26, 23/26 | 56/58, 56/58, 56/58, 56/58 | 133/134, 133/134, 133/134, 133/134 |
| random | fixA | 19/26, 19/26, 19/26, 19/26 | 56/58, 56/58, 56/58, 56/58 | 131/134, 131/134, 131/134, 131/134 |
| random | fixB | 14/15, 14/15, 14/15, 14/15 | 35/36, 35/36, 35/36, 35/36 | 72/72, 72/72, 72/72, 72/72 |

#### Differences (mean leaky − mean fixed)

| split | comparison | Δ acc | Δ macro-F1 | Δ R Benign | Δ R Bot | Δ R Brute_Force_Web | Δ R Brute_Force_XSS | Δ R DDoS_HOIC | Δ R DDoS_LOIC_HTTP | Δ R DoS_HULK | Δ R DoS_SlowHTTP | Δ R SQL_Injection |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| temporal | leaky − fixA | -0.0726 | -0.0204 | -0.003 | +0.001 | -0.470 | -0.362 | -0.310 | -0.000 | +0.001 | +0.000 | +0.346 |
| temporal | leaky − fixB | -0.1072 | -0.2128 | -0.003 | -0.490 | -0.478 | -0.397 | -0.310 | +0.001 | -0.027 | +0.000 | +0.045 |
| random | leaky − fixA | +0.0443 | +0.0593 | +0.021 | +0.497 | +0.015 | +0.000 | +0.000 | +0.001 | +0.002 | +0.000 | +0.163 |
| random | leaky − fixB | -0.0024 | -0.1630 | -0.004 | +0.000 | -0.007 | -0.007 | +0.000 | -0.000 | -0.000 | +0.000 | -0.039 |

#### Runs

| run | n train | n test | fit s | peak RSS GB | thresholds > 1e9 (on IAT) |
|---|---|---|---|---|---|
| random_fixA_s0 | 3261673 | 1087225 | 1143 | 6.54 | 0 (0) |
| random_fixA_s1 | 3261673 | 1087225 | 1148 | 6.68 | 0 (0) |
| random_fixA_s2 | 3261673 | 1087225 | 1203 | 6.63 | 1 (0) |
| random_fixA_s3 | 3261673 | 1087225 | 1198 | 6.02 | 0 (0) |
| random_fixB_s0 | 2216899 | 738622 | 737 | 5.78 | 0 (0) |
| random_fixB_s1 | 2216899 | 738622 | 748 | 5.86 | 0 (0) |
| random_fixB_s2 | 2216899 | 738622 | 744 | 5.65 | 0 (0) |
| random_fixB_s3 | 2216899 | 738622 | 767 | 5.85 | 0 (0) |
| random_leaky_s0 | 3261673 | 1087225 | 1144 | 6.43 | 22657 (22657) |
| random_leaky_s1 | 3261673 | 1087225 | 1192 | 6.59 | 21525 (21525) |
| random_leaky_s2 | 3261673 | 1087225 | 1204 | 6.59 | 21506 (21506) |
| random_leaky_s3 | 3261673 | 1087225 | 1233 | 5.96 | 22174 (22174) |
| temporal_fixA_s0 | 3261675 | 1087223 | 1096 | 6.42 | 0 (0) |
| temporal_fixA_s1 | 3261675 | 1087223 | 1081 | 6.52 | 0 (0) |
| temporal_fixA_s2 | 3261675 | 1087223 | 1100 | 6.43 | 0 (0) |
| temporal_fixA_s3 | 3261675 | 1087223 | 1125 | 6.01 | 0 (0) |
| temporal_fixB_s0 | 2179323 | 776198 | 729 | 5.30 | 0 (0) |
| temporal_fixB_s1 | 2179323 | 776198 | 712 | 5.86 | 0 (0) |
| temporal_fixB_s2 | 2179323 | 776198 | 718 | 5.81 | 0 (0) |
| temporal_fixB_s3 | 2179323 | 776198 | 736 | 5.86 | 0 (0) |
| temporal_leaky_s0 | 3261675 | 1087223 | 1167 | 6.17 | 17741 (17741) |
| temporal_leaky_s1 | 3261675 | 1087223 | 1165 | 6.52 | 17904 (17904) |
| temporal_leaky_s2 | 3261675 | 1087223 | 1185 | 6.53 | 19363 (19363) |
| temporal_leaky_s3 | 3261675 | 1087223 | 1182 | 5.85 | 17448 (17448) |


### D14. Experiment 3 addendum: same rows

Source: `~/Desktop/ntl_exp23/results/exp3/same_rows_analysis.md`

### Addendum: all variants scored on the same rows (seeds 0-2)

fixB drops `packets_count == 1` rows from the test set too, so "leaky − fixB" in SUMMARY.md compares different row sets.
Here leaky and fixA predictions (saved per run in runs/*.pred.npy) are restricted to the multi-packet test rows that fixB keeps.

| split | multi-packet test rows (of which leaked) | leaky acc / macro-F1 | fixA acc / macro-F1 | fixB acc / macro-F1 |
|---|---|---|---|---|
| temporal | 776,198 of 1,087,223 (48,668) | 0.9992 / 0.966 | 0.9991 / 0.967 | 0.9991 / 0.968 |
| random | 738,622 of 1,087,225 (49,815) | 1.0000 / 0.990 | 1.0000 / 0.981 | 1.0000 / 0.986 |

On multi-packet flows the three variants are indistinguishable (Bot recall 0.99-1.00 everywhere). The whole effect of the
leak, inflation on the random split (+4.4 pts) and deflation on the temporal split (-7.3 pts), sits in the 1-packet
(ghost-type) rows, which are ~29-32% of the test set. Leaked multi-packet rows (~49k per split, the "leak beyond
ghosts") do not measurably change these models' accuracy. Half of the rare-class test rows are 1-packet flows
(fixB keeps SQLi 12/26 and 15/26, XSS 28/58 and 36/58, Web 68/134 and 72/134 for temporal/random).
Computed ad hoc from the saved predictions; not part of the spec'd outputs.


---

# E. Data-file index

Every result file of the project. Folders of many per-run or per-file outputs are summarised by count. CSV row counts exclude the header. Paths are relative to `~/Desktop/` unless absolute.


## Step 1 reproducer: `ntl_repro_step1/`

| file | size | CSV rows |
|---|---:|---:|
| `ntl_repro_step1/RESULTS.md` | 3 KB |  |
| `ntl_repro_step1/env.txt` | 0 KB |  |
| `ntl_repro_step1/repro.pcap` | 2 KB |  |
| `ntl_repro_step1/repro.pcap.sha256` | 0 KB |  |
| `ntl_repro_step1/repro_config.json` | 0 KB |  |
| `ntl_repro_step1/repro_config_fork.json` | 0 KB |  |
| `ntl_repro_step1/repro_out.csv` | 19 KB | 6 |
| `ntl_repro_step1/repro_out_fork.csv` | 19 KB | 6 |
| `ntl_repro_step1/run.log` | 2 KB |  |
| `ntl_repro_step1/run_fork.log` | 2 KB |  |

## Census 2018: `ntl_census_step2/`

| file | size | CSV rows |
|---|---:|---:|
| `ntl_census_step2/RESULTS.md` | 4 KB |  |
| `ntl_census_step2/file_list.txt` | 3 KB |  |
| `ntl_census_step2/out/column_scan.csv` | 1 KB | 25 |
| `ntl_census_step2/out/file_list.txt` | 3 KB |  |
| `ntl_census_step2/out/fwd_leak_offset_vs_timestamp.csv` | 3 KB | 32 |
| `ntl_census_step2/out/leak_date_ranges.csv` | 6 KB | 34 |
| `ntl_census_step2/out/leak_hours.csv` | 16 KB | 288 |
| `ntl_census_step2/out/non_numeric_samples.json` | 3 KB |  |
| `ntl_census_step2/out/per_class.csv` | 2 KB | 15 |
| `ntl_census_step2/out/per_file.csv` | 5 KB | 34 |
| `ntl_census_step2/out/report.txt` | 20 KB |  |
| `ntl_census_step2/out/run.log` | 1 KB |  |
| `ntl_census_step2/out/parts/` (34 × .json) | 324 KB | |

## Experiment 1 / 1b (existing models): `ntl_exp1/`

| file | size | CSV rows |
|---|---:|---:|
| `ntl_exp1/` (1 × .json, 1 × .log, 2 × .md, 9 × .npy, 5 × .py, 1 × .sh) | 78.4 MB | |
| `ntl_exp1/exp1b/` (19 × .json, 2 × .log, 28 × .npy, 1 × .npz, 19 × .txt) | 95.5 MB | |

## Experiments 2-3 (2018): `ntl_exp23/`

| file | size | CSV rows |
|---|---:|---:|
| `ntl_exp23/build_train.log` | 0 KB |  |
| `ntl_exp23/results_queue.log` | 5 KB |  |
| `ntl_exp23/exp3/random_split_idx.npz` | 34.8 MB |  |
| `ntl_exp23/results/QUEUE_STATUS.txt` | 5 KB |  |
| `ntl_exp23/results/exp2/SUMMARY.md` | 2 KB |  |
| `ntl_exp23/results/exp2/random_most_frequent.json` | 4 KB |  |
| `ntl_exp23/results/exp2/random_stratified.json` | 5 KB |  |
| `ntl_exp23/results/exp2/random_tree.json` | 5 KB |  |
| `ntl_exp23/results/exp2/random_tree_unweighted.json` | 5 KB |  |
| `ntl_exp23/results/exp2/temporal_most_frequent.json` | 4 KB |  |
| `ntl_exp23/results/exp2/temporal_stratified.json` | 5 KB |  |
| `ntl_exp23/results/exp2/temporal_tree.json` | 5 KB |  |
| `ntl_exp23/results/exp2/temporal_tree_unweighted.json` | 5 KB |  |
| `ntl_exp23/results/exp3/SUMMARY.md` | 7 KB |  |
| `ntl_exp23/results/exp3/same_rows_analysis.md` | 1 KB |  |
| `ntl_exp23/results/exp3/excluded_seed4/temporal_fixA_s4.json` | 7 KB |  |
| `ntl_exp23/results/exp3/excluded_seed4/temporal_fixA_s4.pred.npy` | 8.7 MB |  |
| `ntl_exp23/results/exp3/excluded_seed4/temporal_fixA_s4.worker.json` | 7 KB |  |
| `ntl_exp23/results/exp3/excluded_seed4/temporal_leaky_s4.json` | 7 KB |  |
| `ntl_exp23/results/exp3/excluded_seed4/temporal_leaky_s4.pred.npy` | 8.7 MB |  |
| `ntl_exp23/results/exp3/excluded_seed4/temporal_leaky_s4.worker.json` | 7 KB |  |
| `ntl_exp23/results/exp3/runs/` (48 × .json, 24 × .npy) | 188.0 MB | |
| `ntl_exp23/results/logs/` (34 × .log, 34 × .txt) | 32 KB | |

## Census, flow shapes, experiment 2 and 2017 retrain on other datasets: `ntl_census_multi/`

| file | size | CSV rows |
|---|---:|---:|
| `ntl_census_multi/` (2 × .log, 1 × .md, 7 × .py, 1 × .sh, 2 × .txt) | 59 KB | |
| `ntl_census_multi/BCCC-CIC-IDS-2017/LEAK_SHAPES.md` | 4 KB |  |
| `ntl_census_multi/BCCC-CIC-IDS-2017/RESULTS.md` | 13 KB |  |
| `ntl_census_multi/BCCC-CIC-IDS-2017/combined_row.json` | 0 KB |  |
| `ntl_census_multi/BCCC-CIC-IDS-2017/file_list.txt` | 1 KB |  |
| `ntl_census_multi/BCCC-CIC-IDS-2017/flow_shapes.csv` | 6 KB | 103 |
| `ntl_census_multi/BCCC-CIC-IDS-2017/leak_calendar.csv` | 2 KB | 18 |
| `ntl_census_multi/BCCC-CIC-IDS-2017/leak_shapes_counts.csv` | 1 KB | 15 |
| `ntl_census_multi/BCCC-CIC-IDS-2017/leak_shapes_share_of_leaked.csv` | 1 KB | 15 |
| `ntl_census_multi/BCCC-CIC-IDS-2017/per_class.csv` | 1 KB | 15 |
| `ntl_census_multi/BCCC-CIC-IDS-2017/per_file.csv` | 2 KB | 18 |
| `ntl_census_multi/BCCC-CIC-IDS-2017/exp2_label/random_most_frequent.json` | 6 KB |  |
| `ntl_census_multi/BCCC-CIC-IDS-2017/exp2_label/random_stratified.json` | 7 KB |  |
| `ntl_census_multi/BCCC-CIC-IDS-2017/exp2_label/random_tree.json` | 7 KB |  |
| `ntl_census_multi/BCCC-CIC-IDS-2017/exp2_label/random_tree_unweighted.json` | 6 KB |  |
| `ntl_census_multi/BCCC-CIC-IDS-2017/exp2_label/splits.npz` | 39.0 MB |  |
| `ntl_census_multi/BCCC-CIC-IDS-2017/exp2_label/summary.json` | 1 KB |  |
| `ntl_census_multi/BCCC-CIC-IDS-2017/exp2_label/temporal_most_frequent.json` | 6 KB |  |
| `ntl_census_multi/BCCC-CIC-IDS-2017/exp2_label/temporal_stratified.json` | 7 KB |  |
| `ntl_census_multi/BCCC-CIC-IDS-2017/exp2_label/temporal_tree.json` | 7 KB |  |
| `ntl_census_multi/BCCC-CIC-IDS-2017/exp2_label/temporal_tree_unweighted.json` | 6 KB |  |
| `ntl_census_multi/BCCC-CIC-IDS-2017/exp3/` (6 × .json, 1 × .md, 6 × .npy) | 27.2 MB | |
| `ntl_census_multi/BCCC-CIC-IDS-2017/exp3/logs/` (6 × .log, 7 × .txt) | 6 KB | |
| `ntl_census_multi/BCCC-CIC-IDS-2017/parts/` (18 × .json) | 81 KB | |
| `ntl_census_multi/BCCC-DLLayer-IDS-2025/RESULTS.md` | 2 KB |  |
| `ntl_census_multi/BCCC-DLLayer-IDS-2025/epoch_scan_STP.txt` | 4 KB |  |
| `ntl_census_multi/BCCC-cPacket-Cloud-DDoS-2024/LEAK_SHAPES.md` | 7 KB |  |
| `ntl_census_multi/BCCC-cPacket-Cloud-DDoS-2024/RESULTS.md` | 13 KB |  |
| `ntl_census_multi/BCCC-cPacket-Cloud-DDoS-2024/combined_row.json` | 0 KB |  |
| `ntl_census_multi/BCCC-cPacket-Cloud-DDoS-2024/file_list.txt` | 0 KB |  |
| `ntl_census_multi/BCCC-cPacket-Cloud-DDoS-2024/leak_calendar.csv` | 6 KB | 51 |
| `ntl_census_multi/BCCC-cPacket-Cloud-DDoS-2024/leak_shapes_counts.csv` | 2 KB | 27 |
| `ntl_census_multi/BCCC-cPacket-Cloud-DDoS-2024/leak_shapes_share_of_leaked.csv` | 3 KB | 27 |
| `ntl_census_multi/BCCC-cPacket-Cloud-DDoS-2024/per_class.csv` | 3 KB | 27 |
| `ntl_census_multi/BCCC-cPacket-Cloud-DDoS-2024/per_file.csv` | 6 KB | 51 |
| `ntl_census_multi/BCCC-cPacket-Cloud-DDoS-2024/exp2_activity/random_most_frequent.json` | 16 KB |  |
| `ntl_census_multi/BCCC-cPacket-Cloud-DDoS-2024/exp2_activity/random_stratified.json` | 18 KB |  |
| `ntl_census_multi/BCCC-cPacket-Cloud-DDoS-2024/exp2_activity/random_tree.json` | 18 KB |  |
| `ntl_census_multi/BCCC-cPacket-Cloud-DDoS-2024/exp2_activity/random_tree_unweighted.json` | 17 KB |  |
| `ntl_census_multi/BCCC-cPacket-Cloud-DDoS-2024/exp2_activity/splits.npz` | 11.2 MB |  |
| `ntl_census_multi/BCCC-cPacket-Cloud-DDoS-2024/exp2_activity/summary.json` | 2 KB |  |
| `ntl_census_multi/BCCC-cPacket-Cloud-DDoS-2024/exp2_activity/temporal_most_frequent.json` | 16 KB |  |
| `ntl_census_multi/BCCC-cPacket-Cloud-DDoS-2024/exp2_activity/temporal_stratified.json` | 18 KB |  |
| `ntl_census_multi/BCCC-cPacket-Cloud-DDoS-2024/exp2_activity/temporal_tree.json` | 17 KB |  |
| `ntl_census_multi/BCCC-cPacket-Cloud-DDoS-2024/exp2_activity/temporal_tree_unweighted.json` | 16 KB |  |
| `ntl_census_multi/BCCC-cPacket-Cloud-DDoS-2024/exp2_label/random_most_frequent.json` | 1 KB |  |
| `ntl_census_multi/BCCC-cPacket-Cloud-DDoS-2024/exp2_label/random_stratified.json` | 1 KB |  |
| `ntl_census_multi/BCCC-cPacket-Cloud-DDoS-2024/exp2_label/random_tree.json` | 1 KB |  |
| `ntl_census_multi/BCCC-cPacket-Cloud-DDoS-2024/exp2_label/random_tree_unweighted.json` | 1 KB |  |
| `ntl_census_multi/BCCC-cPacket-Cloud-DDoS-2024/exp2_label/splits.npz` | 11.2 MB |  |
| `ntl_census_multi/BCCC-cPacket-Cloud-DDoS-2024/exp2_label/summary.json` | 1 KB |  |
| `ntl_census_multi/BCCC-cPacket-Cloud-DDoS-2024/exp2_label/temporal_most_frequent.json` | 1 KB |  |
| `ntl_census_multi/BCCC-cPacket-Cloud-DDoS-2024/exp2_label/temporal_stratified.json` | 1 KB |  |
| `ntl_census_multi/BCCC-cPacket-Cloud-DDoS-2024/exp2_label/temporal_tree.json` | 1 KB |  |
| `ntl_census_multi/BCCC-cPacket-Cloud-DDoS-2024/exp2_label/temporal_tree_unweighted.json` | 1 KB |  |
| `ntl_census_multi/BCCC-cPacket-Cloud-DDoS-2024/parts/` (4 × .json) | 36 KB | |

## Section 12 model comparison: `ntl_models/`

| file | size | CSV rows |
|---|---:|---:|
| `ntl_models/` (2 × .bak, 4 × .bak2, 3 × .bak3, 4 × .bak4, 6 × .py, 4 × .sh) | 147 KB | |
| `ntl_models/results/ALL_RUNS_pooled.csv` | 2.5 MB | 7,472 |
| `ntl_models/results/ASSIGNED_ELSEWHERE.txt` | 0 KB |  |
| `ntl_models/results/BOOTSTRAP_CI.csv` | 333 KB | 2,652 |
| `ntl_models/results/QUEUE_STATUS.txt` | 19 KB |  |
| `ntl_models/results/QUEUE_STATUS_laptop.txt` | 12 KB |  |
| `ntl_models/results/SUMMARY.md` | 37 KB |  |
| `ntl_models/results/ZERO_CHECK.json` | 10 KB |  |
| `ntl_models/results/bootstrap/` (46 × .json) | 432 KB | |
| `ntl_models/results/logs/` (138 × .log, 134 × .txt) | 127 KB | |
| `ntl_models/results/runs/` (132 × .json, 132 × .npz) | 24.8 MB | |
| `ntl_models/results/subsamples/cpacket_random.json` | 1 KB |  |
| `ntl_models/results/subsamples/cpacket_random.npz` | 4.2 MB |  |
| `ntl_models/results/subsamples/cpacket_temporal.json` | 1 KB |  |
| `ntl_models/results/subsamples/cpacket_temporal.npz` | 4.2 MB |  |
| `ntl_models/results/subsamples/d2017_random.json` | 0 KB |  |
| `ntl_models/results/subsamples/d2017_random.npz` | 4.8 MB |  |
| `ntl_models/results/subsamples/d2017_temporal.json` | 0 KB |  |
| `ntl_models/results/subsamples/d2017_temporal.npz` | 4.8 MB |  |
| `ntl_models/results/subsamples/d2018_random.json` | 0 KB |  |
| `ntl_models/results/subsamples/d2018_random.npz` | 4.8 MB |  |
| `ntl_models/results/subsamples/d2018_temporal.json` | 0 KB |  |
| `ntl_models/results/subsamples/d2018_temporal.npz` | 4.8 MB |  |

## Large arrays on the data drive

- 2018 model-comparison matrices: `~/pew2/ntl_models_cache/` (contiguous train/test .npy per split, ~4 GB).
- 2018 source arrays: `<drive>/Dataset/ml_module_output/_intermediate` (train/test .npy, used by experiments 1-3).
- 2017 / cPacket feature caches: `ntl_census_multi/<dataset>/cache/` and `.../exp3/cache/` (X.npy + meta).

Not part of this project: `~/pew2/unsw_nb15_ntl/` (an NTLFlowLyzer extraction of UNSW-NB15 from 2026-09-11 with model predictions; no leak analysis was run on it).


---

# F. Literature screen

OpenAlex full-text search on 2026-10-03 for the exact names BCCC-cPacket-Cloud-DDoS-2024, BCCC-CIC-IDS2017, BCCC-CIC-IDS-2017 and BCCC-CSE-CIC-IDS2018. A work is **counted** only if its abstract states experiments on a BCCC dataset (automated screening of OpenAlex abstracts, spot-checked by hand). No study was reproduced. Counted: 20; excluded: 20; source papers: 3. File: `NTL_leak_research/07_literature/literature_screen.csv`.


## Counted

| title | year | dataset | DOI | abstract-reported result / reason |
|---|---|---|---|---|
| LLM-Based Cyberattack Detection Using Network Flow Statistics | 2025 | BCCC-CIC-IDS-2017 | [10.3390/app15126529](https://doi.org/10.3390/app15126529) | all metrics > 99.90% (spot-checked) |
| Z-Shield: A Lightweight Hybrid Browser-Based Intrusion Detection Framework Using Hybrid Machine Learning | 2026 | BCCC-CSE-CIC-IDS2018 | [10.51584/ijrias.2026.11070014](https://doi.org/10.51584/ijrias.2026.11070014) | 99.13% accuracy; 99.58% F1 (spot-checked) |
| A Two-Stage Hybrid Intrusion Detection Framework Based on Hierarchical Attack Mapping and Pruned CNN-GRU Models | 2026 | BCCC-cPacket-Cloud-DDoS-2024 | [10.48084/etasr.16210](https://doi.org/10.48084/etasr.16210) | up to 99.99% accuracy |
| DDoS Detection Framework Using Machine Learning Optimized by Bayesian and PSO Techniques | 2026 | BCCC-cPacket-Cloud-DDoS-2024 | [10.59796/jcst.v16n3.2026.204](https://doi.org/10.59796/jcst.v16n3.2026.204) | 99.29% accuracy; 98.91% F1 |
| SCDF-CNN-BiGRU: A Spatial-Contextual Dual Feature Fusion Framework for Multi dataset Hierarchical Network Intrusion Detection | 2026 | BCCC-cPacket-Cloud-DDoS-2024 | [10.31026/j.eng.2026.09.12](https://doi.org/10.31026/j.eng.2026.09.12) | up to 0.999 accuracy |
| Harnessing PU Learning for Enhanced Cloud-based DDoS Detection: A Comparative Analysis | 2024 | BCCC-cPacket-Cloud-DDoS-2024 | [10.48550/arxiv.2410.18380](https://doi.org/10.48550/arxiv.2410.18380) | F1 > 98% (XGBoost; RF) (spot-checked on arXiv) |
| Scalable and Automated Detection of Cloud-Based DDoS Attacks Using AutoML-Random Forests | 2026 | BCCC-cPacket-Cloud-DDoS-2024 | [10.14445/23488549/ijece-v13i4p124](https://doi.org/10.14445/23488549/ijece-v13i4p124) | ~98% accuracy |
| DDoS Detection Using a Hybrid CNN-RNN Model Enhanced with Multi-Head Attention for Cloud Infrastructure | 2025 | BCCC-cPacket-Cloud-DDoS-2024 | [10.3390/app152111567](https://doi.org/10.3390/app152111567) | 97.78% accuracy |
| Dynamic Decision Boundary Calibration via Nelder-Mead Optimization in a Parallel CNN-BiLSTM Spatial-Temporal Hybrid Architecture for Robust DDoS Mitigation | 2026 | BCCC-cPacket-Cloud-DDoS-2024 | [10.51483/ijaiml.6.10s.2026.1874-1896](https://doi.org/10.51483/ijaiml.6.10s.2026.1874-1896) | 95-97% accuracy (k-fold) |
| Real-Time Network Health Monitoring in an Openstack Based Cloud Environment | 2025 | BCCC-cPacket-Cloud-DDoS-2024 | [10.1109/iconecct67014.2025.11470261](https://doi.org/10.1109/iconecct67014.2025.11470261) | 94.84% accuracy |
| Optimized Random Forest-Based Soft Computing Pipeline for Multi-Class DDoS Detection in Cloud Environments | 2026 | BCCC-cPacket-Cloud-DDoS-2024 | [10.1109/ickecs70176.2026.11527811](https://doi.org/10.1109/ickecs70176.2026.11527811) | 94.52% accuracy |
| Fortifying Firewalls Against Evolving DDoS Attacks with Contrastive AI and LLMs | 2026 | BCCC-cPacket-Cloud-DDoS-2024 | [10.5281/zenodo.21387306](https://doi.org/10.5281/zenodo.21387306) | 93.5% F1 |
| Feature-Selected Machine Learning and Deep Learning Framework for Cloud-Based DDoS Attack Detection | 2026 | BCCC-cPacket-Cloud-DDoS-2024 | [10.32628/ijsrst26131163](https://doi.org/10.32628/ijsrst26131163) | 87.4% accuracy (stratified split) |
| Optimising DDoS Attack Detection Over Cloud | 2026 | BCCC-cPacket-Cloud-DDoS-2024 | [10.1109/icass69550.2026.11547587](https://doi.org/10.1109/icass69550.2026.11547587) | not stated as accuracy |
| Two-Stage FWSC-Based Feature Selection Model for DDoS Detection | 2026 | BCCC-cPacket-Cloud-DDoS-2024 | [10.62527/joiv.10.3.5572](https://doi.org/10.62527/joiv.10.3.5572) | not stated |
| Scalable Enhancement of Cloud-Based DDoS Detection with Adaptive ML Pipelines | 2025 | BCCC-cPacket-Cloud-DDoS-2024 | [10.36227/techrxiv.175037203.37181551/v1](https://doi.org/10.36227/techrxiv.175037203.37181551/v1) | not stated |
| A Comparative Study of Intrusion Detection Performance on CIC-IDS-2017 and BCCC-CIC-IDS-2017 | 2026 | BCCC-CIC-IDS-2017 | [10.1109/ids69480.2026.00027](https://doi.org/10.1109/ids69480.2026.00027) | not stated |
| ARTEMIS: Adaptive Reweighing for Transferable Evasion via Meta-learning in Zero-Query Network Intrusion Detection Systems | 2025 | BCCC-CIC-IDS2017 / BCCC-CSE-CIC-IDS2018 | [10.1109/icnp65844.2025.11192405](https://doi.org/10.1109/icnp65844.2025.11192405) | not stated |
| Evaluating deep learning and traditional machine learning approaches for network intrusion detection | 2026 | BCCC-CIC-IDS-2017 | [10.14457/tu.the.2025.519](https://doi.org/10.14457/tu.the.2025.519) | not stated |
| Automatic cyberattack management system | 2026 | BCCC-CIC-IDS-2017 |  | 99.90% |

## Excluded

| title | year | dataset | DOI | abstract-reported result / reason |
|---|---|---|---|---|
| DDoS classification of network traffic in software defined networking SDN using a hybrid convolutional and gated recurrent neural network | 2025 |  | [10.1038/s41598-025-13754-1](https://doi.org/10.1038/s41598-025-13754-1) | abstract names no BCCC dataset (spot-checked) |
| Understanding employee cybersecurity behavior: The role of information security policies organizational culture and theory | 2026 | BCCC-CIC-IDS2017 | [10.55214/2576-8484.v10i3.12340](https://doi.org/10.55214/2576-8484.v10i3.12340) | not an ML study (n = 579 secondary analysis) |
| DDoSBERT: Fine-tuning variant text classification bidirectional encoder representations from transformers for DDoS detection | 2025 | BCCC-cPacket-Cloud-DDoS-2024 (full text) | [10.1016/j.comnet.2025.111150](https://doi.org/10.1016/j.comnet.2025.111150) | abstract does not state use |
| Detection and mitigation of TCP-based DDoS attacks in cloud environments using a self-attention and intersample attention transformer model | 2025 | BCCC-cPacket-Cloud-DDoS-2024 (full text) | [10.1007/s11227-025-06940-5](https://doi.org/10.1007/s11227-025-06940-5) | no abstract available |
| Advanced Intrusion Detection Systems: A Comparative Study of Deep Learning and Ensemble Learning Models for IIoT Networks | 2026 | BCCC-cPacket-Cloud-DDoS-2024 (full text) | [10.1007/978-3-032-03695-7_2](https://doi.org/10.1007/978-3-032-03695-7_2) | no abstract available |
| Towards Secure Microservices in 6G Multi-Connectivity Networks: Graph-Aware Anomaly Detection Against DoS Attacks | 2025 | BCCC-cPacket-Cloud-DDoS-2024 (full text) | [10.1109/wpmc67460.2025.11351198](https://doi.org/10.1109/wpmc67460.2025.11351198) | abstract does not state use |
| Adaptive Intrusion Detection Systems: Leveraging Meta-Learning for Improved Cybersecurity | 2026 | BCCC-cPacket-Cloud-DDoS-2024 (full text) | [10.1109/tnsm.2026.3706597](https://doi.org/10.1109/tnsm.2026.3706597) | abstract does not state use |
| Graph Neural Network-Based DDoS Protection for Data Center Infrastructure | 2026 | BCCC-cPacket-Cloud-DDoS-2024 (full text) | [10.48550/arxiv.2603.13694](https://doi.org/10.48550/arxiv.2603.13694) | abstract does not state use |
| Analysis and Visualization of Cloud Native Attacks in a Secure Testbed | 2026 | BCCC-cPacket-Cloud-DDoS-2024 (full text) | [10.5121/ijcnc.2026.18206](https://doi.org/10.5121/ijcnc.2026.18206) | abstract does not state use |
| Transaction Intent Graph: Semantic Cross-Layer Defense Orchestration for Microservices Payment System | 2026 | BCCC-cPacket-Cloud-DDoS-2024 (full text) | [10.21203/rs.3.rs-10776464/v1](https://doi.org/10.21203/rs.3.rs-10776464/v1) | no abstract available |
| PUL-Inter-slice Defender: An Anomaly Detection Solution for Distributed Slice Mobility Attacks | 2025 | BCCC-cPacket-Cloud-DDoS-2024 (full text) | [10.48550/arxiv.2510.02236](https://doi.org/10.48550/arxiv.2510.02236) | abstract does not state use |
| Cross-attention Guided Graph-temporal Representation Learning for DDoS Attack Detection | 2026 | BCCC-cPacket-Cloud-DDoS-2024 (full text) | [10.22266/ijies2026.0930.45](https://doi.org/10.22266/ijies2026.0930.45) | abstract does not state use |
| Robust and Adaptive Anomaly Detection for Distributed Slice Mobility Attacks in 5G Network Slicing (dissertation) | 2026 | BCCC-cPacket-Cloud-DDoS-2024 (full text) |  | abstract does not state use |
| Beyond Accuracy: Stable Meaningful and Actionable Explanations for Multi-Attack IDS | 2026 | BCCC-CIC-IDS2017 (full text) | [10.2139/ssrn.6603944](https://doi.org/10.2139/ssrn.6603944) | no abstract available |
| Using the MISP Platform to Collect Incident Data | 2025 | BCCC-CIC-IDS2017 (full text) | [10.20944/preprints202505.0785.v1](https://doi.org/10.20944/preprints202505.0785.v1) | abstract does not state use |
| Towards Practical Quantum Kernels for Network Intrusion Detection | 2025 | BCCC-CSE-CIC-IDS2018 (full text) | [10.1609/aaaiss.v7i1.36903](https://doi.org/10.1609/aaaiss.v7i1.36903) | abstract does not state use |
| AI-Driven Cybersecurity Framework for Safeguarding University Networks from Emerging Threats | 2025 | BCCC-CSE-CIC-IDS2018 (full text) | [10.32604/jcs.2025.069444](https://doi.org/10.32604/jcs.2025.069444) | abstract does not state use |
| On Some Approaches to Intelligent Counteracting Cyberattacks Within Microservice Architecture | 2025 | BCCC-CSE-CIC-IDS2018 (full text) | [10.23939/sisn2025.18.2.061](https://doi.org/10.23939/sisn2025.18.2.061) | abstract does not state use |
| A No-Defense Defense Against Gradient-Based Adversarial Attacks on ML-NIDS: Is Less More? | 2026 | BCCC-CSE-CIC-IDS2018 (full text) | [10.48550/arxiv.2605.18666](https://doi.org/10.48550/arxiv.2605.18666) | abstract does not state use |
| Evaluating large language models effectiveness for flow-based intrusion detection: a comparative study with ML and DL baselines | 2026 | BCCC-CIC-IDS-2017 (full text) | [10.1007/s10462-025-11432-2](https://doi.org/10.1007/s10462-025-11432-2) | abstract names a different dataset (CIC IoT 2023) |

## Source papers (dataset / tool)

| title | year | dataset | DOI | abstract-reported result / reason |
|---|---|---|---|---|
| Toward Generating a New Cloud-Based Distributed Denial of Service (DDoS) Dataset and Cloud Intrusion Traffic Characterization | 2024 | BCCC-cPacket-Cloud-DDoS-2024 | [10.3390/info15040195](https://doi.org/10.3390/info15040195) | dataset paper |
| NTLFlowLyzer: Towards generating an intrusion detection dataset and intruders behavior profiling through network and transport layers traffic analysis and pattern extraction | 2024 | BCCC-CIC-IDS2017 | [10.1016/j.cose.2024.104160](https://doi.org/10.1016/j.cose.2024.104160) | tool paper |
| Toward Generating a Large Scale Intrusion Detection Dataset and Intruders Behavioral Profiling Using Network and Transportation Layers Traffic Flow Analyzer (NTLFlowLyzer) | 2025 | BCCC-CSE-CIC-IDS2018 | [10.1007/s10922-025-09917-0](https://doi.org/10.1007/s10922-025-09917-0) | tool / dataset paper |
