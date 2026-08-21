#!/bin/bash
# Runs every script test suite. Exits non-zero if any suite fails.
cd "$(dirname "$0")" || exit 1
status=0
for t in */test_*.py; do
  echo "=== $t ==="
  if ! python3 "$t" | tail -1; then
    status=1
  fi
done
[ "$status" -eq 0 ] && echo "all suites passed" || echo "one or more suites failed"
exit "$status"
