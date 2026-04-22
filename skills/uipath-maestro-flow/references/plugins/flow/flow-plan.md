# Flow Node

Flow nodes invoke other flows as subprocesses from within a flow. Published flows appear in the registry after `uip login` + `uip maestro flow registry pull`. **In-solution** (unpublished) flows in sibling projects are discovered via `--local` — no login or publish required.

## Node Type Pattern

`uipath.core.flow.{key}`

## When to Use

Use a Flow node when you need to call another published flow as a subprocess.

### Selection Heuristics

| Situation | Use Flow? |
| --- | --- |
| Call another published flow as a subprocess | Yes |
| Group related steps with isolated scope (within same project) | No — use [Subflow](../subflow/planning.md) |
| Invoke a published orchestration process | No — use [Agentic Process](../agentic-process/flow-plan.md) |
| Flow not yet published but in the same solution | Yes — discover with `--local` (no login or publish needed) |
| Flow does not exist yet | Create it in the same solution with `uipath-maestro-flow`, then use `--local` discovery |

## Ports

| Input Port | Output Port(s) |
| --- | --- |
| `input` | `output` |

## Output Variables

- `$vars.{nodeId}.error` — error details if execution fails (`code`, `message`, `detail`, `category`, `status`)

## Discovery

### Published (tenant registry)

```bash
uip maestro flow registry pull --force
uip maestro flow registry search "uipath.core.flow" --output json
```

Requires `uip login`. Only published flows from your tenant appear.

### In-solution (sibling projects)

```bash
uip maestro flow registry list --local --output json
uip maestro flow registry get "<nodeType>" --local --output json
```

No login or publish required. Discovers unpublished flows in sibling projects within the same solution.

## Registry Validation

```bash
# Published
uip maestro flow registry get "uipath.core.flow.{key}" --output json

# In-solution
uip maestro flow registry get "uipath.core.flow.{key}" --local --output json
```

Confirm:

- Input port: `input`
- Output port: `output`
- `model.serviceType` — `Orchestrator.StartAgenticProcess` (shared with agentic-process nodes; `resourceSubType: "Flow"` differentiates)
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

> `resourceKey` takes the form `<FolderPath>.<FlowName>` — confirm the exact value from `uip maestro flow registry get` output.

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

> **Why both are required.** The registry's `Data.Node.model.context[].value` fields ship as template placeholders (`<bindings.name>`, `<bindings.folderPath>`) — not runtime-resolvable expressions. The runtime reads the node instance's `model.context` and resolves `=bindings.<id>` against the top-level `bindings[]` array. Without these two pieces, `uip maestro flow validate` passes but `uip maestro flow debug` fails with "Folder does not exist or the user does not have access to the folder."

> **Definition stays verbatim.** Do NOT rewrite `<bindings.*>` placeholders inside the `definitions` entry — it is a schema copy, not a runtime input. Critical Rule #7 applies unchanged.

## Debug

| Error | Cause | Fix |
| --- | --- | --- |
| Node type not found in registry | Flow not published or registry stale | Run `uip login` then `uip maestro flow registry pull --force`; for in-solution flows use `--local` |
| Flow execution failed | Underlying flow errored | Check `$vars.{nodeId}.error` for details |
