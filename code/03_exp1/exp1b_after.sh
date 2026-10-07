#!/bin/bash
# Waits for the exp1b driver to finish, then builds the RF/KNN/ensemble report.
cd "$(dirname "$0")"
while pgrep -f "^python3 exp1b_run" >/dev/null; do sleep 60; done
{ echo "driver finished $(date '+%F %T')"; tail -3 exp1b/driver.log; echo; python3 exp1b_report.py; echo "REPORT EXIT $?"; } > exp1b/report.txt 2>&1
