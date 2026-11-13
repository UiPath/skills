# BPMN runtime decisions

This reference contains only choices that types and static validation cannot
make from syntax alone. Exact signatures remain in the generated API.

## Variables and the process contract

<!-- RULE:bpmn.variables.public-scope -->
- Declare a process's public contract with `.input()` and `.output()`, not `.var()`:
  the compiler scopes a top-level input to the manual start event and a top-level
  output to the end event whose mapping writes it (`elementId`), which is where the
  canvas declares them and where a grader of the process contract reads them. A
  `.var()` is internal, process-level state. Name an `elementId` only to scope a
  variable to a specific element yourself.

<!-- RULE:bpmn.variables.read-inputs-directly -->
- A script or expression reads a public input as `vars.<id>` directly; the runtime
  seeds every declaration by id. The start-event mapping that bridges each input into
  an internal variable is the canvas's spelling, not a requirement.

<!-- RULE:bpmn.variables.input-name -->
- Input values are matched to declarations by display `name` when a run starts, so an
  input given a `name` (`.input('amount', 'number', { name: 'Amount' })`) is supplied
  under `Amount`. Leave `name` off unless the caller's key is meant to differ from the id.

<!-- RULE:bpmn.variables.node-output-declares-itself -->
- **Do not declare a variable for a node's own output.** An output row declares the
  variable it fills: the compiler derives a declaration from the row, attributed to that
  node, with the row's `name` and `type`. Writing a `.var()` beside the node for the same
  id states the same thing twice and makes it the author's declaration instead of the
  node's. Where the variable carries a JSON Schema, put it on the ROW as `varSchema` —
  the platform writes the shape on the declaration and not on the row, so `varSchema` is
  what reaches it:

  ```ts
  outputRows: [{ name: 'response', type: 'jsonSchema', var: 'act_response',
                 source: '=result', varSchema: 'responseSchema' }]
  ```

  Reserve `.var()` for process-level state nothing fills for you. In the real exports
  measured, 688 of 842 declarations are a node's own output and the product marks only
  the author's with `custom="true"`.

<!-- RULE:bpmn.variables.element-id-is-placement -->
- `elementId` is placement, not scope. The runtime seeds every declaration into one flat
  namespace and resolves `vars.<id>` there whatever it says, and an id is unique across
  the whole document — so two elements cannot each own a `response`. What it decides is
  which element the declaration BELONGS to, which is what the canvas and
  `uip maestro bpmn validate` read (1.203 requires one).

<!-- RULE:bpmn.variables.array-forms -->
- `.vars([…])`, `.bindings([…])` and `.schemas([…])` take the whole block at once, with
  `direction: 'input' | 'output'` on an entry that is not internal state. The singular
  `.var()` / `.input()` / `.output()` / `.binding()` / `.schema()` calls are unchanged and
  mix freely; prefer the array form where there is more than a handful, which is what
  `bpmn decompile` writes.

<!-- RULE:bpmn.variables.preserve-block -->
- `.preserve({ … })` is NOT authoring surface. It carries state a source document had
  that no rule derives and nothing executes — today `variableOrder`, the order the
  variables panel lists declarations in. `bpmn decompile` writes it; leave it alone, and
  do not add to it. Anything authorable belongs in the typed builder, where `check` and a
  reader can see it. If you add or rename a declaration in a decompiled file, either
  update every id in that array or delete the call — `check` warns
  `VARIABLE_ORDER_INCOMPLETE` / `VARIABLE_ORDER_UNKNOWN_ID` /
  `VARIABLE_ORDER_DUPLICATE_ID`, because a PARTIAL list silently reorders the block.

## Script tasks

<!-- RULE:bpmn.script.result-response -->
- A script task (`scriptVersion` v3, what `.scriptTask()` writes) returns its value and the runtime wraps it as `result.response`.
  Read it as `=result.response` for a scalar, or `=result.response.<field>` for one field of a returned object; never `=result.<field>`, which reads nothing.
  Write `return value;`, not `return { response: value };`, which double-wraps to `result.response.response`.
  `check` reports `=result.<field>` on a v2-or-later script as `SCRIPT_RESULT_NOT_RESPONSE` and names the corrected expression; `compile` and `validate` accept it, and the run then completes with the output empty.
<!--skill-flavor:sdk-script-result:start-->
  Needs `@uipath/maestro-builder-sdk` 6.93.7 or later; an older `check` does not report it, so upgrade with `npm install -g @uipath/maestro-builder-sdk@latest`.
<!--skill-flavor:sdk-script-result:end-->

  ```ts
  .scriptTask('score', { script: 'return vars.amount * 0.01;', outputs: { riskScore: '=result.response' } })
  ```

  Returning an object: `script: 'return { severity: s, nextSteps: n };'` with `outputs: { severity: '=result.response.severity', nextSteps: '=result.response.nextSteps' }`.

<!-- RULE:bpmn.script.mapping-type -->
- Do not pass `type` to `.scriptTask()`.
  Its mapping type is always `BPMN.Variables`, the default; any other value replaces the script's extension type, so the script never runs and its outputs read back null.
  `registry get BPMN.ScriptTask` lists `BPMN.ScriptTask`, and that listing is not a value to pass.
  The builder refuses any other value with `BPMN_SCRIPT_TASK_TYPE_INVALID`; drop `type`.
  `.activity(id, 'BPMN.ScriptTask', …)` is refused too (`BPMN_ACTIVITY_SCRIPT_TASK_TYPE`); write the script with `.scriptTask()`.
