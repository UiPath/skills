# Lint coder-eval Task YAML

Score a coder-eval task YAML against a quality rubric and surface anti-patterns. Advisory only — does not modify files.

**Input:** `$ARGUMENTS`
- A path to one task YAML, e.g. `tests/tasks/uipath-maestro-flow/smoke/init_validate.yaml`
- Or a glob, e.g. `tests/tasks/uipath-data-fabric/*.yaml`
- Or a directory, e.g. `tests/tasks/uipath-rpa/` (lints every YAML beneath it)

**Output:** One markdown report per task, printed to chat. No file writes.

This command is the source of truth for the rubric. The PR-bot workflow (`.github/workflows/lint-tasks.yml`) reads this file and applies the same rubric to changed YAMLs at PR time.

---

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
2. List sibling task YAMLs in the same folder (e.g. all `*.yaml` in `tests/tasks/uipath-maestro-flow/smoke/`). These are the "nearby files" used for duplicate detection.
3. Read up to **5** nearby files. If more exist, pick the 5 closest by shared tags (most tag-overlap first, ties broken by alphabetical filename).
4. If the task is in a folder that only contains itself, expand the search to the parent skill directory (e.g. `tests/tasks/uipath-maestro-flow/**/*.yaml`) and pick the same 5 by tag overlap.

## Phase 3 — Apply the Rubric

Score the task on six axes. Each axis is 0–10 unless marked binary. Pass threshold for the overall verdict is **7/10 average across applicable axes, AND no binary FAILs**.

### A. Self-report anti-pattern (binary: PASS / FAIL)

**FAIL the task if both are true:**

1. The `initial_prompt` instructs the agent to write a summary, status, audit, or report file (common names: `report.json`, `summary.json`, `result.json`, `audit.json`, `output.json`, `status.json`). Look for verbs like "save", "write", "create", "produce" near the filename. Custom names that fit the same shape ("a JSON report describing what you did", "a results file with your decisions") count too — judge semantically.
2. One or more `success_criteria` entries (`file_contains`, `file_check`, `json_check`, `file_matches_regex`) reads that same file as their evidence.

