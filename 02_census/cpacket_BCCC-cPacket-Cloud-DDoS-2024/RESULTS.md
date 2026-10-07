# Leak census: BCCC-cPacket-Cloud-DDoS-2024

NTLFlowLyzer output: **yes**. 4 non-empty CSV files, 324 columns, 700,774 rows (file list with sizes: `file_list.txt`). Class key: `label` + `activity`.
IAT columns (30): combined ['packets_IAT_mean', 'packet_IAT_std', 'packet_IAT_max', 'packet_IAT_min', 'packet_IAT_total', 'packets_IAT_median', 'packets_IAT_skewness', 'packets_IAT_cov', 'packets_IAT_mode', 'packets_IAT_variance']; fwd ['fwd_packets_IAT_mean', 'fwd_packets_IAT_std', 'fwd_packets_IAT_max', 'fwd_packets_IAT_min', 'fwd_packets_IAT_total', 'fwd_packets_IAT_median', 'fwd_packets_IAT_skewness', 'fwd_packets_IAT_cov', 'fwd_packets_IAT_mode', 'fwd_packets_IAT_variance']; bwd ['bwd_packets_IAT_mean', 'bwd_packets_IAT_std', 'bwd_packets_IAT_max', 'bwd_packets_IAT_min', 'bwd_packets_IAT_total', 'bwd_packets_IAT_median', 'bwd_packets_IAT_skewness', 'bwd_packets_IAT_cov', 'bwd_packets_IAT_mode', 'bwd_packets_IAT_variance'].
Counts: `packets_count`, `fwd_packets_count`, `bwd_packets_count`. Leak = IAT value > 1e9.

## Per class

| class | n | 1-packet | fwd leak | bwd leak | any leak | % | leak, >1 packet | % of leaked |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| Attack / Attack-Killall-v2 | 6,033 | 1,134 | 1,418 | 331 | 1,453 | 24.08 | 319 | 22.0 |
| Attack / Attack-Killer-TCP | 6,254 | 1,114 | 1,764 | 677 | 1,788 | 28.59 | 674 | 37.7 |
| Attack / Attack-TCP-BYPass-V1 | 138,368 | 132,330 | 132,682 | 437 | 132,732 | 95.93 | 402 | 0.3 |
| Attack / Attack-TCP-Control | 5,744 | 1,052 | 1,461 | 454 | 1,502 | 26.15 | 450 | 30.0 |
| Attack / Attack-TCP-Flag-ACK | 10,683 | 1,318 | 1,724 | 433 | 1,741 | 16.30 | 423 | 24.3 |
| Attack / Attack-TCP-Flag-ACK-PSH | 7,482 | 1,231 | 1,635 | 451 | 1,666 | 22.27 | 435 | 26.1 |
| Attack / Attack-TCP-Flag-MIX | 7,416 | 1,150 | 1,704 | 581 | 1,724 | 23.25 | 574 | 33.3 |
| Attack / Attack-TCP-Flag-OSYN | 867 | 430 | 688 | 305 | 722 | 83.28 | 292 | 40.4 |
| Attack / Attack-TCP-Flag-OSYNP | 890 | 359 | 724 | 374 | 740 | 83.15 | 381 | 51.5 |
| Attack / Attack-TCP-Flag-RST-ACK | 1,445 | 314 | 584 | 278 | 596 | 41.25 | 282 | 47.3 |
| Attack / Attack-TCP-Flag-SYN | 7,845 | 1,275 | 1,738 | 509 | 1,765 | 22.50 | 490 | 27.8 |
| Attack / Attack-TCP-Flag-SYN-ACK | 8,204 | 1,105 | 1,582 | 494 | 1,595 | 19.44 | 490 | 30.7 |
| Attack / Attack-TCP-Flag-SYN-TFO | 3,631 | 518 | 766 | 301 | 807 | 22.23 | 289 | 35.8 |
| Attack / Attack-TCP-Flag-SYN-TIME | 1,360 | 557 | 852 | 413 | 923 | 67.87 | 366 | 39.7 |
| Attack / Attack-TCP-IGMP | 7,251 | 1,173 | 1,608 | 467 | 1,634 | 22.53 | 461 | 28.2 |
| Attack / Attack-TCP-SYN | 6,953 | 1,028 | 1,414 | 448 | 1,450 | 20.85 | 422 | 29.1 |
| Attack / Attack-TCP-Valid-SYN | 8,043 | 1,153 | 1,442 | 315 | 1,459 | 18.14 | 306 | 21.0 |
| Benign / Benign | 302,284 | 139,284 | 193,962 | 115,416 | 244,792 | 80.98 | 105,508 | 43.1 |
| Benign / Benign-Email-Receive | 1,395 | 477 | 578 | 640 | 935 | 67.03 | 458 | 49.0 |
| Benign / Benign-Email-Send | 1,938 | 889 | 640 | 626 | 1,151 | 59.39 | 262 | 22.8 |
| Benign / Benign-FTP | 483 | 204 | 170 | 191 | 307 | 63.56 | 103 | 33.6 |
| Benign / Benign-SSH | 2,985 | 1,097 | 1,350 | 346 | 1,443 | 48.34 | 346 | 24.0 |
| Benign / Benign-Systemic | 48,074 | 5,033 | 6,146 | 3,600 | 8,163 | 16.98 | 3,130 | 38.3 |
| Benign / Benign-Telnet | 4,768 | 1,663 | 1,818 | 2,799 | 3,996 | 83.81 | 2,333 | 58.4 |
| Benign / Benign-Web_Browsing_HTTP-S | 51,272 | 24,319 | 22,264 | 6,929 | 27,810 | 54.24 | 3,491 | 12.6 |
| Suspicious / Suspicious | 59,106 | 10,048 | 15,163 | 5,609 | 15,533 | 26.28 | 5,485 | 35.3 |
| **ALL** | 700,774 | 330,255 | 395,877 | 143,424 | **458,427** | **65.42** | 128,172 | 28.0 |

