---
name: uipath-human-in-the-loop
description: "UiPath Human-in-the-Loop / HITL node authoring — building approval gates, escalations, write-back validation, and data enrichment checkpoints in Flow, Maestro, Case Management, or Coded Agents, plus a guided decision experience that captures reviewer corrections as decisions. NOT for managing, reassigning, or monitoring tasks at runtime (use uipath-tasks for that)."
allowed-tools: Bash, Read, Write, Edit, Glob, Grep
---

# UiPath Human-in-the-Loop Assistant

Recognizes when a business process needs a human decision point, designs the task schema through conversation, and wires the HITL node into the automation — Flow, Maestro, Case Management, or Agent.

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
- User asks to **capture or record a decision** (or to feed the Decision Ledger), or a reviewer **confirms or corrects a proposal**: use the guided decision experience below

**Guided decision experience (opt-in).** Only when the request asks to capture a decision or describes a reviewer confirming or correcting a proposal, read [references/decision-capture-action-app-guide.md](references/decision-capture-action-app-guide.md) before designing the Coded Action App schema, QuickForm or document-validation task. Any other request skips it and is built on the normal path. The guide sets a toggle from the request: on when the user asks to capture a decision, or when a reviewer confirms or corrects something an agent or automation proposed. On adds a fixed set of decision fields beside the author's own and switches the UI to one light layout per surface (reasons with a weight menu, nothing pre-selected, final details that follow the decision, a rationale composed from the reasons, Next time with a scope, and a collapsed record), without renaming the author's fields. QuickForm gets an optional Why on every select field through one function. Never ask a yes/no question about it; state it in one line when you turned it on unasked.

**Do not use this skill for:** managing, reassigning, escalating, or monitoring existing Action Center tasks at runtime — use the `uipath-tasks` skill for those operations. When answering a runtime task management question, provide only administration guidance. Do NOT suggest adding a HITL node, flow, or automation as a follow-up tip or recommendation — even if delays or escalations are mentioned.

See [references/hitl-patterns.md](references/hitl-patterns.md) for the full business pattern recognition guide.

---

## Critical Rules

1. **Never block on schema confirmation.** Design the schema from the prompt and any upstream `.flow`/`caseplan.case` data, write the node, and record the chosen schema prominently in the final report so the user can adjust it afterward. Asking the user is never a precondition for proceeding — if the user is present and offers input, use it, but do not wait for it. Only stop and report the open decision when the request is genuinely too ambiguous to make any reasonable inference. (A prompt that already specifies the fields, outcomes, and output shape is never too ambiguous.)
2. **Wire every QuickForm outcome's own port.** A QuickForm node has one output handle per outcome, named `outcome-<outcome.id>` — never a single `completed` handle. `outcome-completed` is a placeholder that exists only on a schema with zero outcomes; it disappears the instant `inputs.schema.outcomes` has any entry, including the shipped default `Submit`. A HITL node with any outcome port left unwired blocks the flow forever on that branch. App-based (`coded-action-app`) nodes are different: their port stays a static `completed` regardless of the app's own outcomes — do not add an `inputs.schema` block to an app-based node, which would wrongly flip it onto an outcome-derived port. Neither node type ever uses `output`, `success`, or any other name.
3. **Always add the definition entry when inserting into an existing flow.** Before writing the node, check `workflow.definitions[]` for the correct `nodeType` for the selected path (`"uipath.human-in-the-loop.quick-form"` for QuickForm, `"uipath.human-in-the-loop.coded-action-app"` for app-based). If absent, append the full definition entry with its `handleConfiguration` block. Skipping the definition means the node's handles are invisible to the runtime and the wiring check fails.
4. **Regenerate `variables.nodes` after adding the node.** Replace the entire `workflow.variables.nodes` array — do not append. See the reference docs for the algorithm.
5. **Validate after every change.** Run `uip maestro flow validate <file> --output json` after writing the node and edges. The `uip` CLI does not accept `--format`; using it produces `error: unknown option '--format'` and exit code 3.
6. **Read the existing `.flow` file before adding.** Understand which nodes already exist and where the HITL checkpoint belongs in the flow.
7. **The definition entry is added once per node type.** Check `workflow.definitions` — if an entry with the matching `nodeType` is already there, do not add it again.
8. **Check existing node IDs before generating a new one.** Read `workflow.nodes[*].id` from the `.flow` file and pick the next available suffix (e.g. `invoiceReview1`, then `invoiceReview2`).
9. **Never report a failed validation as done.** If `uip maestro flow validate` returns errors, diagnose from the JSON output and fix before reporting to the user.
10. **Output fields are accessed by `field.id`, not `field.variable`.** The runtime result object uses field IDs as keys — `$vars.<nodeId>.output.<fieldId>`. The `variable` property only creates a workflow-global alias; it does NOT change the key used in the node output object, and it is NOT how downstream scripts read the value.
    - WRONG: `$vars.legalApproval` — this is the global alias path, not the script access path
    - WRONG: `$vars.<nodeId>.output.legalApproval` — this uses the variable name as the key
    - RIGHT: `$vars.<nodeId>.output.approved` — uses `field.id` ("approved") as the key
    In every downstream script, use `$vars.<nodeId>.output.<fieldId>` where `<fieldId>` is the `id` you gave the field in the schema — never the `variable` name.
