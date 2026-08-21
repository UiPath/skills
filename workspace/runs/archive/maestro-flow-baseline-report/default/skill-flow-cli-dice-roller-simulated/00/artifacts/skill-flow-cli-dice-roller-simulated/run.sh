#!/usr/bin/env bash
# Convenience wrapper — forward all arguments to dice_roller.py
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
python3 "$SCRIPT_DIR/dice_roller.py" "$@"
