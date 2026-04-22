# Skill Comparison Experiments — Playbook

How to run an apples-to-apples A/B on a skill variant (e.g. "does this restructuring of the skill beat main?"). Use this when the question is *"should we merge this change?"* — not when you're adding a new skill or debugging a single task.

## 1. Decide what you're comparing

Write the hypothesis in one sentence before touching any YAML. Examples:

- *"Collapsing per-node `planning.md`+`impl.md` into one `flow-plan.md` does not hurt success rate."*
- *"Dropping the mandatory two-phase planning workflow improves token efficiency without a success-rate regression."*

If you can't state it in one sentence, the experiment will not produce a clear answer. Split it.

## 2. Set up variants as branches in one repo

**Do not** use two separate clones. Diverging clones drift on unrelated files, so you can no longer claim the only difference is the change you're testing.

Instead, one repo, one branch per variant, all checked out in parallel via `git worktree`:

```bash
# From the skills repo root
git worktree add ../skills-main     main                          # baseline
git worktree add ../skills-variantb   feat/my-change     # variant under test
```

Each worktree is a full working copy on its own branch. They share the `.git` dir, so there's no duplication of history and branches stay in sync. When the experiment is done, delete the worktrees with `git worktree remove`.

For three-way comparisons (baseline vs A vs B) add a third worktree on a third branch.

## 3. Pin each variant to a commit SHA

Record the SHA of each branch in the experiment YAML as a comment. This is the single most important reproducibility step. Paths drift; SHAs don't.

```yaml
  - variant_id: variantb
    # pinned: feat/my-change @ a1b2c3d
    agent:
      plugins:
        - type: "local"
          path: "/Users/you/src/skills-variantb"
```

A month from now, `git checkout a1b2c3d` in either worktree reconstructs exactly what ran. Without the SHA, "variantb" means whatever happens to be at that path today.

## 4. Control the prompt and the environment

Divergent tasks are worth analyzing only if the variants were actually running under the same conditions. Before kicking off:

- **Prompts must not name the skill.** If the task prompt says "use the uipath-maestro-flow skill", you're testing whether the skill's *name* triggers, not the skill's *content*. Edit task YAML prompts to describe goals, not skill names.
- **Run with `cwd` outside the skill repo.** Running inside the repo lets the agent read skill source files directly via `Read`, bypassing the plugin system. Use `sandbox.driver: tempdir` (all existing tasks already do this).
- **Confirm the experiment's `plugins` list is the only plugin source.** If you also have plugins installed at the user level (`~/.claude/plugins/`), they load in addition to the experiment's plugins and can pollute the comparison. Check with `ls ~/.claude/plugins/` before the run; temporarily move any entries aside if they overlap in scope with the skill under test.
- **Lock the model.** Set `model: claude-sonnet-4-6` (or whichever) in `defaults.agent`. Don't let variants pick up different defaults.

## 5. Pick the task set

Start with every task for the affected skill. You want a wide net to find where the variants diverge — not a narrow test that confirms your prior.

```bash
find tasks/uipath-maestro-flow -name '*.yaml'
```

After the first pass, if you have a decision to make, re-run **only the divergent tasks** at higher N (see next step). The tied tasks don't need more reps — they're tied.

## 6. Get more than N=1 per task

`coder-eval` has no `--reps` flag. One task under one variant runs once. That's fine for finding *where* variants diverge, but it's not enough to make a decision — timeouts and `MAX_TURNS` outcomes have high run-to-run variance.

Two workable options:

**Option A — duplicate the variant with distinct IDs** (recommended for automation):

```yaml
variants:
  - variant_id: variantb-r1
    agent: { plugins: [...] }
  - variant_id: variantb-r2
    agent: { plugins: [...] }
  - variant_id: variantb-r3
    agent: { plugins: [...] }
```

Each variant runs the full task set once. Aggregate across the `r1`/`r2`/`r3` variants in analysis.

**Option B — re-run the experiment in a shell loop**:

```bash
for i in 1 2 3; do
  SKILLS_REPO_PATH=$(cd .. && pwd) \
    .venv/bin/coder-eval run tasks/uipath-maestro-flow/*.yaml \
    -e experiments/my-comparison.yaml \
    --run-dir runs/compare-$(date +%F)-rep-$i
done
```

Lower effort to set up, harder to analyze (three separate run dirs to combine).

**Rule of thumb:** N ≥ 3 before calling anything decisive. For any task that diverged at N=1, push to N ≥ 5 on just that task.

## 7. Run and capture output

```bash
cd tests
SKILLS_REPO_PATH=$(cd .. && pwd) \
  .venv/bin/coder-eval run tasks/uipath-maestro-flow/*.yaml \
  -e experiments/my-comparison.yaml \
  -j 1 -v
```

Results land in `runs/<timestamp>/`. The aggregator writes:

- `experiment.md` — per-variant aggregates and per-task comparison
- `<variant-id>/variant.json` — machine-readable variant totals
- `run.md` — flattened per-task table across all variants

Keep `-j 1` for comparison runs. Parallel execution can introduce timing noise (shared API rate limits, disk contention) that distorts small variant effects.

## 8. Interpret the numbers

Look at, in order:

1. **Head-to-head wins and ties.** Most tasks will tie — that's expected, and "skill content is good enough for easy tasks and not good enough for hard ones" is a valid finding. Focus on the divergent tasks.
2. **Why each divergence happened.** Read the agent transcript (`task.json` → `transcript`) for the divergent tasks. A win caused by a timeout on one side is weak evidence; a win caused by a deterministic workflow difference is strong evidence.
3. **Token usage as a tiebreaker.** When success rates are close, the cheaper variant wins — if and only if the token gap is material (>10%).
4. **Variance.** If the same task flips between reps (N≥3), note the flip rate. A 2/3 → 1/3 task is not a decisive win.

Common false positives to watch for:
- **Timeouts on both sides.** High-variance outcomes. Don't weight these heavily.
- **One variant times out at `MAX_TURNS=0`.** The agent never got a turn — you're measuring infrastructure, not the skill.
- **Small N head-to-head wins.** At N=1, 2 wins out of 24 tasks is noise if the divergent tasks are both timeouts.

## 9. Decide and record

Write a short report in the run directory before moving on. Minimum contents:

- Hypothesis (from step 1)
- SHAs of each variant
- Task count, N, model
- Result table (success rate, score, tokens)
- Divergent tasks with one-line root-cause
- Decision: merge / don't merge / rerun at higher N

Commit the experiment YAML and the report into the repo (or link to the run ID in Slack). Ad-hoc experiments tend to disappear — if you don't commit the config, you cannot redo the experiment later.

## 10. Clean up

```bash
git worktree remove ../skills-variantb
git branch -d feat/my-change    # or -D if merged via squash
```

If the variant wins and gets merged, delete the worktree and branch. If it loses, keep the branch around under a `exp/*` prefix for a few weeks in case you want to revisit.

## Template

See [`skill-comparison-template.yaml`](skill-comparison-template.yaml) for a minimal, annotated starting point. Copy, rename, fill in the SHAs, run.
