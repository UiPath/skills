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

→ binding: `"=js:$vars.customerName"`

**When to use globals instead of node outputs:** When data was declared as a flow-level input variable (e.g. the trigger passes it as a named parameter via `triggerNodeId`), it lives in `globals` with `direction: "in"`. Bind directly to `=js:$vars.<globalId>` — do not add `.output` or a node prefix.

| Source | Access pattern |
|---|---|
| Node output | `=js:$vars.<nodeId>.output.<field>` |
| Flow global (`direction: "in"`) | `=js:$vars.<globalId>` |

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
      "id": "a3f7c2d1-8b4e-4f9a-b2c5-6d8e1f3a7b9c",
      "fields": [
        {
          "id": "invoiceid",
          "label": "Invoice ID",
          "type": "text",
          "direction": "input",
          "binding": "=js:$vars.fetchInvoice.output.invoiceId",
          "variable": "=js:$vars.fetchInvoice.output.invoiceId"
        },
        {
          "id": "amount",
          "label": "Amount",
          "type": "number",
          "direction": "input",
          "binding": "=js:$vars.fetchInvoice.output.amount",
          "variable": "=js:$vars.fetchInvoice.output.amount"
        },
        {
          "id": "notes",
          "label": "Notes",
          "type": "text",
          "direction": "output",
          "variable": "notes",
          "required": false
        },
        {
          "id": "decision",
          "label": "Decision",
          "type": "text",
          "direction": "output",
          "variable": "decision",
          "required": true
        }
      ],
      "outcomes": [
        { "id": "approve", "name": "Approve", "isPrimary": true,  "outcomeType": "Positive" },
        { "id": "reject",  "name": "Reject",  "isPrimary": false, "outcomeType": "Negative" }
      ]
    }
  },
  "outputs": {
    "output":   { "type": "object", "source": "=result",        "var": "output" },
    "status":   { "type": "string", "source": "=result.Action", "var": "status" },
    "notes":    { "type": "string", "source": "=result.notes",    "var": "notes",    "custom": true },
    "decision": { "type": "string", "source": "=result.decision", "var": "decision", "custom": true }
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
  "model": { "type": "bpmn:UserTask" },
  "inputDefinition": {
    "type": "quick",
    "schema": {
      "fields": [],
      "outcomes": [{ "id": "submit", "name": "Submit", "type": "string", "isPrimary": true, "outcomeType": "Positive" }]
    },
    "recipient": {
      "channels": ["Email", "ActionCenter"],
      "connections": {},
      "assignee": { "type": "group" }
    },
    "timeout": "PT24H",
    "priority": "Normal"
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
      "binding": { "nodeId": "invoiceReview1", "outputId": "output" }
    },
    {
      "id": "invoiceReview1.status",
      "type": "string",
      "binding": { "nodeId": "invoiceReview1", "outputId": "status" }
    },
    {
      "id": "invoiceReview1.notes",
      "type": "string",
      "binding": { "nodeId": "invoiceReview1", "outputId": "notes" }
    },
    {
      "id": "invoiceReview1.decision",
      "type": "string",
      "binding": { "nodeId": "invoiceReview1", "outputId": "decision" }
    }
  ]
}
```

Include entries for **all** nodes in the flow, not just the HITL node. Replace the entire array — do not append.

**Per-field outputs:** When the schema has `output` or `inOut` direction fields, add one entry per field using the output key name from `node.outputs` (the `variable` property value, or the camelCase-derived name when `variable` is omitted). These are also materialized as flow-level globals in `variables.globals` with `direction: "out"`.

---

## Schema Conversion — Examples

The agent translates the user's business description into the `fields[]` and `outcomes[]` arrays. No CLI needed — apply these rules directly.

### Rules

| What | Rule |
|---|---|
| field `id` | lowercase label, spaces→`-`, strip non-alphanumeric. `"Invoice ID"` → `"invoiceid"`, `"Due Date"` → `"due-date"` |
| `direction` | `inputs[]` items → `"input"`, `outputs[]` → `"output"`, `inOuts[]` → `"inOut"` |
| field `type` | `"string"` → `"text"`, `"number"` → `"number"`, `"boolean"` → `"boolean"`, `"date"` → `"date"` |
| `binding` | Read `variables.nodes` for node outputs → `"=js:$vars.<nodeId>.<outputId>.<field>"`. Read `variables.globals` for flow-level inputs → `"=js:$vars.<globalId>"`. Always read both before constructing bindings — never assume source |
| `variable` (input/inOut direction) | Set to the **same expression as `binding`**. The BPMN engine reads `variable` to build `HitlTaskArguments` and pre-populate the form at task-creation time. `binding` alone is only stored for workbench display — the runtime does not read it. Without `variable`, input fields appear blank in Action Center and inline debug. |
| `variable` (output direction) | Short camelCase name for the output variable — defaults to `id` if not specified |
| `required` | omit if false; set `true` for mandatory outputs |
| `outcomes[0]` | `isPrimary: true`, `outcomeType: "Positive"` |
| `outcomes[1+]` | `isPrimary: false`, `outcomeType: "Negative"` (use `"Neutral"` for middle outcomes like Skip/Defer) |
| `schema.id` | Generate a fresh UUID (e.g. `crypto.randomUUID()` or any UUID v4) |

### Example 1 — Simple approval (inputs only + outcomes)

Business description: *"Reviewer sees invoice ID and amount, clicks Approve or Reject"*

```json
"fields": [
  { "id": "invoiceid", "label": "Invoice ID", "type": "text",   "direction": "input", "binding": "=js:$vars.fetchData1.output.invoiceId", "variable": "=js:$vars.fetchData1.output.invoiceId" },
  { "id": "amount",    "label": "Amount",     "type": "number", "direction": "input", "binding": "=js:$vars.fetchData1.output.amount",    "variable": "=js:$vars.fetchData1.output.amount" }
],
"outcomes": [
  { "id": "approve", "name": "Approve", "isPrimary": true,  "outcomeType": "Positive" },
  { "id": "reject",  "name": "Reject",  "isPrimary": false, "outcomeType": "Negative" }
]
```

### Example 2 — Write-back validation (inOut — human can edit before confirming)

Business description: *"Human sees the AI-drafted email, can edit it, then clicks Send or Discard"*

```json
"fields": [
  { "id": "recipient",  "label": "Recipient",  "type": "text", "direction": "input", "binding": "=js:$vars.draft1.output.recipient", "variable": "=js:$vars.draft1.output.recipient" },
  { "id": "emailbody",  "label": "Email Body", "type": "text", "direction": "inOut", "binding": "=js:$vars.draft1.output.body", "variable": "emailBody" }
],
"outcomes": [
  { "id": "send",    "name": "Send",    "isPrimary": true,  "outcomeType": "Positive" },
  { "id": "discard", "name": "Discard", "isPrimary": false, "outcomeType": "Negative" }
]
```

### Example 3 — Data enrichment (output — human fills in missing fields)

Business description: *"Agent couldn't extract vendor name or cost center. Human fills them in and clicks Submit."*

```json
"fields": [
  { "id": "rawextract",  "label": "Raw Extract",  "type": "text", "direction": "input",  "binding": "=js:$vars.extract1.output.rawText", "variable": "=js:$vars.extract1.output.rawText" },
  { "id": "vendorname",  "label": "Vendor Name",  "type": "text", "direction": "output", "variable": "vendorName",  "required": true },
  { "id": "costcenter",  "label": "Cost Center",  "type": "text", "direction": "output", "variable": "costCenter", "required": true }
],
"outcomes": [
  { "id": "submit", "name": "Submit", "isPrimary": true, "outcomeType": "Positive" }
]
```

### Example 4 — Exception escalation (multiple outcomes + notes output)

Business description: *"If agent confidence is low, escalate. Human sees reasoning and score, can Retry, Skip, or Escalate further."*

```json
"fields": [
  { "id": "reasoning",       "label": "Agent Reasoning",  "type": "text",   "direction": "input",  "binding": "=js:$vars.classify1.output.reasoning", "variable": "=js:$vars.classify1.output.reasoning" },
  { "id": "confidencescore", "label": "Confidence Score", "type": "number", "direction": "input",  "binding": "=js:$vars.classify1.output.score",     "variable": "=js:$vars.classify1.output.score" },
  { "id": "notes",           "label": "Notes",            "type": "text",   "direction": "output", "variable": "notes" }
],
"outcomes": [
  { "id": "retry",    "name": "Retry",    "isPrimary": true,  "outcomeType": "Positive" },
  { "id": "skip",     "name": "Skip",     "isPrimary": false, "outcomeType": "Neutral"  },
  { "id": "escalate", "name": "Escalate", "isPrimary": false, "outcomeType": "Negative" }
]
```

> **`outcomeType` for middle outcomes:** Use `"Neutral"` when the outcome is neither clearly positive nor negative (e.g., Skip, Defer, Hold).

---

## Runtime Variables

After the HITL node, downstream nodes can reference:

| Variable | Type | What it contains |
|---|---|---|
| `$vars.<nodeId>.output` | object | All `output` and `inOut` fields the human filled in, keyed by **field `id`** |
| `$vars.<nodeId>.output.<fieldId>` | varies | Individual field value using the field's `id` property (e.g. `$vars.invoiceReview1.output.decision`) |
| `$vars.<nodeId>.status` | string | Selected outcome id (e.g. `"approve"`, `"reject"`) |
| `$vars.<nodeId>.<variable>` | varies | Per-field output also exposed as a named node variable (key matches `field.variable` or the derived camelCase name) |
| `$vars.<variable>` | varies | Workflow-global variable (`custom: true` in `outputs`). Accessible without the node prefix in downstream expressions |

> **`fieldId` not `variable`**: The output object properties are keyed by the field's `id` (e.g. `"decision"`), not by the `variable` property. The `variable` property creates a separate workflow-global variable (`$vars.{variable}`) — it does not change the key used in the output object. If a field has `"id": "dec1"` and `"variable": "approvalResult"`, access it as `$vars.nodeId.output.dec1`, not `.approvalResult`.

**In a downstream script node:**
```javascript
const output = $vars.invoiceReview1.output;
// Access by field ID, not variable name
if ($vars.invoiceReview1.status === "approve") {
  await updateSystem(output.vendorName, output.costCenter);
}
```
