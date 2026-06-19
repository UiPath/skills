#!/bin/bash
# PostToolUse telemetry hook for the UiPath skills plugin.
#
# Reads the hook JSON payload from stdin, decides whether the tool call is
# attributable to THIS plugin (skill gate), resolves the UiPath environment
# (alpha / staging / prod), and pipes one flat JSON object to `uip track`,
# which forwards it through the CLI's own telemetry tracker as a single
# uip.skills.tool-use Application Insights event. Calls from other plugins or
# bare Claude Code are dropped.
#
# The CLI (see UiPath/cli#2600) owns transport, the App Insights connection,
# the event name, the authenticated cloud identity, and the `source:
# "skills-plugin"` dimension. This hook only derives + sanitizes fields and
# gates on opt-in; value sanitization stays the hook's responsibility because
# the CLI and skills ship co-versioned.
#
# Non-blocking by contract: registered as an async hook in hooks.json
# ("async": true), so Claude Code runs it in the background and never waits for
# it. Always exits 0, swallows every error, and pipes to `uip track` in a
# detached subshell. It never delays or fails the observed tool call.
# Cross-platform (macOS, Linux, Windows via Git Bash / MSYS).
#
# Configuration (env only):
#   UIPATH_TELEMETRY_DISABLED   Gate. Reuses the uip CLI's variable name.
#                               Send ONLY when explicitly set to "0".
#                               Unset (default) or "1" -> do not send.
#                               Privacy-first default-off; absent is treated
#                               as disabled.

set +e

# Send only when telemetry is explicitly NOT disabled (=0). Unset defaults to
# "1" (disabled), so nothing is sent unless the user opts in with =0. `uip
# track` enforces the same gate on its side; we short-circuit here too.
[ "${UIPATH_TELEMETRY_DISABLED:-1}" = "0" ] || exit 0

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
      | grep -Eiq '\.(cs|flow|xaml|uipx|bpmn)"|/(agent|caseplan|project|app\.config|action-schema)\.json"' && is_uipath=1
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
env_name="unknown"; base_url=""; _ts=0
if [ -f "$cache" ]; then
  _ts="$(cache_val _ts)"
  env_name="$(cache_val env_name)"
  base_url="$(cache_val base_url)"
  case "$_ts" in *[!0-9]*|"") _ts=0 ;; esac   # non-numeric -> treat as stale
fi

if [ "$(( now - _ts ))" -ge "$ttl" ]; then
  status_json="$(uip login status --output json 2>/dev/null)"
  base_url="$(printf '%s' "$status_json" \
    | grep -oE '"BaseUrl"[[:space:]]*:[[:space:]]*"[^"]*"' | head -1 | sed 's/.*"\([^"]*\)"$/\1/')"
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
  } > "$cache" 2>/dev/null
fi

# --- derived, low-cardinality fields ---------------------------------------
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
# durationMs is sent as a JSON number. Emit JSON null (not 0) when absent, so a
# missing value doesn't skew latency aggregations. The CLI drops a null-valued
# property, so a missing duration simply records as "no data". Stays unquoted.
case "$duration_ms" in ''|*[!0-9]*) dur_json="null" ;; *) dur_json="$duration_ms" ;; esac

session_id="$(json_str session_id)"
tool_use_id="$(json_str tool_use_id)"   # unique per call: correlation key + ordering tiebreaker
permission_mode="$(json_str permission_mode)"

# Skills version — tracks the CLI version (version-manifest.json `targetCli`).
# The CLI's own app version already rides the tracker as `application_Version`,
# so we no longer send a separate cliVersion. Read from the manifest, NOT git.
# This is the skills/CLI co-version, NOT the .claude-plugin/plugin.json package
# version.
skills_ver="$(grep -oE '"skillsVersion"[[:space:]]*:[[:space:]]*"[^"]*"' \
  "${CLAUDE_PLUGIN_ROOT:-.}/version-manifest.json" 2>/dev/null \
  | head -1 | sed 's/.*"\([^"]*\)"$/\1/')"
effort_level="$(printf '%s' "$payload" \
  | grep -oE '"effort"[[:space:]]*:[[:space:]]*\{[^}]*"level"[[:space:]]*:[[:space:]]*"[^"]*"' \
  | grep -oE '"level"[[:space:]]*:[[:space:]]*"[^"]*"' | head -1 | sed 's/.*"\([^"]*\)"$/\1/')"

# Sanitize free-ish text to keep the hand-built JSON valid and bounded. Value
# sanitization is the hook's job (CLI and skills ship co-versioned); the CLI
# then namespaces, stamps identity, and forwards.
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
skills_ver="$(san "$skills_ver")"
tool_use_id="$(san "$tool_use_id")"
session_id="$(san "$session_id")"

# --- hand off to the CLI telemetry tracker ---------------------------------
# Build a flat key:value JSON object and pipe it to `uip track`. The CLI hard-
# codes the event name (uip.skills.tool-use), stamps source: "skills-plugin",
# attaches the authenticated cloud identity + CLI app version, and owns
# transport + flush. Every scalar key below becomes an event property; the CLI
# drops any non-scalar value (so a null durationMs simply disappears). Send no
# `event` key, no envelope, and no `source` (the CLI overrides it).
#
# Detached subshell ( cmd & ) survives this hook's exit so the agent never
# waits. `uip track` is opt-in and never-fail (exits 0, emits nothing when
# telemetry is off); piping to it is harmless even if the CLI is absent.
( printf '%s' "{\"toolName\":\"$tool\",\"skillName\":\"$skill_name\",\"uipSubcommand\":\"$uip_subcommand\",\"fileExtension\":\"$file_ext\",\"environment\":\"$env_name\",\"baseUrl\":\"$base_url\",\"outcome\":\"$outcome\",\"permissionMode\":\"$permission_mode\",\"effortLevel\":\"$effort_level\",\"skillsVersion\":\"$skills_ver\",\"toolUseId\":\"$tool_use_id\",\"sessionId\":\"$session_id\",\"durationMs\":$dur_json}" \
    | uip track >/dev/null 2>&1 & )

exit 0
