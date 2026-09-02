# RPA Node — Implementation

RPA nodes invoke RPA processes. Pattern: `uipath.core.rpa-workflow.{key}`.

## Discovery

**Published (tenant registry):**

```bash
uip maestro flow registry pull --force
uip maestro flow registry search "uipath.core.rpa-workflow" --output json
```

Search the **node-type token** `uipath.core.rpa-workflow` — this lists every published RPA workflow — then pick the one you need by its `resourceKey` / folder path and description. Do **not** search by the process name from the request: `registry search` matches the Orchestrator **release name**, which is frequently unrelated to the name the user uses or the folder the process lives in. The requested name often appears only in the folder path, so a keyword search for it returns nothing even though the process exists. Match on the folder path inside `resourceKey`, not on a name keyword.

**An empty result is not authoritative — do not conclude the process is unpublished.** Before treating "not found" as real, confirm all three hold: (a) you searched the `uipath.core.rpa-workflow` token, not a name keyword; (b) `registry pull --force` ran first; (c) you scanned the returned folder paths and descriptions for the target, not just the display names. Only then is the process genuinely absent. Jumping to the local-scaffold fallback on a name-search miss builds a flow that validates but has nothing real to run.

**In-solution (local, no login required):**

```bash
uip maestro flow registry list --local --output json
uip maestro flow registry get "<node-type>" --local --output json
```

Run from inside the flow project directory. Discovers sibling RPA projects in the same `.uipx` solution.

## Registry Validation

```bash
uip maestro flow registry get "uipath.core.rpa-workflow.{key}" --output json
uip maestro flow registry get "uipath.core.rpa-workflow.{key}" --local --output json
```

Confirm:

- Input port: `input`
- Output port: `output`
- `model.serviceType` — `Orchestrator.StartJob`
- `model.bindings.resourceSubType` — `Process`
- `model.bindings.resourceKey` — the `<FolderPath>.<ResourceName>` string used to scope binding resolution
- `inputDefinition` — may contain typed input fields (check `properties`)
- `outputDefinition` — always `error` (`source: "=Error"`); processes with output arguments also declare `output` (`source: "=this"`). Either way do not author `output` on the instance — the converter injects `=this`, and `$vars.{nodeId}.output` carries the process return value

## Adding / Editing

For step-by-step add, delete, and wiring procedures, see [editing-operations.md](../../editing-operations.md). Use the JSON structure below for the node-specific `inputs`.

## JSON Structure

### Node instance (inside `nodes[]`)

The instance carries only per-instance data (`inputs`, `outputs`, `display`). BPMN type, serviceType, version, and binding/context templates come from the definition in `definitions[]`.

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

**Declare `error` only — `output` is derived.** Authoring it makes the converter copy your `source` verbatim; `"=result.response"` then resolves to null at runtime while `flow validate` passes. See [file-format.md § Node outputs](../../../shared/file-format.md#node-outputs).

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

> For the resolution mechanics and why these entries are required, see [file-format.md — Bindings](../../../shared/file-format.md#bindings--orchestrator-resource-bindings-top-level-bindings).

## If the RPA Process Is Genuinely Not Published

Reach this path only after the empty-result confirmation in [Discovery](#discovery) — a brand-name search miss does not qualify. When the process truly does not exist on the tenant and no sibling RPA project provides it, tell the user to create the RPA project inside the same solution using `uipath-rpa`. Once the project exists as a sibling in the `.uipx` solution, discover it with `uip maestro flow registry list --local --output json` and wire it directly — no publish required.

A freshly scaffolded RPA project has no implementation, so the wired flow will pass `flow validate` but fault the moment it is debugged or run (`Robot.JobUnexpectedExitCode`) until `uipath-rpa` fills in the actual workflow. A validated flow is not a working one.

## Debug

| Error | Cause | Fix |
| --- | --- | --- |
| Node type not found in registry | Searched by process name (matches release name, not folder), process not published, or registry stale | Search the `uipath.core.rpa-workflow` token and match on folder path — not a name keyword. If in same solution: run `registry list --local`. Otherwise: run `uip login` then `uip maestro flow registry pull --force` |
| Input schema mismatch | Inputs don't match `inputDefinition` | Run `registry get` and check required inputs in `inputDefinition.properties` |
| Process execution failed | Underlying RPA process errored | Check `$vars.{nodeId}.error` for details |
| Mock placeholder still in flow | Process not yet replaced | Follow the mock replacement workflow above |
