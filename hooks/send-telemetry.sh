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
# gates on the opt-out flag; value sanitization stays the hook's responsibility
# because the CLI and skills ship co-versioned.
#
# REGION-SCOPED EXTRACTION (see extract_fields): the payload embeds free-form
# customer content (prompts, command lines, stdout/stderr, file contents). A
# naive grep over the whole payload mis-extracts fields when that content
# contains JSON-shaped text (`"success":false`, `uip solution publish`,
# `.flow"`, `"resolvedModel":"..."`). So a single string-aware awk pass walks
# the JSON once and pulls each field ONLY from the region it lives in:
#   ENVELOPE (top-level)  -> toolName, toolUseId, sessionId, permissionMode,
#                            durationMs, effortLevel (effort.level), agentType
#   tool_input            -> skillName, uipSubcommand (command), fileExtension
#                            (file_path), subagentType (subagent_type, or
#                            agent_type for a Codex spawn_agent call)
#   tool_response         -> outcome (interrupted/success), subagentModel
#                            (resolvedModel)
#
# CROSS-AGENT: registered as a PostToolUse hook, this also runs under other
# coding agents that honor hooks.json (e.g. Codex). Codex's envelope matches
# Claude's (hook_event_name, tool_name, tool_use_id, session_id,
# permission_mode, tool_input/{command,file_path}), so Bash-`uip` and file
# attribution work unchanged. Differences handled / accepted: agent spawns use
# `spawn_agent` + tool_input.agent_type (see is_uipath_call + outkey); Codex
# omits duration_ms / effort.level (-> durationMs null, effortLevel "") and
# serializes tool_response as a JSON STRING, not an object, so success /
# interrupted / resolvedModel are absent and outcome is ok|unknown only.
# Only derived, low-cardinality, PII-free values ever leave the machine.
#
# Non-blocking by contract: registered as an async hook in hooks.json
# ("async": true), so Claude Code runs it in the background and never waits for
# it. Always exits 0, swallows every error, and pipes to `uip track` in a
# detached subshell. Cross-platform (macOS, Linux, Windows via Git Bash /
# MSYS). Pure bash + grep/sed/awk — no jq, node, or python.
#
# Structure: pure helpers + side-effecting procedures (below), driven by main()
# (bottom). Configuration is env only:
#   UIPATH_TELEMETRY_DISABLED   Gate. Reuses the uip CLI's variable name.
#                               Opt-out: send by DEFAULT. Skip ONLY when set to
#                               "1". Unset (default) or "0" -> send. Absent is
#                               treated as enabled.

set +e

# schemaVersion of the emitted event. Bump on ANY change to the key set so App
# Insights can segment events emitted with older/churned schemas.
SCHEMA_VERSION=1

# --- extraction ------------------------------------------------------------

# extract_fields: one string-aware awk pass over the payload (stdin). Prints
# `key<TAB>value` lines, each field pulled ONLY from its region (see header),
# so embedded customer content can never false-match a top-level field. String
# values are emitted raw (escapes left as-is) and single-line (valid JSON
# escapes control chars, so a real TAB never appears inside a value). Large,
# uninteresting value strings (stdout, file contents, prompts) are scanned but
# never buffered, so this stays O(n) without the awk O(n^2) string-concat trap.
extract_fields() {
  awk '
    function interesting(k, d, c) {
      if (d == 1)
        return (k=="tool_name"||k=="tool_use_id"||k=="session_id"|| \
                k=="permission_mode"||k=="duration_ms"||k=="agent_type"|| \
                k=="hook_event_name")
      if (d == 2 && c == "input")
        return (k=="skill"||k=="command"||k=="file_path"||k=="subagent_type"|| \
                k=="agent_type")
      if (d == 2 && c == "response")
        return (k=="interrupted"||k=="success"||k=="resolvedModel")
      if (d == 2 && c == "effort")
        return (k=="level")
      return 0
    }
    # outkey: remap a JSON key to the field name read_fields expects. Codex
    # spawn_agent carries the spawned type in tool_input.agent_type; normalize
    # it to subagent_type so it lands in the same field as Claude (tool_input.
    # subagent_type) and never collides with the envelope agent_type (agentType).
    function outkey(k, d, c) {
      if (d == 2 && c == "input" && k == "agent_type") return "subagent_type"
      return k
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
              if (buffering) print outkey(pkey, pdepth, ctx) "\t" cur
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
          if (interesting(pkey, pdepth, ctx)) print outkey(pkey, pdepth, ctx) "\t" lit
          pend = 0; continue                      # leave delimiter for the main loop
        }
        i++
      }
    }
  '
}

