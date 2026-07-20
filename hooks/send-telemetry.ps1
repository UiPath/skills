# Telemetry hook for the UiPath skills plugin (Claude Code).
#
# TWIN SCRIPT: hooks/send-telemetry.sh is the bash twin of this file — any
# behavioral change here MUST be mirrored there in the same PR (see CLAUDE.md).
# hooks.json runs whichever twin matches the executing shell via a
# bash/PowerShell polyglot command.
#
# Registered on multiple Claude Code hook events (PostToolUse, SessionStart,
# SessionEnd, Stop, StopFailure). Reads the hook JSON payload from stdin, maps
# the event to a canonical eventName, and pipes one flat JSON object to
# `uip track`, which forwards it through the CLI's own telemetry tracker as a
# single uip.skills.<event> Application Insights event.
#
# tool-use is per-call and gated on plugin attribution (skill gate) — calls from
# other plugins or bare Claude Code are dropped. Lifecycle events (session-start,
# session-end, completion) are session-scoped and fire for every session where
# this plugin is installed.
#
# The CLI (see UiPath/cli#2600) owns transport, the App Insights connection,
# the event name, the authenticated cloud identity, the `source:
# "skills-plugin"` dimension, and — since UiPath/cli#2806 — the
# environment/base_url/region base dimensions stamped fresh on every event
# from its own auth context (so this hook sends no environment info). This
# hook only derives + sanitizes fields and gates on the opt-out flag; value
# sanitization stays the hook's responsibility because the CLI and skills
# ship co-versioned.
#
# REGION-SCOPED EXTRACTION: the payload embeds free-form customer content
# (prompts, command lines, stdout/stderr, file contents). A naive text scan
# over the whole payload mis-extracts fields when that content contains
# JSON-shaped text (`"success":false`, `uip solution publish`, `.flow"`,
# `"resolvedModel":"..."`). So the payload is parsed as real JSON
# (ConvertFrom-Json) and each field is read ONLY from the region it lives in:
#   ENVELOPE (top-level)  -> toolName, toolUseId, session_id, permissionMode,
#                            durationMs, effortLevel (effort.level), agentType,
#                            source (-> session_source), reason (session-end),
#                            model (-> agent_model; Claude sends it on
#                            SessionStart, Codex on every event)
#   tool_input            -> skillName, uipSubcommand (command), fileExtension
#                            (file_path), subagentType (subagent_type, or
#                            agent_type for a Codex spawn_agent call)
#   tool_response         -> outcome (interrupted/success), subagentModel
#                            (resolvedModel)
#
# CROSS-AGENT: registered as a PostToolUse hook, this also runs under other
# coding agents that honor hooks.json (e.g. Codex, UiPath Autopilot / Delegate).
# Codex's envelope matches Claude's (hook_event_name, tool_name, tool_use_id,
# session_id, permission_mode, tool_input/{command,file_path}), so Bash-`uip`
# and file attribution work unchanged. Differences handled / accepted: agent
# spawns use `spawn_agent` + tool_input.agent_type (see Test-UipathCall +
# extraction); Codex omits duration_ms / effort.level (-> durationMs null,
# effortLevel "") and serializes tool_response as a JSON STRING, not an object,
# so success / interrupted / resolvedModel are absent and outcome is ok|unknown
# only. UiPath Autopilot / Delegate keep the same envelope but rename the shell
# and file tools — ExecuteBashCommand / ExecutePowershellCommand (vs Bash /
# PowerShell) and ReadFile / WriteFile / EditFile / LsDirectory (vs Read / Write
# / Edit / Glob / Grep); their tool_input still carries command / file_path, so
# the same attribution + derivation fire once those names are gated (see
# Test-UipathCall + Get-DerivedFields). Only derived, low-cardinality, PII-free
# values ever leave the machine.
#
# Non-blocking by contract: registered as an async hook in hooks.json
# ("async": true) on every event EXCEPT SessionEnd, so Claude Code runs it in
# the background and never waits for it. SessionEnd is registered
# SYNCHRONOUSLY (30s timeout): async hooks still running at session teardown
# are killed after a short grace window — shorter than this hook's PowerShell
# + `uip track` startup — which would silently drop the session-end event.
# Always exits 0 and swallows every error. Runs under Windows PowerShell 5.1
# and PowerShell 7+ (pwsh) on Windows, macOS, and Linux — no jq, node, or
# python.
#
# Structure: pure helpers (below), driven by Main (bottom). Configuration is
# env only:
#   UIPATH_TELEMETRY_DISABLED   Gate. Reuses the uip CLI's variable name.
#                               Opt-out: send by DEFAULT. Skip ONLY when set to
#                               "1". Unset (default) or "0" -> send. Absent is
#                               treated as enabled.

