# `uip maestro flow eval` Command Reference

Reference for `uip maestro flow eval`. Commands accept `--output <table|json|yaml|plain>` (default `json`), `--output-filter <jmespath>`, `--log-level <debug|info|warn|error>`, and `--log-file <path>`. **Always pass `--output json` when an agent parses the result.**

## Common Options

| Flag | Required | Description |
|---|---|---|
| `--path <path>` | No; defaults to `.` | Flow project directory, or a solution directory containing exactly one Flow project |
| `--output <fmt>` | No; default `json` | `table`, `json`, `yaml`, or `plain` |
| `--output-filter <expr>` | No | JMESPath expression applied to JSON output before printing |
| `--log-level <debug\|info\|warn\|error>` | No | Logging level |
| `--log-file <path>` | No | Log file |

Top-level `add`, `list`, and `remove` operate on data points (test cases) inside an eval set. Data points are stored inline in the eval set JSON, not as separate files.

## Data Points (Test Cases)

### `uip maestro flow eval add <name>`

Run `uip maestro flow eval add <name>` to add a data point.

| Flag | Required | Description |
|---|---|---|
| `--set <name>` | Yes | Eval set name or ID |
| `--inputs <json>` | No | Input values as a JSON object; keys must be declared as Flow input variables |
| `--input-file <key=path>` | No | Attach a file as input `<key>`; **repeatable** |
| `--expected <json>` | No | Expected output as a JSON object |
| `--criteria <json>` | No | Per-evaluator criteria JSON object keyed by evaluator id |
| `--search-text <text>` | No | Search text for `contains` evaluators |
| `--path <path>` | No | Common option |

Run `uip maestro flow eval list --set "Smoke Tests" --path ./MySolution/MyFlow --output json` to list data points in an eval set.

Run `uip maestro flow eval remove <id>` to remove a data point. `<id>` accepts its UUID or `name`.

## Evaluation Sets

### `uip maestro flow eval set add <name>`

Run `uip maestro flow eval set add <name>` to create an evaluation set.

| Flag | Required | Description |
|---|---|---|
| `--evaluators <refs>` | No; default: all | Comma-separated evaluator IDs or generated file base names; do not pass display names |
| `--entry-point <id>` | No | Entry point node id stored as the eval set's `selectedEntrypoint` |
| `--path <path>` | No | Common option |

When `--evaluators` is omitted, reference **all** evaluators present at creation time using their generated evaluator file refs. Prefer this when creating a set immediately after adding evaluator(s). When passing `--evaluators`, use the generated id/file base returned by `evaluator add/list`, not the evaluator display name.

Run `uip maestro flow eval set list` to list eval sets in the project.

Run `uip maestro flow eval set remove <id>` to remove an eval set. `<id>` accepts its UUID, `name`, or file base name.

## Evaluators

### `uip maestro flow eval evaluator add <name>`

Run `uip maestro flow eval evaluator add <name>` to create an evaluator file in the project's evaluators directory.

| Flag | Required | Description |
|---|---|---|
| `--type <type>` | Yes | `exact-match`, `json-similarity`, `contains`, `llm-judge-output`, `llm-judge-strict-json`, `llm-judge-trajectory`, or `llm-judge-trajectory-simulation` |
| `--description <text>` | No | Evaluator description |
| `--target-key <key>` | No | Output key scored against; defaults to `*` (the entire output) |
| `--model <model>` | No; Yes for `llm-judge-*` | LLM model for LLM-judge evaluators, e.g. `gpt-4.1-2025-04-14` |
| `--prompt <prompt>` | No | Custom LLM judge prompt; defaults to a built-in template per type |
| `--path <path>` | No | Common option |

Use only kebab-case `--type` values; PascalCase fails. For LLM-judge evaluators, `--model` is effectively required: the cloud worker rejects an empty `model` before sending to the LLM gateway. See [evaluators-guide.md](evaluators-guide.md) for the seven types in detail.

Run `uip maestro flow eval evaluator list` to list evaluators in the project.

Run `uip maestro flow eval evaluator remove <id>` to remove an evaluator. `<id>` accepts UUID, `name`, or file base name. Removing an evaluator does not auto-clean `evaluatorRefs` in eval sets; verify after removing.

## Simulations

Simulations intercept specific nodes (connectors, agents, sub-flows) during an eval run and replace real execution with a controlled response. Each targets one component by `componentId` and uses `Llm` or `Static`.

### `uip maestro flow eval simulation add <component-id>`

Run `uip maestro flow eval simulation add <component-id>` to add or replace a simulation on a data point. An existing simulation for `<component-id>` is overwritten.

| Flag | Required | Description |
|---|---|---|
| `--set <name>` | Yes | Eval set name or ID |
| `--data-point <id>` | Yes | Data point name or ID |
| `--strategy <strategy>` | Yes | `Llm` or `Static` |
| `--component-type <type>` | Yes | Component type, e.g. `connector`, `agent`, `subflow` |
| `--component-description <text>` | No | Human-readable component label |
| `--simulation-instructions <text>` | No | LLM prompt describing the component's return value; for `Llm` |
| `--mock-value <json>` | No | Static JSON output; for `Static` |
| `--output-schema <json>` | No | JSON Schema describing expected output shape; constrains the LLM. For `Llm`, auto-resolved from the `.flow` file when omitted and fails if the node is not found or has no outputs; pass explicitly to override |
| `--path <path>` | No | Common option |

Use `Llm` when output should be realistic but non-deterministic, with `--simulation-instructions` and optionally `--output-schema`. Use `Static` for fixed, deterministic output with `--mock-value`.

