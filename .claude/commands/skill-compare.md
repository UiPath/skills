# Skill Comparison Experiment

Run an apples-to-apples A/B comparison between two branches of the skills repo and produce a decision-ready report. Automates the workflow described in [`tests/experiments/skill-comparison-playbook.md`](../../tests/experiments/skill-comparison-playbook.md).

**Input:** `$ARGUMENTS`
- `<branch_a> <branch_b>` — required, the two branches to compare. Must both exist locally or on a remote.
- `<skill_name>` — optional third argument. Restricts the task set to `tests/tasks/<skill_name>/`. Defaults to all tasks (warn the user: this can be slow and expensive).
- `<n_reps>` — optional fourth argument. Reps per variant. Defaults to `3`. Accept integers 1–5.

**Examples:**
- `/skill-compare main feat/my-change uipath-maestro-flow`
- `/skill-compare main feat/my-change uipath-maestro-flow 5`
- `/skill-compare main feat/my-change` (all skills, N=3)

**Output:**
- A new experiment YAML at `tests/experiments/compare-<branch_a_slug>-vs-<branch_b_slug>.yaml`
- Worktrees at `../skills-<branch_a_slug>` and `../skills-<branch_b_slug>` relative to the repo root
- Run results under `tests/runs/compare-<branch_a_slug>-vs-<branch_b_slug>-<timestamp>/`
- Comparison report at `tests/runs/compare-<branch_a_slug>-vs-<branch_b_slug>-<timestamp>/comparison-report.md`

Branch name slugs: replace `/` with `-` and strip any leading `origin/`. Example: `feat/my-change` → `feat-my-change`.

**Working directory.** Every phase runs from `tests/`. All git operations use `git -C ..` to target the repo root. Worktree paths like `../skills-<slug>` resolve alongside the repo, one level above `tests/`.

---

## Phase 1 — Parse & validate

1. Parse `$ARGUMENTS`: require at least two non-empty tokens. If fewer than 2, print usage and stop.
2. Normalize each branch name:
   - Strip leading `origin/` if present.
   - Reject branch names that start with `-` — they can be misread as git flags. Stop with a usage message.
   - Record the original (e.g. `feat/foo`) and the slug (e.g. `feat-foo`) separately.
3. Reject the call if `<branch_a> == <branch_b>` — comparing a branch to itself produces no signal.
4. Reject the call if `<n_reps>` is outside `1..5`. N=1 is allowed for a fast signal check but warn it's underpowered for decisions.
5. For each branch, verify it exists. Use `--` to terminate flag parsing so branch names can never be misread as options:
   ```bash
   git -C .. rev-parse --verify -- "<branch>" >/dev/null 2>&1
   ```
   If the local ref fails, retry with `origin/<branch>` and record that the branch is remote-only (will need a tracking branch during worktree setup). If still not found, stop and tell the user which branch is missing.
6. If `<skill_name>` is provided, verify `tasks/<skill_name>/` exists (relative to `tests/`). If not, list available skills under `tasks/*/` and stop.
7. For each branch, decide whether to create or reuse a worktree at `../skills-<slug>`:
   - If the path does not exist → create it in Phase 3.
   - If it exists, check `git -C .. worktree list --porcelain`. If it's a registered worktree already on the target branch, **reuse it** (skip Phase 3's `worktree add` for this branch and go straight to SHA capture).
   - If it exists but is not a worktree, or is a worktree on a different branch, **stop** and tell the user to remove it (`git worktree remove`) or point the command at different worktree paths. Do not overwrite.

## Phase 2 — Ask for the hypothesis

Before doing anything destructive, ask the user for a one-sentence hypothesis being tested. Use a plain free-form text prompt (not `AskUserQuestion` — that tool is for enumerated choices, and hypotheses are open-ended). Example prompt: *"What's the hypothesis for this comparison? One sentence. For example: 'Collapsing per-node planning+impl docs does not hurt success rate.'"*

Save the answer — it goes into the comparison report and the experiment YAML description.

