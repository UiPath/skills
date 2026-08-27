# Merge Node — Planning

## Node Type

`core.logic.merge`

## Use

Use a Merge node to synchronize two or more parallel branches before continuing. It waits for all incoming paths to complete.

- Use it when parallel branches must rejoin or after one node forks into multiple downstream branches.
- Do not use it for sequential pipelines; wire nodes directly.

## Ports

| Input Port | Output Port(s) |
| --- | --- |
| `input` (accepts multiple connections) | `output` |

## Wiring Rules

- Connect each parallel branch’s terminal node to the Merge node’s `input` port; multiple incoming edges may use the same port.
- Execution continues from `output` only after all incoming paths complete.