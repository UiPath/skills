---
name: uipath-human-in-the-loop
description: "UiPath Human-in-the-Loop / HITL node authoring — building approval gates, escalations, write-back validation, and data enrichment checkpoints in Flow, Maestro, Case Management, or Coded Agents, plus a guided decision experience that captures reviewer corrections as decisions. NOT for managing, reassigning, or monitoring tasks at runtime (use uipath-tasks for that)."
allowed-tools: Bash, Read, Write, Edit, Glob, Grep
---

# UiPath Human-in-the-Loop Assistant

Recognizes processes needing human decisions, designs task schemas conversationally, and wires HITL into Flow, Maestro, Case Management, or an Agent.

> **Coded agents:** wire HITL inside a coded agent with the `uipath-agents` skill; see `skills/uipath-agents/references/coded/capabilities/human-in-the-loop.md`.

## When to Use This Skill

Use for approval gates, exception escalation, write-back validation, enrichment, agentic-output review, IT access/change approval, HR, contract, financial, customer-communication workflows; explicit HITL, human-review, or Action Center requests; automation requiring human action before continuation; decision capture, Decision Ledger input, or reviewer confirmation/correction.

Before any Coded Action App schema, QuickForm, or document-validation task, read [references/decision-capture-action-app-guide.md](references/decision-capture-action-app-guide.md). Turn its toggle on for decision capture or reviewer confirmation/correction; off means an ordinary form. When the toggle is on, add fixed fields beside author fields: `proposedOutcome`, `proposedBy`, `involvement`, `rationaleDraft`, `nextTimeOptions`, `conditionOptions`, `reasons` with `weight`, `fields` with `byDecision`; outputs are `rationaleText`, `decidingReasons`, `nextTimeScope`, `changes`, `record`, and use one light layout per surface: weighted reasons, nothing pre-selected, final details after the decision, rationale composed from reasons, scoped Next time, collapsed record. Do not rename author fields. QuickForm adds optional Why to every select through one function. Never ask a yes/no question about the toggle; if enabled unasked, state it in one line.

**Do not use this skill for** managing, reassigning, escalating, or monitoring existing Action Center tasks at runtime; use `uipath-tasks` and provide only administration guidance. Do not recommend a new HITL node, flow, or automation for those runtime questions, including as a follow-up tip, even when delays or escalations are mentioned.

See [references/hitl-patterns.md](references/hitl-patterns.md) for business-pattern recognition.

## Critical Rules

