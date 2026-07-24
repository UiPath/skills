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
- `outputDefinition` — always `error` (`source: "=Error"`). Whether it also declares `output` varies **per published API workflow**: some declare `output` with `source: "=this"`, some declare only `error`. Read it for the node type you are wiring and mirror what it declares (see § JSON Structure)

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
      "source": "=Error",
      "var": "error"
    }
  }
}
```

**Mirror the registry's `outputDefinition` — never invent a `source`.** Keep `outputs` non-empty (the converter skips an empty/absent `outputs` entirely) and author `output` only when the registry declares it, copying its `source: "=this"`. When the registry declares `error` only, omit `output`: the converter then injects `{name: "output", type: "jsonSchema", source: "=this", var: "output"}` — but only when the instance omits it.

Author `output` with any other `source` and the converter copies it verbatim. `"=result.response"` (correct for connector activities) resolves to nothing on an Orchestrator activity, so `$vars.{nodeId}.output` is **null at runtime** while `flow validate` passes. A downstream agent binding it as a required object then dies at startup: `AGENT_STARTUP.INPUT_VALIDATION_ERROR`, incident `170002`. Downstream reads `$vars.{nodeId}.output` in every one of these cases.

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
| Node Completed but `$vars.{nodeId}.output` is null downstream (e.g. consumer agent faults `AGENT_STARTUP.INPUT_VALIDATION_ERROR` / incident `170002`) | Instance hand-declares `outputs.output` with `source: "=result.response"`, suppressing the converter's injected `=this` output | Set the `source` to `=this`, or delete the `output` entry and let the converter inject it (see § JSON Structure) |
