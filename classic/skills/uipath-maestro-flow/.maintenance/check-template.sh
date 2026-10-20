#!/bin/bash
# Verify each CAPABILITY.md follows the canonical 6-section template:
#   1. When to use this capability
#   2. Critical rules
#   3. Workflow
#   4. Common tasks
#   5. Anti-patterns
#   6. References
# Usage: bash .maintenance/check-template.sh
# Exits non-zero if any CAPABILITY.md is missing a required section.

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT" || exit 1

REQUIRED_SECTIONS=(
  "When to use this capability"
  "Critical rules"
  "Workflow"
  "Common tasks"
  "Anti-patterns"
  "References"
)

failures=0
checked=0

while IFS= read -r capfile; do
  [ -z "$capfile" ] && continue
  checked=$((checked + 1))
  for section in "${REQUIRED_SECTIONS[@]}"; do
    if ! /usr/bin/grep -qE "^## $section\$" "$capfile"; then
      echo "MISSING_SECTION  ${capfile#$ROOT/}  ->  ## $section"
      failures=$((failures + 1))
    fi
  done
done < <(/usr/bin/find "$ROOT/references" -name "CAPABILITY.md" -type f | /usr/bin/sort)

echo ""
echo "capabilities_checked=$checked missing_sections=$failures"

[ "$failures" -gt 0 ] && exit 1
exit 0
