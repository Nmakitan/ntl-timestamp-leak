# Experiment 1: change only the leaked timestamps, re-score the existing RF

Model `~/trained_models/rf_model.onnx` (md5 19e98628...), `feature_order.json` (313 features, 30 IAT), test set
`ml_module_output/_intermediate/test_{X,y}.npy` (1,087,223 rows, 9 classes, temporally latest 25% per file).
Leaked cell = IAT column > 1e9. Modifications in float64 on the IAT block, cast to float32 for scoring.
Note: test_X was already float32 (pipeline read CSVs as float32), so timestamps were already on a 128 s grid;
+1d (86,400 s) and +8y (252,460,800 s) are exact multiples of 128, so no shift is lost to rounding.
Sanity check (non-leaked rows' predictions unchanged) passed in all 8 conditions.
Baseline 0.8919 on all rows; the earlier 0.8928 was on a 200k sample (IDS_MODELS_SUMMARY.txt:363).
Script `exp1.py`; full metrics, confusion matrices and transition matrices in `exp1_results.json`; predictions `pred_*.npy`.

## Leaked test rows
359,693 of 1,087,223 (33.1%). Benign 197,191 (33.6%), Bot 35,830 (50.1%), HOIC 97,477 (39.0%), SlowHTTP 26,387 (100%),
HULK 2,698 (3.4%), Web 66, XSS 30, SQLi 14, LOIC 0.

## Headline
| Condition | Acc all | Macro-F1 all | Acc leaked | Macro-F1 leaked | Predictions changed |
|---|---|---|---|---|---|
| Baseline | 0.8919 | 0.7560 | 0.6736 | 0.2995 | - |
| +8 years | 0.8749 | 0.7916 | 0.6220 | 0.2074 | 22,226 |
| +1 day | 0.8381 | 0.7346 | 0.5110 | 0.2065 | 121,075 |
| Shuffle (5 seeds) | 0.8763 ± 0.0000 | 0.7340 ± 0.0004 | 0.6264 ± 0.0001 | 0.2192 ± 0.0001 | 32,526 ± 68 |
| Zero (fixed data -> leaky model, NOT a retrain) | 0.8749 | 0.7916 | 0.6220 | 0.2074 | 22,226 |

## Per-class recall (all rows) / precision
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

## Findings
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

## Caveat
This measures how much this model depends on the timestamp, not what a model trained without the leak would score
(experiments 2 and 3).