1. **Never block on schema confirmation.** Infer from the prompt and upstream `.flow`/`caseplan.case`, write the node, and prominently report the schema. Use offered input but never wait. Stop/report an open decision only when genuinely too ambiguous for reasonable inference; specified fields, outcomes, and output shape are never too ambiguous.
2. **Wire every QuickForm outcome's own port.** Use `outcome-<outcome.id>`, never `completed`. `outcome-completed` exists only with zero outcomes and disappears once `inputs.schema.outcomes` has any entry, including default `Submit`. Every unwired outcome blocks its branch. App-based (`coded-action-app`) nodes always use static `completed`; do not add `inputs.schema`. Neither type uses `output`, `success`, or another name.
3. **Add the definition when inserting into an existing flow.** Check `workflow.definitions[]` for the selected node type—`"uipath.human-in-the-loop.quick-form"` or `"uipath.human-in-the-loop.coded-action-app"`—and, if absent, append its full `handleConfiguration` entry; add each type once. Skipping the definition means the node's handles are invisible to the runtime and the wiring check fails.
4. **Regenerate `variables.nodes`.** Replace the entire `workflow.variables.nodes` array; never append. Use the reference algorithm.
5. **Validate after every change.** Run `uip maestro flow validate <file> --output json` after writing the node and edges. Never use `--format`; it returns `error: unknown option '--format'`, exit code 3.
6. Read the existing `.flow` before adding; understand nodes and checkpoint location.
7. Check `workflow.nodes[*].id`; choose the next available suffix, e.g. `invoiceReview1`, then `invoiceReview2`.
8. Never report failed validation as done; diagnose JSON errors and fix them.
9. Access outputs by `field.id`: runtime keys are `$vars.<nodeId>.output.<fieldId>`. `variable` only creates a workflow-global alias; never use `$vars.<nodeId>.output.<variable>` or `$vars.<variable>` downstream.
10. Bind input fields by the upstream output key (the script's `return` key, preserving camelCase), not the HITL field `id`; wrong keys validate but produce blank fields. If a script returns `{ supplierName: "Acme" }`, bind `vars.fetchSupplier.output.supplierName`, not `suppliername` (the field `id`).
11. **Downstream scripts must access `$vars.<nodeId>.output`.** Any script node that runs after the HITL node must read `$vars.<nodeId>.output` (the result object) — do not rely solely on `$vars.<nodeId>.status`. Example: `const output = $vars.reviewNode1.output; const reason = output.reason;`. This is required even when routing uses `status`.
12. Before writing any Coded Action App `action-schema.json`, QuickForm, or document-validation schema, read [references/decision-capture-action-app-guide.md](references/decision-capture-action-app-guide.md) and, when the toggle is on, add its fields; writing the schema without it drops those fields.

## Step 0 — Resolve the `uip` binary

```bash
UIP=$(command -v uip 2>/dev/null || npm root -g 2>/dev/null | sed 's|/node_modules$||')/bin/uip
$UIP --version
```

Use `$UIP` thereafter when plain `uip` is unavailable. In the uipcli repo, use `bun run start` instead of `uip`.

## Step 1 — Detect the Surface and Find the Flow File

Run in order:

```bash
find . -name "*.flow" -maxdepth 4 | head -5
find . -maxdepth 4 \( -iname "*.json" -o -iname "*.case" \) -print0 2>/dev/null | xargs -0 grep -l '"case-management:root"' 2>/dev/null | head -3
find . -name "agent.json" -maxdepth 4 | head -3
find . -name "*.bpmn" -maxdepth 4 | head -3
```

The Case search detects the content marker, not filename; skip generated `caseplan.case.bpmn` (it carries the marker) and edit `caseplan.case`.

| Found | Surface and authoring |
|---|---|
<!--skill-flavor:flow-sdk-surface-row:start-->
| `.flow.ts` or `.flow` | **Flow**: author `hitl(...)` in `<Name>.flow.ts` through `uipath-maestro-flow`; see [hitl.md](../uipath-maestro-flow/references/hitl.md). Never write node JSON into compiled `.flow`; `compile` overwrites it. |
<!--skill-flavor:flow-sdk-surface-row:end-->
| `caseplan.case`, or `*.json`/`*.case` whose `nodes[]` have `data.parentElement.type: "case-management:root"` (the marker is per-node; there is no `root` node on disk; project files are flat, no `content/` dir) | **Case**: write an `action` task into the stage; see [hitl-casetask-action.md](references/hitl-casetask-action.md). |
| `agent.json` | **Low Code Agent**: escalation CLI is in-flight; guide manually. |
| `.bpmn` | **Maestro**: write `UserTask` XML directly; see Step 5 Surface: Maestro. |

<!--skill-flavor:flow-sdk-hitl-stop:start-->
**Flow surface (a `.flow.ts`, a `.flow`, or a new flow) — default: stop here.** Hand the request to `uipath-maestro-flow`, which authors `hitl(...)` in `<Name>.flow.ts`—decompiling an existing `.flow` first—and compiles ([hitl.md](../uipath-maestro-flow/references/hitl.md)). Never read or hand-edit compiled `.flow`; `compile` overwrites it. Steps 2–6 cover Case, Low-Code Agent, and Maestro.
<!--skill-flavor:flow-sdk-hitl-stop:end-->

If the user named a path, use it directly.

<!--skill-flavor:flow-project-creation:start-->
If no `.flow` exists and the surface is Flow, scaffold solution-first; Flow projects MUST be inside a solution. Probe once per session with `uip solution init --help --output json`: on success use `solution init`; on `unknown command`, use `uip solution new <SolutionName>`.

```bash
uip solution init <SolutionName> --output json
cd <SolutionName> && uip maestro flow init <ProjectName>
```

This creates `<SolutionName>/<ProjectName>/<ProjectName>.flow`; `<SolutionName>/` contains `.uipx`, and `<ProjectName>/` is the flow project. Names may match but are distinct arguments. Running `uip maestro flow init` outside a solution auto-creates `<ProjectName>Solution/<ProjectName>/`; `--skip-solution-registration` creates bare `<ProjectName>/<ProjectName>.flow`, which fails Studio Web upload, packaging, and downstream tooling.
<!--skill-flavor:flow-project-creation:end-->

## Step 2 — Read the Business Context

Read the existing `.flow` with the Read tool. Identify insertion point, upstream data shown, downstream data supplied, named outcome buttons, and form type—QuickForm (`uipath.human-in-the-loop.quick-form`) or AppTask (`uipath.human-in-the-loop.coded-action-app`).

## Step 2b — Proactive HITL Recommendation

When HITL is not explicit, scan for external writes/updates/posts (write-back validation); low confidence, uncertainty, or edge cases (exception escalation); approval/review/sign-off/four-eyes (approval gate); missing-field filling, extraction validation, or correction (enrichment); and compliance, regulatory, or audit trail (compliance checkpoint).

Never block. For a clear approval/review/sign-off signal, insert HITL and say: “I noticed that [specific quote]. This is a [pattern name] — a point where [consequence without review]. I'm inserting a Human-in-the-Loop step here so that [human role] can [action] before the automation [continues/writes/sends].” Proceed without waiting and prominently report the decision so it can be removed. Skip insertion and report an open decision only when the signal is genuinely ambiguous; missing explicit HITL is not ambiguity.

**Example:**
> User: "Build an automation that reads support tickets, uses AI to generate an RCA, and updates the ticket in ServiceNow."
>
> Agent: "I noticed that the automation writes AI-generated content directly back to ServiceNow. This is a write-back validation pattern — if the RCA is incorrect and nobody reviews it, wrong data goes into production tickets. I'm inserting a Human-in-the-Loop step so that a support lead can review and optionally edit the RCA before the update is applied."

## Step 3 — Choose Task Type

Infer, state, and proceed; ask only when the user is present and available. Non-interactive runs infer and continue. On Flow and Case, do not run a registry search (or pull the registry) before choosing, and do not wait for the user to pick before proceeding.

### Surface: Flow

Options: **QuickForm**, `uipath.human-in-the-loop.quick-form`, inline typed form; **New Coded Action App**, `uipath.human-in-the-loop.coded-action-app`, new React + TypeScript app in the solution; **Existing Deployed App**, the same node type referencing an Orchestrator app. Default QuickForm. Choose an app only when explicitly naming a deployed/coded app or custom UI; state: “I'll use QuickForm — it's inline, no deployment step needed, and works for most approval and review tasks. You can swap in a Coded Action App or an existing deployed app later if you need one.”

Guided decision requests read [Guided decision experience](references/decision-capture-action-app-guide.md), add its fields/layout, and wire as New Coded Action App. For QuickForm read [How to write a QuickForm HITL node](references/hitl-node-quickform.md) for Steps 1–2, then Step 4. For New Coded Action App read [How to scaffold a new Coded Action App](references/hitl-node-coded-action-app.md) for Step 4c, then Step 4. For Existing Deployed App (request must already name the app) read [How to wire an existing deployed Action App](references/hitl-node-apptask.md) for Step 4b, then Step 4.

Fallbacks (never block; fall back to QuickForm, proceed, and say): missing/unfound deployed app or name → QuickForm and say “I couldn't find (or wasn't given) a deployed app name, so I used QuickForm instead. Point me at a real app name and I'll swap it in.” New app without `dist/` → say “The source folder doesn't have a `dist/` build yet, so I wired a QuickForm for now — run your build and ask me to swap in the Coded Action App once it's ready.” No source path → say “No app source path was given, so I used QuickForm to wire the checkpoint now. Point me at the app code and I'll replace it with a Coded Action App.” Custom app API 401 → say “The session looked expired, so I used QuickForm rather than stall on re-authenticating. Run `uip login` and ask me to swap in the app when you're ready.”

