# Orchestrator Package Offline Eval Run

Submit offline evaluation runs for low-code agents published as Orchestrator packages.

Use this when the agent has been published to Orchestrator (via `uip solution deploy` or Studio) and you want to trigger an eval run against the published package rather than using the Agent Runtime.

## Command

```bash
uip or eval run-offline-evals \
  --package-name <processKey> \
  --package-version <version> \
  [--eval-set-id <guid>] \
  [--items <json>] \
  [--evaluators <json>] \
  [--is-legacy] \
  [--folder-key <folder-guid>]
```

The folder resolves from your personal workspace automatically. Pass `--folder-key` to target a specific folder instead.

`--eval-set-id` defaults to `00000000-0000-0000-0000-000000000000` when `--items` and `--evaluators` are provided inline.

## Options

| Flag | Required | Description |
|------|----------|-------------|
| `--package-name` | Yes | Orchestrator package name (processKey, e.g. `MyPackage.agent.Agent`) |
| `--package-version` | Yes | Package version (e.g. `1.0.2`) |
| `--eval-set-id` | No | Eval set ID to run; defaults to zero GUID when items/evaluators are provided inline |
| `--items` | No | JSON array of eval items to override those from the package |
| `--evaluators` | No | JSON array of evaluator configs to override those from the package |
| `--is-legacy` | No | Auto-transform items/evaluators from the raw package format (flat JSON with `type`/`category` fields) to the API wire format. Use this when pasting directly from the package or portal. |
| `--batch-size` | No | Max concurrent evaluation pipelines (default: `5`) |
| `--loop` | No | Repeat until `--count` is reached or Ctrl-C |
| `--interval` | No | Pause between repeated runs (e.g. `30s`, `2m`, `1h`; default: `5m`) |
| `--count` | No | Stop after N runs when `--loop` is set; omit to run indefinitely |
| `--folder-key` | No | Folder key GUID; defaults to personal workspace. Use `uip or folders list` to find available keys. |
| `--tenant` | No | UiPath tenant name |

## Examples

```bash
# Minimal — items/evaluators loaded from the published package
uip or eval run-offline-evals \
  --package-name "MyPackage.agent.Agent" \
  --package-version "1.0.0" \
  --eval-set-id "9e4b2f17-7c3a-4d81-b592-3f6e8a1d5c09"

# Inline override — paste evaluator and item JSON directly from the package/portal.
# Use --is-legacy to auto-transform: wraps evaluator as { evaluatorTypeId, evaluatorConfig }
# and renames expectedAgentBehavior → expectedBehavior on items.
# Replace "model" with the actual model ID used by the agent (not "same-as-agent").
uip or eval run-offline-evals \
  --package-name "MyPackage.agent.Agent" \
  --package-version "1.0.0" \
  --is-legacy \
  --evaluators '[{
    "id": "8f3a1c72-bd4e-4f91-a832-9e5d2b7c04f6",
    "name": "Default Evaluator",
    "type": 5,
    "category": 1,
    "prompt": "As an expert evaluator, analyze the semantic similarity...",
    "model": "anthropic.claude-3-5-sonnet-20240620-v1:0",
    "targetOutputKey": "*",
    "createdAt": "2026-05-31T19:36:35.382Z",
    "updatedAt": "2026-05-31T19:36:35.382Z"
  }]' \
  --items '[{
    "id": "7b2e9f48-c3a1-4d85-b6f2-1e8c5a9d3b70",
    "name": "Test Case 1",
    "inputs": {},
    "expectedOutput": { "content": "The current date is 2026-05-31." },
    "expectedAgentBehavior": ""
  }]'

# Loop 5 times every 2 minutes
uip or eval run-offline-evals \
  --package-name "MyPackage.agent.Agent" \
  --package-version "1.0.0" \
  --eval-set-id "9e4b2f17-7c3a-4d81-b592-3f6e8a1d5c09" \
  --loop --interval 2m --count 5

# Explicit folder key instead of personal workspace
uip or eval run-offline-evals \
  --package-name "MyPackage.agent.Agent" \
  --package-version "1.0.0" \
  --eval-set-id "9e4b2f17-7c3a-4d81-b592-3f6e8a1d5c09" \
  --folder-key "a9f3b2c1-7d4e-4a8b-9c2f-5e1d3b6a8f7e"
```

## Items and Evaluators Format

### Without `--is-legacy` (API wire format)

Pass the data already in the format the API expects:

**Evaluators** — each item must have `id`, `evaluatorTypeId` (string), and `evaluatorConfig`:

```json
[
  {
    "id": "8f3a1c72-bd4e-4f91-a832-9e5d2b7c04f6",
    "version": "",
    "evaluatorTypeId": "5",
    "evaluatorConfig": {
      "id": "8f3a1c72-bd4e-4f91-a832-9e5d2b7c04f6",
      "name": "Default Evaluator",
      "type": 5,
      "category": 1,
      "prompt": "As an expert evaluator...",
      "model": "anthropic.claude-3-5-sonnet-20240620-v1:0",
      "targetOutputKey": "*",
      "createdAt": "2026-05-31T19:36:35.382Z",
      "updatedAt": "2026-05-31T19:36:35.382Z"
    }
  }
]
```

**Items** — each item must include `id`, `name`, `inputs`, and `expectedOutput`:

```json
[
  {
    "id": "7b2e9f48-c3a1-4d85-b6f2-1e8c5a9d3b70",
    "name": "Test Case 1",
    "inputs": {},
    "expectedOutput": { "content": "Expected agent response here." },
    "expectedBehavior": ""
  }
]
```

### With `--is-legacy` (raw package format)

Paste the evaluator JSON directly from the package file (flat, with `type` and `category` at the top level). The CLI will auto-transform to the wire format.

> **Note:** Replace `"model": "same-as-agent"` with the actual model ID (e.g. `"anthropic.claude-3-5-sonnet-20240620-v1:0"`). The `same-as-agent` value requires loading `agent.json` from the package, which is not available in inline mode.

```json
[
  {
    "id": "8f3a1c72-bd4e-4f91-a832-9e5d2b7c04f6",
    "name": "Default Evaluator",
    "type": 5,
    "category": 1,
    "prompt": "As an expert evaluator...",
    "model": "anthropic.claude-3-5-sonnet-20240620-v1:0",
    "targetOutputKey": "*",
    "createdAt": "2026-05-31T19:36:35.382Z",
    "updatedAt": "2026-05-31T19:36:35.382Z"
  }
]
```

Items use `expectedAgentBehavior` (renamed to `expectedBehavior` automatically):

```json
[
  {
    "id": "7b2e9f48-c3a1-4d85-b6f2-1e8c5a9d3b70",
    "name": "Test Case 1",
    "inputs": {},
    "expectedOutput": { "content": "Expected agent response here." },
    "expectedAgentBehavior": ""
  }
]
```

## Output

On success, the command logs the submitted `EvalSetRunId`:

```
Package : MyPackage.agent.Agent v1.0.0
Folder  : user@uipath.com's workspace
Eval set: 00000000-0000-0000-0000-000000000000
Items / evaluators: loaded from --items, --evaluators
Submitted. EvalSetRunId: d989a131-478f-8c16-245e-683757027395
```

Use the `EvalSetRunId` to track results in the UiPath portal.
