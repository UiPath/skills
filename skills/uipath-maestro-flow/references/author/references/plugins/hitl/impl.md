# HITL Node — Implementation

Two node types implement human-in-the-loop checkpoints. Choose based on whether you need an inline form or an existing deployed app.

---

## Option 1 — `uipath.human-in-the-loop` (Inline Schema — OOTB)

This is the preferred option. No registry pull, no app publishing, no tenant dependency. Write the node directly into the `.flow` file as JSON.

**Full implementation guide, JSON examples, and schema conversion rules:**
→ [`uipath-human-in-the-loop` skill — hitl-node-quickform.md](../../../../../../uipath-human-in-the-loop/references/hitl-node-quickform.md)

> **Note:** Skills are self-contained. This cross-skill reference is for documentation context only. The agent uses the `uipath-human-in-the-loop` skill to implement HITL nodes. This implementation guide is for implementation-phase topology resolution only — not for schema design or node writing.

### Adding / Editing

For add, delete, and wiring procedures, see [editing-operations.md](../../editing-operations.md). **Use `Edit` / `Write` for HITL node authoring.** Do not use the dedicated HITL CLI for this non-carve-out structural edit. Wire the `completed` port after adding the node.

### Quick Reference

**Node JSON (minimum viable):**

```json
{
  "id": "hitlReview1",
  "type": "uipath.human-in-the-loop",
  "typeVersion": "1.0",
  "display": { "label": "Invoice Review" },
  "inputs": {
    "type": "quick",
    "schema": {
      "schemaId": "<uuid>",
      "fields": [
        { "id": "invoiceid", "label": "Invoice ID", "type": "text",   "direction": "input", "binding": "vars.fetchInvoice.output.invoiceId" },
        { "id": "amount",    "label": "Amount",     "type": "number", "direction": "input", "binding": "vars.fetchInvoice.output.amount" },
        { "id": "decision",  "label": "Decision",   "type": "text",   "direction": "output", "variable": "vars.decision" }
      ],
      "outcomes": [
        { "id": "approve", "name": "Approve", "type": "string", "isPrimary": true,  "action": "Continue" },
        { "id": "reject",  "name": "Reject",  "type": "string", "isPrimary": false, "action": "End" }
      ]
    },
    "recipient": { "channels": ["Email", "ActionCenter"], "connections": {}, "assignee": { "type": "group" } },
    "priority": "Low"
  },
  "outputs": {
    "output": {
      "type": "object",
      "description": "Task result data",
      "source": "=result",
      "var": "output",
      "properties": {
        "decision": { "type": "string" },
        "Action":   { "type": "string", "enum": ["Approve", "Reject"], "default": "Approve" }
      }
    },
    "status": {
      "type": "string",
      "description": "Task completion status",
      "source": "=result.Action",
      "var": "status",
      "enum": ["Approve", "Reject"],
      "default": "Approve"
    }
  }
}
```

**Field format rules:**
- **Input fields**: `binding: "vars.<nodeId>.output.<field>"` (raw path, no `=js:$` prefix). No `variable` property on input fields.
- **Output fields**: `variable: "vars.<globalName>"` (with `vars.` prefix). No `binding`.
- **InOut fields**: both `binding` and `variable`, same formats as above.
- `schemaId` (not `id`) at the schema level — generate a fresh UUID.
- `typeVersion: "1.0"` (not `"1.0.0"`).
- No `model` block on node instances — only the definition carries it.

**outputs block**: only `output` (with `properties` for output/inOut fields + `Action` outcome) and `status` (with `enum`/`default` from outcomes). No per-field `custom: true` entries.

**Ports:** `input` (target) → `completed` (source)

**Output variables:**
- `$vars.{nodeId}.output` — object with all `output` / `inOut` field values, keyed by **field `id`**
- `$vars.{nodeId}.output.{fieldId}` — individual field value (e.g. `$vars.hitlReview1.output.decision`)
- `$vars.{nodeId}.status` — selected outcome name (e.g. `"Approve"`, `"Reject"`)
- `$vars.{globalId}` — workflow-global variable for output/inOut fields; `globalId` is derived from `field.variable` (strip `vars.` prefix)

