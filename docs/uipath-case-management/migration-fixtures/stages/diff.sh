#!/usr/bin/env bash
#
# Stages golden diff — asserts the direct-JSON-write output is structurally
# equivalent to the CLI output after normalizing random IDs.
#
# Normalizer strategy:
#   - Stage IDs are replaced by canonical names derived from `data.label`
#     (so `Stage_qFyJiu` and `Stage_jW8tRv`, both labeled "Submission Review",
#      both normalize to `Stage_<SubmissionReview>`).
#   - Edge IDs likewise normalized by source+target labels (not exercised here;
#     this fragment has no edges).
#   - Trigger ID `trigger_1` is stable (CLI uses the fixed literal) so no
#     normalization needed.
#   - `data.isRequired: false` is normalized away — the CLI's `stages add`
#     emits nothing for `isRequired` (there is no flag for it), while the
#     direct-JSON-write always emits `false` (see Known CLI divergences in
#     plugins/stages/impl-json.md). Both representations mean the same thing
#     to Studio Web; we strip `isRequired: false` from both sides so the diff
#     focuses on real structural differences.
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
  # Build a map of Stage_* IDs → Stage_<label-slug> using data.label.
  # Then substitute in the full document. Same for any edge IDs if present.
  jq -c '
    # Collect the ID remap from every Stage / ExceptionStage node.
    def stage_remap:
      [ .nodes[]
        | select(.type == "case-management:Stage" or .type == "case-management:ExceptionStage")
        | { key: .id,
            value: ("Stage_" + ((.data.label // "unknown")
                                | gsub("[^A-Za-z0-9]"; ""))) } ]
      | from_entries;

    # Apply the remap to every occurrence in the document (ids, sources, targets, handles).
    def apply(remap):
      walk(
        if type == "string" then
          . as $s
          | if remap | has($s) then remap[$s] else $s end
        else . end
      );

    # Strip `data.isRequired: false` from every stage node — the CLI omits
    # the key entirely, the direct-JSON-write always emits false. See
    # plugins/stages/impl-json.md "Known CLI divergences".
    def strip_isrequired_false:
      .nodes |= map(
        if (.type == "case-management:Stage" or .type == "case-management:ExceptionStage")
           and (.data.isRequired == false)
        then .data |= del(.isRequired)
        else .
        end
      );

    . as $doc
    | ($doc | stage_remap) as $remap
    | $doc | apply($remap) | strip_isrequired_false
  ' "$input" | jq -S .
}

CLI_NORM="$(mktemp)"
JSW_NORM="$(mktemp)"
trap 'rm -f "$CLI_NORM" "$JSW_NORM"' EXIT

normalize "$CLI"  > "$CLI_NORM"
normalize "$JSW" > "$JSW_NORM"

if diff -u "$CLI_NORM" "$JSW_NORM"; then
  echo "OK: stages golden — cli-output.json ≡ json-write-output.json (after ID normalization)"
  exit 0
else
  echo "FAIL: stages golden diverged — see unified diff above" >&2
  exit 1
fi
