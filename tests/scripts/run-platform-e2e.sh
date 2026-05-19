#!/usr/bin/env bash
# Run the full uipath-platform E2E suite with shared suite-level seed.
#
# Setup runs once at start; teardown runs ALWAYS at exit (success, failure,
# or Ctrl-C) via `trap EXIT`. Process-dependent tests reuse the shared deploy
# via TRACES_SMOKE_PROCESS_KEY env var instead of each doing its own.
#
# Usage:
#   bash tests/scripts/run-platform-e2e.sh                  # all platform e2e
#   bash tests/scripts/run-platform-e2e.sh task1.yaml task2.yaml   # subset

set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
SHARED="$REPO_ROOT/tests/tasks/uipath-platform/_shared"

cleanup() {
  echo ">>> Suite teardown..."
  python3 "$SHARED/suite_teardown.py" || true
}
trap cleanup EXIT INT TERM

echo ">>> Suite setup..."
eval "$(python3 "$SHARED/suite_setup.py")"
echo ">>> TRACES_SMOKE_PROCESS_KEY=${TRACES_SMOKE_PROCESS_KEY:-<not set>}"
echo ">>> E2E_SUITE_DEPLOY=${E2E_SUITE_DEPLOY:-<not set>}"

if [[ $# -eq 0 ]]; then
  TASKS=(
    "$REPO_ROOT"/tests/tasks/uipath-platform/orchestrator/*.yaml
    "$REPO_ROOT"/tests/tasks/uipath-platform/resources/*.yaml
    "$REPO_ROOT"/tests/tasks/uipath-platform/solution/*.yaml
  )
else
  TASKS=("$@")
fi

echo ">>> Running coder-eval with ${#TASKS[@]} task file(s)..."
cd "$REPO_ROOT/tests"
SKILLS_REPO_PATH="$REPO_ROOT" .venv/bin/coder-eval run \
  "${TASKS[@]}" \
  -e experiments/e2e.yaml
