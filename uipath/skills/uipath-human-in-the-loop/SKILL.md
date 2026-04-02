---
name: uipath-human-in-the-loop
description: "TRIGGER when: User describes a business process involving human approval, review, escalation, compliance sign-off, exception handling, or write-back validation — even if they do not explicitly say 'HITL'; User is building a Flow, Maestro process, or Coded Agent and a human decision point exists in the business logic; User asks to add a human review step, approval gate, or pause-for-human. DO NOT TRIGGER when: The process is fully automated with no human decision point; User is asking about Action Center task administration or runtime task management (not automation authoring); User is deploying or publishing — use uipath-development instead."
metadata:
  allowed-tools: Bash, Read, Write, Edit, Glob, Grep
---

# UiPath Human-in-the-Loop Assistant

Recognizes when a business process needs a human decision point, designs the task schema through conversation, and wires the HITL node into the automation — Flow, Maestro, or Coded Agent.

## When to Use This Skill

- User describes **approval gates** — invoice approval, offer letter review, compliance sign-off
- User describes **exception escalation** — "if confidence is low, escalate to a human"
- User describes **write-back validation** — "human approves before agent writes to ServiceNow"
- User describes **data enrichment** — human fills in missing fields the automation cannot resolve
- User explicitly asks to **add a HITL node**, human review step, or Action Center task
- User is building any automation where **a human must act before the process can continue**

See [references/hitl-patterns.md](references/hitl-patterns.md) for the full business pattern recognition guide.

---

## Step 0 — Resolve the `uip` binary

```bash
UIP=$(command -v uip 2>/dev/null || npm root -g 2>/dev/null | sed 's|/node_modules$||')/bin/uip
$UIP --version
```

Use `$UIP` in place of `uip` for all subsequent commands if the plain `uip` command isn't found.

> **Local dev note:** If working inside the uipcli repo, replace `uip` with `bun run start`.

---

## Step 1 — Detect the Surface and Find the Flow File

Run these checks in order:

```bash
# Check for a .flow file (Flow project)
find . -name "*.flow" -maxdepth 4 | head -5

# Check for agent.json (Coded Agent project)
find . -name "agent.json" -maxdepth 4 | head -3

# Check for Maestro .bpmn (Maestro process)
find . -name "*.bpmn" -maxdepth 4 | head -3
```

| Found | Surface | CLI available |
|---|---|---|
| `.flow` file | **Flow** | Yes — `uip flow hitl add` |
| `agent.json` | **Coded Agent** | Partial — escalation CLI in-flight |
| `.bpmn` (Maestro) | **Maestro** | Not yet — guide user manually |

**If the user mentioned a specific file path**, use that directly.

**If no `.flow` file exists and surface is Flow**, create one first:

```bash
uip flow init <ProjectName>
# Creates: <ProjectName>/flow_files/<ProjectName>.flow
```

The flow file path will be `<ProjectName>/flow_files/<ProjectName>.flow`.

---

## Step 2 — Read the Business Context

If a `.flow` file already exists, read it to understand the current nodes and edges:

```bash
cat <path-to-flow-file>
```

Identify:
1. **Where** in the process the human decision point belongs (after which existing node)
2. **What the human needs to see** — data produced by upstream nodes
3. **What the human must provide back** — data needed by downstream nodes
4. **What actions they can take** — the named outcome buttons

---

## Step 2b — Proactive HITL Recommendation

**If the user did NOT explicitly mention HITL**, scan the business description for these signals before proceeding:

| Signal | Pattern | Why a human checkpoint matters |
|---|---|---|
| "agent writes to", "updates", "posts to" an external system | Write-back validation | Prevents incorrect writes to production systems |
| "if confidence is low", "when uncertain", "edge case" | Exception escalation | Agent cannot resolve autonomously |
| "approves", "reviews", "signs off", "four-eyes" | Approval gate | Business or compliance requirement |
| "fills in missing", "validates extraction", "corrects" | Data enrichment | Automation produced incomplete data |
| "compliance", "regulatory", "audit trail" | Compliance checkpoint | Mandated human sign-off |

**When a signal is found, say this before doing anything else:**

