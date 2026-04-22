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
- Run results under `tests/runs/<timestamp>/`
- Comparison report at `tests/runs/<timestamp>/comparison-report.md`

Branch name slugs: replace `/` with `-` and strip any leading `origin/`. Example: `feat/my-change` → `feat-my-change`.

---

## Phase 1 — Parse & validate

1. Parse `$ARGUMENTS`: require at least two non-empty tokens. If fewer than 2, print usage and stop.
2. Normalize each branch name:
   - Strip leading `origin/` if present.
   - Record the original (e.g. `feat/foo`) and the slug (e.g. `feat-foo`) separately.
3. Reject the call if `<branch_a> == <branch_b>` — comparing a branch to itself produces no signal.
4. Reject the call if `<n_reps>` is outside `1..5`. N=1 is allowed for a fast signal check but warn it's underpowered for decisions.
5. For each branch, verify it exists:
   ```bash
   git -C <repo_root> rev-parse --verify "<branch>" >/dev/null 2>&1
   ```
   If the local ref fails, retry with `origin/<branch>` and record that the branch is remote-only (will need a tracking branch during worktree setup). If still not found, stop and tell the user which branch is missing.
6. If `<skill_name>` is provided, verify `tests/tasks/<skill_name>/` exists. If not, list available skills under `tests/tasks/*/` and stop.
7. Check that the target worktree paths are free:
   ```bash
   test ! -e ../skills-<slug>  # for each branch
   ```
   If a path exists, stop and ask the user to remove it (`git worktree remove`) before rerunning — do **not** overwrite.

## Phase 2 — Ask for the hypothesis

Before doing anything destructive, ask the user (via `AskUserQuestion`) for a one-sentence hypothesis being tested. Example prompt: *"What's the hypothesis? (one sentence, e.g., 'Collapsing per-node planning+impl docs does not hurt success rate')"*. Use `Something else` as the last option if presenting suggestions.

Save the answer — it goes into the comparison report and the experiment YAML description.

## Phase 3 — Create worktrees

For each branch, from the repo root:

```bash
git worktree add ../skills-<slug> <branch>
```

If the branch is remote-only (from Phase 1), first create a tracking branch:

```bash
git worktree add -b <branch> ../skills-<slug> origin/<branch>
```

Record each worktree's absolute path. Capture the commit SHA (short form):

```bash
git -C ../skills-<slug> rev-parse --short HEAD
```

If any worktree add fails, stop and report. Do not attempt to clean up partial state — the user should inspect.

## Phase 4 — Generate the experiment YAML

Start from [`tests/experiments/skill-comparison-template.yaml`](../../tests/experiments/skill-comparison-template.yaml). Write the generated file to `tests/experiments/compare-<branch_a_slug>-vs-<branch_b_slug>.yaml`.

Fill in:
- `experiment_id`: `compare-<branch_a_slug>-vs-<branch_b_slug>`
- `description`: the hypothesis from Phase 2
- One variant per branch. Variant IDs must be the slugs.
- Absolute worktree paths in each variant's `plugins[].path`.
- A pinned-SHA comment on the line above each variant, e.g. `# pinned: feat/my-change @ a1b2c3d`.

If `<n_reps>` > 1: duplicate each variant N times with `-r1`, `-r2`, ... `-rN` suffixes on the `variant_id`. All reps of a variant share the same path. Example for N=3:

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

1. Resolve the task list:
   - If `<skill_name>` was provided: `find tests/tasks/<skill_name> -name '*.yaml' -type f`
   - Otherwise: `find tests/tasks -name '*.yaml' -type f`
2. Estimate cost and time. A rough per-task budget is **~5 minutes and ~$0.50** at the experiment defaults (`max_turns: 20`, `task_timeout: 600`). Multiply by `num_tasks × num_variants × n_reps`.
3. Present a confirmation prompt via `AskUserQuestion` with these options:
   - **Run now** — proceeds to Phase 6.
   - **Show me the experiment YAML first** — opens the generated file for review, then re-prompts.
   - **Cancel** — stops. Tell the user how to clean up (Phase 9 instructions) even though nothing has run yet, because the worktrees and YAML still exist.
   - **Something else** — accept free-form input (e.g., "drop reps to 1", "limit to smoke tasks") and re-plan accordingly.

