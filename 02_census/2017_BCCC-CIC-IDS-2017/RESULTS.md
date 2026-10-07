# Leak census: BCCC-CIC-IDS-2017

NTLFlowLyzer output: **yes**. 18 non-empty CSV files, 122 columns, 2,438,052 rows (file list with sizes: `file_list.txt`). Class key: `label`.
IAT columns (15): combined ['packets_IAT_mean', 'packet_IAT_std', 'packet_IAT_max', 'packet_IAT_min', 'packet_IAT_total']; fwd ['fwd_packets_IAT_mean', 'fwd_packets_IAT_std', 'fwd_packets_IAT_max', 'fwd_packets_IAT_min', 'fwd_packets_IAT_total']; bwd ['bwd_packets_IAT_mean', 'bwd_packets_IAT_std', 'bwd_packets_IAT_max', 'bwd_packets_IAT_min', 'bwd_packets_IAT_total'].
Counts: `packets_count`, `fwd_packets_count`, `bwd_packets_count`. Leak = IAT value > 1e9.

## Per class

| class | n | 1-packet | fwd leak | bwd leak | any leak | % | leak, >1 packet | % of leaked |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| Benign | 1,786,239 | 400,644 | 471,883 | 354,666 | 627,343 | 35.12 | 226,699 | 36.1 |
| Botnet_ARES | 5,508 | 705 | 4,611 | 3,908 | 4,613 | 83.75 | 3,908 | 84.7 |
| DDoS_LOIT | 95,733 | 49 | 50 | 0 | 50 | 0.05 | 1 | 2.0 |
| DoS_GoldenEye | 8,364 | 521 | 259 | 265 | 523 | 6.25 | 2 | 0.4 |
| DoS_Hulk | 349,240 | 127,983 | 111,228 | 24,994 | 132,146 | 37.84 | 4,163 | 3.2 |
| DoS_Slowhttptest | 6,860 | 1,782 | 1,455 | 527 | 1,981 | 28.88 | 199 | 10.0 |
| DoS_Slowloris | 5,177 | 1,016 | 762 | 256 | 1,017 | 19.64 | 1 | 0.1 |
| FTP-Patator | 9,531 | 3,084 | 3,944 | 4,021 | 5,527 | 57.99 | 2,443 | 44.2 |
| Heartbleed | 12 | 4 | 4 | 0 | 4 | 33.33 | 0 | 0.0 |
| Port_Scan | 161,323 | 2,178 | 159,322 | 159,757 | 161,109 | 99.87 | 158,931 | 98.6 |
| SSH-Patator | 5,949 | 2,937 | 36 | 2,934 | 2,955 | 49.67 | 18 | 0.6 |
| Web_Brute_Force | 2,734 | 1,366 | 1,222 | 144 | 1,366 | 49.96 | 0 | 0.0 |
| Web_SQL_Injection | 24 | 11 | 3 | 8 | 11 | 45.83 | 0 | 0.0 |
| Web_XSS | 1,358 | 679 | 656 | 23 | 679 | 50.00 | 0 | 0.0 |
| **ALL** | 2,438,052 | 542,959 | 755,435 | 551,503 | **939,324** | **38.53** | 396,365 | 42.2 |

## Rule check

fwd leak <=> fwd_packets_count == 1: 0 violations; bwd leak <=> bwd_packets_count == 1: 0; combined leak <=> packets_count == 1: 0 (of 2,438,052 rows).

## Leaked value vs `timestamp` column

Most common offset (leaked fwd value − timestamp): **14400.0 s** = +4 h, in 98.49% of 755,435 leaked-fwd rows; top 5: 14400.0: 744,052, 14400.001: 1,532, 14401.0: 1,115, 14400.002: 756, 14400.003: 602.
So the `timestamp` column is local time (UTC-4) and the leaked IAT is the UTC epoch of the flow start.

## Calendar (local time = UTC-4) vs documented capture days

Leaked rows on their file's documented capture day: **939,324 of 939,324 (100.00%)**.

