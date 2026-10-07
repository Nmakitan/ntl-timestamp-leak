#!/bin/bash
# Tiered queue for the model comparison. Model-major order so every dataset gets each cheap model first.
# One capped process per run; resumable (skips existing JSON); a failed run is logged and the queue continues.
# Work can be split across machines:
#   DATASETS="d2017 cpacket" MODELS="lr xgb" TIERS="tier1" PY=venv/bin/python ./mc_queue.sh
#   VARIANTS="dropIAT" limits the training variants (default: leaky fixA).
#   results/ASSIGNED_ELSEWHERE.txt: one glob per line (e.g. d2017_*_lr_*); matching runs are skipped here.
# numpy madvises big arrays for THP; with defrag=madvise and fragmented RAM that means direct-compaction stalls,
# which systemd-oomd reads as memory pressure and kills the run (rc 137). Disable it.
export NUMPY_MADVISE_HUGEPAGE=0
cd "$(dirname "$0")"; L=results/logs; mkdir -p $L results/runs; S=results/QUEUE_STATUS.txt
PY=${PY:-python3}; DATASETS=${DATASETS:-d2018 d2017 cpacket}; TIERS=${TIERS:-tier1 tier2}; VARIANTS=${VARIANTS:-leaky fixA}; HOST=$(hostname)
elsewhere() {
  [ -f results/ASSIGNED_ELSEWHERE.txt ] || return 1
  while read -r g; do [ -n "$g" ] && [[ $1 == $g ]] && return 0; done < results/ASSIGNED_ELSEWHERE.txt; return 1
}
run() {  # dataset split model variant
  tag="$1_$2_$3_$4"; [ -f results/runs/$tag.json ] && return; elsewhere $tag && return
  echo "$(date '+%F %T') [$HOST] start $tag" >> $S
  for attempt in 1 2 3; do  # rc 137 = SIGKILL, normally systemd-oomd reacting to memory pressure
    systemd-run --user --scope --quiet -p MemoryMax=6.5G -p MemorySwapMax=0 /usr/bin/time -v -o $L/$tag.time.txt \
        $PY mc_run.py $1 $2 $3 $4 > $L/$tag.log 2>&1
    rc=$?; [ $rc -ne 137 ] || [ $attempt -eq 3 ] && break
    echo "$(date '+%F %T') [$HOST] KILLED $tag rc=137 (attempt $attempt), retrying in 120 s" >> $S; sleep 120
  done
  pk=$(grep -o 'Maximum resident set size (kbytes): [0-9]*' $L/$tag.time.txt 2>/dev/null | grep -o '[0-9]*$')
  w=$(grep -c "^WARNING" $L/$tag.log); echo "$(date '+%F %T') [$HOST] end $tag rc=$rc peak_rss_kb=$pk warnings=$w" >> $S
  [ $rc -ne 0 ] && echo "$(date '+%F %T') [$HOST] FAILED $tag (see $L/$tag.log)" >> $S
}
tier() {  # name, models...
  name=$1; shift; [[ " $TIERS " == *" $name "* ]] || return
  echo "$(date '+%F %T') [$HOST] === $name ===" >> $S
  for m in "$@"; do
    [ -n "$MODELS" ] && [[ " $MODELS " != *" $m "* ]] && continue
    for d in $DATASETS; do for s in random temporal; do for v in $VARIANTS; do run $d $s $m $v; done; done; done
  done
  $PY mc_report.py > /dev/null 2>&1; echo "$(date '+%F %T') [$HOST] $name complete" >> $S
}
tier tier1 gnb dt lr xgb
tier tier2 rf linsvc mlp
tier tierknn knn  # run only on request: TIERS=tierknn (slow: full test sets)
tier tierfull rffull xgbfull  # run only on request: TIERS=tierfull DATASETS=d2018 (full training split)
echo "$(date '+%F %T') [$HOST] ALL TIERS DONE ($TIERS; datasets: $DATASETS${MODELS:+; models: $MODELS}; variants: $VARIANTS)" >> $S