## Phase 3 — Create worktrees

For each branch, skip if Phase 1 flagged it for reuse. Otherwise run, from `tests/`:

```bash
git -C .. worktree add ../skills-<slug> -- <branch>
```

If the branch is remote-only (from Phase 1), first create a tracking branch:

```bash
git -C .. worktree add -b <branch> ../skills-<slug> -- origin/<branch>
```

The `--` terminator prevents branch names starting with `-` from being parsed as flags.

Record each worktree's absolute path. Capture the commit SHA (short form):

```bash
git -C ../skills-<slug> rev-parse --short HEAD
```

Keep these SHAs in context — they're re-checked in Phase 6 and reported in Phase 8.

If any worktree add fails, stop and report. Do not attempt to clean up partial state — the user should inspect.

## Phase 4 — Generate the experiment YAML

Start from [`tests/experiments/skill-comparison-template.yaml`](../../tests/experiments/skill-comparison-template.yaml). Write the generated file to `tests/experiments/compare-<branch_a_slug>-vs-<branch_b_slug>.yaml`.

Fill in:
- `experiment_id`: `compare-<branch_a_slug>-vs-<branch_b_slug>`
- `description`: the hypothesis from Phase 2
- One variant per branch. Variant IDs must be the slugs.
- Absolute worktree paths in each variant's `plugins[].path`.
- A pinned-SHA comment on the line above each variant, e.g. `# pinned: feat/my-change @ a1b2c3d`.

Suffix rule for rep variants:
- **N=1** → one variant per branch, `variant_id` is the bare slug (e.g. `variant_id: main`). No `-rN` suffix.
- **N>1** → duplicate each variant N times with `-r1`, `-r2`, ... `-rN` suffixes on the `variant_id`, starting at `-r1`. All reps of a variant share the same path.

Example for N=3:

```yaml
  - variant_id: <slug>-r1
    # pinned: <branch> @ <sha>
    agent:
      plugins:
        - type: "local"
          path: "<abs-worktree-path>"
  - variant_id: <slug>-r2
    # pinned: <branch> @ <sha>
    agent:
      plugins:
        - type: "local"
          path: "<abs-worktree-path>"
  - variant_id: <slug>-r3
    # pinned: <branch> @ <sha>
    agent:
      plugins:
        - type: "local"
          path: "<abs-worktree-path>"
```

Do not include a `bare` variant. This command compares two skill configurations — add baselines manually if needed.

## Phase 5 — Resolve the task set and confirm

1. Resolve the task list. **Sort the output** so ordering is deterministic across runs (filesystem traversal order is not guaranteed, and an unsorted list can produce run-to-run permutation noise):
   - If `<skill_name>` was provided: `find tasks/<skill_name> -name '*.yaml' -type f | sort`
   - Otherwise: `find tasks -name '*.yaml' -type f | sort`
2. Estimate cost and time as a rough planning aid only — actuals depend on model pricing and task complexity. A task at the experiment defaults (`max_turns: 20`, `task_timeout: 600`) usually completes in a few minutes and spends a nontrivial amount in API tokens. Multiply the per-task estimate by `num_tasks × num_variants × n_reps` for the total.
3. Present a confirmation prompt via `AskUserQuestion` with these options:
   - **Run now** — proceeds to Phase 6.
   - **Show me the experiment YAML first** — opens the generated file for review, then re-prompts.
   - **Cancel** — stops. Tell the user how to clean up (Phase 9 instructions) even though nothing has run yet, because the worktrees and YAML still exist.
   - **Something else** — accept free-form input (e.g., "drop reps to 1", "limit to smoke tasks") and re-plan accordingly.

Do not proceed without explicit confirmation. The run can take hours and cost real money.

## Phase 6 — Run

Before running, **re-check each worktree's SHA** against the SHA captured in Phase 3. If either differs (the user pulled, committed, or checked out a different ref in the worktree between Phase 3 and now), stop and ask the user whether to (a) regenerate the YAML with the new SHAs, or (b) reset the worktree to the pinned commit. Never run with stale metadata.

