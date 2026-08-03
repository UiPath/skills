# Orchestrator Runtime Eval Run

Submit runtime evaluation runs and view results for low-code agents published as Orchestrator packages.

Use this when the agent has been published to Orchestrator (via `uip solution deploy` or Studio) and you want to trigger an eval run against the published package.

## Command Structure

```
uip or eval
  ├── run-offline-evals          Submit a new eval run
  ├── run list                   List all runs for a process
  ├── run get <evalSetRunId>     Get details of a specific run
  └── run results <evalSetRunId> View per-item results for a run
```

`run-offline-evals` submits the run. `run list/get/results` query results afterward.

## Submit a Run — run-offline-evals

```bash
uip or eval run-offline-evals \
  --process-key <guid> \
  --items <json> \
  --evaluators <json> \
  [--eval-set-id <guid>] \
  [--batch-size <n>] \
  [--folder-key <folder-guid>] \
  [--tenant <tenant-name>] \
  --output json
```

The folder resolves from your personal workspace automatically. Pass `--folder-key` to target a specific folder instead.

`--eval-set-id` defaults to `00000000-0000-0000-0000-000000000000` when not provided.

### Options

| Flag | Required | Description |
|------|----------|-------------|
| `--process-key` | Yes | Process key (GUID). Use `uip or processes list` to find available keys. |
| `--items` | Yes | JSON array of eval items. See [creating-eval-items.md](creating-eval-items.md) for format. |
| `--evaluators` | Yes | JSON array of evaluator configs. See [creating-evaluators.md](creating-evaluators.md) for format. |
| `--eval-set-id` | No | Eval set ID; defaults to a zero GUID when not provided |
| `--batch-size` | No | Max concurrent evaluation pipelines (default: `5`) |
| `--folder-key` | No | Folder key GUID; defaults to personal workspace. Use `uip or folders list` to find available keys. |
| `--tenant` | No | UiPath tenant name |

### Example

```bash
uip or eval run-offline-evals \
  --process-key "9e4b2f17-7c3a-4d81-b592-3f6e8a1d5c09" \
  --items '[{"id": "i1", "name": "Test", "inputs": {"input": "hello"}, "expectedOutput": {}, "expectedBehavior": ""}]' \
  --evaluators '[{"id": "ev-1", "version": "", "evaluatorTypeId": "5", "evaluatorConfig": {"name": "Semantic", "category": 1, "type": 5, "prompt": "Score 0-100...", "model": "gpt-4.1-2025-04-14", "targetOutputKey": "*"}}]' \
  --output json
```

### Output

```json
{
  "Result": "Success",
  "Code": "EvalRunSubmitted",
  "Data": {
    "ProcessKey": "9e4b2f17-7c3a-4d81-b592-3f6e8a1d5c09",
    "Folder": "user@uipath.com's workspace",
    "EvalSetId": "00000000-0000-0000-0000-000000000000",
    "EvalSetRunId": "f3a7d219-8b4c-4e62-a951-7d3f6e2c8b04"
  }
}
```

Use the `EvalSetRunId` to track results with `run list`, `run get`, and `run results` below.

## List Runs — run list

List all eval set runs for a process.

```bash
uip or eval run list \
  --process-key <guid> \
  [--limit <n>] \
  [--tenant <tenant-name>] \
  --output json
```

| Flag | Required | Description |
|------|----------|-------------|
| `--process-key` | Yes | Process key (GUID) |
| `--limit` | No | Max runs to return (default: `50`) |
| `--tenant` | No | UiPath tenant name |

### Output

```json
{
  "Result": "Success",
  "Code": "EvalSetRunList",
  "Data": [
    {
      "EvalSetRunId": "a1b2c3d4-0000-0000-0000-000000000101",
      "EvalSetId": "f3a7d219-8b4c-4e62-a951-7d3f6e2c8b04",
      "Status": "completed",
      "Score": 0.86,
      "EvalsExecuted": 5,
      "Duration": "42.5s",
      "CreatedAt": "2026-08-01T10:00:00Z"
    }
  ]
}
```

`Score` is `"-"` when no score is available yet. `Duration` is `"-"` when the run is still in progress.

## Get Run Details — run get

Get details of a specific eval set run.

```bash
uip or eval run get <evalSetRunId> \
  --process-key <guid> \
  [--tenant <tenant-name>] \
  --output json
```

