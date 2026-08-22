#!/usr/bin/env bash
# Config gate for a docker run of tests/experiments/flow-v2-preview.yaml.
#
# Asserts only the things that, when wrong, score as capability failures
# instead of config errors. Product behaviour (flow check/compile/scaffold) is
# deliberately NOT checked here: the eval measures that, and asserting CLI
# verbs here just rots.
#
# Pass --env HOME with the HOST value, as the runner does. Without it a manual
# `docker run` authenticates against the image's /root and reproduces nothing.
#
# Usage: tests/docker/flow-v2-preflight.sh [image] [uipath-home]
# Requires NODE_AUTH_TOKEN (GitHub Packages read:packages, SSO-authorized).
set -uo pipefail

IMG="${1:-skills-codex:latest}"
UIPATH_HOME="${2:-$HOME/.uipath}"
SKILLS_REPO="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
: "${NODE_AUTH_TOKEN:?NODE_AUTH_TOKEN must be set (GitHub Packages token)}"
[ -d "$UIPATH_HOME" ] || { echo "FAIL: no uipath home at $UIPATH_HOME"; exit 1; }

LOG="$(mktemp)"
trap 'rm -f "$LOG"' EXIT

docker run --rm \
  --env HOME="$HOME" \
  --env NODE_AUTH_TOKEN \
  --env UIPATH_CLI_DISABLE_VERSION_SYNC=1 \
  -v "$UIPATH_HOME:/.uipath:rw" \
  -v "$SKILLS_REPO:$SKILLS_REPO:ro" \
  --entrypoint bash "$IMG" -c '
    echo "HOME=$HOME"
    echo "userconfig=$(npm config get userconfig)"
    echo "uipath_registry=$(npm config get @uipath:registry)"
    echo "token_seen=$([ -n "${NODE_AUTH_TOKEN:-}" ] && echo yes || echo no)"
    uip login status 2>&1 | head -12
    d=$(mktemp -d); cd "$d"; npm init -y >/dev/null 2>&1
    npm install @uipath/flow-sdk >/dev/null 2>&1
    echo "SDK_VERSION=$(node -e "console.log(require(\"@uipath/flow-sdk/package.json\").version)" 2>&1)"
  ' >"$LOG" 2>&1

fail=0
chk() { if grep -qE "$2" "$LOG"; then echo "  PASS  $1"; else echo "  FAIL  $1"; fail=1; fi; }
echo "=== pre-flight: $IMG ==="
chk "container HOME is the forwarded host HOME" "^HOME=$HOME\$"
chk "npm userconfig is HOME-independent"        '^userconfig=/root/\.npmrc$'
chk "@uipath scope resolves to GitHub Packages" '^uipath_registry=https://npm\.pkg\.github\.com/?$'
chk "GH Packages token reached the container"   '^token_seen=yes$'
chk "uip reports a live login"                  '"Status": "Logged in"'
chk "flow-sdk installs in-sandbox"              '^SDK_VERSION=[0-9]+\.[0-9]+\.[0-9]+$'
if [ "$fail" -ne 0 ]; then echo "GATE=FAIL"; echo "--- container output ---"; cat "$LOG"; exit 1; fi
echo "GATE=PASS"
