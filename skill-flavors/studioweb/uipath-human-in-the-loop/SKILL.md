<!--skill-flavor:bpmn-sdk-surface-detect:start-->
# Check for Maestro .bpmn (Maestro process)
find . -name "*.bpmn" -maxdepth 4 | head -3
<!--skill-flavor:bpmn-sdk-surface-detect:end-->
<!--skill-flavor:flow-sdk-hitl-stop:start-->
**Flow surface (a `.flow.ts`, a `.flow`, or a new flow) — the default: stop here.** Hand the HITL request to the `uipath-maestro-flow` skill: it authors `hitl(...)` in `<Name>.flow.ts` — decompiling an existing `.flow` first — and compiles ([hitl.md](../uipath-maestro-flow/references/hitl.md)). Never read or hand-edit the compiled `.flow`; the next `compile` overwrites it. Steps 2–6 below cover the Case, Low-Code Agent and Maestro surfaces.

<!--skill-flavor:flow-sdk-hitl-stop:end-->
<!--skill-flavor:case-sdk-surface-row:start-->
| `caseplan.case` (any `*.json` or `*.case` whose `nodes[]` carry `data.parentElement.type: "case-management:root"` — the marker is per-node; there is no `root` node on disk) | **Case** | Write `action` task into stage — see [hitl-casetask-action.md](references/hitl-casetask-action.md) |
<!--skill-flavor:case-sdk-surface-row:end-->
<!--skill-flavor:case-sdk-hitl-stop:start-->
<!--skill-flavor:case-sdk-hitl-stop:end-->
<!--skill-flavor:flow-project-creation:start-->
**If no `.flow` file exists and the surface is Flow**, create the Flow project with the `CreateProjects` tool.
<!--skill-flavor:flow-project-creation:end-->
<!--skill-flavor:case-json-task-type:start-->
Infer the right option from the description below — do not pull the registry first, and do not wait for the user to pick before proceeding.

| # | Option | Fingerprint | Description |
|---|---|---|---|
| 1 | **QuickForm (file-based schema)** | separate `<TaskLabel>.hitl.json` file + `hitlType: "quick"` context entry in the action task | Structured form fields in a `.hitl.json` file alongside `caseplan.case`. Action Center renders fields at runtime. No deployed app needed. |
| 2 | **App-based action task** | `data.name` and `data.folderPath` as `=bindings.<id>` references + `data.actionCatalogName` | Uses a deployed Action Center app with custom input/output fields. Requires the app to exist in Orchestrator. |

> **Default: QuickForm.** Pick QuickForm unless the request explicitly names a deployed Action Center app. State the choice, do not ask: "I'll use QuickForm — it's the quickest to set up, supports structured form fields, and doesn't need a deployed app. You can upgrade to an app-based task later if you need a custom UI layout."

> **Build vs design time.** QuickForm in case management must round-trip both ways: the JSON written here is what Studio Web's case designer reads (design time), and what `uip maestro case validate` + Action Center render at runtime (build time). Always validate after writing.

