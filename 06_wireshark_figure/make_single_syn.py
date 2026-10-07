from scapy.all import Ether, IP, TCP, wrpcap
T0 = 1519308000.0  # 22 Feb 2018, 14:00:00 UTC
p = Ether(src="02:00:00:00:00:01", dst="02:00:00:00:00:02")/IP(src="192.168.10.5", dst="192.168.10.50")/TCP(sport=40000, dport=80, flags="S", seq=1000)
p.time = T0
wrpcap("single_syn.pcap", [p])
