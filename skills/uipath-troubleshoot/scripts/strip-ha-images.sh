#!/usr/bin/env bash
#
# Strips base64 image content from healing agent JSON files to reduce file size.
# Replaces AnalysisResult[].Images[].Content with a placeholder string.
# Original files are overwritten in place.
#
# Requires jq. If not found, attempts to install it automatically.
#
# Usage: strip-ha-images.sh [directory]
#   directory: path containing healing agent JSON files (default: current directory)

set -euo pipefail

if ! command -v jq &>/dev/null; then
    echo "Error: jq is required but not installed." >&2
    echo "Install it from: https://jqlang.github.io/jq/download/" >&2
    exit 1
fi

dir="${1:-.}"

shopt -s nullglob
files=("$dir"/*.json)

if [ ${#files[@]} -eq 0 ]; then
    echo "No JSON files found in $dir"
    exit 0
fi

for file in "${files[@]}"; do
    if jq -e '.Content.AnalysisResult[]?.Images[]?.Content' "$file" &>/dev/null; then
        tmp=$(mktemp)
        if jq '(.Content.AnalysisResult[]?.Images[]?.Content) = "[base64 image removed]"' "$file" > "$tmp"; then
            mv "$tmp" "$file"
            echo "Stripped images from $(basename "$file")"
        else
            rm -f "$tmp"
            echo "Warning: Failed to process $(basename "$file")" >&2
        fi
    fi
done
