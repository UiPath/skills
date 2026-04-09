#!/bin/bash
# Checks for new versions of the UiPath skills plugin.
# Runs once per session via the SessionStart plugin hook.
#
# Emits Claude Code hook JSON on stdout with `additionalContext` so Claude
# sees the upgrade notice in the session context BEFORE the first user prompt.
# See: https://code.claude.com/docs/en/hooks — SessionStart hookSpecificOutput.
#
# States:
#   - upgrade available and not snoozed  → emits JSON with upgrade notice
#   - just upgraded (marker present)     → emits JSON with "what's new" notice
#   - up to date / snoozed / offline     → emits nothing

set -e

STATE_DIR="$HOME/.uipath-skills"
CACHE_FILE="$STATE_DIR/last-update-check"
SNOOZE_FILE="$STATE_DIR/update-snoozed"
MARKER_FILE="$STATE_DIR/just-upgraded-from"
REMOTE_URL="https://raw.githubusercontent.com/UiPath/skills/main/.claude-plugin/plugin.json"

# Resolve plugin root so we can locate sibling scripts and plugin.json
PLUGIN_ROOT="${CLAUDE_PLUGIN_ROOT:-}"
if [ -z "$PLUGIN_ROOT" ]; then
  # Fallback: script is in hooks/, plugin root is one level up
  PLUGIN_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
fi

CONFIG_SCRIPT="$PLUGIN_ROOT/scripts/uipath-skills-config.sh"

# Read a config key via the shared config script (single source of truth)
config_get() {
  [ -f "$CONFIG_SCRIPT" ] || return 0
  bash "$CONFIG_SCRIPT" get "$1" 2>/dev/null
}

# Extract version from a plugin.json file
extract_version() {
  grep '"version"' "$1" 2>/dev/null | head -1 | sed 's/.*"\([0-9][^"]*\)".*/\1/'
}

now() {
  date +%s
}

# Emit a Claude Code SessionStart hook JSON payload with additionalContext.
# This is visible to Claude before the first user prompt.
emit_context() {
  local message="$1"
  # Escape backslashes and double quotes for JSON embedding
  local escaped
  escaped=$(printf '%s' "$message" | sed 's/\\/\\\\/g; s/"/\\"/g')
  printf '{"hookSpecificOutput":{"hookEventName":"SessionStart","additionalContext":"%s"}}\n' "$escaped"
}

# ── Step 0: Locate plugin.json and read local version ─────────────
PLUGIN_JSON="$PLUGIN_ROOT/.claude-plugin/plugin.json"
[ -f "$PLUGIN_JSON" ] || exit 0

LOCAL_VERSION=$(extract_version "$PLUGIN_JSON")
[ -z "$LOCAL_VERSION" ] && exit 0

# ── Step 1: Check if updates are disabled ──────────────────────────
update_check=$(config_get "update_check")
[ "$update_check" = "false" ] && exit 0

# ── Step 2: Check for just-upgraded marker ─────────────────────────
if [ -f "$MARKER_FILE" ]; then
  OLD_VERSION=$(cat "$MARKER_FILE" 2>/dev/null)
  rm -f "$MARKER_FILE"
  emit_context "UiPath skills plugin just upgraded from v${OLD_VERSION} to v${LOCAL_VERSION}. Invoke the uipath-upgrade skill to summarize what changed (read CHANGELOG.md between the two versions) and then continue with the user's task."
  exit 0
fi

mkdir -p "$STATE_DIR"

