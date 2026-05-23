#!/bin/bash
# Run the public Maestro BPMN validator drift routine with disposable inputs.
# Usage: bash .maintenance/daily-validator-drift.sh [--input PATH] [--uipcli-checkout PATH] [--work-dir PATH] [--report PATH]
#
# The routine intentionally writes scratch data outside the git worktree by
# default. If callers override paths, repository-level .gitignore still keeps
# Rookery runtime/evidence directories out of product commits.

set -u

SKILL_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
REPO_ROOT="$(cd "$SKILL_ROOT/../.." && pwd)"
INPUT_PATH=""
UIPCLI_CHECKOUT="${UIPCLI_CHECKOUT:-}"
WORK_DIR=""
REPORT_PATH=""

usage() {
  sed -n '2,5p' "$0"
}

is_under_repo_runtime_dir() {
  case "$1" in
    "$REPO_ROOT/.rookery"|"$REPO_ROOT/.rookery"/*) return 0 ;;
    "$REPO_ROOT/.rookery-tmp"|"$REPO_ROOT/.rookery-tmp"/*) return 0 ;;
    "$REPO_ROOT/.codex"|"$REPO_ROOT/.codex"/*) return 0 ;;
    *) return 1 ;;
  esac
}

json_escape() {
  python3 -c 'import json,sys; print(json.dumps(sys.stdin.read()))'
}

write_report() {
  local product_status="$1"
  local product_log="$2"
  local checks_status="$3"
  local checks_reason="$4"
  local input_status="$5"

  {
    printf '{\n'
    printf '  "routine": "maestro-bpmn-validator-drift",\n'
    printf '  "input": {"status": %s},\n' "$(printf '%s' "$input_status" | json_escape)"
    printf '  "product_validation": {"status": %s, "log": %s},\n' \
      "$(printf '%s' "$product_status" | json_escape)" \
      "$(printf '%s' "$product_log" | json_escape)"
    printf '  "workspace_checks": {"status": %s, "reason": %s},\n' \
      "$(printf '%s' "$checks_status" | json_escape)" \
      "$(printf '%s' "$checks_reason" | json_escape)"
    printf '  "commit_hygiene": {"scratch_dir": %s, "report_path": %s}\n' \
      "$(printf '%s' "$WORK_DIR" | json_escape)" \
      "$(printf '%s' "$REPORT_PATH" | json_escape)"
    printf '}\n'
  } >"$REPORT_PATH"
}

while [ "$#" -gt 0 ]; do
  case "$1" in
    --input)
      [ "$#" -ge 2 ] || { usage >&2; exit 2; }
      INPUT_PATH="$2"
      shift 2
      ;;
    --uipcli-checkout)
      [ "$#" -ge 2 ] || { usage >&2; exit 2; }
      UIPCLI_CHECKOUT="$2"
      shift 2
      ;;
    --work-dir)
      [ "$#" -ge 2 ] || { usage >&2; exit 2; }
      WORK_DIR="$2"
      shift 2
      ;;
    --report)
      [ "$#" -ge 2 ] || { usage >&2; exit 2; }
      REPORT_PATH="$2"
      shift 2
      ;;
    -h|--help)
      usage
      exit 0
      ;;
    *)
      echo "unknown argument: $1" >&2
      usage >&2
      exit 2
      ;;
  esac
done

if [ -z "$WORK_DIR" ]; then
  WORK_DIR="$(mktemp -d "${TMPDIR:-/tmp}/maestro-bpmn-validator-drift.XXXXXX")"
else
  mkdir -p "$WORK_DIR" || exit 1
  WORK_DIR="$(cd "$WORK_DIR" && pwd)"
fi

if [ -z "$REPORT_PATH" ]; then
  REPORT_PATH="$WORK_DIR/report.json"
else
  mkdir -p "$(dirname "$REPORT_PATH")" || exit 1
  REPORT_DIR="$(cd "$(dirname "$REPORT_PATH")" && pwd)"
  REPORT_PATH="$REPORT_DIR/$(basename "$REPORT_PATH")"
fi

case "$WORK_DIR" in
  "$REPO_ROOT"|"$REPO_ROOT"/*)
    if ! is_under_repo_runtime_dir "$WORK_DIR"; then
      echo "refusing to write scratch data inside product worktree: $WORK_DIR" >&2
      exit 2
    fi
    ;;
esac

INPUT_STATUS="synthetic fixtures"
if [ -n "$INPUT_PATH" ]; then
  if [ ! -e "$INPUT_PATH" ]; then
    echo "input not found: $INPUT_PATH" >&2
    exit 2
  fi
  INPUT_STATUS="copied disposable input"
  mkdir -p "$WORK_DIR/input" || exit 1
  case "$INPUT_PATH" in
    *.zip)
      if ! command -v unzip >/dev/null 2>&1; then
        echo "unzip not found for zip input: $INPUT_PATH" >&2
        exit 2
      fi
      unzip -q "$INPUT_PATH" -d "$WORK_DIR/input" || exit 1
      ;;
    *)
      cp -R "$INPUT_PATH" "$WORK_DIR/input/" || exit 1
      ;;
  esac
fi

PRODUCT_LOG="$WORK_DIR/product-validation.log"
if (cd "$SKILL_ROOT" && python3 .maintenance/check-validation-fixtures.py >"$PRODUCT_LOG" 2>&1); then
  PRODUCT_STATUS="passed"
else
  PRODUCT_STATUS="failed"
fi

CHECKS_STATUS="structural_skip"
CHECKS_REASON="no uipcli checkout supplied; run_workspace_checks should target the actual uipcli checkout, not this skills worktree"
if [ -n "$UIPCLI_CHECKOUT" ]; then
  if [ ! -d "$UIPCLI_CHECKOUT" ]; then
    CHECKS_REASON="uipcli checkout path does not exist: $UIPCLI_CHECKOUT"
  elif [ ! -f "$UIPCLI_CHECKOUT/package.json" ]; then
    CHECKS_REASON="uipcli checkout lacks package.json: $UIPCLI_CHECKOUT"
  elif ! grep -q '"scripts"' "$UIPCLI_CHECKOUT/package.json"; then
    CHECKS_REASON="uipcli checkout package.json has no scripts block: $UIPCLI_CHECKOUT"
  elif ! command -v bun >/dev/null 2>&1; then
    CHECKS_STATUS="transport_skip"
    CHECKS_REASON="bun is not available on PATH for uipcli workspace checks"
  else
    CHECKS_STATUS="target_ready"
    CHECKS_REASON="uipcli checkout has package scripts and bun is available; invoke Rookery run_workspace_checks against this checkout"
  fi
fi

write_report "$PRODUCT_STATUS" "$(tail -40 "$PRODUCT_LOG")" "$CHECKS_STATUS" "$CHECKS_REASON" "$INPUT_STATUS"

echo "product_validation=$PRODUCT_STATUS"
echo "workspace_checks=$CHECKS_STATUS"
echo "workspace_checks_reason=$CHECKS_REASON"
echo "report=$REPORT_PATH"

exit 0
