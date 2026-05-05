---
name: uipath-human-in-the-loop
description: "UiPath Human-in-the-Loop node for Flow, Maestro, or Coded Agent. Approval gates, escalations, write-back validation, data enrichment — even without user saying 'HITL'. Designs task schema, writes JSON directly."
allowed-tools: Bash, Read, Write, Edit, Glob, Grep
---

# UiPath Human-in-the-Loop Assistant

> **Preview** — skill is under active development; surface and behavior may change.

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
7. **Check existing node IDs before generating a new one.** Read `workflow.nodes[*].id` from the `.flow` file and pick the next available suffix (e.g. `invoiceReview1`, then `invoiceReview2`).
8. **Never report a failed validation as done.** If `uip maestro flow validate` returns errors, diagnose from the JSON output and fix before reporting to the user.
9. **Output fields are accessed by `field.id`, not `field.variable`.** The runtime result object uses field IDs as keys — `$vars.<nodeId>.output.<fieldId>`. The `variable` property creates a separate workflow-global variable (`$vars.{variable}`) but does NOT change the key used in the output object.

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
| `caseplan.json` (any `*.json` with `root.type: "case-management:root"`) | **Case** | Write `action` task into stage — see [hitl-casetask-action.md](references/hitl-casetask-action.md) |
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

**The options differ by surface.** Present the options for the detected surface and confirm before doing anything.

### Surface: Flow

Present three options. Do not choose on behalf of the user or perform any registry search.

| # | Option | `inputs.type` value | Description |
|---|---|---|---|
| 1 | **QuickForm** | `"quick"` | Inline typed form — fields rendered by Action Center from the schema you design here |
| 2 | **New Coded Action App** | `"custom"` | Scaffold a new React + TypeScript app inside the solution — full UI control |
| 3 | **Existing Deployed App** | `"custom"` | Reference an app already deployed to Orchestrator |

> **If the user is unsure or says "just pick one":** Default to QuickForm. Say: "I'll use QuickForm — it's the quickest to set up and works for most approval and review tasks. You can always upgrade to a Coded Action App later."

| User selects | Next step |
|---|---|
| QuickForm | Read [references/hitl-node-quickform.md](references/hitl-node-quickform.md) for Steps 1–2, then continue with Step 4 |
| New Coded Action App | Read [references/hitl-node-coded-action-app.md](references/hitl-node-coded-action-app.md) for Step 4c details, then continue with Step 4 |
| Existing Deployed App → ask: "What is the name of the deployed action app?" | Read [references/hitl-node-apptask.md](references/hitl-node-apptask.md) for Step 4b details, then continue with Step 4 |

**Fallback rules — what to do when the chosen path hits a blocker:**

| Path | Blocker | Response |
|---|---|---|
| Existing Deployed App | App not found in Orchestrator | "I couldn't find an app with that name. Would you like to try a different name, or fall back to QuickForm while you prepare the app?" |
| New Coded Action App | No `dist/` build present in the source path | "The source folder doesn't have a `dist/` build yet. Run your build first (`npm run build` or equivalent), then come back. Or I can set up a QuickForm now so the flow is wired and ready — you can swap in the app later." |
| New Coded Action App | User can't provide a source path | "If you don't have the app code ready yet, I'll use QuickForm to wire the HITL checkpoint. You can replace it with a Coded Action App once it's built." |
| Any custom app | Auth expired (401 on API call) | "The session looks expired — run `uip login` to refresh your credentials, then retry." |

---

### Surface: Case

Present three options. Do not choose on behalf of the user or pull the registry.

| # | Option | `data.formType` | Description |
|---|---|---|---|
| 1 | **QuickForm (inline schema)** | `"quick"` | Inline typed form — fields and outcomes designed here, rendered by Action Center at runtime. No deployed app needed. |
| 2 | **Generic action task** | *(omit)* | Simple approval — no deployed app, no structured form. Human sees `taskTitle` in Action Center and completes the task. |
| 3 | **App-based action task** | *(omit)* | Uses a deployed Action Center app with custom input/output fields. Requires the app to exist in Orchestrator. |

> **If the user is unsure or says "just pick one":** Default to QuickForm. Say: "I'll use QuickForm — it's the quickest to set up, supports structured form fields, and doesn't need a deployed app. You can upgrade to an app-based task later if you need a custom UI layout."

> **Build vs design time.** QuickForm in case management must round-trip both ways: the JSON written here is what Studio Web's case designer reads (design time), and what `uip maestro case validate` + Action Center render at runtime (build time). Always validate after writing.

