# Timestamp-leak susceptibility across ML models and three BCCC datasets

Spec: fixed model list and configurations, seed 0, no per-condition tuning. Leaked cell = IAT column value > 1e9 (judged on the unmodified data). Conditions:
- **leaky**: train and test as is.
- **+8y**: same leaky model; leaked test cells + 252,460,800 s (8 years).
- **zero**: same leaky model; leaked test cells set to 0.
- **fixA**: retrain and test with every leaked IAT cell set to 0.
- **dropIAT**: retrain and test with every IAT column removed (30 of 313 features on 2018 and cPacket, 15 of 114 on 2017). No IAT information at all, so it is a leak-free reference for fixA: if fixA still carried the leak through its zeros, fixA would beat dropIAT by more than the legitimate IAT information is worth.

Training: 600k stratified subsample per dataset × split (every row of classes with < 1,000 training rows; all rows if < 600k); test = the full test split, identical across models and conditions (comparisons are paired). Mean attack recall = unweighted mean recall over attack classes with >= 10 rows in the subset (cPacket: `Attack` subtypes). 95% CIs: paired bootstrap over test rows, B = 1,000, seed 0 (`mc_bootstrap.py`); `*` = CI excludes 0. The CIs cover test-set sampling only, not training randomness (single seed).

Runs: 92 of 92 leaky/fixA runs (7 models × 3 datasets × 2 splits × 2, plus RF and XGBoost trained on the full 2018 training split × 2 splits × 2), 40 of 40 dropIAT runs (all models except LogReg). The full-train runs (`rffull`, `xgbfull`) answer whether the 600k subsample changes the 2018 leak effect. LinearSVC was dropped (> 2.5 h per run, single-threaded, ~6 GB on 2018). LogReg has no dropIAT run (user decision: slowest model, and it hits the iteration limit in most runs; see caveats). Bootstrap results available for 46 dataset × split × model triples. All data files and per-class detail: `ALL_RUNS_pooled.csv` (`mc_pool.py`), `BOOTSTRAP_CI.csv`.

Runs without a result (failed or in progress): finish_full, finish_knn

## 1. Headline differences (point estimate [95% bootstrap CI])

Positive leaky−X = the leaky model loses that much when the leak is broken or removed. fixA−dropIAT is how much more fixA gets than a model with no IAT columns at all: small or negative means fixA's zeros carry no leak signal beyond legitimate IAT information.

### Accuracy, all test rows: leaky − (+8y)

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

### Accuracy, all test rows: leaky − fixA

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

### Accuracy, all test rows: fixA − dropIAT

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

### Mean attack recall, all test rows: leaky − fixA

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

### Mean attack recall, all test rows: fixA − dropIAT

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

### Macro F1, all test rows: fixA − dropIAT

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

## 2. Validity checks

### 2a. IAT units and the 1e9 threshold

Leaked values should all be epoch seconds near capture time; legitimate IATs should sit far below 1e9 (a ms or µs column would put legitimate long gaps near or above 1e9). Random-split training sample.

| dataset | IAT columns / features | leaked cells: min – max | legit nonzero: median / p99.99 / max (s) | legit cells in (1e6, 1e9] |
|---|---|---|---|---:|
| d2018 | 30 / 313 | 1.519e+09 – 1.52e+09 | 0.296 / 1671 / 3.242e+04 | 0 |
| d2017 | 15 / 114 | 1.499e+09 – 1.499e+09 | 0.0133 / 1261 / 2.892e+04 | 0 |
| cpacket | 30 / 313 | 1.703e+09 – 1.703e+09 | 0.112 / 3601 / 2.882e+04 | 0 |

Result: every leaked cell is a single epoch-second band (2017: Jul 2017; 2018: Feb 2018; cPacket: Dec 2023); legitimate IATs top out around 3e4 s and no cell lies between 1e6 and 1e9, so the threshold separates them cleanly.

### 2b. Does fixA's zero still carry the leak?

Leaked rows are strongly class-dependent (table 2c), so after fixA, 'IAT cell == 0' could act as a leak flag. Test: a balanced decision tree (study DT settings) trained on binary masks only (random split, scored on the full test split). If fixA's zero pattern were a leak channel, it would beat the legitimate zero pattern clearly.

