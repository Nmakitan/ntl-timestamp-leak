# Wireshark figure panels (made 2026-10-03 from the steps in ~/Desktop/wire)

Figures: `make_figures.py` builds the two paper figures from the panels. Captured from Wireshark 4.2.2 (run in X11 mode with a throwaway settings folder, epoch time display) with `xwd`;
terminal panels are the scripts' text output rendered as images. Leaked values are highlighted in yellow.

| file | shows |
|---|---|
| **fig_A_combined.png** | **paper figure**: A-left and A-right side by side; the arrival time of frame 45048 and the six identical IAT values boxed in red, the SQL_Injection label in orange |
| **fig_code_calculate_IAT.png** | **paper figure**: `calculate_IAT` (utils.py lines 20-27, upstream commit d99cd53) and one caller (IAT_related.py 11-17); the branch skipped for a single packet in yellow, the lines that pass the raw timestamp on in red, notes in a separate column |
| wire_A_left_cic2018_pcap.png | original CSE-CIC-IDS2018 capture, connection :59823 (13 packets), frame 45048 selected, "Epoch Arrival Time: 1519330475.230912000" highlighted |
| wire_A_right_bccc_row.png | the two published BCCC-CSE-CIC-IDS2018 rows for that connection: 12-packet flow (IATs 0.000021-5.06 s) and the 1-packet ghost flow, IAT max/min/total = 1519330475.230912, both labelled SQL_Injection |
| wire_B_left_single_syn.png | one synthetic SYN, "Epoch Arrival Time: 1519308000.000000000" highlighted |
| wire_B_right_csv.png | NTLFlowLyzer output for it: every combined and forward IAT mean/max/min/total/median/mode = 1519308000; backward = 0 |
| wire_C_left_repro_ghost.png | 21-packet reproducer, port 40003 (8 packets), trailing ACK frame 12, "Epoch Arrival Time: 1519308020.080000000" |
| wire_C_right_csv.png | NTLFlowLyzer rows for port 40003: 7-packet flow (IAT 0.01-0.07) and the 1-packet ghost flow (IAT = 1519308020.08) |

Corrections and caveats
- Figure A shows **13** packets, not the 15 the step list expected: frames 45043-45044 belong to other connections.
  13 = the published 12-packet flow + the 1-packet ghost flow, so the count matches the BCCC rows.
- Wireshark warns that UCAP172.31.69.28_22-02.pcap "appears to have been cut short in the middle of a packet". The file's
  sha256 matches the expected one and frames 45034-45048 are intact; the truncation is at the end of the file.
- Figure B was regenerated on 2026-10-03 with locally administered MACs (02:00:00:00:00:01 -> :02); the NTLFlowLyzer output
  is identical to the original (0 of 347 columns differ). The original files, which carry this machine's MAC, are in
  `old_with_local_mac/`: keep them out of any public release.
- Figure C still shows this machine's MAC (`LCFCElectron_0e:42:13`): the 21-packet reproducer pcap was built with scapy's
  default source MAC. Regenerate it before publishing Figure C, or use Figures A and B only.
- Figure C's synthetic packets all have sequence number 0, so Wireshark marks frames 7, 10, 11 as Keep-Alive /
  Retransmission / Illegal Segments. Harmless for the reproducer, but it looks malformed in a paper figure.

Suggested caption, Figure A: "Left: original CSE-CIC-IDS2018 capture of the SQL-injection victim (172.31.69.28),
22 Feb 2018; the final ACK of connection :59823 (frame 45048) arrives at 1519330475.230912 s. Right: the published
BCCC-CSE-CIC-IDS2018 rows for this connection. NTLFlowLyzer split the trailing ACK off as a separate one-packet flow,
labelled SQL_Injection, whose IAT max/min/total equal this arrival timestamp."
