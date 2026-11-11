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
   Pass `name` and nothing else: no `set`, no body callback.
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
     Do not simplify the branch structure the request describes.
5. **Label each box with the action first and its kind last, in brackets** — `Extract invoice data [RPA workflow]`, `Manager review [Action app]`, `Classify ticket [Agent]`, `Notify the team [Slack]`.
   Take the kind from [Box kinds](#box-kinds).
   When several kinds could fit, pick the one a Studio Web user would most likely choose; the user changes it at the gate if they disagree.
6. **Label each decision arm** with the outcome it carries (`label: 'Approved'`), so the routing reads off the picture.
   `fork` branches take no label: every branch runs.
7. **Declare the variables the decisions read, for real**, with `.var()`.
   The basis a gateway routes on is part of what the user approves: three arms out of a diamond with no stated basis could mean anything.
   A skeleton reads a variable but cannot assign it, because the assignment lives in the payload of the node that produces it.
   Name the producer in the box upstream instead: `Classify ticket [Agent] → category`.

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

A skeleton validates as **Valid** with one warning per variable a decision reads: `Variable "vars.<id>" is read but never assigned; it will be empty at run time`.
That is correct for a skeleton, whose producers are blank boxes.
Act only on errors, and do not report the warning: it appears on every skeleton, so it gets no line in the reply.

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