| file | class | documented day | leaked rows | on that day | first (local) | last (local) | local days |
|---|---|---|---:|---:|---|---|---|
| monday_benign | Benign | 2017-07-03 | 176,234 | 176234 | 2017-07-03 07:56 | 2017-07-03 16:01 | 2017-07-03:176234 |
| tuesday_benign | Benign | 2017-07-04 | 137,504 | 137504 | 2017-07-04 07:54 | 2017-07-04 16:00 | 2017-07-04:137504 |
| ftp_patator | FTP-Patator | 2017-07-04 | 5,527 | 5527 | 2017-07-04 08:19 | 2017-07-04 09:20 | 2017-07-04:5527 |
| ssh_patator-new | SSH-Patator | 2017-07-04 | 2,955 | 2955 | 2017-07-04 13:09 | 2017-07-04 14:11 | 2017-07-04:2955 |
| wednesday_benign | Benign | 2017-07-05 | 138,719 | 138719 | 2017-07-05 07:42 | 2017-07-05 16:08 | 2017-07-05:138719 |
| dos_slowloris | DoS_Slowloris | 2017-07-05 | 1,017 | 1017 | 2017-07-05 08:48 | 2017-07-05 09:13 | 2017-07-05:1017 |
| dos_slowhttptest | DoS_Slowhttptest | 2017-07-05 | 1,981 | 1981 | 2017-07-05 09:14 | 2017-07-05 09:42 | 2017-07-05:1981 |
| dos_hulk | DoS_Hulk | 2017-07-05 | 132,146 | 132146 | 2017-07-05 09:43 | 2017-07-05 10:06 | 2017-07-05:132146 |
| dos_golden_eye | DoS_GoldenEye | 2017-07-05 | 523 | 523 | 2017-07-05 10:10 | 2017-07-05 10:29 | 2017-07-05:523 |
| heartbleed | Heartbleed | 2017-07-05 | 4 | 4 | 2017-07-05 13:53 | 2017-07-05 14:10 | 2017-07-05:4 |
| thursday_benign | Benign | 2017-07-06 | 45,672 | 45672 | 2017-07-06 07:59 | 2017-07-06 10:59 | 2017-07-06:45672 |
| web_brute_force | Web_Brute_Force | 2017-07-06 | 1,366 | 1366 | 2017-07-06 08:16 | 2017-07-06 09:00 | 2017-07-06:1366 |
| web_xss | Web_XSS | 2017-07-06 | 679 | 679 | 2017-07-06 09:15 | 2017-07-06 09:35 | 2017-07-06:679 |
| web_sql_injection | Web_SQL_Injection | 2017-07-06 | 11 | 11 | 2017-07-06 09:40 | 2017-07-06 09:42 | 2017-07-06:11 |
| friday_benign | Benign | 2017-07-07 | 129,214 | 129214 | 2017-07-07 08:00 | 2017-07-07 16:02 | 2017-07-07:129214 |
| botnet_ares | Botnet_ARES | 2017-07-07 | 4,613 | 4613 | 2017-07-07 09:04 | 2017-07-07 15:16 | 2017-07-07:4613 |
| portscan | Port_Scan | 2017-07-07 | 161,109 | 161109 | 2017-07-07 12:55 | 2017-07-07 14:24 | 2017-07-07:161109 |
| ddos_loit | DDoS_LOIT | 2017-07-07 | 50 | 50 | 2017-07-07 15:00 | 2017-07-07 15:16 | 2017-07-07:50 |

## Non-IAT columns with values in 1.4e9..2.2e9

- `bytes_rate`: 32
- `fwd_bytes_rate`: 24
- `bwd_bytes_rate`: 7
- `total_payload_bytes`: 1
- `bwd_total_payload_bytes`: 1
- `bwd_bulk_total_size`: 1

Non-numeric columns (samples): `timestamp`: ['2017-07-07 09:04:13.990571', '2017-07-07 09:04:24.131090', '2017-07-07 09:04:34.262355']; `protocol`: ['TCP']; `label`: ['Botnet_ARES']

## Flow shapes per class (fwd/bwd packet counts capped at 3)

Rows per (fwd, bwd) shape, share of the class, share leaked, and mean SYN/ACK/FIN/RST/PSH flag counts and total payload bytes per flow.

