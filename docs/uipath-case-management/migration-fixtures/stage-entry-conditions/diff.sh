#!/usr/bin/env bash
#
# stage-entry-conditions golden diff — asserts the direct-JSON-write output is
# structurally equivalent to the CLI output after normalizing random IDs.
#
# Normalizer strategy:
#   - Stage IDs → `Stage_<label-slug>` (from `data.label`).
#   - Condition IDs → `Condition_<displayName-slug>` (from `displayName`).
#   - Rule IDs → `Rule_<rule-type>_<parent-displayName-slug>_<index>` (from
#     the containing condition's `displayName` and the rule's position, so two
#     rules of the same type in the same condition still disambiguate).
#   - Trigger ID `trigger_1` is stable (fixed literal) so no normalization.
#   - `selectedStageId` strings are remapped through the stage ID map.
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
    # Stage ID remap: Stage_* → Stage_<label-slug>
    def stage_remap:
      [ .nodes[]
        | select(.type == "case-management:Stage" or .type == "case-management:ExceptionStage")
        | { key: .id,
            value: ("Stage_" + ((.data.label // "unknown")
                                | gsub("[^A-Za-z0-9]"; ""))) } ]
      | from_entries;

    # Condition ID remap: Condition_* → Condition_<displayName-slug>
    # Rule ID remap: Rule_* → Rule_<rule-type>_<condition-displayName-slug>_<index>
    def id_maps:
      [ .nodes[]
        | select(.type == "case-management:Stage" or .type == "case-management:ExceptionStage")
        | (.data.entryConditions // [])[]
        | . as $cond
        | ( { key: $cond.id,
              value: ("Condition_" + (($cond.displayName // "unknown")
                                       | gsub("[^A-Za-z0-9]"; ""))) }
          ),
          ( ($cond.rules // [])
            | to_entries[]
            | .key as $groupIdx
            | .value | to_entries[]
            | .key as $ruleIdx
            | .value as $rule
            | { key: $rule.id,
                value: ("Rule_" + $rule.rule + "_"
                         + (($cond.displayName // "unknown")
                            | gsub("[^A-Za-z0-9]"; ""))
                         + "_" + ($groupIdx|tostring) + "_" + ($ruleIdx|tostring)) } ) ];

    def apply(remap):
      walk(
        if type == "string" then
          . as $s
          | if remap | has($s) then remap[$s] else $s end
        else . end
      );

    . as $doc
    | ($doc | stage_remap) as $stageRemap
    | ($doc | id_maps) as $idList
    | ($idList | from_entries) as $condRuleRemap
    | ($stageRemap * $condRuleRemap) as $remap
    | $doc | apply($remap)
  ' "$input" | jq -S .
}

CLI_NORM="$(mktemp)"
JSW_NORM="$(mktemp)"
trap 'rm -f "$CLI_NORM" "$JSW_NORM"' EXIT

normalize "$CLI"  > "$CLI_NORM"
normalize "$JSW" > "$JSW_NORM"

if diff -u "$CLI_NORM" "$JSW_NORM"; then
  echo "OK: stage-entry-conditions golden — cli-output.json ≡ json-write-output.json (after ID normalization)"
  exit 0
else
  echo "FAIL: stage-entry-conditions golden diverged — see unified diff above" >&2
  exit 1
fi
