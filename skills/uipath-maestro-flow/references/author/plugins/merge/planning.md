# Merge Node — Planning

## Node Type

`core.logic.merge`

## When to Use

Use a Merge node to synchronize parallel branches before continuing. It waits for all incoming paths to complete.

### Selection Heuristics

| Situation | Use Merge? |
| --- | --- |
| Two or more parallel branches need to join before continuing | Yes |
| Sequential pipeline (no parallel branches) | No — wire nodes directly |
| Joining the `true`/`false` branches of ONE Decision (or the cases of one Switch) | **No** — wire both ports straight into the next node (a node accepts several incoming edges). A Merge waits for ALL inputs and a Decision emits exactly one, so the run would hang forever; `flow validate` refuses this shape |

## Ports

| Input Port | Output Port(s) |
| --- | --- |
| `input` (accepts multiple connections) | `output` |

## Wiring Rules

- Connect each parallel branch's terminal node to the Merge node's `input` port
- Merge accepts multiple incoming edges on the same `input` port
- Execution continues from `output` only after all incoming paths complete
- Use after forking from a single node to multiple downstream nodes