<!--skill-flavor:sdk-script-type:start-->
  Needs `@uipath/maestro-builder-sdk` 6.93.8 or later; an older SDK writes whatever `type` says, so upgrade with `npm install -g @uipath/maestro-builder-sdk@latest`.
<!--skill-flavor:sdk-script-type:end-->

<!-- RULE:bpmn.script.error-row -->
- "Typed error handling" on a script task means the task-scoped `Error` output row: `source: '=Error'`, type `jsonSchema`, writing a variable whose schema is the platform error envelope.
  It is not an error boundary or a second end event, which change the graph.
  `.scriptTask()` has no `errorVar`, so spell both rows with `outputRows`, which replaces `outputs`:

  ```ts
  import { bpmn, errorSchema } from '@uipath/maestro-builder-sdk/bpmn';

  .scriptTask('score', {
    script: 'return vars.amount * 0.01;',
    outputRows: [
      { name: 'scriptResponse', type: 'double', var: 'riskScore', source: '=result.response' },
      { name: 'Error', type: 'jsonSchema', var: 'score_Error', source: '=Error', varSchema: errorSchema },
    ],
  })
  ```

  Each row declares its own variable (`score_Error` is scoped to the task), so add no `.var()` for either.
  The row is spelled as the platform's script-task template writes it and passes `compile` and `validate`; no run has yet shown a failing script fill it, so when no live run showed it, report the `Error` mapping as unverified.

## Events and timers

<!-- RULE:bpmn.event.payload-live -->
- Connector event payloads and timer firing are runtime facts. Static validation
  proves the declaration, not that a tenant subscription fires.

<!-- RULE:bpmn.event.net-scope -->
- An event sub-process catches only failures raised in the container it sits directly in.
  Declared at process level it ends the whole run on the first failure; declared inside a multi-instance sub-process it ends only that iteration.
  Place `.eventSubProcess()` in the scope whose failure it should absorb.

<!-- RULE:bpmn.event.error-context -->
- The engine surfaces a failed element's error under the capital-`Error` key with lowercase fields (`code`, `message`, `detail`, `category`, `status`, `traceId`, `response`, `element`).
  `.eventSubProcess({ error: true })` captures it on its start event by default, into `vars.<net>_Error` — a per-net id, which is how the designer names one: every error capture in the measured exports has a unique id with the display name `Error`, and the bare `vars.Error` appears in none. So a net called `failures` reads `vars.failures_Error.<field>` with nothing more written; `errorVar` names it something else and `errorVar: false` omits the capture.
  The platform validator needs the declaration: a `vars.<id>` read with no captured variable is `VARIABLE_DOES_NOT_EXIST`, in a net or anywhere else. Note the runtime resolves `vars.<id>` in ONE flat scope whatever a declaration's `elementId` says, so two captures cannot share an id — that is why the default is per-net.
  A boundary handler captures nothing by default; there `errorVar` is what makes the error readable.

<!-- RULE:bpmn.event.non-interrupting-path -->
- A non-interrupting boundary handler runs beside a token that still reaches the next step, so its path must end on its own; rejoining the main path would run everything after it twice.
  The builder refuses a non-interrupting handler path left open.

## HTTP and Orchestrator work

<!-- RULE:bpmn.http.webhook-url -->
- A request that must reach a connection's webhook (to fire a `waitForEvent` on an HTTP Webhook connection, say) is a manual `.http()` with the webhook URL as a literal `url` and no `connection`: `.http('ping', { url: '<WEBHOOK_URL>', method: 'GET' })`.
  Get the URL from `uip is webhooks config <connector-key> --connection-id <id> --output json`: it is `Data.WebhookUrl`.
  Never use `uip is connections base-url` for it; that is the connection's API base, a different address, so the event never arrives.
  If `webhooks config` fails with `has no element instance id`, check the id and the connector with `uip is connections list <connector-key> --output json`.
  Only a connection of the HTTP Webhook connector (`uipath-http-webhook`) can fire this event.

<!-- RULE:bpmn.orchestrator.names -->
- Published work is addressed by name and folder. Queue items require a folder;
  live execution is the evidence that the resource exists and is runnable.

<!-- RULE:bpmn.orchestrator.job-outputs -->
- A job's output arguments are fields of `result`: map each one with `outputs` on the job node, as in `.executeApiWorkflow('greet', { process, folder, input, outputs: { message: '=result.message' } })`.
  The same `outputs` option reads an RPA process's (`.startProcess()`), an agent's (`.startAgent()`) and a waited-for agentic or case process's (`.startAgenticProcess()`, `.startCaseProcess()` without `async`) output arguments.
  `outputVar` (default `<id>_processResponse`) holds the job envelope, not the arguments; do not read an argument out of it with a `=js:` chain.
  The argument name is the workflow's own output argument, as the deployed process declares it; when no live run has shown it, say the mapping is unverified.

