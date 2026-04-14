# Agentic Process Node — Implementation

Agentic process nodes invoke published orchestration processes. Pattern: `uipath.core.agentic-process.{key}`.

## Discovery

```bash
uip flow registry pull --force
uip flow registry search "uipath.core.agentic-process" --output json
```

## Registry Validation

```bash
uip flow registry get "uipath.core.agentic-process.{key}" --output json
```

Confirm:

- Input port: `input`
- Output port: `output`
- `model.serviceType` — `Orchestrator.StartAgenticProcess`
- `model.bindings.resourceSubType` — `ProcessOrchestration`
- `inputDefinition` — typically empty
- `outputDefinition.error` — error schema

## Adding / Editing

For step-by-step add, delete, and wiring procedures, see [flow-editing-operations.md](../../flow-editing-operations.md). Use the JSON structure below for the node-specific `inputs` and `model` fields.

## JSON Structure

```json
{
  "id": "runOrchestration",
  "type": "uipath.core.agentic-process.5f9ad95a-b862-46c7-98c3-a9be2e5b922f",
  "typeVersion": "1.0.0",
  "ui": { "position": { "x": 400, "y": 300 } },
  "display": { "label": "Run Orchestration" },
  "inputs": {},
  "outputs": {
    "output": {
      "type": "object",
      "description": "The return value of the agentic process",
      "source": "=result.response",
      "var": "output"
    },
    "error": {
      "type": "object",
      "description": "Error information if the agentic process fails",
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
      "resourceSubType": "ProcessOrchestration",
      "resourceKey": "Shared.My Orchestration",
      "orchestratorType": "agentic-process",
      "values": {
        "name": "My Orchestration",
        "folderPath": "Shared"
      }
    }
  }
}
```

## Debug

| Error | Cause | Fix |
| --- | --- | --- |
| Node type not found in registry | Process not published or registry stale | Run `uip login` then `uip flow registry pull --force` |
| Process execution failed | Underlying orchestration errored | Check `$vars.{nodeId}.error` for details |
