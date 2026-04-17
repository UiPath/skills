# Flow Node — Implementation

Flow nodes invoke other published flows as subprocesses. Pattern: `uipath.core.flow.{key}`.

## Discovery

```bash
uip flow registry pull --force
uip flow registry search "uipath.core.flow" --output json
```

## Registry Validation

```bash
uip flow registry get "uipath.core.flow.{key}" --output json
```

Confirm:

- Input port: `input`
- Output port: `output`
- `model.serviceType` — `Orchestrator.StartAgenticProcess`
- `model.bindings.resourceSubType` — `Flow`
- `inputDefinition` — typically empty
- `outputDefinition.error` — error schema

## Adding / Editing

For step-by-step add, delete, and wiring procedures, see [flow-editing-operations.md](../../flow-editing-operations.md). Use the JSON structure below for the node-specific `inputs` and `model` fields.

## JSON Structure

```json
{
  "id": "validateData",
  "type": "uipath.core.flow.629edef0-8ce8-428e-a922-3f8bf19ea682",
  "typeVersion": "1.0.0",
  "display": { "label": "Validate Data" },
  "inputs": {},
  "outputs": {
    "output": {
      "type": "object",
      "description": "The return value of the flow",
      "source": "=result.response",
      "var": "output"
    },
    "error": {
      "type": "object",
      "description": "Error information if the flow fails",
      "source": "=result.Error",
      "var": "error"
    }
  },
  "model": {
    "type": "bpmn:ServiceTask",
    "serviceType": "Orchestrator.StartAgenticProcess",
    "version": "v2",
    "bindings": {
      "resource": "process",
      "resourceSubType": "Flow",
      "resourceKey": "Shared.Validate Data Flow",
      "orchestratorType": "flow",
      "values": {
        "name": "Validate Data Flow",
        "folderPath": "Shared"
      }
    }
  }
}
```

## Debug

| Error | Cause | Fix |
| --- | --- | --- |
| Node type not found in registry | Flow not published or registry stale | Run `uip login` then `uip flow registry pull --force` |
| Flow execution failed | Underlying flow errored | Check `$vars.{nodeId}.error` for details |
