#!/usr/bin/env bash
# Extract a .docx document (typically a PDD) to GitHub-flavored Markdown.
# UTF-8 safe, preserves tables as pipe tables, extracts embedded images
# (screenshots) to a media folder so the agent can Read them.
#
# Usage: docx-extract.sh <input.docx> [output.md]
#   output.md defaults to <input-basename>.md in the current directory
#   embedded media lands in <output-basename>-media/
#
# Exit codes: 0 success · 1 usage error · 2 pandoc missing · 3 conversion failed
set -euo pipefail

if [ $# -lt 1 ] || [ "$1" = "--help" ] || [ "$1" = "-h" ]; then
  echo "Usage: docx-extract.sh <input.docx> [output.md]"
  echo "Converts a .docx to GitHub-flavored Markdown via pandoc."
  echo "Embedded images are extracted to <output-basename>-media/."
  [ $# -lt 1 ] && exit 1 || exit 0
fi

if ! command -v pandoc >/dev/null 2>&1; then
  echo "ERROR: pandoc is not installed." >&2
  echo "Install it, then re-run:" >&2
  echo "  Windows: winget install JohnMacFarlane.Pandoc" >&2
  echo "  macOS:   brew install pandoc" >&2
  echo "  Linux:   sudo apt-get install pandoc" >&2
  exit 2
fi

input="$1"
if [ ! -f "$input" ]; then
  echo "ERROR: input file not found: $input" >&2
  exit 1
fi

base="$(basename "$input")"
output="${2:-${base%.*}.md}"
media_dir="${output%.md}-media"

if ! pandoc "$input" -f docx -t gfm --wrap=none --extract-media="$media_dir" -o "$output"; then
  echo "ERROR: pandoc conversion failed for $input" >&2
  exit 3
fi

echo "Markdown: $output"
if [ -d "$media_dir" ]; then
  echo "Media:    $media_dir/ ($(find "$media_dir" -type f | wc -l | tr -d ' ') file(s))"
  unreadable="$(find "$media_dir" -type f \( -iname '*.emf' -o -iname '*.wmf' \) | tr '\n' ' ')"
  if [ -n "${unreadable% }" ]; then
    echo "WARNING: EMF/WMF media cannot be rendered by the Read tool: $unreadable" >&2
    echo "Ask the user for PNG exports of those figures, or mark dependent extractions [SME REVIEW]." >&2
  fi
else
  echo "Media:    none embedded"
fi