```bash
git -C ../skills-<slug> rev-parse --short HEAD    # for each worktree — must match Phase 3
```

Pick a deterministic run directory so concurrent runs can't be confused with ours. Use a slug + timestamp:

```bash
RUN_DIR="runs/compare-<branch_a_slug>-vs-<branch_b_slug>-$(date +%Y%m%d-%H%M%S)"
SKILLS_REPO_PATH=$(cd .. && pwd) \
  .venv/bin/coder-eval run <resolved-task-files> \
  -e experiments/compare-<branch_a_slug>-vs-<branch_b_slug>.yaml \
  --run-dir "$RUN_DIR" \
  -j 1 -v
```

Record `tests/$RUN_DIR` as the run directory — everything downstream reads from there.

Keep `-j 1`. Parallel execution introduces timing noise (shared API rate limits, disk contention) that can distort small variant effects. If the user explicitly asks for parallelism, honor it but note the caveat in the report.

Stream output. If the run fails mid-way, capture the partial results and continue to Phase 7 with whatever data exists.

## Phase 7 — Analyze

1. Read `<RUN_DIR>/experiment.md` and each variant's `variant.json` (where `<RUN_DIR>` is the path recorded at the end of Phase 6). Build a results table:

   | variant | success rate | avg score | avg duration | total tokens |
   |---|---|---|---|---|
   | <branch_a> | ... | ... | ... | ... |
   | <branch_b> | ... | ... | ... | ... |

   If N>1, aggregate across `-r1`/`-r2`/`-rN`: use mean for score/duration/tokens, and `passed_runs / total_runs` for success rate per task.

