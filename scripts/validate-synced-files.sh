#!/bin/bash
# Validate that every synced copy declared in .github/synced-files.yml is
# byte-for-byte equal to its canonical source.
#
# Usage:
#   scripts/validate-synced-files.sh
#
# Exit codes:
#   0  all copies match their sources (or manifest is empty)
#   1  drift detected, missing files, or manifest hygiene violation
#   2  yq is not installed (hard dependency)

set -u
cd "$(git rev-parse --show-toplevel)" || { echo "ERROR: not inside a git repo" >&2; exit 2; }

MANIFEST=".github/synced-files.yml"

if ! command -v yq >/dev/null 2>&1; then
  cat >&2 <<'EOF'
ERROR: yq is required but not found on PATH.

Install yq:
  Windows : winget install MikeFarah.yq
  macOS   : brew install yq
  Linux   : sudo apt install yq      (or download from https://github.com/mikefarah/yq/releases)
EOF
  exit 2
fi

if [ ! -f "$MANIFEST" ]; then
  echo "ERROR: manifest not found: $MANIFEST" >&2
  exit 1
fi

GROUPS_COUNT=$(yq '.groups | length' "$MANIFEST")

if [ "$GROUPS_COUNT" -eq 0 ]; then
  echo "No synced groups configured in $MANIFEST."
  exit 0
fi

FAILED=0
ALL_SOURCES=()
ALL_COPIES=()

for i in $(seq 0 $((GROUPS_COUNT - 1))); do
  SOURCE=$(yq ".groups[$i].source" "$MANIFEST")
  COPIES_COUNT=$(yq ".groups[$i].copies | length" "$MANIFEST")

  if [ -z "$SOURCE" ] || [ "$SOURCE" = "null" ]; then
    echo "❌ group #$i: missing 'source' field" >&2
    FAILED=1
    continue
  fi

  ALL_SOURCES+=("$SOURCE")

  if [ ! -f "$SOURCE" ]; then
    echo "❌ group #$i: source not found: $SOURCE" >&2
    FAILED=1
    continue
  fi

  if [ "$COPIES_COUNT" -eq 0 ]; then
    echo "❌ group #$i ($SOURCE): no copies declared (empty group)" >&2
    FAILED=1
    continue
  fi

  for j in $(seq 0 $((COPIES_COUNT - 1))); do
    COPY=$(yq ".groups[$i].copies[$j]" "$MANIFEST")
    ALL_COPIES+=("$COPY")

    if [ ! -f "$COPY" ]; then
      echo "❌ $COPY: copy not found (declared in group #$i, source $SOURCE)" >&2
      FAILED=1
      continue
    fi

    if cmp -s "$SOURCE" "$COPY"; then
      echo "✓ $COPY matches $SOURCE"
    else
      echo "❌ $COPY drifted from $SOURCE" >&2
      diff -u "$SOURCE" "$COPY" >&2 || true
      FAILED=1
    fi
  done
done

# Hygiene check 1: a path must not appear as both a source and a copy (no transitivity)
for src in "${ALL_SOURCES[@]}"; do
  for cpy in "${ALL_COPIES[@]}"; do
    if [ "$src" = "$cpy" ]; then
      echo "❌ transitive sync detected: '$src' is both a source and a copy" >&2
      FAILED=1
    fi
  done
done

# Hygiene check 2: a copy path must not appear in two groups (single-source guarantee)
DUPES=$(printf '%s\n' "${ALL_COPIES[@]}" | sort | uniq -d)
if [ -n "$DUPES" ]; then
  while IFS= read -r dupe; do
    echo "❌ copy listed in two groups: $dupe" >&2
    FAILED=1
  done <<< "$DUPES"
fi

if [ "$FAILED" -eq 1 ]; then
  echo "" >&2
  echo "Synced-files validation failed." >&2
  echo "Run \`bash scripts/sync-files.sh --apply\` to refresh copies from sources, then commit." >&2
  exit 1
fi

exit 0
