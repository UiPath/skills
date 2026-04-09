#!/bin/bash
# Minimal config reader/writer for ~/.uipath-skills/config.yaml
# Supports flat YAML only (single-level key: value pairs).
#
# Usage:
#   uipath-skills-config.sh get <key>        # prints value or empty string
#   uipath-skills-config.sh set <key> <value> # creates/updates key
#   uipath-skills-config.sh list             # prints entire config

set -e

CONFIG_DIR="$HOME/.uipath-skills"
CONFIG_FILE="$CONFIG_DIR/config.yaml"

cmd="${1:-}"
key="${2:-}"
value="${3:-}"

case "$cmd" in
  get)
    [ -z "$key" ] && { echo "Usage: $0 get <key>" >&2; exit 1; }
    [ -f "$CONFIG_FILE" ] || exit 0
    grep "^${key}:" "$CONFIG_FILE" 2>/dev/null | head -1 | sed "s/^${key}:[[:space:]]*//"
    ;;
  set)
    [ -z "$key" ] || [ -z "$value" ] && { echo "Usage: $0 set <key> <value>" >&2; exit 1; }
    mkdir -p "$CONFIG_DIR"
    if [ ! -f "$CONFIG_FILE" ]; then
      echo "${key}: ${value}" > "$CONFIG_FILE"
    elif grep -q "^${key}:" "$CONFIG_FILE" 2>/dev/null; then
      # Use a temp file for portable in-place editing (works on macOS + Linux)
      tmp="$CONFIG_FILE.tmp.$$"
      sed "s/^${key}:.*/${key}: ${value}/" "$CONFIG_FILE" > "$tmp"
      mv "$tmp" "$CONFIG_FILE"
    else
      echo "${key}: ${value}" >> "$CONFIG_FILE"
    fi
    ;;
  list)
    [ -f "$CONFIG_FILE" ] && cat "$CONFIG_FILE" || echo "(no config)"
    ;;
  *)
    echo "Usage: $0 {get|set|list} [key] [value]" >&2
    exit 1
    ;;
esac
