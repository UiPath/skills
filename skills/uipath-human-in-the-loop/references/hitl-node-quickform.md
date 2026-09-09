# HITL QuickForm Node — Direct JSON Reference

Write `uipath.human-in-the-loop.quick-form` directly into the `.flow` file as JSON. **Direct JSON is the default.** Use the CLI only when the user explicitly requests it or direct JSON writing fails: [CLI reference: uip maestro flow hitl add](../../uipath-maestro-flow/references/shared/cli-commands.md#uip-maestro-flow-hitl-add).

## Step 1 — Extract the Schema Through Conversation

**Never block.** Infer answers from the prompt and upstream `.flow` data, use volunteered information, design and write the node immediately, and report the chosen schema prominently so the user can adjust it. Stop and report an open decision only when the request is genuinely too ambiguous for a sensible default; a prompt specifying fields, outcomes, and output shape is never too ambiguous.

Determine what the reviewer sees, whether they only choose an outcome or also enter data, and the named actions. Translate business requirements into `inputs`, `outputs`, `inOuts`, and `outcomes`:

- Approval/rejection: read-only context such as `invoiceId`, `amount`; outcomes such as `Approve`, `Reject`.
- Editable review: read-only context plus editable `inOut` data such as `emailBody`.
- Escalation: inputs such as reasoning and confidence; outputs such as action and notes; outcomes such as `Retry`, `Skip`, `Escalate`.
- Data completion: raw input plus output fields; outcome such as `Submit`.
- Proposed change: read-only proposal and target plus editable final value; outcomes such as `Approve`, `Reject`.

## Step 1b — Discover Upstream Variables

Before designing bindings, read both `workflow.variables.nodes` and `workflow.variables.globals`.

Each `variables.nodes` entry exposes a `$vars` path:

```json
{ "id": "fetchInvoice.output", "type": "object", "binding": { "nodeId": "fetchInvoice", "outputId": "output" } }
```

`fetchInvoice.output` maps to `$vars.fetchInvoice.output`; append nested fields such as `$vars.fetchInvoice.output.invoiceId`.

**Binding path key = upstream script output key, not the HITL field `id`.** Inspect upstream script source and use the property name in its `return`: if it returns `{ supplierName: "Acme" }`, bind with `vars.fetchSupplier.output.supplierName`, even if the HITL field id is `suppliername`.

| Node type | `outputId` | Access pattern |
|---|---|---|
| HTTP | `output` | `$vars.{nodeId}.output.body.{field}` |
| Script | `output` | `$vars.{nodeId}.output.{field}` |
| Prior HITL | `output`, `status` | `$vars.{nodeId}.output.{field}` |
| Agent | `output` | `$vars.{nodeId}.output.content` |
| Manual trigger | `output` | `$vars.start.output.{field}` |

Read `workflow.variables.globals`. A global such as:

```json
{ "id": "customerName", "direction": "in", "type": "string" }
```

maps directly to `vars.customerName`. Use `direction: "in"` globals for flow-level trigger inputs via `triggerNodeId`.

| Source | HITL `binding` | Other-node expression |
|---|---|---|
| Node output | `vars.<nodeId>.output.<field>` | `=js:$vars.<nodeId>.output.<field>` |
| Flow global (`direction: "in"`) | `vars.<globalId>` | `=js:$vars.<globalId>` |

`binding` uses the full existing path beginning with `vars.`; never add `=js:$`. `variable` declares an output/inOut global name and also requires `vars.`. See [How $vars paths are constructed in Flow](../../uipath-maestro-flow/references/shared/variables-and-expressions.md).

## Step 2 — Design the Schema

Plan `inputs.schema.fields[]` with these roles:

| Role | `direction` | Human can… | Use for |
|---|---|---|---|
| Input | `"input"` | Read only | Decision context |
| Output | `"output"` | Write | Data automation needs back |
| InOut | `"inOut"` | Read + modify | Data the human may correct |

Supported types are `string`, `number`, `boolean`, `date`, and `file`.

- Bind input fields to upstream data; use globals when appropriate.
- Include only output fields used downstream; set `required: true` for mandatory outputs.
- Use domain-specific outcomes, not generic `Submit` unless appropriate.
- Keep the schema focused.
- Write the node immediately and record the selected schema prominently in the final report.

## Full Node JSON

```json
{
  "id": "invoiceReview1",
  "type": "uipath.human-in-the-loop.quick-form",
  "typeVersion": "1.0",
  "display": { "label": "Invoice Review" },
  "inputs": {
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
        { "id": "invoiceid", "label": "Invoice ID", "type": "string", "direction": "input", "binding": "vars.fetchInvoice.output.invoiceId" },
        { "id": "amount", "label": "Amount", "type": "number", "direction": "input", "binding": "vars.fetchInvoice.output.amount" },
        { "id": "notes", "label": "Notes", "type": "string", "direction": "output", "variable": "vars.notes", "required": false },
        { "id": "decision", "label": "Decision", "type": "string", "direction": "output", "variable": "vars.decision", "required": true }
      ],
      "outcomes": [
        { "id": "approve", "name": "Approve", "type": "string", "isPrimary": true, "action": "Continue" },
        { "id": "reject", "name": "Reject", "type": "string", "isPrimary": false, "action": "End" }
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
        "notes": { "type": "string" },
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

Required top-level fields are `id`, `type`, and `typeVersion`. Put position in top-level `layout.nodes`, keyed by node id, never on the node. Derive the id as camelCase from the label, strip non-alphanumeric characters, append `1`, and increment until unique: `Invoice Review` → `invoiceReview1`.

## Definition Entry

Every `.flow` must contain exactly one `workflow.definitions` entry for this node type; deduplicate by `nodeType`:

```json
{
  "nodeType": "uipath.human-in-the-loop.quick-form",
  "version": "1.0",
  "category": "human-task",
  "description": "Fast inline approvals with inline debug",
  "tags": ["human-task", "hitl", "human-in-the-loop", "quick-form", "approval"],
  "sortOrder": 27,
  "display": { "label": "Quick Form", "icon": "users", "shape": "square" },
  "handleConfiguration": [
    {
      "position": "left",
      "handles": [{ "id": "input", "type": "target", "handleType": "input" }],
      "visible": true
    },
    {
      "position": "right",
      "handles": [{ "id": "completed", "label": "Completed", "type": "source", "handleType": "output", "showButton": true, "constraints": { "forbiddenTargetCategories": ["trigger"] } }],
      "visible": true
    }
  ],
  "model": { "type": "bpmn:UserTask", "serviceType": "Actions.HITL" },
  "inputDefaults": {
    "schema": {
      "fields": [],
      "outcomes": [{ "id": "submit", "name": "Submit", "type": "string", "isPrimary": true, "action": "Continue" }]
    },
    "recipient": { "channels": ["Email", "ActionCenter"], "connections": {}, "assignee": { "type": "group" } }
  },
  "outputDefinition": {
    "output": { "type": "object", "description": "Task result data", "source": "=result", "var": "output" },
    "status": { "type": "string", "description": "Task completion status", "source": "=result.Action", "var": "status" }
  }
}
```

## Edge Wiring

Wire the `completed` output handle to the downstream node. Use edge ids `{sourceNodeId}-{sourcePort}-{targetNodeId}-{targetPort}`; append `-2`, `-3`, and so on for collisions:

```json
{ "id": "invoiceReview1-completed-processApproval1-input", "sourceNodeId": "invoiceReview1", "sourcePort": "completed", "targetNodeId": "processApproval1", "targetPort": "input" }
```

**Always wire `completed`.** Without this edge the flow blocks forever.

## `variables.nodes` — Regenerate After Every Node Add/Remove

After adding or removing a node, completely replace `workflow.variables.nodes` by iterating every node and collecting its outputs. Include all nodes, not only HITL nodes; never append. Each HITL contributes exactly one `output` and one `status` entry, with no per-field entries:

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

Output and inOut values are embedded in the output object and accessed as `$vars.<nodeId>.output.<fieldId>`. **Scripts must always use `$vars.<nodeId>.output.<fieldId>`.** Do not use the global alias from `field.variable` directly in scripts. `$vars.decision` and `$vars.<nodeId>.output.decision` are different paths; the field-id path is reliable in script nodes. See Critical Rule 10 in SKILL.md.

## Canonical Field Shape

```json
{
  "fields": [
    { "id": "invoiceid", "type": "number", "label": "Invoice ID", "direction": "input", "binding": "vars.fetchInvoice1.output.invoiceId" },
    { "id": "vendorname", "type": "string", "label": "Vendor Name", "direction": "input", "binding": "vars.fetchInvoice1.output.vendorName" },
    { "id": "approveddate", "type": "date", "label": "Approved Date", "direction": "output", "variable": "vars.approvedDate" },
    { "id": "approved", "type": "boolean", "label": "Approved", "direction": "output", "variable": "vars.approved" }
  ],
  "outcomes": [
    { "id": "submit", "name": "Submit", "type": "string", "action": "Continue", "isPrimary": true }
  ]
}
```

Field rules:

- `id` is the lowercase label with spaces changed to `-` and non-alphanumeric characters stripped: `Invoice ID` → `invoiceid`, `Due Date` → `due-date`.
- `type` is exactly `string`, `number`, `boolean`, `date`, or `file`; never `text`.
- `binding` is only for input/inOut fields and is a raw `vars...` path with no `=js:$` prefix.
- `variable` is only for output/inOut fields and always has the form `vars.<name>`; default to `vars.<camelCase id>` when unspecified.
- Omit `required` when false; set it to `true` for mandatory outputs.
- Input fields have no `variable`; output fields have no `binding`; inOut fields have both.
- Generate a fresh UUID v4 for `schema.schemaId`, using `crypto.randomUUID()` or equivalent.
- `outcomes[0]` has `isPrimary: true` and `action: "Continue"`; later outcomes have `isPrimary: false` and `action: "End"`.
- Use `outcomeType: "Neutral"` for middle outcomes that are neither clearly positive nor negative, such as Skip, Defer, or Hold.

Compact patterns:

```json
// Input-only approval
"fields": [
  { "id": "invoiceid", "label": "Invoice ID", "type": "string", "direction": "input", "binding": "vars.fetchData1.output.invoiceId" },
  { "id": "amount", "label": "Amount", "type": "number", "direction": "input", "binding": "vars.fetchData1.output.amount" }
],
"outcomes": [
  { "id": "approve", "name": "Approve", "type": "string", "isPrimary": true, "action": "Continue" },
  { "id": "reject", "name": "Reject", "type": "string", "isPrimary": false, "action": "End" }
]

// Editable input
{ "id": "emailbody", "label": "Email Body", "type": "string", "direction": "inOut", "binding": "vars.draft1.output.body", "variable": "vars.emailBody" }

// Human-entered outputs
[
  { "id": "vendorname", "label": "Vendor Name", "type": "string", "direction": "output", "variable": "vars.vendorName", "required": true },
  { "id": "costcenter", "label": "Cost Center", "type": "string", "direction": "output", "variable": "vars.costCenter", "required": true }
]
```

## Runtime Variables

| Variable | Type | Contents |
|---|---|---|
| `$vars.<nodeId>.output` | object | All output and inOut values keyed by field `id` |
| `$vars.<nodeId>.output.<fieldId>` | varies | Individual field value keyed by field `id` |
| `$vars.<nodeId>.status` | string | Selected outcome name, such as `"Approve"` or `"Reject"` |
| `$vars.<globalId>` | varies | Workflow global created by output/inOut `field.variable`; strip `vars.` from the variable path |

The output object uses the field `id`, not the `variable` name. If `id` is `dec1` and `variable` is `vars.approvalResult`, use `$vars.<nodeId>.output.dec1` or `$vars.approvalResult`; in scripts, use only the node output path. Using the variable name as the output-object key produces `undefined`, and `flow validate` does not catch it.

In downstream scripts, access fields inline and do not destructure first:

```javascript
const vendorName = $vars.invoiceReview1.output.vendorName;
const costCenter = $vars.invoiceReview1.output.costCenter;
if ($vars.invoiceReview1.status === "approve") {
  await updateSystem(vendorName, costCenter);
}
// Wrong: const output = $vars.invoiceReview1.output; then output.vendorName
```