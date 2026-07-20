# SessionStart step: export the agent's session id to the uip CLI.
#
# TWIN SCRIPT: hooks/set-session-env.sh is the bash twin of this file — any
# behavioral change here MUST be mirrored there in the same PR (see CLAUDE.md).
#
# Reads the SessionStart payload on stdin, takes its top-level `session_id`,
# and appends `export UIPATH_SESSION_ID='<id>'` to $env:CLAUDE_ENV_FILE so
# every subsequent shell tool subprocess — and therefore every `uip` command
# the agent runs — inherits it. The CLI stamps that value as the `session_id`
# dimension on native command telemetry (UiPath/cli#2800), which joins the
# command stream with the skills events emitted by send-telemetry.ps1: both
# streams then carry the same session id.
#
# Registered SYNCHRONOUSLY in hooks.json (no "async": true): the write must
# complete before the session's first shell call, or early `uip` commands
# would miss the id. Costs a few ms (regex only, no network, no uip call).
#
# Deliberately NOT gated on UIPATH_TELEMETRY_DISABLED: writing a variable
# transmits nothing — whether any event carrying it is ever sent stays
# governed by the CLI's own telemetry gate.
#
# Safety:
#   - host wins: no-op when UIPATH_SESSION_ID is already set in the env;
#   - idempotent: no-op when the env file already exports it;
#   - injection-safe: $env:CLAUDE_ENV_FILE is sourced by the agent, so the
#     value is stripped to [A-Za-z0-9._-] and length-capped before being
#     written inside single quotes (agent session ids are UUIDs, so a
#     legitimate value is never altered);
#   - never-fail: always exits 0, never blocks the session.
#
# Runs under Windows PowerShell 5.1 and PowerShell 7+ (pwsh).

$ErrorActionPreference = 'SilentlyContinue'

function Main {
  $envFile = $env:CLAUDE_ENV_FILE
  if (-not $envFile) { exit 0 }
  if ($env:UIPATH_SESSION_ID) { exit 0 }

  $existing = ''
  if (Test-Path -LiteralPath $envFile -PathType Leaf) {
    try { $existing = [System.IO.File]::ReadAllText($envFile) } catch { $existing = '' }
    if ($existing -cmatch '(?m)^export UIPATH_SESSION_ID=') { exit 0 }
  }

  # Top-level `session_id` from the SessionStart payload. The payload for this
  # event is small and carries no tool output, and the value is hard-sanitized
  # anyway, so a plain regex is sufficient here (no full JSON parse needed).
  $payload = ''
  try { $payload = [Console]::In.ReadToEnd() } catch { exit 0 }
  $sid = ''
  $m = [regex]::Match($payload, '"session_id"\s*:\s*"([^"]*)"')
  if ($m.Success) { $sid = $m.Groups[1].Value }
  $sid = $sid -replace '[^A-Za-z0-9._-]', ''
  if ($sid.Length -gt 64) { $sid = $sid.Substring(0, 64) }
  if (-not $sid) { exit 0 }

  # If the file exists but doesn't end with a newline (another hook's partial
  # write), appending directly would concatenate onto its last line and could
  # break the sourced env file for the whole session — repair it first.
  $prefix = ''
  if ($existing -and -not $existing.EndsWith("`n")) { $prefix = "`n" }

  try {
    [System.IO.File]::AppendAllText($envFile, "${prefix}export UIPATH_SESSION_ID='$sid'`n")
  }
  catch { }

  exit 0
}

Main
