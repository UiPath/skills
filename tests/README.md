# Skill Evaluation Tests

Tests that verify AI agents can correctly use skills from this repository. Tests are defined as [coder_eval](https://github.com/UiPath/coder_eval) task YAML files.

## Prerequisites

1. **UiPath private PyPI credentials** (optional) — only needed if `coder-eval` resolves to packages on the UiPath Azure DevOps `ml-packages` feed. Export these **before** running `make install` to enable the private feed:
   ```bash
   export UV_INDEX_UIPATH_USERNAME=<your-ado-username>
   export UV_INDEX_UIPATH_PASSWORD=<your-ado-pat>
   ```
   The Makefile composes these into `UV_EXTRA_INDEX_URL` for `uv pip install`. If either variable is empty, install continues against public PyPI only and prints a notice.

2. **coder-eval** — install from GitHub (creates a local `.venv`, requires Python 3.13+):
   ```bash
   cd tests
   make install
   ```

3. **uip CLI** — the UiPath CLI must be available:
   ```bash
   npm install -g @uipath/cli
   ```

4. **Environment setup** — API keys and other environment variables are required. See the [coder_eval README](https://github.com/UiPath/coder_eval) for environment setup (`.env`, API keys, etc.).

## Running Tests

```bash
cd tests

# Run all tests (smoke + integration + e2e)
make all

# Run all smoke tests
make smoke

# Run all integration tests
make integration

# Run all e2e tests
make e2e

# Run tests matching a combination of tags (AND semantics — tasks must carry all listed tags) (defaults to experiments/default.yaml):
make tags TAGS="integration connector-feature"
# Optionally override the experiment config 
make tags TAGS="integration connector-feature" EXPERIMENT=experiments/integration.yaml

# Run all tests for a specific skill
make test-uipath-maestro-flow

# Run a single task file
SKILLS_REPO_PATH=$(cd .. && pwd) \
  .venv/bin/coder-eval run tasks/uipath-maestro-flow/smoke/init_validate.yaml \
  -e experiments/default.yaml
```

The `SKILLS_REPO_PATH` environment variable defaults to the parent directory (repo root) when using `make`.

## Evaluation Framework

Tests are organized into three types, distinguished by **tags** (not directories). All tests for a skill live together in `tests/tasks/<skill-name>/`.

| Tag | Purpose | Cadence |
|-----|---------|---------|
| `smoke` | Skill triggers correctly, CLI produces valid output (1-5 simple scenarios) | Every PR |
| `integration` | Correct output across diverse scenarios, error paths, anti-patterns | Daily |
| `e2e` | Full lifecycle: Explore -> Plan -> Build -> Validate -> Deploy -> Run | Daily/weekly (check [Dashboard](https://dataexplorer.azure.com/dashboards/20cc55fe-33ae-4973-a951-855e76528219))|

## Tag Taxonomy

Tags drive `make` targets, coverage reports, and evalboard drilldown. The `tags:` list is a flat array of strings; most tag values carry a namespace prefix in `key:value` form so each dimension is independently queryable (e.g. `where tag startswith "connector:"` in ADX). Required tags are flat (no prefix) so existing `--tags` filters keep working.

| Dimension | Form | Purpose | Values |
|---|---|---|---|
| **skill** | flat, required | Skill under test | `uipath-<name>` — must match the skill folder (e.g. `uipath-maestro-flow`) |
| **tier** | flat, required | Test depth / cost | `smoke`, `integration`, `e2e` |
| **lifecycle** | `lifecycle:X`, required | What the agent is asked to do | `generate`, `edit`, `validate`, `discover`, `activate`, `execute`, `deploy` |
| **shape** | `shape:X`, optional | Flow composition under test | `single-node`, `multi-node` (omit for smoke tests that don't build a flow) |
| **node** | `node:X`, repeatable | Node type(s) under test | `decision`, `switch`, `subflow`, `terminate`, `loop`, `transform`, `hitl` (omit `script`/`http` — ubiquitous) |
| **resource** | flat, present iff applicable | Marks tasks that exercise any resource-node type (`coded-agent`, `lowcode-agent`, `api-workflow`, `rpa`). The specific resource is implied by the file path / `task_id`. |
| **connector** | flat, present iff applicable | Marks tasks that use any IS connector. The specific connector is in the YAML body / file path. |
| **feature** | `feature:X`, repeatable | Cross-cutting capability orthogonal to node/resource/connector. Closed vocabulary: `http`, `trigger`, `registry`, `transform`, `approval-gate`, `write-back`, `escalation`, `connections`, `activities`, `records`, `entities`, `api-workflow`, `compliance`, `test-case`, `hooks`. Do not invent leaf names like `feature:ceql-where` or directory-name markers like `feature:connector-feature` — those duplicate the file path. |

### Rules

1. **Required on every task: `skill` + `tier` + `lifecycle:*`.** These drive `make` targets, coverage, and evalboard dashboards.
2. **One value per singular dimension** (`tier`, `lifecycle`, `shape`). A task doesn't have two tiers.
3. **`node:` and `feature:` are repeatable.** A flow exercising decision and switch nodes gets both `node:decision` and `node:switch`.
4. **`connector` and `resource` are flat boolean markers**, not enumerations. Use them once per task; the specific connector/resource is identifiable from the file path, `task_id`, or YAML body. Adding `connector:slack` etc. is no longer the convention.
5. **Use only the vocabularies above.** Propose new values in the PR — do not invent tags inline. New values should apply to at least two tasks in practice.
6. **Don't repeat the skill name as a feature tag.** Don't tag a flow task with `rpa` (bare) or `uipath-rpa` as a feature.

### Example

```yaml
tags: [uipath-maestro-flow, e2e, lifecycle:generate, shape:multi-node, node:decision, connector, feature:http]
```

### Useful slices this enables

- `make tags TAGS="smoke"` → every skill's entry-gate checks.
- `make tags TAGS="integration connector"` → connector coverage across skills.
- `make tags TAGS="e2e lifecycle:generate"` → end-to-end authoring from scratch, across skills.
- `make tags TAGS="lifecycle:edit"` → modification-on-existing-project behavior.
- Evalboard: `where tag == "connector"` → pass-rate across all connector-using tasks.
- Evalboard: `where tag == "shape:multi-node"` → composite-flow reliability.

## Directory Structure

```
tests/
├── README.md
├── Makefile
├── experiments/
│   ├── default.yaml              # Smoke config
│   ├── integration.yaml          # Integration config (longer timeouts)
│   └── e2e.yaml                  # E2E config (staging tenant, full lifecycle)
├── tasks/
│   └── <skill-name>/             # One folder per skill (must match skills/<name>/)
│       ├── _shared/              # Optional — helpers, cleanup scripts, per-skill pytest
│       ├── smoke/                # Tier: smoke
│       ├── single_node/          # Tests isolating a single node type (optional)
│       ├── multi_node/           # Composite-flow tests (optional)
│       ├── edit/                 # lifecycle:edit tests (optional)
│       └── <other>/              # Skill-specific groupings (e.g. hitl/, connector_features/)
└── reports/                      # Generated by /test-coverage command
    ├── <skill-name>.md           # Per-skill coverage report
    └── SUMMARY.md                # Cross-skill roll-up (when analyzing all)
```

Groupings under a skill are advisory — pick the ones that map to how the skill is exercised. The flow skill uses `smoke/`, `single_node/`, `multi_node/`, `edit/`, `hitl/`, `connector_features/`. Keep dir names short and kebab-case; put only one task YAML per leaf dir (plus its sidecar check scripts).

## Experiment Configs

Experiment files define shared agent defaults per test type. Tasks inherit these defaults and should only override what differs.

| Experiment | Used by | max_iterations | max_turns | task_timeout | turn_timeout |
|------------|---------|----------------|-----------|--------------|--------------|
| `default.yaml` | Smoke | 1 | 20 | 600s | 300s |
| `integration.yaml` | Integration | 2 | 30 | 900s | 300s |
| `e2e.yaml` | E2E | 2 | 40 | 1200s | 300s |

For **A/B comparisons between two skill variants** (e.g. `main` vs a feature branch, or two historical commits), see [`experiments/skill-comparison-playbook.md`](experiments/skill-comparison-playbook.md) and the [`experiments/skill-comparison-template.yaml`](experiments/skill-comparison-template.yaml). The playbook covers worktree setup, SHA pinning for reproducibility, getting N>1, and interpreting divergent tasks. To automate the whole flow, use the `/skill-compare <ref_a> <ref_b> [task_selector] [n_reps]` slash command — each ref can be a branch name or a commit SHA, and `task_selector` accepts a skill name (`uipath-maestro-flow`), tag list (`tags:smoke,init`), or path globs (`paths:tasks/uipath-maestro-flow/*.yaml`).

Task files should **not** duplicate the full `agent:` block — the experiment provides the defaults. Only specify fields that differ from the experiment:

```yaml
# Good — no agent block needed when everything matches the experiment defaults
task_id: skill-flow-init-validate
tags: [uipath-maestro-flow, smoke, init, validate]

sandbox:
  driver: tempdir
  python: {}

initial_prompt: |
  ...

# Good — only override what differs (max_turns: 14 instead of the default 20)
task_id: skill-flow-registry-discovery
tags: [uipath-maestro-flow, smoke, registry]

agent:
  type: claude-code
  max_turns: 14

sandbox:
  driver: tempdir
  python: {}

initial_prompt: |
  ...
```

## Adding Tests for a New Skill

1. Create `tests/tasks/<skill-name>/` matching the skill folder name under `skills/`.
2. Add at minimum **1 smoke test** and **1 e2e test** (required for every new skill PR).
3. Use minimal prompts — the goal is to test whether the skill guides the agent correctly, not to hand-hold it.
4. Tag every task using the [Tag Taxonomy](#tag-taxonomy): required `skill` + `tier`, plus `lifecycle`, `scenario`, and `feature` where applicable.
5. Stick to the closed-vocabulary values. Propose new tags in the PR — do not invent them inline.

### Task ID Convention

```
skill-<domain>-<capability>
```

Examples: `skill-flow-init-validate`, `skill-flow-registry-discovery`

### Smoke Test Example

This is `tasks/uipath-maestro-flow/smoke/init_validate.yaml` — a smoke test that verifies the agent can create and validate a Flow project:

```yaml
task_id: skill-flow-init-validate
description: >
  Skill-guided evaluation: agent uses the uipath-maestro-flow skill to create
  a new UiPath Flow project inside a solution and validate it. Tests whether
  the skill teaches the correct solution-first workflow and CLI usage.
tags: [uipath-maestro-flow, smoke, init, validate]

sandbox:
  driver: tempdir
  python: {}

initial_prompt: |
  Create a new UiPath Flow project called "WeatherAlert" and make sure it
  validates successfully.

  Save a summary of what you did to report.json with at minimum:
    {
      "project_name": "WeatherAlert",
      "commands_used": ["<list of uip commands you ran>"],
      "validation_passed": true
    }

  Important:
  - The `uip` CLI is already available in the environment.
  - Do not run `uip maestro flow debug` — just validate locally.

success_criteria:
  - type: command_executed
    description: "Agent created a solution with uip solution new"
    tool_name: "Bash"
    command_pattern: 'uip\s+solution\s+new'
    min_count: 1
    weight: 1.5
    pass_threshold: 1.0

  - type: command_executed
    description: "Agent initialized a Flow project with uip maestro flow init"
    tool_name: "Bash"
    command_pattern: 'uip\s+(maestro\s+)?flow\s+init'
    min_count: 1
    weight: 1.5
    pass_threshold: 1.0

  - type: command_executed
    description: "Agent validated the .flow file"
    tool_name: "Bash"
    command_pattern: 'uip\s+(maestro\s+)?flow\s+validate'
    min_count: 1
    weight: 1.5
    pass_threshold: 1.0

  - type: command_executed
    description: "Agent used --output json on uip commands"
    tool_name: "Bash"
    command_pattern: 'uip\s+.*--output\s+json'
    min_count: 1
    weight: 1.0
    pass_threshold: 1.0

  - type: command_executed
    description: "Agent linked flow project to solution"
    tool_name: "Bash"
    command_pattern: 'uip\s+solution\s+project\s+add'
    min_count: 1
    weight: 1.0
    pass_threshold: 1.0

  - type: file_exists
    description: "Flow file was created inside the solution"
    path: "WeatherAlert/WeatherAlert/WeatherAlert.flow"
    weight: 1.5
    pass_threshold: 1.0

  - type: json_check
    description: "report.json has correct structure and values"
    path: "report.json"
    assertions:
      - expression: "project_name"
        operator: equals
        expected: "WeatherAlert"
      - expression: "validation_passed"
        operator: equals
        expected: true
      - expression: "length(commands_used)"
        operator: gte
        expected: 3
    weight: 2.0
    pass_threshold: 0.75
```

Key patterns to note:
- **No `agent:` block** — inherits everything from `experiments/default.yaml`
- **No `max_iterations` or `llm_reviewer`** — inherited from the experiment config
- **Minimal prompt** — describes the goal ("create and validate"), not the steps
- **Multiple criteria types** — `command_executed`, `file_exists`, `json_check` cover different aspects
- **Weighted scoring** — core commands (`weight: 1.5`) matter more than supporting checks (`weight: 1.0`)

For another example using `file_contains` and `run_command` criteria, see `tasks/uipath-maestro-flow/smoke/registry_discovery.yaml`. That test also demonstrates overriding a single field (`agent: max_turns: 14`) from the experiment defaults.

## Success Criteria Reference

Each task defines one or more success criteria. The agent's score is the weighted sum of passing criteria.

### `command_executed`

Verify the agent ran a specific CLI command (matched by regex). From `init_validate.yaml`:

```yaml
- type: command_executed
  description: "Agent created a solution with uip solution new"
  tool_name: "Bash"
  command_pattern: 'uip\s+solution\s+new'
  min_count: 1          # minimum times the command must appear
  weight: 1.5           # scoring weight
  pass_threshold: 1.0   # fraction of min_count required to pass
```

### `file_exists`

Verify a file was created in the sandbox. From `init_validate.yaml`:

```yaml
- type: file_exists
  description: "Flow file was created inside the solution"
  path: "WeatherAlert/WeatherAlert/WeatherAlert.flow"
  weight: 1.5
  pass_threshold: 1.0
```

### `file_contains`

Verify a file contains (or excludes) expected strings. **Score real artifacts the agent produced — not files the agent self-reported into.** From `uipath-maestro-flow/hitl/smoke_01_hitl_node_placed.yaml`:

```yaml
- type: file_contains
  description: "Flow contains the inline HITL node type"
  path: "InvoiceApproval/InvoiceApproval/InvoiceApproval.flow"
  includes:
    - '"uipath.human-in-the-loop"'
  weight: 3.0
  pass_threshold: 1.0
```

`excludes:` is also supported — useful for asserting a CSV header excludes system fields or that a generated command doesn't reference a deprecated flag.

### `json_check`

Validate JSON file structure and values using JMESPath assertions. **Score the agent's actual JSON output (a generated config, schema, or fixture) — not a self-described status report.** Counter-example to avoid:

```yaml
# ❌ ANTIPATTERN — agent writes "validation_passed: true" to a summary file
# and the criterion reads it back. The agent could lie. See "Anti-patterns" below.
- type: json_check
  path: "report.json"
  assertions:
    - expression: "validation_passed"
      operator: equals
      expected: true
```

✅ Better — verify the underlying state directly with `run_command`:

```yaml
- type: run_command
  description: "uip flow validate passes against the authored .flow"
  command: "uip maestro flow validate Project/Project/Project.flow --output json"
  timeout: 30
  expected_exit_code: 0
```

`json_check` is fine when the JSON file is itself the genuine artifact (e.g. a generated schema). Supported operators: `equals`, `gte`, `lte`, `gt`, `lt`, `contains`.

### `run_command`

Execute an arbitrary shell command and check the exit code. Use it for direct verification of state the agent created. From `uipath-data-fabric/integration_csv_import.yaml`:

```yaml
- type: run_command
  description: "inventory.csv has at least 4 data rows (header + 4)"
  command: "awk 'END { exit (NR >= 5 ? 0 : 1) }' inventory.csv"
  timeout: 5
  expected_exit_code: 0
  weight: 2.0
  pass_threshold: 1.0
```

Or byte-equality for upload/download round-trips:

```yaml
- type: run_command
  description: "Downloaded file is byte-identical to the original"
  command: "cmp -s original.txt downloaded.txt"
  timeout: 5
  expected_exit_code: 0
```

### `skill_triggered`

Verify the agent invoked a Claude Code Skill tool. Useful for "did the agent recognize this scenario calls for skill X?" Supports positive (`expected: "yes"`) and negative (`expected: "no"`) assertions:

```yaml
- type: skill_triggered
  description: "Agent invoked the uipath-human-in-the-loop skill"
  skill_name: "uipath-human-in-the-loop"
  expected: "yes"
  weight: 3.0
  pass_threshold: 1.0
```

Un-fakeable — the criterion inspects `turn_records.commands` directly. The negative form (`expected: "no"`) is the right primitive for smoke tests where the agent should NOT trigger a particular skill.

### `command_not_executed`

Counterpart to `command_executed`. Verifies the agent did NOT run a prohibited command. Use for refusal / negative-guard tests:

```yaml
- type: command_not_executed
  description: "Agent must not delete an entity"
  tool_name: "Bash"
  command_pattern: 'uip\s+df\s+entities\s+delete'
  weight: 3.0
  pass_threshold: 1.0
```

Score is binary: 1.0 when matches ≤ `max_count` (default `0`), else 0.0. Empty `turn_records` → trivially passes.

## Anti-patterns to avoid

The most common failure mode for new tests is the **self-report antipattern**: the prompt asks the agent to write a summary file (`report.json`, `recommendation.json`, `summary.json`, …) and the success criteria reads that file back. The agent can write whatever it wants in the summary, so the test scores the agent's *claim* about what it did rather than what it actually did.

```yaml
# ❌ DO NOT WRITE TESTS LIKE THIS
initial_prompt: |
  ... do the work ...

  Save a summary to report.json:
  {
    "validation_passed": <true or false>,
    "records_inserted": <count>,
    "import_succeeded": <true or false>
  }

success_criteria:
  - type: json_check
    path: "report.json"
    assertions:
      - expression: "validation_passed"
        operator: equals
        expected: true
      - expression: "records_inserted"
        operator: gte
        expected: 4
```

A misbehaving agent passes this test by writing the right strings into `report.json` regardless of whether the underlying work happened. To verify behavior instead of self-description, use:

| Want to verify… | Use this criterion |
|---|---|
| Agent invoked the right skill | `skill_triggered` (positive or negative) |
| Agent ran the right CLI command | `command_executed` |
| Agent did NOT run a prohibited command | `command_not_executed` |
| A real artifact (`.flow`, `.csv`, `.md`) was produced correctly | `file_contains` / `file_matches_regex` on the artifact |
| A real operation succeeded (validate, hash equality, row count) | `run_command` running the verification directly |

`json_check` and `file_contains` on agent-written summaries are only OK when the file genuinely is the deliverable — e.g. a schema-design task where the agent's JSON output is *itself* the artifact under evaluation. In every other case, prefer one of the criteria above.

## Weight and Threshold Guidance

**`weight`** controls how much a criterion contributes to the overall score. Use higher weights for the core behavior being tested:

| Weight | When to use | Example from existing tests |
|--------|-------------|---------------------------|
| `1.0` | Supporting checks | `--output json` flag used, presence of an auxiliary file |
| `1.5` | Core behavior | `uip solution new` executed, `.flow` file created |
| `2.0` | Important artifact content | `.flow` file contains the expected node type or handle wiring |
| `3.0` | Primary artifact validity | `uip maestro flow validate` passes on the generated flow file |
| `5.0–6.0` | End-to-end execution | Check script runs `flow debug` and verifies output correctness |

**`pass_threshold`** is the fraction of the criterion that must pass. For `json_check` with multiple assertions, `0.75` means 75% of assertions must pass. For most criteria, use `1.0` (all-or-nothing).

## Interpreting Results

After a run, results are written to `tests/runs/<experiment-id>/`:

```
runs/
└── <experiment-id>/
    ├── experiment.md           # Overall summary
    └── default/
        ├── variant.md          # Variant-level summary
        └── <task-id>/
            └── task.json       # Detailed per-task results
```

- **`experiment.md`** — high-level pass/fail summary across all tasks
- **`task.json`** — per-criterion scores, agent transcript, and LLM reviewer output

## Debugging Failures

1. **Read the task result:**
   ```bash
   cat runs/*/default/skill-flow-init-validate/task.json | python -m json.tool
   ```

2. **Check which criteria failed:** Look at the `success_criteria` array in `task.json` — each entry has a `passed` boolean and `score`.

3. **Read the agent transcript:** The `transcript` field in `task.json` shows every agent turn, tool call, and tool result.

4. **Re-run a single task with verbose output:**
   ```bash
   SKILLS_REPO_PATH=$(cd .. && pwd) \
     .venv/bin/coder-eval run tasks/uipath-maestro-flow/smoke/init_validate.yaml \
     -e experiments/default.yaml -v
   ```

5. **Common failure causes:**
   - Agent used wrong CLI command or flags -> check the skill's SKILL.md for correctness
   - Agent didn't activate the skill -> check skill description frontmatter and smoke test
   - Agent ran out of turns -> increase `max_turns` or simplify the prompt
   - Sandbox issue -> check that `uip` CLI is available in the test environment

## Test Coverage Analysis

Use the `/test-coverage` slash command to generate a coverage report that maps what a skill teaches against what its tests verify:

```bash
# Analyze a single skill
/test-coverage uipath-maestro-flow

# Analyze all skills
/test-coverage all
```

Reports are written to `tests/reports/<skill-name>.md` and include:
- Component, workflow step, critical rule, and anti-pattern coverage (Direct/Indirect/None)
- Weighted overall score
- Priority-ranked coverage gaps with concrete test recommendations

The command is defined in [`.claude/commands/test-coverage.md`](../.claude/commands/test-coverage.md).

### Generating Test Tasks

Use the `/generate-tasks` slash command to scaffold new test tasks based on coverage gaps:

```bash
/generate-tasks uipath-platform                      # highest-priority gaps
/generate-tasks uipath-platform authentication        # specific focus area
/generate-tasks uipath-maestro-flow smoke             # specific test tier
```

This generates task YAML files (and optional check scripts) in `tests/tasks/<skill-name>/`. Generated tasks are **starting points for reference only** — review and improve them before relying on them for CI. In particular, verify that CLI commands, success criteria, and prompts match the skill's actual behavior.

The command is defined in [`.claude/commands/generate-tasks.md`](../.claude/commands/generate-tasks.md).

## Further Reading

- [coder_eval repository](https://github.com/UiPath/coder_eval) — framework docs, task definition guide, CLI reference
- [CONTRIBUTING.md](../CONTRIBUTING.md) — skill contribution rules and quality checklist
