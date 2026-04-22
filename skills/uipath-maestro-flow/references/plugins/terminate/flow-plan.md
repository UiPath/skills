# Terminate Node

## Node Type

`core.logic.terminate`

## When to Use

Use a Terminate node to abort the entire flow immediately on a fatal error. Unlike End, Terminate kills all branches.

### Selection Heuristics

| Situation | Use Terminate? |
| --- | --- |
| Fatal error — continuing other branches would be harmful | Yes |
| Normal completion of one execution path | No — use [End](../end/flow-plan.md) |

## Ports

| Input Port | Output Port(s) |
| --- | --- |
| `input` | — (none) |

## Key Rules

- Terminate stops the entire workflow immediately — all parallel branches are killed
- No output mapping — Terminate does not produce workflow outputs
- Use for error paths where recovery is not possible
- **End vs Terminate:** End = graceful completion of one path. Terminate = abort everything.

## Registry Validation

```bash
uip maestro flow registry get core.logic.terminate --output json
```

Confirm: input port `input`, no output ports.

## Adding / Editing

For step-by-step add, delete, and wiring procedures, see [flow-editing-operations.md](../../flow-editing-operations.md). Use the JSON structure below for the node-specific `inputs` and `model` fields.

## JSON Structure

```json
{
  "id": "abortOnError",
  "type": "core.logic.terminate",
  "typeVersion": "1.0.0",
  "display": { "label": "Abort" },
  "inputs": {},
  "model": { "type": "bpmn:EndEvent" }
}
```

## Common Pattern — Error Handler

```text
HTTP Request -> Decision (error?) -> true -> Log Error (Script) -> Terminate
                                  -> false -> Process -> End
```

The Decision node checks `$vars.httpCall.error`, routes to a Script that logs the error, then Terminate aborts the flow.

## Debug

| Error | Cause | Fix |
| --- | --- | --- |
| Terminate has outgoing edges | Wired an edge from Terminate to another node | Remove — Terminate has no output ports |
| Workflow outputs missing | Expected outputs but hit Terminate | Terminate does not produce outputs — use End for paths that need output mapping |
