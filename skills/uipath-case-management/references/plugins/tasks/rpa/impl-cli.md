# rpa task — Implementation

## CLI Command

```bash
uip maestro case tasks add <file> <stage-id> \
  --type rpa \
  --display-name "<display-name>" \
  --name "<process-name>" \
  --folder-path "<folder-path>" \
  --task-type-id "<entityKey>" \
  --should-run-only-once \
  --is-required \
  --output json
```

Enrichment is the same as `process` — passing `--task-type-id` auto-populates inputs and outputs.

## Example

```bash
uip maestro case tasks add caseplan.json stg000abc123 \
  --type rpa \
  --display-name "Extract Invoice Data" \
  --name "InvoiceExtractor" \
  --folder-path "Finance" \
  --task-type-id "b2c3d4e5-6789-01ab-cdef-234567890abc" \
  --is-required \
  --output json
```

## Resulting JSON Shape

> **ID and elementId format.** Task `id` is `t` + 8 random chars. `elementId` is the composite `${stageId}-${taskId}`.

```json
{
  "id": "tQ2pVx7Lm",
  "elementId": "Stage_aB3kL9-tQ2pVx7Lm",
  "type": "rpa",
  "displayName": "Extract Invoice Data",
  "data": {
    "name": "InvoiceExtractor",
    "folderPath": "Finance",
    "inputs": [ /* enriched */ ],
    "outputs": [ /* enriched */ ],
    "context": { "taskTypeId": "b2c3d4e5-6789-01ab-cdef-234567890abc" }
  },
  "isRequired": true
}
```

## Binding Inputs

Use `uip maestro case var bind` — identical pattern to [process/impl-cli.md](../process/impl-cli.md#binding-inputs-and-outputs).

## Post-Add Validation

Capture `TaskId`. Confirm `type: "rpa"` in `caseplan.json` and `data.context.taskTypeId` populated.
