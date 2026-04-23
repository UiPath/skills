# RPA Node — Implementation

RPA nodes invoke RPA processes. Pattern: `uipath.core.rpa-workflow.{key}`.

## Discovery

**Published (tenant registry):**

```bash
uip maestro flow registry pull --force
uip maestro flow registry search "uipath.core.rpa-workflow" --output json
```

**In-solution (local, no login required):**

```bash
uip maestro flow registry list --local --output json
uip maestro flow registry get "<nodeType>" --local --output json
```

Run from inside the flow project directory. Discovers sibling RPA projects in the same `.uipx` solution.

## Registry Validation

```bash
uip maestro flow registry get "uipath.core.rpa-workflow.{key}" --output json
uip maestro flow registry get "uipath.core.rpa-workflow.{key}" --local --output json
```

Confirm (these fields live in the **definition** — copied verbatim from the registry into `definitions[]`, never on the instance):

- Input port: `input`
- Output port: `output`
- `model.serviceType` — `Orchestrator.StartJob`
- `model.bindings.resourceSubType` — `Process`
- `model.bindings.resourceKey` — the `<FolderPath>.<ResourceName>` string used to scope binding resolution
- `inputDefinition` — may contain typed input fields (check `properties`)
- `outputDefinition.output` — process return value
- `outputDefinition.error` — error schema

## Adding / Editing

For step-by-step add, delete, and wiring procedures, see [flow-editing-operations.md](../../flow-editing-operations.md). Use the JSON structure below for the node-specific `inputs`.

## JSON Structure

### Node instance (inside `nodes[]`)

The instance carries only per-instance data (`inputs`, `outputs`, `display`). BPMN type, serviceType, version, and binding/context templates come from the definition in `definitions[]`.

```json
{
  "id": "processInvoices",
  "type": "uipath.core.rpa-workflow.invoice-process-abc123",
  "typeVersion": "1.0.0",
  "display": { "label": "Process Invoices" },
  "inputs": {
    "documentPath": "=js:$vars.fileLocation",
    "batchSize": 50
  },
  "outputs": {
    "output": {
      "type": "object",
      "description": "The return value of the RPA process",
      "source": "=result.response",
      "var": "output"
    },
    "error": {
      "type": "object",
      "description": "Error information if the RPA process fails",
      "source": "=result.Error",
      "var": "error"
    }
  }
}
```

### Top-level `bindings[]` entries (sibling of `nodes`/`edges`/`definitions`)

Add one entry per `(resourceKey, propertyAttribute)` pair. Share entries across node instances that reference the same RPA process — do NOT create duplicates.

```json
"bindings": [
  {
    "id": "bProcessInvoicesName",
    "name": "name",
    "type": "string",
    "resource": "process",
    "resourceKey": "Finance/Automation.Invoice Processor",
    "default": "Invoice Processor",
    "propertyAttribute": "name",
    "resourceSubType": "Process"
  },
  {
    "id": "bProcessInvoicesFolderPath",
    "name": "folderPath",
    "type": "string",
    "resource": "process",
    "resourceKey": "Finance/Automation.Invoice Processor",
    "default": "Finance/Automation",
    "propertyAttribute": "folderPath",
    "resourceSubType": "Process"
  }
]
```

> **Why the top-level `bindings[]` entries are required.** The definition's `model.context[].value` fields are template placeholders of the form `<bindings.{name}>` — deliberately invalid as runtime expressions. Before BPMN emit, the runtime rewrites each placeholder to `=bindings.<id>` by finding a top-level `bindings[]` entry whose `name` matches the placeholder and whose `resourceKey` matches the definition's `model.bindings.resourceKey`. Without matching top-level entries, `uip maestro flow validate` passes but `uip maestro flow debug` fails with "Folder does not exist or the user does not have access to the folder."

> **Definition stays verbatim.** Do NOT rewrite `<bindings.*>` placeholders inside the `definitions` entry — they are the authoring template. Critical Rule #7 applies unchanged.

## If the RPA Process Does Not Exist Yet

Tell the user to create the RPA project inside the same solution using `uipath-rpa`. Once the project exists as a sibling in the `.uipx` solution, discover it with `uip maestro flow registry list --local --output json` and wire it directly — no publish required.

## Debug

| Error | Cause | Fix |
| --- | --- | --- |
| Node type not found in registry | Process not published or registry stale | If in same solution: run `registry list --local`. Otherwise: run `uip login` then `uip maestro flow registry pull --force` |
| Input schema mismatch | Inputs don't match `inputDefinition` | Run `registry get` and check required inputs in `inputDefinition.properties` |
| Process execution failed | Underlying RPA process errored | Check `$vars.{nodeId}.error` for details |
| Mock placeholder still in flow | Process not yet replaced | Follow the mock replacement workflow above |
