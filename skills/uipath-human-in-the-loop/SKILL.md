---
name: uipath-human-in-the-loop
description: "[PREVIEW] Add Human-in-the-Loop node to a Flow, Maestro, or Coded Agent. Triggers on approval gates, escalations, write-back validation, data enrichment — even without user saying 'HITL'. Designs schema, writes JSON directly."
allowed-tools: Bash, Read, Write, Edit, Glob, Grep
---

# UiPath Human-in-the-Loop Assistant

Recognizes when a business process needs a human decision point, designs the task schema through conversation, and wires the HITL node into the automation — Flow, Maestro, or Coded Agent.

## When to Use This Skill

- User describes **approval gates** — invoice approval, offer letter review, compliance sign-off, PO authorization
- User describes **exception escalation** — "if confidence is low, escalate to a human", fraud alert review
- User describes **write-back validation** — "human approves before agent writes to ServiceNow / SAP / CRM"
- User describes **data enrichment** — human fills in missing fields the automation cannot resolve
- User describes **agentic output review** — "review AI-generated email/RCA/summary before it goes out"
- User describes **IT change or access approval** — CAB gate, runbook sign-off, access provisioning review
- User describes **HR or contract workflow** — offer letter review, contract approval, termination sign-off
- User describes **financial transaction approval** — payment release, price override, expense over limit
- User describes **customer communication approval** — agent-drafted reply that needs human sign-off before sending
- User explicitly asks to **add a HITL node**, human review step, or Action Center task
- User is building any automation where **a human must act before the process can continue**

See [references/hitl-patterns.md](references/hitl-patterns.md) for the full business pattern recognition guide.

---

## Critical Rules

1. **Confirm schema with the user before writing anything for quickform type.** Show the designed schema and wait for explicit confirmation.
2. **Always wire the `completed` handle.** A HITL node with no outgoing edge on `completed` blocks the flow forever. Only `completed` is available as an output handle.
3. **Regenerate `variables.nodes` after adding the node.** Replace the entire `workflow.variables.nodes` array — do not append. See the reference docs for the algorithm.
4. **Validate after every change.** Run `uip maestro flow validate <file> --output json` after writing the node and edges. The `uip` CLI does not accept `--format`; using it produces `error: unknown option '--format'` and exit code 3.
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

**If no `.flow` file exists and surface is Flow**, scaffold solution-first — Flow projects MUST live inside a solution:

```bash
uip solution new <SolutionName> --output json
cd <SolutionName> && uip maestro flow init <ProjectName>
# Creates: <SolutionName>/<ProjectName>/<ProjectName>.flow
```

The flow file path is `<SolutionName>/<ProjectName>/<ProjectName>.flow` (double-nested). `<SolutionName>/` is the solution directory (contains the `.uipx` file); `<ProjectName>/` inside it is the flow project. By convention `<SolutionName>` and `<ProjectName>` are often the same string, but they are two distinct scaffolding arguments. Running `uip maestro flow init` without first running `uip solution new` produces a broken single-nested `<ProjectName>/<ProjectName>.flow` layout that fails Studio Web upload, packaging, and downstream tooling.

---

## Step 2 — Read the Business Context

Read the existing `.flow` file to understand current nodes and edges. Use the Read tool on the `.flow` file path, then identify:
1. **Where** the human decision point belongs (after which existing node)
2. **What the human needs to see** — data produced by upstream nodes
3. **What the human must provide back** — data needed by downstream nodes
4. **What actions they can take** — the named outcome buttons
5. **Form type**: QuickForm (`inputs.type = "quick"`, inline schema) or AppTask (`inputs.type = "custom"`, deployed coded app)?

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

## Step 3 — Choose Task Type

Present the user with three options. Do not choose on their behalf or perform any registry search.

| # | Option | `inputs.type` value | Description |
|---|---|---|---|
| 1 | **QuickForm** | `"quick"` | Inline typed form — fields rendered by Action Center from the schema you design here |
| 2 | **New Coded Action App** | `"custom"` | Scaffold a new React + TypeScript app inside the solution — full UI control |
| 3 | **Existing Deployed App** | `"custom"` | Reference an app already deployed to Orchestrator |

| User selects | Next step |
|---|---|
| QuickForm | Read [references/hitl-node-quickform.md](references/hitl-node-quickform.md) for Steps 1–2, then continue with Step 4 |
| New Coded Action App | Read [references/hitl-node-coded-action-app.md](references/hitl-node-coded-action-app.md) for Step 4c details, then continue with Step 4 |
| Existing Deployed App → ask: "What is the name of the deployed action app?" | Read [references/hitl-node-apptask.md](references/hitl-node-apptask.md) for Step 4b details, then continue with Step 4 |