# read_fields: parse extract_fields output ($1) into the field globals. The
# while loop runs in the current shell (here-doc, not a pipe), so the
# assignments persist.
read_fields() {
  event=""; tool=""; tool_use_id=""; session_id=""; permission_mode=""
  duration_ms=""; agent_type=""; skill=""; command=""; file_path=""
  subagent_type=""; interrupted=""; success=""; resolved_model=""
  effort_level=""; response_seen=""
  local k v
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
$1
EOF
}

# --- relevance gate --------------------------------------------------------

# is_uipath_call: 0 if this call is attributable to the plugin, else 1. No
# "active plugin" field exists, so attribute per-call from tool_input signals
# only (command / file_path), so stdout or prompt content can never
# over-attribute.
is_uipath_call() {
  case "$tool" in
    Skill)
      case "$skill" in uipath:*|uipath-*) return 0 ;; esac
      ;;
    Agent|spawn_agent)
      # UiPath agents, or a built-in/generic agent type — NOT custom agents from
      # other plugins (`<plugin>:<name>`) or user-defined ones. Claude Code spawns
      # via `Agent` + tool_input.subagent_type; Codex via `spawn_agent` +
      # tool_input.agent_type (the awk normalizes that to subagent_type). `default`
      # is Codex's generic agent — the equivalent of Claude's general-purpose/claude.
      case "$subagent_type" in
        uipath:*|uipath-*) return 0 ;;
        general-purpose|Explore|Plan|claude|claude-code-guide|statusline-setup|fork|default) return 0 ;;
      esac
      ;;
    Bash|PowerShell)
      printf '%s' "$command" \
        | grep -Eq '(^|[\\"[:space:];|&(])(uip|rpa-tool)[[:space:]]|\$UIP\b' && return 0
      ;;
    Edit|Write|Read|Glob|Grep)
      printf '%s' "$file_path" \
        | grep -Eiq '\.(cs|flow|xaml|uipx|bpmn)$|(^|[/\\])(agent|caseplan|project|app\.config|action-schema)\.json$' && return 0
      ;;
  esac
  return 1
}

# --- environment resolution ------------------------------------------------

# cache_val <file> <key>: emit a cached value stripped to a safe charset. Parses
# the cache as DATA — never `source` it, so a tampered cache can't execute
# arbitrary shell in this hook's context.
cache_val() {
  grep -E "^$2=" "$1" 2>/dev/null | head -1 | cut -d= -f2- | tr -cd 'A-Za-z0-9:._/-'
}

# resolve_environment: set env_name + base_url from `uip login status` (~0.5s),
# cached per-user for 1h so only one tool call per hour pays the cost. The cache
# dir is per-user, owner-only (NOT world-writable /tmp), so another local user
# can't pre-create the file. chmod is a no-op on Windows but harmless.
resolve_environment() {
  local cache_dir cache ttl now _ts status_json
  cache_dir="${XDG_CACHE_HOME:-$HOME/.cache}/uipath-telemetry"
  mkdir -p "$cache_dir" 2>/dev/null && chmod 700 "$cache_dir" 2>/dev/null
  cache="$cache_dir/env.cache"
  ttl=3600
  now="$(date +%s 2>/dev/null || echo 0)"

  env_name="unknown"; base_url=""; _ts=0
  if [ -f "$cache" ]; then
    _ts="$(cache_val "$cache" _ts)"
    env_name="$(cache_val "$cache" env_name)"
    base_url="$(cache_val "$cache" base_url)"
    case "$_ts" in *[!0-9]*|"") _ts=0 ;; esac   # non-numeric -> treat as stale
  fi

  [ "$(( now - _ts ))" -ge "$ttl" ] || return 0

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
}

# --- field derivation ------------------------------------------------------

# derive_fields: set skill_name, uip_subcommand, file_ext from the parsed
# tool_input values (so stdout content can't leak in).
derive_fields() {
  skill_name=""; uip_subcommand=""; file_ext=""
  case "$tool" in
    Skill)
      skill_name="$skill"
      ;;
    Bash|PowerShell)
      # e.g. "solution publish" from "uip solution publish --output json".
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
}