<!-- RULE:bpmn.http.manual -->
- A plain HTTP call with no connection is `.http(id, { url, method, parameters, headers, body })` with no `connection`.
  It writes the request in manual mode with the `ImplicitConnection` binding Studio Web uses, so nothing on the tenant has to exist.
  `outputVar` (default `<id>_response`) holds the response body; `<id>_code`, `<id>_headers` and `<id>_Error` hold the rest.
  `check` warns `HTTP_MANUAL_V1` on the old manual form (`mode="manual"` with the request as context rows), which the runtime faults with 102018 "Body cannot be null"; rewrite it as `.http()` and compile.
<!--skill-flavor:sdk-http-manual:start-->
  Needs `@uipath/maestro-builder-sdk` 6.93.9 or later; an older SDK still writes the old manual form, with `outputVar` holding the whole response and no `HTTP_MANUAL_V1` warning, so upgrade with `npm install -g @uipath/maestro-builder-sdk@latest` and compile again.
  From 6.93.9, `outputVar` is the body, so read `vars.<id>_response.x`, not `vars.<id>_response.body.x`, which read the old form's whole response.
<!--skill-flavor:sdk-http-manual:end-->

<!-- RULE:bpmn.orchestrator.business-rule -->
- A deployed business rule is `.businessRule(id, { process, folder, input, outputs })`, nothing else.
  The builder writes the version, the `BusinessRule` bindings and the `output`/`Error` rows; do not add them. The result is keyed by decision name: a column reads `=result.<Decision>.<column>`, as in `outputs: { tier: '=result.Eligibility.tier' }` or `vars.<id>_businessRuleResponse.Eligibility.tier` downstream, never `=result.tier` or `=response.tier`. `uip rules describe <name> --folder-path <folder> --output json` lists the deployed rule's decisions and columns; only a decision-keyed rule (its `OutputArguments` carry `x-uipath-decision-keyed`) fits this row.
  `releaseKey` is refused: a rule is never addressed by a process key.

<!-- RULE:bpmn.runtime.metadata -->
- `metadata.*` values are empty in local `flow-debug`. Use literals or `vars.*`
  when an offline behavior check must observe the value.

## Human task outcomes

<!-- RULE:bpmn.hitl.inline-form-default -->
- Write every human task as an inline form: `.humanTask(id, { form: { fields, outcomes }, outputs: { decision: '=Action' } })`.
  The form travels in the `.bpmn`, so nothing on the tenant has to exist.
  The SDK cannot yet write a working app-backed task: `.humanTask(id, { app })` writes a v1 `Actions.HITL` task with only an `appId`, which `uip maestro bpmn validate` rejects with `MISSING_BINDING` / `MISSING_RESOURCE` and which the engine does not read.
  When the request names a deployed Action App, author the inline form anyway, tell the user the task is not bound to their app, and point them to the Studio Web designer to switch it to the app.
  Never swap a human task for a plain `.task()` to get past that — use the form.
- A field is `input` (shown, `value: '=vars.x'`), `output` (asked; the answer lands in `variable`, default the id) or `inOut` (shown, editable, written back).
  The call refuses a form that breaks any of these:
  - Every field id is a plain identifier that is not a reserved word: `reviewNote`, not `review-note` or `default`.
  - No field is called `Action`; that is the outcome picked.
  - Outcome ids are unique, including derived ones: `Needs review` and `Needs-review` collide.
  - Each variable has one writer: two answers never share a `variable`, and an `outputs` key is never an answer's variable (a field named `decision` beside `outputs: { decision: '=Action' }` is refused).
  - A picker (`singleSelect`, `multiSelect`, `enum`, or a dropdown `controlType`) has `options`, e.g. `[{ id: 'o1', value: 'high', label: 'High' }]`.
- The cloud engine takes the inline-form path only on a tenant with its quick-form flag on.
  With the flag off, the run fails at the human task with a HITL incident: `170004` "Invalid input for the HITL task" on current engines, or `170015` "No app … found" on engines from before mid-September 2026.
  Then tell the user to enable the quick-form flag on the tenant; do not fall back to `.task()` or to `app`.
- Studio Web's "Edit Schema" canvas does not open for an inline form.

<!-- RULE:bpmn.hitl.output-map -->
- Map any decision used by later routing through `outputs`; the typed platform
  output is not populated by the local runtime. Exercise each important outcome.

<!-- RULE:bpmn.hitl.default-path -->
- With no injected outcome, local debug takes the gateway default. Choose that
  path deliberately and use `--hitl-response` to verify non-default outcomes.

## Connectors and bindings

Choosing the operation, and the author → check → prepare → check → compile loop
that fills it in, are in **[`connectors.md`](connectors.md)**. What follows is the
binding half, which is the same for every connector-backed node.

<!-- RULE:bpmn.connector.bindings -->
- Keep connection and folder values symbolic in TypeScript and resolve them from
  `bindings.json`. Only a live run proves those environment bindings.

