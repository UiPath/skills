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
   Because the start event kept the id `Event_start`, the `init`-generated `entry-points.json` still matches and the skeleton needs no `refresh`.
   If `validate` fails with `entry-points.json references start event "Event_start"`, the id was renamed: put `Event_start` back.
<!--skill-flavor:draft-steps:end-->
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

A skeleton validates as **Valid** with one warning per variable a decision reads: `Variable "vars.<id>" is read but never assigned; it will be empty at run time`.
That is correct for a skeleton, whose producers are blank boxes.
Act only on errors, and do not report the warning: it appears on every skeleton, so it gets no line in the reply.

## Find the resources

A box whose kind runs a deployed resource cannot be built without one: every kind in [Box kinds](#box-kinds) except `Action app`, `Execute script` and `Execute HTTP request`, including Business rule, plus a queue, a Data Fabric entity, and a connector box's connection.
When this run already found no `uip login` (the upload failed for it), skip the lookup and mark each such box `not checked`.
Otherwise run every lookup in **one** Bash call.
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
Mark a box `not checked` only when its lookup ran and exited non-zero, or when this run already found no `uip login`; never write it for a lookup you did not run.
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
This gate is the one round for structure and resource questions; a question the skill asks before the skeleton exists, such as which solution to use, still comes before it.

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