### Surface: Case

Options: **QuickForm (file-based schema)**—`<TaskLabel>.hitl.json` + `hitlType: "quick"` context entry in the action task, structured fields, no deployed app; **App-based action task**—`data.name` and `data.folderPath` as `=bindings.<id>` plus `data.actionCatalogName`, requiring a deployed app. Default QuickForm; state: “I'll use QuickForm — it's the quickest to set up, supports structured form fields, and doesn't need a deployed app. You can upgrade to an app-based task later if you need a custom UI layout.”

Case QuickForm must round-trip through Studio Web case designer, `uip maestro case validate`, and Action Center; always validate after writing. For QuickForm read [references/hitl-casetask-action.md — Path 1](references/hitl-casetask-action.md#path-1--quickform-file-based-schema-no-deployed-app), then Step 4. For App-based (request must name app) read [references/hitl-casetask-action.md — Path 2](references/hitl-casetask-action.md#path-2--app-based-action-task-deployed-action-center-app), then Step 4.

If the app is absent from the registry or `action-apps-index.json`, or unnamed, use QuickForm and say “I couldn't find (or wasn't given) that app, so I used QuickForm instead. Point me at a real app name and I'll swap it in.” For schema rejection (e.g. duplicate field IDs or missing primary outcome), fix the schema yourself from the validator's error, re-validate, apply Step 4b, and report the fix without pausing. API 401 uses the same QuickForm/session-expired response above.

