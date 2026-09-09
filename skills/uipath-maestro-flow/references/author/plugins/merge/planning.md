# Merge Node — Planning

## Node Type

`core.logic.merge`

## Use

Use a Merge node to synchronize two or more parallel branches before continuing. It waits for all incoming paths to complete.

- Use it when parallel branches must rejoin or after one node forks into multiple downstream branches.
- Do not use it for sequential pipelines; wire nodes directly.
- Do not use it to join the `true`/`false` branches of one Decision (or the cases of one Switch); wire both ports straight into the next node, which accepts several incoming edges. A Merge waits for ALL inputs and a Decision emits exactly one, so the run would hang forever; `flow validate` refuses this shape.

## Ports

| Input Port | Output Port(s) |
| --- | --- |
| `input` (accepts multiple connections) | `output` |

## Wiring Rules

- Connect each parallel branch's terminal node to the Merge node's `input` port; multiple incoming edges may use the same port.
- Execution continues from `output` only after all incoming paths complete.