<!-- RULE:bpmn.binding.value-vs-resource-key -->
- `value` is the value; `resourceKey` is never resolved. `=bindings.<id>` evaluates to
  `value` (the wire's `default`), and that is the only field a run reads — resolution is
  `supplied[id] ?? supplied[name] ?? value`, so a binding with neither is UNRESOLVED and
  a dispatching run refuses to start naming every one. `resourceKey` is design-time
  provenance: which tenant resource this was bound to, for a deploy to re-resolve `value`
  against. They are equal only when the property asked for IS the resource's identity (a
  queue is its name); set both when they are different things, and expect no `value` on a
  `folderPath`, which is not knowable when the resource is picked.
  Note the author-side `bindings.json` uses `resourceKey` the OTHER way round — the real
  tenant value, with `default` as an offline placeholder — so do not carry one file's
  reading into the other.

<!-- RULE:bpmn.connector.folder-companion -->
- A `folderKey` binding is the companion of a connection, not a resource of its
  own: its `resourceKey` is the connection's key and only its `value` is the
  folder key. That is how the platform resolves the connection, and `validate`
  reports `MISSING_BINDING` for a folder binding keyed by the folder. Declare the
  pair once — `.binding(c, { resource: 'Connection', propertyAttribute:
  'ConnectionId', value })` and `.binding(f, { resource: 'Connection',
  propertyAttribute: 'folderKey', value })` — and read both from the same node
  (`connection: '=bindings.c'`, `folderKey: '=bindings.f'`); the compiler keys the
  folder by that connection, and `check` warns `FOLDER_BINDING_KEYED_BY_FOLDER` /
  `FOLDER_BINDING_UNPAIRED` when it cannot.

<!-- RULE:bpmn.connector.data-service -->
- Data Fabric (Data Service, connector `uipath-uipath-dataservice`) records and
  file fields are `.dataService(id, { entity, connection, folder, op, … })`, one of
  eight operations: `create`, `update`, `get`, `query`, `delete`, `downloadFile`,
  `uploadFile`, `deleteFile`. It writes the `Intsvc.ActivityExecution` node the
  way the platform's own tools do and needs no connector library or `prepare`
  step. The response lands in `<id>_response` and the error payload in
  `<id>_Error`, both declared for you — read the created record's id as
  `=vars.<id>_response.Id`. Map results onto process outputs on the end event
  (`payload: { type: 'BPMN.Variables', outputRows: [{ name, type, var, source:
  '=vars.<id>_response' }] }`). Do not hand-fill
  `.activity('Intsvc.ActivityExecution', …)` for these operations: the library
  ships one Data Service operation, so `.connector()` cannot author the rest, and a
  hand-filled node gets `objectName`, the parameter targets and the folder binding
  wrong in ways `validate` does not report. `examples/ContractRegistry.bpmn.ts` is
  the full lifecycle.

<!-- RULE:bpmn.connector.data-service-folder-entity -->
- An entity that lives in an Orchestrator folder (the picker shows it under a folder; the request says "folder entity" or "entity scope: folder") is `entity: { name, folder: '<folder path>' }`, not a plain name and not hand-found keys.
  `bpmn check --source` reports it as `RESOURCE_UNRESOLVED` and prints the command that records its keys, `uip maestro registry prepare --entity <name> --folder-path <path>`; run it, then `check` again.
  Run it in the directory you run `bpmn check` and `compile` from: it records into `./.flow-sdk/resources.json` there, which is where they read it.
<!--skill-flavor:sdk-upgrade:start-->
  Needs `@uipath/maestro-builder-sdk` 6.73.0 or later; an older SDK refuses `{ name, folder }` and has no key-less `prepare`, so upgrade with `npm install -g @uipath/maestro-builder-sdk@latest`.
  If `uip maestro registry prepare --entity …` answers `missing required argument 'connector-key'`, the `uip` in use predates key-less `prepare`: run the same command as `npx flow-sdk registry prepare --entity …`.
<!--skill-flavor:sdk-upgrade:end-->
  With no `folder`, `prepare` searches every folder: it records a single match and names the folder to pin, and lists several without picking one.
- `entity.folder` is the folder holding the ENTITY; the `folder` option stays the folder holding the CONNECTION.
  They are often the same folder and are still two options.
- The record operations (`create`, `update`, `get`, `query`, `delete`) then write the connector's `_V3` operation (`CreateEntityRecord_V3`, …) as a V1 task with `entityScope=folder`, `folderEntityName` and `folderEntityName_folderKey` query rows, plus the entity's two `Entity` bindings.
  Only `_V3` takes a folder, and Studio Web's V2 catalog does not list it, so this task stays V1.
  A tenant entity's record operations are V2 tasks on the curated operations (`CreateEntityRecordCurated`, `UpdateEntityRecordV2`, `GetEntityRecordByIdCurated`, `QueryEntityRecordsCurated`, `DeleteEntityRecordCurated`), with the entity in the `pathParameters` row.
<!--skill-flavor:folder-entity-resources:start-->
  Run `uip maestro bpmn refresh <project>` after `compile`, then, when the project has a solution, `uip solution resources refresh --solution-folder <SolutionDir>` (the folder holding the `.uipx`, `<Name>Solution/` in the default scaffold): the first turns the two bindings into the entity's row in `bindings_v2.json`, and the second declares the entity in the solution.
<!--skill-flavor:folder-entity-resources:end-->
  Do not hand-fill the task through `.activity()`, and do not pass a folder entity's name as a plain `entity` string: that writes the tenant-scope operation, which validates but does not address the folder entity.
