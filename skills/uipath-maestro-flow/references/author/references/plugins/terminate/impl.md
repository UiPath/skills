# Terminate Node — Implementation

## Node Type

`core.logic.terminate`

## Registry Validation

Run:

```bash
uip maestro flow registry get core.logic.terminate --output json
```

Confirm the input port is `input` and there are no output ports. Set the node instance `typeVersion` to the response's `version` field; do not hardcode it.

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

For add, delete, and wiring procedures, see [editing-operations.md](../../editing-operations.md). Use the structure above for node-specific `inputs`.

## Common Pattern — Error Handler

```text
HTTP Request
  |-- default -> Process -> End
  |-- error   -> Log Error (Script) -> Terminate
```

Wire the action node's implicit `error` source port directly to the handler. Have the Script log `$vars.httpCall.error`, then use Terminate to abort the flow. Do not put a Decision downstream to test for an error: a failing node has already faulted the flow before execution reaches it.

Add this pattern only when requirements specify failure behavior. Without an error edge, failure faults the flow on its own, which is the correct default. Never set `inputs.errorHandlingEnabled: true` without the edge. See [file-format.md — Implicit error port on action nodes](../../../../shared/file-format.md#implicit-error-port-on-action-nodes).

## Debug

| Error | Cause | Fix |
| --- | --- | --- |
| Terminate has outgoing edges | An edge was wired from Terminate | Remove it; Terminate has no output ports |
| Workflow outputs missing | Terminate was reached where outputs were expected | Use End for paths that need output mapping; Terminate does not produce outputs |