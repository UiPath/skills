# Flow Node — Implementation

Flow nodes invoke other published flows as subprocesses. Pattern: `uipath.core.flow.{key}`.

## Discovery

```bash
uip flow registry pull --force
uip flow registry search "uipath.core.flow" --output json
```

## Registry Validation

```bash
uip flow registry get "uipath.core.flow.{key}" --output json
```

Confirm:

- Input port: `input`
- Output port: `output`
- `model.serviceType` — `Orchestrator.StartAgenticProcess`
- `model.bindings.resourceSubType` — `Flow`
- `inputDefinition` — typically empty
- `outputDefinition.error` — error schema

## Adding / Editing

For step-by-step add, delete, and wiring procedures, see [flow-editing-operations.md](../../flow-editing-operations.md). Use the JSON structure below for the node-specific `inputs` and `model` fields.

## JSON Structure

### Node instance (inside `nodes[]`)

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
  },
  "model": {
    "type": "bpmn:ServiceTask",
    "serviceType": "Orchestrator.StartAgenticProcess",
    "version": "v2",
    "section": "Published",
    "bindings": {
      "resource": "process",
      "resourceSubType": "Flow",
      "resourceKey": "Shared.Validate Data Flow",
      "orchestratorType": "flow",
      "values": {
        "name": "Validate Data Flow",
        "folderPath": "Shared"
      }
    },
    "context": [
      { "name": "name",       "type": "string", "value": "=bindings.bValidateDataName",       "default": "Validate Data Flow" },
      { "name": "folderPath", "type": "string", "value": "=bindings.bValidateDataFolderPath", "default": "Shared" },
      { "name": "_label",     "type": "string", "value": "Validate Data Flow" }
    ]
  }
}
```

> `resourceKey` takes the form `<FolderPath>.<FlowName>` — confirm the exact value from `uip flow registry get` output.

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

> **Why both are required.** The registry's `Data.Node.model.context[].value` fields ship as template placeholders (`<bindings.name>`, `<bindings.folderPath>`) — not runtime-resolvable expressions. The runtime reads the node instance's `model.context` and resolves `=bindings.<id>` against the top-level `bindings[]` array. Without these two pieces, `uip flow validate` passes but `uip flow debug` fails with "Folder does not exist or the user does not have access to the folder."

> **Definition stays verbatim.** Do NOT rewrite `<bindings.*>` placeholders inside the `definitions` entry — it is a schema copy, not a runtime input. Critical Rule #7 applies unchanged.

## Debug

| Error | Cause | Fix |
| --- | --- | --- |
| Node type not found in registry | Flow not published or registry stale | Run `uip login` then `uip flow registry pull --force` |
| Flow execution failed | Underlying flow errored | Check `$vars.{nodeId}.error` for details |
