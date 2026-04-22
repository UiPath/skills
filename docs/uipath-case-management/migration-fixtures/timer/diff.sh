#!/usr/bin/env bash
#
# Timer trigger golden diff — asserts the direct-JSON-write output is
# structurally equivalent to CLI output, across BOTH caseplan.json and
# entry-points.json, after normalizing random IDs + UUIDs.
#
# Normalizer strategy:
#   - Secondary trigger IDs (`trigger_` + 6 chars, not the literal `trigger_1`)
#     are replaced by a canonical slug derived from the trigger's displayName:
#       caseplan: trigger_Q3mNp7 (label "10-min Poll") → trigger_<10minPoll>
#       entry-points: same, looked up from entry.displayName
#     so "trigger_Q3mNp7" (CLI) and "trigger_K8fLr2" (JSON-write) both normalize
#     to the same slug.
#   - Literal `trigger_1` is stable across both paths (no normalization needed).
#   - entry-points.json `uniqueId` UUIDs are stripped (replaced with the
#     literal string "UUID") — CLI calls crypto.randomUUID(), JSON-write does
#     the same; both are non-deterministic.
#
# Usage:
#   ./diff.sh
#
# Exit 0 on equivalence; non-zero with a unified diff otherwise.

set -euo pipefail

HERE="$(cd "$(dirname "$0")" && pwd)"

need() {
  command -v "$1" >/dev/null 2>&1 || { echo "Missing dependency: $1" >&2; exit 2; }
}

need jq
need diff

# Normalize caseplan.json: remap random trigger IDs → trigger_<label-slug>.
normalize_caseplan() {
  jq -c '
    def trigger_remap:
      [ .nodes[]
        | select(.type == "case-management:Trigger")
        | select(.id != "trigger_1")
        | { key: .id,
            value: ("trigger_" + ((.data.label // "unknown")
                                  | gsub("[^A-Za-z0-9]"; ""))) } ]
      | from_entries;

    def apply(remap):
      walk(
        if type == "string" then
          . as $s | if remap | has($s) then remap[$s] else $s end
        else . end
      );

    . as $doc
    | ($doc | trigger_remap) as $remap
    | $doc | apply($remap)
  ' "$1" | jq -S .
}

# Normalize entry-points.json: strip uniqueId, remap embedded trigger IDs in
# filePath by each entry's own displayName.
normalize_entrypoints() {
  jq -c '
    .entryPoints |= map(
      .uniqueId = "UUID"
      | if (.filePath | test("#trigger_1$")) then .
        else
          .filePath = ((.filePath | sub("#[^#]+$"; ""))
                       + "#trigger_"
                       + (.displayName | gsub("[^A-Za-z0-9]"; "")))
        end
    )
  ' "$1" | jq -S .
}

CLI_CASEPLAN="$HERE/cli-output/caseplan.json"
CLI_ENTRYPTS="$HERE/cli-output/entry-points.json"
JSW_CASEPLAN="$HERE/json-write-output/caseplan.json"
JSW_ENTRYPTS="$HERE/json-write-output/entry-points.json"

TMP_DIR="$(mktemp -d)"
trap 'rm -rf "$TMP_DIR"' EXIT

normalize_caseplan    "$CLI_CASEPLAN"  > "$TMP_DIR/cli-caseplan.json"
normalize_caseplan    "$JSW_CASEPLAN"  > "$TMP_DIR/jsw-caseplan.json"
normalize_entrypoints "$CLI_ENTRYPTS"  > "$TMP_DIR/cli-entrypoints.json"
normalize_entrypoints "$JSW_ENTRYPTS"  > "$TMP_DIR/jsw-entrypoints.json"

fail=0

echo "--- caseplan.json ---"
if diff -u "$TMP_DIR/cli-caseplan.json" "$TMP_DIR/jsw-caseplan.json"; then
  echo "OK: caseplan.json equivalent"
else
  fail=1
fi

echo "--- entry-points.json ---"
if diff -u "$TMP_DIR/cli-entrypoints.json" "$TMP_DIR/jsw-entrypoints.json"; then
  echo "OK: entry-points.json equivalent"
else
  fail=1
fi

if [ "$fail" -eq 0 ]; then
  echo "OK: timer golden — cli-output ≡ json-write-output (after ID + UUID normalization)"
  exit 0
else
  echo "FAIL: timer golden diverged — see unified diff(s) above" >&2
  exit 1
fi
