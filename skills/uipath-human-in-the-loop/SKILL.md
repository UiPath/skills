---
name: uipath-human-in-the-loop
description: "[PREVIEW] Add Human-in-the-Loop node to a Flow, Maestro, or Coded Agent. Triggers on approval gates, escalations, write-back validation, data enrichment — even without user saying 'HITL'. Designs schema, writes JSON directly."
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

## Critical Rules

1. **Confirm schema with the user before writing anything.** Show the designed schema (Step 4) and wait for explicit confirmation.
2. **Always wire at least the `completed` handle.** A HITL node with no outgoing edge on `completed` blocks the flow. Wire `cancelled` and `timeout` to end nodes or handlers unless the user explicitly defers them.
3. **Regenerate `variables.nodes` after adding the node.** Replace the entire `workflow.variables.nodes` array — do not append. See the reference docs for the algorithm.
4. **Validate after every change.** Run `uip flow validate <file> --output json` after writing the node and edges.
5. **Read the existing `.flow` file before adding.** Understand which nodes already exist and where the HITL checkpoint belongs in the flow.
6. **The definition entry is added once.** Check `workflow.definitions` — if `uipath.human-in-the-loop` is already there, do not add it again.

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

| Found | Surface | How HITL is added |
|---|---|---|
| `.flow` file | **Flow** | Write node JSON directly — see reference docs |
| `agent.json` | **Coded Agent** | Escalation CLI in-flight — guide manually for now |
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

Read the existing `.flow` file to understand current nodes and edges. Use the Read tool on the `.flow` file path, then identify:
1. **Where** the human decision point belongs (after which existing node)
2. **What the human needs to see** — data produced by upstream nodes
3. **What the human must provide back** — data needed by downstream nodes
4. **What actions they can take** — the named outcome buttons
5. **Form type**: QuickForm (inline schema) or AppTask (deployed coded app)?

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
| Form type | "Should this use a quick inline form, or a deployed Action Center app?" |

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

## Step 5 — Write the Node Directly

### Surface: Flow — QuickForm (inline schema)

Write the node JSON directly into `workflow.nodes`, add the definition to `workflow.definitions` (once), wire edges into `workflow.edges`, and regenerate `workflow.variables.nodes`.

Full reference: **[references/hitl-node-quickform.md](references/hitl-node-quickform.md)** — complete node JSON, definition entry, edge format, `variables.nodes` regeneration algorithm, and four worked schema conversion examples.

After writing, validate:

```bash
uip flow validate <file> --output json
```

### Surface: Flow — AppTask (deployed coded app)

First resolve the app by name via a direct API call (no CLI), then write the node JSON with `inputs.type = "custom"`.

Full reference: **[references/hitl-node-apptask.md](references/hitl-node-apptask.md)** — credential reading, app lookup curl command, complete node JSON, `inputs.app` field mapping.

After writing, validate:

```bash
uip flow validate <file> --output json
```

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

### Surface: Maestro

The Maestro HITL CLI is not yet available. Guide the user to add the HITL node manually in the Maestro process designer using the schema from Step 4. In Maestro, field names in `outputs`/`inOuts` must exactly match declared process variable names and types.

---

## Step 6 — Report to the User

After completing the wiring:

1. **What was inserted** — node ID, label, insertion point
2. **Schema summary** — what the human will see (`inputs`), fill in (`outputs`/`inOuts`), and click (`outcomes`)
3. **Edges wired** — which handles were connected and to which nodes; any handles left unwired
4. **Runtime variables** — `<NodeId>.result` and `<NodeId>.status` and how to reference them
5. **Validation result** — pass or errors to fix
6. **Next step** — pack and publish when ready via `uipath-development` skill

---

## References

- **[QuickForm Node JSON](references/hitl-node-quickform.md)** — Full node JSON, definition entry, edge format, `variables.nodes` regeneration, four schema conversion examples.
- **[AppTask Node JSON](references/hitl-node-apptask.md)** — App lookup via direct API, node JSON with `inputs.type = "custom"`, app field mapping.
- **[HITL Business Pattern Recognition](references/hitl-patterns.md)** — Signal tables for detecting when a process needs a human checkpoint. Includes proactive recommendation language and when NOT to recommend HITL.
