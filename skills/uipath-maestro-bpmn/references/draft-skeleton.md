# Draft first — the skeleton

Author a blank-box skeleton with real control flow and labels, compile and validate it, show it to the user, and stop for approval. Make no registry calls.

**When.** Draft when the user asks for a draft or wants to see the shape before it is built: *create a draft*, *outline it*, *show me the shape*, *sketch it*, *what would it look like*, *before you build it*, or a session in plan mode; these always gate, even when the request describes the whole process. A request whose wording leans toward a draft without saying it (*a rough version*, *a first pass*, *a quick mock-up*) gets the draft, unless it also says outright to build or deploy the whole process. That exception is for leaning wording only. Build directly for an outright build request. Brownfield edits, [discovery-only](bpmn-runtime.md#registry-extension-types) questions (nothing authored), and source-only "draft project" or "draft handoff" requests (files to import or hand off, with no upload or run) also skip the draft: they are builds. Never ask whether to draft or build, and never block on that choice: decide from the request, and build when nothing in it asks for a draft or to see the shape first. Plan mode is the host's state; never enter it yourself. For an unresolved connector, follow [Draft with an unresolved connector](connectors.md#7-draft-with-an-unresolved-connector).

**The deliverable is a file.** A chat diagram or prose outline is not a draft. Write `.bpmn.ts`, run [Steps](#steps), and only then reply. The deliverable is the compiled, formatted, validated `<Project>/<Name>.bpmn`, which opens on the canvas.

**In plan mode, writes wait for plan approval.** Put the ordered boxes, decisions, conditions, and start event in the plan. After approval, build and validate the file, then apply the same gate.

## What a skeleton is

A skeleton is not a working process and must never be reported as one.

1. Make every activity a bare `.task(id, { name })`; pass only `name`, except per-item `loop` (rule 8), with no `set`. Use a body callback only for `onError` or `onTimer`; it compiles to plain `<bpmn:task>` with no `uipath:activity` payload.
2. Use no typed activity method: not `scriptTask`, `humanTask`, `http`, `connector`, `externalAgent`, `externalWorkflow`, `dataService`, `businessRule`, Orchestrator start/execute/queue methods, or `activity`. The label carries the kind (rule 5).
3. Make no registry calls: no `uip maestro bpmn registry pull`, `search`, or `get`. Choose types after approval. After the skeleton validates, immediately before the gate, look up each box's resource as [Find the resources](#find-the-resources) says; these tenant reads are not registry calls.
4. Use real control flow:
   - Use the actual start event: plain for a caller, `{ timer }` for a schedule, or `{ message: '<name>' }` for a message. `{ timer: { cycle: 'R/2026-01-05T07:00:00Z/P7D' } }` means every Monday at 7:00 UTC; use the user's UTC offset instead of `Z` for local time, `Z` when none is stated, and a duration string for a one-off delay. Never set `trigger: true`; it adds the platform trigger's `uipath:activity` payload and is a build-time decision.
   - Keep start-event id `Event_start`, named by the `init` stub and `entry-points.json`, and keep seeded `.metadata({ entryPointId })`. Change its name and definition, never its id.
   - Use `.choose()` with `when` on every arm except one `otherwise: true` arm; use `.fork()` for parallel splits. Arms rejoin at the next statement through the builder's join, so branches converge on one end event unless separate outcomes are requested. A separate outcome inside a `.fork()` branch ends with `terminate: true` (rule 9). Do not simplify requested branch structure.
   - Declare requested handlers in the box callback: `onError((h) => ...)`; interrupting `onTimer('PT10M', (h) => ...)`; non-interrupting `onTimer('PT10M', { interrupting: false }, (h) => ...)`. A non-interrupting path must end in its own `.endEvent()`; `check` rejects fall-through. Filter one error with `onError({ name: 'ServerError', code: '500' }, (h) => ...)`, or catch all with `onError(true, (h) => ...)`. Every later `onError` on a box needs its own id or `check` fails `BPMN_DUP_BOUNDARY_ID`, e.g. `onError({ name: 'ServerError', code: '500' }, { id: 'pack_on500' }, (h) => ...)` beside `onError(true, { id: 'pack_onAnyError' }, (h) => ... )`.
5. Label each box action-first and kind-last in brackets, e.g. `Extract invoice data [RPA workflow]`, `Manager review [Action app]`, `Classify ticket [Agent]`, `Notify the team [Slack]`. Use [Box kinds](#box-kinds); when several fit, choose what a Studio Web user most likely chooses. The user may change it at the gate.
6. Label every decision arm with its outcome (`label: 'Approved'`). Fork branches have no label.
7. Declare decision variables with `.var()`, or start-provided values with `.input()`. The routing basis is part of approval. A skeleton may read but not assign variables; name the upstream producer, e.g. `Classify ticket [Agent] → category`. Declare a start input with `.input(<id>, '<type>')`; never draw a box only to receive, read, or capture it. A decision or per-item box reading an input reads the variable mapped by the start event; write that mapping (the skeleton's one payload) with `.var()` scoped to `Event_start`, as in [Process contract](bpmn-runtime.md#variables-and-the-process-contract). Data supplied after start is a real `[Action app]` step.
8. For a per-item step, pass `loop: { collection, itemVar }` on its own `.task()` and declare the collection with `.var(<id>, 'array')`, or `.input(<id>, 'array')` when start-provided and read through its mapping. Add `sequential: true` only for one-at-a-time execution; omit it when concurrent or unspecified. For early stop, add `completion: '=js:vars.<flag>'` and declare the boolean flag. Do not hand-roll this with a gateway and `.goto()`, or defer the marker to *Build it*.
9. A path leaving a `.fork()` branch early must end the process; other paths continue to the join. Fork and join fire only after every incoming flow delivers; `check` and `validate` do not catch stalls:
   - A plain `.endEvent()` in a branch, `.choose()`/`.race()` arm, or interrupting handler consumes the token and leaves the join waiting.
   - A `.goto()` into a sibling branch, past the join, into the join while that branch also reaches it, or from anywhere (including after the join) targeting the `.fork()` breaks the count or prevents firing.
   - An interrupting handler that does not end rejoins after the activity; on a branch's last activity this is the fork join, but the cancelled activity flow does not deliver and the handler is an extra input.
   - A `.goto()` into a fork gives it a second incoming flow.

   Write the safe shape:
   - When the failure or outcome stops the process, end its path in `.endEvent(<id>, { name, terminate: true })`, or `.endEvent(<id>, { name, error: '<ErrorName>' })` when a caller or event sub-process handles it—never both: `terminate: true` drops the error. Continue after a `.choose()` or `.race()` arm with neither end event nor `.goto()`. Continue after a handler by writing another statement on that branch so it rejoins once; a bare `.exclusiveGateway()` inside a branch does not compile, so merge on a box. Retry a whole parallel block by targeting the box immediately before `.fork()`, never the fork; add that box when the fork directly follows the start. A non-interrupting handler leaves its step running and ends in its own end event (rule 4); its `.goto()` must not target the fork or a node reaching `<fork>_join`. Rule 9 does not apply to the end event closing a `.subProcess()` body, which continues on its branch.

### Box kinds

Use these exact Studio Web toolbox names. A connector box uses the user's app name (`Slack`, `Outlook`, `Jira`), not `Connector`; use `Connector` only when no app is named.

| Step | Kind |
|---|---|
| A person reviews, approves, or fills a form | Action app |
| An unattended robot job | RPA workflow |
| An AI agent decides or extracts | Agent |
| An API workflow | API workflow |
| A coded function | Function |
| A deployed business rule | Business rule |
| A call to an outside app | `<App>` |
| Another Maestro BPMN process, case, or flow | Maestro BPMN, Maestro Case, Maestro Flow |
| An inline calculation | Execute script |
| An HTTP call with no connector | Execute HTTP request |

## A worked skeleton

"Every Monday at 7, count the warehouse stock; when any item is below its reorder point, raise purchase orders for them, otherwise just log the count."

```ts
import { bpmn } from '@uipath/maestro-builder-sdk/bpmn';

export default bpmn('Process_1')
  .name('WeeklyStockCheck')
  .metadata({ entryPointId: '<the UUID the decompiled stub carries>' })
  .flowMode('sequence')
  .var('itemsBelowReorder', 'number')
  .startEvent('Event_start', { name: 'Every Monday at 7:00', timer: { cycle: 'R/2026-01-05T07:00:00Z/P7D' } })
  .task('countStock', { name: 'Count warehouse stock [RPA workflow] → itemsBelowReorder' })
  .choose('needsReorder', [
    { when: '=js:vars.itemsBelowReorder > 0', label: 'Below reorder point', body: (b) => b.task('raiseOrders', { name: 'Raise purchase orders [API workflow]' }) },
    { otherwise: true, label: 'Stock is fine', body: (b) => b.task('logCount', { name: 'Log the stock count [Execute script]' }) },
  ])
  .endEvent('done', { name: 'Stock checked' })
  .build();
```

It compiles to three bare `bpmn:task` boxes, a timer start, an exclusive gateway with a condition and a default, a join, and an end event.

### Per-item boxes and fork exits

"Verify the new hire's documents one at a time and stop at the first failure. Then set up accounts and payroll in parallel: if account setup fails, IT creates them by hand; if payroll fails, stop the onboarding; chase payroll after an hour. Welcome every team the hire joins."

```ts
// standard imports, .name(), .metadata() and .flowMode() omitted
  .var('documents', 'array')
  .var('documentFailed', 'boolean')
  .var('teams', 'array')
  .startEvent('Event_start', { name: 'New hire submitted' })
  .task('verifyDoc', {
    name: 'Verify document [Action app] → documentFailed',
    loop: { collection: '=js:vars.documents', itemVar: 'document', sequential: true, completion: '=js:vars.documentFailed' },
  })
  .fork('setup', [
    (b) => b
      .task('createAccounts', { name: 'Create accounts [RPA workflow]' }, (a) => a
        .onError((h) => h.task('createByHand', { name: 'Create accounts by hand [Action app]' })))
      .task('confirmAccounts', { name: 'Confirm accounts [Execute script]' }),
    (b) => b
      .task('registerPayroll', { name: 'Register in payroll [API workflow]' }, (a) => a
        .onError((h) => h.task('alertHr', { name: 'Alert HR [Connector]' }).endEvent('stopped', { name: 'Onboarding stopped', terminate: true }))
        .onTimer('PT1H', { interrupting: false }, (h) => h.task('chasePayroll', { name: 'Chase payroll [Connector]' }).endEvent('chased', { name: 'Payroll chased' }))),
  ])
  .task('welcome', { name: 'Welcome the hire [Connector]', loop: { collection: '=js:vars.teams', itemVar: 'team' } })
  .endEvent('done', { name: 'Onboarded' })
  .build();
```

`createByHand` rejoins at `confirmAccounts`, so the first branch reaches `setup_join` on one flow.
Without `confirmAccounts`, the compiled file carries `createByHand → setup_join` beside `createAccounts → setup_join`, and the join never fires after a failure.

## Steps

<!--skill-flavor:draft-steps:start-->
1. Before `init`, run the solution scan in step 1 of [SKILL.md](../SKILL.md#workflow), ask which solution to use when that step says to, and run `init` only after the solution is settled. From that step's directory run `uip maestro bpmn init <Name> --output json`; take the project directory from `Data.Path`; the commands below write it as `<Project>`. Outside a solution it is `<Name>Solution/<Name>/`, not always `<Name>/`. If the user named the destination, run the path-specific `init` command from step 1 of [SKILL.md](../SKILL.md#workflow). Seed `<Name>.bpmn.ts` with `uip maestro bpmn decompile <Project>/<Name>.bpmn -o <Name>.bpmn.ts --style nested`, as in [SKILL.md](../SKILL.md#workflow).
2. Rewrite the chain as the skeleton in one write, retaining the seeded process id, `entryPointId`, and start-event id.
3. Run the loop:

   ```bash
   uip maestro bpmn check <Name>.bpmn.ts --source
   uip maestro bpmn check <Name>.bpmn.ts --graph
   uip maestro bpmn compile <Name>.bpmn.ts -o <Project>/<Name>.bpmn
   uip maestro bpmn format <Project>/<Name>.bpmn
   uip maestro bpmn validate <Project>/<Name>.bpmn --output json
   ```

   `validate` must report `Status: Valid`.
<!--skill-flavor:draft-steps:end-->
Between `check --graph` and compile, audit every `.fork()` for rule 9; neither `check` nor `validate` does this:
- In `.bpmn.ts`, every `.endEvent(` inside a fork-branch callback has `terminate: true` or `error`, except a non-interrupting handler path or `.subProcess()` body close.
- Every `.goto()` from a fork-branch callback targets a node declared there, or `<fork>_join` when that is the branch's only flow into the join. Reject sibling, past-join, duplicate-join, fork, and pre-fork targets. This also applies to `decompile` output: a sibling jump leaves the join's `Incoming` count unchanged, so `check --graph` cannot prove safety. A non-interrupting handler's `.goto()` is exempt when its target cannot reach `<fork>_join`.
- No `.goto()` anywhere targets a `.fork()` id; whole-block retries target the preceding box.
- In `check --graph`, under `Data.Graph.Nodes`, `<fork>_join` has `Incoming` no larger than the `<fork>` node's number of `Outgoing` entries. A larger value means an extra handler or decision-arm path reaches the join.

Fix every finding using rule 9 before compile.
<!--skill-flavor:draft-steps-no-refresh:start-->
Because the start event remains `Event_start`, `init`'s `entry-points.json` still matches and no `refresh` is needed. If `validate` fails with `entry-points.json references start event "Event_start"`, restore `Event_start`.
<!--skill-flavor:draft-steps-no-refresh:end-->
<!--skill-flavor:draft-upload:start-->
4. **Upload it, so the user sees it on the canvas**, unless the request forbids upload: run `uip solution upload <SolutionDir> --output json`, where `<SolutionDir>` is the solution scaffolded by `init` (`<Name>Solution/`) or the one where it registered the project. The gate reply carries `Data.DesignerUrl`. Do not ask first when this run created the solution (`init` or `uip solution init` did so): the draft request authorizes this showing upload. If the solution already existed, check its cloud copy before overwriting, as [Studio Web upload](operate.md#studio-web-upload) says. Upload without asking only when the user selected it from the solution question, which warned that upload overwrites its cloud copy; otherwise do not upload because the gate's one sentence waits for go-ahead. A skeleton needs no other section pre-flight: it keeps `Event_start`, needs no `refresh`, and binds no resource. If upload is forbidden or no solution exists (the user named a path and chose none), do not upload or create a solution; the gate carries the local path. Do not pack, debug, or run; these require separate approval.
<!--skill-flavor:draft-upload:end-->
5. **Find each box's resource**, as [Find the resources](#find-the-resources) says, then reply as [Show the shape and stop](#show-the-shape-and-stop) says.

### Expected findings — do not chase them

A skeleton may be **Valid** with `Variable "vars.<id>" is read but never assigned; it will be empty at run time`; blank producers make this correct. Error paths merging onto a box may also produce `[FAKE_JOIN] "<box>" has <n> incoming flows; the platform accepts this, but joining with a gateway is clearer`; this is intended. Act only on errors and `VARIABLE_NOT_SET`, which means a decision reads an input without the start-event mapping (rule 7). Do not report these expected warnings; they get no reply line.

## Find the resources

A deployed-resource kind cannot be built without one: every [Box kinds](#box-kinds) kind except `Action app`, `Execute script`, and `Execute HTTP request`, including Business rule, plus queues, Data Fabric entities, and connector connections.
<!--skill-flavor:lookup-no-login:start-->
When this run already found no `uip login` (the upload failed for it), skip lookup and mark each such box `not checked`. Otherwise run every lookup in **one** Bash call.
<!--skill-flavor:lookup-no-login:end-->
Lookups only read the tenant, so upload/run prohibitions do not prohibit them. They are the final tool call: before them read [gate-reply-template.md](gate-reply-template.md), search the target for each box's `id="<id>"` as [End the turn](gate-reply-template.md#end-the-turn) says, and send any progress note. Afterward send the gate reply as the next and final message, beginning with its first line.

- **Processes and queues:** run `uip solution resources list --kind <Process|Queue> --search "<term>" --output json`. It lists solution (`Source: Local`) and tenant (`Source: Remote`) resources. For `--kind Process`, match `Type`: RPA workflow `process`, API workflow `api`, Agent `agent`, Maestro BPMN `processOrchestration`, Maestro Case `CaseManagement`, Maestro Flow `Flow`, Function `function`.
- **Connections:** when any box is a connector or Data Fabric entity, run once (even with no provider); otherwise skip. No connector key or `--limit`:

  ```bash
  uip is connections list --all-folders --output-filter "[?contains(ConnectorName,'<WORD>')].{Connector:ConnectorName,Connection:Name,State:State,IsDefault:IsDefault,Folder:Folder}" --output json
  ```

  Replace the `contains(...)` test with one per service joined by `||`. For a named app use one distinctive, normally capitalized word (`Slack`, `Outlook`, `SharePoint`, `Jira`, `Salesforce`), case-sensitive; never its full unknown display name. For a box that names no provider, such as "send an email", use exact names, never `contains(...,'Mail')` (it also matches Mailchimp and Mailgun): `ConnectorName=='Gmail'`, `ConnectorName=='Microsoft Outlook 365'`, `ConnectorName=='Mail'`, `ConnectorName=='Exchange Server'`. Add `ConnectorName=='UiPath Data Fabric'` for a Data Fabric entity. Match connector boxes on `Connector` only because keys can contain another service's name (the Slack connector's key contains `salesforce`). Prefer `State: Enabled`, then the named folder, then `IsDefault: Yes`. An empty service result is `none yet`; never say the tenant has no such connection.
- **Business rules:** run `uip rules list --all-folders --limit 10000 --output-filter "[].{Name:Name,FolderPath:FolderPath}" --output json`, matching name and folder path.
- **Data Fabric entities:** run `uip df entities list --include-folders --output-filter "[?contains(Name,'<KEYWORD>') || contains(Name,'<keyword>')].{Name:Name,FolderId:FolderId}" --output json`, matching `Name` only. The row has folder id, not folder name, so do not put a folder on the box line. Never list unfiltered. `contains` is case-sensitive: test each label keyword as written, capitalized, lowercase, and a stem plural (`Compan` for `companies`, matching `Company` and `Companies`), joined by `||`. The box also needs the `UiPath Data Fabric` connection.

Run each lookup exactly as written and add no flags: `uip` rejects `--output-filter` on `uip solution resources list` without `--limit`, and rejects `--limit` on every `uip is` and `uip df` list. `--search` matches names only; never list a kind unfiltered, including after an empty search. Put every search in the one lookup call: the user's resource words plus one or two label keywords (`invoice`, `extract` for `Extract invoice data [RPA workflow]`). If a lookup fails, mark its boxes `not checked`, state why in the gate's permitted first-line sentence, and do not retry.
<!--skill-flavor:lookup-not-checked-rule:start-->
Mark a box `not checked` only when its lookup ran and exited non-zero, or when this run already found no `uip login`; never write it for a lookup not run.
<!--skill-flavor:lookup-not-checked-rule:end-->
A failed lookup proves nothing is missing: say `Couldn't check your Slack connections`, never `No Slack connection in this tenant`, and never name a connector key, kind, or CLI term.

Give each box one status:
- Use a user-named resource or the sole fitting row, naming it and its folder when present.
- For several fits, name the best two and ask which.
- For none, write `none yet, create it or name one`; the user can create/name one or choose *Change it*.
- `Action app`, `Execute script`, and `Execute HTTP request` need no lookup: write `no resource needed`. `Action app` has this status even when the user named an Action App; it is built as an inline form ([Human task outcomes](bpmn-runtime.md#human-task-outcomes)).

A row fits only when its kind matches (`Type` as above) and its name and folder show it performs the box's step. Shared keywords alone do not fit: a process called `invoice-cleanup` in an unrelated project's folder is not the invoice-recording step; if uncertain, treat it as none and never bind it. Run lookup again at every gate so newly created resources appear.
<!--skill-flavor:gate-one-round:start-->
This gate is the one round for structure and resource questions. A pre-skeleton question, such as which solution to use, comes before it.
<!--skill-flavor:gate-one-round:end-->

## Show the shape and stop

Read [gate-reply-template.md](gate-reply-template.md) in full, then end the turn with that reply exactly: template and nothing else, with no line before, between parts, or after.

## After the answer

<!--skill-flavor:draft-cloud-copy:start-->
When the skeleton was uploaded, the user may have edited it on the canvas. Before editing, download and compare the cloud copy as [Check the cloud copy](operate.md#check-the-cloud-copy-before-editing) says; if different, build on it without asking using that section's *To build on the Studio Web copy* paragraph (copy it over `<Project>/<Name>.bpmn`, then decompile and `merge`), not compile and `format`, so layout survives. Mention this in the reply's one sentence.
<!--skill-flavor:draft-cloud-copy:end-->

<!--skill-flavor:draft-change-it:start-->
- **Change it**: edit the skeleton, rerun the loop, and show it as steps 4 and 5. When building on the cloud copy, use `merge` instead of the loop's `compile` and `format` ([Brownfield](bpmn-runtime.md#brownfield-editing)).
<!--skill-flavor:draft-change-it:end-->
  In a sequence scope, deleting a `.task()` removes the box and rewires neighbors; reread `check --graph` after editing.
- **Build it**: replace each `.task()` with the typed method named by its label, retaining its id, and author real payloads, registry calls, bindings, and connections. Bind resource-requiring boxes to the gate's named resource by name and folder; bind connector boxes through their connection binding, as [Connectors and bindings](bpmn-runtime.md#connectors-and-bindings) says. Ask nothing more about structure or resources. An open value (rate, threshold, formula) is not a question: choose a plausible value, name it under `Assumed`, and never invent an identifier or URL part.
<!--skill-flavor:draft-build-merge:start-->
  When this turn's source was decompiled from the current target or an earlier `merge` wrote it, finish through `merge` as for an existing process. Only a skeleton reaching the target through compile alone is compiled and formatted as the loop says; its source has the `init` stub's decompile stamp, so `merge` refuses it (`MERGE_ORIGINAL_CHANGED`).
<!--skill-flavor:draft-build-merge:end-->
  An Action app becomes inline-form `.humanTask`, as [Human task outcomes](bpmn-runtime.md#human-task-outcomes) says, never `.humanTask(id, { app })`. If the user named an Action App, say under `Assumed` that it is an inline form, not their app, and Studio Web can switch it.
  A gate-marked `none yet` process-running box (RPA workflow, Agent, API workflow, Function, Maestro BPMN, Case, or Flow) gets a placeholder binding pair shaped as [RULE `bpmn.orchestrator.in-solution-process`](bpmn-runtime.md#http-and-orchestrator-work): `value` and `resourceKey` are a short label-derived name (`PilotEmailExtractor`), `resourceSubType` is its `ProcessType` from [RULE `bpmn.orchestrator.process-type`](bpmn-runtime.md#http-and-orchestrator-work) (`Process`, `Agent`, `Api`, `Function`), and folder binding has no value.
  Every other `none yet` box (connector, Data Fabric, Business rule, or queue) stays a bare `.task()` because `refresh` rejects a non-connection-id binding. Name connector/Data Fabric boxes as the second bullet of [Draft with an unresolved connector](connectors.md#7-draft-with-an-unresolved-connector) says; retain the gate label for Business rule/queue. List these under `Needs:` as `built, not runnable yet`.
  A gate-named connection is the user's choice after *Build it*, including their personal one, unless it belongs to another person or is not `State: Enabled`; then treat the box as `none yet`, per [connection rules](connectors.md#3-the-loop-author--check--prepare--check--compile). For an unanswered two-resource choice, use the first named resource and report it under `Assumed`. Look up `not checked` boxes now using [Find the resources](#find-the-resources). A real trigger, renamed start event, or new entry point requires `uip maestro bpmn refresh` before `validate`, as [SKILL.md](../SKILL.md#workflow) step 7 says. End with [final report](final-report-template.md), as [SKILL.md](../SKILL.md#workflow) step 9 says; its first line says `(draft mode)` because this run stopped at a gate.
- **Keep it**: stop and report the file as an outline, not a working process.

Only *Build it* authorizes the build. Until then the skeleton is an outline; calling it finished misreports it.
