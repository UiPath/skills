# Agentic Process Node — Implementation

Agentic process nodes invoke orchestration processes. Pattern: `uipath.core.agentic-process.{key}`.

## Discovery

### Published (tenant registry)

```bash
uip maestro flow registry pull --force
uip maestro flow registry search "uipath.core.agentic-process" --output json
```

### In-solution (sibling projects)

```bash
uip maestro flow registry list --local --output json
uip maestro flow registry get "<nodeType>" --local --output json
```

## Registry Validation

```bash
# Published
uip maestro flow registry get "uipath.core.agentic-process.{key}" --output json

# In-solution
uip maestro flow registry get "uipath.core.agentic-process.{key}" --local --output json
```

Confirm:

- Input port: `input`
- Output port: `output`
- `model.serviceType` — `Orchestrator.StartAgenticProcess`
- `model.bindings.resourceSubType` — `ProcessOrchestration`
- `model.bindings.resourceKey` — the `<FolderPath>.<ProcessName>` string used to scope binding resolution
- `inputDefinition` — typically empty
- `outputDefinition.error` — error schema

## Adding / Editing

For step-by-step add, delete, and wiring procedures, see [editing-operations.md](../../editing-operations.md). Use the JSON structure below for the node-specific `inputs`.

## JSON Structure

### Node instance (inside `nodes[]`)

The instance carries only per-instance data (`inputs`, `outputs`, `display`). BPMN type, serviceType, version, and binding/context templates come from the definition in `definitions[]`.

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
  }
}
```

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

> For the resolution mechanics and why these entries are required, see [file-format.md — Bindings](../../file-format.md#bindings--orchestrator-resource-bindings-top-level-bindings).

## Debug

| Error | Cause | Fix |
| --- | --- | --- |
| Node type not found in registry | Process not published or registry stale | Run `uip login` then `uip maestro flow registry pull --force`; for in-solution processes use `--local` |
| Process execution failed | Underlying orchestration errored | Check `$vars.{nodeId}.error` for details |
