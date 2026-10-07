# Step 2: leak census of BCCC-CSE-CIC-IDS2018 (original per-day files)

Data: 34 original per-day files, 10 capture days, 48,182,782 rows, one 323-column header (list with sizes: `file_list.txt`).
Inner files dated 2023-07..2023-11, archive entries 2024-02-23, downloaded 2026-09-04. Wed 28-02 has no attack file in the
published zip. 14-02, 15-02 and 01-03 were read straight from their inner zips (Deflate64, streamed via `unzip -p`).
Scripts: `common.py`, `census.py` (one chunked pass), `report.py`. Full tables in `out/`. 0 files failed, no fallback needed.
Leak = IAT value > 1e9.

## Per class

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

## Rule check
fwd leak <=> fwd_packets_count == 1, bwd leak <=> bwd_packets_count == 1, combined leak <=> packets_count == 1:
**0 violations in 48,182,782 rows** for all three. The dataset was built with the same `calculate_IAT` behaviour reproduced in Step 1.

## Leaked values = flow start time
Leaked fwd value minus the `timestamp` column is exactly +18000 s in 96-100% of rows per file (100% in most attack files);
the rest are within ~5 s (+18001, +18000.001, +18004.97). So the `timestamp` column (and the time in `flow_id`) is
local UTC-5, and the leaked IAT is the flow's true UTC start epoch.

## Calendar (`out/leak_date_ranges.csv`, hourly: `out/leak_hours.csv`)
Every attack file's leaked values fall on its own capture day, inside a narrow window, e.g. FTP 14-02 14:33-16:10 UTC,
SSH 14-02 18:01-19:32, GoldenEye 15-02 13:27-14:11, HULK 16-02 17:45-17:58, HOIC 21-02 18:11-19:05,
SQLi 22-02 20:14-20:27 and 23-02 19:05-19:17, Bot 02-03 14:13-19:54, Infiltration 01-03 19:37.
Benign spans each day ~12:20 UTC to ~00:40 the next day. The day is identifiable from the leaked value alone,
and within a day attack and benign windows overlap only partly.
Anomaly: some benign files contain leaked values from other days (fri_23_02 benign: 3,250 rows from 21-22 Feb;
fri_02_03 benign: 6,849 rows incl. 27-28 Feb; wed_28_02 and fri_02_03 benign share the identical minimum value
2018-02-27 12:18:27.392139, wed_28_02 and thu_01_03 the identical maximum). Possibly duplicated rows across day files; not yet checked.

## Full-column scan (values in 1.4e9..2.2e9)
Only the 18 IAT mean/max/min/total/median/mode columns hit systematically (std/var/cov/skew never do).
Non-IAT hits: avg_bwd_bulk_rate 360,968, avg_fwd_bulk_rate 405, bytes_rate 336, fwd_bytes_rate 279, bwd_bytes_rate 95,
variance_*_delta_len 71. Hand check: values spread uniformly over the range, none within a day of the flow start, so
**not a second timestamp leak**. The bulk-rate values are implausible, though (1.6e9 B/s bulk rate on flows with
bytes_rate ~42 B/s): a separate artifact. The variance hits (Bot) are genuine (~486 KB payloads).
Non-numeric placeholder columns: `delta_start` (small signed seconds, e.g. -0.0004, -4.3) and `handshake_duration`
(e.g. 0.0002): durations, not timestamps.
