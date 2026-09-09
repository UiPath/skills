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
#   scripts/apply-required-checks.sh --check                # diff doc vs live; non-zero on drift

set -euo pipefail

REPO="${REPO:-UiPath/skills}"
RULESET_ID="${RULESET_ID:-14795269}"
# GitHub Actions. Pins each context to the Actions app so a third-party check
# cannot satisfy a required context by publishing the same name.
ACTIONS_APP_ID=15368

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
DOC="$REPO_ROOT/docs/REQUIRED-CHECKS.md"
PARSER="$REPO_ROOT/scripts/parse-required-checks.py"

DRY_RUN=0
WITH_RELEASE=0
LIST_ONLY=0
CHECK_ONLY=0

for arg in "$@"; do
  case "$arg" in
    --dry-run)                DRY_RUN=1 ;;
    --with-release-branches)  WITH_RELEASE=1 ;;
    --list)                   LIST_ONLY=1 ;;
    --check)                  CHECK_ONLY=1 ;;
    -h|--help)                sed -n '/^# Usage:/,/^$/p' "${BASH_SOURCE[0]}" | sed 's/^# \{0,1\}//'; exit 0 ;;
    *) echo "Unknown argument: $arg" >&2; exit 2 ;;
  esac
done

for bin in gh jq python3; do
  command -v "$bin" >/dev/null || { echo "Required tool not found: $bin" >&2; exit 1; }
done

# Fetch the live ruleset once. Every read below works off this, so a transient
# API failure aborts instead of being mistaken for "the ruleset is empty".
fetch_ruleset() {
  gh api "repos/$REPO/rulesets/$RULESET_ID" ||
    { echo "Failed to read ruleset $RULESET_ID from $REPO (auth? admin? network?)" >&2; exit 1; }
}

live_contexts() {
  jq -r '[.rules[]|select(.type=="required_status_checks").parameters.required_status_checks[].context]|sort|.[]'
}

if [ "$LIST_ONLY" -eq 1 ]; then
  fetch_ruleset | live_contexts
  exit 0
fi

[ -f "$DOC" ] || { echo "Cannot find $DOC" >&2; exit 1; }

# Parse via scripts/parse-required-checks.py — THE single parser for the table.
# tests/scripts/test_required_checks_contract.py imports the same module, so the
# set applied here is by construction the set the contract guard validated. This
# script used to carry its own awk parser, which accepted rows the guard's regex
# dropped: a context could be PUT to the ruleset having never been checked
# against the workflows, or applied as a mangled string GitHub waits for forever.
# The parser raises on a malformed row rather than silently skipping it, and
# rejects duplicates.
if ! CONTEXTS=$(python3 "$PARSER" --contexts); then
  echo "Failed to parse the target set from $DOC" >&2
  exit 1
fi

if [ -z "$CONTEXTS" ]; then
  echo "Parsed zero contexts from $DOC — has the table format changed?" >&2
  exit 1
fi

COUNT=$(printf '%s\n' "$CONTEXTS" | wc -l | tr -d ' ')

# Reading a ruleset needs admin on the repository. `--dry-run` is documented in
# CLAUDE.md as the pre-PR preview, so it must still work for a contributor who
# cannot read the live one — fall back to the skeleton below and say so. Every
# path that actually PUTs requires the real thing.
if CURRENT=$(gh api "repos/$REPO/rulesets/$RULESET_ID" 2>/dev/null); then
  :
elif [ "$DRY_RUN" -eq 1 ]; then
  echo "NOTE: cannot read ruleset $RULESET_ID (admin required). Previewing against" >&2
  echo "      a skeleton — the applied body is built from live state, so the" >&2
  echo "      enforcement, bypass_actors and pull_request fields below are absent" >&2
  echo "      here and preserved there." >&2
  CURRENT='{"name":"main","target":"branch","enforcement":"active","bypass_actors":[],
            "conditions":{"ref_name":{"include":["~DEFAULT_BRANCH"],"exclude":[]}},
            "rules":[{"type":"deletion"},{"type":"non_fast_forward"}]}'
else
  echo "Failed to read ruleset $RULESET_ID from $REPO (auth? admin? network?)" >&2
  exit 1
fi

