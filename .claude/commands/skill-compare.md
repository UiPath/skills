# Skill Comparison Experiment

Run an apples-to-apples A/B comparison between two refs of the skills repo — each ref is either a branch or a commit SHA — and produce a decision-ready report. Automates the workflow described in [`tests/experiments/skill-comparison-playbook.md`](../../tests/experiments/skill-comparison-playbook.md).

**Input:** `$ARGUMENTS`
- `<ref_a> <ref_b>` — required, the two refs to compare. Each ref is either a **branch name** (local or remote-tracking) or a **commit SHA** (short or full, must already be in the local object database). The two refs can be any mix of the two kinds.
- `<task_selector>` — optional third argument. Restricts which tasks run. Defaults to **all tasks** (warn the user: this can be slow and expensive). Accepts three forms; pick the most specific one that fits the question:
  - **Skill name** (bare word): `uipath-maestro-flow` → all task files under `tests/tasks/uipath-maestro-flow/`. Use this when the comparison is scoped to one skill.
  - **Tag filter** with `tags:` prefix: `tags:smoke` or `tags:smoke,init` → comma-separated tags, OR semantics (any task carrying any of these tags). Forwarded to `coder-eval run --tags`. Use this for cross-skill slices like "only smoke tests" or "only e2e + connector tests".
  - **Path glob** with `paths:` prefix: `paths:tasks/uipath-maestro-flow/init_validate.yaml` or `paths:tasks/*/smoke_*.yaml` (comma-separated globs allowed). Use this when you want a hand-picked subset.
- `<n_reps>` — optional fourth argument. Reps per variant. Defaults to `3`. Accept integers 1–5.

**Examples:**
- `/skill-compare main feat/my-change uipath-maestro-flow` — two branches, scoped to one skill.
- `/skill-compare main a1b2c3d uipath-maestro-flow` — branch vs. commit SHA, scoped to one skill.
- `/skill-compare a1b2c3d e4f5g6h uipath-maestro-flow` — two SHAs (compare two historical points).
- `/skill-compare main feat/my-change tags:smoke` — two branches, only smoke tests across all skills.
- `/skill-compare main feat/my-change tags:smoke,init 5` — smoke OR init tasks, N=5.
- `/skill-compare main feat/my-change paths:tasks/uipath-maestro-flow/init_validate.yaml,tasks/uipath-maestro-flow/registry_discovery.yaml` — two specific files.
- `/skill-compare main feat/my-change` — all tasks across all skills, N=3 (slow + expensive; expect to be re-prompted at Phase 5).

**Ref slugs** (used in filenames and worktree paths):
- Branch: replace `/` with `-` and strip any leading `origin/`. Example: `feat/my-change` → `feat-my-change`.
- SHA: resolve to the 7-char short form via `git rev-parse --short`. Example: `a1b2c3defabc` → `a1b2c3d`. Short SHAs are already filename-safe; no further transformation.

**Output:**
- A new experiment YAML at `tests/experiments/compare-<ref_a_slug>-vs-<ref_b_slug>.yaml`
- Worktrees at `../skills-<ref_a_slug>` and `../skills-<ref_b_slug>` relative to the repo root
- Run results under `tests/runs/compare-<ref_a_slug>-vs-<ref_b_slug>-<timestamp>/`
- Comparison report at `tests/runs/compare-<ref_a_slug>-vs-<ref_b_slug>-<timestamp>/comparison-report.md`

**Working directory.** Every phase runs from `tests/`. All git operations use `git -C ..` to target the repo root. Worktree paths like `../skills-<slug>` resolve alongside the repo, one level above `tests/`.

---

## Phase 1 — Parse & validate

