# Generate Test Task

Generate **one** coder-eval task YAML (and an optional check script) for the scenario described in `$ARGUMENTS`.

**Input:** `$ARGUMENTS` — a free-form description of the scenario the task should cover. The target skill is **always inferred** from the description (Phase 1a). Do not require or accept a skill name as a separate argument.

**Optional tier filter.** If the description contains a bare `smoke` / `integration` / `e2e` token (whitespace-separated), use it as the tier hint. Otherwise pick the tier from the scenario itself per the Phase 2a table.

**Output:** ONE task YAML at `tests/tasks/<skill-name>/...` plus an optional `check_*.py` for e2e tasks. Always one task per invocation — re-run the command for additional scenarios.

> ## ⚠ Generated tasks are unverified scaffolds
>
> The author **MUST** before merging:
> 1. Run the task end-to-end with `coder-eval` (command in the Phase 4 summary).
> 2. Confirm it passes.
> 3. State that explicitly in the PR description (e.g. `Ran <task-id> locally and it passed.`).
>
> The lint workflow at `.github/workflows/lint-tasks.yml` raises a **High** issue when the PR description doesn't claim a passing run. Pushing the YAML alone is not enough.

---

## Phase 1 — Context Gathering

### 1a. Infer the target skill from the description

1. List candidates via `ls skills/uipath-*/SKILL.md`.
2. Read every `SKILL.md` frontmatter (name + description) — that is what the runtime uses to decide which skill activates on a given prompt.
3. Match the input description to the skill whose frontmatter best covers it. Tiebreak by inspecting the candidates' `references/` and `assets/` filenames.
4. If two or more skills are plausible, ask the user to disambiguate before proceeding. Do not guess.

Once resolved, `<skill-name>` is fixed for the rest of the run.

### 1b. Read context (parallel Explore agents or parallel tool calls)

1. `skills/<skill-name>/SKILL.md` plus everything under `skills/<skill-name>/references/` and `skills/<skill-name>/assets/`.
2. `tests/README.md` — authoritative source for the **Tag Taxonomy**, **Weight scale**, and **experiment defaults** (`smoke.yaml` for PR-gate, `default.yaml` for nightly e2e and ad-hoc, `smoke-windows.yaml` for Windows RPA). Do not duplicate that material here; reference it.
3. `.claude/commands/lint-task.md` — the quality rubric (six axes, four severities). Generated tasks must not trip a Medium-or-above issue on any axis.
4. `tests/reports/<skill-name>.md` if it exists — use it to detect that the scenario in the description is already a known gap with prior recommendations.
5. Every existing `*.yaml` task under `tests/tasks/` — collect all `task_id` values (collision check), study conventions for the target skill (or a peer skill if the target has none yet), and confirm the described scenario is not already covered.

## Phase 2 — Task Design

The described scenario IS the task. If an existing task already covers it, stop and tell the user — do not generate a duplicate. Suggest the existing task; if the existing task is weak (Medium-or-above issues against `lint-task.md`), suggest amending it instead of adding a new one.

### 2a. Tier

Per the tier table in `tests/README.md`:

| Signal | Tier |
|---|---|
| CLI produces correct output, report generation | smoke |
| Multi-step workflow with error handling, cross-component integration | integration |
| Full build → validate → run cycle, artifact correctness | e2e |

### 2b. Tags

Required, in this order: `<skill-name>` first, then `<tier>`, then `mode:<X>`. Optional dimensions (`shape:*`, `node:*`, `resource`, `connector`, `feature:*`) follow per `tests/README.md#tag-taxonomy`.

