# Leak census across BCCC datasets

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

## What the leaked rows are (flow shapes)

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

## Is the leak exploitable? Timestamp-only baseline (Experiment 2) on all three datasets

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