---

## Step 4 — Common configuration

| Timeout | "How long before the task times out if nobody acts? (default: 24 hours)" |
| Priority | "What priority should this task have? Options: Low, Medium, High (default: Low)" |

---

## Step 5 — Write the Node Directly

### Surface: Flow — QuickForm (inline schema only)

Write the node JSON directly into `workflow.nodes`, add the definition to `workflow.definitions` (once), wire edges into `workflow.edges`, and regenerate `workflow.variables.nodes`. **Direct JSON is the default.**

Full reference: **[references/hitl-node-quickform.md](references/hitl-node-quickform.md)** — complete node JSON, definition entry, edge format, `variables.nodes` regeneration algorithm, and four worked schema conversion examples.

**CLI (opt-in):** When the user explicitly requests a CLI command:

```bash
uip maestro flow hitl add <path/to/file.flow> \
  --label "<TaskLabel>" \
  --priority <Low|Medium|High> \
  --assignee <email-or-group> \
  --schema '<json>' \
  --output json
```

The CLI writes the node, adds the definition entry, and updates `variables.nodes` automatically. Wire the `completed` port after it returns.

After writing, validate:

```bash
uip maestro flow validate <file> --output json
```

### Surface: Flow — Coded Action App (new inline)

Step 4c must be completed first — app name confirmed, solution directory located, SDK tarball identified, schema designed and confirmed.

Scaffold the project directory and all source files, add the project to the solution, write the solution resource files, then write the HITL node with `inputs.type = "custom"` and `inputs.app` referencing the new app (`appSystemName: null` since the app has not been deployed yet).

Full reference: **[references/hitl-node-coded-action-app.md](references/hitl-node-coded-action-app.md)** — complete project structure, all file templates, UUID generation, solution CLI commands, resource file templates (`resources/solution_folder/app/codedAction/` and `resources/solution_folder/package/`), node JSON with `inputs.app` field mapping, and post-creation build instructions.

After writing, validate:

```bash
uip maestro flow validate <file> --output json
```

### Surface: Flow — AppTask (deployed action app only)

Step 4b must be completed first — app resolved, configuration retrieved. Then:

Resolve the solution context (`.uipx` file), write solution resource files, register the app reference, merge `debug_overwrites.json`, then write the node JSON with `inputs.type = "custom"` and `inputs.app` populated from the Step 3b configuration.

Full reference: **[references/hitl-node-apptask.md](references/hitl-node-apptask.md)** — credential sourcing from `~/.uipath/.auth`, solution context resolution, app search/selection (with multi-match list), retrieve-configuration, resource file writing, reference registration, debug overwrites, complete node JSON, `inputs.app` field mapping.

After writing, validate:

```bash
uip maestro flow validate <file> --output json
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

The Maestro HITL CLI is not yet available. Guide the user to add the HITL node manually in the Maestro process designer using the schema from Step 5. In Maestro, field names in `outputs`/`inOuts` must exactly match declared process variable names and types.

---

## Step 6 — Report to the User

After completing the wiring:

1. **What was inserted** — node ID, label, insertion point
2. **Schema summary** — what the human will see (input-direction fields), fill in (output/inOut-direction fields), and click (outcomes). For deployed action app show the actionSchema from the retrieve-configuration api response here.
3. **Edges wired** — which handles were connected and to which nodes; any handles left unwired
4. **Runtime variables** — `$vars.<nodeId>.result` (object) and `$vars.<nodeId>.status` (string) and how to reference them downstream
5. **Validation result** — pass or errors to fix
6. **Next step** — pack and publish when ready via `uipath-development` skill

---

## References

- **[QuickForm Node JSON](references/hitl-node-quickform.md)** — Full node JSON, definition entry, edge format, `variables.nodes` regeneration, four schema conversion examples.
- **[AppTask Node JSON](references/hitl-node-apptask.md)** — App lookup via direct API, node JSON with `inputs.type = "custom"`, app field mapping.
- **[Coded Action App (inline)](references/hitl-node-coded-action-app.md)** — Scaffold a new React coded action app inside the solution; full project template, resource files, HITL node JSON.
- **[HITL Business Pattern Recognition](references/hitl-patterns.md)** — Signal tables for detecting when a process needs a human checkpoint. Includes proactive recommendation language and when NOT to recommend HITL.
