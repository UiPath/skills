# Terminate Node — Implementation

## Node Type

`core.logic.terminate`

## Registry Validation

```bash
uip flow registry get core.logic.terminate --output json
```

Confirm: input port `input`, no output ports.

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

## Adding via CLI

```bash
uip flow node add <ProjectName>.flow core.logic.terminate --output json \
  --label "Abort" \
  --position 700,500
```

## Common Pattern — Error Handler

```
HTTP Request -> Decision (error?) -> true -> Log Error (Script) -> Terminate
                                  -> false -> Process -> End
```

The Decision node checks `$vars.httpCall.error`, routes to a Script that logs the error, then Terminate aborts the flow.

## Debug

| Error | Cause | Fix |
| --- | --- | --- |
| Terminate has outgoing edges | Wired an edge from Terminate to another node | Remove — Terminate has no output ports |
| Workflow outputs missing | Expected outputs but hit Terminate | Terminate does not produce outputs — use End for paths that need output mapping |
