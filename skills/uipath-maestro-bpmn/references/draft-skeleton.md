# Draft first — the skeleton

Author a skeleton of blank boxes, real control flow and labels, compile and validate it, show it to the user, and stop for their approval.
It makes no registry calls.

**When.** The user wants to see the shape before it is built: *show me the shape*, *sketch it*, *what would it look like*, *before you build it*, or a session in plan mode.
A request to build the process outright skips the draft and authors real nodes directly.
A brownfield edit (the shape already exists) and a discovery-only question (nothing is authored) skip it too.

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
3. **Make no registry calls.** No `uip maestro bpmn registry pull`, `search` or `get`, and no connection or resource lookup.
   Types and resources are chosen after the shape is approved.
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
   Do not hand-roll a loop from a gateway and a `.goto()`, and do not leave the marker to *Build it*: it is structure, and the user is approving it.
9. **A path that leaves a `.fork()` branch early must end the process; every other path continues on its own branch to the join.**
   A parallel join fires only when every incoming flow has delivered a token.
   Three shapes break that, and `check` and `validate` all pass them:
   - A plain `.endEvent()` anywhere inside a branch — on the branch's own path, in a `.choose()` or `.race()` arm such as a rejection, or at the end of an interrupting `onError` or `onTimer` handler — consumes the branch's token, so the join waits forever.
   - A `.goto()` inside a branch that jumps out of it, to a shared exit or a sibling branch, takes the branch's token with it, so the join waits forever.
   - An interrupting handler whose path does not end rejoins at the statement after the activity, and for a branch's last activity that statement is the fork's join.
     The handler's path then becomes an extra input to the join: the activity's own flow never delivers because the handler cancelled it, so the join waits forever.

   Write the safe shape:
   - When the failure or outcome stops the process, end its path in `.endEvent(<id>, { name, terminate: true })`, or in an error end event (`.endEvent(<id>, { name, error: '<ErrorName>' })`) when a caller or an event sub-process handles the error.
     Never set both: `terminate: true` drops the error.
   - When the process carries on after a `.choose()` or `.race()` arm, give the arm no end event and no `.goto()`, so it rejoins at the next statement.
   - When the process carries on after a handler, write another statement on the same branch after the activity, such as the next box, so the handler's path rejoins there and the branch reaches the join on one flow.
     A bare `.exclusiveGateway()` inside a branch does not compile, so merge on a box.

   A non-interrupting handler leaves the step running on its branch and ends in its own end event (rule 4), so this rule does not apply to it.
   Nor does it apply to the end event that closes a `.subProcess()` body: the sub-process then continues on its branch.

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

1. Run `uip maestro bpmn init <Name> --output json` and take the project directory from its `Data.Path`; the commands below write it as `<Project>`.
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
   Before you compile, audit every `.fork()` for the stalls rule 9 describes; neither `check` nor `validate` does it for you:
   - In the `.bpmn.ts`, every `.endEvent(` inside a fork branch's callback carries `terminate: true` or `error`, except one ending a non-interrupting handler's path or closing a `.subProcess()` body.
   - In the `.bpmn.ts`, no `.goto()` inside a fork branch's callback targets an element outside that branch.
   - In the `check --graph` output, under `Data.Graph.Nodes`, the node whose `Id` is `<fork>_join` has an `Incoming` no larger than the number of `Outgoing` entries on the `<fork>` node.
     A larger `Incoming` means a handler's path flows into the join; the join's extra source is a box inside an `onError` or `onTimer` handler.

   Fix either as rule 9 says before you compile.
   Because the start event kept the id `Event_start`, the `init`-generated `entry-points.json` still matches and the skeleton needs no `refresh`.
   If `validate` fails with `entry-points.json references start event "Event_start"`, the id was renamed: put `Event_start` back.
