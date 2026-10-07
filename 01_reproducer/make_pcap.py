from scapy.all import Ether, IP, TCP, Raw, wrpcap
C, S, T0 = "10.0.0.1", "10.0.0.2", 1519308000.0
# Pinned MACs so Ether() does not resolve them from live network state at
# write time (avoids getmacbyip warnings and makes repro.pcap byte-reproducible).
C_MAC, S_MAC = "00:00:00:00:00:01", "00:00:00:00:00:02"
def p(t, fwd, sport, flags, data=b""):
    src, dst = (C, S) if fwd else (S, C)
    smac, dmac = (C_MAC, S_MAC) if fwd else (S_MAC, C_MAC)
    sp, dp = (sport, 80) if fwd else (80, sport)
    pkt = Ether(src=smac, dst=dmac)/IP(src=src, dst=dst)/TCP(sport=sp, dport=dp, flags=flags)
    if data: pkt = pkt/Raw(data)
    pkt.time = t; return pkt
pk = []
pk += [p(T0, 1, 40001, "S")]                                          # A
t = T0+10; pk += [p(t,1,40002,"S"), p(t+.01,0,40002,"SA"), p(t+.02,0,40002,"R")]   # B
t = T0+20; pk += [p(t,1,40003,"S"), p(t+.01,0,40003,"SA"), p(t+.02,1,40003,"A"),
    p(t+.03,1,40003,"PA",b"GET / HTTP/1.0\r\n\r\n"), p(t+.05,0,40003,"PA",b"HTTP/1.0 200 OK\r\n\r\n"),
    p(t+.06,1,40003,"FA"), p(t+.07,0,40003,"FA"), p(t+.08,1,40003,"A")]  # C
t = T0+30; pk += [p(t+i*.01, i%2==0, 40004, f, b"x"*10 if f=="PA" else b"")
    for i, f in enumerate(["S","SA","A","PA","PA","PA","PA","R"])]      # D
pk += [p(T0+31536000, 1, 40005, "S")]                                 # E
wrpcap("repro.pcap", pk)
