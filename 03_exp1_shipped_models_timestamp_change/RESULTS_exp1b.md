# Experiment 1b: KNN and ensemble under timestamp-only changes (vs RF)

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

## Accuracy (population-weighted) / accuracy on leaked rows

| Condition | RF | KNN | Ensemble |
|---|---|---|---|
| Baseline | 0.8930 / 0.669 | **0.9934 / 0.990** | **0.9934 / 0.991** |
| +8 years | 0.8750 / 0.612 | 0.8713 / 0.614 | 0.8714 / 0.614 |
| +1 day | 0.8384 / 0.506 | 0.9036 / 0.724 | 0.9036 / 0.722 |
| Shuffle (5 seeds) | 0.8764 ± 0.0006 / 0.617 | 0.9195 ± 0.0023 / 0.760 | 0.9192 ± 0.0023 / 0.756 |
| Zero (fixed data, leaky model) | 0.8750 / 0.612 | 0.8709 / 0.612 | 0.8709 / 0.612 |

Macro-F1 (pop-weighted), baseline -> +8y: RF 0.758 -> 0.799, KNN 0.908 -> 0.763, ensemble 0.953 -> 0.769.

## Recall, baseline -> +8y (all sample rows)

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

## Findings
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

## Caveat
As in Experiment 1, this measures how much these trained models depend on the timestamp, not what models trained without
the leak would score (Experiment 3).
