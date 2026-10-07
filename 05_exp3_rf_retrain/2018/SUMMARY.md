# Experiment 3: RF retrained with and without the leak

RandomForestClassifier(n_estimators=200, max_depth=30, min_samples_leaf=10, class_weight='balanced', n_jobs=2, random_state=seed), 313 features. Mean ± std over completed seeds.

fixA = leaked IAT cells set to 0 in train and test. fixB = fixA + rows with packets_count == 1 dropped (the test set shrinks too, so fixB is scored on a different row set).

**LEAK CHECK FLAGGED (split thresholds > 1e9 in a fixed model): ['random_fixA_s2: 1 (0 on IAT features)']**

**Of these, on IAT features: none.** The flagged thresholds are on non-IAT columns. The census column scan found genuine non-timestamp values above 1e9 only in avg_bwd_bulk_rate, avg_fwd_bulk_rate, bytes_rate, fwd/bwd_bytes_rate and variance_*_delta_len (implausible rates, not capture times), so these are not leaks.

## All test rows

| split | variant | seeds | acc | macro-F1 | R Benign | R Bot | R Brute_Force_Web | R Brute_Force_XSS | R DDoS_HOIC | R DDoS_LOIC_HTTP | R DoS_HULK | R DoS_SlowHTTP | R SQL_Injection |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| temporal | leaky | 0,1,2,3 | 0.8919 ± 0.0000 | 0.7566 ± 0.0032 | 0.997 ± 0.000 | 0.502 ± 0.000 | 0.507 ± 0.000 | 0.603 ± 0.034 | 0.690 ± 0.000 | 1.000 ± 0.000 | 0.968 ± 0.000 | 1.000 ± 0.000 | 0.962 ± 0.000 |
| temporal | fixA | 0,1,2,3 | 0.9645 ± 0.0001 | 0.7770 ± 0.0100 | 0.999 ± 0.000 | 0.502 ± 0.002 | 0.978 ± 0.000 | 0.966 ± 0.000 | 1.000 ± 0.000 | 1.000 ± 0.000 | 0.968 ± 0.000 | 1.000 ± 0.000 | 0.615 ± 0.000 |
| temporal | fixB | 0,1,2,3 | 0.9991 ± 0.0000 | 0.9694 ± 0.0039 | 1.000 ± 0.000 | 0.993 ± 0.000 | 0.985 ± 0.017 | 1.000 ± 0.000 | 1.000 ± 0.000 | 0.999 ± 0.000 | 0.996 ± 0.000 | 1.000 ± 0.000 | 0.917 ± 0.000 |
| random | leaky | 0,1,2,3 | 0.9976 ± 0.0008 | 0.8229 ± 0.0010 | 0.996 ± 0.001 | 1.000 ± 0.000 | 0.993 ± 0.000 | 0.966 ± 0.000 | 1.000 ± 0.000 | 1.000 ± 0.000 | 1.000 ± 0.000 | 1.000 ± 0.000 | 0.894 ± 0.019 |
| random | fixA | 0,1,2,3 | 0.9533 ± 0.0020 | 0.7635 ± 0.0225 | 0.974 ± 0.004 | 0.503 ± 0.000 | 0.978 ± 0.000 | 0.966 ± 0.000 | 1.000 ± 0.000 | 0.999 ± 0.000 | 0.998 ± 0.000 | 1.000 ± 0.000 | 0.731 ± 0.000 |
| random | fixB | 0,1,2,3 | 1.0000 ± 0.0000 | 0.9859 ± 0.0006 | 1.000 ± 0.000 | 1.000 ± 0.000 | 1.000 ± 0.000 | 0.972 ± 0.000 | 1.000 ± 0.000 | 1.000 ± 0.000 | 1.000 ± 0.000 | 1.000 ± 0.000 | 0.933 ± 0.000 |

## Leaked test rows (rows leaked in the unmodified data)

