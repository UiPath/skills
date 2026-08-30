# `/check-is-scorecard` — Integration Service Scorecard Accuracy Checker

*Design · 2026-07-13 · Owner: Baishali Ghosh*

## Purpose

A reusable slash command that audits the accuracy of the published Integration Service (IS) Product Capability Enumeration — Confluence page `90898825832`, the source feeding the org Coding-Agents Scorecard's Integration Service row — by reconciling it against live repo state on fresh `main`.

Motivation: the IS enumeration was twice published with wrong numbers (diagnose 17% instead of 46%) because the analysis ran against a checkout 237 commits behind `origin/main`. This command catches that class of drift automatically.

## Form factor

`.claude/commands/check-is-scorecard.md` in `UiPath/skills`, sibling to `test-coverage`, `lint-task`, `generate-confluence-scorecard`. Invoked `/check-is-scorecard` from the repo root. Read-only by default; mutation only on explicit user confirmation.

## Parameters (declared at top of the command, IS defaults; clone by swapping)

| Param | IS default |
|---|---|
| `CONFLUENCE_PAGE_ID` | `90898825832` |
| `TAGS` | `integration-service`, `ipe` |
| `PLAYBOOK_DIR` | `skills/uipath-troubleshoot/references/products/integration-service/playbooks/` |
| `REPO_DOC` | `tests/reports/integration-service-capability-enumeration.md` |
| `COVERAGE_KEY` | `uipath-integration-service` (in `tests/reports/coverage.json`) |
| `SCORECARD_ROW` | `Integration Service (uip is)` |

## Sources

- **Source of truth:** Confluence page (`getConfluencePage`, contentFormat html), tables parsed for cited `task_id`s, playbook names, and the coverage tally (Build/Operate/Diagnose %, covered/total counts).
- **Repo state (fresh `main`):** IS eval `task.yaml`s selected by `TAGS` across host skills; playbook files under `PLAYBOOK_DIR`; `tests/reports/coverage.json` (`skills.<COVERAGE_KEY>`) if present.

## Staleness guard (runs FIRST, before any check)

Run `git fetch origin main` then compare `HEAD` to `origin/main`. If behind, **hard-fail immediately** with a loud warning and instruct `git pull --ff-only` before re-running. This is the primary bug this command exists to prevent — do not proceed to the four checks against a stale tree.

## The four checks

### Check 1 — Doc ↔ repo evals
- Every `task_id` cited in the Confluence doc exists on `main` with the claimed `mode:*` tag. Cite each stale/mismatched id.
- Every repo eval carrying a `TAGS` alias is represented in the doc. Cite each un-listed eval (dir/task_id).
- FAIL if any stale citation or any un-listed eval.

### Check 2 — Doc ↔ playbooks
- Every file in `PLAYBOOK_DIR` appears in the doc (a covered row OR a gap row). Cite missing ones.
- No playbook cited in the doc that does not exist on disk (phantom). Cite phantoms.
- FAIL on any missing or phantom.

### Check 3 — Doc ↔ scorecard numbers
- The doc's Build/Operate/Diagnose % reconcile with `coverage.json` `mode_coverage` (when the `COVERAGE_KEY` entry exists). Tolerance: exact for counts, ±0 for percentages derived from the same counts.
- If a scorecard page id is passed (`--scorecard <id>`), also compare the doc's per-mode % against the published scorecard's IS row cells.
- If `coverage.json` lacks the `COVERAGE_KEY` entry, WARN (not FAIL): "IS not yet registered cross-cutting; scorecard uses platform-aggregate floor" — points at the known open task.

### Check 4 — Internal consistency
- The doc's summary tally (e.g. "Diagnose 12/26") equals the actual covered vs uncovered row counts in the DM feature tables. Same for Build/Operate.
- Total = sum of per-mode. FAIL on any arithmetic mismatch; cite the table and the two disagreeing numbers.

## Output

Per-check PASS/FAIL table with specific mismatches (task_id / playbook / file:line / cell). Example:

```
CHECK 0 staleness      PASS (HEAD == origin/main)
CHECK 1 doc↔evals      FAIL  2 stale ids: skill-troubleshoot-foo, -bar
CHECK 2 doc↔playbooks  PASS  26/26 represented
CHECK 3 doc↔scorecard  WARN  coverage.json has no uipath-integration-service entry
CHECK 4 internal       FAIL  Diagnose tally 12/26 but 11 covered rows counted
```

On any FAIL/WARN, offer to fix (single AskUserQuestion): **(a)** patch the repo markdown, **(b)** republish the Confluence page, **(c)** do nothing. Never mutate without explicit choice. Fixing is a separate, confirmed phase — the audit itself is read-only.

## Non-goals

- Does not run evals or compute coverage from scratch (that's `/test-coverage`).
- Does not generate the scorecard (that's `/generate-confluence-scorecard`).
- Does not auto-commit or auto-push.

## Reusability

All IS specifics are the six parameters above. Cloning for ECS/context-grounding = a new command file with those six values swapped (page id, tags, playbook dir, repo doc, coverage key, scorecard row). The four-check logic is capability-agnostic.
