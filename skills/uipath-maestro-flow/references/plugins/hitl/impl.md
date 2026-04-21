# HITL Node — Implementation

HITL nodes pause the flow for human input via a UiPath App. Pattern: `uipath.core.human-task.{key}`.

## Discovery

**Published (tenant registry):**

```bash
uip flow registry pull --force
uip flow registry search "uipath.core.human-task" --output json
```

**In-solution (local, no login required):**

```bash
uip flow registry list --local --output json
uip flow registry get "<nodeType>" --local --output json
```

Run from inside the flow project directory. Discovers sibling projects in the same `.uipx` solution.

## Registry Validation

```bash
# Published (tenant registry)
uip flow registry get "uipath.core.human-task.{key}" --output json

# In-solution (local, no login required)
uip flow registry get "uipath.core.human-task.{key}" --local --output json
```

Confirm:

- Input port: `input`
- Output port: `output`
- `model.serviceType` — `Actions.HITL`
- `model.bindings.resourceSubType` — the app type

## Adding / Editing

For step-by-step add, delete, and wiring procedures, see [flow-editing-operations.md](../../flow-editing-operations.md). Use the JSON structure below for the node-specific `inputs` and `model` fields.

The human task node's output (`$vars.{nodeId}.output`) contains the form data submitted by the user.

## JSON Structure

### Node instance (inside `nodes[]`)

```json
{
  "id": "reviewExtraction",
  "type": "uipath.core.human-task.abc123",
  "typeVersion": "1.0.0",
  "display": { "label": "Review Extraction" },
  "inputs": {},
  "outputs": {
    "output": {
      "type": "object",
      "description": "Form data submitted by the user",
      "source": "=result.response",
      "var": "output"
    },
    "error": {
      "type": "object",
      "description": "Error information if the human task fails",
      "source": "=result.Error",
      "var": "error"
    }
  },
  "model": {
    "type": "bpmn:ServiceTask",
    "serviceType": "Actions.HITL",
    "version": "v2",
    "section": "Published",
    "bindings": {
      "resource": "process",
      "resourceSubType": "<appType>",
      "resourceKey": "Shared.Review Form App",
      "orchestratorType": "human-task",
      "values": {
        "name": "Review Form App",
        "folderPath": "Shared"
      }
    },
    "context": [
      { "name": "name",       "type": "string", "value": "=bindings.bReviewExtractionName",       "default": "Review Form App" },
      { "name": "folderPath", "type": "string", "value": "=bindings.bReviewExtractionFolderPath", "default": "Shared" },
      { "name": "_label",     "type": "string", "value": "Review Form App" }
    ]
  }
}
```

> `resourceKey` takes the form `<FolderPath>.<AppName>` and `resourceSubType` is the app type — confirm both from `uip flow registry get` output.

### Top-level `bindings[]` entries (sibling of `nodes`/`edges`/`definitions`)

Add one entry per `(resourceKey, propertyAttribute)` pair. Share entries across node instances that reference the same app — do NOT create duplicates.

```json
"bindings": [
  {
    "id": "bReviewExtractionName",
    "name": "name",
    "type": "string",
    "resource": "process",
    "resourceKey": "Shared.Review Form App",
    "default": "Review Form App",
    "propertyAttribute": "name",
    "resourceSubType": "<appType>"
  },
  {
    "id": "bReviewExtractionFolderPath",
    "name": "folderPath",
    "type": "string",
    "resource": "process",
    "resourceKey": "Shared.Review Form App",
    "default": "Shared",
    "propertyAttribute": "folderPath",
    "resourceSubType": "<appType>"
  }
]
```

> **Why both are required.** The registry's `Data.Node.model.context[].value` fields ship as template placeholders (`<bindings.name>`, `<bindings.folderPath>`) — not runtime-resolvable expressions. The runtime reads the node instance's `model.context` and resolves `=bindings.<id>` against the top-level `bindings[]` array. Without these two pieces, `uip flow validate` passes but `uip flow debug` fails with "Folder does not exist or the user does not have access to the folder."

> **Definition stays verbatim.** Do NOT rewrite `<bindings.*>` placeholders inside the `definitions` entry — it is a schema copy, not a runtime input. Critical Rule #7 applies unchanged.

## Use Cases

- **Approval workflows** — manager approval before processing
- **Data validation** — human reviews extracted data before submission
- **Exception handling** — human resolves items the automation cannot handle

## Common Pattern — Human-in-the-Loop

```text
Manual Trigger -> RPA Process (extract) -> HITL (review) -> Decision (approved?) ->
  true: Script (submit) -> End
  false: End
```

## Debug

| Error | Cause | Fix |
| --- | --- | --- |
| Node type not found in registry | App not published or registry stale | If in same solution: run `registry list --local`. Otherwise: run `uip login` then `uip flow registry pull --force` |
| Task never completes | Human hasn't submitted the form | Check task assignment in Orchestrator |
| Output missing expected fields | App form doesn't match expected schema | Verify app form fields match what the flow expects |
