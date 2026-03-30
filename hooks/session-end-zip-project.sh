#!/bin/bash
# Collects session traces for the UiPath Studio project that was worked on:
#   1. Creates .traces folder in user's Documents
#   2. Copies the session transcript into .traces/timestamp
#   3. Packs the project into .traces (best-effort)
# Runs at SessionEnd via the plugin hook.

# ── helpers ──────────────────────────────────────────────────────────

fail() {
  echo "$1" >&2
  exit 2
}

# Save stdin directly to a temp file to preserve raw JSON bytes.
# Bash mangles backslashes in variables, so we never store JSON in a shell var.
read_hook_input() {
  HOOK_INPUT_FILE=$(mktemp)
  cat > "$HOOK_INPUT_FILE"
}

# Parse a field from the saved JSON file using node.
# Node reads the file via process.argv to avoid /dev/stdin issues on Windows.
parse_field() {
  local field="$1"
  local win_path
  win_path="$(cygpath -w "$HOOK_INPUT_FILE" 2>/dev/null || echo "$HOOK_INPUT_FILE")"

  local value
  value="$(node -e "
    const d = JSON.parse(require('fs').readFileSync(process.argv[1], 'utf8'));
    process.stdout.write(d['$field'] || '');
  " "$win_path" 2>/dev/null)" || true
  echo "$value"
}

get_documents_dir() {
  local os
  os="$(uname -s 2>/dev/null || echo "Windows")"

  case "$os" in
    MINGW*|MSYS*|CYGWIN*|Windows*)
      local win_home="${USERPROFILE:-$HOME}"
      echo "$win_home/Documents"
      ;;
    Darwin*)
      echo "$HOME/Documents"
      ;;
    Linux*)
      echo "${XDG_DOCUMENTS_DIR:-$HOME/Documents}"
      ;;
    *) echo "$HOME/Documents" ;;
  esac
}

find_project_dir() {
  # Use cwd from the hook input — it's the working directory of the session
  local cwd
  cwd="$(parse_field cwd)"

  if [ -n "$cwd" ]; then
    local unix_cwd
    unix_cwd="$(cygpath "$cwd" 2>/dev/null || echo "$cwd")"

    if [ -f "$unix_cwd/project.json" ]; then
      echo "$unix_cwd"
      return
    fi
  fi

  # Fall back to current working directory
  if [ -f "./project.json" ]; then
    echo "$(pwd)"
    return
  fi

  echo ""
}

# ── step 1: create .traces/<timestamp> folder ───────────────────────
create_traces_dir() {
  local documents_dir
  documents_dir="$(get_documents_dir)"
  local timestamp
  timestamp="$(date +%Y%m%d_%H%M%S)"
  local traces_dir="$documents_dir/.traces/$timestamp"

  mkdir -p "$traces_dir"

  echo "$traces_dir"
}

# ── step 2: copy session transcript ─────────────────────────────────
copy_transcript() {
  local traces_dir="$1"

  local transcript_path
  transcript_path="$(parse_field transcript_path)"

  if [ -z "$transcript_path" ]; then
    return
  fi

  local unix_path
  unix_path="$(cygpath "$transcript_path" 2>/dev/null || echo "$transcript_path")"

  if [ ! -f "$unix_path" ]; then
    return
  fi

  cp "$unix_path" "$traces_dir/"
}

# ── step 3: pack project (best-effort) ──────────────────────────────
pack_project() {
  local project_dir="$1"
  local traces_dir="$2"

  if ! command -v uip &> /dev/null; then
    return
  fi

  local project_name
  project_name="$(basename "$project_dir")"
  local timestamp
  timestamp="$(date +%Y%m%d_%H%M%S)"

  local output
  output="$(uip rpa pack \
    --project-path "$project_dir" \
    --destination-path "$traces_dir" \
    --package-id "$project_name" \
    --package-version "1.0.0-snapshot.$timestamp" \
    --package-author "claude-session-hook" \
    --package-description "Session snapshot of $project_name" \
    2>&1)" || true
}

cleanup() {
  rm -f "$HOOK_INPUT_FILE"
}

# ── main ─────────────────────────────────────────────────────────────

read_hook_input
trap cleanup EXIT

traces_dir="$(create_traces_dir)"
copy_transcript "$traces_dir"

# project_dir="$(find_project_dir)"

# if [ -z "$project_dir" ]; then
#   exit 0
# fi
# pack_project "$project_dir" "$traces_dir"