| class | fwd | bwd | rows | % of class | % leaked | SYN | ACK | FIN | RST | PSH | payload B |
|---|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| Benign | 2 | 2 | 568,778 | 31.8 | 0.0 | 0.00 | 0.01 | 0.00 | 0.00 | 0.00 | 310 |
| Benign | 3+ | 3+ | 461,910 | 25.9 | 0.0 | 1.91 | 92.79 | 1.69 | 0.12 | 11.14 | 90106 |
| Benign | 1 | 0 | 261,613 | 14.6 | 100.0 | 0.00 | 0.77 | 0.00 | 0.34 | 0.00 | 1 |
| Benign | 1 | 1 | 199,206 | 11.2 | 100.0 | 0.02 | 0.29 | 0.05 | 0.09 | 0.02 | 211 |
| Benign | 0 | 1 | 139,031 | 7.8 | 100.0 | 0.00 | 0.83 | 0.05 | 0.21 | 0.00 | 0 |
| Benign | 3+ | 2 | 72,829 | 4.1 | 0.0 | 0.82 | 1.74 | 0.82 | 0.01 | 0.05 | 265 |
| Benign | 0 | 2 | 30,152 | 1.7 | 0.0 | 0.00 | 1.22 | 0.34 | 0.80 | 0.07 | 110 |
| Benign | 2 | 1 | 13,795 | 0.8 | 100.0 | 0.03 | 2.72 | 0.76 | 0.28 | 0.22 | 891 |
| Benign | 0 | 3+ | 13,348 | 0.7 | 0.0 | 0.00 | 2.96 | 1.01 | 0.05 | 0.00 | 1 |
| Benign | 3+ | 0 | 9,033 | 0.5 | 0.0 | 0.74 | 1.84 | 1.46 | 0.12 | 1.07 | 1561 |
| Benign | 1 | 2 | 8,439 | 0.5 | 100.0 | 0.01 | 2.61 | 0.81 | 0.39 | 0.18 | 302 |
| Benign | 2 | 0 | 2,719 | 0.2 | 0.0 | 0.07 | 0.43 | 0.20 | 0.21 | 0.01 | 111 |
| Benign | 3+ | 1 | 2,634 | 0.1 | 100.0 | 0.26 | 9.57 | 0.85 | 0.44 | 2.02 | 12912 |
| Benign | 1 | 3+ | 2,625 | 0.1 | 100.0 | 1.20 | 4.60 | 1.24 | 0.05 | 0.15 | 6 |
| Benign | 2 | 3+ | 127 | 0.0 | 0.0 | 0.04 | 4.88 | 1.39 | 0.44 | 0.50 | 63 |
| Botnet_ARES | 1 | 1 | 3,906 | 70.9 | 100.0 | 1.00 | 1.00 | 0.00 | 1.00 | 0.00 | 0 |
| Botnet_ARES | 3+ | 3+ | 736 | 13.4 | 0.0 | 2.00 | 11.45 | 2.00 | 0.00 | 2.10 | 7176 |
| Botnet_ARES | 1 | 0 | 705 | 12.8 | 100.0 | 0.00 | 1.00 | 0.00 | 0.00 | 0.00 | 0 |
| Botnet_ARES | 3+ | 0 | 159 | 2.9 | 0.0 | 3.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0 |
| DDoS_LOIT | 3+ | 3+ | 95,660 | 99.9 | 0.0 | 2.00 | 12.38 | 1.27 | 1.00 | 2.05 | 11685 |
| DoS_GoldenEye | 3+ | 3+ | 7,762 | 92.8 | 0.0 | 2.18 | 14.09 | 1.02 | 0.39 | 3.13 | 10979 |
| DoS_GoldenEye | 0 | 1 | 263 | 3.1 | 100.0 | 0.00 | 0.02 | 0.00 | 0.98 | 0.00 | 0 |
| DoS_GoldenEye | 1 | 0 | 258 | 3.1 | 100.0 | 0.00 | 0.00 | 0.00 | 1.00 | 0.00 | 0 |
| DoS_GoldenEye | 0 | 2 | 78 | 0.9 | 0.0 | 0.00 | 2.00 | 1.00 | 0.00 | 0.00 | 0 |
| DoS_Hulk | 3+ | 3+ | 158,650 | 45.4 | 0.0 | 2.12 | 11.45 | 1.37 | 0.63 | 2.20 | 12001 |
| DoS_Hulk | 1 | 0 | 107,098 | 30.7 | 100.0 | 0.00 | 0.00 | 0.00 | 1.00 | 0.00 | 0 |
| DoS_Hulk | 0 | 2 | 58,117 | 16.6 | 0.0 | 0.00 | 1.00 | 0.01 | 1.00 | 0.01 | 1 |
| DoS_Hulk | 0 | 1 | 20,885 | 6.0 | 100.0 | 0.00 | 0.00 | 0.00 | 1.00 | 0.00 | 0 |
| DoS_Hulk | 1 | 1 | 4,076 | 1.2 | 100.0 | 0.00 | 1.00 | 0.98 | 1.00 | 0.29 | 12 |
| DoS_Hulk | 3+ | 2 | 201 | 0.1 | 0.0 | 4.31 | 3.89 | 0.04 | 0.00 | 0.00 | 0 |
| DoS_Hulk | 3+ | 0 | 109 | 0.0 | 0.0 | 2.94 | 0.07 | 0.02 | 0.00 | 0.02 | 80 |
| DoS_Hulk | 1 | 2 | 53 | 0.0 | 100.0 | 0.00 | 2.00 | 1.00 | 1.00 | 0.91 | 10 |
| DoS_Slowhttptest | 3+ | 0 | 2,824 | 41.2 | 0.0 | 6.92 | 0.07 | 0.06 | 0.00 | 0.06 | 40 |
| DoS_Slowhttptest | 3+ | 3+ | 1,816 | 26.5 | 0.0 | 2.82 | 14.05 | 1.53 | 0.14 | 6.39 | 5445 |
| DoS_Slowhttptest | 1 | 0 | 1,260 | 18.4 | 100.0 | 0.00 | 0.01 | 0.00 | 0.99 | 0.00 | 0 |
| DoS_Slowhttptest | 0 | 1 | 522 | 7.6 | 100.0 | 0.00 | 0.01 | 0.00 | 0.99 | 0.00 | 0 |
| DoS_Slowhttptest | 1 | 2 | 194 | 2.8 | 100.0 | 0.00 | 2.00 | 0.99 | 1.00 | 1.00 | 1983 |
| DoS_Slowhttptest | 3+ | 2 | 151 | 2.2 | 0.0 | 3.14 | 14.56 | 5.99 | 0.00 | 9.46 | 2852 |
| DoS_Slowhttptest | 2 | 2 | 82 | 1.2 | 0.0 | 0.00 | 3.00 | 1.00 | 1.00 | 1.00 | 1983 |
| DoS_Slowloris | 3+ | 3+ | 2,492 | 48.1 | 0.0 | 3.30 | 17.77 | 0.67 | 0.69 | 11.05 | 4352 |
| DoS_Slowloris | 3+ | 0 | 1,642 | 31.7 | 0.0 | 2.98 | 0.07 | 0.07 | 0.00 | 0.07 | 23 |
| DoS_Slowloris | 1 | 0 | 761 | 14.7 | 100.0 | 0.03 | 0.00 | 0.00 | 0.97 | 0.00 | 0 |
| DoS_Slowloris | 0 | 1 | 255 | 4.9 | 100.0 | 0.00 | 0.04 | 0.00 | 0.96 | 0.00 | 0 |
| FTP-Patator | 3+ | 3+ | 3,992 | 41.9 | 0.0 | 2.00 | 24.33 | 1.37 | 0.62 | 13.96 | 308 |
| FTP-Patator | 1 | 1 | 2,438 | 25.6 | 100.0 | 0.00 | 1.01 | 1.00 | 0.99 | 0.01 | 0 |
| FTP-Patator | 0 | 1 | 1,578 | 16.6 | 100.0 | 0.00 | 0.03 | 0.02 | 0.97 | 0.00 | 0 |
| FTP-Patator | 1 | 0 | 1,506 | 15.8 | 100.0 | 0.00 | 0.01 | 0.01 | 0.99 | 0.00 | 0 |
| Heartbleed | 3+ | 3+ | 8 | 66.7 | 0.0 | 2.00 | 6169.50 | 1.50 | 0.50 | 359.88 | 10024923 |
| Heartbleed | 1 | 0 | 4 | 33.3 | 100.0 | 0.00 | 0.00 | 0.00 | 1.00 | 0.00 | 0 |
| Port_Scan | 1 | 1 | 157,970 | 97.9 | 100.0 | 1.00 | 1.00 | 0.00 | 1.00 | 0.00 | 0 |
| Port_Scan | 1 | 0 | 1,349 | 0.8 | 100.0 | 0.09 | 0.71 | 0.00 | 0.61 | 0.00 | 0 |
| Port_Scan | 0 | 1 | 829 | 0.5 | 100.0 | 1.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0 |
| Port_Scan | 2 | 1 | 484 | 0.3 | 100.0 | 2.00 | 1.00 | 0.00 | 1.00 | 0.00 | 0 |
| Port_Scan | 3+ | 1 | 474 | 0.3 | 100.0 | 2.00 | 3.00 | 0.00 | 1.00 | 0.00 | 0 |
| Port_Scan | 3+ | 3+ | 208 | 0.1 | 0.0 | 2.00 | 8.97 | 1.46 | 0.41 | 1.61 | 4879 |
| SSH-Patator | 3+ | 3+ | 2,980 | 50.1 | 0.0 | 2.00 | 52.79 | 2.00 | 0.01 | 30.74 | 4732 |
| SSH-Patator | 0 | 1 | 2,916 | 49.0 | 100.0 | 0.00 | 1.00 | 0.00 | 0.00 | 0.00 | 0 |
| Web_Brute_Force | 1 | 0 | 1,222 | 44.7 | 100.0 | 0.00 | 1.00 | 0.00 | 0.00 | 0.00 | 0 |
| Web_Brute_Force | 3+ | 2 | 1,180 | 43.2 | 0.0 | 2.00 | 4.00 | 2.00 | 0.00 | 0.00 | 0 |
| Web_Brute_Force | 3+ | 3+ | 185 | 6.8 | 0.0 | 2.00 | 123.26 | 2.00 | 0.00 | 79.04 | 45600 |
| Web_Brute_Force | 0 | 1 | 144 | 5.3 | 100.0 | 0.00 | 1.00 | 0.00 | 0.00 | 0.00 | 0 |
| Web_SQL_Injection | 3+ | 3+ | 12 | 50.0 | 0.0 | 2.00 | 8.42 | 2.00 | 0.00 | 2.00 | 2804 |
| Web_SQL_Injection | 0 | 1 | 8 | 33.3 | 100.0 | 0.00 | 1.00 | 0.00 | 0.00 | 0.00 | 0 |
| Web_SQL_Injection | 1 | 0 | 3 | 12.5 | 100.0 | 0.00 | 1.00 | 0.00 | 0.00 | 0.00 | 0 |
| Web_SQL_Injection | 0 | 2 | 1 | 4.2 | 0.0 | 0.00 | 2.00 | 0.00 | 0.00 | 0.00 | 0 |
| Web_XSS | 1 | 0 | 656 | 48.3 | 100.0 | 0.00 | 1.00 | 0.00 | 0.00 | 0.00 | 0 |
| Web_XSS | 3+ | 2 | 633 | 46.6 | 0.0 | 2.00 | 4.00 | 2.00 | 0.00 | 0.00 | 0 |
| Web_XSS | 3+ | 3+ | 43 | 3.2 | 0.0 | 2.00 | 133.40 | 2.00 | 0.00 | 84.84 | 97539 |
| Web_XSS | 0 | 1 | 23 | 1.7 | 100.0 | 0.00 | 1.00 | 0.00 | 0.00 | 0.00 | 0 |

