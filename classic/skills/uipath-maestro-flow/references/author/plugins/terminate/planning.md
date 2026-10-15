# Terminate Node — Planning

## Node Type

`core.logic.terminate`

## When to Use

Use a Terminate node to abort the entire flow immediately on a fatal error. Unlike End, Terminate kills all branches.

### Selection Heuristics

| Situation | Use Terminate? |
| --- | --- |
| Fatal error — continuing other branches would be harmful | Yes |
| Normal completion of one execution path | No — use [End](../end/planning.md) |

## Ports

| Input Port | Output Port(s) |
| --- | --- |
| `input` | — (none) |

## Key Rules

- Terminate stops the entire workflow immediately — all parallel branches are killed
- No output mapping — Terminate does not produce workflow outputs
- Use for error paths where recovery is not possible
- **End vs Terminate:** End = graceful completion of one path. Terminate = abort everything.