## Step 4 — Common configuration

Do not block; use defaults, write them into the node, and report them. Timeout defaults to 24 hours unless the description states or implies another duration. Priority defaults to Low; if the description states or implies urgency (e.g. "high priority", "urgent", "time-sensitive"), use High or Medium accordingly. Write the chosen value into the node's `priority` field — asking the question is not enough; the value must land in the node.

## Step 4b — Schema Design Resilience (QuickForm — Flow and Case)

Apply before writing; per Critical Rule 1, do not wait on the user to confirm. Flow and Case QuickForms share `fields[]`, `outcomes[]`, and `direction`: `input` is visible/read-only context ("can see", "shown to", "read-only", "displays", "context for reviewer"); `output` is human-entered/selected/required decisions ("fills in", "enters", "types", "selects", "required decision", "approves"); `inOut` is upstream-prefilled and editable ("can edit", "can correct", "pre-filled but editable", "suggested value the reviewer can adjust"), exposed as `$vars.<nodeId>.output.<fieldId>`. Only `string`, `number`, `boolean`, `date`, `file`; never `text`. Case additionally supports `datetime`; see [hitl-casetask-action.md](references/hitl-casetask-action.md).

For vague requests ("just add some fields", "use whatever makes sense"), infer schemas from upstream/downstream needs—Flow `.flow`, or Case upstream task `outputs[]` and `root.data.uipath.variables`; explicitly show the proposed schema before writing: “Here's what I'm proposing — let me know if you want to change anything.” With no upstream values (Flow with only a trigger; Case with this as the first task), use output-only fields and state: “There are no upstream values to pull data from, so the reviewer will fill in all fields from scratch.” Every `inputs.schema.fields` field needs a nonempty `label`; never omit it or use `"label": ""`. Empty/whitespace labels cause `HITL_QUICK_FORM_FIELD_LABEL_REQUIRED` and block Debug/Publish.

## Step 5 — Write the Node Directly

### Surface: Flow — QuickForm (inline schema only)

Write JSON into `workflow.nodes`, add the definition once, wire `workflow.edges`, and replace `workflow.variables.nodes`. See **[How to write a QuickForm HITL node](references/hitl-node-quickform.md)** for node/definition/edge formats, the `variables.nodes` algorithm, and examples.

Only when explicitly requested, run:

```bash
uip maestro flow hitl add <path/to/file.flow> \
  --label "<TaskLabel>" \
  --priority <Low|Medium|High> \
  --assignee <email-or-group> \
  --schema '<json>' \
  --output json
```

The CLI writes the node, definition, and `variables.nodes`; afterward wire one `outcome-<outcome.id>` per outcome. On either path, validate after writing:

```bash
uip maestro flow validate <file> --output json
```

### Surface: Flow — Coded Action App (new inline)

Complete Step 4c first: confirm app name, locate solution, identify SDK tarball, and design/confirm schema. Scaffold directory/source, add the project to the solution, write solution resources, then write node type `uipath.human-in-the-loop.coded-action-app` with `inputs.app` referencing the new app and `appSystemName: null` until deployment. Follow **[How to scaffold a new Coded Action App](references/hitl-node-coded-action-app.md)** for template, UUIDs, solution commands, resources, node JSON, and build steps. Validate with `uip maestro flow validate <file> --output json`.

### Surface: Flow — AppTask (deployed action app only)

