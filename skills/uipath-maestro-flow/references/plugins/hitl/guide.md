# HITL Node — Guide

The flow needs to pause for a human to review, approve, or fill in data. Two node types serve this need — choose based on form complexity and whether an app already exists.

---

## Which HITL Node to Use

| Use case | Node type | Form source |
| --- | --- | --- |
| Inline form designed right now (fields + outcomes defined in the flow) | `uipath.human-in-the-loop` | Schema embedded in node inputs — no app needed |
| Existing coded app or Action Center app | `uipath.core.human-task.{key}` | Deployed app from Orchestrator |

**Prefer `uipath.human-in-the-loop`** for new flows. It is an OOTB node — no registry discovery, no app publishing, no tenant dependency.

---

## Option 1 — `uipath.human-in-the-loop` (Inline Schema — OOTB)

Node type: `uipath.human-in-the-loop`
Available: always — no `uip login` or registry pull required.

### When to Select

| Situation | Select? |
| --- | --- |
| Manager approval before processing | Yes |
| Human reviews extracted data before submission | Yes |
| Human resolves exceptions the automation cannot handle | Yes |
| Need a quick form with specific fields and outcomes | Yes |
| Existing coded/Action Center app should be used | No — use Option 2 |
| Fully automated processing, no human involvement | No |

### Ports

| Input port | Output port |
| --- | --- |
| `input` | `completed` |

**The output port must be wired.** A node with no edge on `completed` blocks the flow indefinitely.

### Output Variables

- `$vars.{nodeId}.result` — object containing all output and inOut fields the human filled in
- `$vars.{nodeId}.result.{fieldName}` — individual field value
- `$vars.{nodeId}.status` — `"completed"`

### Schema Design

The schema defines what the human sees and provides. Three field categories:

| Category | Human can... | Use for |
| --- | --- | --- |
| `inputs` | Read only | Context the human needs to decide |
| `outputs` | Write | Data the automation needs back |
| `inOuts` | Read + modify | Fields the human can see and optionally correct |

Outcomes are the action buttons (e.g., Approve/Reject). First outcome is primary.

**In the architectural plan**, describe the schema:
```
inputs:   [invoiceId (string), amount (number)]
outputs:  [decision (string, required)]
outcomes: [Approve, Reject]
priority: Low
```

Full JSON format and conversion examples: see [`uipath-human-in-the-loop` skill](../../../../uipath-human-in-the-loop/references/hitl-node-quickform.md).

> **Note:** Skills are self-contained — cross-skill references are for documentation context only. The agent uses the `uipath-human-in-the-loop` skill to implement HITL nodes; this planning guide is for topology selection only.

### Wiring Pattern

```
[Upstream] -> [HITL] ->|completed| [Continue]
```

### Common Topology Patterns

**Approval gate:**
```
Trigger -> Fetch Data -> HITL (review) ->|completed| Decision (approved?) ->
  true: Script (process) -> End
  false: Script (log rejection) -> End
```

**Exception escalation:**
```
Trigger -> Process -> Decision (confidence ok?) ->
  true: Continue -> End
  false: HITL (exception review) ->|completed| Script (retry with human input) -> End
```

### Planning Annotation

In the node table:
```
| hitlReview | Invoice Review | human-task | uipath.human-in-the-loop | inputs: [invoiceId, amount] outputs: [decision] outcomes: [Approve, Reject] | result, status |
```

---

## Option 2 — `uipath.core.human-task.{key}` (App-Based)

Node type: `uipath.core.human-task.{key}`
Available: tenant-specific resource — requires `uip login` + `uip flow registry pull`.

### When to Select

Use when there is an existing coded app or Action Center app that should be the task form.

### Ports

| Input port | Output port |
| --- | --- |
| `input` | `output` |

### Output Variables

- `$vars.{nodeId}.output` — form data submitted by the user
- `$vars.{nodeId}.error` — error details if execution fails

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

### Planning Annotation

- If the app exists: note as `resource: <name> (human-task)`
- If it does not exist: note as `[CREATE NEW] <description>` with skill `uipath-coded-apps`, use `core.logic.mock` placeholder

---

## Implementation

### Option 1 — `uipath.human-in-the-loop` (Inline Schema — OOTB)

This is the preferred option. No registry pull, no app publishing, no tenant dependency. Write the node directly into the `.flow` file as JSON.

**Full implementation guide, JSON examples, and schema conversion rules:**
-> [`uipath-human-in-the-loop` skill — hitl-node-quickform.md](../../../../../uipath-human-in-the-loop/references/hitl-node-quickform.md)

> **Note:** Skills are self-contained. This cross-skill reference is for documentation context only. The agent uses the `uipath-human-in-the-loop` skill to implement HITL nodes. This implementation guide is for implementation-phase topology resolution only — not for schema design or node writing.

#### Quick Reference

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
  "model": { "type": "bpmn:UserTask", "serviceType": "Actions.HITL" }
}
```

**Ports:** `input` (target) -> `completed` (source)

**Output variables:**
- `$vars.{nodeId}.result` — object with all `output` / `inOut` fields the human filled in
- `$vars.{nodeId}.result.{fieldName}` — individual field value
- `$vars.{nodeId}.status` — `"completed"`

---

### Option 2 — `uipath.core.human-task.{key}` (App-Based)

Use when there is an existing deployed Action Center app that should serve as the task form.

#### Registry Validation

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

#### Node JSON

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

#### If the app does not exist yet

Note as `[CREATE NEW] <description>` in the node table and use `core.logic.mock` as a placeholder. The app itself is out of scope for this skill — use the `uipath-coded-apps` skill to build it.

---

### Common Pattern — Human-in-the-Loop

```text
Manual Trigger -> RPA Process (extract) -> HITL (review) -> Decision (approved?) ->
  true: Script (submit) -> End
  false: End
```

### Debug

| Error | Cause | Fix |
| --- | --- | --- |
| Node type not found in registry (Option 2) | App not published or registry stale | If in same solution: `uip flow registry list --local`. Otherwise: `uip login` then `uip flow registry pull --force` |
| Task never completes | Human hasn't submitted the form | Check task assignment in Orchestrator |
| Output missing expected fields | App form doesn't match expected schema | Verify app form fields match what the flow expects |
| `completed` port unwired (Option 1) | Missing edge on output handle | Wire the `completed` output handle — an unwired `completed` blocks the flow indefinitely |
