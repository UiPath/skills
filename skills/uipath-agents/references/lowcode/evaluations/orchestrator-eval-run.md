# Orchestrator Package Offline Eval Run

Submit offline evaluation runs for low-code agents published as Orchestrator packages.

Use this when the agent has been published to Orchestrator (via `uip solution deploy` or Studio) and you want to trigger an eval run against the published package rather than using the Agent Runtime.

## Command

```bash
uip or eval run-offline-evals \
  --package-name <processKey> \
  --package-version <version> \
  --eval-set-id <eval-set-guid> \
  [--workload-id <agent-guid>] \
  [--folder-key <folder-guid>]
```

The command resolves the folder from your personal workspace automatically. Pass `--folder-key` to target a specific folder instead.

## Options

| Flag | Required | Description |
|------|----------|-------------|
| `--package-name` | Yes | Orchestrator package name (processKey, e.g. `MyPackage.agent.Agent`) |
| `--package-version` | Yes | Package version (e.g. `1.0.2`) |
| `--eval-set-id` | Yes | Eval set ID (GUID) to run — must exist in the published package |
| `--workload-id` | No | Workload GUID; defaults to `00000000-0000-0000-0000-000000000000` |
| `--folder-key` | No | Folder key GUID; defaults to personal workspace |
| `--eval-file` | No | JSON file to override items and/or evaluators from the package |
| `--batch-size` | No | Max concurrent evaluation pipelines (default: `5`) |
| `--loop` | No | Repeat indefinitely until Ctrl-C |
| `--interval` | No | Pause between repeated runs when `--loop` is set (e.g. `30s`, `5m`, `1h`; default: `5m`) |
| `--tenant` | No | UiPath tenant name |

## Examples

```bash
# Minimal run — items/evaluators loaded from the published package
uip or eval run-offline-evals \
  --package-name "PackageTester.agent.Agent" \
  --package-version "1.0.2" \
  --eval-set-id "076f85d8-e907-40cc-aa26-5ff01012b013" \
  --workload-id "413f5032-63c8-4482-9a84-a03b55f2e8cd"

# Override items/evaluators from a local file
uip or eval run-offline-evals \
  --package-name "PackageTester.agent.Agent" \
  --package-version "1.0.2" \
  --eval-set-id "076f85d8-e907-40cc-aa26-5ff01012b013" \
  --eval-file ./overrides.json

# Loop mode — resubmit every 10 minutes
uip or eval run-offline-evals \
  --package-name "PackageTester.agent.Agent" \
  --package-version "1.0.2" \
  --eval-set-id "076f85d8-e907-40cc-aa26-5ff01012b013" \
  --loop --interval 10m

# Explicit folder key instead of personal workspace
uip or eval run-offline-evals \
  --package-name "PackageTester.agent.Agent" \
  --package-version "1.0.2" \
  --eval-set-id "076f85d8-e907-40cc-aa26-5ff01012b013" \
  --folder-key "740defec-0b7f-4d48-a4c3-dd730001e124"
```

## Output

On success, the command logs the submitted `EvalSetRunId`:

```
Package : PackageTester.agent.Agent v1.0.2
Folder  : anirudh.agnihotry@uipath.com's workspace
Eval set: 076f85d8-e907-40cc-aa26-5ff01012b013
Items / evaluators: loaded from package
Submitted. EvalSetRunId: d989a131-478f-8c16-245e-683757027395
```

Use the `EvalSetRunId` to track results in the UiPath portal or with `uip or eval` subcommands.

## Eval File Format

When using `--eval-file`, provide a JSON file with optional `items` and/or `evaluators` arrays:

```json
{
  "items": [
    { "input": "What is the capital of France?", "expectedOutput": "Paris" }
  ],
  "evaluators": [
    { "type": "semantic-similarity", "threshold": 0.85 }
  ],
  "batchSize": 10
}
```

Omit either field to load it from the published package instead.