Complete Step 4b: resolve app/configuration; resolve `.uipx`, write solution resources, register the app reference, merge `debug_overwrites.json`, then write node type `uipath.human-in-the-loop.coded-action-app` with `inputs.app` from Step 3b. Follow **[How to wire an existing deployed Action App](references/hitl-node-apptask.md)** for lookup, configuration, resources, node JSON, and `appInputBindings`. Validate with `uip maestro flow validate <file> --output json`.

### Surface: Case

Edit detected `caseplan.case`, or older-CLI `caseplan.json`; never create a second plan. Write `action` directly into `stage.data.tasks[lane][]`; direct JSON is the only supported method, and `uipath-maestro-case` has no HITL CLI subcommand. Read **[references/hitl-casetask-action.md](references/hitl-casetask-action.md)** for three task shapes, fields, assignees, verification, and downstream output access.

QuickForm writes `<TaskLabel>.hitl.json` with unified `fields[]`/`direction`/`outcomes[]`, plus an action task containing `data.context[hitlType].value: "quick"`, placeholder UUID `_schemaFileId`, and `hitlSchemaId` matching `.hitl.json` `schemaId`; `data.inputs[]` and `data.outputs[]` are empty, with no `root.data.uipath.bindings[]`. Apply Step 4b. App-based writes `data.actionCatalogName`, `data.name` and `data.folderPath` as `=bindings.<id>` references, plus two root-level bindings.

After writing, validate — must pass before reporting success:

```bash
uip maestro case validate <caseplan.case> --output json
```

This is the only `uip maestro case` command here; all Case authoring is direct JSON.

### Surface: Low-Code Agent

The `uip agent escalation add` CLI is in-flight; configure manually until it ships:

**`agent.json` escalation entry:**
```json
{
  "escalations": [
    {
      "name": "<escalation-name>",
      "inputSchema": { "inputs": [...], "inOuts": [...] },
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

QuickForm and coded-action-app are supported. `uipath.human-in-the-loop.quick-form` and `uipath.human-in-the-loop.coded-action-app` are BPMN-validator registry shortcuts, not literal XML; see [bpmn-spec.json](../uipath-maestro-bpmn/validator/bpmn-spec.json). There is no Maestro HITL CLI; write directly to `.bpmn` XML.

QuickForm uses plain `bpmn:task`, not `bpmn:UserTask`, with `uipath:type` `Actions.HITL` version `v2`. The generic `bpmn-spec.json` `bpmn:UserTask`, `version="v1"` template is for app-based/coded-action-app and uses `appId`, `appVersion`, `actions`, `key`, `taskTitle`.

**Confirmed node shape (verified by direct reproduction against a real Studio Web BPMN process with a working, editable QuickForm task):**

```xml
<bpmn:task id="Activity_InvoiceApproval" name="Invoice Approval">
  <bpmn:extensionElements>
    <uipath:activity version="v1">
      <uipath:type value="Actions.HITL" version="v2" />
      <uipath:context>
        <uipath:input name="hitlType" type="string" value="quick" />
        <uipath:input name="taskTitle" type="string" value="Please review this invoice and approve or reject" />
        <uipath:input name="labels" type="string" />
        <uipath:input name="priority" type="string" value="Medium" />
        <uipath:input name="actionCatalogName" type="string" />
        <uipath:input name="enableActionableNotifications" type="boolean" value="false" />
        <uipath:input name="assignmentCriteria" type="string" />
        <uipath:input name="recipient" type="json" />
        <uipath:input name="_schemaFileId" type="string" value="<see file-id callout below>" />
        <uipath:input name="hitlSchemaId" type="string" value="<matches schemaId in the .hitl.json sidecar>" />
        <uipath:inputSchema type="jsonSchema"><![CDATA[{"$schema":"http://json-schema.org/draft-07/schema#","type":"object","properties":{"invoiceid":{"type":"string","title":"Invoice ID"},"amount":{"type":"number","title":"Amount"}},"required":[]}]]></uipath:inputSchema>
      </uipath:context>
      <uipath:input name="HitlTaskArguments" type="json" target="bodyField"><![CDATA[{"invoiceid":"INV-1001","amount":500}]]></uipath:input>
      <uipath:output name="Action" type="string" source="=Action" var="invoiceDecision" options="[{&#34;value&#34;:&#34;Approve&#34;,&#34;label&#34;:&#34;Approve&#34;},{&#34;value&#34;:&#34;Reject&#34;,&#34;label&#34;:&#34;Reject&#34;}]" />
    </uipath:activity>
  </bpmn:extensionElements>
  <bpmn:incoming>edge_into_task</bpmn:incoming>
  <bpmn:outgoing>edge_out_of_task</bpmn:outgoing>
