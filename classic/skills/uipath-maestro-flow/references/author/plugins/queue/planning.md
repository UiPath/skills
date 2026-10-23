# Queue Node — Planning

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
| Direct process invocation with known inputs | No — use [RPA Workflow](../rpa/planning.md) |
| Iterate over items sequentially in the flow | No — use [Loop](../loop/planning.md) |

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
