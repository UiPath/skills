# RPA Node — Implementation

RPA nodes invoke RPA processes using `uipath.core.rpa-workflow.{key}`.

## Discovery

**Published (tenant registry):**

```bash
uip maestro flow registry pull --force
uip maestro flow registry search "uipath.core.rpa-workflow" --output json
```

Run `registry pull --force` first. Search the **node-type token** `uipath.core.rpa-workflow`, not the process name. Select the published workflow by `resourceKey` / folder path and description. `registry search` matches the Orchestrator **release name**, often unrelated to the process name or folder; match the folder path inside `resourceKey`, not a name keyword.

Treat an empty result as non-authoritative until you confirm that you searched the node-type token, refreshed the registry, and scanned returned folder paths and descriptions rather than only display names. Do not use the local-scaffold fallback after only a name-search miss.

**In-solution (local, no login required):** Run these inside the flow project directory to discover sibling RPA projects in the same `.uipx` solution:

```bash
uip maestro flow registry list --local --output json
uip maestro flow registry get "<node-type>" --local --output json
```

## Registry Validation

```bash
uip maestro flow registry get "uipath.core.rpa-workflow.{key}" --output json
uip maestro flow registry get "uipath.core.rpa-workflow.{key}" --local --output json
```

Confirm:

- Input port: `input`
- Output port: `output`
- `model.serviceType`: `Orchestrator.StartJob`
- `model.bindings.resourceSubType`: `Process`
- `model.bindings.resourceKey`: the `<FolderPath>.<ResourceName>` string used to scope binding resolution
- `inputDefinition`: may contain typed input fields; check `properties`
- `outputDefinition`: always `error` (`source: "=Error"`); processes with output arguments also declare `output` (`source: "=this"`). Do not author `output` on the instance: the converter injects `=this`, and `$vars.{nodeId}.output` carries the process return value.

## Adding and Editing

For step-by-step add, delete, and wiring procedures, see [editing-operations.md](../../editing-operations.md). Use the JSON structure below for node-specific `inputs`.

### Node instance (`nodes[]`)

The instance carries per-instance data (`inputs`, `outputs`, `display`); BPMN type, serviceType, version, and binding/context templates come from `definitions[]`.

```json
{
  "id": "processInvoices",
  "type": "uipath.core.rpa-workflow.invoice-process-abc123",
  "typeVersion": "<DEFINITION_VERSION>",
  "display": { "label": "Process Invoices" },
  "inputs": {
    "documentPath": "=js:$vars.fileLocation",
    "batchSize": 50
  },
  "outputs": {
    "error": {
      "type": "object",
      "description": "Error information if the RPA process fails",
      "source": "=Error",
      "var": "error"
    }
  }
}
```

Declare `error` only; `output` is derived. If authored, the converter copies its `source` verbatim, so values such as `"=result.response"` resolve to null at runtime even when `flow validate` passes. See [file-format.md § Node outputs](../../../shared/file-format.md#node-outputs).

### Top-level `bindings[]`

Add one entry per `(resourceKey, propertyAttribute)` pair as a sibling of `nodes`/`edges`/`definitions`. Share entries across instances referencing the same RPA process; do not duplicate them.

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

For resolution mechanics and why these entries are required, see [file-format.md — Bindings](../../../shared/file-format.md#bindings--orchestrator-resource-bindings-top-level-bindings).

## If the RPA Process Is Genuinely Not Published

Use this path only after completing the empty-result confirmation in [Discovery](#discovery) and only when no sibling RPA project provides the process. Tell the user to create the RPA project inside the same solution using `uipath-rpa`. After it exists as a sibling in the `.uipx` solution, run `uip maestro flow registry list --local --output json` and wire it directly; publishing is not required.

A freshly scaffolded RPA project has no implementation. The wired flow may pass `flow validate` but fault during debug or execution (`Robot.JobUnexpectedExitCode`) until `uipath-rpa` fills in the workflow. A validated flow is not necessarily a working one.

## Debug

| Error | Cause | Fix |
| --- | --- | --- |
| Node type not found in registry | Searched by process name (matches release name, not folder), process not published, or registry stale | Search the `uipath.core.rpa-workflow` token and match on folder path — not a name keyword. If in same solution: run `registry list --local`. Otherwise: run `uip login` then `uip maestro flow registry pull --force` |
| Input schema mismatch | Inputs don't match `inputDefinition` | Run `registry get` and check required inputs in `inputDefinition.properties` |
| Process execution failed | Underlying RPA process errored | Check `$vars.{nodeId}.error` for details |
| Mock placeholder still in flow | Process not yet replaced | Follow the mock replacement workflow above |