$ErrorActionPreference = 'SilentlyContinue'

# schemaVersion of the emitted event. Bump on ANY change to the key set so App
# Insights can segment events emitted with older/churned schemas. v2: adds the
# eventName / session_source / reason / agent_model keys, renames
# sessionId -> session_id (canonical casing, matches the CLI command stream,
# UiPath/cli#2800), and drops environment/baseUrl (the CLI stamps fresh
# environment/base_url/region base dimensions itself, UiPath/cli#2806).
$SCHEMA_VERSION = 2

# --- extraction helpers ------------------------------------------------------

# Safe property read on a ConvertFrom-Json PSCustomObject: $null when the key
# is absent (never throws, never falls back to another region).
function Get-Prop($Obj, [string]$Name) {
  if ($null -eq $Obj) { return $null }
  $p = $Obj.PSObject.Properties[$Name]
  if ($p) { return $p.Value }
  return $null
}

function Test-JsonObject($Value) {
  return ($Value -is [System.Management.Automation.PSCustomObject])
}

# JSON booleans -> the literal strings 'true'/'false'; everything else -> ''.
function ConvertTo-BoolString($Value) {
  if ($Value -is [bool]) { if ($Value) { return 'true' } return 'false' }
  return ''
}

# --- relevance gate --------------------------------------------------------

# Test-UipathCall: $true if this call is attributable to the plugin, else
# $false. No "active plugin" field exists, so attribute per-call from
# tool_input signals only (command / file_path), so stdout or prompt content
# can never over-attribute. Matching is case-sensitive to mirror the CLI's
# own casing (file extensions are the deliberate case-insensitive exception).
function Test-UipathCall([string]$Tool, [string]$Skill, [string]$SubagentType, [string]$Command, [string]$FilePath) {
  switch ($Tool) {
    'Skill' {
      if ($Skill -clike 'uipath:*' -or $Skill -clike 'uipath-*') { return $true }
      break
    }
    { $_ -cin @('Agent', 'spawn_agent') } {
      # UiPath agents, or a built-in/generic agent type — NOT custom agents from
      # other plugins (`<plugin>:<name>`) or user-defined ones. Claude Code spawns
      # via `Agent` + tool_input.subagent_type; Codex via `spawn_agent` +
      # tool_input.agent_type (extraction normalizes that to subagent_type).
      # `default` is Codex's generic agent — the equivalent of Claude's
      # general-purpose/claude.
      if ($SubagentType -clike 'uipath:*' -or $SubagentType -clike 'uipath-*') { return $true }
      if (@('general-purpose', 'Explore', 'Plan', 'claude', 'claude-code-guide', 'statusline-setup', 'fork', 'default') -ccontains $SubagentType) { return $true }
      break
    }
    { $_ -cin @('Bash', 'PowerShell', 'ExecuteBashCommand', 'ExecutePowershellCommand') } {
      if ($Command -cmatch '(^|[\\";|&(\s])(uip|rpa-tool)\s' -or $Command -cmatch '\$UIP\b') { return $true }
      break
    }
    { $_ -cin @('Edit', 'Write', 'Read', 'Glob', 'Grep', 'ReadFile', 'WriteFile', 'EditFile', 'LsDirectory') } {
      if ($FilePath -imatch '\.(cs|flow|xaml|uipx|bpmn)$' -or $FilePath -imatch '(^|[/\\])(agent|caseplan|project|app\.config|action-schema)\.json$') { return $true }
      break
    }
  }
  return $false
}

# --- field derivation ------------------------------------------------------

