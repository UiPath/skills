# Case runtime decisions

This reference contains only choices that types and static validation cannot
make from syntax alone. Exact signatures remain in the generated API.

## Triggers and live payloads

<!-- RULE:case.trigger.event-resolution -->
- A connector event without a subscription is a placeholder. A resolved event
  needs a generated descriptor or connector key/event plus symbolic connection
  and folder bindings. For an unresolved placeholder, put the watched object
  in `object` (`@uipath/maestro-builder-sdk` 6.32.6 or later) and keep the
  source system and event verbatim in the name or description. Do not fabricate a
  connector descriptor or node type. This example keeps the source object
  while remaining a valid placeholder:

  ```ts
  eventTrigger({ name: 'T02', object: 'aged_invoice_cases', description: 'record created' })
  ```

  `object` and `subscription` are mutually exclusive. Only a live
  subscription proves the payload shape.
  A placeholder trigger never starts the case. When you report the result
  (the [final report](final-report-template.md)'s `Needs:`),
  list each placeholder trigger and what the user must set in the designer:
  connector, connection, object, event and filter. Say that the case cannot
  start on its own until they do.

## Human and on-demand work

<!-- RULE:case.select-next-stage.live -->
- `wait-for-user` and select-next-stage behavior depends on a live Case runtime.
  Static validation proves the contract, not the human selection outcome.

<!-- RULE:case.action.both-outcomes -->
- A boolean decision from an action has TWO outcomes, and downstream routing has
  to express both. Gating only the affirmative arm (`approved === true`) leaves
  the rejection path implicit: nothing runs, the stage never completes for that
  reader, and the plan validates anyway because an unreferenced value is not an
  error. Write the complementary condition explicitly, even when the negative
  arm only routes to a close-out.

<!-- RULE:case.action.names-app -->
- An action task opens an Action App, and `.action({ ... })` with no `app`
  names none. In a plan that binds any other resource, `case check`
  (SDK 6.121.1+) warns `STRICT_BINDINGS_TASK_ABSENT` on it and
  `case validate --strict` fails: the task cannot run. Name the app:

  ```ts
  .action({ title: 'Approve', recipient: 'approver@corp.com', app: { name: 'ApprovalApp', folder: 'Shared' } })
  ```

  If the app is not published yet, write `t.unresolved('action')` instead and
  fill the task in once it is; do not invent an app name. Brownfield: a
  decompiled quick form (an inline form, no app) is fine as is. `case check`
  does not warn on it, but `case validate --strict` still reports
  `STRICT_BINDINGS_TASK_ABSENT` there (a CLI false positive): keep the quick
  form and do not add an app to silence it.

<!-- RULE:case.action.designer-outputs -->
- The Case Designer gives an action task that opens an app three outputs
  besides the app's own fields: `Action`, the outcome the assignee picked,
  with the app's outcomes as its `options` (`OUTCOMES` below; a coded action
  app's are the property names under `outcomes.properties` in its
  `action-schema.json`); `hitlTask`, the task; and `Error`. `compile` adds
  none of them, so declare them on each such task you add:

  ```ts
  .action({ ..., outputs: [
    { name: 'decision', type: 'string', value: 'decision' },
    { name: 'Action', type: 'string', value: 'action', options: OUTCOMES.map((v) => ({ value: v, label: v })) },
    { name: 'hitlTask', type: 'jsonSchema', value: 'hitlTask' },
    { name: 'Error', type: 'jsonSchema', value: 'error' },
  ] })
  ```

  Each of the three writes a variable of its own: set its `value` to a name
  no task output or case variable in the plan holds, the camelCased name or,
  once that is taken, the first free one suffixed from `2` (`action2`,
  `error3`), as the Designer numbers them. In an existing plan, take the
  names in use from every `id` and `var` under its tasks' `outputs`: a
  decompiled source omits a connector task's, whose `Error` may hold
  `error`. A name in use makes two tasks write one variable, or `compile`
  renames the saved output that held it. Left out, `compile` numbers the row
  by task order, and in an existing plan can hand it a saved output's name.
  A form field's `value` may name the same variable on several tasks.

  Keep a saved task's outputs as saved: an older save may hold only `Action`.

## Action recipients and the go-live trap

