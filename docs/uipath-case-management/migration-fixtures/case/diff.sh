#!/usr/bin/env bash
#
# Case (root) golden diff — asserts the direct-JSON-write output is
# structurally equivalent to the CLI output for both the minimal and
# full-flags variants.
#
# Normalizer strategy:
#   - Root `id` is a literal ("root") in CLI — no remap needed.
#   - Initial Trigger `id` is literal ("trigger_1") — no remap needed.
#   - `root.description: ""` is stripped from both sides — the CLI's
#     `cases add` omits the key entirely when `--description` is not
#     passed, while direct-JSON-write always emits `description: <value>`
#     (empty string when sdd.md has no description). See Known CLI
#     divergences in plugins/case/impl-json.md. Non-empty descriptions
#     are NOT stripped so real structural differences still surface.
#
# Usage:
#   ./diff.sh
#
# Exit 0 on equivalence; non-zero otherwise.

set -euo pipefail

HERE="$(cd "$(dirname "$0")" && pwd)"

need() {
  command -v "$1" >/dev/null 2>&1 || { echo "Missing dependency: $1" >&2; exit 2; }
}

need jq
need diff

normalize() {
  local input="$1"
  jq -c '
    # Strip `root.description: ""` only — non-empty descriptions are
    # preserved so genuine divergences surface.
    if (.root.description // null) == "" then
      .root |= del(.description)
    else .
    end
  ' "$input" | jq -S .
}

compare() {
  local label="$1"
  local cli="$2"
  local jsw="$3"

  local cli_norm jsw_norm
  cli_norm="$(mktemp)"
  jsw_norm="$(mktemp)"
  trap 'rm -f "$cli_norm" "$jsw_norm"' RETURN

  normalize "$cli" > "$cli_norm"
  normalize "$jsw" > "$jsw_norm"

  if diff -u "$cli_norm" "$jsw_norm"; then
    echo "OK: case golden [$label] — $(basename "$cli") ≡ $(basename "$jsw")"
  else
    echo "FAIL: case golden [$label] diverged — see unified diff above" >&2
    return 1
  fi
}

rc=0
compare "minimal" "$HERE/cli-output-minimal.json" "$HERE/json-write-output-minimal.json" || rc=1
compare "full"    "$HERE/cli-output-full.json"    "$HERE/json-write-output-full.json"    || rc=1

exit $rc