- `entity: { name, folderKey }` is for a folder key already in hand.
  It writes no `Entity` bindings, so `bpmn refresh` does not declare the entity in the solution; prefer `{ name, folder }` even with a key in hand.
  A decompiled process shows a `{ name, folder }` task as an `.activity()` with its query rows and its two `Entity` bindings; it compiles back as it is.
- The file operations (`downloadFile`, `uploadFile`, `deleteFile`) refuse a folder-scoped entity; there is no SDK form for them yet.
  Tell the user the file operation is not supported on a folder-scoped entity; do not fall back to a plain entity name, which addresses a tenant-level entity instead, or hand-fill `.activity()`.
- The entity and its folder are literals in the compiled task: the two `Entity` bindings declare the entity in the solution, and the task does not read them.
  Do not add bindings by hand or promise per-environment re-pointing; tell the user the entity is fixed at compile time.

<!-- RULE:bpmn.connector.parameter-rows -->
- `.connector()`, `.dataService()`, `.eventTrigger()` and `.waitForEvent()` write a V2 task (`activityConfigurationVersion: v2`), the shape Studio Web's connector panel saves and `uip maestro bpmn registry get --input-details` builds.
<!--skill-flavor:sdk-v2-connector:start-->
  Needs `@uipath/maestro-builder-sdk` 6.84.0 or later; an older SDK writes a new `.connector()` task with one `target="path"` / `target="query"` row per parameter and an `operation` context row, so upgrade with `npm install -g @uipath/maestro-builder-sdk@latest` and compile again; do not hand-convert its rows.
<!--skill-flavor:sdk-v2-connector:end-->
  Its path parameters are one json row, `pathParameters` (`target="pathParameters"`), and its query parameters another, `queryParameters` (`target="queryParameters"`), each keyed by the library's own parameter names (`send_as`, not `sendAs`); the request body is the one json `target="body"` row, and a multipart file part is its own `target="file"` row.
  `.dataService()` has two exceptions, which it still writes as V1 tasks: the file operations (`downloadFile`, `uploadFile`, `deleteFile`), whose `_V3` operations have no field-name parameter, and every record operation on a folder-scoped entity (see the folder-entity rule above).
- An imported process can also carry V1 tasks, with one `target="path"` / `target="query"` row per parameter and an `operation` context row.
  Leave them as they are: a task you add beside them is V2, and a file may mix the two.
  Leave the process-level `uipath:intsvcActivityConfig` marker as you found it, as `registry get --input-details` instructs: a new workflow from `bpmn init` has it, and an existing workflow without it needs none.
  Do not add it to an existing workflow: Studio Web would then read every unversioned V1 task in the file as V2.
