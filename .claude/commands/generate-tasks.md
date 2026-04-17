# Generate Test Tasks

Generate coder_eval task YAML files (and optional check scripts) to increase test coverage for a skill.

**Input:** `$ARGUMENTS`
- `<skill-name>` — generate tasks for highest-priority coverage gaps (e.g., `uipath-platform`)
- `<skill-name> <focus>` — target specific areas (e.g., `uipath-platform authentication and folder listing`)
- `<skill-name> <test-type>` — generate only that tier (e.g., `uipath-maestro-flow smoke`)

**Argument precedence.** After the skill name, if everything remaining is exactly one of `smoke`, `integration`, or `e2e`, treat it as `<test-type>`. Otherwise, treat the entire remainder (one or more whitespace-separated words) as a free-form `<focus>` description. To combine a focus area with a test-type filter, include the tier word inside the focus string (e.g., `uipath-platform smoke tests for authentication`) — this will be parsed as a focus since it contains more than just the tier keyword.

**Output:** Task YAML files (+ optional `check_*.py` scripts) in `tests/tasks/<skill-name>/`.

---

## Phase 1 — Context Gathering

1. Parse `$ARGUMENTS`: extract skill name, optional focus area or test-type filter (`smoke`, `integration`, `e2e`).
2. Verify `skills/<skill-name>/SKILL.md` exists. If not, list available skills under `skills/uipath-*/` and fail with an error.
3. Read the skill's SKILL.md and every file in `references/` and `assets/`. This is required to write prompts and criteria that use correct CLI commands, flags, and project structures.
4. Check for an existing coverage report at `tests/reports/<skill-name>.md`.
   - If it exists: read and extract the "Coverage Gaps — Priority Ranked" and "Recommendations" sections. These drive task selection.
   - If not: do a lightweight gap analysis inline — inventory the skill's components, workflow steps, and critical rules, then identify what has no test coverage.
5. Read all existing `*.yaml` task files in `tests/tasks/` across all skills. This serves three purposes:
   - Collect all `task_id` values repo-wide to prevent collisions.
   - Learn conventions from the target skill's existing tests (agent config, prompt style, criteria types, weight scales).
   - If the target skill has no existing tests, learn conventions from other skills' tests.
6. Read the experiment configs to know inherited agent config per test type. Generated tasks should only override fields that differ from these defaults:
   - Smoke → `tests/experiments/default.yaml`
   - Integration → `tests/experiments/integration.yaml`
   - E2E → `tests/experiments/e2e.yaml`

For multi-file reads, use parallel tool calls or Explore agents to speed up context gathering.

## Phase 2 — Task Design

Select coverage gaps to address. If the user provided a focus area, filter to that area. Otherwise, prioritize by the coverage report's "High Priority" gaps. Generate 2–5 tasks per invocation by default, focusing on highest coverage impact. Always generate at least 1 smoke + 1 e2e if the skill has zero tests (minimum bar per CONTRIBUTING.md).

For each gap, design a task:

### 2a. Choose test type

| Signal | Test type |
|--------|-----------|
| CLI command produces correct output, report generation | smoke |
| Multi-step workflow with error handling, cross-component integration | integration |
| Full build -> validate -> run lifecycle, artifact correctness | e2e |

### 2b. Choose task_id

Convention: `skill-<domain>-<capability>`

Domain mapping:

| Skill | Domain |
|-------|--------|
| uipath-maestro-flow | flow |
| uipath-platform | platform |
| uipath-agents | agent |
| uipath-rpa | rpa |
| uipath-servo | servo |
| uipath-coded-apps | codedapp |
| uipath-diagnostics | diagnostics |
| uipath-feedback | feedback |
| uipath-planner | planner |
| uipath-human-in-the-loop | hitl |
| uipath-case-management | case |

If a skill is not listed, derive `<domain>` by stripping the `uipath-` prefix and using the shortest unambiguous segment (e.g., `uipath-new-thing` → `newthing`). Check existing `task_id` values for the skill's domain prefix and follow suit.

