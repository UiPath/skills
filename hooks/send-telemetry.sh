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
# REGION-SCOPED EXTRACTION (why the awk pass exists): the payload embeds
# free-form customer content (prompts, command lines, stdout/stderr, file
# contents). A naive grep over the whole payload mis-extracts fields when that
# content happens to contain `"success":false`, `uip solution publish`,
# `.flow"`, `"resolvedModel":"..."`, etc. So a single string-aware awk pass
# walks the JSON once, tracks brace/string depth, and emits each field ONLY
# from the region it actually lives in:
#   ENVELOPE (top-level keys, depth 1) -> tool_name, tool_use_id, session_id,
#     permission_mode, duration_ms, agent_type, hook_event_name
#   tool_input  (depth 2) -> skill, command, file_path, subagent_type
#   tool_response (depth 2) -> interrupted, success, resolvedModel
#   effort      (depth 2) -> level
# Nested content (depth >= 2 inside the wrong region, or anything inside a JSON
# string) can never false-match an envelope field. Only derived, low-
# cardinality, PII-free values ever leave the machine.
#
# Non-blocking by contract: registered as an async hook in hooks.json
# ("async": true), so Claude Code runs it in the background and never waits for
# it. Always exits 0, swallows every error, and pipes to `uip track` in a
# detached subshell. It never delays or fails the observed tool call.
# Cross-platform (macOS, Linux, Windows via Git Bash / MSYS). Pure bash +
# grep/sed/awk — no jq, node, or python.
#
# Configuration (env only):
#   UIPATH_TELEMETRY_DISABLED   Gate. Reuses the uip CLI's variable name.
#                               Send ONLY when explicitly set to "0".
#                               Unset (default) or "1" -> do not send.
#                               Privacy-first default-off; absent is treated
#                               as disabled.

set +e

# schemaVersion of the emitted event. Bump on ANY change to the key set so App
# Insights can segment events emitted with older/churned schemas.
SCHEMA_VERSION=1

# Send only when telemetry is explicitly NOT disabled (=0). Unset defaults to
# "1" (disabled), so nothing is sent unless the user opts in with =0. `uip
# track` enforces the same gate on its side; we short-circuit here too.
[ "${UIPATH_TELEMETRY_DISABLED:-1}" = "0" ] || exit 0

payload="$(cat)"

# --- single-pass, region-scoped field extraction --------------------------
# One string-aware walk over the payload. Emits `key<TAB>value` lines for the
# fields we want, each pulled from its correct region (see header). String
# values are emitted raw (escapes left as-is); they are single-line because
# valid JSON escapes control chars, so a real TAB never appears inside a value.
# Large, uninteresting value strings (stdout, file contents, prompts) are
# scanned but never buffered, so this stays O(n) without the awk O(n^2)
# string-concat trap.
fields="$(printf '%s' "$payload" | awk '
  function interesting(k, d, c) {
    if (d == 1)
      return (k=="tool_name"||k=="tool_use_id"||k=="session_id"|| \
              k=="permission_mode"||k=="duration_ms"||k=="agent_type"|| \
              k=="hook_event_name")
    if (d == 2 && c == "input")
      return (k=="skill"||k=="command"||k=="file_path"||k=="subagent_type")
    if (d == 2 && c == "response")
      return (k=="interrupted"||k=="success"||k=="resolvedModel")
    if (d == 2 && c == "effort")
      return (k=="level")
    return 0
  }
  { buf = buf $0 "\n" }
  END {
    n = length(buf)
    depth = 0; instr = 0; esc = 0
    pend = 0; pkey = ""; pdepth = 0       # pending value after a key + colon
    ctx = ""                              # region at depth 2: input/response/effort/other
    laststr = ""                          # last closed string (candidate key)
    cur = ""; buffering = 0; isval = 0
    i = 1
    while (i <= n) {
      c = substr(buf, i, 1)
      if (instr) {
        if (esc)          { if (buffering) cur = cur c; esc = 0; i++; continue }
        if (c == "\\")    { if (buffering) cur = cur c; esc = 1; i++; continue }
        if (c == "\"") {
          instr = 0
          if (isval) {
            if (buffering) print pkey "\t" cur
            pend = 0; isval = 0
          } else {
            laststr = cur
          }
          cur = ""; buffering = 0; i++; continue
        }
        if (buffering) cur = cur c
        i++; continue
      }
      if (c == "\"") {
        instr = 1; cur = ""
        if (pend) { isval = 1; buffering = interesting(pkey, pdepth, ctx) }
        else      { isval = 0; buffering = 1 }   # key strings are small
        i++; continue
      }
      if (c == ":") {
        pkey = laststr; pdepth = depth; pend = 1
        if (depth == 1 && laststr == "tool_response") print "tool_response_seen\t1"
        i++; continue
      }
      if (c == "{") {
        if (pend) {
          if (pdepth == 1) {
            if (pkey == "tool_input")        ctx = "input"
            else if (pkey == "tool_response") ctx = "response"
            else if (pkey == "effort")        ctx = "effort"
            else                              ctx = "other"
          }
          pend = 0
        }
        depth++; i++; continue
      }
      if (c == "[") {
        if (pend) { if (pdepth == 1) ctx = "other"; pend = 0 }
        depth++; i++; continue
      }
      if (c == "}" || c == "]") {
        depth--; if (depth <= 1) ctx = ""; pend = 0; i++; continue
      }
      if (c == ",")  { pend = 0; i++; continue }
      if (c == " " || c == "\t" || c == "\n" || c == "\r") { i++; continue }
      if (pend) {                               # literal value: number/true/false/null
        lit = ""
        while (i <= n) {
          c = substr(buf, i, 1)
          if (c==","||c=="}"||c=="]"||c==" "||c=="\t"||c=="\n"||c=="\r") break
          lit = lit c; i++
        }
        if (interesting(pkey, pdepth, ctx)) print pkey "\t" lit
        pend = 0; continue                      # leave delimiter for the main loop
      }
      i++
    }
  }
