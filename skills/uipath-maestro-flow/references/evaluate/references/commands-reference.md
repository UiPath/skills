# `uip maestro flow eval` Command Reference

Complete syntax reference for every subcommand under `uip maestro flow eval`. All commands accept the global flags `--output <table|json|yaml|plain>` (default `json`), `--output-filter <jmespath>`, `--log-level <debug|info|warn|error>`, and `--log-file <path>`. Repeated reminders below: always pass `--output json` when an agent will parse the result.

## Command Tree

```
uip maestro flow eval
├── add        — Add a data point to an evaluation set
├── list       — List data points in an evaluation set
├── remove     — Remove a data point from an evaluation set
├── set
│   ├── add    — Create an evaluation set
│   ├── list   — List evaluation sets
│   └── remove — Remove an evaluation set
├── evaluator
│   ├── add    — Add an evaluator to the flow project
│   ├── list   — List evaluators in a flow project
│   └── remove — Remove an evaluator from a flow project
└── run
    ├── start    — Start a Studio Web evaluation run
    ├── status   — Check the status of a run
    ├── results  — Get detailed per-data-point results
    ├── list     — List runs for an eval set
    └── compare  — Compare two runs side-by-side
```

`add` / `remove` / `list` at the top level operate on **data points** (test cases) inside an eval set. Data points are stored inline within the eval set JSON, not as separate files.

## Common Options

Every subcommand accepts:

| Flag | Required | Description |
|------|----------|-------------|
| `--path <path>` | No (defaults to `.`) | Flow project directory, or a solution directory containing exactly one Flow project |
| `--output <fmt>` | No (default `json`) | `table`, `json`, `yaml`, or `plain` |
| `--output-filter <expr>` | No | JMESPath expression applied to JSON output before printing |

## Data Points (Test Cases)

### `uip maestro flow eval add <name>`

Add a data point to an eval set.

| Flag | Required | Description |
|------|----------|-------------|
| `--set <name>` | Yes | Eval set name or ID |
| `--inputs <json>` | No | Input values as a JSON object |
| `--input-file <key=path>` | No | Attach a file as input `<key>`; **repeatable** |
| `--expected <json>` | No | Expected output as a JSON object |
| `--criteria <json>` | No | Per-evaluator criteria JSON object keyed by evaluator id |
| `--search-text <text>` | No | Search text for `contains` evaluators |
| `--path <path>` | No | (see Common Options) |

Example:

```bash
uip maestro flow eval add greeting-test \
  --set "Smoke Tests" \
  --inputs '{"name":"Alice"}' \
  --expected '{"greeting":"Hello, Alice!"}' \
  --path ./MySolution/MyFlow --output json
```

### `uip maestro flow eval list`

List data points in an eval set.

```bash
uip maestro flow eval list --set "Smoke Tests" --path ./MySolution/MyFlow --output json
```

### `uip maestro flow eval remove <id>`

Remove a data point. `<id>` accepts the data point's UUID or its `name`.

## Evaluation Sets

### `uip maestro flow eval set add <name>`

Create an evaluation set.

| Flag | Required | Description |
|------|----------|-------------|
| `--evaluators <refs>` | No (default: all) | Comma-separated evaluator IDs or file base names |
| `--entry-point <id>` | No | Entry point node id stored as the eval set's `selectedEntrypoint` |
| `--path <path>` | No | (see Common Options) |

When `--evaluators` is omitted, the new eval set references **all** evaluators present in the project at creation time.

### `uip maestro flow eval set list`

List eval sets in the project.

### `uip maestro flow eval set remove <id>`

Remove an eval set. `<id>` accepts the eval set's UUID, `name`, or file base name.

## Evaluators

### `uip maestro flow eval evaluator add <name>`

Create an evaluator file in the project's evaluators directory.

| Flag | Required | Description |
|------|----------|-------------|
| `--type <type>` | Yes | One of: `exact-match`, `json-similarity`, `contains`, `llm-judge-output`, `llm-judge-strict-json`, `llm-judge-trajectory`, `llm-judge-trajectory-simulation` |
| `--description <text>` | No | Evaluator description |
| `--target-key <key>` | No | Output key the evaluator scores against (defaults to `*` — the entire output) |
| `--model <model>` | No (Yes for llm-judge-*) | LLM model for LLM-judge evaluators (e.g. `gpt-4.1-2025-04-14`) |
| `--prompt <prompt>` | No | Custom LLM judge prompt; defaults to a built-in template per type |
| `--path <path>` | No | (see Common Options) |

