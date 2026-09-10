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
| A narrowed PR trigger excludes the PR — `paths:`, `paths-ignore:`, `branches:`, `branches-ignore:`, or a `types:` list missing `synchronize` | Workflow never runs, no check reported | Drop the filter; short-circuit inside the job instead |
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
- `if: ${{ !cancelled() }}` plus an explicit check of each `needs.<job>.result`
  (what the two `gate-summary` aggregators do).

`test_required_job_needs_are_covered` in
`tests/scripts/test_required_checks_contract.py` enforces this — including that
the rollup job actually reads each `needs.<job>.result`, since a job that runs
regardless and ignores its needs reports green whatever they did.

### Rule 3a — two runs must never race on one SHA

A cancelled run still reports its jobs, and `cancelled` is **not** a pass. So a
required context can go red purely because its run was superseded.

`activation-gate.yml` triggers on `ready_for_review` and grouped its concurrency
by `head_ref` with `cancel-in-progress: true`. Taking a PR out of draft
therefore started a second run that cancelled the first **on the same head
SHA**. GitHub keeps the latest check run per context name, so merge turned on
which of the two recorded its result last. PR #3100 hit this: commit
`1056e6c56` carried a red `Skill activation gate` beside a green one (runs
`34055252280` and `34055306035`, ~70s apart).

The fix is in the concurrency block, not the job — and it is an **allow-list**:

```yaml
cancel-in-progress: ${{ github.event.action == 'synchronize' }}
```

`synchronize` is the only `pull_request` event that arrives with a new head SHA,
so it is the only one where cancelling is free: the superseded run's red lands
on a commit nobody is merging. Every other event can fire on a commit a run is
already in flight for:

| Event | Same-SHA path |
|---|---|
| `ready_for_review` | Taking a PR out of draft — the measured #3100 case |
| `reopened` | Closing a PR does not cancel its runs; close and reopen during one and the new run kills the old on the unchanged SHA |
| `opened` | A `workflow_dispatch` run already in flight for that ref |

An earlier version of this rule deny-listed `ready_for_review` alone and claimed
it was the only same-SHA event. It is not, and a deny-list also has to be
re-audited every time GitHub adds an activity type. The allow-list needs no
maintenance and costs at most one extra run per draft flip or reopen — cheap,
since the gated jobs skip on drafts.

All six required workflows carrying `cancel-in-progress` use this expression:
`activation-gate.yml`, `verb-gate.yml`, `smoke-skills.yml`,
`smoke-rpa-skills.yml`, `task-driver-gate.yml`, `validate-version-sync.yml`.
`test_concurrency_only_cancels_on_a_new_head_sha` enforces it, so a revert to
`cancel-in-progress: true` fails the contract guard rather than surfacing as an
intermittent red months later.

**If a superseded red does land**, it is not a ruleset bug and needs no ruleset
edit: re-run that run (`gh run rerun <id>`) and its fresh result replaces the
`cancelled` one, since GitHub keeps only the latest check run per context name.

### Why `!cancelled()` and not `always()`

Both aggregators use `if: ${{ !cancelled() }}`. The `${{ }}` wrapper is not
optional — a bare `!` starts a YAML tag.

Be clear about what this does **not** do. It does not make a cancelled run
pass. A job skipped by `if:` during run cancellation is reported `cancelled`,
not `skipped` — measured by dispatching `activation-gate.yml` and cancelling it
mid-flight (run `34067126301`: `cancelled  Skill activation gate`). Rule 3a
above is what keeps such a run off a SHA that also has a passing one.

What it buys, against `always()`:

- The aggregator resolves the instant the run is cancelled, instead of queueing
  for a runner and taking ~10s to decide. That shrinks the window in which it
  can record its check *after* the superseding run recorded its own.
- No `::error::activation gate could not determine which skills to gate` in the
  log of a run that was merely superseded.

It still runs, and still fails, when a needed job fails and when a leg hits
`timeout-minutes` — a timed-out job does not cancel the run, so the result
arrives as `cancelled` and the explicit check fires.

Because a cancelled run stays non-passing, cancelling a run is not a way to
skip these gates.

> This is the one place the 2026-09-03 audit was wrong. It recommended dropping
> `Detect changed RPA skills` as "a detect job, not a gate … it only guards its
> own downstream job." It guards that job's *skip* path, which is exactly the
> path that reports green.

## Rule 4 — never require nondeterministic or advisory output

Do not require: LLM output (`Claude Code Review`, `Lint changed task YAMLs`, `copilot-pull-request-reviewer`), `workflow_dispatch`-only harnesses (`Run coder-eval (Linux)` / `(Windows)`), anything carrying `continue-on-error`, report-only apps (`Socket Security: Project Report`), or soft holds (`WIP`).

## Current target set

Renaming a job here renames its check and **breaks the ruleset**. Update both in the same PR.