- **`<skill-name>`** — always the first tag. Must match the `skills/<name>/` folder exactly (e.g. `uipath-maestro-flow`, `uipath-agents`). Never abbreviate or drop the `uipath-` prefix.
- **`<tier>`** — `smoke`, `integration`, or `e2e`.
- **`mode:<X>`** — required per the Coding Agents Scorecard tagging system (introduced in skills PR #614 by Tomasz Religa). Pick exactly one:
  - `mode:build` — creating, designing, editing, or deploying flows, nodes, or skills.
  - `mode:operate` — running, triggering, managing live instances, connectors, or integrations in production.
  - `mode:diagnose` — investigating faults, inspecting execution traces/variables, evaluating, or debugging.

**Use only the closed-vocabulary values listed in `tests/README.md`.** If no value fits an optional dimension, omit it and surface it in the Phase 4 summary so the taxonomy can be extended deliberately. Never invent tag values inline.

Final tag order: `[<skill-name>, <tier>, mode:X, shape:X, node:..., resource, connector, feature:...]`.

Example:

```yaml
tags: [uipath-maestro-flow, e2e, mode:build, shape:multi-node, node:decision, connector, feature:http]
```

### 2c. task_id

Convention: `skill-<domain>-<capability>` (lowercase kebab-case, see `tests/README.md` for the domain mapping). Verify uniqueness against the IDs collected in Phase 1.

### 2d. initial_prompt

State the **goal and expected output**. The skill teaches the procedure — that is what the test is verifying. Mirror the prompt style of existing tasks for the target skill.

Two anti-patterns from `lint-task.md` to actively avoid:

- **Self-report anti-pattern (Critical).** Never instruct the agent to write a summary/status/report file that the success criteria then read for evidence. Criteria must check what the agent *did* (commands, real artifacts), not what it *claims* it did.
- **Prompt over-specification (High/Medium/Low).** No step-by-step procedure, no prescribing flags or exact output formats unless they are ground-truth anchors that the criteria assert. Naming a node type that matches a `node:X` tag is fine — that is deliberate scoping.

Keep prompts concise (typically under 3 lines).

### 2e. success_criteria

Pick from the criteria types documented in `tests/README.md` and the coder-eval docs:

| Type | Use for |
|---|---|
| `command_executed` | Agent ran a specific CLI command (regex on tool calls) |
| `command_not_executed` | Agent did NOT run a prohibited command (negative-guard tests) |
| `skill_triggered` | Agent invoked a Claude Code Skill — un-fakeable |
| `file_exists` / `file_contains` / `file_check` | Artifact existence + content |
| `json_check` | JSON structure + JMESPath assertions (operators: `equals`, `gte`, `lte`, `gt`, `lt`, `contains`) |
| `run_command` | Execute a shell command, check exit code (and optionally stdout) |
| `pytest`, `pylint_score`, `file_matches_regex` | Less common; see coder-eval docs |

**Quality bar (from `lint-task.md`):**

- **Meaningful coverage.** At least one criterion must validate output *content*, not just existence. `file_exists` alone or `command_executed` with a loose regex is not enough — pair them with `json_check` / `run_command` stdout / substantive `file_contains`.
- **Could-pass-for-wrong-reason.** Ask: would a dummy implementation that skips the skill entirely satisfy these criteria? If yes, tighten them.
- **Validate-only flow tests.** For e2e tasks tagged `uipath-maestro-flow`, include `command_executed` matching `flow\s+debug` (or document the rationale in `description`). `flow validate` alone checks shape, not correctness.

**Weight scale** (per `tests/README.md`): `1.0` supporting / `1.5` core behavior / `2.0` artifact content / `3.0` primary artifact validity / `5.0–6.0` end-to-end execution. **`pass_threshold`** is usually `1.0` (all-or-nothing).

### 2f. agent / sandbox

`sandbox` is always required:

```yaml
sandbox:
  driver: tempdir
  python: {}
```

Only include `agent:` or `max_iterations` when overriding the experiment defaults for the chosen tier (see `tests/README.md`).

## Phase 3 — File Layout and YAML

### 3a. Directory and filename

Mirror the existing layout for the target skill (groupings under each skill are advisory per `tests/README.md`). Common patterns: `smoke/`, `single_node/`, `multi_node/`, `edit/`, `hitl/`, `connector_features/`, plus per-capability subdirs for e2e tests with sidecar check scripts.

Filenames are `snake_case` (not kebab). E2E tasks with check scripts go in their own capability subdir.

### 3b. YAML structure

```yaml
task_id: <id>
description: >
  <one or two sentences on what the task tests>
tags: [<skill>, <tier>, mode:<X>, ...]

# Top-level overrides — only present when differing from experiment defaults.
# Inheritable fields per tests/README.md: max_iterations, task_timeout,
# max_turns, turn_timeout. As of coder_eval #225, max_turns and turn_timeout
# live at the top level (not inside agent:).
# max_iterations: <N>
# task_timeout: <seconds>
# max_turns: <N>
# turn_timeout: <seconds>
# agent:
#   type: claude-code
#   permission_mode: acceptEdits
#   allowed_tools: ["Skill", "Bash", "Read", ...]

sandbox:
  driver: tempdir
  python: {}
  # Optional — pin Node packages for tasks that drive the uip CLI:
  # node:
  #   env_packages:
  #     - "@uipath/cli@<pinned-version>"

initial_prompt: |
  <goal-stated prompt>

success_criteria:
  - type: <criterion_type>
    description: "<what this checks>"
    ...
    weight: <float>
    pass_threshold: <float>
```

Field order: `task_id`, `description`, `tags`, top-level overrides (`max_iterations`, `task_timeout`, `max_turns`, `turn_timeout`) if any, `agent` (if any), `sandbox`, `initial_prompt`, `success_criteria` — matches existing tests.

### 3c. Check script (e2e only, when needed)

For e2e tasks that need to verify execution output beyond what the built-in criteria cover:

1. Create `tests/tasks/<skill>/<capability>/check_<name>.py` next to the YAML.
2. Follow the pattern from existing check scripts (e.g. `check_calculator_flow.py`):
   - `#!/usr/bin/env python3` + module docstring
   - `sys.exit("FAIL: ...")` on failure, `print("OK: ...")` on success
   - If importing from `tests/tasks/<skill>/_shared/`, use the `sys.path.insert(...)` bootstrap that existing scripts use (the script is invoked as `python3 $TASK_DIR/check_<name>.py`).
3. Wire it into the YAML via `run_command`:
   ```yaml
   - type: run_command
     command: "python3 $TASK_DIR/check_<name>.py"
   ```

Only create a `_shared/` helper if the skill already has one or a second e2e test will reuse the logic. Otherwise keep the check script self-contained.

## Phase 4 — Validation and Summary

### 4a. Validate

1. Re-read the YAML and verify it parses (`python3 -c "import yaml; yaml.safe_load(open('<path>'))"`).
2. Confirm `task_id` is unique against the IDs collected in Phase 1.
3. Confirm tags conform to `tests/README.md#tag-taxonomy`. Note any dimension you omitted because no closed-vocabulary value fit.
4. Self-lint against the six axes in `.claude/commands/lint-task.md` (Self-report, Over-specification, Meaningful coverage, Could pass for wrong reason, Near-duplicate, Validate-only flow). If any axis would raise Medium or above, revise before finishing.
5. For check scripts: `python3 -c "import py_compile; py_compile.compile('<path>', doraise=True)"`.

### 4b. Summary

Tell the user, in your own words, what was generated and what they need to do next. No rigid template — write it to be skimmed. Cover at minimum:

- Which file was written (path), the task_id, the tier, and which skill the description resolved to.
- A one-line description of what the task exercises.
- Anything the author needs to manually verify before trusting the YAML — assumed CLI commands or flags, omitted tag dimensions you couldn't fit into the closed vocabulary, file paths or expected outputs that were guessed, etc. If nothing needs review, say so.

Then — **always, never omit** — a clearly-flagged reminder that the YAML is an unverified scaffold and the author must run it end-to-end with `coder-eval` before merging. Include the exact invocation:

```
cd tests
SKILLS_REPO_PATH=$(cd .. && pwd) \
  .venv/bin/coder-eval run tasks/<skill>/<path>.yaml \
  -e experiments/<tier>.yaml
```

And remind them that the PR description must include an explicit passing-run claim (e.g. `Ran <task-id> locally and it passed.`), because `.github/workflows/lint-tasks.yml` raises a High issue if no such claim is present.

---

## Rules

1. **One task per invocation.** Re-run the command for more. Multiple-task batches bloat review and let unvalidated tasks slip through.
2. **Read the skill thoroughly.** Every SKILL.md, every reference. Prompts and criteria must use real CLI commands and flags from the skill.
3. **Follow existing test patterns.** Read the target skill's existing YAMLs (or a peer skill's if the target has none) to learn agent config, prompt style, criteria patterns, and tier conventions.
4. **Honor the Tag Taxonomy.** Use only values from `tests/README.md#tag-taxonomy`. If no value fits, omit the dimension and flag it under Manual review — never invent tags inline.
5. **Avoid the lint axes.** Self-check against `.claude/commands/lint-task.md` before finalizing. Any Medium-or-above issue means revise.
6. **Minimal prompts.** Describe the goal, not the steps.
7. **Realistic criteria.** Only assert on things that can actually be checked in the sandbox. Don't `command_executed` a command the agent might legitimately not need.
8. **No duplicate task_ids.** Verify against every existing YAML in `tests/tasks/`.
9. **Do not invent CLI commands.** Every `command_pattern` regex and `command` string must come from the skill's documentation.
10. **Do not modify existing files.** This command only creates new files.
11. **Always print the run-with-coder-eval reminder.** The author cannot merge a generated task on push alone — it must be run locally and that fact recorded in the PR description.
