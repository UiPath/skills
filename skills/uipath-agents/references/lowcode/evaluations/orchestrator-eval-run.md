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
  --eval-set-id "c4f2a817-3e9b-4d1c-8f5a-2b7e6d4c9a01"

# Inline override — items and evaluators passed directly
uip or eval run-offline-evals \
  --package-name "MyPackage.agent.Agent" \
  --package-version "1.0.0" \
  --folder-key "a9f3b2c1-7d4e-4a8b-9c2f-5e1d3b6a8f7e" \
  --evaluators '[{
    "id": "3d221ae1-5356-4ad4-9459-adb7e3d90277",
    "evaluatorTypeId": "semantic-similarity",
    "evaluatorConfig": { "model": "same-as-agent", "targetOutputKey": "*" }
  }]' \
  --items '[{
    "id": "e9897fd5-63b9-493c-bfb5-f8933459f359",
    "name": "Test Case 1",
    "inputs": {},
    "evaluationCriterias": {
      "3d221ae1-5356-4ad4-9459-adb7e3d90277": {
        "expectedOutput": { "content": "The current date is 2026-05-31." }
      }
    }
  }]'

# Loop 5 times every 2 minutes
uip or eval run-offline-evals \
  --package-name "MyPackage.agent.Agent" \
  --package-version "1.0.0" \
  --eval-set-id "c4f2a817-3e9b-4d1c-8f5a-2b7e6d4c9a01" \
  --loop --interval 2m --count 5

# Explicit folder key
uip or eval run-offline-evals \
  --package-name "MyPackage.agent.Agent" \
  --package-version "1.0.0" \
  --eval-set-id "c4f2a817-3e9b-4d1c-8f5a-2b7e6d4c9a01" \
  --folder-key "a9f3b2c1-7d4e-4a8b-9c2f-5e1d3b6a8f7e"
```

## Items and Evaluators Format

### Evaluators (`--evaluators`)

Each evaluator must include `id` (used as matching key), `evaluatorTypeId`, and optional `evaluatorConfig`:

```json
[
  {
    "id": "3d221ae1-5356-4ad4-9459-adb7e3d90277",
    "evaluatorTypeId": "semantic-similarity",
    "evaluatorConfig": {
      "model": "same-as-agent",
      "targetOutputKey": "*"
    }
  }
]
```

### Items (`--items`)

Each item must include `id`, `name`, `inputs`, and `evaluationCriterias` keyed by evaluator id:

```json
[
  {
    "id": "e9897fd5-63b9-493c-bfb5-f8933459f359",
    "name": "Test Case 1",
    "inputs": {},
    "evaluationCriterias": {
      "3d221ae1-5356-4ad4-9459-adb7e3d90277": {
        "expectedOutput": { "content": "Expected agent response here." }
      }
    }
  }
]
```

`evaluationCriterias` keys must match the `id` of an evaluator in `--evaluators`. The value is evaluator-specific — for `semantic-similarity` it is `{ "expectedOutput": { ... } }`.

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
