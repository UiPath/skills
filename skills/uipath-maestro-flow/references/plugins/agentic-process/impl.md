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

### Node instance (inside `nodes[]`)

```json
{
  "id": "runOrchestration",
  "type": "uipath.core.agentic-process.5f9ad95a-b862-46c7-98c3-a9be2e5b922f",
  "typeVersion": "1.0.0",
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
    "section": "Published",
    "bindings": {
      "resource": "process",
      "resourceSubType": "ProcessOrchestration",
      "resourceKey": "Shared.My Orchestration",
      "orchestratorType": "agentic-process",
      "values": {
        "name": "My Orchestration",
        "folderPath": "Shared"
      }
    },
    "context": [
      { "name": "name",       "type": "string", "value": "=bindings.bRunOrchestrationName",       "default": "My Orchestration" },
      { "name": "folderPath", "type": "string", "value": "=bindings.bRunOrchestrationFolderPath", "default": "Shared" },
      { "name": "_label",     "type": "string", "value": "My Orchestration" }
    ]
  }
}
```

> `resourceKey` takes the form `<FolderPath>.<ProcessName>` — confirm the exact value from `uip flow registry get` output.

### Top-level `bindings[]` entries (sibling of `nodes`/`edges`/`definitions`)

Add one entry per `(resourceKey, propertyAttribute)` pair. Share entries across node instances that reference the same agentic process — do NOT create duplicates.

```json
"bindings": [
  {
    "id": "bRunOrchestrationName",
    "name": "name",
    "type": "string",
    "resource": "process",
    "resourceKey": "Shared.My Orchestration",
    "default": "My Orchestration",
    "propertyAttribute": "name",
    "resourceSubType": "ProcessOrchestration"
  },
  {
    "id": "bRunOrchestrationFolderPath",
    "name": "folderPath",
    "type": "string",
    "resource": "process",
    "resourceKey": "Shared.My Orchestration",
    "default": "Shared",
    "propertyAttribute": "folderPath",
    "resourceSubType": "ProcessOrchestration"
  }
]
```

> **Why both are required.** The registry's `Data.Node.model.context[].value` fields ship as template placeholders (`<bindings.name>`, `<bindings.folderPath>`) — not runtime-resolvable expressions. The runtime reads the node instance's `model.context` and resolves `=bindings.<id>` against the top-level `bindings[]` array. Without these two pieces, `uip flow validate` passes but `uip flow debug` fails with "Folder does not exist or the user does not have access to the folder."

> **Definition stays verbatim.** Do NOT rewrite `<bindings.*>` placeholders inside the `definitions` entry — it is a schema copy, not a runtime input. Critical Rule #7 applies unchanged.

## Debug

| Error | Cause | Fix |
| --- | --- | --- |
| Node type not found in registry | Process not published or registry stale | Run `uip login` then `uip flow registry pull --force` |
| Process execution failed | Underlying orchestration errored | Check `$vars.{nodeId}.error` for details |