Verify the chosen `task_id` does not appear in any existing task YAML (collected in Phase 1 step 5).

### 2c. Write initial_prompt

General principles:
1. Describe the GOAL, not the steps — the skill teaches the steps, and that is what we are testing.
2. Keep prompts concise (under 3 lines), just like a human developer would write it.
3. Include specific inputs/outputs when the test needs to verify correctness (e.g., "takes two numbers as input and calculates their product").

**Learn the prompt style from existing tests.** Read all existing task YAMLs for the skill (and for other skills if this skill has none yet) to pick up the conventions currently in use — what instructions are included, how skill loading is handled, what constraints are specified. Mirror those conventions in the generated prompts rather than inventing new patterns.

### 2d. Design success criteria

**Learn from existing tests.** Read the criteria patterns used in existing task YAMLs (collected in Phase 1 step 5–6) and use the same criterion types, weight scales, and threshold values for the same tier of test.

Available criterion types (from coder_eval):

| Type | What it checks | Typical use |
|------|---------------|-------------|
| `command_executed` | Agent ran a specific CLI command (regex match on tool calls) | Smoke: verify CLI workflow steps |
| `file_exists` | A file was created at a path | Smoke/e2e: verify artifact creation |
| `file_contains` | A file contains expected strings | Smoke: verify report content |
| `json_check` | JSON structure and values via JMESPath assertions | Smoke: verify structured output |
| `run_command` | Execute a shell command, check exit code (and optionally stdout) | E2E: run validation tools, run check scripts |

Operators for `json_check` assertions: `equals`, `gte`, `lte`, `gt`, `lt`, `contains`.

**Criteria must be verifiable.** Only assert on things that can actually be checked in the sandbox. Do not assert on cloud-dependent state if the test is local-only. Do not use `command_executed` for commands the agent might not need to run.

### 2e. Configure agent and sandbox

**Learn from existing tests.** Read the experiment configs and existing task YAMLs to determine what needs to be specified vs. what can be inherited. Only include `agent:` and `max_iterations` fields when they differ from the experiment defaults for the chosen test type.

The `sandbox` block is always required:

```yaml
sandbox:
  driver: tempdir
  python: {}
```

The `agent:` block and `max_iterations` should only appear when overriding experiment defaults — check what existing tests for the same tier do and follow suit.

## Phase 3 — Generation

### 3a. File organization

Task filenames use `snake_case` (e.g., `init_validate.yaml`, `login_status.yaml`), not kebab-case. This differs from reference files which use kebab-case.

| Test type | File location | Example |
|-----------|---------------|---------|
| Smoke | `tests/tasks/<skill>/capability.yaml` (top-level) | `tests/tasks/uipath-platform/login_status.yaml` |
| E2E | `tests/tasks/<skill>/capability/capability.yaml` (subdirectory) | `tests/tasks/uipath-platform/folders_list/folders_list.yaml` |

Create the `tests/tasks/<skill-name>/` directory if it does not exist.

### 3b. Generate task YAML files

Write YAML files following the field ordering observed in existing tests. A typical structure:

```yaml
task_id: <id>
description: >
  <multi-line description of what the task tests>
tags: [<skill-name>, <test-type>, ...]

# Only include fields below when overriding experiment defaults:
# max_iterations: <N>
# agent:
#   type: claude-code
#   ...

sandbox:
  driver: tempdir
  python: {}

initial_prompt: |
  <prompt text>

success_criteria:
  - type: <criterion_type>
    description: "<what this criterion checks>"
    ...
    weight: <float>
    pass_threshold: <float>
```

Field ordering must match existing tests: `task_id`, `description`, `tags`, `max_iterations` (if present), `agent` (if present), `sandbox`, `initial_prompt`, `success_criteria`.

### 3c. Generate check scripts (e2e only)

When an e2e test needs a check script (to verify artifact execution or complex output):