# Get-DerivedFields: skillName, uipSubcommand, fileExt from the parsed
# tool_input values (so stdout content can't leak in).
function Get-DerivedFields([string]$Tool, [string]$Skill, [string]$Command, [string]$FilePath) {
  $derived = @{ skillName = ''; uipSubcommand = ''; fileExt = '' }
  switch ($Tool) {
    'Skill' {
      $derived.skillName = $Skill
      break
    }
    { $_ -cin @('Bash', 'PowerShell', 'ExecuteBashCommand', 'ExecutePowershellCommand') } {
      # e.g. "solution publish" from "uip solution publish --output json".
      $m = [regex]::Match($Command, '(uip|\$UIP)\s+[a-z][a-z-]*(\s+[a-z][a-z-]*)?')
      if ($m.Success) {
        $derived.uipSubcommand = $m.Value -creplace '^(uip|\$UIP)\s+', ''
      }
      break
    }
    { $_ -cin @('Edit', 'Write', 'Read', 'Glob', 'Grep', 'ReadFile', 'WriteFile', 'EditFile', 'LsDirectory') } {
      $m = [regex]::Match($FilePath, '\.[A-Za-z0-9]+$')
      if ($m.Success) { $derived.fileExt = $m.Value }
      if ($FilePath -clike '*agent.json') { $derived.fileExt = 'agent.json' }
      if ($FilePath -clike '*caseplan.json') { $derived.fileExt = 'caseplan.json' }
      break
    }
  }
  return $derived
}

# Get-Outcome: outcome from the tool_response region ONLY — content never
# flips it.
#   interrupted == true -> interrupted (takes precedence)
#   success     == false -> failure
#   tool_response present, no failure signal -> ok (Read/Edit/Write/most MCP)
#   no tool_response at all -> unknown
function Get-Outcome([string]$Interrupted, [string]$Success, [bool]$ResponseSeen) {
  if ($Interrupted -eq 'true') { return 'interrupted' }
  if ($Success -eq 'false') { return 'failure' }
  if ($ResponseSeen) { return 'ok' }
  return 'unknown'
}

# Get-EventName: translate the agent hook event into the canonical eventName
# token the CLI's `uip track` maps to a uip.skills.<event> event. An
# unrecognized event returns empty so Main drops it. Stop and StopFailure both
# map to `completion`, distinguished by outcome (see Get-LifecycleOutcome).
# CROSS-AGENT: Codex fires SessionStart and Stop under these SAME names with a
# matching envelope (session_id/source/model; docs: developers.openai.com/
# codex/hooks), so both map here unchanged. Codex has NO SessionEnd (completion
# is its terminal signal) and no StopFailure (its API-error turns are not
# distinguished). Gemini/Cursor use different hook names — separate follow-ups.
function Get-EventName([string]$HookEvent) {
  switch ($HookEvent) {
    'PostToolUse'  { return 'tool-use' }
    'SessionStart' { return 'session-start' }
    'SessionEnd'   { return 'session-end' }
    'Stop'         { return 'completion' }
    'StopFailure'  { return 'completion' }
  }
  return ''
}

# Get-LifecycleOutcome: outcome for the non-tool events. A normal turn end
# (Stop) is `ok`; an API-error turn end (StopFailure) is `failure`.
# session-start and session-end carry no turn outcome (session-end's `reason`
# conveys the why).
function Get-LifecycleOutcome([string]$HookEvent) {
  switch ($HookEvent) {
    'Stop'        { return 'ok' }
    'StopFailure' { return 'failure' }
  }
  return ''
}

# Get-ModelFamily: the low-cardinality family, dropping the context-window
# marker (e.g. claude-opus-4-8[1m] -> opus). Empty when absent (plain
# main-loop call); `other` for an unrecognized family.
function Get-ModelFamily([string]$Model) {
  if (-not $Model) { return '' }
  if ($Model -clike '*opus*')   { return 'opus' }
  if ($Model -clike '*sonnet*') { return 'sonnet' }
  if ($Model -clike '*haiku*')  { return 'haiku' }
  if ($Model -clike '*fable*')  { return 'fable' }
  return 'other'
}

