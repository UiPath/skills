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
- `outputDefinition` — always `error` (`source: "=Error"`). Whether it also declares `output` varies per published API workflow; either way, do not author `output` on the instance (see § JSON Structure)

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

**Declare `error` only — `output` is derived.** The converter injects `{name: "output", type: "jsonSchema", source: "=this", var: "output"}` whenever a non-empty `outputs` omits `output`; Studio Web writes the block that way too. Downstream reads `$vars.{nodeId}.output` either way.

Authoring `output` is the trap: for Orchestrator-job nodes the converter copies your `source` verbatim, so `"=result.response"` — correct only on connector and script/transform nodes — leaves `$vars.{nodeId}.output` **null at runtime** while `flow validate` passes. A downstream agent binding it as a required object then dies at startup: `AGENT_STARTUP.INPUT_VALIDATION_ERROR`, incident `170002`.

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
