#!/usr/bin/env bash
# ensure-migrator.sh — locate, download, and verify the UiPath Activity Migrator (UiPath.Upgrade.exe).
#
# TWIN SCRIPT: scripts/ensure-migrator.ps1 is the PowerShell twin of this file.
# The two must stay behaviorally identical; change both in the same PR.
#
# Usage:  bash ensure-migrator.sh [--check-only] [--force]
# Env:    UIPATH_ACTIVITY_MIGRATOR_DIR      install/cache root (default %LOCALAPPDATA%\UiPath\ActivityMigrator)
#         UIPATH_ACTIVITY_MIGRATOR_URL      archive URL (default https://download.uipath.com/upgrade/UiPath.Upgrade.Cli.zip)
#         UIPATH_ACTIVITY_MIGRATOR_OFFLINE  set to 1 to never touch the network
# Output: the last stdout line is one JSON object; see references/acquisition-guide.md § Script output contract.
# Exit:   0 ok, 1 error, 3 missing (check-only).
set -u

DEFAULT_URL="https://download.uipath.com/upgrade/UiPath.Upgrade.Cli.zip"
URL="${UIPATH_ACTIVITY_MIGRATOR_URL:-$DEFAULT_URL}"
OFFLINE="${UIPATH_ACTIVITY_MIGRATOR_OFFLINE:-0}"
CHECK_ONLY=0
FORCE=0
for arg in "$@"; do
  case "$arg" in
    --check-only) CHECK_ONLY=1 ;;
    --force) FORCE=1 ;;
    *) ;;
  esac
done

json_escape() { printf '%s' "$1" | sed -e 's/\\/\\\\/g' -e 's/"/\\"/g'; }
emit_error() {
  printf '{"status":"error","code":"%s","message":"%s"}\n' "$1" "$(json_escape "$2")"
  exit 1
}
to_win() { if command -v cygpath >/dev/null 2>&1; then cygpath -w "$1"; else printf '%s' "$1"; fi; }
to_unix() { if command -v cygpath >/dev/null 2>&1; then cygpath -u "$1"; else printf '%s' "$1"; fi; }
last_modified_from() { tr -d '\r' < "$1" | awk 'tolower($1)=="last-modified:"{sub(/^[^:]*: */,""); v=$0} END{print v}'; }

# --- 1. Windows only -------------------------------------------------------
case "$(uname -s 2>/dev/null)" in
  MINGW*|MSYS*|CYGWIN*) ;;
  *)
    [ "${OS:-}" = "Windows_NT" ] || emit_error not-windows "The Activity Migrator is a Windows-only .NET 8 desktop tool. Run this skill from a Windows machine that holds the project."
    ;;
esac

# --- 2. Resolve install root and any existing exe --------------------------
SOURCE=""
if [ -n "${UIPATH_ACTIVITY_MIGRATOR_DIR:-}" ]; then
  ROOT="$(to_unix "$UIPATH_ACTIVITY_MIGRATOR_DIR")"
  SOURCE="env"
else
  [ -n "${LOCALAPPDATA:-}" ] || emit_error verify-failed "LOCALAPPDATA is not set. Set UIPATH_ACTIVITY_MIGRATOR_DIR to an install folder."
  ROOT="$(to_unix "$LOCALAPPDATA")/UiPath/ActivityMigrator"
fi
CURRENT="$ROOT/current"
STAMP="$ROOT/.last-modified"
EXE=""
if [ -f "$ROOT/UiPath.Upgrade.exe" ]; then
  EXE="$ROOT/UiPath.Upgrade.exe"
elif [ -f "$CURRENT/UiPath.Upgrade.exe" ]; then
  EXE="$CURRENT/UiPath.Upgrade.exe"
fi
[ -n "$SOURCE" ] || SOURCE="cached"

if [ -z "$EXE" ] && [ "$CHECK_ONLY" = 1 ]; then
  printf '{"status":"missing","dir":"%s"}\n' "$(json_escape "$(to_win "$ROOT")")"
  exit 3
fi
if [ -z "$EXE" ] && [ "$OFFLINE" = 1 ]; then
  emit_error offline-missing "UIPATH_ACTIVITY_MIGRATOR_OFFLINE=1 and no tool found under $(to_win "$ROOT"). Place the extracted archive there; see references/acquisition-guide.md § Manual placement."
fi

# --- 3. Decide whether to download ----------------------------------------
NEED_DOWNLOAD=0
IS_UPDATE=0
if [ -z "$EXE" ]; then
  NEED_DOWNLOAD=1
elif [ "$FORCE" = 1 ]; then
  NEED_DOWNLOAD=1
elif [ "$SOURCE" = "env" ] || [ "$OFFLINE" = 1 ] || [ "$CHECK_ONLY" = 1 ]; then
  NEED_DOWNLOAD=0
else
  REMOTE_LM=""
  if command -v curl >/dev/null 2>&1; then
    HEAD_FILE="$ROOT/.head.tmp"
    if curl -sSIL --max-time 20 -o "$HEAD_FILE" "$URL" 2>/dev/null; then
      REMOTE_LM="$(last_modified_from "$HEAD_FILE")"
    fi
    rm -f "$HEAD_FILE"
  fi
  LOCAL_LM=""
  [ -f "$STAMP" ] && LOCAL_LM="$(tr -d '\r\n' < "$STAMP")"
  if [ -n "$REMOTE_LM" ] && [ -n "$LOCAL_LM" ] && [ "$REMOTE_LM" != "$LOCAL_LM" ]; then
    NEED_DOWNLOAD=1
    IS_UPDATE=1
  fi
  if [ -n "$REMOTE_LM" ] && [ -z "$LOCAL_LM" ]; then
    printf '%s' "$REMOTE_LM" > "$STAMP"
  fi
