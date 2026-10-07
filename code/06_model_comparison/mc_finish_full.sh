#!/bin/bash
# One-off: after the full-train (rffull, xgbfull) queue on 2018, regenerate CIs, pooled CSV, summary, master, data dir.
cd "$(dirname "$0")"; LOG=results/logs/finish_full.log; export NUMPY_MADVISE_HUGEPAGE=0
while kill -0 1040920 2>/dev/null; do sleep 120; done
{ echo "$(date '+%F %T') finishing full-train tier"
  python3 mc_bootstrap.py 1000 && python3 mc_pool.py && python3 mc_report.py > /dev/null && echo "summary regenerated"
  python3 ~/Desktop/build_NTL_master.py && python3 ~/Desktop/organize_NTL_data.py
  echo "$(date '+%F %T') done"; } >> $LOG 2>&1
echo "$(date '+%F %T') [pc] full-train finishing steps done (see $LOG)" >> results/QUEUE_STATUS.txt
