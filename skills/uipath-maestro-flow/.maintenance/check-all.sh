#!/bin/bash
# Run the full audit suite for this skill.
# Usage: bash .maintenance/check-all.sh
#
# Runs each checker in turn and prints its summary line.
# Exits non-zero if any checker fails. Continues running all checkers
# even when one fails — the goal is to surface every issue in a single pass.

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT" || exit 1

CHECKERS=(
  "check-links.sh"
  "check-link-text.sh"
  "check-anchors.sh"
  "check-depth.sh"
  "check-template.sh"
  "check-orphans.sh"
  "check-plugin-pairs.sh"
)

overall=0

for checker in "${CHECKERS[@]}"; do
  echo "=== $checker ==="
  if ! /bin/bash ".maintenance/$checker"; then
    overall=1
  fi
  echo ""
done

if [ "$overall" -eq 0 ]; then
  echo "All checks passed."
else
  echo "One or more checks failed. See output above for details."
fi

exit "$overall"
