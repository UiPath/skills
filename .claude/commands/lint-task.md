# Lint coder-eval Task YAML

Review a coder-eval task YAML against a quality rubric and surface anti-patterns. Advisory only — does not modify files.

**Input:** `$ARGUMENTS`
- A path to one task YAML, e.g. `tests/tasks/uipath-maestro-flow/smoke/init_validate.yaml`
- Or a glob, e.g. `tests/tasks/uipath-data-fabric/*.yaml`
- Or a directory, e.g. `tests/tasks/uipath-rpa/` (lints every YAML beneath it)

**Output:** One markdown report per task, printed to chat. No file writes.

This command is the source of truth for the rubric. The PR-bot workflow (`.github/workflows/lint-tasks.yml`) reads this file and applies the same rubric to changed YAMLs at PR time.

---

## Severity Levels

Every issue is tagged with one of four severities:

| Level | Meaning |
|---|---|
| **Critical** | Test cannot meaningfully validate the skill — must fix |
| **High** | Test is broken or misleading in a way that wastes infra cost or hides regressions — should fix before merge |
| **Medium** | Quality gap that reduces signal but doesn't break the test — should fix |
| **Low** | Polish — nice to have |

The task's overall **verdict** is the max severity across all issues raised. A task with no issues is **OK**.

## Phase 1 — Resolve Targets

1. Parse `$ARGUMENTS`.
2. If it's a directory, glob `<dir>/**/*.yaml`.
3. If it's a glob, expand it.
4. If it's a single path, use it directly.
5. Skip files under `_shared/` — those are helper scripts, not task definitions.
6. If zero files match, print an error and stop.

For each resolved task file, run Phases 2–4 in parallel where possible.

## Phase 2 — Read Task and Neighbors

For each target task file:

1. Read the full YAML.
2. List sibling task YAMLs in the same folder. These are the "nearby files" used for duplicate detection.
3. Read up to **5** nearby files. If more exist, pick the 5 closest by shared tags (most tag-overlap first, ties broken by alphabetical filename).
4. If the task is in a folder that only contains itself, expand the search to the parent skill directory and pick the same 5 by tag overlap.

## Phase 3 — Apply the Rubric

Evaluate the task against six axes. Each axis can produce zero or more issues, each tagged with a severity.

### A. Self-report anti-pattern

**Raise a Critical issue if both are true:**

1. The `initial_prompt` instructs the agent to write a summary, status, audit, or report file (common names: `report.json`, `summary.json`, `result.json`, `audit.json`, `output.json`, `status.json`). Look for verbs like "save", "write", "create", "produce" near the filename. Custom names that fit the same shape ("a JSON report describing what you did", "a results file with your decisions") count too — judge semantically.
2. One or more `success_criteria` entries (`file_contains`, `file_check`, `json_check`, `file_matches_regex`) reads that same file as their evidence.

**Why it's broken:** the test should check what the agent *did* (commands run, artifacts produced) using deterministic criteria, not what the agent *claims* it did in a self-written summary. The agent grades its own homework, the result is hallucination-prone, and the deterministic criteria coder-eval was built for are bypassed.

### B. Prompt over-specification

Evaluate how much `initial_prompt` leaks the procedure that the skill should be teaching.

Penalize:
- Step-by-step instructions in `initial_prompt` ("1. Walk the discovery hierarchy, 2. List all packages, 3. ...") — the skill should teach the procedure, the prompt should state the goal
- Prescribing specific CLI flags ("Use --output json on every uip tm command") — the skill teaches when to use flags
- Prescribing exact file paths or output formats that `success_criteria` then check (e.g. prompt says "save to `processes.json`", criterion checks `path: processes.json` exists)
- Bulleted imperatives that read like "do X, then Y, then Z" rather than "achieve goal G"