fi

# --- 4. Download and extract ----------------------------------------------
if [ "$NEED_DOWNLOAD" = 1 ]; then
  command -v curl >/dev/null 2>&1 || emit_error download-failed "curl not found. Download $URL manually; see references/acquisition-guide.md § Manual placement."
  mkdir -p "$ROOT" || emit_error download-failed "Cannot create $(to_win "$ROOT")."
  TMP_ZIP="$ROOT/UiPath.Upgrade.Cli.zip.tmp"
  HEADERS="$ROOT/.headers.tmp"
  CURL_ERR="$ROOT/.curl-error.tmp"
  rm -f "$TMP_ZIP" "$HEADERS" "$CURL_ERR"
  if ! curl -fSL --retry 3 --retry-delay 2 -D "$HEADERS" -o "$TMP_ZIP" "$URL" 2>"$CURL_ERR"; then
    ERR="$(tr -d '\r\n' < "$CURL_ERR" | tail -c 300)"
    rm -f "$TMP_ZIP" "$HEADERS" "$CURL_ERR"
    emit_error download-failed "Download failed: $ERR. Check proxy settings (HTTPS_PROXY) or place the tool manually; see references/acquisition-guide.md § Manual placement."
  fi
  NEW_LM="$(last_modified_from "$HEADERS")"

  STAGE="$ROOT/.extract-tmp"
  rm -rf "$STAGE"
  mkdir -p "$STAGE"
  WIN_ZIP="$(to_win "$TMP_ZIP")"
  WIN_STAGE="$(to_win "$STAGE")"
  EXTRACTED=0
  if command -v powershell.exe >/dev/null 2>&1; then
    powershell.exe -NoProfile -NonInteractive -Command "\$ProgressPreference='SilentlyContinue'; Expand-Archive -LiteralPath '$WIN_ZIP' -DestinationPath '$WIN_STAGE' -Force" >/dev/null 2>&1 && EXTRACTED=1
  fi
  if [ "$EXTRACTED" = 0 ] && [ -x "/c/Windows/System32/tar.exe" ]; then
    /c/Windows/System32/tar.exe -xf "$WIN_ZIP" -C "$WIN_STAGE" >/dev/null 2>&1 && EXTRACTED=1
  fi
  if [ "$EXTRACTED" = 0 ] && command -v unzip >/dev/null 2>&1; then
    unzip -q -o "$TMP_ZIP" -d "$STAGE" >/dev/null 2>&1 && EXTRACTED=1
  fi
  if [ "$EXTRACTED" != 1 ]; then
    rm -rf "$STAGE"
    emit_error extract-failed "Could not extract $WIN_ZIP with Expand-Archive, tar, or unzip. Extract it manually into $(to_win "$CURRENT")."
  fi
  if [ ! -f "$STAGE/UiPath.Upgrade.exe" ] || [ ! -d "$STAGE/Extensions" ]; then
    rm -rf "$STAGE"
    emit_error extract-failed "Archive layout unexpected: UiPath.Upgrade.exe or Extensions/ missing after extraction."
  fi
  rm -rf "$CURRENT"
  mv "$STAGE" "$CURRENT" || emit_error extract-failed "Could not replace $(to_win "$CURRENT")."
  rm -f "$TMP_ZIP" "$HEADERS" "$CURL_ERR"
  [ -n "$NEW_LM" ] && printf '%s' "$NEW_LM" > "$STAMP"
  EXE="$CURRENT/UiPath.Upgrade.exe"
  if [ "$IS_UPDATE" = 1 ]; then SOURCE="updated"; else SOURCE="downloaded"; fi
fi

# --- 5. .NET Desktop Runtime 8 ---------------------------------------------
DOTNET=""
if command -v dotnet >/dev/null 2>&1; then
  DOTNET="dotnet"
else
  PF="$(to_unix "${ProgramFiles:-C:\\Program Files}")"
  [ -x "$PF/dotnet/dotnet.exe" ] && DOTNET="$PF/dotnet/dotnet.exe"
fi
RUNTIME=""
if [ -n "$DOTNET" ]; then
  RUNTIME="$("$DOTNET" --list-runtimes 2>/dev/null | tr -d '\r' | awk '$1=="Microsoft.WindowsDesktop.App" && $2 ~ /^8\./ {v=$2} END{print v}')"
fi
[ -n "$RUNTIME" ] || emit_error runtime-missing "Microsoft.WindowsDesktop.App 8.x not found. Install the .NET Desktop Runtime 8 (x64) from https://dotnet.microsoft.com/download/dotnet/8.0 and rerun."

# --- 6. Verify the tool answers --------------------------------------------
VERSION="$("$EXE" version 2>/dev/null | tr -d '\r' | tail -n 1)"
[ -n "$VERSION" ] || emit_error verify-failed "$(to_win "$EXE") did not print a version. The install may be incomplete; rerun with --force."

printf '{"status":"ok","exe":"%s","version":"%s","source":"%s","runtime":"%s"}\n' \
  "$(json_escape "$(to_win "$EXE")")" "$(json_escape "$VERSION")" "$SOURCE" "$(json_escape "$RUNTIME")"
exit 0
