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

## Ports

| Input Port | Output Port(s) |
| --- | --- |
| `input` (accepts multiple connections) | `output` |

## Wiring Rules

- Connect each parallel branch's terminal node to the Merge node's `input` port
- Merge accepts multiple incoming edges on the same `input` port
- Execution continues from `output` only after all incoming paths complete
- Use after forking from a single node to multiple downstream nodes
