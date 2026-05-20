#!/bin/bash
# Validate the synthetic BPMN/package fixture corpus for this skill.
# Usage: bash .maintenance/check-validation-fixtures.sh

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT" || exit 1

python3 .maintenance/check-validation-fixtures.py
