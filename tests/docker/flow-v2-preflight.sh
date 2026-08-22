#!/usr/bin/env bash
# Pre-flight gate for a docker-driver run of the Flow v2 (Maestro builder-SDK)
# preview skills. Pairs with tests/experiments/flow-v2-preview.yaml.
#
# Runs ONE container that reproduces the harness environment and asserts the
# preconditions a 250-row run depends on. Every check here stands for a failure
# that has actually happened and that scores as a capability problem rather than
# a config one, so it is invisible in the results:
#
#   * npm cannot reach GitHub Packages  -> "@uipath/flow-sdk is not installed"
#                                          on every compile
#   * the login state is not readable   -> "Not logged in" on every tenant call
#   * the skills repo root is unmounted  -> criteria that shell out to
#                                          tests/tasks/**/_shared/*.py exit 2
#
# The single most important detail: pass --env HOME with the HOST value, exactly
# as the runner does. A manual `docker run` WITHOUT it authenticates fine
# against the image's /root and reproduces nothing.
#
# The login mount is `:/.uipath:rw`, byte-for-byte what nightly.yaml uses. That
# destination is the empirical one, not a derived one: it is the arrangement with
# a 500-task/night track record, and the "uip reports a live login" check below
# is what confirms it still holds for this image. Do not "fix" it to
# $HOME/.uipath without re-running this gate.
#
# Usage: tests/docker/flow-v2-preflight.sh [image] [uipath-home]
#   image        default skills-codex:latest
#   uipath-home  host dir holding .uipath login state, default $HOME/.uipath
#
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
    echo "HOME=$HOME"; node -v; echo "uip $(uip --version 2>&1 | tail -1)"
    echo "userconfig=$(npm config get userconfig)"
    echo "uipath_registry=$(npm config get @uipath:registry)"
    echo "token_seen=$([ -n "${NODE_AUTH_TOKEN:-}" ] && echo yes || echo no)"
    uip login status 2>&1 | head -12
    d=$(mktemp -d); cd "$d"; npm init -y >/dev/null 2>&1
    npm install @uipath/flow-sdk 2>&1 | tail -2
    echo "SDK_VERSION=$(node -e "console.log(require(\"@uipath/flow-sdk/package.json\").version)" 2>&1)"
    cat > Hello.flow.ts <<TS
import { flow, script, input, out, types } from "@uipath/flow-sdk";
export default flow("hello").name("Hello")
  .input({ name: types.string }).output({ greeting: types.string })
  .step("greet", script({ code: "return 1;" }))
  .return({ greeting: out("greet") }).build();
TS
    uip maestro flow check Hello.flow.ts --source >/dev/null 2>&1; echo "RC_CHECK_SOURCE=$?"
    uip maestro flow compile Hello -o Hello.flow >/dev/null 2>&1; echo "RC_COMPILE=$?"
    [ -s Hello.flow ] && echo "EMITTED=yes" || echo "EMITTED=no"
    uip maestro flow check Hello.flow --compiled >/dev/null 2>&1; echo "RC_CHECK_COMPILED=$?"
    uip solution init HelloSol >/dev/null 2>&1
    ( cd HelloSol && uip maestro flow init Hello >/dev/null 2>&1 )
    [ -f HelloSol/Hello/project.uiproj ] && echo "SCAFFOLD=yes" || echo "SCAFFOLD=no"
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
chk "flow check --source exits 0"               '^RC_CHECK_SOURCE=0$'
chk "flow compile exits 0"                      '^RC_COMPILE=0$'
chk "compile emitted an artifact"               '^EMITTED=yes$'
chk "flow check --compiled exits 0"             '^RC_CHECK_COMPILED=0$'
chk "product scaffold emits project.uiproj"     '^SCAFFOLD=yes$'
echo "  $(grep -m1 '^SDK_VERSION=' "$LOG")  $(grep -m1 '^uip ' "$LOG")"
if [ "$fail" -ne 0 ]; then echo "GATE=FAIL"; echo "--- container output ---"; cat "$LOG"; exit 1; fi
echo "GATE=PASS"
