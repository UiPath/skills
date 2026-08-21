#!/bin/bash
# Find .md files under references/ that no other .md file links to.
# Usage: bash .maintenance/check-orphans.sh
# Output: ORPHAN lines per orphan, then "files_checked=N orphans=M" summary.
#
# Skips:
# - SKILL.md (the entry point — has no inbound links by design)
# - CAPABILITY.md files (linked from SKILL.md and peer indexes)
# - Links inside fenced code blocks (```...```)
# - Links inside inline code spans (`...`)
#
# A file is considered "linked to" if any other .md file references it via
# `[text](path)` or via a folder link (`[text](folder/)`) that resolves to its parent dir.
#
# Exits non-zero if any orphans found.

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT" || exit 1

# Per-file: strip fenced code blocks and inline code spans, then extract links.
extract_links() {
  /usr/bin/awk '
    /^```/ { fenced = !fenced; next }
    !fenced {
      gsub(/`[^`]*`/, "", $0)
      while (match($0, /\]\([^)]+\)/)) {
        link = substr($0, RSTART, RLENGTH)
        sub(/^\]\(/, "", link)
        sub(/\)$/, "", link)
        print link
        $0 = substr($0, RSTART + RLENGTH)
      }
    }
  ' "$1"
}

resolve_link() {
  local from_file="$1"
  local link="$2"
  link="${link%%#*}"
  [ -z "$link" ] && return 1
  case "$link" in
    http://*|https://*) return 1 ;;
    /uipath:*|/uipath-feedback*) return 1 ;;
  esac
  local from_dir
  from_dir=$(/usr/bin/dirname "$from_file")
  local target="$from_dir/$link"
  local resolved_dir
  resolved_dir=$(cd "$(/usr/bin/dirname "$target")" 2>/dev/null && /bin/pwd)
  [ -z "$resolved_dir" ] && return 1
  echo "$resolved_dir/$(/usr/bin/basename "$target")"
}

# Build the set of every .md path that any .md file links to (file links + folder links).
linked_set=$(/usr/bin/mktemp)
trap 'rm -f "$linked_set"' EXIT

while IFS= read -r srcfile; do
  while IFS= read -r raw_link; do
    target=$(resolve_link "$srcfile" "$raw_link") || continue
    [ -z "$target" ] && continue
    if [ -d "$target" ]; then
      # Folder link → mark every .md inside as linked
      /usr/bin/find "$target" -name "*.md" -type f >> "$linked_set"
    elif [ -f "$target" ]; then
      echo "$target" >> "$linked_set"
    fi
  done < <(extract_links "$srcfile")
done < <(/usr/bin/find . -name "*.md" -type f)

# Sort + dedupe linked set
sorted_linked=$(/usr/bin/sort -u "$linked_set")

# Check each .md under references/ — orphan if not in linked set, with exceptions.
orphans=0
checked=0
while IFS= read -r f; do
  [ -z "$f" ] && continue
  basename=$(/usr/bin/basename "$f")
  [ "$basename" = "CAPABILITY.md" ] && continue
  checked=$((checked + 1))
  if ! echo "$sorted_linked" | /usr/bin/grep -qx "$f"; then
    echo "ORPHAN  ${f#$ROOT/}"
    orphans=$((orphans + 1))
  fi
done < <(/usr/bin/find "$ROOT/references" -name "*.md" -type f | /usr/bin/sort)

echo ""
echo "files_checked=$checked orphans=$orphans"

[ "$orphans" -gt 0 ] && exit 1
exit 0
