#!/bin/bash
# Verify every plugin folder under references/author/references/plugins/ has both
# `planning.md` and `impl.md` (the per-plugin convention from skill-structure.md).
# Usage: bash .maintenance/check-plugin-pairs.sh
# Output: MISSING lines per failure, then "plugins_checked=N missing_files=M" summary.
#
# Exits non-zero if any plugin folder is missing planning.md or impl.md.

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT" || exit 1

PLUGINS_DIR="$ROOT/references/author/references/plugins"

if [ ! -d "$PLUGINS_DIR" ]; then
  echo "ERROR: plugins directory not found at $PLUGINS_DIR" >&2
  exit 2
fi

REQUIRED_FILES=("planning.md" "impl.md")

failures=0
checked=0

while IFS= read -r plugin_dir; do
  [ -z "$plugin_dir" ] && continue
  checked=$((checked + 1))
  for required in "${REQUIRED_FILES[@]}"; do
    if [ ! -f "$plugin_dir/$required" ]; then
      echo "MISSING  ${plugin_dir#$ROOT/}/$required"
      failures=$((failures + 1))
    fi
  done
done < <(/usr/bin/find "$PLUGINS_DIR" -mindepth 1 -maxdepth 1 -type d | /usr/bin/sort)

echo ""
echo "plugins_checked=$checked missing_files=$failures"

[ "$failures" -gt 0 ] && exit 1
exit 0
