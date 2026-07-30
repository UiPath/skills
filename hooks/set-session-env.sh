#!/bin/bash
# SessionStart step: export the agent's session id and the skills plugin
# version to the uip CLI.
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
# Also reads the skills/CLI co-version from version-manifest.json (same
# "skillsVersion" field send-telemetry.sh's read_skills_version() reads) and
# appends `export UIPATH_SKILLS_VERSION='<version>'`, so `uip feedback send`
# can print it in the ticket's Environment block (UiPath/cli#2637, PR #1608).
#
# Registered SYNCHRONOUSLY in hooks.json (no "async": true): the write must
# complete before the session's first Bash call, or early `uip` commands would
# miss the id. Costs a few ms (grep/sed/tr only, no network, no uip call).
#
# Deliberately NOT gated on UIPATH_TELEMETRY_DISABLED: writing a variable
# transmits nothing — whether any event carrying it is ever sent stays
# governed by the CLI's own telemetry gate.
#
# Safety (applies independently to each export):
#   - host wins: no-op when the target var is already set in the env;
#   - idempotent: no-op when the env file already exports it;
#   - injection-safe: $CLAUDE_ENV_FILE is sourced by the agent, so each value
#     is stripped to a safe charset and length-capped before being written
#     inside single quotes (agent session ids are UUIDs and skills versions
#     are dotted version strings, so a legitimate value is never altered);
#   - never-fail: always exits 0, never blocks the session.

set +e

# append_export <env_var_name> <sanitized_value>: write
# `export <env_var_name>='<value>'` to $CLAUDE_ENV_FILE, repairing a missing
# trailing newline first (see the inline comment at the call site for why).
append_export() {
  if [ -s "$CLAUDE_ENV_FILE" ] && [ -n "$(tail -c 1 "$CLAUDE_ENV_FILE" 2>/dev/null)" ]; then
    printf '\n' >> "$CLAUDE_ENV_FILE" 2>/dev/null
  fi
  printf "export %s='%s'\n" "$1" "$2" >> "$CLAUDE_ENV_FILE" 2>/dev/null
}

# export_session_id <payload>: UIPATH_SESSION_ID from the SessionStart
# payload's top-level `session_id`.
export_session_id() {
  [ -z "$UIPATH_SESSION_ID" ] || return 0
  if [ -f "$CLAUDE_ENV_FILE" ] \
    && grep -q '^export UIPATH_SESSION_ID=' "$CLAUDE_ENV_FILE" 2>/dev/null; then
    return 0
  fi

  # The payload for this event is small and carries no tool output, and the
  # value is hard-sanitized anyway, so a plain grep is sufficient here (no
  # region-scoped pass needed).
  sid="$(printf '%s' "$1" | grep -oE '"session_id"[[:space:]]*:[[:space:]]*"[^"]*"' \
    | head -1 | sed 's/.*"\([^"]*\)"$/\1/' | tr -cd 'A-Za-z0-9._-' | cut -c1-64)"
  [ -n "$sid" ] || return 0

  append_export UIPATH_SESSION_ID "$sid"
}

# export_skills_version: UIPATH_SKILLS_VERSION from the "skillsVersion" field
# of ${CLAUDE_PLUGIN_ROOT}/version-manifest.json — same source and extraction
# as send-telemetry.sh's read_skills_version().
export_skills_version() {
  [ -z "$UIPATH_SKILLS_VERSION" ] || return 0
  if [ -f "$CLAUDE_ENV_FILE" ] \
    && grep -q '^export UIPATH_SKILLS_VERSION=' "$CLAUDE_ENV_FILE" 2>/dev/null; then
    return 0
  fi

  ver="$(grep -oE '"skillsVersion"[[:space:]]*:[[:space:]]*"[^"]*"' \
    "${CLAUDE_PLUGIN_ROOT:-.}/version-manifest.json" 2>/dev/null \
    | head -1 | sed 's/.*"\([^"]*\)"$/\1/' | tr -cd 'A-Za-z0-9._-' | cut -c1-32)"
  [ -n "$ver" ] || return 0

  append_export UIPATH_SKILLS_VERSION "$ver"
}

main() {
  [ -n "$CLAUDE_ENV_FILE" ] || exit 0

  payload="$(cat)"
  export_session_id "$payload"
  export_skills_version

  exit 0
}

main
