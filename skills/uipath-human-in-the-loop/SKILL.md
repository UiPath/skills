---
name: uipath-human-in-the-loop
description: "UiPath Human-in-the-Loop / HITL node authoring — building approval gates, escalations, write-back validation, and data enrichment checkpoints in Flow, Maestro, Case Management, or Coded Agents. NOT for managing, reassigning, or monitoring tasks at runtime (use uipath-tasks for that)."
allowed-tools: Bash, Read, Write, Edit, Glob, Grep
---

# UiPath Human-in-the-Loop Assistant

Recognizes processes requiring human decisions, designs task schemas conversationally, and wires HITL into Flow, Maestro, Case Management, or an Agent.

> **Coded agents:** use the `uipath-agents` skill for coded-agent HITL wiring: `skills/uipath-agents/references/coded/capabilities/human-in-the-loop.md`.

## When to Use This Skill

Use for approvals, sign-offs, exception or low-confidence review, write-back validation, data enrichment, agent-output review, IT/access, HR, contract, financial, customer-communication, or any workflow requiring human action, including explicit HITL or Action Center tasks.

Do **not** manage, reassign, escalate, or monitor existing Action Center tasks at runtime. Use `uipath-tasks` and provide administration guidance only; do not add a HITL node, flow, or automation. See [references/hitl-patterns.md](references/hitl-patterns.md).

## Critical Rules

1. **Never block on schema confirmation.** Infer the schema from the prompt and upstream `.flow`/`caseplan.json` data, write the node, and prominently report the chosen schema so it can be changed. Use available user input but never wait for it. Stop only when no reasonable inference is possible; a prompt specifying fields, outcomes, and output shape is sufficiently clear.
2. **Always wire `completed`.** It is the only HITL output handle—not `output`, `success`, or another name—even if other nodes use `sourcePort: "output"`.
3. **Definitions first.** Check `workflow.definitions[]` for `uipath.human-in-the-loop.quick-form` or `uipath.human-in-the-loop.coded-action-app`; if absent, append the complete definition with `handleConfiguration.completed`.
4. **Regenerate `variables.nodes`.** After adding a node, replace the entire `workflow.variables.nodes` array; never append. See the reference algorithm.
5. **Validate every change.** Run `uip maestro flow validate <file> --output json` after writing nodes and edges. Do not use `--format`; it is rejected.
6. **Read the existing `.flow` first** to identify nodes and the insertion point.
7. **Add each definition once per node type.** Never duplicate a matching `nodeType` entry.
8. **Avoid duplicate IDs.** Read `workflow.nodes[*].id` and choose the next available suffix.
9. **Never report failed validation as complete.** Diagnose validator JSON errors, fix them, and revalidate.
10. **Use output field IDs, not variables.** Downstream access is `$vars.<nodeId>.output.<fieldId>`. `field.variable` creates only a global alias, not an output-object key. Never use `$vars.<nodeId>.output.<variable>` or rely on `$vars.<variable>` for node outputs.
11. **Bind inputs from upstream output keys, not HITL field IDs.** Derive the key from the upstream script `return`, preserving casing; for example, `supplierName` binds as `vars.<upstreamNode>.output.supplierName` even if the HITL field ID differs.
12. **Downstream scripts read `$vars.<nodeId>.output`.** For example: `const output = $vars.reviewNode1.output; const reason = output.reason;`. Do not rely only on `$vars.<nodeId>.status`, even when routing uses status.

## Step 0 — Resolve the `uip` Binary

```bash
UIP=$(command -v uip 2>/dev/null || npm root -g 2>/dev/null | sed 's|/node_modules$||')/bin/uip
$UIP --version
```

Use `$UIP` thereafter if `uip` is unavailable. In the uipcli repository, use `bun run start` instead.

## Step 1 — Detect the Surface and Find the Flow File

Run in order:

```bash
find . -name "*.flow" -maxdepth 4 | head -5
find . -maxdepth 4 -iname "*.json*" -print0 2>/dev/null | xargs -0 grep -l '"case-management:root"' 2>/dev/null | head -3
find . -name "agent.json" -maxdepth 4 | head -3
find . -name "*.bpmn" -maxdepth 4 | head -3
```

Use a user-provided path directly.

| Found | Surface | Authoring |
|---|---|---|
| `.flow` | Flow | Write node JSON; see QuickForm reference |
| JSON with `root.type: "case-management:root"` | Case | Write an `action` task into the stage; see [hitl-casetask-action.md](references/hitl-casetask-action.md) |
| `agent.json` | Low-Code Agent | Configure escalation manually for now |
| `.bpmn` | Maestro | Write `UserTask`/HITL XML directly; see Step 5 |

<!--skill-flavor:flow-project-creation:start-->
**If no `.flow` exists and the surface is Flow**, scaffold solution-first; Flow projects MUST be inside a solution:

