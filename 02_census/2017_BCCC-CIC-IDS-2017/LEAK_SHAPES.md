# What the leaked rows are: BCCC-CIC-IDS-2017

Every leaked row (any IAT > 1e9) classified by packet counts, TCP flags (summed over both directions) and payload. Script `leak_shapes.py`; full counts `leak_shapes_counts.csv`, shares `leak_shapes_share_of_leaked.csv`.

## Coarse view: share of each class's leaked rows

| class | rows | leaked | % leaked | ghost / fragment (ACK, RST, FIN, teardown) | connection attempt (SYN, SYN->RST, SYN->SYN-ACK) | carries payload (data packet or session) | other, no payload |
|---|---:|---:|---:|---:|---:|---:|---:|
| Benign | 1,786,239 | 627,343 | 35.1 | 65.3 | 0.9 | 28.9 | 4.8 |
| Botnet_ARES | 5,508 | 4,613 | 83.8 | 15.3 | 84.7 | 0.0 | 0.0 |
| DDoS_LOIT | 95,733 | 50 | 0.1 | 98.0 | 0.0 | 2.0 | 0.0 |
| DoS_GoldenEye | 8,364 | 523 | 6.3 | 99.6 | 0.2 | 0.0 | 0.2 |
| DoS_Hulk | 349,240 | 132,146 | 37.8 | 99.0 | 0.0 | 1.0 | 0.0 |
| DoS_Slowhttptest | 6,860 | 1,981 | 28.9 | 90.0 | 0.0 | 10.0 | 0.0 |
| DoS_Slowloris | 5,177 | 1,017 | 19.6 | 97.5 | 2.5 | 0.0 | 0.0 |
| FTP-Patator | 9,531 | 5,527 | 58.0 | 99.4 | 0.0 | 0.6 | 0.0 |
| Heartbleed | 12 | 4 | 33.3 | 100.0 | 0.0 | 0.0 | 0.0 |
| Port_Scan | 161,323 | 161,109 | 99.9 | 0.6 | 99.2 | 0.0 | 0.2 |
| SSH-Patator | 5,949 | 2,955 | 49.7 | 99.8 | 0.0 | 0.0 | 0.2 |
| Web_Brute_Force | 2,734 | 1,366 | 50.0 | 100.0 | 0.0 | 0.0 | 0.0 |
| Web_SQL_Injection | 24 | 11 | 45.8 | 100.0 | 0.0 | 0.0 | 0.0 |
| Web_XSS | 1,358 | 679 | 50.0 | 100.0 | 0.0 | 0.0 | 0.0 |
| **ALL** | 2,438,052 | 939,324 | 38.5 | 59.2 | 18.0 | 19.5 | 3.3 |

## Detailed categories: share of each class's leaked rows (%; categories under 0.5% everywhere omitted)

| class | lone SYN | lone RST | lone FIN | lone ACK, no payload (ghost ACK) | SYN -> RST pair (probe/refused) | FIN/RST teardown pair | 1+1 with payload | 1+1 other | multi-packet with payload (session) | repeated SYNs, no payload | multi-packet, no payload |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| Benign | 0.0 | 18.7 | 1.1 | 44.0 | 0.7 | 1.5 | 27.4 | 2.1 | 1.4 | 0.2 | 2.8 |
| Botnet_ARES |  |  |  | 15.3 | 84.7 |  |  |  |  | 0.0 |  |
| DDoS_LOIT |  | 98.0 |  |  |  |  |  |  | 2.0 |  |  |
| DoS_GoldenEye |  | 98.5 |  | 1.1 |  |  |  | 0.2 |  | 0.2 |  |
| DoS_Hulk |  | 96.8 |  |  |  | 2.2 | 0.9 |  | 0.0 | 0.0 | 0.0 |
| DoS_Slowhttptest |  | 89.3 | 0.1 | 0.6 |  |  | 0.1 |  | 10.0 |  |  |
| DoS_Slowloris | 2.5 | 96.5 |  | 1.0 |  | 0.1 |  |  |  |  |  |
| FTP-Patator |  | 54.8 | 0.9 | 0.2 |  | 43.6 | 0.5 |  | 0.1 |  |  |
| Heartbleed |  | 100.0 |  |  |  |  |  |  |  |  |  |
| Port_Scan | 0.6 | 0.5 |  | 0.1 | 98.1 |  | 0.0 |  |  | 0.6 |  |
| SSH-Patator |  | 0.1 |  | 99.3 |  | 0.4 |  | 0.1 |  |  | 0.1 |
| Web_Brute_Force |  | 0.1 |  | 99.9 |  |  |  |  |  |  |  |
| Web_SQL_Injection |  |  |  | 100.0 |  |  |  |  |  |  |  |
| Web_XSS |  | 0.1 |  | 99.9 |  |  |  |  |  |  |  |
| ALL | 0.1 | 26.9 | 0.8 | 30.0 | 17.7 | 1.6 | 18.5 | 1.4 | 1.0 | 0.2 | 1.9 |

## Interpretation
- Pooled over the 12 attack classes other than Port_Scan and Botnet_ARES (146,259 leaked rows): **98.9% fragments**
  (lone RST 27-100% for DoS / Heartbleed / FTP, ghost ACKs 99-100% for SSH-Patator and the three web attacks,
  FIN/RST teardown pairs 44% for FTP-Patator), **0.0% connection attempts, 1.0% with payload**. These rows carry no
  attack content; the attack sessions themselves (multi-packet, with payload) are never leaked.
- **Exceptions: Port_Scan and Botnet_ARES** (165,722 leaked rows): 98.8% are single SYN -> RST/ACK pairs (probes,
  refused connections). For a port scan that *is* the attack behaviour, so here the leak sits on genuinely
  attack-specific rows, not on fragments.
- Benign leaked rows differ: 65.3% fragments, but 28.9% carry payload (mostly "1+1 with payload").
