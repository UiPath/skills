#!/bin/bash
# Verify every markdown file under references/ is reachable from SKILL.md within the configured max hops.
# Usage: bash .maintenance/check-depth.sh [MAX_HOPS]
# Default MAX_HOPS=2. Output per file: "DEPTH=N  path/to/file.md" + summary.
#
# Counts BFS hops via outbound links. Folder links count as reachability for every file in the folder
# (per the convention documented in .maintenance/README.md — folder links satisfy practical reachability).
#
# Skips:
# - Links inside fenced code blocks (```...```)
# - Links inside inline code spans (`...`)
# - http(s):// links
# - Anchor-only links (#anchor)
# - Slash-command links (/uipath:..., /uipath-feedback)
#
# Exits non-zero if any file exceeds MAX_HOPS or is unreachable.
# Compatible with bash 3.2 (no associative arrays — uses tab-separated state files).

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT" || exit 1

MAX_HOPS="${1:-2}"

# State files: each line is "<depth>\t<absolute_path>"
visited=$(/usr/bin/mktemp)
frontier=$(/usr/bin/mktemp)
next_frontier=$(/usr/bin/mktemp)
trap 'rm -f "$visited" "$frontier" "$next_frontier"' EXIT

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

is_visited() {
  /usr/bin/grep -q "	$1$" "$visited"
}

mark_visited() {
  printf "%s\t%s\n" "$1" "$2" >> "$visited"
}

depth_of() {
  /usr/bin/awk -F'\t' -v p="$1" '$2 == p { print $1; exit }' "$visited"
}

# Seed with SKILL.md at depth 0
mark_visited 0 "$ROOT/SKILL.md"
echo "$ROOT/SKILL.md" > "$frontier"

current_depth=0
while [ -s "$frontier" ] && [ "$current_depth" -lt "$MAX_HOPS" ]; do
  : > "$next_frontier"
  while IFS= read -r file; do
    [ -z "$file" ] && continue
    while IFS= read -r raw_link; do
      target=$(resolve_link "$file" "$raw_link") || continue
      [ -z "$target" ] && continue
      if [ -d "$target" ]; then
        while IFS= read -r f; do
          [ -z "$f" ] && continue
          if ! is_visited "$f"; then
            mark_visited $((current_depth + 1)) "$f"
            echo "$f" >> "$next_frontier"
          fi
        done < <(/usr/bin/find "$target" -name "*.md" -type f)
      elif [ -f "$target" ]; then
        if ! is_visited "$target"; then
          mark_visited $((current_depth + 1)) "$target"
          echo "$target" >> "$next_frontier"
        fi
      fi
    done < <(extract_links "$file")
  done < "$frontier"
  /bin/cp "$next_frontier" "$frontier"
  current_depth=$((current_depth + 1))
done

# Report — every .md under references/ should be visited within MAX_HOPS
total=0
unreachable=0
exceeded=0
while IFS= read -r f; do
  [ -z "$f" ] && continue
  total=$((total + 1))
  d=$(depth_of "$f")
  if [ -z "$d" ]; then
    echo "UNREACHABLE  ${f#$ROOT/}"
    unreachable=$((unreachable + 1))
  elif [ "$d" -gt "$MAX_HOPS" ]; then
    echo "EXCEEDS_DEPTH ($d > $MAX_HOPS)  ${f#$ROOT/}"
    exceeded=$((exceeded + 1))
  fi
done < <(/usr/bin/find "$ROOT/references" -name "*.md" -type f | /usr/bin/sort -u)

echo ""
echo "max_hops=$MAX_HOPS total_files=$total reachable_within=$((total - unreachable - exceeded)) unreachable=$unreachable exceeds_depth=$exceeded"

if [ "$unreachable" -gt 0 ] || [ "$exceeded" -gt 0 ]; then
  exit 1
fi
exit 0