(Shapes with < 0.5% of a class and < 50 rows omitted; full table in `flow_shapes.csv`.)

## Notes (hand checks, added after generation)

**Non-IAT epoch-range values are not timestamps** (`../nonIAT_handcheck.txt`): none lies within a day of its flow's
start. `bytes_rate`-type hits are ~0 s flows (2-3 packets) where dividing by a tiny duration gives a huge rate;
the one `total_payload_bytes` / `bwd_bulk_total_size` hit is a genuine 1.87 GB transfer (1.5M packets, 576 s).

**What the leaked rows are** (flow-shape table above):
- Web_Brute_Force / Web_XSS / Web_SQL_Injection: ~45-48% of each class are lone forward ACKs with no payload: the
  trailing-ACK ghost flow reproduced in Step 1. The real attack sessions (3+/2, 3+/3+) are never leaked.
- SSH-Patator: 49% are lone backward ACKs (the same ghost in the other direction).
- DoS_Hulk / Slowloris / Slowhttptest / GoldenEye, FTP-Patator, Heartbleed: leaked rows are lone RST packets or
  FIN/RST teardown fragments split off from the real session.
- Port_Scan (97.9%: 1 fwd SYN + 1 bwd RST/ACK) and Botnet_ARES (70.9%: SYN + RST/ACK, no payload): probes and
  refused connections. Here the leaked rows are the attack's own signature, not fragments; Port_Scan is 99.87% leaked.
- Benign: 14.6% 1/0 (ACK/RST fragments), 11.2% 1/1, 7.8% 0/1.
- Shapes with 0 forward packets (0/1, 0/2, 0/3+) exist although a flow's first packet defines "forward": a further
  flow-splitting artifact (traffic arriving after a flow was closed).
