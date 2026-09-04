#!/usr/bin/env bash
#
# Apply the required-status-check set from docs/REQUIRED-CHECKS.md to the `main`
# ruleset. The doc's "Current target set" table is the source of truth; this
# script parses the first column so the two can never disagree.
#
# Adding a context whose job has never reported blocks EVERY open PR. Verify the
# check appears on a fresh PR head before applying — see docs/REQUIRED-CHECKS.md
# § Applying a change.
#
# Usage:
#   scripts/apply-required-checks.sh --dry-run              # print the payload
#   scripts/apply-required-checks.sh                        # apply to ~DEFAULT_BRANCH
#   scripts/apply-required-checks.sh --with-release-branches # also gate refs/heads/release/*
#   scripts/apply-required-checks.sh --list                 # show what is required today

set -euo pipefail

REPO="${REPO:-UiPath/skills}"
RULESET_ID="${RULESET_ID:-14795269}"
# GitHub Actions. Pins each context to the Actions app so a third-party check
# cannot satisfy a required context by publishing the same name.
ACTIONS_APP_ID=15368

DOC="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)/docs/REQUIRED-CHECKS.md"

DRY_RUN=0
WITH_RELEASE=0
LIST_ONLY=0

for arg in "$@"; do
  case "$arg" in
    --dry-run)                DRY_RUN=1 ;;
    --with-release-branches)  WITH_RELEASE=1 ;;
    --list)                   LIST_ONLY=1 ;;
    -h|--help)                sed -n '3,16p' "${BASH_SOURCE[0]}"; exit 0 ;;
    *) echo "Unknown argument: $arg" >&2; exit 2 ;;
  esac
done

for bin in gh jq; do
  command -v "$bin" >/dev/null || { echo "Required tool not found: $bin" >&2; exit 1; }
done

if [ "$LIST_ONLY" -eq 1 ]; then
  gh api "repos/$REPO/rulesets/$RULESET_ID" \
    --jq '[.rules[]|select(.type=="required_status_checks").parameters.required_status_checks[].context]|sort|.[]'
  exit 0
fi

[ -f "$DOC" ] || { echo "Cannot find $DOC" >&2; exit 1; }

# Parse the "Current target set" table: rows between that heading and the next
# heading, first pipe-delimited column, stripped of backticks. The header and
# separator rows have no backticks, so they drop out on their own.
CONTEXTS=$(
  awk '
    /^## Current target set/     { intable = 1; next }
    intable && /^## /            { exit }
    intable && /^\| *`/ {
      line = $0
      sub(/^\| *`/, "", line)
      sub(/` *\|.*/, "", line)
      print line
    }
  ' "$DOC"
)

if [ -z "$CONTEXTS" ]; then
  echo "Parsed zero contexts from $DOC — has the table format changed?" >&2
  exit 1
fi

COUNT=$(printf '%s\n' "$CONTEXTS" | wc -l | tr -d ' ')

DUPES=$(printf '%s\n' "$CONTEXTS" | sort | uniq -d)
if [ -n "$DUPES" ]; then
  echo "Duplicate contexts in the table:" >&2
  printf '  %s\n' "$DUPES" >&2
  exit 1
fi

if [ "$WITH_RELEASE" -eq 1 ]; then
  REF_INCLUDE='["~DEFAULT_BRANCH", "refs/heads/release/*"]'
else
  REF_INCLUDE='["~DEFAULT_BRANCH"]'
fi

PAYLOAD=$(
  printf '%s\n' "$CONTEXTS" | jq -R . | jq -s \
    --argjson app "$ACTIONS_APP_ID" \
    --argjson refs "$REF_INCLUDE" \
    '{
      conditions: { ref_name: { include: $refs, exclude: [] } },
      rules: [
        { type: "deletion" },
        { type: "non_fast_forward" },
        { type: "pull_request", parameters: {
            required_approving_review_count: 1,
            require_code_owner_review: true,
            require_last_push_approval: false,
            dismiss_stale_reviews_on_push: false,
            required_review_thread_resolution: false,
            require_extra_approval_for_unattributed_changes: true,
            allowed_merge_methods: ["merge", "squash", "rebase"] } },
        { type: "required_status_checks", parameters: {
            do_not_enforce_on_create: false,
            # Off on purpose: forcing a re-run on base drift would serialize the
            # merge queue behind `Run skill smoke tests` (p95 22 min).
            strict_required_status_checks_policy: false,
            required_status_checks: [ .[] | { context: ., integration_id: $app } ] } }
      ]
    }'
)

echo "$COUNT required context(s), ref scope: $REF_INCLUDE"

if [ "$DRY_RUN" -eq 1 ]; then
  echo "$PAYLOAD"
  exit 0
fi

# Warn about contexts that have never been reported on the default branch's most
# recent PR heads — the failure mode that blocks every open PR.
echo "Checking that each context has reported recently..."
RECENT_SHAS=$(gh api "repos/$REPO/pulls?state=open&per_page=10" --jq '.[].head.sha' || true)
if [ -n "$RECENT_SHAS" ]; then
  SEEN=$(
    while IFS= read -r sha; do
      gh api "repos/$REPO/commits/$sha/check-runs?per_page=100&filter=latest" \
        --jq '.check_runs[].name' 2>/dev/null || true
    done <<< "$RECENT_SHAS" | sort -u
  )
  MISSING=$(comm -23 <(printf '%s\n' "$CONTEXTS" | sort -u) <(printf '%s\n' "$SEEN"))
  if [ -n "$MISSING" ]; then
    echo "WARNING: not reported on any of the 10 most recent open PR heads:" >&2
    printf '  %s\n' "$MISSING" >&2
    echo "Requiring a context that never reports blocks every PR. Continue? [y/N]" >&2
    read -r reply
    [ "$reply" = "y" ] || { echo "Aborted."; exit 1; }
  fi
fi

printf '%s' "$PAYLOAD" | gh api -X PUT "repos/$REPO/rulesets/$RULESET_ID" --input -
echo "Applied. Current set:"
gh api "repos/$REPO/rulesets/$RULESET_ID" \
  --jq '[.rules[]|select(.type=="required_status_checks").parameters.required_status_checks[].context]|sort|.[]'
