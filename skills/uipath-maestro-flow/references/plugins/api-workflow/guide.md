# API Workflow Node — Guide

API workflow nodes invoke API functions from within a flow. Published API workflows appear in the registry after `uip login` + `uip maestro flow registry pull`. **In-solution** (unpublished) API workflows in sibling projects are discovered via `--local` — no login or publish required.

## Node Type Pattern

`uipath.core.api-workflow.{key}`

## When to Use

Use an API Workflow node when the flow needs to call a published UiPath API function.

### Selection Heuristics

| Situation | Use API Workflow? |
| --- | --- |
| Call a published UiPath API function | Yes |
| Call an external REST API | No — use [HTTP](../http/guide.md) or [Connector](../connector/guide.md) |
| Invoke a published RPA process | No — use [RPA Workflow](../rpa/guide.md) |
| API workflow not yet published but in the same solution | Yes — discover with `--local` (no login or publish needed) |
| API workflow does not exist yet | Create it in the same solution, then use `--local` discovery |

## Ports

| Input Port | Output Port(s) |
| --- | --- |
| `input` | `output`, `error` |

The `error` port is the implicit error port shared with all action nodes — see [Implicit error port on action nodes](../../flow-file-format.md#implicit-error-port-on-action-nodes).

## Output Variables

- `$vars.{nodeId}.error` — error details if execution fails (`code`, `message`, `detail`, `category`, `status`)

## Discovery

### Published (tenant registry)

```bash
uip maestro flow registry pull --force
uip maestro flow registry search "uipath.core.api-workflow" --output json
```

Requires `uip login`. Only published API workflows from your tenant appear.

### In-solution (sibling projects)

```bash
uip maestro flow registry list --local --output json
uip maestro flow registry get "<nodeType>" --local --output json
```

No login or publish required. Discovers unpublished API workflows in sibling projects within the same solution.

## Planning Annotation

In the architectural plan:

- If the API workflow exists: note as `resource: <name> (api-workflow)`
- If it does not exist: note as `[CREATE NEW] <description>`

---

## Implementation

### Registry Validation

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
- `inputDefinition` — typically empty
- `outputDefinition.error` — error schema

### Adding / Editing

For step-by-step add, delete, and wiring procedures, see [flow-editing-operations.md](../../flow-editing-operations.md). Use the JSON structure below for the node-specific `inputs` and `model` fields.

### JSON Structure

#### Node instance (inside `nodes[]`)

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

> `resourceKey` takes the form `<FolderPath>.<ApiName>` — confirm the exact value from `uip maestro flow registry get` output.

#### Top-level `bindings[]` entries (sibling of `nodes`/`edges`/`definitions`)

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

> **Why both are required.** The registry's `Data.Node.model.context[].value` fields ship as template placeholders (`<bindings.name>`, `<bindings.folderPath>`) — not runtime-resolvable expressions. The runtime reads the node instance's `model.context` and resolves `=bindings.<id>` against the top-level `bindings[]` array. Without these two pieces, `uip maestro flow validate` passes but `uip maestro flow debug` fails with "Folder does not exist or the user does not have access to the folder."

> **Definition stays verbatim.** Do NOT rewrite `<bindings.*>` placeholders inside the `definitions` entry — it is a schema copy, not a runtime input. Critical Rule #7 applies unchanged.

### Debug

| Error | Cause | Fix |
| --- | --- | --- |
| Node type not found in registry | API workflow not published or registry stale | Run `uip login` then `uip maestro flow registry pull --force`; for in-solution API workflows use `--local` |
| Execution failed | Underlying API workflow errored | Check `$vars.{nodeId}.error` for details |
