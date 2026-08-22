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

The loop is a container node, so its handles split across an outer and an inner boundary.

| Boundary | Input Port(s) | Output Port(s) |
| --- | --- | --- |
| outer | `input` | `success`, `error` |
| inner | `continue`, `break` | `start` |

- `start` — feeds the first node inside the loop body
- `continue` — receives the edge returning from the last node inside the loop body
- `break` — early exit from inside the body (only when `breakEnabled`)
- `success` — fires after all iterations complete
- `error` — implicit error port shared with all action nodes; fires when the loop or an iteration throws. See [Implicit error port on action nodes](../../../../shared/file-format.md#implicit-error-port-on-action-nodes).

> Aggregated results are an output **variable** (`$vars.<loopId>.output`), not a port.

## Key Inputs

| Input | Required | Description |
| --- | --- | --- |
| `collection` | Yes | Expression pointing to an array (e.g., `$vars.fetchData.output.body.items`) |
| `parallel` | No | `true` to execute all iterations concurrently (default: sequential) |

## Loop Variables (available inside loop body only)

- `$vars.<loopId>.currentItem` — the item being processed in this iteration
- `$vars.<loopId>.currentIteration` — 1-based iteration number (there is no `currentIndex`)
- `$vars.<loopId>.collection` — the full collection

Where `<loopId>` is the loop node's `id` (e.g., `$vars.loop1.currentItem`).

After the loop, `$vars.<loopId>.output` holds one entry per iteration, each keyed by body node id — plan a flattening step if a downstream consumer needs bare values.

## Wiring Rules

- The loop body starts from the loop node's inner `start` port
- The last node in the loop body connects back to the loop's inner `continue` port
- After all iterations, execution continues from the outer `success` port
- Do not create cycles except through the `continue` handle
- **Every node inside the loop body must have `"parentId": "<loopId>"`** — without this, variableUpdates will not fire per-iteration and loop variables will be inaccessible