</bpmn:task>
```

`<uipath:inputSchema>` must be the final `<uipath:context>` child, and sibling `HitlTaskArguments` is required; otherwise Studio Web's Edit Schema canvas does not open. This mirrors Case `data.inputSchema`/`data.inputs[]` — see [hitl-casetask-action.md § Step 3](references/hitl-casetask-action.md). Add process-level `<uipath:inputOutput id="<varId>" name="Action" type="string" elementId="<taskId>" />` inside top-level `<uipath:variables version="v1">`. Add a `<TaskLabel>.hitl.json` sidecar matching Case: `title`, `fields[]` with `direction` and optional `colSpan`/`binding` or `variable`, `outcomes[]` with **no `action` key**, and `schemaId`; see [hitl-casetask-action.md § Step 2](references/hitl-casetask-action.md).

`_schemaFileId` cannot be authored blind — it is a server-assigned foreign key, has no resolving CLI, and must not block progress. Write a fresh placeholder UUID v4, finish the rest of the node, validate, and move on — do not attempt the live reconciliation (GET/PUT FileOperations) yourself and do not stop to ask about it. Report exactly: “This task's schema was written with a placeholder `_schemaFileId`, so Studio Web's 'Edit Schema' canvas won't open for it yet. Making it editable requires resolving the real file ID Studio Web assigns to the `.hitl.json` after upload (`GET /api/Project/{projectId}/FileOperations/Structure`) and pushing it back with a targeted single-file update (`PUT /api/Project/{projectId}/FileOperations/File/{fileId}`) — not another whole-project `uip solution upload`, which re-pushes every file and mints a fresh random file ID for each one, undoing the fix. Ask me to do this reconciliation if you want the schema editable in Studio Web.”

Every `bpmn:sequenceFlow` needs a matching `bpmndi:BPMNEdge` with two `di:waypoint` points aligned to source/target connecting edges; logical flows alone disconnect visual connectors. Design per Step 4b without waiting. Validate frequently with `uip maestro bpmn validate <file>.bpmn --output json`. In Maestro, `outputs`/`inOuts` names must exactly match declared process variable names and types.

## Step 6 — Report to the User

Report: (1) inserted node ID, label, insertion point; (2) schema summary—shown input fields, completed output/inOut fields, clicked outcomes, and for deployed apps the `actionSchema` from retrieve-configuration; (3) wired handles/target nodes and unwired handles; (4) `$vars.<nodeId>.output` object and `$vars.<nodeId>.status` string with downstream access rules; (5) validation pass or errors; (6) readiness—QuickForm deployable once packaged; New Coded Action App requires `npm run build` in its source and solution packaging and remains `appSystemName: null` until first deployment; Existing Deployed App immediately deployable; (7) next step: pack and publish through `uipath-development`.

## References

- **[How to write a QuickForm HITL node](references/hitl-node-quickform.md)** — Read after QuickForm selection; node JSON, definition, edges, `variables.nodes`, and examples.
- **[How to wire an existing deployed Action App](references/hitl-node-apptask.md)** — Read for existing apps; Orchestrator lookup, `inputs.app`, `appInputBindings`, and resources.
- **[How to scaffold a new Coded Action App](references/hitl-node-coded-action-app.md)** — Read for new apps; template, UUIDs, solution commands, and builds.
- **[Guided decision experience](references/decision-capture-action-app-guide.md)** — Read before Coded Action App schemas; toggle, capture depth, fields, backend record, and layout.
- **[HITL business pattern recognition](references/hitl-patterns.md)** — Read during Step 2/2b for patterns, recommendation language, and when not to recommend.
- **[Action Center URL patterns](../uipath-tasks/references/action-center-urls.md)** — Read before surfacing Action Center URLs; tenant-slug anti-pattern and API/UI host mapping.
- **[Case Action Task (HITL)](references/hitl-casetask-action.md)** — Case action JSON, QuickForm/app paths, `.hitl` format, context, binding, and downstream access.