## Rule check

fwd leak <=> fwd_packets_count == 1: 0 violations; bwd leak <=> bwd_packets_count == 1: 0; combined leak <=> packets_count == 1: 0 (of 700,774 rows).

## Leaked value vs `timestamp` column

Most common offset (leaked fwd value − timestamp): **18000.0 s** = +5 h, in 99.59% of 395,877 leaked-fwd rows; top 5: 18000.0: 394,258, 18006.0: 155, 18006.004: 95, 18000.209: 74, 18000.206: 64.
So the `timestamp` column is local time (UTC-5) and the leaked IAT is the UTC epoch of the flow start.

## Calendar (local time = UTC-5) vs documented capture days

Leaked rows on their file's documented capture day: **458,427 of 458,427 (100.00%)**.

| file | class | documented day | leaked rows | on that day | first (local) | last (local) | local days |
|---|---|---|---:|---:|---|---|---|
| Thursday_14_Dec_2023 | Benign / Benign | 2023-12-14 | 63,760 | 63760 | 2023-12-14 09:01 | 2023-12-14 17:00 | 2023-12-14:63760 |
| Thursday_14_Dec_2023 | Benign / Benign-Email-Receive | 2023-12-14 | 322 | 322 | 2023-12-14 09:01 | 2023-12-14 16:55 | 2023-12-14:322 |
| Thursday_14_Dec_2023 | Benign / Benign-Systemic | 2023-12-14 | 1,967 | 1967 | 2023-12-14 09:01 | 2023-12-14 17:00 | 2023-12-14:1967 |
| Thursday_14_Dec_2023 | Benign / Benign-Telnet | 2023-12-14 | 2,727 | 2727 | 2023-12-14 09:01 | 2023-12-14 17:00 | 2023-12-14:2727 |
| Thursday_14_Dec_2023 | Benign / Benign-Web_Browsing_HTTP-S | 2023-12-14 | 5,573 | 5573 | 2023-12-14 09:01 | 2023-12-14 16:59 | 2023-12-14:5573 |
| Thursday_14_Dec_2023 | Benign / Benign-Email-Send | 2023-12-14 | 360 | 360 | 2023-12-14 09:07 | 2023-12-14 16:55 | 2023-12-14:360 |
| Thursday_14_Dec_2023 | Benign / Benign-FTP | 2023-12-14 | 193 | 193 | 2023-12-14 09:10 | 2023-12-14 16:48 | 2023-12-14:193 |
| Thursday_14_Dec_2023 | Benign / Benign-SSH | 2023-12-14 | 577 | 577 | 2023-12-14 09:11 | 2023-12-14 16:58 | 2023-12-14:577 |
| Saturday_16_Dec_2023 | Benign / Benign | 2023-12-16 | 124,716 | 124716 | 2023-12-16 09:00 | 2023-12-16 17:00 | 2023-12-16:124716 |
| Saturday_16_Dec_2023 | Benign / Benign-SSH | 2023-12-16 | 637 | 637 | 2023-12-16 09:00 | 2023-12-16 16:54 | 2023-12-16:637 |
| Saturday_16_Dec_2023 | Benign / Benign-Telnet | 2023-12-16 | 924 | 924 | 2023-12-16 09:00 | 2023-12-16 16:58 | 2023-12-16:924 |
| Saturday_16_Dec_2023 | Benign / Benign-Web_Browsing_HTTP-S | 2023-12-16 | 7,267 | 7267 | 2023-12-16 09:00 | 2023-12-16 17:00 | 2023-12-16:7267 |
| Saturday_16_Dec_2023 | Benign / Benign-Systemic | 2023-12-16 | 4,099 | 4099 | 2023-12-16 09:01 | 2023-12-16 17:00 | 2023-12-16:4099 |
| Saturday_16_Dec_2023 | Benign / Benign-Email-Receive | 2023-12-16 | 324 | 324 | 2023-12-16 09:02 | 2023-12-16 16:58 | 2023-12-16:324 |
| Saturday_16_Dec_2023 | Benign / Benign-Email-Send | 2023-12-16 | 356 | 356 | 2023-12-16 09:08 | 2023-12-16 16:58 | 2023-12-16:356 |
| Saturday_16_Dec_2023 | Benign / Benign-FTP | 2023-12-16 | 66 | 66 | 2023-12-16 09:33 | 2023-12-16 16:54 | 2023-12-16:66 |
| Monday_18_Dec_2023 | Attack / Attack-TCP-Valid-SYN | 2023-12-18 | 1,459 | 1459 | 2023-12-18 08:56 | 2023-12-18 09:29 | 2023-12-18:1459 |
| Monday_18_Dec_2023 | Benign / Benign | 2023-12-18 | 28,348 | 28348 | 2023-12-18 08:56 | 2023-12-18 17:00 | 2023-12-18:28348 |
| Monday_18_Dec_2023 | Benign / Benign-Systemic | 2023-12-18 | 1,139 | 1139 | 2023-12-18 08:56 | 2023-12-18 17:00 | 2023-12-18:1139 |
| Monday_18_Dec_2023 | Benign / Benign-Telnet | 2023-12-18 | 159 | 159 | 2023-12-18 08:56 | 2023-12-18 16:54 | 2023-12-18:159 |
| Monday_18_Dec_2023 | Benign / Benign-Web_Browsing_HTTP-S | 2023-12-18 | 10,871 | 10871 | 2023-12-18 08:56 | 2023-12-18 17:00 | 2023-12-18:10871 |
| Monday_18_Dec_2023 | Benign / Benign-Email-Receive | 2023-12-18 | 152 | 152 | 2023-12-18 08:57 | 2023-12-18 16:53 | 2023-12-18:152 |
| Monday_18_Dec_2023 | Benign / Benign-FTP | 2023-12-18 | 24 | 24 | 2023-12-18 08:59 | 2023-12-18 16:23 | 2023-12-18:24 |
| Monday_18_Dec_2023 | Benign / Benign-SSH | 2023-12-18 | 115 | 115 | 2023-12-18 08:59 | 2023-12-18 16:56 | 2023-12-18:115 |
| Monday_18_Dec_2023 | Benign / Benign-Email-Send | 2023-12-18 | 243 | 243 | 2023-12-18 09:00 | 2023-12-18 16:55 | 2023-12-18:243 |
| Monday_18_Dec_2023 | Attack / Attack-TCP-BYPass-V1 | 2023-12-18 | 132,732 | 132732 | 2023-12-18 09:30 | 2023-12-18 09:59 | 2023-12-18:132732 |
| Monday_18_Dec_2023 | Suspicious / Suspicious | 2023-12-18 | 6,137 | 6137 | 2023-12-18 09:50 | 2023-12-18 17:00 | 2023-12-18:6137 |
| Monday_18_Dec_2023 | Attack / Attack-Killall-v2 | 2023-12-18 | 1,453 | 1453 | 2023-12-18 10:00 | 2023-12-18 10:29 | 2023-12-18:1453 |
| Monday_18_Dec_2023 | Attack / Attack-TCP-IGMP | 2023-12-18 | 1,634 | 1634 | 2023-12-18 10:30 | 2023-12-18 10:59 | 2023-12-18:1634 |
| Monday_18_Dec_2023 | Attack / Attack-TCP-SYN | 2023-12-18 | 1,450 | 1450 | 2023-12-18 11:00 | 2023-12-18 11:29 | 2023-12-18:1450 |
| Monday_18_Dec_2023 | Attack / Attack-Killer-TCP | 2023-12-18 | 1,788 | 1788 | 2023-12-18 11:30 | 2023-12-18 11:59 | 2023-12-18:1788 |
| Monday_18_Dec_2023 | Attack / Attack-TCP-Control | 2023-12-18 | 1,502 | 1502 | 2023-12-18 13:00 | 2023-12-18 13:29 | 2023-12-18:1502 |
| Monday_18_Dec_2023 | Attack / Attack-TCP-Flag-MIX | 2023-12-18 | 1,724 | 1724 | 2023-12-18 13:30 | 2023-12-18 13:59 | 2023-12-18:1724 |
| Monday_18_Dec_2023 | Attack / Attack-TCP-Flag-SYN | 2023-12-18 | 1,765 | 1765 | 2023-12-18 14:00 | 2023-12-18 14:29 | 2023-12-18:1765 |
| Monday_18_Dec_2023 | Attack / Attack-TCP-Flag-ACK | 2023-12-18 | 1,741 | 1741 | 2023-12-18 14:30 | 2023-12-18 14:59 | 2023-12-18:1741 |
| Monday_18_Dec_2023 | Attack / Attack-TCP-Flag-SYN-ACK | 2023-12-18 | 1,595 | 1595 | 2023-12-18 15:00 | 2023-12-18 15:29 | 2023-12-18:1595 |
| Monday_18_Dec_2023 | Attack / Attack-TCP-Flag-ACK-PSH | 2023-12-18 | 1,666 | 1666 | 2023-12-18 15:30 | 2023-12-18 15:59 | 2023-12-18:1666 |
| Tuesday_19_Dec_2023 | Benign / Benign | 2023-12-19 | 27,968 | 27968 | 2023-12-19 08:59 | 2023-12-19 17:00 | 2023-12-19:27968 |
| Tuesday_19_Dec_2023 | Benign / Benign-Web_Browsing_HTTP-S | 2023-12-19 | 4,099 | 4099 | 2023-12-19 08:59 | 2023-12-19 16:58 | 2023-12-19:4099 |
| Tuesday_19_Dec_2023 | Suspicious / Suspicious | 2023-12-19 | 9,396 | 9396 | 2023-12-19 08:59 | 2023-12-19 17:00 | 2023-12-19:9396 |
| Tuesday_19_Dec_2023 | Attack / Attack-TCP-Flag-RST-ACK | 2023-12-19 | 596 | 596 | 2023-12-19 09:00 | 2023-12-19 09:29 | 2023-12-19:596 |
| Tuesday_19_Dec_2023 | Benign / Benign-Email-Send | 2023-12-19 | 192 | 192 | 2023-12-19 09:00 | 2023-12-19 16:59 | 2023-12-19:192 |
| Tuesday_19_Dec_2023 | Benign / Benign-Telnet | 2023-12-19 | 186 | 186 | 2023-12-19 09:00 | 2023-12-19 16:55 | 2023-12-19:186 |
| Tuesday_19_Dec_2023 | Benign / Benign-Systemic | 2023-12-19 | 958 | 958 | 2023-12-19 09:01 | 2023-12-19 16:59 | 2023-12-19:958 |
| Tuesday_19_Dec_2023 | Benign / Benign-Email-Receive | 2023-12-19 | 137 | 137 | 2023-12-19 09:08 | 2023-12-19 16:56 | 2023-12-19:137 |
| Tuesday_19_Dec_2023 | Benign / Benign-SSH | 2023-12-19 | 114 | 114 | 2023-12-19 09:11 | 2023-12-19 16:56 | 2023-12-19:114 |
| Tuesday_19_Dec_2023 | Attack / Attack-TCP-Flag-SYN-TFO | 2023-12-19 | 807 | 807 | 2023-12-19 09:30 | 2023-12-19 09:59 | 2023-12-19:807 |
| Tuesday_19_Dec_2023 | Attack / Attack-TCP-Flag-SYN-TIME | 2023-12-19 | 923 | 923 | 2023-12-19 10:00 | 2023-12-19 10:29 | 2023-12-19:923 |
| Tuesday_19_Dec_2023 | Benign / Benign-FTP | 2023-12-19 | 24 | 24 | 2023-12-19 10:03 | 2023-12-19 16:59 | 2023-12-19:24 |
| Tuesday_19_Dec_2023 | Attack / Attack-TCP-Flag-OSYN | 2023-12-19 | 722 | 722 | 2023-12-19 10:30 | 2023-12-19 10:59 | 2023-12-19:722 |
| Tuesday_19_Dec_2023 | Attack / Attack-TCP-Flag-OSYNP | 2023-12-19 | 740 | 740 | 2023-12-19 11:00 | 2023-12-19 11:29 | 2023-12-19:740 |