# ── Step 3: Check cache ───────────────────────────────────────────
CACHED_STATUS=""
CACHED_REMOTE=""
if [ -f "$CACHE_FILE" ]; then
  CACHED=$(cat "$CACHE_FILE" 2>/dev/null)
  CACHED_STATUS=$(echo "$CACHED" | awk '{print $1}')
  CACHED_LOCAL=$(echo "$CACHED" | awk '{print $2}')
  CACHED_REMOTE=$(echo "$CACHED" | awk '{print $3}')
  CACHED_EPOCH=$(echo "$CACHED" | awk '{print $4}')
  NOW=$(now)

  # Invalidate cache if local version changed (user manually updated)
  if [ "$CACHED_LOCAL" = "$LOCAL_VERSION" ] && [ -n "$CACHED_EPOCH" ]; then
    AGE=$(( NOW - CACHED_EPOCH ))

    if [ "$CACHED_STATUS" = "UP_TO_DATE" ] && [ "$AGE" -lt 3600 ]; then
      # Up to date, cache fresh (60 min TTL)
      exit 0
    elif [ "$CACHED_STATUS" = "UPGRADE_AVAILABLE" ] && [ "$AGE" -lt 43200 ]; then
      # Upgrade available, cache fresh (720 min TTL) — fall through to snooze check
      :
    else
      # Cache expired, fall through to fetch
      CACHED_STATUS=""
    fi
  else
    CACHED_STATUS=""
  fi
fi

# ── Step 4: Check snooze ─────────────────────────────────────────
check_snooze() {
  [ -f "$SNOOZE_FILE" ] || return 1

  local snoozed_version snoozed_level snoozed_epoch
  snoozed_version=$(awk '{print $1}' "$SNOOZE_FILE" 2>/dev/null)
  snoozed_level=$(awk '{print $2}' "$SNOOZE_FILE" 2>/dev/null)
  snoozed_epoch=$(awk '{print $3}' "$SNOOZE_FILE" 2>/dev/null)

  local remote_ver="${1:-}"

  # New version resets snooze
  if [ -n "$remote_ver" ] && [ "$remote_ver" != "$snoozed_version" ]; then
    rm -f "$SNOOZE_FILE"
    return 1
  fi

  local NOW delay
  NOW=$(now)
  case "$snoozed_level" in
    1) delay=86400 ;;    # 24h
    2) delay=172800 ;;   # 48h
    *) delay=604800 ;;   # 7d
  esac

  if [ $(( NOW - snoozed_epoch )) -lt "$delay" ]; then
    return 0  # Still snoozed
  fi

  return 1  # Snooze expired
}

# If we have a cached UPGRADE_AVAILABLE and snooze is active, stay quiet
if [ "$CACHED_STATUS" = "UPGRADE_AVAILABLE" ]; then
  if check_snooze "$CACHED_REMOTE"; then
    exit 0
  fi
  emit_context "UiPath skills plugin upgrade available: v${LOCAL_VERSION} → v${CACHED_REMOTE}. Invoke the uipath-upgrade skill to prompt the user for consent and perform the upgrade. Do not proceed until you have followed that skill's flow."
  exit 0
fi

# ── Step 5: Fetch remote version ──────────────────────────────────
TMPFILE=$(mktemp "${TMPDIR:-/tmp}/uipath-update-check.XXXXXX")
trap 'rm -f "$TMPFILE"' EXIT

if ! curl -sf --max-time 10 -o "$TMPFILE" "$REMOTE_URL" 2>/dev/null; then
  # Network failure — exit silently, retry next session
  exit 0
fi

REMOTE_VERSION=$(extract_version "$TMPFILE")
[ -z "$REMOTE_VERSION" ] && exit 0

# ── Step 6: Compare and output ────────────────────────────────────
NOW=$(now)

if [ "$LOCAL_VERSION" = "$REMOTE_VERSION" ]; then
  echo "UP_TO_DATE $LOCAL_VERSION $REMOTE_VERSION $NOW" > "$CACHE_FILE"
  exit 0
fi

# Versions differ — upgrade available
echo "UPGRADE_AVAILABLE $LOCAL_VERSION $REMOTE_VERSION $NOW" > "$CACHE_FILE"

# Check snooze before prompting
if check_snooze "$REMOTE_VERSION"; then
  exit 0
fi

emit_context "UiPath skills plugin upgrade available: v${LOCAL_VERSION} → v${REMOTE_VERSION}. Invoke the uipath-upgrade skill to prompt the user for consent and perform the upgrade. Do not proceed until you have followed that skill's flow."