1. Parse `$ARGUMENTS`: require at least two non-empty tokens. If fewer than 2, print usage and stop.
2. For each ref, reject inputs that start with `-` — they can be misread as git flags. Stop with a usage message.
3. **Classify each ref as branch or SHA.** Use `--` to terminate flag parsing throughout:
   ```bash
   # Is it a branch (local or remote-tracking)?
   git -C .. show-ref --verify --quiet "refs/heads/<ref>"         && kind=branch     # local branch
   git -C .. show-ref --verify --quiet "refs/remotes/origin/<ref>" && kind=branch-remote  # remote-only
   # Otherwise, does it resolve to a commit in the local object database?
   [ "$(git -C .. cat-file -t "<ref>" 2>/dev/null)" = "commit" ]  && kind=sha
   ```
   - If `kind=branch`: strip leading `origin/` from the recorded ref if present. Slug = branch name with `/` → `-`.
   - If `kind=branch-remote`: record the remote-only flag — Phase 3 will need `-b <branch> origin/<branch>` to create a tracking branch. Slug = branch name with `/` → `-`.
   - If `kind=sha`: resolve to the 7-char short form with `git -C .. rev-parse --short --verify -- "<ref>"`. Slug = the short SHA. Record the pinned SHA as the short form.
   - If none match: stop and report the ref as not found. For SHAs that might be unfetched, hint at `git fetch origin` or `git fetch origin <sha>` (git supports fetching by SHA on most remotes).
4. Reject the call if the two refs resolve to the **same commit SHA** — comparing identical content produces no signal. Treat `main` and `a1b2c3d` as identical if `main` currently points at `a1b2c3d`; warn the user and stop.
5. Reject the call if `<n_reps>` is outside `1..5`. N=1 is allowed for a fast signal check but warn it's underpowered for decisions.
6. If `<task_selector>` is provided, classify and validate it:
   - **`tags:` prefix** → split the rest on `,` and record as a tag list. No filesystem check at this stage; Phase 5 will warn if the tag list matches zero task files.
   - **`paths:` prefix** → split the rest on `,` and record as a glob list (paths relative to `tests/`). For each glob, check it expands to at least one existing `.yaml` file under `tests/tasks/`. If any glob expands to zero files, stop and list which one was empty.
   - **Bare word** (no prefix) → treat as a skill name. Verify `tasks/<word>/` exists (relative to `tests/`). If not, list available skills under `tasks/*/` and stop.
   - **Anything else** (e.g. `tags:` with no list, `paths:` outside `tests/tasks/`) → stop with a usage message showing the three accepted forms.
7. For each ref, decide whether to create or reuse a worktree at `../skills-<slug>`:
   - If the path does not exist → create it in Phase 3.
   - If it exists, check `git -C .. worktree list --porcelain`:
     - Branch kind: reuse if the worktree is already on that branch.
     - SHA kind: reuse if the worktree has a detached HEAD at the pinned short SHA (compare `git -C <path> rev-parse --short HEAD`).
   - If it exists but isn't a worktree, or is at the wrong branch/SHA, **stop** and tell the user to remove it (`git worktree remove`) or point the command at a different worktree path. Do not overwrite.

## Phase 2 — Ask for the hypothesis

Before doing anything destructive, ask the user for a one-sentence hypothesis being tested. Use a plain free-form text prompt (not `AskUserQuestion` — that tool is for enumerated choices, and hypotheses are open-ended). Example prompt: *"What's the hypothesis for this comparison? One sentence. For example: 'Collapsing per-node planning+impl docs does not hurt success rate.'"*

Save the answer — it goes into the comparison report and the experiment YAML description.

## Phase 3 — Create worktrees

For each ref, skip if Phase 1 flagged it for reuse. Otherwise, from `tests/`, run the command that matches the ref's kind:

**Branch (local):**
```bash
git -C .. worktree add ../skills-<slug> -- <branch>
```

**Branch (remote-only):** create a tracking branch at the same time:
```bash
git -C .. worktree add -b <branch> ../skills-<slug> -- origin/<branch>
```

**SHA:** create a detached-HEAD worktree pinned at that commit. No local branch is created, so a SHA input never pollutes your branch list:
```bash
git -C .. worktree add --detach ../skills-<slug> <sha>
```

The `--` terminator prevents branch names starting with `-` from being parsed as flags; it's not required with `--detach` since the SHA form is unambiguous.

Record each worktree's absolute path. Capture the commit SHA (short form):

```bash
git -C ../skills-<slug> rev-parse --short HEAD
```

For SHA-kind refs, this should equal the pinned SHA from Phase 1 step 3 — if it doesn't, stop (the worktree is at the wrong commit). Keep these SHAs in context; they're re-checked in Phase 6 and reported in Phase 8.

If any worktree add fails, stop and report. Do not attempt to clean up partial state — the user should inspect.