# Read-SkillsVersion: skills/CLI co-version from version-manifest.json (NOT
# git, NOT the plugin package version). The CLI's own app version already rides
# the tracker as application_Version, so no separate cliVersion is sent.
function Read-SkillsVersion {
  $root = $env:CLAUDE_PLUGIN_ROOT
  if (-not $root) { $root = '.' }
  try { $text = [System.IO.File]::ReadAllText((Join-Path $root 'version-manifest.json')) }
  catch { return '' }
  $m = [regex]::Match($text, '"skillsVersion"\s*:\s*"([^"]*)"')
  if ($m.Success) { return $m.Groups[1].Value }
  return ''
}

# Get-Sanitized: sanitize free-ish text to keep the assembled JSON valid and
# bounded. Strips anything outside a safe charset (so no quotes / backslashes /
# control chars / pipes survive) and caps length.
function Get-Sanitized([string]$Value) {
  if ($null -eq $Value) { return '' }
  $s = $Value -creplace '[^A-Za-z0-9:._/ -]', '_'
  if ($s.Length -gt 120) { $s = $s.Substring(0, 120) }
  return $s
}

# --- main ------------------------------------------------------------------
function Main {
  # Opt-out: send by default; skip only when telemetry is explicitly disabled
  # (UIPATH_TELEMETRY_DISABLED=1 or =true). Matches the CLI's isTelemetryDisabled()
  # gate, so `uip track` and this hook short-circuit on the same values.
  if ($env:UIPATH_TELEMETRY_DISABLED -cin @('1', 'true')) { exit 0 }

  $raw = ''
  try { $raw = [Console]::In.ReadToEnd() } catch { exit 0 }
  $payload = $null
  try { $payload = $raw | ConvertFrom-Json -ErrorAction Stop } catch { exit 0 }
  if (-not (Test-JsonObject $payload)) { exit 0 }

  # ENVELOPE region.
  $hookEvent      = [string](Get-Prop $payload 'hook_event_name')
  $tool           = [string](Get-Prop $payload 'tool_name')
  $toolUseId      = [string](Get-Prop $payload 'tool_use_id')
  $sessionId      = [string](Get-Prop $payload 'session_id')
  $permissionMode = [string](Get-Prop $payload 'permission_mode')
  $durationMs     = Get-Prop $payload 'duration_ms'
  $agentType      = [string](Get-Prop $payload 'agent_type')
  $sessionSource  = [string](Get-Prop $payload 'source')
  $reason         = [string](Get-Prop $payload 'reason')
  $agentModel     = [string](Get-Prop $payload 'model')

  $effortLevel = ''
  $effort = Get-Prop $payload 'effort'
  if (Test-JsonObject $effort) { $effortLevel = [string](Get-Prop $effort 'level') }

  # tool_input region.
  $skill = ''; $command = ''; $filePath = ''; $subagentType = ''
  $toolInput = Get-Prop $payload 'tool_input'
  if (Test-JsonObject $toolInput) {
    $skill        = [string](Get-Prop $toolInput 'skill')
    $command      = [string](Get-Prop $toolInput 'command')
    $filePath     = [string](Get-Prop $toolInput 'file_path')
    $subagentType = [string](Get-Prop $toolInput 'subagent_type')
    # Codex spawn_agent carries the spawned type in tool_input.agent_type;
    # normalize it to subagentType so it lands in the same field as Claude and
    # never collides with the envelope agent_type (agentType).
    if (-not $subagentType) { $subagentType = [string](Get-Prop $toolInput 'agent_type') }
  }

  # tool_response region. Presence of the KEY (any value shape) marks the
  # response as seen; the fields are read only when it is a real object
  # (Codex serializes tool_response as a JSON string -> ok|unknown only).
  $responseSeen = [bool]$payload.PSObject.Properties['tool_response']
  $interrupted = ''; $success = ''; $resolvedModel = ''
  $toolResponse = Get-Prop $payload 'tool_response'
  if (Test-JsonObject $toolResponse) {
    $interrupted   = ConvertTo-BoolString (Get-Prop $toolResponse 'interrupted')
    $success       = ConvertTo-BoolString (Get-Prop $toolResponse 'success')
    $resolvedModel = [string](Get-Prop $toolResponse 'resolvedModel')
  }

  # Map the hook event to a canonical eventName; drop unrecognized events.
  $eventName = Get-EventName $hookEvent
  if (-not $eventName) { exit 0 }

  # Derived only on tool-use; keep defined so the fixed key set always assembles.
  $skillName = ''; $uipSubcommand = ''; $fileExt = ''; $subagentModel = ''

  if ($eventName -eq 'tool-use') {
    # tool-use is per-call: gate on plugin attribution, then derive tool fields.
    if (-not (Test-UipathCall $tool $skill $subagentType $command $filePath)) { exit 0 }
    $derived = Get-DerivedFields $tool $skill $command $filePath
    $skillName     = $derived.skillName
    $uipSubcommand = $derived.uipSubcommand
    $fileExt       = $derived.fileExt
    $outcome       = Get-Outcome $interrupted $success $responseSeen
    $subagentModel = Get-ModelFamily $resolvedModel
  }
  else {
    # Lifecycle events are session-scoped — they fire for every session where
    # this plugin is installed (the activation-rate denominator), so they skip
    # the per-call attribution gate and tool-field derivation.
    $outcome = Get-LifecycleOutcome $hookEvent
  }

  # Enforce the per-event field scoping the contract documents: session_source
  # only on session-start, reason only on session-end. `source`/`reason` are
  # extracted from ANY event's envelope, so a future payload that adds either
  # key to another event must not bleed into these dimensions.
  if ($eventName -ne 'session-start') { $sessionSource = '' }
  if ($eventName -ne 'session-end')   { $reason = '' }

  $skillsVer = Read-SkillsVersion

  # durationMs is a JSON number. Emit JSON null (not 0) when absent, so a missing
  # value doesn't skew latency aggregations. The CLI drops a null-valued
  # property, so a missing duration records as "no data". Stays unquoted.
  $durJson = 'null'
  if ($null -ne $durationMs -and "$durationMs" -cmatch '^[0-9]+$') { $durJson = "$durationMs" }

  # Assemble the canonical, ordered, flat JSON. The key set is defined ONCE
  # here (fixed order, every key always emitted). Each row is
  # (name, kind, value): `s` -> JSON string, `n` -> JSON number/literal. Every
  # string value passes Get-Sanitized, so no quote/backslash can survive into
  # the assembled JSON.
  $spec = @(
    @('schemaVersion',  'n', "$SCHEMA_VERSION"),
    @('eventName',      's', $eventName),
    @('toolName',       's', $tool),
    @('skillName',      's', $skillName),
    @('uipSubcommand',  's', $uipSubcommand),
    @('fileExtension',  's', $fileExt),
    @('outcome',        's', $outcome),
    @('permissionMode', 's', $permissionMode),
    @('effortLevel',    's', $effortLevel),
    @('skillsVersion',  's', $skillsVer),
    @('toolUseId',      's', $toolUseId),
    @('session_id',     's', $sessionId),
    @('subagentModel',  's', $subagentModel),
    @('subagentType',   's', $subagentType),
    @('agentType',      's', $agentType),
    @('agent_model',    's', $agentModel),
    @('session_source', 's', $sessionSource),
    @('reason',         's', $reason),
    @('durationMs',     'n', $durJson)
  )
  $parts = foreach ($field in $spec) {
    if ($field[1] -eq 'n') { '"' + $field[0] + '":' + $field[2] }
    else { '"' + $field[0] + '":"' + (Get-Sanitized $field[2]) + '"' }
  }
  $json = '{' + ($parts -join ',') + '}'

  # Hand off to the CLI telemetry tracker. The CLI maps our eventName token to
  # the uip.skills.<event> name, stamps source: "skills-plugin", attaches the
  # authenticated cloud identity + CLI app version, owns transport + flush,
  # redacts PII, and drops any non-scalar value (so a null durationMs
  # disappears). Send no envelope and no `source` (the CLI overrides it).
  #
  # `uip track` is never-fail (exits 0, emits nothing when telemetry is opted
  # out); piping to it is harmless even if the CLI is absent (the catch
  # swallows the command-not-found error). The hook is registered async in
  # hooks.json (sync with a 30s timeout on SessionEnd — see header), so the
  # agent never waits on this call mid-session.
  try { $json | & uip track *> $null } catch { }

  exit 0
}

Main