- Through `.activity()`, copy the `<uipath:context>` rows of the element `registry get --input-details` returns (`Data.V2.ElementXml`), `activityConfigurationVersion: 'v2'` included; see [§4 of the connectors reference](connectors.md#4-when-the-connector-is-not-in-the-library).
  A request field goes in `inputs: { field: value }` and is folded into the body row (`inputs: { script }` on a JDBC query becomes `{"script": …}` in the body); path and query parameters go in `inputs: { pathParameters: { … }, queryParameters: { … } }`, which become the two json rows.
  `inputRows`, when present, replaces `inputs`: spell every row, the body row included (`{ name: 'body', type: 'json', target: 'body', body: { script } }`), or the request fields are silently dropped.
  Give each row its `target`: a row without one is never sent, and `check` refuses it (`CONNECTOR_INPUT_ROW_NO_TARGET`).

## Registry extension types

<!-- RULE:bpmn.activity.escape-hatch -->
- Use `.activity(id, 'Type.Name', opts)` for any registry extension type with no
  typed method. Prefer a typed method when one exists.

<!-- RULE:bpmn.activity.discover-type -->
- Find the type name with `uip maestro bpmn registry search <term> --output json`,
  then `registry get <Type.Name> --output json` to read its context and input
  fields. The SDK's typed methods cover only the types in its committed snapshot,
  so a type absent from them is not evidence the platform lacks it — ask the
  registry before concluding a node cannot be authored.

<!-- RULE:bpmn.activity.two-registries -->
- **This is not the connector library.** `uip maestro bpmn registry` serves the
  `uipath:*` EXTENSION TYPES; `uip maestro registry` (no family word) serves the
  Integration Service OPERATIONS. A connector key passed to the first answers
  `Extension type not found`, which is correct and is not evidence the connector is
  missing. The caches are separate and pulling one does nothing to the other. See
  [`connectors.md`](connectors.md).

<!-- RULE:bpmn.activity.registry-freshness -->
- `registry search` and `registry get` answer from a local cache that does not
  refresh itself. Run `uip maestro bpmn registry pull --force` first whenever a
  type may be newer than that cache, or a real type reads as missing.

<!-- RULE:bpmn.activity.inline-spec -->
- A type the registry does not describe at all (`registry get` answers "Extension
  type not found") is still emittable: pass its emission spec inline,
  `.activity(id, 'Type.Name', { spec, context, inputs })`, where `spec` is a
  `RegistryTypeSpec` — the BPMN element and `uipath:*` tag, the context fields
  with their types and defaults, the payload `inputPattern`, and the output row.
  The spec is used as is, in place of the snapshot and the tenant.
  `decompile` writes one for an imported node whose type the registry does not
  list. It reads it off the file: the element and the payload tag, with no
  context fields, inputs or output for the builder to add, and every
  `contextRows` / `inputRows` / `outputRows` row spelled out beside it. Leave the
  `spec` as decompile wrote it. Editing a row's value is fine; the row is written
  exactly as it reads. The spec does not say which fields the type needs, so for a
  new node of that type, write the full spec.
<!--skill-flavor:sdk-inline-spec:start-->
  Needs `@uipath/maestro-builder-sdk` 6.85.7 or later.
  An older SDK refuses the type at decompile with `BPMN_TYPE_UNKNOWN`, so upgrade
  with `npm install -g @uipath/maestro-builder-sdk@latest`.
<!--skill-flavor:sdk-inline-spec:end-->

<!-- RULE:bpmn.activity.offsnapshot-resolve -->
- You do not have to transcribe the shape by hand: a type outside the SDK's
  snapshot is resolved from the registry at compile time. The build warns that it
  needed a tenant and names the snapshot refresh — report that warning rather
  than suppressing it, because until the snapshot is refreshed that project no
  longer compiles offline.

## Brownfield editing

<!-- RULE:bpmn.brownfield.merge -->
- For a targeted edit, decompile the original, edit the source, then `merge` the edit into the original.
  A bare recompile rewrites untouched elements and drops original layout; `merge` emits every element the edit did not touch from the original byte for byte.

<!--skill-flavor:brownfield-merge-form:start-->

  ```bash
  uip maestro bpmn decompile <Project>/<Name>.bpmn -o <Name>.bpmn.ts --style nested
  # edit <Name>.bpmn.ts, then run check --source --baseline <Project>/<Name>.bpmn until no (edited) error is left
  # (bpmn.brownfield.check-baseline)
  uip maestro bpmn merge <Name>.bpmn.ts --original <Project>/<Name>.bpmn
  ```

  `merge` writes the result over `--original`, so pass no `-o`.
  Line 1 of the `.bpmn.ts` is the stamp `decompile` writes (`// @decompiled-from … sha256:…`): it records a hash of the source decompiled from the original and the decompile options, and `merge` reads them, so do not edit or remove that line and pass `merge` no decompile options.
  To fix the source after a merge, edit the same `.bpmn.ts` and merge again, also after `format`: `merge` restamps it for the merged file, and the check ignores what decompile does not read, such as the layout `format` rewrites and line endings.
  When `merge` refuses with `MERGE_ORIGINAL_CHANGED` (the original's process changed since the decompile), `MERGE_SOURCE_NOT_STAMPED` or `MERGE_SOURCE_STAMP_UNREADABLE` (line 1 is missing or edited), it writes nothing: decompile the original again and reapply the edit.
  On `MERGE_OPTION_CONFLICT`, drop the decompile option given to `merge`; the stamp already records it.
  Needs `@uipath/maestro-builder-sdk` 6.95.0 or later; on an older SDK `merge` stops with a ConfigError asking for an upgrade, so run the install command the ConfigError prints and merge again.
<!--skill-flavor:brownfield-merge-form:end-->
  Then `format` (only when the edit added elements; see `bpmn.brownfield.format`), `refresh` and `validate` the target as in the validation loop.

<!-- RULE:bpmn.brownfield.check-baseline -->
- Check only what you changed: pass the original `.bpmn` to `check` as `--baseline`.
  Without it, `check` judges the whole process, so a defect the original already has on an element you did not touch fails every edit.
  For instance, an import whose connector tasks name no connection gets one `INTSVC_CONNECTION_MISSING` error per task, and a one-word fix in a script task can never get a clean check.
  With `--baseline`, `check` decompiles the original, checks it the same way, and marks each finding:

  ```text
  $ uip maestro bpmn check <Name>.bpmn.ts --source --baseline <Project>/<Name>.bpmn
    ✗ [EXPR_UNDECLARED_REF] in scriptTask "Task_A" input: Expression references `vars.ghost`, ... (edited)
    ⚠ [INTSVC_CONNECTION_MISSING] "Activity_x" (Intsvc.ActivityExecution) names no connection ... (pre-existing, not counted)
  check: 1 error(s) in edited elements, 0 pre-existing SDK defect(s), 1 pre-existing warning(s).
  ```

  - **`(edited)`** (with `--output json`, `Origin: "edited"` under `Data.Diagnostics`; each finding's `NodeId` names its element): fix it. It is on an element you changed or added, or on an untouched element your edit broke (the original does not have it). A renamed element is a new element: its findings count. The exit code is 1 only while one is left.
  - **`(pre-existing, not counted)`**: the original already has it, on an element you did not change. It is a warning. Leave it unless the user asked you to fix it.
  - **`(pre-existing)` worded as a probable SDK defect** (`Class: "lowering"`): `compile` cannot write that element, so `merge` refuses too and the edit cannot be finished. Stop, do not edit the element to get around it, name the element, and tell the user it is a probable SDK defect to report at <https://github.com/UiPath/builder-sdk/issues>.
  - **`CHECK_INCOMPLETE`**: check stopped at a refusal about the whole process (two elements with one id), so the rest was not judged. Fix that refusal first, even if the original has it, then check again.

  "Unchanged" means the element builds the same from your source as from a fresh decompile of the original, payload included; wiring is not part of it. So keep line 1 of the `.bpmn.ts` (the decompile stamp): `check` decompiles the original with the options it records.
  Pass the original, not a compiled baseline. On the first `check` of an unedited decompile, every finding is pre-existing, so run that one without `--baseline` when you need to see the original's own problems.
<!--skill-flavor:sdk-check-baseline:start-->
  Needs `@uipath/maestro-builder-sdk` 6.97.0 or later and a `uip` that declares `--baseline` on `bpmn check` (the release with UiPath/cli#6080). `error: unknown option '--baseline'` comes from `uip` itself: an older `uip` rejects the flag before it loads any SDK, so upgrade `uip`, not the SDK. Until then, run `check --source` without `--baseline` and fix only the errors on elements you changed. A `uip` that has it refuses an older SDK with a ConfigError naming `--baseline on bpmn check`: run the install command the ConfigError prints, then check again.
<!--skill-flavor:sdk-check-baseline:end-->

<!-- RULE:bpmn.brownfield.nested-style -->
- `bpmn decompile --style nested` lifts an import's boundary events, gateways and event sub-processes into the nesting constructs, writes the top level in `flowMode('sequence')`, and prints why each region it left flat stayed flat; the lifted source is written only after it has been compiled and its graph verified identical to the flat form's. The flow ids the constructs imply are KEPT: each is pinned back with `.flowIds([{ source, target, id }])`, emitted once at the top of the chain, so the recompiled artifact carries the ids it arrived with. This is what makes the lift safe for brownfield editing — `uip maestro bpmn merge` keys every process child by id with no filter for kind, so renaming a flow made the merge treat it as new, delete the original along with its `BPMNEdge`, and leave an untouched gateway's `default` naming an id that no longer exists (`MISSING_CONDITION_EXPRESSION` at validate). Measured on a three-flow fixture, a no-edit round trip now merges back byte-identical. `--keep-flow-ids` confines the lift to regions whose ids already match the derived form, for source with no pin table.
  A flow id that is not `Flow_<source>_<target>` keeps its region flat; the graph, its ids and `merge` are unaffected either way, so the choice is about the source you read and edit, not the artifact.

<!-- RULE:bpmn.brownfield.connector-lift -->
- Whenever a library opens (`--library <dir>`, else the `registry pull` cache, with `--connectors-local <dir>` as the prepared overlay on top), `bpmn decompile` LIFTS an `Intsvc.ActivityExecution` task the library can name into the `.connector(key, action, inputs, { connection, folder, outputVar, errorVar, outputs })` call an author writes, and keeps the rest as the verbatim `.activity()` with `contextVerbatim` and a `metadata` blob, printing the reason for each (`decompile: connectors — lifted 6 to .connector(); verbatim: Activity_mrv8tl (body field "Status" is not in the library …)`).
  Only a V2 task (`activityConfigurationVersion: v2`) is lifted, because `.connector()` writes V2; a V1 task stays the verbatim `.activity()` (reason: `a V1 connector task, kept verbatim so it stays V1`), so a no-edit round trip does not convert it.
  A lift is written only after that one call has been compiled on its own and its task compared with the original, so a lift that lost an input or picked the wrong action is refused per element, not approximated.
  The lifted form is the one to copy when adding a connector task to an import. What stays verbatim: a body field the static library does not declare (a Data Fabric update's entity columns; `registry prepare` loads them), a `connection` that is not a `=bindings.<id>` reference, a designer row with an attribute no option spells. A lifted task's variables keep the file's own `jsonSchema` declaration as an explicit `.vars([…])` entry rather than a row the call no longer has.
  A lifted task's canvas metadata is regenerated on compile, so a no-edit round trip through `merge` is not byte-identical for those tasks; `--connectors verbatim` keeps every task as written, for a byte-identical brownfield edit. `examples/InvoiceApproval.bpmn.ts` shows both forms side by side.
  That file was decompiled before the lift became V2-only: its six `.connector()` calls came from V1 tasks and now compile to V2 tasks beside the six verbatim V1 ones, while a fresh decompile of the same export keeps all twelve verbatim.

<!-- RULE:bpmn.brownfield.unused-bindings -->
- `bpmn decompile` DROPS a binding nothing references, and names what it dropped. The
  designer writes a binding pair every time a resource is picked and collects none of
  them, so a real export accumulates rows no `=bindings.<id>` reads — 298 of 528 across
  the exports measured, including four `folderPath` rows for one queue. They are not
  inert: a binding with no `value` is unresolved, so each one is reported missing and a
  dispatching run refuses to start, and the canvas offers no way to delete one. The
  cleanup reaches the tenant through `uip maestro bpmn merge`, which takes the process
  extension block from the edited source. Pass `--keep-unused-bindings` to `decompile`
  when you need the decompiled source to match the original row for row instead.

<!-- RULE:bpmn.brownfield.palette-elements -->
- How `bpmn decompile` writes the palette elements that carry no `uipath:*` payload:
  - a complex gateway becomes `.complexGateway(id, { name, default })`;
  - a bare call activity becomes `.plainTask(id, { element: 'bpmn:callActivity' })`.
    Do not author it: `validate` rejects it and `check` reports `CALL_ACTIVITY_NO_PAYLOAD`.
    To call a process, use an `Orchestrator.Start*Process` type through `.activity()`, with
    a process binding;
  - data objects, data object references and data store references are left out of the
    source. A header comment that starts `// DATA ELEMENTS LEFT TO THE ORIGINAL` lists
    each one; keep it. Merging the edit (`bpmn.brownfield.merge`) keeps them from
    the original, with their data associations and shapes. A bare `compile` drops them.

<!--skill-flavor:sdk-palette-elements:start-->
  Needs `@uipath/maestro-builder-sdk` 6.88.1 or later; an older SDK refuses every
  element above with "has no builder equivalent", so upgrade with
  `npm install -g @uipath/maestro-builder-sdk@latest` and decompile again.
<!--skill-flavor:sdk-palette-elements:end-->

  Decompile still refuses a complex gateway with an `activationCondition` and a bare call
  activity with a `calledElement`. The refusal names the attribute and the next step: the
  Maestro runtime does not read `activationCondition`, and the platform ignores
  `calledElement`, so removing either one from the source `.bpmn` does not change what the
  process does. Tell the user, remove the attribute, and decompile again. A bare call
  activity then decompiles to the round-trip form above and still fails `validate` with
  `CALL_ACTIVITY_NO_PAYLOAD`; to make it call a process, give it an
  `Orchestrator.Start*Process` type with a process binding.

<!-- RULE:bpmn.brownfield.format -->
- Format after adding elements that need diagram shapes. Avoid formatting a
  metadata-only edit because it replaces preserved geometry.

## Contract metadata

<!-- RULE:bpmn.metadata.case-management -->
- A process-level `uipath:caseManagement` marker is distinct from a typed
  `Orchestrator.StartCaseMgmtProcess` or `Orchestrator.StartCaseMgmtProcessAsync`
  call activity. When a contract or fixture explicitly requires that marker,
  author it with synthetic content through
  `.metadata({ caseManagement: { version: 'v1', value: '{"mode":"preserve-only"}' } })`.
  A case-process call does not emit or replace the marker.

## Packaging and layout

<!-- RULE:bpmn.package.derived -->
- Treat project metadata as derived from the BPMN. `project.uiproj` and
  `operate.json` use the bare filename; `entry-points.json` adds `#<start-id>`;
  `package-descriptor.json` uses a top-level `content` array.

  Every root start event compiles with a `uipath:entryPointId`: the one you set, else a
  stable GUID the SDK derives from the process and start-event ids (the same on every
  compile and machine; it changes if the process or start id changes, so when renaming
  either in a deployed process, pin the old id). `refresh` reads it from the BPMN to
  write `entry-points.json`, so nothing is required before `.startEvent('<start-id>')`.
  To keep the id `bpmn init` assigned, decompile the stub it wrote (the id is carried
  into the seed) or declare `.metadata({ entryPointId: '<uuid>' })`; a second root start
  takes its own on the event (`.startEvent(id, { entryPointId })`), and `false` writes
  none. A value you set must be a
  GUID — `validate` refuses any other (`Root start event uipath:entryPointId value …
  must be a GUID`), and `check` reports `ENTRYPOINT_ID_NOT_GUID` first. Then generate the files from the built BPMN:

  ```sh
  uip maestro bpmn refresh <project-dir> --output json   # `Demo/` here; needs its project.uiproj
  ```

  `Data.WrittenFiles` names the files that were stale. Do not use the deprecated
  `update-metadata`: it does not materialize `Intsvc.*` connection bindings, so a
  package it wrote passes `validate` and faults at run time.

  For `Demo.bpmn` with root start event `start`, the minimal derived values are:

  ```jsonc
  // project.uiproj
  { "name": "Demo", "main": "Demo.bpmn", "designOptions": { "projectType": "ProcessOrchestration" } }
  // operate.json
  { "main": "Demo.bpmn", "contentType": "ProcessOrchestration" }
  // entry-points.json
  { "entryPoints": [{ "filePath": "/content/Demo.bpmn#start", "input": [], "output": [] }] }
  // bindings_v2.json
  { "version": "2.0", "resources": [] }
  // package-descriptor.json
  { "content": ["content/Demo.bpmn", "content/bindings_v2.json", "content/entry-points.json", "content/operate.json"] }
  ```

  Inspect every generated metadata file against this contract. In particular,
  `entry-points.json.entryPoints` must be non-empty and reference the built BPMN
  plus its start id. If it is empty, do not hand-write the JSON: the BPMN was not
  compiled by the SDK and its root start event has no `uipath:entryPointId`; fix the
  source, rebuild, and rerun `refresh`. `refresh` refusing with `Expected one
  uipath:entryPointId on root manual start event` means an `entryPointId: false` on that
  start (from decompiling an id-less import): delete it and rebuild.

<!-- RULE:bpmn.layout.separate -->
- Compile emits semantic XML. Run `uip maestro bpmn format` only when a canvas
  layout is required.

## Product boundary

<!-- RULE:bpmn.validation.layers -->
- TypeScript checks call shape, `bpmn check` checks graph semantics, and
  `uip maestro bpmn validate` checks the compiled product contract. A live run
  is still required for tenant resources and runtime outcomes.
