#!/bin/bash
# Run the planner's SDD gate after an SDD is written, and hand its findings back.
#
# Why a hook. The gate (skills/uipath-planner/scripts/audit_sdd.py) names the
# defects that otherwise reach a reviewer as a vague "would not finalize into a
# working case" judgement: a variable consumed but never produced, an illegal
# WHEN/Marks-Complete pair, a backtick-wrapped <UNRESOLVED>. Telling the agent to
# run it in prose does not work — the Case Design Lane's reading set is already
# ~158 KB and every attempt to add that instruction pushed the design tasks past
# their turn walls. A hook costs the agent no reading at all.
#
# Loop safety is the whole design. Findings are surfaced ONCE per (session, file):
# the agent gets them, repairs, and the hook stays quiet on later writes. Without
# that, repair-write-refire is unbounded — an earlier prose version of this idea
# produced 13 and 16 gate invocations and timed the tasks out.
#
# Fail-open everywhere: no python, no gate, unparseable payload, anything
# unexpected -> exit 0 and stay invisible.
set -uo pipefail

payload="$(cat 2>/dev/null || true)"
[ -z "$payload" ] && exit 0

read_field() {
  printf '%s' "$payload" | python3 -c "
import json,sys
try:
    d=json.load(sys.stdin)
except Exception:
    sys.exit(0)
cur=d
for k in '$1'.split('.'):
    if not isinstance(cur,dict): sys.exit(0)
    cur=cur.get(k)
    if cur is None: sys.exit(0)
print(cur)
" 2>/dev/null || true
}

tool="$(read_field tool_name)"
case "$tool" in Write|Edit|MultiEdit) ;; *) exit 0 ;; esac

file="$(read_field tool_input.file_path)"
[ -z "$file" ] && exit 0
base="$(basename "$file")"
case "$base" in sdd.md|sdd.draft.md|*-sdd.md|*-sdd.draft.md) ;; *) exit 0 ;; esac
[ -f "$file" ] || exit 0

gate="${CLAUDE_PLUGIN_ROOT:-}/skills/uipath-planner/scripts/audit_sdd.py"
[ -f "$gate" ] || exit 0
command -v python3 >/dev/null 2>&1 || exit 0

# Once per (session, file). Keyed on the session id when present so parallel
# eval tasks in one sandbox never share a marker.
session="$(read_field session_id)"
marker_dir="${TMPDIR:-/tmp}/uipath-sdd-gate"
mkdir -p "$marker_dir" 2>/dev/null || exit 0
marker="$marker_dir/$(printf '%s|%s' "${session:-nosession}" "$file" | cksum | tr -d ' ')"
[ -e "$marker" ] && exit 0

out="$(cd "$(dirname "$file")" && python3 "$gate" "$base" 2>&1)" || true
printf '%s' "$out" | grep -q "AUDIT FAIL" || exit 0

: > "$marker" 2>/dev/null || true
{
  echo "SDD gate findings for $base (audit_sdd.py, reported once):"
  printf '%s\n' "$out"
  echo "Repair these with Edit from the line numbers above. Do not re-read the whole document."
} >&2
exit 2
