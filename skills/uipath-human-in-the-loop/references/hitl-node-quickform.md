# HITL QuickForm Node — Direct JSON Reference

The agent writes the `uipath.human-in-the-loop` node directly into the `.flow` file as JSON. **Direct JSON is the default.** A CLI opt-in is also available when the user explicitly requests it — see [cli-commands.md — uip maestro flow hitl add](../../../../uipath-maestro-flow/references/shared/cli-commands.md#uip-maestro-flow-hitl-add).

---

## Step 1 — Extract the Schema Through Conversation

Before designing the schema, ask these focused questions if the business description doesn't answer them. **Ask all missing ones in a single message — never one at a time.**

| What you need to know | Question to ask |
|---|---|
| What the reviewer sees | "What information does the reviewer need to make their decision?" |
| What they fill in | "Does the reviewer need to enter any data, or just click Approve/Reject?" |
| What actions they take | "What are the named actions — e.g. Approve/Reject, or something domain-specific like Accept/Negotiate/Decline?" |

**Common business descriptions → schema translations:**

| Business description | Schema shape |
|---|---|
| "Human reviews and approves/rejects an invoice" | `inputs: [invoiceId, amount]`, `outcomes: [Approve, Reject]` |
| "Reviewer checks agent-drafted email before sending" | `inputs: [draftEmail, recipientName]`, `inOuts: [emailBody]`, `outcomes: [Approve, Reject]` |
| "Escalate to human when confidence < 0.7" | `inputs: [agentReasoning, confidenceScore]`, `outputs: [action, notes]`, `outcomes: [Retry, Skip, Escalate]` |
| "Human fills in missing vendor data" | `inputs: [rawExtract]`, `outputs: [vendorName, costCenter]`, `outcomes: [Submit]` |
| "Approve before writing to ServiceNow" | `inputs: [proposedChange, targetSystem]`, `inOuts: [finalValue]`, `outcomes: [Approve, Reject]` |

---

## Step 1b — Discover Upstream Variables

Before designing input field bindings, read **both** `workflow.variables.nodes` and `workflow.variables.globals` from the `.flow` file.

### Node outputs (`variables.nodes`)

Each entry exposes exactly what `$vars` paths are available:

```json
{ "id": "fetchInvoice.output", "type": "object", "binding": { "nodeId": "fetchInvoice", "outputId": "output" } }
```

The `id` field is the `$vars` path — `fetchInvoice.output` → `$vars.fetchInvoice.output`. Nested field access appends `.fieldName` (e.g., `$vars.fetchInvoice.output.invoiceId`).

**outputId by node type:**

| Node type | outputId | Access pattern |
|---|---|---|
| HTTP node | `output` | `$vars.{nodeId}.output.body.{field}` |
| Script node | `output` | `$vars.{nodeId}.output.{field}` |
| Prior HITL node | `output`, `status` | `$vars.{nodeId}.output.{field}` |
| Agent node | `output` | `$vars.{nodeId}.output.content` |
| Trigger (manual) | `output` | `$vars.start.output.{field}` |

### Flow-level globals (`variables.globals`)

Also read `workflow.variables.globals`. Each entry has an `id` that maps directly to a `$vars` reference — no node prefix, no `.output` segment:

```json
{ "id": "customerName", "direction": "in", "type": "string" }
```

→ HITL binding: `"vars.customerName"` (no `=js:$` prefix — HITL binding is a raw path)

**When to use globals instead of node outputs:** When data was declared as a flow-level input variable (e.g. the trigger passes it as a named parameter via `triggerNodeId`), it lives in `globals` with `direction: "in"`. Bind directly to `vars.<globalId>` — do not add `.output` or a node prefix.

| Source | HITL `binding` format | Expression format (other nodes) |
|---|---|---|
| Node output | `vars.<nodeId>.output.<field>` | `=js:$vars.<nodeId>.output.<field>` |
| Flow global (`direction: "in"`) | `vars.<globalId>` | `=js:$vars.<globalId>` |

For the full variable system, see → [uipath-maestro-flow — variables-and-expressions.md](../../../../uipath-maestro-flow/references/shared/variables-and-expressions.md)

---

## Step 2 — Design the Schema

The node schema uses `fields[]` entries inside `inputs.schema`. Use these conceptual roles to plan the fields before writing the node JSON:

| Role | `direction` value | Human can… | Use for |
|---|---|---|---|
| Input field | `"input"` | Read only | Context the human needs to make a decision |
| Output field | `"output"` | Write | Data the automation needs back |
| InOut field | `"inOut"` | Read + modify | Data the human can see and optionally correct |

**Supported field types:** `text` (maps from `string`), `number`, `boolean`, `date`

**Date field notes:**
- Bound values must be ISO 8601 date strings: `"YYYY-MM-DD"` (e.g. `"2026-04-01"`). Non-ISO formats will not parse.
- **"Invalid time value" at design time** is a known rendering limitation. When `binding` is a JS expression (e.g. `=js:$vars.script1.output.submittedDate`), the form preview cannot evaluate the expression statically and displays "Invalid time value". This is display-only — at runtime the date picker pre-populates correctly if the upstream value is a valid `YYYY-MM-DD` string.
- Avoid JavaScript `Date` objects or epoch integers in the bound value; always coerce to `YYYY-MM-DD` string in the upstream script node before binding.

**Design rules:**
- Input fields: everything the human needs to decide — IDs, amounts, context; bind to upstream node output via `binding`
- Output fields: only what downstream nodes actually use; set `required: true` for mandatory outputs
- `outcomes`: use domain-specific names (Approve/Reject, not just Submit)
- Keep it focused — don't add fields the automation won't use

**Show the designed schema to the user and confirm before writing the node.**

---

## Full Node JSON

```json
{
  "id": "invoiceReview1",
  "type": "uipath.human-in-the-loop",
  "typeVersion": "1.0",
  "display": { "label": "Invoice Review" },
  "inputs": {
    "type": "quick",
    "title": "Invoice Review",
    "recipient": {
      "channels": ["Email", "ActionCenter"],
      "connections": {},
      "assignee": { "type": "group" }
    },
    "priority": "Low",
    "schema": {
      "schemaId": "a3f7c2d1-8b4e-4f9a-b2c5-6d8e1f3a7b9c",
      "fields": [
        {
          "id": "invoiceid",
          "label": "Invoice ID",
          "type": "text",
          "direction": "input",
          "binding": "vars.fetchInvoice.output.invoiceId"
        },
        {
          "id": "amount",
          "label": "Amount",
          "type": "number",
          "direction": "input",
          "binding": "vars.fetchInvoice.output.amount"
        },
        {
          "id": "notes",
          "label": "Notes",
          "type": "text",
          "direction": "output",
          "variable": "vars.notes",
          "required": false
        },
        {
          "id": "decision",
          "label": "Decision",
          "type": "text",
          "direction": "output",
          "variable": "vars.decision",
          "required": true
        }
      ],
      "outcomes": [
        { "id": "approve", "name": "Approve", "type": "string", "isPrimary": true,  "action": "Continue" },
        { "id": "reject",  "name": "Reject",  "type": "string", "isPrimary": false, "action": "End" }
      ]
    }
  },
  "outputs": {
    "output": {
      "type": "object",
      "description": "Task result data",
      "source": "=result",
      "var": "output",
      "properties": {
        "notes":    { "type": "string" },
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

**Required fields:** `id`, `type`, `typeVersion`. Position goes in the top-level `layout.nodes` object (keyed by node id), not on the node itself.

**Node ID rule:** camelCase from the label, strip non-alphanumeric, append `1` (increment to `2`, `3`... until unique among existing node IDs). Example: `"Invoice Review"` → `invoiceReview1`.

---

## Definition Entry

Every `.flow` file must have one definition entry for `uipath.human-in-the-loop` in `workflow.definitions`. Add it exactly once — deduplicate by `nodeType`.

```json
{
  "nodeType": "uipath.human-in-the-loop",
  "version": "1.0",
  "category": "human-task",
  "tags": ["human-task", "hitl", "human-in-the-loop", "approval"],
  "sortOrder": 50,
  "display": {
    "label": "Human in the Loop",
    "icon": "users",
    "shape": "square"
  },
  "handleConfiguration": [
    {
      "position": "left",
      "handles": [
        {
          "id": "input",
          "type": "target",
          "handleType": "input"
        }
      ],
      "visible": true
    },
    {
      "position": "right",
      "handles": [
        { "id": "completed", "label": "Completed", "type": "source", "handleType": "output", "showButton": true, "constraints": { "forbiddenTargetCategories": ["trigger"] } }
      ],
      "visible": true
    }
  ],
  "model": { "type": "bpmn:UserTask", "serviceType": "Actions.HITL" },
  "inputDefaults": {
    "type": "quick",
    "schema": {
      "fields": [],
      "outcomes": [{ "id": "submit", "name": "Submit", "type": "string", "isPrimary": true, "action": "Continue" }]
    },
    "recipient": {
      "channels": ["Email", "ActionCenter"],
      "connections": {},
      "assignee": { "type": "group" }
    }
  },
  "outputDefinition": {
    "output": { "type": "object", "description": "Task result data", "source": "=result", "var": "output" },
    "status": { "type": "string", "description": "Task completion status", "source": "=result.Action", "var": "status" }
  }
}
```

---

## Edge Wiring

Wire the `completed` output handle to the downstream node. Edge ID format: `{sourceNodeId}-{sourcePort}-{targetNodeId}-{targetPort}` (append `-2`, `-3` on collision).

```json
{ "id": "invoiceReview1-completed-processApproval1-input", "sourceNodeId": "invoiceReview1", "sourcePort": "completed", "targetNodeId": "processApproval1", "targetPort": "input" }
```

**Always wire `completed`.** A HITL node with no edge on `completed` blocks the flow forever.

---

## `variables.nodes` — Regenerate After Every Node Add/Remove

The HITL node exposes two outputs (`output`, `status`). After adding it, **completely replace** `workflow.variables.nodes` by iterating all nodes and collecting their outputs:

```json
"variables": {
  "nodes": [
    {
      "id": "invoiceReview1.output",
      "type": "object",
      "description": "Task result data",
      "binding": { "nodeId": "invoiceReview1", "outputId": "output" }
    },
    {
      "id": "invoiceReview1.status",
      "type": "string",
      "description": "Task completion status",
      "binding": { "nodeId": "invoiceReview1", "outputId": "status" }
    }
  ]
}
```

Include entries for **all** nodes in the flow, not just the HITL node. Replace the entire array — do not append. Add one `output` entry and one `status` entry per HITL node — no per-field entries. Output and inOut field values from the task are accessible via `$vars.<nodeId>.output.<fieldId>` at runtime (fields are embedded in the output object, not exposed as separate node variables).

Output-direction and inOut-direction fields are also materialized as workflow-level globals in `variables.globals` with `direction: "inout"` — these are accessible directly as `$vars.<globalId>` without a node prefix.

---

## Schema Conversion — Examples

The agent translates the user's business description into the `fields[]` and `outcomes[]` arrays. No CLI needed — apply these rules directly.

### Rules

| What | Rule |
|---|---|
| field `id` | lowercase label, spaces→`-`, strip non-alphanumeric. `"Invoice ID"` → `"invoiceid"`, `"Due Date"` → `"due-date"` |
| `direction` | `inputs[]` items → `"input"`, `outputs[]` → `"output"`, `inOuts[]` → `"inOut"` |
| field `type` | `"string"` → `"text"`, `"number"` → `"number"`, `"boolean"` → `"boolean"`, `"date"` → `"date"` |
| `binding` | **Input / inOut fields only.** Format: `"vars.<nodeId>.output.<field>"` for node outputs; `"vars.<globalId>"` for flow globals. **No `=js:$` prefix** — HITL binding is a raw path, not an expression. |
| `variable` | **Output / inOut fields only** — absent on input fields. Format: `"vars.<name>"` (with `vars.` prefix). Defaults to `"vars.<camelCaseId>"` if not specified. |
| `required` | omit if false; set `true` for mandatory outputs |
| `outcomes[0]` | `isPrimary: true`, `action: "Continue"` |
| `outcomes[1+]` | `isPrimary: false`, `action: "End"` |
| `schema.schemaId` | Generate a fresh UUID (e.g. `crypto.randomUUID()` or any UUID v4) |

### Example 1 — Simple approval (inputs only + outcomes)

Business description: *"Reviewer sees invoice ID and amount, clicks Approve or Reject"*

```json
"fields": [
  { "id": "invoiceid", "label": "Invoice ID", "type": "text",   "direction": "input", "binding": "vars.fetchData1.output.invoiceId" },
  { "id": "amount",    "label": "Amount",     "type": "number", "direction": "input", "binding": "vars.fetchData1.output.amount" }
],
"outcomes": [
  { "id": "approve", "name": "Approve", "type": "string", "isPrimary": true,  "action": "Continue" },
  { "id": "reject",  "name": "Reject",  "type": "string", "isPrimary": false, "action": "End" }
]
```

### Example 2 — Write-back validation (inOut — human can edit before confirming)

Business description: *"Human sees the AI-drafted email, can edit it, then clicks Send or Discard"*

```json
"fields": [
  { "id": "recipient",  "label": "Recipient",  "type": "text", "direction": "input", "binding": "vars.draft1.output.recipient" },
  { "id": "emailbody",  "label": "Email Body", "type": "text", "direction": "inOut", "binding": "vars.draft1.output.body", "variable": "vars.emailBody" }
],
"outcomes": [
  { "id": "send",    "name": "Send",    "type": "string", "isPrimary": true,  "action": "Continue" },
  { "id": "discard", "name": "Discard", "type": "string", "isPrimary": false, "action": "End" }
]
```

### Example 3 — Data enrichment (output — human fills in missing fields)

Business description: *"Agent couldn't extract vendor name or cost center. Human fills them in and clicks Submit."*

```json
"fields": [
  { "id": "rawextract",  "label": "Raw Extract",  "type": "text", "direction": "input",  "binding": "vars.extract1.output.rawText" },
  { "id": "vendorname",  "label": "Vendor Name",  "type": "text", "direction": "output", "variable": "vars.vendorName",  "required": true },
  { "id": "costcenter",  "label": "Cost Center",  "type": "text", "direction": "output", "variable": "vars.costCenter", "required": true }
],
"outcomes": [
  { "id": "submit", "name": "Submit", "type": "string", "isPrimary": true, "action": "Continue" }
]
```

### Example 4 — Exception escalation (multiple outcomes + notes output)

Business description: *"If agent confidence is low, escalate. Human sees reasoning and score, can Retry, Skip, or Escalate further."*

```json
"fields": [
  { "id": "reasoning",       "label": "Agent Reasoning",  "type": "text",   "direction": "input",  "binding": "vars.classify1.output.reasoning" },
  { "id": "confidencescore", "label": "Confidence Score", "type": "number", "direction": "input",  "binding": "vars.classify1.output.score" },
  { "id": "notes",           "label": "Notes",            "type": "text",   "direction": "output", "variable": "vars.notes" }
],
"outcomes": [
  { "id": "retry",    "name": "Retry",    "type": "string", "isPrimary": true,  "action": "Continue" },
  { "id": "skip",     "name": "Skip",     "type": "string", "isPrimary": false, "action": "End" },
  { "id": "escalate", "name": "Escalate", "type": "string", "isPrimary": false, "action": "End" }
]
```

> **`outcomeType` for middle outcomes:** Use `"Neutral"` when the outcome is neither clearly positive nor negative (e.g., Skip, Defer, Hold).

---

## Runtime Variables

After the HITL node, downstream nodes can reference:

| Variable | Type | What it contains |
|---|---|---|
| `$vars.<nodeId>.output` | object | All `output` and `inOut` field values keyed by **field `id`** |
| `$vars.<nodeId>.output.<fieldId>` | varies | Individual field value using the field's `id` (e.g. `$vars.invoiceReview1.output.decision`) |
| `$vars.<nodeId>.status` | string | Selected outcome name (e.g. `"Approve"`, `"Reject"`) |
| `$vars.<globalId>` | varies | Workflow-global variable for output/inOut fields — accessible without node prefix. The `globalId` is derived from `field.variable` (strip `vars.` prefix) |

> **`fieldId` not `variable`**: The output object properties are keyed by the field's `id` (e.g. `"decision"`), not by the `variable` property. The `variable` property (`"vars.approvalResult"`) creates a separate workflow-global variable (`$vars.approvalResult`) — it does not change the key used in the output object. If a field has `"id": "dec1"` and `"variable": "vars.approvalResult"`, access it via the object as `$vars.nodeId.output.dec1`, or directly as `$vars.approvalResult`.

**In a downstream script node:**
```javascript
const output = $vars.invoiceReview1.output;
// Access by field ID, not variable name
if ($vars.invoiceReview1.status === "approve") {
  await updateSystem(output.vendorName, output.costCenter);
}
```
