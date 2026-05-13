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

# Force `@uipath` to public npm. Narrowly guards users who set a custom
# default `registry=...` in `~/.npmrc` (e.g., a corporate proxy/mirror)
# but no `@uipath:registry=...` scope override — without this flag,
# `outdated`, `view`, and `install` route through their default mirror,
# which may not host `@uipath` or may serve a different `latest`.
# `--registry=` does NOT bypass scope mappings; only the scope-specific
# override does. Apply to `outdated` / `view` (registry lookup) and
# `install`; `ls` reads disk and doesn't need it.
#
# Users WITH a non-public `@uipath:registry=...` scope mapping (UiPath
# devs on the GitHub Packages prerelease line, private mirrors aliasing
# the scope) are skipped earlier by `is_from_other_feed`, so this flag
# never clobbers a deliberate non-public install — it only protects the
# narrow "custom default registry, no scope mapping" path.
UIPATH_REGISTRY_FLAG="--@uipath:registry=https://registry.npmjs.org/"

# True if $1 is a POSIX symlink, a Windows directory symlink, OR a
# Windows directory junction. bash `[ -L ]` catches POSIX symlinks but
# NOT Windows junctions — and junctions are the default fallback
# `npm link` uses on Windows when run without developer mode or admin
# rights, so a pure `[ -L ]` check silently misses the most common
# Windows local-link layout.
#
# Windows: delegate to `fsutil reparsepoint query`. Purpose-built,
# ships with every Windows install since XP, exits 0 iff the path is
# a reparse point (covers symlinks AND junctions), locale-independent,
# and `query` doesn't require admin. Reachable from git-bash / MSYS /
# Cygwin via Windows PATH lookup, and from WSL via interop (`.exe`).
# POSIX (Linux/macOS): fall back to `[ -L ]` — junctions don't exist.
is_symlink_or_junction() {
  local input="$1" posix_p win_p
  # Compute both forms: POSIX (for bash `[ -e ]`) and Windows (for fsutil).
  # The caller may hand us either form — npm on Windows returns `C:\...`
  # even when invoked from WSL/Cygwin/MSYS bash, while `$HOME` is POSIX.
  # IMPORTANT: wslpath and cygpath misbehave when given the form they
  # output (`wslpath -u /home/foo` prepends /mnt/c/, `wslpath -w C:\foo`
  # strips backslashes). Detect input form and convert in one direction
  # only.
  if [[ "$input" =~ ^[A-Za-z]: ]]; then
    win_p="$input"
    if command -v wslpath &>/dev/null; then
      posix_p="$(wslpath -u "$input" 2>/dev/null || echo "$input")"
    elif command -v cygpath &>/dev/null; then
      posix_p="$(cygpath -u "$input" 2>/dev/null || echo "$input")"
    else
      posix_p="$input"
    fi
  else
    posix_p="$input"
    if command -v wslpath &>/dev/null; then
      win_p="$(wslpath -w "$input" 2>/dev/null || echo "$input")"
    elif command -v cygpath &>/dev/null; then
      win_p="$(cygpath -w "$input" 2>/dev/null || echo "$input")"
    else
      win_p="$input"
    fi
  fi
  [ -e "$posix_p" ] || return 1
  # Windows: `fsutil reparsepoint query` is purpose-built — exits 0 iff
  # the path is a reparse point (covers symlinks AND junctions), ships
  # with every Windows install since XP, no admin needed for query, no
  # locale-dependent output to parse. Prefer the `.exe` form so WSL
  # interop resolves it without relying on PATHEXT.
  if command -v fsutil.exe &>/dev/null; then
    fsutil.exe reparsepoint query "$win_p" &>/dev/null
    return $?
  fi
  if command -v fsutil &>/dev/null; then
    fsutil reparsepoint query "$win_p" &>/dev/null
    return $?
  fi
  # POSIX (Linux/macOS): `[ -L ]` covers symbolic links; junctions don't
  # exist on these platforms.
  [ -L "$posix_p" ]
}

# Detect a local-source install via `npm link` / `bun link` (see the CLI
# repo README, "Building from Source"). Linked installs point at a
# working tree that is, by definition, ahead of the published `latest`
# tag — upgrading would clobber the developer's local build with an
# older registry version. Windows-junction handling lives in
# `is_symlink_or_junction`.
is_linked_package() {
  local pkg="$1"
  local npm_root
  npm_root="$(npm root -g 2>/dev/null)"
  [ -n "$npm_root" ] && is_symlink_or_junction "$npm_root/$pkg" && return 0
  is_symlink_or_junction "$HOME/.bun/install/global/node_modules/$pkg" && return 0
  return 1
}

# Detect a scope mapped to a non-public feed (GitHub Packages, an internal
# Artifactory, etc.). Such builds typically carry prerelease versions ahead
# of the public `latest` tag — forcing an upgrade against the public
# registry would downgrade the developer's chosen feed. Signal is the
# merged npm config for `@<scope>:registry`: if the user's `.npmrc` (any
# level) maps the package's scope to something other than the public
# registry, leave the install alone. Reads merged config so project/user/
# global/env overrides are all honored. Unscoped packages → never skip.
is_from_other_feed() {
  local pkg="$1" scope cfg
  case "$pkg" in
    @*/*) scope="${pkg%%/*}" ;;
    *) return 1 ;;
  esac
  cfg="$(npm config get "$scope:registry" 2>/dev/null)"
  if [ -z "$cfg" ] || [ "$cfg" = "undefined" ]; then
    return 1
  fi
  case "${cfg%/}" in
    https://registry.npmjs.org) return 1 ;;
    *) return 0 ;;
  esac
}

# npm install -g always re-downloads and re-installs, even if the same version
# is already present. This is slow for a synchronous session hook and also
# re-triggers package lifecycle scripts. Check first, install only when needed.
# Stay silent on the happy path: Claude Code surfaces ANY stderr from an
# exit-0 SessionStart hook as "Failed with non-blocking status code",
# which is misleading. Capture install output and only emit on failure.
ensure_npm_package() {
  local pkg="$1"

  if is_linked_package "$pkg" || is_from_other_feed "$pkg"; then
    return
  fi

  if npm ls -g "$pkg" --depth=0 &>/dev/null \
     && [ -z "$(npm outdated -g "$pkg" $UIPATH_REGISTRY_FLAG 2>/dev/null)" ]; then
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
