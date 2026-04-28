#!/bin/bash
# Propagate canonical source files to their byte-identical copies as declared
# in .github/synced-files.yml.
#
# Usage:
#   scripts/sync-files.sh --apply
#       Refresh every copy from its source. Idempotent.
#
#   scripts/sync-files.sh --add <source-path> <copy-path>
#       Register a new sync (appends to manifest, performs the initial copy).
#       Refuses if <copy-path> already exists, or if either path is already
#       in the manifest in a conflicting role.
#
# yq is required.

set -u
cd "$(git rev-parse --show-toplevel)" || { echo "ERROR: not inside a git repo" >&2; exit 2; }

MANIFEST=".github/synced-files.yml"

require_yq() {
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
}

require_manifest() {
  if [ ! -f "$MANIFEST" ]; then
    echo "ERROR: manifest not found: $MANIFEST" >&2
    exit 1
  fi
}

usage() {
  cat <<'EOF'
Usage:
  scripts/sync-files.sh --apply
  scripts/sync-files.sh --add <source-path> <copy-path>
EOF
}

cmd_apply() {
  require_yq
  require_manifest

  local groups_count source copies_count copy
  groups_count=$(yq '.groups | length' "$MANIFEST")

  if [ "$groups_count" -eq 0 ]; then
    echo "No synced groups configured in $MANIFEST. Nothing to do."
    return 0
  fi

  local refreshed=0 unchanged=0
  for i in $(seq 0 $((groups_count - 1))); do
    source=$(yq ".groups[$i].source" "$MANIFEST")
    if [ ! -f "$source" ]; then
      echo "ERROR: source not found: $source" >&2
      exit 1
    fi
    copies_count=$(yq ".groups[$i].copies | length" "$MANIFEST")
    for j in $(seq 0 $((copies_count - 1))); do
      copy=$(yq ".groups[$i].copies[$j]" "$MANIFEST")
      if [ -f "$copy" ] && cmp -s "$source" "$copy"; then
        unchanged=$((unchanged + 1))
        continue
      fi
      mkdir -p "$(dirname "$copy")"
      cp -f "$source" "$copy"
      echo "✓ refreshed $copy from $source"
      refreshed=$((refreshed + 1))
    done
  done

  echo ""
  echo "Done. $refreshed refreshed, $unchanged already in sync."
}

cmd_add() {
  local source="$1"
  local copy="$2"

  require_yq
  require_manifest

  if [ -z "$source" ] || [ -z "$copy" ]; then
    usage >&2
    exit 1
  fi

  if [ ! -f "$source" ]; then
    echo "ERROR: source not found: $source" >&2
    exit 1
  fi

  if [ -f "$copy" ]; then
    echo "ERROR: copy already exists: $copy (refusing to overwrite)" >&2
    echo "       If you intended to convert an existing file into a synced copy, delete it first and re-run --add." >&2
    exit 1
  fi

  # Reject if source is already a copy in some group (no transitivity)
  local source_as_copy
  source_as_copy=$(yq '.groups[].copies[] | select(. == "'"$source"'")' "$MANIFEST")
  if [ -n "$source_as_copy" ]; then
    echo "ERROR: '$source' is already a copy in the manifest -- cannot also be a source (no transitive sync)." >&2
    exit 1
  fi

  # Reject if copy is already a source or copy anywhere
  local copy_as_source
  copy_as_source=$(yq '.groups[].source | select(. == "'"$copy"'")' "$MANIFEST")
  if [ -n "$copy_as_source" ]; then
    echo "ERROR: '$copy' is already a source in the manifest." >&2
    exit 1
  fi
  local copy_as_copy
  copy_as_copy=$(yq '.groups[].copies[] | select(. == "'"$copy"'")' "$MANIFEST")
  if [ -n "$copy_as_copy" ]; then
    echo "ERROR: '$copy' is already a copy in the manifest." >&2
    exit 1
  fi

  # Either extend an existing group with the same source, or create a new group.
  local existing_index
  existing_index=$(yq '.groups | to_entries | map(select(.value.source == "'"$source"'")) | .[0].key // ""' "$MANIFEST")

  if [ -n "$existing_index" ] && [ "$existing_index" != "null" ]; then
    yq -i '.groups['"$existing_index"'].copies += ["'"$copy"'"] | .groups['"$existing_index"'].copies |= sort' "$MANIFEST"
    echo "Extended existing group for source $source with copy $copy."
  else
    yq -i '.groups += [{"source": "'"$source"'", "copies": ["'"$copy"'"]}] | .groups |= sort_by(.source)' "$MANIFEST"
    echo "Added new group: source=$source, copy=$copy."
  fi

  mkdir -p "$(dirname "$copy")"
  cp -f "$source" "$copy"
  echo "✓ created $copy as a byte-identical copy of $source"
  echo ""
  echo "Manifest updated: $MANIFEST"
  echo "Don't forget: \`git update-index --chmod=+x\` is not needed for .md copies, only .sh files."
}

case "${1:-}" in
  --apply)
    cmd_apply
    ;;
  --add)
    if [ "$#" -ne 3 ]; then
      usage >&2
      exit 1
    fi
    cmd_add "$2" "$3"
    ;;
  -h|--help|"")
    usage
    ;;
  *)
    echo "ERROR: unknown subcommand: $1" >&2
    usage >&2
    exit 1
    ;;
esac
