# Leak census: BCCC-DLLayer-IDS-2025 (pass 1 only)

**NTLFlowLyzer output: no.** 17 CSV files in 11 class folders, 7.5 GB; 3 Benign files are empty (0 bytes:
Jul7, Jul8, Jul11). The 14 non-empty files share one 277-column header of layer-2 / frame features: `connection`,
`tcp_stream`, `protocol`, MAC address + vendor/OUI fields, `eth_type`, `time_delta`, `num_frame`, `sum_frame_len`,
per-protocol counters and ratios (ARP, DHCP, STP, CDP, 802.1Q), `label`. No IAT, `packets_count` or
`fwd/bwd_packets_count` columns. The extractor is not identifiable from the files (file names end in
`_features_combined_<date>`, which suggests a custom frame-level extractor run in Oct 2025).

## Epoch scan (one file, as the brief specifies)
File `STP_attack/Aug1-STP_features_combined_20251013_155048.csv`: 153,486 rows (Benign 136,843, STP attack 16,643).
Every numeric column scanned at three scales: seconds (1.4e9-2.2e9), milliseconds (1.4e12-2.2e12), microseconds
(1.4e15-2.2e15). Millisecond and microsecond scale: **no hits**. Second scale hits:

| column | rows in range | distinct values | in capture period (Jul-Aug 2025) | what it is |
|---|---:|---:|---:|---|
| arp_over_dhcp_ratio | 375 | 9 | 0 | ratio; round values (1.4e9, 1.5e9, 2.0e9) |
| stp_over_cdp_ratio | 160 | 8 | 0 | ratio; round values |
| dhcp_mean_transaction_id | 148 | 134 | 0 | random 32-bit DHCP transaction IDs |
| dhcp_min_transaction_id | 144 | 127 | 0 | same |
| dhcp_max_transaction_id | 136 | 121 | 0 | same |
| sum_frame_len_div_time | 67 | 33 | 0 | rate (bytes / time) |
| dhcp_sum_transaction_id | 51 | 51 | 0 | sum of transaction IDs |
| cdp_over_stp_ratio | 17 | 6 | 0 | ratio; round values |

None of the values lie in the capture period, and they decode to dates spread over 2014-2038.
**No timestamp leak.** Per the brief, this dataset stops at pass 1. (The round-valued ratios, 6-9 distinct values,
look like division by a tiny epsilon: a separate quality issue, not a leak.)

Script: `epoch_scan.py`; output: `epoch_scan_STP.txt`.
