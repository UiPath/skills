#!/bin/bash
# Verify markdown link text agrees with link URL when text contains a file-like token.
# Usage: bash .maintenance/check-link-text.sh
# Output: BROKEN lines per failure, then "checked=N broken=M" summary.
#
# Failure modes (all hard failures):
# - basename-mismatch: text contains a file-like token whose basename != URL basename.
# - prefix-mismatch: basenames match but the directory prefix in the text doesn't match
#   the URL's directory (and isn't a suffix of it). Catches misleading text like
#   "operate/manage.md" pointing to "references/manage.md".
# - folder-url-but-text-is-file: URL ends with "/" but text claims a file.
#
# Skips:
# - links inside fenced code blocks (```...```)
# - links inside inline code spans (`...`)
# - http(s):// links
# - slash-command links (/uipath:..., /uipath-feedback)
# - same-file anchor-only links (#anchor)
# - image links (![alt](url))
# - links whose text contains no file-like token
#
# File-like token regex: [A-Za-z0-9_./-]+\.(md|sh|json|js|ts|py|cs|xaml|flow|yaml|yml)
#
# Run from any directory; resolves to the skill root automatically.

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT" || exit 1

broken=0
checked=0

# Per-file: strip fenced code blocks and inline code spans, then emit "lineno<TAB>text<TAB>url"
# for every non-image link on every line.
extract_pairs() {
  /usr/bin/awk '
    /^```/ { fenced = !fenced; next }
    !fenced {
      lineno = NR
      line = $0
      gsub(/`[^`]*`/, "", line)
      while (match(line, /\[[^]]*\]\([^)]+\)/)) {
        m = substr(line, RSTART, RLENGTH)
        # Skip image links: ![alt](url)
        if (RSTART > 1 && substr(line, RSTART - 1, 1) == "!") {
          line = substr(line, RSTART + RLENGTH)
          continue
        }
        ti = index(m, "](")
        text = substr(m, 2, ti - 2)
        url  = substr(m, ti + 2, length(m) - ti - 2)
        printf "%d\t%s\t%s\n", lineno, text, url
        line = substr(line, RSTART + RLENGTH)
      }
    }
  ' "$1"
}

# Extract the first file-like token from a string. Empty if none found.
first_file_token() {
  printf '%s' "$1" | /usr/bin/grep -oE '[A-Za-z0-9_./-]+\.(md|sh|json|js|ts|py|cs|xaml|flow|yaml|yml)' | /usr/bin/head -n1
}

while IFS= read -r srcfile; do
  while IFS=$'\t' read -r lineno text url; do
    [ -z "$url" ] && continue

    case "$url" in
      http://*|https://*) continue ;;
      /uipath:*|/uipath-feedback*) continue ;;
      \#*) continue ;;
    esac

    url_nofrag="${url%%#*}"
    [ -z "$url_nofrag" ] && continue

    text_token=$(first_file_token "$text")
    [ -z "$text_token" ] && continue

    checked=$((checked+1))

    case "$url_nofrag" in
      */)
        echo "BROKEN  $srcfile:$lineno -> text=\"$text\" url=$url reason=folder-url-but-text-is-file"
        broken=$((broken+1))
        continue
        ;;
    esac

    text_base="${text_token##*/}"
    url_base="${url_nofrag##*/}"

    if [ "$text_base" != "$url_base" ]; then
      echo "BROKEN  $srcfile:$lineno -> text=\"$text\" url=$url reason=basename-mismatch"
      broken=$((broken+1))
      continue
    fi

    # Basenames match. Check directory coherence.
    text_dir="${text_token%/*}"
    [ "$text_dir" = "$text_token" ] && text_dir=""
    url_dir="${url_nofrag%/*}"
    [ "$url_dir" = "$url_nofrag" ] && url_dir=""

    if [ -n "$text_dir" ] && [ "$text_dir" != "$url_dir" ]; then
      # Tolerate the case where the text directory is a suffix of the URL directory
      # (e.g., text "author/greenfield.md" vs. url "references/author/greenfield.md").
      mismatch=1
      case "/$url_dir/" in
        */"$text_dir"/*) mismatch=0 ;;
      esac
      if [ "$mismatch" -eq 1 ]; then
        echo "BROKEN  $srcfile:$lineno -> text=\"$text\" url=$url reason=prefix-mismatch"
        broken=$((broken+1))
      fi
    fi
  done < <(extract_pairs "$srcfile")
done < <(/usr/bin/find . -name "*.md" -type f)

echo ""
echo "checked=$checked broken=$broken"

[ "$broken" -gt 0 ] && exit 1
exit 0