This table is machine-read. `scripts/parse-required-checks.py` is its only parser — `apply-required-checks.sh` shells out to it and the contract guard imports it, so what gets applied is by construction what got validated. Both cells of every row must be backticked; the parser errors on a row it cannot read rather than dropping it.

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
| `maestro-bpmn checker unit tests` | `test-helpers.yml` |
| `maestro-case checker unit tests` | `test-helpers.yml` |
| `uipath-agents checker unit tests` | `test-helpers.yml` |
| `uipath-planner checker unit tests` | `test-helpers.yml` |
| `uipath-admin verify negative controls` | `test-helpers.yml` |
| `runtime-payload key-casing contract guard` | `test-helpers.yml` |
| `maestro-bpmn contract guards` | `test-helpers.yml` |
| `catalog build integrity guards` | `test-helpers.yml` |
| `skills.sh grouping checker unit tests` | `test-helpers.yml` |
| `telemetry hook contract guard` | `test-helpers.yml` |
| `preview SDK workspace stager contract guard` | `test-helpers.yml` |
| `task/experiment gate unit tests` | `test-helpers.yml` |
| `required-check contract guard` | `test-helpers.yml` |
| `Skill activation gate` | `activation-gate.yml` (aggregator) |
| `CLI verb gate` | `verb-gate.yml` (aggregator) |

Deliberately **not** required: `Detect changed skills (CLI verb gate)` and `detect` in `activation-gate.yml`. Both are rolled up by their workflow's `!cancelled()` aggregator (Rule 3), so requiring them adds nothing.

## Applying a change

Adding a context before the job has reported once blocks every open PR. Sequence:

1. Merge the workflow change.
2. Confirm the check reports on a PR opened **after** that merge:

   ```bash
   gh api "repos/UiPath/skills/commits/$(gh pr view <PR> --json headRefOid -q .headRefOid)/check-runs?per_page=100&filter=latest" \
     --jq '.check_runs[].name' | sort
   ```

3. Only then add the context to the ruleset. `scripts/apply-required-checks.sh` reads the table above and PUTs the ruleset:

   ```bash
   ./scripts/apply-required-checks.sh --dry-run   # print the payload (stdout is pipeable JSON)
   ./scripts/apply-required-checks.sh             # apply
   ```

   The script builds the PUT body from the **live** ruleset and replaces only the required-status-check list. `name`, `enforcement`, `bypass_actors` and the `pull_request` parameters are carried through: GitHub's behaviour for fields omitted from `PUT /repos/{owner}/{repo}/rulesets/{id}` is undocumented, so sending a literal body risks clearing admin bypass on `main`, and hardcoding the review count silently reverts a change someone made in the Rules UI.

## Checking for drift

Every test in `tests/scripts/test_required_checks_contract.py` reads this doc and validates it against the workflows. **Nothing in CI compares it to the live ruleset**, and that direction fails in two ways no test can see:

- Delete a table row and its job in one PR: the contract guard stays green, the ruleset keeps waiting on a context that no longer reports, and **every PR blocks**.
- Edit the ruleset in the Rules UI: the ruleset is right and this doc is fiction.

Close the loop by hand, or from a scheduled job:

```bash
./scripts/apply-required-checks.sh --check   # exits non-zero on any doc/ruleset difference
```

Reading a ruleset needs admin on the repository, which the default `GITHUB_TOKEN` does not have — wiring `--check` to a `schedule:` trigger requires a PAT in a secret. Until that exists, run it after any change to the table above.

## Open items

- **`release/*` has no required checks.** The ruleset condition is `["~DEFAULT_BRANCH"]`, so ~92 release-branch PRs per quarter (mostly cherry-picks — where a stale conflict resolution most easily breaks a checker) merge on review alone. Fix by extending the condition to `["~DEFAULT_BRANCH", "refs/heads/release/*"]`; `apply-required-checks.sh --with-release-branches` emits that payload.
- **`strict_required_status_checks_policy` is `false`.** Branches may merge green against a stale base. Leave it off while `Run skill smoke tests` (p95 22 min) is required — forcing re-runs on base drift would serialize the merge queue.
- **`Validate task schema (advisory)` is not requirable yet.** It is `continue-on-error` by design and validates the whole task tree, so pre-existing drift shows red on unrelated PRs. Clean the tree, then drop `continue-on-error` and the `(advisory)` suffix.
- **`--check` is not scheduled.** See § Checking for drift — it needs an admin-scoped token to read the ruleset from CI.
- **`validate-skill-flavors.yml` is the only required workflow on GitHub-hosted runners.** Every other one is `uipath-ubuntu-latest`. Dropping its `paths:` filter (Rule 1) puts a ~52s node build on billed minutes for every PR, doc-only ones included. Accepted on purpose: the build is what ships to consumers and the 28-entry path list it replaced went stale each time an input was added. Move it to the self-hosted pool once that pool is verified to carry `rg` and `sha512sum`.
- **Three rulesets overlap.** `Merge rule` (`14273765`) and `Require PR` (`13681075`) duplicate the `main` ruleset's `pull_request` rule. `Merge rule` returns an empty ref filter from the API — confirm its scope in the Rules UI before folding it in.
