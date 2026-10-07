# Timestamp-only tree: binary attack-vs-benign on leaked test rows

Single feature t (smallest leaked IAT value). **detect** = leaked attack rows predicted as any attack class; **FPR** = leaked benign rows predicted as any attack class. Random / temporal rows are recomputed from the stored confusion matrices of Experiment 2 (no rerun); leave-one-day-out from this directory. cPacket: Suspicious counted as neither attack nor benign.

| dataset | split | tree | leaked attack rows | detect | leaked benign rows | FPR |
|---|---|---|---:|---:|---:|---:|
| CSE-CIC-IDS2018 | random | balanced (pre-specified) | 188,770 | 1.000 | 209,648 | 0.091 |
| CSE-CIC-IDS2018 | random | unweighted (added afterwards) | 188,770 | 0.997 | 209,648 | 0.083 |
| CSE-CIC-IDS2018 | temporal | balanced (pre-specified) | 162,502 | 0.157 | 197,191 | 0.015 |
| CSE-CIC-IDS2018 | temporal | unweighted (added afterwards) | 162,502 | 0.157 | 197,191 | 0.015 |
| CIC-IDS-2017 | random | balanced (pre-specified) | 77,963 | 1.000 | 156,946 | 0.319 |
| CIC-IDS-2017 | random | unweighted (added afterwards) | 77,963 | 0.940 | 156,946 | 0.017 |
| CIC-IDS-2017 | temporal | balanced (pre-specified) | 78,273 | 0.356 | 161,365 | 0.222 |
| CIC-IDS-2017 | temporal | unweighted (added afterwards) | 78,273 | 0.351 | 161,365 | 0.000 |
| cPacket (26 subtypes) | random | balanced (pre-specified) | 38,647 | 0.993 | 72,114 | 0.130 |
| cPacket (26 subtypes) | random | unweighted (added afterwards) | 38,647 | 0.896 | 72,114 | 0.035 |
| cPacket (26 subtypes) | temporal | balanced (pre-specified) | 38,244 | 0.899 | 72,635 | 0.066 |
| cPacket (26 subtypes) | temporal | unweighted (added afterwards) | 38,244 | 0.876 | 72,635 | 0.049 |
| CIC-IDS-2017 | leave-one-day-out (5 days pooled) | balanced (pre-specified) | 311,981 | 0.000 | 627,343 | 0.000 |
| CIC-IDS-2017 | leave-one-day-out (5 days pooled) | unweighted (added afterwards) | 311,981 | 0.000 | 627,343 | 0.000 |

## Leave-one-day-out per held-out day (CIC-IDS-2017, leaked test rows)

| held-out day | tree | leaked attack rows | detect | leaked benign rows | FPR | majority-guess FPR |
|---|---|---:|---:|---:|---:|---:|
| 0703 | balanced (pre-specified) | 0 | – | 176,234 | 0.000 | 0.000 |
| 0703 | unweighted (added afterwards) | 0 | – | 176,234 | 0.000 | 0.000 |
| 0704 | balanced (pre-specified) | 8,482 | 0.000 | 137,504 | 0.000 | 0.000 |
| 0704 | unweighted (added afterwards) | 8,482 | 0.000 | 137,504 | 0.000 | 0.000 |
| 0705 | balanced (pre-specified) | 135,671 | 0.000 | 138,719 | 0.000 | 0.000 |
| 0705 | unweighted (added afterwards) | 135,671 | 0.000 | 138,719 | 0.000 | 0.000 |
| 0706 | balanced (pre-specified) | 2,056 | 0.000 | 45,672 | 0.000 | 0.000 |
| 0706 | unweighted (added afterwards) | 2,056 | 0.000 | 45,672 | 0.000 | 0.000 |
| 0707 | balanced (pre-specified) | 165,772 | 0.000 | 129,214 | 0.000 | 0.000 |
| 0707 | unweighted (added afterwards) | 165,772 | 0.000 | 129,214 | 0.000 | 0.000 |
