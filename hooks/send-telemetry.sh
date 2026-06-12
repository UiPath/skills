#!/bin/bash
# PostToolUse telemetry hook for the UiPath skills plugin.
#
# Reads the hook JSON payload from stdin, decides whether the tool call is
# attributable to THIS plugin (skill gate), resolves the UiPath environment
# (alpha / staging / prod), and emits one customEvent to Azure Application
# Insights. Calls from other plugins or bare Claude Code are dropped.
#
# Non-blocking by contract: always exits 0, swallows every error, and POSTs in
# a detached subshell so it never delays the observed tool call.
# Cross-platform (macOS, Linux, Windows via Git Bash / MSYS).
#
# Configuration (env only — nothing is sent unless the connection string is set):
#   UIPATH_TELEMETRY_CONNECTION_STRING   App Insights connection string
#       (InstrumentationKey=...;IngestionEndpoint=https://<region>.in.applicationinsights.azure.com/)
#   APPLICATIONINSIGHTS_CONNECTION_STRING  Fallback if the above is unset.
#   UIPATH_TELEMETRY_DISABLE=1           Hard off-switch.

set +e

[ "${UIPATH_TELEMETRY_DISABLE:-}" = "1" ] && exit 0

conn="${UIPATH_TELEMETRY_CONNECTION_STRING:-${APPLICATIONINSIGHTS_CONNECTION_STRING:-}}"
[ -z "$conn" ] && exit 0   # not configured -> no-op

payload="$(cat)"

# --- field helpers ---------------------------------------------------------
json_str() { # $1 = key; prints first JSON string value for that key
  printf '%s' "$payload" \
    | grep -oE "\"$1\"[[:space:]]*:[[:space:]]*\"[^\"]*\"" \
    | head -1 | sed 's/.*"\([^"]*\)"$/\1/'
}

event="$(json_str hook_event_name)"
tool="$(json_str tool_name)"
[ "$event" = "PostToolUse" ] || exit 0

# --- UiPath relevance gate -------------------------------------------------
# No "active plugin" field exists in the payload, so attribute per-call from
# concrete signals in tool_input. Anything that doesn't match -> exit 0.
skill="$(json_str skill)"
file_path="$(json_str file_path)"

is_uipath=0
case "$tool" in
  Skill)
    case "$skill" in uipath:*|uipath-*) is_uipath=1 ;; esac
    ;;
  Bash|PowerShell)
    printf '%s' "$payload" \
      | grep -Eq '(^|[\\"[:space:];|&(])(uip|rpa-tool)[[:space:]]|\$UIP\b' && is_uipath=1
    ;;
  Edit|Write|Read|Glob|Grep)
    printf '%s' "$payload" \
      | grep -Eiq '\.(flow|xaml|uipx|bpmn)"|/(agent|caseplan|project|app\.config|action-schema)\.json"' && is_uipath=1
    ;;
esac
[ "$is_uipath" = "1" ] || exit 0

# --- environment resolution (cached; `uip login status` is ~0.5s) ----------
# Resolve once per TTL and reuse, so only one tool call per hour pays the cost.
# Per-user, owner-only cache dir (NOT world-writable /tmp), so another local
# user can't pre-create the file. chmod is a no-op on Windows but harmless.
cache_dir="${XDG_CACHE_HOME:-$HOME/.cache}/uipath-telemetry"
mkdir -p "$cache_dir" 2>/dev/null && chmod 700 "$cache_dir" 2>/dev/null
cache="$cache_dir/env.cache"
ttl=3600
now="$(date +%s 2>/dev/null || echo 0)"

# Parse the cache as DATA into whitelisted variables — never `source` it, so a
# tampered cache can't execute arbitrary shell in this hook's context.
cache_val() { # $1 = key; emits value stripped to a safe charset
  grep -E "^$1=" "$cache" 2>/dev/null | head -1 | cut -d= -f2- | tr -cd 'A-Za-z0-9:._/-'
}
env_name="unknown"; base_url=""; cli_ver=""; _ts=0
if [ -f "$cache" ]; then
  _ts="$(cache_val _ts)"
  env_name="$(cache_val env_name)"
  base_url="$(cache_val base_url)"
  cli_ver="$(cache_val cli_ver)"
  case "$_ts" in *[!0-9]*|"") _ts=0 ;; esac   # non-numeric -> treat as stale
fi

if [ "$(( now - _ts ))" -ge "$ttl" ]; then
  status_json="$(uip login status --output json 2>/dev/null)"
  base_url="$(printf '%s' "$status_json" \
    | grep -oE '"BaseUrl"[[:space:]]*:[[:space:]]*"[^"]*"' | head -1 | sed 's/.*"\([^"]*\)"$/\1/')"
  cli_ver="$(uip --version 2>/dev/null | awk 'NR==1{print $1}')"
  case "$base_url" in
    *alpha.uipath.com*)   env_name="alpha" ;;
    *staging.uipath.com*) env_name="staging" ;;
    *cloud.uipath.com*)   env_name="prod" ;;
    "")                   env_name="unknown" ;;
    *)                    env_name="other" ;;
  esac
  {
    echo "_ts=$now"
    echo "env_name=$env_name"
    echo "base_url=$base_url"
    echo "cli_ver=$cli_ver"
  } > "$cache" 2>/dev/null
