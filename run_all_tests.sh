#!/usr/bin/env bash
# Run the test suites of all four projects. Usage:  bash run_all_tests.sh   [PYTHON=/path/to/python bash run_all_tests.sh]
set -u
cd "$(dirname "$0")"
PY="${PYTHON:-python3}"; case "$PY" in */*) PY="$(cd "$(dirname "$PY")" && pwd)/$(basename "$PY")";; esac
export PYTHONDONTWRITEBYTECODE=1 MPLBACKEND=Agg
fail=0; summary=""
for p in 01-design-basis-sld 03-load-sizing 04-shortcircuit-protection 05-bess; do
  echo "==================== $p"
  out=$(cd "$p" && "$PY" -m pytest -q -p no:cacheprovider 2>&1); rc=$?
  echo "$out" | tail -n 15
  line=$(echo "$out" | grep -E "passed|failed|error" | tail -n 1)
  summary+=$(printf "%-28s %s\n" "$p" "${line:-no result (rc=$rc)}")$'\n'
  [ $rc -ne 0 ] && fail=1
done
echo; echo "==================== SUMMARY"; printf "%s" "$summary"
[ $fail -eq 0 ] && echo "ALL TEST SUITES PASSED" || echo "SOME TEST SUITES FAILED"
exit $fail
