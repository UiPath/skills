#!/bin/bash
# Ensures @uipath/uipcli and @uipath/rpa-tool are installed globally.
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
    echo "Please restart your terminal, then run: npm install -g @uipath/uipcli" >&2
    exit 2
  fi
}

ensure_github_packages_registry() {
  # @uipath packages are hosted on GitHub Packages, not the public npm registry.
  # Configure the @uipath scope to point there and authenticate with a token.
  local current_registry
  current_registry="$(npm config get @uipath:registry 2>/dev/null || echo "")"

  if [ "$current_registry" != "https://npm.pkg.github.com" ]; then
    echo "Configuring @uipath npm scope to use GitHub Packages registry..." >&2
    npm config set @uipath:registry https://npm.pkg.github.com
  fi

  if [ -z "${GH_NPM_REGISTRY_TOKEN:-}" ]; then
    echo "Error: GH_NPM_REGISTRY_TOKEN environment variable is not set." >&2
    echo "This token is required to install @uipath packages from GitHub Packages." >&2
    echo "Set it in your shell profile:" >&2
    echo "  export GH_NPM_REGISTRY_TOKEN=ghp_your_token_here" >&2
    exit 2
  fi

  # Set the auth token for npm.pkg.github.com
  npm config set //npm.pkg.github.com/:_authToken "$GH_NPM_REGISTRY_TOKEN"
}

ensure_npm_package() {
  local pkg="$1"
  echo "Installing or updating $pkg globally..." >&2

  if ! npm install -g "$pkg" 2>&1; then
    echo "Failed to install $pkg. Please run: npm install -g $pkg" >&2
    exit 2
  fi
}

ensure_uipcli_tool() {
  local pkg="$1"
  echo "Installing or updating uipcli tool ($pkg)..." >&2

  local output
  output="$(uipcli tools install "$pkg" 2>&1)"

  if echo "$output" | grep -qi "error"; then
    echo "Failed to install uipcli tool $pkg:" >&2
    echo "$output" >&2
    echo "Please run manually: uipcli tools install $pkg" >&2
    exit 2
  fi
}

# ── main ─────────────────────────────────────────────────────────────
ensure_npm
ensure_github_packages_registry
ensure_npm_package @uipath/uipcli
ensure_uipcli_tool @uipath/rpa-tool
