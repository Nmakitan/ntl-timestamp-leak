# Addendum: all variants scored on the same rows (seeds 0-2)

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