## Phase 4 — Generate the experiment YAML

Start from [`tests/experiments/skill-comparison-template.yaml`](../../tests/experiments/skill-comparison-template.yaml). Write the generated file to `tests/experiments/compare-<ref_a_slug>-vs-<ref_b_slug>.yaml`.

Fill in:
- `experiment_id`: `compare-<ref_a_slug>-vs-<ref_b_slug>`
- `description`: the hypothesis from Phase 2
- `defaults.repeats`: set to `<n_reps>` (the value from `$ARGUMENTS`, default 3). This replaces the per-variant duplication approach — coder_eval's native repeats support fans out each (task, variant) pair into `<n_reps>` replicates automatically.
- One variant per ref (no `-rN` suffixes). Variant IDs must be the slugs.
- Absolute worktree paths in each variant's `plugins[].path`.
- A pinned-SHA comment on the line above each variant. Format depends on ref kind:
  - Branch ref: `# pinned: <branch> @ <sha>` — e.g. `# pinned: feat/my-change @ a1b2c3d`.
  - SHA ref: `# pinned: <sha>` — e.g. `# pinned: a1b2c3d` (no branch; the input was the SHA itself).

Example (shown for N=3):

```yaml
defaults:
  ...
  repeats: 3
  agent:
    ...
    system_prompt: |
      You are a coding agent. Work only inside your current working directory.
      Do NOT read, list, or access any files outside your working directory.
      In particular, do NOT access the plugin directories — those are loaded by
      the skill system and you do not need to read them directly.

variants:
  # pinned: main @ a1b2c3d
  - variant_id: main
    agent:
      plugins:
        - type: "local"
          path: "<abs-worktree-path-main>"

  # pinned: feat/my-change @ e4f5g6h
  - variant_id: feat-my-change
    agent:
      plugins:
        - type: "local"
          path: "<abs-worktree-path-variant>"
```

Do not include a `bare` variant. This command compares two skill configurations — add baselines manually if needed.

## Phase 5 — Resolve the task set and confirm

1. Resolve the task list and the extra `coder-eval` flags from the `<task_selector>` classification recorded in Phase 1 step 6. **Sort the output** so ordering is deterministic across runs (filesystem traversal order is not guaranteed, and an unsorted list can produce run-to-run permutation noise):
   - **Skill name** (or no selector): expand to `find tasks/<skill_name> -name '*.yaml' -type f | sort` (or `find tasks -name '*.yaml' -type f | sort` for no selector). No extra flags.
   - **Tags**: expand to `find tasks -name '*.yaml' -type f | sort` (the full set), and add `--tags <tag1>,<tag2>,...` to the `coder-eval run` invocation. `coder-eval` does the tag filtering at runtime; passing the full file list keeps the resolution logic uniform.
   - **Paths**: expand each glob in order with `ls <glob> 2>/dev/null` (relative to `tests/`), concatenate, then `| sort -u` to dedupe. Stop if the final list is empty.

   After resolution, if the final task count is zero (e.g. tags matched no files), stop and report which selector matched nothing.
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
RUN_DIR="runs/compare-<ref_a_slug>-vs-<ref_b_slug>-$(date +%Y%m%d-%H%M%S)"
SKILLS_REPO_PATH=$(cd .. && pwd) \
  .venv/bin/coder-eval run <resolved-task-files> \
  -e experiments/compare-<ref_a_slug>-vs-<ref_b_slug>.yaml \
  --run-dir "$RUN_DIR" \
  --repeats <n_reps> \
  [--tags <tag1>,<tag2>,...]   # only when <task_selector> was tags:...
  -j 1 -v
