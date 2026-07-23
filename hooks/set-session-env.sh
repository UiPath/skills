#!/bin/bash
# SessionStart step: export the agent's session id to the uip CLI.
#
# TWIN SCRIPT: hooks/set-session-env.ps1 is the PowerShell twin of this file —
# any behavioral change here MUST be mirrored there in the same PR (see
# CLAUDE.md).
#
# Reads the SessionStart payload on stdin, takes its top-level `session_id`,
# and appends `export UIPATH_SESSION_ID='<id>'` to $CLAUDE_ENV_FILE so every
# subsequent Bash tool subprocess — and therefore every `uip` command the
# agent runs — inherits it. The CLI stamps that value as the `session_id`
# dimension on native command telemetry (UiPath/cli#2800), which joins the
# command stream with the skills events emitted by send-telemetry.sh: both
# streams then carry the same session id.
#
# Registered SYNCHRONOUSLY in hooks.json (no "async": true): the write must
# complete before the session's first Bash call, or early `uip` commands would
# miss the id. Costs a few ms (grep/sed/tr only, no network, no uip call).
#
# Deliberately NOT gated on UIPATH_TELEMETRY_DISABLED: writing a variable
# transmits nothing — whether any event carrying it is ever sent stays
# governed by the CLI's own telemetry gate.
#
# Safety:
#   - host wins: no-op when UIPATH_SESSION_ID is already set in the env;
#   - idempotent: no-op when the env file already exports it;
#   - injection-safe: $CLAUDE_ENV_FILE is sourced by the agent, so the value
#     is stripped to [A-Za-z0-9._-] and length-capped before being written
#     inside single quotes (agent session ids are UUIDs, so a legitimate
#     value is never altered);
#   - never-fail: always exits 0, never blocks the session.

set +e

main() {
  [ -n "$CLAUDE_ENV_FILE" ] || exit 0
  [ -z "$UIPATH_SESSION_ID" ] || exit 0
  if [ -f "$CLAUDE_ENV_FILE" ] \
    && grep -q '^export UIPATH_SESSION_ID=' "$CLAUDE_ENV_FILE" 2>/dev/null; then
    exit 0
  fi

  # Top-level `session_id` from the SessionStart payload. The payload for this
  # event is small and carries no tool output, and the value is hard-sanitized
  # anyway, so a plain grep is sufficient here (no region-scoped pass needed).
  sid="$(grep -oE '"session_id"[[:space:]]*:[[:space:]]*"[^"]*"' \
    | head -1 | sed 's/.*"\([^"]*\)"$/\1/' | tr -cd 'A-Za-z0-9._-' | cut -c1-64)"
  [ -n "$sid" ] || exit 0

  # If the file exists but doesn't end with a newline (another hook's partial
  # write), appending directly would concatenate onto its last line and could
  # break the sourced env file for the whole session — repair it first.
  # `tail -c 1` in a $() strips a trailing newline, so "" means the file is
  # newline-terminated.
  if [ -s "$CLAUDE_ENV_FILE" ] && [ -n "$(tail -c 1 "$CLAUDE_ENV_FILE" 2>/dev/null)" ]; then
    printf '\n' >> "$CLAUDE_ENV_FILE" 2>/dev/null
  fi

  printf "export UIPATH_SESSION_ID='%s'\n" "$sid" >> "$CLAUDE_ENV_FILE" 2>/dev/null

  exit 0
}

main