1. Create `tests/tasks/<skill-name>/<capability>/check_<name>.py` in the same subdirectory as the task YAML.
2. Follow the pattern from existing check scripts (e.g., `check_calculator_flow.py`):
   - Shebang: `#!/usr/bin/env python3`
   - Module docstring explaining what it checks
   - Use `sys.exit("FAIL: ...")` on failure
   - Use `print("OK: ...")` on success
   - If importing from `tests/tasks/<skill-name>/_shared/`, first add the skill task directory (the parent of the check script's directory) to `sys.path`, because the script is run as `python3 $TASK_DIR/check_<name>.py`. Use the bootstrap pattern already used by existing scripts such as `check_calculator_flow.py`:
     ```python
     import os
     import sys

     sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
     from _shared.<module> import <name>  # noqa: E402
     ```
   - If the skill has no `_shared` helpers, write standalone checks instead.
3. Reference the script in the task YAML using `$TASK_DIR`:
   ```yaml
   - type: run_command
     command: "python3 $TASK_DIR/check_<name>.py"
   ```

### 3d. Generate `_shared/` helpers (only if needed)

Only create `tests/tasks/<skill-name>/_shared/` if:
- Multiple e2e tests will share validation logic for this skill
- The skill has a common artifact format that needs parsing

For skills without a common artifact format, keep check scripts self-contained. If the skill already has a `_shared/` directory, import from it.

## Phase 4 — Validation and Summary

### 4a. Validate generated files

For each generated YAML file:
1. Read the file back and verify the YAML structure is correct (proper indentation, no unescaped colons in values, matching quotes). If `pyyaml` is available, run `python3 -c "import yaml; yaml.safe_load(open('<path>'))"` as an additional check.
2. Verify `task_id` is unique across all existing task YAMLs in the repo.
3. Verify `tags` array includes the skill name as first element and test type as second.
4. Verify `sandbox.driver` is set to `tempdir`.
5. Verify file paths in `success_criteria` are consistent with what `initial_prompt` asks the agent to create.
6. For check scripts: verify they are syntactically valid Python (`python3 -c "import py_compile; py_compile.compile('<path>', doraise=True)"`).

### 4b. Print summary

After generating all files, print a summary:

```
## Generated Tasks

| File | Task ID | Type | Gaps Covered |
|------|---------|------|--------------|
| tests/tasks/<skill>/foo.yaml | skill-x-foo | smoke | Component A, Component B |
| tests/tasks/<skill>/bar/bar.yaml | skill-x-bar | e2e | Full lifecycle |

Infrastructure notes:
- All generated tests require: <requirements from coverage report>
- To run: make test-<skill-name>
```

---

## Rules

1. **Read the skill thoroughly.** Every SKILL.md, every reference file. Generated prompts must use correct CLI commands, flags, project structures, and naming conventions from the skill.
2. **Follow existing test patterns.** Read existing task YAMLs (both for the target skill and other skills) to learn current conventions for agent config, prompt style, and criteria patterns. Mirror those conventions rather than hardcoding assumptions that may become stale.
3. **Minimal prompts.** Describe goals, not steps. The skill teaches the steps — that is what we are testing.
4. **Realistic criteria.** Only assert on things that can actually be checked in the sandbox. Do not assert on cloud state if the test runs locally. Do not use `command_executed` for commands the agent might not need to run.
5. **No duplicate task_ids.** Check all existing YAMLs across all skills before generating.
6. **Respect infrastructure limits.** Note what each generated test requires (cloud auth, Windows, Servo CLI, etc.). Prefer local-only tests when possible — they are cheaper and can run in CI.
7. **Generate 2–5 tasks per invocation by default.** Focus on highest coverage impact from the gap analysis. The user can run the command again for more. Always generate at least 1 smoke + 1 e2e if the skill has zero tests (minimum bar from CONTRIBUTING.md).
8. **Lean on coverage reports.** If `tests/reports/<skill>.md` exists, use its prioritized gap list directly rather than re-analyzing the skill from scratch.
9. **Do not invent CLI commands.** Every `command_pattern` regex and `command` string must come from the skill's documentation. If unsure whether a command exists, read the skill's references to verify.
10. **Do not modify existing files.** This command only creates new files. It does not edit existing task YAMLs, skill files, or experiment configs.
