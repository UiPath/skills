#!/usr/bin/env bash
#
# SLA golden diff — asserts the direct-JSON-write output is structurally
# equivalent to the CLI output after normalizing random escalation IDs.
#
# Normalizer strategy:
#   - Every escalation rule's `.id` (format `esc_xxxxxx`) is stripped before
#     comparison. Escalations live at known paths:
#       root.data.slaRules[].escalationRule[]
#       nodes[].data.slaRules[].escalationRule[]
#     Stripping .id on matching objects keeps all other structural fields.
#   - Stage IDs and trigger IDs carry stable values in this fixture
#     (`Stage_aB3kL9`, `trigger_1`) so no stage-level ID remap is needed.
#   - Field ordering is normalized with `jq -S`.
#
# Usage:
#   ./diff.sh
#
# Exit 0 on equivalence; non-zero otherwise.

set -euo pipefail

HERE="$(cd "$(dirname "$0")" && pwd)"
CLI="$HERE/cli-output.json"
JSW="$HERE/json-write-output.json"

need() {
  command -v "$1" >/dev/null 2>&1 || { echo "Missing dependency: $1" >&2; exit 2; }
}

need jq
need diff

normalize() {
  local input="$1"
  # Strip `.id` from every escalation-rule object (those with triggerInfo + action).
  # This removes the random `esc_xxxxxx` IDs from both sides without touching
  # stage IDs, edge IDs, trigger IDs, or anything else.
  jq -c '
    walk(
      if type == "object"
         and has("id")
         and has("triggerInfo")
         and has("action")
      then del(.id)
      else .
      end
    )
  ' "$input" | jq -S .
}

CLI_NORM="$(mktemp)"
JSW_NORM="$(mktemp)"
trap 'rm -f "$CLI_NORM" "$JSW_NORM"' EXIT

normalize "$CLI"  > "$CLI_NORM"
normalize "$JSW" > "$JSW_NORM"

if diff -u "$CLI_NORM" "$JSW_NORM"; then
  echo "OK: sla golden — cli-output.json ≡ json-write-output.json (after escalation ID normalization)"
  exit 0
else
  echo "FAIL: sla golden diverged — see unified diff above" >&2
  exit 1
fi
