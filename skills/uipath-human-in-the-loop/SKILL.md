---
name: uipath-human-in-the-loop
description: "UiPath Human-in-the-Loop / HITL node authoring — building approval gates, escalations, write-back validation, and data enrichment checkpoints in Flow, Maestro, or Coded Agents. NOT for managing, reassigning, or monitoring tasks at runtime (use uipath-tasks for that)."
allowed-tools: Bash, Read, Write, Edit, Glob, Grep
---

# UiPath Human-in-the-Loop Assistant

Recognizes when a business process needs a human decision point, designs the task schema through conversation, and wires the HITL node into the automation — Flow, Maestro, or Agent.

> **Coded agents:** for wiring HITL inside a coded agent, use the `uipath-agents` skill — see `skills/uipath-agents/references/coded/capabilities/human-in-the-loop.md`.

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

**Do not use this skill for:** managing, reassigning, escalating, or monitoring existing Action Center tasks at runtime — use the `uipath-tasks` skill for those operations. When answering a runtime task management question, provide only administration guidance. Do NOT suggest adding a HITL node, flow, or automation as a follow-up tip or recommendation — even if delays or escalations are mentioned.

See [references/hitl-patterns.md](references/hitl-patterns.md) for the full business pattern recognition guide.

---

## Critical Rules

1. **Confirm schema with the user before writing anything for quickform type.** Show the designed schema and wait for explicit confirmation.
2. **Always wire the `completed` handle.** A HITL node with no outgoing edge on `completed` blocks the flow forever. Only `completed` is available as an output handle — **not** `output`, `success`, or any other name. This is true even when inserting into an existing flow whose other nodes use `"sourcePort": "output"`.
3. **Always add the definition entry when inserting into an existing flow.** Before writing the node, check `workflow.definitions[]` for `"nodeType": "uipath.human-in-the-loop"`. If absent, append the full definition entry (with `handleConfiguration` including the `completed` handle). Skipping the definition means the `completed` handle is invisible to the runtime and the wiring check fails.
4. **Regenerate `variables.nodes` after adding the node.** Replace the entire `workflow.variables.nodes` array — do not append. See the reference docs for the algorithm.
5. **Validate after every change.** Run `uip maestro flow validate <file> --output json` after writing the node and edges. The `uip` CLI does not accept `--format`; using it produces `error: unknown option '--format'` and exit code 3.
6. **Read the existing `.flow` file before adding.** Understand which nodes already exist and where the HITL checkpoint belongs in the flow.
7. **The definition entry is added once.** Check `workflow.definitions` — if `uipath.human-in-the-loop` is already there, do not add it again.
8. **Check existing node IDs before generating a new one.** Read `workflow.nodes[*].id` from the `.flow` file and pick the next available suffix (e.g. `invoiceReview1`, then `invoiceReview2`).
9. **Never report a failed validation as done.** If `uip maestro flow validate` returns errors, diagnose from the JSON output and fix before reporting to the user.
10. **Output fields are accessed by `field.id`, not `field.variable`.** The runtime result object uses field IDs as keys — `$vars.<nodeId>.output.<fieldId>`. The `variable` property creates a separate workflow-global variable (`$vars.{variable}`) but does NOT change the key used in the output object.
11. **Input field binding paths use the upstream output key, not the HITL field's own `id`.** These are two different things: the HITL field `id` identifies the form field (always lowercase); the binding path key is the name used in the upstream script's `return` statement (preserves camelCase). If a script returns `{ supplierName: "Acme" }`, the correct binding is `vars.fetchSupplier.output.supplierName` — writing `suppliername` (the field `id`) produces a path that does not exist at runtime. The form field will be blank; `flow validate` will not catch it. Always derive the binding key from the upstream script source, not from the HITL schema you are designing.
12. **Downstream scripts must access `$vars.<nodeId>.output`.** Any script node that runs after the HITL node must read `$vars.<nodeId>.output` (the result object) — do not rely solely on `$vars.<nodeId>.status`. Concrete example: `const output = $vars.reviewNode1.output; const reason = output.reason;`. This is required even when the primary routing uses `status`.

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

# Check for agent.json (Low-Code Agent project)
find . -name "agent.json" -maxdepth 4 | head -3

