# Flow Node — Implementation

Flow nodes invoke other flows as subprocesses. Pattern: `uipath.core.flow.{key}`.

## Discovery

### Published (tenant registry)

```bash
uip maestro flow registry pull --force
uip maestro flow registry search "uipath.core.flow" --output json
```

### In-solution (sibling projects)

```bash
uip maestro flow registry list --local --output json
uip maestro flow registry get "<nodeType>" --local --output json
```

## Registry Validation

```bash
# Published
uip maestro flow registry get "uipath.core.flow.{key}" --output json

# In-solution
uip maestro flow registry get "uipath.core.flow.{key}" --local --output json
```

Confirm:

- Input port: `input`
- Output port: `output`
- `model.serviceType` — `Orchestrator.StartAgenticProcess` (shared with agentic-process nodes; `resourceSubType: "Flow"` differentiates)
- `model.bindings.resourceSubType` — `Flow`
- `model.bindings.resourceKey` — the `<FolderPath>.<FlowName>` string used to scope binding resolution
- `inputDefinition` — typically empty
- `outputDefinition.error` — error schema

## Adding / Editing

For step-by-step add, delete, and wiring procedures, see [editing-operations.md](../../editing-operations.md). Use the JSON structure below for the node-specific `inputs`.

## JSON Structure

### Node instance (inside `nodes[]`)

The instance carries only per-instance data (`inputs`, `outputs`, `display`). BPMN type, serviceType, version, and binding/context templates come from the definition in `definitions[]`.

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
  }
}
```

### Top-level `bindings[]` entries (sibling of `nodes`/`edges`/`definitions`)

Add one entry per `(resourceKey, propertyAttribute)` pair. Share entries across node instances that reference the same flow — do NOT create duplicates.

```json
"bindings": [
  {
    "id": "bValidateDataName",
    "name": "name",
    "type": "string",
    "resource": "process",
    "resourceKey": "Shared.Validate Data Flow",
    "default": "Validate Data Flow",
    "propertyAttribute": "name",
    "resourceSubType": "Flow"
  },
  {
    "id": "bValidateDataFolderPath",
    "name": "folderPath",
    "type": "string",
    "resource": "process",
    "resourceKey": "Shared.Validate Data Flow",
    "default": "Shared",
    "propertyAttribute": "folderPath",
    "resourceSubType": "Flow"
  }
]
```

> For the resolution mechanics and why these entries are required, see [file-format.md — Bindings](../../shared/file-format.md#bindings--orchestrator-resource-bindings-top-level-bindings).

## Debug

| Error | Cause | Fix |
| --- | --- | --- |
| Node type not found in registry | Flow not published or registry stale | Run `uip login` then `uip maestro flow registry pull --force`; for in-solution flows use `--local` |
| Flow execution failed | Underlying flow errored | Check `$vars.{nodeId}.error` for details |
