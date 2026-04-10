# HITL QuickForm Node — Direct JSON Reference

The agent writes the `uipath.human-in-the-loop` node directly into the `.flow` file as JSON. No CLI command needed to add the node.

---

## Full Node JSON

```json
{
  "id": "invoiceReview1",
  "type": "uipath.human-in-the-loop",
  "typeVersion": "1.0.0",
  "display": { "label": "Invoice Review" },
  "ui": { "position": { "x": 474, "y": 144 } },
  "inputs": {
    "type": "quick",
    "channels": [],
    "recipient": {
      "channels": ["ActionCenter"],
      "connections": {},
      "assignee": { "type": "group" }
    },
    "priority": "normal",
    "timeout": "PT24H",
    "schema": {
      "id": "a3f7c2d1-8b4e-4f9a-b2c5-6d8e1f3a7b9c",
      "title": "Invoice Review",
      "fields": [
        {
          "id": "invoiceid",
          "label": "Invoice ID",
          "type": "text",
          "direction": "input",
          "binding": "=js:$vars.fetchInvoice.result.invoiceId"
        },
        {
          "id": "amount",
          "label": "Amount",
          "type": "number",
          "direction": "input",
          "binding": "=js:$vars.fetchInvoice.result.amount"
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
        { "id": "approve", "name": "Approve", "isPrimary": true,  "outcomeType": "Positive", "action": "Continue" },
        { "id": "reject",  "name": "Reject",  "isPrimary": false, "outcomeType": "Negative", "action": "End" }
      ]
    }
  },
  "model": { "type": "bpmn:UserTask" }
}
```

**Required fields:** `id`, `type`, `typeVersion`, `ui.position`

**Node ID rule:** camelCase from the label, strip non-alphanumeric, append `1` (increment to `2`, `3`... until unique among existing node IDs). Example: `"Invoice Review"` → `invoiceReview1`.

---

## Definition Entry

Every `.flow` file must have one definition entry for `uipath.human-in-the-loop` in `workflow.definitions`. Add it exactly once — deduplicate by `nodeType`.

```json
{
  "nodeType": "uipath.human-in-the-loop",
  "version": "1.0.0",
  "category": "human-task",
  "tags": ["human-task", "hitl", "human-in-the-loop", "approval"],
  "sortOrder": 50,
  "display": {
    "label": "Human in the Loop",
    "icon": "users",
    "shape": "rectangle"
  },
  "handleConfiguration": [
    {
      "position": "left",
      "handles": [
        {
          "id": "input",
          "type": "target",
          "handleType": "input",
          "constraints": {
            "forbiddenSourceCategories": ["trigger"],
            "validationMessage": "Human tasks cannot be directly triggered"
          }
        }
      ],
      "visible": true
    },
    {
      "position": "right",
      "handles": [
        { "id": "completed", "label": "Completed", "type": "source", "handleType": "output", "showButton": true, "constraints": { "forbiddenTargetCategories": ["trigger"] } },
        { "id": "cancelled", "label": "Cancelled", "type": "source", "handleType": "output", "showButton": true, "constraints": { "forbiddenTargetCategories": ["trigger"] } },
        { "id": "timeout",   "label": "Timeout",   "type": "source", "handleType": "output", "showButton": true, "constraints": { "forbiddenTargetCategories": ["trigger"] } }
      ],
      "visible": true
    }
  ],
  "model": { "type": "bpmn:UserTask" },
  "inputDefinition": {
    "channels": [],
    "schema": {
      "inputs": [], "outputs": [], "inOuts": [],
      "outcomes": [{ "name": "Submit", "type": "string" }]
    },
    "timeout": "PT24H",
    "priority": "normal"
  },
  "outputDefinition": {
    "result": { "type": "object", "description": "Task result data", "source": "=result", "var": "result" },
    "status": { "type": "string", "description": "Task completion status (completed, cancelled, timeout)", "source": "=status", "var": "status" }
  }
}
```

---

## Edge Wiring

Wire all three output handles. Edge ID format: `{sourceNodeId}-{sourcePort}-{targetNodeId}-{targetPort}` (append `-2`, `-3` on collision).

```json
{ "id": "invoiceReview1-completed-processApproval1-input", "sourceNodeId": "invoiceReview1", "sourcePort": "completed", "targetNodeId": "processApproval1", "targetPort": "input" },
{ "id": "invoiceReview1-cancelled-end1-input",             "sourceNodeId": "invoiceReview1", "sourcePort": "cancelled", "targetNodeId": "end1",             "targetPort": "input" },
{ "id": "invoiceReview1-timeout-end2-input",               "sourceNodeId": "invoiceReview1", "sourcePort": "timeout",   "targetNodeId": "end2",             "targetPort": "input" }
```

**Always wire `completed`.** A HITL node with no edge on `completed` blocks the flow forever. Wire `cancelled` and `timeout` to end nodes if no specific handler exists.

---

## `variables.nodes` — Regenerate After Every Node Add/Remove

The HITL node exposes two outputs (`result`, `status`). After adding it, **completely replace** `workflow.variables.nodes` by iterating all nodes and collecting their outputs:

```json
"variables": {
  "nodes": [
    {
      "id": "invoiceReview1.result",
      "type": "object",
      "binding": { "nodeId": "invoiceReview1", "outputId": "result" }
    },
    {
      "id": "invoiceReview1.status",
      "type": "string",
      "binding": { "nodeId": "invoiceReview1", "outputId": "status" }
    }
  ]
}
```

