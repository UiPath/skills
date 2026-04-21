#!/bin/bash
# Detects whether Claude Code has an allowlist for `uip` subcommands.
# If none is found, prints a one-line nudge pointing at /uipath:install-permissions.
# Non-blocking — never fails the session, even if detection fails.
# Cross-platform (macOS, Linux, Windows via Git Bash / MSYS / Cygwin).

# Only run inside a Claude Code plugin context.
if [ -z "${CLAUDE_PLUGIN_ROOT:-}" ]; then
  exit 0
fi

# Candidate settings files, most-to-least specific.
candidates=()
if [ -n "${CLAUDE_PROJECT_DIR:-}" ]; then
  candidates+=("$CLAUDE_PROJECT_DIR/.claude/settings.local.json")
  candidates+=("$CLAUDE_PROJECT_DIR/.claude/settings.json")
fi
candidates+=("$PWD/.claude/settings.local.json")
candidates+=("$PWD/.claude/settings.json")
candidates+=("$HOME/.claude/settings.json")

# If any candidate already mentions Bash(uip...) in its permissions, stay silent.
for f in "${candidates[@]}"; do
  [ -f "$f" ] || continue
  if grep -q 'Bash(uip' "$f" 2>/dev/null; then
    exit 0
  fi
done

# No allowlist detected — print a one-line nudge to stderr (the Claude Code
# SessionStart convention for status messages).
echo "uipath: To skip 25+ approval prompts per uip build, run: /uipath:install-permissions" >&2
exit 0