## Non-IAT columns with values in 1.4e9..2.2e9

- `total_payload_bytes`: 19
- `bwd_total_payload_bytes`: 14
- `fwd_total_payload_bytes`: 5
- `fwd_bulk_total_size`: 5
- `avg_fwd_bulk_rate`: 2
- `bytes_rate`: 1
- `fwd_bytes_rate`: 1
- `bwd_bytes_rate`: 1

Non-numeric columns (samples): `timestamp`: ['2023-12-18 08:56:39.743361', '2023-12-18 08:56:40.409563', '2023-12-18 08:56:39.214012']; `protocol`: ['TCP']; `delta_start`: ['not a complete handshake', '0.0000', '0.0013']; `handshake_duration`: ['not a complete handshake', '0.1111', '0.1080']; `label`: ['Attack', 'Benign', 'Suspicious']; `activity`: ['Attack-TCP-Valid-SYN', 'Benign', 'Benign-Web_Browsing_HTTP-S']

## Notes (hand checks, added after generation)

**Non-IAT epoch-range values are not timestamps** (`../nonIAT_handcheck.txt`): none lies within a day of its flow's
start. `total_payload_bytes` / `bulk_total_size` hits are genuine 1.5-2.2 GB transfers (1.2-1.6M packets, 50-300 s);
rate hits are ~0 s flows.
`label` has three values (Attack, Benign, Suspicious); `activity` gives the subtype, so classes are reported as
"label / activity". `delta_start` / `handshake_duration` use the string "not a complete handshake" as a placeholder.
Attack-TCP-BYPass-V1 is 95.6% 1-packet flows (132,330 of 138,368) and 95.93% leaked.
