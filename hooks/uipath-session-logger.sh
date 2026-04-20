#!/bin/bash
# Opt-in Claude Code session logger for UiPath skills.
# Wired into hooks.json — invoked as:
#   uipath-session-logger.sh <EVENT_NAME>
# with the hook JSON payload on stdin.
#
# Writes to <cwd>/.uipath-logs/<session-id>/ when UIPATH_SESSION_LOG is set
# to one of 1, true, yes, on (case-insensitive). Never fails the session.
#
# See skills/uipath-session-logs/ for the user-facing documentation.

EVENT="${1:-}"

# ── Enablement gate ──────────────────────────────────────────────────
# Any failure below this line is swallowed — we must never block the user.
case "$(printf '%s' "${UIPATH_SESSION_LOG:-}" | tr '[:upper:]' '[:lower:]')" in
  1|true|yes|on) ;;
  *) exit 0 ;;
esac

warn() { printf '[uipath-session-logger] %s\n' "$*" >&2; }

# All further errors are caught and logged; the script still exits 0.
{

set +e

if ! command -v jq >/dev/null 2>&1; then
  warn "jq not found on PATH — capture disabled for this session. Install jq to enable."
  exit 0
fi

# ── Read payload ─────────────────────────────────────────────────────
# Hook JSON is delivered on stdin. Buffer it once; reuse for every query.
PAYLOAD="$(cat)"
if [ -z "$PAYLOAD" ]; then
  warn "empty hook payload for event=$EVENT"
  exit 0
fi

# jq helper — returns empty string on parse failure instead of failing.
jget() { printf '%s' "$PAYLOAD" | jq -r "$1 // empty" 2>/dev/null; }

SESSION_ID="$(jget '.session_id')"
CWD_FROM_HOOK="$(jget '.cwd')"
CWD="${CWD_FROM_HOOK:-$(pwd)}"

if [ -z "$SESSION_ID" ]; then
  warn "missing .session_id in payload for event=$EVENT"
  exit 0
fi

LOG_DIR="$CWD/.uipath-logs/$SESSION_ID"
mkdir -p "$LOG_DIR" 2>/dev/null || { warn "cannot create $LOG_DIR"; exit 0; }

TS="$(date -u +%Y-%m-%dT%H:%M:%SZ)"

# Truncate any string field > TRUNC_BYTES; replace with a marker object.
# 64 KiB keeps single-tool logs reasonable while preserving most CLI output.
TRUNC_BYTES=65536

# Walks the given JSON value; for each string field larger than TRUNC_BYTES,
# replaces it with {truncated, bytes, sha256}. Non-string values are untouched.
truncate_large_strings() {
  local raw="$1"
  printf '%s' "$raw" | jq --argjson limit "$TRUNC_BYTES" '
    def walk_trunc:
      if type == "string" and (length > $limit) then
        { truncated: true, bytes: length }
      elif type == "array" then
        map(walk_trunc)
      elif type == "object" then
        with_entries(.value |= walk_trunc)
      else
        .
      end;
    walk_trunc
  ' 2>/dev/null
}

# Append a JSON object (one line) to a JSONL file.
append_jsonl() {
  local file="$1" obj="$2"
  printf '%s\n' "$obj" >> "$file" 2>/dev/null || warn "append failed: $file"
}

# ── Event dispatch ───────────────────────────────────────────────────
case "$EVENT" in
  SessionStart)
    # session.json — one-shot; do not overwrite a resumed session's metadata.
    if [ ! -f "$LOG_DIR/session.json" ]; then
      ENV_JSON="$(env | awk -F= '/^UIPATH_/{k=$1; sub(/^[^=]*=/,""); printf "%s\t%s\n", k, $0}' \
        | jq -R -s '
            split("\n") | map(select(length>0)) | map(split("\t")) |
            map({key: .[0], value: .[1]}) | from_entries
          ' 2>/dev/null)"
      [ -z "$ENV_JSON" ] && ENV_JSON='{}'

      jq -n \
        --arg session_id "$SESSION_ID" \
        --arg cwd "$CWD" \
        --arg event "$EVENT" \
        --arg ts "$TS" \
        --argjson env "$ENV_JSON" \
        '{session_id:$session_id, cwd:$cwd, hook_event_name:$event, start_ts:$ts, env:$env}' \
        > "$LOG_DIR/session.json" 2>/dev/null \
        || warn "failed to write session.json"
    fi

    # project-snapshot — copy *.uis / solution.json / project.json from cwd.
    SNAP="$LOG_DIR/project-snapshot"
    mkdir -p "$SNAP" 2>/dev/null
    copied=0
    for pattern in '*.uis' 'solution.json' 'project.json'; do
      for src in "$CWD"/$pattern; do
        [ -e "$src" ] || continue
        cp -p "$src" "$SNAP/" 2>/dev/null && copied=$((copied+1))
      done
    done
    if [ "$copied" -eq 0 ]; then
      rmdir "$SNAP" 2>/dev/null
    fi
    ;;

  UserPromptSubmit)
    PROMPT="$(jget '.prompt')"
    OBJ="$(jq -n -c \
      --arg ts "$TS" \
      --arg session_id "$SESSION_ID" \
      --arg prompt "$PROMPT" \
      '{ts:$ts, session_id:$session_id, prompt:$prompt}' 2>/dev/null)"
    [ -n "$OBJ" ] && append_jsonl "$LOG_DIR/prompts.jsonl" "$OBJ"
    ;;

  PreToolUse)
    TOOL="$(jget '.tool_name')"
    RAW_INPUT="$(printf '%s' "$PAYLOAD" | jq -c '.tool_input // null' 2>/dev/null)"
    SAFE_INPUT="$(truncate_large_strings "$RAW_INPUT")"
    [ -z "$SAFE_INPUT" ] && SAFE_INPUT='null'

    OBJ="$(jq -n -c \
      --arg ts "$TS" \
      --arg session_id "$SESSION_ID" \
      --arg tool "$TOOL" \
      --argjson input "$SAFE_INPUT" \
      '{ts:$ts, session_id:$session_id, phase:"pre", tool:$tool, input:$input}' 2>/dev/null)"
    [ -n "$OBJ" ] && append_jsonl "$LOG_DIR/tools.jsonl" "$OBJ"
    ;;

  PostToolUse)
    TOOL="$(jget '.tool_name')"
    RAW_RESP="$(printf '%s' "$PAYLOAD" | jq -c '.tool_response // null' 2>/dev/null)"
    SAFE_RESP="$(truncate_large_strings "$RAW_RESP")"
    [ -z "$SAFE_RESP" ] && SAFE_RESP='null'

    DURATION_MS="$(jget '.tool_duration_ms')"
    [ -z "$DURATION_MS" ] && DURATION_MS='null'

    OBJ="$(jq -n -c \
      --arg ts "$TS" \
      --arg session_id "$SESSION_ID" \
      --arg tool "$TOOL" \
      --argjson response "$SAFE_RESP" \
      --argjson duration "$DURATION_MS" \
      '{ts:$ts, session_id:$session_id, phase:"post", tool:$tool, response:$response, duration_ms:$duration}' 2>/dev/null)"
    [ -n "$OBJ" ] && append_jsonl "$LOG_DIR/tools.jsonl" "$OBJ"
    ;;

  Stop|SessionEnd)
    TOOLS_FILE="$LOG_DIR/tools.jsonl"
    PROMPTS_FILE="$LOG_DIR/prompts.jsonl"
    SESSION_FILE="$LOG_DIR/session.json"

    START_TS='null'
    [ -f "$SESSION_FILE" ] && START_TS="$(jq -c '.start_ts // null' "$SESSION_FILE" 2>/dev/null)"

    TOOL_COUNTS='{}'
    ERROR_COUNT=0
    if [ -f "$TOOLS_FILE" ]; then
      TOOL_COUNTS="$(jq -s -c '
        map(select(.phase=="pre")) | group_by(.tool)
        | map({key:.[0].tool, value:length}) | from_entries
      ' "$TOOLS_FILE" 2>/dev/null)"
      ERROR_COUNT="$(jq -s '
        map(select(.phase=="post")
            | select((.response | tostring | test("\"is_error\"\\s*:\\s*true"))
                  or ((.response.exit_code? // 0) != 0)))
        | length
      ' "$TOOLS_FILE" 2>/dev/null)"
    fi
    [ -z "$TOOL_COUNTS" ] && TOOL_COUNTS='{}'
    [ -z "$ERROR_COUNT" ] && ERROR_COUNT=0

    PROMPT_COUNT=0
    [ -f "$PROMPTS_FILE" ] && PROMPT_COUNT="$(wc -l < "$PROMPTS_FILE" | tr -d ' ')"

    TOTAL_BYTES=0
    for f in "$SESSION_FILE" "$PROMPTS_FILE" "$TOOLS_FILE"; do
      [ -f "$f" ] || continue
      size=$(wc -c < "$f" | tr -d ' ')
      TOTAL_BYTES=$((TOTAL_BYTES + size))
    done

    jq -n \
      --arg session_id "$SESSION_ID" \
      --argjson start_ts "$START_TS" \
      --arg end_ts "$TS" \
      --argjson tool_counts "$TOOL_COUNTS" \
      --argjson error_count "$ERROR_COUNT" \
      --argjson prompt_count "$PROMPT_COUNT" \
      --argjson total_bytes "$TOTAL_BYTES" \
      --arg event "$EVENT" \
      '{
        session_id:$session_id,
        start_ts:$start_ts,
        end_ts:$end_ts,
        prompt_count:$prompt_count,
        tool_counts:$tool_counts,
        error_count:$error_count,
        total_bytes:$total_bytes,
        finalized_on:$event
      }' > "$LOG_DIR/summary.json" 2>/dev/null \
      || warn "failed to write summary.json"
    ;;

  *)
    # Unknown event — ignore silently.
    ;;
esac

} 2>&1 | while IFS= read -r line; do
  # Forward only our tagged warnings to the real stderr; swallow the rest.
  case "$line" in
    '[uipath-session-logger]'*) printf '%s\n' "$line" >&2 ;;
  esac
done

exit 0
