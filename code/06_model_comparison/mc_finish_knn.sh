#!/bin/bash
# One-off: after the overnight KNN queue (PC) and the final laptop sync, check the laptop for further disk corruption,
# then regenerate bootstrap CIs, pooled CSV, SUMMARY.md and the master file. Log: results/logs/finish_knn.log
cd "$(dirname "$0")"; LOG=results/logs/finish_knn.log; S=results/QUEUE_STATUS.txt
export NUMPY_MADVISE_HUGEPAGE=0
until grep -q "ALL TIERS DONE.*models: knn" $S && ! kill -0 3366448 2>/dev/null; do sleep 120; done
{
  echo "$(date '+%F %T') finishing KNN"
  echo "--- laptop integrity: sklearn files and data caches vs PC (expect 0 differences)"
  F="ntl_census_multi/BCCC-CIC-IDS-2017/exp3/cache/X.npy ntl_census_multi/BCCC-cPacket-Cloud-DDoS-2024/cache/X.npy ntl_census_multi/BCCC-CIC-IDS-2017/exp2_label/splits.npz ntl_census_multi/BCCC-cPacket-Cloud-DDoS-2024/exp2_activity/splits.npz"
  diff <(cd ~/Desktop && md5sum $F) <(ssh -n -o BatchMode=yes USER@REMOTE_HOST "cd ~/Desktop && md5sum $F") && echo "data caches: identical"
  diff <(cd ~/.local/lib/python3.12/site-packages && find sklearn -type f \( -name '*.so' -o -name '*.py' \) -print0 | sort -z | xargs -0 md5sum) \
       <(ssh -n -o BatchMode=yes USER@REMOTE_HOST "cd ~/ntl_models/venv/lib/python3.12/site-packages && find sklearn -type f \( -name '*.so' -o -name '*.py' \) -print0 | sort -z | xargs -0 md5sum") \
       > /dev/null && echo "sklearn files: identical" || echo "sklearn files: DIFFER (laptop disk problem continues)"
  python3 mc_bootstrap.py 1000 && python3 mc_pool.py && python3 mc_report.py > /dev/null && echo "summary regenerated"
  python3 ~/Desktop/build_NTL_master.py
  echo "$(date '+%F %T') done"
} >> $LOG 2>&1
echo "$(date '+%F %T') [pc] KNN finishing steps done (see $LOG)" >> $S
