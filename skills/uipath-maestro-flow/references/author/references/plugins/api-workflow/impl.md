# API Workflow Node — Implementation

API workflow nodes invoke API functions. Pattern: `uipath.core.api-workflow.{key}`.

## Discovery

### Published (tenant registry)

```bash
uip maestro flow registry pull --force
uip maestro flow registry search "uipath.core.api-workflow" --output json
```

### In-solution (sibling projects)

```bash
uip maestro flow registry list --local --output json
uip maestro flow registry get "<node-type>" --local --output json
```

## Registry Validation

```bash
# Published
uip maestro flow registry get "uipath.core.api-workflow.{key}" --output json

# In-solution
uip maestro flow registry get "uipath.core.api-workflow.{key}" --local --output json
```

Confirm:

- Input port: `input`
- Output port: `output`
- `model.serviceType` — `Orchestrator.ExecuteApiWorkflowAsync`
- `model.bindings.resourceSubType` — `Api`
- `model.bindings.resourceKey` — the `<FolderPath>.<ApiName>` string used to scope binding resolution
- `inputDefinition` — typically empty
- `outputDefinition.error` — error schema. This node type declares **no `output`** — do not author one (see § JSON Structure)

## Adding / Editing

For step-by-step add, delete, and wiring procedures, see [editing-operations.md](../../editing-operations.md). Use the JSON structure below for the node-specific `inputs`.

## JSON Structure

### Node instance (inside `nodes[]`)

The instance carries only per-instance data (`inputs`, `outputs`, `display`). BPMN type, serviceType, version, and binding/context templates come from the definition in `definitions[]`.

```json
{
  "id": "callApiFunction",
  "type": "uipath.core.api-workflow.346b8959-c126-48d3-9c46-942abcf944d7",
  "typeVersion": "<DEFINITION_VERSION>",
  "display": { "label": "Call API Function" },
  "inputs": {},
  "outputs": {
    "error": {
      "type": "object",
      "description": "Error information if the API workflow fails",
      "source": "=result.Error",
      "var": "error"
    }
  }
}
```

**Declare `error` only — never author an `output` entry.** The converter injects the return-value output itself (`{name: "output", type: "jsonSchema", source: "=this", var: "output"}`) and only when the instance omits `outputs.output`. Author `output` yourself and the converter copies your `source` verbatim: `"=result.response"` resolves to nothing on this activity, so `$vars.{nodeId}.output` is **null at runtime** while `flow validate` still passes. A downstream agent binding it as a required object then dies at startup — `AGENT_STARTUP.INPUT_VALIDATION_ERROR`, surfaced as flow incident `170002`.

Downstream nodes read the return value as `$vars.{nodeId}.output` either way. General rule: author only the output keys the registry's `outputDefinition` declares — for this node type, that is `error`.

### Top-level `bindings[]` entries (sibling of `nodes`/`edges`/`definitions`)

Add one entry per `(resourceKey, propertyAttribute)` pair. Share entries across node instances that reference the same API workflow — do NOT create duplicates.

```json
"bindings": [
  {
    "id": "bCallApiFunctionName",
    "name": "name",
    "type": "string",
    "resource": "process",
    "resourceKey": "Shared.My API Function",
    "default": "My API Function",
    "propertyAttribute": "name",
    "resourceSubType": "Api"
  },
  {
    "id": "bCallApiFunctionFolderPath",
    "name": "folderPath",
    "type": "string",
    "resource": "process",
    "resourceKey": "Shared.My API Function",
    "default": "Shared",
    "propertyAttribute": "folderPath",
    "resourceSubType": "Api"
  }
]
```

> For the resolution mechanics and why these entries are required, see [file-format.md — Bindings](../../../../shared/file-format.md#bindings--orchestrator-resource-bindings-top-level-bindings).

## Debug

| Error | Cause | Fix |
| --- | --- | --- |
| Node type not found in registry | API workflow not published or registry stale | Run `uip login` then `uip maestro flow registry pull --force`; for in-solution API workflows use `--local` |
| Execution failed | Underlying API workflow errored | Check `$vars.{nodeId}.error` for details |
| Node Completed but `$vars.{nodeId}.output` is null downstream (e.g. consumer agent faults `AGENT_STARTUP.INPUT_VALIDATION_ERROR` / incident `170002`) | Instance hand-declares `outputs.output` with `source: "=result.response"`, suppressing the converter's injected `=this` output | Delete the `output` entry — keep `error` only (see § JSON Structure) |