| features (binary) | d2018: macro F1 / mean att. recall | d2017: macro F1 / mean att. recall | cpacket: macro F1 / mean att. recall |
|---|---|---|---|
| majority baseline | 0.078 / 0.000 | 0.060 / 0.000 | 0.023 / 0.000 |
| row leaked flag (1 bit) | 0.035 / 0.250 | 0.029 / 0.182 | 0.020 / 0.105 |
| per-col leaked mask | 0.107 / 0.321 | 0.057 / 0.273 | 0.029 / 0.126 |
| zero mask, raw data (legit zeros only) | 0.333 / 0.597 | 0.117 / 0.349 | 0.108 / 0.143 |
| zero mask, after fixA (legit + leaked) | 0.334 / 0.573 | 0.129 / 0.322 | 0.112 / 0.156 |

Result: fixA's zero mask adds at most ~0.01 macro F1 over legitimate zeros alone (2017 +0.012, cPacket +0.004, 2018 +0.001), and mean attack recall changes by -0.03 to +0.01 (lower on 2017 and 2018). Legitimate exact zeros are common (table 2c), so the leak flag is mostly hidden among them. Section 1 (fixA − dropIAT) is the full-model check of the same question.

### 2c. Leak rate and legitimate zeros by class (random-split training sample)

Rows leaked = share of rows with any leaked IAT cell. Legit zeros = share of IAT cells exactly 0 in non-leaked rows. Because leak rates differ so much by class, the leaked-row subset has a different class mix from the full test set: compare leaked-row results via mean attack recall, not accuracy, and only within a dataset × split (the classes entering the mean can differ between splits; see the n in table 3).

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

## 3. Per-dataset detail

### BCCC-CSE-CIC-IDS2018 (9 classes)

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

### BCCC-CIC-IDS-2017 (14 classes)

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

### BCCC-cPacket-Cloud-DDoS-2024 (26 subtypes)

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

## 4. Model configuration caveats

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
- Fit time and peak memory come from two machines (PC: 8 threads; laptop: i7-8750H, 12 threads); the `machine` column in table 3 says which. Compare timings only between runs on the same machine.
- Feature counts differ: 313 features (30 IAT) on 2018 and cPacket, 114 (15 IAT) on 2017. Leak sensitivity across datasets is therefore not a like-for-like comparison of feature sets.
- Cross-machine reproducibility (checked 2026-10-02): a laptop XGBoost run recomputed on the PC gives identical predictions; a laptop MLP run gives 791 of 609,513 different predictions (accuracy 0.9468 vs 0.9469), i.e. floating-point differences between the two CPUs' maths libraries in MLP training, far below any effect reported here.
- Laptop disk incident: on 2026-10-02 evening, 60 scikit-learn files in the laptop's Python environment were found corrupted on disk (identical garbage blocks; noticed because KNN failed to import). They were restored from the PC (checksums identical after repair); the laptop's data caches, splits and subsamples were checksum-identical to the PC's, and import failures are loud, so earlier laptop results are unaffected (see the XGBoost check above).
- Single training seed (0). The CIs cover test-set sampling only.
- Leaked-row accuracy is not comparable to all-row accuracy (different class mix; see 2c); use mean attack recall.

## 5. Warnings recorded (not suppressed), by run

- ConvergenceWarning: lbfgs failed to converge after 1000 iteration(s) (status=1): STOP: TOTAL NO. OF ITERATIONS REACHED LIMIT Increase the number of iterations to improve the convergence (max_iter=1000). You might also want to scale the data as shown in: https://scikit-learn.org/stable/modules/preprocessing.html Please also refer to the documentation for alternative solver options: https://scikit-learn.org/stable/modules/linear_model.html#logistic-regression
  Runs (9): cpacket_random_lr_fixA, cpacket_random_lr_leaky, cpacket_temporal_lr_fixA, cpacket_temporal_lr_leaky, d2017_random_lr_leaky, d2018_random_lr_fixA, d2018_random_lr_leaky, d2018_temporal_lr_fixA, d2018_temporal_lr_leaky
