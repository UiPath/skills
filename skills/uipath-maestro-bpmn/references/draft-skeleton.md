# Draft first — the skeleton

Author a skeleton of blank boxes, real control flow and labels, compile and validate it, show it to the user, and stop for their approval.
It makes no registry calls.

**When.** The user wants to see the shape before it is built: *show me the shape*, *sketch it*, *what would it look like*, *before you build it*, or a session in plan mode.
A request to build the process outright skips the draft and authors real nodes directly.
A brownfield edit (the shape already exists) and a discovery-only question (nothing is authored) skip it too.
Never ask the user whether to draft or build, and never block on that choice: decide from the request, and build when nothing in it asks to see the shape first.
Judge the intent, not the word: a "draft project" or "draft handoff" that asks for a source-only deliverable (files to import or hand off later, with no upload or run) is a build, not the draft gate.
A connector step it cannot resolve then follows [Draft with an unresolved connector](connectors.md#7-draft-with-an-unresolved-connector).
Plan mode is the host's state: never enter it yourself to satisfy "show me first".

**The deliverable is a file.**
A mermaid or ASCII diagram in chat is not a draft, and neither is a prose outline: the draft is the compiled, formatted, validated `<Project>/<Name>.bpmn`, which opens on the canvas.
Write the `.bpmn.ts`, run the loop below, and only then reply.

**In plan mode, writes wait for plan approval.**
Put the skeleton outline in the plan instead — each box's label in order, the decisions with their conditions, the start event — and build the file with the steps below once the plan is approved.
The gate below then comes after the file validates, as it does outside plan mode.

## What a skeleton is

A skeleton is not a working process and must never be reported as one.

1. **Every activity is a bare `.task(id, { name })`.**
   Pass `name` and nothing else, except `loop` on a box that runs once per item (rule 8): no `set`.
   Give a box a body callback only to declare its `onError` or `onTimer` handlers (rule 4).
   It compiles to a plain `<bpmn:task>` with no `uipath:activity` payload.
2. **Use no typed activity method** — not `scriptTask`, `humanTask`, `http`, `connector`, `externalAgent`, `externalWorkflow`, `dataService`, `businessRule`, the Orchestrator start/execute/queue methods, or `activity`.
   The label carries the kind (rule 5).
3. **Make no registry calls.** No `uip maestro bpmn registry pull`, `search` or `get`.
   Types are chosen after the shape is approved.
   Each box's resource is looked up once the skeleton validates, just before the gate ([Find the resources](#find-the-resources)); those lookups read the tenant and are not registry calls.
4. **Control flow is real.**
   - The start event is the one the process actually has: plain when something calls it, `{ timer }` when it runs on a schedule (`{ timer: { cycle: 'R/2026-01-05T07:00:00Z/P7D' } }` for every Monday at 7:00 UTC; use the user's UTC offset in place of `Z` when they give a local time, and `Z` when they state none; a duration string for a one-off delay), `{ message: '<name>' }` when a message starts it.
     Do not set `trigger: true`: it adds the platform trigger's `uipath:activity` payload, which is a build-time decision.
   - Keep the start event's id `Event_start`, the id the `init` stub carries and `entry-points.json` names, and keep the seeded `.metadata({ entryPointId })`.
     Change the start event's `name` and definition, never its id.
   - Write decisions with `.choose()`: a `when` on every arm but one, and an `otherwise: true` arm for the default.
     Write a parallel split with `.fork()`.
     Arms rejoin at the next statement through a join gateway the builder adds, so every branch converges on one end event unless the request names separate outcomes.
     Inside a `.fork()` branch, a separate outcome ends the process with `terminate: true` (rule 9).
     Do not simplify the branch structure the request describes.
   - When the request names a failure or a deadline on a step, declare it in that box's body callback: `onError((h) => ...)` for a failure, `onTimer('PT10M', (h) => ...)` for a deadline that cancels the step.
     A deadline that escalates while the step keeps running is non-interrupting: `onTimer('PT10M', { interrupting: false }, (h) => ...)`.
     A non-interrupting handler's path must end in its own `.endEvent()`; `check` rejects one that falls through.
     For one kind of error, pass it first: `onError({ name: 'ServerError', code: '500' }, (h) => ...)`; `onError(true, (h) => ...)` catches any error.
     Each `onError` after the first on one box needs its own `id`, or `check` fails with `BPMN_DUP_BOUNDARY_ID`: `onError({ name: 'ServerError', code: '500' }, { id: 'pack_on500' }, (h) => ...)` beside `onError(true, { id: 'pack_onAnyError' }, (h) => ...)`.
5. **Label each box with the action first and its kind last, in brackets** — `Extract invoice data [RPA workflow]`, `Manager review [Action app]`, `Classify ticket [Agent]`, `Notify the team [Slack]`.
   Take the kind from [Box kinds](#box-kinds).
   When several kinds could fit, pick the one a Studio Web user would most likely choose; the user changes it at the gate if they disagree.
6. **Label each decision arm** with the outcome it carries (`label: 'Approved'`), so the routing reads off the picture.
   `fork` branches take no label: every branch runs.
7. **Declare the variables the decisions read, for real**, with `.var()`.
   The basis a gateway routes on is part of what the user approves: three arms out of a diamond with no stated basis could mean anything.
   A skeleton reads a variable but cannot assign it, because the assignment lives in the payload of the node that produces it.
   Name the producer in the box upstream instead: `Classify ticket [Agent] → category`.
8. **Mark a step that runs once per item on its own box.**
   When the request says a step runs for each item ("for every line item", "notify each supplier"), pass `loop: { collection, itemVar }` on that `.task()`, and declare the collection with `.var(<id>, 'array')`.
   Add `sequential: true` when the items go one after another, and leave it out when they run all at once or the request does not say.
   When the step stops early ("stop at the first failed document"), add `completion: '=vars.<flag>'` and declare that boolean flag too.
   Do not hand-roll a loop from a gateway and a `.goto()` for a per-item step, and do not leave the marker to *Build it*: it is structure, and the user is approving it.
9. **A path that leaves a `.fork()` branch early must end the process; every other path continues on its own branch to the join.**
   A parallel gateway, the fork as well as the join, fires only when every incoming flow has delivered a token.
   Four shapes break that, and `check` and `validate` all pass them:
   - A plain `.endEvent()` anywhere inside a branch — on the branch's own path, in a `.choose()` or `.race()` arm such as a rejection, or at the end of an interrupting `onError` or `onTimer` handler — consumes the branch's token, so the join waits forever.
   - A `.goto()` inside a branch that jumps into a sibling branch, past the join, or into the join while the branch's own path also reaches it, breaks the join's count: the branch's own input to the join never delivers, or the join gets an input that never delivers, so the join waits forever.
   - An interrupting handler whose path does not end rejoins at the statement after the activity, and for a branch's last activity that statement is the fork's join.
     The handler's path then becomes an extra input to the join: the activity's own flow never delivers because the handler cancelled it, so the join waits forever.
   - A `.goto()` from anywhere, after the join included, that targets the `.fork()` itself gives the fork a second incoming flow; a parallel gateway waits for every incoming flow, so the fork never fires.

   Write the safe shape:
   - When the failure or outcome stops the process, end its path in `.endEvent(<id>, { name, terminate: true })`, or in an error end event (`.endEvent(<id>, { name, error: '<ErrorName>' })`) when a caller or an event sub-process handles the error.
     Never set both: `terminate: true` drops the error.
   - When the process carries on after a `.choose()` or `.race()` arm, give the arm no end event and no `.goto()`, so it rejoins at the next statement.
   - When the process carries on after a handler, write another statement on the same branch after the activity, such as the next box, so the handler's path rejoins there and the branch reaches the join on one flow.
     A bare `.exclusiveGateway()` inside a branch does not compile, so merge on a box.
   - To retry the whole parallel block, `.goto()` the box just before the `.fork()`, never the fork: the box merges the loop, and the fork keeps one incoming flow.
     When the fork directly follows the start event, add that box first, such as the step that prepares the retry.

   A non-interrupting handler leaves the step running on its branch and ends in its own end event (rule 4), so rule 9 lets it end separately; a `.goto()` on its path still must not target the fork or a node that reaches `<fork>_join`.
   Rule 9 also does not apply to the end event that closes a `.subProcess()` body: the sub-process then continues on its branch.

### Box kinds

The short names Studio Web's BPMN toolbox shows; write each exactly as it appears here.
A connector box names its app as the user names it (`Slack`, `Outlook`, `Jira`), not `Connector`; write `Connector` only when the request names no app.

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
    { when: '=vars.itemsBelowReorder > 0', label: 'Below reorder point', body: (b) => b.task('raiseOrders', { name: 'Raise purchase orders [API workflow]' }) },
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
    loop: { collection: '=vars.documents', itemVar: 'document', sequential: true, completion: '=vars.documentFailed' },
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
  .task('welcome', { name: 'Welcome the hire [Connector]', loop: { collection: '=vars.teams', itemVar: 'team' } })
  .endEvent('done', { name: 'Onboarded' })
  .build();
```

`createByHand` rejoins at `confirmAccounts`, so the first branch reaches `setup_join` on one flow.
Without `confirmAccounts`, the compiled file carries `createByHand → setup_join` beside `createAccounts → setup_join`, and the join never fires after a failure.

## Steps

<!--skill-flavor:draft-steps:start-->
1. Before `init`, run the solution scan in step 1 of [SKILL.md](../SKILL.md#workflow), and ask which solution to use when that step says to; run `init` only once the solution is settled.
   Run `uip maestro bpmn init <Name> --output json` from the directory that step places the project in, and take the project directory from its `Data.Path`; the commands below write it as `<Project>`.
   It is not always `<Name>/`: outside a solution, `init` scaffolds one and the project lands at `<Name>Solution/<Name>/`.
   When the user named where the `.bpmn` goes, run the `init` command that step 1 of [SKILL.md](../SKILL.md#workflow) gives for that path instead.
   Then seed `<Name>.bpmn.ts` from the stub with `uip maestro bpmn decompile <Project>/<Name>.bpmn -o <Name>.bpmn.ts --style nested`, as in [SKILL.md](../SKILL.md#workflow).
2. Rewrite the chain as the skeleton, in one write, keeping the seeded process id, `entryPointId` and start event id.
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
   Between `check --graph` and compile, audit every `.fork()` for the stalls rule 9 describes; neither `check` nor `validate` does it for you:
   - In the `.bpmn.ts`, every `.endEvent(` inside a fork branch's callback carries `terminate: true` or `error`, except one ending a non-interrupting handler's path or closing a `.subProcess()` body.
   - In the `.bpmn.ts`, every `.goto()` that starts inside a fork branch's callback targets a node declared inside that same branch's callback, or `<fork>_join` when that `.goto()` is the branch's only flow into the join.
     A `.goto()` into a sibling branch, past the join, or into the join while the branch's own path also reaches it fails the audit, as does a `.goto()` to the fork or to any node before it.
     This holds for source that `decompile` wrote too: its `.goto()` rejoins pass only when they stay on their own branch, and the `check --graph` bullet below cannot prove that, because a jump into a sibling branch leaves the join's `Incoming` count unchanged.
     A non-interrupting handler's `.goto()` is exempt when its target cannot reach `<fork>_join`.
   - In the `.bpmn.ts`, no `.goto()` anywhere targets a `.fork()` id; a whole-block retry targets the box before the fork (rule 9).
   - In the `check --graph` output, under `Data.Graph.Nodes`, the node whose `Id` is `<fork>_join` has an `Incoming` no larger than the number of `Outgoing` entries on the `<fork>` node.
     A larger `Incoming` means an extra path flows into the join; the join's extra source is a box inside an `onError` or `onTimer` handler, or a `.goto()` from a decision arm.

   Fix any of them as rule 9 says before you compile.
<!--skill-flavor:draft-steps-no-refresh:start-->
   Because the start event kept the id `Event_start`, the `init`-generated `entry-points.json` still matches and the skeleton needs no `refresh`.
   If `validate` fails with `entry-points.json references start event "Event_start"`, the id was renamed: put `Event_start` back.
<!--skill-flavor:draft-steps-no-refresh:end-->
<!--skill-flavor:draft-upload:start-->
4. **Upload it, so the user sees it on the canvas**, unless the request forbids upload: `uip solution upload <SolutionDir> --output json`, where `<SolutionDir>` is the solution `init` scaffolded (`<Name>Solution/`) or registered the project in.
   The gate reply carries the returned `Data.DesignerUrl`.
   Do not ask first when this run created the solution (its `init` or `uip solution init` made it): the request to draft the process authorizes the upload that shows it, and a consent question per iteration would defeat the draft.
   When the solution already existed, check its cloud copy before uploading over it, as [Studio Web upload](operate.md#studio-web-upload) says.
   Upload without asking only when the user picked it from the solution question, which already said the upload overwrites its cloud copy; otherwise do not upload, because the gate asks no other question: its one sentence says the upload waits for the user's go-ahead.
   The skeleton needs none of that section's other pre-flight steps: it keeps `Event_start`, so it needs no `refresh`, and it binds no resource.
   When the request forbids upload, or the project has no solution (the user named its path and chose none), do not upload and do not create a solution to show a draft: the gate reply carries the local path.
   Do not pack, debug or run anything.
   Those are separate decisions, and the user has not approved the shape yet.
<!--skill-flavor:draft-upload:end-->
5. **Find each box's resource**, as [Find the resources](#find-the-resources) says, then reply as [Show the shape and stop](#show-the-shape-and-stop) says.

### Expected findings — do not chase them

A skeleton validates as **Valid** with one warning per declared variable it reads — each variable a decision reads, and each collection or stop flag a multi-instance box reads: `Variable "vars.<id>" is read but never assigned; it will be empty at run time`.
That is correct for a skeleton, whose producers are blank boxes.
When an error path merges onto a box (rule 9), `check` also warns `[FAKE_JOIN] "<box>" has <n> incoming flows; the platform accepts this, but joining with a gateway is clearer`; that is the intended merge.
Act only on errors, and do not report these warnings: they are expected on a skeleton, so they get no line in the reply.

## Find the resources

A box whose kind runs a deployed resource cannot be built without one: every kind in [Box kinds](#box-kinds) except `Action app`, `Execute script` and `Execute HTTP request`, including Business rule, plus a queue, a Data Fabric entity, and a connector box's connection.
<!--skill-flavor:lookup-no-login:start-->
When this run already found no `uip login` (the upload failed for it), skip the lookup and mark each such box `not checked`.
Otherwise run every lookup in **one** Bash call.
<!--skill-flavor:lookup-no-login:end-->
The lookups only read the tenant, so a request that forbids uploading or running anything does not forbid them.
It is the turn's last tool call: read [gate-reply-template.md](gate-reply-template.md) and send any progress note before it, and when it returns, send the gate reply as your next and final message, starting with its first line.

- **Processes and queues:** `uip solution resources list --kind <Process|Queue> --search "<term>" --output json`.
  It lists what the solution already holds (`Source: Local`) and what the tenant has (`Source: Remote`).
  `--kind Process` returns every process type; match the box's kind on `Type`: RPA workflow `process`, API workflow `api`, Agent `agent`, Maestro BPMN `processOrchestration`, Maestro Case `CaseManagement`, Maestro Flow `Flow`, Function `function`.
- **Connections:** run this once when any box is a connector box or a Data Fabric entity box, including when the user named no provider; skip it when no box is either.
  No connector key is needed, and the command has no `--limit`, so the `--output-filter` row filter keeps the output to the boxes' connectors:

  ```bash
  uip is connections list --all-folders --output-filter "[?contains(ConnectorName,'<WORD>')].{Connector:ConnectorName,Connection:Name,State:State,IsDefault:IsDefault,Folder:Folder}" --output json
  ```

  Replace the `contains(...)` test with one per service the boxes use, joined with `||`.
  `<WORD>` is one distinctive word of the app the user named, in the app's usual capitalization (`Slack`, `Outlook`, `SharePoint`, `Jira`, `Salesforce`); `contains` is case-sensitive and the exact display name is unknown, so never pass a full name for a named app.
  For a box that names no provider, such as "send an email", use exact names, never `contains(...,'Mail')` (it also matches Mailchimp and Mailgun): `ConnectorName=='Gmail'`, `ConnectorName=='Microsoft Outlook 365'`, `ConnectorName=='Mail'`, `ConnectorName=='Exchange Server'`.
  When any box is a Data Fabric entity, add `ConnectorName=='UiPath Data Fabric'`.
  Match each connector box on `Connector` only, since a connector's key can contain another service's name (the Slack connector's key contains `salesforce`).
  Prefer `State: Enabled`; among those, the folder the step names, then `IsDefault: Yes`.
  An empty result for a box's service marks the box `none yet`; never say the tenant has no such connection.
- **Business rules:** `uip rules list --all-folders --limit 10000 --output-filter "[].{Name:Name,FolderPath:FolderPath}" --output json`, matched on name and folder path.
- **Data Fabric entities:** `uip df entities list --include-folders --output-filter "[].{Name:Name,FolderId:FolderId}" --output json`, matched on `Name` alone; the row carries a folder id, not a folder name, so name no folder on the box's line.
  The box also needs the `UiPath Data Fabric` connection from the connections lookup.

Run each lookup exactly as written, adding no flag: `uip` rejects `--output-filter` on `uip solution resources list` without `--limit`, and rejects `--limit` on every `uip is` and `uip df` list.
`--search` matches names only, and tenants hold thousands of processes, so never list a kind unfiltered, not even after a search came back empty.
Put every search in the one lookup call: the user's own words for the resource, and one or two keywords from the box's label (`invoice`, `extract` for `Extract invoice data [RPA workflow]`).
When a lookup fails, mark its boxes `not checked`, say why in the one sentence the reply's first line allows, and do not retry.
<!--skill-flavor:lookup-not-checked-rule:start-->
Mark a box `not checked` only when its lookup ran and exited non-zero, or when this run already found no `uip login`; never write it for a lookup you did not run.
<!--skill-flavor:lookup-not-checked-rule:end-->
A failed lookup proves nothing is missing: say "Couldn't check your Slack connections", never "No Slack connection in this tenant", and never name a connector key, a kind or a CLI term.

Then give each box one status:

- When the user named the resource, or exactly one row fits the box, use it and name it, with its folder when the row has one.
- When several fit, name the best two and ask which one.
- When none fits, write `none yet, create it or name one`: the user creates it or names one, or picks *Change it*.
- `Action app`, `Execute script` and `Execute HTTP request` boxes need no resource: write `no resource needed` and look nothing up for them.
  An Action app box gets it even when the user named an Action App, overriding the first bullet: it is built as an inline form ([Human task outcomes](bpmn-runtime.md#human-task-outcomes)).

A row fits only when both hold: its kind is the box's kind (match `Type` as above), and its name and folder show it does the step the box describes.
A name that merely shares a keyword does not fit: a process called `invoice-cleanup` in an unrelated project's folder is not the invoice-recording step.
When you cannot tell that a row serves the step, treat the box as having none, and never bind to that row.
Run the lookup again at every gate, so a resource the user created since the last gate shows up.
<!--skill-flavor:gate-one-round:start-->
This gate is the one round for structure and resource questions; a question the skill asks before the skeleton exists, such as which solution to use, still comes before it.
<!--skill-flavor:gate-one-round:end-->

## Show the shape and stop

Read [gate-reply-template.md](gate-reply-template.md) in full before you write the gate reply, then end the turn with the reply exactly as it shows.
The reply is the template and nothing else: no line before it, between its parts or after it.

## After the answer

<!--skill-flavor:draft-cloud-copy:start-->
When you uploaded the skeleton, the user may have changed it on the canvas before answering.
Before you edit it again, download the cloud copy and compare it, as [Check the cloud copy](operate.md#check-the-cloud-copy-before-editing) says; when it differs, build on their copy without asking, and say so in the reply's one sentence.
<!--skill-flavor:draft-cloud-copy:end-->

<!--skill-flavor:draft-change-it:start-->
- **Change it**: edit the skeleton, run the loop again, and show it again as steps 4 and 5 do.
<!--skill-flavor:draft-change-it:end-->
  In a sequence scope, deleting a `.task()` line removes the box and rewires its neighbours; read `check --graph` after the edit.
- **Build it**: replace each `.task()` with the typed method its label names, keeping its id, and author the real payloads as the rest of this skill describes — registry calls, bindings and connections included.
  Bind each box that needs a resource to the resource the gate named, by its name and folder (a connector box through its connection binding, as [Connectors and bindings](bpmn-runtime.md#connectors-and-bindings) says), and ask nothing more about structure or resources.
  An Action app box becomes an inline-form `.humanTask`, as [Human task outcomes](bpmn-runtime.md#human-task-outcomes) says, never `.humanTask(id, { app })`.
  When the user named an Action App, say under `Assumed` that the task is an inline form, not their app, and that Studio Web can switch it to the app.
  A box the gate marked `none yet` gets a placeholder binding: the resource's symbolic name, with no tenant value, as [Draft with an unresolved connector](connectors.md#7-draft-with-an-unresolved-connector) shows for a connection; the final report lists it under `Needs:`.
  An unanswered which-of-two takes the first resource named, reported under `Assumed`.
  A `not checked` box is looked up now, with the commands of [Find the resources](#find-the-resources).
  A real start trigger, a renamed start event or a new entry point now needs `uip maestro bpmn refresh` before `validate`, as [SKILL.md](../SKILL.md#workflow) step 7 says.
  End the turn with the [final report](final-report-template.md); its first line says `(draft mode)`, because this run stopped at a gate.
- **Keep it**: stop, and report the file as an outline, not a working process.

Only *Build it* authorizes the build.
Until then the skeleton is an outline, and calling it a finished process misreports it.
