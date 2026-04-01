# HITL (Human-in-the-Loop) Node — Reference

A HITL node pauses a flow and waits for a human to complete a task in UiPath Action Center. When the task is done, the flow resumes on one of three output handles: `completed`, `cancelled`, or `timeout`.

Internally the node is `uipath.human-in-the-loop` — a `bpmn:UserTask` with `serviceType: Actions.HITL`. The task schema (inputs/outputs/outcomes) is embedded directly in the `.flow` file — no external app, no separate deployment.

---

## When to Add a HITL Node

| Signal in description | HITL use case |
|---|---|
| "human reviews / approves / rejects" | Approval gate |
| "escalate to a person / manager" | Exception escalation |
| "fill in missing data / enrich" | Data enrichment by human |
| "compliance sign-off / four-eyes check" | Compliance review |
| "pause until someone confirms" | Manual confirmation gate |

---

## Schema Design Guide

The `--schema` value defines what data the human task collects. It uses a flat list format (NOT JSON Schema):

```json
{
  "inputs":   [{ "name": "fieldName", "type": "string" }],
  "outputs":  [{ "name": "fieldName", "type": "string" }],
  "inOuts":   [{ "name": "fieldName", "type": "string" }],
  "outcomes": [{ "name": "Approve",  "type": "string" }, { "name": "Reject", "type": "string" }]
}
```

- **`inputs`** — data passed into the task (read-only for the human)
- **`outputs`** — data the human fills in and returns to the flow
- **`inOuts`** — data the human can read and modify
- **`outcomes`** — named action buttons the human clicks to complete the task

All fields are optional. If omitted, defaults to `outcomes: [{ name: "Submit", type: "string" }]`.

### Approval pattern

```json
{
  "inputs":   [{ "name": "invoiceId",     "type": "string" },
               { "name": "invoiceAmount", "type": "number" }],
  "outcomes": [{ "name": "Approve", "type": "string" },
               { "name": "Reject",  "type": "string" }]
}
```

### Data enrichment pattern (human fills in missing fields)

```json
{
  "inputs":  [{ "name": "rawData",    "type": "string" }],
  "outputs": [{ "name": "vendorName", "type": "string" },
              { "name": "costCenter", "type": "string" }],
  "outcomes": [{ "name": "Submit", "type": "string" }]
}
```

### Exception handling pattern

```json
{
  "outputs":  [{ "name": "action", "type": "string" },
               { "name": "reason", "type": "string" }],
  "outcomes": [{ "name": "Retry",    "type": "string" },
               { "name": "Skip",     "type": "string" },
               { "name": "Escalate", "type": "string" }]
}
```

---

## CLI Command Reference

Minimal (defaults only):

```bash
uip flow hitl add <file>
```

With schema and options:

```bash
uip flow hitl add flow_files/InvoiceApproval.flow \
  --schema '{"inputs":[{"name":"invoiceId","type":"string"}],"outcomes":[{"name":"Approve","type":"string"},{"name":"Reject","type":"string"}]}' \
  --label "Invoice Review" \
  --priority normal \
  --timeout PT48H \
  --position 400,200
```

| Option | Values | Default |
|---|---|---|
| `--schema` | JSON string (inputs/outputs/inOuts/outcomes) | `{ outcomes: [{ name: "Submit" }] }` |
| `--label` | display label on the canvas | `"Human in the Loop"` |
| `--priority` | `low` `normal` `high` `critical` | `normal` |
| `--timeout` | ISO 8601 duration string | `PT24H` |
| `--position` | `x,y` canvas coordinates | `0,0` |

**Output:**
```json
{
  "Result": "Success",
  "Code": "HitlNodeAdded",
  "Data": {
    "NodeId": "invoiceReview1",
    "NodeType": "uipath.human-in-the-loop",
    "Label": "Invoice Review",
    "DefinitionAdded": true
  }
}
```

Note the returned `NodeId` — you need it to wire edges.

---

## After Adding — Wire the Edges

The HITL node has three output handles. Wire the ones relevant to your flow:

```bash
# Human completed the task → continue the happy path
uip flow edge add <file> --source <hitl-node-id>:completed --target <next-node-id>:input

# Human cancelled the task → route to cancellation handler
uip flow edge add <file> --source <hitl-node-id>:cancelled --target <cancel-handler-id>:input

# Task timed out → route to timeout handler
uip flow edge add <file> --source <hitl-node-id>:timeout --target <timeout-handler-id>:input
```

At minimum, always wire `completed`. Wire `cancelled` and `timeout` to end nodes or error handlers.

### Runtime outputs

The HITL node produces two variables after completion:

| Variable | Type | Description |
|---|---|---|
| `result` | object | The data the human filled in (matches `outputs` and `inOuts` schema fields) |
| `status` | string | `"completed"`, `"cancelled"`, or `"timeout"` |

Reference these in subsequent nodes as `=<hitl-node-id>.result` and `=<hitl-node-id>.status`.

---

## Validate After Adding

```bash
uip flow validate flow_files/<ProjectName>.flow --format json
```

Always validate after adding the node and wiring its edges.

---

## Full Example — Invoice Approval Flow

**Scenario**: RPA extracts invoice data → human reviews and approves → approved invoices are posted to ERP.

### 1. Add the HITL review node

```bash
uip flow hitl add flow_files/InvoiceApproval.flow \
  --schema '{"inputs":[{"name":"invoiceId","type":"string"},{"name":"amount","type":"number"}],"outcomes":[{"name":"Approve","type":"string"},{"name":"Reject","type":"string"}]}' \
  --label "Invoice Review" \
  --priority normal
```

Note the returned node id, e.g. `invoiceReview1`.

### 2. Wire the edges

```bash
# extraction node → HITL review
uip flow edge add flow_files/InvoiceApproval.flow \
  --source extractInvoice1:output --target invoiceReview1:input

# HITL completed → post to ERP
uip flow edge add flow_files/InvoiceApproval.flow \
  --source invoiceReview1:completed --target postToErp1:input

# HITL cancelled → notify and stop
uip flow edge add flow_files/InvoiceApproval.flow \
  --source invoiceReview1:cancelled --target notifyRejection1:input

# HITL timeout → escalation path
uip flow edge add flow_files/InvoiceApproval.flow \
  --source invoiceReview1:timeout --target escalate1:input
```

### 3. Validate

```bash
uip flow validate flow_files/InvoiceApproval.flow --format json
```
