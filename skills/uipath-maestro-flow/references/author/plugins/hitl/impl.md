# HITL Node — Implementation

Choose one checkpoint: an inline QuickForm or an existing deployed Action Center app.

## Option 1 — `uipath.human-in-the-loop.quick-form` (Inline Schema — OOTB)

Preferred: no registry pull, app publishing, or tenant dependency. Write the node directly into the `.flow` file as JSON.

For implementation guide, JSON examples, and schema conversion rules, see [`uipath-human-in-the-loop` skill — hitl-node-quickform.md](../../../../../uipath-human-in-the-loop/references/hitl-node-quickform.md). Use that skill for HITL implementation; this guide covers implementation-phase topology resolution, not schema design or node writing.

For add, delete, and wiring procedures, see [editing-operations.md](../../editing-operations.md). **Use `Edit` / `Write` for HITL node authoring.** Do not use the dedicated HITL CLI for this non-carve-out structural edit. Wire the `outcome-completed` port after adding the node.

### Quick reference

```json
{
  "id": "hitlReview1",
  "type": "uipath.human-in-the-loop.quick-form",
  "typeVersion": "1.0",
  "display": { "label": "Invoice Review" },
  "inputs": {
    "schema": {
      "schemaId": "<uuid>",
      "fields": [
        { "id": "invoiceid", "label": "Invoice ID", "type": "text", "direction": "input", "binding": "vars.fetchInvoice.output.invoiceId" },
        { "id": "amount", "label": "Amount", "type": "number", "direction": "input", "binding": "vars.fetchInvoice.output.amount" },
        { "id": "decision", "label": "Decision", "type": "text", "direction": "output", "variable": "vars.decision" }
      ],
      "outcomes": [
        { "id": "approve", "name": "Approve", "type": "string", "isPrimary": true, "action": "Continue" },
        { "id": "reject", "name": "Reject", "type": "string", "isPrimary": false, "action": "End" }
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
        "Action": { "type": "string", "enum": ["Approve", "Reject"], "default": "Approve" }
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

Rules:
- Input fields use `binding: "vars.<nodeId>.output.<field>"` (raw path; no `=js:$` prefix) and no `variable`.
- Output fields use `variable: "vars.<globalName>"` (`vars.` required) and no `binding`.
- InOut fields use both properties in those formats.
- Use `schemaId` (not `id`) at schema level and generate a fresh UUID.
- Use `typeVersion: "1.0"` for this node. **Do not run `registry get` to derive it; do not use `"1.1"` or another version.**
- Do not include a `model` block on node instances; only the definition carries it.
- `outputs` contains only `output` (with `properties` for output/inOut fields plus `Action`) and `status` (with outcome `enum`/`default`). Do not add per-field `custom: true` entries.
- Ports: `input` (target) → `outcome-completed` (source, label: Completed).
- Outputs are `$vars.{nodeId}.output` (object keyed by field `id`), `$vars.{nodeId}.output.{fieldId}`, `$vars.{nodeId}.status` (selected outcome name), and `$vars.{globalId}` (workflow-global alias from `field.variable` with `vars.` stripped). **Do not use the alias in scripts; use `$vars.{nodeId}.output.{fieldId}`.**

## Option 2 — App-Based HITL (`uipath.human-in-the-loop.coded-action-app`)

Use an existing deployed Action Center app as the task form.

### Discovery

**Run:**

```bash
uip solution resources list --kind App --output json
```

Filter returned Action Center app types (`vB Action`, `workflow Action`, `Coded Action`, `JS Action`) by app name. **Run:**

```bash
uip solution resources get <key> --output json
```

If the CLI is unavailable, use:

```
GET {BASE_URL}/{ORG}/studio_/backend/api/resourcebuilder/solutions/{SOLUTION_ID}/resources/search
  ?kind=app&pageSize=25&projectKey={PROJECT_KEY}&includeSolutionResources=true
  &types=VB%20Action&types=Workflow%20Action&types=Coded%20Action&types=CodedAction&types=JS%20Action
```

For app search → retrieve-configuration → resource files → reference registration → debug overwrites, see **[hitl-node-apptask.md](../../../../../uipath-human-in-the-loop/references/hitl-node-apptask.md)**.

### Quick reference

```json
{
  "id": "invoiceReview1",
  "type": "uipath.human-in-the-loop.coded-action-app",
  "typeVersion": "<DEFINITION_VERSION>",
  "display": { "label": "Invoice Review" },
  "inputs": {
    "recipient": { "channels": ["ActionCenter"], "connections": {}, "assignee": { "type": "group" } },
    "app": {
      "displayName": "Invoice Approval",
      "name": "Invoice Approval",
      "key": "<app.key>",
      "folderPath": "Shared",
      "inputSchema": {
        "type": "object",
        "properties": { "<paramName>": { "type": "string" } }
      },
      "outputSchema": {
        "type": "object",
        "properties": { "<outputName>": { "type": "string" } }
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
      "properties": { "Action": { "type": "string", "enum": ["Submit"], "default": "Submit" } }
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

Rules:
- Fill `typeVersion` with the version returned by `uip maestro flow registry get <appKey>` for the specific deployed app. Unlike QuickForm, AppTask versions vary by app definition.
- `inputs.app.inputSchema` and `outputSchema` are JSON Schema objects (`{ "type": "object", "properties": { ... } }`), not arrays.
- `inputs.appInputBindings` maps names from `inputSchema.properties` to `"=vars.<path>"` expressions (with `=` and no `js:`). Without these bindings, input fields are blank.

### If the app does not exist

Record `[CREATE NEW] <description>` in the node table and use `core.logic.mock` as a placeholder. The app is out of scope; use the `uipath-coded-apps` skill to build it.

## Common pattern

```text
Manual Trigger -> RPA Process (extract) -> HITL (review) -> Decision (approved?) ->
  true: Script (submit) -> End
  false: End
```

## Debug

| Error | Cause | Fix |
| --- | --- | --- |
| Node type not found in registry (Option 2) | App not published or registry stale | If in same solution: `uip maestro flow registry list --local`. Otherwise: `uip login` then `uip maestro flow registry pull --force` |
| Task never completes | Human has not submitted the form | Check task assignment in Orchestrator |
| Output missing expected fields | App form does not match expected schema | Verify app form fields match what the flow expects |
| `outcome-completed` port unwired (Option 1) | Missing edge on output handle | Wire the `outcome-completed` output handle; an unwired `outcome-completed` blocks the flow indefinitely |