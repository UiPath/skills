# BPMN runtime decisions

Runtime facts and choices that syntax/static validation cannot establish; exact signatures remain in the generated API. Registry extension types: [bpmn-registry.md](bpmn-registry.md); contract metadata, packaging/layout, validation layers: [bpmn-packaging.md](bpmn-packaging.md).

## Variables and the process contract

<!-- RULE:bpmn.variables.public-scope -->
- Declare the public contract with `.input()`/`.output()`, not `.var()`. Top-level input scopes to the manual start; top-level output scopes to the end event whose mapping writes it (`elementId`); `.var()` is internal state. Use `elementId` only for element scope.

<!-- RULE:bpmn.variables.output-end-mapping -->
- A process returns only what its end event maps. Task `outputs: { score: '…' }` sets execution state but returns `null`; validation/completion pass, Maestro debug reveals it, and local `flow-debug` does not ([offline checks](operate.md#debug--a-controlled-studio-web-run)). Compute in `.var()`, map it at every terminating end event, and read that `.var()` before the event, never `.output()`:
  ```ts
  .output('score', 'number')
  .var('scoreValue', 'number')
  // … tasks write scoreValue …
  .endEvent('done', { payload: { type: 'BPMN.Variables', outputRows: [
    { name: 'score', type: 'number', source: '=js:vars.scoreValue', var: 'score' },
  ] } })
  ```

<!-- RULE:bpmn.variables.public-types -->
- Public `.input()`/`.output()` types are `string`, `boolean`, `integer`, `number`, `array`, or `object`. `refresh` also names `json`, but the SDK has no `json`; `check --source` fails `TS2345`. `double`/`float` pass `check`, `compile`, and `validate` but `refresh` fails `Unsupported process input/output type "double"`; use `number`. `double` is valid for `.var()` and node output rows.

<!-- RULE:bpmn.variables.reserved-names -->
- `validate`/`refresh` reject `.var()`/`.input()` display names (id unless `name` is supplied), case-insensitively, with `RESERVED_VARIABLE_NAME`: `vars`, `iterator`, `metadata`, `bindings`, `datafabric`, `instanceglobals`, `orchestrator`, `outputs`, `result`, `runtime`, `senderinfo`, `this`. `check` does not report it. A job node's `outputs` key and `outputVar` are variable names too: `outputs: { result: '=result.x' }` fails `validate`, and a newer SDK refuses it in `check` (`BPMN_JOB_OUTPUT_VAR_RESERVED`); name the key for its value: `outputs: { message: '=result.message' }`. Public `.output()` may be named `result`.

<!-- RULE:bpmn.variables.inputs-through-start -->
- Inputs belong to the start event; later `vars.<inputId>` is `A variable is unresolved`, and `validate` may warn `VARIABLE_NOT_SET`, which must be fixed. At the start, map each read input into a start-scoped variable and read that variable. If already mapped, read that row's `var` and add no row.
  ```ts
  .input('amount', 'number')
  .var('amountIn', 'number', { elementId: 'start' })
  .var('total', 'number')
  .startEvent('start', { payload: { type: 'BPMN.Variables', outputRows: [
    { name: 'amount', type: 'number', source: '=vars.amount', var: 'amountIn' },
  ] } })
  .task('double', { set: { total: '=js:vars.amountIn * 2' } })
  ```
  A start row does not declare its variable: declare `.var()` or `check` fails `EXPR_UNDECLARED_REF`.

<!-- RULE:bpmn.expression.js-everywhere -->
- Write every expression you author as `=js:` JavaScript, in any field: `set`, `when`, row `source`, connector inputs, loop `collection`/`completion`, timer `date`. Plain `=` passes `check`, `compile`, and `validate` but is C#: beyond bare variable reads it opens the C# editor; JavaScript methods can fault `400302`, and gateway `when` can evaluate false. Local `flow-debug` does not show this ([offline checks](operate.md#debug--a-controlled-studio-web-run)). Retain plain forms only where the canvas writes them: node results (`=result…`, `=response…`, `=Error`), form fields (`=Action`), agent output (`=Decision`), `=bindings.<id>`, `=iterator[0]`, start rows (`=vars.<inputId>`), and human-form `value` (`=vars.<id>`: UiPath expressions, not JavaScript). Imported plain expressions remain C# (`examples/InvoiceApproval.bpmn.ts`): leave them as they are, and copy none of them. In retained plain `=`, `.length` reads `null` with no incident: use `.Count`; `.length` works only in `=js:`. `.task()` `set` values are strings: use `'=js:true'`, not `true` (`TS2322`; otherwise compile reports `value.startsWith is not a function`).

<!-- RULE:bpmn.variables.input-name -->
- Match inputs by display `name`; `.input('amount', 'number', { name: 'Amount' })` is supplied under `Amount`. Omit `name` unless the caller key differs from the id.

<!-- RULE:bpmn.variables.node-output-declares-itself -->
- Do not declare a node's own output with `.var()`; its output row's `name`/`type` declares it. The start still needs `.var()`. Put JSON Schema on the row as `varSchema`, e.g. `outputRows: [{ name: 'response', type: 'jsonSchema', var: 'act_response', source: '=result', varSchema: 'responseSchema' }]`; reserve `.var()` for state not filled by a node.

<!-- RULE:bpmn.variables.element-id-is-placement -->
- `elementId` is runtime placement/canvas scope. Runtime declarations share one flat, document-wide-unique namespace; `elementId` identifies canvas ownership and is required by `uip maestro bpmn validate` 1.203. For inputs see `bpmn.variables.inputs-through-start`.

<!-- RULE:bpmn.variables.array-forms -->
- `.vars([…])`, `.bindings([…])`, and `.schemas([…])` take complete blocks; non-internal entries use `direction: 'input' | 'output'`. Singular `.var()`, `.input()`, `.output()`, `.binding()`, and `.schema()` remain interchangeable. Prefer arrays for more than a handful, as `bpmn decompile` writes them.

<!-- RULE:bpmn.variables.preserve-block -->
- `.preserve({ … })` is source-only state, currently `variableOrder`; `bpmn decompile` writes it. Leave it alone, never add to it; authorable data goes in the typed builder. If declarations change, update every id or delete the call; on a partial list `check` warns `VARIABLE_ORDER_INCOMPLETE`, `VARIABLE_ORDER_UNKNOWN_ID`, or `VARIABLE_ORDER_DUPLICATE_ID`, and the block silently reorders.

## Script tasks

<!-- RULE:bpmn.script.compute-step -->
- A new step whose job is computation (totalling or counting over a collection, filtering, combining several values, deciding) is a `.scriptTask()`, in any pattern or composition outside a draft skeleton (bare `.task()` only there).
  `.task()` with `set` assigns or copies values (a per-item append, a status flag, one simple expression). The designer shows a `set` task as an Assign step, so a computation hidden in it is not visible as a Script step. Leave existing `.task()`/`set` steps in an imported file as they are.

<!-- RULE:bpmn.script.result-response -->
- A v3 script task (`scriptVersion` v3, written by `.scriptTask()`) returns `result.response`; read `=result.response` or `=result.response.<field>`, never `=result.<field>`. Use `return value;`, not `return { response: value };`, which double-wraps to `result.response.response`. `check` reports `=result.<field>` on a v2-or-later script as `SCRIPT_RESULT_NOT_RESPONSE` and names the corrected expression; `compile`/`validate` accept it, and the run then completes with the output empty.
<!--skill-flavor:sdk-script-result:start-->
  Needs `@uipath/maestro-builder-sdk` 6.93.7 or later; upgrade with `npm install -g @uipath/maestro-builder-sdk@latest`.
<!--skill-flavor:sdk-script-result:end-->

  ```ts
  .scriptTask('score', { script: 'return vars.amount * 0.01;', outputs: { riskScore: '=result.response' } })
  ```

  Returning an object: `script: 'return { severity: s, nextSteps: n };'` with `outputs: { severity: '=result.response.severity', nextSteps: '=result.response.nextSteps' }`.

<!-- RULE:bpmn.script.mapping-type -->
- Do not pass `type` to `.scriptTask()`; mapping type is always `BPMN.Variables`. Any other value (including `BPMN.ScriptTask`, which `registry get` lists) replaces the extension type, so the task does not run and outputs are null; it fails `BPMN_SCRIPT_TASK_TYPE_INVALID`. `.activity(id, 'BPMN.ScriptTask', …)` fails `BPMN_ACTIVITY_SCRIPT_TASK_TYPE`; use `.scriptTask()`.
<!--skill-flavor:sdk-script-type:start-->
  Needs `@uipath/maestro-builder-sdk` 6.93.8 or later; upgrade with `npm install -g @uipath/maestro-builder-sdk@latest`.
<!--skill-flavor:sdk-script-type:end-->

<!-- RULE:bpmn.script.ts-string-escapes -->
- `script` and every `=js:` value is a TypeScript string. Escapes are processed first: quoted `\n` becomes a newline and faults `300501` "Invalid or unexpected token" although `check`/`validate` pass; `\d` becomes `d`. Double every backslash the script needs (`\\n`, `\\d`); in backticks also escape `\${` and ``\` ``.

<!-- RULE:bpmn.script.error-row -->
- Typed script errors use the task-scoped `Error` output row: `source: '=Error'`, `type: 'jsonSchema'`, and the platform error-envelope schema. It is not an error boundary/second end event. `.scriptTask()` has no `errorVar`, so spell both rows with `outputRows`, which replaces `outputs`:

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

  Each row declares its variable (`score_Error` is scoped to the task), so add no `.var()`. Script `Error` fields are PascalCase (`Code`, `Message`, `Detail`, `Category`, `Status`, `Element`); read `vars.score_Error.Message`. Boundary captures use lowercase fields.

## Events and timers

<!-- RULE:bpmn.event.payload-live -->
- Connector payloads and timer firing are runtime facts; static validation proves declarations, not tenant subscriptions.

<!-- RULE:bpmn.event.timer-units -->
- Write timer durations in days, hours, minutes, and seconds, e.g. `P7D`, not `P1W`. Week/month/year designators fail at runtime while `check`/`validate` only warn `TIMER_DURATION_NOT_RUNTIME_PARSEABLE` and `TIMER_DURATION_WEEK_UNSUPPORTED`; treat either warning as an error.

<!-- RULE:bpmn.event.net-scope -->
- An event subprocess catches failures only in its direct container. At process level it ends the whole run on first failure; inside a multi-instance subprocess it ends only that iteration. Place `.eventSubProcess()` in the intended scope.

<!-- RULE:bpmn.activity.retry -->
- Configure retry as `retry: { maxRetries, backoff, backoffType, exponentialBase, maxDuration, allErrors }` (compiles to `<uipath:retry maxRetryCount retryBackoff …>`, Studio Web Error handling → Retry). `maxDuration` caps each delay, not total time. Set `allErrors: true` only when every failure of the step is transient (it also retries business errors); otherwise only `errorMapping` rows with `retryable: true` retry; neither means no retry. `errorMapping.code` is the **id of a declared `bpmn:error`**, whose `errorCode` is matched against the failure's code (HTTP/connector: the status as a string, `"429"`); `code: '429'` passes checks but retries nothing. To retry one status, declare it with a boundary, e.g. `t.onError({ name: 'RateLimited', code: '429' }, { id: 'onRateLimit' }, …)` (also catches it once retries run out); compile, read the id from `<bpmn:error id="Error_1" … errorCode="429">` (numbered in declaration order), use it in the row, compile again. HTTP/connector 5xx already retry 3 times internally; 4xx such as 429 do not. Never draw a retry loop; `.goto()` rerunning a business block such as a parallel block ([Draft skeleton](draft-skeleton.md)) is a process step, not retry.

<!-- RULE:bpmn.event.error-context -->
- Failed-element errors use capital `Error`. Boundary `errorVar` and event-subprocess captures use lowercase `code`, `message`, `detail`, `category`, `status`, `response`, `element`; script `Error` rows use PascalCase; other task rows are unverified. `.eventSubProcess({ error: true })` captures by default at its start into `vars.<net>_Error` (net `failures`: `vars.failures_Error`); `errorVar` renames it, `errorVar: false` omits it. Every event-subprocess capture is a JSON **string**: parse it (`=js:JSON.parse(vars.failures_Error).message` or `JSON.parse(vars.failures_Error).code`). A plain `vars.failures_Error.message` reads undefined, and a condition on it always takes the other arm; direct boundary/script-row captures are not strings. `vars.Error` never resolves. Reading a `vars.<id>` that no capture or declaration provides is `VARIABLE_DOES_NOT_EXIST`. Runtime ids are flat/unique regardless of `elementId`, requiring per-net defaults. A boundary captures nothing unless `errorVar` is set.

<!-- RULE:bpmn.event.non-interrupting-path -->
- A non-interrupting boundary runs beside the continuing token; its path must end independently. Rejoining executes subsequent work twice, and the builder rejects an open handler path.

## HTTP and Orchestrator work

<!-- RULE:bpmn.http.webhook-url -->
- Reach a connection webhook with manual `.http('ping', { url: '<WEBHOOK_URL>', method: 'GET' })` and no `connection`. Run `uip is webhooks config <CONNECTOR_KEY> --connection-id <CONNECTION_ID> --output json` and use `Data.WebhookUrl`; never use `uip is connections base-url`. If it reports `has no element instance id`, verify with `uip is connections list <CONNECTOR_KEY> --output json`. Only `uipath-http-webhook` can fire this event.

<!-- RULE:bpmn.orchestrator.names -->
- Address published work by name and folder; queue items require a folder. A live execution proves a resource exists and is runnable.

<!-- RULE:bpmn.orchestrator.process-type -->
- Choose by `ProcessType`, never name/label. Run `uip or processes list --folder-path <FOLDER_PATH> --all-fields --output json`; default output omits it:

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

  A `ProcessType` not in the table cannot be called from a process. Never author `A2A.AgentExecution`.

<!-- RULE:bpmn.orchestrator.in-solution-process -->
- A Maestro BPMN sibling in the same solution is called without deploying it: bind by name with `resourceKey` equal to the project name and no folder, then call `.startAgenticProcess()`:
  ```ts
  .binding('childName', { name: 'name', value: 'CreditAssessment', resource: 'process',
    propertyAttribute: 'name', resourceKey: 'CreditAssessment', resourceSubType: 'ProcessOrchestration' })
  .binding('childFolder', { name: 'folderPath', resource: 'process',
    propertyAttribute: 'folderPath', resourceKey: 'CreditAssessment', resourceSubType: 'ProcessOrchestration' })
  // …
  .startAgenticProcess('assess', { process: '=bindings.childName', folder: '=bindings.childFolder',
    input: { annualIncome: '=js:vars.annualIncome' }, outputs: { score: '=result.score' } })
  ```
  The child must map outputs at its end event ([output end mapping](#variables-and-the-process-contract)) or `result.score` is `null`.
<!--skill-flavor:in-solution-debug:start-->
  Studio Web Debug starts the child project; local `uip maestro bpmn debug` uploads only this project and faults `[170007] The job's associated process could not be found`. Debug the child separately with the CLI and the pair in Studio Web, and say so.
<!--skill-flavor:in-solution-debug:end-->

<!-- RULE:bpmn.orchestrator.sibling-resource -->
- Bind a resource another skill builds for this process after it is deployed, in order:
  1. Create its project in the process's solution.
  2. Hand its authoring, with the inputs and outputs the process needs, to the owning skill (uipath-rpa, uipath-api-workflow, uipath-agents, uipath-maestro-flow, uipath-functions, uipath-maestro-case); without that skill, tell the user to build it and stop.
<!--skill-flavor:sibling-deploy:start-->
  3. With the user's go-ahead, pack the solution with `uip solution pack <SolutionDir> <OutputDir> --version <VERSION> --output json`,
     publish it to the tenant feed as [Orchestrator deployment](operate.md#orchestrator-deployment) does (not a Studio Web upload), then deploy it with
     `uip solution deploy run --name <DEPLOYMENT_NAME> --package-name <PACKAGE_NAME> --package-version <VERSION> --folder-name <FOLDER_NAME> --parent-folder-path <FOLDER_PATH> --output json`.
<!--skill-flavor:sibling-deploy:end-->
  4. Find it with `uip or processes list --all-folders --name <PROCESS_NAME> --all-fields --output json`: folder is `OrganizationUnitFullyQualifiedName` (`--all-fields` omits `FolderPath`), type is `ProcessType`. Only then write the node with that `process` and `folder`.

  `folder: 'solution_folder'` compiles to a literal folder with no binding (`bindings_v2.json` stays empty); for a Maestro BPMN sibling use the `RULE:bpmn.orchestrator.in-solution-process` binding pair instead. The owning skill handing the project back is not the end.
<!--skill-flavor:sibling-redeploy:start-->
  A new `deploy run` name deploys to a new folder, so ship the finished solution into the same
  deployment: with the user's go-ahead, pack it with a higher `--version` than step 3's and publish it, then
  `uip solution deploy upgrade --name <DEPLOYMENT_NAME> --package-name <PACKAGE_NAME> --version <NEW_VERSION> --output json`.
  Never run a second `deploy run`: the folder the node names would no longer hold the resource.
<!--skill-flavor:sibling-redeploy:end-->

<!-- RULE:bpmn.orchestrator.job-outputs -->
- Job output arguments are `result` fields; map with node `outputs`, e.g. `.executeApiWorkflow('greet', { process, folder, input, outputs: { message: '=result.message' } })`. The same applies to `.startProcess()`, `.startAgent()`, and waited `.startAgenticProcess()`/`.startCaseProcess()` without `async`. These builders take no `outputRows`, and only `.startAgenticProcess()`/`.startCaseProcess()` take `async`: an older SDK drops either silently, a newer one refuses it (`BPMN_UNKNOWN_OPTION`). `outputVar` (default `<id>_processResponse`) is the envelope, not arguments; do not chain into it with `=js:`. Use the deployed workflow's own argument name; if no live run has shown it, say the mapping is unverified.
  The source is an expression, not a key: read a non-identifier name (`test-123`, a space, unicode) with brackets, `outputs: { test123: '=this["test-123"]' }`, written `source="=this[&quot;test-123&quot;]"`. Use the name exactly as declared, unescaped (a TypeScript string literal still needs its own escapes); an empty name or one containing `"` or `]` cannot be mapped: report it unsupported. Bare `=result.test-123` is subtraction: a wrong number (`27` when `result.test` is `150`) or an empty variable, with no error.

<!-- RULE:bpmn.http.manual -->
- Manual no-connection HTTP is `.http(id, { url, method, parameters, headers, body })` with no `connection`; it uses `ImplicitConnection`. `outputVar` defaults to `<id>_response`; `<id>_code`, `<id>_headers`, and `<id>_Error` hold the rest. Never put credentials in `headers`/`url`; use a connection ([connectors](connectors.md)), ask the user when none exists, and if a literal is insisted on, state its visibility before upload. Rewrite old `mode="manual"` context-row form when `check` warns `HTTP_MANUAL_V1`; it faults 102018 `Body cannot be null`; rewrite it as `.http()` and compile.
<!--skill-flavor:sdk-http-manual:start-->
  Needs `@uipath/maestro-builder-sdk` 6.93.9 or later; an older SDK still writes the old manual form, with `outputVar` holding the whole response and no `HTTP_MANUAL_V1` warning, so upgrade with `npm install -g @uipath/maestro-builder-sdk@latest` and compile again. Since 6.93.9 `outputVar` is the body: read `vars.<id>_response.x`, not `.body.x`.
<!--skill-flavor:sdk-http-manual:end-->

<!-- RULE:bpmn.http.connector -->
- For an existing connection and catalog-absent endpoint use `.http(id, { method, url, connection, folder, connectorKey })`. First run `uip is connections base-url <CONNECTION_ID> --output json`; it must host the target API, else do not bind it or send this API's path relative to it: use absolute manual HTTP (no credential) and name a suitable connection on `Needs:` ([connectors](connectors.md)). `url` is the vendor endpoint relative to that base (Slack's `/team.info` under `https://slack.com/api`), never an Integration Service `Path`; another-host absolute URLs fail 400 `Invalid request URL` (`MANAGED_HTTP_ABSOLUTE_URL`); wrong paths can yield `[102021] Received failure from vendor system`. Get `connectorKey` from `uip is connections list --all-folders --output json`; omit only for `uipath-uipath-http`. A wrong/missing key passes `check`, fails `validate` with `MISSING_BINDING`. `connection`/`folder` bind `ConnectionId`/`folderKey` (the connection's `Id` and `FolderKey`, or what `prepare` wrote); folder is required (`EMPTY_REQUIRED_FIELD folderKey`). `outputVar` is `<id>_response`; `<id>_code`, `<id>_headers`, and `<id>_Error` hold the rest.

  ```ts
  .binding('gh', { resource: 'Connection', propertyAttribute: 'ConnectionId', value: '<CONNECTION_ID>' })
  .binding('ghFolder', { resource: 'Connection', propertyAttribute: 'folderKey', value: '<FOLDER_KEY>' })
  .http('rateLimit', { method: 'GET', url: '/rate_limit', connection: 'gh', folder: 'ghFolder', connectorKey: 'uipath-microsoft-github' })
  ```

<!-- RULE:bpmn.http.url-placeholders -->
- Replace every `{name}` or `<NAME>` in an HTTP URL before compile with a discovered/given value or `=js:` expression; never invent one. `/repos/{owner}/{repo}` passes static checks but is sent literally.

<!-- RULE:bpmn.orchestrator.business-rule -->
- A deployed rule is `.businessRule(id, { process, folder, input, outputs })`, nothing else; the builder writes version, `BusinessRule` bindings, and `output`/`Error` rows. Results are decision-keyed: use `=result.<decisionKey>.<column>`, as in `outputs: { tier: '=result.eligibility.tier' }`, or `vars.<id>_businessRuleResponse.eligibility.tier`, never `=result.tier` or `=response.tier`. `releaseKey` is refused; rules are not addressed by process key.
<!--skill-flavor:business-rule-key:start-->
  `<decisionKey>` is the property name under `OutputArguments.properties` from `uip rules describe <RULE_NAME> --folder-path <FOLDER_PATH> --output json` (e.g. `decision1`), not the entry point's `DisplayName`: a display name reads null. Whole `=result` mapping also works. Only a decision-keyed rule with `x-uipath-decision-keyed` fits this row.
<!--skill-flavor:business-rule-key:end-->

<!-- RULE:bpmn.runtime.metadata -->
- `metadata.*` is empty in local `flow-debug`; for offline checks use literals or `vars.*`.

## Human task outcomes

<!-- RULE:bpmn.hitl.inline-form-default -->
- Always author inline forms: `.humanTask(id, { form: { fields, outcomes }, outputs: { decision: '=Action' } })`; the form travels in `.bpmn`. SDK app-backed tasks write v1 `Actions.HITL` with only `appId`: `uip maestro bpmn validate` rejects it (`MISSING_BINDING`/`MISSING_RESOURCE`), the engine does not read it. For a deployed Action App, author the inline form, tell the user it is unbound and to switch it in Studio Web; never substitute `.task()`.
- Field `direction`: `input` (shown, `value: '=vars.x'`), `output` (answer lands in `variable`, default id), `inOut` (shown, editable, written back); `type` is the data type: `{ id: 'amount', label: 'Amount', type: 'number', direction: 'input', value: '=vars.amount' }`; `type: 'input'` fails `check` (`TS2322`). Field ids are plain non-reserved identifiers (`reviewNote`, not `review-note` or `default`), never `Action`; outcome ids are unique, derived ids included (`Needs review` and `Needs-review` collide); one writer per variable; no answer variable equals an `outputs` key (field `decision` beside `outputs: { decision: '=Action' }` is refused); pickers (`singleSelect`, `multiSelect`, `enum`, dropdown `controlType`) require `options`, e.g. `[{ id: 'o1', value: 'high', label: 'High' }]`.
- Inline forms need the cloud quick-form flag; without it the human task fails `170004` `Invalid input for the HITL task` (pre-mid-September 2026 engines: `170015` `No app … found`). Tell the user to enable it; never fall back to `.task()` or `app`. Studio Web Edit Schema does not open for inline forms.

<!-- RULE:bpmn.hitl.no-completer-identity -->
- Inline forms return fields and `Action`, not completer identity: `hitlTask` `CompletedByUser`, `AssignedToUser`, `CompletionTime` come only from Action App tasks, which the SDK cannot bind. Never derive identity controls (four-eyes, "a different approver", an audit "who") from typed fields; route instead and tell the user to switch to an Action App in Studio Web or use Action Center assignee groups.

<!-- RULE:bpmn.hitl.task-settings -->
- `.humanTask()` writes only Action Center settings `title`, `priority` (`Low`, `Medium`, `High`, `Critical`), and string `labels`. Task timer (task SLA: reminder, reassign, unassign or auto-complete after a time) and assignee are set in Studio Web; `Timer` fails `check --source` (`TS2353`), compile alone drops it. Tell the user to set SLA in the panel. If the panel shows no Task timer (feature-flagged), or the process must act on breach, draw a non-interrupting `onTimer` in the task body (notify a manager) and call it a process timer, not task SLA.

<!-- RULE:bpmn.hitl.output-map -->
- Map decisions used by routing through `outputs`; typed platform output is not populated by local runtime. Exercise every important outcome.

<!-- RULE:bpmn.hitl.default-path -->
- Without injected outcome, local debug takes the gateway default. Choose it deliberately and use `--hitl-response` to test non-default outcomes.

## Connectors and bindings

Choosing operations and the author → check → prepare → check → compile loop is in **[`connectors.md`](connectors.md)**; these rules cover bindings.

<!-- RULE:bpmn.connector.bindings -->
- Keep connection/folder values symbolic in TypeScript and resolve them from `bindings.json`; only a live run proves environment bindings.

<!-- RULE:bpmn.binding.value-vs-resource-key -->
- `value` is the runtime value; `resourceKey` is never resolved. `=bindings.<id>` reads `value` (`default` on the wire); resolution is `supplied[id] ?? supplied[name] ?? value`, so a binding with neither is `UNRESOLVED` and a dispatching run refuses to start, naming each. `resourceKey` is design-time provenance for deploy re-resolution; set both when identity and value differ; `folderPath` has no `value`. Author-side `bindings.json` reverses them (`resourceKey` = tenant value, `default` = offline placeholder); never carry semantics between the files.

<!-- RULE:bpmn.connector.folder-companion -->
- `folderKey` is a connection companion, not a resource of its own: its `resourceKey` is the connection key; only `value` is the folder key. Declare the pair once, `.binding(c, { resource: 'Connection', propertyAttribute: 'ConnectionId', value })` and `.binding(f, { resource: 'Connection', propertyAttribute: 'folderKey', value })`, and read both from one node (`connection: '=bindings.c'`, `folderKey: '=bindings.f'`). A folder-keyed folder binding fails `validate` `MISSING_BINDING`; `check` warns `FOLDER_BINDING_KEYED_BY_FOLDER`/`FOLDER_BINDING_UNPAIRED` on bad pairing.

<!-- RULE:bpmn.connector.data-service -->
- Data Fabric records/files use `.dataService(id, { entity, connection, folder, op, … })`, with exactly `create`, `update`, `get`, `query`, `delete`, `downloadFile`, `uploadFile`, `deleteFile`. It writes `Intsvc.ActivityExecution`, needs no connector library or `prepare`, and declares `<id>_response`/`<id>_Error`; read record id as `=js:vars.<id>_response.Id`. Map results at the end event (`payload: { type: 'BPMN.Variables', outputRows: [{ name, type, var, source: '=js:vars.<id>_response' }] }`). Do not hand-fill `.activity('Intsvc.ActivityExecution', …)` or use `.connector()` for these operations. `examples/ContractRegistry.bpmn.ts` is the full lifecycle.

<!-- RULE:bpmn.connector.data-service-folder-entity -->
- Folder entities (picker shows it under a folder; request says "folder entity" or "entity scope: folder") use `entity: { name, folder: '<folder path>' }`, not plain name/hand-found keys. On `bpmn check --source` `RESOURCE_UNRESOLVED`, run `uip maestro registry prepare --entity <name> --folder-path <path>` in the `bpmn check`/`compile` directory (records `./.flow-sdk/resources.json`), then `check` again. Without a folder, `prepare` searches all folders: it records and names one match, or lists several. `entity.folder` holds the ENTITY; the `folder` option holds the CONNECTION: two options even when the same folder. Record operations use `_V3` (`CreateEntityRecord_V3`, …); `create`, `update`, `get`, `query` use V2 picker bindings; `delete` stays V1 with `entityScope=folder`, `folderEntityName`, `folderEntityName_folderKey`. Do not hand-convert. Tenant entities use curated V2 operations (`CreateEntityRecordCurated`, `UpdateEntityRecordV2`, `GetEntityRecordByIdCurated`, `QueryEntityRecordsCurated`, `DeleteEntityRecordCurated`) with entity in `pathParameters`.
<!--skill-flavor:sdk-upgrade:start-->
  Needs `@uipath/maestro-builder-sdk` 6.73.0 or later; upgrade with `npm install -g @uipath/maestro-builder-sdk@latest`. If `uip maestro registry prepare --entity …` reports `missing required argument 'connector-key'`, run `npx flow-sdk registry prepare --entity …`.
<!--skill-flavor:sdk-upgrade:end-->
<!--skill-flavor:sdk-df-folder-v2:start-->
  Needs `@uipath/maestro-builder-sdk` 6.122.0 or later; an older SDK writes every record operation on a folder entity as a V1 task, which still validates and runs, so upgrade with `npm install -g @uipath/maestro-builder-sdk@latest` and compile again when a V2 task is asked for; do not hand-convert its rows.
<!--skill-flavor:sdk-df-folder-v2:end-->
<!--skill-flavor:folder-entity-resources:start-->
  Run `uip maestro bpmn refresh <project>` after `compile`, then, when the project has a solution, `uip solution resources refresh --solution-folder <SolutionDir>` (the folder holding the `.uipx`, `<Name>Solution/` in the default scaffold); the first writes the entity row to `bindings_v2.json`, the second declares it in the solution.
<!--skill-flavor:folder-entity-resources:end-->
- Do not pass folder entity name as plain `entity`, hand-fill `.activity()`, or add entity bindings; compile writes the pair. A V2 task reads it, so its entity can be re-pointed per environment at deploy; a `delete` task's entity is fixed at compile time. `entity: { name, folderKey }` is allowed for a known key; `check` prints `uip maestro registry prepare --entity <name> --folder-key <key>`, then run it and check again.
<!--skill-flavor:sdk-folder-key:start-->
  If `uip` answers `unknown option '--folder-key'`, run `npx flow-sdk registry prepare --entity <name> --folder-key <key>`. If `uip` says `--folder-key` needs a builder SDK release that supports it, or `npx flow-sdk` answers `unknown option '--folder-key'`, use `{ name, folder }` instead.
<!--skill-flavor:sdk-folder-key:end-->
- An `=` folder key cannot be recorded and produces V1 with no solution declaration; prefer `{ name, folder }`. Decompiled folder tasks remain `.activity()` with rows/bindings and compile unchanged. File operations refuse folder-scoped entities; tell the user unsupported and do not fall back to tenant entity or hand-fill. `.eventTrigger()` uses the same `entity: { name, folder }` ([connector events](connectors.md#6-connector-events)).

<!-- RULE:bpmn.connector.parameter-rows -->
- `.connector()`, `.dataService()`, `.eventTrigger()`, `.waitForEvent()` write V2 (`activityConfigurationVersion: v2`), as Studio Web's connector panel saves and `uip maestro bpmn registry get --input-details` builds: path parameters in one JSON `pathParameters` row, query parameters in `queryParameters`, body in one `target="body"` row, multipart parts in `target="file"`; use library names (`send_as`, not `sendAs`). `.dataService()` still writes V1 for file operations (`downloadFile`, `uploadFile`, `deleteFile`) and, on a folder-scoped entity, for `delete` and an `=`-expression folder key.
<!--skill-flavor:sdk-v2-connector:start-->
  Needs `@uipath/maestro-builder-sdk` 6.84.0 or later; upgrade with `npm install -g @uipath/maestro-builder-sdk@latest` and compile again; do not hand-convert old rows.
<!--skill-flavor:sdk-v2-connector:end-->
- Imported V1 tasks keep one `target="path"`/`target="query"` row per parameter plus `operation`; leave them. Leave the process-level `uipath:intsvcActivityConfig` marker as found; never add it to an existing workflow: Studio Web would read every unversioned V1 task as V2. Through `.activity()`, copy `registry get --input-details` `Data.V2.ElementXml` context rows, including `activityConfigurationVersion: 'v2'`; body fields go in `inputs` (JDBC `inputs: { script }` becomes body `{"script": …}`), path/query parameters in `inputs: { pathParameters: { … }, queryParameters: { … } }`. `inputRows` replaces `inputs`: spell every row, body row included (`{ name: 'body', type: 'json', target: 'body', body: { script } }`), or request fields are silently dropped. A row without `target` is not sent; `check` fails `CONNECTOR_INPUT_ROW_NO_TARGET`. See [§4 of the connectors reference](connectors.md#4-when-the-connector-is-not-in-the-library).

## Brownfield editing

<!-- RULE:bpmn.brownfield.merge -->
- For targeted edits, decompile the original, edit the source, then `merge` it into the original. Bare recompile rewrites untouched elements and loses layout; merge preserves untouched elements byte for byte.

<!--skill-flavor:brownfield-merge-form:start-->
  ```bash
  uip maestro bpmn decompile <Project>/<Name>.bpmn -o <Name>.bpmn.ts --style nested
  # edit <Name>.bpmn.ts, then run check --source until it is clean
  uip maestro bpmn merge <Name>.bpmn.ts --original <Project>/<Name>.bpmn
  ```
  `merge` overwrites `--original`; pass no `-o`. Preserve line 1 stamp `// @decompiled-from … sha256:…`; pass no decompile options to merge. After edits or `format`, merge the same source again. On `MERGE_ORIGINAL_CHANGED`, `MERGE_SOURCE_NOT_STAMPED`, or `MERGE_SOURCE_STAMP_UNREADABLE`, decompile again and reapply. On `MERGE_OPTION_CONFLICT`, omit the merge decompile option. Needs SDK 6.95.0 or later; on an older SDK run the install command the ConfigError prints and merge again.
<!--skill-flavor:brownfield-merge-form:end-->
- Then `refresh` and `validate`; do not `format` unless `refresh`/`validate` reports `BPMN_PARSE_ERROR` with `No diagrams found`, `MISSING_DI_SHAPE`, or `MISSING_DI_EDGE`, or the target is a template/replacement process (see `bpmn.brownfield.format`).

<!-- RULE:bpmn.brownfield.nested-style -->
- `bpmn decompile --style nested` lifts boundaries, gateways, and event subprocesses, uses `flowMode('sequence')`, and verifies the lifted graph before writing. It keeps original flow ids, pinning each with `.flowIds([{ source, target, id }])` once at the top; merge requires this because it keys every process child by id (a renamed flow leaves an untouched gateway's `default` naming a missing id: `MISSING_CONDITION_EXPRESSION` at validate). `--keep-flow-ids` limits lifting to already matching derived ids, for source with no pin table. A non-`Flow_<source>_<target>` id remains flat without changing graph or ids.

<!-- RULE:bpmn.brownfield.connector-lift -->
- With `--library <dir>` (else the registry-pull cache; `--connectors-local <dir>` overlays it), decompile lifts only V2 `Intsvc.ActivityExecution` tasks the library can name into `.connector(key, action, inputs, { connection, folder, outputVar, errorVar, outputs })`, compiling and comparing each lift before writing; others stay verbatim `.activity()` with `contextVerbatim` and metadata, each reason reported (V1: `a V1 connector task, kept verbatim so it stays V1`). Copy the lifted `.connector()` form when adding a connector task to an import. Kept verbatim: a body field the static library does not declare (Data Fabric update entity columns; `registry prepare` loads them), a `connection` not a `=bindings.<id>` reference, a designer row with an attribute no option spells. A lifted task keeps the file's `jsonSchema` declaration as an explicit `.vars([…])` entry. Lifted canvas metadata is regenerated, so a no-edit `merge` round trip is not byte-identical for them; `--connectors verbatim` preserves tasks byte-identically. `examples/InvoiceApproval.bpmn.ts` shows both forms; its six `.connector()` calls predate the V2-only lift (from V1 tasks, now compiling to V2), while a fresh decompile keeps all twelve verbatim.

<!-- RULE:bpmn.brownfield.unused-bindings -->
- `bpmn decompile` drops unreferenced bindings and reports them; a binding without `value` is unresolved and blocks dispatch. Retain them with `--keep-unused-bindings`. Tenant cleanup occurs through `uip maestro bpmn merge`, which takes the edited source extension block.

<!-- RULE:bpmn.brownfield.palette-elements -->
- Decompile writes complex gateways as `.complexGateway(id, { name, default })` and bare call activities as `.plainTask(id, { element: 'bpmn:callActivity' })`; do not author bare calls (`validate` rejects, `check` reports `CALL_ACTIVITY_NO_PAYLOAD`). Use an `Orchestrator.Start*Process` type with a process binding. Data objects/references/store references are omitted; preserve the `// DATA ELEMENTS LEFT TO THE ORIGINAL` header so merge retains them; bare compile drops them.
<!--skill-flavor:sdk-palette-elements:start-->
  Needs `@uipath/maestro-builder-sdk` 6.88.1 or later; an older SDK refuses every element above with "has no builder equivalent", so upgrade with `npm install -g @uipath/maestro-builder-sdk@latest` and decompile again.
<!--skill-flavor:sdk-palette-elements:end-->
- Decompile refuses a complex gateway with `activationCondition` or bare call with `calledElement`; tell the user, remove the attribute, and decompile again. Runtime does not read the former and the platform ignores the latter. The bare call still fails `validate` with `CALL_ACTIVITY_NO_PAYLOAD` until given an `Orchestrator.Start*Process` type and binding.

<!-- RULE:bpmn.brownfield.format -->
- Do not relayout a merged process. Merge keeps original shapes, edges, pools, lanes, colors, placement (growing a lane, pool or expanded sub-process lacking room for a new shape and shifting shapes below, rerouting an existing edge whose flow the edit rewired) and draws only additions. `format --relayout` lays out the whole diagram; plain `format` on a CLI whose help lacks `--relayout` also relayouts, dropping pools, lanes, colors, placement. Run plain `format` only when `refresh`/`validate` reports `BPMN_PARSE_ERROR` with `No diagrams found`, `MISSING_DI_SHAPE`, or `MISSING_DI_EDGE`; then `refresh` and `validate`; on a CLI without `--relayout`, when the original had a diagram (`MISSING_DI_SHAPE`/`MISSING_DI_EDGE`), tell the user the canvas layout was reset. For a one-start/at-most-one-end template or user-chosen replacement, run `format --relayout` (plain `format` without the flag), then `refresh` and `validate`.
