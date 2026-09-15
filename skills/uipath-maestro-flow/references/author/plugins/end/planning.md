# End Node — Planning

## Node Type

`core.control.end`

## When to Use

Use an End node for graceful workflow completion. Each terminal path in the flow needs its own End node.

### Selection Heuristics

| Situation | Use End? |
| --- | --- |
| Normal completion of an execution path | Yes |
| Fatal error — abort everything immediately | No — use [Terminate](../terminate/planning.md) |

## Ports

| Input Port | Output Port(s) |
| --- | --- |
| `input` | — (none) |

## Key Rules

- A flow can have multiple End nodes (one per terminal path)
- Every `out` variable in `variables.globals` **must** be mapped on **every** reachable End node via `outputs`
- End nodes only terminate their own path — other parallel branches continue