```

The `--repeats` flag overrides the `repeats:` value in the experiment YAML at runtime, so the YAML can stay committed with `repeats: 1` as a safe default while runs always use the CLI-supplied value.

Record `tests/$RUN_DIR` as the run directory — everything downstream reads from there.

Keep `-j 1`. Parallel execution introduces timing noise (shared API rate limits, disk contention) that can distort small variant effects. If the user explicitly asks for parallelism, honor it but note the caveat in the report.

Stream output. If the run fails mid-way, capture the partial results and continue to Phase 7 with whatever data exists.

## Phase 7 — Analyze

1. Read `<RUN_DIR>/experiment.md` and each variant's `variant.json` (where `<RUN_DIR>` is the path recorded at the end of Phase 6). Build a results table:

   | variant | success rate | avg score | avg duration | total tokens |
   |---|---|---|---|---|
   | <ref_a> | ... | ... | ... | ... |
   | <ref_b> | ... | ... | ... | ... |

   If N>1, coder_eval produces per-replicate output under `<RUN_DIR>/<variant>/<task>/00/`, `01/`, etc. Aggregate across replicates: use mean for score/duration/tokens, and `passed_runs / total_runs` for success rate per task. The top-level `variant.json` already includes aggregated statistics when `repeats > 1`; prefer those over manual aggregation.

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
   - **Flip rate** (N>1 only) — for each task, compare the winning variant across replicates (`00/`, `01/`, ...). A task is "flipped" if not all replicates produced the same winner (ties across replicates are not flips). Report `flip_rate = flipped_tasks / tasks_with_at_least_one_non_tie_replicate`. Flip rate `> 0` is a high-variance signal.
   - **Token efficiency** — percent difference between variants' total tokens. Only material at `> 10%`.

## Phase 8 — Write the comparison report

Write `<RUN_DIR>/comparison-report.md` with this structure:

```markdown
# Skill Comparison: <ref_a> vs <ref_b>

**Hypothesis:** <from Phase 2>
**Run:** `<RUN_DIR basename>`
**Model:** <from experiment defaults>
**Tasks:** <count> (selector: <verbatim task_selector or "all">)
**N:** <n_reps> rep(s) per variant

## Variants
- `<ref_a>` @ `<sha_a>`
- `<ref_b>` @ `<sha_b>`

## Results
<results table from Phase 7 step 1>

## Head-to-head
- <ref_a> wins: <count>
- <ref_b> wins: <count>
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
git worktree remove ../skills-<ref_a_slug>
git worktree remove ../skills-<ref_b_slug>
```

If the losing ref was a **branch** (not a SHA), also consider:
```bash
# Optional — delete the losing branch (only if it was merged or you're sure you don't want it):
git branch -d <losing_branch>
```

SHA-kind refs create no local branch, so nothing to delete there.

**If the user cancelled at Phase 5 (no run happened):**
```bash
# Nothing ran — clean up the worktrees and generated YAML:
git worktree remove ../skills-<ref_a_slug>
git worktree remove ../skills-<ref_b_slug>
rm tests/experiments/compare-<ref_a_slug>-vs-<ref_b_slug>.yaml
```

Leave the generated experiment YAML in place after a completed run unless the user asks to delete it — it's a record of what was tested and is safe to commit or discard later.

## Error handling

- **Ref not found:** stop, print which ref is missing. For branches, suggest `git fetch origin <branch>`. For SHAs, suggest `git fetch origin` (or `git fetch origin <sha>` if the SHA isn't reachable from any known remote ref).
- **Worktree path exists at a non-worktree directory, or on a different branch:** stop, print `git worktree remove` instructions. Don't overwrite. (If the path is already a valid worktree on the target branch, reuse it — see Phase 1 step 7.)
- **SHA drift before run (Phase 6):** stop and ask the user whether to regenerate the YAML with new SHAs or reset the worktree to the pinned commit.
- **`coder-eval` not installed:** print the `make install` command from `tests/README.md` and stop.
- **Task set empty:** stop and report which selector matched zero files. Possible causes: skill folder doesn't exist, tag list matches nothing, path globs don't expand to any `.yaml` files.
- **Partial run (interrupted):** report on whatever data exists, mark incomplete variants in the results table, skip the recommendation and say "incomplete run — rerun to decide".

## Anti-patterns

- **Never skip Phase 5's confirmation.** This command spends money. Always confirm before `coder-eval run`.
- **Never auto-clean worktrees or branches.** Destructive. User decides.
- **Never conclude from N=1 alone.** If N=1 was chosen for speed, the recommendation in Phase 8 must say "rerun at N≥3 before deciding".
- **Never mix task sets between variants.** Both variants run the same tasks, same count. That's the whole point of A/B.
- **Never include a `bare` baseline unless the user asks.** This command is a two-way comparison. Baselines are a separate question.
- **Never commit the generated experiment YAML automatically.** The user decides whether it's worth keeping.
