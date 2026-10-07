# NTLFlowLyzer timestamp leak: all metrics of all runs

Generated 2026-10-03 21:47 by `~/Desktop/build_NTL_metrics.py` from the result files. Every number below is copied from a run's result JSON (or computed from it where stated); nothing is retyped.

**Contents:** Legend · Part 1 Experiment 1/1b (our 2018 models, timestamps changed) · Part 2 Experiment 2 (timestamp-only baseline) · Part 3 Experiment 3 (RandomForest retrain, 2018 and 2017) · Part 4 Section 12 (seven model families × three datasets, plus full-training-set RF/XGBoost on 2018).

## Legend

### The leak in one paragraph

NTLFlowLyzer writes a flow's absolute start time (Unix epoch seconds, ~1.5e9-1.7e9) into every inter-arrival-time (IAT) feature of a flow direction that holds exactly one packet. A **leaked cell** is an IAT value > 1e9 in the unmodified data; a **leaked row** has at least one leaked cell. Capture time identifies the attack window, so a model can learn the class from the timestamp instead of from the traffic.

### Datasets

| short name | dataset | classes | features used |
|---|---|---|---|
| 2018 / d2018 | BCCC-CSE-CIC-IDS2018 (published CSVs) | 9 (Benign + 8 attacks, after the original pipeline's class selection) | 313 (30 IAT) |
| 2017 / d2017 | BCCC-CIC-IDS-2017 | 14 (Benign + 13 attacks) | 114 (15 IAT) |
| cPacket / cpacket | BCCC-cPacket-Cloud-DDoS-2024 | 26 subtypes: 17 `Attack / …`, 8 `Benign / …`, `Suspicious` (Experiment 2 also uses the 3 top-level labels) | 313 (30 IAT) |

### Splits

| split | meaning |
|---|---|
| random | stratified 75 % train / 25 % test by class, seed 0. Train and test flows come from the same capture windows, so the timestamp can identify the class. |
| temporal | the latest 25 % of each (file, class) by flow time is the test set (2018: the original training pipeline's split, with its class caps). Test flows come after the training flows, so learned time ranges often do not reach them. |

### Training variants (what the model was trained on)

| variant | meaning |
|---|---|
| leaky | trained on the data as published (leak present). |
| fixA | every leaked IAT cell set to 0 in train and test. Equivalent to the code fix (a one-packet direction gets IAT 0), because the leak rule has no exceptions. The main leak-free baseline. |
| fixB | fixA, plus every row with `packets_count == 1` removed from train and test (Experiment 3 only). Scored on a smaller, different test set. |
| dropIAT | every IAT column removed from train and test (Section 12 only). No IAT information at all: a check that fixA's zeros do not leak. |
| subsample vs full | Section 12 models train on a 600k-row stratified subsample of the training split (all rows of classes with < 1,000 rows). `rffull` / `xgbfull` train on the full 2018 training split (3.26M rows), as Experiment 3 did. |

### Test conditions (what the trained model was scored on)

| condition | applies to | meaning |
|---|---|---|
| leaky / baseline | leaky models | test data as published. |
| +8y | leaky models, no retraining | every leaked test cell + 252,460,800 s (8 years). Breaks the timestamp, keeps everything else. |
| +1d | leaky models (Exp. 1) | every leaked test cell + 86,400 s (1 day). |
| shuffle | leaky models (Exp. 1) | each leaked row gets another leaked row's timestamp (5 seeds; per-class values here are seed s0, overall values the 5-seed mean). |
| zero | leaky models, no retraining | every leaked test cell set to 0: fixed data fed to the leaky model. |
| fixA / dropIAT / fixB | models trained on that variant | scored on test data prepared the same way. |

### Row subsets

| subset | meaning |
|---|---|
| all rows | the whole test split. |
| leaked rows | test rows leaked in the unmodified data (the same rows for every condition of a split). Its class mix differs from all rows, so compare it via recall / mean attack recall, not accuracy. |
| multi-packet rows | test rows with `packets_count != 1` (2017 Experiment 3 only). |

### Metrics

| metric | meaning |
|---|---|
| accuracy | share of test rows predicted correctly. |
| macro F1 | unweighted mean F1 over all classes (a class with no support and no predictions counts as 0). |
| mean attack recall (MAR) | unweighted mean recall over attack classes with >= 10 rows in the subset (cPacket: the 17 `Attack / …` subtypes; `Suspicious` is not an attack). |
| recall / precision | per class: recall = correct / support (how many of the class were found); precision = correct / predicted as that class (how many alarms were right). Shown as `recall / precision`. |
| support | number of test rows of that class in the subset. |
| 95% CI | paired bootstrap over test rows, B = 1,000, seed 0 (Section 12 only). Covers test sampling, not training randomness. |
| popw | Experiment 1b scores a 20,001-row stratified sample; accuracy, macro F1 and precision are population-weighted back to the full test set. |

### Models

| model | configuration | class weighting | where |
|---|---|---|---|
| RF (our 2018 model) | ONNX RandomForest, 200 trees, depth 30, min_samples_leaf 10, trained on the full 2018 training set, seed 42 | balanced | Exp. 1 |
| KNN, ensemble (our 2018 models) | ONNX StandardScaler + distance-weighted 5-NN (600k subsample); soft-voting RF + KNN | none (KNN) | Exp. 1b |
| timestamp-only tree | DecisionTree on one feature t = smallest leaked IAT in the row (0 if none), depth 20, min_samples_leaf 10; `tree` balanced (pre-specified), `tree_unweighted` added afterwards; baselines `most_frequent`, `stratified` | as named | Exp. 2 |
| RF retrain | RandomForest, 200 trees, depth 30, min_samples_leaf 10, balanced, n_jobs 2 | balanced | Exp. 3 (2018 seeds 0-3, 2017 seed 0), Section 12 (`rf`, `rffull`) |
| gnb | GaussianNB, defaults. Near chance on cPacket: a broken baseline, not interpreted. | none | Section 12 |
| dt | DecisionTree, depth 30, min_samples_leaf 10 | balanced | Section 12 |
| lr | StandardScaler + LogisticRegression (lbfgs, max_iter 1000). Hit the iteration limit in most runs: not interpreted. | balanced | Section 12 |
| xgb | XGBoost, 200 trees, depth 8, learning rate 0.1, hist | balanced (sample weights) | Section 12 (`xgb`, `xgbfull`) |
| mlp | StandardScaler + MLP (128, 64), max_iter 50, early stopping. Under-trained: not interpreted. | none | Section 12 |
| knn | StandardScaler + distance-weighted 5-NN (as our 2018 model) | none | Section 12 |


---

## Part 1. Experiment 1: our 2018 models, only the leaked timestamps changed

Original temporal test split of 2018 (1,087,223 rows, 359,693 leaked). No retraining: the same trained model scores the test set with only the leaked IAT cells changed. Non-leaked rows' predictions were checked to be unchanged in every condition.

### 1.1 RandomForest (full test set)

| condition | accuracy (all) | macro F1 (all) | accuracy (leaked) | macro F1 (leaked) | predictions changed |
|---|---:|---:|---:|---:|---:|
| leaky | 0.892 | 0.756 | 0.674 | 0.299 | - |
| +8y | 0.875 | 0.792 | 0.622 | 0.207 | 22,226 |
| +1d | 0.838 | 0.735 | 0.511 | 0.206 | 121,075 |
| shuffle (mean of 5 seeds) | 0.876 | 0.734 | 0.626 | 0.219 | 32,526 |
| zero | 0.875 | 0.792 | 0.622 | 0.207 | 22,226 |

RandomForest, per class, all test rows (recall / precision):

| class | support | leaky | +8y | +1d | shuffle (s0) | zero |
|---|---:|---|---|---|---|---|
| Benign | 587,523 | 0.997 / 0.835 | 1.000 / 0.812 | 0.932 / 0.882 | 0.993 / 0.821 | 1.000 / 0.812 |
| Bot | 71,525 | 0.502 / 1.000 | 0.498 / 1.000 | 0.498 / 1.000 | 0.499 / 0.997 | 0.498 / 1.000 |
| Brute_Force_Web | 134 | 0.507 / 0.944 | 0.493 / 0.943 | 0.493 / 0.943 | 0.493 / 0.930 | 0.493 / 0.943 |
| Brute_Force_XSS | 58 | 0.586 / 1.000 | 0.483 / 1.000 | 0.483 / 1.000 | 0.483 / 0.933 | 0.483 / 1.000 |
| DDoS_HOIC | 250,175 | 0.690 / 1.000 | 0.610 / 1.000 | 0.610 / 1.000 | 0.632 / 0.970 | 0.610 / 1.000 |
| DDoS_LOIC_HTTP | 72,382 | 1.000 / 1.000 | 1.000 / 1.000 | 1.000 / 1.000 | 1.000 / 1.000 | 1.000 / 1.000 |
| DoS_HULK | 79,013 | 0.968 / 1.000 | 0.968 / 1.000 | 0.968 / 1.000 | 0.968 / 1.000 | 0.968 / 1.000 |
| DoS_SlowHTTP | 26,387 | 1.000 / 1.000 | 1.000 / 1.000 | 1.000 / 1.000 | 1.000 / 1.000 | 1.000 / 1.000 |
| SQL_Injection | 26 | 0.962 / 0.013 | 0.423 / 0.688 | 0.962 / 0.000 | 0.423 / 0.005 | 0.423 / 0.688 |

RandomForest, per class, leaked test rows (recall / precision):

| class | support | leaky | +8y | +1d | shuffle (s0) | zero |
|---|---:|---|---|---|---|---|
| Benign | 197,191 | 0.991 / 0.628 | 1.000 / 0.592 | 0.797 / 0.682 | 0.980 / 0.603 | 1.000 / 0.592 |
| Bot | 35,830 | 0.009 / 1.000 | 0.000 / 0.000 | 0.000 / 0.000 | 0.001 / 0.230 | 0.000 / 0.000 |
| Brute_Force_Web | 66 | 0.030 / 1.000 | 0.000 / 0.000 | 0.000 / 0.000 | 0.000 / 0.000 | 0.000 / 0.000 |
| Brute_Force_XSS | 30 | 0.200 / 1.000 | 0.000 / 0.000 | 0.000 / 0.000 | 0.000 / 0.000 | 0.000 / 0.000 |
| DDoS_HOIC | 97,477 | 0.205 / 1.000 | 0.000 / 0.000 | 0.000 / 0.000 | 0.057 / 0.530 | 0.000 / 0.000 |
| DDoS_LOIC_HTTP | 0 | 0.000 / 0.000 | 0.000 / 0.000 | 0.000 / 0.000 | 0.000 / 0.000 | 0.000 / 0.000 |
| DoS_HULK | 2,698 | 0.088 / 1.000 | 0.066 / 1.000 | 0.066 / 1.000 | 0.066 / 0.983 | 0.066 / 1.000 |
| DoS_SlowHTTP | 26,387 | 1.000 / 1.000 | 1.000 / 1.000 | 1.000 / 1.000 | 1.000 / 1.000 | 1.000 / 1.000 |
| SQL_Injection | 14 | 1.000 / 0.008 | 0.000 / 0.000 | 1.000 / 0.000 | 0.000 / 0.000 | 0.000 / 0.000 |

### 1.2 RF, KNN and soft-voting ensemble on a 20,001-row stratified sample (Experiment 1b)

Sample stratified by (class, leaked), all SQL_Injection / XSS / Web rows included; values population-weighted (popw).

| model | condition | accuracy popw (all) | macro F1 popw (all) | accuracy popw (leaked) | non-leaked rows unchanged |
|---|---|---:|---:|---:|---|
| rf | leaky | 0.893 | 0.758 | 0.677 | True |
| rf | +8y | 0.875 | 0.799 | 0.622 | True |
| rf | +1d | 0.838 | 0.736 | 0.512 | True |
| rf | shuffle (s0) | 0.876 | 0.737 | 0.625 | True |
| rf | zero | 0.875 | 0.799 | 0.622 | True |
| knn | leaky | 0.993 | 0.908 | 0.993 | True |
| knn | +8y | 0.871 | 0.763 | 0.624 | True |
| knn | +1d | 0.904 | 0.779 | 0.721 | True |
| knn | shuffle (s0) | 0.918 | 0.739 | 0.766 | True |
| knn | zero | 0.871 | 0.762 | 0.622 | True |
| ensemble | leaky | 0.993 | 0.952 | 0.992 | True |
| ensemble | +8y | 0.871 | 0.769 | 0.624 | True |
| ensemble | +1d | 0.904 | 0.801 | 0.721 | True |
| ensemble | shuffle (s0) | 0.918 | 0.723 | 0.765 | True |
| ensemble | zero | 0.871 | 0.768 | 0.622 | True |

knn, per class, all sample rows (recall / precision popw):

| class | support | leaky | +8y | +1d | shuffle (s0) | zero |
|---|---:|---|---|---|---|---|
| Benign | 587,523 | 1.000 / 0.988 | 1.000 / 0.808 | 1.000 / 0.988 | 1.000 / 0.910 | 1.000 / 0.807 |
| Bot | 71,525 | 0.935 / 0.999 | 0.445 / 0.993 | 0.935 / 0.998 | 0.500 / 0.741 | 0.437 / 1.000 |
| Brute_Force_Web | 134 | 0.978 / 0.879 | 0.485 / 0.956 | 0.978 / 0.001 | 0.500 / 0.052 | 0.485 / 0.956 |
| Brute_Force_XSS | 58 | 0.966 / 1.000 | 0.483 / 1.000 | 0.966 / 1.000 | 0.724 / 1.000 | 0.483 / 1.000 |
| DDoS_HOIC | 250,175 | 1.000 / 1.000 | 0.610 / 1.000 | 0.610 / 1.000 | 0.799 / 0.921 | 0.610 / 1.000 |
| DDoS_LOIC_HTTP | 72,382 | 1.000 / 0.999 | 1.000 / 0.999 | 1.000 / 0.999 | 1.000 / 0.999 | 1.000 / 0.999 |
| DoS_HULK | 79,012 | 0.969 / 1.000 | 0.969 / 1.000 | 0.969 / 1.000 | 0.969 / 1.000 | 0.969 / 1.000 |
| DoS_SlowHTTP | 26,386 | 1.000 / 1.000 | 1.000 / 1.000 | 1.000 / 1.000 | 1.000 / 1.000 | 1.000 / 1.000 |
| SQL_Injection | 26 | 0.192 / 1.000 | 0.192 / 1.000 | 0.192 / 1.000 | 0.192 / 1.000 | 0.192 / 1.000 |

ensemble, per class, all sample rows (recall / precision popw):

| class | support | leaky | +8y | +1d | shuffle (s0) | zero |
|---|---:|---|---|---|---|---|
| Benign | 587,523 | 1.000 / 0.988 | 1.000 / 0.808 | 1.000 / 0.988 | 1.000 / 0.909 | 1.000 / 0.807 |
| Bot | 71,525 | 0.933 / 1.000 | 0.445 / 0.997 | 0.934 / 0.999 | 0.492 / 0.745 | 0.437 / 1.000 |
| Brute_Force_Web | 134 | 0.918 / 0.969 | 0.485 / 0.956 | 0.784 / 0.001 | 0.485 / 0.365 | 0.485 / 0.956 |
| Brute_Force_XSS | 58 | 0.966 / 1.000 | 0.483 / 1.000 | 0.966 / 1.000 | 0.534 / 1.000 | 0.483 / 1.000 |
| DDoS_HOIC | 250,175 | 1.000 / 1.000 | 0.610 / 1.000 | 0.610 / 1.000 | 0.799 / 0.921 | 0.610 / 1.000 |
| DDoS_LOIC_HTTP | 72,382 | 1.000 / 1.000 | 1.000 / 1.000 | 1.000 / 1.000 | 1.000 / 1.000 | 1.000 / 1.000 |
| DoS_HULK | 79,012 | 0.969 / 1.000 | 0.969 / 1.000 | 0.969 / 1.000 | 0.969 / 1.000 | 0.969 / 1.000 |
| DoS_SlowHTTP | 26,386 | 1.000 / 1.000 | 1.000 / 1.000 | 1.000 / 1.000 | 1.000 / 1.000 | 1.000 / 1.000 |
| SQL_Injection | 26 | 0.731 / 0.679 | 0.231 / 1.000 | 0.731 / 0.404 | 0.231 / 0.005 | 0.231 / 1.000 |

rf, per class, all sample rows (recall / precision popw):

| class | support | leaky | +8y | +1d | shuffle (s0) | zero |
|---|---:|---|---|---|---|---|
| Benign | 587,523 | 0.997 / 0.837 | 1.000 / 0.812 | 0.932 / 0.880 | 0.993 / 0.821 | 1.000 / 0.812 |
| Bot | 71,525 | 0.502 / 1.000 | 0.498 / 1.000 | 0.498 / 1.000 | 0.498 / 0.989 | 0.498 / 1.000 |
| Brute_Force_Web | 134 | 0.507 / 1.000 | 0.493 / 1.000 | 0.493 / 1.000 | 0.493 / 1.000 | 0.493 / 1.000 |
| Brute_Force_XSS | 58 | 0.586 / 1.000 | 0.483 / 1.000 | 0.483 / 1.000 | 0.483 / 1.000 | 0.483 / 1.000 |
| DDoS_HOIC | 250,175 | 0.695 / 1.000 | 0.610 / 1.000 | 0.610 / 1.000 | 0.632 / 0.970 | 0.610 / 1.000 |
| DDoS_LOIC_HTTP | 72,382 | 1.000 / 1.000 | 1.000 / 1.000 | 1.000 / 1.000 | 1.000 / 1.000 | 1.000 / 1.000 |
| DoS_HULK | 79,012 | 0.969 / 1.000 | 0.969 / 1.000 | 0.969 / 1.000 | 0.969 / 1.000 | 0.969 / 1.000 |
| DoS_SlowHTTP | 26,386 | 1.000 / 1.000 | 1.000 / 1.000 | 1.000 / 1.000 | 1.000 / 1.000 | 1.000 / 1.000 |
| SQL_Injection | 26 | 0.962 / 0.012 | 0.423 / 0.917 | 0.962 / 0.000 | 0.423 / 0.005 | 0.423 / 0.917 |

---

## Part 2. Experiment 2: the timestamp as the only feature

One feature t = smallest leaked IAT value in the row (0 if none). The claim tested: the timestamp alone identifies the attack rows that carry it, so the main metrics are on **leaked test rows**. Overall accuracy on all rows is low by construction (all non-leaked rows share t = 0).

### 2.1 2018

| split | model | accuracy (all) | macro F1 (all) | accuracy (leaked) | macro F1 (leaked) | n test | n leaked |
|---|---|---:|---:|---:|---:|---:|---:|
| random | most_frequent | 0.540 | 0.078 | 0.526 | 0.077 | 1,087,225 | 398,418 |
| random | stratified | 0.360 | 0.111 | 0.365 | 0.102 | 1,087,225 | 398,418 |
| random | tree | 0.415 | 0.369 | 0.952 | 0.546 | 1,087,225 | 398,418 |
| random | tree_unweighted | 0.698 | 0.336 | 0.955 | 0.504 | 1,087,225 | 398,418 |
| temporal | most_frequent | 0.540 | 0.078 | 0.548 | 0.079 | 1,087,223 | 359,693 |
| temporal | stratified | 0.360 | 0.112 | 0.368 | 0.103 | 1,087,223 | 359,693 |
| temporal | tree | 0.269 | 0.133 | 0.611 | 0.190 | 1,087,223 | 359,693 |
| temporal | tree_unweighted | 0.561 | 0.134 | 0.610 | 0.159 | 1,087,223 | 359,693 |

2018, random split, per class on **leaked test rows** (recall / precision):

| class | support | tree | tree_unweighted |
|---|---:|---|---|
| Benign | 209,648 | 0.909 / 1.000 | 0.917 / 0.997 |
| Bot | 35,787 | 1.000 / 0.868 | 0.998 / 0.871 |
| Brute_Force_Web | 62 | 1.000 / 0.118 | 0.000 / 0.000 |
| Brute_Force_XSS | 22 | 0.773 / 0.048 | 0.000 / 0.000 |
| DDoS_HOIC | 125,565 | 1.000 / 0.934 | 1.000 / 0.934 |
| DDoS_LOIC_HTTP | 50 | 0.000 / 0.000 | 0.000 / 0.000 |
| DoS_HULK | 886 | 0.999 / 0.528 | 0.691 / 0.801 |
| DoS_SlowHTTP | 26,387 | 1.000 / 0.891 | 0.999 / 0.895 |
| SQL_Injection | 11 | 0.636 / 0.075 | 0.000 / 0.000 |

2018, temporal split, per class on **leaked test rows** (recall / precision):

| class | support | tree | tree_unweighted |
|---|---:|---|---|
| Benign | 197,191 | 0.985 / 0.586 | 0.985 / 0.586 |
| Bot | 35,830 | 0.009 / 1.000 | 0.009 / 1.000 |
| Brute_Force_Web | 66 | 0.030 / 1.000 | 0.000 / 0.000 |
| Brute_Force_XSS | 30 | 0.067 / 1.000 | 0.000 / 0.000 |
| DDoS_HOIC | 97,477 | 0.205 / 1.000 | 0.205 / 1.000 |
| DDoS_LOIC_HTTP | 0 | 0.000 / 0.000 | 0.000 / 0.000 |
| DoS_HULK | 2,698 | 0.051 / 1.000 | 0.000 / 0.000 |
| DoS_SlowHTTP | 26,387 | 0.195 / 1.000 | 0.195 / 1.000 |
| SQL_Injection | 14 | 1.000 / 0.005 | 1.000 / 0.005 |

### 2.2 2017

| split | model | accuracy (all) | macro F1 (all) | accuracy (leaked) | macro F1 (leaked) | n test | n leaked |
|---|---|---:|---:|---:|---:|---:|---:|
| random | most_frequent | 0.733 | 0.060 | 0.668 | 0.057 | 609,513 | 234,909 |
| random | stratified | 0.563 | 0.072 | 0.520 | 0.069 | 609,513 | 234,909 |
| random | tree | 0.342 | 0.243 | 0.786 | 0.319 | 609,513 | 234,909 |
| random | tree_unweighted | 0.848 | 0.186 | 0.969 | 0.249 | 609,513 | 234,909 |
| temporal | most_frequent | 0.733 | 0.060 | 0.673 | 0.057 | 609,513 | 239,638 |
| temporal | stratified | 0.563 | 0.072 | 0.523 | 0.069 | 609,513 | 239,638 |
| temporal | tree | 0.291 | 0.158 | 0.639 | 0.246 | 609,513 | 239,638 |
| temporal | tree_unweighted | 0.778 | 0.120 | 0.788 | 0.136 | 609,513 | 239,638 |

2017, random split, per class on **leaked test rows** (recall / precision):

| class | support | tree | tree_unweighted |
|---|---:|---|---|
| Benign | 156,946 | 0.681 / 1.000 | 0.983 / 0.970 |
| Botnet_ARES | 1,154 | 0.969 / 0.043 | 0.019 / 0.489 |
| DDoS_LOIT | 11 | 0.000 / 0.000 | 0.000 / 0.000 |
| DoS_GoldenEye | 129 | 1.000 / 0.089 | 0.000 / 0.000 |
| DoS_Hulk | 32,978 | 1.000 / 0.959 | 1.000 / 0.959 |
| DoS_Slowhttptest | 527 | 0.972 / 0.167 | 0.000 / 0.000 |
| DoS_Slowloris | 225 | 0.991 / 0.128 | 0.440 / 0.607 |
| FTP-Patator | 1,375 | 1.000 / 0.189 | 0.000 / 0.000 |
| Heartbleed | 2 | 1.000 / 0.003 | 0.000 / 0.000 |
| Port_Scan | 40,275 | 0.996 / 0.971 | 0.996 / 0.971 |
| SSH-Patator | 769 | 1.000 / 0.120 | 0.000 / 0.000 |
| Web_Brute_Force | 345 | 1.000 / 0.085 | 0.000 / 0.000 |
| Web_SQL_Injection | 3 | 1.000 / 0.009 | 0.000 / 0.000 |
| Web_XSS | 170 | 1.000 / 0.128 | 0.000 / 0.000 |

2017, temporal split, per class on **leaked test rows** (recall / precision):

| class | support | tree | tree_unweighted |
|---|---:|---|---|
| Benign | 161,365 | 0.778 / 0.713 | 1.000 / 0.761 |
| Botnet_ARES | 1,218 | 0.014 / 1.000 | 0.000 / 0.000 |
| DDoS_LOIT | 42 | 0.000 / 0.000 | 0.000 / 0.000 |
| DoS_GoldenEye | 289 | 0.062 / 1.000 | 0.000 / 0.000 |
| DoS_Hulk | 32,764 | 0.233 / 0.998 | 0.233 / 0.998 |
| DoS_Slowhttptest | 555 | 0.043 / 0.444 | 0.000 / 0.000 |
| DoS_Slowloris | 615 | 0.104 / 1.000 | 0.000 / 0.000 |
| FTP-Patator | 1,357 | 0.088 / 1.000 | 0.000 / 0.000 |
| Heartbleed | 1 | 1.000 / 0.000 | 0.000 / 0.000 |
| Port_Scan | 40,175 | 0.491 / 0.996 | 0.491 / 0.996 |
| SSH-Patator | 738 | 0.062 / 1.000 | 0.000 / 0.000 |
| Web_Brute_Force | 344 | 0.061 / 1.000 | 0.000 / 0.000 |
| Web_SQL_Injection | 3 | 0.333 / 1.000 | 0.000 / 0.000 |
| Web_XSS | 172 | 0.221 / 1.000 | 0.000 / 0.000 |

### 2.3 cPacket, 26 subtypes

| split | model | accuracy (all) | macro F1 (all) | accuracy (leaked) | macro F1 (leaked) | n test | n leaked |
|---|---|---:|---:|---:|---:|---:|---:|
| random | most_frequent | 0.431 | 0.023 | 0.534 | 0.027 | 175,194 | 114,644 |
| random | stratified | 0.243 | 0.038 | 0.295 | 0.035 | 175,194 | 114,644 |
| random | tree | 0.346 | 0.259 | 0.510 | 0.412 | 175,194 | 114,644 |
| random | tree_unweighted | 0.623 | 0.133 | 0.826 | 0.239 | 175,194 | 114,644 |
| temporal | most_frequent | 0.431 | 0.023 | 0.538 | 0.027 | 175,191 | 114,773 |
| temporal | stratified | 0.244 | 0.038 | 0.298 | 0.036 | 175,191 | 114,773 |
| temporal | tree | 0.237 | 0.096 | 0.341 | 0.156 | 175,191 | 114,773 |
| temporal | tree_unweighted | 0.303 | 0.069 | 0.342 | 0.077 | 175,191 | 114,773 |

cPacket, 26 subtypes, random split, per class on **leaked test rows** (recall / precision):

| class | support | tree | tree_unweighted |
|---|---:|---|---|
| Attack / Attack-Killall-v2 | 349 | 0.971 / 0.359 | 0.593 / 0.370 |
| Attack / Attack-Killer-TCP | 465 | 0.963 / 0.413 | 0.557 / 0.480 |
| Attack / Attack-TCP-BYPass-V1 | 33,209 | 0.991 / 0.997 | 0.997 / 0.988 |
| Attack / Attack-TCP-Control | 413 | 1.000 / 0.310 | 0.000 / 0.000 |
| Attack / Attack-TCP-Flag-ACK | 450 | 1.000 / 0.409 | 0.256 / 0.421 |
| Attack / Attack-TCP-Flag-ACK-PSH | 439 | 1.000 / 0.398 | 0.153 / 0.416 |
| Attack / Attack-TCP-Flag-MIX | 413 | 0.983 / 0.379 | 0.223 / 0.453 |
| Attack / Attack-TCP-Flag-OSYN | 189 | 0.926 / 0.284 | 0.085 / 0.320 |
| Attack / Attack-TCP-Flag-OSYNP | 183 | 0.951 / 0.288 | 0.142 / 0.426 |
| Attack / Attack-TCP-Flag-RST-ACK | 140 | 0.957 / 0.283 | 0.000 / 0.000 |
| Attack / Attack-TCP-Flag-SYN | 427 | 0.995 / 0.374 | 0.155 / 0.382 |
| Attack / Attack-TCP-Flag-SYN-ACK | 367 | 0.997 / 0.400 | 0.278 / 0.466 |
| Attack / Attack-TCP-Flag-SYN-TFO | 198 | 0.975 / 0.299 | 0.000 / 0.000 |
| Attack / Attack-TCP-Flag-SYN-TIME | 235 | 1.000 / 0.313 | 0.000 / 0.000 |
| Attack / Attack-TCP-IGMP | 408 | 0.966 / 0.406 | 0.740 / 0.428 |
| Attack / Attack-TCP-SYN | 363 | 1.000 / 0.368 | 0.364 / 0.391 |
| Attack / Attack-TCP-Valid-SYN | 399 | 1.000 / 0.375 | 0.351 / 0.375 |
| Benign / Benign | 61,174 | 0.247 / 0.928 | 0.959 / 0.786 |
| Benign / Benign-Email-Receive | 236 | 0.292 / 0.008 | 0.000 / 0.000 |
| Benign / Benign-Email-Send | 285 | 0.418 / 0.015 | 0.000 / 0.000 |
| Benign / Benign-FTP | 72 | 0.764 / 0.009 | 0.000 / 0.000 |
| Benign / Benign-SSH | 377 | 0.682 / 0.086 | 0.000 / 0.000 |
| Benign / Benign-Systemic | 2,004 | 0.019 / 0.198 | 0.000 / 0.000 |
| Benign / Benign-Telnet | 992 | 0.483 / 0.039 | 0.000 / 0.000 |
| Benign / Benign-Web_Browsing_HTTP-S | 6,974 | 0.243 / 0.357 | 0.167 / 0.495 |
| Suspicious / Suspicious | 3,883 | 0.613 / 0.326 | 0.054 / 0.410 |

cPacket, 26 subtypes, temporal split, per class on **leaked test rows** (recall / precision):

| class | support | tree | tree_unweighted |
|---|---:|---|---|
| Attack / Attack-Killall-v2 | 342 | 0.000 / 0.000 | 0.000 / 0.000 |
| Attack / Attack-Killer-TCP | 373 | 0.029 / 0.162 | 0.000 / 0.000 |
| Attack / Attack-TCP-BYPass-V1 | 33,122 | 0.988 / 1.000 | 0.988 / 1.000 |
| Attack / Attack-TCP-Control | 341 | 0.144 / 1.000 | 0.000 / 0.000 |
| Attack / Attack-TCP-Flag-ACK | 374 | 0.182 / 0.213 | 0.000 / 0.000 |
| Attack / Attack-TCP-Flag-ACK-PSH | 406 | 0.702 / 0.105 | 0.702 / 0.105 |
| Attack / Attack-TCP-Flag-MIX | 321 | 0.000 / 0.000 | 0.000 / 0.000 |
| Attack / Attack-TCP-Flag-OSYN | 163 | 0.147 / 0.194 | 0.000 / 0.000 |
| Attack / Attack-TCP-Flag-OSYNP | 196 | 0.015 / 0.083 | 0.000 / 0.000 |
| Attack / Attack-TCP-Flag-RST-ACK | 60 | 0.050 / 1.000 | 0.000 / 0.000 |
| Attack / Attack-TCP-Flag-SYN | 498 | 0.092 / 0.070 | 0.000 / 0.000 |
| Attack / Attack-TCP-Flag-SYN-ACK | 494 | 0.769 / 0.235 | 0.769 / 0.259 |
| Attack / Attack-TCP-Flag-SYN-TFO | 184 | 0.054 / 0.526 | 0.000 / 0.000 |
| Attack / Attack-TCP-Flag-SYN-TIME | 183 | 0.454 / 0.814 | 0.000 / 0.000 |
| Attack / Attack-TCP-IGMP | 421 | 0.109 / 0.529 | 0.000 / 0.000 |
| Attack / Attack-TCP-SYN | 388 | 0.095 / 0.435 | 0.000 / 0.000 |
| Attack / Attack-TCP-Valid-SYN | 378 | 0.119 / 1.000 | 0.000 / 0.000 |
| Benign / Benign | 61,728 | 0.002 / 0.078 | 0.010 / 0.069 |
| Benign / Benign-Email-Receive | 236 | 0.008 / 0.002 | 0.000 / 0.000 |
| Benign / Benign-Email-Send | 293 | 0.007 / 0.002 | 0.000 / 0.000 |
| Benign / Benign-FTP | 78 | 0.026 / 0.004 | 0.000 / 0.000 |
| Benign / Benign-SSH | 344 | 0.000 / 0.000 | 0.000 / 0.000 |
| Benign / Benign-Systemic | 1,889 | 0.715 / 0.026 | 0.715 / 0.026 |
| Benign / Benign-Telnet | 1,010 | 0.001 / 0.001 | 0.000 / 0.000 |
| Benign / Benign-Web_Browsing_HTTP-S | 7,057 | 0.000 / 0.000 | 0.000 / 0.000 |
| Suspicious / Suspicious | 3,894 | 0.999 / 0.225 | 0.999 / 0.231 |

### 2.4 cPacket, 3 labels

| split | model | accuracy (all) | macro F1 (all) | accuracy (leaked) | macro F1 (leaked) | n test | n leaked |
|---|---|---:|---:|---:|---:|---:|---:|
| random | most_frequent | 0.590 | 0.247 | 0.630 | 0.258 | 175,194 | 114,864 |
| random | stratified | 0.461 | 0.333 | 0.482 | 0.328 | 175,194 | 114,864 |
| random | tree | 0.625 | 0.595 | 0.858 | 0.750 | 175,194 | 114,864 |
| random | tree_unweighted | 0.777 | 0.525 | 0.915 | 0.623 | 175,194 | 114,864 |
| temporal | most_frequent | 0.590 | 0.247 | 0.808 | 0.298 | 175,194 | 91,828 |
| temporal | stratified | 0.462 | 0.334 | 0.528 | 0.315 | 175,194 | 91,828 |
| temporal | tree | 0.403 | 0.299 | 0.651 | 0.354 | 175,194 | 91,828 |
| temporal | tree_unweighted | 0.507 | 0.289 | 0.651 | 0.354 | 175,194 | 91,828 |

cPacket, 3 labels, random split, per class on **leaked test rows** (recall / precision):

| class | support | tree | tree_unweighted |
|---|---:|---|---|
| Attack | 38,670 | 0.952 / 0.865 | 0.860 / 0.987 |
| Benign | 72,322 | 0.800 / 0.969 | 0.994 / 0.886 |
| Suspicious | 3,872 | 0.993 / 0.305 | 0.006 / 0.490 |

cPacket, 3 labels, temporal split, per class on **leaked test rows** (recall / precision):

| class | support | tree | tree_unweighted |
|---|---:|---|---|
| Attack | 13,716 | 0.000 / 0.000 | 0.000 / 0.000 |
| Benign | 74,218 | 0.753 / 0.842 | 0.753 / 0.840 |
| Suspicious | 3,894 | 1.000 / 0.153 | 0.999 / 0.154 |

---

## Part 3. Experiment 3: RandomForest retrained with and without the leak

Full training split (2018: 3.26M rows; 2017: 1.83M rows). fixB rows are scored on a smaller test set (1-packet rows removed).

### 3.1 2018, four seeds (0-3)

| split | variant | seed | n test | accuracy (all) | macro F1 (all) | accuracy (leaked) | macro F1 (leaked) | split thresholds > 1e9 |
|---|---|---:|---:|---:|---:|---:|---:|---:|
| random | leaky | 0 | 1,087,225 | 0.998 | 0.824 | 0.995 | 0.728 | 22657 |
| random | leaky | 1 | 1,087,225 | 0.997 | 0.822 | 0.992 | 0.726 | 21525 |
| random | leaky | 2 | 1,087,225 | 0.997 | 0.822 | 0.991 | 0.725 | 21506 |
| random | leaky | 3 | 1,087,225 | 0.998 | 0.823 | 0.996 | 0.728 | 22174 |
| random | fixA | 0 | 1,087,225 | 0.950 | 0.792 | 0.864 | 0.550 | 0 |
| random | fixA | 1 | 1,087,225 | 0.954 | 0.767 | 0.875 | 0.506 | 0 |
| random | fixA | 2 | 1,087,225 | 0.954 | 0.756 | 0.875 | 0.495 | 1 |
| random | fixA | 3 | 1,087,225 | 0.954 | 0.739 | 0.875 | 0.479 | 0 |
| random | fixB | 0 | 738,622 | 1.000 | 0.985 | 1.000 | 0.443 | 0 |
| random | fixB | 1 | 738,622 | 1.000 | 0.987 | 1.000 | 0.443 | 0 |
| random | fixB | 2 | 738,622 | 1.000 | 0.986 | 1.000 | 0.443 | 0 |
| random | fixB | 3 | 738,622 | 1.000 | 0.985 | 1.000 | 0.443 | 0 |
| temporal | leaky | 0 | 1,087,223 | 0.892 | 0.754 | 0.674 | 0.299 | 17741 |
| temporal | leaky | 1 | 1,087,223 | 0.892 | 0.761 | 0.674 | 0.318 | 17904 |
| temporal | leaky | 2 | 1,087,223 | 0.892 | 0.755 | 0.674 | 0.299 | 19363 |
| temporal | leaky | 3 | 1,087,223 | 0.892 | 0.756 | 0.674 | 0.299 | 17448 |
| temporal | fixA | 0 | 1,087,223 | 0.965 | 0.770 | 0.893 | 0.436 | 0 |
| temporal | fixA | 1 | 1,087,223 | 0.965 | 0.780 | 0.893 | 0.445 | 0 |
| temporal | fixA | 2 | 1,087,223 | 0.965 | 0.790 | 0.893 | 0.456 | 0 |
| temporal | fixA | 3 | 1,087,223 | 0.964 | 0.768 | 0.893 | 0.436 | 0 |
| temporal | fixB | 0 | 776,198 | 0.999 | 0.971 | 0.990 | 0.281 | 0 |
| temporal | fixB | 1 | 776,198 | 0.999 | 0.964 | 0.990 | 0.281 | 0 |
| temporal | fixB | 2 | 776,198 | 0.999 | 0.970 | 0.990 | 0.281 | 0 |
| temporal | fixB | 3 | 776,198 | 0.999 | 0.973 | 0.990 | 0.281 | 0 |

2018 random, per class, all test rows (recall / precision; support = leaky/fixA test set, fixB differs):

| class | support | leaky (mean of 4 seeds) | fixA (mean of 4 seeds) | fixB (mean of 4 seeds) |
|---|---:|---|---|---|
| Benign | 587,524 | 0.996 / 1.000 | 0.974 / 1.000 | 1.000 / 1.000 |
| Bot | 71,525 | 1.000 / 0.987 | 0.503 / 0.998 | 1.000 / 1.000 |
| Brute_Force_Web | 134 | 0.993 / 0.358 | 0.978 / 0.426 | 1.000 / 0.855 |
| Brute_Force_XSS | 58 | 0.966 / 0.287 | 0.966 / 0.568 | 0.972 / 1.000 |
| DDoS_HOIC | 250,176 | 1.000 / 0.995 | 1.000 / 0.876 | 1.000 / 1.000 |
| DDoS_LOIC_HTTP | 72,382 | 1.000 / 1.000 | 0.999 / 1.000 | 1.000 / 1.000 |
| DoS_HULK | 79,013 | 1.000 / 1.000 | 0.998 / 0.997 | 1.000 / 1.000 |
| DoS_SlowHTTP | 26,387 | 1.000 / 1.000 | 1.000 / 1.000 | 1.000 / 1.000 |
| SQL_Injection | 26 | 0.894 / 0.299 | 0.731 / 0.001 | 0.933 / 1.000 |

2018 random, per class, leaked test rows (recall / precision; support = leaky/fixA test set, fixB differs):

| class | support | leaky (mean of 4 seeds) | fixA (mean of 4 seeds) | fixB (mean of 4 seeds) |
|---|---:|---|---|---|
| Benign | 209,648 | 0.988 / 1.000 | 0.929 / 0.999 | 1.000 / 1.000 |
| Bot | 35,787 | 1.000 / 0.975 | 0.007 / 0.789 | 0.983 / 1.000 |
| Brute_Force_Web | 62 | 0.984 / 0.210 | 0.952 / 0.263 | 0.000 / 0.000 |
| Brute_Force_XSS | 22 | 0.955 / 0.131 | 0.955 / 0.390 | 0.000 / 0.000 |
| DDoS_HOIC | 125,565 | 1.000 / 0.991 | 1.000 / 0.779 | 0.000 / 0.000 |
| DDoS_LOIC_HTTP | 50 | 0.900 / 0.662 | 0.000 / 0.000 | 0.000 / 0.000 |
| DoS_HULK | 886 | 0.994 / 0.968 | 0.825 / 0.771 | 1.000 / 0.996 |
| DoS_SlowHTTP | 26,387 | 1.000 / 1.000 | 1.000 / 1.000 | 1.000 / 1.000 |
| SQL_Injection | 11 | 0.818 / 0.142 | 0.455 / 0.000 | 0.000 / 0.000 |

2018 temporal, per class, all test rows (recall / precision; support = leaky/fixA test set, fixB differs):

| class | support | leaky (mean of 4 seeds) | fixA (mean of 4 seeds) | fixB (mean of 4 seeds) |
|---|---:|---|---|---|
| Benign | 587,523 | 0.997 / 0.835 | 0.999 / 0.995 | 1.000 / 0.998 |
| Bot | 71,525 | 0.502 / 1.000 | 0.502 / 0.999 | 0.993 / 1.000 |
| Brute_Force_Web | 134 | 0.507 / 0.922 | 0.978 / 0.553 | 0.985 / 0.912 |
| Brute_Force_XSS | 58 | 0.603 / 0.993 | 0.966 / 0.380 | 1.000 / 0.983 |
| DDoS_HOIC | 250,175 | 0.690 / 1.000 | 1.000 / 0.876 | 1.000 / 1.000 |
| DDoS_LOIC_HTTP | 72,382 | 1.000 / 1.000 | 1.000 / 1.000 | 0.999 / 1.000 |
| DoS_HULK | 79,013 | 0.968 / 1.000 | 0.968 / 1.000 | 0.996 / 1.000 |
| DoS_SlowHTTP | 26,387 | 1.000 / 1.000 | 1.000 / 1.000 | 1.000 / 1.000 |
| SQL_Injection | 26 | 0.962 / 0.013 | 0.615 / 0.093 | 0.917 / 0.702 |

2018 temporal, per class, leaked test rows (recall / precision; support = leaky/fixA test set, fixB differs):

| class | support | leaky (mean of 4 seeds) | fixA (mean of 4 seeds) | fixB (mean of 4 seeds) |
|---|---:|---|---|---|
| Benign | 197,191 | 0.991 / 0.628 | 0.998 / 0.986 | 1.000 / 0.977 |
| Bot | 35,830 | 0.009 / 1.000 | 0.010 / 0.912 | 0.000 / 0.000 |
| Brute_Force_Web | 66 | 0.030 / 1.000 | 0.955 / 0.410 | 0.000 / 0.000 |
| Brute_Force_XSS | 30 | 0.233 / 1.000 | 0.933 / 0.238 | 0.000 / 0.000 |
| DDoS_HOIC | 97,477 | 0.205 / 1.000 | 1.000 / 0.734 | 0.000 / 0.000 |
| DDoS_LOIC_HTTP | 0 | 0.000 / 0.000 | 0.000 / 0.000 | 0.000 / 0.000 |
| DoS_HULK | 2,698 | 0.088 / 1.000 | 0.066 / 1.000 | 0.370 / 1.000 |
| DoS_SlowHTTP | 26,387 | 1.000 / 1.000 | 1.000 / 1.000 | 1.000 / 1.000 |
| SQL_Injection | 14 | 1.000 / 0.008 | 0.357 / 0.032 | 0.000 / 0.000 |

### 3.2 2017, seed 0

| split | variant | n test | accuracy (all) | macro F1 (all) | accuracy (leaked) | accuracy (multi-packet rows) | split thresholds > 1e9 on IAT |
|---|---|---:|---:|---:|---:|---:|---:|
| random | leaky | 609,513 | 0.992 | 0.740 | 0.985 | 0.996 | 41107 |
| random | fixA | 609,513 | 0.875 | 0.534 | 0.684 | 0.995 | 0 |
| random | fixB | 473,541 | 0.994 | 0.749 | 0.994 | 0.994 | 0 |
| temporal | leaky | 609,513 | 0.940 | 0.633 | 0.859 | 0.990 | 33854 |
| temporal | fixA | 609,513 | 0.833 | 0.476 | 0.587 | 0.993 | 0 |
| temporal | fixB | 475,470 | 0.992 | 0.742 | 0.996 | 0.992 | 0 |

2017 random, per class, all test rows (recall / precision):

| class | support | leaky | fixA | fixB |
|---|---:|---|---|---|
| Benign | 446,560 | 0.989 / 1.000 | 0.846 / 0.999 | 0.993 / 1.000 |
| Botnet_ARES | 1,377 | 1.000 / 0.635 | 1.000 / 0.072 | 1.000 / 0.773 |
| DDoS_LOIT | 23,933 | 1.000 / 0.999 | 1.000 / 1.000 | 1.000 / 1.000 |
| DoS_GoldenEye | 2,091 | 0.982 / 0.897 | 0.921 / 0.960 | 0.978 / 0.969 |
| DoS_Hulk | 87,310 | 0.999 / 0.993 | 0.940 / 0.832 | 0.999 / 0.990 |
| DoS_Slowhttptest | 1,715 | 0.967 / 0.784 | 0.699 / 0.855 | 0.975 / 0.854 |
| DoS_Slowloris | 1,294 | 0.971 / 0.808 | 0.804 / 0.876 | 0.966 / 0.926 |
| FTP-Patator | 2,383 | 0.997 / 0.788 | 0.832 / 0.147 | 0.998 / 0.808 |
| Heartbleed | 3 | 0.667 / 0.026 | 0.000 / 0.000 | 0.000 / 0.000 |
| Port_Scan | 40,331 | 1.000 / 0.997 | 0.993 / 1.000 | 1.000 / 1.000 |
| SSH-Patator | 1,487 | 0.995 / 0.800 | 0.989 / 0.295 | 0.989 / 0.875 |
| Web_Brute_Force | 683 | 0.777 / 0.367 | 0.262 / 0.275 | 0.533 / 0.271 |
| Web_SQL_Injection | 6 | 0.667 / 0.049 | 0.500 / 0.000 | 0.333 / 0.333 |
| Web_XSS | 340 | 0.859 / 0.356 | 0.835 / 0.015 | 0.735 / 0.168 |

2017 random, per class, leaked test rows (recall / precision):

| class | support | leaky | fixA | fixB |
|---|---:|---|---|---|
| Benign | 156,946 | 0.978 / 1.000 | 0.572 / 0.997 | 0.990 / 1.000 |
| Botnet_ARES | 1,154 | 1.000 / 0.667 | 1.000 / 0.062 | 1.000 / 0.880 |
| DDoS_LOIT | 11 | 0.818 / 0.300 | 0.000 / 0.000 | 0.000 / 0.000 |
| DoS_GoldenEye | 129 | 1.000 / 0.454 | 0.000 / 0.000 | 0.000 / 0.000 |
| DoS_Hulk | 32,978 | 1.000 / 0.995 | 0.844 / 0.633 | 0.995 / 0.981 |
| DoS_Slowhttptest | 527 | 0.968 / 0.663 | 0.097 / 0.981 | 1.000 / 0.981 |
| DoS_Slowloris | 225 | 0.996 / 0.499 | 0.022 / 0.106 | 0.000 / 0.000 |
| FTP-Patator | 1,375 | 0.998 / 0.683 | 0.711 / 0.079 | 1.000 / 0.629 |
| Heartbleed | 2 | 1.000 / 0.026 | 0.000 / 0.000 | 0.000 / 0.000 |
| Port_Scan | 40,275 | 1.000 / 0.997 | 0.993 / 1.000 | 1.000 / 1.000 |
| SSH-Patator | 769 | 1.000 / 0.678 | 0.986 / 0.178 | 0.333 / 0.011 |
| Web_Brute_Force | 345 | 1.000 / 0.358 | 0.000 / 0.000 | 0.000 / 0.000 |
| Web_SQL_Injection | 3 | 1.000 / 0.039 | 0.667 / 0.000 | 0.000 / 0.000 |
| Web_XSS | 170 | 1.000 / 0.412 | 0.965 / 0.009 | 0.000 / 0.000 |

2017 random, per class, multi-packet test rows (recall / precision):

| class | support | leaky | fixA | fixB |
|---|---:|---|---|---|
| Benign | 346,264 | 0.996 / 1.000 | 0.994 / 1.000 | 0.993 / 1.000 |
| Botnet_ARES | 1,175 | 1.000 / 0.836 | 1.000 / 0.772 | 1.000 / 0.773 |
| DDoS_LOIT | 23,923 | 1.000 / 1.000 | 1.000 / 1.000 | 1.000 / 1.000 |
| DoS_GoldenEye | 1,962 | 0.981 / 0.960 | 0.981 / 0.960 | 0.978 / 0.969 |
| DoS_Hulk | 55,346 | 0.998 / 0.992 | 0.998 / 0.991 | 0.999 / 0.990 |
| DoS_Slowhttptest | 1,239 | 0.968 / 0.858 | 0.968 / 0.855 | 0.975 / 0.854 |
| DoS_Slowloris | 1,069 | 0.966 / 0.933 | 0.968 / 0.908 | 0.966 / 0.926 |
| FTP-Patator | 1,593 | 0.998 / 0.993 | 0.998 / 0.815 | 0.998 / 0.808 |
| Heartbleed | 1 | 0.000 / 0.000 | 0.000 / 0.000 | 0.000 / 0.000 |
| Port_Scan | 39,737 | 1.000 / 1.000 | 1.000 / 1.000 | 1.000 / 1.000 |
| SSH-Patator | 721 | 0.990 / 0.962 | 0.990 / 0.892 | 0.989 / 0.875 |
| Web_Brute_Force | 338 | 0.550 / 0.385 | 0.530 / 0.339 | 0.533 / 0.271 |
| Web_SQL_Injection | 3 | 0.333 / 0.167 | 0.333 / 0.333 | 0.333 / 0.333 |
| Web_XSS | 170 | 0.718 / 0.299 | 0.706 / 0.257 | 0.735 / 0.168 |

2017 temporal, per class, all test rows (recall / precision):

| class | support | leaky | fixA | fixB |
|---|---:|---|---|---|
| Benign | 446,559 | 0.985 / 0.940 | 0.851 / 0.998 | 0.994 / 0.999 |
| Botnet_ARES | 1,377 | 0.105 / 1.000 | 0.877 / 0.069 | 0.876 / 1.000 |
| DDoS_LOIT | 23,933 | 0.999 / 0.924 | 0.997 / 1.000 | 0.999 / 1.000 |
| DoS_GoldenEye | 2,091 | 0.824 / 0.887 | 0.813 / 0.885 | 0.938 / 0.893 |
| DoS_Hulk | 87,310 | 0.717 / 0.993 | 0.632 / 0.994 | 0.989 / 0.993 |
| DoS_Slowhttptest | 1,715 | 0.758 / 0.593 | 0.725 / 0.564 | 0.987 / 0.573 |
| DoS_Slowloris | 1,294 | 0.783 / 0.935 | 0.339 / 0.814 | 0.601 / 0.872 |
| FTP-Patator | 2,383 | 0.520 / 0.986 | 0.861 / 0.145 | 0.998 / 0.853 |
| Heartbleed | 3 | 0.667 / 0.001 | 0.667 / 0.000 | 0.000 / 0.000 |
| Port_Scan | 40,331 | 0.987 / 0.974 | 0.990 / 1.000 | 0.998 / 1.000 |
| SSH-Patator | 1,487 | 0.508 / 0.995 | 0.949 / 0.261 | 0.936 / 0.931 |
| Web_Brute_Force | 684 | 0.270 / 0.279 | 0.237 / 0.186 | 0.474 / 0.239 |
| Web_SQL_Injection | 6 | 0.667 / 0.667 | 0.833 / 0.001 | 1.000 / 0.600 |
| Web_XSS | 340 | 0.412 / 0.194 | 0.779 / 0.014 | 0.607 / 0.119 |

2017 temporal, per class, leaked test rows (recall / precision):

| class | support | leaky | fixA | fixB |
|---|---:|---|---|---|
| Benign | 161,365 | 0.968 / 0.851 | 0.598 / 0.998 | 0.995 / 0.999 |
| Botnet_ARES | 1,218 | 0.119 / 1.000 | 0.991 / 0.069 | 0.990 / 1.000 |
| DDoS_LOIT | 42 | 0.976 / 0.020 | 0.000 / 0.000 | 0.000 / 0.000 |
| DoS_GoldenEye | 289 | 0.062 / 1.000 | 0.000 / 0.000 | 0.000 / 0.000 |
| DoS_Hulk | 32,764 | 0.265 / 0.988 | 0.036 / 0.983 | 0.967 / 0.974 |
| DoS_Slowhttptest | 555 | 0.283 / 0.840 | 0.180 / 0.654 | 1.000 / 0.962 |
| DoS_Slowloris | 615 | 0.945 / 0.993 | 0.005 / 0.097 | 0.000 / 0.000 |
| FTP-Patator | 1,357 | 0.158 / 1.000 | 0.757 / 0.079 | 1.000 / 0.726 |
| Heartbleed | 1 | 1.000 / 0.000 | 1.000 / 0.000 | 0.000 / 0.000 |
| Port_Scan | 40,175 | 0.989 / 0.974 | 0.992 / 1.000 | 1.000 / 1.000 |
| SSH-Patator | 738 | 0.062 / 1.000 | 0.951 / 0.149 | 0.091 / 0.020 |
| Web_Brute_Force | 344 | 0.061 / 1.000 | 0.000 / 0.000 | 0.000 / 0.000 |
| Web_SQL_Injection | 3 | 0.333 / 1.000 | 0.667 / 0.000 | 0.000 / 0.000 |
| Web_XSS | 172 | 0.221 / 1.000 | 0.953 / 0.009 | 0.000 / 0.000 |

2017 temporal, per class, multi-packet test rows (recall / precision):

| class | support | leaky | fixA | fixB |
|---|---:|---|---|---|
| Benign | 348,131 | 0.996 / 0.997 | 0.995 / 0.999 | 0.994 / 0.999 |
| Botnet_ARES | 1,377 | 0.105 / 1.000 | 0.877 / 1.000 | 0.876 / 1.000 |
| DDoS_LOIT | 23,892 | 0.999 / 1.000 | 0.999 / 1.000 | 0.999 / 1.000 |
| DoS_GoldenEye | 1,802 | 0.946 / 0.886 | 0.944 / 0.885 | 0.938 / 0.893 |
| DoS_Hulk | 55,773 | 0.989 / 0.994 | 0.989 / 0.994 | 0.989 / 0.993 |
| DoS_Slowhttptest | 1,260 | 0.987 / 0.590 | 0.987 / 0.564 | 0.987 / 0.573 |
| DoS_Slowloris | 680 | 0.635 / 0.866 | 0.641 / 0.858 | 0.601 / 0.872 |
| FTP-Patator | 1,725 | 0.689 / 0.986 | 0.999 / 0.836 | 0.998 / 0.853 |
| Heartbleed | 2 | 0.500 / 1.000 | 0.500 / 1.000 | 0.000 / 0.000 |
| Port_Scan | 39,557 | 0.998 / 0.974 | 0.998 / 1.000 | 0.998 / 1.000 |
| SSH-Patator | 760 | 0.934 / 0.994 | 0.933 / 0.989 | 0.936 / 0.931 |
| Web_Brute_Force | 340 | 0.482 / 0.255 | 0.476 / 0.264 | 0.474 / 0.239 |
| Web_SQL_Injection | 3 | 1.000 / 0.600 | 1.000 / 0.750 | 1.000 / 0.600 |
| Web_XSS | 168 | 0.607 / 0.149 | 0.601 / 0.136 | 0.607 / 0.119 |

---

## Part 4. Section 12: seven model families × three datasets × two splits × five conditions

162 runs. Seed 0, 600k-row training subsample (except `rffull`, `xgbfull`: full 2018 training split), full test split. Overall values carry 95% bootstrap CIs in brackets where available. `rffull` / `xgbfull` rows only exist for 2018.

### 4.1 BCCC-CSE-CIC-IDS2018

**Overall** (all test rows, then leaked test rows):

| model | split | condition | accuracy (all) [95% CI] | macro F1 (all) | MAR (all) [95% CI] | accuracy (leaked) | MAR (leaked) | n attack classes in MAR (leaked) |
|---|---|---|---|---:|---|---:|---:|---:|
| gnb | random | leaky | 0.329 [0.328, 0.330] | 0.296 | 0.573 [0.546, 0.602] | 0.384 | 0.307 | 8 |
| gnb | random | +8y | 0.306 [0.305, 0.306] | 0.211 | 0.448 [0.421, 0.477] | 0.320 | 0.182 | 8 |
| gnb | random | zero | 0.305 [0.305, 0.306] | 0.206 | 0.424 [0.398, 0.452] | 0.319 | 0.125 | 8 |
| gnb | random | fixA | 0.298 [0.297, 0.298] | 0.301 | 0.587 [0.554, 0.616] | 0.069 | 0.125 | 8 |
| gnb | random | dropIAT | 0.298 [0.297, 0.298] | 0.301 | 0.587 [0.554, 0.616] | 0.069 | 0.125 | 8 |
| gnb | temporal | leaky | 0.314 [0.313, 0.314] | 0.288 | 0.567 [0.539, 0.598] | 0.346 | 0.347 | 7 |
| gnb | temporal | +8y | 0.290 [0.289, 0.291] | 0.201 | 0.442 [0.414, 0.473] | 0.275 | 0.204 | 7 |
| gnb | temporal | zero | 0.290 [0.289, 0.291] | 0.198 | 0.413 [0.388, 0.441] | 0.275 | 0.143 | 7 |
| gnb | temporal | fixA | 0.319 [0.318, 0.319] | 0.310 | 0.582 [0.552, 0.611] | 0.076 | 0.143 | 7 |
| gnb | temporal | dropIAT | 0.319 [0.318, 0.319] | 0.310 | 0.582 [0.552, 0.611] | 0.076 | 0.143 | 7 |
| dt | random | leaky | 0.999 [0.999, 0.999] | 0.808 | 0.963 [0.941, 0.983] | 0.999 | 0.945 | 8 |
| dt | random | +8y | 0.850 [0.850, 0.851] | 0.707 | 0.701 [0.669, 0.736] | 0.592 | 0.127 | 8 |
| dt | random | zero | 0.839 [0.838, 0.839] | 0.662 | 0.741 [0.711, 0.773] | 0.561 | 0.311 | 8 |
| dt | random | fixA | 0.954 [0.954, 0.955] | 0.749 | 0.897 [0.875, 0.918] | 0.876 | 0.649 | 8 |
| dt | random | dropIAT | 0.954 [0.954, 0.955] | 0.751 | 0.897 [0.875, 0.918] | 0.876 | 0.649 | 8 |
| dt | temporal | leaky | 0.925 [0.924, 0.925] | 0.801 | 0.919 [0.900, 0.935] | 0.774 | 0.712 | 7 |
| dt | temporal | +8y | 0.907 [0.906, 0.907] | 0.715 | 0.759 [0.727, 0.791] | 0.720 | 0.346 | 7 |
| dt | temporal | zero | 0.864 [0.863, 0.865] | 0.674 | 0.711 [0.680, 0.738] | 0.591 | 0.235 | 7 |
| dt | temporal | fixA | 0.952 [0.952, 0.953] | 0.681 | 0.901 [0.880, 0.921] | 0.860 | 0.689 | 7 |
| dt | temporal | dropIAT | 0.952 [0.952, 0.953] | 0.680 | 0.911 [0.892, 0.926] | 0.860 | 0.690 | 7 |
| lr | random | leaky | 0.900 [0.900, 0.901] | 0.697 | 0.902 [0.874, 0.925] | 0.730 | 0.653 | 8 |
| lr | random | +8y | 0.735 [0.734, 0.735] | 0.585 | 0.755 [0.724, 0.786] | 0.278 | 0.463 | 8 |
| lr | random | zero | 0.802 [0.802, 0.803] | 0.674 | 0.765 [0.735, 0.792] | 0.463 | 0.290 | 8 |
| lr | random | fixA | 0.785 [0.785, 0.786] | 0.618 | 0.840 [0.813, 0.863] | 0.415 | 0.528 | 8 |
| lr | temporal | leaky | 0.870 [0.869, 0.871] | 0.657 | 0.799 [0.773, 0.826] | 0.621 | 0.490 | 7 |
| lr | temporal | +8y | 0.786 [0.785, 0.787] | 0.554 | 0.728 [0.700, 0.759] | 0.367 | 0.307 | 7 |
| lr | temporal | zero | 0.824 [0.824, 0.825] | 0.633 | 0.730 [0.701, 0.759] | 0.483 | 0.303 | 7 |
| lr | temporal | fixA | 0.868 [0.868, 0.869] | 0.656 | 0.800 [0.773, 0.828] | 0.615 | 0.490 | 7 |
| xgb | random | leaky | 1.000 [1.000, 1.000] | 0.961 | 0.990 [0.977, 0.999] | 1.000 | 0.867 | 8 |
| xgb | random | +8y | 0.883 [0.882, 0.884] | 0.808 | 0.771 [0.739, 0.804] | 0.681 | 0.282 | 8 |
| xgb | random | zero | 0.851 [0.851, 0.852] | 0.810 | 0.709 [0.678, 0.742] | 0.594 | 0.228 | 8 |
| xgb | random | fixA | 0.952 [0.951, 0.952] | 0.779 | 0.915 [0.896, 0.930] | 0.868 | 0.681 | 8 |
| xgb | random | dropIAT | 0.952 [0.951, 0.952] | 0.779 | 0.915 [0.896, 0.930] | 0.868 | 0.681 | 8 |
| xgb | temporal | leaky | 0.995 [0.995, 0.995] | 0.882 | 0.976 [0.960, 0.989] | 0.989 | 0.859 | 7 |
| xgb | temporal | +8y | 0.906 [0.906, 0.907] | 0.816 | 0.824 [0.799, 0.852] | 0.720 | 0.479 | 7 |
| xgb | temporal | zero | 0.874 [0.873, 0.875] | 0.792 | 0.678 [0.648, 0.709] | 0.622 | 0.154 | 7 |
| xgb | temporal | fixA | 0.947 [0.947, 0.948] | 0.776 | 0.911 [0.895, 0.923] | 0.852 | 0.711 | 7 |
| xgb | temporal | dropIAT | 0.947 [0.947, 0.947] | 0.775 | 0.910 [0.894, 0.922] | 0.852 | 0.711 | 7 |
| xgbfull | random | leaky | 1.000 [1.000, 1.000] | 0.982 | 0.995 [0.988, 1.000] | 0.999 | 0.867 | 8 |
| xgbfull | random | +8y | 0.879 [0.878, 0.879] | 0.805 | 0.759 [0.728, 0.788] | 0.669 | 0.263 | 8 |
| xgbfull | random | zero | 0.851 [0.851, 0.852] | 0.817 | 0.714 [0.683, 0.744] | 0.594 | 0.228 | 8 |
| xgbfull | random | fixA | 0.952 [0.951, 0.952] | 0.782 | 0.915 [0.897, 0.930] | 0.868 | 0.681 | 8 |
| xgbfull | random | dropIAT | 0.952 [0.951, 0.952] | 0.782 | 0.915 [0.897, 0.930] | 0.868 | 0.681 | 8 |
| xgbfull | temporal | leaky | 0.976 [0.976, 0.977] | 0.882 | 0.965 [0.947, 0.977] | 0.934 | 0.829 | 7 |
| xgbfull | temporal | +8y | 0.903 [0.902, 0.904] | 0.799 | 0.779 [0.750, 0.807] | 0.712 | 0.397 | 7 |
| xgbfull | temporal | zero | 0.873 [0.873, 0.874] | 0.792 | 0.676 [0.649, 0.707] | 0.622 | 0.153 | 7 |
| xgbfull | temporal | fixA | 0.947 [0.947, 0.947] | 0.777 | 0.910 [0.892, 0.923] | 0.852 | 0.711 | 7 |
| xgbfull | temporal | dropIAT | 0.947 [0.947, 0.947] | 0.777 | 0.910 [0.892, 0.923] | 0.852 | 0.710 | 7 |
| rf | random | leaky | 0.995 [0.995, 0.995] | 0.753 | 0.998 [0.993, 1.000] | 0.987 | 0.987 | 8 |
| rf | random | +8y | 0.844 [0.844, 0.845] | 0.807 | 0.713 [0.680, 0.744] | 0.575 | 0.147 | 8 |
| rf | random | zero | 0.851 [0.850, 0.852] | 0.812 | 0.714 [0.681, 0.745] | 0.594 | 0.228 | 8 |
| rf | random | fixA | 0.831 [0.830, 0.831] | 0.685 | 0.885 [0.860, 0.907] | 0.538 | 0.614 | 8 |
| rf | random | dropIAT | 0.784 [0.783, 0.785] | 0.605 | 0.880 [0.855, 0.903] | 0.411 | 0.614 | 8 |
| rf | temporal | leaky | 0.892 [0.891, 0.892] | 0.795 | 0.845 [0.829, 0.860] | 0.673 | 0.515 | 7 |
| rf | temporal | +8y | 0.875 [0.874, 0.875] | 0.779 | 0.684 [0.653, 0.714] | 0.622 | 0.152 | 7 |
| rf | temporal | zero | 0.875 [0.874, 0.875] | 0.779 | 0.684 [0.653, 0.714] | 0.622 | 0.152 | 7 |
| rf | temporal | fixA | 0.869 [0.869, 0.870] | 0.697 | 0.853 [0.824, 0.875] | 0.605 | 0.560 | 7 |
| rf | temporal | dropIAT | 0.903 [0.902, 0.903] | 0.673 | 0.867 [0.840, 0.890] | 0.707 | 0.595 | 7 |
| rffull | random | leaky | 0.998 [0.998, 0.998] | 0.824 | 0.985 [0.968, 0.998] | 0.995 | 0.956 | 8 |
| rffull | random | +8y | 0.851 [0.850, 0.852] | 0.818 | 0.713 [0.683, 0.743] | 0.593 | 0.147 | 8 |
| rffull | random | zero | 0.851 [0.850, 0.852] | 0.818 | 0.714 [0.683, 0.744] | 0.593 | 0.176 | 8 |
| rffull | random | fixA | 0.950 [0.950, 0.951] | 0.792 | 0.897 [0.873, 0.918] | 0.864 | 0.649 | 8 |
| rffull | random | dropIAT | 0.954 [0.954, 0.955] | 0.784 | 0.897 [0.873, 0.918] | 0.876 | 0.649 | 8 |
| rffull | temporal | leaky | 0.892 [0.891, 0.892] | 0.754 | 0.777 [0.756, 0.799] | 0.674 | 0.362 | 7 |
| rffull | temporal | +8y | 0.875 [0.874, 0.875] | 0.790 | 0.684 [0.656, 0.716] | 0.622 | 0.152 | 7 |
| rffull | temporal | zero | 0.875 [0.874, 0.875] | 0.790 | 0.684 [0.656, 0.716] | 0.622 | 0.152 | 7 |
| rffull | temporal | fixA | 0.965 [0.964, 0.965] | 0.770 | 0.879 [0.854, 0.904] | 0.893 | 0.617 | 7 |
| rffull | temporal | dropIAT | 0.961 [0.960, 0.961] | 0.764 | 0.871 [0.847, 0.896] | 0.893 | 0.617 | 7 |
| mlp | random | leaky | 0.919 [0.919, 0.920] | 0.793 | 0.736 [0.707, 0.765] | 0.780 | 0.353 | 8 |
| mlp | random | +8y | 0.919 [0.919, 0.920] | 0.793 | 0.736 [0.707, 0.765] | 0.780 | 0.353 | 8 |
| mlp | random | zero | 0.851 [0.850, 0.851] | 0.763 | 0.673 [0.643, 0.702] | 0.593 | 0.157 | 8 |
| mlp | random | fixA | 0.920 [0.919, 0.920] | 0.804 | 0.731 [0.703, 0.759] | 0.781 | 0.353 | 8 |
| mlp | random | dropIAT | 0.919 [0.919, 0.920] | 0.795 | 0.727 [0.698, 0.755] | 0.780 | 0.353 | 8 |
| mlp | temporal | leaky | 0.915 [0.915, 0.916] | 0.771 | 0.697 [0.671, 0.724] | 0.757 | 0.295 | 7 |
| mlp | temporal | +8y | 0.915 [0.915, 0.916] | 0.771 | 0.697 [0.671, 0.724] | 0.757 | 0.295 | 7 |
| mlp | temporal | zero | 0.870 [0.870, 0.871] | 0.754 | 0.648 [0.622, 0.675] | 0.621 | 0.152 | 7 |
| mlp | temporal | fixA | 0.916 [0.915, 0.916] | 0.772 | 0.692 [0.667, 0.719] | 0.757 | 0.295 | 7 |
| mlp | temporal | dropIAT | 0.915 [0.915, 0.916] | 0.780 | 0.697 [0.671, 0.724] | 0.757 | 0.295 | 7 |
| knn | random | leaky | 1.000 [1.000, 1.000] | 0.964 | 0.988 [0.972, 1.000] | 1.000 | 0.868 | 8 |
| knn | random | +8y | 0.850 [0.850, 0.851] | 0.801 | 0.704 [0.672, 0.736] | 0.592 | 0.158 | 8 |
| knn | random | zero | 0.799 [0.799, 0.800] | 0.733 | 0.744 [0.713, 0.775] | 0.453 | 0.263 | 8 |
| knn | random | fixA | 0.884 [0.884, 0.885] | 0.856 | 0.883 [0.856, 0.908] | 0.684 | 0.627 | 8 |
| knn | random | dropIAT | 0.884 [0.884, 0.885] | 0.858 | 0.883 [0.856, 0.908] | 0.684 | 0.627 | 8 |
| knn | temporal | leaky | 0.993 [0.993, 0.993] | 0.917 | 0.958 [0.936, 0.975] | 0.992 | 0.852 | 7 |
| knn | temporal | +8y | 0.871 [0.870, 0.872] | 0.763 | 0.660 [0.630, 0.691] | 0.623 | 0.154 | 7 |
| knn | temporal | zero | 0.824 [0.824, 0.825] | 0.695 | 0.704 [0.677, 0.735] | 0.482 | 0.256 | 7 |
| knn | temporal | fixA | 0.904 [0.903, 0.904] | 0.840 | 0.874 [0.850, 0.900] | 0.721 | 0.635 | 7 |
| knn | temporal | dropIAT | 0.904 [0.903, 0.904] | 0.840 | 0.873 [0.848, 0.899] | 0.721 | 0.635 | 7 |

**gnb, random split, per class, all test rows** (recall / precision):

| class | support | leaky | +8y | zero | fixA | dropIAT |
|---|---:|---|---|---|---|---|
| Benign | 587,524 | 0.034 / 1.000 | 0.035 / 0.470 | 0.035 / 0.470 | 0.044 / 1.000 | 0.044 / 1.000 |
| Bot | 71,525 | 0.003 / 0.232 | 0.003 / 0.231 | 0.003 / 0.236 | 0.003 / 0.478 | 0.003 / 0.477 |
| Brute_Force_Web | 134 | 0.007 / 0.000 | 0.007 / 0.000 | 0.007 / 0.000 | 0.276 / 0.001 | 0.276 / 0.001 |
| Brute_Force_XSS | 58 | 0.552 / 0.008 | 0.552 / 0.008 | 0.552 / 0.008 | 0.552 / 0.016 | 0.552 / 0.016 |
| DDoS_HOIC | 250,176 | 0.656 / 0.298 | 0.656 / 0.298 | 0.656 / 0.239 | 0.495 / 0.525 | 0.495 / 0.525 |
| DDoS_LOIC_HTTP | 72,382 | 0.999 / 0.289 | 0.999 / 0.289 | 0.999 / 0.289 | 0.999 / 1.000 | 0.999 / 1.000 |
| DoS_HULK | 79,013 | 0.947 / 0.958 | 0.947 / 0.958 | 0.947 / 0.958 | 0.945 / 0.973 | 0.945 / 0.973 |
| DoS_SlowHTTP | 26,387 | 1.000 / 0.620 | 0.000 / 0.000 | 0.000 / 0.000 | 1.000 / 0.062 | 1.000 / 0.062 |
| SQL_Injection | 26 | 0.423 / 0.000 | 0.423 / 0.000 | 0.231 / 0.007 | 0.423 / 0.000 | 0.423 / 0.000 |

**gnb, random split, per class, leaked test rows** (recall / precision):

| class | support | leaky | +8y | zero | fixA | dropIAT |
|---|---:|---|---|---|---|---|
| Benign | 209,648 | 0.004 / 0.999 | 0.008 / 0.070 | 0.008 / 0.064 | 0.005 / 1.000 | 0.005 / 1.000 |
| Bot | 35,787 | 0.000 / 0.000 | 0.000 / 0.000 | 0.000 / 0.000 | 0.000 / 0.000 | 0.000 / 0.000 |
| Brute_Force_Web | 62 | 0.000 / 0.000 | 0.000 / 0.000 | 0.000 / 0.000 | 0.000 / 0.000 | 0.000 / 0.000 |
| Brute_Force_XSS | 22 | 0.000 / 0.000 | 0.000 / 0.000 | 0.000 / 0.000 | 0.000 / 0.000 | 0.000 / 0.000 |
| DDoS_HOIC | 125,565 | 1.000 / 0.526 | 1.000 / 0.526 | 1.000 / 0.336 | 0.000 / 0.000 | 0.000 / 0.000 |
| DDoS_LOIC_HTTP | 50 | 0.000 / 0.000 | 0.000 / 0.000 | 0.000 / 0.000 | 0.000 / 0.000 | 0.000 / 0.000 |
| DoS_HULK | 886 | 0.000 / 0.000 | 0.000 / 0.000 | 0.000 / 0.000 | 0.000 / 0.000 | 0.000 / 0.000 |
| DoS_SlowHTTP | 26,387 | 1.000 / 0.620 | 0.000 / 0.000 | 0.000 / 0.000 | 1.000 / 0.069 | 1.000 / 0.069 |
| SQL_Injection | 11 | 0.455 / 0.000 | 0.455 / 0.000 | 0.000 / 0.000 | 0.000 / 0.000 | 0.000 / 0.000 |

**gnb, temporal split, per class, all test rows** (recall / precision):

| class | support | leaky | +8y | zero | fixA | dropIAT |
|---|---:|---|---|---|---|---|
| Benign | 587,523 | 0.028 / 1.000 | 0.029 / 0.423 | 0.029 / 0.425 | 0.040 / 1.000 | 0.040 / 1.000 |
| Bot | 71,525 | 0.005 / 0.215 | 0.005 / 0.215 | 0.005 / 0.215 | 0.005 / 0.538 | 0.005 / 0.538 |
| Brute_Force_Web | 134 | 0.000 / 0.000 | 0.000 / 0.000 | 0.000 / 0.000 | 0.246 / 0.001 | 0.246 / 0.001 |
| Brute_Force_XSS | 58 | 0.483 / 0.004 | 0.483 / 0.004 | 0.483 / 0.004 | 0.483 / 0.009 | 0.483 / 0.009 |
| DDoS_HOIC | 250,175 | 0.603 / 0.281 | 0.603 / 0.281 | 0.603 / 0.227 | 0.598 / 0.595 | 0.598 / 0.595 |
| DDoS_LOIC_HTTP | 72,382 | 0.999 / 0.263 | 0.999 / 0.263 | 0.999 / 0.263 | 0.998 / 1.000 | 0.998 / 1.000 |
| DoS_HULK | 79,013 | 0.941 / 0.936 | 0.941 / 0.936 | 0.941 / 0.936 | 0.941 / 0.980 | 0.941 / 0.980 |
| DoS_SlowHTTP | 26,387 | 1.000 / 0.643 | 0.000 / 0.000 | 0.000 / 0.000 | 1.000 / 0.068 | 1.000 / 0.068 |
| SQL_Injection | 26 | 0.500 / 0.000 | 0.500 / 0.000 | 0.269 / 0.013 | 0.385 / 0.000 | 0.385 / 0.000 |

**gnb, temporal split, per class, leaked test rows** (recall / precision):

| class | support | leaky | +8y | zero | fixA | dropIAT |
|---|---:|---|---|---|---|---|
| Benign | 197,191 | 0.004 / 0.999 | 0.008 / 0.061 | 0.007 / 0.057 | 0.005 / 1.000 | 0.005 / 1.000 |
| Bot | 35,830 | 0.000 / 0.000 | 0.000 / 0.000 | 0.000 / 0.000 | 0.000 / 0.000 | 0.000 / 0.000 |
| Brute_Force_Web | 66 | 0.000 / 0.000 | 0.000 / 0.000 | 0.000 / 0.000 | 0.000 / 0.000 | 0.000 / 0.000 |
| Brute_Force_XSS | 30 | 0.000 / 0.000 | 0.000 / 0.000 | 0.000 / 0.000 | 0.000 / 0.000 | 0.000 / 0.000 |
| DDoS_HOIC | 97,477 | 1.000 / 0.472 | 1.000 / 0.472 | 1.000 / 0.291 | 0.000 / 0.000 | 0.000 / 0.000 |
| DDoS_LOIC_HTTP | 0 | 0.000 / 0.000 | 0.000 / 0.000 | 0.000 / 0.000 | 0.000 / 0.000 | 0.000 / 0.000 |
| DoS_HULK | 2,698 | 0.000 / 0.000 | 0.000 / 0.000 | 0.000 / 0.000 | 0.000 / 0.000 | 0.000 / 0.000 |
| DoS_SlowHTTP | 26,387 | 1.000 / 0.643 | 0.000 / 0.000 | 0.000 / 0.000 | 1.000 / 0.077 | 1.000 / 0.077 |
| SQL_Injection | 14 | 0.429 / 0.000 | 0.429 / 0.000 | 0.000 / 0.000 | 0.000 / 0.000 | 0.000 / 0.000 |

**dt, random split, per class, all test rows** (recall / precision):

| class | support | leaky | +8y | zero | fixA | dropIAT |
|---|---:|---|---|---|---|---|
| Benign | 587,524 | 0.999 / 1.000 | 0.999 / 0.783 | 0.977 / 0.781 | 0.976 / 1.000 | 0.976 / 1.000 |
| Bot | 71,525 | 1.000 / 0.999 | 0.500 / 0.999 | 0.500 / 0.999 | 0.503 / 0.998 | 0.503 / 0.998 |
| Brute_Force_Web | 134 | 0.985 / 0.379 | 0.537 / 0.333 | 0.843 / 0.008 | 0.978 / 0.350 | 0.978 / 0.337 |
| Brute_Force_XSS | 58 | 0.948 / 0.270 | 0.586 / 0.391 | 0.586 / 0.391 | 0.966 / 0.475 | 0.966 / 0.514 |
| DDoS_HOIC | 250,176 | 1.000 / 1.000 | 0.498 / 1.000 | 0.498 / 1.000 | 1.000 / 0.875 | 1.000 / 0.875 |
| DDoS_LOIC_HTTP | 72,382 | 1.000 / 0.999 | 0.999 / 1.000 | 0.999 / 1.000 | 0.999 / 1.000 | 0.999 / 1.000 |
| DoS_HULK | 79,013 | 1.000 / 0.999 | 0.989 / 1.000 | 0.998 / 0.997 | 0.998 / 0.999 | 0.998 / 0.999 |
| DoS_SlowHTTP | 26,387 | 1.000 / 1.000 | 1.000 / 1.000 | 1.000 / 1.000 | 1.000 / 1.000 | 1.000 / 1.000 |
| SQL_Injection | 26 | 0.769 / 0.190 | 0.500 / 0.194 | 0.500 / 0.194 | 0.731 / 0.001 | 0.731 / 0.001 |

**dt, random split, per class, leaked test rows** (recall / precision):

| class | support | leaky | +8y | zero | fixA | dropIAT |
|---|---:|---|---|---|---|---|
| Benign | 209,648 | 0.998 / 1.000 | 1.000 / 0.564 | 0.937 / 0.549 | 0.935 / 0.999 | 0.935 / 0.999 |
| Bot | 35,787 | 1.000 / 0.999 | 0.000 / 0.000 | 0.000 / 0.000 | 0.007 / 0.813 | 0.007 / 0.816 |
| Brute_Force_Web | 62 | 0.968 / 0.455 | 0.000 / 0.000 | 0.661 / 0.003 | 0.952 / 0.248 | 0.952 / 0.248 |
| Brute_Force_XSS | 22 | 0.955 / 0.179 | 0.000 / 0.000 | 0.000 / 0.000 | 0.955 / 0.568 | 0.955 / 0.583 |
| DDoS_HOIC | 125,565 | 1.000 / 1.000 | 0.000 / 0.000 | 0.000 / 0.000 | 1.000 / 0.779 | 1.000 / 0.779 |
| DDoS_LOIC_HTTP | 50 | 1.000 / 0.521 | 0.000 / 0.000 | 0.000 / 0.000 | 0.000 / 0.000 | 0.000 / 0.000 |
| DoS_HULK | 886 | 0.998 / 0.932 | 0.019 / 0.773 | 0.825 / 0.744 | 0.825 / 0.952 | 0.825 / 0.952 |
| DoS_SlowHTTP | 26,387 | 1.000 / 1.000 | 1.000 / 1.000 | 1.000 / 1.000 | 1.000 / 1.000 | 1.000 / 1.000 |
| SQL_Injection | 11 | 0.636 / 0.184 | 0.000 / 0.000 | 0.000 / 0.000 | 0.455 / 0.000 | 0.455 / 0.000 |

**dt, temporal split, per class, all test rows** (recall / precision):

| class | support | leaky | +8y | zero | fixA | dropIAT |
|---|---:|---|---|---|---|---|
| Benign | 587,523 | 0.998 / 0.879 | 0.999 / 0.995 | 0.980 / 0.996 | 0.978 / 0.995 | 0.978 / 0.995 |
| Bot | 71,525 | 0.994 / 0.999 | 0.994 / 0.420 | 0.496 / 0.998 | 0.497 / 0.998 | 0.497 / 0.998 |
| Brute_Force_Web | 134 | 0.866 / 0.571 | 0.507 / 0.444 | 0.507 / 0.134 | 0.978 / 0.229 | 0.978 / 0.241 |
| Brute_Force_XSS | 58 | 0.914 / 0.639 | 0.414 / 0.522 | 0.414 / 0.522 | 0.966 / 0.106 | 0.966 / 0.090 |
| DDoS_HOIC | 250,175 | 0.690 / 1.000 | 0.610 / 1.000 | 0.610 / 1.000 | 1.000 / 0.876 | 1.000 / 0.876 |
| DDoS_LOIC_HTTP | 72,382 | 1.000 / 1.000 | 1.000 / 1.000 | 1.000 / 1.000 | 0.994 / 1.000 | 0.994 / 1.000 |
| DoS_HULK | 79,013 | 0.969 / 1.000 | 0.968 / 1.000 | 0.968 / 1.000 | 0.968 / 1.000 | 0.968 / 1.000 |
| DoS_SlowHTTP | 26,387 | 1.000 / 1.000 | 1.000 / 1.000 | 1.000 / 1.000 | 1.000 / 1.000 | 1.000 / 1.000 |
| SQL_Injection | 26 | 0.923 / 0.020 | 0.577 / 0.097 | 0.692 / 0.000 | 0.808 / 0.002 | 0.885 / 0.002 |

**dt, temporal split, per class, leaked test rows** (recall / precision):

| class | support | leaky | +8y | zero | fixA | dropIAT |
|---|---:|---|---|---|---|---|
| Benign | 197,191 | 0.994 / 0.710 | 0.997 / 0.986 | 0.943 / 0.989 | 0.938 / 0.988 | 0.938 / 0.988 |
| Bot | 35,830 | 0.993 / 1.000 | 0.993 / 0.266 | 0.000 / 0.000 | 0.009 / 0.845 | 0.009 / 0.845 |
| Brute_Force_Web | 66 | 0.727 / 0.649 | 0.000 / 0.000 | 0.000 / 0.000 | 0.955 / 0.504 | 0.955 / 0.504 |
| Brute_Force_XSS | 30 | 0.967 / 0.784 | 0.000 / 0.000 | 0.000 / 0.000 | 0.933 / 0.636 | 0.933 / 0.609 |
| DDoS_HOIC | 97,477 | 0.205 / 1.000 | 0.000 / 0.000 | 0.000 / 0.000 | 1.000 / 0.734 | 1.000 / 0.734 |
| DDoS_LOIC_HTTP | 0 | 0.000 / 0.000 | 0.000 / 0.000 | 0.000 / 0.000 | 0.000 / 0.000 | 0.000 / 0.000 |
| DoS_HULK | 2,698 | 0.093 / 1.000 | 0.070 / 1.000 | 0.070 / 1.000 | 0.070 / 1.000 | 0.079 / 0.995 |
| DoS_SlowHTTP | 26,387 | 1.000 / 1.000 | 1.000 / 1.000 | 1.000 / 1.000 | 1.000 / 1.000 | 1.000 / 1.000 |
| SQL_Injection | 14 | 1.000 / 0.013 | 0.357 / 0.088 | 0.571 / 0.000 | 0.857 / 0.001 | 0.857 / 0.001 |

**lr, random split, per class, all test rows** (recall / precision):

| class | support | leaky | +8y | zero | fixA |
|---|---:|---|---|---|---|
| Benign | 587,524 | 0.817 / 0.999 | 0.729 / 1.000 | 0.910 / 0.998 | 0.817 / 0.999 |
| Bot | 71,525 | 0.997 / 0.950 | 0.999 / 0.256 | 0.500 / 0.997 | 0.997 / 0.356 |
| Brute_Force_Web | 134 | 0.522 / 0.427 | 0.522 / 0.429 | 0.761 / 0.029 | 0.530 / 0.526 |
| Brute_Force_XSS | 58 | 0.966 / 0.010 | 0.603 / 0.001 | 0.603 / 0.921 | 0.966 / 0.010 |
| DDoS_HOIC | 250,176 | 1.000 / 0.847 | 0.498 / 0.999 | 0.498 / 0.999 | 0.498 / 0.732 |
| DDoS_LOIC_HTTP | 72,382 | 0.999 / 1.000 | 1.000 / 0.786 | 0.999 / 1.000 | 0.999 / 1.000 |
| DoS_HULK | 79,013 | 0.998 / 0.996 | 0.998 / 0.996 | 0.992 / 0.999 | 0.998 / 0.996 |
| DoS_SlowHTTP | 26,387 | 1.000 / 1.000 | 0.881 / 1.000 | 1.000 / 1.000 | 1.000 / 1.000 |
| SQL_Injection | 26 | 0.731 / 0.000 | 0.538 / 0.032 | 0.769 / 0.000 | 0.731 / 0.000 |

**lr, random split, per class, leaked test rows** (recall / precision):

| class | support | leaky | +8y | zero | fixA |
|---|---:|---|---|---|---|
| Benign | 209,648 | 0.490 / 0.998 | 0.243 / 1.000 | 0.752 / 0.995 | 0.490 / 0.998 |
| Bot | 35,787 | 0.993 / 0.908 | 0.997 / 0.147 | 0.000 / 0.000 | 0.993 / 0.216 |
| Brute_Force_Web | 62 | 0.000 / 0.000 | 0.000 / 0.000 | 0.516 / 0.009 | 0.000 / 0.000 |
| Brute_Force_XSS | 22 | 0.955 / 0.004 | 0.000 / 0.000 | 0.000 / 0.000 | 0.955 / 0.004 |
| DDoS_HOIC | 125,565 | 1.000 / 0.735 | 0.000 / 0.000 | 0.000 / 0.000 | 0.000 / 0.001 |
| DDoS_LOIC_HTTP | 50 | 0.000 / 0.000 | 1.000 / 0.003 | 0.000 / 0.000 | 0.000 / 0.000 |
| DoS_HULK | 886 | 0.825 / 0.750 | 0.824 / 0.749 | 0.257 / 0.966 | 0.825 / 0.763 |
| DoS_SlowHTTP | 26,387 | 1.000 / 1.000 | 0.881 / 1.000 | 1.000 / 1.000 | 1.000 / 1.000 |
| SQL_Injection | 11 | 0.455 / 0.000 | 0.000 / 0.000 | 0.545 / 0.000 | 0.455 / 0.000 |

**lr, temporal split, per class, all test rows** (recall / precision):

| class | support | leaky | +8y | zero | fixA |
|---|---:|---|---|---|---|
| Benign | 587,523 | 0.832 / 0.987 | 0.782 / 0.989 | 0.914 / 0.988 | 0.829 / 0.986 |
| Bot | 71,525 | 0.438 / 0.994 | 0.936 / 0.313 | 0.438 / 0.996 | 0.438 / 0.981 |
| Brute_Force_Web | 134 | 0.485 / 0.575 | 0.485 / 0.016 | 0.724 / 0.033 | 0.493 / 0.589 |
| Brute_Force_XSS | 58 | 0.966 / 0.019 | 0.517 / 0.001 | 0.483 / 0.259 | 0.966 / 0.011 |
| DDoS_HOIC | 250,175 | 1.000 / 0.751 | 0.610 / 1.000 | 0.610 / 1.000 | 1.000 / 0.753 |
| DDoS_LOIC_HTTP | 72,382 | 1.000 / 1.000 | 1.000 / 0.792 | 1.000 / 0.995 | 1.000 / 1.000 |
| DoS_HULK | 79,013 | 0.967 / 1.000 | 0.968 / 0.949 | 0.967 / 1.000 | 0.967 / 1.000 |
| DoS_SlowHTTP | 26,387 | 1.000 / 1.000 | 1.000 / 1.000 | 1.000 / 1.000 | 1.000 / 1.000 |
| SQL_Injection | 26 | 0.538 / 0.000 | 0.308 / 0.004 | 0.615 / 0.000 | 0.538 / 0.000 |

**lr, temporal split, per class, leaked test rows** (recall / precision):

| class | support | leaky | +8y | zero | fixA |
|---|---:|---|---|---|---|
| Benign | 197,191 | 0.503 / 0.979 | 0.353 / 0.992 | 0.746 / 0.987 | 0.493 / 0.978 |
| Bot | 35,830 | 0.000 / 0.000 | 0.994 / 0.195 | 0.000 / 0.000 | 0.000 / 0.000 |
| Brute_Force_Web | 66 | 0.000 / 0.000 | 0.000 / 0.000 | 0.485 / 0.011 | 0.000 / 0.000 |
| Brute_Force_XSS | 30 | 0.933 / 0.010 | 0.067 / 0.000 | 0.000 / 0.000 | 0.933 / 0.006 |
| DDoS_HOIC | 97,477 | 1.000 / 0.541 | 0.000 / 0.000 | 0.000 / 0.000 | 1.000 / 0.543 |
| DDoS_LOIC_HTTP | 0 | 0.000 / 0.000 | 0.000 / 0.000 | 0.000 / 0.000 | 0.000 / 0.000 |
| DoS_HULK | 2,698 | 0.068 / 0.984 | 0.091 / 0.056 | 0.067 / 0.958 | 0.066 / 0.937 |
| DoS_SlowHTTP | 26,387 | 1.000 / 1.000 | 1.000 / 1.000 | 1.000 / 1.000 | 1.000 / 1.000 |
| SQL_Injection | 14 | 0.429 / 0.000 | 0.000 / 0.000 | 0.571 / 0.000 | 0.429 / 0.000 |

**xgb, random split, per class, all test rows** (recall / precision):

| class | support | leaky | +8y | zero | fixA | dropIAT |
|---|---:|---|---|---|---|---|
| Benign | 587,524 | 1.000 / 1.000 | 0.998 / 0.999 | 1.000 / 0.784 | 0.971 / 1.000 | 0.971 / 1.000 |
| Bot | 71,525 | 1.000 / 1.000 | 1.000 / 0.361 | 0.500 / 1.000 | 0.503 / 0.989 | 0.503 / 0.989 |
| Brute_Force_Web | 134 | 0.993 / 0.858 | 0.537 / 0.960 | 0.537 / 0.960 | 0.970 / 0.331 | 0.970 / 0.330 |
| Brute_Force_XSS | 58 | 0.966 / 0.982 | 0.603 / 0.972 | 0.603 / 0.972 | 0.966 / 0.903 | 0.966 / 0.903 |
| DDoS_HOIC | 250,176 | 1.000 / 1.000 | 0.498 / 1.000 | 0.498 / 1.000 | 1.000 / 0.876 | 1.000 / 0.876 |
| DDoS_LOIC_HTTP | 72,382 | 0.999 / 1.000 | 0.999 / 1.000 | 0.999 / 1.000 | 0.999 / 1.000 | 0.999 / 1.000 |
| DoS_HULK | 79,013 | 1.000 / 1.000 | 0.992 / 1.000 | 0.998 / 0.999 | 0.998 / 1.000 | 0.998 / 1.000 |
| DoS_SlowHTTP | 26,387 | 1.000 / 1.000 | 1.000 / 1.000 | 1.000 / 1.000 | 1.000 / 1.000 | 1.000 / 1.000 |
| SQL_Injection | 26 | 0.962 / 0.625 | 0.538 / 0.824 | 0.538 / 0.824 | 0.885 / 0.001 | 0.885 / 0.001 |

**xgb, random split, per class, leaked test rows** (recall / precision):

| class | support | leaky | +8y | zero | fixA | dropIAT |
|---|---:|---|---|---|---|---|
| Benign | 209,648 | 0.999 / 1.000 | 0.996 / 0.997 | 1.000 / 0.565 | 0.919 / 0.999 | 0.919 / 0.999 |
| Bot | 35,787 | 1.000 / 0.999 | 1.000 / 0.220 | 0.000 / 0.000 | 0.007 / 0.396 | 0.007 / 0.396 |
| Brute_Force_Web | 62 | 0.984 / 0.762 | 0.000 / 0.000 | 0.000 / 0.000 | 0.935 / 0.182 | 0.935 / 0.182 |
| Brute_Force_XSS | 22 | 0.955 / 1.000 | 0.000 / 0.000 | 0.000 / 0.000 | 0.955 / 0.778 | 0.955 / 0.778 |
| DDoS_HOIC | 125,565 | 1.000 / 1.000 | 0.000 / 0.000 | 0.000 / 0.000 | 1.000 / 0.779 | 1.000 / 0.779 |
| DDoS_LOIC_HTTP | 50 | 0.000 / 0.000 | 0.000 / 0.000 | 0.000 / 0.000 | 0.000 / 0.000 | 0.000 / 0.000 |
| DoS_HULK | 886 | 0.994 / 0.966 | 0.257 / 0.996 | 0.825 / 0.884 | 0.825 / 0.992 | 0.825 / 0.992 |
| DoS_SlowHTTP | 26,387 | 1.000 / 1.000 | 1.000 / 1.000 | 1.000 / 1.000 | 1.000 / 1.000 | 1.000 / 1.000 |
| SQL_Injection | 11 | 1.000 / 0.478 | 0.000 / 0.000 | 0.000 / 0.000 | 0.727 / 0.000 | 0.727 / 0.000 |

**xgb, temporal split, per class, all test rows** (recall / precision):

| class | support | leaky | +8y | zero | fixA | dropIAT |
|---|---:|---|---|---|---|---|
| Benign | 587,523 | 0.998 / 0.994 | 0.999 / 0.994 | 1.000 / 0.811 | 0.974 / 0.990 | 0.974 / 0.989 |
| Bot | 71,525 | 0.982 / 1.000 | 0.982 / 0.418 | 0.484 / 1.000 | 0.451 / 0.990 | 0.445 / 0.990 |
| Brute_Force_Web | 134 | 0.970 / 0.963 | 0.493 / 0.930 | 0.493 / 0.930 | 0.978 / 0.369 | 0.978 / 0.368 |
| Brute_Force_XSS | 58 | 0.966 / 0.966 | 0.966 / 0.949 | 0.483 / 1.000 | 0.966 / 0.889 | 0.966 / 0.889 |
| DDoS_HOIC | 250,175 | 1.000 / 1.000 | 0.610 / 1.000 | 0.610 / 1.000 | 1.000 / 0.876 | 1.000 / 0.876 |
| DDoS_LOIC_HTTP | 72,382 | 1.000 / 1.000 | 1.000 / 1.000 | 1.000 / 1.000 | 1.000 / 1.000 | 1.000 / 1.000 |
| DoS_HULK | 79,013 | 0.970 / 1.000 | 0.968 / 1.000 | 0.968 / 1.000 | 0.968 / 1.000 | 0.968 / 1.000 |
| DoS_SlowHTTP | 26,387 | 1.000 / 1.000 | 1.000 / 1.000 | 1.000 / 1.000 | 1.000 / 1.000 | 1.000 / 1.000 |
| SQL_Injection | 26 | 0.923 / 0.017 | 0.577 / 0.333 | 0.385 / 0.909 | 0.923 / 0.002 | 0.923 / 0.002 |

**xgb, temporal split, per class, leaked test rows** (recall / precision):

| class | support | leaky | +8y | zero | fixA | dropIAT |
|---|---:|---|---|---|---|---|
| Benign | 197,191 | 0.993 / 0.987 | 0.998 / 0.986 | 1.000 / 0.592 | 0.922 / 0.988 | 0.922 / 0.988 |
| Bot | 35,830 | 0.994 / 1.000 | 0.994 / 0.267 | 0.000 / 0.000 | 0.010 / 0.539 | 0.010 / 0.539 |
| Brute_Force_Web | 66 | 0.970 / 1.000 | 0.000 / 0.000 | 0.000 / 0.000 | 0.955 / 0.223 | 0.955 / 0.223 |
| Brute_Force_XSS | 30 | 0.933 / 0.933 | 0.933 / 0.903 | 0.000 / 0.000 | 0.933 / 0.800 | 0.933 / 0.800 |
| DDoS_HOIC | 97,477 | 1.000 / 1.000 | 0.000 / 0.000 | 0.000 / 0.000 | 1.000 / 0.734 | 1.000 / 0.734 |
| DDoS_LOIC_HTTP | 0 | 0.000 / 0.000 | 0.000 / 0.000 | 0.000 / 0.000 | 0.000 / 0.000 | 0.000 / 0.000 |
| DoS_HULK | 2,698 | 0.119 / 1.000 | 0.071 / 1.000 | 0.078 / 1.000 | 0.078 / 1.000 | 0.078 / 1.000 |
| DoS_SlowHTTP | 26,387 | 1.000 / 1.000 | 1.000 / 1.000 | 1.000 / 1.000 | 1.000 / 1.000 | 1.000 / 1.000 |
| SQL_Injection | 14 | 1.000 / 0.010 | 0.357 / 0.147 | 0.000 / 0.000 | 1.000 / 0.001 | 1.000 / 0.001 |

**xgbfull, random split, per class, all test rows** (recall / precision):

| class | support | leaky | +8y | zero | fixA | dropIAT |
|---|---:|---|---|---|---|---|
| Benign | 587,524 | 1.000 / 1.000 | 0.997 / 0.999 | 1.000 / 0.784 | 0.971 / 1.000 | 0.971 / 1.000 |
| Bot | 71,525 | 1.000 / 1.000 | 1.000 / 0.353 | 0.500 / 1.000 | 0.503 / 0.989 | 0.503 / 0.989 |
| Brute_Force_Web | 134 | 0.993 / 0.924 | 0.537 / 1.000 | 0.537 / 1.000 | 0.970 / 0.339 | 0.970 / 0.339 |
| Brute_Force_XSS | 58 | 0.966 / 0.982 | 0.603 / 0.972 | 0.603 / 0.972 | 0.966 / 0.933 | 0.966 / 0.933 |
| DDoS_HOIC | 250,176 | 1.000 / 1.000 | 0.498 / 1.000 | 0.498 / 1.000 | 1.000 / 0.876 | 1.000 / 0.876 |
| DDoS_LOIC_HTTP | 72,382 | 0.999 / 1.000 | 0.999 / 1.000 | 0.999 / 1.000 | 0.999 / 1.000 | 0.999 / 1.000 |
| DoS_HULK | 79,013 | 1.000 / 0.999 | 0.991 / 1.000 | 0.998 / 0.999 | 0.998 / 1.000 | 0.998 / 1.000 |
| DoS_SlowHTTP | 26,387 | 1.000 / 1.000 | 0.865 / 1.000 | 1.000 / 1.000 | 1.000 / 1.000 | 1.000 / 1.000 |
| SQL_Injection | 26 | 1.000 / 0.839 | 0.577 / 0.882 | 0.577 / 0.882 | 0.885 / 0.001 | 0.885 / 0.001 |

**xgbfull, random split, per class, leaked test rows** (recall / precision):

| class | support | leaky | +8y | zero | fixA | dropIAT |
|---|---:|---|---|---|---|---|
| Benign | 209,648 | 0.999 / 1.000 | 0.991 / 0.997 | 1.000 / 0.565 | 0.920 / 0.999 | 0.920 / 0.999 |
| Bot | 35,787 | 1.000 / 0.999 | 1.000 / 0.214 | 0.000 / 0.000 | 0.007 / 0.397 | 0.007 / 0.397 |
| Brute_Force_Web | 62 | 0.984 / 0.847 | 0.000 / 0.000 | 0.000 / 0.000 | 0.935 / 0.187 | 0.935 / 0.187 |
| Brute_Force_XSS | 22 | 0.955 / 1.000 | 0.000 / 0.000 | 0.000 / 0.000 | 0.955 / 0.840 | 0.955 / 0.840 |
| DDoS_HOIC | 125,565 | 1.000 / 1.000 | 0.000 / 0.000 | 0.000 / 0.000 | 1.000 / 0.779 | 1.000 / 0.779 |
| DDoS_LOIC_HTTP | 50 | 0.000 / 0.000 | 0.000 / 0.000 | 0.000 / 0.000 | 0.000 / 0.000 | 0.000 / 0.000 |
| DoS_HULK | 886 | 0.994 / 0.894 | 0.242 / 1.000 | 0.825 / 0.937 | 0.825 / 0.997 | 0.825 / 0.997 |
| DoS_SlowHTTP | 26,387 | 1.000 / 1.000 | 0.865 / 1.000 | 1.000 / 1.000 | 1.000 / 1.000 | 1.000 / 1.000 |
| SQL_Injection | 11 | 1.000 / 0.786 | 0.000 / 0.000 | 0.000 / 0.000 | 0.727 / 0.000 | 0.727 / 0.000 |

**xgbfull, temporal split, per class, all test rows** (recall / precision):

| class | support | leaky | +8y | zero | fixA | dropIAT |
|---|---:|---|---|---|---|---|
| Benign | 587,523 | 0.999 / 0.959 | 0.999 / 0.988 | 1.000 / 0.810 | 0.974 / 0.988 | 0.974 / 0.988 |
| Bot | 71,525 | 0.969 / 1.000 | 0.969 / 0.413 | 0.471 / 1.000 | 0.445 / 0.991 | 0.445 / 0.991 |
| Brute_Force_Web | 134 | 0.970 / 0.992 | 0.493 / 1.000 | 0.493 / 1.000 | 0.978 / 0.388 | 0.978 / 0.388 |
| Brute_Force_XSS | 58 | 0.966 / 1.000 | 0.724 / 1.000 | 0.483 / 1.000 | 0.966 / 0.889 | 0.966 / 0.889 |
| DDoS_HOIC | 250,175 | 0.919 / 1.000 | 0.610 / 1.000 | 0.610 / 1.000 | 1.000 / 0.876 | 1.000 / 0.876 |
| DDoS_LOIC_HTTP | 72,382 | 1.000 / 1.000 | 1.000 / 1.000 | 1.000 / 1.000 | 1.000 / 1.000 | 1.000 / 1.000 |
| DoS_HULK | 79,013 | 0.970 / 1.000 | 0.968 / 1.000 | 0.968 / 1.000 | 0.968 / 1.000 | 0.968 / 1.000 |
| DoS_SlowHTTP | 26,387 | 1.000 / 1.000 | 0.894 / 1.000 | 1.000 / 1.000 | 1.000 / 1.000 | 1.000 / 1.000 |
| SQL_Injection | 26 | 0.923 / 0.036 | 0.577 / 0.349 | 0.385 / 0.909 | 0.923 / 0.002 | 0.923 / 0.002 |

**xgbfull, temporal split, per class, leaked test rows** (recall / precision):

| class | support | leaky | +8y | zero | fixA | dropIAT |
|---|---:|---|---|---|---|---|
| Benign | 197,191 | 0.997 / 0.896 | 0.998 / 0.975 | 1.000 / 0.592 | 0.922 / 0.986 | 0.922 / 0.986 |
| Bot | 35,830 | 0.994 / 1.000 | 0.994 / 0.266 | 0.000 / 0.000 | 0.010 / 0.569 | 0.010 / 0.569 |
| Brute_Force_Web | 66 | 0.970 / 0.985 | 0.000 / 0.000 | 0.000 / 0.000 | 0.955 / 0.233 | 0.955 / 0.233 |
| Brute_Force_XSS | 30 | 0.933 / 1.000 | 0.467 / 1.000 | 0.000 / 0.000 | 0.933 / 0.800 | 0.933 / 0.800 |
| DDoS_HOIC | 97,477 | 0.792 / 1.000 | 0.000 / 0.000 | 0.000 / 0.000 | 1.000 / 0.734 | 1.000 / 0.734 |
| DDoS_LOIC_HTTP | 0 | 0.000 / 0.000 | 0.000 / 0.000 | 0.000 / 0.000 | 0.000 / 0.000 | 0.000 / 0.000 |
| DoS_HULK | 2,698 | 0.112 / 1.000 | 0.070 / 1.000 | 0.070 / 1.000 | 0.076 / 1.000 | 0.073 / 1.000 |
| DoS_SlowHTTP | 26,387 | 1.000 / 1.000 | 0.894 / 1.000 | 1.000 / 1.000 | 1.000 / 1.000 | 1.000 / 1.000 |
| SQL_Injection | 14 | 1.000 / 0.021 | 0.357 / 0.156 | 0.000 / 0.000 | 1.000 / 0.001 | 1.000 / 0.001 |

**rf, random split, per class, all test rows** (recall / precision):

| class | support | leaky | +8y | zero | fixA | dropIAT |
|---|---:|---|---|---|---|---|
| Benign | 587,524 | 0.991 / 1.000 | 0.988 / 0.782 | 1.000 / 0.784 | 0.901 / 1.000 | 0.815 / 1.000 |
| Bot | 71,525 | 1.000 / 0.972 | 0.500 / 0.837 | 0.500 / 1.000 | 1.000 / 0.362 | 1.000 / 0.289 |
| Brute_Force_Web | 134 | 1.000 / 0.258 | 0.537 / 0.889 | 0.537 / 0.889 | 0.851 / 0.161 | 0.851 / 0.165 |
| Brute_Force_XSS | 58 | 0.983 / 0.141 | 0.603 / 1.000 | 0.603 / 1.000 | 0.966 / 0.615 | 0.966 / 0.086 |
| DDoS_HOIC | 250,176 | 1.000 / 0.993 | 0.498 / 1.000 | 0.498 / 1.000 | 0.498 / 1.000 | 0.498 / 1.000 |
| DDoS_LOIC_HTTP | 72,382 | 1.000 / 1.000 | 0.999 / 1.000 | 0.999 / 1.000 | 0.999 / 1.000 | 0.999 / 1.000 |
| DoS_HULK | 79,013 | 1.000 / 0.999 | 0.991 / 1.000 | 0.998 / 0.997 | 0.998 / 0.997 | 0.998 / 0.997 |
| DoS_SlowHTTP | 26,387 | 1.000 / 1.000 | 1.000 / 1.000 | 1.000 / 1.000 | 1.000 / 1.000 | 1.000 / 1.000 |
| SQL_Injection | 26 | 1.000 / 0.075 | 0.577 / 0.833 | 0.577 / 0.833 | 0.769 / 0.000 | 0.731 / 0.000 |

**rf, random split, per class, leaked test rows** (recall / precision):

| class | support | leaky | +8y | zero | fixA | dropIAT |
|---|---:|---|---|---|---|---|
| Benign | 209,648 | 0.976 / 1.000 | 0.967 / 0.556 | 0.999 / 0.564 | 0.723 / 0.999 | 0.481 / 0.998 |
| Bot | 35,787 | 1.000 / 0.945 | 0.002 / 0.008 | 0.000 / 0.000 | 0.999 / 0.221 | 0.999 / 0.169 |
| Brute_Force_Web | 62 | 1.000 / 0.141 | 0.000 / 0.000 | 0.000 / 0.000 | 0.677 / 0.067 | 0.677 / 0.069 |
| Brute_Force_XSS | 22 | 1.000 / 0.059 | 0.000 / 0.000 | 0.000 / 0.000 | 0.955 / 0.375 | 0.955 / 0.034 |
| DDoS_HOIC | 125,565 | 1.000 / 0.986 | 0.000 / 0.000 | 0.000 / 0.000 | 0.000 / 0.000 | 0.000 / 0.000 |
| DDoS_LOIC_HTTP | 50 | 0.900 / 0.662 | 0.000 / 0.000 | 0.000 / 0.000 | 0.000 / 0.000 | 0.000 / 0.000 |
| DoS_HULK | 886 | 0.994 / 0.954 | 0.172 / 1.000 | 0.825 / 0.769 | 0.825 / 0.769 | 0.825 / 0.778 |
| DoS_SlowHTTP | 26,387 | 1.000 / 1.000 | 1.000 / 1.000 | 1.000 / 1.000 | 1.000 / 1.000 | 1.000 / 1.000 |
| SQL_Injection | 11 | 1.000 / 0.034 | 0.000 / 0.000 | 0.000 / 0.000 | 0.455 / 0.000 | 0.455 / 0.000 |

**rf, temporal split, per class, all test rows** (recall / precision):

| class | support | leaky | +8y | zero | fixA | dropIAT |
|---|---:|---|---|---|---|---|
| Benign | 587,523 | 0.997 / 0.835 | 1.000 / 0.812 | 1.000 / 0.812 | 0.823 / 0.994 | 0.885 / 0.994 |
| Bot | 71,525 | 0.502 / 1.000 | 0.498 / 1.000 | 0.498 / 1.000 | 0.502 / 0.998 | 0.498 / 0.999 |
| Brute_Force_Web | 134 | 0.724 / 0.924 | 0.493 / 0.892 | 0.493 / 0.892 | 0.731 / 0.925 | 0.851 / 0.432 |
| Brute_Force_XSS | 58 | 0.914 / 0.964 | 0.483 / 0.933 | 0.483 / 0.933 | 0.966 / 0.022 | 0.966 / 0.022 |
| DDoS_HOIC | 250,175 | 0.690 / 1.000 | 0.610 / 1.000 | 0.610 / 1.000 | 1.000 / 0.748 | 1.000 / 0.749 |
| DDoS_LOIC_HTTP | 72,382 | 1.000 / 1.000 | 1.000 / 1.000 | 1.000 / 1.000 | 1.000 / 1.000 | 1.000 / 1.000 |
| DoS_HULK | 79,013 | 0.968 / 1.000 | 0.968 / 1.000 | 0.968 / 1.000 | 0.968 / 1.000 | 0.968 / 1.000 |
| DoS_SlowHTTP | 26,387 | 1.000 / 1.000 | 1.000 / 1.000 | 1.000 / 1.000 | 1.000 / 1.000 | 1.000 / 1.000 |
| SQL_Injection | 26 | 0.962 / 0.012 | 0.423 / 0.458 | 0.423 / 0.458 | 0.654 / 0.000 | 0.654 / 0.001 |

**rf, temporal split, per class, leaked test rows** (recall / precision):

| class | support | leaky | +8y | zero | fixA | dropIAT |
|---|---:|---|---|---|---|---|
| Benign | 197,191 | 0.990 / 0.628 | 1.000 / 0.592 | 1.000 / 0.592 | 0.473 / 0.972 | 0.659 / 0.979 |
| Bot | 35,830 | 0.009 / 1.000 | 0.000 / 0.000 | 0.000 / 0.000 | 0.009 / 0.837 | 0.008 / 0.881 |
| Brute_Force_Web | 66 | 0.470 / 1.000 | 0.000 / 0.000 | 0.000 / 0.000 | 0.485 / 1.000 | 0.727 / 0.251 |
| Brute_Force_XSS | 30 | 0.833 / 1.000 | 0.000 / 0.000 | 0.000 / 0.000 | 0.933 / 0.011 | 0.933 / 0.011 |
| DDoS_HOIC | 97,477 | 0.205 / 1.000 | 0.000 / 0.000 | 0.000 / 0.000 | 1.000 / 0.537 | 1.000 / 0.537 |
| DDoS_LOIC_HTTP | 0 | 0.000 / 0.000 | 0.000 / 0.000 | 0.000 / 0.000 | 0.000 / 0.000 | 0.000 / 0.000 |
| DoS_HULK | 2,698 | 0.088 / 1.000 | 0.066 / 1.000 | 0.066 / 1.000 | 0.066 / 1.000 | 0.066 / 1.000 |
| DoS_SlowHTTP | 26,387 | 1.000 / 1.000 | 1.000 / 1.000 | 1.000 / 1.000 | 1.000 / 1.000 | 1.000 / 1.000 |
| SQL_Injection | 14 | 1.000 / 0.007 | 0.000 / 0.000 | 0.000 / 0.000 | 0.429 / 0.000 | 0.429 / 0.000 |

**rffull, random split, per class, all test rows** (recall / precision):

| class | support | leaky | +8y | zero | fixA | dropIAT |
|---|---:|---|---|---|---|---|
| Benign | 587,524 | 0.997 / 1.000 | 1.000 / 0.784 | 1.000 / 0.784 | 0.969 / 1.000 | 0.976 / 1.000 |
| Bot | 71,525 | 1.000 / 0.992 | 0.500 / 1.000 | 0.500 / 1.000 | 0.503 / 0.998 | 0.503 / 0.998 |
| Brute_Force_Web | 134 | 0.993 / 0.358 | 0.537 / 0.889 | 0.537 / 0.889 | 0.978 / 0.430 | 0.978 / 0.425 |
| Brute_Force_XSS | 58 | 0.966 / 0.283 | 0.603 / 1.000 | 0.603 / 1.000 | 0.966 / 0.933 | 0.966 / 0.800 |
| DDoS_HOIC | 250,176 | 1.000 / 0.996 | 0.498 / 1.000 | 0.498 / 1.000 | 1.000 / 0.876 | 1.000 / 0.876 |
| DDoS_LOIC_HTTP | 72,382 | 1.000 / 1.000 | 0.999 / 1.000 | 0.999 / 1.000 | 0.999 / 1.000 | 0.999 / 1.000 |
| DoS_HULK | 79,013 | 1.000 / 1.000 | 0.991 / 1.000 | 0.993 / 1.000 | 0.998 / 0.997 | 0.998 / 0.997 |
| DoS_SlowHTTP | 26,387 | 1.000 / 1.000 | 1.000 / 1.000 | 1.000 / 1.000 | 1.000 / 1.000 | 1.000 / 1.000 |
| SQL_Injection | 26 | 0.923 / 0.308 | 0.577 / 1.000 | 0.577 / 1.000 | 0.731 / 0.001 | 0.731 / 0.001 |

**rffull, random split, per class, leaked test rows** (recall / precision):

| class | support | leaky | +8y | zero | fixA | dropIAT |
|---|---:|---|---|---|---|---|
| Benign | 209,648 | 0.990 / 1.000 | 1.000 / 0.564 | 1.000 / 0.564 | 0.913 / 0.999 | 0.934 / 0.999 |
| Bot | 35,787 | 1.000 / 0.985 | 0.002 / 0.983 | 0.000 / 0.000 | 0.007 / 0.746 | 0.007 / 0.743 |
| Brute_Force_Web | 62 | 0.984 / 0.210 | 0.000 / 0.000 | 0.000 / 0.000 | 0.952 / 0.263 | 0.952 / 0.262 |
| Brute_Force_XSS | 22 | 0.955 / 0.129 | 0.000 / 0.000 | 0.000 / 0.000 | 0.955 / 0.840 | 0.955 / 0.600 |
| DDoS_HOIC | 125,565 | 1.000 / 0.992 | 0.000 / 0.000 | 0.000 / 0.000 | 1.000 / 0.779 | 1.000 / 0.779 |
| DDoS_LOIC_HTTP | 50 | 0.900 / 0.662 | 0.000 / 0.000 | 0.000 / 0.000 | 0.000 / 0.000 | 0.000 / 0.000 |
| DoS_HULK | 886 | 0.994 / 0.980 | 0.176 / 1.000 | 0.410 / 0.965 | 0.825 / 0.778 | 0.825 / 0.769 |
| DoS_SlowHTTP | 26,387 | 1.000 / 1.000 | 1.000 / 1.000 | 1.000 / 1.000 | 1.000 / 1.000 | 1.000 / 1.000 |
| SQL_Injection | 11 | 0.818 / 0.143 | 0.000 / 0.000 | 0.000 / 0.000 | 0.455 / 0.000 | 0.455 / 0.000 |

**rffull, temporal split, per class, all test rows** (recall / precision):

| class | support | leaky | +8y | zero | fixA | dropIAT |
|---|---:|---|---|---|---|---|
| Benign | 587,523 | 0.997 / 0.835 | 1.000 / 0.812 | 1.000 / 0.812 | 0.999 / 0.995 | 0.999 / 0.988 |
| Bot | 71,525 | 0.502 / 1.000 | 0.498 / 1.000 | 0.498 / 1.000 | 0.503 / 0.999 | 0.445 / 0.999 |
| Brute_Force_Web | 134 | 0.507 / 0.919 | 0.493 / 0.917 | 0.493 / 0.917 | 0.978 / 0.550 | 0.978 / 0.555 |
| Brute_Force_XSS | 58 | 0.586 / 0.971 | 0.483 / 0.966 | 0.483 / 0.966 | 0.966 / 0.315 | 0.966 / 0.316 |
| DDoS_HOIC | 250,175 | 0.690 / 1.000 | 0.610 / 1.000 | 0.610 / 1.000 | 1.000 / 0.876 | 1.000 / 0.876 |
| DDoS_LOIC_HTTP | 72,382 | 1.000 / 1.000 | 1.000 / 1.000 | 1.000 / 1.000 | 1.000 / 1.000 | 1.000 / 1.000 |
| DoS_HULK | 79,013 | 0.968 / 1.000 | 0.968 / 1.000 | 0.968 / 1.000 | 0.968 / 1.000 | 0.968 / 1.000 |
| DoS_SlowHTTP | 26,387 | 1.000 / 1.000 | 1.000 / 1.000 | 1.000 / 1.000 | 1.000 / 1.000 | 1.000 / 1.000 |
| SQL_Injection | 26 | 0.962 / 0.013 | 0.423 / 0.688 | 0.423 / 0.688 | 0.615 / 0.094 | 0.615 / 0.092 |

**rffull, temporal split, per class, leaked test rows** (recall / precision):

| class | support | leaky | +8y | zero | fixA | dropIAT |
|---|---:|---|---|---|---|---|
| Benign | 197,191 | 0.991 / 0.628 | 1.000 / 0.592 | 1.000 / 0.592 | 0.998 / 0.986 | 0.998 / 0.986 |
| Bot | 35,830 | 0.009 / 1.000 | 0.000 / 0.000 | 0.000 / 0.000 | 0.010 / 0.916 | 0.010 / 0.911 |
| Brute_Force_Web | 66 | 0.030 / 1.000 | 0.000 / 0.000 | 0.000 / 0.000 | 0.955 / 0.409 | 0.955 / 0.409 |
| Brute_Force_XSS | 30 | 0.200 / 1.000 | 0.000 / 0.000 | 0.000 / 0.000 | 0.933 / 0.187 | 0.933 / 0.189 |
| DDoS_HOIC | 97,477 | 0.205 / 1.000 | 0.000 / 0.000 | 0.000 / 0.000 | 1.000 / 0.734 | 1.000 / 0.734 |
| DDoS_LOIC_HTTP | 0 | 0.000 / 0.000 | 0.000 / 0.000 | 0.000 / 0.000 | 0.000 / 0.000 | 0.000 / 0.000 |
| DoS_HULK | 2,698 | 0.088 / 1.000 | 0.066 / 1.000 | 0.066 / 1.000 | 0.066 / 1.000 | 0.066 / 1.000 |
| DoS_SlowHTTP | 26,387 | 1.000 / 1.000 | 1.000 / 1.000 | 1.000 / 1.000 | 1.000 / 1.000 | 1.000 / 1.000 |
| SQL_Injection | 14 | 1.000 / 0.008 | 0.000 / 0.000 | 0.000 / 0.000 | 0.357 / 0.032 | 0.357 / 0.032 |

**mlp, random split, per class, all test rows** (recall / precision):

| class | support | leaky | +8y | zero | fixA | dropIAT |
|---|---:|---|---|---|---|---|
| Benign | 587,524 | 0.912 / 0.999 | 0.912 / 0.999 | 1.000 / 0.784 | 0.913 / 0.999 | 0.912 / 0.999 |
| Bot | 71,525 | 0.500 / 1.000 | 0.500 / 1.000 | 0.500 / 1.000 | 0.500 / 1.000 | 0.500 / 1.000 |
| Brute_Force_Web | 134 | 0.537 / 0.923 | 0.537 / 0.923 | 0.537 / 0.923 | 0.537 / 0.900 | 0.537 / 0.857 |
| Brute_Force_XSS | 58 | 0.586 / 0.694 | 0.586 / 0.694 | 0.586 / 0.694 | 0.586 / 1.000 | 0.586 / 0.872 |
| DDoS_HOIC | 250,176 | 1.000 / 0.742 | 1.000 / 0.741 | 0.498 / 1.000 | 1.000 / 0.742 | 1.000 / 0.742 |
| DDoS_LOIC_HTTP | 72,382 | 0.999 / 1.000 | 0.999 / 1.000 | 0.999 / 1.000 | 0.999 / 1.000 | 0.999 / 1.000 |
| DoS_HULK | 79,013 | 0.998 / 0.997 | 0.998 / 0.997 | 0.992 / 1.000 | 0.998 / 0.998 | 0.998 / 0.997 |
| DoS_SlowHTTP | 26,387 | 1.000 / 1.000 | 1.000 / 1.000 | 1.000 / 0.999 | 1.000 / 1.000 | 1.000 / 1.000 |
| SQL_Injection | 26 | 0.269 / 0.500 | 0.269 / 0.500 | 0.269 / 0.500 | 0.231 / 0.750 | 0.192 / 1.000 |

**mlp, random split, per class, leaked test rows** (recall / precision):

| class | support | leaky | +8y | zero | fixA | dropIAT |
|---|---:|---|---|---|---|---|
| Benign | 209,648 | 0.755 / 0.998 | 0.753 / 0.998 | 1.000 / 0.564 | 0.755 / 0.998 | 0.754 / 0.998 |
| Bot | 35,787 | 0.000 / 0.000 | 0.000 / 0.000 | 0.000 / 0.000 | 0.001 / 1.000 | 0.000 / 0.000 |
| Brute_Force_Web | 62 | 0.000 / 0.000 | 0.000 / 0.000 | 0.000 / 0.000 | 0.000 / 0.000 | 0.000 / 0.000 |
| Brute_Force_XSS | 22 | 0.000 / 0.000 | 0.000 / 0.000 | 0.000 / 0.000 | 0.000 / 0.000 | 0.000 / 0.000 |
| DDoS_HOIC | 125,565 | 1.000 / 0.591 | 1.000 / 0.590 | 0.000 / 0.000 | 1.000 / 0.591 | 1.000 / 0.590 |
| DDoS_LOIC_HTTP | 50 | 0.000 / 0.000 | 0.000 / 0.000 | 0.000 / 0.000 | 0.000 / 0.000 | 0.000 / 0.000 |
| DoS_HULK | 886 | 0.825 / 0.776 | 0.825 / 0.776 | 0.257 / 0.991 | 0.823 / 0.818 | 0.825 / 0.777 |
| DoS_SlowHTTP | 26,387 | 1.000 / 1.000 | 1.000 / 1.000 | 1.000 / 0.999 | 1.000 / 1.000 | 1.000 / 1.000 |
| SQL_Injection | 11 | 0.000 / 0.000 | 0.000 / 0.000 | 0.000 / 0.000 | 0.000 / 0.000 | 0.000 / 0.000 |

**mlp, temporal split, per class, all test rows** (recall / precision):

| class | support | leaky | +8y | zero | fixA | dropIAT |
|---|---:|---|---|---|---|---|
| Benign | 587,523 | 0.917 / 0.987 | 0.917 / 0.987 | 0.999 / 0.807 | 0.917 / 0.987 | 0.916 / 0.987 |
| Bot | 71,525 | 0.438 / 0.996 | 0.438 / 0.996 | 0.438 / 0.996 | 0.438 / 1.000 | 0.439 / 1.000 |
| Brute_Force_Web | 134 | 0.493 / 0.857 | 0.493 / 0.857 | 0.493 / 0.857 | 0.493 / 0.868 | 0.493 / 0.943 |
| Brute_Force_XSS | 58 | 0.483 / 0.778 | 0.483 / 0.778 | 0.483 / 0.778 | 0.483 / 1.000 | 0.483 / 1.000 |
| DDoS_HOIC | 250,175 | 1.000 / 0.747 | 1.000 / 0.747 | 0.610 / 0.999 | 1.000 / 0.747 | 1.000 / 0.747 |
| DDoS_LOIC_HTTP | 72,382 | 1.000 / 1.000 | 1.000 / 1.000 | 1.000 / 1.000 | 1.000 / 1.000 | 1.000 / 1.000 |
| DoS_HULK | 79,013 | 0.967 / 1.000 | 0.967 / 1.000 | 0.967 / 1.000 | 0.967 / 1.000 | 0.967 / 1.000 |
| DoS_SlowHTTP | 26,387 | 1.000 / 1.000 | 1.000 / 1.000 | 1.000 / 0.991 | 1.000 / 1.000 | 1.000 / 0.999 |
| SQL_Injection | 26 | 0.192 / 1.000 | 0.192 / 1.000 | 0.192 / 1.000 | 0.154 / 1.000 | 0.192 / 1.000 |

**mlp, temporal split, per class, leaked test rows** (recall / precision):

| class | support | leaky | +8y | zero | fixA | dropIAT |
|---|---:|---|---|---|---|---|
| Benign | 197,191 | 0.752 / 0.982 | 0.752 / 0.982 | 0.998 / 0.592 | 0.752 / 0.982 | 0.751 / 0.982 |
| Bot | 35,830 | 0.000 / 0.000 | 0.000 / 0.000 | 0.000 / 0.000 | 0.000 / 0.000 | 0.000 / 0.000 |
| Brute_Force_Web | 66 | 0.000 / 0.000 | 0.000 / 0.000 | 0.000 / 0.000 | 0.000 / 0.000 | 0.000 / 0.000 |
| Brute_Force_XSS | 30 | 0.000 / 0.000 | 0.000 / 0.000 | 0.000 / 0.000 | 0.000 / 0.000 | 0.000 / 0.000 |
| DDoS_HOIC | 97,477 | 1.000 / 0.535 | 1.000 / 0.535 | 0.000 / 0.000 | 1.000 / 0.535 | 1.000 / 0.535 |
| DDoS_LOIC_HTTP | 0 | 0.000 / 0.000 | 0.000 / 0.000 | 0.000 / 0.000 | 0.000 / 0.000 | 0.000 / 0.000 |
| DoS_HULK | 2,698 | 0.066 / 1.000 | 0.066 / 1.000 | 0.066 / 1.000 | 0.066 / 0.989 | 0.066 / 1.000 |
| DoS_SlowHTTP | 26,387 | 1.000 / 1.000 | 1.000 / 1.000 | 1.000 / 0.991 | 1.000 / 1.000 | 1.000 / 0.999 |
| SQL_Injection | 14 | 0.000 / 0.000 | 0.000 / 0.000 | 0.000 / 0.000 | 0.000 / 0.000 | 0.000 / 0.000 |

**knn, random split, per class, all test rows** (recall / precision):

| class | support | leaky | +8y | zero | fixA | dropIAT |
|---|---:|---|---|---|---|---|
| Benign | 587,524 | 1.000 / 1.000 | 0.999 / 0.784 | 0.904 / 0.999 | 1.000 / 1.000 | 1.000 / 1.000 |
| Bot | 71,525 | 1.000 / 1.000 | 0.503 / 0.978 | 0.500 / 1.000 | 1.000 / 0.363 | 1.000 / 0.363 |
| Brute_Force_Web | 134 | 1.000 / 0.937 | 0.537 / 0.960 | 0.858 / 0.001 | 0.985 / 0.923 | 0.985 / 0.923 |
| Brute_Force_XSS | 58 | 0.983 / 0.877 | 0.603 / 0.921 | 0.603 / 0.921 | 0.966 / 0.875 | 0.966 / 0.875 |
| DDoS_HOIC | 250,176 | 1.000 / 1.000 | 0.498 / 1.000 | 0.498 / 1.000 | 0.498 / 1.000 | 0.498 / 1.000 |
| DDoS_LOIC_HTTP | 72,382 | 0.999 / 1.000 | 0.999 / 1.000 | 0.999 / 1.000 | 0.999 / 1.000 | 0.999 / 1.000 |
| DoS_HULK | 79,013 | 0.999 / 1.000 | 0.992 / 1.000 | 0.993 / 1.000 | 0.998 / 1.000 | 0.998 / 1.000 |
| DoS_SlowHTTP | 26,387 | 1.000 / 1.000 | 1.000 / 1.000 | 1.000 / 1.000 | 1.000 / 1.000 | 1.000 / 1.000 |
| SQL_Injection | 26 | 0.923 / 0.686 | 0.500 / 0.722 | 0.500 / 0.722 | 0.615 / 0.667 | 0.615 / 0.696 |

**knn, random split, per class, leaked test rows** (recall / precision):

| class | support | leaky | +8y | zero | fixA | dropIAT |
|---|---:|---|---|---|---|---|
| Benign | 209,648 | 1.000 / 0.999 | 0.996 / 0.563 | 0.732 / 0.996 | 1.000 / 0.999 | 1.000 / 0.999 |
| Bot | 35,787 | 0.999 / 1.000 | 0.007 / 0.240 | 0.000 / 0.000 | 0.999 / 0.222 | 0.999 / 0.222 |
| Brute_Force_Web | 62 | 1.000 / 0.912 | 0.000 / 0.000 | 0.694 / 0.000 | 0.968 / 0.882 | 0.968 / 0.882 |
| Brute_Force_XSS | 22 | 1.000 / 0.815 | 0.000 / 0.000 | 0.000 / 0.000 | 0.955 / 0.808 | 0.955 / 0.808 |
| DDoS_HOIC | 125,565 | 1.000 / 1.000 | 0.000 / 0.000 | 0.000 / 0.000 | 0.000 / 0.744 | 0.000 / 0.744 |
| DDoS_LOIC_HTTP | 50 | 0.000 / 0.000 | 0.000 / 0.000 | 0.000 / 0.000 | 0.000 / 0.000 | 0.000 / 0.000 |
| DoS_HULK | 886 | 0.947 / 0.982 | 0.257 / 0.987 | 0.407 / 0.965 | 0.825 / 0.991 | 0.825 / 0.991 |
| DoS_SlowHTTP | 26,387 | 1.000 / 1.000 | 1.000 / 1.000 | 1.000 / 1.000 | 1.000 / 1.000 | 1.000 / 1.000 |
| SQL_Injection | 11 | 1.000 / 0.647 | 0.000 / 0.000 | 0.000 / 0.000 | 0.273 / 0.500 | 0.273 / 0.500 |

**knn, temporal split, per class, all test rows** (recall / precision):

| class | support | leaky | +8y | zero | fixA | dropIAT |
|---|---:|---|---|---|---|---|
| Benign | 587,523 | 1.000 / 0.988 | 1.000 / 0.807 | 0.914 / 0.987 | 1.000 / 0.988 | 1.000 / 0.988 |
| Bot | 71,525 | 0.935 / 1.000 | 0.443 / 0.995 | 0.438 / 1.000 | 0.935 / 0.407 | 0.935 / 0.407 |
| Brute_Force_Web | 134 | 0.985 / 0.950 | 0.507 / 0.958 | 0.866 / 0.001 | 0.978 / 0.929 | 0.970 / 0.935 |
| Brute_Force_XSS | 58 | 0.966 / 0.789 | 0.483 / 0.903 | 0.483 / 0.903 | 0.966 / 0.918 | 0.966 / 0.903 |
| DDoS_HOIC | 250,175 | 1.000 / 1.000 | 0.610 / 1.000 | 0.610 / 1.000 | 0.610 / 1.000 | 0.610 / 1.000 |
| DDoS_LOIC_HTTP | 72,382 | 1.000 / 1.000 | 1.000 / 1.000 | 1.000 / 1.000 | 1.000 / 1.000 | 1.000 / 1.000 |
| DoS_HULK | 79,013 | 0.967 / 1.000 | 0.967 / 1.000 | 0.967 / 1.000 | 0.967 / 1.000 | 0.967 / 1.000 |
| DoS_SlowHTTP | 26,387 | 1.000 / 1.000 | 1.000 / 1.000 | 1.000 / 1.000 | 1.000 / 1.000 | 1.000 / 1.000 |
| SQL_Injection | 26 | 0.808 / 0.333 | 0.269 / 0.412 | 0.269 / 0.412 | 0.538 / 0.275 | 0.538 / 0.286 |

**knn, temporal split, per class, leaked test rows** (recall / precision):

| class | support | leaky | +8y | zero | fixA | dropIAT |
|---|---:|---|---|---|---|---|
| Benign | 197,191 | 1.000 / 0.986 | 0.999 / 0.592 | 0.744 / 0.982 | 1.000 / 0.986 | 1.000 / 0.986 |
| Bot | 35,830 | 0.993 / 1.000 | 0.010 / 0.701 | 0.000 / 0.000 | 0.992 / 0.267 | 0.992 / 0.267 |
| Brute_Force_Web | 66 | 0.970 / 0.941 | 0.000 / 0.000 | 0.727 / 0.000 | 0.955 / 0.900 | 0.955 / 0.900 |
| Brute_Force_XSS | 30 | 0.933 / 0.700 | 0.000 / 0.000 | 0.000 / 0.000 | 0.933 / 0.933 | 0.933 / 0.933 |
| DDoS_HOIC | 97,477 | 1.000 / 1.000 | 0.000 / 0.000 | 0.000 / 0.000 | 0.000 / 0.875 | 0.000 / 0.875 |
| DDoS_LOIC_HTTP | 0 | 0.000 / 0.000 | 0.000 / 0.000 | 0.000 / 0.000 | 0.000 / 0.000 | 0.000 / 0.000 |
| DoS_HULK | 2,698 | 0.066 / 0.994 | 0.066 / 0.994 | 0.066 / 1.000 | 0.066 / 1.000 | 0.066 / 1.000 |
| DoS_SlowHTTP | 26,387 | 1.000 / 1.000 | 1.000 / 1.000 | 1.000 / 1.000 | 1.000 / 1.000 | 1.000 / 1.000 |
| SQL_Injection | 14 | 1.000 / 0.304 | 0.000 / 0.000 | 0.000 / 0.000 | 0.500 / 0.206 | 0.500 / 0.206 |

### 4.2 BCCC-CIC-IDS-2017

**Overall** (all test rows, then leaked test rows):

| model | split | condition | accuracy (all) [95% CI] | macro F1 (all) | MAR (all) [95% CI] | accuracy (leaked) | MAR (leaked) | n attack classes in MAR (leaked) |
|---|---|---|---|---:|---|---:|---:|---:|
| gnb | random | leaky | 0.196 [0.195, 0.197] | 0.084 | 0.236 [0.234, 0.238] | 0.186 | 0.179 | 11 |
| gnb | random | +8y | 0.196 [0.195, 0.197] | 0.085 | 0.236 [0.234, 0.238] | 0.186 | 0.179 | 11 |
| gnb | random | zero | 0.130 [0.129, 0.131] | 0.034 | 0.102 [0.101, 0.103] | 0.016 | 0.086 | 11 |
| gnb | random | fixA | 0.203 [0.202, 0.204] | 0.140 | 0.288 [0.282, 0.294] | 0.021 | 0.132 | 11 |
| gnb | random | dropIAT | 0.203 [0.202, 0.204] | 0.140 | 0.288 [0.282, 0.294] | 0.021 | 0.132 | 11 |
| gnb | temporal | leaky | 0.242 [0.241, 0.243] | 0.090 | 0.232 [0.229, 0.234] | 0.203 | 0.176 | 11 |
| gnb | temporal | +8y | 0.242 [0.240, 0.243] | 0.091 | 0.232 [0.229, 0.234] | 0.203 | 0.176 | 11 |
| gnb | temporal | zero | 0.177 [0.176, 0.177] | 0.040 | 0.101 [0.100, 0.101] | 0.037 | 0.089 | 11 |
| gnb | temporal | fixA | 0.186 [0.185, 0.187] | 0.134 | 0.311 [0.307, 0.315] | 0.040 | 0.138 | 11 |
| gnb | temporal | dropIAT | 0.187 [0.186, 0.188] | 0.134 | 0.311 [0.307, 0.315] | 0.040 | 0.138 | 11 |
| dt | random | leaky | 0.994 [0.994, 0.994] | 0.778 | 0.950 [0.945, 0.955] | 0.991 | 0.984 | 11 |
| dt | random | +8y | 0.936 [0.935, 0.936] | 0.633 | 0.665 [0.658, 0.672] | 0.840 | 0.165 | 11 |
| dt | random | zero | 0.867 [0.866, 0.867] | 0.460 | 0.514 [0.507, 0.522] | 0.661 | 0.009 | 11 |
| dt | random | fixA | 0.933 [0.932, 0.933] | 0.588 | 0.838 [0.831, 0.845] | 0.832 | 0.518 | 11 |
| dt | random | dropIAT | 0.930 [0.930, 0.931] | 0.574 | 0.837 [0.831, 0.843] | 0.832 | 0.518 | 11 |
| dt | temporal | leaky | 0.932 [0.932, 0.933] | 0.571 | 0.572 [0.566, 0.579] | 0.839 | 0.289 | 11 |
| dt | temporal | +8y | 0.874 [0.873, 0.875] | 0.492 | 0.521 [0.515, 0.528] | 0.690 | 0.178 | 11 |
| dt | temporal | zero | 0.866 [0.865, 0.867] | 0.454 | 0.437 [0.431, 0.443] | 0.670 | 0.016 | 11 |
| dt | temporal | fixA | 0.889 [0.888, 0.890] | 0.533 | 0.736 [0.729, 0.743] | 0.728 | 0.448 | 11 |
| dt | temporal | dropIAT | 0.887 [0.886, 0.888] | 0.521 | 0.737 [0.731, 0.744] | 0.728 | 0.449 | 11 |
| lr | random | leaky | 0.826 [0.825, 0.827] | 0.434 | 0.840 [0.834, 0.846] | 0.628 | 0.518 | 11 |
| lr | random | +8y | 0.772 [0.771, 0.773] | 0.425 | 0.809 [0.802, 0.816] | 0.489 | 0.437 | 11 |
| lr | random | zero | 0.799 [0.798, 0.800] | 0.367 | 0.544 [0.537, 0.551] | 0.559 | 0.104 | 11 |
| lr | random | fixA | 0.823 [0.822, 0.824] | 0.435 | 0.840 [0.834, 0.845] | 0.621 | 0.518 | 11 |
| lr | temporal | leaky | 0.785 [0.784, 0.786] | 0.400 | 0.744 [0.738, 0.750] | 0.526 | 0.442 | 11 |
| lr | temporal | +8y | 0.770 [0.769, 0.771] | 0.409 | 0.738 [0.731, 0.744] | 0.488 | 0.435 | 11 |
| lr | temporal | zero | 0.797 [0.796, 0.798] | 0.337 | 0.480 [0.473, 0.487] | 0.558 | 0.108 | 11 |
| lr | temporal | fixA | 0.781 [0.780, 0.782] | 0.405 | 0.745 [0.739, 0.751] | 0.523 | 0.442 | 11 |
| xgb | random | leaky | 0.987 [0.986, 0.987] | 0.745 | 0.947 [0.942, 0.952] | 0.968 | 0.972 | 11 |
| xgb | random | +8y | 0.913 [0.913, 0.914] | 0.623 | 0.672 [0.666, 0.679] | 0.778 | 0.262 | 11 |
| xgb | random | zero | 0.871 [0.871, 0.872] | 0.503 | 0.524 [0.518, 0.531] | 0.669 | 0.023 | 11 |
| xgb | random | fixA | 0.924 [0.923, 0.925] | 0.570 | 0.840 [0.834, 0.846] | 0.806 | 0.516 | 11 |
| xgb | random | dropIAT | 0.922 [0.922, 0.923] | 0.560 | 0.843 [0.836, 0.849] | 0.806 | 0.516 | 11 |
| xgb | temporal | leaky | 0.977 [0.976, 0.977] | 0.730 | 0.812 [0.806, 0.819] | 0.948 | 0.748 | 11 |
| xgb | temporal | +8y | 0.922 [0.922, 0.923] | 0.628 | 0.558 [0.552, 0.565] | 0.810 | 0.146 | 11 |
| xgb | temporal | zero | 0.870 [0.869, 0.871] | 0.564 | 0.471 [0.465, 0.478] | 0.677 | 0.060 | 11 |
| xgb | temporal | fixA | 0.885 [0.884, 0.886] | 0.523 | 0.744 [0.737, 0.750] | 0.715 | 0.446 | 11 |
| xgb | temporal | dropIAT | 0.883 [0.883, 0.884] | 0.515 | 0.746 [0.739, 0.752] | 0.715 | 0.446 | 11 |
| rf | random | leaky | 0.987 [0.987, 0.988] | 0.702 | 0.954 [0.949, 0.958] | 0.981 | 0.978 | 11 |
| rf | random | +8y | 0.932 [0.931, 0.933] | 0.617 | 0.667 [0.659, 0.674] | 0.837 | 0.165 | 11 |
| rf | random | zero | 0.867 [0.866, 0.868] | 0.524 | 0.517 [0.509, 0.524] | 0.668 | 0.019 | 11 |
| rf | random | fixA | 0.889 [0.889, 0.890] | 0.532 | 0.840 [0.835, 0.846] | 0.728 | 0.510 | 11 |
| rf | random | dropIAT | 0.878 [0.877, 0.878] | 0.523 | 0.843 [0.838, 0.849] | 0.699 | 0.510 | 11 |
| rf | temporal | leaky | 0.938 [0.938, 0.939] | 0.566 | 0.660 [0.653, 0.667] | 0.861 | 0.393 | 11 |
| rf | temporal | +8y | 0.929 [0.929, 0.930] | 0.562 | 0.530 [0.523, 0.537] | 0.838 | 0.090 | 11 |
| rf | temporal | zero | 0.865 [0.864, 0.866] | 0.491 | 0.446 [0.440, 0.453] | 0.674 | 0.019 | 11 |
| rf | temporal | fixA | 0.846 [0.845, 0.846] | 0.477 | 0.744 [0.738, 0.750] | 0.626 | 0.444 | 11 |
| rf | temporal | dropIAT | 0.837 [0.836, 0.838] | 0.469 | 0.743 [0.737, 0.749] | 0.605 | 0.444 | 11 |
| mlp | random | leaky | 0.947 [0.946, 0.948] | 0.625 | 0.661 [0.656, 0.665] | 0.869 | 0.286 | 11 |
| mlp | random | +8y | 0.947 [0.946, 0.948] | 0.625 | 0.660 [0.655, 0.665] | 0.869 | 0.286 | 11 |
| mlp | random | zero | 0.872 [0.871, 0.872] | 0.487 | 0.459 [0.454, 0.464] | 0.674 | 0.004 | 11 |
| mlp | random | fixA | 0.947 [0.946, 0.948] | 0.624 | 0.658 [0.653, 0.663] | 0.869 | 0.284 | 11 |
| mlp | random | dropIAT | 0.947 [0.946, 0.947] | 0.625 | 0.661 [0.656, 0.666] | 0.869 | 0.287 | 11 |
| mlp | temporal | leaky | 0.945 [0.945, 0.946] | 0.621 | 0.618 [0.613, 0.623] | 0.873 | 0.317 | 11 |
| mlp | temporal | +8y | 0.945 [0.945, 0.946] | 0.621 | 0.618 [0.613, 0.623] | 0.873 | 0.316 | 11 |
| mlp | temporal | zero | 0.868 [0.867, 0.869] | 0.460 | 0.396 [0.392, 0.401] | 0.676 | 0.018 | 11 |
| mlp | temporal | fixA | 0.945 [0.945, 0.946] | 0.623 | 0.624 [0.619, 0.629] | 0.872 | 0.317 | 11 |
| mlp | temporal | dropIAT | 0.945 [0.945, 0.946] | 0.628 | 0.623 [0.618, 0.628] | 0.873 | 0.316 | 11 |
| knn | random | leaky | 0.995 [0.995, 0.995] | 0.804 | 0.902 [0.896, 0.908] | 0.991 | 0.905 | 11 |
| knn | random | +8y | 0.940 [0.940, 0.941] | 0.677 | 0.668 [0.662, 0.675] | 0.848 | 0.198 | 11 |
| knn | random | zero | 0.871 [0.871, 0.872] | 0.549 | 0.503 [0.497, 0.510] | 0.670 | 0.010 | 11 |
| knn | random | fixA | 0.895 [0.895, 0.896] | 0.560 | 0.700 [0.693, 0.706] | 0.732 | 0.368 | 11 |
| knn | random | dropIAT | 0.895 [0.894, 0.895] | 0.532 | 0.670 [0.664, 0.676] | 0.732 | 0.368 | 11 |
| knn | temporal | leaky | 0.951 [0.951, 0.952] | 0.761 | 0.709 [0.703, 0.716] | 0.884 | 0.477 | 11 |
| knn | temporal | +8y | 0.903 [0.902, 0.904] | 0.666 | 0.626 [0.619, 0.633] | 0.761 | 0.303 | 11 |
| knn | temporal | zero | 0.869 [0.868, 0.870] | 0.555 | 0.448 [0.441, 0.455] | 0.675 | 0.017 | 11 |
| knn | temporal | fixA | 0.895 [0.894, 0.896] | 0.590 | 0.653 [0.646, 0.660] | 0.741 | 0.386 | 11 |
| knn | temporal | dropIAT | 0.894 [0.894, 0.895] | 0.554 | 0.623 [0.617, 0.629] | 0.741 | 0.386 | 11 |

**gnb, random split, per class, all test rows** (recall / precision):

| class | support | leaky | +8y | zero | fixA | dropIAT |
|---|---:|---|---|---|---|---|
| Benign | 446,560 | 0.104 / 0.999 | 0.104 / 0.999 | 0.104 / 0.999 | 0.149 / 0.996 | 0.149 / 0.996 |
| Botnet_ARES | 1,377 | 0.007 / 0.012 | 0.007 / 0.012 | 0.007 / 0.019 | 0.014 / 0.013 | 0.014 / 0.013 |
| DDoS_LOIT | 23,933 | 0.998 / 0.085 | 0.998 / 0.085 | 0.998 / 0.047 | 0.834 / 0.932 | 0.832 / 0.932 |
| DoS_GoldenEye | 2,091 | 0.000 / 0.000 | 0.000 / 0.000 | 0.000 / 0.000 | 0.643 / 0.051 | 0.644 / 0.052 |
| DoS_Hulk | 87,310 | 0.101 / 0.939 | 0.101 / 0.939 | 0.101 / 0.941 | 0.389 / 0.573 | 0.389 / 0.575 |
| DoS_Slowhttptest | 1,715 | 0.003 / 0.000 | 0.003 / 0.000 | 0.013 / 0.001 | 0.032 / 0.004 | 0.032 / 0.005 |
| DoS_Slowloris | 1,294 | 0.000 / 0.000 | 0.000 / 0.000 | 0.000 / 0.000 | 0.003 / 0.000 | 0.005 / 0.000 |
| FTP-Patator | 2,383 | 0.000 / 0.000 | 0.000 / 0.000 | 0.003 / 0.002 | 0.244 / 0.004 | 0.244 / 0.004 |
| Heartbleed | 3 | 0.667 / 0.000 | 0.667 / 0.000 | 0.000 / 0.000 | 0.000 / 0.000 | 0.000 / 0.000 |
| Port_Scan | 40,331 | 0.978 / 0.446 | 0.978 / 0.452 | 0.000 / 0.000 | 0.010 / 0.015 | 0.010 / 0.016 |
| SSH-Patator | 1,487 | 0.510 / 0.017 | 0.510 / 0.017 | 0.000 / 0.000 | 0.473 / 0.133 | 0.473 / 0.134 |
| Web_Brute_Force | 683 | 0.000 / 0.000 | 0.000 / 0.000 | 0.000 / 0.000 | 0.026 / 0.003 | 0.026 / 0.003 |
| Web_SQL_Injection | 6 | 0.000 / 0.000 | 0.000 / 0.000 | 0.000 / 0.000 | 0.333 / 0.000 | 0.333 / 0.000 |
| Web_XSS | 340 | 0.000 / 0.000 | 0.000 / 0.000 | 0.000 / 0.000 | 0.500 / 0.001 | 0.500 / 0.001 |

**gnb, random split, per class, leaked test rows** (recall / precision):

| class | support | leaky | +8y | zero | fixA | dropIAT |
|---|---:|---|---|---|---|---|
| Benign | 156,946 | 0.022 / 0.997 | 0.022 / 0.996 | 0.023 / 0.996 | 0.024 / 0.999 | 0.024 / 0.999 |
| Botnet_ARES | 1,154 | 0.000 / 0.000 | 0.000 / 0.000 | 0.000 / 0.000 | 0.000 / 0.000 | 0.000 / 0.000 |
| DDoS_LOIT | 11 | 0.000 / 0.000 | 0.000 / 0.000 | 0.909 / 0.000 | 0.000 / 0.000 | 0.000 / 0.000 |
| DoS_GoldenEye | 129 | 0.000 / 0.000 | 0.000 / 0.000 | 0.000 / 0.000 | 0.000 / 0.000 | 0.000 / 0.000 |
| DoS_Hulk | 32,978 | 0.000 / 0.000 | 0.000 / 0.000 | 0.000 / 0.000 | 0.000 / 0.000 | 0.000 / 0.000 |
| DoS_Slowhttptest | 527 | 0.000 / 0.000 | 0.000 / 0.000 | 0.032 / 0.006 | 0.017 / 0.053 | 0.017 / 0.052 |
| DoS_Slowloris | 225 | 0.000 / 0.000 | 0.000 / 0.000 | 0.000 / 0.000 | 0.000 / 0.000 | 0.000 / 0.000 |
| FTP-Patator | 1,375 | 0.000 / 0.000 | 0.000 / 0.000 | 0.004 / 0.003 | 0.420 / 0.008 | 0.420 / 0.008 |
| Heartbleed | 2 | 1.000 / 0.000 | 1.000 / 0.000 | 0.000 / 0.000 | 0.000 / 0.000 | 0.000 / 0.000 |
| Port_Scan | 40,275 | 0.979 / 0.447 | 0.979 / 0.452 | 0.000 / 0.000 | 0.010 / 0.059 | 0.010 / 0.060 |
| SSH-Patator | 769 | 0.987 / 0.017 | 0.987 / 0.017 | 0.000 / 0.000 | 0.000 / 0.000 | 0.000 / 0.000 |
| Web_Brute_Force | 345 | 0.000 / 0.000 | 0.000 / 0.000 | 0.000 / 0.000 | 0.000 / 0.000 | 0.000 / 0.000 |
| Web_SQL_Injection | 3 | 0.000 / 0.000 | 0.000 / 0.000 | 0.000 / 0.000 | 0.000 / 0.000 | 0.000 / 0.000 |
| Web_XSS | 170 | 0.000 / 0.000 | 0.000 / 0.000 | 0.000 / 0.000 | 1.000 / 0.001 | 1.000 / 0.001 |

**gnb, temporal split, per class, all test rows** (recall / precision):

| class | support | leaky | +8y | zero | fixA | dropIAT |
|---|---:|---|---|---|---|---|
| Benign | 446,559 | 0.167 / 0.998 | 0.167 / 0.998 | 0.167 / 0.998 | 0.133 / 0.996 | 0.133 / 0.996 |
| Botnet_ARES | 1,377 | 0.000 / 0.000 | 0.000 / 0.000 | 0.000 / 0.000 | 0.000 / 0.000 | 0.000 / 0.000 |
| DDoS_LOIT | 23,933 | 0.997 / 0.088 | 0.997 / 0.088 | 0.999 / 0.048 | 0.688 / 0.910 | 0.687 / 0.910 |
| DoS_GoldenEye | 2,091 | 0.000 / 0.000 | 0.000 / 0.000 | 0.000 / 0.000 | 0.542 / 0.040 | 0.542 / 0.040 |
| DoS_Hulk | 87,310 | 0.104 / 0.836 | 0.104 / 0.836 | 0.104 / 0.837 | 0.400 / 0.816 | 0.400 / 0.817 |
| DoS_Slowhttptest | 1,715 | 0.000 / 0.000 | 0.000 / 0.000 | 0.000 / 0.000 | 0.019 / 0.001 | 0.019 / 0.001 |
| DoS_Slowloris | 1,294 | 0.000 / 0.000 | 0.000 / 0.000 | 0.000 / 0.000 | 0.000 / 0.000 | 0.000 / 0.000 |
| FTP-Patator | 2,383 | 0.000 / 0.000 | 0.000 / 0.000 | 0.003 / 0.000 | 0.294 / 0.004 | 0.294 / 0.004 |
| Heartbleed | 3 | 0.333 / 0.000 | 0.333 / 0.000 | 0.000 / 0.000 | 0.000 / 0.000 | 0.000 / 0.000 |
| Port_Scan | 40,331 | 0.972 / 0.435 | 0.970 / 0.440 | 0.000 / 0.000 | 0.000 / 0.000 | 0.000 / 0.000 |
| SSH-Patator | 1,487 | 0.477 / 0.016 | 0.477 / 0.016 | 0.000 / 0.000 | 0.477 / 0.130 | 0.477 / 0.130 |
| Web_Brute_Force | 684 | 0.000 / 0.000 | 0.000 / 0.000 | 0.000 / 0.000 | 0.025 / 0.044 | 0.025 / 0.045 |
| Web_SQL_Injection | 6 | 0.000 / 0.000 | 0.000 / 0.000 | 0.000 / 0.000 | 0.500 / 0.000 | 0.500 / 0.000 |
| Web_XSS | 340 | 0.000 / 0.000 | 0.000 / 0.000 | 0.000 / 0.000 | 0.974 / 0.002 | 0.974 / 0.002 |

**gnb, temporal split, per class, leaked test rows** (recall / precision):

| class | support | leaky | +8y | zero | fixA | dropIAT |
|---|---:|---|---|---|---|---|
| Benign | 161,365 | 0.054 / 0.995 | 0.054 / 0.995 | 0.055 / 0.995 | 0.054 / 1.000 | 0.054 / 1.000 |
| Botnet_ARES | 1,218 | 0.000 / 0.000 | 0.000 / 0.000 | 0.000 / 0.000 | 0.000 / 0.000 | 0.000 / 0.000 |
| DDoS_LOIT | 42 | 0.000 / 0.000 | 0.000 / 0.000 | 0.976 / 0.000 | 0.000 / 0.000 | 0.000 / 0.000 |
| DoS_GoldenEye | 289 | 0.000 / 0.000 | 0.000 / 0.000 | 0.000 / 0.000 | 0.000 / 0.000 | 0.000 / 0.000 |
| DoS_Hulk | 32,764 | 0.000 / 0.000 | 0.000 / 0.000 | 0.000 / 0.000 | 0.000 / 0.000 | 0.000 / 0.000 |
| DoS_Slowhttptest | 555 | 0.000 / 0.000 | 0.000 / 0.000 | 0.000 / 0.000 | 0.000 / 0.000 | 0.000 / 0.000 |
| DoS_Slowloris | 615 | 0.000 / 0.000 | 0.000 / 0.000 | 0.000 / 0.000 | 0.000 / 0.000 | 0.000 / 0.000 |
| FTP-Patator | 1,357 | 0.000 / 0.000 | 0.000 / 0.000 | 0.004 / 0.002 | 0.515 / 0.010 | 0.515 / 0.010 |
| Heartbleed | 1 | 1.000 / 0.000 | 1.000 / 0.000 | 0.000 / 0.000 | 0.000 / 0.000 | 0.000 / 0.000 |
| Port_Scan | 40,175 | 0.976 / 0.435 | 0.974 / 0.440 | 0.000 / 0.000 | 0.000 / 0.000 | 0.000 / 0.000 |
| SSH-Patator | 738 | 0.961 / 0.016 | 0.961 / 0.016 | 0.000 / 0.000 | 0.000 / 0.000 | 0.000 / 0.000 |
| Web_Brute_Force | 344 | 0.000 / 0.000 | 0.000 / 0.000 | 0.000 / 0.000 | 0.000 / 0.000 | 0.000 / 0.000 |
| Web_SQL_Injection | 3 | 0.000 / 0.000 | 0.000 / 0.000 | 0.000 / 0.000 | 0.000 / 0.000 | 0.000 / 0.000 |
| Web_XSS | 172 | 0.000 / 0.000 | 0.000 / 0.000 | 0.000 / 0.000 | 1.000 / 0.001 | 1.000 / 0.001 |

**dt, random split, per class, all test rows** (recall / precision):

| class | support | leaky | +8y | zero | fixA | dropIAT |
|---|---:|---|---|---|---|---|
| Benign | 446,560 | 0.993 / 1.000 | 0.996 / 0.923 | 0.993 / 0.884 | 0.925 / 0.999 | 0.922 / 0.999 |
| Botnet_ARES | 1,377 | 0.988 / 0.793 | 0.843 / 0.854 | 0.152 / 0.639 | 0.989 / 0.161 | 0.991 / 0.161 |
| DDoS_LOIT | 23,933 | 1.000 / 0.998 | 0.999 / 0.999 | 0.999 / 0.999 | 0.999 / 0.997 | 0.999 / 0.998 |
| DoS_GoldenEye | 2,091 | 0.979 / 0.850 | 0.918 / 0.895 | 0.918 / 0.760 | 0.914 / 0.899 | 0.918 / 0.916 |
| DoS_Hulk | 87,310 | 0.999 / 0.998 | 0.622 / 0.999 | 0.622 / 0.998 | 0.940 / 0.835 | 0.940 / 0.835 |
| DoS_Slowhttptest | 1,715 | 0.958 / 0.736 | 0.658 / 0.784 | 0.686 / 0.784 | 0.689 / 0.812 | 0.687 / 0.738 |
| DoS_Slowloris | 1,294 | 0.957 / 0.730 | 0.787 / 0.793 | 0.787 / 0.478 | 0.787 / 0.785 | 0.790 / 0.781 |
| FTP-Patator | 2,383 | 0.999 / 0.777 | 0.423 / 0.963 | 0.423 / 0.963 | 0.833 / 0.150 | 0.834 / 0.149 |
| Heartbleed | 3 | 0.667 / 0.105 | 0.000 / 0.000 | 0.000 / 0.000 | 0.000 / 0.000 | 0.000 / 0.000 |
| Port_Scan | 40,331 | 0.999 / 0.996 | 0.991 / 0.985 | 0.001 / 0.319 | 0.992 / 0.999 | 0.993 / 0.999 |
| SSH-Patator | 1,487 | 0.989 / 0.932 | 0.475 / 0.939 | 0.475 / 0.033 | 0.991 / 0.861 | 0.994 / 0.847 |
| Web_Brute_Force | 683 | 0.755 / 0.668 | 0.258 / 0.587 | 0.258 / 0.587 | 0.335 / 0.440 | 0.309 / 0.188 |
| Web_SQL_Injection | 6 | 0.500 / 0.079 | 0.000 / 0.000 | 0.000 / 0.000 | 0.333 / 0.003 | 0.333 / 0.003 |
| Web_XSS | 340 | 0.829 / 0.456 | 0.338 / 0.302 | 0.338 / 0.302 | 0.747 / 0.060 | 0.753 / 0.052 |

**dt, random split, per class, leaked test rows** (recall / precision):

| class | support | leaky | +8y | zero | fixA | dropIAT |
|---|---:|---|---|---|---|---|
| Benign | 156,946 | 0.987 / 1.000 | 0.996 / 0.808 | 0.988 / 0.728 | 0.794 / 0.998 | 0.794 / 0.998 |
| Botnet_ARES | 1,154 | 0.997 / 0.829 | 0.825 / 0.922 | 0.000 / 0.000 | 0.999 / 0.141 | 0.999 / 0.141 |
| DDoS_LOIT | 11 | 0.909 / 0.294 | 0.000 / 0.000 | 0.000 / 0.000 | 0.000 / 0.000 | 0.000 / 0.000 |
| DoS_GoldenEye | 129 | 1.000 / 0.485 | 0.000 / 0.000 | 0.000 / 0.000 | 0.000 / 0.000 | 0.000 / 0.000 |
| DoS_Hulk | 32,978 | 1.000 / 0.995 | 0.000 / 0.857 | 0.001 / 0.240 | 0.844 / 0.633 | 0.844 / 0.633 |
| DoS_Slowhttptest | 527 | 0.979 / 0.648 | 0.002 / 1.000 | 0.095 / 0.769 | 0.097 / 0.761 | 0.097 / 0.689 |
| DoS_Slowloris | 225 | 0.978 / 0.534 | 0.000 / 0.000 | 0.000 / 0.000 | 0.027 / 0.068 | 0.027 / 0.094 |
| FTP-Patator | 1,375 | 0.999 / 0.681 | 0.000 / 0.000 | 0.000 / 0.000 | 0.713 / 0.080 | 0.713 / 0.080 |
| Heartbleed | 2 | 1.000 / 0.118 | 0.000 / 0.000 | 0.000 / 0.000 | 0.000 / 0.000 | 0.000 / 0.000 |
| Port_Scan | 40,275 | 1.000 / 0.997 | 0.992 / 0.986 | 0.000 / 0.036 | 0.992 / 1.000 | 0.993 / 1.000 |
| SSH-Patator | 769 | 0.993 / 0.925 | 0.000 / 0.000 | 0.000 / 0.000 | 0.996 / 0.787 | 0.996 / 0.789 |
| Web_Brute_Force | 345 | 0.986 / 0.720 | 0.000 / 0.000 | 0.000 / 0.000 | 0.049 / 0.147 | 0.049 / 0.177 |
| Web_SQL_Injection | 3 | 1.000 / 0.100 | 0.000 / 0.000 | 0.000 / 0.000 | 0.667 / 0.003 | 0.667 / 0.003 |
| Web_XSS | 170 | 0.982 / 0.705 | 0.000 / 0.000 | 0.000 / 0.000 | 0.982 / 0.043 | 0.982 / 0.043 |

**dt, temporal split, per class, all test rows** (recall / precision):

| class | support | leaky | +8y | zero | fixA | dropIAT |
|---|---:|---|---|---|---|---|
| Benign | 446,559 | 0.977 / 0.939 | 0.918 / 0.977 | 0.996 / 0.849 | 0.929 / 0.998 | 0.925 / 0.998 |
| Botnet_ARES | 1,377 | 0.105 / 0.973 | 0.000 / 0.000 | 0.000 / 0.000 | 0.877 / 0.148 | 0.881 / 0.147 |
| DDoS_LOIT | 23,933 | 0.999 / 0.797 | 0.999 / 0.274 | 0.997 / 1.000 | 0.997 / 0.998 | 0.997 / 0.999 |
| DoS_GoldenEye | 2,091 | 0.820 / 0.821 | 0.810 / 0.824 | 0.810 / 0.813 | 0.810 / 0.796 | 0.771 / 0.794 |
| DoS_Hulk | 87,310 | 0.718 / 0.999 | 0.618 / 0.999 | 0.619 / 0.999 | 0.632 / 0.999 | 0.632 / 0.999 |
| DoS_Slowhttptest | 1,715 | 0.718 / 0.614 | 0.647 / 0.601 | 0.704 / 0.446 | 0.697 / 0.564 | 0.710 / 0.526 |
| DoS_Slowloris | 1,294 | 0.350 / 0.754 | 0.298 / 0.745 | 0.298 / 0.744 | 0.311 / 0.669 | 0.304 / 0.644 |
| FTP-Patator | 2,383 | 0.482 / 0.946 | 0.430 / 0.964 | 0.430 / 0.962 | 0.860 / 0.148 | 0.861 / 0.148 |
| Heartbleed | 3 | 0.333 / 0.000 | 0.000 / 0.000 | 0.000 / 0.000 | 0.667 / 0.000 | 0.667 / 0.000 |
| Port_Scan | 40,331 | 0.987 / 0.967 | 0.985 / 0.950 | 0.002 / 0.587 | 0.990 / 0.998 | 0.989 / 0.998 |
| SSH-Patator | 1,487 | 0.512 / 0.824 | 0.481 / 0.819 | 0.481 / 0.730 | 0.950 / 0.929 | 0.951 / 0.884 |
| Web_Brute_Force | 684 | 0.311 / 0.534 | 0.281 / 0.508 | 0.281 / 0.508 | 0.304 / 0.343 | 0.307 / 0.199 |
| Web_SQL_Injection | 6 | 0.500 / 0.158 | 0.333 / 0.111 | 0.333 / 0.111 | 0.833 / 0.008 | 0.833 / 0.008 |
| Web_XSS | 340 | 0.294 / 0.286 | 0.185 / 0.201 | 0.185 / 0.201 | 0.668 / 0.055 | 0.709 / 0.051 |

**dt, temporal split, per class, leaked test rows** (recall / precision):

| class | support | leaky | +8y | zero | fixA | dropIAT |
|---|---:|---|---|---|---|---|
| Benign | 161,365 | 0.942 / 0.845 | 0.779 / 0.934 | 0.994 / 0.672 | 0.807 / 0.998 | 0.807 / 0.998 |
| Botnet_ARES | 1,218 | 0.119 / 1.000 | 0.000 / 0.000 | 0.000 / 0.000 | 0.991 / 0.148 | 0.996 / 0.147 |
| DDoS_LOIT | 42 | 0.976 / 0.007 | 0.976 / 0.001 | 0.000 / 0.000 | 0.000 / 0.000 | 0.000 / 0.000 |
| DoS_GoldenEye | 289 | 0.073 / 0.618 | 0.000 / 0.000 | 0.000 / 0.000 | 0.000 / 0.000 | 0.000 / 0.000 |
| DoS_Hulk | 32,764 | 0.264 / 0.998 | 0.000 / 0.000 | 0.001 / 0.812 | 0.036 / 0.999 | 0.036 / 0.997 |
| DoS_Slowhttptest | 555 | 0.222 / 0.764 | 0.000 / 0.000 | 0.178 / 0.115 | 0.178 / 0.416 | 0.180 / 0.380 |
| DoS_Slowloris | 615 | 0.109 / 0.807 | 0.000 / 0.000 | 0.000 / 0.000 | 0.005 / 0.058 | 0.005 / 0.057 |
| FTP-Patator | 1,357 | 0.091 / 0.816 | 0.000 / 0.000 | 0.000 / 0.000 | 0.757 / 0.080 | 0.757 / 0.080 |
| Heartbleed | 1 | 1.000 / 0.000 | 0.000 / 0.000 | 0.000 / 0.000 | 1.000 / 0.000 | 1.000 / 0.000 |
| Port_Scan | 40,175 | 0.989 / 0.968 | 0.986 / 0.951 | 0.000 / 0.000 | 0.991 / 0.999 | 0.991 / 1.000 |
| SSH-Patator | 738 | 0.062 / 0.902 | 0.000 / 0.000 | 0.000 / 0.000 | 0.955 / 0.877 | 0.955 / 0.885 |
| Web_Brute_Force | 344 | 0.061 / 1.000 | 0.000 / 0.000 | 0.000 / 0.000 | 0.049 / 0.110 | 0.049 / 0.110 |
| Web_SQL_Injection | 3 | 0.333 / 1.000 | 0.000 / 0.000 | 0.000 / 0.000 | 0.667 / 0.003 | 0.667 / 0.003 |
| Web_XSS | 172 | 0.215 / 1.000 | 0.000 / 0.000 | 0.000 / 0.000 | 0.965 / 0.044 | 0.965 / 0.044 |

**lr, random split, per class, all test rows** (recall / precision):

| class | support | leaky | +8y | zero | fixA |
|---|---:|---|---|---|---|
| Benign | 446,560 | 0.780 / 1.000 | 0.767 / 1.000 | 0.898 / 0.881 | 0.777 / 1.000 |
| Botnet_ARES | 1,377 | 1.000 / 0.054 | 1.000 / 0.046 | 0.162 / 0.189 | 1.000 / 0.054 |
| DDoS_LOIT | 23,933 | 0.999 / 0.994 | 0.999 / 0.994 | 0.999 / 0.994 | 0.999 / 0.995 |
| DoS_GoldenEye | 2,091 | 0.904 / 0.648 | 0.904 / 0.666 | 0.935 / 0.104 | 0.903 / 0.616 |
| DoS_Hulk | 87,310 | 0.937 / 0.739 | 0.629 / 0.905 | 0.630 / 0.710 | 0.936 / 0.741 |
| DoS_Slowhttptest | 1,715 | 0.703 / 0.438 | 0.703 / 0.424 | 0.703 / 0.481 | 0.706 / 0.456 |
| DoS_Slowloris | 1,294 | 0.777 / 0.285 | 0.777 / 0.289 | 0.773 / 0.298 | 0.773 / 0.374 |
| FTP-Patator | 2,383 | 0.831 / 0.123 | 0.828 / 0.124 | 0.666 / 0.450 | 0.828 / 0.119 |
| Heartbleed | 3 | 0.000 / 0.000 | 0.667 / 0.000 | 0.000 / 0.000 | 0.000 / 0.000 |
| Port_Scan | 40,331 | 0.987 / 0.990 | 0.987 / 0.962 | 0.003 / 0.500 | 0.987 / 0.978 |
| SSH-Patator | 1,487 | 0.987 / 0.122 | 0.987 / 0.110 | 0.477 / 0.473 | 0.986 / 0.111 |
| Web_Brute_Force | 683 | 0.227 / 0.065 | 0.676 / 0.026 | 0.227 / 0.066 | 0.243 / 0.033 |
| Web_SQL_Injection | 6 | 0.500 / 0.001 | 0.500 / 0.002 | 0.833 / 0.000 | 0.500 / 0.001 |
| Web_XSS | 340 | 0.891 / 0.017 | 0.409 / 0.054 | 0.409 / 0.054 | 0.876 / 0.021 |

**lr, random split, per class, leaked test rows** (recall / precision):

| class | support | leaky | +8y | zero | fixA |
|---|---:|---|---|---|---|
| Benign | 156,946 | 0.490 / 1.000 | 0.452 / 1.000 | 0.825 / 0.706 | 0.480 / 1.000 |
| Botnet_ARES | 1,154 | 1.000 / 0.047 | 1.000 / 0.040 | 0.000 / 0.000 | 1.000 / 0.047 |
| DDoS_LOIT | 11 | 0.091 / 0.500 | 0.091 / 0.500 | 0.091 / 0.500 | 0.091 / 1.000 |
| DoS_GoldenEye | 129 | 0.000 / 0.000 | 0.000 / 0.000 | 0.504 / 0.004 | 0.000 / 0.000 |
| DoS_Hulk | 32,978 | 0.843 / 0.544 | 0.028 / 0.816 | 0.030 / 0.055 | 0.843 / 0.543 |
| DoS_Slowhttptest | 527 | 0.095 / 0.104 | 0.095 / 0.087 | 0.095 / 0.214 | 0.097 / 0.169 |
| DoS_Slowloris | 225 | 0.022 / 0.021 | 0.022 / 0.025 | 0.000 / 0.000 | 0.022 / 0.045 |
| FTP-Patator | 1,375 | 0.710 / 0.067 | 0.703 / 0.067 | 0.424 / 0.277 | 0.703 / 0.066 |
| Heartbleed | 2 | 0.000 / 0.000 | 1.000 / 0.000 | 0.000 / 0.000 | 0.000 / 0.000 |
| Port_Scan | 40,275 | 0.988 / 0.993 | 0.989 / 0.965 | 0.003 / 0.984 | 0.988 / 0.986 |
| SSH-Patator | 769 | 0.986 / 0.070 | 0.986 / 0.062 | 0.001 / 0.003 | 0.986 / 0.064 |
| Web_Brute_Force | 345 | 0.000 / 0.000 | 0.890 / 0.020 | 0.000 / 0.000 | 0.009 / 0.001 |
| Web_SQL_Injection | 3 | 0.000 / 0.000 | 0.000 / 0.000 | 0.667 / 0.000 | 0.000 / 0.000 |
| Web_XSS | 170 | 0.965 / 0.011 | 0.000 / 0.000 | 0.000 / 0.000 | 0.959 / 0.013 |

**lr, temporal split, per class, all test rows** (recall / precision):

| class | support | leaky | +8y | zero | fixA |
|---|---:|---|---|---|---|
| Benign | 446,559 | 0.787 / 0.999 | 0.767 / 0.999 | 0.900 / 0.874 | 0.782 / 0.999 |
| Botnet_ARES | 1,377 | 0.885 / 0.051 | 0.885 / 0.045 | 0.000 / 0.000 | 0.883 / 0.052 |
| DDoS_LOIT | 23,933 | 0.997 / 0.997 | 0.997 / 0.997 | 0.997 / 0.997 | 0.997 / 0.997 |
| DoS_GoldenEye | 2,091 | 0.794 / 0.534 | 0.794 / 0.534 | 0.863 / 0.056 | 0.792 / 0.563 |
| DoS_Hulk | 87,310 | 0.629 / 0.922 | 0.629 / 0.921 | 0.616 / 0.923 | 0.628 / 0.917 |
| DoS_Slowhttptest | 1,715 | 0.723 / 0.359 | 0.722 / 0.324 | 0.722 / 0.380 | 0.723 / 0.378 |
| DoS_Slowloris | 1,294 | 0.359 / 0.176 | 0.458 / 0.035 | 0.357 / 0.183 | 0.379 / 0.233 |
| FTP-Patator | 2,383 | 0.861 / 0.123 | 0.725 / 0.522 | 0.723 / 0.431 | 0.859 / 0.120 |
| Heartbleed | 3 | 0.667 / 0.000 | 0.667 / 0.000 | 0.333 / 0.000 | 0.667 / 0.000 |
| Port_Scan | 40,331 | 0.980 / 0.993 | 0.981 / 0.896 | 0.000 / 0.000 | 0.980 / 0.984 |
| SSH-Patator | 1,487 | 0.948 / 0.131 | 0.948 / 0.119 | 0.476 / 0.543 | 0.951 / 0.129 |
| Web_Brute_Force | 684 | 0.211 / 0.029 | 0.661 / 0.024 | 0.209 / 0.081 | 0.211 / 0.031 |
| Web_SQL_Injection | 6 | 0.500 / 0.001 | 0.500 / 0.002 | 0.833 / 0.000 | 0.500 / 0.001 |
| Web_XSS | 340 | 0.794 / 0.016 | 0.315 / 0.045 | 0.315 / 0.045 | 0.794 / 0.015 |

**lr, temporal split, per class, leaked test rows** (recall / precision):

| class | support | leaky | +8y | zero | fixA |
|---|---:|---|---|---|---|
| Benign | 161,365 | 0.510 / 1.000 | 0.453 / 1.000 | 0.823 / 0.697 | 0.504 / 0.999 |
| Botnet_ARES | 1,218 | 1.000 / 0.054 | 1.000 / 0.046 | 0.000 / 0.000 | 0.998 / 0.055 |
| DDoS_LOIT | 42 | 0.000 / 0.000 | 0.000 / 0.000 | 0.000 / 0.000 | 0.000 / 0.000 |
| DoS_GoldenEye | 289 | 0.000 / 0.000 | 0.000 / 0.000 | 0.495 / 0.005 | 0.000 / 0.000 |
| DoS_Hulk | 32,764 | 0.035 / 0.752 | 0.036 / 0.753 | 0.000 / 0.000 | 0.035 / 0.688 |
| DoS_Slowhttptest | 555 | 0.180 / 0.165 | 0.178 / 0.101 | 0.178 / 0.241 | 0.180 / 0.135 |
| DoS_Slowloris | 615 | 0.005 / 0.022 | 0.213 / 0.009 | 0.000 / 0.000 | 0.005 / 0.026 |
| FTP-Patator | 1,357 | 0.757 / 0.068 | 0.518 / 0.407 | 0.515 / 0.290 | 0.754 / 0.068 |
| Heartbleed | 1 | 1.000 / 0.000 | 1.000 / 0.000 | 0.000 / 0.000 | 1.000 / 0.000 |
| Port_Scan | 40,175 | 0.984 / 0.994 | 0.985 / 0.896 | 0.000 / 0.000 | 0.984 / 0.993 |
| SSH-Patator | 738 | 0.951 / 0.074 | 0.951 / 0.066 | 0.000 / 0.000 | 0.951 / 0.071 |
| Web_Brute_Force | 344 | 0.003 / 0.000 | 0.898 / 0.018 | 0.000 / 0.000 | 0.003 / 0.000 |
| Web_SQL_Injection | 3 | 0.000 / 0.000 | 0.000 / 0.000 | 0.667 / 0.000 | 0.000 / 0.000 |
| Web_XSS | 172 | 0.948 / 0.012 | 0.000 / 0.000 | 0.000 / 0.000 | 0.948 / 0.011 |

**xgb, random split, per class, all test rows** (recall / precision):

| class | support | leaky | +8y | zero | fixA | dropIAT |
|---|---:|---|---|---|---|---|
| Benign | 446,560 | 0.989 / 1.000 | 0.965 / 0.979 | 0.999 / 0.885 | 0.913 / 0.999 | 0.911 / 0.999 |
| Botnet_ARES | 1,377 | 0.999 / 0.742 | 0.852 / 0.777 | 0.160 / 0.527 | 1.000 / 0.119 | 0.999 / 0.119 |
| DDoS_LOIT | 23,933 | 1.000 / 0.994 | 1.000 / 0.358 | 1.000 / 1.000 | 1.000 / 1.000 | 0.999 / 1.000 |
| DoS_GoldenEye | 2,091 | 0.981 / 0.374 | 0.920 / 0.964 | 0.920 / 0.964 | 0.921 / 0.963 | 0.925 / 0.941 |
| DoS_Hulk | 87,310 | 0.970 / 0.998 | 0.623 / 1.000 | 0.622 / 1.000 | 0.941 / 0.836 | 0.940 / 0.836 |
| DoS_Slowhttptest | 1,715 | 0.952 / 0.678 | 0.697 / 0.881 | 0.697 / 0.880 | 0.695 / 0.888 | 0.694 / 0.884 |
| DoS_Slowloris | 1,294 | 0.956 / 0.780 | 0.784 / 0.965 | 0.784 / 0.884 | 0.791 / 0.914 | 0.791 / 0.918 |
| FTP-Patator | 2,383 | 0.998 / 0.611 | 0.457 / 0.990 | 0.512 / 0.993 | 0.834 / 0.151 | 0.834 / 0.151 |
| Heartbleed | 3 | 0.667 / 0.065 | 0.000 / 0.000 | 0.000 / 0.000 | 0.000 / 0.000 | 0.000 / 0.000 |
| Port_Scan | 40,331 | 1.000 / 0.997 | 0.990 / 1.000 | 0.002 / 1.000 | 0.993 / 1.000 | 0.993 / 1.000 |
| SSH-Patator | 1,487 | 0.988 / 0.920 | 0.475 / 1.000 | 0.475 / 0.034 | 0.992 / 0.522 | 0.993 / 0.522 |
| Web_Brute_Force | 683 | 0.861 / 0.436 | 0.370 / 0.733 | 0.370 / 0.733 | 0.373 / 0.314 | 0.303 / 0.161 |
| Web_SQL_Injection | 6 | 0.500 / 0.273 | 0.000 / 0.000 | 0.000 / 0.000 | 0.333 / 0.003 | 0.333 / 0.003 |
| Web_XSS | 340 | 0.718 / 0.589 | 0.226 / 0.475 | 0.226 / 0.470 | 0.703 / 0.040 | 0.797 / 0.042 |

**xgb, random split, per class, leaked test rows** (recall / precision):

| class | support | leaky | +8y | zero | fixA | dropIAT |
|---|---:|---|---|---|---|---|
| Benign | 156,946 | 0.970 / 1.000 | 0.903 / 0.940 | 1.000 / 0.731 | 0.755 / 0.998 | 0.755 / 0.998 |
| Botnet_ARES | 1,154 | 1.000 / 0.805 | 0.825 / 0.873 | 0.000 / 0.000 | 1.000 / 0.104 | 0.999 / 0.104 |
| DDoS_LOIT | 11 | 0.909 / 0.070 | 0.909 / 0.000 | 0.000 / 0.000 | 0.000 / 0.000 | 0.000 / 0.000 |
| DoS_GoldenEye | 129 | 1.000 / 0.037 | 0.000 / 0.000 | 0.000 / 0.000 | 0.000 / 0.000 | 0.000 / 0.000 |
| DoS_Hulk | 32,978 | 0.921 / 0.994 | 0.003 / 1.000 | 0.001 / 1.000 | 0.844 / 0.633 | 0.844 / 0.633 |
| DoS_Slowhttptest | 527 | 0.928 / 0.443 | 0.097 / 1.000 | 0.097 / 0.981 | 0.097 / 1.000 | 0.097 / 0.981 |
| DoS_Slowloris | 225 | 0.991 / 0.418 | 0.000 / 0.000 | 0.000 / 0.000 | 0.027 / 0.107 | 0.027 / 0.107 |
| FTP-Patator | 1,375 | 0.999 / 0.478 | 0.060 / 0.976 | 0.156 / 1.000 | 0.714 / 0.081 | 0.714 / 0.081 |
| Heartbleed | 2 | 1.000 / 0.065 | 0.000 / 0.000 | 0.000 / 0.000 | 0.000 / 0.000 | 0.000 / 0.000 |
| Port_Scan | 40,275 | 1.000 / 0.997 | 0.990 / 1.000 | 0.000 / 1.000 | 0.993 / 1.000 | 0.993 / 1.000 |
| SSH-Patator | 769 | 0.991 / 0.856 | 0.000 / 0.000 | 0.000 / 0.000 | 0.996 / 0.362 | 0.996 / 0.362 |
| Web_Brute_Force | 345 | 0.971 / 0.334 | 0.000 / 0.000 | 0.000 / 0.000 | 0.049 / 0.035 | 0.049 / 0.035 |
| Web_SQL_Injection | 3 | 1.000 / 0.375 | 0.000 / 0.000 | 0.000 / 0.000 | 0.667 / 0.003 | 0.667 / 0.003 |
| Web_XSS | 170 | 0.982 / 0.663 | 0.000 / 0.000 | 0.000 / 0.000 | 0.959 / 0.028 | 0.959 / 0.028 |

**xgb, temporal split, per class, all test rows** (recall / precision):

| class | support | leaky | +8y | zero | fixA | dropIAT |
|---|---:|---|---|---|---|---|
| Benign | 446,559 | 0.975 / 0.998 | 0.981 / 0.924 | 0.999 / 0.852 | 0.923 / 0.999 | 0.920 / 0.999 |
| Botnet_ARES | 1,377 | 0.105 / 1.000 | 0.000 / 0.000 | 0.000 / 0.000 | 0.877 / 0.129 | 0.881 / 0.128 |
| DDoS_LOIT | 23,933 | 0.997 / 1.000 | 0.997 / 1.000 | 0.997 / 1.000 | 0.997 / 1.000 | 0.997 / 1.000 |
| DoS_GoldenEye | 2,091 | 0.943 / 0.910 | 0.805 / 0.897 | 0.805 / 0.897 | 0.801 / 0.898 | 0.800 / 0.890 |
| DoS_Hulk | 87,310 | 0.994 / 1.000 | 0.619 / 1.000 | 0.619 / 1.000 | 0.632 / 1.000 | 0.632 / 1.000 |
| DoS_Slowhttptest | 1,715 | 0.906 / 0.651 | 0.721 / 0.638 | 0.721 / 0.638 | 0.714 / 0.567 | 0.718 / 0.619 |
| DoS_Slowloris | 1,294 | 0.709 / 0.791 | 0.335 / 0.680 | 0.335 / 0.680 | 0.332 / 0.768 | 0.338 / 0.498 |
| FTP-Patator | 2,383 | 0.995 / 0.279 | 0.670 / 0.990 | 0.703 / 0.992 | 0.860 / 0.149 | 0.860 / 0.149 |
| Heartbleed | 3 | 0.667 / 0.001 | 0.333 / 1.000 | 0.333 / 1.000 | 0.667 / 0.000 | 0.667 / 0.000 |
| Port_Scan | 40,331 | 0.996 / 0.941 | 0.996 / 0.801 | 0.005 / 0.990 | 0.990 / 1.000 | 0.990 / 1.000 |
| SSH-Patator | 1,487 | 0.950 / 0.949 | 0.477 / 1.000 | 0.477 / 1.000 | 0.950 / 0.755 | 0.950 / 0.732 |
| Web_Brute_Force | 684 | 0.827 / 0.775 | 0.326 / 0.576 | 0.326 / 0.575 | 0.363 / 0.153 | 0.284 / 0.101 |
| Web_SQL_Injection | 6 | 1.000 / 0.857 | 0.500 / 0.750 | 0.500 / 0.750 | 0.833 / 0.004 | 0.833 / 0.004 |
| Web_XSS | 340 | 0.512 / 0.570 | 0.194 / 0.335 | 0.194 / 0.335 | 0.662 / 0.057 | 0.756 / 0.058 |

**xgb, temporal split, per class, leaked test rows** (recall / precision):

| class | support | leaky | +8y | zero | fixA | dropIAT |
|---|---:|---|---|---|---|---|
| Benign | 161,365 | 0.933 / 0.997 | 0.950 / 0.812 | 1.000 / 0.676 | 0.788 / 0.998 | 0.787 / 0.998 |
| Botnet_ARES | 1,218 | 0.119 / 1.000 | 0.000 / 0.000 | 0.000 / 0.000 | 0.992 / 0.129 | 0.996 / 0.128 |
| DDoS_LOIT | 42 | 0.000 / 0.000 | 0.000 / 0.000 | 0.000 / 0.000 | 0.000 / 0.000 | 0.000 / 0.000 |
| DoS_GoldenEye | 289 | 1.000 / 1.000 | 0.000 / 0.000 | 0.000 / 0.000 | 0.000 / 0.000 | 0.000 / 0.000 |
| DoS_Hulk | 32,764 | 0.999 / 1.000 | 0.001 / 1.000 | 0.001 / 1.000 | 0.036 / 0.998 | 0.036 / 1.000 |
| DoS_Slowhttptest | 555 | 0.753 / 0.761 | 0.180 / 0.990 | 0.180 / 0.990 | 0.180 / 0.385 | 0.180 / 0.437 |
| DoS_Slowloris | 615 | 0.785 / 0.925 | 0.000 / 0.000 | 0.000 / 0.000 | 0.005 / 0.064 | 0.005 / 0.038 |
| FTP-Patator | 1,357 | 0.993 / 0.180 | 0.423 / 0.990 | 0.481 / 0.995 | 0.757 / 0.081 | 0.757 / 0.081 |
| Heartbleed | 1 | 1.000 / 0.000 | 0.000 / 0.000 | 0.000 / 0.000 | 1.000 / 0.000 | 1.000 / 0.000 |
| Port_Scan | 40,175 | 0.997 / 0.940 | 0.997 / 0.801 | 0.002 / 1.000 | 0.992 / 1.000 | 0.992 / 1.000 |
| SSH-Patator | 738 | 0.951 / 0.902 | 0.000 / 0.000 | 0.000 / 0.000 | 0.953 / 0.606 | 0.953 / 0.604 |
| Web_Brute_Force | 344 | 0.997 / 1.000 | 0.000 / 0.000 | 0.000 / 0.000 | 0.049 / 0.014 | 0.049 / 0.014 |
| Web_SQL_Injection | 3 | 1.000 / 1.000 | 0.000 / 0.000 | 0.000 / 0.000 | 0.667 / 0.002 | 0.667 / 0.002 |
| Web_XSS | 172 | 0.628 / 1.000 | 0.000 / 0.000 | 0.000 / 0.000 | 0.942 / 0.043 | 0.942 / 0.043 |

**rf, random split, per class, all test rows** (recall / precision):

| class | support | leaky | +8y | zero | fixA | dropIAT |
|---|---:|---|---|---|---|---|
| Benign | 446,560 | 0.984 / 1.000 | 0.991 / 0.924 | 0.994 / 0.851 | 0.866 / 0.999 | 0.850 / 0.999 |
| Botnet_ARES | 1,377 | 0.999 / 0.587 | 0.853 / 0.387 | 0.162 / 0.508 | 1.000 / 0.159 | 1.000 / 0.089 |
| DDoS_LOIT | 23,933 | 1.000 / 1.000 | 0.999 / 1.000 | 1.000 / 1.000 | 0.999 / 1.000 | 0.999 / 1.000 |
| DoS_GoldenEye | 2,091 | 0.985 / 0.839 | 0.923 / 0.923 | 0.923 / 0.923 | 0.923 / 0.921 | 0.924 / 0.904 |
| DoS_Hulk | 87,310 | 0.999 / 0.992 | 0.621 / 0.990 | 0.621 / 0.990 | 0.940 / 0.831 | 0.939 / 0.831 |
| DoS_Slowhttptest | 1,715 | 0.968 / 0.749 | 0.667 / 0.797 | 0.697 / 0.804 | 0.697 / 0.785 | 0.694 / 0.780 |
| DoS_Slowloris | 1,294 | 0.956 / 0.779 | 0.786 / 0.928 | 0.790 / 0.899 | 0.791 / 0.897 | 0.791 / 0.895 |
| FTP-Patator | 2,383 | 0.997 / 0.782 | 0.422 / 0.977 | 0.422 / 0.977 | 0.829 / 0.145 | 0.829 / 0.144 |
| Heartbleed | 3 | 0.667 / 0.014 | 0.000 / 0.000 | 0.000 / 0.000 | 0.000 / 0.000 | 0.000 / 0.000 |
| Port_Scan | 40,331 | 0.999 / 0.996 | 0.993 / 0.992 | 0.001 / 1.000 | 0.992 / 1.000 | 0.992 / 1.000 |
| SSH-Patator | 1,487 | 0.989 / 0.756 | 0.476 / 1.000 | 0.476 / 1.000 | 0.985 / 0.297 | 0.985 / 0.298 |
| Web_Brute_Force | 683 | 0.775 / 0.220 | 0.269 / 0.159 | 0.269 / 0.159 | 0.265 / 0.096 | 0.252 / 0.097 |
| Web_SQL_Injection | 6 | 0.833 / 0.029 | 0.333 / 0.250 | 0.333 / 0.250 | 0.667 / 0.001 | 0.667 / 0.001 |
| Web_XSS | 340 | 0.824 / 0.208 | 0.324 / 0.117 | 0.324 / 0.117 | 0.821 / 0.015 | 0.871 / 0.015 |

**rf, random split, per class, leaked test rows** (recall / precision):

| class | support | leaky | +8y | zero | fixA | dropIAT |
|---|---:|---|---|---|---|---|
| Benign | 156,946 | 0.972 / 1.000 | 0.992 / 0.811 | 1.000 / 0.668 | 0.638 / 0.998 | 0.595 / 0.997 |
| Botnet_ARES | 1,154 | 0.999 / 0.605 | 0.825 / 0.367 | 0.000 / 0.000 | 1.000 / 0.140 | 1.000 / 0.077 |
| DDoS_LOIT | 11 | 0.818 / 0.750 | 0.000 / 0.000 | 0.091 / 1.000 | 0.000 / 0.000 | 0.000 / 0.000 |
| DoS_GoldenEye | 129 | 1.000 / 0.355 | 0.000 / 0.000 | 0.000 / 0.000 | 0.000 / 0.000 | 0.000 / 0.000 |
| DoS_Hulk | 32,978 | 1.000 / 0.995 | 0.000 / 1.000 | 0.000 / 1.000 | 0.844 / 0.633 | 0.843 / 0.633 |
| DoS_Slowhttptest | 527 | 0.979 / 0.661 | 0.000 / 0.000 | 0.097 / 0.981 | 0.097 / 0.981 | 0.097 / 0.962 |
| DoS_Slowloris | 225 | 0.978 / 0.448 | 0.000 / 0.000 | 0.022 / 0.122 | 0.022 / 0.122 | 0.022 / 0.122 |
| FTP-Patator | 1,375 | 0.996 / 0.682 | 0.000 / 0.000 | 0.000 / 0.000 | 0.705 / 0.077 | 0.705 / 0.076 |
| Heartbleed | 2 | 1.000 / 0.014 | 0.000 / 0.000 | 0.000 / 0.000 | 0.000 / 0.000 | 0.000 / 0.000 |
| Port_Scan | 40,275 | 1.000 / 0.996 | 0.993 / 0.992 | 0.000 / 1.000 | 0.993 / 1.000 | 0.993 / 1.000 |
| SSH-Patator | 769 | 0.991 / 0.617 | 0.000 / 0.000 | 0.000 / 0.000 | 0.984 / 0.179 | 0.984 / 0.180 |
| Web_Brute_Force | 345 | 1.000 / 0.277 | 0.000 / 0.000 | 0.000 / 0.000 | 0.000 / 0.000 | 0.000 / 0.000 |
| Web_SQL_Injection | 3 | 1.000 / 0.019 | 0.000 / 0.000 | 0.000 / 0.000 | 0.667 / 0.000 | 0.667 / 0.000 |
| Web_XSS | 170 | 1.000 / 0.419 | 0.000 / 0.000 | 0.000 / 0.000 | 0.965 / 0.009 | 0.965 / 0.009 |

**rf, temporal split, per class, all test rows** (recall / precision):

| class | support | leaky | +8y | zero | fixA | dropIAT |
|---|---:|---|---|---|---|---|
| Benign | 446,559 | 0.982 / 0.950 | 0.994 / 0.921 | 0.994 / 0.850 | 0.869 / 0.998 | 0.858 / 0.998 |
| Botnet_ARES | 1,377 | 0.105 / 1.000 | 0.000 / 0.000 | 0.000 / 0.000 | 0.877 / 0.148 | 0.876 / 0.092 |
| DDoS_LOIT | 23,933 | 0.997 / 1.000 | 0.997 / 1.000 | 0.997 / 1.000 | 0.997 / 1.000 | 0.997 / 1.000 |
| DoS_GoldenEye | 2,091 | 0.846 / 0.292 | 0.804 / 0.893 | 0.804 / 0.893 | 0.809 / 0.887 | 0.793 / 0.900 |
| DoS_Hulk | 87,310 | 0.717 / 0.992 | 0.618 / 0.992 | 0.618 / 0.992 | 0.631 / 0.992 | 0.631 / 0.993 |
| DoS_Slowhttptest | 1,715 | 0.941 / 0.599 | 0.661 / 0.527 | 0.720 / 0.538 | 0.718 / 0.520 | 0.719 / 0.566 |
| DoS_Slowloris | 1,294 | 0.781 / 0.933 | 0.332 / 0.861 | 0.332 / 0.860 | 0.335 / 0.817 | 0.337 / 0.656 |
| FTP-Patator | 2,383 | 0.637 / 0.983 | 0.430 / 0.975 | 0.430 / 0.975 | 0.861 / 0.143 | 0.861 / 0.144 |
| Heartbleed | 3 | 0.667 / 0.000 | 0.333 / 0.250 | 0.333 / 0.250 | 0.667 / 0.000 | 0.667 / 0.000 |
| Port_Scan | 40,331 | 0.986 / 0.973 | 0.983 / 0.966 | 0.001 / 1.000 | 0.989 / 1.000 | 0.989 / 1.000 |
| SSH-Patator | 1,487 | 0.510 / 0.996 | 0.477 / 1.000 | 0.477 / 1.000 | 0.949 / 0.259 | 0.948 / 0.261 |
| Web_Brute_Force | 684 | 0.301 / 0.165 | 0.224 / 0.128 | 0.224 / 0.128 | 0.222 / 0.080 | 0.212 / 0.066 |
| Web_SQL_Injection | 6 | 1.000 / 0.043 | 0.500 / 0.375 | 0.500 / 0.375 | 0.833 / 0.001 | 0.833 / 0.001 |
| Web_XSS | 340 | 0.435 / 0.126 | 0.306 / 0.092 | 0.306 / 0.092 | 0.791 / 0.014 | 0.809 / 0.014 |

**rf, temporal split, per class, leaked test rows** (recall / precision):

| class | support | leaky | +8y | zero | fixA | dropIAT |
|---|---:|---|---|---|---|---|
| Benign | 161,365 | 0.967 / 0.874 | 0.999 / 0.811 | 1.000 / 0.674 | 0.655 / 0.998 | 0.624 / 0.997 |
| Botnet_ARES | 1,218 | 0.119 / 1.000 | 0.000 / 0.000 | 0.000 / 0.000 | 0.991 / 0.148 | 0.990 / 0.092 |
| DDoS_LOIT | 42 | 0.000 / 0.000 | 0.000 / 0.000 | 0.024 / 1.000 | 0.024 / 1.000 | 0.024 / 1.000 |
| DoS_GoldenEye | 289 | 0.304 / 0.021 | 0.000 / 0.000 | 0.000 / 0.000 | 0.000 / 0.000 | 0.000 / 0.000 |
| DoS_Hulk | 32,764 | 0.263 / 0.991 | 0.000 / 0.000 | 0.000 / 0.000 | 0.036 / 0.972 | 0.035 / 0.973 |
| DoS_Slowhttptest | 555 | 0.863 / 0.882 | 0.000 / 0.000 | 0.180 / 0.704 | 0.180 / 0.641 | 0.180 / 0.775 |
| DoS_Slowloris | 615 | 0.945 / 0.993 | 0.000 / 0.000 | 0.000 / 0.000 | 0.005 / 0.097 | 0.005 / 0.052 |
| FTP-Patator | 1,357 | 0.363 / 1.000 | 0.000 / 0.000 | 0.000 / 0.000 | 0.757 / 0.078 | 0.757 / 0.078 |
| Heartbleed | 1 | 1.000 / 0.000 | 0.000 / 0.000 | 0.000 / 0.000 | 1.000 / 0.000 | 1.000 / 0.000 |
| Port_Scan | 40,175 | 0.989 / 0.973 | 0.986 / 0.966 | 0.000 / 0.000 | 0.992 / 1.000 | 0.992 / 1.000 |
| SSH-Patator | 738 | 0.066 / 0.942 | 0.000 / 0.000 | 0.000 / 0.000 | 0.951 / 0.149 | 0.951 / 0.149 |
| Web_Brute_Force | 344 | 0.154 / 1.000 | 0.000 / 0.000 | 0.000 / 0.000 | 0.000 / 0.000 | 0.000 / 0.000 |
| Web_SQL_Injection | 3 | 1.000 / 0.023 | 0.000 / 0.000 | 0.000 / 0.000 | 0.667 / 0.000 | 0.667 / 0.000 |
| Web_XSS | 172 | 0.256 / 1.000 | 0.000 / 0.000 | 0.000 / 0.000 | 0.953 / 0.009 | 0.953 / 0.009 |

**mlp, random split, per class, all test rows** (recall / precision):

| class | support | leaky | +8y | zero | fixA | dropIAT |
|---|---:|---|---|---|---|---|
| Benign | 446,560 | 0.949 / 0.981 | 0.950 / 0.981 | 0.998 / 0.852 | 0.949 / 0.981 | 0.949 / 0.981 |
| Botnet_ARES | 1,377 | 0.821 / 0.998 | 0.821 / 0.998 | 0.131 / 0.989 | 0.817 / 0.994 | 0.816 / 0.996 |
| DDoS_LOIT | 23,933 | 1.000 / 1.000 | 1.000 / 1.000 | 1.000 / 1.000 | 0.999 / 1.000 | 1.000 / 1.000 |
| DoS_GoldenEye | 2,091 | 0.893 / 0.996 | 0.893 / 0.996 | 0.893 / 0.996 | 0.903 / 0.974 | 0.892 / 0.963 |
| DoS_Hulk | 87,310 | 0.937 / 0.777 | 0.937 / 0.777 | 0.619 / 0.991 | 0.939 / 0.776 | 0.940 / 0.775 |
| DoS_Slowhttptest | 1,715 | 0.685 / 0.803 | 0.685 / 0.803 | 0.655 / 0.796 | 0.691 / 0.828 | 0.693 / 0.826 |
| DoS_Slowloris | 1,294 | 0.772 / 0.955 | 0.772 / 0.955 | 0.772 / 0.955 | 0.747 / 0.960 | 0.767 / 0.976 |
| FTP-Patator | 2,383 | 0.647 / 0.950 | 0.644 / 0.956 | 0.424 / 0.990 | 0.632 / 0.958 | 0.654 / 0.927 |
| Heartbleed | 3 | 0.000 / 0.000 | 0.000 / 0.000 | 0.000 / 0.000 | 0.000 / 0.000 | 0.000 / 0.000 |
| Port_Scan | 40,331 | 0.993 / 1.000 | 0.993 / 1.000 | 0.038 / 0.995 | 0.992 / 1.000 | 0.992 / 1.000 |
| SSH-Patator | 1,487 | 0.477 / 0.996 | 0.477 / 0.996 | 0.477 / 0.996 | 0.476 / 1.000 | 0.477 / 0.999 |
| Web_Brute_Force | 683 | 0.026 / 1.000 | 0.026 / 1.000 | 0.026 / 1.000 | 0.026 / 1.000 | 0.026 / 1.000 |
| Web_SQL_Injection | 6 | 0.000 / 0.000 | 0.000 / 0.000 | 0.000 / 0.000 | 0.000 / 0.000 | 0.000 / 0.000 |
| Web_XSS | 340 | 0.018 / 1.000 | 0.018 / 1.000 | 0.018 / 1.000 | 0.018 / 1.000 | 0.018 / 1.000 |

**mlp, random split, per class, leaked test rows** (recall / precision):

| class | support | leaky | +8y | zero | fixA | dropIAT |
|---|---:|---|---|---|---|---|
| Benign | 156,946 | 0.859 / 0.948 | 0.860 / 0.948 | 0.999 / 0.672 | 0.860 / 0.948 | 0.859 / 0.948 |
| Botnet_ARES | 1,154 | 0.822 / 1.000 | 0.822 / 1.000 | 0.000 / 0.000 | 0.824 / 1.000 | 0.822 / 0.996 |
| DDoS_LOIT | 11 | 0.000 / 0.000 | 0.000 / 0.000 | 0.000 / 0.000 | 0.000 / 0.000 | 0.000 / 0.000 |
| DoS_GoldenEye | 129 | 0.000 / 0.000 | 0.000 / 0.000 | 0.000 / 0.000 | 0.000 / 0.000 | 0.000 / 0.000 |
| DoS_Hulk | 32,978 | 0.843 / 0.546 | 0.843 / 0.546 | 0.000 / 0.034 | 0.843 / 0.546 | 0.843 / 0.545 |
| DoS_Slowhttptest | 527 | 0.097 / 1.000 | 0.097 / 1.000 | 0.000 / 0.000 | 0.095 / 0.943 | 0.097 / 0.981 |
| DoS_Slowloris | 225 | 0.000 / 0.000 | 0.000 / 0.000 | 0.000 / 0.000 | 0.000 / 0.000 | 0.000 / 0.000 |
| FTP-Patator | 1,375 | 0.395 / 0.870 | 0.390 / 0.884 | 0.009 / 0.545 | 0.370 / 0.885 | 0.404 / 0.821 |
| Heartbleed | 2 | 0.000 / 0.000 | 0.000 / 0.000 | 0.000 / 0.000 | 0.000 / 0.000 | 0.000 / 0.000 |
| Port_Scan | 40,275 | 0.993 / 1.000 | 0.993 / 1.000 | 0.037 / 1.000 | 0.993 / 1.000 | 0.993 / 1.000 |
| SSH-Patator | 769 | 0.000 / 0.000 | 0.000 / 0.000 | 0.000 / 0.000 | 0.000 / 0.000 | 0.000 / 0.000 |
| Web_Brute_Force | 345 | 0.000 / 0.000 | 0.000 / 0.000 | 0.000 / 0.000 | 0.000 / 0.000 | 0.000 / 0.000 |
| Web_SQL_Injection | 3 | 0.000 / 0.000 | 0.000 / 0.000 | 0.000 / 0.000 | 0.000 / 0.000 | 0.000 / 0.000 |
| Web_XSS | 170 | 0.000 / 0.000 | 0.000 / 0.000 | 0.000 / 0.000 | 0.000 / 0.000 | 0.000 / 0.000 |

**mlp, temporal split, per class, all test rows** (recall / precision):

| class | support | leaky | +8y | zero | fixA | dropIAT |
|---|---:|---|---|---|---|---|
| Benign | 446,559 | 0.951 / 0.979 | 0.951 / 0.979 | 0.998 / 0.850 | 0.950 / 0.980 | 0.950 / 0.979 |
| Botnet_ARES | 1,377 | 0.873 / 0.996 | 0.873 / 0.996 | 0.000 / 0.000 | 0.879 / 0.908 | 0.866 / 0.993 |
| DDoS_LOIT | 23,933 | 0.997 / 1.000 | 0.997 / 1.000 | 0.997 / 1.000 | 0.997 / 1.000 | 0.997 / 1.000 |
| DoS_GoldenEye | 2,091 | 0.783 / 0.892 | 0.783 / 0.892 | 0.783 / 0.863 | 0.795 / 0.963 | 0.794 / 0.971 |
| DoS_Hulk | 87,310 | 0.929 / 0.778 | 0.929 / 0.778 | 0.616 / 0.994 | 0.931 / 0.778 | 0.929 / 0.778 |
| DoS_Slowhttptest | 1,715 | 0.703 / 0.622 | 0.703 / 0.622 | 0.703 / 0.622 | 0.717 / 0.651 | 0.717 / 0.663 |
| DoS_Slowloris | 1,294 | 0.307 / 0.717 | 0.307 / 0.717 | 0.307 / 0.717 | 0.337 / 0.600 | 0.335 / 0.760 |
| FTP-Patator | 2,383 | 0.710 / 0.960 | 0.708 / 0.963 | 0.430 / 1.000 | 0.703 / 0.970 | 0.708 / 0.960 |
| Heartbleed | 3 | 0.333 / 1.000 | 0.333 / 1.000 | 0.333 / 1.000 | 0.333 / 1.000 | 0.333 / 1.000 |
| Port_Scan | 40,331 | 0.989 / 0.999 | 0.989 / 0.999 | 0.015 / 0.949 | 0.988 / 0.998 | 0.988 / 0.999 |
| SSH-Patator | 1,487 | 0.473 / 1.000 | 0.473 / 1.000 | 0.473 / 1.000 | 0.484 / 1.000 | 0.486 / 1.000 |
| Web_Brute_Force | 684 | 0.025 / 0.944 | 0.025 / 0.944 | 0.025 / 0.944 | 0.025 / 0.189 | 0.025 / 0.198 |
| Web_SQL_Injection | 6 | 0.000 / 0.000 | 0.000 / 0.000 | 0.000 / 0.000 | 0.000 / 0.000 | 0.000 / 0.000 |
| Web_XSS | 340 | 0.012 / 0.800 | 0.012 / 0.800 | 0.012 / 1.000 | 0.012 / 1.000 | 0.012 / 1.000 |

**mlp, temporal split, per class, leaked test rows** (recall / precision):

| class | support | leaky | +8y | zero | fixA | dropIAT |
|---|---:|---|---|---|---|---|
| Benign | 161,365 | 0.867 / 0.949 | 0.867 / 0.949 | 1.000 / 0.675 | 0.867 / 0.949 | 0.867 / 0.948 |
| Botnet_ARES | 1,218 | 0.987 / 1.000 | 0.987 / 1.000 | 0.000 / 0.000 | 0.993 / 0.926 | 0.979 / 1.000 |
| DDoS_LOIT | 42 | 0.000 / 0.000 | 0.000 / 0.000 | 0.000 / 0.000 | 0.000 / 0.000 | 0.000 / 0.000 |
| DoS_GoldenEye | 289 | 0.000 / 0.000 | 0.000 / 0.000 | 0.000 / 0.000 | 0.000 / 0.000 | 0.000 / 0.000 |
| DoS_Hulk | 32,764 | 0.835 / 0.545 | 0.835 / 0.545 | 0.000 / 0.000 | 0.835 / 0.545 | 0.834 / 0.545 |
| DoS_Slowhttptest | 555 | 0.178 / 0.990 | 0.178 / 0.990 | 0.178 / 0.990 | 0.178 / 0.952 | 0.178 / 0.980 |
| DoS_Slowloris | 615 | 0.000 / 0.000 | 0.000 / 0.000 | 0.000 / 0.000 | 0.005 / 0.115 | 0.000 / 0.000 |
| FTP-Patator | 1,357 | 0.492 / 0.905 | 0.488 / 0.912 | 0.000 / 0.000 | 0.480 / 0.926 | 0.489 / 0.908 |
| Heartbleed | 1 | 0.000 / 0.000 | 0.000 / 0.000 | 0.000 / 0.000 | 0.000 / 0.000 | 0.000 / 0.000 |
| Port_Scan | 40,175 | 0.992 / 0.999 | 0.992 / 0.999 | 0.014 / 0.949 | 0.992 / 1.000 | 0.992 / 1.000 |
| SSH-Patator | 738 | 0.000 / 0.000 | 0.000 / 0.000 | 0.000 / 0.000 | 0.000 / 0.000 | 0.000 / 0.000 |
| Web_Brute_Force | 344 | 0.000 / 0.000 | 0.000 / 0.000 | 0.000 / 0.000 | 0.000 / 0.000 | 0.000 / 0.000 |
| Web_SQL_Injection | 3 | 0.000 / 0.000 | 0.000 / 0.000 | 0.000 / 0.000 | 0.000 / 0.000 | 0.000 / 0.000 |
| Web_XSS | 172 | 0.000 / 0.000 | 0.000 / 0.000 | 0.000 / 0.000 | 0.000 / 0.000 | 0.000 / 0.000 |

**knn, random split, per class, all test rows** (recall / precision):

| class | support | leaky | +8y | zero | fixA | dropIAT |
|---|---:|---|---|---|---|---|
| Benign | 446,560 | 0.996 / 0.999 | 0.999 / 0.926 | 0.999 / 0.852 | 0.937 / 0.996 | 0.936 / 0.995 |
| Botnet_ARES | 1,377 | 0.972 / 0.874 | 0.837 / 0.989 | 0.147 / 0.940 | 0.983 / 0.162 | 0.978 / 0.161 |
| DDoS_LOIT | 23,933 | 0.999 / 1.000 | 0.999 / 1.000 | 0.999 / 1.000 | 0.999 / 0.358 | 0.999 / 0.358 |
| DoS_GoldenEye | 2,091 | 0.957 / 0.899 | 0.895 / 0.955 | 0.895 / 0.955 | 0.933 / 0.145 | 0.919 / 0.143 |
| DoS_Hulk | 87,310 | 0.999 / 0.997 | 0.633 / 0.997 | 0.622 / 0.997 | 0.633 / 0.997 | 0.633 / 0.997 |
| DoS_Slowhttptest | 1,715 | 0.941 / 0.797 | 0.668 / 0.884 | 0.668 / 0.874 | 0.665 / 0.884 | 0.647 / 0.880 |
| DoS_Slowloris | 1,294 | 0.947 / 0.860 | 0.780 / 0.944 | 0.780 / 0.944 | 0.785 / 0.922 | 0.784 / 0.912 |
| FTP-Patator | 2,383 | 0.988 / 0.785 | 0.558 / 0.966 | 0.423 / 1.000 | 0.662 / 0.969 | 0.662 / 0.969 |
| Heartbleed | 3 | 0.000 / 0.000 | 0.000 / 0.000 | 0.000 / 0.000 | 0.000 / 0.000 | 0.000 / 0.000 |
| Port_Scan | 40,331 | 0.994 / 0.999 | 0.993 / 0.999 | 0.012 / 0.988 | 0.993 / 1.000 | 0.993 / 1.000 |
| SSH-Patator | 1,487 | 0.989 / 0.997 | 0.475 / 1.000 | 0.475 / 1.000 | 0.475 / 1.000 | 0.475 / 1.000 |
| Web_Brute_Force | 683 | 0.577 / 0.758 | 0.340 / 0.682 | 0.340 / 0.682 | 0.382 / 0.704 | 0.179 / 0.421 |
| Web_SQL_Injection | 6 | 0.500 / 0.600 | 0.167 / 0.500 | 0.167 / 0.500 | 0.167 / 0.500 | 0.167 / 0.500 |
| Web_XSS | 340 | 0.559 / 0.625 | 0.174 / 0.404 | 0.174 / 0.404 | 0.185 / 0.426 | 0.097 / 0.232 |

**knn, random split, per class, leaked test rows** (recall / precision):

| class | support | leaky | +8y | zero | fixA | dropIAT |
|---|---:|---|---|---|---|---|
| Benign | 156,946 | 0.990 / 0.997 | 0.999 / 0.815 | 1.000 / 0.669 | 0.822 / 0.988 | 0.822 / 0.988 |
| Botnet_ARES | 1,154 | 0.984 / 0.863 | 0.823 / 1.000 | 0.000 / 0.000 | 0.998 / 0.141 | 0.997 / 0.141 |
| DDoS_LOIT | 11 | 0.818 / 0.750 | 0.000 / 0.000 | 0.000 / 0.000 | 0.909 / 0.000 | 0.909 / 0.000 |
| DoS_GoldenEye | 129 | 1.000 / 0.487 | 0.000 / 0.000 | 0.000 / 0.000 | 0.512 / 0.006 | 0.512 / 0.006 |
| DoS_Hulk | 32,978 | 1.000 / 0.995 | 0.031 / 0.981 | 0.000 / 0.000 | 0.031 / 0.983 | 0.031 / 0.985 |
| DoS_Slowhttptest | 527 | 0.985 / 0.663 | 0.095 / 0.962 | 0.095 / 0.746 | 0.095 / 0.962 | 0.095 / 0.962 |
| DoS_Slowloris | 225 | 0.960 / 0.608 | 0.000 / 0.000 | 0.000 / 0.000 | 0.022 / 0.122 | 0.022 / 0.122 |
| FTP-Patator | 1,375 | 0.981 / 0.676 | 0.236 / 0.874 | 0.002 / 1.000 | 0.417 / 0.918 | 0.417 / 0.918 |
| Heartbleed | 2 | 0.000 / 0.000 | 0.000 / 0.000 | 0.000 / 0.000 | 0.000 / 0.000 | 0.000 / 0.000 |
| Port_Scan | 40,275 | 0.994 / 0.999 | 0.993 / 1.000 | 0.011 / 0.991 | 0.993 / 1.000 | 0.993 / 1.000 |
| SSH-Patator | 769 | 0.993 / 0.995 | 0.000 / 0.000 | 0.000 / 0.000 | 0.000 / 0.000 | 0.000 / 0.000 |
| Web_Brute_Force | 345 | 0.470 / 0.900 | 0.000 / 0.000 | 0.000 / 0.000 | 0.049 / 1.000 | 0.049 / 1.000 |
| Web_SQL_Injection | 3 | 0.667 / 0.667 | 0.000 / 0.000 | 0.000 / 0.000 | 0.000 / 0.000 | 0.000 / 0.000 |
| Web_XSS | 170 | 0.771 / 0.829 | 0.000 / 0.000 | 0.000 / 0.000 | 0.024 / 0.667 | 0.024 / 0.667 |

**knn, temporal split, per class, all test rows** (recall / precision):

| class | support | leaky | +8y | zero | fixA | dropIAT |
|---|---:|---|---|---|---|---|
| Benign | 446,559 | 0.997 / 0.942 | 0.951 / 0.980 | 0.999 / 0.850 | 0.939 / 0.994 | 0.938 / 0.994 |
| Botnet_ARES | 1,377 | 0.874 / 0.995 | 0.874 / 0.997 | 0.000 / 0.000 | 0.877 / 0.149 | 0.874 / 0.149 |
| DDoS_LOIT | 23,933 | 0.999 / 0.971 | 0.999 / 0.328 | 0.997 / 0.999 | 0.999 / 0.366 | 0.999 / 0.366 |
| DoS_GoldenEye | 2,091 | 0.818 / 0.868 | 0.808 / 0.866 | 0.808 / 0.843 | 0.872 / 0.131 | 0.879 / 0.131 |
| DoS_Hulk | 87,310 | 0.717 / 0.997 | 0.632 / 0.997 | 0.618 / 0.998 | 0.632 / 0.997 | 0.631 / 0.997 |
| DoS_Slowhttptest | 1,715 | 0.724 / 0.738 | 0.710 / 0.747 | 0.710 / 0.727 | 0.700 / 0.682 | 0.698 / 0.687 |
| DoS_Slowloris | 1,294 | 0.386 / 0.733 | 0.335 / 0.718 | 0.335 / 0.718 | 0.338 / 0.806 | 0.336 / 0.674 |
| FTP-Patator | 2,383 | 0.726 / 0.970 | 0.523 / 0.981 | 0.429 / 0.996 | 0.715 / 0.969 | 0.715 / 0.969 |
| Heartbleed | 3 | 0.333 / 1.000 | 0.333 / 1.000 | 0.333 / 1.000 | 0.333 / 1.000 | 0.333 / 1.000 |
| Port_Scan | 40,331 | 0.988 / 0.999 | 0.988 / 0.995 | 0.012 / 0.996 | 0.988 / 1.000 | 0.988 / 1.000 |
| SSH-Patator | 1,487 | 0.956 / 0.987 | 0.484 / 0.999 | 0.484 / 0.999 | 0.484 / 0.999 | 0.484 / 1.000 |
| Web_Brute_Force | 684 | 0.390 / 0.752 | 0.325 / 0.716 | 0.325 / 0.716 | 0.354 / 0.722 | 0.175 / 0.393 |
| Web_SQL_Injection | 6 | 0.833 / 0.714 | 0.500 / 0.750 | 0.500 / 0.750 | 0.500 / 0.750 | 0.500 / 0.600 |
| Web_XSS | 340 | 0.221 / 0.401 | 0.209 / 0.390 | 0.209 / 0.390 | 0.224 / 0.409 | 0.071 / 0.194 |

**knn, temporal split, per class, leaked test rows** (recall / precision):

| class | support | leaky | +8y | zero | fixA | dropIAT |
|---|---:|---|---|---|---|---|
| Benign | 161,365 | 0.995 / 0.857 | 0.867 / 0.946 | 0.999 / 0.675 | 0.833 / 0.988 | 0.833 / 0.988 |
| Botnet_ARES | 1,218 | 0.988 / 0.998 | 0.988 / 1.000 | 0.000 / 0.000 | 0.991 / 0.149 | 0.988 / 0.149 |
| DDoS_LOIT | 42 | 0.976 / 0.055 | 0.976 / 0.001 | 0.000 / 0.000 | 0.976 / 0.001 | 0.976 / 0.001 |
| DoS_GoldenEye | 289 | 0.073 / 1.000 | 0.000 / 0.000 | 0.000 / 0.000 | 0.495 / 0.012 | 0.495 / 0.012 |
| DoS_Hulk | 32,764 | 0.265 / 0.996 | 0.036 / 0.979 | 0.000 / 0.000 | 0.036 / 0.980 | 0.036 / 0.984 |
| DoS_Slowhttptest | 555 | 0.222 / 0.794 | 0.178 / 0.980 | 0.178 / 0.673 | 0.178 / 0.430 | 0.178 / 0.430 |
| DoS_Slowloris | 615 | 0.109 / 0.848 | 0.000 / 0.000 | 0.000 / 0.000 | 0.005 / 0.064 | 0.005 / 0.064 |
| FTP-Patator | 1,357 | 0.520 / 0.930 | 0.165 / 0.903 | 0.000 / 0.000 | 0.502 / 0.927 | 0.502 / 0.927 |
| Heartbleed | 1 | 0.000 / 0.000 | 0.000 / 0.000 | 0.000 / 0.000 | 0.000 / 0.000 | 0.000 / 0.000 |
| Port_Scan | 40,175 | 0.990 / 0.999 | 0.990 / 0.995 | 0.010 / 1.000 | 0.990 / 1.000 | 0.990 / 1.000 |
| SSH-Patator | 738 | 0.951 / 0.975 | 0.000 / 0.000 | 0.000 / 0.000 | 0.000 / 0.000 | 0.000 / 0.000 |
| Web_Brute_Force | 344 | 0.131 / 1.000 | 0.000 / 0.000 | 0.000 / 0.000 | 0.049 / 1.000 | 0.049 / 1.000 |
| Web_SQL_Injection | 3 | 0.667 / 0.667 | 0.000 / 0.000 | 0.000 / 0.000 | 0.000 / 0.000 | 0.000 / 0.000 |
| Web_XSS | 172 | 0.023 / 0.800 | 0.000 / 0.000 | 0.000 / 0.000 | 0.023 / 1.000 | 0.023 / 1.000 |

### 4.3 BCCC-cPacket-Cloud-DDoS-2024

**Overall** (all test rows, then leaked test rows):

| model | split | condition | accuracy (all) [95% CI] | macro F1 (all) | MAR (all) [95% CI] | accuracy (leaked) | MAR (leaked) | n attack classes in MAR (leaked) |
|---|---|---|---|---:|---|---:|---:|---:|
| gnb | random | leaky | 0.207 [0.206, 0.209] | 0.048 | 0.107 [0.106, 0.109] | 0.297 | 0.059 | 17 |
| gnb | random | +8y | 0.207 [0.206, 0.209] | 0.048 | 0.107 [0.106, 0.109] | 0.297 | 0.059 | 17 |
| gnb | random | zero | 0.019 [0.018, 0.019] | 0.023 | 0.060 [0.059, 0.062] | 0.008 | 0.047 | 17 |
| gnb | random | fixA | 0.016 [0.015, 0.016] | 0.029 | 0.056 [0.053, 0.060] | 0.009 | 0.000 | 17 |
| gnb | random | dropIAT | 0.016 [0.015, 0.016] | 0.029 | 0.056 [0.053, 0.060] | 0.009 | 0.000 | 17 |
| gnb | temporal | leaky | 0.207 [0.205, 0.208] | 0.049 | 0.101 [0.100, 0.103] | 0.295 | 0.059 | 17 |
| gnb | temporal | +8y | 0.207 [0.205, 0.208] | 0.049 | 0.101 [0.100, 0.102] | 0.295 | 0.059 | 17 |
| gnb | temporal | zero | 0.018 [0.018, 0.019] | 0.025 | 0.057 [0.056, 0.058] | 0.008 | 0.049 | 17 |
| gnb | temporal | fixA | 0.017 [0.016, 0.017] | 0.029 | 0.035 [0.034, 0.037] | 0.009 | 0.000 | 17 |
| gnb | temporal | dropIAT | 0.017 [0.016, 0.018] | 0.029 | 0.035 [0.034, 0.037] | 0.009 | 0.000 | 17 |
| dt | random | leaky | 0.748 [0.746, 0.750] | 0.447 | 0.559 [0.552, 0.566] | 0.815 | 0.929 | 17 |
| dt | random | +8y | 0.339 [0.337, 0.341] | 0.254 | 0.206 [0.200, 0.212] | 0.190 | 0.000 | 17 |
| dt | random | zero | 0.494 [0.492, 0.497] | 0.269 | 0.207 [0.201, 0.213] | 0.427 | 0.001 | 17 |
| dt | random | fixA | 0.658 [0.656, 0.661] | 0.308 | 0.303 [0.296, 0.311] | 0.676 | 0.133 | 17 |
| dt | random | dropIAT | 0.658 [0.656, 0.660] | 0.308 | 0.303 [0.296, 0.311] | 0.676 | 0.134 | 17 |
| dt | temporal | leaky | 0.539 [0.536, 0.541] | 0.297 | 0.292 [0.286, 0.299] | 0.509 | 0.230 | 17 |
| dt | temporal | +8y | 0.298 [0.296, 0.300] | 0.238 | 0.186 [0.181, 0.192] | 0.142 | 0.001 | 17 |
| dt | temporal | zero | 0.450 [0.447, 0.452] | 0.236 | 0.186 [0.181, 0.192] | 0.374 | 0.001 | 17 |
| dt | temporal | fixA | 0.596 [0.593, 0.598] | 0.275 | 0.269 [0.262, 0.275] | 0.596 | 0.118 | 17 |
| dt | temporal | dropIAT | 0.595 [0.592, 0.597] | 0.273 | 0.261 [0.254, 0.268] | 0.596 | 0.117 | 17 |
| lr | random | leaky | 0.583 [0.581, 0.585] | 0.271 | 0.258 [0.251, 0.265] | 0.612 | 0.106 | 17 |
| lr | random | +8y | 0.532 [0.530, 0.535] | 0.243 | 0.258 [0.251, 0.264] | 0.534 | 0.130 | 17 |
| lr | random | zero | 0.410 [0.407, 0.412] | 0.245 | 0.248 [0.241, 0.254] | 0.347 | 0.117 | 17 |
| lr | random | fixA | 0.583 [0.581, 0.585] | 0.271 | 0.259 [0.251, 0.266] | 0.611 | 0.106 | 17 |
| lr | temporal | leaky | 0.556 [0.554, 0.559] | 0.232 | 0.224 [0.218, 0.230] | 0.575 | 0.113 | 17 |
| lr | temporal | +8y | 0.481 [0.479, 0.483] | 0.225 | 0.214 [0.209, 0.220] | 0.460 | 0.092 | 17 |
| lr | temporal | zero | 0.399 [0.397, 0.402] | 0.208 | 0.209 [0.204, 0.213] | 0.336 | 0.101 | 17 |
| lr | temporal | fixA | 0.556 [0.554, 0.558] | 0.231 | 0.224 [0.219, 0.230] | 0.575 | 0.113 | 17 |
| xgb | random | leaky | 0.760 [0.758, 0.762] | 0.482 | 0.585 [0.579, 0.592] | 0.811 | 0.911 | 17 |
| xgb | random | +8y | 0.393 [0.390, 0.395] | 0.314 | 0.236 [0.230, 0.242] | 0.250 | 0.000 | 17 |
| xgb | random | zero | 0.562 [0.559, 0.564] | 0.327 | 0.236 [0.230, 0.242] | 0.508 | 0.001 | 17 |
| xgb | random | fixA | 0.677 [0.675, 0.679] | 0.341 | 0.330 [0.322, 0.337] | 0.684 | 0.137 | 17 |
| xgb | random | dropIAT | 0.659 [0.656, 0.661] | 0.339 | 0.333 [0.326, 0.341] | 0.660 | 0.142 | 17 |
| xgb | temporal | leaky | 0.634 [0.632, 0.636] | 0.380 | 0.387 [0.379, 0.395] | 0.634 | 0.539 | 17 |
| xgb | temporal | +8y | 0.355 [0.352, 0.357] | 0.262 | 0.186 [0.181, 0.191] | 0.207 | 0.000 | 17 |
| xgb | temporal | zero | 0.506 [0.503, 0.508] | 0.263 | 0.186 [0.181, 0.191] | 0.438 | 0.001 | 17 |
| xgb | temporal | fixA | 0.615 [0.613, 0.618] | 0.300 | 0.272 [0.265, 0.278] | 0.605 | 0.121 | 17 |
| xgb | temporal | dropIAT | 0.615 [0.613, 0.617] | 0.298 | 0.272 [0.266, 0.279] | 0.607 | 0.122 | 17 |
| rf | random | leaky | 0.759 [0.757, 0.761] | 0.470 | 0.596 [0.590, 0.603] | 0.817 | 0.943 | 17 |
| rf | random | +8y | 0.314 [0.312, 0.316] | 0.271 | 0.239 [0.232, 0.246] | 0.138 | 0.003 | 17 |
| rf | random | zero | 0.444 [0.442, 0.447] | 0.318 | 0.237 [0.231, 0.244] | 0.337 | 0.001 | 17 |
| rf | random | fixA | 0.615 [0.613, 0.617] | 0.334 | 0.345 [0.337, 0.353] | 0.598 | 0.144 | 17 |
| rf | random | dropIAT | 0.616 [0.614, 0.618] | 0.335 | 0.340 [0.333, 0.348] | 0.597 | 0.142 | 17 |
| rf | temporal | leaky | 0.591 [0.589, 0.594] | 0.339 | 0.348 [0.342, 0.355] | 0.575 | 0.460 | 17 |
| rf | temporal | +8y | 0.288 [0.286, 0.290] | 0.241 | 0.193 [0.188, 0.197] | 0.113 | 0.001 | 17 |
| rf | temporal | zero | 0.409 [0.407, 0.411] | 0.261 | 0.193 [0.188, 0.197] | 0.297 | 0.001 | 17 |
| rf | temporal | fixA | 0.607 [0.605, 0.609] | 0.297 | 0.278 [0.272, 0.285] | 0.602 | 0.118 | 17 |
| rf | temporal | dropIAT | 0.610 [0.608, 0.612] | 0.299 | 0.280 [0.274, 0.286] | 0.603 | 0.117 | 17 |
| mlp | random | leaky | 0.823 [0.821, 0.825] | 0.369 | 0.171 [0.166, 0.175] | 0.881 | 0.061 | 17 |
| mlp | random | +8y | 0.822 [0.820, 0.824] | 0.368 | 0.171 [0.166, 0.175] | 0.879 | 0.061 | 17 |
| mlp | random | zero | 0.758 [0.756, 0.760] | 0.322 | 0.171 [0.166, 0.175] | 0.782 | 0.062 | 17 |
| mlp | random | fixA | 0.820 [0.818, 0.822] | 0.353 | 0.169 [0.165, 0.173] | 0.879 | 0.062 | 17 |
| mlp | random | dropIAT | 0.822 [0.820, 0.824] | 0.366 | 0.172 [0.167, 0.176] | 0.880 | 0.065 | 17 |
| mlp | temporal | leaky | 0.809 [0.807, 0.811] | 0.312 | 0.148 [0.145, 0.150] | 0.878 | 0.058 | 17 |
| mlp | temporal | +8y | 0.806 [0.804, 0.808] | 0.309 | 0.148 [0.145, 0.150] | 0.874 | 0.058 | 17 |
| mlp | temporal | zero | 0.772 [0.770, 0.774] | 0.284 | 0.148 [0.145, 0.150] | 0.822 | 0.058 | 17 |
| mlp | temporal | fixA | 0.802 [0.801, 0.804] | 0.292 | 0.152 [0.149, 0.154] | 0.875 | 0.058 | 17 |
| mlp | temporal | dropIAT | 0.812 [0.810, 0.814] | 0.311 | 0.146 [0.143, 0.149] | 0.878 | 0.059 | 17 |
| knn | random | leaky | 0.841 [0.839, 0.843] | 0.517 | 0.386 [0.378, 0.394] | 0.921 | 0.597 | 17 |
| knn | random | +8y | 0.453 [0.451, 0.455] | 0.305 | 0.168 [0.163, 0.174] | 0.328 | 0.010 | 17 |
| knn | random | zero | 0.736 [0.734, 0.738] | 0.369 | 0.223 [0.217, 0.228] | 0.760 | 0.067 | 17 |
| knn | random | fixA | 0.658 [0.656, 0.660] | 0.376 | 0.235 [0.229, 0.241] | 0.641 | 0.116 | 17 |
| knn | random | dropIAT | 0.658 [0.656, 0.660] | 0.374 | 0.233 [0.227, 0.239] | 0.641 | 0.116 | 17 |
| knn | temporal | leaky | 0.654 [0.652, 0.657] | 0.335 | 0.231 [0.225, 0.236] | 0.656 | 0.263 | 17 |
| knn | temporal | +8y | 0.399 [0.397, 0.402] | 0.257 | 0.124 [0.121, 0.128] | 0.267 | 0.002 | 17 |
| knn | temporal | zero | 0.727 [0.725, 0.729] | 0.296 | 0.180 [0.176, 0.183] | 0.767 | 0.060 | 17 |
| knn | temporal | fixA | 0.643 [0.641, 0.646] | 0.301 | 0.188 [0.184, 0.192] | 0.639 | 0.100 | 17 |
| knn | temporal | dropIAT | 0.644 [0.642, 0.646] | 0.299 | 0.186 [0.183, 0.190] | 0.640 | 0.100 | 17 |

**gnb, random split, per class, all test rows** (recall / precision):

| class | support | leaky | +8y | zero | fixA | dropIAT |
|---|---:|---|---|---|---|---|
| Attack / Attack-Killall-v2 | 1,508 | 0.009 / 0.013 | 0.009 / 0.013 | 0.009 / 0.013 | 0.000 / 0.000 | 0.000 / 0.000 |
| Attack / Attack-Killer-TCP | 1,563 | 0.000 / 0.000 | 0.000 / 0.000 | 0.000 / 0.000 | 0.000 / 0.000 | 0.000 / 0.000 |
| Attack / Attack-TCP-BYPass-V1 | 34,592 | 0.957 / 0.446 | 0.957 / 0.446 | 0.000 / 0.000 | 0.000 / 0.000 | 0.000 / 0.000 |
| Attack / Attack-TCP-Control | 1,436 | 0.000 / 0.000 | 0.000 / 0.000 | 0.000 / 0.000 | 0.004 / 0.008 | 0.004 / 0.008 |
| Attack / Attack-TCP-Flag-ACK | 2,671 | 0.000 / 0.000 | 0.000 / 0.000 | 0.000 / 0.000 | 0.000 / 0.000 | 0.000 / 0.000 |
| Attack / Attack-TCP-Flag-ACK-PSH | 1,871 | 0.000 / 0.000 | 0.000 / 0.000 | 0.000 / 0.000 | 0.554 / 0.033 | 0.554 / 0.033 |
| Attack / Attack-TCP-Flag-MIX | 1,854 | 0.000 / 0.000 | 0.000 / 0.000 | 0.000 / 0.000 | 0.002 / 0.018 | 0.002 / 0.018 |
| Attack / Attack-TCP-Flag-OSYN | 217 | 0.000 / 0.000 | 0.000 / 0.000 | 0.000 / 0.000 | 0.000 / 0.000 | 0.000 / 0.000 |
| Attack / Attack-TCP-Flag-OSYNP | 222 | 0.000 / 0.000 | 0.000 / 0.000 | 0.000 / 0.000 | 0.000 / 0.000 | 0.000 / 0.000 |
| Attack / Attack-TCP-Flag-RST-ACK | 361 | 0.000 / 0.000 | 0.000 / 0.000 | 0.000 / 0.000 | 0.299 / 0.046 | 0.299 / 0.046 |
| Attack / Attack-TCP-Flag-SYN | 1,961 | 0.000 / 0.000 | 0.000 / 0.000 | 0.000 / 0.000 | 0.000 / 0.000 | 0.000 / 0.000 |
| Attack / Attack-TCP-Flag-SYN-ACK | 2,051 | 0.000 / 0.000 | 0.000 / 0.000 | 0.000 / 0.000 | 0.000 / 0.000 | 0.000 / 0.000 |
| Attack / Attack-TCP-Flag-SYN-TFO | 908 | 0.000 / 0.000 | 0.000 / 0.000 | 0.000 / 0.000 | 0.000 / 0.000 | 0.000 / 0.000 |
| Attack / Attack-TCP-Flag-SYN-TIME | 340 | 0.059 / 0.017 | 0.059 / 0.017 | 0.059 / 0.017 | 0.094 / 0.012 | 0.094 / 0.012 |
| Attack / Attack-TCP-IGMP | 1,813 | 0.000 / 0.000 | 0.000 / 0.000 | 0.000 / 0.000 | 0.000 / 0.000 | 0.000 / 0.000 |
| Attack / Attack-TCP-SYN | 1,738 | 0.000 / 0.000 | 0.000 / 0.000 | 0.000 / 0.000 | 0.000 / 0.000 | 0.000 / 0.000 |
| Attack / Attack-TCP-Valid-SYN | 2,011 | 0.800 / 0.032 | 0.800 / 0.032 | 0.959 / 0.019 | 0.000 / 0.000 | 0.000 / 0.000 |
| Benign / Benign | 75,571 | 0.000 / 0.091 | 0.000 / 0.077 | 0.000 / 0.000 | 0.000 / 0.000 | 0.000 / 0.000 |
| Benign / Benign-Email-Receive | 349 | 0.181 / 0.504 | 0.181 / 0.504 | 0.181 / 0.508 | 0.181 / 0.496 | 0.181 / 0.496 |
| Benign / Benign-Email-Send | 484 | 0.341 / 0.088 | 0.341 / 0.088 | 0.341 / 0.088 | 0.322 / 0.177 | 0.322 / 0.177 |
| Benign / Benign-FTP | 121 | 0.025 / 0.111 | 0.025 / 0.094 | 0.025 / 0.111 | 0.025 / 0.100 | 0.025 / 0.100 |
| Benign / Benign-SSH | 746 | 0.005 / 0.333 | 0.005 / 0.333 | 0.005 / 0.333 | 0.005 / 0.500 | 0.005 / 0.500 |
| Benign / Benign-Systemic | 12,019 | 0.016 / 0.328 | 0.016 / 0.330 | 0.016 / 0.324 | 0.000 / 0.090 | 0.000 / 0.088 |
| Benign / Benign-Telnet | 1,192 | 0.863 / 0.023 | 0.863 / 0.023 | 0.599 / 0.010 | 0.998 / 0.009 | 0.998 / 0.009 |
| Benign / Benign-Web_Browsing_HTTP-S | 12,818 | 0.011 / 0.645 | 0.011 / 0.651 | 0.011 / 0.645 | 0.011 / 0.689 | 0.011 / 0.690 |
| Suspicious / Suspicious | 14,777 | 0.000 / 0.000 | 0.000 / 0.000 | 0.000 / 0.000 | 0.000 / 0.000 | 0.000 / 0.000 |

**gnb, random split, per class, leaked test rows** (recall / precision):

| class | support | leaky | +8y | zero | fixA | dropIAT |
|---|---:|---|---|---|---|---|
| Attack / Attack-Killall-v2 | 349 | 0.000 / 0.000 | 0.000 / 0.000 | 0.000 / 0.000 | 0.000 / 0.000 | 0.000 / 0.000 |
| Attack / Attack-Killer-TCP | 465 | 0.000 / 0.000 | 0.000 / 0.000 | 0.000 / 0.000 | 0.000 / 0.000 | 0.000 / 0.000 |
| Attack / Attack-TCP-BYPass-V1 | 33,209 | 0.997 / 0.446 | 0.997 / 0.446 | 0.000 / 0.000 | 0.000 / 0.000 | 0.000 / 0.000 |
| Attack / Attack-TCP-Control | 413 | 0.000 / 0.000 | 0.000 / 0.000 | 0.000 / 0.000 | 0.000 / 0.000 | 0.000 / 0.000 |
| Attack / Attack-TCP-Flag-ACK | 450 | 0.000 / 0.000 | 0.000 / 0.000 | 0.000 / 0.000 | 0.000 / 0.000 | 0.000 / 0.000 |
| Attack / Attack-TCP-Flag-ACK-PSH | 439 | 0.000 / 0.000 | 0.000 / 0.000 | 0.000 / 0.000 | 0.000 / 0.000 | 0.000 / 0.000 |
| Attack / Attack-TCP-Flag-MIX | 413 | 0.000 / 0.000 | 0.000 / 0.000 | 0.000 / 0.000 | 0.000 / 0.000 | 0.000 / 0.000 |
| Attack / Attack-TCP-Flag-OSYN | 189 | 0.000 / 0.000 | 0.000 / 0.000 | 0.000 / 0.000 | 0.000 / 0.000 | 0.000 / 0.000 |
| Attack / Attack-TCP-Flag-OSYNP | 183 | 0.000 / 0.000 | 0.000 / 0.000 | 0.000 / 0.000 | 0.000 / 0.000 | 0.000 / 0.000 |
| Attack / Attack-TCP-Flag-RST-ACK | 140 | 0.000 / 0.000 | 0.000 / 0.000 | 0.000 / 0.000 | 0.000 / 0.000 | 0.000 / 0.000 |
| Attack / Attack-TCP-Flag-SYN | 427 | 0.000 / 0.000 | 0.000 / 0.000 | 0.000 / 0.000 | 0.000 / 0.000 | 0.000 / 0.000 |
| Attack / Attack-TCP-Flag-SYN-ACK | 367 | 0.000 / 0.000 | 0.000 / 0.000 | 0.000 / 0.000 | 0.000 / 0.000 | 0.000 / 0.000 |
| Attack / Attack-TCP-Flag-SYN-TFO | 198 | 0.000 / 0.000 | 0.000 / 0.000 | 0.000 / 0.000 | 0.000 / 0.000 | 0.000 / 0.000 |
| Attack / Attack-TCP-Flag-SYN-TIME | 235 | 0.000 / 0.000 | 0.000 / 0.000 | 0.000 / 0.000 | 0.000 / 0.000 | 0.000 / 0.000 |
| Attack / Attack-TCP-IGMP | 408 | 0.000 / 0.000 | 0.000 / 0.000 | 0.000 / 0.000 | 0.000 / 0.000 | 0.000 / 0.000 |
| Attack / Attack-TCP-SYN | 363 | 0.000 / 0.000 | 0.000 / 0.000 | 0.000 / 0.000 | 0.000 / 0.000 | 0.000 / 0.000 |
| Attack / Attack-TCP-Valid-SYN | 399 | 0.000 / 0.000 | 0.000 / 0.000 | 0.802 / 0.006 | 0.000 / 0.000 | 0.000 / 0.000 |
| Benign / Benign | 61,174 | 0.000 / 0.091 | 0.000 / 0.077 | 0.000 / 0.000 | 0.000 / 0.000 | 0.000 / 0.000 |
| Benign / Benign-Email-Receive | 236 | 0.000 / 0.000 | 0.000 / 0.000 | 0.000 / 0.000 | 0.000 / 0.000 | 0.000 / 0.000 |
| Benign / Benign-Email-Send | 285 | 0.000 / 0.000 | 0.000 / 0.000 | 0.000 / 0.000 | 0.000 / 0.000 | 0.000 / 0.000 |
| Benign / Benign-FTP | 72 | 0.000 / 0.000 | 0.000 / 0.000 | 0.000 / 0.000 | 0.000 / 0.000 | 0.000 / 0.000 |
| Benign / Benign-SSH | 377 | 0.000 / 0.000 | 0.000 / 0.000 | 0.000 / 0.000 | 0.000 / 0.000 | 0.000 / 0.000 |
| Benign / Benign-Systemic | 2,004 | 0.000 / 0.000 | 0.000 / 0.000 | 0.003 / 0.207 | 0.001 / 0.130 | 0.001 / 0.130 |
| Benign / Benign-Telnet | 992 | 0.883 / 0.022 | 0.883 / 0.022 | 0.566 / 0.009 | 1.000 / 0.009 | 1.000 / 0.009 |
| Benign / Benign-Web_Browsing_HTTP-S | 6,974 | 0.008 / 0.701 | 0.007 / 0.722 | 0.008 / 0.701 | 0.007 / 0.699 | 0.007 / 0.699 |
| Suspicious / Suspicious | 3,883 | 0.000 / 0.000 | 0.000 / 0.000 | 0.000 / 0.000 | 0.000 / 0.000 | 0.000 / 0.000 |

**gnb, temporal split, per class, all test rows** (recall / precision):

| class | support | leaky | +8y | zero | fixA | dropIAT |
|---|---:|---|---|---|---|---|
| Attack / Attack-Killall-v2 | 1,508 | 0.009 / 0.012 | 0.009 / 0.012 | 0.009 / 0.012 | 0.000 / 0.000 | 0.000 / 0.000 |
| Attack / Attack-Killer-TCP | 1,564 | 0.000 / 0.000 | 0.000 / 0.000 | 0.000 / 0.000 | 0.000 / 0.000 | 0.000 / 0.000 |
| Attack / Attack-TCP-BYPass-V1 | 34,592 | 0.954 / 0.446 | 0.954 / 0.446 | 0.000 / 0.000 | 0.000 / 0.000 | 0.000 / 0.000 |
| Attack / Attack-TCP-Control | 1,436 | 0.000 / 0.000 | 0.000 / 0.000 | 0.000 / 0.000 | 0.006 / 0.014 | 0.006 / 0.014 |
| Attack / Attack-TCP-Flag-ACK | 2,671 | 0.000 / 0.000 | 0.000 / 0.000 | 0.000 / 0.000 | 0.000 / 0.000 | 0.000 / 0.000 |
| Attack / Attack-TCP-Flag-ACK-PSH | 1,870 | 0.000 / 0.000 | 0.000 / 0.000 | 0.000 / 0.000 | 0.000 / 0.000 | 0.000 / 0.000 |
| Attack / Attack-TCP-Flag-MIX | 1,854 | 0.000 / 0.000 | 0.000 / 0.000 | 0.000 / 0.000 | 0.000 / 0.000 | 0.000 / 0.000 |
| Attack / Attack-TCP-Flag-OSYN | 217 | 0.000 / 0.000 | 0.000 / 0.000 | 0.000 / 0.000 | 0.000 / 0.000 | 0.000 / 0.000 |
| Attack / Attack-TCP-Flag-OSYNP | 222 | 0.000 / 0.000 | 0.000 / 0.000 | 0.000 / 0.000 | 0.000 / 0.000 | 0.000 / 0.000 |
| Attack / Attack-TCP-Flag-RST-ACK | 361 | 0.000 / 0.000 | 0.000 / 0.000 | 0.000 / 0.000 | 0.000 / 0.000 | 0.000 / 0.000 |
| Attack / Attack-TCP-Flag-SYN | 1,961 | 0.000 / 0.000 | 0.000 / 0.000 | 0.000 / 0.000 | 0.000 / 0.000 | 0.000 / 0.000 |
| Attack / Attack-TCP-Flag-SYN-ACK | 2,051 | 0.757 / 0.031 | 0.757 / 0.031 | 0.957 / 0.013 | 0.563 / 0.036 | 0.563 / 0.036 |
| Attack / Attack-TCP-Flag-SYN-TFO | 908 | 0.000 / 0.000 | 0.000 / 0.000 | 0.000 / 0.000 | 0.001 / 0.001 | 0.001 / 0.001 |
| Attack / Attack-TCP-Flag-SYN-TIME | 340 | 0.003 / 0.008 | 0.003 / 0.008 | 0.003 / 0.008 | 0.032 / 0.009 | 0.032 / 0.009 |
| Attack / Attack-TCP-IGMP | 1,813 | 0.000 / 0.000 | 0.000 / 0.000 | 0.000 / 0.000 | 0.000 / 0.000 | 0.000 / 0.000 |
| Attack / Attack-TCP-SYN | 1,738 | 0.000 / 0.000 | 0.000 / 0.000 | 0.000 / 0.000 | 0.000 / 0.000 | 0.000 / 0.000 |
| Attack / Attack-TCP-Valid-SYN | 2,011 | 0.000 / 0.000 | 0.000 / 0.000 | 0.000 / 0.000 | 0.000 / 0.000 | 0.000 / 0.000 |
| Benign / Benign | 75,571 | 0.000 / 0.000 | 0.000 / 0.000 | 0.000 / 0.000 | 0.000 / 0.000 | 0.000 / 0.000 |
| Benign / Benign-Email-Receive | 348 | 0.195 / 0.531 | 0.195 / 0.531 | 0.195 / 0.535 | 0.193 / 0.558 | 0.193 / 0.558 |
| Benign / Benign-Email-Send | 485 | 0.309 / 0.093 | 0.309 / 0.093 | 0.309 / 0.093 | 0.305 / 0.200 | 0.305 / 0.200 |
| Benign / Benign-FTP | 120 | 0.125 / 0.043 | 0.125 / 0.043 | 0.125 / 0.043 | 0.117 / 0.040 | 0.117 / 0.040 |
| Benign / Benign-SSH | 745 | 0.004 / 0.200 | 0.004 / 0.200 | 0.004 / 0.200 | 0.004 / 0.429 | 0.004 / 0.429 |
| Benign / Benign-Systemic | 12,019 | 0.007 / 0.151 | 0.007 / 0.152 | 0.007 / 0.146 | 0.001 / 0.160 | 0.001 / 0.160 |
| Benign / Benign-Telnet | 1,192 | 0.846 / 0.023 | 0.846 / 0.023 | 0.487 / 0.026 | 0.998 / 0.009 | 0.998 / 0.009 |
| Benign / Benign-Web_Browsing_HTTP-S | 12,818 | 0.025 / 0.892 | 0.025 / 0.895 | 0.025 / 0.883 | 0.026 / 0.889 | 0.028 / 0.895 |
| Suspicious / Suspicious | 14,776 | 0.000 / 0.000 | 0.000 / 0.000 | 0.000 / 0.000 | 0.000 / 0.016 | 0.000 / 0.016 |

**gnb, temporal split, per class, leaked test rows** (recall / precision):

| class | support | leaky | +8y | zero | fixA | dropIAT |
|---|---:|---|---|---|---|---|
| Attack / Attack-Killall-v2 | 342 | 0.000 / 0.000 | 0.000 / 0.000 | 0.000 / 0.000 | 0.000 / 0.000 | 0.000 / 0.000 |
| Attack / Attack-Killer-TCP | 373 | 0.000 / 0.000 | 0.000 / 0.000 | 0.000 / 0.000 | 0.000 / 0.000 | 0.000 / 0.000 |
| Attack / Attack-TCP-BYPass-V1 | 33,122 | 0.996 / 0.446 | 0.996 / 0.446 | 0.000 / 0.000 | 0.000 / 0.000 | 0.000 / 0.000 |
| Attack / Attack-TCP-Control | 341 | 0.000 / 0.000 | 0.000 / 0.000 | 0.000 / 0.000 | 0.000 / 0.000 | 0.000 / 0.000 |
| Attack / Attack-TCP-Flag-ACK | 374 | 0.000 / 0.000 | 0.000 / 0.000 | 0.000 / 0.000 | 0.000 / 0.000 | 0.000 / 0.000 |
| Attack / Attack-TCP-Flag-ACK-PSH | 406 | 0.000 / 0.000 | 0.000 / 0.000 | 0.000 / 0.000 | 0.000 / 0.000 | 0.000 / 0.000 |
| Attack / Attack-TCP-Flag-MIX | 321 | 0.000 / 0.000 | 0.000 / 0.000 | 0.000 / 0.000 | 0.000 / 0.000 | 0.000 / 0.000 |
| Attack / Attack-TCP-Flag-OSYN | 163 | 0.000 / 0.000 | 0.000 / 0.000 | 0.000 / 0.000 | 0.000 / 0.000 | 0.000 / 0.000 |
| Attack / Attack-TCP-Flag-OSYNP | 196 | 0.000 / 0.000 | 0.000 / 0.000 | 0.000 / 0.000 | 0.000 / 0.000 | 0.000 / 0.000 |
| Attack / Attack-TCP-Flag-RST-ACK | 60 | 0.000 / 0.000 | 0.000 / 0.000 | 0.000 / 0.000 | 0.000 / 0.000 | 0.000 / 0.000 |
| Attack / Attack-TCP-Flag-SYN | 498 | 0.000 / 0.000 | 0.000 / 0.000 | 0.000 / 0.000 | 0.000 / 0.000 | 0.000 / 0.000 |
| Attack / Attack-TCP-Flag-SYN-ACK | 494 | 0.002 / 0.083 | 0.000 / 0.000 | 0.830 / 0.004 | 0.002 / 0.059 | 0.002 / 0.059 |
| Attack / Attack-TCP-Flag-SYN-TFO | 184 | 0.000 / 0.000 | 0.000 / 0.000 | 0.000 / 0.000 | 0.000 / 0.000 | 0.000 / 0.000 |
| Attack / Attack-TCP-Flag-SYN-TIME | 183 | 0.000 / 0.000 | 0.000 / 0.000 | 0.000 / 0.000 | 0.000 / 0.000 | 0.000 / 0.000 |
| Attack / Attack-TCP-IGMP | 421 | 0.000 / 0.000 | 0.000 / 0.000 | 0.000 / 0.000 | 0.000 / 0.000 | 0.000 / 0.000 |
| Attack / Attack-TCP-SYN | 388 | 0.000 / 0.000 | 0.000 / 0.000 | 0.000 / 0.000 | 0.000 / 0.000 | 0.000 / 0.000 |
| Attack / Attack-TCP-Valid-SYN | 378 | 0.000 / 0.000 | 0.000 / 0.000 | 0.000 / 0.000 | 0.000 / 0.000 | 0.000 / 0.000 |
| Benign / Benign | 61,728 | 0.000 / 0.000 | 0.000 / 0.000 | 0.000 / 0.000 | 0.000 / 0.000 | 0.000 / 0.000 |
| Benign / Benign-Email-Receive | 236 | 0.000 / 0.000 | 0.000 / 0.000 | 0.000 / 0.000 | 0.000 / 0.000 | 0.000 / 0.000 |
| Benign / Benign-Email-Send | 293 | 0.000 / 0.000 | 0.000 / 0.000 | 0.000 / 0.000 | 0.000 / 0.000 | 0.000 / 0.000 |
| Benign / Benign-FTP | 78 | 0.000 / 0.000 | 0.000 / 0.000 | 0.000 / 0.000 | 0.000 / 0.000 | 0.000 / 0.000 |
| Benign / Benign-SSH | 344 | 0.000 / 0.000 | 0.000 / 0.000 | 0.000 / 0.000 | 0.000 / 0.000 | 0.000 / 0.000 |
| Benign / Benign-Systemic | 1,889 | 0.000 / 0.000 | 0.000 / 0.000 | 0.002 / 0.080 | 0.000 / 0.000 | 0.000 / 0.000 |
| Benign / Benign-Telnet | 1,010 | 0.887 / 0.022 | 0.887 / 0.022 | 0.463 / 0.026 | 1.000 / 0.009 | 1.000 / 0.009 |
| Benign / Benign-Web_Browsing_HTTP-S | 7,057 | 0.000 / 0.250 | 0.000 / 0.333 | 0.000 / 0.222 | 0.000 / 0.111 | 0.000 / 0.111 |
| Suspicious / Suspicious | 3,894 | 0.000 / 0.000 | 0.000 / 0.000 | 0.000 / 0.000 | 0.000 / 0.000 | 0.000 / 0.000 |

**dt, random split, per class, all test rows** (recall / precision):

| class | support | leaky | +8y | zero | fixA | dropIAT |
|---|---:|---|---|---|---|---|
| Attack / Attack-Killall-v2 | 1,508 | 0.387 / 0.180 | 0.174 / 0.101 | 0.176 / 0.101 | 0.323 / 0.060 | 0.312 / 0.062 |
| Attack / Attack-Killer-TCP | 1,563 | 0.451 / 0.200 | 0.177 / 0.099 | 0.178 / 0.096 | 0.166 / 0.084 | 0.177 / 0.088 |
| Attack / Attack-TCP-BYPass-V1 | 34,592 | 0.956 / 0.998 | 0.000 / 0.000 | 0.000 / 0.000 | 0.948 / 0.999 | 0.948 / 0.999 |
| Attack / Attack-TCP-Control | 1,436 | 0.478 / 0.291 | 0.208 / 0.184 | 0.209 / 0.183 | 0.217 / 0.159 | 0.213 / 0.153 |
| Attack / Attack-TCP-Flag-ACK | 2,671 | 0.411 / 0.464 | 0.251 / 0.392 | 0.251 / 0.397 | 0.244 / 0.378 | 0.256 / 0.366 |
| Attack / Attack-TCP-Flag-ACK-PSH | 1,871 | 0.392 / 0.273 | 0.165 / 0.152 | 0.165 / 0.152 | 0.175 / 0.141 | 0.185 / 0.143 |
| Attack / Attack-TCP-Flag-MIX | 1,854 | 0.408 / 0.318 | 0.197 / 0.212 | 0.197 / 0.210 | 0.204 / 0.181 | 0.207 / 0.195 |
| Attack / Attack-TCP-Flag-OSYN | 217 | 0.811 / 0.288 | 0.018 / 0.009 | 0.018 / 0.020 | 0.230 / 0.006 | 0.263 / 0.006 |
| Attack / Attack-TCP-Flag-OSYNP | 222 | 0.847 / 0.319 | 0.081 / 0.098 | 0.081 / 0.102 | 0.288 / 0.020 | 0.270 / 0.019 |
| Attack / Attack-TCP-Flag-RST-ACK | 361 | 0.831 / 0.501 | 0.490 / 0.550 | 0.490 / 0.602 | 0.524 / 0.102 | 0.510 / 0.097 |
| Attack / Attack-TCP-Flag-SYN | 1,961 | 0.348 / 0.312 | 0.146 / 0.188 | 0.146 / 0.188 | 0.143 / 0.158 | 0.142 / 0.152 |
| Attack / Attack-TCP-Flag-SYN-ACK | 2,051 | 0.345 / 0.287 | 0.177 / 0.192 | 0.177 / 0.192 | 0.178 / 0.178 | 0.183 / 0.182 |
| Attack / Attack-TCP-Flag-SYN-TFO | 908 | 0.852 / 0.621 | 0.669 / 0.638 | 0.669 / 0.720 | 0.672 / 0.559 | 0.672 / 0.560 |
| Attack / Attack-TCP-Flag-SYN-TIME | 340 | 0.771 / 0.282 | 0.126 / 0.006 | 0.132 / 0.100 | 0.218 / 0.048 | 0.191 / 0.042 |
| Attack / Attack-TCP-IGMP | 1,813 | 0.321 / 0.241 | 0.119 / 0.124 | 0.119 / 0.121 | 0.146 / 0.125 | 0.141 / 0.123 |
| Attack / Attack-TCP-SYN | 1,738 | 0.388 / 0.309 | 0.194 / 0.217 | 0.194 / 0.215 | 0.197 / 0.192 | 0.206 / 0.199 |
| Attack / Attack-TCP-Valid-SYN | 2,011 | 0.501 / 0.255 | 0.310 / 0.189 | 0.310 / 0.189 | 0.279 / 0.279 | 0.278 / 0.248 |
| Benign / Benign | 75,571 | 0.751 / 0.974 | 0.349 / 0.956 | 0.721 / 0.927 | 0.673 / 0.937 | 0.671 / 0.937 |
| Benign / Benign-Email-Receive | 349 | 0.499 / 0.038 | 0.418 / 0.093 | 0.347 / 0.070 | 0.438 / 0.069 | 0.438 / 0.068 |
| Benign / Benign-Email-Send | 484 | 0.719 / 0.106 | 0.690 / 0.180 | 0.541 / 0.058 | 0.709 / 0.159 | 0.707 / 0.152 |
| Benign / Benign-FTP | 121 | 0.669 / 0.093 | 0.322 / 0.007 | 0.471 / 0.002 | 0.587 / 0.045 | 0.587 / 0.045 |
| Benign / Benign-SSH | 746 | 0.818 / 0.342 | 0.479 / 0.144 | 0.764 / 0.203 | 0.772 / 0.405 | 0.773 / 0.411 |
| Benign / Benign-Systemic | 12,019 | 0.859 / 0.869 | 0.803 / 0.793 | 0.801 / 0.629 | 0.844 / 0.874 | 0.845 / 0.877 |
| Benign / Benign-Telnet | 1,192 | 0.805 / 0.161 | 0.334 / 0.448 | 0.805 / 0.102 | 0.811 / 0.114 | 0.809 / 0.114 |
| Benign / Benign-Web_Browsing_HTTP-S | 12,818 | 0.782 / 0.904 | 0.675 / 0.862 | 0.789 / 0.684 | 0.668 / 0.933 | 0.667 / 0.933 |
| Suspicious / Suspicious | 14,777 | 0.597 / 0.828 | 0.579 / 0.105 | 0.377 / 0.971 | 0.380 / 0.949 | 0.383 / 0.948 |

**dt, random split, per class, leaked test rows** (recall / precision):

| class | support | leaky | +8y | zero | fixA | dropIAT |
|---|---:|---|---|---|---|---|
| Attack / Attack-Killall-v2 | 349 | 0.917 / 0.493 | 0.000 / 0.000 | 0.009 / 0.068 | 0.450 / 0.036 | 0.453 / 0.036 |
| Attack / Attack-Killer-TCP | 465 | 0.920 / 0.594 | 0.000 / 0.000 | 0.002 / 0.010 | 0.024 / 0.018 | 0.026 / 0.019 |
| Attack / Attack-TCP-BYPass-V1 | 33,209 | 0.996 / 0.998 | 0.000 / 0.000 | 0.000 / 0.000 | 0.988 / 0.999 | 0.988 / 0.999 |
| Attack / Attack-TCP-Control | 413 | 0.942 / 0.524 | 0.002 / 0.111 | 0.005 / 0.095 | 0.027 / 0.038 | 0.031 / 0.043 |
| Attack / Attack-TCP-Flag-ACK | 450 | 0.951 / 0.632 | 0.000 / 0.000 | 0.000 / 0.000 | 0.002 / 0.010 | 0.002 / 0.010 |
| Attack / Attack-TCP-Flag-ACK-PSH | 439 | 0.968 / 0.638 | 0.000 / 0.000 | 0.000 / 0.000 | 0.002 / 0.009 | 0.005 / 0.019 |
| Attack / Attack-TCP-Flag-MIX | 413 | 0.949 / 0.590 | 0.000 / 0.000 | 0.000 / 0.000 | 0.005 / 0.010 | 0.005 / 0.010 |
| Attack / Attack-TCP-Flag-OSYN | 189 | 0.910 / 0.390 | 0.000 / 0.000 | 0.000 / 0.000 | 0.228 / 0.005 | 0.249 / 0.005 |
| Attack / Attack-TCP-Flag-OSYNP | 183 | 0.929 / 0.410 | 0.000 / 0.000 | 0.000 / 0.000 | 0.262 / 0.016 | 0.246 / 0.015 |
| Attack / Attack-TCP-Flag-RST-ACK | 140 | 0.879 / 0.384 | 0.000 / 0.000 | 0.000 / 0.000 | 0.043 / 0.004 | 0.043 / 0.004 |
| Attack / Attack-TCP-Flag-SYN | 427 | 0.927 / 0.597 | 0.000 / 0.000 | 0.000 / 0.000 | 0.019 / 0.040 | 0.019 / 0.038 |
| Attack / Attack-TCP-Flag-SYN-ACK | 367 | 0.940 / 0.594 | 0.000 / 0.000 | 0.000 / 0.000 | 0.014 / 0.075 | 0.014 / 0.067 |
| Attack / Attack-TCP-Flag-SYN-TFO | 198 | 0.843 / 0.410 | 0.000 / 0.000 | 0.000 / 0.000 | 0.010 / 0.008 | 0.015 / 0.012 |
| Attack / Attack-TCP-Flag-SYN-TIME | 235 | 0.932 / 0.409 | 0.000 / 0.000 | 0.009 / 0.036 | 0.111 / 0.023 | 0.111 / 0.024 |
| Attack / Attack-TCP-IGMP | 408 | 0.900 / 0.541 | 0.000 / 0.000 | 0.000 / 0.000 | 0.049 / 0.081 | 0.047 / 0.082 |
| Attack / Attack-TCP-SYN | 363 | 0.928 / 0.535 | 0.000 / 0.000 | 0.000 / 0.000 | 0.022 / 0.039 | 0.022 / 0.041 |
| Attack / Attack-TCP-Valid-SYN | 399 | 0.962 / 0.587 | 0.000 / 0.000 | 0.000 / 0.000 | 0.000 / 0.000 | 0.000 / 0.000 |
| Benign / Benign | 61,174 | 0.730 / 0.973 | 0.234 / 0.939 | 0.693 / 0.913 | 0.630 / 0.925 | 0.630 / 0.925 |
| Benign / Benign-Email-Receive | 236 | 0.415 / 0.027 | 0.297 / 0.106 | 0.191 / 0.055 | 0.331 / 0.056 | 0.331 / 0.057 |
| Benign / Benign-Email-Send | 285 | 0.642 / 0.073 | 0.593 / 0.154 | 0.340 / 0.026 | 0.628 / 0.119 | 0.628 / 0.118 |
| Benign / Benign-FTP | 72 | 0.611 / 0.063 | 0.028 / 0.000 | 0.278 / 0.001 | 0.431 / 0.022 | 0.431 / 0.022 |
| Benign / Benign-SSH | 377 | 0.772 / 0.272 | 0.101 / 0.022 | 0.666 / 0.120 | 0.676 / 0.346 | 0.668 / 0.362 |
| Benign / Benign-Systemic | 2,004 | 0.457 / 0.450 | 0.125 / 0.107 | 0.111 / 0.041 | 0.385 / 0.423 | 0.385 / 0.430 |
| Benign / Benign-Telnet | 992 | 0.809 / 0.145 | 0.244 / 0.531 | 0.810 / 0.090 | 0.814 / 0.100 | 0.811 / 0.100 |
| Benign / Benign-Web_Browsing_HTTP-S | 6,974 | 0.722 / 0.872 | 0.525 / 0.777 | 0.734 / 0.541 | 0.519 / 0.918 | 0.518 / 0.914 |
| Suspicious / Suspicious | 3,883 | 0.835 / 0.660 | 0.769 / 0.040 | 0.000 / 0.000 | 0.011 / 0.240 | 0.012 / 0.251 |

**dt, temporal split, per class, all test rows** (recall / precision):

| class | support | leaky | +8y | zero | fixA | dropIAT |
|---|---:|---|---|---|---|---|
| Attack / Attack-Killall-v2 | 1,508 | 0.219 / 0.081 | 0.219 / 0.082 | 0.219 / 0.082 | 0.314 / 0.059 | 0.284 / 0.058 |
| Attack / Attack-Killer-TCP | 1,564 | 0.176 / 0.149 | 0.168 / 0.148 | 0.169 / 0.137 | 0.152 / 0.098 | 0.169 / 0.097 |
| Attack / Attack-TCP-BYPass-V1 | 34,592 | 0.953 / 0.997 | 0.000 / 0.000 | 0.000 / 0.000 | 0.943 / 0.999 | 0.943 / 0.999 |
| Attack / Attack-TCP-Control | 1,436 | 0.246 / 0.234 | 0.201 / 0.205 | 0.201 / 0.197 | 0.207 / 0.158 | 0.199 / 0.151 |
| Attack / Attack-TCP-Flag-ACK | 2,671 | 0.262 / 0.296 | 0.237 / 0.379 | 0.237 / 0.379 | 0.231 / 0.359 | 0.204 / 0.362 |
| Attack / Attack-TCP-Flag-ACK-PSH | 1,870 | 0.314 / 0.096 | 0.166 / 0.087 | 0.166 / 0.087 | 0.166 / 0.085 | 0.170 / 0.083 |
| Attack / Attack-TCP-Flag-MIX | 1,854 | 0.269 / 0.147 | 0.266 / 0.166 | 0.266 / 0.166 | 0.268 / 0.147 | 0.285 / 0.155 |
| Attack / Attack-TCP-Flag-OSYN | 217 | 0.143 / 0.111 | 0.037 / 0.009 | 0.046 / 0.015 | 0.152 / 0.003 | 0.166 / 0.003 |
| Attack / Attack-TCP-Flag-OSYNP | 222 | 0.086 / 0.099 | 0.068 / 0.000 | 0.063 / 0.093 | 0.248 / 0.006 | 0.216 / 0.005 |
| Attack / Attack-TCP-Flag-RST-ACK | 361 | 0.305 / 0.431 | 0.299 / 0.387 | 0.299 / 0.500 | 0.305 / 0.062 | 0.241 / 0.050 |
| Attack / Attack-TCP-Flag-SYN | 1,961 | 0.118 / 0.081 | 0.093 / 0.090 | 0.093 / 0.091 | 0.101 / 0.085 | 0.105 / 0.091 |
| Attack / Attack-TCP-Flag-SYN-ACK | 2,051 | 0.343 / 0.199 | 0.163 / 0.155 | 0.163 / 0.156 | 0.153 / 0.150 | 0.152 / 0.151 |
| Attack / Attack-TCP-Flag-SYN-TFO | 908 | 0.765 / 0.574 | 0.753 / 0.602 | 0.752 / 0.628 | 0.756 / 0.471 | 0.733 / 0.456 |
| Attack / Attack-TCP-Flag-SYN-TIME | 340 | 0.253 / 0.213 | 0.053 / 0.003 | 0.047 / 0.062 | 0.091 / 0.014 | 0.097 / 0.015 |
| Attack / Attack-TCP-IGMP | 1,813 | 0.109 / 0.159 | 0.084 / 0.132 | 0.084 / 0.130 | 0.101 / 0.106 | 0.108 / 0.115 |
| Attack / Attack-TCP-SYN | 1,738 | 0.091 / 0.147 | 0.068 / 0.121 | 0.068 / 0.118 | 0.089 / 0.108 | 0.071 / 0.099 |
| Attack / Attack-TCP-Valid-SYN | 2,011 | 0.315 / 0.285 | 0.295 / 0.306 | 0.295 / 0.306 | 0.297 / 0.294 | 0.298 / 0.249 |
| Benign / Benign | 75,571 | 0.380 / 0.912 | 0.314 / 0.975 | 0.643 / 0.906 | 0.559 / 0.961 | 0.557 / 0.961 |
| Benign / Benign-Email-Receive | 348 | 0.379 / 0.112 | 0.382 / 0.141 | 0.241 / 0.047 | 0.422 / 0.075 | 0.422 / 0.073 |
| Benign / Benign-Email-Send | 485 | 0.586 / 0.177 | 0.623 / 0.193 | 0.522 / 0.017 | 0.625 / 0.154 | 0.625 / 0.144 |
| Benign / Benign-FTP | 120 | 0.525 / 0.148 | 0.250 / 0.112 | 0.433 / 0.056 | 0.550 / 0.040 | 0.550 / 0.040 |
| Benign / Benign-SSH | 745 | 0.420 / 0.251 | 0.369 / 0.345 | 0.486 / 0.057 | 0.344 / 0.264 | 0.379 / 0.290 |
| Benign / Benign-Systemic | 12,019 | 0.902 / 0.258 | 0.815 / 0.836 | 0.813 / 0.825 | 0.871 / 0.863 | 0.872 / 0.863 |
| Benign / Benign-Telnet | 1,192 | 0.548 / 0.139 | 0.192 / 0.454 | 0.643 / 0.019 | 0.858 / 0.129 | 0.862 / 0.130 |
| Benign / Benign-Web_Browsing_HTTP-S | 12,818 | 0.513 / 0.838 | 0.379 / 0.935 | 0.777 / 0.677 | 0.616 / 0.943 | 0.616 / 0.940 |
| Suspicious / Suspicious | 14,776 | 0.558 / 0.432 | 0.562 / 0.129 | 0.303 / 0.919 | 0.305 / 0.866 | 0.313 / 0.871 |

**dt, temporal split, per class, leaked test rows** (recall / precision):

| class | support | leaky | +8y | zero | fixA | dropIAT |
|---|---:|---|---|---|---|---|
| Attack / Attack-Killall-v2 | 342 | 0.003 / 0.013 | 0.000 / 0.000 | 0.000 / 0.000 | 0.485 / 0.039 | 0.485 / 0.039 |
| Attack / Attack-Killer-TCP | 373 | 0.032 / 0.167 | 0.000 / 0.000 | 0.005 / 0.012 | 0.011 / 0.005 | 0.011 / 0.005 |
| Attack / Attack-TCP-BYPass-V1 | 33,122 | 0.995 / 0.997 | 0.000 / 0.000 | 0.000 / 0.000 | 0.985 / 0.999 | 0.985 / 0.999 |
| Attack / Attack-TCP-Control | 341 | 0.191 / 0.613 | 0.000 / 0.000 | 0.000 / 0.000 | 0.021 / 0.021 | 0.018 / 0.018 |
| Attack / Attack-TCP-Flag-ACK | 374 | 0.179 / 0.096 | 0.000 / 0.000 | 0.000 / 0.000 | 0.000 / 0.000 | 0.000 / 0.000 |
| Attack / Attack-TCP-Flag-ACK-PSH | 406 | 0.682 / 0.110 | 0.000 / 0.000 | 0.000 / 0.000 | 0.010 / 0.025 | 0.010 / 0.027 |
| Attack / Attack-TCP-Flag-MIX | 321 | 0.012 / 0.010 | 0.000 / 0.000 | 0.000 / 0.000 | 0.006 / 0.006 | 0.006 / 0.006 |
| Attack / Attack-TCP-Flag-OSYN | 163 | 0.141 / 0.139 | 0.000 / 0.000 | 0.012 / 0.003 | 0.160 / 0.002 | 0.160 / 0.002 |
| Attack / Attack-TCP-Flag-OSYNP | 196 | 0.026 / 0.086 | 0.005 / 0.000 | 0.000 / 0.000 | 0.209 / 0.004 | 0.179 / 0.004 |
| Attack / Attack-TCP-Flag-RST-ACK | 60 | 0.033 / 0.051 | 0.000 / 0.000 | 0.000 / 0.000 | 0.050 / 0.002 | 0.050 / 0.002 |
| Attack / Attack-TCP-Flag-SYN | 498 | 0.098 / 0.058 | 0.000 / 0.000 | 0.000 / 0.000 | 0.006 / 0.013 | 0.004 / 0.008 |
| Attack / Attack-TCP-Flag-SYN-ACK | 494 | 0.749 / 0.264 | 0.000 / 0.000 | 0.000 / 0.000 | 0.000 / 0.000 | 0.000 / 0.000 |
| Attack / Attack-TCP-Flag-SYN-TFO | 184 | 0.065 / 0.085 | 0.005 / 0.014 | 0.000 / 0.000 | 0.022 / 0.010 | 0.027 / 0.012 |
| Attack / Attack-TCP-Flag-SYN-TIME | 183 | 0.383 / 0.438 | 0.011 / 0.000 | 0.000 / 0.000 | 0.027 / 0.003 | 0.027 / 0.003 |
| Attack / Attack-TCP-IGMP | 421 | 0.105 / 0.512 | 0.000 / 0.000 | 0.000 / 0.000 | 0.012 / 0.023 | 0.012 / 0.023 |
| Attack / Attack-TCP-SYN | 388 | 0.106 / 0.363 | 0.000 / 0.000 | 0.000 / 0.000 | 0.005 / 0.007 | 0.005 / 0.007 |
| Attack / Attack-TCP-Valid-SYN | 378 | 0.106 / 0.141 | 0.000 / 0.000 | 0.000 / 0.000 | 0.003 / 0.007 | 0.003 / 0.008 |
| Benign / Benign | 61,728 | 0.273 / 0.872 | 0.192 / 0.976 | 0.594 / 0.886 | 0.491 / 0.956 | 0.491 / 0.956 |
| Benign / Benign-Email-Receive | 236 | 0.258 / 0.156 | 0.263 / 0.385 | 0.055 / 0.013 | 0.297 / 0.060 | 0.301 / 0.061 |
| Benign / Benign-Email-Send | 293 | 0.457 / 0.156 | 0.519 / 0.185 | 0.352 / 0.007 | 0.529 / 0.116 | 0.529 / 0.113 |
| Benign / Benign-FTP | 78 | 0.436 / 0.166 | 0.013 / 0.021 | 0.295 / 0.032 | 0.513 / 0.027 | 0.513 / 0.027 |
| Benign / Benign-SSH | 344 | 0.142 / 0.077 | 0.032 / 0.059 | 0.285 / 0.017 | 0.154 / 0.110 | 0.145 / 0.104 |
| Benign / Benign-Systemic | 1,889 | 0.610 / 0.036 | 0.056 / 0.074 | 0.044 / 0.053 | 0.403 / 0.423 | 0.401 / 0.431 |
| Benign / Benign-Telnet | 1,010 | 0.495 / 0.115 | 0.075 / 0.475 | 0.607 / 0.015 | 0.859 / 0.115 | 0.863 / 0.116 |
| Benign / Benign-Web_Browsing_HTTP-S | 7,057 | 0.266 / 0.654 | 0.023 / 0.714 | 0.745 / 0.540 | 0.468 / 0.928 | 0.469 / 0.925 |
| Suspicious / Suspicious | 3,894 | 0.969 / 0.266 | 0.982 / 0.064 | 0.000 / 0.000 | 0.005 / 0.072 | 0.004 / 0.066 |

**lr, random split, per class, all test rows** (recall / precision):

| class | support | leaky | +8y | zero | fixA |
|---|---:|---|---|---|---|
| Attack / Attack-Killall-v2 | 1,508 | 0.340 / 0.079 | 0.340 / 0.079 | 0.338 / 0.079 | 0.324 / 0.077 |
| Attack / Attack-Killer-TCP | 1,563 | 0.316 / 0.091 | 0.434 / 0.071 | 0.316 / 0.091 | 0.337 / 0.091 |
| Attack / Attack-TCP-BYPass-V1 | 34,592 | 0.948 / 0.990 | 0.948 / 0.990 | 0.948 / 0.996 | 0.948 / 0.989 |
| Attack / Attack-TCP-Control | 1,436 | 0.178 / 0.217 | 0.178 / 0.217 | 0.177 / 0.218 | 0.182 / 0.205 |
| Attack / Attack-TCP-Flag-ACK | 2,671 | 0.003 / 0.055 | 0.003 / 0.055 | 0.003 / 0.055 | 0.004 / 0.062 |
| Attack / Attack-TCP-Flag-ACK-PSH | 1,871 | 0.122 / 0.103 | 0.138 / 0.021 | 0.122 / 0.102 | 0.108 / 0.105 |
| Attack / Attack-TCP-Flag-MIX | 1,854 | 0.138 / 0.194 | 0.138 / 0.194 | 0.138 / 0.197 | 0.134 / 0.199 |
| Attack / Attack-TCP-Flag-OSYN | 217 | 0.207 / 0.006 | 0.074 / 0.012 | 0.138 / 0.006 | 0.207 / 0.006 |
| Attack / Attack-TCP-Flag-OSYNP | 222 | 0.329 / 0.011 | 0.342 / 0.007 | 0.072 / 0.052 | 0.333 / 0.010 |
| Attack / Attack-TCP-Flag-RST-ACK | 361 | 0.335 / 0.432 | 0.424 / 0.019 | 0.335 / 0.453 | 0.330 / 0.465 |
| Attack / Attack-TCP-Flag-SYN | 1,961 | 0.066 / 0.188 | 0.068 / 0.191 | 0.066 / 0.190 | 0.070 / 0.190 |
| Attack / Attack-TCP-Flag-SYN-ACK | 2,051 | 0.050 / 0.204 | 0.050 / 0.204 | 0.050 / 0.197 | 0.049 / 0.212 |
| Attack / Attack-TCP-Flag-SYN-TFO | 908 | 0.739 / 0.144 | 0.741 / 0.144 | 0.747 / 0.124 | 0.740 / 0.145 |
| Attack / Attack-TCP-Flag-SYN-TIME | 340 | 0.279 / 0.006 | 0.159 / 0.066 | 0.318 / 0.006 | 0.294 / 0.007 |
| Attack / Attack-TCP-IGMP | 1,813 | 0.063 / 0.154 | 0.063 / 0.154 | 0.055 / 0.159 | 0.061 / 0.147 |
| Attack / Attack-TCP-SYN | 1,738 | 0.071 / 0.104 | 0.071 / 0.104 | 0.184 / 0.021 | 0.068 / 0.100 |
| Attack / Attack-TCP-Valid-SYN | 2,011 | 0.209 / 0.153 | 0.209 / 0.153 | 0.209 / 0.153 | 0.209 / 0.151 |
| Benign / Benign | 75,571 | 0.593 / 0.941 | 0.466 / 0.958 | 0.191 / 0.973 | 0.593 / 0.941 |
| Benign / Benign-Email-Receive | 349 | 0.278 / 0.451 | 0.327 / 0.047 | 0.284 / 0.054 | 0.281 / 0.394 |
| Benign / Benign-Email-Send | 484 | 0.531 / 0.537 | 0.531 / 0.530 | 0.486 / 0.614 | 0.533 / 0.545 |
| Benign / Benign-FTP | 121 | 0.554 / 0.056 | 0.512 / 0.011 | 0.521 / 0.148 | 0.570 / 0.053 |
| Benign / Benign-SSH | 746 | 0.761 / 0.485 | 0.765 / 0.514 | 0.751 / 0.418 | 0.759 / 0.503 |
| Benign / Benign-Systemic | 12,019 | 0.796 / 0.846 | 0.794 / 0.848 | 0.758 / 0.881 | 0.797 / 0.847 |
| Benign / Benign-Telnet | 1,192 | 0.718 / 0.069 | 0.680 / 0.078 | 0.851 / 0.028 | 0.720 / 0.069 |
| Benign / Benign-Web_Browsing_HTTP-S | 12,818 | 0.651 / 0.934 | 0.696 / 0.919 | 0.670 / 0.885 | 0.646 / 0.937 |
| Suspicious / Suspicious | 14,777 | 0.077 / 0.813 | 0.077 / 0.798 | 0.076 / 0.817 | 0.078 / 0.815 |

**lr, random split, per class, leaked test rows** (recall / precision):

| class | support | leaky | +8y | zero | fixA |
|---|---:|---|---|---|---|
| Attack / Attack-Killall-v2 | 349 | 0.006 / 0.077 | 0.006 / 0.065 | 0.000 / 0.000 | 0.006 / 0.077 |
| Attack / Attack-Killer-TCP | 465 | 0.000 / 0.000 | 0.396 / 0.044 | 0.000 / 0.000 | 0.000 / 0.000 |
| Attack / Attack-TCP-BYPass-V1 | 33,209 | 0.988 / 0.992 | 0.988 / 0.992 | 0.988 / 0.999 | 0.988 / 0.992 |
| Attack / Attack-TCP-Control | 413 | 0.002 / 0.077 | 0.005 / 0.125 | 0.000 / 0.000 | 0.002 / 0.077 |
| Attack / Attack-TCP-Flag-ACK | 450 | 0.000 / 0.000 | 0.000 / 0.000 | 0.000 / 0.000 | 0.000 / 0.000 |
| Attack / Attack-TCP-Flag-ACK-PSH | 439 | 0.000 / 0.000 | 0.068 / 0.003 | 0.000 / 0.000 | 0.000 / 0.000 |
| Attack / Attack-TCP-Flag-MIX | 413 | 0.000 / 0.000 | 0.000 / 0.000 | 0.000 / 0.000 | 0.000 / 0.000 |
| Attack / Attack-TCP-Flag-OSYN | 189 | 0.206 / 0.005 | 0.053 / 0.010 | 0.127 / 0.005 | 0.201 / 0.005 |
| Attack / Attack-TCP-Flag-OSYNP | 183 | 0.311 / 0.009 | 0.328 / 0.006 | 0.000 / 0.000 | 0.322 / 0.009 |
| Attack / Attack-TCP-Flag-RST-ACK | 140 | 0.000 / 0.000 | 0.229 / 0.004 | 0.000 / 0.000 | 0.000 / 0.000 |
| Attack / Attack-TCP-Flag-SYN | 427 | 0.000 / 0.000 | 0.007 / 0.273 | 0.000 / 0.000 | 0.005 / 0.182 |
| Attack / Attack-TCP-Flag-SYN-ACK | 367 | 0.000 / 0.000 | 0.000 / 0.000 | 0.000 / 0.000 | 0.000 / 0.000 |
| Attack / Attack-TCP-Flag-SYN-TFO | 198 | 0.005 / 0.042 | 0.015 / 0.086 | 0.040 / 0.010 | 0.005 / 0.056 |
| Attack / Attack-TCP-Flag-SYN-TIME | 235 | 0.247 / 0.004 | 0.072 / 0.136 | 0.302 / 0.004 | 0.243 / 0.004 |
| Attack / Attack-TCP-IGMP | 408 | 0.037 / 0.125 | 0.037 / 0.126 | 0.000 / 0.000 | 0.034 / 0.107 |
| Attack / Attack-TCP-SYN | 363 | 0.000 / 0.000 | 0.000 / 0.000 | 0.537 / 0.014 | 0.000 / 0.000 |
| Attack / Attack-TCP-Valid-SYN | 399 | 0.000 / 0.000 | 0.000 / 0.000 | 0.000 / 0.000 | 0.000 / 0.000 |
| Benign / Benign | 61,174 | 0.519 / 0.927 | 0.361 / 0.947 | 0.021 / 0.938 | 0.518 / 0.928 |
| Benign / Benign-Email-Receive | 236 | 0.106 / 0.198 | 0.178 / 0.018 | 0.114 / 0.016 | 0.106 / 0.195 |
| Benign / Benign-Email-Send | 285 | 0.319 / 0.338 | 0.319 / 0.331 | 0.242 / 0.399 | 0.319 / 0.351 |
| Benign / Benign-FTP | 72 | 0.375 / 0.027 | 0.306 / 0.004 | 0.319 / 0.107 | 0.375 / 0.025 |
| Benign / Benign-SSH | 377 | 0.642 / 0.514 | 0.650 / 0.598 | 0.621 / 0.366 | 0.645 / 0.539 |
| Benign / Benign-Systemic | 2,004 | 0.303 / 0.461 | 0.288 / 0.458 | 0.073 / 0.421 | 0.308 / 0.464 |
| Benign / Benign-Telnet | 992 | 0.718 / 0.062 | 0.672 / 0.071 | 0.877 / 0.025 | 0.718 / 0.062 |
| Benign / Benign-Web_Browsing_HTTP-S | 6,974 | 0.536 / 0.914 | 0.619 / 0.887 | 0.572 / 0.820 | 0.526 / 0.915 |
| Suspicious / Suspicious | 3,883 | 0.002 / 0.231 | 0.004 / 0.234 | 0.000 / 0.000 | 0.001 / 0.208 |

**lr, temporal split, per class, all test rows** (recall / precision):

| class | support | leaky | +8y | zero | fixA |
|---|---:|---|---|---|---|
| Attack / Attack-Killall-v2 | 1,508 | 0.298 / 0.074 | 0.298 / 0.074 | 0.298 / 0.074 | 0.294 / 0.069 |
| Attack / Attack-Killer-TCP | 1,564 | 0.471 / 0.044 | 0.354 / 0.102 | 0.354 / 0.102 | 0.476 / 0.044 |
| Attack / Attack-TCP-BYPass-V1 | 34,592 | 0.943 / 0.990 | 0.943 / 0.990 | 0.943 / 0.996 | 0.943 / 0.990 |
| Attack / Attack-TCP-Control | 1,436 | 0.136 / 0.216 | 0.136 / 0.217 | 0.135 / 0.217 | 0.135 / 0.208 |
| Attack / Attack-TCP-Flag-ACK | 2,671 | 0.003 / 0.075 | 0.003 / 0.075 | 0.003 / 0.074 | 0.003 / 0.085 |
| Attack / Attack-TCP-Flag-ACK-PSH | 1,870 | 0.102 / 0.067 | 0.102 / 0.067 | 0.102 / 0.067 | 0.091 / 0.070 |
| Attack / Attack-TCP-Flag-MIX | 1,854 | 0.256 / 0.140 | 0.256 / 0.139 | 0.256 / 0.140 | 0.258 / 0.141 |
| Attack / Attack-TCP-Flag-OSYN | 217 | 0.203 / 0.006 | 0.088 / 0.003 | 0.055 / 0.037 | 0.194 / 0.005 |
| Attack / Attack-TCP-Flag-OSYNP | 222 | 0.239 / 0.004 | 0.252 / 0.002 | 0.068 / 0.037 | 0.243 / 0.004 |
| Attack / Attack-TCP-Flag-RST-ACK | 361 | 0.003 / 0.007 | 0.050 / 0.002 | 0.003 / 0.008 | 0.000 / 0.000 |
| Attack / Attack-TCP-Flag-SYN | 1,961 | 0.019 / 0.063 | 0.019 / 0.063 | 0.198 / 0.010 | 0.020 / 0.072 |
| Attack / Attack-TCP-Flag-SYN-ACK | 2,051 | 0.047 / 0.238 | 0.047 / 0.238 | 0.047 / 0.238 | 0.040 / 0.225 |
| Attack / Attack-TCP-Flag-SYN-TFO | 908 | 0.765 / 0.240 | 0.767 / 0.239 | 0.767 / 0.183 | 0.764 / 0.240 |
| Attack / Attack-TCP-Flag-SYN-TIME | 340 | 0.079 / 0.021 | 0.074 / 0.047 | 0.074 / 0.051 | 0.100 / 0.025 |
| Attack / Attack-TCP-IGMP | 1,813 | 0.017 / 0.109 | 0.016 / 0.105 | 0.013 / 0.114 | 0.022 / 0.131 |
| Attack / Attack-TCP-SYN | 1,738 | 0.012 / 0.027 | 0.012 / 0.028 | 0.012 / 0.027 | 0.012 / 0.028 |
| Attack / Attack-TCP-Valid-SYN | 2,011 | 0.221 / 0.125 | 0.221 / 0.125 | 0.221 / 0.125 | 0.215 / 0.128 |
| Benign / Benign | 75,571 | 0.545 / 0.955 | 0.372 / 0.963 | 0.183 / 0.971 | 0.543 / 0.955 |
| Benign / Benign-Email-Receive | 348 | 0.284 / 0.254 | 0.305 / 0.051 | 0.316 / 0.052 | 0.287 / 0.231 |
| Benign / Benign-Email-Send | 485 | 0.474 / 0.524 | 0.474 / 0.549 | 0.458 / 0.301 | 0.476 / 0.504 |
| Benign / Benign-FTP | 120 | 0.433 / 0.013 | 0.433 / 0.040 | 0.425 / 0.106 | 0.425 / 0.013 |
| Benign / Benign-SSH | 745 | 0.395 / 0.416 | 0.395 / 0.404 | 0.389 / 0.339 | 0.388 / 0.428 |
| Benign / Benign-Systemic | 12,019 | 0.835 / 0.793 | 0.833 / 0.792 | 0.787 / 0.805 | 0.834 / 0.792 |
| Benign / Benign-Telnet | 1,192 | 0.727 / 0.077 | 0.648 / 0.083 | 0.788 / 0.026 | 0.729 / 0.076 |
| Benign / Benign-Web_Browsing_HTTP-S | 12,818 | 0.600 / 0.936 | 0.608 / 0.938 | 0.619 / 0.873 | 0.600 / 0.938 |
| Suspicious / Suspicious | 14,776 | 0.063 / 0.698 | 0.063 / 0.697 | 0.063 / 0.695 | 0.066 / 0.708 |

**lr, temporal split, per class, leaked test rows** (recall / precision):

| class | support | leaky | +8y | zero | fixA |
|---|---:|---|---|---|---|
| Attack / Attack-Killall-v2 | 342 | 0.000 / 0.000 | 0.000 / 0.000 | 0.000 / 0.000 | 0.000 / 0.000 |
| Attack / Attack-Killer-TCP | 373 | 0.488 / 0.016 | 0.000 / 0.000 | 0.000 / 0.000 | 0.488 / 0.016 |
| Attack / Attack-TCP-BYPass-V1 | 33,122 | 0.985 / 0.993 | 0.985 / 0.993 | 0.985 / 0.999 | 0.985 / 0.993 |
| Attack / Attack-TCP-Control | 341 | 0.003 / 0.091 | 0.006 / 0.167 | 0.000 / 0.000 | 0.000 / 0.000 |
| Attack / Attack-TCP-Flag-ACK | 374 | 0.000 / 0.000 | 0.000 / 0.000 | 0.000 / 0.000 | 0.000 / 0.000 |
| Attack / Attack-TCP-Flag-ACK-PSH | 406 | 0.000 / 0.000 | 0.000 / 0.000 | 0.000 / 0.000 | 0.000 / 0.000 |
| Attack / Attack-TCP-Flag-MIX | 321 | 0.000 / 0.000 | 0.000 / 0.000 | 0.000 / 0.000 | 0.000 / 0.000 |
| Attack / Attack-TCP-Flag-OSYN | 163 | 0.209 / 0.005 | 0.055 / 0.002 | 0.012 / 0.024 | 0.209 / 0.005 |
| Attack / Attack-TCP-Flag-OSYNP | 196 | 0.204 / 0.003 | 0.219 / 0.001 | 0.010 / 0.014 | 0.209 / 0.003 |
| Attack / Attack-TCP-Flag-RST-ACK | 60 | 0.000 / 0.000 | 0.283 / 0.001 | 0.000 / 0.000 | 0.000 / 0.000 |
| Attack / Attack-TCP-Flag-SYN | 498 | 0.000 / 0.000 | 0.000 / 0.000 | 0.707 / 0.010 | 0.000 / 0.000 |
| Attack / Attack-TCP-Flag-SYN-ACK | 494 | 0.000 / 0.000 | 0.000 / 0.000 | 0.000 / 0.000 | 0.000 / 0.000 |
| Attack / Attack-TCP-Flag-SYN-TFO | 184 | 0.005 / 0.043 | 0.011 / 0.065 | 0.011 / 0.002 | 0.000 / 0.000 |
| Attack / Attack-TCP-Flag-SYN-TIME | 183 | 0.011 / 0.002 | 0.000 / 0.000 | 0.000 / 0.000 | 0.011 / 0.002 |
| Attack / Attack-TCP-IGMP | 421 | 0.014 / 0.088 | 0.012 / 0.071 | 0.000 / 0.000 | 0.014 / 0.090 |
| Attack / Attack-TCP-SYN | 388 | 0.000 / 0.000 | 0.000 / 0.000 | 0.000 / 0.000 | 0.000 / 0.000 |
| Attack / Attack-TCP-Valid-SYN | 378 | 0.000 / 0.000 | 0.000 / 0.000 | 0.000 / 0.000 | 0.000 / 0.000 |
| Benign / Benign | 61,728 | 0.459 / 0.948 | 0.248 / 0.956 | 0.016 / 0.965 | 0.458 / 0.948 |
| Benign / Benign-Email-Receive | 236 | 0.131 / 0.110 | 0.161 / 0.019 | 0.178 / 0.021 | 0.131 / 0.095 |
| Benign / Benign-Email-Send | 293 | 0.287 / 0.317 | 0.287 / 0.343 | 0.259 / 0.135 | 0.287 / 0.298 |
| Benign / Benign-FTP | 78 | 0.321 / 0.007 | 0.321 / 0.022 | 0.308 / 0.078 | 0.308 / 0.006 |
| Benign / Benign-SSH | 344 | 0.140 / 0.231 | 0.140 / 0.210 | 0.128 / 0.124 | 0.140 / 0.246 |
| Benign / Benign-Systemic | 1,889 | 0.359 / 0.459 | 0.347 / 0.449 | 0.058 / 0.190 | 0.361 / 0.450 |
| Benign / Benign-Telnet | 1,010 | 0.724 / 0.070 | 0.631 / 0.075 | 0.795 / 0.023 | 0.724 / 0.070 |
| Benign / Benign-Web_Browsing_HTTP-S | 7,057 | 0.451 / 0.915 | 0.466 / 0.922 | 0.487 / 0.788 | 0.451 / 0.920 |
| Suspicious / Suspicious | 3,894 | 0.001 / 0.200 | 0.002 / 0.300 | 0.000 / 0.056 | 0.001 / 0.214 |

**xgb, random split, per class, all test rows** (recall / precision):

| class | support | leaky | +8y | zero | fixA | dropIAT |
|---|---:|---|---|---|---|---|
| Attack / Attack-Killall-v2 | 1,508 | 0.416 / 0.226 | 0.210 / 0.145 | 0.210 / 0.145 | 0.321 / 0.073 | 0.318 / 0.073 |
| Attack / Attack-Killer-TCP | 1,563 | 0.532 / 0.195 | 0.250 / 0.114 | 0.250 / 0.114 | 0.268 / 0.099 | 0.257 / 0.095 |
| Attack / Attack-TCP-BYPass-V1 | 34,592 | 0.955 / 0.998 | 0.001 / 0.645 | 0.001 / 0.645 | 0.949 / 0.999 | 0.949 / 0.999 |
| Attack / Attack-TCP-Control | 1,436 | 0.497 / 0.354 | 0.239 / 0.300 | 0.240 / 0.301 | 0.244 / 0.262 | 0.253 / 0.278 |
| Attack / Attack-TCP-Flag-ACK | 2,671 | 0.421 / 0.546 | 0.294 / 0.531 | 0.294 / 0.531 | 0.285 / 0.518 | 0.289 / 0.521 |
| Attack / Attack-TCP-Flag-ACK-PSH | 1,871 | 0.463 / 0.218 | 0.280 / 0.152 | 0.280 / 0.152 | 0.302 / 0.144 | 0.282 / 0.141 |
| Attack / Attack-TCP-Flag-MIX | 1,854 | 0.414 / 0.442 | 0.204 / 0.346 | 0.204 / 0.346 | 0.196 / 0.315 | 0.196 / 0.336 |
| Attack / Attack-TCP-Flag-OSYN | 217 | 0.825 / 0.357 | 0.046 / 0.192 | 0.046 / 0.192 | 0.194 / 0.012 | 0.346 / 0.006 |
| Attack / Attack-TCP-Flag-OSYNP | 222 | 0.865 / 0.347 | 0.086 / 0.345 | 0.086 / 0.345 | 0.360 / 0.010 | 0.297 / 0.017 |
| Attack / Attack-TCP-Flag-RST-ACK | 361 | 0.850 / 0.511 | 0.499 / 0.759 | 0.499 / 0.759 | 0.526 / 0.083 | 0.518 / 0.088 |
| Attack / Attack-TCP-Flag-SYN | 1,961 | 0.393 / 0.320 | 0.186 / 0.223 | 0.186 / 0.223 | 0.187 / 0.227 | 0.185 / 0.230 |
| Attack / Attack-TCP-Flag-SYN-ACK | 2,051 | 0.363 / 0.316 | 0.203 / 0.256 | 0.203 / 0.256 | 0.206 / 0.278 | 0.209 / 0.276 |
| Attack / Attack-TCP-Flag-SYN-TFO | 908 | 0.896 / 0.683 | 0.703 / 0.867 | 0.705 / 0.867 | 0.699 / 0.771 | 0.692 / 0.808 |
| Attack / Attack-TCP-Flag-SYN-TIME | 340 | 0.779 / 0.404 | 0.132 / 0.381 | 0.132 / 0.378 | 0.185 / 0.066 | 0.185 / 0.061 |
| Attack / Attack-TCP-IGMP | 1,813 | 0.337 / 0.269 | 0.116 / 0.147 | 0.116 / 0.146 | 0.125 / 0.158 | 0.130 / 0.178 |
| Attack / Attack-TCP-SYN | 1,738 | 0.409 / 0.352 | 0.217 / 0.264 | 0.217 / 0.261 | 0.224 / 0.277 | 0.217 / 0.263 |
| Attack / Attack-TCP-Valid-SYN | 2,011 | 0.536 / 0.290 | 0.345 / 0.261 | 0.345 / 0.261 | 0.332 / 0.275 | 0.345 / 0.250 |
| Benign / Benign | 75,571 | 0.752 / 0.981 | 0.432 / 0.971 | 0.826 / 0.908 | 0.682 / 0.940 | 0.641 / 0.953 |
| Benign / Benign-Email-Receive | 349 | 0.542 / 0.035 | 0.421 / 0.076 | 0.433 / 0.066 | 0.473 / 0.057 | 0.476 / 0.053 |
| Benign / Benign-Email-Send | 484 | 0.705 / 0.191 | 0.692 / 0.193 | 0.353 / 0.090 | 0.700 / 0.186 | 0.707 / 0.172 |
| Benign / Benign-FTP | 121 | 0.694 / 0.058 | 0.372 / 0.106 | 0.521 / 0.043 | 0.620 / 0.044 | 0.620 / 0.039 |
| Benign / Benign-SSH | 746 | 0.855 / 0.489 | 0.497 / 0.307 | 0.798 / 0.605 | 0.806 / 0.575 | 0.807 / 0.567 |
| Benign / Benign-Systemic | 12,019 | 0.886 / 0.950 | 0.834 / 0.944 | 0.840 / 0.932 | 0.878 / 0.909 | 0.878 / 0.909 |
| Benign / Benign-Telnet | 1,192 | 0.861 / 0.136 | 0.495 / 0.337 | 0.898 / 0.025 | 0.878 / 0.117 | 0.873 / 0.117 |
| Benign / Benign-Web_Browsing_HTTP-S | 12,818 | 0.817 / 0.930 | 0.732 / 0.894 | 0.940 / 0.706 | 0.728 / 0.942 | 0.726 / 0.941 |
| Suspicious / Suspicious | 14,777 | 0.630 / 0.832 | 0.643 / 0.105 | 0.409 / 0.955 | 0.411 / 0.954 | 0.409 / 0.957 |

**xgb, random split, per class, leaked test rows** (recall / precision):

| class | support | leaky | +8y | zero | fixA | dropIAT |
|---|---:|---|---|---|---|---|
| Attack / Attack-Killall-v2 | 349 | 0.891 / 0.527 | 0.000 / 0.000 | 0.003 / 0.100 | 0.450 / 0.037 | 0.456 / 0.038 |
| Attack / Attack-Killer-TCP | 465 | 0.948 / 0.523 | 0.000 / 0.000 | 0.000 / 0.000 | 0.073 / 0.040 | 0.058 / 0.037 |
| Attack / Attack-TCP-BYPass-V1 | 33,209 | 0.994 / 0.998 | 0.000 / 0.000 | 0.000 / 0.000 | 0.988 / 0.999 | 0.988 / 0.999 |
| Attack / Attack-TCP-Control | 413 | 0.898 / 0.425 | 0.000 / 0.000 | 0.002 / 1.000 | 0.024 / 0.077 | 0.027 / 0.092 |
| Attack / Attack-TCP-Flag-ACK | 450 | 0.753 / 0.584 | 0.000 / 0.000 | 0.000 / 0.000 | 0.000 / 0.000 | 0.000 / 0.000 |
| Attack / Attack-TCP-Flag-ACK-PSH | 439 | 0.781 / 0.645 | 0.000 / 0.000 | 0.000 / 0.000 | 0.021 / 0.200 | 0.023 / 0.227 |
| Attack / Attack-TCP-Flag-MIX | 413 | 0.942 / 0.605 | 0.000 / 0.000 | 0.000 / 0.000 | 0.002 / 0.053 | 0.005 / 0.065 |
| Attack / Attack-TCP-Flag-OSYN | 189 | 0.894 / 0.376 | 0.000 / 0.000 | 0.000 / 0.000 | 0.175 / 0.009 | 0.328 / 0.005 |
| Attack / Attack-TCP-Flag-OSYNP | 183 | 0.945 / 0.347 | 0.000 / 0.000 | 0.000 / 0.000 | 0.350 / 0.008 | 0.279 / 0.013 |
| Attack / Attack-TCP-Flag-RST-ACK | 140 | 0.907 / 0.349 | 0.000 / 0.000 | 0.000 / 0.000 | 0.057 / 0.004 | 0.064 / 0.005 |
| Attack / Attack-TCP-Flag-SYN | 427 | 0.951 / 0.524 | 0.000 / 0.000 | 0.000 / 0.000 | 0.016 / 0.127 | 0.014 / 0.085 |
| Attack / Attack-TCP-Flag-SYN-ACK | 367 | 0.891 / 0.450 | 0.000 / 0.000 | 0.000 / 0.000 | 0.025 / 0.300 | 0.019 / 0.333 |
| Attack / Attack-TCP-Flag-SYN-TFO | 198 | 0.889 / 0.387 | 0.000 / 0.000 | 0.010 / 1.000 | 0.020 / 0.040 | 0.010 / 0.037 |
| Attack / Attack-TCP-Flag-SYN-TIME | 235 | 0.936 / 0.409 | 0.000 / 0.000 | 0.000 / 0.000 | 0.089 / 0.025 | 0.111 / 0.028 |
| Attack / Attack-TCP-IGMP | 408 | 0.980 / 0.480 | 0.000 / 0.000 | 0.000 / 0.000 | 0.032 / 0.159 | 0.025 / 0.119 |
| Attack / Attack-TCP-SYN | 363 | 0.917 / 0.566 | 0.000 / 0.000 | 0.000 / 0.000 | 0.014 / 0.091 | 0.011 / 0.089 |
| Attack / Attack-TCP-Valid-SYN | 399 | 0.965 / 0.364 | 0.000 / 0.000 | 0.000 / 0.000 | 0.000 / 0.000 | 0.000 / 0.000 |
| Benign / Benign | 61,174 | 0.729 / 0.980 | 0.335 / 0.964 | 0.821 / 0.891 | 0.641 / 0.928 | 0.596 / 0.944 |
| Benign / Benign-Email-Receive | 236 | 0.479 / 0.026 | 0.301 / 0.077 | 0.318 / 0.058 | 0.381 / 0.045 | 0.386 / 0.046 |
| Benign / Benign-Email-Send | 285 | 0.614 / 0.135 | 0.593 / 0.136 | 0.018 / 0.004 | 0.607 / 0.129 | 0.614 / 0.121 |
| Benign / Benign-FTP | 72 | 0.597 / 0.037 | 0.056 / 0.026 | 0.306 / 0.018 | 0.472 / 0.023 | 0.472 / 0.022 |
| Benign / Benign-SSH | 377 | 0.780 / 0.419 | 0.072 / 0.045 | 0.666 / 0.661 | 0.692 / 0.555 | 0.692 / 0.589 |
| Benign / Benign-Systemic | 2,004 | 0.440 / 0.797 | 0.131 / 0.497 | 0.165 / 0.447 | 0.395 / 0.522 | 0.395 / 0.526 |
| Benign / Benign-Telnet | 992 | 0.856 / 0.122 | 0.416 / 0.355 | 0.900 / 0.021 | 0.875 / 0.103 | 0.870 / 0.103 |
| Benign / Benign-Web_Browsing_HTTP-S | 6,974 | 0.696 / 0.914 | 0.539 / 0.829 | 0.921 / 0.578 | 0.532 / 0.939 | 0.532 / 0.937 |
| Suspicious / Suspicious | 3,883 | 0.839 / 0.671 | 0.891 / 0.041 | 0.000 / 0.000 | 0.017 / 0.793 | 0.015 / 0.822 |

**xgb, temporal split, per class, all test rows** (recall / precision):

| class | support | leaky | +8y | zero | fixA | dropIAT |
|---|---:|---|---|---|---|---|
| Attack / Attack-Killall-v2 | 1,508 | 0.395 / 0.173 | 0.213 / 0.102 | 0.213 / 0.102 | 0.310 / 0.067 | 0.299 / 0.065 |
| Attack / Attack-Killer-TCP | 1,564 | 0.388 / 0.219 | 0.252 / 0.157 | 0.252 / 0.157 | 0.263 / 0.114 | 0.262 / 0.102 |
| Attack / Attack-TCP-BYPass-V1 | 34,592 | 0.945 / 0.997 | 0.000 / 0.214 | 0.000 / 0.214 | 0.943 / 0.999 | 0.943 / 0.999 |
| Attack / Attack-TCP-Control | 1,436 | 0.414 / 0.497 | 0.220 / 0.344 | 0.220 / 0.344 | 0.216 / 0.313 | 0.216 / 0.316 |
| Attack / Attack-TCP-Flag-ACK | 2,671 | 0.235 / 0.299 | 0.229 / 0.441 | 0.229 / 0.440 | 0.222 / 0.481 | 0.220 / 0.459 |
| Attack / Attack-TCP-Flag-ACK-PSH | 1,870 | 0.422 / 0.070 | 0.240 / 0.102 | 0.240 / 0.102 | 0.268 / 0.097 | 0.282 / 0.098 |
| Attack / Attack-TCP-Flag-MIX | 1,854 | 0.319 / 0.197 | 0.300 / 0.203 | 0.300 / 0.203 | 0.304 / 0.192 | 0.299 / 0.198 |
| Attack / Attack-TCP-Flag-OSYN | 217 | 0.507 / 0.385 | 0.032 / 0.269 | 0.032 / 0.269 | 0.134 / 0.002 | 0.147 / 0.003 |
| Attack / Attack-TCP-Flag-OSYNP | 222 | 0.468 / 0.689 | 0.036 / 0.333 | 0.036 / 0.333 | 0.275 / 0.006 | 0.279 / 0.006 |
| Attack / Attack-TCP-Flag-RST-ACK | 361 | 0.271 / 0.803 | 0.133 / 0.750 | 0.133 / 0.738 | 0.158 / 0.026 | 0.183 / 0.030 |
| Attack / Attack-TCP-Flag-SYN | 1,961 | 0.158 / 0.125 | 0.107 / 0.135 | 0.107 / 0.135 | 0.110 / 0.140 | 0.105 / 0.138 |
| Attack / Attack-TCP-Flag-SYN-ACK | 2,051 | 0.310 / 0.217 | 0.141 / 0.179 | 0.141 / 0.179 | 0.139 / 0.176 | 0.138 / 0.181 |
| Attack / Attack-TCP-Flag-SYN-TFO | 908 | 0.839 / 0.709 | 0.759 / 0.694 | 0.761 / 0.689 | 0.768 / 0.638 | 0.762 / 0.646 |
| Attack / Attack-TCP-Flag-SYN-TIME | 340 | 0.050 / 0.086 | 0.000 / 0.000 | 0.000 / 0.000 | 0.009 / 0.002 | 0.012 / 0.004 |
| Attack / Attack-TCP-IGMP | 1,813 | 0.121 / 0.187 | 0.082 / 0.139 | 0.082 / 0.139 | 0.074 / 0.140 | 0.085 / 0.159 |
| Attack / Attack-TCP-SYN | 1,738 | 0.256 / 0.338 | 0.072 / 0.182 | 0.072 / 0.182 | 0.067 / 0.169 | 0.062 / 0.152 |
| Attack / Attack-TCP-Valid-SYN | 2,011 | 0.473 / 0.351 | 0.352 / 0.287 | 0.352 / 0.287 | 0.357 / 0.317 | 0.337 / 0.298 |
| Benign / Benign | 75,571 | 0.562 / 0.973 | 0.417 / 0.972 | 0.731 / 0.917 | 0.574 / 0.965 | 0.575 / 0.964 |
| Benign / Benign-Email-Receive | 348 | 0.414 / 0.062 | 0.425 / 0.053 | 0.316 / 0.063 | 0.428 / 0.053 | 0.425 / 0.050 |
| Benign / Benign-Email-Send | 485 | 0.594 / 0.210 | 0.631 / 0.240 | 0.480 / 0.251 | 0.635 / 0.193 | 0.637 / 0.186 |
| Benign / Benign-FTP | 120 | 0.550 / 0.111 | 0.275 / 0.145 | 0.450 / 0.102 | 0.583 / 0.040 | 0.583 / 0.039 |
| Benign / Benign-SSH | 745 | 0.423 / 0.534 | 0.400 / 0.542 | 0.544 / 0.029 | 0.440 / 0.475 | 0.442 / 0.453 |
| Benign / Benign-Systemic | 12,019 | 0.917 / 0.400 | 0.840 / 0.836 | 0.843 / 0.934 | 0.891 / 0.908 | 0.891 / 0.907 |
| Benign / Benign-Telnet | 1,192 | 0.862 / 0.123 | 0.332 / 0.427 | 0.876 / 0.025 | 0.900 / 0.131 | 0.895 / 0.131 |
| Benign / Benign-Web_Browsing_HTTP-S | 12,818 | 0.626 / 0.915 | 0.440 / 0.939 | 0.892 / 0.698 | 0.695 / 0.927 | 0.691 / 0.928 |
| Suspicious / Suspicious | 14,776 | 0.511 / 0.580 | 0.595 / 0.092 | 0.343 / 0.893 | 0.345 / 0.875 | 0.340 / 0.877 |

**xgb, temporal split, per class, leaked test rows** (recall / precision):

| class | support | leaky | +8y | zero | fixA | dropIAT |
|---|---:|---|---|---|---|---|
| Attack / Attack-Killall-v2 | 342 | 0.804 / 0.868 | 0.000 / 0.000 | 0.000 / 0.000 | 0.482 / 0.040 | 0.482 / 0.040 |
| Attack / Attack-Killer-TCP | 373 | 0.571 / 0.789 | 0.000 / 0.000 | 0.000 / 0.000 | 0.032 / 0.011 | 0.035 / 0.010 |
| Attack / Attack-TCP-BYPass-V1 | 33,122 | 0.987 / 0.997 | 0.000 / 0.000 | 0.000 / 0.000 | 0.985 / 1.000 | 0.985 / 1.000 |
| Attack / Attack-TCP-Control | 341 | 0.815 / 1.000 | 0.000 / 0.000 | 0.000 / 0.000 | 0.018 / 0.078 | 0.015 / 0.088 |
| Attack / Attack-TCP-Flag-ACK | 374 | 0.048 / 0.025 | 0.000 / 0.000 | 0.000 / 0.000 | 0.000 / 0.000 | 0.000 / 0.000 |
| Attack / Attack-TCP-Flag-ACK-PSH | 406 | 0.837 / 0.050 | 0.000 / 0.000 | 0.000 / 0.000 | 0.000 / 0.000 | 0.002 / 0.045 |
| Attack / Attack-TCP-Flag-MIX | 321 | 0.109 / 0.129 | 0.000 / 0.000 | 0.000 / 0.000 | 0.000 / 0.000 | 0.000 / 0.000 |
| Attack / Attack-TCP-Flag-OSYN | 163 | 0.632 / 0.396 | 0.000 / 0.000 | 0.000 / 0.000 | 0.147 / 0.002 | 0.153 / 0.002 |
| Attack / Attack-TCP-Flag-OSYNP | 196 | 0.490 / 0.756 | 0.000 / 0.000 | 0.000 / 0.000 | 0.245 / 0.005 | 0.250 / 0.005 |
| Attack / Attack-TCP-Flag-RST-ACK | 60 | 0.833 / 0.862 | 0.000 / 0.000 | 0.000 / 0.000 | 0.083 / 0.002 | 0.083 / 0.002 |
| Attack / Attack-TCP-Flag-SYN | 498 | 0.201 / 0.109 | 0.000 / 0.000 | 0.000 / 0.000 | 0.006 / 0.065 | 0.004 / 0.043 |
| Attack / Attack-TCP-Flag-SYN-ACK | 494 | 0.700 / 0.265 | 0.000 / 0.000 | 0.000 / 0.000 | 0.002 / 0.067 | 0.002 / 0.062 |
| Attack / Attack-TCP-Flag-SYN-TFO | 184 | 0.397 / 0.890 | 0.000 / 0.000 | 0.011 / 0.200 | 0.016 / 0.033 | 0.022 / 0.045 |
| Attack / Attack-TCP-Flag-SYN-TIME | 183 | 0.093 / 0.142 | 0.000 / 0.000 | 0.000 / 0.000 | 0.016 / 0.002 | 0.022 / 0.004 |
| Attack / Attack-TCP-IGMP | 421 | 0.171 / 0.626 | 0.000 / 0.000 | 0.000 / 0.000 | 0.010 / 0.066 | 0.012 / 0.100 |
| Attack / Attack-TCP-SYN | 388 | 0.825 / 0.509 | 0.000 / 0.000 | 0.000 / 0.000 | 0.008 / 0.075 | 0.008 / 0.061 |
| Attack / Attack-TCP-Valid-SYN | 378 | 0.646 / 0.988 | 0.000 / 0.000 | 0.000 / 0.000 | 0.000 / 0.000 | 0.000 / 0.000 |
| Benign / Benign | 61,728 | 0.489 / 0.971 | 0.311 / 0.968 | 0.696 / 0.901 | 0.503 / 0.960 | 0.507 / 0.960 |
| Benign / Benign-Email-Receive | 236 | 0.288 / 0.045 | 0.305 / 0.036 | 0.144 / 0.037 | 0.314 / 0.037 | 0.301 / 0.035 |
| Benign / Benign-Email-Send | 293 | 0.471 / 0.135 | 0.532 / 0.168 | 0.283 / 0.143 | 0.539 / 0.124 | 0.543 / 0.122 |
| Benign / Benign-FTP | 78 | 0.449 / 0.080 | 0.026 / 0.030 | 0.295 / 0.063 | 0.500 / 0.024 | 0.513 / 0.025 |
| Benign / Benign-SSH | 344 | 0.076 / 0.217 | 0.026 / 0.113 | 0.337 / 0.009 | 0.116 / 0.179 | 0.122 / 0.169 |
| Benign / Benign-Systemic | 1,889 | 0.568 / 0.062 | 0.074 / 0.082 | 0.093 / 0.368 | 0.400 / 0.533 | 0.398 / 0.527 |
| Benign / Benign-Telnet | 1,010 | 0.847 / 0.110 | 0.221 / 0.628 | 0.862 / 0.022 | 0.891 / 0.118 | 0.888 / 0.117 |
| Benign / Benign-Web_Browsing_HTTP-S | 7,057 | 0.371 / 0.872 | 0.034 / 0.988 | 0.854 / 0.567 | 0.496 / 0.913 | 0.489 / 0.913 |
| Suspicious / Suspicious | 3,894 | 0.637 / 0.338 | 0.958 / 0.042 | 0.000 / 0.000 | 0.004 / 0.106 | 0.003 / 0.081 |

**rf, random split, per class, all test rows** (recall / precision):

| class | support | leaky | +8y | zero | fixA | dropIAT |
|---|---:|---|---|---|---|---|
| Attack / Attack-Killall-v2 | 1,508 | 0.426 / 0.232 | 0.216 / 0.152 | 0.216 / 0.152 | 0.316 / 0.075 | 0.326 / 0.074 |
| Attack / Attack-Killer-TCP | 1,563 | 0.531 / 0.208 | 0.250 / 0.123 | 0.250 / 0.123 | 0.251 / 0.117 | 0.249 / 0.112 |
| Attack / Attack-TCP-BYPass-V1 | 34,592 | 0.955 / 0.998 | 0.000 / 0.000 | 0.000 / 0.000 | 0.948 / 0.993 | 0.948 / 0.993 |
| Attack / Attack-TCP-Control | 1,436 | 0.533 / 0.350 | 0.269 / 0.261 | 0.269 / 0.261 | 0.272 / 0.246 | 0.280 / 0.259 |
| Attack / Attack-TCP-Flag-ACK | 2,671 | 0.425 / 0.585 | 0.267 / 0.533 | 0.267 / 0.533 | 0.271 / 0.536 | 0.264 / 0.543 |
| Attack / Attack-TCP-Flag-ACK-PSH | 1,871 | 0.483 / 0.241 | 0.257 / 0.153 | 0.257 / 0.153 | 0.255 / 0.154 | 0.243 / 0.149 |
| Attack / Attack-TCP-Flag-MIX | 1,854 | 0.426 / 0.371 | 0.216 / 0.283 | 0.216 / 0.283 | 0.218 / 0.280 | 0.204 / 0.276 |
| Attack / Attack-TCP-Flag-OSYN | 217 | 0.862 / 0.273 | 0.060 / 0.094 | 0.060 / 0.096 | 0.364 / 0.007 | 0.341 / 0.007 |
| Attack / Attack-TCP-Flag-OSYNP | 222 | 0.883 / 0.298 | 0.099 / 0.126 | 0.090 / 0.175 | 0.410 / 0.015 | 0.423 / 0.014 |
| Attack / Attack-TCP-Flag-RST-ACK | 361 | 0.881 / 0.427 | 0.512 / 0.690 | 0.512 / 0.663 | 0.526 / 0.131 | 0.504 / 0.151 |
| Attack / Attack-TCP-Flag-SYN | 1,961 | 0.397 / 0.295 | 0.194 / 0.197 | 0.194 / 0.197 | 0.200 / 0.200 | 0.197 / 0.205 |
| Attack / Attack-TCP-Flag-SYN-ACK | 2,051 | 0.359 / 0.321 | 0.189 / 0.228 | 0.189 / 0.228 | 0.197 / 0.230 | 0.191 / 0.231 |
| Attack / Attack-TCP-Flag-SYN-TFO | 908 | 0.898 / 0.647 | 0.698 / 0.871 | 0.699 / 0.869 | 0.702 / 0.855 | 0.693 / 0.830 |
| Attack / Attack-TCP-Flag-SYN-TIME | 340 | 0.818 / 0.307 | 0.168 / 0.178 | 0.147 / 0.195 | 0.268 / 0.011 | 0.259 / 0.011 |
| Attack / Attack-TCP-IGMP | 1,813 | 0.345 / 0.271 | 0.137 / 0.163 | 0.137 / 0.163 | 0.137 / 0.156 | 0.133 / 0.156 |
| Attack / Attack-TCP-SYN | 1,738 | 0.401 / 0.331 | 0.208 / 0.247 | 0.208 / 0.247 | 0.208 / 0.236 | 0.206 / 0.245 |
| Attack / Attack-TCP-Valid-SYN | 2,011 | 0.515 / 0.302 | 0.321 / 0.248 | 0.321 / 0.248 | 0.323 / 0.249 | 0.320 / 0.238 |
| Benign / Benign | 75,571 | 0.751 / 0.978 | 0.297 / 0.974 | 0.573 / 0.922 | 0.551 / 0.964 | 0.556 / 0.964 |
| Benign / Benign-Email-Receive | 349 | 0.484 / 0.042 | 0.295 / 0.079 | 0.384 / 0.010 | 0.461 / 0.062 | 0.456 / 0.066 |
| Benign / Benign-Email-Send | 484 | 0.676 / 0.181 | 0.707 / 0.033 | 0.531 / 0.336 | 0.698 / 0.202 | 0.696 / 0.213 |
| Benign / Benign-FTP | 121 | 0.719 / 0.060 | 0.405 / 0.014 | 0.545 / 0.021 | 0.587 / 0.033 | 0.579 / 0.034 |
| Benign / Benign-SSH | 746 | 0.842 / 0.519 | 0.491 / 0.284 | 0.784 / 0.590 | 0.796 / 0.593 | 0.795 / 0.614 |
| Benign / Benign-Systemic | 12,019 | 0.873 / 0.943 | 0.816 / 0.951 | 0.818 / 0.943 | 0.867 / 0.905 | 0.866 / 0.905 |
| Benign / Benign-Telnet | 1,192 | 0.803 / 0.117 | 0.339 / 0.233 | 0.886 / 0.020 | 0.805 / 0.097 | 0.794 / 0.096 |
| Benign / Benign-Web_Browsing_HTTP-S | 12,818 | 0.834 / 0.929 | 0.535 / 0.482 | 0.888 / 0.706 | 0.709 / 0.945 | 0.706 / 0.944 |
| Suspicious / Suspicious | 14,777 | 0.611 / 0.823 | 0.614 / 0.106 | 0.382 / 0.983 | 0.382 / 0.983 | 0.377 / 0.984 |

**rf, random split, per class, leaked test rows** (recall / precision):

| class | support | leaky | +8y | zero | fixA | dropIAT |
|---|---:|---|---|---|---|---|
| Attack / Attack-Killall-v2 | 349 | 0.911 / 0.506 | 0.000 / 0.000 | 0.003 / 0.100 | 0.447 / 0.037 | 0.447 / 0.037 |
| Attack / Attack-Killer-TCP | 465 | 0.944 / 0.541 | 0.000 / 0.000 | 0.000 / 0.000 | 0.009 / 0.020 | 0.009 / 0.040 |
| Attack / Attack-TCP-BYPass-V1 | 33,209 | 0.995 / 0.998 | 0.000 / 0.000 | 0.000 / 0.000 | 0.988 / 0.993 | 0.988 / 0.993 |
| Attack / Attack-TCP-Control | 413 | 0.920 / 0.536 | 0.002 / 1.000 | 0.002 / 1.000 | 0.027 / 0.105 | 0.027 / 0.108 |
| Attack / Attack-TCP-Flag-ACK | 450 | 0.942 / 0.701 | 0.000 / 0.000 | 0.000 / 0.000 | 0.002 / 0.091 | 0.000 / 0.000 |
| Attack / Attack-TCP-Flag-ACK-PSH | 439 | 0.966 / 0.691 | 0.000 / 0.000 | 0.000 / 0.000 | 0.002 / 0.083 | 0.002 / 0.045 |
| Attack / Attack-TCP-Flag-MIX | 413 | 0.942 / 0.549 | 0.000 / 0.000 | 0.000 / 0.000 | 0.002 / 0.167 | 0.002 / 0.200 |
| Attack / Attack-TCP-Flag-OSYN | 189 | 0.921 / 0.315 | 0.000 / 0.000 | 0.000 / 0.000 | 0.339 / 0.006 | 0.312 / 0.005 |
| Attack / Attack-TCP-Flag-OSYNP | 183 | 0.962 / 0.324 | 0.011 / 0.033 | 0.000 / 0.000 | 0.383 / 0.012 | 0.404 / 0.011 |
| Attack / Attack-TCP-Flag-RST-ACK | 140 | 0.950 / 0.278 | 0.000 / 0.000 | 0.000 / 0.000 | 0.029 / 0.003 | 0.014 / 0.002 |
| Attack / Attack-TCP-Flag-SYN | 427 | 0.930 / 0.569 | 0.000 / 0.000 | 0.000 / 0.000 | 0.009 / 0.089 | 0.009 / 0.089 |
| Attack / Attack-TCP-Flag-SYN-ACK | 367 | 0.948 / 0.590 | 0.000 / 0.000 | 0.000 / 0.000 | 0.003 / 0.100 | 0.003 / 0.083 |
| Attack / Attack-TCP-Flag-SYN-TFO | 198 | 0.914 / 0.340 | 0.000 / 0.000 | 0.005 / 0.333 | 0.000 / 0.000 | 0.000 / 0.000 |
| Attack / Attack-TCP-Flag-SYN-TIME | 235 | 0.970 / 0.343 | 0.030 / 0.090 | 0.000 / 0.000 | 0.166 / 0.005 | 0.162 / 0.005 |
| Attack / Attack-TCP-IGMP | 408 | 0.924 / 0.477 | 0.000 / 0.000 | 0.000 / 0.000 | 0.027 / 0.200 | 0.029 / 0.200 |
| Attack / Attack-TCP-SYN | 363 | 0.923 / 0.523 | 0.000 / 0.000 | 0.000 / 0.000 | 0.011 / 0.087 | 0.014 / 0.102 |
| Attack / Attack-TCP-Valid-SYN | 399 | 0.977 / 0.473 | 0.000 / 0.000 | 0.000 / 0.000 | 0.000 / 0.000 | 0.000 / 0.000 |
| Benign / Benign | 61,174 | 0.731 / 0.977 | 0.169 / 0.966 | 0.510 / 0.902 | 0.484 / 0.957 | 0.484 / 0.958 |
| Benign / Benign-Email-Receive | 236 | 0.394 / 0.030 | 0.114 / 0.064 | 0.246 / 0.005 | 0.352 / 0.050 | 0.356 / 0.048 |
| Benign / Benign-Email-Send | 285 | 0.558 / 0.110 | 0.611 / 0.017 | 0.312 / 0.219 | 0.596 / 0.133 | 0.596 / 0.132 |
| Benign / Benign-FTP | 72 | 0.611 / 0.042 | 0.083 / 0.002 | 0.319 / 0.009 | 0.389 / 0.016 | 0.375 / 0.016 |
| Benign / Benign-SSH | 377 | 0.775 / 0.469 | 0.080 / 0.043 | 0.660 / 0.613 | 0.684 / 0.607 | 0.679 / 0.621 |
| Benign / Benign-Systemic | 2,004 | 0.409 / 0.782 | 0.066 / 0.578 | 0.077 / 0.456 | 0.372 / 0.517 | 0.369 / 0.520 |
| Benign / Benign-Telnet | 992 | 0.796 / 0.110 | 0.239 / 0.311 | 0.896 / 0.017 | 0.801 / 0.088 | 0.799 / 0.089 |
| Benign / Benign-Web_Browsing_HTTP-S | 6,974 | 0.751 / 0.912 | 0.201 / 0.166 | 0.851 / 0.573 | 0.521 / 0.941 | 0.519 / 0.940 |
| Suspicious / Suspicious | 3,883 | 0.869 / 0.646 | 0.880 / 0.043 | 0.000 / 0.000 | 0.004 / 0.842 | 0.005 / 0.808 |

**rf, temporal split, per class, all test rows** (recall / precision):

| class | support | leaky | +8y | zero | fixA | dropIAT |
|---|---:|---|---|---|---|---|
| Attack / Attack-Killall-v2 | 1,508 | 0.247 / 0.139 | 0.192 / 0.116 | 0.192 / 0.116 | 0.182 / 0.116 | 0.196 / 0.109 |
| Attack / Attack-Killer-TCP | 1,564 | 0.314 / 0.163 | 0.272 / 0.148 | 0.272 / 0.148 | 0.368 / 0.078 | 0.370 / 0.080 |
| Attack / Attack-TCP-BYPass-V1 | 34,592 | 0.952 / 0.994 | 0.000 / 0.000 | 0.000 / 0.000 | 0.943 / 0.993 | 0.943 / 0.993 |
| Attack / Attack-TCP-Control | 1,436 | 0.370 / 0.405 | 0.233 / 0.304 | 0.233 / 0.304 | 0.235 / 0.283 | 0.233 / 0.293 |
| Attack / Attack-TCP-Flag-ACK | 2,671 | 0.362 / 0.416 | 0.237 / 0.506 | 0.237 / 0.506 | 0.239 / 0.492 | 0.263 / 0.566 |
| Attack / Attack-TCP-Flag-ACK-PSH | 1,870 | 0.389 / 0.107 | 0.241 / 0.108 | 0.241 / 0.108 | 0.227 / 0.106 | 0.229 / 0.104 |
| Attack / Attack-TCP-Flag-MIX | 1,854 | 0.394 / 0.192 | 0.317 / 0.182 | 0.317 / 0.182 | 0.325 / 0.179 | 0.300 / 0.176 |
| Attack / Attack-TCP-Flag-OSYN | 217 | 0.157 / 0.187 | 0.046 / 0.169 | 0.055 / 0.179 | 0.244 / 0.004 | 0.253 / 0.004 |
| Attack / Attack-TCP-Flag-OSYNP | 222 | 0.144 / 0.132 | 0.077 / 0.084 | 0.068 / 0.142 | 0.266 / 0.005 | 0.297 / 0.005 |
| Attack / Attack-TCP-Flag-RST-ACK | 361 | 0.166 / 0.451 | 0.158 / 0.640 | 0.158 / 0.613 | 0.175 / 0.037 | 0.150 / 0.045 |
| Attack / Attack-TCP-Flag-SYN | 1,961 | 0.149 / 0.137 | 0.097 / 0.121 | 0.097 / 0.121 | 0.101 / 0.120 | 0.101 / 0.122 |
| Attack / Attack-TCP-Flag-SYN-ACK | 2,051 | 0.327 / 0.208 | 0.160 / 0.183 | 0.160 / 0.183 | 0.163 / 0.179 | 0.154 / 0.193 |
| Attack / Attack-TCP-Flag-SYN-TFO | 908 | 0.923 / 0.694 | 0.759 / 0.686 | 0.759 / 0.687 | 0.759 / 0.673 | 0.762 / 0.674 |
| Attack / Attack-TCP-Flag-SYN-TIME | 340 | 0.247 / 0.268 | 0.006 / 0.008 | 0.006 / 0.013 | 0.015 / 0.003 | 0.021 / 0.005 |
| Attack / Attack-TCP-IGMP | 1,813 | 0.144 / 0.202 | 0.081 / 0.134 | 0.081 / 0.134 | 0.090 / 0.132 | 0.088 / 0.142 |
| Attack / Attack-TCP-SYN | 1,738 | 0.230 / 0.362 | 0.060 / 0.143 | 0.060 / 0.143 | 0.059 / 0.125 | 0.060 / 0.145 |
| Attack / Attack-TCP-Valid-SYN | 2,011 | 0.405 / 0.300 | 0.339 / 0.266 | 0.339 / 0.266 | 0.340 / 0.270 | 0.340 / 0.261 |
| Benign / Benign | 75,571 | 0.464 / 0.966 | 0.274 / 0.976 | 0.526 / 0.929 | 0.570 / 0.962 | 0.578 / 0.962 |
| Benign / Benign-Email-Receive | 348 | 0.371 / 0.050 | 0.325 / 0.042 | 0.371 / 0.009 | 0.408 / 0.060 | 0.405 / 0.068 |
| Benign / Benign-Email-Send | 485 | 0.563 / 0.159 | 0.635 / 0.084 | 0.487 / 0.335 | 0.641 / 0.218 | 0.641 / 0.227 |
| Benign / Benign-FTP | 120 | 0.567 / 0.076 | 0.292 / 0.044 | 0.492 / 0.024 | 0.467 / 0.027 | 0.467 / 0.028 |
| Benign / Benign-SSH | 745 | 0.432 / 0.478 | 0.372 / 0.575 | 0.432 / 0.467 | 0.443 / 0.470 | 0.431 / 0.470 |
| Benign / Benign-Systemic | 12,019 | 0.911 / 0.328 | 0.828 / 0.932 | 0.827 / 0.918 | 0.883 / 0.885 | 0.883 / 0.884 |
| Benign / Benign-Telnet | 1,192 | 0.705 / 0.144 | 0.314 / 0.258 | 0.931 / 0.022 | 0.790 / 0.106 | 0.782 / 0.109 |
| Benign / Benign-Web_Browsing_HTTP-S | 12,818 | 0.572 / 0.872 | 0.423 / 0.934 | 0.824 / 0.471 | 0.663 / 0.942 | 0.662 / 0.941 |
| Suspicious / Suspicious | 14,776 | 0.564 / 0.421 | 0.564 / 0.080 | 0.309 / 0.918 | 0.309 / 0.898 | 0.302 / 0.898 |

**rf, temporal split, per class, leaked test rows** (recall / precision):

| class | support | leaky | +8y | zero | fixA | dropIAT |
|---|---:|---|---|---|---|---|
| Attack / Attack-Killall-v2 | 342 | 0.240 / 0.466 | 0.000 / 0.000 | 0.000 / 0.000 | 0.000 / 0.000 | 0.000 / 0.000 |
| Attack / Attack-Killer-TCP | 373 | 0.174 / 0.464 | 0.000 / 0.000 | 0.000 / 0.000 | 0.429 / 0.035 | 0.424 / 0.038 |
| Attack / Attack-TCP-BYPass-V1 | 33,122 | 0.994 / 0.994 | 0.000 / 0.000 | 0.000 / 0.000 | 0.985 / 0.993 | 0.985 / 0.993 |
| Attack / Attack-TCP-Control | 341 | 0.578 / 0.929 | 0.000 / 0.000 | 0.000 / 0.000 | 0.012 / 0.103 | 0.012 / 0.125 |
| Attack / Attack-TCP-Flag-ACK | 374 | 0.890 / 0.311 | 0.000 / 0.000 | 0.000 / 0.000 | 0.000 / 0.000 | 0.000 / 0.000 |
| Attack / Attack-TCP-Flag-ACK-PSH | 406 | 0.685 / 0.106 | 0.000 / 0.000 | 0.000 / 0.000 | 0.000 / 0.000 | 0.000 / 0.000 |
| Attack / Attack-TCP-Flag-MIX | 321 | 0.445 / 0.250 | 0.000 / 0.000 | 0.000 / 0.000 | 0.003 / 0.011 | 0.000 / 0.000 |
| Attack / Attack-TCP-Flag-OSYN | 163 | 0.147 / 0.190 | 0.000 / 0.000 | 0.012 / 0.182 | 0.264 / 0.003 | 0.264 / 0.003 |
| Attack / Attack-TCP-Flag-OSYNP | 196 | 0.087 / 0.123 | 0.010 / 0.021 | 0.000 / 0.000 | 0.224 / 0.004 | 0.260 / 0.004 |
| Attack / Attack-TCP-Flag-RST-ACK | 60 | 0.050 / 0.065 | 0.000 / 0.000 | 0.000 / 0.000 | 0.050 / 0.002 | 0.017 / 0.001 |
| Attack / Attack-TCP-Flag-SYN | 498 | 0.203 / 0.181 | 0.000 / 0.000 | 0.000 / 0.000 | 0.002 / 0.032 | 0.004 / 0.077 |
| Attack / Attack-TCP-Flag-SYN-ACK | 494 | 0.694 / 0.237 | 0.000 / 0.000 | 0.000 / 0.000 | 0.000 / 0.000 | 0.000 / 0.000 |
| Attack / Attack-TCP-Flag-SYN-TFO | 184 | 0.810 / 0.730 | 0.000 / 0.000 | 0.000 / 0.000 | 0.005 / 0.037 | 0.000 / 0.000 |
| Attack / Attack-TCP-Flag-SYN-TIME | 183 | 0.448 / 0.516 | 0.000 / 0.000 | 0.000 / 0.000 | 0.016 / 0.002 | 0.005 / 0.001 |
| Attack / Attack-TCP-IGMP | 421 | 0.271 / 0.582 | 0.000 / 0.000 | 0.000 / 0.000 | 0.010 / 0.073 | 0.014 / 0.115 |
| Attack / Attack-TCP-SYN | 388 | 0.758 / 0.797 | 0.000 / 0.000 | 0.000 / 0.000 | 0.005 / 0.065 | 0.005 / 0.105 |
| Attack / Attack-TCP-Valid-SYN | 378 | 0.352 / 0.847 | 0.000 / 0.000 | 0.000 / 0.000 | 0.000 / 0.000 | 0.000 / 0.000 |
| Benign / Benign | 61,728 | 0.370 / 0.961 | 0.137 / 0.977 | 0.445 / 0.910 | 0.503 / 0.957 | 0.505 / 0.957 |
| Benign / Benign-Email-Receive | 236 | 0.242 / 0.031 | 0.174 / 0.021 | 0.242 / 0.004 | 0.288 / 0.047 | 0.288 / 0.045 |
| Benign / Benign-Email-Send | 293 | 0.420 / 0.083 | 0.539 / 0.046 | 0.294 / 0.184 | 0.549 / 0.140 | 0.549 / 0.141 |
| Benign / Benign-FTP | 78 | 0.474 / 0.068 | 0.051 / 0.009 | 0.359 / 0.013 | 0.321 / 0.015 | 0.321 / 0.015 |
| Benign / Benign-SSH | 344 | 0.169 / 0.252 | 0.038 / 0.342 | 0.169 / 0.237 | 0.174 / 0.240 | 0.174 / 0.262 |
| Benign / Benign-Systemic | 1,889 | 0.573 / 0.047 | 0.041 / 0.456 | 0.034 / 0.200 | 0.390 / 0.495 | 0.391 / 0.493 |
| Benign / Benign-Telnet | 1,010 | 0.680 / 0.134 | 0.219 / 0.303 | 0.948 / 0.019 | 0.782 / 0.098 | 0.782 / 0.101 |
| Benign / Benign-Web_Browsing_HTTP-S | 7,057 | 0.305 / 0.752 | 0.033 / 0.928 | 0.763 / 0.319 | 0.466 / 0.950 | 0.467 / 0.950 |
| Suspicious / Suspicious | 3,894 | 0.965 / 0.254 | 0.966 / 0.038 | 0.000 / 0.000 | 0.000 / 0.009 | 0.001 / 0.017 |

**mlp, random split, per class, all test rows** (recall / precision):

| class | support | leaky | +8y | zero | fixA | dropIAT |
|---|---:|---|---|---|---|---|
| Attack / Attack-Killall-v2 | 1,508 | 0.021 / 0.421 | 0.021 / 0.443 | 0.021 / 0.427 | 0.023 / 0.500 | 0.018 / 0.614 |
| Attack / Attack-Killer-TCP | 1,563 | 0.000 / 0.000 | 0.000 / 0.000 | 0.000 / 0.000 | 0.000 / 0.000 | 0.000 / 0.000 |
| Attack / Attack-TCP-BYPass-V1 | 34,592 | 0.950 / 0.997 | 0.950 / 0.997 | 0.949 / 0.997 | 0.949 / 0.998 | 0.949 / 0.998 |
| Attack / Attack-TCP-Control | 1,436 | 0.102 / 0.341 | 0.102 / 0.341 | 0.099 / 0.344 | 0.198 / 0.355 | 0.093 / 0.358 |
| Attack / Attack-TCP-Flag-ACK | 2,671 | 0.223 / 0.629 | 0.223 / 0.629 | 0.223 / 0.629 | 0.219 / 0.661 | 0.222 / 0.656 |
| Attack / Attack-TCP-Flag-ACK-PSH | 1,871 | 0.003 / 0.214 | 0.003 / 0.214 | 0.003 / 0.214 | 0.001 / 0.250 | 0.005 / 0.161 |
| Attack / Attack-TCP-Flag-MIX | 1,854 | 0.064 / 0.398 | 0.064 / 0.398 | 0.064 / 0.399 | 0.076 / 0.319 | 0.065 / 0.316 |
| Attack / Attack-TCP-Flag-OSYN | 217 | 0.014 / 0.200 | 0.014 / 0.200 | 0.014 / 0.200 | 0.000 / 0.000 | 0.005 / 0.333 |
| Attack / Attack-TCP-Flag-OSYNP | 222 | 0.009 / 0.222 | 0.009 / 0.250 | 0.000 / 0.000 | 0.000 / 0.000 | 0.032 / 0.233 |
| Attack / Attack-TCP-Flag-RST-ACK | 361 | 0.335 / 0.818 | 0.335 / 0.818 | 0.335 / 0.871 | 0.319 / 0.885 | 0.316 / 0.927 |
| Attack / Attack-TCP-Flag-SYN | 1,961 | 0.036 / 0.310 | 0.036 / 0.310 | 0.036 / 0.310 | 0.064 / 0.264 | 0.050 / 0.286 |
| Attack / Attack-TCP-Flag-SYN-ACK | 2,051 | 0.131 / 0.412 | 0.131 / 0.412 | 0.131 / 0.412 | 0.028 / 0.432 | 0.136 / 0.379 |
| Attack / Attack-TCP-Flag-SYN-TFO | 908 | 0.698 / 0.851 | 0.698 / 0.851 | 0.703 / 0.846 | 0.729 / 0.802 | 0.731 / 0.798 |
| Attack / Attack-TCP-Flag-SYN-TIME | 340 | 0.029 / 0.714 | 0.029 / 0.714 | 0.029 / 0.667 | 0.018 / 0.500 | 0.021 / 0.875 |
| Attack / Attack-TCP-IGMP | 1,813 | 0.015 / 0.176 | 0.015 / 0.176 | 0.015 / 0.176 | 0.061 / 0.239 | 0.054 / 0.266 |
| Attack / Attack-TCP-SYN | 1,738 | 0.115 / 0.292 | 0.115 / 0.292 | 0.118 / 0.284 | 0.013 / 0.373 | 0.075 / 0.268 |
| Attack / Attack-TCP-Valid-SYN | 2,011 | 0.160 / 0.684 | 0.160 / 0.684 | 0.160 / 0.684 | 0.180 / 0.546 | 0.151 / 0.676 |
| Benign / Benign | 75,571 | 0.995 / 0.892 | 0.994 / 0.893 | 0.912 / 0.837 | 0.996 / 0.889 | 0.995 / 0.891 |
| Benign / Benign-Email-Receive | 349 | 0.266 / 0.886 | 0.255 / 0.899 | 0.206 / 0.947 | 0.261 / 0.958 | 0.261 / 0.910 |
| Benign / Benign-Email-Send | 484 | 0.525 / 0.640 | 0.525 / 0.640 | 0.498 / 0.064 | 0.335 / 0.953 | 0.521 / 0.656 |
| Benign / Benign-FTP | 121 | 0.413 / 0.581 | 0.413 / 0.581 | 0.273 / 0.717 | 0.347 / 0.488 | 0.413 / 0.481 |
| Benign / Benign-SSH | 746 | 0.702 / 0.817 | 0.702 / 0.815 | 0.705 / 0.682 | 0.677 / 0.846 | 0.677 / 0.824 |
| Benign / Benign-Systemic | 12,019 | 0.857 / 0.929 | 0.815 / 0.969 | 0.813 / 0.964 | 0.815 / 0.965 | 0.853 / 0.920 |
| Benign / Benign-Telnet | 1,192 | 0.435 / 0.691 | 0.422 / 0.700 | 0.247 / 0.739 | 0.290 / 0.767 | 0.401 / 0.675 |
| Benign / Benign-Web_Browsing_HTTP-S | 12,818 | 0.877 / 0.732 | 0.910 / 0.714 | 0.559 / 0.461 | 0.917 / 0.706 | 0.881 / 0.728 |
| Suspicious / Suspicious | 14,777 | 0.715 / 0.430 | 0.721 / 0.428 | 0.707 / 0.430 | 0.700 / 0.422 | 0.708 / 0.433 |

**mlp, random split, per class, leaked test rows** (recall / precision):

| class | support | leaky | +8y | zero | fixA | dropIAT |
|---|---:|---|---|---|---|---|
| Attack / Attack-Killall-v2 | 349 | 0.003 / 0.091 | 0.000 / 0.000 | 0.003 / 0.100 | 0.000 / 0.000 | 0.000 / 0.000 |
| Attack / Attack-Killer-TCP | 465 | 0.000 / 0.000 | 0.000 / 0.000 | 0.000 / 0.000 | 0.000 / 0.000 | 0.000 / 0.000 |
| Attack / Attack-TCP-BYPass-V1 | 33,209 | 0.988 / 0.999 | 0.988 / 0.999 | 0.988 / 0.999 | 0.988 / 0.999 | 0.988 / 0.999 |
| Attack / Attack-TCP-Control | 413 | 0.010 / 0.267 | 0.010 / 0.267 | 0.000 / 0.000 | 0.024 / 0.400 | 0.027 / 0.423 |
| Attack / Attack-TCP-Flag-ACK | 450 | 0.000 / 0.000 | 0.000 / 0.000 | 0.000 / 0.000 | 0.000 / 0.000 | 0.000 / 0.000 |
| Attack / Attack-TCP-Flag-ACK-PSH | 439 | 0.000 / 0.000 | 0.000 / 0.000 | 0.000 / 0.000 | 0.000 / 0.000 | 0.000 / 0.000 |
| Attack / Attack-TCP-Flag-MIX | 413 | 0.000 / 0.000 | 0.000 / 0.000 | 0.000 / 0.000 | 0.000 / 0.000 | 0.000 / 0.000 |
| Attack / Attack-TCP-Flag-OSYN | 189 | 0.000 / 0.000 | 0.000 / 0.000 | 0.000 / 0.000 | 0.000 / 0.000 | 0.000 / 0.000 |
| Attack / Attack-TCP-Flag-OSYNP | 183 | 0.011 / 0.250 | 0.011 / 0.286 | 0.000 / 0.000 | 0.000 / 0.000 | 0.038 / 0.269 |
| Attack / Attack-TCP-Flag-RST-ACK | 140 | 0.000 / 0.000 | 0.000 / 0.000 | 0.000 / 0.000 | 0.000 / 0.000 | 0.000 / 0.000 |
| Attack / Attack-TCP-Flag-SYN | 427 | 0.000 / 0.000 | 0.000 / 0.000 | 0.000 / 0.000 | 0.000 / 0.000 | 0.000 / 0.000 |
| Attack / Attack-TCP-Flag-SYN-ACK | 367 | 0.000 / 0.000 | 0.000 / 0.000 | 0.000 / 0.000 | 0.000 / 0.000 | 0.000 / 0.000 |
| Attack / Attack-TCP-Flag-SYN-TFO | 198 | 0.000 / 0.000 | 0.000 / 0.000 | 0.020 / 0.364 | 0.020 / 0.444 | 0.020 / 0.267 |
| Attack / Attack-TCP-Flag-SYN-TIME | 235 | 0.026 / 1.000 | 0.026 / 1.000 | 0.026 / 0.857 | 0.026 / 0.857 | 0.026 / 0.857 |
| Attack / Attack-TCP-IGMP | 408 | 0.000 / 0.000 | 0.000 / 0.000 | 0.000 / 0.000 | 0.000 / 0.000 | 0.000 / 0.000 |
| Attack / Attack-TCP-SYN | 363 | 0.000 / 0.000 | 0.000 / 0.000 | 0.014 / 0.135 | 0.000 / 0.000 | 0.000 / 0.000 |
| Attack / Attack-TCP-Valid-SYN | 399 | 0.000 / 0.000 | 0.000 / 0.000 | 0.000 / 0.000 | 0.000 / 0.000 | 0.000 / 0.000 |
| Benign / Benign | 61,174 | 0.995 / 0.877 | 0.993 / 0.879 | 0.892 / 0.810 | 0.996 / 0.876 | 0.995 / 0.876 |
| Benign / Benign-Email-Receive | 236 | 0.089 / 0.724 | 0.072 / 0.739 | 0.000 / 0.000 | 0.076 / 1.000 | 0.085 / 1.000 |
| Benign / Benign-Email-Send | 285 | 0.319 / 0.401 | 0.319 / 0.401 | 0.274 / 0.022 | 0.000 / 0.000 | 0.319 / 0.427 |
| Benign / Benign-FTP | 72 | 0.250 / 0.419 | 0.250 / 0.419 | 0.014 / 0.333 | 0.181 / 0.265 | 0.236 / 0.283 |
| Benign / Benign-SSH | 377 | 0.615 / 0.768 | 0.615 / 0.763 | 0.621 / 0.542 | 0.618 / 0.777 | 0.613 / 0.773 |
| Benign / Benign-Systemic | 2,004 | 0.371 / 0.548 | 0.119 / 0.623 | 0.102 / 0.519 | 0.118 / 0.622 | 0.378 / 0.551 |
| Benign / Benign-Telnet | 992 | 0.387 / 0.666 | 0.371 / 0.675 | 0.160 / 0.710 | 0.327 / 0.779 | 0.381 / 0.667 |
| Benign / Benign-Web_Browsing_HTTP-S | 6,974 | 0.800 / 0.604 | 0.861 / 0.588 | 0.215 / 0.159 | 0.870 / 0.579 | 0.805 / 0.602 |
| Suspicious / Suspicious | 3,883 | 0.054 / 0.344 | 0.075 / 0.318 | 0.023 / 0.267 | 0.049 / 0.350 | 0.035 / 0.349 |

**mlp, temporal split, per class, all test rows** (recall / precision):

| class | support | leaky | +8y | zero | fixA | dropIAT |
|---|---:|---|---|---|---|---|
| Attack / Attack-Killall-v2 | 1,508 | 0.001 / 0.023 | 0.001 / 0.023 | 0.001 / 0.023 | 0.003 / 0.074 | 0.001 / 0.038 |
| Attack / Attack-Killer-TCP | 1,564 | 0.000 / 0.000 | 0.000 / 0.000 | 0.000 / 0.000 | 0.000 / 0.000 | 0.000 / 0.000 |
| Attack / Attack-TCP-BYPass-V1 | 34,592 | 0.943 / 0.998 | 0.943 / 0.998 | 0.944 / 0.989 | 0.943 / 0.998 | 0.943 / 0.998 |
| Attack / Attack-TCP-Control | 1,436 | 0.038 / 0.385 | 0.038 / 0.385 | 0.038 / 0.382 | 0.056 / 0.286 | 0.070 / 0.351 |
| Attack / Attack-TCP-Flag-ACK | 2,671 | 0.325 / 0.888 | 0.325 / 0.888 | 0.325 / 0.888 | 0.418 / 0.472 | 0.351 / 0.677 |
| Attack / Attack-TCP-Flag-ACK-PSH | 1,870 | 0.002 / 0.014 | 0.002 / 0.014 | 0.002 / 0.014 | 0.001 / 0.054 | 0.011 / 0.036 |
| Attack / Attack-TCP-Flag-MIX | 1,854 | 0.183 / 0.163 | 0.183 / 0.163 | 0.183 / 0.163 | 0.182 / 0.165 | 0.112 / 0.214 |
| Attack / Attack-TCP-Flag-OSYN | 217 | 0.000 / 0.000 | 0.000 / 0.000 | 0.000 / 0.000 | 0.000 / 0.000 | 0.000 / 0.000 |
| Attack / Attack-TCP-Flag-OSYNP | 222 | 0.000 / 0.000 | 0.000 / 0.000 | 0.000 / 0.000 | 0.000 / 0.000 | 0.000 / 0.000 |
| Attack / Attack-TCP-Flag-RST-ACK | 361 | 0.000 / 0.000 | 0.000 / 0.000 | 0.000 / 0.000 | 0.000 / 0.000 | 0.000 / 0.000 |
| Attack / Attack-TCP-Flag-SYN | 1,961 | 0.014 / 0.229 | 0.014 / 0.229 | 0.014 / 0.229 | 0.025 / 0.195 | 0.011 / 0.179 |
| Attack / Attack-TCP-Flag-SYN-ACK | 2,051 | 0.051 / 0.416 | 0.051 / 0.416 | 0.051 / 0.416 | 0.000 / 0.000 | 0.024 / 0.533 |
| Attack / Attack-TCP-Flag-SYN-TFO | 908 | 0.765 / 0.632 | 0.765 / 0.632 | 0.765 / 0.632 | 0.769 / 0.566 | 0.761 / 0.708 |
| Attack / Attack-TCP-Flag-SYN-TIME | 340 | 0.003 / 0.071 | 0.003 / 0.071 | 0.003 / 0.071 | 0.000 / 0.000 | 0.003 / 0.040 |
| Attack / Attack-TCP-IGMP | 1,813 | 0.001 / 0.077 | 0.001 / 0.091 | 0.001 / 0.125 | 0.002 / 0.143 | 0.010 / 0.352 |
| Attack / Attack-TCP-SYN | 1,738 | 0.007 / 0.067 | 0.007 / 0.067 | 0.007 / 0.067 | 0.007 / 0.077 | 0.005 / 0.048 |
| Attack / Attack-TCP-Valid-SYN | 2,011 | 0.179 / 0.729 | 0.179 / 0.729 | 0.179 / 0.729 | 0.178 / 0.785 | 0.178 / 0.803 |
| Benign / Benign | 75,571 | 0.994 / 0.890 | 0.994 / 0.890 | 0.921 / 0.846 | 0.994 / 0.887 | 0.994 / 0.890 |
| Benign / Benign-Email-Receive | 348 | 0.362 / 0.689 | 0.348 / 0.590 | 0.193 / 0.848 | 0.270 / 0.870 | 0.368 / 0.790 |
| Benign / Benign-Email-Send | 485 | 0.478 / 0.844 | 0.400 / 0.829 | 0.307 / 0.993 | 0.480 / 0.685 | 0.466 / 0.853 |
| Benign / Benign-FTP | 120 | 0.275 / 0.311 | 0.275 / 0.311 | 0.108 / 0.167 | 0.292 / 0.084 | 0.342 / 0.109 |
| Benign / Benign-SSH | 745 | 0.223 / 0.417 | 0.219 / 0.417 | 0.215 / 0.413 | 0.216 / 0.506 | 0.242 / 0.405 |
| Benign / Benign-Systemic | 12,019 | 0.888 / 0.897 | 0.888 / 0.897 | 0.886 / 0.896 | 0.885 / 0.904 | 0.890 / 0.917 |
| Benign / Benign-Telnet | 1,192 | 0.467 / 0.754 | 0.466 / 0.757 | 0.327 / 0.777 | 0.329 / 0.798 | 0.453 / 0.762 |
| Benign / Benign-Web_Browsing_HTTP-S | 12,818 | 0.823 / 0.723 | 0.743 / 0.911 | 0.794 / 0.582 | 0.818 / 0.715 | 0.816 / 0.716 |
| Suspicious / Suspicious | 14,776 | 0.617 / 0.378 | 0.658 / 0.344 | 0.608 / 0.380 | 0.555 / 0.358 | 0.667 / 0.399 |

**mlp, temporal split, per class, leaked test rows** (recall / precision):

| class | support | leaky | +8y | zero | fixA | dropIAT |
|---|---:|---|---|---|---|---|
| Attack / Attack-Killall-v2 | 342 | 0.000 / 0.000 | 0.000 / 0.000 | 0.000 / 0.000 | 0.000 / 0.000 | 0.000 / 0.000 |
| Attack / Attack-Killer-TCP | 373 | 0.000 / 0.000 | 0.000 / 0.000 | 0.000 / 0.000 | 0.000 / 0.000 | 0.000 / 0.000 |
| Attack / Attack-TCP-BYPass-V1 | 33,122 | 0.985 / 0.999 | 0.985 / 0.999 | 0.985 / 0.990 | 0.985 / 0.999 | 0.985 / 0.999 |
| Attack / Attack-TCP-Control | 341 | 0.000 / 0.000 | 0.000 / 0.000 | 0.000 / 0.000 | 0.000 / 0.000 | 0.012 / 0.444 |
| Attack / Attack-TCP-Flag-ACK | 374 | 0.000 / 0.000 | 0.000 / 0.000 | 0.000 / 0.000 | 0.000 / 0.000 | 0.000 / 0.000 |
| Attack / Attack-TCP-Flag-ACK-PSH | 406 | 0.000 / 0.000 | 0.000 / 0.000 | 0.000 / 0.000 | 0.000 / 0.000 | 0.000 / 0.000 |
| Attack / Attack-TCP-Flag-MIX | 321 | 0.000 / 0.000 | 0.000 / 0.000 | 0.000 / 0.000 | 0.000 / 0.000 | 0.000 / 0.000 |
| Attack / Attack-TCP-Flag-OSYN | 163 | 0.000 / 0.000 | 0.000 / 0.000 | 0.000 / 0.000 | 0.000 / 0.000 | 0.000 / 0.000 |
| Attack / Attack-TCP-Flag-OSYNP | 196 | 0.000 / 0.000 | 0.000 / 0.000 | 0.000 / 0.000 | 0.000 / 0.000 | 0.000 / 0.000 |
| Attack / Attack-TCP-Flag-RST-ACK | 60 | 0.000 / 0.000 | 0.000 / 0.000 | 0.000 / 0.000 | 0.000 / 0.000 | 0.000 / 0.000 |
| Attack / Attack-TCP-Flag-SYN | 498 | 0.000 / 0.000 | 0.000 / 0.000 | 0.000 / 0.000 | 0.002 / 0.100 | 0.000 / 0.000 |
| Attack / Attack-TCP-Flag-SYN-ACK | 494 | 0.000 / 0.000 | 0.000 / 0.000 | 0.000 / 0.000 | 0.000 / 0.000 | 0.000 / 0.000 |
| Attack / Attack-TCP-Flag-SYN-TFO | 184 | 0.000 / 0.000 | 0.000 / 0.000 | 0.000 / 0.000 | 0.000 / 0.000 | 0.000 / 0.000 |
| Attack / Attack-TCP-Flag-SYN-TIME | 183 | 0.000 / 0.000 | 0.000 / 0.000 | 0.000 / 0.000 | 0.000 / 0.000 | 0.000 / 0.000 |
| Attack / Attack-TCP-IGMP | 421 | 0.000 / 0.000 | 0.000 / 0.000 | 0.000 / 0.000 | 0.000 / 0.000 | 0.000 / 0.000 |
| Attack / Attack-TCP-SYN | 388 | 0.000 / 0.000 | 0.000 / 0.000 | 0.000 / 0.000 | 0.000 / 0.000 | 0.000 / 0.000 |
| Attack / Attack-TCP-Valid-SYN | 378 | 0.000 / 0.000 | 0.000 / 0.000 | 0.000 / 0.000 | 0.000 / 0.000 | 0.000 / 0.000 |
| Benign / Benign | 61,728 | 0.995 / 0.877 | 0.995 / 0.877 | 0.905 / 0.824 | 0.994 / 0.875 | 0.996 / 0.877 |
| Benign / Benign-Email-Receive | 236 | 0.250 / 0.567 | 0.229 / 0.429 | 0.000 / 0.000 | 0.102 / 0.750 | 0.250 / 0.656 |
| Benign / Benign-Email-Send | 293 | 0.283 / 0.664 | 0.154 / 0.536 | 0.000 / 0.000 | 0.287 / 0.462 | 0.263 / 0.733 |
| Benign / Benign-FTP | 78 | 0.256 / 0.308 | 0.256 / 0.308 | 0.000 / 0.000 | 0.256 / 0.072 | 0.256 / 0.080 |
| Benign / Benign-SSH | 344 | 0.140 / 0.213 | 0.131 / 0.206 | 0.122 / 0.196 | 0.110 / 0.259 | 0.116 / 0.220 |
| Benign / Benign-Systemic | 1,889 | 0.415 / 0.536 | 0.416 / 0.534 | 0.400 / 0.522 | 0.412 / 0.522 | 0.425 / 0.585 |
| Benign / Benign-Telnet | 1,010 | 0.431 / 0.759 | 0.430 / 0.764 | 0.265 / 0.798 | 0.349 / 0.863 | 0.430 / 0.755 |
| Benign / Benign-Web_Browsing_HTTP-S | 7,057 | 0.730 / 0.587 | 0.585 / 0.891 | 0.677 / 0.410 | 0.723 / 0.578 | 0.721 / 0.576 |
| Suspicious / Suspicious | 3,894 | 0.039 / 0.208 | 0.195 / 0.156 | 0.006 / 0.085 | 0.032 / 0.205 | 0.032 / 0.215 |

**knn, random split, per class, all test rows** (recall / precision):

| class | support | leaky | +8y | zero | fixA | dropIAT |
|---|---:|---|---|---|---|---|
| Attack / Attack-Killall-v2 | 1,508 | 0.223 / 0.237 | 0.103 / 0.136 | 0.103 / 0.135 | 0.107 / 0.128 | 0.107 / 0.127 |
| Attack / Attack-Killer-TCP | 1,563 | 0.260 / 0.275 | 0.066 / 0.098 | 0.066 / 0.098 | 0.067 / 0.075 | 0.069 / 0.076 |
| Attack / Attack-TCP-BYPass-V1 | 34,592 | 0.959 / 0.966 | 0.005 / 0.145 | 0.953 / 0.967 | 0.954 / 0.951 | 0.954 / 0.951 |
| Attack / Attack-TCP-Control | 1,436 | 0.295 / 0.342 | 0.144 / 0.226 | 0.142 / 0.229 | 0.148 / 0.223 | 0.148 / 0.221 |
| Attack / Attack-TCP-Flag-ACK | 2,671 | 0.398 / 0.422 | 0.277 / 0.349 | 0.277 / 0.353 | 0.276 / 0.335 | 0.280 / 0.337 |
| Attack / Attack-TCP-Flag-ACK-PSH | 1,871 | 0.255 / 0.292 | 0.084 / 0.127 | 0.087 / 0.126 | 0.084 / 0.126 | 0.083 / 0.125 |
| Attack / Attack-TCP-Flag-MIX | 1,854 | 0.312 / 0.359 | 0.146 / 0.227 | 0.145 / 0.227 | 0.142 / 0.208 | 0.141 / 0.207 |
| Attack / Attack-TCP-Flag-OSYN | 217 | 0.378 / 0.509 | 0.014 / 0.097 | 0.014 / 0.158 | 0.018 / 0.074 | 0.009 / 0.040 |
| Attack / Attack-TCP-Flag-OSYNP | 222 | 0.419 / 0.487 | 0.072 / 0.239 | 0.050 / 0.367 | 0.099 / 0.250 | 0.081 / 0.198 |
| Attack / Attack-TCP-Flag-RST-ACK | 361 | 0.604 / 0.659 | 0.463 / 0.749 | 0.460 / 0.728 | 0.465 / 0.718 | 0.460 / 0.716 |
| Attack / Attack-TCP-Flag-SYN | 1,961 | 0.227 / 0.263 | 0.110 / 0.157 | 0.111 / 0.158 | 0.111 / 0.153 | 0.113 / 0.156 |
| Attack / Attack-TCP-Flag-SYN-ACK | 2,051 | 0.255 / 0.306 | 0.133 / 0.194 | 0.134 / 0.200 | 0.133 / 0.195 | 0.133 / 0.197 |
| Attack / Attack-TCP-Flag-SYN-TFO | 908 | 0.784 / 0.781 | 0.694 / 0.845 | 0.694 / 0.667 | 0.698 / 0.840 | 0.693 / 0.836 |
| Attack / Attack-TCP-Flag-SYN-TIME | 340 | 0.332 / 0.511 | 0.085 / 0.330 | 0.079 / 0.500 | 0.085 / 0.330 | 0.082 / 0.292 |
| Attack / Attack-TCP-IGMP | 1,813 | 0.221 / 0.232 | 0.100 / 0.129 | 0.104 / 0.130 | 0.104 / 0.120 | 0.100 / 0.117 |
| Attack / Attack-TCP-SYN | 1,738 | 0.283 / 0.306 | 0.152 / 0.209 | 0.154 / 0.207 | 0.156 / 0.194 | 0.157 / 0.191 |
| Attack / Attack-TCP-Valid-SYN | 2,011 | 0.360 / 0.345 | 0.212 / 0.246 | 0.212 / 0.246 | 0.352 / 0.025 | 0.351 / 0.025 |
| Benign / Benign | 75,571 | 0.969 / 0.939 | 0.617 / 0.925 | 0.828 / 0.849 | 0.639 / 0.918 | 0.639 / 0.918 |
| Benign / Benign-Email-Receive | 349 | 0.401 / 0.651 | 0.384 / 0.713 | 0.209 / 0.948 | 0.401 / 0.819 | 0.401 / 0.828 |
| Benign / Benign-Email-Send | 484 | 0.655 / 0.766 | 0.678 / 0.087 | 0.339 / 0.932 | 0.682 / 0.356 | 0.682 / 0.357 |
| Benign / Benign-FTP | 121 | 0.579 / 0.700 | 0.339 / 0.695 | 0.339 / 0.695 | 0.339 / 0.651 | 0.339 / 0.661 |
| Benign / Benign-SSH | 746 | 0.749 / 0.807 | 0.413 / 0.780 | 0.708 / 0.760 | 0.723 / 0.824 | 0.717 / 0.822 |
| Benign / Benign-Systemic | 12,019 | 0.876 / 0.926 | 0.822 / 0.958 | 0.819 / 0.944 | 0.864 / 0.915 | 0.865 / 0.919 |
| Benign / Benign-Telnet | 1,192 | 0.449 / 0.659 | 0.409 / 0.777 | 0.391 / 0.740 | 0.435 / 0.733 | 0.432 / 0.730 |
| Benign / Benign-Web_Browsing_HTTP-S | 12,818 | 0.902 / 0.887 | 0.559 / 0.475 | 0.830 / 0.396 | 0.783 / 0.563 | 0.783 / 0.563 |
| Suspicious / Suspicious | 14,777 | 0.687 / 0.647 | 0.704 / 0.135 | 0.523 / 0.628 | 0.532 / 0.616 | 0.531 / 0.617 |

**knn, random split, per class, leaked test rows** (recall / precision):

| class | support | leaky | +8y | zero | fixA | dropIAT |
|---|---:|---|---|---|---|---|
| Attack / Attack-Killall-v2 | 349 | 0.527 / 0.646 | 0.009 / 0.231 | 0.009 / 0.188 | 0.023 / 0.060 | 0.023 / 0.059 |
| Attack / Attack-Killer-TCP | 465 | 0.652 / 0.701 | 0.000 / 0.000 | 0.000 / 0.000 | 0.009 / 0.011 | 0.009 / 0.011 |
| Attack / Attack-TCP-BYPass-V1 | 33,209 | 0.994 / 0.997 | 0.000 / 0.429 | 0.988 / 0.999 | 0.988 / 0.981 | 0.988 / 0.981 |
| Attack / Attack-TCP-Control | 413 | 0.535 / 0.626 | 0.012 / 0.161 | 0.005 / 0.286 | 0.024 / 0.152 | 0.024 / 0.149 |
| Attack / Attack-TCP-Flag-ACK | 450 | 0.718 / 0.749 | 0.000 / 0.000 | 0.000 / 0.000 | 0.000 / 0.000 | 0.000 / 0.000 |
| Attack / Attack-TCP-Flag-ACK-PSH | 439 | 0.733 / 0.767 | 0.007 / 0.097 | 0.016 / 0.099 | 0.005 / 0.039 | 0.005 / 0.039 |
| Attack / Attack-TCP-Flag-MIX | 413 | 0.748 / 0.720 | 0.002 / 0.100 | 0.000 / 0.000 | 0.002 / 0.011 | 0.002 / 0.011 |
| Attack / Attack-TCP-Flag-OSYN | 189 | 0.418 / 0.549 | 0.000 / 0.000 | 0.000 / 0.000 | 0.005 / 0.027 | 0.005 / 0.027 |
| Attack / Attack-TCP-Flag-OSYNP | 183 | 0.454 / 0.497 | 0.033 / 0.140 | 0.005 / 0.167 | 0.060 / 0.190 | 0.060 / 0.190 |
| Attack / Attack-TCP-Flag-RST-ACK | 140 | 0.386 / 0.462 | 0.021 / 0.333 | 0.014 / 0.143 | 0.014 / 0.125 | 0.014 / 0.125 |
| Attack / Attack-TCP-Flag-SYN | 427 | 0.539 / 0.703 | 0.000 / 0.000 | 0.002 / 0.100 | 0.014 / 0.092 | 0.014 / 0.091 |
| Attack / Attack-TCP-Flag-SYN-ACK | 367 | 0.708 / 0.714 | 0.027 / 0.161 | 0.035 / 0.394 | 0.030 / 0.297 | 0.030 / 0.297 |
| Attack / Attack-TCP-Flag-SYN-TFO | 198 | 0.419 / 0.474 | 0.005 / 0.111 | 0.005 / 0.005 | 0.015 / 0.158 | 0.015 / 0.158 |
| Attack / Attack-TCP-Flag-SYN-TIME | 235 | 0.400 / 0.537 | 0.043 / 0.238 | 0.034 / 1.000 | 0.043 / 0.208 | 0.043 / 0.200 |
| Attack / Attack-TCP-IGMP | 408 | 0.544 / 0.659 | 0.007 / 0.158 | 0.025 / 0.159 | 0.027 / 0.061 | 0.027 / 0.062 |
| Attack / Attack-TCP-SYN | 363 | 0.623 / 0.659 | 0.000 / 0.000 | 0.008 / 0.097 | 0.017 / 0.044 | 0.017 / 0.044 |
| Attack / Attack-TCP-Valid-SYN | 399 | 0.747 / 0.805 | 0.000 / 0.000 | 0.000 / 0.000 | 0.704 / 0.011 | 0.704 / 0.011 |
| Benign / Benign | 61,174 | 0.965 / 0.934 | 0.530 / 0.909 | 0.791 / 0.820 | 0.557 / 0.900 | 0.557 / 0.900 |
| Benign / Benign-Email-Receive | 236 | 0.284 / 0.486 | 0.258 / 0.550 | 0.000 / 0.000 | 0.284 / 0.713 | 0.284 / 0.728 |
| Benign / Benign-Email-Send | 285 | 0.537 / 0.640 | 0.575 / 0.046 | 0.000 / 0.000 | 0.582 / 0.221 | 0.582 / 0.221 |
| Benign / Benign-FTP | 72 | 0.444 / 0.696 | 0.042 / 0.600 | 0.042 / 0.600 | 0.042 / 0.333 | 0.042 / 0.333 |
| Benign / Benign-SSH | 377 | 0.716 / 0.792 | 0.050 / 0.442 | 0.634 / 0.697 | 0.660 / 0.836 | 0.660 / 0.836 |
| Benign / Benign-Systemic | 2,004 | 0.459 / 0.620 | 0.130 / 0.627 | 0.115 / 0.436 | 0.384 / 0.533 | 0.385 / 0.537 |
| Benign / Benign-Telnet | 992 | 0.410 / 0.627 | 0.362 / 0.774 | 0.341 / 0.724 | 0.390 / 0.715 | 0.390 / 0.715 |
| Benign / Benign-Web_Browsing_HTTP-S | 6,974 | 0.854 / 0.847 | 0.223 / 0.172 | 0.721 / 0.242 | 0.635 / 0.375 | 0.635 / 0.375 |
| Suspicious / Suspicious | 3,883 | 0.645 / 0.705 | 0.712 / 0.043 | 0.023 / 0.495 | 0.057 / 0.360 | 0.057 / 0.361 |

**knn, temporal split, per class, all test rows** (recall / precision):

| class | support | leaky | +8y | zero | fixA | dropIAT |
|---|---:|---|---|---|---|---|
| Attack / Attack-Killall-v2 | 1,508 | 0.087 / 0.110 | 0.070 / 0.098 | 0.070 / 0.096 | 0.070 / 0.092 | 0.071 / 0.091 |
| Attack / Attack-Killer-TCP | 1,564 | 0.096 / 0.140 | 0.066 / 0.108 | 0.065 / 0.106 | 0.065 / 0.092 | 0.069 / 0.098 |
| Attack / Attack-TCP-BYPass-V1 | 34,592 | 0.950 / 0.969 | 0.004 / 0.111 | 0.946 / 0.970 | 0.946 / 0.961 | 0.947 / 0.961 |
| Attack / Attack-TCP-Control | 1,436 | 0.148 / 0.241 | 0.120 / 0.208 | 0.118 / 0.206 | 0.117 / 0.200 | 0.114 / 0.193 |
| Attack / Attack-TCP-Flag-ACK | 2,671 | 0.312 / 0.309 | 0.262 / 0.366 | 0.261 / 0.370 | 0.262 / 0.360 | 0.263 / 0.360 |
| Attack / Attack-TCP-Flag-ACK-PSH | 1,870 | 0.176 / 0.117 | 0.058 / 0.072 | 0.059 / 0.072 | 0.058 / 0.072 | 0.056 / 0.069 |
| Attack / Attack-TCP-Flag-MIX | 1,854 | 0.248 / 0.175 | 0.196 / 0.159 | 0.196 / 0.160 | 0.196 / 0.156 | 0.180 / 0.152 |
| Attack / Attack-TCP-Flag-OSYN | 217 | 0.065 / 0.292 | 0.009 / 0.049 | 0.009 / 0.182 | 0.014 / 0.120 | 0.005 / 0.045 |
| Attack / Attack-TCP-Flag-OSYNP | 222 | 0.086 / 0.235 | 0.000 / 0.000 | 0.000 / 0.000 | 0.009 / 0.049 | 0.009 / 0.045 |
| Attack / Attack-TCP-Flag-RST-ACK | 361 | 0.133 / 0.558 | 0.078 / 0.475 | 0.078 / 0.609 | 0.078 / 0.418 | 0.075 / 0.409 |
| Attack / Attack-TCP-Flag-SYN | 1,961 | 0.139 / 0.131 | 0.069 / 0.098 | 0.068 / 0.096 | 0.070 / 0.098 | 0.067 / 0.086 |
| Attack / Attack-TCP-Flag-SYN-ACK | 2,051 | 0.181 / 0.137 | 0.111 / 0.137 | 0.110 / 0.137 | 0.110 / 0.135 | 0.107 / 0.135 |
| Attack / Attack-TCP-Flag-SYN-TFO | 908 | 0.818 / 0.691 | 0.754 / 0.688 | 0.756 / 0.554 | 0.754 / 0.677 | 0.758 / 0.679 |
| Attack / Attack-TCP-Flag-SYN-TIME | 340 | 0.074 / 0.203 | 0.000 / 0.000 | 0.000 / 0.000 | 0.000 / 0.000 | 0.000 / 0.000 |
| Attack / Attack-TCP-IGMP | 1,813 | 0.096 / 0.142 | 0.062 / 0.104 | 0.065 / 0.107 | 0.067 / 0.101 | 0.067 / 0.101 |
| Attack / Attack-TCP-SYN | 1,738 | 0.086 / 0.161 | 0.058 / 0.126 | 0.058 / 0.126 | 0.059 / 0.118 | 0.058 / 0.117 |
| Attack / Attack-TCP-Valid-SYN | 2,011 | 0.226 / 0.283 | 0.200 / 0.261 | 0.200 / 0.261 | 0.323 / 0.022 | 0.324 / 0.022 |
| Benign / Benign | 75,571 | 0.628 / 0.919 | 0.515 / 0.937 | 0.841 / 0.850 | 0.638 / 0.913 | 0.638 / 0.913 |
| Benign / Benign-Email-Receive | 348 | 0.371 / 0.620 | 0.368 / 0.719 | 0.195 / 0.782 | 0.371 / 0.759 | 0.371 / 0.772 |
| Benign / Benign-Email-Send | 485 | 0.505 / 0.503 | 0.466 / 0.970 | 0.309 / 0.980 | 0.616 / 0.349 | 0.614 / 0.347 |
| Benign / Benign-FTP | 120 | 0.433 / 0.211 | 0.158 / 0.099 | 0.158 / 0.101 | 0.158 / 0.096 | 0.150 / 0.090 |
| Benign / Benign-SSH | 745 | 0.231 / 0.577 | 0.215 / 0.597 | 0.263 / 0.484 | 0.232 / 0.513 | 0.219 / 0.513 |
| Benign / Benign-Systemic | 12,019 | 0.920 / 0.300 | 0.837 / 0.925 | 0.834 / 0.920 | 0.886 / 0.891 | 0.886 / 0.902 |
| Benign / Benign-Telnet | 1,192 | 0.479 / 0.724 | 0.430 / 0.777 | 0.378 / 0.774 | 0.475 / 0.713 | 0.479 / 0.715 |
| Benign / Benign-Web_Browsing_HTTP-S | 12,818 | 0.624 / 0.800 | 0.522 / 0.499 | 0.798 / 0.406 | 0.755 / 0.577 | 0.754 / 0.577 |
| Suspicious / Suspicious | 14,776 | 0.657 / 0.498 | 0.669 / 0.109 | 0.452 / 0.528 | 0.458 / 0.525 | 0.463 / 0.527 |

**knn, temporal split, per class, leaked test rows** (recall / precision):

| class | support | leaky | +8y | zero | fixA | dropIAT |
|---|---:|---|---|---|---|---|
| Attack / Attack-Killall-v2 | 342 | 0.076 / 0.210 | 0.000 / 0.000 | 0.000 / 0.000 | 0.009 / 0.027 | 0.009 / 0.027 |
| Attack / Attack-Killer-TCP | 373 | 0.129 / 0.381 | 0.003 / 0.167 | 0.000 / 0.000 | 0.005 / 0.012 | 0.005 / 0.012 |
| Attack / Attack-TCP-BYPass-V1 | 33,122 | 0.988 / 0.998 | 0.000 / 0.294 | 0.985 / 0.998 | 0.985 / 0.989 | 0.985 / 0.989 |
| Attack / Attack-TCP-Control | 341 | 0.126 / 0.672 | 0.006 / 0.250 | 0.000 / 0.000 | 0.003 / 0.036 | 0.003 / 0.036 |
| Attack / Attack-TCP-Flag-ACK | 374 | 0.364 / 0.167 | 0.005 / 0.065 | 0.000 / 0.000 | 0.003 / 0.018 | 0.003 / 0.018 |
| Attack / Attack-TCP-Flag-ACK-PSH | 406 | 0.547 / 0.167 | 0.002 / 0.033 | 0.010 / 0.066 | 0.002 / 0.020 | 0.002 / 0.020 |
| Attack / Attack-TCP-Flag-MIX | 321 | 0.302 / 0.261 | 0.003 / 0.025 | 0.000 / 0.000 | 0.000 / 0.000 | 0.000 / 0.000 |
| Attack / Attack-TCP-Flag-OSYN | 163 | 0.074 / 0.308 | 0.000 / 0.000 | 0.000 / 0.000 | 0.000 / 0.000 | 0.000 / 0.000 |
| Attack / Attack-TCP-Flag-OSYNP | 196 | 0.097 / 0.275 | 0.000 / 0.000 | 0.000 / 0.000 | 0.005 / 0.032 | 0.005 / 0.032 |
| Attack / Attack-TCP-Flag-RST-ACK | 60 | 0.333 / 0.455 | 0.000 / 0.000 | 0.000 / 0.000 | 0.000 / 0.000 | 0.000 / 0.000 |
| Attack / Attack-TCP-Flag-SYN | 498 | 0.277 / 0.201 | 0.004 / 0.200 | 0.000 / 0.000 | 0.004 / 0.074 | 0.004 / 0.069 |
| Attack / Attack-TCP-Flag-SYN-ACK | 494 | 0.298 / 0.136 | 0.004 / 0.087 | 0.000 / 0.000 | 0.000 / 0.000 | 0.000 / 0.000 |
| Attack / Attack-TCP-Flag-SYN-TFO | 184 | 0.321 / 0.686 | 0.005 / 0.200 | 0.011 / 0.008 | 0.011 / 0.091 | 0.011 / 0.100 |
| Attack / Attack-TCP-Flag-SYN-TIME | 183 | 0.137 / 0.260 | 0.000 / 0.000 | 0.000 / 0.000 | 0.000 / 0.000 | 0.000 / 0.000 |
| Attack / Attack-TCP-IGMP | 421 | 0.145 / 0.357 | 0.000 / 0.000 | 0.010 / 0.091 | 0.007 / 0.020 | 0.005 / 0.014 |
| Attack / Attack-TCP-SYN | 388 | 0.126 / 0.355 | 0.000 / 0.000 | 0.000 / 0.000 | 0.000 / 0.000 | 0.000 / 0.000 |
| Attack / Attack-TCP-Valid-SYN | 378 | 0.138 / 0.712 | 0.000 / 0.000 | 0.000 / 0.000 | 0.664 / 0.009 | 0.664 / 0.009 |
| Benign / Benign | 61,728 | 0.548 / 0.904 | 0.410 / 0.927 | 0.809 / 0.824 | 0.560 / 0.896 | 0.560 / 0.896 |
| Benign / Benign-Email-Receive | 236 | 0.258 / 0.496 | 0.254 / 0.645 | 0.000 / 0.000 | 0.258 / 0.726 | 0.258 / 0.762 |
| Benign / Benign-Email-Send | 293 | 0.324 / 0.284 | 0.259 / 0.950 | 0.000 / 0.000 | 0.509 / 0.212 | 0.509 / 0.212 |
| Benign / Benign-FTP | 78 | 0.436 / 0.181 | 0.013 / 0.008 | 0.013 / 0.008 | 0.013 / 0.007 | 0.013 / 0.007 |
| Benign / Benign-SSH | 344 | 0.084 / 0.319 | 0.049 / 0.279 | 0.154 / 0.268 | 0.081 / 0.230 | 0.078 / 0.223 |
| Benign / Benign-Systemic | 1,889 | 0.632 / 0.045 | 0.102 / 0.474 | 0.083 / 0.374 | 0.418 / 0.542 | 0.417 / 0.543 |
| Benign / Benign-Telnet | 1,010 | 0.447 / 0.730 | 0.388 / 0.803 | 0.328 / 0.803 | 0.442 / 0.715 | 0.446 / 0.725 |
| Benign / Benign-Web_Browsing_HTTP-S | 7,057 | 0.372 / 0.627 | 0.186 / 0.173 | 0.689 / 0.250 | 0.610 / 0.392 | 0.610 / 0.392 |
| Suspicious / Suspicious | 3,894 | 0.790 / 0.424 | 0.835 / 0.042 | 0.015 / 0.137 | 0.037 / 0.219 | 0.037 / 0.221 |