fi

# --- derived, low-cardinality, PII-free fields -----------------------------
skill_name=""; uip_subcommand=""; file_ext=""
case "$tool" in
  Skill)
    skill_name="$skill"
    ;;
  Bash|PowerShell)
    # e.g. "solution publish" from "uip solution publish --output json"
    uip_subcommand="$(printf '%s' "$payload" \
      | grep -oE '(uip|\$UIP)[[:space:]]+[a-z][a-z-]*([[:space:]]+[a-z][a-z-]*)?' \
      | head -1 | sed -E 's/^(uip|\$UIP)[[:space:]]+//')"
    ;;
  Edit|Write|Read|Glob|Grep)
    file_ext="$(printf '%s' "$file_path" | grep -oE '\.[A-Za-z0-9]+$' | head -1)"
    case "$file_path" in
      *agent.json)    file_ext="agent.json" ;;
      *caseplan.json) file_ext="caseplan.json" ;;
    esac
    ;;
esac

# Outcome from tool_response (no stdout/stderr content leaves the machine).
outcome="ok"
printf '%s' "$payload" | grep -q '"interrupted"[[:space:]]*:[[:space:]]*true'  && outcome="interrupted"
printf '%s' "$payload" | grep -q '"success"[[:space:]]*:[[:space:]]*false'     && outcome="failure"

duration_ms="$(printf '%s' "$payload" | grep -oE '"duration_ms"[[:space:]]*:[[:space:]]*[0-9]+' | head -1 | grep -oE '[0-9]+$')"
[ -z "$duration_ms" ] && duration_ms=0

session_id="$(json_str session_id)"
permission_mode="$(json_str permission_mode)"
effort_level="$(printf '%s' "$payload" \
  | grep -oE '"effort"[[:space:]]*:[[:space:]]*\{[^}]*"level"[[:space:]]*:[[:space:]]*"[^"]*"' \
  | grep -oE '"level"[[:space:]]*:[[:space:]]*"[^"]*"' | head -1 | sed 's/.*"\([^"]*\)"$/\1/')"
os_name="$(uname -s 2>/dev/null)"

# cwd contains the OS username -> never send raw. Hash to a stable anon id.
cwd="$(json_str cwd)"
hash_of() {
  if   command -v sha256sum >/dev/null 2>&1; then printf '%s' "$1" | sha256sum    | cut -c1-16
  elif command -v shasum    >/dev/null 2>&1; then printf '%s' "$1" | shasum -a 256 | cut -c1-16
  else printf '%s' "$1" | cksum | tr -d ' '; fi
}
workspace_id="$(hash_of "$cwd")"

# Sanitize free-ish text to keep the hand-built JSON valid and bounded.
san() { printf '%s' "$1" | tr -c 'A-Za-z0-9:._/ -' '_' | cut -c1-120; }
tool="$(san "$tool")"
skill_name="$(san "$skill_name")"
uip_subcommand="$(san "$uip_subcommand")"
file_ext="$(san "$file_ext")"
env_name="$(san "$env_name")"
base_url="$(san "$base_url")"
outcome="$(san "$outcome")"
permission_mode="$(san "$permission_mode")"
effort_level="$(san "$effort_level")"
cli_ver="$(san "$cli_ver")"
os_name="$(san "$os_name")"

# --- emit to Application Insights ------------------------------------------
ikey="$(printf '%s' "$conn" | grep -oE 'InstrumentationKey=[^;]+' | head -1 | cut -d= -f2)"
endpoint="$(printf '%s' "$conn" | grep -oE 'IngestionEndpoint=[^;]+' | head -1 | cut -d= -f2)"
[ -z "$endpoint" ] && endpoint="https://dc.services.visualstudio.com"
endpoint="${endpoint%/}"
[ -z "$ikey" ] && exit 0

ts_iso="$(date -u +%Y-%m-%dT%H:%M:%S.000Z 2>/dev/null)"

body="$(cat <<JSON
{"name":"Microsoft.ApplicationInsights.Event","time":"$ts_iso","iKey":"$ikey","tags":{"ai.cloud.role":"uipath-skills-plugin","ai.cloud.roleInstance":"$env_name","ai.session.id":"$session_id","ai.user.id":"$workspace_id","ai.application.ver":"$cli_ver"},"data":{"baseType":"EventData","baseData":{"ver":2,"name":"ToolUse","properties":{"toolName":"$tool","skillName":"$skill_name","uipSubcommand":"$uip_subcommand","fileExt":"$file_ext","environment":"$env_name","baseUrl":"$base_url","outcome":"$outcome","permissionMode":"$permission_mode","effortLevel":"$effort_level","os":"$os_name","cliVersion":"$cli_ver"},"measurements":{"durationMs":$duration_ms}}}}
JSON
)"

# Detached subshell ( cmd & ) survives this hook's exit so the agent never waits.
( curl -sS -m 4 -X POST "$endpoint/v2/track" \
    -H "Content-Type: application/json" \
    --data "$body" >/dev/null 2>&1 & )

exit 0
