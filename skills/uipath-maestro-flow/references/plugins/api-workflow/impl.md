# API Workflow Node — Implementation

API workflow nodes invoke published API functions. Pattern: `uipath.core.api-workflow.{key}`.

## Discovery

```bash
uip flow registry pull --force
uip flow registry search "uipath.core.api-workflow" --output json
```

## Registry Validation

```bash
uip flow registry get "uipath.core.api-workflow.{key}" --output json
```

Confirm:

- Input port: `input`
- Output port: `output`
- `model.serviceType` — `Orchestrator.ExecuteApiWorkflowAsync`
- `model.bindings.resourceSubType` — `Api`
- `inputDefinition` — typically empty
- `outputDefinition.error` — error schema

## Adding via CLI

```bash
uip flow node add <ProjectName>.flow "uipath.core.api-workflow.{key}" --output json \
  --label "Call API Function" \
  --position 400,300
```

## JSON Structure

```json
{
  "id": "callApiFunction",
  "type": "uipath.core.api-workflow.346b8959-c126-48d3-9c46-942abcf944d7",
  "typeVersion": "1.0.0",
  "ui": { "position": { "x": 400, "y": 300 } },
  "display": { "label": "Call API Function" },
  "inputs": {},
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
| Node type not found in registry | API workflow not published or registry stale | Run `uip login` then `uip flow registry pull --force` |
| Execution failed | Underlying API workflow errored | Check `$vars.{nodeId}.error` for details |