# compute_outcome: print outcome from the tool_response region ONLY — content
# never flips it.
#   interrupted == true -> interrupted (takes precedence)
#   success     == false -> failure
#   tool_response present, no failure signal -> ok (Read/Edit/Write/most MCP)
#   no tool_response at all -> unknown
compute_outcome() {
  if   [ "$interrupted" = "true" ];  then printf 'interrupted'
  elif [ "$success" = "false" ];     then printf 'failure'
  elif [ -n "$response_seen" ];      then printf 'ok'
  else                                    printf 'unknown'
  fi
}

# model_family <resolvedModel>: print the low-cardinality family and drop the
# context-window marker (e.g. claude-opus-4-8[1m] -> opus). Empty when absent
# (plain main-loop call); `other` for an unrecognized family.
model_family() {
  case "$1" in
    "")       printf '' ;;
    *opus*)   printf 'opus' ;;
    *sonnet*) printf 'sonnet' ;;
    *haiku*)  printf 'haiku' ;;
    *fable*)  printf 'fable' ;;
    *)        printf 'other' ;;
  esac
}

# read_skills_version: skills/CLI co-version from version-manifest.json (NOT
# git, NOT the plugin package version). The CLI's own app version already rides
# the tracker as application_Version, so no separate cliVersion is sent.
read_skills_version() {
  grep -oE '"skillsVersion"[[:space:]]*:[[:space:]]*"[^"]*"' \
    "${CLAUDE_PLUGIN_ROOT:-.}/version-manifest.json" 2>/dev/null \
    | head -1 | sed 's/.*"\([^"]*\)"$/\1/'
}

# san: sanitize free-ish text to keep the assembled JSON valid and bounded.
# Strips anything outside a safe charset (so no quotes / backslashes / control
# chars / pipes survive) and caps length.
san() { printf '%s' "$1" | tr -c 'A-Za-z0-9:._/ -' '_' | cut -c1-120; }

# build_event_json: assemble the canonical, ordered, flat JSON from the
# (already sanitized) field globals + dur_json + SCHEMA_VERSION. The key set is
# defined ONCE here and assembled by iteration (fixed order, every key always
# emitted). Each row is `name|type|value`: `s` -> JSON string, `n` -> JSON
# number/literal. Sanitized values cannot contain `|` (san maps it to `_`).
build_event_json() {
  local spec json sep fkey ftyp fval
  spec="schemaVersion|n|$SCHEMA_VERSION
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
$spec
EOF
  printf '%s}' "$json"
}

# --- main ------------------------------------------------------------------
main() {
  # Opt-out: send by default; skip only when telemetry is explicitly disabled
  # (UIPATH_TELEMETRY_DISABLED=1 or =true). Matches the CLI's isTelemetryDisabled()
  # gate, so `uip track` and this hook short-circuit on the same values.
  case "${UIPATH_TELEMETRY_DISABLED:-0}" in 1|true) exit 0 ;; esac

  payload="$(cat)"
  read_fields "$(printf '%s' "$payload" | extract_fields)"

  [ "$event" = "PostToolUse" ] || exit 0
  is_uipath_call || exit 0

  resolve_environment
  derive_fields

  outcome="$(compute_outcome)"
  # durationMs is a JSON number. Emit JSON null (not 0) when absent, so a missing
  # value doesn't skew latency aggregations. The CLI drops a null-valued
  # property, so a missing duration records as "no data". Stays unquoted.
  case "$duration_ms" in ''|*[!0-9]*) dur_json="null" ;; *) dur_json="$duration_ms" ;; esac
  subagent_model="$(model_family "$resolved_model")"
  skills_ver="$(read_skills_version)"

  # Sanitize every string field before assembly.
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

  # Hand off to the CLI telemetry tracker. The CLI hard-codes the event name
  # (uip.skills.tool-use), stamps source: "skills-plugin", attaches the
  # authenticated cloud identity + CLI app version, and owns transport + flush;
  # it drops any non-scalar value (so a null durationMs disappears). Send no
  # `event` key, no envelope, and no `source` (the CLI overrides it).
  #
  # Detached subshell ( cmd & ) survives this hook's exit so the agent never
  # waits. `uip track` is never-fail (exits 0, emits nothing when telemetry is
  # opted out); piping to it is harmless even if the CLI is absent.
  ( printf '%s' "$(build_event_json)" | uip track >/dev/null 2>&1 & )

  exit 0
}

main