| Flag | Required | Description |
|------|----------|-------------|
| `<evalSetRunId>` | Yes | Eval set run ID (GUID) — positional argument |
| `--process-key` | Yes | Process key (GUID) |
| `--tenant` | No | UiPath tenant name |

### Output

```json
{
  "Result": "Success",
  "Code": "EvalSetRunDetails",
  "Data": {
    "EvalSetRunId": "a1b2c3d4-0000-0000-0000-000000000101",
    "EvalSetId": "f3a7d219-8b4c-4e62-a951-7d3f6e2c8b04",
    "Status": "completed",
    "Score": 0.86,
    "EvalsExecuted": 5,
    "Duration": "42.5s",
    "CreatedAt": "2026-08-01T10:00:00Z"
  }
}
```

## View Per-Item Results — run results

View per-item eval run results for an eval set run.

```bash
uip or eval run results <evalSetRunId> \
  --process-key <guid> \
  [--tenant <tenant-name>] \
  --output json
```

| Flag | Required | Description |
|------|----------|-------------|
| `<evalSetRunId>` | Yes | Eval set run ID (GUID) — positional argument |
| `--process-key` | Yes | Process key (GUID) |
| `--tenant` | No | UiPath tenant name |

### Output

```json
{
  "Result": "Success",
  "Code": "EvalRunResults",
  "Data": [
    {
      "EvalRunId": "c3d4e5f6-0000-0000-0000-000000000201",
      "DataPoint": "Test Case 1",
      "Status": "completed",
      "Result": { "score": 0.92 },
      "CreatedAt": "2026-08-01T10:01:00Z"
    }
  ]
}
```

`DataPoint` is the test case name (from `evalSnapshot.name`).

## Items and Evaluators Format

For full details on building these JSON arrays, see:
- [Creating Evaluators for Runtime Evals](creating-evaluators.md) — evaluator types, templates, model requirements
- [Creating Eval Items for Runtime Evals](creating-eval-items.md) — item schema, examples per evaluator type
- [Creating Eval Sets](creating-eval-sets.md) — combining evaluators and items together

**Evaluators** — each must have `id`, `evaluatorTypeId` (string), and `evaluatorConfig`:

```json
[
  {
    "id": "8f3a1c72-bd4e-4f91-a832-9e5d2b7c04f6",
    "version": "",
    "evaluatorTypeId": "5",
    "evaluatorConfig": {
      "name": "Default Evaluator",
      "category": 1,
      "type": 5,
      "prompt": "As an expert evaluator...",
      "model": "gpt-4.1-2025-04-14",
      "targetOutputKey": "*"
    }
  }
]
```

**Items** — each must include `id`, `name`, `inputs`:

```json
[
  {
    "id": "7b2e9f48-c3a1-4d85-b6f2-1e8c5a9d3b70",
    "name": "Test Case 1",
    "inputs": { "input": "hello" },
    "expectedOutput": { "content": "Expected agent response here." },
    "expectedBehavior": ""
  }
]
```

## Validation Rules

The CLI enforces these rules before making any network calls:

1. **`--items` and `--evaluators` are required.** Both must be provided.
2. **`--items` must be a valid JSON array of objects.** Non-array values or arrays with non-object elements are rejected.
3. **`--evaluators` must be a valid JSON array of objects.** Same validation as `--items`.
4. **`--batch-size` must be a positive integer.** Non-numeric values are rejected.

## Troubleshooting

| Error | Cause | Fix |
|-------|-------|-----|
| `401 Unauthorized` | Auth expired or not configured | Run `uip login` |
| `Authentication failed` | No active session | Run `uip login` first |
| `Process not found` | Invalid process key | Verify with `uip or processes list` |
| `Eval set not found` | Invalid `--eval-set-id` GUID | Verify the eval set exists in the portal |
| `personal workspace not found` | Account has no personal workspace | Pass `--folder-key` explicitly |
| `Folder not found` | `--folder-key` GUID invalid or inaccessible | Run `uip or folders list` to find valid keys |
| `--items is not a valid JSON array` | Malformed JSON or not an array | Check JSON syntax; must be an array of objects |
| `--evaluators is not a valid JSON array` | Malformed JSON or not an array | Check JSON syntax; must be an array of objects |
| `Invalid --batch-size` | Non-numeric value | Pass a positive integer (e.g. `--batch-size 10`) |

## Anti-patterns

- **Don't pass `"model": "same-as-agent"` with inline `--evaluators`.** Runtime evals have no access to `agent.json`; the API cannot resolve `same-as-agent` and will error.