2. Identify divergent tasks. Use the per-task `passed` boolean (from `success_criteria` in `task.json`) and the reliability score, in this order:
   - **Hard divergence** — one variant's `passed` is `true` and the other's is `false` for the same task. Always a divergence, regardless of scores.
   - **Soft divergence** — both variants have the same `passed` value but their reliability scores differ by more than `0.1` (chosen so that swings within one scoring tier — e.g., `0.533` → `0.562` on the same partial-pass task — don't register as divergences).
   - **Tie** — everything else.

   Do not key divergence on the `status` field (`SUCCESS` / `FAILURE` / `TIMEOUT` / `MAX_TURNS_EXHAUSTED`). A task can score 0.95 and still be `FAILURE`; a task can hit `MAX_TURNS_EXHAUSTED` and still partially pass.

3. For each divergent task, read the losing variant's `task.json` transcript and extract a one-line root cause. Look for:
   - **Timeout at `MAX_TURNS=0`** — agent never got a turn. Infrastructure issue, discard this divergence.
   - **Rabbit hole** — agent repeatedly retried a failing approach. Cite the specific command or error that looped.
   - **Missed workflow step** — agent skipped a critical rule (e.g., didn't run a required setup command). Cite the skipped step.
   - **Validation failure** — generated artifact was wrong. Cite what was wrong.

4. Count reliability signals:
   - **Head-to-head wins** per variant — count divergent-task wins only. A win requires the winner's `passed` to be `true` OR the winner's score to be higher by more than 0.1.
   - **Flip rate** (N>1 only) — for each task, determine the winning variant in each rep. A task is "flipped" if not all reps produced the same winner (ties across reps are not flips). Report `flip_rate = flipped_tasks / tasks_with_at_least_one_non_tie_rep`. Flip rate `> 0` is a high-variance signal.
   - **Token efficiency** — percent difference between variants' total tokens. Only material at `> 10%`.

## Phase 8 — Write the comparison report

Write `<RUN_DIR>/comparison-report.md` with this structure:

```markdown
# Skill Comparison: <branch_a> vs <branch_b>

**Hypothesis:** <from Phase 2>
**Run:** `<RUN_DIR basename>`
**Model:** <from experiment defaults>
**Tasks:** <count> (skill filter: <skill_name or "all">)
**N:** <n_reps> rep(s) per variant

## Variants
- `<branch_a>` @ `<sha_a>`
- `<branch_b>` @ `<sha_b>`

## Results
<results table from Phase 7 step 1>

## Head-to-head
- <branch_a> wins: <count>
- <branch_b> wins: <count>
- Ties: <count>

## Divergent tasks
<one bullet per divergent task with: task id, scores per variant, one-line root cause>

## Flip rate (N > 1 only)
<list any task where reps flipped winners, otherwise "none">

## Recommendation
<one of the three verdicts below, with a one-paragraph justification>

## Caveats
<any of these that apply, each as one bullet>
- N=<n> is low for decisions; flip rate X% on Y tasks.
- Both divergent tasks were timeouts; high variance.
- One variant hit MAX_TURNS=0 on <task> (agent never got a turn).
- Token gap <X>%; not material.
```

**Decision rule for the recommendation** — apply in order, the first match wins:

1. **`inconclusive — rerun at N≥3`** if any of: `N == 1`, `flip_rate > 0`, every divergence had a `MAX_TURNS=0` / infrastructure root cause, or the run was partial/interrupted.
2. **`merge <winner>`** if one variant has strictly more head-to-head wins than the other AND `flip_rate == 0` across all divergent tasks AND `N ≥ 3`.
3. **`do not merge — no material difference`** if head-to-head wins are tied (including 0–0 with all tasks tied) AND token efficiency gap is `≤ 10%`.

If none of these apply, default to `inconclusive` and explain why in the justification.

Keep the report under one screen of text. It is for a decision, not a novel.

## Phase 9 — Cleanup instructions

Do **not** run `git worktree remove` or `git branch -d` yourself. Print cleanup instructions appropriate to how the command ended:

**If the run completed (Phase 7 produced a report):**
```bash
# Once the user has acted on the recommendation:
git worktree remove ../skills-<branch_a_slug>
git worktree remove ../skills-<branch_b_slug>

# Optional — delete the losing branch (only if it was merged or you're sure you don't want it):
git branch -d <losing_branch>
```

**If the user cancelled at Phase 5 (no run happened):**
```bash
# Nothing ran — clean up the worktrees and generated YAML:
git worktree remove ../skills-<branch_a_slug>
git worktree remove ../skills-<branch_b_slug>
rm tests/experiments/compare-<branch_a_slug>-vs-<branch_b_slug>.yaml
```

Leave the generated experiment YAML in place after a completed run unless the user asks to delete it — it's a record of what was tested and is safe to commit or discard later.

## Error handling

- **Branch not found:** stop, print which branch is missing and how to fetch (`git fetch origin <branch>`).
- **Worktree path exists at a non-worktree directory, or on a different branch:** stop, print `git worktree remove` instructions. Don't overwrite. (If the path is already a valid worktree on the target branch, reuse it — see Phase 1 step 7.)
- **SHA drift before run (Phase 6):** stop and ask the user whether to regenerate the YAML with new SHAs or reset the worktree to the pinned commit.
- **`coder-eval` not installed:** print the `make install` command from `tests/README.md` and stop.
- **Task set empty:** stop. Either the skill filter matched nothing, or there are no task YAMLs.
- **Partial run (interrupted):** report on whatever data exists, mark incomplete variants in the results table, skip the recommendation and say "incomplete run — rerun to decide".

## Anti-patterns

- **Never skip Phase 5's confirmation.** This command spends money. Always confirm before `coder-eval run`.
- **Never auto-clean worktrees or branches.** Destructive. User decides.
- **Never conclude from N=1 alone.** If N=1 was chosen for speed, the recommendation in Phase 8 must say "rerun at N≥3 before deciding".
- **Never mix task sets between variants.** Both variants run the same tasks, same count. That's the whole point of A/B.
- **Never include a `bare` baseline unless the user asks.** This command is a two-way comparison. Baselines are a separate question.
- **Never commit the generated experiment YAML automatically.** The user decides whether it's worth keeping.
