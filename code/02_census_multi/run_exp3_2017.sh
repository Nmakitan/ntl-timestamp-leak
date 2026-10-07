#!/bin/bash
# Single-seed 2x2 (+ fixB) retrain on 2017, one memory-capped process per run, as for 2018.
cd "$(dirname "$0")"; L=BCCC-CIC-IDS-2017/exp3/logs; mkdir -p $L
for run in "random leaky" "random fixA" "temporal leaky" "temporal fixA" "random fixB" "temporal fixB"; do
  set -- $run; tag="$1_$2_s0"
  [ -f BCCC-CIC-IDS-2017/exp3/$tag.json ] && continue
  echo "$(date '+%F %T') start $tag" >> $L/status.txt
  systemd-run --user --scope --quiet -p MemoryMax=6.5G -p MemorySwapMax=0 /usr/bin/time -v -o $L/$tag.time.txt \
      python3 exp3_2017.py $1 $2 0 > $L/$tag.log 2>&1
  echo "$(date '+%F %T') end $tag rc=$? peak_rss_kb=$(grep -o 'Maximum resident set size (kbytes): [0-9]*' $L/$tag.time.txt | grep -o '[0-9]*$')" >> $L/status.txt
done
echo "$(date '+%F %T') ALL DONE" >> $L/status.txt