<!-- RULE:case.recipient.externalize -->
- A literal `recipient: '<email>'` compiles to `{ Type: 2, Value: <email> }`
  and bakes the address into the plan: going live means editing every action
  and publishing a new version. When the request names a test, placeholder or
  not-yet-known assignee, wire it through a case input instead:

  ```ts
  .input({ approver: { type: 'string', default: '<TEST_EMAIL>' } }, { from: manual })
  // ...
  .action({ ..., recipient: { type: 3, value: '=vars.approver' } })
  ```

  Going live then means changing the input default, or passing the real
  address when the case starts; the actions stay unchanged.
  Recipient types are `0` user id, `1` group name, `2` email, `3` expression.
  Type `3` evaluates `value` and assigns the result as a user when it is an
  email, and as a group name otherwise. An expression needs type `3`: a bare
  string `'=vars.approver'` is type `2` and is looked up as a literal email.
  `case check` warns `STRICT_RECIPIENT_EXPRESSION_TYPE` on that, and
  `case validate --strict` fails. The SDK's `RecipientType` doc comment still
  calls `0`/`1`/`3` reserved; that comment is stale, and type `3` is the
  expression type the CLI and `case check` accept.
  Brownfield: keep a decompiled `{ type, value }` recipient as is.

<!-- RULE:case.recipient.no-silent-default -->
- Before `uip solution upload` or `uip solution publish`, tell the user the
  list below, and repeat that list in the final summary of every build or
  edit (the [final report](final-report-template.md)'s `Assumed:`). List each assignee the user did not name as the production assignee: an input default, a literal
  `recipient`, or an SLA escalation target (`toUser`, `toGroup`). These include
  a test mailbox, the user's own email, and `<UNRESOLVED: ...>`. For each one,
  give the address or group, the actions or escalations it routes, and what
  going live changes: the input default, or each literal in the source plus a
  new published version.

  `uip maestro case debug` and `uip maestro case process run` start a case
  instance and create real tasks for these assignees. `upload`, `publish`,
  `check`, `compile` and `validate` start none. Before `debug` or
  `process run`:
  1. An assignee still `<UNRESOLVED: ...>`: do not run it.
  2. An address or group the user did not confirm: ask. A request or
     pre-approval that names that step is the user's answer. When no user can
     answer and nothing names that step, do not run it.

## Script tasks

<!-- RULE:case.script.positional-rename -->
- The function form's parameters are positional: first parameter becomes
  `vars`, second becomes `metadata`. The mapping is by position, not by
  name. Any names work, except `metadata` first or `vars` second, which
  compile refuses. A function-local `const` is fine;
  a module-scope constant or an `import` is refused at compile.
  Compile also refuses destructured parameters (`({ amount }) =>`),
  aliasing (`const v = vars`), bracket access (`vars['x']`), optional
  chaining on `vars`, and passing `vars` to another function.

<!-- RULE:case.script.body-and-refs -->
- A string body compiles as authored. Declare every `vars.x` read
  with `.var()` or `.input()` before referencing it.

<!-- RULE:case.script.outputs -->
- `.outputs({ scriptResult: '=result.response' })` maps the whole return value
  to a case variable. Compile refuses any source except `=result.response` and
  `=Error` (code `SCRIPT_OUTPUT`). To reach a single field, read
  `vars.scriptResult.<field>` downstream. The compiled output row is named
  `scriptResponse`.

## HTTP requests

<!-- RULE:case.http.modes -->
- `.httpRequest({ method, url, ... })` sends one HTTP call. Without `connector`
  the request goes to `url` unauthenticated. With
  `connector: { key, connection, folder }` it reuses that connection's auth and
  `path` replaces `url`. Compile refuses `url` through a connector or `path`
  without one.

<!-- RULE:case.http.body -->
- An `=` value inside an object body compiles to the code it reads:
  `body: { id: '=vars.id' }` sends the variable's value, and so does a
  `'=js:<expr>'` leaf. Each `=js:` value must be exactly one expression
  (acorn-parsed); a statement or unparseable text is refused at compile
  (`HTTP_REQUEST_BODY_EXPRESSION`). Both work nested and in arrays. Other
  `=` forms (`=vars.a + 1`) are also refused with the same code; write as
  `'=js:vars.a + 1'`. A string body must be JSON or an `=` expression;
  other text is refused at compile (`HTTP_REQUEST_BODY_FORM`).

<!-- RULE:case.http.credentials -->
- Compile writes literal credential headers and query parameters as authored.
  Use `=vars.` references for secrets; `check` warns on literals.

<!-- RULE:case.http.outputs -->
- Outputs are the fixed four: `code`, `headers`, `body`, `Error`.
  `.outputs({ v: '=response.body' })` maps one to a case variable.

## Document extraction

<!-- RULE:case.docextraction.discovery -->
- Discovery: `uip ixp projects list --output json` first. Pass the project's
  **`Name`** (not `Title`) to `uip ixp deployments list <Name> --output json`.
  That listing gives model (`DeploymentName`), deployment (`DeploymentTitle`),
  and `folderKey`. For `deploymentKey` and `folder`: run
  `uip solution resources list --kind IxpDeployment --source remote
  --output json` and take the row whose `Name` equals `DeploymentTitle` and
  whose `FolderKey` matches — its `Key` is `deploymentKey`, its `Folder` is
  `folder`. Ask the user if no match. `sdd resolve` does not resolve them.
  After discovery, add the deployment to the solution:
  `uip solution resources add --source remote --kind IxpDeployment
  --name "<DeploymentTitle>" --folder-key "<FOLDER_KEY>" --output json`
<!--skill-flavor:docextraction-refresh:start-->
  Then refresh:
  `uip solution resources refresh --solution-folder <SOLUTION_DIR> --output json`
<!--skill-flavor:docextraction-refresh:end-->

<!-- RULE:case.docextraction.check -->
- Compile refuses a missing `deploymentKey`; `check` reports blank model,
  deployment, folder, folderKey, and file individually.

<!-- RULE:case.docextraction.legacy -->
- Decompile emits `.savedDocumentExtraction()` for the older flat format.
  It is read-only: no `.outputs()`, no deployment edit. `check` warns
  `DOCUMENT_EXTRACTION_OLDER_SHAPE`.

<!-- RULE:case.docextraction.floor -->
- `uip maestro case validate` needs uip 1.206.0+ for document-extraction
  tasks. Older versions reject with `CASE_MGMT_BINDING_PAIR_INCOMPLETE`.
  On an older `uip`, report the floor requirement and stop. Do not rewrite
  bindings or strip the extraction task to silence the error.

## Connections and external work

<!-- RULE:case.connector.bindings -->
- Source connection and folder ids from `bindings.json`; TypeScript uses symbolic
  names. Compiling into a scaffolded project regenerates its existing
<!--skill-flavor:bindings-refresh:start-->
  `bindings_v2.json`; then run `uip solution resources refresh --solution-folder
  {solution} --output json`.
<!--skill-flavor:bindings-refresh:end-->
  A live run is the evidence that those environment
  resources resolve. A `CONNECTION_STUB` warning from `case check` or `case
  compile` means a connection or folder label compiles to a value that is not
  a real id; it still compiles (fine for an offline or validate-only task), but
  bind it with the `registry prepare` command the warning prints before a live
  run.

<!-- RULE:case.resources.live -->
- Published process, agent, RPA, API workflow, sub-case, connector, and folder
  references are tenant facts. Static validation cannot prove they exist.

<!-- RULE:case.external.mode -->
- An `externalAgent` or `externalWorkflow` task's `mode` is the connector
  object's `executionType` (`sync`, `async` or `hybrid`), never a choice about
  the case. Leave it out when the connector library records it; otherwise copy
  it from the activity's `case spec` result
  (`Data.EssentialConfiguration.essentialConfiguration.executionType`). An
  `async` or `hybrid` object also answers through an event: unless the library
  records it, pass `event: { operation, mode }` from the same result's
  `Data.CaseShape.context` rows `operation` and `eventMode`. A `hybrid` task
  without one is refused (`EXTERNAL_TASK_EVENT`); a `sync` task takes none.
  `mode` does not decide whether the stage waits: a task the stage must not
  wait on is `.required(false)`, whatever its `mode`.

<!--skill-flavor:orphan-cleanup:start-->
- Resource refresh is additive. After removing or repointing a resource-bound
  task, prune orphans before refreshing:

  1. Recompile. `compile` (SDK 6.86.23+) emits `ORPHANED_SOLUTION_RESOURCE`
     for each process or app declaration no binding still references. An
     older SDK emits nothing, so step 2 removes nothing and the orphan ships.
  2. For each reported orphan:
     `uip solution resources remove {key} --solution-folder {solution} --output json`
  3. Connection declarations are not covered by the warning. Remove one
     only when no project in the solution still binds it. Search both
     binding files, because a coded agent binds a connection in
     `bindings.json`, not `bindings_v2.json`:
     `grep -rl --include=bindings_v2.json --include=bindings.json --exclude-dir=resources --exclude-dir=.venv '<connection-key>' {solution}`
     No match means safe to remove with `resources remove`.
  4. Never remove the Case project's own process/package pair, and never
     target package entries directly.
  5. `uip solution resources refresh --solution-folder {solution} --output json`
<!--skill-flavor:orphan-cleanup:end-->

## SLA and runtime semantics

<!-- RULE:case.sla.calendar -->
- SLA `d`, `w`, and `m` are calendar units. A business-day requirement needs an
  explicit product decision or live calendar service; do not invent a conversion.

- An `sla-status-change` breach response uses only `{ sla }`; an at-risk response
  also names `{ escalation }`. Put an enter-stage response on an
  `exceptionStage(...)` with `.required(false)` ([Completion and
  optionality](#completion-and-optionality)).

<!-- RULE:case.sla.escalation-absent -->
- An ABSENT `escalation` is the persisted representation of Breached — not a
  missing field. A reference to an at-risk escalation, or the Case Designer's
  `escalationId: "any"` wildcard, makes the rule at-risk; one to an
  `sla-breached` escalation is Breached. The wildcard is valid and fires on
  every at-risk escalation of that SLA (in SDK source,
  `escalation: ANY_ESCALATION`). In `caseplan.json` do not write `"any"` by
  hand; in `.case.ts` use `ANY_ESCALATION` only when the requirement means
  every at-risk escalation. When the SDD names one escalation, name it.
  Repair an existing rule by the requirement's status, never
  by what the plan already carries: a breach response drops the reference and
  leaves a plain breach rule on the SLA; repointing it at an at-risk escalation
  keeps it at-risk, which fires at a different time. Only an at-risk response
  needs a concrete escalation, and it must be one declared on that same SLA.

<!-- RULE:case.sla.lane-exit -->
- A secondary lane's exit type is a routing decision, and the two shapes are not
  interchangeable. A lane that hands the case BACK to the work it interrupted
  exits `return-to-origin`, which lets the origin stage's own conditions carry
  the case onward — no lane needs a duplicated exit rule per possible origin. A
  lane that ends the case instead exits `exit-only`, and then the case needs a
  matching `caseExitRules` row, or the case can reach the lane and never leave
  it. Read the SDD's own words for which: "returns to", "resumes", "rework"
  means the first; "closed", "terminated", "escalated out" means the second.

<!-- RULE:case.skip.live -->
- Whether a skipped task satisfies a completion rule is runtime behavior. For a
  critical bypass, use a separate expression-gated exit or prove the path live.

## Stage routing

<!-- RULE:case.exit.branch-entry -->
- `exitToStage` on an `exit-only` exit does not route at run time: the
  runtime drops the target and, when a stage completes or exits, enters every
  stage whose entry holds. A destination enters on `selected-stage-completed`
  when its exit marks the stage complete, and on `selected-stage-exited` when
  it does not. Without an expression, either holds for every exit of its kind
  out of that stage, so a stage that branches several ways opens every
  destination at once. Gate each destination's entry so only its own branch
  opens it:

  ```ts
  .stage('Review', s => s
    .entryWhen(rule('selected-stage-completed', { stage: 'Triage', expression: '=js:vars.route === "review"' })))
  ```

  Copy each exit's expression when the exits' expressions exclude one
  another; otherwise rewrite the gates until they do. A fallback exit with no
  expression gates its destination on the negation of the others
  (`=js:!(vars.amount > 1000)`). When the exits differ only by which task
  completed, have every deciding task write one shared variable, each its own
  value, and gate on that value. A variable only one task writes keeps its
  value when the stage runs again, so that task's destination opens again on
  a later pass. The SDK's `exitToStage` doc comments say the exit routes and
  suggest a `selected-tasks-completed` stage entry; `validate` refuses that
  rule in a stage entry (`CASE_MGMT_RULE_SLOT_MISMATCH`).

  A `wait-for-user` exit's destination enters on `user-selected-stage`, since
  a person picks the onward stage; this rule does not gate it.

  With an SDD, each entry row's IF is that entry's gate, and
  `validate --strict --sdd` refuses an expression on a row whose IF is blank
  (`STRICT_SDD_CONDITION_EXPRESSION_UNDECLARED`). When the SDD leaves IF blank
  on a destination this rule gates, send the SDD back through the planner to
  add the IF before building that stage.

## Completion and optionality

<!-- RULE:case.exit.non-completing -->
- `marksCaseComplete` distinguishes two different outcomes, and a case usually
  needs both. At least one `completeWhen(...)` rule must carry `true`, or the
  case can never close. An outcome that ENDS the case without closing it
  normally — an escalated close-out, a rejection, a withdrawal — is a separate
  rule with `marksCaseComplete: false`. It is added ALONGSIDE the positive rule
  and never replaces it: folding both readings into one `true` rule ("Case
  resolved or escalated") loses the distinction the plan was asked to make.

  Three-exit pattern (completing + rejected + withdrawn):

  ```ts
  .completeWhen(rule('required-stages-completed'), { marksCaseComplete: true })
  .completeWhen(rule('selected-stage-completed', { stage: 'Rejection' }), { marksCaseComplete: false })
  .completeWhen(rule('selected-stage-completed', { stage: 'Withdrawal' }), { marksCaseComplete: false })
  ```

<!-- RULE:case.optionality.explicit -->
- A task or stage the request (or SDD `Required` / `Required for Case
  Completion: No`) calls optional gets `.required(false)`; one that must gate
  gets `.required()`. Omitting it writes no `isRequired`, which the plan
  compiler reads as not required: `required-tasks-completed` waits only on
  tasks, and `required-stages-completed` only on primary stages, marked
  `isRequired: true`.
  The Designer writes the flag explicitly, so write it either way.
- SDD `Stage Kind: secondary` is `.exceptionStage(label, fn)`, never
  `.stage()`: only `exceptionStage` writes `stageType: secondary`. Add
  `.required(false)`: the Designer forces it false on a secondary stage it
  edits, and `check` warns `EXCEPTION_STAGE_REQUIRED` without it.

## Activation modes

<!-- RULE:case.activation.lane -->
- For an SDD `Activation Mode` column, use `runs-sequentially` and `lane`.
  `lane` is the third argument to `.task()`: `.task(name, fn, { lane: N })`.
  It sets the set index in `data.tasks[][]` (`lane ?? 0` in the SDK).
  Tasks that share a lane start together after the predecessor set completes.

  | SDD Activation Mode | SDK entry rule | `lane` | Effect |
  |---|---|---|---|
  | `parallel` | `rule('current-stage-entered')` | omit | Task starts at stage entry, in its own set. |
  | `parallel-after-predecessor` | `rule('runs-sequentially')` | shared | Siblings share a set; start together after the predecessor set. The predecessor also uses `runs-sequentially`. |
  | `sequential` | `rule('runs-sequentially')` | unique per task | Strict chain: each task waits for the previous set. |

  A task without `runs-sequentially` gets its own set regardless of `lane`.
  See `examples/PermitIssuance.case.ts` for a three-set stage.

<!-- RULE:case.activation.anti-pattern -->
- Omitting `lane` on all `runs-sequentially` tasks defaults them to set 0 —
  they start together, losing sequential structure. The same happens when every
  task gets the same explicit `lane`. Every `runs-sequentially` task needs an
  explicit `lane`.

## Task exit rules

<!-- RULE:case.task-exit.semantics -->
- A `task-exited` rule reacts to a task of its own stage that ended without
  completing: `failed` (the task failed on its own, after its retries) or
  `userExited` (a person ended the running task through the exit API). A task
  the case itself cancelled (an interrupting stage) is neither and fires no
  rule. The rule fires once EVERY task it names has exited; for "any one of
  them", write one rule per task. An exited task does not satisfy
  `required-tasks-completed`: the stage stays open until a rule moves the case
  on, or an operator re-runs the task.

<!-- RULE:case.task-exit.placement -->
- Put the rule on the entry of the task that should start (a manual fallback),
  or on an exit of the failing task's stage with `{ marksStageComplete: false }`
  and enter the next stage with `rule('selected-stage-exited', { stage })`.
  Elsewhere the rule is written and never fires: at a stage entry, on an exit
  that marks the stage complete (unless `type: 'wait-for-user'`), or at case
  completion (`check`: `TASK_EXITED_PLACEMENT`;
  `validate`: `CASE_MGMT_CASE_CONDITION_RULE_TASK_EXITED_NOT_HERE`; at a stage
  entry `validate` also refuses it, `CASE_MGMT_RULE_SLOT_MISMATCH`). Name only
  tasks of the rule's own stage (`TASK_EXITED_TASK_OUTSIDE_STAGE`), and never
  the task whose entry holds the rule: that re-runs it after every failure
  until the case guardrail stops the loop (`TASK_EXITED_SELF_RERUN`).

  ```ts
  // --- stage 'Intake' ---
  .exitWhen(rule('task-exited', { tasks: ['Fetch Policy'], exitReasons: ['failed'], errorCategories: ['Deployment'] }),
    { displayName: 'Fetch failed to deploy', marksStageComplete: false })
  .task('Enter Policy By Hand', t => t.action({ title: 'Enter the policy' }).required(false)
    .entryWhen(rule('task-exited', { tasks: ['Fetch Policy'] })))
  // --- stage 'Review' ---
  .entryWhen(rule('selected-stage-exited', { stage: 'Intake' }))
  ```

<!-- RULE:case.task-exit.filters -->
- `exitReasons` narrows the rule to `failed`, `userExited`, or both; omit it
  for either. `errorCategories` (`User`, `System`, `Deployment`) applies only
  to a failures-only rule (`exitReasons: ['failed']`): only a failure carries an
  error, and the platform ignores the filter on any other rule
  (`TASK_EXITED_FILTER_IGNORED`). Anything finer than the category, such as the
  error code or message, is an `expression` over the task's error, not a
  filter.

<!-- RULE:case.task-exit.flags -->
- A plan with a `task-exited` rule compiles with both case flags on,
  `caseExecutionExitsOnTaskFailure` (a failing task exits and the case keeps
  running instead of faulting) and `caseExecutionUsesTaskExitRules` (the rules
  react to exits). Call `.exitOnTaskFailure()` on the `casePlan()` chain alone
  for a case that wants the exit behaviour without a rule. Call
  `.exitOnTaskFailure(false)` or `.taskExitRules(false)` only to keep the old
  behaviour, which makes every `task-exited` rule a no-op
  (`TASK_EXITED_IGNORED`). A decompiled plan carries the calls explicitly, so
  keep them.

<!-- RULE:case.task-exit.cli -->
- The rule needs an SDK and a `uip` that both know it: SDK 6.125.0 or later
  and `uip` 1.207.0 or later. An SDK without it answers `UNKNOWN_RULE`
  (`Unknown rule "task-exited"`) at `check --source`.
  A `uip` that knows it lists `task-exited` under `task-entry` and `stage-exit`
  in `uip maestro case rule-types list --output json`; one that does not
  rejects the rule at `validate` as an invalid discriminator.
<!--skill-flavor:task-exit-upgrade:start-->
  Upgrade the one that is behind (the SDK with `npm install -g
  @uipath/maestro-builder-sdk@latest`), then compile. If `uip` still does not
  list `task-exited` after the upgrade, no `uip` on this machine supports the
  rule yet: stop and tell the user. Do not author the rule, and never write a
  different rule in its place. Never remove a rule the plan already has to
  pass.
<!--skill-flavor:task-exit-upgrade:end-->

## Design fidelity

<!-- RULE:case.sdd.declared-shapes -->
- When the request supplies an SDD, its declared task TYPES are part of the
  contract, not a hint. A task the SDD calls `process` stays a process even when
  an agent looks like a better fit for the described work, and a
  `wait-for-timer` stays a timer even when its duration reads like a connector
  poll. Substituting the type silently answers a different question, and no
  static check can see it because both spellings validate. Where the SDD is
  genuinely unresolvable, use `.unresolved('<kind>')` — which preserves the
  declared kind — rather than picking a different one.

<!-- RULE:case.sdd.output-contract -->
- The SDD's Out-variable table is a three-part contract:

  1. **Declaration.** Every SDD Out-variable needs a case-level `.output()`
     that reserves the variable.
  2. **Production.** At least one task must write the variable. For a
     non-action task, use `.outputs({ name: <source> })`. For an action
     task, map a form field to the case variable through the field's
     `value` in `.action({ outputs: [{ name, value }] })` — do not add a
     custom `.outputs()` entry, which creates a duplicate row that
     `validate --sdd` reports.
  3. **Casing and paths.** Output keys and extract paths must match the
     SDD's field names character-for-character, including casing. When
     the SDD declares a sub-property dereference, extract it from the
     producing task's own output root: `=response.<field>` on a connector
     or wait-for-connector task, `=<OutputName>.<field>` on other types.
     An output argument that is an object named `response` is therefore
     read `=response.<field>` on any type: `uip maestro case tasks describe
     --type <TASK_TYPE> --id <ENTITY_KEY> --output json` lists it in
     `Data.Outputs[]` as `name: "response"`, `type: "jsonSchema"`,
     `_jsonSchema.type: "object"`. Keep that source through `check`'s
     `REFERENCE_OUTPUT_SOURCE`, which compile does not run.
     When the SDD dereferences in place (e.g. inside a `$xref`
     expression), keep the SDD's casing and null-guard it:
     `vars.analysisResult?.unusualClauses`.

## Metadata fidelity

<!-- RULE:case.metadata.intsvc-activity-config -->
- A new case carries `metadata.intsvcActivityConfig: "v2"`. `case init` writes
  it on a new case; `decompile` → `compile` preserves whatever the plan's
  metadata carried. Never add `"v2"` to a decompiled plan that lacks
  it — a V1 plan must stay V1. Tasks that call Integration Service use V2 I/O
  negotiation when the marker is present.

<!-- RULE:case.variable.closed-types -->
- Case variable `type` values are a closed set: `string`, `integer`, `float`,
  `double`, `boolean`, `datetime`, `date`, `time`, `object`, `file`, `array`,
  `jsonSchema`. These apply to `variables.inputs`, `variables.outputs`, and
  `variables.inputOutputs`. Do not use `number` (that is a Flow SDK type, not
  a Case type); use `integer` for whole numbers, `float` or `double` for
  decimals. `case validate` warns `number` (`CASE_MGMT_VARIABLE_TYPE_ALIAS`);
  write `double`.

## Brownfield editing

<!-- RULE:case.brownfield.pipeline -->
- Start with `uip maestro case decompile <plan> -o <Name>.case.ts --no-pipeline`.
  Edit the generated `.case.ts` and retain `preserveCaseJson(...)`: it keeps
  the foreign metadata the typed surface does not own. Compile back into the
  same plan: `uip maestro case compile <Name>.case.ts -o <plan>`.
<!--skill-flavor:sdk-upgrade:start-->
  Needs `@uipath/maestro-builder-sdk` 6.50.1 or later, which resolves the decompiled
  labels (for example `bOC1`) against that plan's own `bindings` array; an
  older SDK writes the label in as the key, so upgrade first.
<!--skill-flavor:sdk-upgrade:end-->
  Do not pass
  `--bindings <plan>`: it replaces `bindings.json`, so a connector the edit
  adds loses its mapping. Do not run `<Name>.pipeline.mjs`: it writes a plan
  pack and debug never read. Strict decompile fails closed on unresolved
  references. For an explicitly broken input, rerun
  with `--best-effort`, inspect every reported diagnostic, and replace every
  `__UNRESOLVED_*` marker before checking or compiling the repair. Removing or
  repointing a bound task also requires the orphan cleanup under
  [Connections and external work](#connections-and-external-work); compilation
  and resource refresh do not remove solution declarations.

<!-- RULE:case.brownfield.recompile -->
- Repair by recompiling from source, not by editing the emitted JSON. The
  compiler owns everything synthetic in the plan — a formal argument's slot `id`
  is minted from its name rather than copied from it, task and condition ids are
  derived, and companions are wired to match. A hand-edit fixes the field you
  looked at and leaves the derived ones carrying whatever the broken input had,
  which plain `uip maestro case validate` does not report. `--strict` rejects a
  slot id copied from its name (`STRICT_FORMAL_ARG_ID`), but neither profile
  checks that task and condition ids match their derived form, so `Valid` from
  either does not prove a hand-edit is complete. Round-tripping the whole plan
  re-derives all of them at once.

### Check only what you changed: `check --baseline`

`check` judges the whole case. In an existing plan it also reports defects the
plan already had on stages and tasks you never touched, for example
`TASK_NO_ENTRY` on a task the Designer saved with no entry rule. Those would
fail every edit. Pass the original plan as `--baseline` and each finding says
whether your edit caused it.

The baseline must be the plan as it was before your first compile: compile
writes back into the same plan, so after it the file on disk is your edit.
Never pass that plan itself as `--baseline`: the edit compared with itself
reports every finding as pre-existing, so `check` passes with errors in it.
<!--skill-flavor:check-baseline-original:start-->
At the start of each editing session, before its first compile, copy it aside
and check against the copy. Overwrite any copy an earlier session left: an old
copy would count that session's changes as yours.

```bash
mkdir -p .flow-sdk/original && cp <project>/<plan> .flow-sdk/original/
uip maestro case check <Name>.case.ts --source --baseline .flow-sdk/original/<plan>
```
<!--skill-flavor:check-baseline-original:end-->

```text
✗ [TASK_NO_ENTRY] Task "Escalate" in stage "Intake" has no entry rule — ... (edited)
⚠ [TASK_NO_ENTRY] Task "Archive" in stage "Intake" has no entry rule — ... (pre-existing, not counted)
check: 1 error(s) in edited parts of the case, 0 pre-existing SDK defect(s), 1 pre-existing warning(s).
```

- **`(edited)`** (JSON `origin: "edited"`): fix it. The finding is on a stage,
  task or trigger you added or changed (a renamed task counts as changed), or
  it is new on one you did not touch, so your edit caused it. The exit code is
  1 only while one is left.
- **`(pre-existing, not counted)`**: the original reports the same code on the
  same unchanged stage, task or trigger. Leave it unless the user asked you to
  fix it. A finding that names no stage or task (a case-level rule) is
  pre-existing only when the original reports the same code and message.
- **`(pre-existing)` worded as a probable SDK defect** (JSON
  `class: "lowering"`): `compile` refuses that task even though you did not
  change it, so the compile stops on it. Do not edit the task to get around
  it. Stop, name the task and the code, and tell the user it is a probable SDK
  defect to report at <https://github.com/UiPath/builder-sdk/issues>.
- **`CHECK_INCOMPLETE`**: check stopped before it judged the whole case. Fix
  the error it names, even if the original has it too, then check again.
- **`--baseline ... is not the plan this source was decompiled from`** (exit
  2): the file you passed is not the original, most often the plan after a
  compile wrote your edit into it. Pass the copy you made before the first
  compile. If you no longer have it, decompile the current plan again and use
  that plan as the baseline from now on.

<!--skill-flavor:check-baseline-sdk-upgrade:start-->
Needs two releases: `@uipath/maestro-builder-sdk` 6.97.0 or later, and the
`uip` release that carries UiPath/cli#6081 (`uip` 1.205.0 does not).
- `unknown option '--baseline'` means `uip` is too old, whatever the SDK
  version. Upgrade `uip`. Upgrading the SDK alone gives the same error again.
- `--baseline on case check needs a @uipath/maestro-builder-sdk release that
  supports it` means `uip` is new enough and the SDK is not. Upgrade with
  `npm install -g @uipath/maestro-builder-sdk@latest`.

Until both are upgraded, run `check --source` without `--baseline`. In this
fallback only, fix only the errors on stages and tasks you changed, even
though the exit code stays non-zero.
<!--skill-flavor:check-baseline-sdk-upgrade:end-->

## Product boundary

<!-- RULE:case.validation.layers -->
- TypeScript checks call shape, `case check` checks source semantics, and
  `uip maestro case validate` checks the compiled product contract. Run all
  applicable layers; use live debug only when execution is part of the task.
