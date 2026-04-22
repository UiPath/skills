# RPA Node

RPA nodes invoke RPA processes (XAML or coded C# workflows) from within a flow. Published processes appear in the registry after `uip login` + `uip flow registry pull`. **In-solution** (unpublished) processes in sibling projects are discovered via `--local` — no login or publish required.

## Node Type Pattern

`uipath.core.rpa-workflow.{key}`

## When to Use

Use an RPA node when the flow needs desktop/browser automation via a published RPA process.

### Selection Heuristics

| Situation | Use RPA? |
| --- | --- |
| Desktop/browser automation via a published RPA process | Yes |
| Target system has a REST API | No — use [Connector](../connector/flow-plan.md) or [HTTP](../http/flow-plan.md) |
| RPA process in the same solution but not yet published | Yes — use `--local` discovery (see below) |
| RPA process does not exist yet | Create it in the same solution with `uipath-rpa`, then use `--local` discovery |
| Need AI reasoning, not desktop automation | No — use [Agent](../agent/flow-plan.md) |

## Ports

| Input Port | Output Port(s) |
| --- | --- |
| `input` | `output`, `error` |

The `error` port is the implicit error port shared with all action nodes — see [Implicit error port on action nodes](../../flow-file-format.md#implicit-error-port-on-action-nodes).

## Output Variables

- `$vars.{nodeId}.output` — the RPA process return value (structure depends on the process)
- `$vars.{nodeId}.error` — error details if execution fails (`code`, `message`, `detail`, `category`, `status`)

## Discovery

**Published (tenant registry):**

```bash
uip flow registry pull --force
uip flow registry search "uipath.core.rpa-workflow" --output json
```

Requires `uip login`. Only published processes from your tenant appear.

**In-solution (local, no login required):**

```bash
uip flow registry list --local --output json
uip flow registry get "<nodeType>" --local --output json
```

Run from inside the flow project directory. Discovers sibling RPA projects in the same `.uipx` solution.

## Registry Validation

```bash
uip flow registry get "uipath.core.rpa-workflow.{key}" --output json
uip flow registry get "uipath.core.rpa-workflow.{key}" --local --output json
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

## JSON Structure

### Node instance (inside `nodes[]`)

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
      { "name": "name",       "type": "string", "value": "=bindings.bProcessInvoicesName",       "default": "Invoice Processor" },
      { "name": "folderPath", "type": "string", "value": "=bindings.bProcessInvoicesFolderPath", "default": "Finance/Automation" },
      { "name": "_label",     "type": "string", "value": "Invoice Processor" }
    ]
  }
}
```

> `resourceKey` takes the form `<FolderPath>.<ResourceName>` — confirm the exact value from `uip flow registry get` output (it already has the correct key format).

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

> **Why both are required.** The registry's `Data.Node.model.context[].value` fields ship as template placeholders (`<bindings.name>`, `<bindings.folderPath>`) — not runtime-resolvable expressions. The runtime reads the node instance's `model.context` and resolves `=bindings.<id>` against the top-level `bindings[]` array. Without these two pieces, `uip flow validate` passes but `uip flow debug` fails with "Folder does not exist or the user does not have access to the folder."

> **Definition stays verbatim.** Do NOT rewrite `<bindings.*>` placeholders inside the `definitions` entry — it is a schema copy, not a runtime input. Critical Rule #7 applies unchanged.

## Configuration

### If the RPA Process Does Not Exist Yet

Tell the user to create the RPA project inside the same solution using `uipath-rpa`. Once the project exists as a sibling in the `.uipx` solution, discover it with `uip flow registry list --local --output json` and wire it directly — no publish required.

## Debug

| Error | Cause | Fix |
| --- | --- | --- |
| Node type not found in registry | Process not published or registry stale | If in same solution: run `registry list --local`. Otherwise: run `uip login` then `uip flow registry pull --force` |
| Input schema mismatch | Inputs don't match `inputDefinition` | Run `registry get` and check required inputs in `inputDefinition.properties` |
| Process execution failed | Underlying RPA process errored | Check `$vars.{nodeId}.error` for details |
| Mock placeholder still in flow | Process not yet replaced | Follow the mock replacement workflow above |