> "I noticed that [quote the specific part of their description]. This is a [pattern name] — a point where [brief consequence if no human reviews]. I recommend inserting a Human-in-the-Loop step here so that [human role] can [action] before the automation [continues/writes/sends]. Should I add it?"

Wait for confirmation. Do not proceed to schema design until the user confirms.

**Example:**
> User: "Build an automation that reads support tickets, uses AI to generate an RCA, and updates the ticket in ServiceNow."
>
> Agent: "I noticed that the automation writes AI-generated content directly back to ServiceNow. This is a write-back validation pattern — if the RCA is incorrect and nobody reviews it, wrong data goes into production tickets. I recommend inserting a Human-in-the-Loop step so that a support lead can review and optionally edit the RCA before the update is applied. Should I add it?"

---

## Step 3 — Extract the Schema Through Conversation

Before designing the schema, ask these focused questions if the business description doesn't answer them. **Ask all missing ones in a single message — never one at a time.**

| What you need to know | Question to ask |
|---|---|
| What the reviewer sees | "What information does the reviewer need to make their decision?" |
| What they fill in | "Does the reviewer need to enter any data, or just click Approve/Reject?" |
| What actions they take | "What are the named actions — e.g. Approve/Reject, or something domain-specific like Accept/Negotiate/Decline?" |
| Timeout | "How long before the task times out if nobody acts? (default: 24 hours)" |
| Priority | "Is this normal priority, or high/critical?" |

**Common business descriptions → schema translations:**

| Business description | Schema shape |
|---|---|
| "Human reviews and approves/rejects an invoice" | `inputs: [invoiceId, amount]`, `outcomes: [Approve, Reject]` |
| "Reviewer checks agent-drafted email before sending" | `inputs: [draftEmail, recipientName]`, `inOuts: [emailBody]`, `outcomes: [Approve, Reject]` |
| "Escalate to human when confidence < 0.7" | `inputs: [agentReasoning, confidenceScore]`, `outputs: [action, notes]`, `outcomes: [Retry, Skip, Escalate]` |
| "Human fills in missing vendor data" | `inputs: [rawExtract]`, `outputs: [vendorName, costCenter]`, `outcomes: [Submit]` |
| "Approve before writing to ServiceNow" | `inputs: [proposedChange, targetSystem]`, `inOuts: [finalValue]`, `outcomes: [Approve, Reject]` |

---

## Step 4 — Design the Schema

The CLI accepts this format for `--schema`:

```json
{
  "inputs":   [{ "name": "fieldName", "type": "string" }],
  "outputs":  [{ "name": "fieldName", "type": "string" }],
  "inOuts":   [{ "name": "fieldName", "type": "string" }],
  "outcomes": [{ "name": "Approve",  "type": "string" }]
}
```

| Field | Human can… | Use for |
|---|---|---|
| `inputs` | Read only | Context the human needs to make a decision |
| `outputs` | Write | Data the automation needs back |
| `inOuts` | Read + modify | Data the human can see and optionally correct |
| `outcomes` | Click one | Named action buttons |

**Supported types:** `string`, `number`, `boolean`, `date`

**Design rules:**
- `inputs`: everything the human needs to decide — IDs, amounts, context
- `outputs`: only what downstream nodes actually use
- `outcomes`: use domain-specific names (Approve/Reject, not just Submit)
- Keep it focused — don't add fields the automation won't use

**Show the designed schema to the user and confirm before running the CLI.**

---

## Step 5 — Run the CLI

### Surface: Flow

**Full sequence:**

```bash
# 1. Add the HITL node
uip flow hitl add <path-to-flow-file> \
  --schema '<schema-json>' \
  --label "<Label>" \
  --priority normal \
  --timeout PT24H

# Note the NodeId returned in Data.NodeId

# 2. Wire the output handles
uip flow edge add <file> --source <NodeId>:completed --target <next-node-id>:input
uip flow edge add <file> --source <NodeId>:cancelled --target <cancel-node-id>:input
uip flow edge add <file> --source <NodeId>:timeout   --target <timeout-node-id>:input

# 3. Validate
uip flow validate <file> --format json
```

**CLI options:**

