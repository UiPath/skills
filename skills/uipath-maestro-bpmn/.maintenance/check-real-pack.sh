#!/bin/bash
# Package validation fixtures through the installed uip CLI.
# Usage: bash .maintenance/check-real-pack.sh
#
# Runs local `uip maestro bpmn pack` for every validation fixture. Also runs
# `uip solution pack` for fixtures that are expected to be full solution-pack
# contracts. Solution pack reads the current tenant context, so that leg is
# skipped when the CLI is not logged in.

set -u

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT" || exit 1

if ! command -v uip >/dev/null 2>&1; then
  echo "uip not found on PATH; skipping real pack checks"
  echo "real_pack_fixtures=0 solution_pack_fixtures=0 errors=0"
  exit 0
fi

TMPDIR="$(mktemp -d)"
trap 'rm -rf "$TMPDIR"' EXIT

errors=0
bpmn_count=0
solution_count=0

run_json_command() {
  local label="$1"
  shift
  local log="$TMPDIR/${label//[^A-Za-z0-9_.-]/_}.log"
  if "$@" >"$log" 2>&1; then
    return 0
  fi
  echo "ERROR: $label failed"
  tail -80 "$log"
  return 1
}

for project in fixtures/validation/*; do
  [ -d "$project" ] || continue
  name="$(basename "$project")"
  bpmn_count=$((bpmn_count + 1))
  mkdir -p "$TMPDIR/bpmn-pack/$name"
  if ! run_json_command "bpmn-pack-$name" \
    uip maestro bpmn pack "$project" "$TMPDIR/bpmn-pack/$name" --output json; then
    errors=1
  fi
done

if uip login status --output json >"$TMPDIR/login-status.json" 2>&1 \
  && grep -q '"Status": "Logged in"' "$TMPDIR/login-status.json"; then
  for name in agent-invocation; do
    project="fixtures/validation/$name"
    solution_dir="$TMPDIR/solution-$name"
    solution_file="$solution_dir/solution-$name.uipx"
    solution_count=$((solution_count + 1))

    if ! run_json_command "solution-new-$name" \
      uip solution new "$solution_dir" --output json; then
      errors=1
      continue
    fi
    if ! run_json_command "solution-import-$name" \
      uip solution project import --source "$project" --solutionFile "$solution_file" --output json; then
      errors=1
      continue
    fi
    if ! run_json_command "solution-pack-$name" \
      uip solution pack "$solution_dir" "$TMPDIR/solution-pack/$name" --output json; then
      errors=1
    fi
  done
else
  echo "uip is not logged in; skipping solution pack fixtures"
fi

echo "real_pack_fixtures=$bpmn_count solution_pack_fixtures=$solution_count errors=$errors"
exit "$errors"
