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

## Adding / Editing

For step-by-step add, delete, and wiring procedures, see [flow-editing-operations.md](../../flow-editing-operations.md). Use the JSON structure below for the node-specific `inputs` and `model` fields.

**This node type needs top-level `bindings[]` entries.** `uipath.core.api-workflow.*` is a resource node — it invokes a published API workflow, and the runtime resolves the target via two process-style bindings in the flow's top-level `bindings[]` array (regenerated into `bindings_v2.json` at `flow debug`/`flow pack` time). The CLI's `flow node add` wires these automatically; when hand-writing JSON, follow the [Resource Node Bindings](../../flow-editing-operations-json.md#resource-node-bindings-direct-json) procedure. **For API workflow nodes:** `resourceSubType = "Api"`, `orchestratorType = "api"`.

## JSON Structure

A complete API workflow node requires three pieces in the `.flow` file:

1. The **node entry** in `nodes[]` (with `model.bindings` and `model.context[]`)
2. Two **top-level bindings** in `bindings[]` (one for `name`, one for `folderPath`)
3. The **definition** in `definitions[]` (copied verbatim from `uip flow registry get`)

### Node entry

```json
{
  "id": "callApiFunction",
  "type": "uipath.core.api-workflow.374783dd-a097-497c-8bf8-c4226940c798",
  "typeVersion": "1.0.0",
  "display": { "label": "Call API Function" },
  "inputs": {},
  "model": {
    "type": "bpmn:ServiceTask",
    "serviceType": "Orchestrator.ExecuteApiWorkflowAsync",
    "version": "v2",
    "section": "Published",
    "bindings": {
      "resource": "process",
      "resourceSubType": "Api",
      "resourceKey": "Shared/NameToAge APIWF.API Workflow",
      "orchestratorType": "api",
      "values": {
        "name": "API Workflow",
        "folderPath": "Shared/NameToAge APIWF"
      }
    },
    "context": [
      { "name": "name", "type": "string", "value": "=bindings.bRvY4IVSo", "default": "API Workflow" },
      { "name": "folderPath", "type": "string", "value": "=bindings.bqTxLRQ2K", "default": "Shared/NameToAge APIWF" },
      { "name": "_label", "type": "string", "value": "API Workflow" }
    ]
  }
}
```

- `resourceKey`, `name`, `folderPath` come from `Data.Node.model.bindings` in `uip flow registry get` — copy verbatim, don't paraphrase the path.
- `orchestratorType` is `"api"` (not `"api-workflow"`) — this comes from the registry manifest; copy it verbatim.
- `context[]` values must use `=bindings.<id>` where `<id>` matches an entry in the flow's top-level `bindings[]` (next block).
- `inputs` keys must match `Data.Node.inputDefinition.properties` from `registry get`.

### Top-level `bindings[]` entries

Append these two entries to the flow's top-level `bindings[]` array (sibling of `nodes`, `edges`, `definitions`):

```json
{
  "id": "bRvY4IVSo",
  "name": "name",
  "type": "string",
  "resource": "process",
  "resourceKey": "Shared/NameToAge APIWF.API Workflow",
  "default": "API Workflow",
  "propertyAttribute": "name",
  "resourceSubType": "Api"
},
{
  "id": "bqTxLRQ2K",
  "name": "folderPath",
  "type": "string",
  "resource": "process",
  "resourceKey": "Shared/NameToAge APIWF.API Workflow",
  "default": "Shared/NameToAge APIWF",
  "propertyAttribute": "folderPath",
  "resourceSubType": "Api"
}
```

- The two `id`s must match the `=bindings.<id>` references inside the node's `model.context[]`.
- `resourceKey` must equal the `resourceKey` in the node's `model.bindings`.
- If another api-workflow node in the same flow targets the same published function (same `resourceKey`), reuse these two binding entries — do not duplicate.

See [Resource Node Bindings](../../flow-editing-operations-json.md#resource-node-bindings-direct-json) for the general procedure shared across agent / rpa-workflow / api-workflow nodes.

## Debug

| Error | Cause | Fix |
| --- | --- | --- |
| Node type not found in registry | API workflow not published or registry stale | Run `uip login` then `uip flow registry pull --force` |
| Execution failed | Underlying API workflow errored | Check `$vars.{nodeId}.error` for details |