')"

# --- parse the emitted key<TAB>value lines into shell variables ------------
event=""; tool=""; tool_use_id=""; session_id=""; permission_mode=""
duration_ms=""; agent_type=""; skill=""; command=""; file_path=""
subagent_type=""; interrupted=""; success=""; resolved_model=""
effort_level=""; response_seen=""
while IFS="$(printf '\t')" read -r k v; do
  case "$k" in
    hook_event_name)    event="$v" ;;
    tool_name)          tool="$v" ;;
    tool_use_id)        tool_use_id="$v" ;;
    session_id)         session_id="$v" ;;
    permission_mode)    permission_mode="$v" ;;
    duration_ms)        duration_ms="$v" ;;
    agent_type)         agent_type="$v" ;;
    skill)              skill="$v" ;;
    command)            command="$v" ;;
    file_path)          file_path="$v" ;;
    subagent_type)      subagent_type="$v" ;;
    interrupted)        interrupted="$v" ;;
    success)            success="$v" ;;
    resolvedModel)      resolved_model="$v" ;;
    level)              effort_level="$v" ;;
    tool_response_seen) response_seen="1" ;;
  esac
done <<EOF
$fields
EOF

[ "$event" = "PostToolUse" ] || exit 0

# --- UiPath relevance gate (scoped to tool_input, never to content) --------
# No "active plugin" field exists in the payload, so attribute per-call from
# concrete signals in tool_input. Anything that doesn't match -> exit 0. The
# command / file_path tested here come from tool_input only, so stdout or
# prompt content can never cause over-attribution.
is_uipath=0
case "$tool" in
  Skill)
    case "$skill" in uipath:*|uipath-*) is_uipath=1 ;; esac
    ;;
  Agent)
    # Track subagent spawns only for UiPath agents or Claude's built-in agent
    # types — NOT custom agents from other plugins (`<plugin>:<name>`) or
    # user-defined ones.
    case "$subagent_type" in
      uipath:*|uipath-*) is_uipath=1 ;;
      general-purpose|Explore|Plan|claude|claude-code-guide|statusline-setup|fork) is_uipath=1 ;;
    esac
    ;;
  Bash|PowerShell)
    printf '%s' "$command" \
      | grep -Eq '(^|[\\"[:space:];|&(])(uip|rpa-tool)[[:space:]]|\$UIP\b' && is_uipath=1
    ;;
  Edit|Write|Read|Glob|Grep)
    printf '%s' "$file_path" \
      | grep -Eiq '\.(cs|flow|xaml|uipx|bpmn)$|(^|[/\\])(agent|caseplan|project|app\.config|action-schema)\.json$' && is_uipath=1
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
    # e.g. "solution publish" from "uip solution publish --output json".
    # Derived from tool_input.command only, so stdout content can't leak in.
    uip_subcommand="$(printf '%s' "$command" \
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

