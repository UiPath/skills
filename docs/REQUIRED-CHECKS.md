# Required Status Checks

Which PR checks gate a merge, why, and how to change the set.

Enforcement lives in the **`main` ruleset** (id `14795269`), not in branch protection — `/branches/main/protection` returns 404 on purpose. Read the current set with:

```bash
gh api repos/UiPath/skills/rulesets/14795269 \
  --jq '[.rules[]|select(.type=="required_status_checks").parameters.required_status_checks[].context]'
```

## Rule 1 — a required check must run on every PR

A required context is a literal string GitHub waits for. If the check never reports, the PR stays pending and **merge blocks forever**. Two things stop a check from reporting:

| Cause | Effect | Fix |
|---|---|---|
| `on.pull_request.paths:` excludes the PR | Workflow never runs, no check reported | Drop the filter; short-circuit inside the job instead |
| Job name is an expression (`${{ matrix.skill }}`) | Name changes per PR, so the fixed context never matches | Add a fixed-name aggregator job and require that |

A job that runs and is **skipped** by an `if:` condition reports `skipped`, which GitHub counts as a pass. That is the supported way to keep a required check cheap — not a `paths:` filter.

Every workflow producing a required check therefore carries a comment on its `on:` block explaining the missing `paths:` filter. Keep it when editing.

> A `paths:` list is also a bad trigger on its own terms. `validate-skills-sh.yml`'s old filter named `skills/*/SKILL.md` yet stayed silent on #2252 — the PR that introduced the very drift the guard exists to catch.

## Rule 2 — no two jobs share a check name

A context matching two jobs is ambiguous about which run satisfied it. Two collisions were resolved in this repo; keep them distinct:

- `Detect changed skills` (`smoke-skills.yml`) vs `Detect changed skills (CLI verb gate)` (`verb-gate.yml`)
- `Validate version sync` (`validate-version-sync.yml`, `pull_request`) vs `Validate version sync (publish guard)` (`publish.yml`, `push`)

## Rule 3 — a required job must not be skippable by its own `needs:` failing

`Run skill smoke tests` and `Run RPA skill smoke tests (Windows)` are gated as
`needs: detect` + `if: needs.detect.outputs.skip != 'true'`. When `detect`
**fails**, its outputs are empty, the gated job is *skipped* — and GitHub counts
a skipped job as a pass. The repo's most expensive gate then reports green
having run nothing.

So a required job needs one of:

- every job in its `needs:` also required (what `detect` is for in the two smoke
  workflows), or
- `if: always()` plus an explicit check of each `needs.<job>.result` (what the
  two `gate-summary` aggregators do).

`test_required_job_needs_are_covered` in
`tests/scripts/test_required_checks_contract.py` enforces this.

> This is the one place the 2026-09-03 audit was wrong. It recommended dropping
> `Detect changed RPA skills` as "a detect job, not a gate … it only guards its
> own downstream job." It guards that job's *skip* path, which is exactly the
> path that reports green.

## Rule 4 — never require nondeterministic or advisory output

Do not require: LLM output (`Claude Code Review`, `Lint changed task YAMLs`, `copilot-pull-request-reviewer`), `workflow_dispatch`-only harnesses (`Run coder-eval (Linux)` / `(Windows)`), anything carrying `continue-on-error`, report-only apps (`Socket Security: Project Report`), or soft holds (`WIP`).

## Current target set

Renaming a job here renames its check and **breaks the ruleset**. Update both in the same PR.

| Check | Workflow |
|---|---|
| `Run skill smoke tests` | `smoke-skills.yml` |
| `Detect changed skills` | `smoke-skills.yml` (guards the skip path above — Rule 3) |
| `Run RPA skill smoke tests (Windows)` | `smoke-rpa-skills.yml` |
| `Detect changed RPA skills` | `smoke-rpa-skills.yml` (guards the skip path above — Rule 3) |
| `No task pins sandbox.driver tempdir` | `task-driver-gate.yml` |
| `path-to-ga approval` | `path-to-ga-approval.yml` |
| `Validate version sync` | `validate-version-sync.yml` |
| `Validate skill descriptions` | `validate-skills.yml` |
| `Validate skill status manifest & README` | `validate-skill-status.yml` |
| `Validate skills.sh.json against skills/` | `validate-skills-sh.yml` |
| `Build and inspect every skill package` | `validate-skill-flavors.yml` |
| `maestro-flow checker unit tests` | `test-helpers.yml` |
| `maestro-case checker unit tests` | `test-helpers.yml` |
| `uipath-agents checker unit tests` | `test-helpers.yml` |
| `uipath-planner checker unit tests` | `test-helpers.yml` |
| `uipath-admin verify negative controls` | `test-helpers.yml` |
| `runtime-payload key-casing contract guard` | `test-helpers.yml` |
| `catalog build integrity guards` | `test-helpers.yml` |
| `skills.sh grouping checker unit tests` | `test-helpers.yml` |
| `telemetry hook contract guard` | `test-helpers.yml` |
| `required-check contract guard` | `test-helpers.yml` |
| `Skill activation gate` | `activation-gate.yml` (aggregator) |
| `CLI verb gate` | `verb-gate.yml` (aggregator) |

Deliberately **not** required: `Detect changed skills (CLI verb gate)` and `detect` in `activation-gate.yml`. Both are covered by their workflow's `always()` aggregator (Rule 3), so requiring them adds nothing.

## Applying a change

Adding a context before the job has reported once blocks every open PR. Sequence:

1. Merge the workflow change.
2. Confirm the check reports on a PR opened **after** that merge:

   ```bash
   gh api "repos/UiPath/skills/commits/$(gh pr view <PR> --json headRefOid -q .headRefOid)/check-runs?filter=latest" \
     --jq '.check_runs[].name' | sort
   ```

3. Only then add the context to the ruleset. `scripts/apply-required-checks.sh` reads the table above and PUTs the full rule set:

   ```bash
   ./scripts/apply-required-checks.sh --dry-run   # print the payload
   ./scripts/apply-required-checks.sh             # apply
   ```

## Open items

- **`release/*` has no required checks.** The ruleset condition is `["~DEFAULT_BRANCH"]`, so ~92 release-branch PRs per quarter (mostly cherry-picks — where a stale conflict resolution most easily breaks a checker) merge on review alone. Fix by extending the condition to `["~DEFAULT_BRANCH", "refs/heads/release/*"]`; `apply-required-checks.sh --with-release-branches` emits that payload.
- **`strict_required_status_checks_policy` is `false`.** Branches may merge green against a stale base. Leave it off while `Run skill smoke tests` (p95 22 min) is required — forcing re-runs on base drift would serialize the merge queue.
- **`Validate task schema (advisory)` is not requirable yet.** It is `continue-on-error` by design and validates the whole task tree, so pre-existing drift shows red on unrelated PRs. Clean the tree, then drop `continue-on-error` and the `(advisory)` suffix.
- **Three rulesets overlap.** `Merge rule` (`14273765`) and `Require PR` (`13681075`) duplicate the `main` ruleset's `pull_request` rule. `Merge rule` returns an empty ref filter from the API — confirm its scope in the Rules UI before folding it in.