Do not proceed without explicit confirmation. The run can take hours and cost real money.

## Phase 6 — Run

From inside `tests/`:

```bash
SKILLS_REPO_PATH=$(cd .. && pwd) \
  .venv/bin/coder-eval run <resolved-task-files> \
  -e experiments/compare-<branch_a_slug>-vs-<branch_b_slug>.yaml \
  -j 1 -v
```

Keep `-j 1`. Parallel execution introduces timing noise (shared API rate limits, disk contention) that can distort small variant effects. If the user explicitly asks for parallelism, honor it but note the caveat in the report.

Stream output. If the run fails mid-way, capture the partial results and continue to Phase 7 with whatever data exists.

Find the run directory: it's the newest subdirectory of `tests/runs/` created after the command started. Record its absolute path.

## Phase 7 — Analyze

1. Read `tests/runs/<timestamp>/experiment.md` and each variant's `variant.json`. Build a results table:

   | variant | success rate | avg score | avg duration | total tokens |
   |---|---|---|---|---|
   | <branch_a> | ... | ... | ... | ... |
   | <branch_b> | ... | ... | ... | ... |

   If N>1, aggregate across `-r1`/`-r2`/`-rN`: use mean for score/duration/tokens, and `passed_runs / total_runs` for success rate per task.

2. Identify divergent tasks. A task is divergent if its scores differ between variants by more than 0.1, **or** one variant succeeded while the other hit `TIMEOUT`/`MAX_TURNS_EXHAUSTED`/`FAILURE`. Ties (same status, scores within 0.1) are not divergent.

3. For each divergent task, read the losing variant's `task.json` transcript and extract a one-line root cause. Look for:
   - **Timeout at `MAX_TURNS=0`** — agent never got a turn. Infrastructure issue, discard.
   - **Rabbit hole** — agent repeatedly retried a failing approach. Cite the specific command or error that looped.
   - **Missed workflow step** — agent skipped a critical rule (e.g., didn't run a required setup command). Cite the skipped step.
   - **Validation failure** — generated artifact was wrong. Cite what was wrong.

4. Count reliability signals:
   - Head-to-head wins per variant (divergent-task wins only).
   - Flip rate across reps: for each task at N>1, how often does the same variant win? Flip rate >0 is a high-variance signal.
   - Token efficiency: percent difference between variants' total tokens. Only material at >10%.

## Phase 8 — Write the comparison report

Write `tests/runs/<timestamp>/comparison-report.md` with this structure:

```markdown
# Skill Comparison: <branch_a> vs <branch_b>

**Hypothesis:** <from Phase 2>
**Run:** `<timestamp>`
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
<one of: "merge <branch>", "do not merge <branch>", "inconclusive — rerun at N=<higher>", with a one-paragraph justification>

## Caveats
<any of these that apply, each as one bullet>
- N=<n> is low for decisions; flip rate X% on Y tasks.
- Both divergent tasks were timeouts; high variance.
- One variant hit MAX_TURNS=0 on <task> (agent never got a turn).
- Token gap <X>%; not material.
```

Keep it under one screen of text. The report is for a decision, not a novel.

## Phase 9 — Cleanup instructions

Do **not** run `git worktree remove` or `git branch -d` yourself. Tell the user to clean up manually after they've acted on the recommendation:

```bash
# When the comparison is resolved:
git worktree remove ../skills-<branch_a_slug>
git worktree remove ../skills-<branch_b_slug>

# Optional — delete the losing branch (only if it was merged or you're sure you don't want it):
git branch -d <losing_branch>
```

Leave the generated experiment YAML in place unless the user asks to delete it — it's a record of what was tested and is safe to commit or discard later.

## Error handling

- **Branch not found:** stop, print which branch is missing and how to fetch (`git fetch origin <branch>`).
- **Worktree path exists:** stop, print `git worktree remove` instructions. Don't overwrite.
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