11. **Input field binding paths use the upstream output key, not the HITL field's own `id`.** These are two different things: the HITL field `id` identifies the form field (always lowercase); the binding path key is the name used in the upstream script's `return` statement (preserves camelCase). If a script returns `{ supplierName: "Acme" }`, the correct binding is `vars.fetchSupplier.output.supplierName` — writing `suppliername` (the field `id`) produces a path that does not exist at runtime. The form field will be blank; `flow validate` will not catch it. Always derive the binding key from the upstream script source, not from the HITL schema you are designing.
12. **Downstream scripts must access `$vars.<nodeId>.output`.** Any script node that runs after the HITL node must read `$vars.<nodeId>.output` (the result object) — do not rely solely on `$vars.<nodeId>.status`. Concrete example: `const output = $vars.reviewNode1.output; const reason = output.reason;`. This is required even when the primary routing uses `status`.
13. **When the request asks to capture a decision, or a reviewer confirms or corrects a proposal, read the guided decision guide before writing the Coded Action App `action-schema.json`, QuickForm schema or document-validation schema.** Open [references/decision-capture-action-app-guide.md](references/decision-capture-action-app-guide.md) first; it sets the decision toggle from the request and, when on, lists the fields to add (`proposedOutcome`, `proposedBy`, `involvement`, `nextTimeOptions`, `conditionOptions`, `reasons` with `weight`, `fields` with `byDecision`, and the outputs `rationaleText`, `decidingReasons`, `nextTimeScope`, `changes`, `record`). Writing the schema without it drops those fields. The guide also lists the Human Context Capture principles the app must satisfy and the `@uipath/intrinsic-signals` markup and `intrinsicSignals` output a Coded Action App must include. For any other request, do not open it: build the ordinary schema and app with no decision fields.
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

# Check for a Case Management project — detect by content marker, not by filename.
# Project files are flat in the project dir (no content/ dir on disk). The generated
# sibling caseplan.case.bpmn carries the same marker; these patterns skip it. Edit caseplan.case.
find . -maxdepth 4 \( -iname "*.json" -o -iname "*.case" \) -print0 2>/dev/null | xargs -0 grep -l '"case-management:root"' 2>/dev/null | head -3

# Check for agent.json (Low-Code Agent project)
find . -name "agent.json" -maxdepth 4 | head -3

