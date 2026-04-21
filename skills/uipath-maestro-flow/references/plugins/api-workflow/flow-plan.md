# API Workflow Node

API workflow nodes invoke published API functions from within a flow. They are tenant-specific resources that appear in the registry after `uip login` + `uip flow registry pull`.

## Node Type Pattern

`uipath.core.api-workflow.{key}`

## When to Use

Use an API Workflow node when the flow needs to call a published UiPath API function.

### Selection Heuristics

| Situation | Use API Workflow? |
| --- | --- |
| Call a published UiPath API function | Yes |
| Call an external REST API | No — use [HTTP](../http/planning.md) or [Connector](../connector/planning.md) |
| Invoke a published RPA process | No — use [RPA Workflow](../rpa/planning.md) |
| Resource not yet published | No — use `core.logic.mock` placeholder |

## Ports

| Input Port | Output Port(s) |
| --- | --- |
| `input` | `output` |

## Output Variables

- `$vars.{nodeId}.error` — error details if execution fails (`code`, `message`, `detail`, `category`, `status`)

## Discovery

```bash
uip flow registry pull --force
uip flow registry search "uipath.core.api-workflow" --output json
```

Requires `uip login`. Only published API workflows from your tenant appear.

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

## JSON Structure

### Node instance (inside `nodes[]`)

```json
{
  "id": "callApiFunction",
  "type": "uipath.core.api-workflow.346b8959-c126-48d3-9c46-942abcf944d7",
  "typeVersion": "1.0.0",
  "display": { "label": "Call API Function" },
  "inputs": {},
  "outputs": {
    "output": {
      "type": "object",
      "description": "The return value of the API workflow",
      "source": "=result.response",
      "var": "output"
    },
    "error": {
      "type": "object",
      "description": "Error information if the API workflow fails",
      "source": "=result.Error",
      "var": "error"
    }
  },
  "model": {
    "type": "bpmn:ServiceTask",
    "serviceType": "Orchestrator.ExecuteApiWorkflowAsync",
    "version": "v2",
    "section": "Published",
    "bindings": {
      "resource": "process",
      "resourceSubType": "Api",
      "resourceKey": "Shared.My API Function",
      "orchestratorType": "api-workflow",
      "values": {
        "name": "My API Function",
        "folderPath": "Shared"
      }
    },
    "context": [
      { "name": "name",       "type": "string", "value": "=bindings.bCallApiFunctionName",       "default": "My API Function" },
      { "name": "folderPath", "type": "string", "value": "=bindings.bCallApiFunctionFolderPath", "default": "Shared" },
      { "name": "_label",     "type": "string", "value": "My API Function" }
    ]
  }
}
```

> `resourceKey` takes the form `<FolderPath>.<ApiName>` — confirm the exact value from `uip flow registry get` output.

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

> **Why both are required.** The registry's `Data.Node.model.context[].value` fields ship as template placeholders (`<bindings.name>`, `<bindings.folderPath>`) — not runtime-resolvable expressions. The runtime reads the node instance's `model.context` and resolves `=bindings.<id>` against the top-level `bindings[]` array. Without these two pieces, `uip flow validate` passes but `uip flow debug` fails with "Folder does not exist or the user does not have access to the folder."

> **Definition stays verbatim.** Do NOT rewrite `<bindings.*>` placeholders inside the `definitions` entry — it is a schema copy, not a runtime input. Critical Rule #7 applies unchanged.

## Debug

| Error | Cause | Fix |
| --- | --- | --- |
| Node type not found in registry | API workflow not published or registry stale | Run `uip login` then `uip flow registry pull --force` |
| Execution failed | Underlying API workflow errored | Check `$vars.{nodeId}.error` for details |
