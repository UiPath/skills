# RPA Node — Implementation

RPA nodes invoke published RPA processes. Pattern: `uipath.core.rpa-workflow.{key}`.

## Discovery

```bash
uip flow registry pull --force
uip flow registry search "uipath.core.rpa-workflow" --output json
```

## Registry Validation

```bash
uip flow registry get "uipath.core.rpa-workflow.{key}" --output json
```

Confirm:

- Input port: `input`
- Output port: `output`
- `model.serviceType` — `Orchestrator.StartJob`
- `model.bindings.resourceSubType` — `Process`
- `inputDefinition` — may contain typed input fields (check `properties`)
- `outputDefinition.output` — process return value
- `outputDefinition.error` — error schema

## Adding / Editing

For step-by-step add, delete, and wiring procedures, see [flow-editing-operations.md](../../flow-editing-operations.md). Use the JSON structure below for the node-specific `inputs` and `model` fields.

**This node type needs top-level `bindings[]` entries.** `uipath.core.rpa-workflow.*` is a resource node — it invokes a published Orchestrator process, and the runtime resolves the target via two process-style bindings in the flow's top-level `bindings[]` array (regenerated into `bindings_v2.json` at `flow debug`/`flow pack` time). The CLI's `flow node add` wires these automatically; when hand-writing JSON, follow the [Resource Node Bindings](../../flow-editing-operations-json.md#resource-node-bindings-direct-json) procedure. **For RPA workflow nodes:** `resourceSubType = "Process"`, `orchestratorType = "process"`.

## JSON Structure

A complete RPA workflow node requires three pieces in the `.flow` file:

1. The **node entry** in `nodes[]` (with `model.bindings` and `model.context[]`)
2. Two **top-level bindings** in `bindings[]` (one for `name`, one for `folderPath`)
3. The **definition** in `definitions[]` (copied verbatim from `uip flow registry get`)

### Node entry

```json
{
  "id": "processInvoices",
  "type": "uipath.core.rpa-workflow.f5a7f387-1f3b-4111-b758-e2514f770e3e",
  "typeVersion": "1.0.0",
  "display": { "label": "Process Invoices" },
  "inputs": {
    "documentPath": "=js:$vars.fileLocation",
    "batchSize": 50
  },
  "model": {
    "type": "bpmn:ServiceTask",
    "serviceType": "Orchestrator.StartJob",
    "version": "v2",
    "section": "Published",
    "bindings": {
      "resource": "process",
      "resourceSubType": "Process",
      "resourceKey": "Finance/Automation.Invoice Processor",
      "orchestratorType": "process",
      "values": {
        "name": "Invoice Processor",
        "folderPath": "Finance/Automation"
      }
    },
    "context": [
      { "name": "name", "type": "string", "value": "=bindings.bBsXAJft1", "default": "Invoice Processor" },
      { "name": "folderPath", "type": "string", "value": "=bindings.b7e1mNnOV", "default": "Finance/Automation" },
      { "name": "_label", "type": "string", "value": "Invoice Processor" }
    ]
  }
}
```

- `resourceKey`, `name`, `folderPath` come from `Data.Node.model.bindings` in `uip flow registry get` — copy verbatim, don't paraphrase the path.
- `context[]` values must use `=bindings.<id>` where `<id>` matches an entry in the flow's top-level `bindings[]` (next block).
- `inputs` keys must match `Data.Node.inputDefinition.properties` from `registry get`.

### Top-level `bindings[]` entries

Append these two entries to the flow's top-level `bindings[]` array (sibling of `nodes`, `edges`, `definitions`):

```json
{
  "id": "bBsXAJft1",
  "name": "name",
  "type": "string",
  "resource": "process",
  "resourceKey": "Finance/Automation.Invoice Processor",
  "default": "Invoice Processor",
  "propertyAttribute": "name",
  "resourceSubType": "Process"
},
{
  "id": "b7e1mNnOV",
  "name": "folderPath",
  "type": "string",
  "resource": "process",
  "resourceKey": "Finance/Automation.Invoice Processor",
  "default": "Finance/Automation",
  "propertyAttribute": "folderPath",
  "resourceSubType": "Process"
}
```

- The two `id`s must match the `=bindings.<id>` references inside the node's `model.context[]`.
- `resourceKey` must equal the `resourceKey` in the node's `model.bindings`.
- If another RPA node in the same flow targets the same published process (same `resourceKey`), reuse these two binding entries — do not duplicate.

See [Resource Node Bindings](../../flow-editing-operations-json.md#resource-node-bindings-direct-json) for the general procedure shared across agent / rpa-workflow / api-workflow nodes.

## Mock Placeholder (If Not Yet Published)

If the RPA process is not yet published, add a `core.logic.mock` placeholder and tell the user to create it with `uipath-rpa`. After publishing, follow the [mock replacement procedure](../../flow-editing-operations-cli.md#replace-a-mock-with-a-real-resource-node) to swap the mock for the real resource node.

## Debug

| Error | Cause | Fix |
| --- | --- | --- |
| Node type not found in registry | Process not published or registry stale | Run `uip login` then `uip flow registry pull --force` |
| Input schema mismatch | Inputs don't match `inputDefinition` | Run `registry get` and check required inputs in `inputDefinition.properties` |
| Process execution failed | Underlying RPA process errored | Check `$vars.{nodeId}.error` for details |
| Mock placeholder still in flow | Process not yet replaced | Follow the mock replacement workflow above |
