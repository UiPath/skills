# Queue Create and Wait (`core.action.queue.create-and-wait`)

**Type:** `core.action.queue.create-and-wait` | **Version:** `1.0.0` | **Category:** `data-operations`
**BPMN Model:** `bpmn:ServiceTask`

## When to Use

| Situation | Use This Node? |
|-----------|---------------|
| Distribute work to robots and need the result before continuing | Yes |
| Fire-and-forget queue item creation | No — use `core.action.queue.create` |
| Direct process invocation with known inputs | No — use an RPA Workflow resource node |

This node blocks execution until the queue item is processed by a robot. The processed result is available via `$vars.{nodeId}.output`.

## Ports

| Direction | Port ID | Notes |
|-----------|---------|-------|
| target | `input` | |
| source | `success` | Fires after the queue item is processed and result is returned |

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
| `output` | object | Processed queue item result from the robot |

## Definition

> Queue nodes are dynamic — definitions must be obtained via `uip flow registry get core.action.queue.create-and-wait --output json`. There is no bundled definition for this node type.

## Instance Example

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

## Common Mistakes

1. **Queue name mismatch** — the `queue` value must exactly match the Orchestrator queue name.
2. **Wait timeout** — if no robot is available or processing takes too long, the flow blocks indefinitely. Check Orchestrator robot allocation.
3. **Invalid `itemData`** — must be valid JSON. Wrap with `=js:JSON.stringify({...})`.
4. **Missing definition** — queue node definitions are not bundled. Always obtain via `uip flow registry get`.
5. **Using this when fire-and-forget suffices** — if you don't need the processing result, use `core.action.queue.create` instead to avoid blocking.
