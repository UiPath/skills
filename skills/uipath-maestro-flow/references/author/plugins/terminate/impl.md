# Terminate Node — Implementation

## Node Type

`core.logic.terminate`

## Registry Validation

```bash
uip maestro flow registry get core.logic.terminate --output json
```

Confirm: input port `input`, no output ports. Set the node instance `typeVersion` to the `version` field from this response — do not hardcode it.

## JSON Structure

```json
{
  "id": "abortOnError",
  "type": "core.logic.terminate",
  "typeVersion": "<DEFINITION_VERSION>",
  "display": { "label": "Abort" },
  "inputs": {}
}
```

## Adding / Editing

For step-by-step add, delete, and wiring procedures, see [editing-operations.md](../../editing-operations.md). Use the JSON structure above for the node-specific `inputs`.

## Common Pattern — Error Handler

```text
HTTP Request
  |-- default -> Process -> End
  |-- error   -> Log Error (Script) -> Terminate
```

Wire the action node's implicit `error` source port straight to the handler; the Script logs `$vars.httpCall.error`, then Terminate aborts the flow. Do **not** put a Decision downstream to test for an error — a failing node has already faulted the flow before execution reaches it.

Add this pattern only when the requirements state what a failure should do. With no error edge the failure faults the flow on its own, which is the correct default — and never set `inputs.errorHandlingEnabled: true` without the edge. See [file-format.md — Implicit error port on action nodes](../../../shared/file-format.md#implicit-error-port-on-action-nodes).

## Debug

| Error | Cause | Fix |
| --- | --- | --- |
| Terminate has outgoing edges | Wired an edge from Terminate to another node | Remove — Terminate has no output ports |
| Workflow outputs missing | Expected outputs but hit Terminate | Terminate does not produce outputs — use End for paths that need output mapping |
