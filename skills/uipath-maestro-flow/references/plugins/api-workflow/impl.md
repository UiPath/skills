# API Workflow Node — Implementation

API workflow nodes invoke API functions. Pattern: `uipath.core.api-workflow.{key}`.

## Discovery

**Published (tenant registry):**

```bash
uip maestro flow registry pull --force
uip maestro flow registry search "uipath.core.api-workflow" --output json
```

**In-solution (local, no login required):**

```bash
uip maestro flow registry list --local --output json
uip maestro flow registry get "<nodeType>" --local --output json
```

## Registry Validation

**Published:**

```bash
uip maestro flow registry get "uipath.core.api-workflow.{key}" --output json
```

**In-solution (local):**

```bash
uip maestro flow registry get "uipath.core.api-workflow.{key}" --local --output json
```

Confirm:

- Input port: `input`
- Output port: `output`
- `model.serviceType` — `Orchestrator.ExecuteApiWorkflowAsync`
- `model.bindings.resourceSubType` — `Api`
- `inputDefinition` — typically empty
- `outputDefinition.error` — error schema

## Adding / Editing

For step-by-step add, delete, and wiring procedures, see [flow-editing-operations.md](../../flow-editing-operations.md). Use the JSON structure below for the node-specific `inputs` and `model` fields.

## JSON Structure

```json
{
  "id": "callApiFunction",
  "type": "uipath.core.api-workflow.346b8959-c126-48d3-9c46-942abcf944d7",
  "typeVersion": "1.0.0",
  "display": { "label": "Call API Function" },
  "inputs": {},
  "outputs": {
    "output": {
      "type": "object",
      "description": "The return value of the API workflow",
      "source": "=result.response",
      "var": "output"
    },
    "error": {
      "type": "object",
      "description": "Error information if the API workflow fails",
      "source": "=result.Error",
      "var": "error"
    }
  },
  "model": {
    "type": "bpmn:ServiceTask",
    "serviceType": "Orchestrator.ExecuteApiWorkflowAsync",
    "version": "v2",
    "bindings": {
      "resource": "process",
      "resourceSubType": "Api",
      "resourceKey": "Shared.My API Function",
      "orchestratorType": "api-workflow",
      "values": {
        "name": "My API Function",
        "folderPath": "Shared"
      }
    }
  }
}
```

## Debug

| Error | Cause | Fix |
| --- | --- | --- |
| Node type not found in registry | API workflow not published or registry stale | If in same solution: run `registry list --local`. Otherwise: run `uip login` then `uip maestro flow registry pull --force` |
| Execution failed | Underlying API workflow errored | Check `$vars.{nodeId}.error` for details |
