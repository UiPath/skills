# HITL Node — Implementation

Two node types implement human-in-the-loop checkpoints. Choose based on whether you need an inline form or an existing deployed app.

---

## Option 1 — `uipath.human-in-the-loop` (Inline Schema — OOTB)

This is the preferred option. No registry pull, no app publishing, no tenant dependency. Write the node directly into the `.flow` file as JSON, or use the CLI.

**Full implementation guide, JSON examples, and schema conversion rules:**
→ [`uipath-human-in-the-loop` skill — hitl-node-quickform.md](../../../../../uipath-human-in-the-loop/references/hitl-node-quickform.md)

> **Note:** Skills are self-contained. This cross-skill reference is for documentation context only. The agent uses the `uipath-human-in-the-loop` skill to implement HITL nodes. This implementation guide is for implementation-phase topology resolution only — not for schema design or node writing.

### CLI Command (preferred for new nodes)

```bash
uip maestro flow hitl add <path/to/file.flow> \
  --label "Invoice Review" \
  --priority High \
  --assignee finance-approvers \
  --schema '{"inputs":[{"name":"invoiceId","binding":"fetchInvoice.result.invoiceId"}],"outputs":[{"name":"decision","required":true}],"outcomes":[{"name":"Approve"},{"name":"Reject"}]}' \
  --output json
```

The command handles the full lifecycle: writes the node, adds the `uipath.human-in-the-loop` definition entry once, and regenerates `variables.nodes`. Wire the `completed` port manually after the command returns (see Edge Wiring below). Full flag reference: [flow-commands.md — uip maestro flow hitl add](../../flow-commands.md#uip-maestro-flow-hitl-add).

### Quick Reference

**Node JSON (minimum viable):**

```json
{
  "id": "hitlReview1",
  "type": "uipath.human-in-the-loop",
  "typeVersion": "1.0.0",
  "display": { "label": "Invoice Review" },
  "inputs": {
    "type": "quick",
    "schema": {
      "fields": [
        { "id": "invoiceId", "label": "Invoice ID", "type": "text",   "direction": "input" },
        { "id": "amount",    "label": "Amount",     "type": "number", "direction": "input" }
      ],
      "outcomes": [
        { "id": "approve", "name": "Approve", "type": "string", "isPrimary": true,  "outcomeType": "Positive", "action": "Continue" },
        { "id": "reject",  "name": "Reject",  "type": "string", "isPrimary": false, "outcomeType": "Negative", "action": "End" }
      ]
    },
    "recipient": { "channels": ["ActionCenter"], "connections": {}, "assignee": { "type": "group" } },
    "priority": "Low"
  },
  "outputs": {
    "result": { "type": "object", "description": "Task result data", "source": "=result", "var": "result" },
    "status": { "type": "string", "description": "Task completion status", "source": "=status", "var": "status" }
  },
  "model": { "type": "bpmn:UserTask", "serviceType": "Actions.HITL" }
}
```

**Ports:** `input` (target) → `completed` (source)

**Output variables:**
- `$vars.{nodeId}.result` — object with all `output` / `inOut` fields the human filled in
- `$vars.{nodeId}.result.{fieldName}` — individual field value
- `$vars.{nodeId}.status` — `"completed"`

---

## Option 2 — `uipath.core.human-task.{key}` (App-Based)

Use when there is an existing deployed Action Center app that should serve as the task form.

### Discovery

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

### Registry Validation

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

### Node JSON

For step-by-step add, delete, and wiring procedures, see [flow-editing-operations.md](../../flow-editing-operations.md). Use the JSON structure below for the node-specific `inputs` and `model` fields.

The human task node's output (`$vars.{nodeId}.output`) contains the form data submitted by the user.

**Node instance (inside `nodes[]`):**

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

**Top-level `bindings[]` entries (sibling of `nodes`/`edges`/`definitions`):**

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

### If the app does not exist yet

Note as `[CREATE NEW] <description>` in the node table and use `core.logic.mock` as a placeholder. The app itself is out of scope for this skill — use the `uipath-coded-apps` skill to build it.

---

## Common Pattern — Human-in-the-Loop

```text
Manual Trigger -> RPA Process (extract) -> HITL (review) -> Decision (approved?) ->
  true: Script (submit) -> End
  false: End
```

## Debug

| Error | Cause | Fix |
| --- | --- | --- |
| Node type not found in registry (Option 2) | App not published or registry stale | If in same solution: `uip flow registry list --local`. Otherwise: `uip login` then `uip flow registry pull --force` |
| Task never completes | Human hasn't submitted the form | Check task assignment in Orchestrator |
| Output missing expected fields | App form doesn't match expected schema | Verify app form fields match what the flow expects |
| `completed` port unwired (Option 1) | Missing edge on output handle | Wire the `completed` output handle — an unwired `completed` blocks the flow indefinitely |
