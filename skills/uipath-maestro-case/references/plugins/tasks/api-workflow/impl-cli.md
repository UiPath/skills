# api-workflow task — Implementation

## CLI Command

```bash
uip maestro case tasks add <file> <stage-id> \
  --type api-workflow \
  --display-name "<display-name>" \
  --name "<workflow-name>" \
  --folder-path "<folder-path>" \
  --task-type-id "<entityKey>" \
  --should-run-only-once \
  --is-required \
  --output json
```

Passing `--task-type-id` auto-enriches inputs and outputs.

## Example

```bash
uip maestro case tasks add caseplan.json stg000abc123 \
  --type api-workflow \
  --display-name "Monitor Order Inbox" \
  --name "OrderInboxWatcher" \
  --folder-path "Shared" \
  --task-type-id "c3d4e5f6-7890-1234-abcd-345678901234" \
  --should-run-only-once \
  --is-required \
  --output json
```

## Resulting JSON Shape

> **ID and elementId format.** Task `id` is `t` + 8 random chars. `elementId` is the composite `${stageId}-${taskId}`.

```json
{
  "id": "tK7nRs3Wp",
  "elementId": "Stage_aB3kL9-tK7nRs3Wp",
  "type": "api-workflow",
  "displayName": "Monitor Order Inbox",
  "data": {
    "name": "OrderInboxWatcher",
    "folderPath": "Shared",
    "inputs": [ /* enriched */ ],
    "outputs": [ /* enriched */ ],
    "context": { "taskTypeId": "c3d4e5f6-7890-1234-abcd-345678901234" }
  },
  "isRequired": true
}
```

## Binding Inputs

Use `uip maestro case var bind` per [bindings-and-expressions.md](../../../bindings-and-expressions.md).

## Post-Add Validation

Capture `TaskId`. Confirm `type: "api-workflow"` and `data.context.taskTypeId` populated.
