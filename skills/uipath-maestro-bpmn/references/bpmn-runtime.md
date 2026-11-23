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

<!-- RULE:bpmn.variables.output-end-mapping -->
- A process returns only what its end event maps. A task that writes an `.output()` variable
  directly (`outputs: { score: '…' }`) sets it inside the run, but the caller and the job receive
  `null`: validate passes and the run completes, so only a Maestro debug run shows it; local
  `flow-debug` does not ([offline checks](operate.md#debug--a-controlled-studio-web-run)). Compute into a `.var()`
  and map it onto the output at each end event that finishes the process, the canvas's shape:
  ```ts
  .output('score', 'number')
  .var('scoreValue', 'number')
  // … tasks write scoreValue …
  .endEvent('done', { payload: { type: 'BPMN.Variables', outputRows: [
    { name: 'score', type: 'number', source: '=js:vars.scoreValue', var: 'score' },
  ] } })
  ```
  Never read an `.output()` before its end event; read the `.var()` instead.

<!-- RULE:bpmn.variables.public-types -->
- A public `.input()` / `.output()` takes `string`, `boolean`, `integer`, `number`,
  `array` or `object` (`refresh`'s error also names `json`, but the SDK has no `json`
  type: `check --source` fails with `TS2345`). `double` and `float` pass `check`, `compile` and
  `validate`, then `refresh` fails with `Unsupported process input/output type "double"`:
  write `number`. `double` on a `.var()` or a node's output row is fine.

<!-- RULE:bpmn.variables.reserved-names -->
- `validate` and `refresh` reject a `.var()` or `.input()` whose display `name` (the id,
  unless `name` is given) is one of these, matched case-insensitively
  (`RESERVED_VARIABLE_NAME`): `vars`, `iterator`, `metadata`, `bindings`, `datafabric`,
  `instanceglobals`, `orchestrator`, `outputs`, `result`, `runtime`, `senderinfo`,
  `this`. `check` does not report it. A public `.output()` may be named `result`.

<!-- RULE:bpmn.variables.inputs-through-start -->
- A process input belongs to the start event, so a later step that reads `vars.<inputId>` is
  "A variable is unresolved" on the canvas, and `validate` passes with at most a
  `VARIABLE_NOT_SET` warning: fix it, never wave it off. On the start event, map each input the
  steps read into a variable scoped to that event, as the canvas does, and read that variable
  downstream. When the start event already maps the input (a
  canvas-made process), read that row's `var`; add no second row.
  ```ts
  .input('amount', 'number')
  .var('amountIn', 'number', { elementId: 'start' })
  .var('total', 'number')
  .startEvent('start', { payload: { type: 'BPMN.Variables', outputRows: [
    { name: 'amount', type: 'number', source: '=vars.amount', var: 'amountIn' },
  ] } })
  .task('double', { set: { total: '=js:vars.amountIn * 2' } })
  ```
  Unlike a task's output row, a start-event row does not declare its variable: without the
  `.var()`, `check` fails `EXPR_UNDECLARED_REF`.

<!-- RULE:bpmn.expression.js-everywhere -->
- Write every expression you author as `=js:` JavaScript, in any field: `set`, a `when`, a row
  `source`, a connector input, a loop `collection` or `completion`, a timer `date`
  (`'=js:vars.total * 0.9'`, `'=js:vars.tier == "gold"'`). A plain `=` passes `check`, `compile` and
  `validate`, but it is C#: the designer opens any plain expression beyond a bare variable read in its
  C# editor, and a JavaScript method in it (`=vars.d.toLowerCase() == "approve"`) faults the run
  (incident `400302`), or in a gateway `when` evaluates `false` and takes the wrong branch. Local
  `flow-debug` does not show this ([offline checks](operate.md#debug--a-controlled-studio-web-run)).
  Leave plain only what the canvas writes plain: a row `source` reading the node's own result
  (`=result…`, `=response…`, `=Error`, a form field such as `=Action`, an agent output such as
  `=Decision`), `=bindings.<id>`, `=iterator[0]`, the start-event row that maps a process input
  (`=vars.<inputId>`), and a human-task form field's `value` (`=vars.<id>`: its runtime evaluates
  UiPath expressions, not JavaScript). An imported file's existing plain `=` expressions are C#
  (`examples/InvoiceApproval.bpmn.ts`): leave them as they are, and copy none of them.
  In a plain `=` you keep or edit, `.length` reads back `null` with no incident: use `.Count`.
  `.length` works only inside `=js:`.
- A `.task()`'s `set` values are strings: an `=js:` expression or a literal. `set: { done: true }`
  fails `check` (`TS2322`) and `compile` (`value.startsWith is not a function`); write `'=js:true'`.

<!-- RULE:bpmn.variables.input-name -->
- Input values are matched to declarations by display `name` when a run starts, so an
  input given a `name` (`.input('amount', 'number', { name: 'Amount' })`) is supplied
  under `Amount`. Leave `name` off unless the caller's key is meant to differ from the id.

<!-- RULE:bpmn.variables.node-output-declares-itself -->
- **Do not declare a variable for a node's own output.** An output row declares the
  variable it fills: the compiler derives a declaration from the row, attributed to that
  node, with the row's `name` and `type`. Writing a `.var()` beside the node for the
  same id states the same thing twice and makes it the author's declaration instead of
  the node's. A start-event row is the exception: it does not declare its variable, so
  its `.var()` stays (see `bpmn.variables.inputs-through-start` above). Where the
  variable carries a JSON Schema, put it on the ROW as `varSchema` — the platform writes
  the shape on the declaration and not on the row, so `varSchema` is what reaches it:

  ```ts
  outputRows: [{ name: 'response', type: 'jsonSchema', var: 'act_response',
                 source: '=result', varSchema: 'responseSchema' }]
  ```

  Reserve `.var()` for process-level state nothing fills for you. In the real exports
  measured, 688 of 842 declarations are a node's own output and the product marks only
  the author's with `custom="true"`.

<!-- RULE:bpmn.variables.element-id-is-placement -->
- `elementId` is placement to the runtime and scope to the canvas. The runtime seeds
  every declaration into one flat namespace and resolves `vars.<id>` there whatever it
  says, and an id is unique across the whole document — so two elements cannot each own
  a `response`. What it decides is which element the declaration BELONGS to, which is
  what the canvas and `uip maestro bpmn validate` read (1.203 requires one). For a
  process input, see `bpmn.variables.inputs-through-start`.

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

<!-- RULE:bpmn.script.ts-string-escapes -->
- A `script` (and any `=js:` value) is a TypeScript string, so TypeScript reads its escapes before the runtime does, whatever the quotes: `\n` inside a quoted (`'…'`/`"…"`) string in the script becomes a real newline and the run faults `300501` "Invalid or unexpected token" though `check` and `validate` pass; `\d` in a regex silently becomes `d`.
  Double every backslash the script needs (`\\n`, `\\d`); inside backticks also escape `\${` and `` \` ``.

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
  The row is spelled as the platform's script-task template writes it. A live run of a failing script filled it with an object whose keys are PascalCase (`Code`, `Message`, `Detail`, `Category`, `Status`, `Element`), unlike a boundary's `errorVar` capture (`code`, `message`, …), so read `vars.score_Error.Message`.

## Events and timers

<!-- RULE:bpmn.event.payload-live -->
- Connector event payloads and timer firing are runtime facts. Static validation
  proves the declaration, not that a tenant subscription fires.

<!-- RULE:bpmn.event.timer-units -->
- Write a timer duration in days, hours, minutes and seconds: `P7D`, not `P1W`.
  The runtime parses no week, month or year designator, so such a timer fails at run
  time while `check` and `validate` only warn (`TIMER_DURATION_NOT_RUNTIME_PARSEABLE`,
  `TIMER_DURATION_WEEK_UNSUPPORTED`). Treat either warning as an error.

<!-- RULE:bpmn.event.net-scope -->
- An event sub-process catches only failures raised in the container it sits directly in.
  Declared at process level it ends the whole run on the first failure; declared inside a multi-instance sub-process it ends only that iteration.
  Place `.eventSubProcess()` in the scope whose failure it should absorb.

<!-- RULE:bpmn.activity.retry -->
- Retry is activity configuration: `retry: { maxRetries, backoff, backoffType, exponentialBase, maxDuration, allErrors }` on the activity.
  It compiles to `<uipath:retry maxRetryCount retryBackoff …>` in the activity's extensions, the same setting as Studio Web's Error handling → Retry. `maxDuration` caps each delay, not the total time.
  Which failures it retries: `allErrors: true`, only when every failure of that step is transient, because it also retries business errors; else the `errorMapping` rows with `retryable: true`. With neither it retries nothing.
  An `errorMapping` row's `code` is the **id of a declared `bpmn:error`**, whose `errorCode` the engine matches against the failure's code (for an HTTP or connector call, the status as a string, `"429"`), not the code itself: `code: '429'` passes `check` and `validate` and retries nothing.
  To retry one status, declare it with a boundary, `t.onError({ name: 'RateLimited', code: '429' }, { id: 'onRateLimit' }, …)`, which also catches it once retries run out; compile, read the declaration's id from the `.bpmn` (`<bpmn:error id="Error_1" … errorCode="429">`, numbered in declaration order), set the row's `code` to that id, and compile again.
  An HTTP or connector call's 5xx is already retried 3 times inside the engine before the element fails; a 4xx such as 429 never is.
  Never draw a retry loop for a failing activity. A `.goto()` that re-runs a whole business block, such as a parallel block ([Draft skeleton](draft-skeleton.md)), is a process step, not a retry.

<!-- RULE:bpmn.event.error-context -->
- The engine surfaces a failed element's error under the capital-`Error` key. A boundary's `errorVar` capture and an event sub-process's capture (once parsed) carry lowercase fields (`code`, `message`, `detail`, `category`, `status`, `response`, `element`); a script task's `Error` row is PascalCase (see [Script tasks](#script-tasks)); other tasks' `Error` rows are unverified.
  `.eventSubProcess({ error: true })` captures it on its start event by default, into `vars.<net>_Error` — a per-net id, which is how the designer names one: every error capture in the measured exports has a unique id with the display name `Error`, and the bare `vars.Error` appears in none. So a net called `failures` captures `vars.failures_Error` with nothing more written; `errorVar` names it something else and `errorVar: false` omits the capture.
  The engine always stores an event sub-process's capture, the default `<net>_Error` or one renamed with `errorVar` (the same `=Error` row), as a JSON **string** (the net start's `=Error` row reads the serialized payload), so parse it before reading a field: `=js:JSON.parse(vars.failures_Error).message`, and in a script `JSON.parse(vars.failures_Error).code`. A plain `vars.failures_Error.message` reads undefined, and a condition on it always takes the other arm. Read a boundary's `errorVar` capture and a script task's `Error` row directly; neither is a string. `vars.Error` never resolves.
  The platform validator needs the declaration: a `vars.<id>` read with no captured variable is `VARIABLE_DOES_NOT_EXIST`, in a net or anywhere else. Note the runtime resolves `vars.<id>` in ONE flat scope whatever a declaration's `elementId` says, so two captures cannot share an id — that is why the default is per-net.
  A boundary handler captures nothing by default; there `errorVar` is what makes the error readable.

<!-- RULE:bpmn.event.non-interrupting-path -->
- A non-interrupting boundary handler runs beside a token that still reaches the next step, so its path must end on its own; rejoining the main path would run everything after it twice.
  The builder refuses a non-interrupting handler path left open.

## HTTP and Orchestrator work

<!-- RULE:bpmn.http.webhook-url -->
- A request that must reach a connection's webhook (to fire a `waitForEvent` on an HTTP Webhook connection, say) is a manual `.http()` with the webhook URL as a literal `url` and no `connection`: `.http('ping', { url: '<WEBHOOK_URL>', method: 'GET' })`.
  Get the URL from `uip is webhooks config <CONNECTOR_KEY> --connection-id <CONNECTION_ID> --output json`: it is `Data.WebhookUrl`.
  Never use `uip is connections base-url` for it; that is the connection's API base, a different address, so the event never arrives.
  If `webhooks config` fails with `has no element instance id`, check the id and the connector with `uip is connections list <CONNECTOR_KEY> --output json`.
  Only a connection of the HTTP Webhook connector (`uipath-http-webhook`) can fire this event.

<!-- RULE:bpmn.orchestrator.names -->
- Published work is addressed by name and folder. Queue items require a folder;
  live execution is the evidence that the resource exists and is runnable.

<!-- RULE:bpmn.orchestrator.process-type -->
- Pick the method by the target's `ProcessType`, never by its name or label. Read it with
  `uip or processes list --folder-path <FOLDER_PATH> --all-fields --output json` (the default list omits it):

  | `ProcessType` | Method |
  |---|---|
  | `Agent` (low-code or coded agent) | `.startAgent()` |
  | `Process` (RPA) | `.startProcess()` |
  | `Api` | `.executeApiWorkflow()` |
  | `ProcessOrchestration` | `.startAgenticProcess()` |
  | `CaseManagement` | `.startCaseProcess()` |
  | `WebApp` (an Action App) | `.humanTask()` with an inline form, per [Human tasks](#human-task-outcomes): the SDK cannot yet bind the app |
  | `Flow` | `.activity(id, 'Orchestrator.StartFlowProcess', { context: { name, folderPath } })`, or `…StartFlowProcessAsync` |
  | `Function` (a Coded Function, not an agent) | `.activity(id, 'Orchestrator.ExecuteFunctionAsync', { context: { name, folderPath } })` (Preview) |
  | An agent behind an Integration Service connection | `.externalAgent()`, with its own connection binding |

  This is the mapping Studio Web's resource picker applies. A `ProcessType` not in the table
  cannot be called from a process. Never author `A2A.AgentExecution`: Studio Web no longer
  offers it and shows it only on old nodes.

<!-- RULE:bpmn.orchestrator.in-solution-process -->
- A Maestro BPMN process in the same solution is called without deploying it: bind it by name the
  way Studio Web's picker does, a binding pair with `resourceKey` = the project name and no folder value.
  ```ts
  .binding('childName', { name: 'name', value: 'CreditAssessment', resource: 'process',
    propertyAttribute: 'name', resourceKey: 'CreditAssessment', resourceSubType: 'ProcessOrchestration' })
  .binding('childFolder', { name: 'folderPath', resource: 'process',
    propertyAttribute: 'folderPath', resourceKey: 'CreditAssessment', resourceSubType: 'ProcessOrchestration' })
  // …
  .startAgenticProcess('assess', { process: '=bindings.childName', folder: '=bindings.childFolder',
    input: { annualIncome: '=js:vars.annualIncome' }, outputs: { score: '=result.score' } })
  ```
  The called process must map its outputs at its end event ([output end mapping](#variables-and-the-process-contract)),
  or `result.score` is `null`.
<!--skill-flavor:in-solution-debug:start-->
  Studio Web Debug starts the child project; a local `uip maestro bpmn debug` uploads only this
  project and faults (`[170007] The job's associated process could not be found`), so debug the
  child on its own with the CLI and the pair in Studio Web, and say so.
<!--skill-flavor:in-solution-debug:end-->

<!-- RULE:bpmn.orchestrator.sibling-resource -->
- A resource another skill builds for this process is bound after it is deployed, in this order:
  1. Create its project in the same solution as the process.
  2. Hand its authoring to the owning skill (uipath-rpa, uipath-api-workflow, uipath-agents, uipath-maestro-flow, uipath-functions, uipath-maestro-case) with the
     inputs and outputs the process needs; without that skill, tell the user to build it and stop there.
<!--skill-flavor:sibling-deploy:start-->
  3. With the user's go-ahead, pack the solution with `uip solution pack <SolutionDir> <OutputDir> --version <VERSION> --output json`,
     publish it to the tenant feed as [Orchestrator deployment](operate.md#orchestrator-deployment) does (not a Studio Web upload), then deploy it with
     `uip solution deploy run --name <DEPLOYMENT_NAME> --package-name <PACKAGE_NAME> --package-version <VERSION> --folder-name <FOLDER_NAME> --parent-folder-path <FOLDER_PATH> --output json`.
<!--skill-flavor:sibling-deploy:end-->
  4. Find it with `uip or processes list --all-folders --name <PROCESS_NAME> --all-fields --output json`:
     its folder is `OrganizationUnitFullyQualifiedName` (`--all-fields` omits `FolderPath`) and its
     type is `ProcessType`. Only then write the node with that `process` and `folder`.

  `folder: 'solution_folder'` compiles to a literal folder with no binding, so `bindings_v2.json`
  stays empty; for a Maestro BPMN sibling use the binding pair in `RULE:bpmn.orchestrator.in-solution-process` above instead.
  The owning skill handing the project back is not the end.
<!--skill-flavor:sibling-redeploy:start-->
  A new `deploy run` name deploys to a new folder, so ship the finished solution into the same
  deployment: with the user's go-ahead, pack it with a higher `--version` than step 3's and publish it, then
  `uip solution deploy upgrade --name <DEPLOYMENT_NAME> --package-name <PACKAGE_NAME> --version <NEW_VERSION> --output json`.
  Never run a second `deploy run`: the folder the node names would no longer hold the resource.
<!--skill-flavor:sibling-redeploy:end-->

<!-- RULE:bpmn.orchestrator.job-outputs -->
- A job's output arguments are fields of `result`: map each one with `outputs` on the job node, as in `.executeApiWorkflow('greet', { process, folder, input, outputs: { message: '=result.message' } })`.
  The same `outputs` option reads an RPA process's (`.startProcess()`), an agent's (`.startAgent()`) and a waited-for agentic or case process's (`.startAgenticProcess()`, `.startCaseProcess()` without `async`) output arguments.
  `outputVar` (default `<id>_processResponse`) holds the job envelope, not the arguments; do not read an argument out of it with a `=js:` chain.
  The argument name is the workflow's own output argument, as the deployed process declares it; when no live run has shown it, say the mapping is unverified.

<!-- RULE:bpmn.http.manual -->
- A plain HTTP call with no connection is `.http(id, { url, method, parameters, headers, body })` with no `connection`.
  It writes the request in manual mode with the `ImplicitConnection` binding Studio Web uses, so nothing on the tenant has to exist.
  `outputVar` (default `<id>_response`) holds the response body; `<id>_code`, `<id>_headers` and `<id>_Error` hold the rest.
  Never write a credential (a bearer token, an API key, a password) into `headers` or `url`: it is stored in plain text in the
  `.bpmn` and in Studio Web. Use a connection ([connectors](connectors.md)); when none exists for the API, ask the user.
  When the user insists on a literal, say where it will be visible before you upload.
  `check` warns `HTTP_MANUAL_V1` on the old manual form (`mode="manual"` with the request as context rows), which the runtime faults with 102018 "Body cannot be null"; rewrite it as `.http()` and compile.
<!--skill-flavor:sdk-http-manual:start-->
  Needs `@uipath/maestro-builder-sdk` 6.93.9 or later; an older SDK still writes the old manual form, with `outputVar` holding the whole response and no `HTTP_MANUAL_V1` warning, so upgrade with `npm install -g @uipath/maestro-builder-sdk@latest` and compile again.
  From 6.93.9, `outputVar` is the body, so read `vars.<id>_response.x`, not `vars.<id>_response.body.x`, which read the old form's whole response.
<!--skill-flavor:sdk-http-manual:end-->

<!-- RULE:bpmn.http.connector -->
- An endpoint the connector catalog has no activity for, called through an existing connection, is
  `.http(id, { method, url, connection, folder, connectorKey })`.
  - `url` is the vendor API's own endpoint, relative to the connection's base URL (`uip is connections base-url <CONNECTION_ID> --output json`), such as Slack's `/team.info` under `https://slack.com/api`. Never use an Integration Service resource `Path` from `uip is resources list` or `describe`, which belongs to `.connector()`: the request reaches the vendor as written, so an Integration Service path that differs from the vendor's returns the vendor's 404 (`[102021] Received failure from vendor system`). An absolute URL to another host gets 400 "Invalid request URL" (`check`: `MANAGED_HTTP_ABSOLUTE_URL`).
  - `connectorKey` is the connection's connector key from `uip is connections list --all-folders --output json`; omit it only for a `uipath-uipath-http` connection. A wrong or missing one passes `check` and fails `validate` with `MISSING_BINDING`.
  - `connection` and `folder` name `.binding()`s holding the connection's `Id` and its `FolderKey` (or what `prepare` wrote); `folder` is required (`EMPTY_REQUIRED_FIELD folderKey`).
  - `outputVar` (`<id>_response`) is the body; `<id>_code`, `<id>_headers` and `<id>_Error` hold the rest.

  ```ts
  .binding('gh', { resource: 'Connection', propertyAttribute: 'ConnectionId', value: '<CONNECTION_ID>' })
  .binding('ghFolder', { resource: 'Connection', propertyAttribute: 'folderKey', value: '<FOLDER_KEY>' })
  .http('rateLimit', { method: 'GET', url: '/rate_limit', connection: 'gh', folder: 'ghFolder', connectorKey: 'uipath-microsoft-github' })
  ```

<!-- RULE:bpmn.http.url-placeholders -->
- Fill every `{name}` or `<NAME>` in an HTTP `url` before compiling, with a discovered or given value or an `=js:` expression; never invent one. Nothing checks this: `check`, `compile` and `validate` all pass `/repos/{owner}/{repo}`, and the request goes out literally.

<!-- RULE:bpmn.orchestrator.business-rule -->
- A deployed business rule is `.businessRule(id, { process, folder, input, outputs })`, nothing else.
  The builder writes the version, the `BusinessRule` bindings and the `output`/`Error` rows; do not add them. The result is keyed by decision: a column reads `=result.<decisionKey>.<column>`, as in `outputs: { tier: '=result.eligibility.tier' }` or `vars.<id>_businessRuleResponse.eligibility.tier` downstream, never `=result.tier` or `=response.tier`.
<!--skill-flavor:business-rule-key:start-->
  `<decisionKey>` is the property name under `OutputArguments.properties` in `uip rules describe <RULE_NAME> --folder-path <FOLDER_PATH> --output json` (such as `decision1`), not the entry point's `DisplayName`: a display name reads null. Mapping the whole `=result` into one variable, as the designer does, also works.
  Only a decision-keyed rule (its `OutputArguments` carry `x-uipath-decision-keyed`) fits this row.
<!--skill-flavor:business-rule-key:end-->
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
- A field's `direction` is `input` (shown, `value: '=vars.x'`), `output` (asked; the answer lands in `variable`, default the id) or `inOut` (shown, editable, written back); its `type` is the data type:
  `{ id: 'amount', label: 'Amount', type: 'number', direction: 'input', value: '=vars.amount' }`. `type: 'input'` fails `check` with `TS2322`.
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

<!-- RULE:bpmn.hitl.no-completer-identity -->
- An inline-form task returns only its form fields and `Action`, never who completed it: the
  `hitlTask` object with `CompletedByUser`, `AssignedToUser` and `CompletionTime` comes only from an
  Action App task, which the SDK cannot bind yet. So never build a control on identity (four-eyes,
  "a different approver", an audit "who") from a field the user types. Build the routing, and tell
  the user the identity check needs the task switched to an Action App in Studio Web, or
  enforced by task assignment (assignee groups) in Action Center.

<!-- RULE:bpmn.hitl.task-settings -->
- `title` (the task title), `priority` (`Low`, `Medium`, `High`, `Critical`) and `labels` (a
  string) are the only Action Center task settings `.humanTask()` writes. The Task timer (the task's SLA: reminder, reassign,
  unassign or auto-complete after a time) and the assignee are set in the Studio Web task panel.
  An option such as `Timer` fails `check --source` (`TS2353`); `compile` alone drops it without an error.
  Tell the user to set the SLA in the panel. When the panel shows no Task timer (it sits behind a
  feature flag), or when the process itself must act on the breach (notify a manager), draw a
  non-interrupting `onTimer` in the task's body and call it a process timer, not the task SLA.

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
  `=js:vars.<id>_response.Id`. Map results onto process outputs on the end event
  (`payload: { type: 'BPMN.Variables', outputRows: [{ name, type, var, source:
  '=js:vars.<id>_response' }] }`). Do not hand-fill
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
- The record operations then write the connector's `_V3` operation (`CreateEntityRecord_V3`, …), the only one that takes a folder.
  `create`, `update`, `get` and `query` are the V2 task Studio Web's connector panel saves: `folderEntityName` is a solution-resource picker on the entity's two `resource="entity"` bindings, which the task reads, so a deploy can re-point the entity.
  `delete` is a V1 task with `entityScope=folder`, `folderEntityName` and `folderEntityName_folderKey` query rows, the two bindings beside it; its V2 form cannot be built yet.
<!--skill-flavor:sdk-df-folder-v2:start-->
  Needs `@uipath/maestro-builder-sdk` 6.122.0 or later; an older SDK writes every record operation on a folder entity as a V1 task, which still validates and runs, so upgrade with `npm install -g @uipath/maestro-builder-sdk@latest` and compile again when a V2 task is asked for; do not hand-convert its rows.
<!--skill-flavor:sdk-df-folder-v2:end-->
  A tenant entity's record operations are V2 tasks on the curated operations (`CreateEntityRecordCurated`, `UpdateEntityRecordV2`, `GetEntityRecordByIdCurated`, `QueryEntityRecordsCurated`, `DeleteEntityRecordCurated`), with the entity in the `pathParameters` row.
<!--skill-flavor:folder-entity-resources:start-->
  Run `uip maestro bpmn refresh <project>` after `compile`, then, when the project has a solution, `uip solution resources refresh --solution-folder <SolutionDir>` (the folder holding the `.uipx`, `<Name>Solution/` in the default scaffold): the first turns the two bindings into the entity's row in `bindings_v2.json`, and the second declares the entity in the solution.
<!--skill-flavor:folder-entity-resources:end-->
  Do not hand-fill the task through `.activity()`, and do not pass a folder entity's name as a plain `entity` string: that writes the tenant-scope operation, which validates but does not address the folder entity.
- `entity: { name, folderKey }` is for a folder key already in hand.
  It resolves the same way: `check` prints `uip maestro registry prepare --entity <name> --folder-key <key>`, which records the entity's own key; run it, then `check` again.
<!--skill-flavor:sdk-folder-key:start-->
  If `uip` answers `unknown option '--folder-key'`, the `uip` in use predates the flag: run the same command as `npx flow-sdk registry prepare --entity <name> --folder-key <key>`.
  If `uip` says `--folder-key` needs a builder SDK release that supports it, or `npx flow-sdk` answers `unknown option '--folder-key'`, the SDK predates the flag: name the folder by path with `{ name, folder }` instead, which needs no `--folder-key`.
<!--skill-flavor:sdk-folder-key:end-->
  A folder key written as an `=`-expression cannot be recorded, so it writes the V1 task and declares nothing in the solution; prefer `{ name, folder }`.
  A decompiled process shows a folder-entity task as an `.activity()` with its rows and the entity's two bindings, with or without the connector library: a `.connector()` call would drop the picker, so decompile keeps the task as it is, and it compiles back unchanged.
- The file operations (`downloadFile`, `uploadFile`, `deleteFile`) refuse a folder-scoped entity; there is no SDK form for them yet.
  Tell the user the file operation is not supported on a folder-scoped entity; do not fall back to a plain entity name, which addresses a tenant-level entity instead, or hand-fill `.activity()`.
- Do not add entity bindings by hand: compile writes the pair.
  A V2 task reads it, so its entity can be re-pointed per environment at deploy; a `delete` task's entity is fixed at compile time.

<!-- RULE:bpmn.connector.parameter-rows -->
- `.connector()`, `.dataService()`, `.eventTrigger()` and `.waitForEvent()` write a V2 task (`activityConfigurationVersion: v2`), the shape Studio Web's connector panel saves and `uip maestro bpmn registry get --input-details` builds.
<!--skill-flavor:sdk-v2-connector:start-->
  Needs `@uipath/maestro-builder-sdk` 6.84.0 or later; an older SDK writes a new `.connector()` task with one `target="path"` / `target="query"` row per parameter and an `operation` context row, so upgrade with `npm install -g @uipath/maestro-builder-sdk@latest` and compile again; do not hand-convert its rows.
<!--skill-flavor:sdk-v2-connector:end-->
  Its path parameters are one json row, `pathParameters` (`target="pathParameters"`), and its query parameters another, `queryParameters` (`target="queryParameters"`), each keyed by the library's own parameter names (`send_as`, not `sendAs`); the request body is the one json `target="body"` row, and a multipart file part is its own `target="file"` row.
  `.dataService()` still writes V1 tasks for the file operations (`downloadFile`, `uploadFile`, `deleteFile`), and on a folder-scoped entity for `delete` and for a folder key written as an `=`-expression (see the folder-entity rule above).
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

<!-- RULE:bpmn.activity.discovery-only -->
- **Discovery only.** When the request asks to discover types or save registry evidence before authoring, or says not to author yet, run no `init`, write no `.bpmn.ts`, and read no other reference.
  Save each command's raw JSON, one file per command, in `<EVIDENCE_DIR>`: the directory the request names, else `registry-evidence/` outside `<Project>` (in Studio Web, `/tmp/registry-evidence/`, since nothing under `/solution` may be deleted):

  ```bash
  E=<EVIDENCE_DIR>
  mkdir -p "$E"
  uip maestro bpmn registry pull --output json > "$E/pull.json"
  uip maestro bpmn registry list --limit -1 --output json > "$E/list.json"
  uip maestro bpmn registry search <TERM> --output json > "$E/search-<TERM>.json"
  uip maestro bpmn registry get <TYPE_NAME> --output json > "$E/get-<TYPE_NAME>.json"
  ```

  Run `get` for each type the request needs, then stop and report the type names found.
  When a command answers `"Result": "Failure"`, keep its file as written and report the failure; never replace it with JSON you wrote yourself.

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
  # edit <Name>.bpmn.ts, then run check --source until it is clean
  uip maestro bpmn merge <Name>.bpmn.ts --original <Project>/<Name>.bpmn
  ```

  `merge` writes the result over `--original`, so pass no `-o`.
  Line 1 of the `.bpmn.ts` is the stamp `decompile` writes (`// @decompiled-from … sha256:…`): it records a hash of the source decompiled from the original and the decompile options, and `merge` reads them, so do not edit or remove that line and pass `merge` no decompile options.
  To fix the source after a merge, edit the same `.bpmn.ts` and merge again, also after `format`: `merge` restamps it for the merged file, and the check ignores what decompile does not read, such as the layout `format` rewrites and line endings.
  When `merge` refuses with `MERGE_ORIGINAL_CHANGED` (the original's process changed since the decompile), `MERGE_SOURCE_NOT_STAMPED` or `MERGE_SOURCE_STAMP_UNREADABLE` (line 1 is missing or edited), it writes nothing: decompile the original again and reapply the edit.
  On `MERGE_OPTION_CONFLICT`, drop the decompile option given to `merge`; the stamp already records it.
  Needs `@uipath/maestro-builder-sdk` 6.95.0 or later; on an older SDK `merge` stops with a ConfigError asking for an upgrade, so run the install command the ConfigError prints and merge again.
<!--skill-flavor:brownfield-merge-form:end-->
  Then `refresh` and `validate` the target as in the validation loop; do not `format` it unless `refresh` or `validate` reports `BPMN_PARSE_ERROR` with `No diagrams found`, `MISSING_DI_SHAPE` or `MISSING_DI_EDGE`, or the target was a template or a process the user chose to replace (see `bpmn.brownfield.format`).

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
- Do not lay out a merged process again. `merge` keeps every shape and edge of the
  original where the user put it (it grows a lane, pool or expanded sub-process that has
  no room for a new shape and shifts the shapes below it, and reroutes an existing edge
  whose flow the edit rewired), and draws the shapes of the elements the
  edit added. `format --relayout` lays out the whole diagram again: it keeps pools, lanes
  and colors but moves every shape the user placed. Plain `format` on a CLI whose
  `format --help` lists no `--relayout` lays it out again too, and drops the user's
  pools, lanes, colors and placement.
  Run `format` without `--relayout` only when `refresh` or `validate` reports
  `BPMN_PARSE_ERROR` with `No diagrams found` (the original had no diagram, so there is no
  layout to lose), `MISSING_DI_SHAPE` or `MISSING_DI_EDGE` (an older SDK's `merge`
  draws no shapes for new elements), run
  `refresh` and `validate` again, and, on a CLI without `--relayout`, when the original
  had a diagram (`MISSING_DI_SHAPE` / `MISSING_DI_EDGE`), tell the user that the canvas
  layout was reset.
  A merge into a template that holds only one start event and at most one end event (as
  Studio Web or `init` writes), or into a process the user chose to replace, builds a
  new process: run `format --relayout` (plain `format` where the CLI lacks the flag),
  then `refresh` and `validate` again.

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
- Treat project metadata as derived from the BPMN. `operate.json.main` and each
  `entry-points.json` `filePath` are `/content/<Name>.bpmn#<start-id>`;
  `package-descriptor.json` has a `files` map; `project.uiproj` names no file.

  Every root start event compiles with a `uipath:entryPointId`: the one you set, else a
  stable GUID the SDK derives from the process and start-event ids (the same on every
  compile and machine; it changes if the process or start id changes, so when renaming
  either in a deployed process, pin the old id). `refresh` reads it from the BPMN to
  write `entry-points.json`, so nothing is required before `.startEvent('<start-id>')`.
  To keep the id `bpmn init` assigned, decompile the stub it wrote (the id is carried
  into the seed) or declare `.metadata({ entryPointId: '<uuid>' })`; a second root start
  takes its own on the event (`.startEvent(id, { entryPointId })`), and `false` writes
  none (`decompile` writes `false` for an id-less import; delete it, see below). A value you set must be a
  GUID — `validate` refuses any other (`Root start event uipath:entryPointId value …
  must be a GUID`), and `check` reports `ENTRYPOINT_ID_NOT_GUID` first. Then generate the files from the built BPMN:

  ```sh
  uip maestro bpmn refresh <project-dir> --output json   # `Demo/` here; needs its project.uiproj
  ```

  `Data.WrittenFiles` names the files that were stale. Do not use the deprecated
  `update-metadata`: it does not materialize `Intsvc.*` connection bindings, so a
  package it wrote passes `validate` and faults at run time.

  For `Demo.bpmn` with root start event `start`, `init` plus `refresh` write these
  values (other fields omitted):

  ```jsonc
  // project.uiproj (written by init; refresh leaves it alone)
  { "Name": "Demo", "ProjectType": "ProcessOrchestration" }
  // operate.json
  { "main": "/content/Demo.bpmn#start", "contentType": "ProcessOrchestration", "targetFramework": "Portable" }
  // entry-points.json
  { "entryPoints": [{ "filePath": "/content/Demo.bpmn#start", "type": "ProcessOrchestration",
      "input": { "type": "object", "properties": {} }, "output": { "type": "object", "properties": {} } }] }
  // bindings_v2.json
  { "version": "2.0", "resources": [] }
  // package-descriptor.json
  { "files": { "operate.json": "operate.json", "entry-points.json": "entry-points.json",
      "bindings.json": "bindings_v2.json", "Demo.bpmn": "Demo.bpmn" } }
  ```

  Inspect every generated metadata file against this contract. In particular,
  `entry-points.json.entryPoints` must be non-empty and reference the built BPMN
  plus its start id. If it is empty, do not hand-write the JSON: the BPMN was not
  compiled by the SDK and its root start event has no `uipath:entryPointId`; fix the
  source, rebuild, and rerun `refresh`. `refresh` refusing with `Expected one
  uipath:entryPointId on root manual start event` means an `entryPointId: false` on that
  start (from decompiling an id-less import): delete it and rebuild.

<!-- RULE:bpmn.layout.separate -->
- Compile emits semantic XML with no diagram, and `validate` refuses a file without
  one: `format` every newly compiled process; a merged one only when `refresh` or `validate`
  reports a missing diagram or shape, or it merged into a template or a process the user
  chose to replace (`bpmn.brownfield.format`).

## Product boundary

<!-- RULE:bpmn.validation.layers -->
- TypeScript checks call shape, `bpmn check` checks graph semantics, and
  `uip maestro bpmn validate` checks the compiled product contract. A live run
  is still required for tenant resources and runtime outcomes.