| Option | Values | Default |
|---|---|---|
| `--schema` | JSON string (Step 4 format) | `{ outcomes: [{ name: "Submit" }] }` |
| `--label` | canvas label | `"Human in the Loop"` |
| `--priority` | `low` `normal` `high` `critical` | `normal` |
| `--timeout` | ISO 8601 duration (PT24H, PT48H, P7D) | `PT24H` |
| `--position` | `x,y` canvas coordinates | `0,0` |

**If no downstream nodes exist yet** for cancelled/timeout, wire them to the nearest end node or omit and note them as TODOs for the user.

**Runtime variables available after the HITL node:**
- `$vars.<NodeId>.result` — object containing all `outputs` and `inOuts` the human filled in
- `$vars.<NodeId>.result.<fieldName>` — access individual fields
- `$vars.<NodeId>.status` — `"completed"`, `"cancelled"`, or `"timeout"`

**How to use HITL output in a downstream script node:**

```javascript
// In a script node that runs after the HITL node completes
const reviewResult = $vars.rcaReview1.result;
const proposedUpdate = reviewResult.proposedUpdate;  // inOut field the human edited
const reviewNotes = reviewResult.notes;              // output field the human filled in

if ($vars.rcaReview1.status === "completed") {
    // Use the human-reviewed value for the write-back
    await updateServiceNow(ticketId, proposedUpdate);
}
```

**If no downstream nodes exist yet** for `cancelled`/`timeout`, create placeholder end nodes first:

```bash
# Create end nodes for the non-happy paths
uip flow node add <file> --type uipath.end --label "Cancelled" --id cancelEnd1
uip flow node add <file> --type uipath.end --label "Timeout" --id timeoutEnd1

# Then wire all three handles
uip flow edge add <file> --source <NodeId>:completed --target <next-node-id>:input
uip flow edge add <file> --source <NodeId>:cancelled --target cancelEnd1:input
uip flow edge add <file> --source <NodeId>:timeout   --target timeoutEnd1:input
```

**Complete example — invoice approval:**

```bash
uip flow init InvoiceApproval

uip flow hitl add InvoiceApproval/flow_files/InvoiceApproval.flow \
  --schema '{"inputs":[{"name":"invoiceId","type":"string"},{"name":"amount","type":"number"}],"outcomes":[{"name":"Approve","type":"string"},{"name":"Reject","type":"string"}]}' \
  --label "Invoice Review" \
  --priority normal

# Returns: { "NodeId": "invoiceReview1", ... }

uip flow edge add InvoiceApproval/flow_files/InvoiceApproval.flow \
  --source invoiceReview1:completed --target end:input

uip flow validate InvoiceApproval/flow_files/InvoiceApproval.flow --format json
```

See [../uipath-flow/references/flow-hitl.md](../uipath-flow/references/flow-hitl.md) for the complete Flow HITL reference.

---

### Surface: Coded Agent

The Coded Agent escalation CLI (`uip agent escalation add`) is currently in-flight. Until it ships, configure manually:

**`agent.json` escalation entry:**
```json
{
  "escalations": [
    {
      "name": "<escalation-name>",
      "inputSchema":  { "inputs": [...], "inOuts": [...] },
      "outputSchema": { "outputs": [...], "outcomes": [...] }
    }
  ]
}
```

**Agent source (Python):**
```python
from uipath.sdk import interrupt, CreateTask

response = interrupt(CreateTask(
    escalation_name="<escalation-name>",
    data={ "fieldName": value }
))
# response contains the human's outputs and chosen outcome
```

---

### Surface: Maestro

The Maestro HITL CLI is not yet available. Guide the user to add the HITL node manually in the Maestro process designer using the schema from Step 4. Note: in Maestro, field names in `outputs`/`inOuts` must exactly match declared process variable names and types.

---

## Step 6 — Report to the User

After completing the wiring:

1. **What was inserted** — node ID, label, insertion point
2. **Schema summary** — what the human will see (`inputs`), fill in (`outputs`/`inOuts`), and click (`outcomes`)
3. **Edges wired** — which handles were connected and to which nodes; any handles left unwired
4. **Runtime variables** — `<NodeId>.result` and `<NodeId>.status` and how to reference them
5. **Validation result** — pass or errors to fix
6. **Next step** — pack and publish when ready via `uipath-development` skill