Only kebab-case `--type` values are accepted; PascalCase fails with an error.

For LLM-judge evaluators, `--model` is effectively required — the cloud worker rejects an empty `model` before sending to the LLM gateway. See [evaluators-guide.md](evaluators-guide.md) for the seven types in detail.

### `uip maestro flow eval evaluator list`

List evaluators in the project.

### `uip maestro flow eval evaluator remove <id>`

Remove an evaluator. `<id>` accepts UUID, name, or file base name. Removing an evaluator does not auto-clean `evaluatorRefs` in eval sets — verify after removing.

## Run

### `uip maestro flow eval run start`

Start a Studio Web evaluation run. The Flow solution **must already exist in Studio Web** — see [upload-safety.md](upload-safety.md).

| Flag | Required | Description | Default |
|------|----------|-------------|---------|
| `--set <name>` | Yes | Eval set name or ID | — |
| `--solution-id <id>` | No | Solution ID from Studio Web | Auto-resolved from project metadata |
| `--project-id <id>` | No | Flow project ID from Studio Web | Auto-resolved |
| `--path <path>` | No | (see Common Options) | `.` |
| `--entry-point <entry>` | No | Flow entry point path (e.g. `/Main.bpmn#start`) or start node ID | Eval set's `selectedEntrypoint` |
| `--folder-key <key>` | No | Orchestrator folder key | Personal workspace |
| `--debug-mode <mode>` | No | Studio Web debug mode override | (server default) |
| `--wait` | No | Block until terminal state, then print results | `false` |
| `--timeout <seconds>` | No | Max time to block on `--wait` | `600` (10 min) |

Without `--wait`, returns immediately with `EvalSetRunId`. With `--wait`, the CLI polls until `Completed` or `Failed`, or `--timeout` elapses (the server-side run continues regardless).

### `uip maestro flow eval run status <evalSetRunId>`

Get current status. Terminal states: `Completed`, `Failed`.

| Flag | Required | Description |
|------|----------|-------------|
| `--set <name>` | Yes | Eval set name or ID |
| `--solution-id <id>` | No | Override solution ID |
| `--project-id <id>` | No | Override project ID |
| `--path <path>` | No | (see Common Options) |

### `uip maestro flow eval run results <evalSetRunId>`

Per-data-point results.

| Flag | Required | Description |
|------|----------|-------------|
| `--set <name>` | Yes | Eval set name or ID |
| `--only-failed` | No | Show only failed/errored data points |
| `--verbose` | No | Include evaluator justifications |
| `--export-format <json\|csv>` | No | Export results to a file |
| `--solution-id`, `--project-id`, `--path` | No | (see start) |

Per-row output fields: `DataPoint`, `Status`, `EvaluatorScores`, `Duration`, `Error` (plus `Justifications` when `--verbose`).

### `uip maestro flow eval run list`

List runs for an eval set.

```bash
uip maestro flow eval run list --set "Smoke Tests" --path ./MySolution/MyFlow --output json
```

### `uip maestro flow eval run compare <evalSetRunId>`

Compare two runs side-by-side.

| Flag | Required | Description |
|------|----------|-------------|
| `--compare-to <id>` | Yes | Second eval set run ID |
| `--set <name>` | Yes | Eval set name or ID |
| `--solution-id`, `--project-id`, `--path` | No | (see start) |

`compare` aligns data points by `name` within the eval set. Comparing runs from different eval sets is meaningless.

## Output Codes

The CLI emits a `Code` field on every JSON response. Useful when filtering or scripting:

| Subcommand | `Code` |
|------------|--------|
| `eval add` | `MaestroFlowEvalAdd` |
| `eval list` | `MaestroFlowEvalList` |
| `eval remove` | `MaestroFlowEvalRemove` |
| `eval set add` / `list` / `remove` | `MaestroFlowEvalSetAdd` / `List` / `Remove` |
| `eval evaluator add` / `list` / `remove` | `MaestroFlowEvaluatorAdd` / `List` / `Remove` |
| `eval run start` (no `--wait`) | `MaestroFlowEvalRunStarted` |
| `eval run start --wait` (summary) | `MaestroFlowEvalRunCompleted` |
| `eval run status` | `MaestroFlowEvalRunStatus` |
| `eval run results` | `MaestroFlowEvalRunResults` |
| `eval run list` | `MaestroFlowEvalRunList` |
| `eval run compare` | `MaestroFlowEvalRunComparison` |

If actual emitted codes diverge from the table above, trust the JSON output — file an issue.
