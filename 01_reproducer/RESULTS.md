# NTLFlowLyzer Step 1: minimal reproducer

Upstream `ahlashkari/NTLFlowLyzer` @ `d99cd5377faaed53b39450ce262652902501188d`, unmodified. Python 3.12.3, Linux.
pcap sha256: `61ea9c3ed384b17f1048a8546496660105882ed598079ca683a71bc4df8a3e87` (21 packets, 5 TCP conversations, T0 = 1519308000)

> Note: `make_pcap.py` pins Ethernet MAC addresses so `repro.pcap` regenerates bit-for-bit identically (sha256 above). The NTLFlowLyzer output (`repro_out.csv`) is unaffected by the MAC values.

Reproduce: `python make_pcap.py && ntlflowlyzer -c repro_config.json`

| Flow | Port | pkts (fwd/bwd) | Epoch-valued IAT columns | Value | = packet timestamp? |
|---|---|---|---|---|---|
| A lone SYN | 40001 | 1 (1/0) | `packets_IAT_*`, `fwd_packets_IAT_*` | 1519308000.0 | yes (T0) |
| B SYN/SYN-ACK/RST | 40002 | 3 (1/2) | `fwd_packets_IAT_*` only | 1519308010.0 | yes (T0+10) |
| C main | 40003 | 7 (4/3) | none | 0.01-0.04 | n/a |
| C ghost (trailing ACK) | 40003 | 1 (1/0) | `packets_IAT_*`, `fwd_packets_IAT_*` | 1519308020.08 | yes (T0+20.08) |
| D control | 40004 | 8 (4/4) | none | 0.01-0.02 | n/a |
| E lone SYN +1 yr | 40005 | 1 (1/0) | `packets_IAT_*`, `fwd_packets_IAT_*` | 1550844000.0 | yes (T0+31536000; E-A exactly 1 year) |

Affected columns per direction: mean, max, min, total, median, mode (std/variance/cov = 0, skewness = NaN).
A direction with 0 packets gets IAT = 0, not epoch, so the leak is specifically "exactly one packet in that direction".

## Findings
1. **IAT leak.** Any direction (or whole flow) with exactly one packet gets its absolute epoch timestamp as IAT.
   Root cause `NTLFlowLyzer/features/utils.py:20-27` (`calculate_IAT`): when `len(times) == 1` the list of raw timestamps is returned unchanged.
2. **Ghost flow.** Flow C is split in two (5 conversations -> 6 flows). The flow is closed as soon as both directions have sent FIN
   (`network_flow_capturer/network_flow_capturer.py:305-311`, `has_two_FIN_flags`), so the final ACK of the close starts a new 1-packet flow, which then also shows the leak.
3. **No dropped flows.** Both lone SYNs (A, E) appear in the output.
4. **Local-time rendering.** `timestamp` and the time in `flow_id` show 15:00 for 14:00 UTC (machine TZ Europe/Zagreb, CET in Feb). IAT values are true epoch seconds, unaffected.
5. Control flow D is fully clean.

## Fork comparison
Fork `Nmakitan/NTLFlowLyzer` @ `31c677cfb5982999410d728260995807102c4533` (upstream d99cd53 + 2 commits touching only
`network_flow_capturer.py` for continuous-batch polling), installed in a separate venv (`venv_fork`), run on the same pcap
(`repro_config_fork.json` -> `repro_out_fork.csv`, `run_fork.log`).
Result: same 6 flows, 347 columns, **byte-identical output to upstream** (`cmp` reports no difference).
The fork neither causes nor changes the IAT leak or the ghost flow.
