# Loop Node — Planning

## Node Type

`core.logic.loop`

## When to Use

Use a Loop node to iterate over a collection of items. Supports sequential and parallel execution.

### Selection Heuristics

| Situation | Use Loop? |
| --- | --- |
| Process each item in an array | Yes |
| Run the same operation on multiple inputs concurrently | Yes (with `parallel: true`) |
| Simple data transformation on a collection | No — use [Transform](../transform/planning.md) |
| Distribute work items to robots | No — use [Queue](../queue/planning.md) |

## Ports

| Input Port(s) | Output Port(s) |
| --- | --- |
| `input`, `loopBack` | `success`, `output` |

- `loopBack` — receives the edge returning from the last node inside the loop body
- `success` — fires after all iterations complete
- `output` — carries aggregated results from all iterations

## Key Inputs

| Input | Required | Description |
| --- | --- | --- |
| `collection` | Yes | Expression pointing to an array (e.g., `$vars.fetchData.output.body.items`) |
| `parallel` | No | `true` to execute all iterations concurrently (default: sequential) |

## Loop Variables (available inside loop body only)

- `$vars.<loopId>.currentItem` — the item being processed in this iteration
- `$vars.<loopId>.currentIndex` — 0-based iteration index
- `$vars.<loopId>.collection` — the full collection

Where `<loopId>` is the loop node's `id` (e.g., `$vars.loop1.currentItem`).

## Wiring Rules

- The loop body starts from the `output` port of the loop node
- The last node in the loop body connects back to the loop's `loopBack` port
- After all iterations, execution continues from the `success` port
- Do not create cycles except through the `loopBack` mechanism
- **Every node inside the loop body must have `"parentId": "<loopId>"`** — without this, variableUpdates will not fire per-iteration and loop variables will be inaccessible
