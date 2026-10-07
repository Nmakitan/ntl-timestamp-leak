# What the leaked rows are: BCCC-cPacket-Cloud-DDoS-2024

Every leaked row (any IAT > 1e9) classified by packet counts, TCP flags (summed over both directions) and payload. Script `leak_shapes.py`; full counts `leak_shapes_counts.csv`, shares `leak_shapes_share_of_leaked.csv`.

## Coarse view: share of each class's leaked rows

| class | rows | leaked | % leaked | ghost / fragment (ACK, RST, FIN, teardown) | connection attempt (SYN, SYN->RST, SYN->SYN-ACK) | carries payload (data packet or session) | other, no payload |
|---|---:|---:|---:|---:|---:|---:|---:|
| Attack / Attack-Killall-v2 | 6,033 | 1,453 | 24.1 | 61.9 | 35.9 | 2.1 | 0.2 |
| Attack / Attack-Killer-TCP | 6,254 | 1,788 | 28.6 | 47.3 | 52.6 | 0.0 | 0.1 |
| Attack / Attack-TCP-BYPass-V1 | 138,368 | 132,732 | 95.9 | 0.8 | 99.2 | 0.0 | 0.0 |
| Attack / Attack-TCP-Control | 5,744 | 1,502 | 26.1 | 46.9 | 50.7 | 1.3 | 1.1 |
| Attack / Attack-TCP-Flag-ACK | 10,683 | 1,741 | 16.3 | 55.7 | 44.1 | 0.0 | 0.2 |
| Attack / Attack-TCP-Flag-ACK-PSH | 7,482 | 1,666 | 22.3 | 49.5 | 49.9 | 0.1 | 0.5 |
| Attack / Attack-TCP-Flag-MIX | 7,416 | 1,724 | 23.2 | 42.3 | 57.2 | 0.3 | 0.2 |
| Attack / Attack-TCP-Flag-OSYN | 867 | 722 | 83.3 | 28.4 | 70.6 | 0.3 | 0.7 |
| Attack / Attack-TCP-Flag-OSYNP | 890 | 740 | 83.1 | 18.9 | 80.8 | 0.0 | 0.3 |
| Attack / Attack-TCP-Flag-RST-ACK | 1,445 | 596 | 41.2 | 20.5 | 79.4 | 0.2 | 0.0 |
| Attack / Attack-TCP-Flag-SYN | 7,845 | 1,765 | 22.5 | 57.1 | 42.9 | 0.0 | 0.0 |
| Attack / Attack-TCP-Flag-SYN-ACK | 8,204 | 1,595 | 19.4 | 48.3 | 51.5 | 0.0 | 0.2 |
| Attack / Attack-TCP-Flag-SYN-TFO | 3,631 | 807 | 22.2 | 32.5 | 66.5 | 0.6 | 0.4 |
| Attack / Attack-TCP-Flag-SYN-TIME | 1,360 | 923 | 67.9 | 37.6 | 61.1 | 0.8 | 0.5 |
| Attack / Attack-TCP-IGMP | 7,251 | 1,634 | 22.5 | 59.6 | 39.3 | 0.7 | 0.4 |
| Attack / Attack-TCP-SYN | 6,953 | 1,450 | 20.9 | 60.0 | 39.8 | 0.1 | 0.1 |
| Attack / Attack-TCP-Valid-SYN | 8,043 | 1,459 | 18.1 | 61.3 | 38.5 | 0.2 | 0.0 |
| Benign / Benign | 302,284 | 244,792 | 81.0 | 25.4 | 74.5 | 0.0 | 0.0 |
| Benign / Benign-Email-Receive | 1,395 | 935 | 67.0 | 31.2 | 56.8 | 0.0 | 12.0 |
| Benign / Benign-Email-Send | 1,938 | 1,151 | 59.4 | 65.2 | 34.2 | 0.1 | 0.5 |
| Benign / Benign-FTP | 483 | 307 | 63.6 | 61.6 | 34.5 | 3.6 | 0.3 |
| Benign / Benign-SSH | 2,985 | 1,443 | 48.3 | 69.7 | 28.5 | 1.7 | 0.1 |
| Benign / Benign-Systemic | 48,074 | 8,163 | 17.0 | 56.6 | 41.4 | 1.0 | 1.0 |
| Benign / Benign-Telnet | 4,768 | 3,996 | 83.8 | 31.1 | 68.9 | 0.0 | 0.0 |
| Benign / Benign-Web_Browsing_HTTP-S | 51,272 | 27,810 | 54.2 | 86.2 | 6.9 | 2.5 | 4.3 |
| Suspicious / Suspicious | 59,106 | 15,533 | 26.3 | 32.0 | 67.4 | 0.2 | 0.4 |
| **ALL** | 700,774 | 458,427 | 65.4 | 24.2 | 75.2 | 0.2 | 0.3 |