Include entries for **all** nodes in the flow, not just the HITL node. Replace the entire array — do not append.

---

## Schema Conversion — Examples

The agent translates the user's business description into the `fields[]` and `outcomes[]` arrays. No CLI needed — apply these rules directly.

### Rules

| What | Rule |
|---|---|
| field `id` | lowercase label, spaces→`-`, strip non-alphanumeric. `"Invoice ID"` → `"invoiceid"`, `"Due Date"` → `"due-date"` |
| `direction` | `inputs[]` items → `"input"`, `outputs[]` → `"output"`, `inOuts[]` → `"inOut"` |
| field `type` | `"string"` → `"text"`, `"number"` → `"number"`, `"boolean"` → `"boolean"`, `"date"` → `"date"` |
| `binding` | `"varName"` → `"=js:$vars.<upstream-node-id>.result.<varName>"` (for input/inOut) |
| `variable` | output/inOut variable name — defaults to `id` if not specified |
| `required` | omit if false; set `true` for mandatory outputs |
| `outcomes[0]` | `isPrimary: true`, `outcomeType: "Positive"`, `action: "Continue"` |
| `outcomes[1+]` | `isPrimary: false`, `outcomeType: "Negative"`, `action: "End"` |
| `schema.id` | Generate a fresh UUID (e.g. `crypto.randomUUID()` or any UUID v4) |

### Example 1 — Simple approval (inputs only + outcomes)

Business description: *"Reviewer sees invoice ID and amount, clicks Approve or Reject"*

```json
"fields": [
  { "id": "invoiceid", "label": "Invoice ID", "type": "text",   "direction": "input", "binding": "=js:$vars.fetchData1.result.invoiceId" },
  { "id": "amount",    "label": "Amount",     "type": "number", "direction": "input", "binding": "=js:$vars.fetchData1.result.amount" }
],
"outcomes": [
  { "id": "approve", "name": "Approve", "isPrimary": true,  "outcomeType": "Positive", "action": "Continue" },
  { "id": "reject",  "name": "Reject",  "isPrimary": false, "outcomeType": "Negative", "action": "End" }
]
```

### Example 2 — Write-back validation (inOut — human can edit before confirming)

Business description: *"Human sees the AI-drafted email, can edit it, then clicks Send or Discard"*

```json
"fields": [
  { "id": "recipient",  "label": "Recipient",  "type": "text", "direction": "input", "binding": "=js:$vars.draft1.result.recipient" },
  { "id": "emailbody",  "label": "Email Body", "type": "text", "direction": "inOut", "binding": "=js:$vars.draft1.result.body", "variable": "emailBody" }
],
"outcomes": [
  { "id": "send",    "name": "Send",    "isPrimary": true,  "outcomeType": "Positive", "action": "Continue" },
  { "id": "discard", "name": "Discard", "isPrimary": false, "outcomeType": "Negative", "action": "End" }
]
```

### Example 3 — Data enrichment (output — human fills in missing fields)

Business description: *"Agent couldn't extract vendor name or cost center. Human fills them in and clicks Submit."*

```json
"fields": [
  { "id": "rawextract",  "label": "Raw Extract",  "type": "text", "direction": "input",  "binding": "=js:$vars.extract1.result.rawText" },
  { "id": "vendorname",  "label": "Vendor Name",  "type": "text", "direction": "output", "variable": "vendorName",  "required": true },
  { "id": "costcenter",  "label": "Cost Center",  "type": "text", "direction": "output", "variable": "costCenter", "required": true }
],
"outcomes": [
  { "id": "submit", "name": "Submit", "isPrimary": true, "outcomeType": "Positive", "action": "Continue" }
]
```

### Example 4 — Exception escalation (multiple outcomes + notes output)

Business description: *"If agent confidence is low, escalate. Human sees reasoning and score, can Retry, Skip, or Escalate further."*

```json
"fields": [
  { "id": "reasoning",       "label": "Agent Reasoning",  "type": "text",   "direction": "input",  "binding": "=js:$vars.classify1.result.reasoning" },
  { "id": "confidencescore", "label": "Confidence Score", "type": "number", "direction": "input",  "binding": "=js:$vars.classify1.result.score" },
  { "id": "notes",           "label": "Notes",            "type": "text",   "direction": "output", "variable": "notes" }
],
"outcomes": [
  { "id": "retry",    "name": "Retry",    "isPrimary": true,  "outcomeType": "Positive", "action": "Continue" },
  { "id": "skip",     "name": "Skip",     "isPrimary": false, "outcomeType": "Neutral",  "action": "Continue" },
  { "id": "escalate", "name": "Escalate", "isPrimary": false, "outcomeType": "Negative", "action": "End" }
]
```

> **`outcomeType` for middle outcomes:** Use `"Neutral"` when the outcome is neither clearly positive nor negative (e.g., Skip, Defer, Hold).

---

## Runtime Variables

After the HITL node, downstream nodes can reference:

| Variable | Type | What it contains |
|---|---|---|
| `$vars.<nodeId>.result` | object | All `output` and `inOut` fields the human filled in |
| `$vars.<nodeId>.result.<fieldVariable>` | varies | Individual field value (e.g. `$vars.invoiceReview1.result.decision`) |
| `$vars.<nodeId>.status` | string | `"completed"`, `"cancelled"`, or `"timeout"` |

**In a downstream script node:**
```javascript
const result = $vars.invoiceReview1.result;
if ($vars.invoiceReview1.status === "completed") {
  await updateSystem(result.vendorName, result.costCenter);
}
```
