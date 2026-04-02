#!/bin/bash
# Ensures @uipath/cli, @uipath/servo and @uipath/rpa-tool are installed globally.
# Runs once per session via the SessionStart plugin hook.
# If npm is missing, attempts to install Node.js first.
# Supports Windows, macOS, and Linux.

set -e

# ── helpers ──────────────────────────────────────────────────────────
fail() {
  echo "$1" >&2
  echo "Please install Node.js from https://nodejs.org and restart your session." >&2
  exit 2
}

is_windows() {
  local os
  os="$(uname -s 2>/dev/null || echo "Windows")"
  case "$os" in
    MINGW*|MSYS*|CYGWIN*|Windows*) return 0 ;;
    *) return 1 ;;
  esac
}

ensure_npm() {
  command -v npm &> /dev/null && return

  echo "npm not found, attempting to install Node.js..." >&2

  local os
  os="$(uname -s 2>/dev/null || echo "Windows")"

  case "$os" in
    MINGW*|MSYS*|CYGWIN*|Windows*)
      if   command -v winget &> /dev/null; then
        winget install --id OpenJS.NodeJS.LTS \
          --accept-source-agreements --accept-package-agreements 2>&1
      elif command -v choco  &> /dev/null; then choco install nodejs-lts -y 2>&1
      elif command -v nvm    &> /dev/null; then nvm install --lts 2>&1 && nvm use --lts 2>&1
      else fail "No package manager found (winget, choco, or nvm)."; fi
      export PATH="$PATH:/c/Program Files/nodejs:/c/ProgramData/nvm"
      ;;
    Darwin*)
      if   command -v brew &> /dev/null; then brew install node 2>&1
      elif command -v nvm  &> /dev/null; then nvm install --lts 2>&1 && nvm use --lts 2>&1
      else fail "No package manager found (brew or nvm)."; fi
      ;;
    Linux*)
      if   command -v apt-get &> /dev/null; then sudo apt-get update -y && sudo apt-get install -y nodejs npm 2>&1
      elif command -v dnf     &> /dev/null; then sudo dnf install -y nodejs npm 2>&1
      elif command -v yum     &> /dev/null; then sudo yum install -y nodejs npm 2>&1
      elif command -v pacman  &> /dev/null; then sudo pacman -Sy --noconfirm nodejs npm 2>&1
      elif command -v nvm     &> /dev/null; then nvm install --lts 2>&1 && nvm use --lts 2>&1
      else fail "No supported package manager found."; fi
      ;;
    *) fail "Unsupported platform." ;;
  esac

  hash -r 2>/dev/null

  if ! command -v npm &> /dev/null; then
    echo "Node.js was installed but npm is not yet available in this session." >&2
    echo "Please restart your terminal, then run: npm install -g @uipath/cli @uipath/servo" >&2
    exit 2
  fi
}

# npm install -g always re-downloads and re-installs, even if the same version
# is already present. This is slow for a synchronous session hook and also
# re-triggers package lifecycle scripts (e.g. servo runs preinstall hooks
# that should only execute on actual version changes). Check first, install
# only when needed.
ensure_npm_package() {
  local pkg="$1"

  if npm ls -g "$pkg" --depth=0 &>/dev/null \
     && [ -z "$(npm outdated -g "$pkg" 2>/dev/null)" ]; then
    echo "$pkg is already installed and up to date." >&2
    return
  fi

  echo "Installing or updating $pkg globally..." >&2
  if ! npm install -g "$pkg" 2>&1; then
    echo "Failed to install $pkg. Please run: npm install -g $pkg" >&2
    exit 2
  fi
}

ensure_uip_tool() {
  local pkg="$1"
  echo "Installing or updating uip tool ($pkg)..." >&2

  local output
  output="$(uip tools install "$pkg" 2>&1)"

  if echo "$output" | grep -qi "error"; then
    echo "Failed to install uip tool $pkg:" >&2
    echo "$output" >&2
    echo "Please run manually: uip tools install $pkg" >&2
    exit 2
  fi
}

# ── main ─────────────────────────────────────────────────────────────
ensure_npm
ensure_npm_package @uipath/cli
if is_windows; then
  ensure_npm_package @uipath/servo
fi
ensure_uip_tool @uipath/rpa-tool