Do **not** penalize:
- Stating the high-level goal and expected output ("Use `uip` to list Flow processes and save the results")
- Naming the artifact when the agent has to know it (e.g. file paths are part of the goal, not the procedure)
- Routing context ("Use the `<skill-name>` skill workflow") — that's a skill-trigger hint, not over-specification
- **Ground-truth anchors.** Literals in the prompt that match expected values checked by `success_criteria` (e.g. prompt says "respond with 'amazing day'", criterion `file_contains` checks for `"amazing day"`). These are test fixtures — the prompt is supplying the expected output the test grades against, not leaking procedure. Same for input values the criteria assert downstream.
- **Tag-justified node/feature names.** If the prompt names a node type or feature that's also the test's `node:X` or feature tag (e.g. "Use a Switch node" on a `node:switch` task, "using a Loop node" on a `node:loop` task), that's deliberate scoping, not over-specification — the test's whole point is to exercise that node type.

Severity:
- **High** — prompt is essentially a recipe; the skill is not actually being tested because any agent could follow the recipe without invoking it
- **Medium** — prompt prescribes 2+ procedure steps or non-trivial flags
- **Low** — prompt leaks one minor detail (e.g. a single flag, a file path that wasn't necessary to specify) that is *not* covered by either carve-out above

### C. Meaningful coverage

Evaluate whether `success_criteria` actually validate skill correctness, vs. trivial existence checks.

Penalize:
- Only `file_exists` (no content check)
- Only `command_executed` with no output validation
- `llm_judge` as the only or dominant criterion (graded by an LLM with no ground truth)
- Criteria that would pass for any non-empty / well-formed input regardless of correctness
- For `command_executed`, `min_count: 1` with a very loose regex — proves nothing about correctness

Reward:
- `json_check` with assertions on actual output values
- `run_command` with `expected_stdout` + `stdout_match: regex`
- `file_check` / `file_contains` with substantive `includes`/`excludes` patterns
- `pytest` with non-trivial test count
- A mix of "did the agent do the thing" (`command_executed`) **and** "is the output correct" (`json_check`/`run_command`)

Severity:
- **High** — no criterion validates correctness; only existence or loose command pattern matches
- **Medium** — at least one correctness check exists but key outputs go unvalidated
- **Low** — minor coverage gap (e.g. one expected file isn't content-checked)

### D. Could pass for the wrong reason

Evaluate whether a trivial / dummy / hard-coded implementation could satisfy the criteria without exercising the skill.

Specifically ask: if the agent skipped the skill entirely and wrote `{"status": "ok"}` to the expected file, or echoed the expected stdout, would the test pass? If yes, the test is gameable.

Penalize:
- Self-report files (already raised under axis A — do not double-count, but reference here)
- `file_contains` with strings the agent could trivially write without invoking the skill (e.g. expecting `"success"` in the output)
- `command_executed` patterns so loose that any usage of the CLI passes
- Tests where the criteria can be satisfied without actually invoking the underlying CLI/SDK that the skill teaches

Reward:
- Criteria tied to side effects in the real platform (created entities, deployed processes, debug runs)
- Output files whose contents are produced by a real CLI call, not the agent's prose
- Cross-checks (agent ran command X **and** file Y contains the output of X)

Severity:
- **Critical** — a dummy implementation passes; the skill is not exercised at all (typically co-occurs with axis A)
- **High** — a lazy agent passes by writing expected strings to disk without using the skill
- **Medium** — a careful agent could game the criteria but the prompt nudges the right way
- **Low** — minor gameability, e.g. one weak criterion among several strong ones

### E. Near-duplicate of nearby files

For each of the 5 nearest files, compare:
- Same skill features tested?
- Same CLI commands required?
- Same workflow shape?
- Same primary node types / connectors / criteria types?

If two tasks differ only in surface-level naming (renamed entity, slightly different prompt wording, same criteria template), they're near-duplicates.

**Scaffold reuse is not duplication.** Tasks that share a YAML scaffold (same sandbox config, same general structure of `success_criteria`, same prompt template) but exercise *materially distinct operations* — e.g. `add_node`, `remove_node`, `move_node`, `update_node` all sharing an edit-flow scaffold while testing entirely different edits — are good template reuse, not duplicates. Do not raise an issue in this case. Only raise when the *operation under test* substantively overlaps.

Severity:
- **High** — this task and a sibling are interchangeable; one of them is pure infra cost with no marginal coverage
- **Medium** — substantial overlap with one neighbor; mild novelty (e.g. different connector but same shape)
- **Low** — same general area as neighbors *and* materially-similar operation (different input but same logic). If the operation is materially distinct, do not raise.

When raising Medium or High, **name the most-similar neighbor** in the issue description.

### F. Validate-only flow tests miss correctness

**Applies only if** the task's `tags` include a flow-building skill (e.g. `uipath-maestro-flow`) AND the task's tier is `e2e` or `integration` (smoke is exempt — smoke tests legitimately stop at validate).

`flow validate` checks JSON shape only; it cannot tell you whether the flow actually produces the right output. A wrong flow that happens to be schema-valid would pass a validate-only test.

Severity:
- **High** — `e2e` tier with no `command_executed` matching `flow\s+debug`. End-to-end means the test should exercise the runtime; without `flow debug`, an e2e test cannot verify correctness.
- **Medium** — `integration` tier with no `flow debug`. Many integration tasks legitimately run without a live tenant in the sandbox; the gap is real but the constraint is well-understood.

**Description-rationale carve-out.** If the task's `description` field explicitly documents the rationale for skipping `flow debug` (e.g. "validate-only because no live tenant", "skipping debug due to trigger-fired execution unreliability"), downgrade the severity by one level (High → Medium, Medium → Low) and quote the rationale in the issue. Authors who document deliberate trade-offs should not be punished as harshly as silent omissions.

## Phase 4 — Compose Per-Task Report

For each task, print:

```
─── tests/tasks/<skill>/<file>.yaml ───────────────────────────

verdict: <OK | Low | Medium | High | Critical>

issues:
  - [Critical] axis A: <one-line description with line refs>
  - [High]     axis B: <one-line description with line refs>
  - [Medium]   axis E: <description, neighbor: foo.yaml>
  - [Low]      axis C: <description>

suggested fixes:
  - <concrete change to make>
  - ...
```

If a task has no issues, print:

```
─── tests/tasks/<skill>/<file>.yaml ───────────────────────────

verdict: OK
```

After all tasks, print one summary line:

```
═══ <N> tasks linted: <C> Critical, <H> High, <M> Medium, <L> Low, <O> OK ═══
```

If multiple tasks share the same root cause (e.g. 4 tasks share the same self-report anti-pattern), call that out once at the bottom under `themes:` rather than repeating the issue per-task. Number themes (Theme 1, Theme 2, …) so per-task lines can reference them.

**Theme-aware downgrade.** When a per-task issue is fully captured by a theme:

- **Downgrade the affected task's overall verdict by one level** (Critical → High, High → Medium, Medium → Low, Low → OK). The systemic finding stays visible at theme severity; per-task lines show membership without amplifying noise.
- The theme entry itself retains the original severity and full description.

**Suppress the issue list when fully theme-captured.** If *every* issue on a task is captured by a theme (i.e. the task adds no unique findings beyond cluster membership), drop the `issues:` and `suggested fixes:` blocks entirely and emit a one-line verdict instead:

```
─── tests/tasks/<skill>/<file>.yaml ───────────────────────────

verdict: <Low | Medium | …> (theme-captured; see Theme 1, 3)
```

If a task has *some* unique issues plus *some* theme-captured ones, keep the issues block but list only the unique issues (drop the `see Theme N` lines). The theme list at the top of the report makes membership visible across tasks; repeating "see Theme N" per task is pure clutter.

A task whose only issues are all captured by themes is effectively "an instance of a known cluster" — its individual verdict reflects how much extra signal it adds beyond the cluster, which is little. The cluster's severity is what readers should react to.

## Rules

1. **Read-only.** Never modify task files. Suggestions are advisory.
2. **Cite line numbers.** When flagging an issue, give the line range in the YAML so the author can navigate.
3. **Be concrete in suggested fixes.** "Improve the test" is not actionable. "Replace `file_exists: report.json` with `command_executed` matching `uip df entity get` plus `json_check` on its output" is.
4. **Skip `_shared/` and check scripts.** Only lint task YAMLs. `_shared/check_*.py` files are helpers.
5. **Stay in scope.** This linter scores test design only. Skill-content quality is out of scope.
6. **Be terse.** One line per issue. The author can drill in if needed; the report is for triage.
