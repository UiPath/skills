#!/bin/bash
# Ensures @uipath/cli and @uipath/rpa-tool are installed globally.
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
    echo "Please restart your terminal, then run: npm install -g @uipath/cli" >&2
    exit 2
  fi
}

# Force the `@uipath` scope to public npm. If a user's `~/.npmrc` maps
# `@uipath` to GitHub Packages (the internal feed), `latest` resolves
# to a `1.0.0-alpha.*` prerelease instead of the public stable line.
# `--registry=` does NOT bypass scope mappings — only the scope-specific
# override does. Apply to `outdated` (registry lookup) and `install`;
# `ls` reads disk and doesn't need it.
UIPATH_REGISTRY_FLAG="--@uipath:registry=https://registry.npmjs.org/"

# npm install -g always re-downloads and re-installs, even if the same version
# is already present. This is slow for a synchronous session hook and also
# re-triggers package lifecycle scripts. Check first, install only when needed.
# Stay silent on the happy path: Claude Code surfaces ANY stderr from an
# exit-0 SessionStart hook as "Failed with non-blocking status code",
# which is misleading. Capture install output and only emit on failure.
ensure_npm_package() {
  local pkg="$1"

  if npm ls -g "$pkg" --depth=0 &>/dev/null \
     && [ -z "$(npm outdated -g "$pkg" $UIPATH_REGISTRY_FLAG 2>/dev/null)" ]; then
    return
  fi

  # bun-global mirror of the same gate. On hosts that install @uipath
  # plugins via bun, the npm install fall-through below is guaranteed
  # to fail (the prerelease tarball ships `workspace:*` deps that npm
  # rejects with EUNSUPPORTEDPROTOCOL), so upgrade via bun instead.
  # Freshness query reuses `npm view` — pure registry read, no install
  # side-effects, honors $UIPATH_REGISTRY_FLAG.
  local bun_pkg_json="$HOME/.bun/install/global/node_modules/$pkg/package.json"
  if [ -f "$bun_pkg_json" ]; then
    local installed_ver latest_ver
    installed_ver="$(grep -m1 '"version"' "$bun_pkg_json" 2>/dev/null | sed -n 's/.*"version"[[:space:]]*:[[:space:]]*"\([^"]*\)".*/\1/p')"
    # `|| true` keeps `set -e` from killing the script on registry
    # errors; the lenient match below treats empty $latest_ver as "skip".
    latest_ver="$(npm view "$pkg" version $UIPATH_REGISTRY_FLAG 2>/dev/null || true)"

    # Lenient match — mirrors the npm path, which treats empty `npm
    # outdated` output (including transient registry errors) as "skip".
    if [ -n "$installed_ver" ] \
       && { [ -z "$latest_ver" ] || [ "$installed_ver" = "$latest_ver" ]; }; then
      return
    fi

    # Outdated → upgrade via bun. On failure, warn and continue: the
    # existing bun-installed copy still works, so a flaky upgrade
    # shouldn't break the session (asymmetric vs. the npm path's
    # exit 2, where install failure means no tool at all).
    local bun_output
    if command -v bun &>/dev/null && ! bun_output="$(bun install -g "$pkg" 2>&1)"; then
      echo "Warning: failed to upgrade $pkg via bun (continuing with installed $installed_ver):" >&2
      echo "$bun_output" >&2
    fi
    return
  fi

  local output
  if ! output="$(npm install -g $UIPATH_REGISTRY_FLAG "$pkg" 2>&1)"; then
    echo "Failed to install $pkg:" >&2
    echo "$output" >&2
    echo "Please run manually: npm install -g $UIPATH_REGISTRY_FLAG $pkg" >&2
    exit 2
  fi
}

# ── main ─────────────────────────────────────────────────────────────
ensure_npm
ensure_npm_package @uipath/cli
ensure_npm_package @uipath/rpa-tool
