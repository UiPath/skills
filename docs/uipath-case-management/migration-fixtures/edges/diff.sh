#!/usr/bin/env bash
#
# Edges golden diff — asserts the direct-JSON-write output is structurally
# equivalent to the CLI output after normalizing random IDs.
#
# Normalizer strategy (two-pass):
#   1. Stage IDs → `Stage_<labelSlug>` (same as stages fixture).
#   2. Apply the stage remap across the document so edge.source/target,
#      sourceHandle, and targetHandle all reference canonical node IDs.
#   3. Edge IDs → `edge_<sourceIdSlug>__<targetIdSlug>` derived from the
#      post-stage-remap source/target (so `edge_Tr1Gr2` and `edge_jWr001`,
#      both trigger_1→Submission Review, both normalize to the same canonical).
#   4. `data.isRequired: false` on stages is stripped — the CLI's `stages add`
#      emits no key, direct-JSON-write always emits false. See stages
#      plugin's "Known CLI divergences".
#   5. Trigger ID `trigger_1` is stable (fixed literal from `cases add`).
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
  jq -c '
    # Pass 1 — remap Stage_* IDs by data.label.
    def stage_remap:
      [ .nodes[]
        | select(.type == "case-management:Stage" or .type == "case-management:ExceptionStage")
        | { key: .id,
            value: ("Stage_" + ((.data.label // "unknown")
                                | gsub("[^A-Za-z0-9]"; ""))) } ]
      | from_entries;

    # Substring-replace every remap key with its value on every string value.
    # Necessary because handle strings embed IDs (e.g. `Stage_xxxxxx____source____right`).
    def apply(remap):
      walk(
        if type == "string" then
          reduce (remap | to_entries[]) as $kv (
            .;
            gsub($kv.key; $kv.value)
          )
        else . end
      );

    # Pass 2 — remap edge_* IDs by (post-remap source, post-remap target).
    def edge_remap:
      [ .edges[]
        | { key: .id,
            value: ("edge_" + (.source | gsub("[^A-Za-z0-9]"; ""))
                            + "__"
                            + (.target | gsub("[^A-Za-z0-9]"; ""))) } ]
      | from_entries;

    # Strip `data.isRequired: false` on stages (see stages fixture notes).
    def strip_isrequired_false:
      .nodes |= map(
        if (.type == "case-management:Stage" or .type == "case-management:ExceptionStage")
           and (.data.isRequired == false)
        then .data |= del(.isRequired)
        else .
        end
      );

    . as $doc
    | ($doc | stage_remap) as $sr
    | ($doc | apply($sr)) as $after_stages
    | ($after_stages | edge_remap) as $er
    | $after_stages | apply($er) | strip_isrequired_false
  ' "$input" | jq -S .
}

CLI_NORM="$(mktemp)"
JSW_NORM="$(mktemp)"
trap 'rm -f "$CLI_NORM" "$JSW_NORM"' EXIT

normalize "$CLI"  > "$CLI_NORM"
normalize "$JSW" > "$JSW_NORM"

if diff -u "$CLI_NORM" "$JSW_NORM"; then
  echo "OK: edges golden — cli-output.json ≡ json-write-output.json (after ID normalization)"
  exit 0
else
  echo "FAIL: edges golden diverged — see unified diff above" >&2
  exit 1
fi