| User selects | Next step |
|---|---|
| QuickForm (inline schema) | Read [references/hitl-casetask-action.md — Path 1](references/hitl-casetask-action.md#path-1--quickform-inline-schema-no-deployed-app), then continue with Step 4 |
| Generic action task | Read [references/hitl-casetask-action.md — Path 2](references/hitl-casetask-action.md#path-2--generic-action-task-no-deployed-app-no-form-fields), then continue with Step 4 |
| App-based action task → ask: "What is the name of the deployed Action Center app?" | Read [references/hitl-casetask-action.md — Path 3](references/hitl-casetask-action.md#path-3--app-based-action-task-deployed-action-center-app), then continue with Step 4 |

**Fallback rules:**

| Path | Blocker | Response |
|---|---|---|
| App-based | App not found in registry or `action-apps-index.json` | "I couldn't find that app. Would you like to try a different name, or fall back to QuickForm while the app is prepared?" |
| QuickForm | Schema design rejected on validate (e.g. duplicate field IDs, missing primary outcome) | Surface the validator's error, fix the schema, re-show to user, validate again. Apply Step 4b checks. |
| Any | Auth expired (401 on API call) | "The session looks expired — run `uip login` to refresh your credentials, then retry." |

---

## Step 4 — Common configuration

| Timeout | "How long before the task times out if nobody acts? (default: 24 hours)" |
| Priority | "What priority should this task have? Options: Low, Medium, High (default: Low)" |

---

## Step 4b — Schema Design Resilience (QuickForm — Flow and Case)

Apply these checks while designing the schema before confirming with the user. Applies equally to Flow QuickForm nodes and Case QuickForm action tasks — same `fields[]` + `outcomes[]` shape, same `direction` semantics.

### Data type warnings

Flag these patterns and confirm before proceeding:

| Field description contains | Suggest type | Warning to show |
|---|---|---|
| "amount", "price", "cost", "total", "quantity", "count", "score", "percentage" | `number` | "I'm using `number` for `<field>` — confirm that's correct, or tell me if it should be text." |
| "date", "deadline", "due", "scheduled" | `date` | "I'm using `date` for `<field>` — confirm, or use `text` if the format varies." |
| "approved", "enabled", "active", "is ", "flag" | `boolean` | "I'm using `boolean` (true/false) for `<field>` — confirm, or use `text` if you need more than two states." |

### Vague or incomplete schema descriptions

If the user says something like "just add some fields" or "use whatever makes sense":

1. Infer sensible defaults from the upstream data and downstream needs visible in the `.flow` file (Flow) or in `caseplan.json` upstream task `outputs[]` and `root.data.uipath.variables` (Case).
2. Show the proposed schema explicitly before writing: "Here's what I'm proposing — let me know if you want to change anything."
3. If there is nothing upstream to bind to (Flow with only a trigger; Case with this as the first task), use output-direction fields only and note: "There are no upstream values to pull data from, so the reviewer will fill in all fields from scratch."

### Partial confirmation

If the user says "yes but change X" or gives conditional approval, apply the change and re-show the full updated schema for final confirmation before writing. Never write with an unresolved change.

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

### Surface: Case

Read the `caseplan.json` to identify the target stage. Write an `action` task directly into `stage.data.tasks[lane][]`. **Direct JSON write is the only supported method** — the `uipath-maestro-case` skill ships no `hitl` CLI subcommand (unlike Flow's `uip maestro flow hitl add`).

Full reference: **[references/hitl-casetask-action.md](references/hitl-casetask-action.md)** — three task JSON shapes (QuickForm, generic, app-based), field reference, assignee handling, post-write verification, and downstream output access.

| Path chosen in Step 3 | What gets written |
|---|---|
| QuickForm | Action task with `data.formType: "quick"` and inline `data.schema.{fields,outcomes}`. No `root.data.uipath.bindings[]` entries. Apply Step 4b schema-design checks before writing. |
| Generic | Action task with `data.taskTitle` only — no `formType`, no `schema`, no app references. |
| App-based | Action task with `data.actionCatalogName`, `data.name` and `data.folderPath` as `=bindings.<id>` references. Add 2 root-level bindings. |

After writing, validate (build-time check — must pass before reporting success):

```bash
uip maestro case validate <caseplan.json> --output json
```

> `uip maestro case validate` is the only `uip maestro case` CLI used by this skill on the Case surface. All authoring is direct JSON.

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

- **[QuickForm Node JSON](references/hitl-node-quickform.md)** — Full node JSON, definition entry, edge format, `variables.nodes` regeneration, four schema conversion examples.
- **[AppTask Node JSON](references/hitl-node-apptask.md)** — App lookup via direct API, node JSON with `inputs.type = "custom"`, app field mapping.
- **[Coded Action App (inline)](references/hitl-node-coded-action-app.md)** — Scaffold a new React coded action app inside the solution; full project template, resource files, HITL node JSON.
- **[HITL Business Pattern Recognition](references/hitl-patterns.md)** — Signal tables for detecting when a process needs a human checkpoint. Includes proactive recommendation language and when NOT to recommend HITL.
- **[Action Center URL patterns](../uipath-tasks/references/action-center-urls.md)** (in `uipath-tasks` skill) — Canonical task deep-link forms. Read before surfacing any task URL to the user; covers the missing-tenant-slug anti-pattern (which the portal-UI misclassifies as "Orchestrator not enabled") and the API-host vs UI-host mapping.
- **[Case Action Task (HITL)](references/hitl-casetask-action.md)** — Case surface: action task JSON for QuickForm (inline schema), generic, and app-based flavors; field reference; build-time vs design-time round-trip; downstream output access.
