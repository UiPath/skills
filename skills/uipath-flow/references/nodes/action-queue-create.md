# Queue Create (`core.action.queue.create`)

**Type:** `core.action.queue.create` | **Version:** `1.0.0` | **Category:** `data-operations`
**BPMN Model:** `bpmn:ServiceTask`

## When to Use

| Situation | Use This Node? |
|-----------|---------------|
| Distribute work items to robots via Orchestrator queues — fire-and-forget | Yes |
| Need the result before continuing the flow | No — use `core.action.queue.create-and-wait` |
| Direct process invocation with known inputs | No — use an RPA Workflow resource node |
| Iterate over items sequentially in the flow | No — use `core.logic.loop` |

## Ports

| Direction | Port ID | Notes |
|-----------|---------|-------|
| target | `input` | |
| source | `success` | Fires immediately after item is enqueued |

## Inputs

| Field | Type | Required | Notes |
|-------|------|----------|-------|
| `queue` | string | Yes | Orchestrator queue name — must match exactly |
| `itemData` | string | No | JSON payload for the queue item. Use `=js:JSON.stringify({...})` |
| `priority` | string | No | `Low`, `Normal` (default), `High` |
| `reference` | string | No | Tracking reference string |
| `deferDate` | string | No | ISO 8601 — earliest time to process |
| `dueDate` | string | No | ISO 8601 — deadline for processing |

## Outputs

| Key | Type | Source Expression |
|-----|------|-------------------|
| `output` | object | Queue item creation result |

## Definition

> Queue nodes are dynamic — definitions must be obtained via `uip flow registry get core.action.queue.create --output json`. There is no bundled definition for this node type.

## Instance Example

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

## Common Mistakes

1. **Queue name mismatch** — the `queue` value must exactly match the Orchestrator queue name. No fuzzy matching.
2. **Invalid `itemData`** — must be valid JSON. Wrap with `=js:JSON.stringify({...})` to ensure correct formatting.
3. **Confusing with `create-and-wait`** — this variant fires immediately after enqueuing. If you need the processing result, use `core.action.queue.create-and-wait`.
4. **Missing definition** — queue node definitions are not bundled. Always obtain via `uip flow registry get`.