```bash
# Probe once per session:
#   uip solution init --help --output json
# Success: use solution init. If unknown, use uip solution new <SolutionName>.
uip solution init <SolutionName> --output json
cd <SolutionName> && uip maestro flow init <ProjectName>
```

This creates `<SolutionName>/<ProjectName>/<ProjectName>.flow`; the solution directory contains the `.uipx`. Names are distinct, though often equal. Running `uip maestro flow init` outside a solution auto-creates `<ProjectName>Solution/<ProjectName>/`; initializing the solution first controls its name. `--skip-solution-registration` creates a bare single-nested layout that fails Studio Web upload, packaging, and downstream tooling.
<!--skill-flavor:flow-project-creation:end-->

## Step 2 — Read the Business Context

Read the existing `.flow` with the Read tool. Determine the checkpoint, reviewer inputs, returned human data, outcome buttons, and whether to use QuickForm (`uipath.human-in-the-loop.quick-form`) or AppTask (`uipath.human-in-the-loop.coded-action-app`).

## Step 2b — Proactive HITL Recommendation

When HITL is not explicit, scan for write-back validation, exceptions or uncertainty, approval/sign-off/four-eyes, data enrichment or extraction correction, and compliance, regulatory, or audit signals.

For a clear signal, add HITL without waiting and explain: “I noticed that [specific description]. This is a [pattern]—[risk]. I’m inserting a Human-in-the-Loop step so [role] can [action] before the automation [continues/writes/sends].” Record the decision in the final report. Skip it and report an open decision only when the signal is genuinely ambiguous.

## Step 3 — Choose Task Type

Infer and state the choice; never block. Ask only if the user is present and available; otherwise infer.

### Surface: Flow

| Option | Node type | Use |
|---|---|---|
| QuickForm | `uipath.human-in-the-loop.quick-form` | Inline typed Action Center form |
| New Coded Action App | `uipath.human-in-the-loop.coded-action-app` | New React + TypeScript solution app |
| Existing Deployed App | `uipath.human-in-the-loop.coded-action-app` | Existing Orchestrator app |

Default to QuickForm. Use an app only when named or custom UI is required. Read [hitl-node-quickform.md](references/hitl-node-quickform.md), [hitl-node-coded-action-app.md](references/hitl-node-coded-action-app.md), or [hitl-node-apptask.md](references/hitl-node-apptask.md), then continue with Step 4.

### Surface: Case

| Option | Fingerprint | Use |
|---|---|---|
| QuickForm | `<TaskLabel>.hitl.json` plus `hitlType: "quick"` | Structured file form without deployment |
| App-based action task | `data.name`, `data.folderPath` as `=bindings.<id>`, and `data.actionCatalogName` | Deployed Action Center app |

