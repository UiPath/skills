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

   > **Do not add `@uipath/cli` to `sandbox.node.env_packages` in task YAMLs.** The GH smoke runner installs it globally before any task runs. Listing it in `env_packages` is redundant and, when pinned to a version, causes skew against the runner's `@latest` install.

4. **Environment setup** — API keys and other environment variables are required. See the [coder_eval README](https://github.com/UiPath/coder_eval) for environment setup (`.env`, API keys, etc.).

## Running Tests

> **Platform-specific sandbox driver:**
> - **Linux smoke tests** use `driver: docker` for better isolation. Build the Docker image once before running:
>   ```bash
>   cd .coder_eval
>   make docker-image
>   cd ../tests
>   ```
> - **Windows RPA tests** use `driver: tempdir` (Docker image not available on Windows runner).

```bash
cd tests

# Run everything under the default config (full lifecycle, longest budget)
make all

# Run smoke tests (Linux, fast PR-gate budget)
make smoke

# Run Windows RPA smoke tests (tempdir)
make smoke_rpa

# Run e2e-tagged tests under the default config
make e2e

# Run tests matching a combination of tags (AND semantics — tasks must carry all listed tags) (defaults to experiments/default.yaml):
make tags TAGS="integration connector-feature"
# Optionally override the experiment config 
make tags TAGS="integration connector-feature" EXPERIMENT=experiments/smoke.yaml

# Run all tests for a specific skill
make test-uipath-maestro-flow

# Run a single task file
SKILLS_REPO_PATH=$(cd .. && pwd) \
  .venv/bin/coder-eval run tasks/uipath-maestro-flow/smoke/init_validate.yaml \
  -e experiments/default.yaml
```

The `SKILLS_REPO_PATH` environment variable defaults to the parent directory (repo root) when using `make`.

### Parallelism

All `make` targets run tasks serially by default (`-j 1`). Override with `TASK_PARALLELISM`:

```bash
# Run smoke tests with 4 tasks in parallel
TASK_PARALLELISM=4 make smoke

# Or export once for the shell session
export TASK_PARALLELISM=4
make all
```

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
| **mode** | `mode:X`, required | Coding Agents Scorecard mode | `build` (creating, designing, editing, deploying), `operate` (running, triggering, managing live instances/connectors/integrations), `diagnose` (investigating faults, inspecting traces, debugging) |
| **lifecycle** | `lifecycle:X`, required | Coding Agents Scorecard lifecycle phase | `discover` (read-only exploration: list/get/inspect existing state), `generate` (produce a new local artifact: pack, scaffold, render), `setup` (mutate tenant state: create/edit/delete resources, deploy, configure) |
| **shape** | `shape:X`, optional | Flow composition under test | `single-node`, `multi-node` (omit for smoke tests that don't build a flow) |
| **node** | `node:X`, repeatable | Node type(s) under test | `decision`, `switch`, `subflow`, `terminate`, `loop`, `transform`, `hitl`, `inline-agent` (omit `script`/`http` — ubiquitous) |
| **resource** | flat, present iff applicable | Marks tasks that exercise any resource-node type (`coded-agent`, `lowcode-agent`, `api-workflow`, `rpa`). The specific resource is implied by the file path / `task_id`. |
| **connector** | flat, present iff applicable | Marks tasks that use any IS connector. The specific connector is in the YAML body / file path. |
| **windows** | flat, present iff applicable | Marks tasks that require a Windows host (e.g. RPA `.xaml`/`.cs` projects that need Studio Helm). Used by `smoke-rpa-skills.yml` to route the task to a `windows-latest` runner; Linux/macOS smoke runs skip it. |
| **feature** | `feature:X`, repeatable | Cross-cutting capability orthogonal to node/resource/connector. Closed vocabulary: `http`, `trigger`, `registry`, `transform`, `eval`, `approval-gate`, `write-back`, `escalation`, `connections`, `activities`, `records`, `entities`, `api-workflow`, `compliance`, `test-case`, `hooks`. Do not invent leaf names like `feature:ceql-where` or directory-name markers like `feature:connector-feature` — those duplicate the file path. |

### Rules

1. **Required on every task: `skill` + `tier` + `mode:*` + `lifecycle:*`.** These drive `make` targets, coverage, and evalboard dashboards.
2. **One value per singular dimension** (`tier`, `mode`, `shape`). A task doesn't have two tiers.
3. **`node:` and `feature:` are repeatable.** A flow exercising decision and switch nodes gets both `node:decision` and `node:switch`.
4. **`connector`, `resource`, and `windows` are flat boolean markers**, not enumerations. Use them once per task; the specific connector/resource is identifiable from the file path, `task_id`, or YAML body. Adding `connector:slack` etc. is no longer the convention.
5. **Use only the vocabularies above.** Propose new values in the PR — do not invent tags inline. New values should apply to at least two tasks in practice.
6. **Don't repeat the skill name as a feature tag.** Don't tag a flow task with `rpa` (bare) or `uipath-rpa` as a feature.

### Example

```yaml
tags: [uipath-maestro-flow, e2e, mode:build, shape:multi-node, node:decision, connector, feature:http]
```

### Useful slices this enables

- `make tags TAGS="smoke"` → every skill's entry-gate checks.
- `make tags TAGS="smoke windows"` → Windows-only smoke tasks (the slice `smoke-rpa-skills.yml` runs on `windows-latest`).
- `make tags TAGS="integration connector"` → connector coverage across skills.
- `make tags TAGS="e2e mode:build"` → end-to-end build tasks across skills.
- `make tags TAGS="mode:diagnose"` → diagnosis-mode coverage across skills.
- Evalboard: `where tag == "connector"` → pass-rate across all connector-using tasks.
- Evalboard: `where tag == "shape:multi-node"` → composite-flow reliability.

## Directory Structure

```
tests/
├── README.md
├── Makefile
├── experiments/
│   ├── default.yaml              # Dev / ad-hoc — tempdir, full lifecycle (no docker image required)
│   ├── nightly.yaml              # Nightly cron — docker, full lifecycle, staging tenant
│   ├── smoke.yaml                # PR-gate smoke (Linux, docker, faster budget)
│   ├── smoke-windows.yaml        # Windows RPA smoke (tempdir)
│   ├── activation.yaml           # Opt-in skill-activation benchmark (1-turn)
│   ├── skill-comparison-playbook.md      # A/B comparison playbook (research)
│   └── skill-comparison-template.yaml    # Template for compare-<a>-vs-<b>.yaml (research)
├── tasks/
│   └── <skill-name>/             # One folder per skill (must match skills/<name>/)
│       ├── _shared/              # Optional — helpers, cleanup scripts, per-skill pytest
│       ├── smoke/                # Tier: smoke
│       ├── single_node/          # Tests isolating a single node type (optional)
│       ├── multi_node/           # Composite-flow tests (optional)
│       ├── edit/                 # Tests that modify an existing artifact (optional)
│       └── <other>/              # Skill-specific groupings (e.g. hitl/, connector_features/)
└── reports/                      # Generated by /test-coverage command
    ├── <skill-name>.md           # Per-skill coverage report
    └── SUMMARY.md                # Cross-skill roll-up (when analyzing all)
```

Groupings under a skill are advisory — pick the ones that map to how the skill is exercised. The flow skill uses `smoke/`, `single_node/`, `multi_node/`, `edit/`, `hitl/`, `connector_features/`. Keep dir names short and kebab-case; put only one task YAML per leaf dir (plus its sidecar check scripts).

## Experiment Configs

Experiment files define shared agent defaults per test type. Tasks inherit these defaults and should only override what differs.

Run-time caps live under `defaults.run_limits` (see coder_eval `RunLimits`).

| Experiment | Driver | Used by | max_turns | task_timeout | turn_timeout |
|------------|--------|---------|-----------|--------------|--------------|
| `default.yaml` | tempdir | Devs locally, ad-hoc runs | 200 | 1200s | 900s |
| `nightly.yaml` | docker | Nightly cron (`daily.sh`) | 200 | 1200s | 900s |
| `smoke.yaml` | docker | PR-gate smoke (Linux) | 40 | 900s | 900s |
| `smoke-windows.yaml` | tempdir | PR-gate smoke (Windows RPA only) | 40 | 900s | 900s |
| `activation.yaml` | tempdir | Skill activation classifier (benchmark) | 1 | 120s | 120s |

`activation.yaml` is a different shape from the tiered configs above — it runs the agent for exactly one turn against single-prompt rows to measure whether the right skill fires (precision/recall/F1 per skill). It's an opt-in benchmark, not a smoke gate. See [`tasks/activation/README.md`](tasks/activation/README.md).

For **A/B comparisons between two skill variants** (e.g. `main` vs a feature branch, or two historical commits), see [`experiments/skill-comparison-playbook.md`](experiments/skill-comparison-playbook.md) and the [`experiments/skill-comparison-template.yaml`](experiments/skill-comparison-template.yaml). The playbook covers worktree setup, SHA pinning for reproducibility, getting N>1, and interpreting divergent tasks. To automate the whole flow, use the `/skill-compare <ref_a> <ref_b> [task_selector] [n_reps]` slash command — each ref can be a branch name or a commit SHA, and `task_selector` accepts a skill name (`uipath-maestro-flow`), tag list (`tags:smoke,init`), or path globs (`paths:tasks/uipath-maestro-flow/*.yaml`).

Task files should **not** duplicate the full `agent:` block — the experiment provides the defaults. Only specify fields that differ from the experiment:

```yaml
# Good — no agent block needed when everything matches the experiment defaults
task_id: skill-flow-init-validate
tags: [uipath-maestro-flow, smoke, mode:build]

sandbox:
  driver: docker
  python: {}

initial_prompt: |
  ...

# Good — only override what differs (max_turns: 14 instead of the default 20)
task_id: skill-flow-registry-discovery
tags: [uipath-maestro-flow, smoke, mode:build, feature:registry]

agent:
  type: claude-code
  max_turns: 14

sandbox:
  driver: docker
  python: {}

initial_prompt: |
  ...
```

## Lifecycle E2E tests (uipath-platform pattern)

`tests/tasks/uipath-platform/{orchestrator,resources}/` and
`tests/tasks/uipath-solution/` follow the same shape as `traces_e2e.yaml`:
the agent receives a process key (and derived folder) via env var, exercises
the operational scenario, and a `check_*.py` script verifies tenant state
directly.

### Shape

```yaml
pre_run:
  - command: "E2E_PROCESS_KEY=$E2E_PROCESS_KEY python3 $SKILLS_REPO_PATH/tests/tasks/uipath-platform/seed.py"
    timeout: 30
```

A single helper script (`tests/tasks/uipath-platform/seed.py`) writes
`seed.json` with a fresh `uuid8` and — when `E2E_PROCESS_KEY` is set —
`process_key` + `folder_path` (resolved via `uip or processes list`, matched by Key — the `get` endpoint doesn't populate FolderPath). Tests
that don't need a process omit the env var assignment; the script just
writes `uuid8`.

### Tenant prerequisites

Two pre-existing processes on the tenant, referenced by their keys via CI
secrets (matches the existing `TRACES_SMOKE_PROCESS_KEY` pattern):

| Secret | Purpose | Used by |
|---|---|---|
| `E2E_PROCESS_KEY` | Standard coded-agent process, runs to terminal quickly | job/trigger/webhook/resource tests |
| `E2E_LONG_PROCESS_KEY` | Same shape but sleeps ~30s | `job_control_e2e` (needs a stop/restart window) |

Both processes live in folders, so `folder_path` is derived from the
process key — no separate folder secret needed. Tests needing a second
folder create it themselves as part of the scenario.

### Cleanup

There is no `post_run`. The agent creates and deletes its own ephemeral
resources as part of the test scenario; the check script verifies the
final tenant state. Shared resources (the pre-seeded processes and their
folders) persist on the tenant across runs.

## Adding Tests for a New Skill

1. Create `tests/tasks/<skill-name>/` matching the skill folder name under `skills/`.
2. Add at minimum **1 smoke test** and **1 e2e test** (required for every new skill PR).
3. Use minimal prompts — the goal is to test whether the skill guides the agent correctly, not to hand-hold it.
4. Tag every task using the [Tag Taxonomy](#tag-taxonomy): required `skill` + `tier` + `mode:*`, plus optional `shape`, `node`, `resource`, `connector`, and `feature` where applicable.
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
tags: [uipath-maestro-flow, smoke, mode:build]

sandbox:
  driver: docker
  python: {}

initial_prompt: |
  Create a new UiPath Flow project called "WeatherAlert" and make sure it
  validates successfully.

  Use the `uipath-maestro-flow` skill workflow. A Flow project MUST be created
  inside a solution:
  1. Create the solution first.
  2. Create the Flow project inside that solution.
  3. Link the project to the solution.

  The correct flow-file path is:
    WeatherAlert/WeatherAlert/WeatherAlert.flow

  The task is NOT complete until `uip maestro flow validate` has passed for
  that exact file path.

  Important:
  - The `uip` CLI is already available in the environment.
  - Do not run `uip maestro flow debug` — just validate locally.

success_criteria:
  - type: command_executed
    description: "Agent created a solution with uip solution new"
    tool_name: "Bash"
    command_pattern: '(uip|\$UIP)\s+solution\s+new'
    min_count: 1
    weight: 1.5
    pass_threshold: 1.0

  - type: command_executed
    description: "Agent initialized a Flow project with uip maestro flow init"
    tool_name: "Bash"
    command_pattern: '(uip|\$UIP)\s+(maestro\s+)?flow\s+init'
    min_count: 1
    weight: 1.5
    pass_threshold: 1.0

  - type: command_executed
    description: "Agent validated the .flow file"
    tool_name: "Bash"
    command_pattern: '(uip|\$UIP)\s+(maestro\s+)?flow\s+validate'
    min_count: 1
    weight: 1.5
    pass_threshold: 1.0

  - type: command_executed
    description: "Agent used --output json on uip commands"
    tool_name: "Bash"
    command_pattern: '(uip|\$UIP)\s+.*--output\s+json'
    min_count: 1
    weight: 1.0
    pass_threshold: 1.0

  - type: command_executed
    description: "Agent linked flow project to solution"
    tool_name: "Bash"
    command_pattern: '(uip|\$UIP)\s+solution\s+project\s+add'
    min_count: 1
    weight: 1.0
    pass_threshold: 1.0

  - type: file_exists
    description: "Flow file was created inside the solution"
    path: "WeatherAlert/WeatherAlert/WeatherAlert.flow"
    weight: 1.5
    pass_threshold: 1.0
```

Key patterns to note:
- **No `agent:` block** — inherits everything from `experiments/default.yaml`
- **No `run_limits:` block** — inherits turn / timeout caps from the experiment config
- **Minimal prompt** — describes the goal ("create and validate"), not the steps
- **Behavior-only criteria** — `command_executed` and `file_exists` verify real operations, not agent self-reports
- **Weighted scoring** — core commands (`weight: 1.5`) matter more than supporting checks (`weight: 1.0`)

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

Verify a file contains (or excludes) expected strings. From `uipath-maestro-flow/hitl/smoke_01_hitl_node_placed.yaml`:

```yaml
- type: file_contains
  description: "Flow contains the inline HITL node type"
  path: "InvoiceApproval/InvoiceApproval/InvoiceApproval.flow"
  includes:
    - '"uipath.human-in-the-loop"'
  weight: 3.0
  pass_threshold: 1.0
```

`excludes:` is also supported — useful for asserting a file does not contain a deprecated flag or forbidden value.

### `json_check`

Validate JSON file structure and values using JMESPath assertions. Supported operators: `equals`, `gte`, `lte`, `gt`, `lt`, `contains`.

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

## Authoring Workflow

Author tests in this order. Each step has a dedicated slash command.

### 1. `/test-coverage <skill-name>` — find the gap

Generates a coverage report that maps what a skill teaches against what its tests verify.

```bash
/test-coverage uipath-maestro-flow   # single skill
/test-coverage all                   # cross-skill roll-up
```

Reports are written to `tests/reports/<skill-name>.md` and include:
- Component, workflow step, critical rule, and anti-pattern coverage (Direct/Indirect/None)
- Weighted overall score
- Priority-ranked coverage gaps with concrete test recommendations

Defined in [`.claude/commands/test-coverage.md`](../.claude/commands/test-coverage.md).

### 2. `/generate-task <description>` — scaffold the YAML

Scaffolds a single task YAML from a free-form description of the scenario to cover. The command always infers the target skill from the description — do not pass a skill name.

```bash
/generate-task smoke test for folder listing via uip orchestrator
/generate-task e2e flow that uses HITL with an approval gate and write-back
/generate-task cover the new uip flow registry get subcommand
```

Output lands in `tests/tasks/<skill-name>/` as one task YAML (and optional check script). Generated tasks are **unverified scaffolds** — verify that CLI commands, success criteria, and prompts match the skill's actual behavior.

Defined in [`.claude/commands/generate-task.md`](../.claude/commands/generate-task.md).

### 3. `/lint-task <path>` — lint before committing

Lints the generated YAML against repo conventions (sandbox rules, tag taxonomy, criterion shape, CLI verb reachability) before it lands in a PR. Run this before step 4.

### 3a. `/audit-verbs` — full CLI-verb sweep (conditional)

When step 3 surfaces **CLI verb reachability** findings, run `/audit-verbs` to see whether the same stale verb appears in other tasks or in skill docs. Writes `tests/reports/cli-verb-audit.md` and `tests/reports/skill-verb-audit.md`, both regenerated from the `uip` catalog at `assets/uip-catalog-snapshot.json`. Skip this step when `/lint-task` reports clean.

Defined in [`.claude/commands/audit-verbs.md`](../.claude/commands/audit-verbs.md).

### 4. Run with `coder-eval` and attach a passing-run claim

Run the task end-to-end (see [Running Tests](#running-tests)) and add a passing-run claim to the PR description. The lint workflow flags missing claims as High severity.

### Tooling self-tests

Regression tests for the audit pipeline live under `tests/scripts/`. Run them when you modify any of `scripts/build-uip-catalog.py`, `scripts/check-cli-verbs.py`, or `scripts/check-skill-verbs.py`:

```bash
pytest tests/scripts/
```

## Further Reading

- [coder_eval repository](https://github.com/UiPath/coder_eval) — framework docs, task definition guide, CLI reference
- [CONTRIBUTING.md](../CONTRIBUTING.md) — skill contribution rules and quality checklist
