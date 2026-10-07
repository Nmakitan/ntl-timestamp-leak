#!/bin/bash
# Pull finished runs from the second machine (laptop USER@REMOTE_HOST) every 5 min; never overwrites local results.
# Stops once the laptop queue has written ALL TIERS DONE and a final pull is done.
cd "$(dirname "$0")"; R=USER@REMOTE_HOST; RD=Desktop/ntl_models/results
NDONE=${1:-1}  # stop after the laptop log holds this many "ALL TIERS DONE" lines
while true; do
  rsync -a --ignore-existing --exclude '*.tmp' -e "ssh -o BatchMode=yes -o ConnectTimeout=10" $R:$RD/runs/ results/runs/ 2>/dev/null
  rsync -a --ignore-existing -e "ssh -o BatchMode=yes -o ConnectTimeout=10" $R:$RD/logs/ results/logs/ 2>/dev/null
  rsync -a -e "ssh -o BatchMode=yes -o ConnectTimeout=10" $R:$RD/QUEUE_STATUS.txt results/QUEUE_STATUS_laptop.txt 2>/dev/null
  [ "$(grep -c "ALL TIERS DONE" results/QUEUE_STATUS_laptop.txt 2>/dev/null)" -ge $NDONE ] && { python3 mc_report.py >/dev/null 2>&1; echo "$(date '+%F %T') laptop results synced (final)" >> results/QUEUE_STATUS.txt; exit 0; }
  sleep 300
done