if [ "$CHECK_ONLY" -eq 1 ]; then
  # Drift in the doc -> ruleset direction, which no test can see: the contract
  # guard only ever compares the table to the workflows. Delete a row and its
  # job together and the guard stays green while the ruleset keeps waiting on a
  # context that no longer reports — blocking every PR. Edit the ruleset in the
  # UI and the doc silently becomes fiction.
  # LC_ALL=C on both sides: jq's `sort` is codepoint order, and a locale-aware
  # `sort` would report a pure ordering difference as drift.
  LIVE=$(printf '%s' "$CURRENT" | live_contexts | LC_ALL=C sort -u)
  if DIFF=$(diff <(printf '%s\n' "$CONTEXTS" | LC_ALL=C sort -u) <(printf '%s\n' "$LIVE")); then
    echo "OK — $COUNT context(s), doc and ruleset $RULESET_ID agree."
    exit 0
  fi
  {
    echo "DRIFT between docs/REQUIRED-CHECKS.md and ruleset $RULESET_ID."
    echo "  '<' = in the doc, missing from the ruleset (documented but not enforced)"
    echo "  '>' = in the ruleset, missing from the doc (enforced, and nothing validates it"
    echo "        against the workflows — a rename here blocks every PR)"
    printf '%s\n' "$DIFF"
  } >&2
  exit 1
fi

CHECKS_JSON=$(printf '%s\n' "$CONTEXTS" | jq -R . | jq -s \
  --argjson app "$ACTIONS_APP_ID" '[ .[] | { context: ., integration_id: $app } ]')

if [ "$WITH_RELEASE" -eq 1 ]; then
  EXTRA_REFS='["refs/heads/release/*"]'
else
  EXTRA_REFS='[]'
fi

# Build the PUT body from the LIVE ruleset rather than from a literal. A literal
# body sends only `conditions` and `rules`, and GitHub's behaviour for fields
# omitted from PUT /repos/{owner}/{repo}/rulesets/{id} is undocumented and has
# changed — if omitted means cleared, the first run drops `enforcement` and
# every `bypass_actors` entry (admin bypass included) from `main`. Same argument
# for the `pull_request` parameters: hardcoding them silently reverts a
# review-count change someone made in the UI. Only the required-status-check
# list is authored here; everything else is carried through untouched.
PAYLOAD=$(
  printf '%s' "$CURRENT" | jq \
    --argjson checks "$CHECKS_JSON" \
    --argjson extra "$EXTRA_REFS" \
    '{ name, target, enforcement, bypass_actors, conditions, rules }
     | .conditions.ref_name.include = ((.conditions.ref_name.include // []) + $extra | unique)
     | .rules = (
         [ .rules[] | select(.type != "required_status_checks") ]
         + [ ( ( .rules[] | select(.type == "required_status_checks") )
               // { type: "required_status_checks",
                    parameters: { do_not_enforce_on_create: false,
                                  # Off on purpose: forcing a re-run on base drift would
                                  # serialize the merge queue behind `Run skill smoke
                                  # tests` (p95 22 min).
                                  strict_required_status_checks_policy: false } } )
             | .parameters.required_status_checks = $checks ]
       )'
)

REF_SCOPE=$(printf '%s' "$PAYLOAD" | jq -c '.conditions.ref_name.include')

# stderr, so `--dry-run` stdout is a pipeable JSON document.
echo "$COUNT required context(s), ref scope: $REF_SCOPE" >&2

if [ "$DRY_RUN" -eq 1 ]; then
  echo "$PAYLOAD"
  exit 0
fi

# Warn about contexts that have never been reported on the default branch's most
# recent PR heads — the failure mode that blocks every open PR.
echo "Checking that each context has reported recently..." >&2
# Fail closed: an auth or network failure here is indistinguishable from "no
# open PRs", and treating it as the latter skips the one safety check standing
# between a typo and every PR blocking.
RECENT_SHAS=$(gh api "repos/$REPO/pulls?state=open&per_page=10" --jq '.[].head.sha') ||
  { echo "Could not list open PRs — refusing to apply without the reported-recently check." >&2; exit 1; }
if [ -n "$RECENT_SHAS" ]; then
  SEEN=$(
    while IFS= read -r sha; do
      gh api "repos/$REPO/commits/$sha/check-runs?per_page=100&filter=latest" \
        --jq '.check_runs[].name' ||
        { echo "Could not read check runs for $sha." >&2; exit 1; }
    done <<< "$RECENT_SHAS" | sort -u
  )
  MISSING=$(comm -23 <(printf '%s\n' "$CONTEXTS" | sort -u) <(printf '%s\n' "$SEEN"))
  if [ -n "$MISSING" ]; then
    echo "WARNING: not reported on any of the 10 most recent open PR heads:" >&2
    printf '  %s\n' "$MISSING" >&2
    echo "Requiring a context that never reports blocks every PR. Continue? [y/N]" >&2
    # `read` returns non-zero at EOF (piped stdin, </dev/null, a CI job), and
    # `set -e` would kill the script here before the explicit "Aborted." line.
    read -r reply || reply=n
    [ "$reply" = "y" ] || { echo "Aborted."; exit 1; }
  fi
else
  echo "No open PRs to check against — applying without the reported-recently check." >&2
fi

printf '%s' "$PAYLOAD" | gh api -X PUT "repos/$REPO/rulesets/$RULESET_ID" --input -
echo "Applied. Current set:"
fetch_ruleset | live_contexts
