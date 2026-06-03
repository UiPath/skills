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

Confirm:

- Input port: `input`
- Output port: `output`
- `model.serviceType` — `Orchestrator.StartJob`
- `model.bindings.resourceSubType` — `Process`
- `model.bindings.resourceKey` — scopes binding resolution. **Shape differs by source:**
  - Published (tenant): `<FolderPath>.<ResourceName>` (e.g., `Autopilot.Wikipedia`)
  - In-solution (`--local`): the sibling project's GUID (e.g., `5b4b19fa-3586-457b-801b-ad898800062e`); `model.bindings.values.folderPath` is `""`. Local definitions also carry extra `model.projectId` and `model.projectName` fields not present in published definitions — leave them in the definition verbatim
- `inputDefinition` — may contain typed input fields (check `properties`)
- `outputDefinition.output` — process return value
- `outputDefinition.error` — error schema

## Adding / Editing

For step-by-step add, delete, and wiring procedures, see [editing-operations.md](../../editing-operations.md). Use the JSON structure below for the node-specific `inputs`.

## JSON Structure

### Node instance (inside `nodes[]`)

The instance carries only per-instance data (`inputs`, `outputs`, `display`). BPMN type, serviceType, version, and binding/context templates come from the definition in `definitions[]`. Set `typeVersion` to the `version` field of the definition copied from `registry get` (e.g., `"1.0.0"`).

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
    "output": {
      "type": "object",
      "description": "The return value of the RPA process",
      "source": "=this",
      "var": "output"
    },
    "error": {
      "type": "object",
      "description": "Error information if the RPA process fails",
      "source": "=Error",
      "var": "error"
    }
  }
}
```

> **`source` must be copied verbatim from the registry.** Set `outputs.output.source` and `outputs.error.source` to the exact values returned in `outputDefinition.output.source` / `outputDefinition.error.source` by `uip maestro flow registry get`. For RPA processes these are typically `=this` / `=Error` (HTTP/script nodes use a different envelope and resolve to `=result.response` / `=result.Error` — do **not** copy that pattern onto an RPA node).

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

> For the resolution mechanics and why these entries are required, see [file-format.md — Bindings](../../../../shared/file-format.md#bindings--orchestrator-resource-bindings-top-level-bindings).

#### In-solution (`--local`) bindings

For sibling RPA projects discovered via `--local`, the same two-entry shape applies but `resourceKey` is the project GUID and `folderPath.default` is `""`:

```json
"bindings": [
  {
    "id": "bInvoicerName",
    "name": "name",
    "type": "string",
    "resource": "process",
    "resourceKey": "5b4b19fa-3586-457b-801b-ad898800062e",
    "default": "Invoicer",
    "propertyAttribute": "name",
    "resourceSubType": "Process"
  },
  {
    "id": "bInvoicerFolderPath",
    "name": "folderPath",
    "type": "string",
    "resource": "process",
    "resourceKey": "5b4b19fa-3586-457b-801b-ad898800062e",
    "default": "",
    "propertyAttribute": "folderPath",
    "resourceSubType": "Process"
  }
]
```

The `resourceKey` here matches the sibling project's `Id` in the solution `.uipx` file. Do **not** invent a `<FolderPath>.<Name>` key for local resources — `flow validate` accepts both, but only the GUID resolves at runtime.

## If the RPA Process Does Not Exist Yet

Hand off to the `uipath-rpa` skill. The user (or that skill) creates the project as a sibling inside the same `.uipx` solution:

```bash
cd <SolutionDir>
uip rpa create-project --name <ProcessName> --location . \
  --target-framework Portable --expression-language CSharp --output json
uip solution project add <ProcessName> --output json
```

Once the project exists as a sibling, discover it with `uip maestro flow registry list --local --output json` and wire it directly — no publish required. The `resourceKey` in `bindings[]` will be the project's GUID (see "In-solution (`--local`) bindings" above).

## Debug

| Error | Cause | Fix |
| --- | --- | --- |
| Node type not found in registry | Process not published or registry stale | If in same solution: run `registry list --local`. Otherwise: run `uip login` then `uip maestro flow registry pull --force` |
| Input schema mismatch | Inputs don't match `inputDefinition` | Run `registry get` and check required inputs in `inputDefinition.properties` |
| Process execution failed | Underlying RPA process errored | Check `$vars.{nodeId}.error` for details |
| Mock placeholder still in flow | Process not yet replaced | See [editing-operations-json.md — Replace a mock with a real resource node](../../editing-operations-json.md#replace-a-mock-with-a-real-resource-node) |
| Validator returns `[error] [(root)] Schema validation failed: Invalid input: expected string, received undefined` with no path | Almost always a missing or misnamed field on an `edges[]` entry | Edge fields are `sourceNodeId` / `sourcePort` / `targetNodeId` / `targetPort` — NOT `source` / `target`. See [shared/file-format.md](../../../../shared/file-format.md) edges section |
| Wrong values bound at runtime even though `flow validate` passes | `outputs.*.source` doesn't match what the registry returns for this node type | Copy `outputDefinition.output.source` / `outputDefinition.error.source` verbatim from `uip maestro flow registry get`. For RPA: typically `=this` / `=Error` — never `=result.response` / `=result.Error` (that's the HTTP/script envelope) |