# Check for Maestro .bpmn (Maestro process)
find . -name "*.bpmn" -maxdepth 4 | head -3
```

| Found | Surface | How HITL is added |
|---|---|---|
| `.flow` file | **Flow** | Write node JSON directly — see reference docs |
| `agent.json` | **Low Code Agent** | Escalation CLI in-flight — guide manually for now |
| `.bpmn` (Maestro) | **Maestro** | Not yet — guide user manually |

**If the user mentioned a specific file path**, use that directly.

**If no `.flow` file exists and surface is Flow**, scaffold solution-first — Flow projects MUST live inside a solution:

```bash
# Probe the solution verb once per session before scaffolding:
#   uip solution init --help --output json
# Success → use `solution init` (post-rename, default).
# `unknown command` → CLI predates the rename; substitute `uip solution new <SolutionName>` below.

uip solution init <SolutionName> --output json
cd <SolutionName> && uip maestro flow init <ProjectName>
# Creates: <SolutionName>/<ProjectName>/<ProjectName>.flow
```

The flow file path is `<SolutionName>/<ProjectName>/<ProjectName>.flow` (double-nested). `<SolutionName>/` is the solution directory (contains the `.uipx` file); `<ProjectName>/` inside it is the flow project. By convention `<SolutionName>` and `<ProjectName>` are often the same string, but they are two distinct scaffolding arguments. Running `uip maestro flow init` without first running `uip solution init` produces a broken single-nested `<ProjectName>/<ProjectName>.flow` layout that fails Studio Web upload, packaging, and downstream tooling.

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

> **If the user's request is purely business-oriented** (no mention of a deployed app, coded action app, or custom UI): skip the question and proceed directly with QuickForm. Do not ask. Say: "I'll use QuickForm — it's inline, no deployment step needed, and works for most approval and review tasks."

> **If the user is unsure or says "just pick one":** Default to QuickForm. Say: "I'll use QuickForm — it's the quickest to set up and works for most approval and review tasks. You can always upgrade to a Coded Action App later."

| User selects | Next step |
|---|---|
| QuickForm | Read [How to write a QuickForm HITL node](references/hitl-node-quickform.md) for Steps 1–2, then continue with Step 4 |
| New Coded Action App | Read [How to scaffold a new Coded Action App](references/hitl-node-coded-action-app.md) for Step 4c details, then continue with Step 4 |
| Existing Deployed App → ask: "What is the name of the deployed action app?" | Read [How to wire an existing deployed Action App](references/hitl-node-apptask.md) for Step 4b details, then continue with Step 4 |

**Fallback rules — what to do when the chosen path hits a blocker:**

| Path | Blocker | Response |
|---|---|---|
| Existing Deployed App | App not found in Orchestrator | "I couldn't find an app with that name. Would you like to try a different name, or fall back to QuickForm while you prepare the app?" |
| New Coded Action App | No `dist/` build present in the source path | "The source folder doesn't have a `dist/` build yet. Run your build first (`npm run build` or equivalent), then come back. Or I can set up a QuickForm now so the flow is wired and ready — you can swap in the app later." |
| New Coded Action App | User can't provide a source path | "If you don't have the app code ready yet, I'll use QuickForm to wire the HITL checkpoint. You can replace it with a Coded Action App once it's built." |
| Any custom app | Auth expired (401 on API call) | "The session looks expired — run `uip login` to refresh your credentials, then retry." |

---

## Step 4 — Common configuration

| Timeout | "How long before the task times out if nobody acts? (default: 24 hours)" |
| Priority | "What priority should this task have? Options: Low, Medium, High (default: Low)" |

---

## Step 4b — Schema Design Resilience (QuickForm only)

Apply these checks while designing the schema before confirming with the user.

### Data type warnings

Flag these patterns and confirm before proceeding:

| Field description contains | Suggest type | Warning to show |
|---|---|---|
| "amount", "price", "cost", "total", "quantity", "count", "score", "percentage" | `number` | "I'm using `number` for `<field>` — confirm that's correct, or tell me if it should be text." |
| "date", "deadline", "due", "scheduled" | `date` | "I'm using `date` for `<field>` — confirm, or use `text` if the format varies." |
| "approved", "enabled", "active", "is ", "flag" | `boolean` | "I'm using `boolean` (true/false) for `<field>` — confirm, or use `text` if you need more than two states." |

### Vague or incomplete schema descriptions

If the user says something like "just add some fields" or "use whatever makes sense":

1. Infer sensible defaults from the upstream data and downstream needs visible in the `.flow` file.
2. Show the proposed schema explicitly before writing: "Here's what I'm proposing — let me know if you want to change anything."
3. If there are no upstream nodes to bind to (flow is just a trigger), use output-direction fields only and note: "There are no upstream nodes to pull data from, so the reviewer will fill in all fields from scratch."

### Empty field labels block validation

Every field in `inputs.schema.fields` must have a non-empty `label`. `flow validate` emits `HITL_QUICK_FORM_FIELD_LABEL_REQUIRED` (error severity) for each field with an empty or whitespace-only `label` — Debug and Publish are blocked until all labels are filled in. Never generate a field with `"label": ""` or omit the `label` key.

### Partial confirmation

If the user says "yes but change X" or gives conditional approval, apply the change and re-show the full updated schema for final confirmation before writing. Never write with an unresolved change.

---

## Step 5 — Write the Node Directly

### Surface: Flow — QuickForm (inline schema only)

Write the node JSON directly into `workflow.nodes`, add the definition to `workflow.definitions` (once), wire edges into `workflow.edges`, and regenerate `workflow.variables.nodes`. **Direct JSON is the default.**

Node JSON, definition entry, edge format, `variables.nodes` algorithm, and four worked examples: **[How to write a QuickForm HITL node](references/hitl-node-quickform.md)**

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

Full project template, UUID generation, solution CLI commands, resource file templates, node JSON, and post-creation build steps: **[How to scaffold a new Coded Action App](references/hitl-node-coded-action-app.md)**

After writing, validate:

```bash
uip maestro flow validate <file> --output json
```

### Surface: Flow — AppTask (deployed action app only)

Step 4b must be completed first — app resolved, configuration retrieved. Then:

Resolve the solution context (`.uipx` file), write solution resource files, register the app reference, merge `debug_overwrites.json`, then write the node JSON with `inputs.type = "custom"` and `inputs.app` populated from the Step 3b configuration.

App search/selection, retrieve-configuration, resource file writing, complete node JSON with `appInputBindings`: **[How to wire an existing deployed Action App](references/hitl-node-apptask.md)**

After writing, validate:

```bash
uip maestro flow validate <file> --output json
```

### Surface: Low-Code Agent

The Low-Code Agent escalation CLI (`uip agent escalation add`) is currently in-flight. Until it ships, configure manually:

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
4. **Runtime variables** — `$vars.<nodeId>.output` (object) and `$vars.<nodeId>.status` (string) and how to reference them downstream
5. **Validation result** — pass or errors to fix
6. **Production readiness note:**
   - **QuickForm**: ready to deploy once the solution is packaged. No additional build steps.
   - **New Coded Action App**: the app must be built (`npm run build` inside the app source) and the solution packaged before the HITL task can be used in production. The app will appear with `appSystemName: null` until first deployment assigns it a system name.
   - **Existing Deployed App**: ready to deploy immediately — the app is already live.
7. **Next step** — pack and publish when ready via `uipath-development` skill

---

## References

- **[How to write a QuickForm HITL node](references/hitl-node-quickform.md)** — Read this after the user confirms QuickForm in Step 3. Covers the complete node JSON, definition entry, edge wiring, `variables.nodes` regeneration algorithm, and four worked schema examples.
- **[How to wire an existing deployed Action App](references/hitl-node-apptask.md)** — Read this when the user selects an existing deployed app in Step 3. Covers app lookup via the Orchestrator API, `inputs.app` field mapping, `appInputBindings`, and solution resource files.
- **[How to scaffold a new Coded Action App](references/hitl-node-coded-action-app.md)** — Read this when the user wants to build a new React app inside the solution. Covers full project template, UUID generation, solution CLI commands, and post-creation build steps.
- **[HITL business pattern recognition](references/hitl-patterns.md)** — Read this during Step 2 / Step 2b to identify whether a process needs a human checkpoint and which pattern applies. Includes proactive recommendation language and when NOT to recommend HITL.
- **[Action Center URL patterns](../uipath-tasks/references/action-center-urls.md)** (in `uipath-tasks` skill) — Read this before surfacing any Action Center task URL to the user. Covers the missing-tenant-slug anti-pattern and the API-host vs UI-host mapping.