<!--skill-flavor:bpmn-sdk-surface-detect:start-->
# Check for Maestro .bpmn or .bpmn.ts source (Maestro process)
find . -maxdepth 4 \( -name "*.bpmn" -o -name "*.bpmn.ts" \) | head -3
<!--skill-flavor:bpmn-sdk-surface-detect:end-->
```

| Found | Surface | How HITL is added |
|---|---|---|
<!--skill-flavor:flow-sdk-surface-row:start-->
| `.flow.ts` or `.flow` file | **Flow** | Author with `hitl(...)` in `<Name>.flow.ts` through the `uipath-maestro-flow` skill ([hitl.md](../uipath-maestro-flow/references/hitl.md)); never write node JSON into the compiled `.flow` — `compile` overwrites it |
<!--skill-flavor:flow-sdk-surface-row:end-->
<!--skill-flavor:case-sdk-surface-row:start-->
| `<Name>.case.ts`, or `caseplan.case` (any `*.json` or `*.case` whose `nodes[]` carry `data.parentElement.type: "case-management:root"` — the marker is per-node; there is no `root` node on disk) | **Case** | Author an `action(...)` task in `<Name>.case.ts` through the `uipath-maestro-case` skill (Capability router); never write task JSON into the compiled plan — `compile` overwrites it |
<!--skill-flavor:case-sdk-surface-row:end-->
| `agent.json` | **Low Code Agent** | Escalation CLI in-flight — guide manually for now |
<!--skill-flavor:bpmn-sdk-surface-row:start-->
| `<Name>.bpmn.ts` or `.bpmn` (Maestro) | **Maestro** | Author a `.humanTask(...)` in `<Name>.bpmn.ts` through the `uipath-maestro-bpmn` skill (its *Human task outcomes* section in `references/bpmn-runtime.md`); never write task XML into the compiled `.bpmn` — `compile` overwrites it |
<!--skill-flavor:bpmn-sdk-surface-row:end-->

<!--skill-flavor:flow-sdk-hitl-stop:start-->
**Flow surface (a `.flow.ts`, a `.flow`, or a new flow) — the default: stop here.** Hand the HITL request to the `uipath-maestro-flow` skill: it authors `hitl(...)` in `<Name>.flow.ts` — decompiling an existing `.flow` first — and compiles ([hitl.md](../uipath-maestro-flow/references/hitl.md)). Never read or hand-edit the compiled `.flow`; the next `compile` overwrites it. Steps 2–6 below cover the Low-Code Agent surface; Case and Maestro have their own stops below.

<!--skill-flavor:flow-sdk-hitl-stop:end-->
<!--skill-flavor:case-sdk-hitl-stop:start-->
**Case surface (a `<Name>.case.ts`, a `caseplan.case`, a `caseplan.json`, or a new case) — the default: stop here too.** Hand the HITL request to the `uipath-maestro-case` skill: it authors `action(...)` in `<Name>.case.ts` — decompiling an existing plan first — and compiles (see the `uipath-maestro-case` skill, case runtime: human and on-demand work). Never hand-edit the compiled plan; the next `compile` overwrites it. **A Case human task is an Action App task, not a QuickForm, so the QuickForm default below does not apply here.** The SDK cannot write a Case quick form: its `hitlType` context and `inputSchema` are only carried over from a plan saved in the Studio Web Case designer (`@uipath/maestro-builder-sdk` `dist/case/preserve.d.ts`). Name a deployed Action App with `action({ app: { name, folder } })`; if none exists, build and deploy a Coded Action App first (the `uipath-coded-apps` skill), then name it. When the user wants a quick form anyway, they add it in the Studio Web designer, and a later decompile and compile keep it. In this package, Steps 2–6 below cover only the Low-Code Agent surface.

<!--skill-flavor:case-sdk-hitl-stop:end-->
<!--skill-flavor:bpmn-sdk-hitl-stop:start-->
**Maestro surface (a `<Name>.bpmn.ts`, a `.bpmn`, or a new Maestro process) — the default: stop here too.** Hand the HITL request to the `uipath-maestro-bpmn` skill: it authors `.humanTask(...)` in `<Name>.bpmn.ts` — decompiling an existing `.bpmn` first — and compiles (that skill's *Human task outcomes* section in `references/bpmn-runtime.md`). It writes every task as an inline form: the SDK cannot yet bind a deployed Action App, so when the request names one, it says so and points the user to the Studio Web designer. Never hand-edit the compiled `.bpmn`; the next `compile` overwrites it. In this package, the Maestro sections of Steps 2–6 below do not apply.

<!--skill-flavor:bpmn-sdk-hitl-stop:end-->
**If the user mentioned a specific file path**, use that directly.

<!--skill-flavor:flow-project-creation:start-->
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

The flow file path is `<SolutionName>/<ProjectName>/<ProjectName>.flow` (double-nested). `<SolutionName>/` is the solution directory (contains the `.uipx` file); `<ProjectName>/` inside it is the flow project. By convention `<SolutionName>` and `<ProjectName>` are often the same string, but they are two distinct scaffolding arguments. Run `uip maestro flow init` outside a solution and it auto-scaffolds `<ProjectName>Solution/<ProjectName>/` for you; running `uip solution init` first lets you control the solution name (otherwise it defaults to `<ProjectName>Solution`). Passing `--skip-solution-registration` leaves a bare single-nested `<ProjectName>/<ProjectName>.flow` layout that fails Studio Web upload, packaging, and downstream tooling.
<!--skill-flavor:flow-project-creation:end-->

---

## Step 2 — Read the Business Context

Read the existing `.flow` file to understand current nodes and edges. Use the Read tool on the `.flow` file path, then identify:
1. **Where** the human decision point belongs (after which existing node)
2. **What the human needs to see** — data produced by upstream nodes
3. **What the human must provide back** — data needed by downstream nodes
4. **What actions they can take** — the named outcome buttons
5. **Form type**: QuickForm (inline schema, node type `uipath.human-in-the-loop.quick-form`) or AppTask (deployed coded app, node type `uipath.human-in-the-loop.coded-action-app`)?

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

**Never block on this.** When a signal is clear-cut (an explicit approval / review / sign-off requirement), add the HITL step and state that you did so, in this form:

> "I noticed that [quote the specific part of their description]. This is a [pattern name] — a point where [brief consequence if no human reviews]. I'm inserting a Human-in-the-Loop step here so that [human role] can [action] before the automation [continues/writes/sends]."

Proceed straight to schema design after saying this — do not wait for a reply. Record the decision prominently in the final report so the user can remove the step if they disagree. Only skip adding it and report the open decision when the signal is genuinely ambiguous (not just "no explicit HITL mention" — the signals table above is itself the ambiguity test).

**Example:**
> User: "Build an automation that reads support tickets, uses AI to generate an RCA, and updates the ticket in ServiceNow."
>
> Agent: "I noticed that the automation writes AI-generated content directly back to ServiceNow. This is a write-back validation pattern — if the RCA is incorrect and nobody reviews it, wrong data goes into production tickets. I'm inserting a Human-in-the-Loop step so that a support lead can review and optionally edit the RCA before the update is applied."

---

## Step 3 — Choose Task Type

**The options differ by surface.** Never block here — pick the option that best fits the surface and the business description, state the choice, and proceed. Only ask when the user is actually present and available; in a non-interactive run, infer and move on.

### Surface: Flow

Infer the right option from the signals below and state your choice — do not perform a registry search first, and do not wait for the user to pick before proceeding.

| # | Option | Node type | Description |
|---|---|---|---|
| 1 | **QuickForm** | `uipath.human-in-the-loop.quick-form` | Inline typed form — fields rendered by Action Center from the schema you design here |
| 2 | **New Coded Action App** | `uipath.human-in-the-loop.coded-action-app` | Scaffold a new React + TypeScript app inside the solution — full UI control |
| 3 | **Existing Deployed App** | `uipath.human-in-the-loop.coded-action-app` | Reference an app already deployed to Orchestrator |

> **Default: QuickForm.** Pick QuickForm unless the request explicitly names a deployed app, a coded action app, or a custom UI requirement — those are the only signals that point at options 2 or 3. State the choice, do not ask: "I'll use QuickForm — it's inline, no deployment step needed, and works for most approval and review tasks. You can swap in a Coded Action App or an existing deployed app later if you need one."

| Option chosen | Next step |
|---|---|
| Guided decision experience (the request asks to capture a decision, or a reviewer corrects a proposal) | Read [Guided decision experience](references/decision-capture-action-app-guide.md) to add the decision fields and guided layout, then wire it as a New Coded Action App |
| QuickForm | Read [How to write a QuickForm HITL node](references/hitl-node-quickform.md) for Steps 1–2, then continue with Step 4 |
| New Coded Action App | Read [How to scaffold a new Coded Action App](references/hitl-node-coded-action-app.md) for Step 4c details, then continue with Step 4 |
| Existing Deployed App — the request must already name the app | Read [How to wire an existing deployed Action App](references/hitl-node-apptask.md) for Step 4b details, then continue with Step 4 |

**Fallback rules — never block on these, fall back and state what you did:**

| Path | Blocker | Response |
|---|---|---|
| Existing Deployed App | App not found in Orchestrator, or no app name was given | Fall back to QuickForm and proceed. State: "I couldn't find (or wasn't given) a deployed app name, so I used QuickForm instead. Point me at a real app name and I'll swap it in." |
| New Coded Action App | No `dist/` build present in the source path | Fall back to QuickForm and proceed. State: "The source folder doesn't have a `dist/` build yet, so I wired a QuickForm for now — run your build and ask me to swap in the Coded Action App once it's ready." |
| New Coded Action App | No source path given | Fall back to QuickForm and proceed. State: "No app source path was given, so I used QuickForm to wire the checkpoint now. Point me at the app code and I'll replace it with a Coded Action App." |
| Any custom app | Auth expired (401 on API call) | Fall back to QuickForm and proceed. State: "The session looked expired, so I used QuickForm rather than stall on re-authenticating. Run `uip login` and ask me to swap in the app when you're ready." |

---

### Surface: Case

<!--skill-flavor:case-json-task-type:start-->
In this package, Case HITL is authored by the `uipath-maestro-case` skill (the Case stop in Step 1). Skip this section.
<!--skill-flavor:case-json-task-type:end-->

---

## Step 4 — Common configuration

Never block on these — use the stated default when no answer is available, write it into the node, and note the default in the final report so the user can change it.

| Timeout | Default: 24 hours. If the description states or implies a different duration, use that instead. |
| Priority | Default: Low. If the description states or implies urgency (e.g. "high priority", "urgent", "time-sensitive"), use High or Medium accordingly. Write the chosen value into the node's `priority` field — asking the question is not enough; the value must land in the node. |

---

## Step 4b — Schema Design Resilience (QuickForm — Flow and Case)

Apply these checks while designing the schema, before writing it — per Critical Rule 1, do not wait on the user to confirm. Applies equally to Flow QuickForm nodes and Case QuickForm action tasks — same `fields[]` + `outcomes[]` shape, same `direction` semantics.

### Field direction

Pick direction based on what the human does with the field:

| Signal | Direction |
|---|---|
| "can see", "shown to", "read-only", "displays", "context for reviewer" | `input` |
| "fills in", "enters", "types", "selects", "required decision", "approves" | `output` |
| "can edit", "can correct", "pre-filled but editable", "suggested value the reviewer can adjust" | `inOut` |

`inOut` means the field is pre-populated from an upstream node AND the human can modify it before submitting. The runtime exposes it under `$vars.<nodeId>.output.<fieldId>` the same as an output field.

### Field types

Use the JS/JSON type that fits the field: `string`, `number`, `boolean`, `date`, or `file`. These are the only valid values — do not use `text`. Case also supports `datetime` (distinct from `date`, for full date+time values) — see [hitl-casetask-action.md](references/hitl-casetask-action.md) for the Case-specific type table.

### Vague or incomplete schema descriptions

If the user says something like "just add some fields" or "use whatever makes sense":

1. Infer sensible defaults from the upstream data and downstream needs visible in the `.flow` file (Flow) or in `caseplan.case` upstream task `outputs[]` and `root.data.uipath.variables` (Case).
2. Show the proposed schema explicitly before writing: "Here's what I'm proposing — let me know if you want to change anything."
3. If there is nothing upstream to bind to (Flow with only a trigger; Case with this as the first task), use output-direction fields only and note: "There are no upstream values to pull data from, so the reviewer will fill in all fields from scratch."

### Empty field labels block validation

Every field in `inputs.schema.fields` must have a non-empty `label`. `flow validate` emits `HITL_QUICK_FORM_FIELD_LABEL_REQUIRED` (error severity) for each field with an empty or whitespace-only `label` — Debug and Publish are blocked until all labels are filled in. Never generate a field with `"label": ""` or omit the `label` key.

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

The CLI writes the node, adds the definition entry, and updates `variables.nodes` automatically. Wire one `outcome-<outcome.id>` port per outcome after it returns.

After writing, validate:

```bash
uip maestro flow validate <file> --output json
```

### Surface: Flow — Coded Action App (new inline)

Step 4c must be completed first — app name confirmed, solution directory located, SDK tarball identified, schema designed and confirmed.

Scaffold the project directory and all source files, add the project to the solution, write the solution resource files, then write the HITL node (type `uipath.human-in-the-loop.coded-action-app`) with `inputs.app` referencing the new app (`appSystemName: null` since the app has not been deployed yet).

Full project template, UUID generation, solution CLI commands, resource file templates, node JSON, and post-creation build steps: **[How to scaffold a new Coded Action App](references/hitl-node-coded-action-app.md)**

After writing, validate:

```bash
uip maestro flow validate <file> --output json
```

### Surface: Flow — AppTask (deployed action app only)

Step 4b must be completed first — app resolved, configuration retrieved. Then:

Resolve the solution context (`.uipx` file), write solution resource files, register the app reference, merge `debug_overwrites.json`, then write the node JSON (type `uipath.human-in-the-loop.coded-action-app`) with `inputs.app` populated from the Step 3b configuration.

App search/selection, retrieve-configuration, resource file writing, complete node JSON with `appInputBindings`: **[How to wire an existing deployed Action App](references/hitl-node-apptask.md)**

After writing, validate:

```bash
uip maestro flow validate <file> --output json
```

### Surface: Case

<!--skill-flavor:case-json-write:start-->
In this package, Case HITL is authored by the `uipath-maestro-case` skill (the Case stop in Step 1). Do not write a Case plan here.
<!--skill-flavor:case-json-write:end-->

---

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

<!--skill-flavor:bpmn-xml-write:start-->
In this package, Maestro HITL is authored by the `uipath-maestro-bpmn` skill (the Maestro stop in Step 1). Do not write BPMN XML here. If the `uipath-maestro-bpmn` skill is not installed, tell the user it is needed to add a human task to a Maestro process (`npx skills add UiPath/skills --skill uipath-maestro-bpmn`), and stop; do not fall back to writing XML into the compiled `.bpmn`.
<!--skill-flavor:bpmn-xml-write:end-->

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
- **[Guided decision experience](references/decision-capture-action-app-guide.md)** — Read this only when the request asks to capture a decision or a reviewer corrects a proposal; it decides from the request whether the guided decision experience is on. Covers the toggle, how capture depth scales to stakes, the decision fields it adds beside the author's own, what the backend records, and the capture layout.
- **[HITL business pattern recognition](references/hitl-patterns.md)** — Read this during Step 2 / Step 2b to identify whether a process needs a human checkpoint and which pattern applies. Includes proactive recommendation language and when NOT to recommend HITL.
- **[Action Center URL patterns](../uipath-tasks/references/action-center-urls.md)** (in `uipath-tasks` skill) — Read this before surfacing any Action Center task URL to the user. Covers the missing-tenant-slug anti-pattern and the API-host vs UI-host mapping.
- **[Case Action Task (HITL)](references/hitl-casetask-action.md)** — Case surface: action task JSON, QuickForm vs app-based paths, `.hitl` file format, context entries, field binding, and downstream output access.
