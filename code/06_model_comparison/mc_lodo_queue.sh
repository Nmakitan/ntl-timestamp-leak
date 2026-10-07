#!/bin/bash
# Leave-one-day-out runs on d2017, split across machines by position in the job list.
#   PART=0 NPARTS=2 PY=python3 ./mc_lodo_queue.sh      (this machine takes jobs 0, 2, 4, ...)
#   MODELS="rf" FOLDS="lodo_0705 lodo_0703" ./mc_lodo_queue.sh   (defaults: dt gnb; all five folds)
# Same per-run cap and logging as mc_queue.sh; JOBS runs in parallel (default 2, ~2 GB each); skips existing JSON.
export NUMPY_MADVISE_HUGEPAGE=0
cd "$(dirname "$0")"; L=results/logs; mkdir -p $L results/runs; S=results/QUEUE_STATUS.txt
PY=${PY:-python3}; MODELS=${MODELS:-dt gnb}; FOLDS=${FOLDS:-lodo_0705 lodo_0707 lodo_0703 lodo_0704 lodo_0706}; PART=${PART:-0}; NPARTS=${NPARTS:-1}; JOBS=${JOBS:-2}; HOST=$(hostname)
one() {  # split model variant
  tag="d2017_$1_$2_$3"; [ -f results/runs/$tag.json ] && return
  echo "$(date '+%F %T') [$HOST] start $tag" >> $S
  systemd-run --user --scope --quiet -p MemoryMax=6.5G -p MemorySwapMax=0 /usr/bin/time -v -o $L/$tag.time.txt \
      $PY mc_run.py d2017 $1 $2 $3 > $L/$tag.log 2>&1
  rc=$?; pk=$(grep -o 'Maximum resident set size (kbytes): [0-9]*' $L/$tag.time.txt 2>/dev/null | grep -o '[0-9]*$')
  echo "$(date '+%F %T') [$HOST] end $tag rc=$rc peak_rss_kb=$pk" >> $S
  [ $rc -ne 0 ] && echo "$(date '+%F %T') [$HOST] FAILED $tag (see $L/$tag.log)" >> $S
}
export -f one; export PY S L HOST
i=0
for s in $FOLDS; do for m in $MODELS; do for v in leaky fixA; do
  [ $((i % NPARTS)) -eq $PART ] && echo "$s $m $v"; i=$((i + 1))
done; done; done | xargs -P $JOBS -L 1 bash -c 'one "$@"' _
echo "$(date '+%F %T') [$HOST] LODO PART $PART/$NPARTS DONE" >> $S