For omitted `--output-schema` with `Llm`, the CLI finds the node by `<component-id>` in the `.flow` file and derives its schema from connector `outputJsonSchema`, agent `agentOutputVariables`, or `node.outputs`. It fails with an actionable error if the node is not found or has no outputs. The schema is sent with `--simulation-instructions` to constrain the LLM; without it, the LLM generates free-form text. Override it with JSON Schema, for example:

```bash
--output-schema '{"type":"object","properties":{"status":{"type":"string"},"message":{"type":"string"}}}'
```

### `uip maestro flow eval simulation list`

Run `uip maestro flow eval simulation list` to list all simulations configured on a data point.

| Flag | Required | Description |
|---|---|---|
| `--set <name>` | Yes | Eval set name or ID |
| `--data-point <id>` | Yes | Data point name or ID |
| `--path <path>` | No | Common option |

### `uip maestro flow eval simulation remove <component-id>`

Run `uip maestro flow eval simulation remove <component-id>` to remove a simulation from a data point. Return an error if no simulation with `<component-id>` exists on that data point.

| Flag | Required | Description |
|---|---|---|
| `--set <name>` | Yes | Eval set name or ID |
| `--data-point <id>` | Yes | Data point name or ID |
| `--path <path>` | No | Common option |

## Run

### `uip maestro flow eval run start`

<!--skill-flavor:upload-safety-run-start-prereq:start-->
Start a Studio Web evaluation run. The Flow solution **must already exist in Studio Web** — see [upload-safety.md](upload-safety.md).
<!--skill-flavor:upload-safety-run-start-prereq:end-->

Run `uip maestro flow eval run start` to start a Studio Web evaluation run.

| Flag | Required | Description | Default |
|---|---|---|---|
| `--set <name>` | Yes | Eval set name or ID | — |
| `--solution-id <id>` | No | Solution ID from Studio Web | Auto-resolved from project metadata |
| `--project-id <id>` | No | Flow project ID from Studio Web | Auto-resolved |
| `--path <path>` | No | Common option | `.` |
| `--entry-point <entry>` | No | Flow entry point path, e.g. `/Main.bpmn#start`, or start node ID | Eval set's `selectedEntrypoint` |
| `--folder-key <key>` | No | Orchestrator folder key | Personal workspace |
| `--debug-mode <mode>` | No | Studio Web debug mode override | server default |
| `--wait` | No | Block until terminal state, then print results | `false` |
| `--timeout <seconds>` | No | Maximum time to block on `--wait` | `600` (10 min) |

Without `--wait`, return immediately with `EvalSetRunId`. With `--wait`, poll until `Completed` or `Failed`, or until `--timeout` elapses; the server-side run continues regardless.

Run `uip maestro flow eval run status <evalSetRunId>` to get current status. Terminal states are `Completed` and `Failed`.

| Flag | Required | Description |
|---|---|---|
| `--set <name>` | Yes | Eval set name or ID |
| `--solution-id <id>` | No | Override solution ID |
| `--project-id <id>` | No | Override project ID |
| `--path <path>` | No | Common option |

Run `uip maestro flow eval run results <evalSetRunId>` to get per-data-point results.

| Flag | Required | Description |
|---|---|---|
| `--set <name>` | Yes | Eval set name or ID |
| `--only-failed` | No | Show only failed/errored data points |
| `--verbose` | No | Include evaluator justifications |
| `--export-format <json\|csv>` | No | Export results to a file |
| `--solution-id`, `--project-id`, `--path` | No | See `start` |

Per-row fields: `DataPoint`, `Status`, `EvaluatorScores`, `Duration`, and `Error`; include `Justifications` with `--verbose`.

Run `uip maestro flow eval run list --set "Smoke Tests" --path ./MySolution/MyFlow --output json` to list runs for an eval set.

### `uip maestro flow eval run compare <evalSetRunId>`

Run `uip maestro flow eval run compare <evalSetRunId>` to compare two runs side-by-side.

| Flag | Required | Description |
|---|---|---|
| `--compare-to <id>` | Yes | Second eval set run ID |
| `--set <name>` | Yes | Eval set name or ID |
| `--solution-id`, `--project-id`, `--path` | No | See `start` |

`compare` aligns data points by `name` within the eval set. Comparing runs from different eval sets is meaningless.

## Output Codes

The CLI emits a `Code` field on every JSON response. Use it for filtering or scripting:

| Subcommand | `Code` |
|---|---|
| `eval add` | `FlowEvalAdd` |
| `eval list` | `FlowEvalList` |
| `eval remove` | `FlowEvalRemove` |
| `eval set add` / `list` / `remove` | `FlowEvalSetAdd` / `FlowEvalSetList` / `FlowEvalSetRemove` |
| `eval evaluator add` / `list` / `remove` | `FlowEvalEvaluatorAdd` / `FlowEvalEvaluatorList` / `FlowEvalEvaluatorRemove` |
| `eval simulation add` / `list` / `remove` | `FlowEvalSimulationAdd` / `FlowEvalSimulationList` / `FlowEvalSimulationRemove` |
| `eval run start` (no `--wait`) | `FlowEvalRunStarted` |
| `eval run start --wait` (summary) | `FlowEvalRunCompleted` |
| `eval run status` | `FlowEvalRunStatus` |
| `eval run results` | `FlowEvalRunResults` |
| `eval run list` | `FlowEvalRunList` |
| `eval run compare` | `FlowEvalRunComparison` |

The `eval run *` codes dropped their `Maestro` prefix (for example, `MaestroFlowEvalRunResults` → `FlowEvalRunResults`) to match the rest of the `eval` family. Older CLI versions emit the `Maestro`-prefixed names. If actual emitted codes diverge from this table, trust the JSON output and file an issue.