---

## Option 2 — App-Based HITL (`uipath.human-in-the-loop` with `inputs.type = "custom"`)

Use when there is an existing deployed Action Center app that should serve as the task form. Same node type as Option 1 — only `inputs.type`, `inputs.app`, and `inputs.appInputBindings` differ.

### Discovery

**CLI (primary path):**

```bash
uip solution resource list --kind App --output json
```

Returns all Action Center app types (`vB Action`, `workflow Action`, `Coded Action`, `JS Action`). Filter by app name. Then retrieve the configuration:

```bash
uip solution resource get <key> --output json
```

**Direct API fallback (if CLI unavailable):**

```
GET {BASE_URL}/{ORG}/studio_/backend/api/resourcebuilder/solutions/{SOLUTION_ID}/resources/search
  ?kind=app&pageSize=25&projectKey={PROJECT_KEY}&includeSolutionResources=true
  &types=VB%20Action&types=Workflow%20Action&types=Coded%20Action&types=CodedAction&types=JS%20Action
```

Full step-by-step (app search → retrieve-configuration → resource files → reference registration → debug overwrites) → **[hitl-node-apptask.md](../../../../../../uipath-human-in-the-loop/references/hitl-node-apptask.md)**

### Node JSON (Quick Reference)

```json
{
  "id": "invoiceReview1",
  "type": "uipath.human-in-the-loop",
  "typeVersion": "1.0",
  "display": { "label": "Invoice Review" },
  "inputs": {
    "type": "custom",
    "recipient": { "channels": ["ActionCenter"], "connections": {}, "assignee": { "type": "group" } },
    "app": {
      "displayName": "Invoice Approval",
      "name": "Invoice Approval",
      "key": "<app.key>",
      "folderPath": "Shared",
      "inputSchema": {
        "type": "object",
        "properties": {
          "<paramName>": { "type": "string" }
        }
      },
      "outputSchema": {
        "type": "object",
        "properties": {
          "<outputName>": { "type": "string" }
        }
      }
    },
    "appInputBindings": {
      "<inputParamName>": "=vars.<nodeId>.output.<field>",
      "<inputParamName2>": "=metadata.InstanceId"
    },
    "schema": {
      "fields": [],
      "outcomes": [{ "id": "submit", "name": "Submit", "type": "string", "isPrimary": true, "action": "Continue" }]
    },
    "priority": "Medium"
  },
  "outputs": {
    "output": {
      "type": "object",
      "description": "Task result data",
      "source": "=result",
      "var": "output",
      "properties": {
        "Action": { "type": "string", "enum": ["Submit"], "default": "Submit" }
      }
    },
    "status": {
      "type": "string",
      "description": "Task completion status",
      "source": "=result.Action",
      "var": "status",
      "enum": ["Submit"],
      "default": "Submit"
    }
  }
}
```

**`inputs.app`**: `inputSchema` and `outputSchema` are JSON Schema objects (`{ "type": "object", "properties": { ... } }`), **not arrays**.

**`inputs.appInputBindings`** — maps app input parameter names to binding expressions. Format: `"=vars.<path>"` (with `=` prefix, no `js:`). Key = parameter name from `inputSchema.properties`. Without this, all input fields appear blank.

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
| Node type not found in registry (Option 2) | App not published or registry stale | If in same solution: `uip maestro flow registry list --local`. Otherwise: `uip login` then `uip maestro flow registry pull --force` |
| Task never completes | Human hasn't submitted the form | Check task assignment in Orchestrator |
| Output missing expected fields | App form doesn't match expected schema | Verify app form fields match what the flow expects |
| `completed` port unwired (Option 1) | Missing edge on output handle | Wire the `completed` output handle — an unwired `completed` blocks the flow indefinitely |