| split | variant | seeds | acc | macro-F1 | R Benign | R Bot | R Brute_Force_Web | R Brute_Force_XSS | R DDoS_HOIC | R DDoS_LOIC_HTTP | R DoS_HULK | R DoS_SlowHTTP | R SQL_Injection |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| temporal | leaky | 4 | 0.6736 ± 0.0000 | 0.3041 ± 0.0092 | 0.991 ± 0.000 | 0.009 ± 0.000 | 0.030 ± 0.000 | 0.233 ± 0.067 | 0.205 ± 0.000 | - | 0.088 ± 0.000 | 1.000 ± 0.000 | 1.000 ± 0.000 |
| temporal | fixA | 4 | 0.8933 ± 0.0001 | 0.4432 ± 0.0097 | 0.998 ± 0.000 | 0.010 ± 0.000 | 0.955 ± 0.000 | 0.933 ± 0.000 | 1.000 ± 0.000 | - | 0.066 ± 0.000 | 1.000 ± 0.000 | 0.357 ± 0.000 |
| temporal | fixB | 4 | 0.9895 ± 0.0000 | 0.2809 ± 0.0000 | 1.000 ± 0.000 | 0.000 ± 0.000 | - | - | - | - | 0.370 ± 0.000 | 1.000 ± 0.000 | - |
| random | leaky | 4 | 0.9935 ± 0.0021 | 0.7265 ± 0.0013 | 0.988 ± 0.004 | 1.000 ± 0.000 | 0.984 ± 0.000 | 0.955 ± 0.000 | 1.000 ± 0.000 | 0.900 ± 0.000 | 0.994 ± 0.000 | 1.000 ± 0.000 | 0.818 ± 0.000 |
| random | fixA | 4 | 0.8727 ± 0.0055 | 0.5075 ± 0.0306 | 0.929 ± 0.010 | 0.007 ± 0.000 | 0.952 ± 0.000 | 0.955 ± 0.000 | 1.000 ± 0.000 | 0.000 ± 0.000 | 0.825 ± 0.000 | 1.000 ± 0.000 | 0.455 ± 0.000 |
| random | fixB | 4 | 0.9998 ± 0.0000 | 0.4432 ± 0.0000 | 1.000 ± 0.000 | 0.983 ± 0.000 | - | - | - | - | 1.000 ± 0.000 | 1.000 ± 0.000 | - |

## Rare classes: exact counts (correct / support per seed, all test rows)

| split | variant | SQL_Injection | Brute_Force_XSS | Brute_Force_Web |
|---|---|---|---|---|
| temporal | leaky | 25/26, 25/26, 25/26, 25/26 | 34/58, 38/58, 34/58, 34/58 | 68/134, 68/134, 68/134, 68/134 |
| temporal | fixA | 16/26, 16/26, 16/26, 16/26 | 56/58, 56/58, 56/58, 56/58 | 131/134, 131/134, 131/134, 131/134 |
| temporal | fixB | 11/12, 11/12, 11/12, 11/12 | 28/28, 28/28, 28/28, 28/28 | 68/68, 66/68, 66/68, 68/68 |
| random | leaky | 24/26, 23/26, 23/26, 23/26 | 56/58, 56/58, 56/58, 56/58 | 133/134, 133/134, 133/134, 133/134 |
| random | fixA | 19/26, 19/26, 19/26, 19/26 | 56/58, 56/58, 56/58, 56/58 | 131/134, 131/134, 131/134, 131/134 |
| random | fixB | 14/15, 14/15, 14/15, 14/15 | 35/36, 35/36, 35/36, 35/36 | 72/72, 72/72, 72/72, 72/72 |

## Differences (mean leaky − mean fixed)

| split | comparison | Δ acc | Δ macro-F1 | Δ R Benign | Δ R Bot | Δ R Brute_Force_Web | Δ R Brute_Force_XSS | Δ R DDoS_HOIC | Δ R DDoS_LOIC_HTTP | Δ R DoS_HULK | Δ R DoS_SlowHTTP | Δ R SQL_Injection |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| temporal | leaky − fixA | -0.0726 | -0.0204 | -0.003 | +0.001 | -0.470 | -0.362 | -0.310 | -0.000 | +0.001 | +0.000 | +0.346 |
| temporal | leaky − fixB | -0.1072 | -0.2128 | -0.003 | -0.490 | -0.478 | -0.397 | -0.310 | +0.001 | -0.027 | +0.000 | +0.045 |
| random | leaky − fixA | +0.0443 | +0.0593 | +0.021 | +0.497 | +0.015 | +0.000 | +0.000 | +0.001 | +0.002 | +0.000 | +0.163 |
| random | leaky − fixB | -0.0024 | -0.1630 | -0.004 | +0.000 | -0.007 | -0.007 | +0.000 | -0.000 | -0.000 | +0.000 | -0.039 |

## Runs

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
