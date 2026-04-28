#!/usr/bin/env bash
# derive-routing-name.sh — produce a canonical, length-capped UiPath dashboard
# routing name from an --app-name. Same logic scaffold-project.sh uses
# internally; extracted so the Plan-phase agent can compute the slug BEFORE
# the build runs, ensuring the slug shown in the plan equals the slug the
# scaffold persists.
#
# Convention:
#   <prefix>govdash-</prefix><kebab-of-app-name><suffix>-<4-rand></suffix>
#
# Constraints:
#   - Server enforces 32-char total length cap.
#   - Lowercase alphanumeric + hyphens only.
#   - "govdash-" (8 chars) + "-<4rand>" (5 chars) reserves 13 chars.
#   - Kebab body MUST fit in 19 characters.
#
# Length-fitting steps applied in order:
#   1. Lowercase, replace non-alphanumeric with hyphens, collapse runs.
#   2. Apply abbreviations to common dashboard terms (observability → obs etc.)
#   3. If still > 19 chars, truncate to 19, drop trailing partial word at last
#      hyphen. Last resort: hard cut.
#   4. Append "-<4-rand>" suffix.
#
# Usage:
#   derive-routing-name.sh --app-name "Agent Observability Dashboard"
#   derive-routing-name.sh --app-name "Queue Throughput" --suffix abc1
#
# Output: the routing name on stdout. Errors to stderr.

set -euo pipefail

APP_NAME="" SUFFIX=""

while [[ $# -gt 0 ]]; do
  case "$1" in
    --app-name) APP_NAME="$2"; shift 2 ;;
    --suffix)   SUFFIX="$2"; shift 2 ;;
    -h|--help)
      sed -n 's/^# \?//p' "$0" | head -30
      exit 0 ;;
    *) echo "Unknown arg: $1" >&2; exit 2 ;;
  esac
done

[[ -z "$APP_NAME" ]] && { echo "Missing --app-name" >&2; exit 2; }

ROUTING_NAME_PREFIX="govdash-"
ROUTING_NAME_MAX=32
KEBAB_BODY_MAX=$(( ROUTING_NAME_MAX - ${#ROUTING_NAME_PREFIX} - 1 - 4 ))   # = 19

# Step 1: kebab-case
KEBAB=$(printf '%s' "$APP_NAME" \
  | tr '[:upper:]' '[:lower:]' \
  | tr -s ' ' '-' \
  | tr -cd 'a-z0-9-' \
  | sed -E 's/-+/-/g; s/^-+//; s/-+$//')

if [[ -z "$KEBAB" ]]; then
  echo "Cannot derive routing name from --app-name '$APP_NAME' (empty after kebab)" >&2
  exit 2
fi

# Step 2: abbreviations for common dashboard terms
ABBREV="$KEBAB"
ABBREV="${ABBREV//observability/obs}"
ABBREV="${ABBREV//performance/perf}"
ABBREV="${ABBREV//monitoring/mon}"
ABBREV="${ABBREV//governance/gov}"
ABBREV="${ABBREV//operations/ops}"
ABBREV="${ABBREV//analytics/analyt}"
ABBREV="${ABBREV//throughput/tput}"
ABBREV="${ABBREV//invocation/invoc}"
ABBREV="${ABBREV//dashboard/dash}"
ABBREV="${ABBREV//pipeline/pipe}"
ABBREV=$(printf '%s' "$ABBREV" | sed -E 's/-+/-/g; s/^-+//; s/-+$//')

# Step 3: truncate at last hyphen if still too long
if [[ ${#ABBREV} -gt $KEBAB_BODY_MAX ]]; then
  TRIMMED="${ABBREV:0:$KEBAB_BODY_MAX}"
  TRIMMED="${TRIMMED%-*}"
  TRIMMED="${TRIMMED%-}"
  if [[ ${#TRIMMED} -ge 4 ]]; then
    ABBREV="$TRIMMED"
  else
    ABBREV="${ABBREV:0:$KEBAB_BODY_MAX}"
    ABBREV="${ABBREV%-}"
  fi
fi

# Step 4: random suffix (or use --suffix override for deterministic output)
#
# Using node (already a hard dependency for this skill) avoids the SIGPIPE
# trap that `tr -dc 'a-z0-9' </dev/urandom | head -c 4` falls into on Git
# Bash + Windows: pipefail promotes the SIGPIPE that tr receives when head
# closes the pipe to a script-level exit 141. Single-process node = no pipe
# = no SIGPIPE = identical behavior on Mac/Linux/Windows.
if [[ -z "$SUFFIX" ]]; then
  SUFFIX=$(node -e "
    const c = 'abcdefghijklmnopqrstuvwxyz0123456789';
    let s = '';
    for (let i = 0; i < 4; i++) s += c[Math.floor(Math.random() * c.length)];
    process.stdout.write(s);
  ")
fi

ROUTING_NAME="${ROUTING_NAME_PREFIX}${ABBREV}-${SUFFIX}"

if [[ ${#ROUTING_NAME} -gt $ROUTING_NAME_MAX ]]; then
  echo "Generated routing name exceeds ${ROUTING_NAME_MAX} chars: $ROUTING_NAME" >&2
  exit 2
fi

echo "$ROUTING_NAME"
