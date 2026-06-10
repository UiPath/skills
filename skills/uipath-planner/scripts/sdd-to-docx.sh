#!/usr/bin/env bash
# Convert a generated SDD markdown file to a styled Word document.
# Optionally takes a corporate .docx as a style reference (--reference-doc)
# so the output picks up the customer's fonts, heading styles, and margins
# without committing any template binary to this repo.
#
# Usage: sdd-to-docx.sh <sdd.md> [output.docx] [--reference-doc <template.docx>]
#   output.docx defaults to <input-basename>.docx in the current directory
#
# Known limitation: mermaid code blocks are NOT rendered — they appear as
# code in the document. Render them separately (e.g. mermaid-cli) and replace
# manually if the deliverable needs diagram images.
#
# Exit codes: 0 success · 1 usage error · 2 pandoc missing · 3 conversion failed
set -euo pipefail

if [ $# -lt 1 ] || [ "$1" = "--help" ] || [ "$1" = "-h" ]; then
  echo "Usage: sdd-to-docx.sh <sdd.md> [output.docx] [--reference-doc <template.docx>]"
  echo "Converts an SDD markdown file to .docx via pandoc, with table of contents."
  echo "--reference-doc applies the styles of an existing Word document."
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
shift
if [ ! -f "$input" ]; then
  echo "ERROR: input file not found: $input" >&2
  exit 1
fi

base="$(basename "$input")"
output="${base%.*}.docx"
reference=""

while [ $# -gt 0 ]; do
  case "$1" in
    --reference-doc)
      [ $# -ge 2 ] || { echo "ERROR: --reference-doc needs a path" >&2; exit 1; }
      reference="$2"
      shift 2
      ;;
    *)
      output="$1"
      shift
      ;;
  esac
done

args=("$input" -f gfm -t docx --toc --toc-depth=2 -o "$output")
if [ -n "$reference" ]; then
  if [ ! -f "$reference" ]; then
    echo "ERROR: reference doc not found: $reference" >&2
    exit 1
  fi
  args+=("--reference-doc=$reference")
fi

if ! pandoc "${args[@]}"; then
  echo "ERROR: pandoc conversion failed for $input" >&2
  exit 3
fi

echo "Word document: $output"
if grep -q '```mermaid' "$input"; then
  echo "NOTE: the SDD contains mermaid diagrams — they are embedded as code" >&2
  echo "blocks, not rendered images. Render separately if the deliverable" >&2
  echo "needs visuals." >&2
fi
