#!/usr/bin/env bash
# run-live-e2e.sh — run compliance pack live e2e against the currently logged-in uip tenant.
# Usage: bash tests/run-live-e2e.sh
# Prereq: uip login must have been run first.

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
AUTH_FILE="$HOME/.uipath/.auth"

# ── 1. Check prerequisites ────────────────────────────────────────────────────

if ! command -v uip &>/dev/null; then
  echo "ERROR: uip CLI not found. Run: npm install -g @uipath/cli" >&2
  exit 1
fi

if [[ ! -f "$AUTH_FILE" ]]; then
  echo "ERROR: Not logged in — $AUTH_FILE not found. Run: uip login" >&2
  exit 1
fi

if [[ ! -f "$SCRIPT_DIR/.venv/Scripts/activate" ]]; then
  echo "ERROR: coder-eval venv not found. Run: cd tests && make install" >&2
  exit 1
fi

# ── 2. Read auth from ~/.uipath/.auth ────────────────────────────────────────

AUTH_TOKEN=$(grep '^UIPATH_ACCESS_TOKEN=' "$AUTH_FILE" | cut -d'=' -f2-)
ORG_ID=$(grep '^UIPATH_ORGANIZATION_ID=' "$AUTH_FILE" | cut -d'=' -f2-)
ORG_NAME=$(grep '^UIPATH_ORGANIZATION_NAME=' "$AUTH_FILE" | cut -d'=' -f2-)
TENANT_ID=$(grep '^UIPATH_TENANT_ID=' "$AUTH_FILE" | cut -d'=' -f2-)
TENANT_NAME=$(grep '^UIPATH_TENANT_NAME=' "$AUTH_FILE" | cut -d'=' -f2-)

if [[ -z "$AUTH_TOKEN" ]]; then
  echo "ERROR: No access token in $AUTH_FILE. Run: uip login" >&2
  exit 1
fi

echo "Running live e2e against: $ORG_NAME / $TENANT_NAME"
echo "────────────────────────────────────────────────"

# ── 3. Activate venv and run ─────────────────────────────────────────────────

cd "$SCRIPT_DIR"
source "$SCRIPT_DIR/.venv/Scripts/activate"

# Windows: create python3.cmd wrapper in the venv Scripts dir so post_run
# commands using `python3` resolve correctly in subprocesses launched by coder-eval.
if [[ "$OSTYPE" == "msys" || "$OSTYPE" == "cygwin" || "$OSTYPE" == "win32" ]]; then
  printf '@python %%*\r\n' > "$SCRIPT_DIR/.venv/Scripts/python3.cmd"
fi

PYTHONIOENCODING=utf-8 \
SKILLS_REPO_PATH="$(dirname "$SCRIPT_DIR")" \
UIPATH_CLI_ENABLE_ENV_AUTH=1 \
UIPATH_CLI_AUTH_TOKEN="$AUTH_TOKEN" \
UIPATH_CLI_ORGANIZATION_ID="$ORG_ID" \
UIPATH_CLI_ORGANIZATION_NAME="$ORG_NAME" \
UIPATH_CLI_TENANT_ID="$TENANT_ID" \
UIPATH_CLI_TENANT_NAME="$TENANT_NAME" \
  coder-eval run \
    tasks/uipath-governance/compliance-pack/full_apply_e2e_live.yaml \
    -e experiments/live-e2e-local.yaml \
    -v
