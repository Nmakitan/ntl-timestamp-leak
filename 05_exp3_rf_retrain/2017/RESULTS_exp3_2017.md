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
