#!/bin/bash
# Verify every markdown anchor link (`[text](file.md#anchor)`) resolves to an actual heading in the target file.
# Usage: bash .maintenance/check-anchors.sh
# Output: BAD ANCHOR lines per failure, then "anchors_checked=N anchors_bad=M" summary.
#
# Skips:
# - links inside fenced code blocks (```...```)
# - links inside inline code spans (`...`)
# - links without a `#anchor` fragment
# - http(s):// links
# - slash-command links
# - same-file anchor-only links (#anchor without a path)
# - links to files that don't exist (those are caught by check-links.sh, not this checker)
#
# Slug rule (matches GitHub heading-anchor generation):
# 1. Lowercase the heading
# 2. Strip backtick, asterisk, underscore, and any non-alphanumeric/non-space/non-dash character
# 3. Replace each remaining space with `-`
# 4. Separator characters do not collapse
#
# See .maintenance/README.md for common gotchas.

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT" || exit 1

heading_anchors() {
  /usr/bin/awk '
    /^#{1,6} /{
      sub(/^#+ /, "");
      gsub(/[`*_]/, "");
      anchor = tolower($0);
      gsub(/[^a-z0-9 -]/, "", anchor);
      gsub(/ /, "-", anchor);
      print anchor;
    }' "$1"
}

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

broken=0
checked=0

while IFS= read -r srcfile; do
  while IFS= read -r raw; do
    case "$raw" in
      \#*) continue ;;
      http*|/uipath*) continue ;;
    esac
    [[ "$raw" != *#* ]] && continue
    target_path="${raw%%#*}"
    anchor="${raw#*#}"
    [ -z "$target_path" ] && continue
    srcdir=$(/usr/bin/dirname "$srcfile")
    full="$srcdir/$target_path"
    resolved=$(cd "$(/usr/bin/dirname "$full")" 2>/dev/null && /bin/pwd)/$(/usr/bin/basename "$full")
    [ ! -f "$resolved" ] && continue
    checked=$((checked+1))
    if heading_anchors "$resolved" | /usr/bin/grep -qx "$anchor"; then
      :
    else
      echo "BAD ANCHOR  $srcfile -> $raw"
      broken=$((broken+1))
    fi
  done < <(extract_links "$srcfile")
done < <(/usr/bin/find . -name "*.md" -type f)

echo ""
echo "anchors_checked=$checked anchors_bad=$broken"