This is the dominant anti-pattern flagged in the 2026-04-30 audit (skills PR #507). The agent grades its own homework, hallucination-prone, and bypasses the deterministic criteria coder-eval was built for.

**Why it's banned:** the test should check what the agent *did* (commands run, artifacts produced) using deterministic criteria, not what the agent *claims* it did.

### B. Prompt over-specification (0–10)

**Score how much the prompt leaks the answer or the procedure that the skill should be teaching.**

Penalize:
- Step-by-step instructions in `initial_prompt` ("1. Walk the discovery hierarchy, 2. List all packages, 3. ...") — the skill should teach the procedure, the prompt should state the goal
- Prescribing specific CLI flags (`Use --output json on every uip tm command`) — the skill teaches when to use flags
- Prescribing exact file paths or output formats that `success_criteria` then check (e.g. prompt says "save to `processes.json`", criterion checks `path: processes.json` exists)
- Bulleted imperatives that read like "do X, then Y, then Z" rather than "achieve goal G"

Do **not** penalize:
- Stating the high-level goal and expected output ("Use `uip` to list Flow processes and save the results")
- Naming the artifact when the agent has to know it (e.g. file paths are part of the goal, not the procedure)
- Routing context ("Use the `uipath-maestro-flow` skill workflow") — that's a skill-trigger hint, not over-specification

Anchor:
- 9–10: minimal goal-only prompt, agent must use the skill to figure out how
- 7–8: states goal + a small amount of necessary context (e.g. naming a tenant, providing inputs)
- 5–6: leaks 1–2 steps or flags
- 3–4: prompt is mostly a recipe; skill is barely needed
- 0–2: prompt is the recipe; criteria just verify obedience

### C. Meaningful coverage (0–10)

**Score whether the criteria actually validate skill correctness, vs. trivial existence checks.**

Penalize:
- Only `file_exists` (no content check)
- Only `command_executed` with no output validation (agent ran the command but did anything else with it)
- `llm_judge` as the only or dominant criterion (graded by an LLM with no ground truth)
- Criteria that would pass for any non-empty / well-formed input regardless of correctness
- For `command_executed`, `min_count: 1` with a very loose regex (`uip\s+.*`) — proves nothing about correctness

Reward:
- `json_check` with assertions on actual output values
- `run_command` with `expected_stdout` + `stdout_match: regex`
- `file_check` / `file_contains` with substantive `includes`/`excludes` patterns
- `pytest` with non-trivial test count
- A mix of "did the agent do the thing" (`command_executed`) **and** "is the output correct" (`json_check`/`run_command`)

Anchor:
- 9–10: every criterion ties to observable correctness; output values are checked, not just file presence
- 7–8: at least one strong correctness check, plus existence/command checks
- 5–6: command_executed + file_exists, no content validation
- 3–4: only existence checks, or only loose command pattern matches
- 0–2: criteria that pass for any input

### D. Could pass for the wrong reason (0–10) — *higher = harder to game*

**Score whether a trivial / dummy / hard-coded implementation could satisfy the criteria without exercising the skill.**

Specifically ask: if the agent skipped the skill entirely and wrote `{"status": "ok"}` to the expected file, or echoed the expected stdout, would the test pass? If yes, the test is gameable.

Penalize:
- Self-report files (already caught by axis A but compounds the score here)
- `file_contains` with strings the agent could trivially write without invoking the skill (e.g. expecting `"success"` in the output)
- `command_executed` patterns so loose that any usage of the CLI passes (e.g. `uip\s+.*`)
- Tests where the criteria can be satisfied without actually invoking the underlying CLI/SDK that the skill teaches
- Tests where success is determined by the agent's self-report

Reward:
- Criteria tied to side effects in the real platform (created entities, deployed processes, debug runs)
- Output files whose contents are produced by a real CLI call, not the agent's prose
- Cross-checks (agent ran command X **and** file Y contains the output of X)

Anchor:
- 9–10: the test cannot pass without actually invoking the skill's tooling correctly
- 7–8: gaming would require non-trivial effort and produce obvious red flags
- 5–6: a careful agent could pass without using the skill, but the prompt nudges it the right way
- 3–4: a lazy agent could pass by writing the expected strings to disk
- 0–2: a dummy implementation passes; the skill is not actually exercised

### E. Near-duplicate (vs. nearby files) (0–10) — *higher = more unique*

**Score how much marginal coverage this task adds over its nearest siblings.**

For each of the 5 nearest files, compare:
- Same skill features tested?
- Same CLI commands required?
- Same workflow shape (e.g. both create-then-validate)?
- Same primary node types / connectors / criteria types?

If two tasks differ only in surface-level naming (renamed entity, slightly different prompt wording, same criteria template), they're near-duplicates.

Anchor:
- 9–10: covers a feature/path no neighbor covers
- 7–8: same area as neighbors but materially different input or topology
- 5–6: substantial overlap with one neighbor, mild novelty
- 3–4: another task tests almost the same thing
- 0–2: this task and a sibling are interchangeable

When scoring below 7, **name the most-similar neighbor** in the report.

### F. Maestro-flow: validate-only is weak (binary FLAG, only applies when relevant)

**Applies only if** the task's `tags` include `uipath-maestro-flow` AND the task's `tier` is `e2e` or `integration` (smoke is exempt — smoke tests legitimately stop at validate).

**FLAG if:**
- No `command_executed` criterion matches `flow\s+debug` (i.e. test never runs `uip maestro flow debug`), AND
- The task is supposed to verify correctness end-to-end

`flow validate` checks JSON shape only; it cannot tell you whether the flow actually produces the right output. Real correctness for e2e/integration maestro-flow tests requires `flow debug` (or equivalent platform execution).

Smoke-tier validate-only tests are fine — that's what smoke is for. Anything tagged `e2e` or `integration` that stops at validate is implicitly an axis-D fail (could pass for the wrong reason: a wrong flow that happens to be schema-valid).

## Phase 4 — Compose Per-Task Report

For each task, print:

```
─── tests/tasks/<skill>/<file>.yaml ───────────────────────────

overall: <X>/10  <✅ pass | ❌ below threshold | ❌ FAIL: <axis name>>

A. self-report anti-pattern   <PASS | FAIL>
B. prompt over-specification  <X>/10
C. meaningful coverage        <X>/10
D. hard to game               <X>/10
E. unique vs. neighbors       <X>/10  <neighbor: <filename> if <7>
F. maestro-flow debug check   <PASS | FAIL | N/A>

issues:
  - <axis letter> <severity>: <one-line description with line refs>
  - ...

suggested fixes:
  - <concrete change to make, e.g. "replace report.json self-report with command_executed for `uip df entity delete` (expected exit code != 0)">
  - ...
```

After all tasks, print one summary line:

```
═══ <N> tasks linted: <P> pass, <F> fail. Avg <X>/10. ═══
```

If multiple tasks fail with the same root cause (e.g. 4 tasks share the `report.json` anti-pattern), call that out once at the bottom under `themes:` rather than repeating the issue per-task.

## Rules

1. **Read-only.** Never modify task files. Suggestions are advisory.
2. **Cite line numbers.** When flagging an issue, give the line range in the YAML so the author can navigate.
3. **Be concrete in suggested fixes.** "Improve the test" is not actionable. "Replace `file_exists: report.json` with `command_executed` matching `uip df entity get` plus `json_check` on its output" is.
4. **Skip `_shared/` and check scripts.** Only lint task YAMLs. `_shared/check_*.py` files are helpers.
5. **Don't re-litigate skill choice.** This linter scores test design, not whether the skill itself is well-named or scoped. Skill-level review is `/test-coverage` and `.claude/rules/skill-review.md`.
6. **Be terse.** One line per issue. The author can drill in if needed; the report is for triage.
