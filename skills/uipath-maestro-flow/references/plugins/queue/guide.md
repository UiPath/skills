# Queue Node — Guide

## Node Types

| Node Type | Description |
| --- | --- |
| `core.action.queue.create` | Create a queue item and continue immediately (fire-and-forget) |
| `core.action.queue.create-and-wait` | Create a queue item and wait for processing to complete |

## When to Use

Use Queue nodes to distribute work items to robots via Orchestrator queues.

### Selection Heuristics

| Situation | Use Queue? |
| --- | --- |
| Distribute work to robots — fire-and-forget | Yes (`create`) |
| Distribute work and need the result before continuing | Yes (`create-and-wait`) |
| Direct process invocation with known inputs | No — use [RPA Workflow](../rpa/guide.md) |
| Iterate over items sequentially in the flow | No — use [Loop](../loop/guide.md) |

## Ports

| Input Port | Output Port(s) |
| --- | --- |
| `input` | `success` |

## Key Inputs

| Input | Required | Description |
| --- | --- | --- |
| `queue` | Yes | Orchestrator queue name |
| `itemData` | No | JSON payload for the queue item |
| `priority` | No | `Low`, `Normal` (default), `High` |
| `reference` | No | Tracking reference string |
| `deferDate` | No | ISO 8601 — earliest time to process |
| `dueDate` | No | ISO 8601 — deadline for processing |

## Common Pattern — Fan-Out to Queue

```text
Manual Trigger -> Script (split batch) -> Loop -> Queue Create (per item) -> End Loop -> End
```

## Implementation

### Registry Validation

```bash
uip maestro flow registry get core.action.queue.create --output json
uip maestro flow registry get core.action.queue.create-and-wait --output json
```

Confirm: input port `input`, output port `success`.

### JSON Structure

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
  "outputs": {
    "output": {
      "type": "object",
      "description": "The return value of the queue operation",
      "source": "=result.response",
      "var": "output"
    },
    "error": {
      "type": "object",
      "description": "Error information if the queue operation fails",
      "source": "=result.Error",
      "var": "error"
    }
  },
  "model": { "type": "bpmn:ServiceTask" }
}
```

### Adding / Editing

For step-by-step add, delete, and wiring procedures, see [flow-editing-operations.md](../../flow-editing-operations.md). Use the JSON structure above for the node-specific `inputs` and `model` fields.

### Wait Variant

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
  "outputs": {
    "output": {
      "type": "object",
      "description": "The return value of the queue operation",
      "source": "=result.response",
      "var": "output"
    },
    "error": {
      "type": "object",
      "description": "Error information if the queue operation fails",
      "source": "=result.Error",
      "var": "error"
    }
  },
  "model": { "type": "bpmn:ServiceTask" }
}
```

### Debug

| Error | Cause | Fix |
| --- | --- | --- |
| Queue not found | Queue name doesn't match Orchestrator | Verify queue name in Orchestrator |
| `itemData` invalid | Not valid JSON | Ensure `JSON.stringify()` wraps the data object |
| Queue item stuck | No robot available to process | Check Orchestrator robot allocation |
| Wait timeout | Robot took too long to process item | Check queue processing time and robot availability |