Default to QuickForm unless a deployed app is named. It must support Studio Web round-trip and runtime validation/rendering; always validate after writing. Read [hitl-casetask-action.md](references/hitl-casetask-action.md#path-1--quickform-file-based-schema-no-deployed-app) or [#path-2--app-based-action-task-deployed-action-center-app](references/hitl-casetask-action.md#path-2--app-based-action-task-deployed-action-center-app).

### Fallbacks

- Missing or unresolved deployed app: use QuickForm and state it can be swapped later.
- New coded app without source or `dist/`: use QuickForm, state why, and offer a later swap.
- Custom-app API returns 401: use QuickForm, state that the session appears expired, and suggest `uip login`.
- Case QuickForm schema validation failure: fix errors, apply Step 4b, note the fix, and revalidate; do not pause.

## Step 4 — Common Configuration

Infer and write these defaults unless the description implies otherwise; report them:

| Setting | Default |
|---|---|
| Timeout | 24 hours |
| Priority | Low; Medium or High for stated urgency |

## Step 4b — Schema Design Resilience (QuickForm — Flow and Case)

Apply before writing; never wait for confirmation. Both surfaces use `fields[]` and `outcomes[]` with the same direction semantics.

- `input`: displayed/read-only context.
- `output`: human-entered, selected, or required decision.
- `inOut`: prefilled and editable; runtime output is `$vars.<nodeId>.output.<fieldId>`.
- Allowed types: `string`, `number`, `boolean`, `date`, `file`; do not use `text`. Case also supports `datetime`; see [hitl-casetask-action.md](references/hitl-casetask-action.md).
- Infer vague schemas from upstream and downstream `.flow` data, or Case `outputs[]` and `root.data.uipath.variables`. With no upstream data, use output-only fields and state that the reviewer fills them from scratch.
- Every `inputs.schema.fields[]` item needs a non-empty `label`; otherwise `flow validate` reports `HITL_QUICK_FORM_FIELD_LABEL_REQUIRED` and blocks Debug/Publish.
- Explicitly show the proposed schema before writing.

## Step 5 — Write the Node Directly

### Surface: Flow — QuickForm

Write the node to `workflow.nodes`, add the matching definition once, wire `workflow.edges`, and replace `workflow.variables.nodes`. Use [hitl-node-quickform.md](references/hitl-node-quickform.md) for JSON, definitions, edges, regeneration, and examples.

Only when explicitly requested, the CLI may add the node, definition, and variables:

```bash
uip maestro flow hitl add <path/to/file.flow> \
  --label "<TaskLabel>" \
  --priority <Low|Medium|High> \
  --assignee <email-or-group> \
  --schema '<json>' \
  --output json
```

Wire `completed` afterward and validate:

```bash
uip maestro flow validate <file> --output json
```

### Surface: Flow — New Coded Action App

Complete Step 4c: confirm the app name, locate the solution, identify the SDK tarball, and design/confirm the schema. Scaffold source, add project and solution resources, then write `uipath.human-in-the-loop.coded-action-app` with `inputs.app.appSystemName: null`. Follow [hitl-node-coded-action-app.md](references/hitl-node-coded-action-app.md) and validate.

### Surface: Flow — Existing Deployed Action App

Complete Step 4b; resolve the app and configuration, resolve the `.uipx` solution, write resources, register the app, merge `debug_overwrites.json`, and write the coded-action-app node with `inputs.app` and `appInputBindings` from the configuration. Follow [hitl-node-apptask.md](references/hitl-node-apptask.md) and validate.

### Surface: Case

Read `caseplan.json`, identify the target stage, and write an `action` task into `stage.data.tasks[lane][]`. Direct JSON is the only supported authoring method; there is no `uipath-maestro-case hitl` CLI.

Follow [references/hitl-casetask-action.md](references/hitl-casetask-action.md) for task shapes, fields, assignees, verification, and downstream output access.

- **QuickForm:** write `<TaskLabel>.hitl.json` with unified `fields[]`, `direction`, and `outcomes[]`; add `hitlType: "quick"`, `_schemaFileId` placeholder UUID, and matching `hitlSchemaId`/`schemaId`. Keep `data.inputs[]` and `data.outputs[]` empty; add no root `bindings[]` entries.
- **App-based:** write `data.actionCatalogName`, `data.name`, and `data.folderPath` as `=bindings.<id>` references, plus two root-level bindings.

Validate before reporting success:

```bash
uip maestro case validate <caseplan.json> --output json
```

### Surface: Low-Code Agent

The escalation CLI (`uip agent escalation add`) is in-flight. Configure manually with an `agent.json` escalation entry and an `interrupt(CreateTask(...))` call in the agent Python. See [references/hitl-surface-lowcode-agent.md](references/hitl-surface-lowcode-agent.md).

### Surface: Maestro

For `.bpmn`, write QuickForm or coded-action-app HITL directly into XML; registry shortcut names are not literal XML and there is no dedicated CLI. Use Step 4b and validate frequently:

```bash
uip maestro bpmn validate <file>.bpmn --output json
```

Follow [references/hitl-surface-maestro.md](references/hitl-surface-maestro.md) for the QuickForm `bpmn:task` shape—not `bpmn:UserTask`—including `uipath:inputSchema`, `HitlTaskArguments`, the `Action` process variable, `.hitl.json` sidecar, `_schemaFileId` placeholder, and diagram-interchange edges.

## Step 6 — Report to the User

After wiring, report:

1. **What was inserted:** node ID, label, and insertion point.
2. **Schema summary:** reviewer-visible input fields, human-provided or editable output/inOut fields, and outcomes. For a deployed app, show the `actionSchema` from retrieve-configuration.
3. **Edges wired:** handles and destination nodes, including unwired handles.
4. **Runtime variables:** `$vars.<nodeId>.output` (object), `$vars.<nodeId>.status` (string), and downstream access syntax.
5. **Validation result:** pass or remaining errors to fix.
6. **Production readiness:** QuickForm is ready after solution packaging; a new coded app requires `npm run build` and packaging and remains `appSystemName: null` until deployment; an existing deployed app is ready immediately.
7. **Next step:** pack and publish via the `uipath-development` skill.

## References

- [How to write a QuickForm HITL node](references/hitl-node-quickform.md)
- [How to wire an existing deployed Action App](references/hitl-node-apptask.md)
- [How to scaffold a new Coded Action App](references/hitl-node-coded-action-app.md)
- [HITL business pattern recognition](references/hitl-patterns.md)
- [Action Center URL patterns](../uipath-tasks/references/action-center-urls.md)
- [Case Action Task (HITL)](references/hitl-casetask-action.md)
- [HITL on Maestro BPMN](references/hitl-surface-maestro.md)
- [HITL on a Low-Code Agent](references/hitl-surface-lowcode-agent.md)