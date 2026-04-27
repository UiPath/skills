# process task — Implementation

## CLI Command

```bash
uip maestro case tasks add <file> <stage-id> \
  --type process \
  --display-name "<display-name>" \
  --name "<process-name>" \
  --folder-path "<folder-path>" \
  --task-type-id "<entityKey>" \
  --should-run-only-once \
  --is-required \
  --output json
```

### Required flags

| Flag | Source | Required |
|------|--------|----------|
| `--type process` | fixed | yes |
| `--display-name` | tasks.md title | yes |
| `--task-type-id` | tasks.md `taskTypeId` | yes (triggers enrichment) |

### Optional flags

| Flag | Purpose |
|------|---------|
| `--name` | Process name (display) |
| `--folder-path` | Orchestrator folder path |
| `--should-run-only-once` | Runs once per case instance |
| `--is-required` | Stage completion depends on this task |
| `--description` | Task description |

Passing `--task-type-id` auto-enriches the task with inputs, outputs, and bindings. If enrichment fails, re-run `uip maestro case tasks enrich --type process --id <entityKey>` separately.

## Example

```bash
uip maestro case tasks add caseplan.json stg000abc123 \
  --type process \
  --display-name "Run KYC" \
  --name "KYC" \
  --folder-path "Shared" \
  --task-type-id "f1b2c3d4-1234-5678-abcd-ef1234567890" \
  --should-run-only-once \
  --is-required \
  --output json
```

## Resulting JSON Shape in caseplan.json

After the command runs, the stage's `data.tasks[0]` array gains an entry like:

> **ID and elementId format.** Task `id` is `t` + 8 random chars (e.g. `t8GQTYo8O`). `elementId` is the composite `${stageId}-${taskId}` (e.g. `Stage_aB3kL9-t8GQTYo8O`).

```json
{
  "id": "t8GQTYo8O",
  "elementId": "Stage_aB3kL9-t8GQTYo8O",
  "type": "process",
  "displayName": "Run KYC",
  "data": {
    "name": "KYC",
    "folderPath": "Shared",
    "inputs": [ /* enriched from taskTypeId */ ],
    "outputs": [ /* enriched */ ],
    "context": { "taskTypeId": "f1b2c3d4-1234-5678-abcd-ef1234567890" }
  },
  "shouldRunOnReEntry": false,
  "isRequired": true
}
```

## Binding Inputs and Outputs

After `tasks add`, bind each input from tasks.md per [bindings-and-expressions.md](../../../bindings-and-expressions.md):

```bash
# Literal or expression input
uip maestro case var bind <file> <stage-id> <task-id> <input-name> --value "<value>" --output json

# Cross-task reference input
uip maestro case var bind <file> <stage-id> <task-id> <input-name> \
  --source-stage <src-stage-id> \
  --source-task <src-task-id> \
  --source-output <output-name> \
  --output json
```

## Post-Add Validation

Capture `TaskId` from the `--output json` response. Save it in the stage/task ID map for downstream cross-task references.

Confirm the task appears in `caseplan.json` with the expected `type: "process"` and a non-empty `data.context.taskTypeId`.
