# Agentic Process Node — Implementation

Agentic process nodes invoke orchestration processes. Pattern: `uipath.core.agentic-process.{key}`.

## Discovery

<!--skill-flavor:agentic-process-impl-discovery:start-->
### Published (tenant registry)

```bash
uip maestro flow registry pull --force
uip maestro flow registry search "uipath.core.agentic-process" --output json
```

### In-solution (sibling projects)

```bash
uip maestro flow registry list --local --output json
uip maestro flow registry get "<node-type>" --local --output json
```
<!--skill-flavor:agentic-process-impl-discovery:end-->

## Registry Validation

<!--skill-flavor:agentic-process-impl-registry-get:start-->
```bash
# Published
uip maestro flow registry get "uipath.core.agentic-process.{key}" --output json

# In-solution
uip maestro flow registry get "uipath.core.agentic-process.{key}" --local --output json
```
<!--skill-flavor:agentic-process-impl-registry-get:end-->

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
  "typeVersion": "<DEFINITION_VERSION>",
  "display": { "label": "Run Orchestration" },
  "inputs": {},
  "outputs": {
    "error": {
      "type": "object",
      "description": "Error information if the agentic process fails",
      "source": "=Error",
      "var": "error"
    }
  }
}
```

**Declare `error` only — `output` is derived.** Authoring it makes the converter copy your `source` verbatim; `"=result.response"` then resolves to null at runtime while `flow validate` passes. See [file-format.md § Node outputs](../../../shared/file-format.md#node-outputs).

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

> For the resolution mechanics and why these entries are required, see [file-format.md — Bindings](../../../shared/file-format.md#bindings--orchestrator-resource-bindings-top-level-bindings).

## Debug

<!--skill-flavor:agentic-process-impl-debug-table:start-->
| Error | Cause | Fix |
| --- | --- | --- |
| Node type not found in registry | Process not published or registry stale | Run `uip login` then `uip maestro flow registry pull --force`; for in-solution processes use `--local` |
| Process execution failed | Underlying orchestration errored | Check `$vars.{nodeId}.error` for details |
<!--skill-flavor:agentic-process-impl-debug-table:end-->