## Detailed categories: share of each class's leaked rows (%; categories under 0.5% everywhere omitted)

| class | lone SYN | lone RST | lone FIN | lone ACK, no payload (ghost ACK) | SYN -> RST pair (probe/refused) | SYN -> SYN-ACK pair | FIN/RST teardown pair | 1+1 with payload | 1+1 other | multi-packet with payload (session) | repeated SYNs, no payload | multi-packet, no payload |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| Attack / Attack-Killall-v2 | 16.2 | 54.1 |  | 7.2 | 19.1 |  | 0.6 | 0.6 | 0.1 | 1.1 | 0.4 | 0.1 |
| Attack / Attack-Killer-TCP | 15.0 | 45.7 |  | 1.6 | 36.5 |  |  |  |  |  | 1.1 | 0.1 |
| Attack / Attack-TCP-BYPass-V1 | 98.9 | 0.7 |  | 0.0 | 0.3 |  | 0.0 |  |  | 0.0 | 0.0 |  |
| Attack / Attack-TCP-Control | 24.2 | 39.3 |  | 6.4 | 25.8 | 0.3 | 1.2 |  | 0.1 | 1.2 | 0.3 | 1.0 |
| Attack / Attack-TCP-Flag-ACK | 21.7 | 51.9 |  | 2.1 | 21.9 | 0.1 | 1.7 |  | 0.1 |  | 0.3 | 0.1 |
| Attack / Attack-TCP-Flag-ACK-PSH | 24.4 | 47.4 |  | 2.0 | 24.9 |  | 0.1 |  | 0.2 | 0.1 | 0.6 | 0.2 |
| Attack / Attack-TCP-Flag-MIX | 25.1 | 39.1 |  | 2.5 | 31.4 | 0.2 | 0.7 | 0.1 | 0.2 | 0.2 | 0.5 | 0.1 |
| Attack / Attack-TCP-Flag-OSYN | 31.3 | 20.1 |  | 8.0 | 37.1 |  | 0.3 | 0.1 |  | 0.1 | 2.1 | 0.7 |
| Attack / Attack-TCP-Flag-OSYNP | 29.3 | 15.1 |  | 3.8 | 48.2 |  |  |  | 0.1 |  | 3.0 | 0.1 |
| Attack / Attack-TCP-Flag-RST-ACK | 31.7 | 18.8 |  | 1.7 | 44.6 |  |  |  |  |  | 2.7 |  |
| Attack / Attack-TCP-Flag-SYN | 18.8 | 50.7 |  | 2.5 | 23.5 |  | 3.9 |  |  |  | 0.5 |  |
| Attack / Attack-TCP-Flag-SYN-ACK | 21.1 | 46.8 |  | 1.4 | 30.0 |  | 0.1 |  | 0.1 |  | 0.4 | 0.1 |
| Attack / Attack-TCP-Flag-SYN-TFO | 31.7 | 26.4 |  | 5.9 | 31.6 |  | 0.1 | 0.5 |  | 0.1 | 3.1 | 0.4 |
| Attack / Attack-TCP-Flag-SYN-TIME | 22.9 | 28.8 |  | 8.7 | 33.8 | 2.4 | 0.1 | 0.5 | 0.2 | 0.2 | 2.1 | 0.3 |
| Attack / Attack-TCP-IGMP | 16.6 | 51.0 |  | 4.0 | 22.2 |  | 4.6 |  | 0.2 | 0.7 | 0.4 | 0.2 |
| Attack / Attack-TCP-SYN | 14.1 | 53.9 |  | 2.7 | 25.0 |  | 3.4 | 0.1 |  | 0.1 | 0.6 |  |
| Attack / Attack-TCP-Valid-SYN | 17.6 | 60.6 |  | 0.8 | 20.3 |  |  | 0.1 |  |  | 0.5 |  |
| Benign / Benign | 31.4 | 25.4 |  | 0.0 | 26.4 | 0.0 | 0.0 | 0.0 |  | 0.0 | 16.7 | 0.0 |
| Benign / Benign-Email-Receive | 19.8 | 13.6 |  | 17.6 | 18.7 |  |  |  | 11.6 |  | 18.3 | 0.4 |
| Benign / Benign-Email-Send | 12.1 | 9.2 |  | 56.0 | 9.7 |  |  |  | 0.3 | 0.1 | 12.4 | 0.3 |
| Benign / Benign-FTP | 8.1 | 27.4 | 1.0 | 30.0 | 14.0 |  | 3.3 | 0.3 |  | 3.3 | 12.4 | 0.3 |
| Benign / Benign-SSH | 7.6 | 11.2 | 0.2 | 56.4 | 14.9 | 0.5 | 1.9 | 0.3 |  | 1.0 | 5.3 | 0.1 |
| Benign / Benign-Systemic | 10.6 | 48.2 | 0.5 | 2.2 | 13.0 |  | 5.6 | 0.7 | 0.0 | 0.2 | 17.8 | 1.0 |
| Benign / Benign-Telnet | 10.5 | 31.1 |  | 0.1 | 15.5 | 0.0 |  |  |  |  | 42.8 |  |
| Benign / Benign-Web_Browsing_HTTP-S | 1.8 | 36.3 | 0.5 | 48.6 | 2.6 | 0.0 | 0.8 | 0.4 | 1.2 | 2.0 | 2.4 | 3.2 |
| Suspicious / Suspicious | 33.8 | 27.7 | 0.0 | 3.1 | 32.2 | 0.1 | 1.2 | 0.1 | 0.1 | 0.1 | 1.2 | 0.3 |
| ALL | 48.1 | 20.2 | 0.0 | 3.7 | 17.2 | 0.0 | 0.3 | 0.1 | 0.1 | 0.1 | 9.9 | 0.2 |

## Interpretation
- Leaked attack rows carry almost no payload (0.1% over all attack subtypes).
- The 16 attack subtypes other than BYPass-V1 (21,565 leaked rows) all show the **same generic mix**: lone RST 39-61%,
  lone SYN 14-32%, SYN -> RST pairs 19-48%, ghost ACKs 1-9%; pooled 49.0% fragments, 50.3% connection attempts,
  0.4% payload. The mix does not follow the attack type: the leaked rows of the ACK, ACK-PSH and RST-ACK floods are
  not ACK or RST-ACK packets but the same SYN / RST shapes. Total-variation distance between the subtypes' category
  mixes: median 0.18; to Benign 0.26, to Suspicious 0.20. Benign and Suspicious leaked rows look alike too
  (~33% fragments, ~67% connection attempts, 0.2-0.3% payload). So the leaked rows carry no subtype-specific
  behaviour; what separates them is mainly when they occurred.
- **Exception: Attack-TCP-BYPass-V1** (132,732 leaked rows, 87% of all leaked attack rows): 98.9% lone SYNs. For a
  SYN-based attack the lone SYN may be the attack packet itself, so this class does not support the "no attack
  behaviour" reading.
