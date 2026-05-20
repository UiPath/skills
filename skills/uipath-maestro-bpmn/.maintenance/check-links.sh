#!/bin/bash
# Verify every markdown file-path link in the skill resolves to an existing file or directory.
# Usage: bash .maintenance/check-links.sh
# Output: BROKEN lines per failure, then "checked=N broken=M" summary.
#
# Skips:
# - links inside fenced code blocks (```...```)
# - links inside inline code spans (`...`)
# - http(s):// links
# - slash-command links (/uipath:..., /uipath-feedback)
# - same-file anchor-only links (#anchor)
#
# Accepts:
# - file links resolving to a file (-f)
# - folder links resolving to a directory (-d)
#
# Run from any directory; resolves to the skill root automatically.

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT" || exit 1

broken=0
checked=0

# Per-file: strip fenced code blocks and inline code spans, then extract links.
extract_links() {
  /usr/bin/awk '
    /^```/ { fenced = !fenced; next }
    !fenced {
      # Strip inline code spans: anything between two backticks
      gsub(/`[^`]*`/, "", $0)
      # Match all ](...) link targets on this line
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

while IFS= read -r srcfile; do
  while IFS= read -r link; do
    link="${link%%#*}"
    [ -z "$link" ] && continue
    case "$link" in
      http://*|https://*) continue ;;
      /uipath:*|/uipath-feedback*) continue ;;
    esac
    filedir=$(/usr/bin/dirname "$srcfile")
    target="$filedir/$link"
    resolved_dir=$(cd "$(/usr/bin/dirname "$target")" 2>/dev/null && /bin/pwd)
    resolved_base=$(/usr/bin/basename "$target")
    resolved="$resolved_dir/$resolved_base"
    checked=$((checked+1))
    if [ -f "$resolved" ] || [ -d "$resolved" ]; then
      :
    elif [ -d "$target" ]; then
      :
    else
      echo "BROKEN  $srcfile -> $link"
      broken=$((broken+1))
    fi
  done < <(extract_links "$srcfile")
done < <(/usr/bin/find . -name "*.md" -type f)

echo ""
echo "checked=$checked broken=$broken"