<!--skill-flavor:draft-upload:start-->
4. **Upload it, so the user sees it on the canvas**, unless the request forbids upload: `uip solution upload <SolutionDir> --output json`, where `<SolutionDir>` is the solution `init` scaffolded (`<Name>Solution/`) or registered the project in.
   The gate reply carries the returned `Data.DesignerUrl`.
   Do not ask first when this run's `init` scaffolded the solution: the request to draft the process authorizes the upload that shows it, and a consent question per iteration would defeat the draft.
   Confirm first when the solution already existed, and check its cloud copy before uploading over it, as [Studio Web upload](operate.md#studio-web-upload) says.
   The skeleton needs none of that section's other pre-flight steps: it keeps `Event_start`, so it needs no `refresh`, and it binds no resource.
   When the request forbids upload, or the project has no solution (`init` ran with `--skip-solution-registration`), do not upload and do not create a solution to show a draft: the gate reply carries the local path.
   Do not pack, debug or run anything.
   Those are separate decisions, and the user has not approved the shape yet.
<!--skill-flavor:draft-upload:end-->

### Expected findings — do not chase them

A skeleton validates as **Valid** with one warning per declared variable it reads — each variable a decision reads, and each collection or stop flag a multi-instance box reads: `Variable "vars.<id>" is read but never assigned; it will be empty at run time`.
That is correct for a skeleton, whose producers are blank boxes.
When an error path merges onto a box (rule 9), `check` also warns `[FAKE_JOIN] "<box>" has <n> incoming flows; the platform accepts this, but joining with a gateway is clearer`; that is the intended merge.
Act only on errors, and do not report these warnings: they are expected on a skeleton, so they get no line in the reply.

## Show the shape and stop

Reply in this shape, and end the turn:

```text
<!--skill-flavor:gate-first-line:start-->
<Name>: outline ready<, uploaded> (draft mode). <One sentence if the upload failed or you kept the user's Studio Web edits.>
<!--skill-flavor:gate-first-line:end-->
<!--skill-flavor:gate-path-line:start-->
<the Studio Web link (Data.DesignerUrl) on its own line when it uploaded, else the local <Project>/<Name>.bpmn path as plain text, never a link>
<!--skill-flavor:gate-path-line:end-->

- <each box's label, in order>

Is this the process you want?
1. **Build it**: make every step work.
2. **Change it**: tell me what to add, remove, or move.
3. **Keep it**: stop here with this outline.
```

The reply is the template and nothing else: no line before it, between its parts or after it.
<!--skill-flavor:gate-uploaded-rule:start-->
Write `, uploaded` only when this turn's upload succeeded.
<!--skill-flavor:gate-uploaded-rule:end-->
When the path line is the local path, write the plain path, such as `InvoiceIntake/InvoiceIntake.bpmn`, not as a Markdown link with the file name as its text.
That rules out a status or validation line (`Valid`, `zero errors`, `Uploaded`), an explanation of a warning, a note about a default you chose, and a question of your own (a time zone, which app); anything the user should settle waits for *Change it*.
List every task box, in order, and nothing else: not the start event, a gateway or the end event.
A box line is the box's label exactly as its `.task()` name spells it, `→ variable` suffix included, and never a branch condition, an arm label or a route: `- Manager review [Action app]`, not `- Manager review [Action app] (amount 1000 or more)`.
Unlike v1, which appends `: <resource status>` to a box label, v2 adds no status suffix after the label.
Add no drawn diagram, no table and no step log; the file is the picture.
Ask the question in the message, not with a pick-list or question tool, and wait for the user's answer.
A pending question keeps the turn open, and Studio Web locks the canvas while a turn runs, so the user could not review the shape they are asked to approve.

## After the answer

<!--skill-flavor:draft-cloud-copy:start-->
When you uploaded the skeleton, the user may have changed it on the canvas before answering.
Before you edit it again, download the cloud copy and compare it, as [Check the cloud copy](operate.md#check-the-cloud-copy-before-editing) says; when it differs, build on their copy without asking, and say so in the reply's one sentence.
<!--skill-flavor:draft-cloud-copy:end-->

- **Change it**: edit the skeleton, run the loop again, and show it again as step 4 does.
  In a sequence scope, deleting a `.task()` line removes the box and rewires its neighbours; read `check --graph` after the edit.
- **Build it**: replace each `.task()` with the typed method its label names, keeping its id, and author the real payloads as the rest of this skill describes — registry calls, bindings and connections included.
  A real start trigger, a renamed start event or a new entry point now needs `uip maestro bpmn refresh` before `validate`, as [SKILL.md](../SKILL.md#workflow) step 7 says.
  End the turn with the [final report](#the-final-report-after-build-it).
- **Keep it**: stop, and report the file as an outline, not a working process.

Only *Build it* authorizes the build.
Until then the skeleton is an outline, and calling it a finished process misreports it.

## The final report after Build it

<!--skill-flavor:final-upload:start-->
When the built process validates, run the [pre-flight](operate.md#pre-flight-before-any-cloud-action), which a built process needs and a skeleton did not, and upload it again, as step 4 did: `uip solution upload <SolutionDir> --output json` returns the `Data.DesignerUrl`.
Skip the upload when the request forbids it or the project has no solution.
The *Build it* answer does not authorize uploading a process that is not ready: when a connector's enrichment or a binding is still unresolved, do not upload ([Operate](operate.md#anti-patterns)).
<!--skill-flavor:final-upload:end-->
Then reply in this shape, dropping lines that do not apply:

```text
<!--skill-flavor:final-first-line:start-->
<Name>: built, validated<, uploaded> (draft mode). <One sentence if you kept the user's Studio Web edits.>
<!--skill-flavor:final-first-line:end-->
<!--skill-flavor:final-path-line:start-->
<the Studio Web link (Data.DesignerUrl) on its own line when it uploaded, else the local <Project>/<Name>.bpmn path>
<!--skill-flavor:final-path-line:end-->

- <what changed, one line each, at most 5 lines in all>

Needs: <...>
Assumed: <...>  Unverified: <...>
```

The first line names the mode: the run stopped at a draft gate, so it says `(draft mode)`, never `(auto mode)`.
When validation fails only because tenant resources are missing (no connection, agent, process or queue to bind), the first line reads `<Name>: built, not runnable yet (draft mode).` and `Needs:` names each missing resource in the user's words, such as `a Slack connection` or `the ticket triage agent`.
Drop `Needs:` when nothing is missing.

Write every line in the user's words: say what each step now does.
No element type ids (`Orchestrator.StartAgentJob`), connector keys, object or operation names, payload, binding or placeholder terms, and no file names other than the path line.

This reply is your whole final message, and its first characters are the process name: no status sentence or introduction before the `<Name>:` line.
Send nothing beyond these lines: no extra sections, headings, tables, numbered lists, questions or suggested next steps.
Write at most five change lines; when there are more, merge related steps, and fold anything else the user must act on into `Needs`, `Assumed` or `Unverified`.