# Outcome from the tool_response region ONLY — content never flips it.
#   interrupted == true -> interrupted
#   success     == false -> failure
#   tool_response present, no failure signal -> ok (Read/Edit/Write/most MCP)
#   no tool_response at all -> unknown
if [ "$interrupted" = "true" ]; then
  outcome="interrupted"
elif [ "$success" = "false" ]; then
  outcome="failure"
elif [ -n "$response_seen" ]; then
  outcome="ok"
else
  outcome="unknown"
fi

# durationMs is a JSON number. Emit JSON null (not 0) when absent, so a missing
# value doesn't skew latency aggregations. The CLI drops a null-valued property,
# so a missing duration simply records as "no data". Stays unquoted.
case "$duration_ms" in ''|*[!0-9]*) dur_json="null" ;; *) dur_json="$duration_ms" ;; esac

# Normalize the resolved subagent model to a low-cardinality family and drop
# the context-window marker (e.g. `claude-opus-4-8[1m]` -> `opus`). Empty when
# absent (plain main-loop call); `other` for an unrecognized family.
case "$resolved_model" in
  "")        subagent_model="" ;;
  *opus*)    subagent_model="opus" ;;
  *sonnet*)  subagent_model="sonnet" ;;
  *haiku*)   subagent_model="haiku" ;;
  *fable*)   subagent_model="fable" ;;
  *)         subagent_model="other" ;;
esac

# Skills version — tracks the CLI version (version-manifest.json `targetCli`).
# The CLI's own app version already rides the tracker as `application_Version`,
# so we no longer send a separate cliVersion. Read from the manifest, NOT git.
# This is the skills/CLI co-version, NOT the .claude-plugin/plugin.json package
# version.
skills_ver="$(grep -oE '"skillsVersion"[[:space:]]*:[[:space:]]*"[^"]*"' \
  "${CLAUDE_PLUGIN_ROOT:-.}/version-manifest.json" 2>/dev/null \
  | head -1 | sed 's/.*"\([^"]*\)"$/\1/')"

# Sanitize free-ish text to keep the assembled JSON valid and bounded. Strips
# anything outside a safe charset (so no quotes / backslashes / control chars /
# pipes survive) and caps length. Value sanitization is the hook's job (CLI and
# skills ship co-versioned); the CLI then namespaces, stamps identity, forwards.
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
subagent_model="$(san "$subagent_model")"
subagent_type="$(san "$subagent_type")"
agent_type="$(san "$agent_type")"

# --- hand off to the CLI telemetry tracker ---------------------------------
# Canonical field set, defined ONCE and assembled by iteration (fixed order,
# every key always emitted). Each row is `name|type|value`: type `s` -> JSON
# string, `n` -> JSON number/literal. Values are already sanitized, so `|`
# cannot appear inside one (san maps it to `_`); durationMs/schemaVersion are
# numeric/literal. The CLI hard-codes the event name (uip.skills.tool-use),
# stamps source: "skills-plugin", attaches the authenticated cloud identity +
# CLI app version, and owns transport + flush. The CLI drops any non-scalar
# value (so a null durationMs simply disappears). Send no `event` key, no
# envelope, and no `source` (the CLI overrides it).
fields_spec="schemaVersion|n|$SCHEMA_VERSION
toolName|s|$tool
skillName|s|$skill_name
uipSubcommand|s|$uip_subcommand
fileExtension|s|$file_ext
environment|s|$env_name
baseUrl|s|$base_url
outcome|s|$outcome
permissionMode|s|$permission_mode
effortLevel|s|$effort_level
skillsVersion|s|$skills_ver
toolUseId|s|$tool_use_id
sessionId|s|$session_id
subagentModel|s|$subagent_model
subagentType|s|$subagent_type
agentType|s|$agent_type
durationMs|n|$dur_json"

json="{"; sep=""
while IFS='|' read -r fkey ftyp fval; do
  [ -n "$fkey" ] || continue
  case "$ftyp" in
    n) json="$json$sep\"$fkey\":$fval" ;;
    *) json="$json$sep\"$fkey\":\"$fval\"" ;;
  esac
  sep=","
done <<EOF
$fields_spec
EOF
json="$json}"

# Detached subshell ( cmd & ) survives this hook's exit so the agent never
# waits. `uip track` is opt-in and never-fail (exits 0, emits nothing when
# telemetry is off); piping to it is harmless even if the CLI is absent.
( printf '%s' "$json" | uip track >/dev/null 2>&1 & )

exit 0
