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
HTTP Request -> Decision (error?) -> true -> Log Error (Script) -> Terminate
                                  -> false -> Process -> End
```

The Decision node checks `$vars.httpCall.error`, routes to a Script that logs the error, then Terminate aborts the flow.

## Debug

| Error | Cause | Fix |
| --- | --- | --- |
| Terminate has outgoing edges | Wired an edge from Terminate to another node | Remove — Terminate has no output ports |
| Workflow outputs missing | Expected outputs but hit Terminate | Terminate does not produce outputs — use End for paths that need output mapping |
