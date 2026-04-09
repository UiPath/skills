# Subflow Node — Planning

## Node Type

`core.subflow`

## When to Use

Use a Subflow node to group related steps into a reusable, drillable container with isolated variable scope.

### Selection Heuristics

| Situation | Use Subflow? |
| --- | --- |
| Group related steps into a reusable container | Yes |
| Encapsulate logic with its own variable scope | Yes |
| Simple sequential steps that don't need isolation | No — wire nodes directly |
| Call a published flow as a subprocess | No — use [Flow](../flow/planning.md) |

## Ports

| Input Port | Output Port(s) |
| --- | --- |
| `input` | `output`, `error` |

## Key Properties

- Subflows have their own `nodes`, `edges`, and `variables` stored in `subflows.{nodeId}`
- Parent-scope `$vars` are **not** visible inside the subflow — pass values explicitly via inputs
- Subflow inputs map to `direction: "in"` variables; outputs map to `direction: "out"` variables
- Nesting supported up to 3 levels deep
- Every subflow must have its own Start node (`core.trigger.manual`) and End node (`core.control.end`)