| Option chosen | Next step |
|---|---|
| QuickForm (file-based schema) | Read [references/hitl-casetask-action.md — Path 1](references/hitl-casetask-action.md#path-1--quickform-file-based-schema-no-deployed-app), then continue with Step 4 |
| App-based action task — the request must already name the app | Read [references/hitl-casetask-action.md — Path 2](references/hitl-casetask-action.md#path-2--app-based-action-task-deployed-action-center-app), then continue with Step 4 |

**Fallback rules — never block on these, fall back and state what you did:**

| Path | Blocker | Response |
|---|---|---|
| App-based | App not found in registry or `action-apps-index.json`, or no app name was given | Fall back to QuickForm and proceed. State: "I couldn't find (or wasn't given) that app, so I used QuickForm instead. Point me at a real app name and I'll swap it in." |
| QuickForm | Schema design rejected on validate (e.g. duplicate field IDs, missing primary outcome) | Fix the schema yourself from the validator's error and re-validate. Apply Step 4b checks. Note the fix in the final report — do not pause to re-show the schema first. |
| Any | Auth expired (401 on API call) | Fall back to QuickForm and proceed. State: "The session looked expired, so I used QuickForm rather than stall on re-authenticating. Run `uip login` and ask me to swap in the app when you're ready." |
<!--skill-flavor:case-json-task-type:end-->
<!--skill-flavor:case-json-write:start-->
Read the plan file the detection above found to identify the target stage: `caseplan.case`, or `caseplan.json` in a project an older CLI scaffolded. Edit and validate that file; never create a second plan beside it. Write an `action` task directly into `stage.data.tasks[lane][]`. **Direct JSON write is the only supported method** — the `uipath-maestro-case` skill ships no `hitl` CLI subcommand (unlike Flow's `uip maestro flow hitl add`).

Full reference: **[references/hitl-casetask-action.md](references/hitl-casetask-action.md)** — three task JSON shapes (QuickForm, generic, app-based), field reference, assignee handling, post-write verification, and downstream output access.

| Path chosen in Step 3 | What gets written |
|---|---|
| QuickForm | A `<TaskLabel>.hitl.json` schema file (unified `fields[]` with `direction`, `outcomes[]`) + action task in `caseplan.case` with `data.context[hitlType].value: "quick"`, `_schemaFileId` (placeholder UUID), and `hitlSchemaId` (matches `schemaId` in `.hitl.json`). `data.inputs[]` and `data.outputs[]` are empty arrays. No `root.data.uipath.bindings[]` entries. Apply Step 4b schema-design checks before writing. |
| App-based | Action task with `data.actionCatalogName`, `data.name` and `data.folderPath` as `=bindings.<id>` references. Add 2 root-level bindings. |

After writing, validate (build-time check — must pass before reporting success):

```bash
uip maestro case validate <caseplan.case> --output json
```

> `uip maestro case validate` is the only `uip maestro case` CLI used by this skill on the Case surface. All authoring is direct JSON.
<!--skill-flavor:case-json-write:end-->
<!--skill-flavor:bpmn-sdk-surface-row:start-->
| `.bpmn` (Maestro) | **Maestro** | Write the `UserTask` XML directly — see Step 5 Surface: Maestro |
<!--skill-flavor:bpmn-sdk-surface-row:end-->
<!--skill-flavor:bpmn-sdk-hitl-stop:start-->
<!--skill-flavor:bpmn-sdk-hitl-stop:end-->
<!--skill-flavor:bpmn-xml-write:start-->
QuickForm and coded-action-app HITL nodes are both supported on Maestro BPMN processes. `uipath.human-in-the-loop.quick-form` and `uipath.human-in-the-loop.coded-action-app` are registered as **registry shortcut names** in the BPMN validator ([bpmn-spec.json](../uipath-maestro-bpmn/validator/bpmn-spec.json)) — these are palette/discovery identifiers, not literal XML to write. There is no dedicated CLI subcommand for Maestro (unlike Flow's `uip maestro flow hitl add`) — write the node directly into the `.bpmn` XML.

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

Notes on what's easy to get wrong:
- **Element is `bpmn:task`, not `bpmn:UserTask`.** `bpmn-spec.json`'s generic `Actions.HITL` XML template uses `bpmn:UserTask` and `version="v1"` — that template is for the app-based/coded-action-app path (its `context` fields are `appId`, `appVersion`, `actions`, `key`, `taskTitle`). A real QuickForm task exported from Studio Web is a plain `bpmn:task` with `uipath:type value="Actions.HITL" version="v2"`. Use the shape above for QuickForm; the spec's template for app-based.
- **`<uipath:inputSchema>` (last child of `<uipath:context>`) and `<uipath:input name="HitlTaskArguments">` (sibling of `<uipath:context>`, not inside it) are both required.** Without them the "Edit Schema" canvas in Studio Web doesn't open at all — confirmed by direct reproduction. This mirrors the Case surface's `data.inputSchema`/`data.inputs[]` requirement — see [hitl-casetask-action.md § Step 3](references/hitl-casetask-action.md) for the parallel Case shape and full field-by-field rationale.
- **The `Action` output requires a matching process-level variable declaration** — add `<uipath:inputOutput id="<varId>" name="Action" type="string" elementId="<taskId>" />` inside the process's top-level `<uipath:variables version="v1">` block.
- **A separate `<TaskLabel>.hitl.json` sidecar file is required**, same shape as the Case surface's (`title`, `fields[]` with `direction`/optional `colSpan`/`binding` or `variable`, `outcomes[]` with **no** `action` key, `schemaId`) — see [hitl-casetask-action.md § Step 2](references/hitl-casetask-action.md) for the exact shape; it's identical across both surfaces.
- **`_schemaFileId` cannot be authored blind — it is a server-assigned foreign key, not a UUID you invent.** A placeholder value makes "Edit Schema" fail silently (a `404` on Studio Web's internal `FileOperations/File/Rename` call, confirmed by direct reproduction). There is no `uip` CLI command that resolves this today. **Never block on this.** Write a fresh placeholder UUID v4, finish the rest of the node, validate, and move on — do not attempt the live reconciliation yourself and do not stop to ask about it. State plainly in the final report: "This task's schema was written with a placeholder `_schemaFileId`, so Studio Web's 'Edit Schema' canvas won't open for it yet. Making it editable requires resolving the real file ID Studio Web assigns to the `.hitl.json` after upload (`GET /api/Project/{projectId}/FileOperations/Structure`) and pushing it back with a targeted single-file update (`PUT /api/Project/{projectId}/FileOperations/File/{fileId}`) — not another whole-project `uip solution upload`, which re-pushes every file and mints a fresh random file ID for each one, undoing the fix. Ask me to do this reconciliation if you want the schema editable in Studio Web." This is a real product/tooling gap the user can act on later, not something to resolve mid-task.
- **Diagram-interchange edges are required for the connector lines to render, even though the logical `bpmn:sequenceFlow`s already exist.** Every `bpmn:sequenceFlow` needs a matching `bpmndi:BPMNEdge` (with two `di:waypoint` points, aligned to the source/target shapes' connecting edges) in the `bpmndi:BPMNPlane` — omitting it leaves the nodes logically connected but visually disconnected in the canvas. Confirmed by direct reproduction.

Design the schema per Step 4b — never block waiting on the user, per Critical Rule 1 — then validate frequently (`uip maestro bpmn validate <file>.bpmn --output json`) while wiring the node so any shape mistakes surface immediately rather than at deploy time. In Maestro, field names in `outputs`/`inOuts` must exactly match declared process variable names and types.
<!--skill-flavor:bpmn-xml-write:end-->
