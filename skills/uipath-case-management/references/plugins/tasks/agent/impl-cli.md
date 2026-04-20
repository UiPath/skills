# agent task — Implementation

## CLI Command

```bash
uip maestro case tasks add <file> <stage-id> \
  --type agent \
  --display-name "<display-name>" \
  --name "<agent-name>" \
  --folder-path "<folder-path>" \
  --task-type-id "<entityKey>" \
  --should-run-only-once \
  --is-required \
  --output json
```

For agents with multiple element bindings, pre-enrich with the element-id:

```bash
uip maestro case tasks enrich --type agent --id "<entityKey>" --element-id "<elementId>"
```

## Example

```bash
uip maestro case tasks add caseplan.json stg000abc123 \
  --type agent \
  --display-name "Classify Purchase Order" \
  --name "PO Classifier" \
  --folder-path "Shared" \
  --task-type-id "a1b2c3d4-5678-90ab-cdef-1234567890ab" \
  --should-run-only-once \
  --is-required \
  --output json
```

## Resulting JSON Shape

> **ID and elementId format.** Task `id` is `t` + 8 random chars. `elementId` is the composite `${stageId}-${taskId}`.

```json
{
  "id": "tH3kLmNp9",
  "elementId": "Stage_aB3kL9-tH3kLmNp9",
  "type": "agent",
  "displayName": "Classify Purchase Order",
  "data": {
    "name": "PO Classifier",
    "folderPath": "Shared",
    "inputs": [ /* enriched */ ],
    "outputs": [ /* enriched */ ],
    "context": { "taskTypeId": "a1b2c3d4-5678-90ab-cdef-1234567890ab" }
  },
  "isRequired": true
}
```

## Binding Inputs

Same as [process/impl-cli.md](../process/impl-cli.md#binding-inputs-and-outputs) — use `uip maestro case var bind` with `--value` or `--source-*` per [bindings-and-expressions.md](../../../bindings-and-expressions.md).

## Post-Add Validation

Capture `TaskId`. Confirm `data.context.taskTypeId` is non-empty. Verify `data.inputs` and `data.outputs` are populated (if empty, enrichment failed — retry `uip maestro case tasks enrich`).
