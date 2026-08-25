# Detects whether Claude Code has an allowlist for `uip` subcommands.
# If none is found, prints a one-line nudge pointing at /uipath:install-permissions.
# Non-blocking — never fails the session, even if detection fails.
# Runs under Windows PowerShell 5.1 and PowerShell 7+ (pwsh).
#
# TWIN SCRIPT: hooks/suggest-permissions.sh is the bash twin of this file —
# any behavioral change here MUST be mirrored there in the same PR (see
# CLAUDE.md).

$ErrorActionPreference = 'SilentlyContinue'

# Only run inside a Claude Code plugin context.
if (-not $env:CLAUDE_PLUGIN_ROOT) { exit 0 }

# Codex exposes Claude-compatible plugin environment variables for hook
# compatibility. This nudge is Claude-specific, so keep Codex sessions silent.
if ($env:PLUGIN_ROOT) { exit 0 }

# Candidate settings files, most-to-least specific.
$candidates = @()
if ($env:CLAUDE_PROJECT_DIR) {
  $candidates += Join-Path $env:CLAUDE_PROJECT_DIR '.claude/settings.local.json'
  $candidates += Join-Path $env:CLAUDE_PROJECT_DIR '.claude/settings.json'
}
$cwd = (Get-Location).Path
$candidates += Join-Path $cwd '.claude/settings.local.json'
$candidates += Join-Path $cwd '.claude/settings.json'
$candidates += Join-Path $HOME '.claude/settings.json'

# If any candidate already mentions Bash(uip...) in its permissions, stay silent.
# Intentional simplification: this matches `allow`, `ask`, AND `deny` blocks.
# Any explicit `uip` rule means the user has made a decision about this CLI —
# we don't second-guess by nudging them toward a permissive allowlist.
foreach ($f in $candidates) {
  if (-not (Test-Path -LiteralPath $f -PathType Leaf)) { continue }
  try {
    if (Select-String -LiteralPath $f -Pattern 'Bash(uip' -SimpleMatch -Quiet) { exit 0 }
  }
  catch { }
}

# No allowlist detected — print a one-line nudge to stderr (the Claude Code
# SessionStart convention for status messages).
[Console]::Error.WriteLine('uipath: To skip 25+ approval prompts per uip build, run: /uipath:install-permissions')
exit 0
