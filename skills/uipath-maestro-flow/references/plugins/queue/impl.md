# Queue Node — Implementation

## Node Types

| Node Type | Description |
| --- | --- |
| `core.action.queue.create` | Fire-and-forget queue item creation |
| `core.action.queue.create-and-wait` | Create queue item and wait for result |

## Registry Validation

```bash
uip flow registry get core.action.queue.create --output json
uip flow registry get core.action.queue.create-and-wait --output json
```

Confirm: input port `input`, output port `success`.

## JSON Structure

```json
{
  "id": "enqueueItem",
  "type": "core.action.queue.create",
  "typeVersion": "1.0.0",
  "display": { "label": "Enqueue Invoice" },
  "inputs": {
    "queue": "InvoiceProcessingQueue",
    "itemData": "=js:JSON.stringify({ orderId: $vars.order.id, amount: $vars.order.total })",
    "priority": "High",
    "reference": "=js:$vars.order.id",
    "deferDate": "2026-04-01T10:00:00Z",
    "dueDate": "2026-04-07T17:00:00Z"
  },
  "model": { "type": "bpmn:ServiceTask" }
}
```

## Adding via CLI

```bash
uip flow node add <ProjectName>.flow core.action.queue.create --output json \
  --input '{"queue": "InvoiceProcessingQueue", "priority": "High"}' \
  --label "Enqueue Invoice" \
  --position 400,300
```

## Wait Variant

`core.action.queue.create-and-wait` blocks execution until the queue item is processed by a robot. The processed result is available via `$vars.{nodeId}.output`.

```json
{
  "id": "processAndWait",
  "type": "core.action.queue.create-and-wait",
  "typeVersion": "1.0.0",
  "display": { "label": "Process and Wait" },
  "inputs": {
    "queue": "InvoiceProcessingQueue",
    "itemData": "=js:JSON.stringify({ invoiceId: $vars.invoiceId })"
  },
  "model": { "type": "bpmn:ServiceTask" }
}
```

## Debug

| Error | Cause | Fix |
| --- | --- | --- |
| Queue not found | Queue name doesn't match Orchestrator | Verify queue name in Orchestrator |
| `itemData` invalid | Not valid JSON | Ensure `JSON.stringify()` wraps the data object |
| Queue item stuck | No robot available to process | Check Orchestrator robot allocation |
| Wait timeout | Robot took too long to process item | Check queue processing time and robot availability |
