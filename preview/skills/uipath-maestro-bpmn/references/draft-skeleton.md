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

A skeleton exists so the shape can be read end to end — so the user can say "yes, that's it" or "drop that step", and so the build has a validated structure to fill in.
It is not a working process and must never be reported as one.

1. **Every activity is a bare `.task(id, { name })`.**
   Pass `name` and nothing else: no `set`, no body callback.
   It compiles to a plain `<bpmn:task>` with no `uipath:activity` payload.
2. **Use no typed activity method** — not `scriptTask`, `humanTask`, `http`, `connector`, `externalAgent`, `externalWorkflow`, `dataService`, `businessRule`, the Orchestrator start/execute/queue methods, or `activity`.
   Each one decides the product choice the user has not approved yet, and its icon says so on the canvas.
   The label carries the meaning a blank box cannot (rule 5).
3. **Make no registry calls.** No `uip maestro bpmn registry pull`, `search` or `get`, and no connection or resource lookup.
   Types and resources are chosen after the shape is approved.
4. **Control flow is real.**
   - The start event is the one the process actually has: plain when something calls it, `{ timer }` when it runs on a schedule (`{ timer: { cycle: 'R/2026-01-01T06:00:00Z/P1D' } }` for every day at 6:00 UTC; use the user's UTC offset in place of `Z` when they give a local time, and `Z` when they state none; a duration string for a one-off delay), `{ message: '<name>' }` when a message starts it.
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

The short names Studio Web's BPMN toolbox shows.
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
| An inline calculation | Script |
| An HTTP call with no connector | HTTP request |

## A worked skeleton

"Every morning at 6, look at yesterday's orders; on a busy day, more than 100 orders, the manager gets a full summary, otherwise a short one."

```ts
import { bpmn } from '@uipath/maestro-builder-sdk/bpmn';

export default bpmn('Process_1')
  .name('NightlyReportSketch')
  .metadata({ entryPointId: '<the UUID the decompiled stub carries>' })
  .flowMode('sequence')
  .var('orderCount', 'number')
  .startEvent('Event_start', { name: 'Every day at 6:00', timer: { cycle: 'R/2026-01-01T06:00:00Z/P1D' } })
  .task('loadOrders', { name: "Load yesterday's orders [RPA workflow] → orderCount" })
  .choose('busyDay', [
    { when: '=vars.orderCount > 100', label: 'Busy day', body: (b) => b.task('fullSummary', { name: 'Send the manager a full summary [Outlook]' }) },
    { otherwise: true, label: 'Normal day', body: (b) => b.task('shortSummary', { name: 'Send the manager a short summary [Outlook]' }) },
  ])
  .endEvent('done', { name: 'Report sent' })
  .build();
```

It compiles to three bare `bpmn:task` boxes, a timer start, an exclusive gateway with a condition and a default, a join, and an end event.

## Steps

1. Run `uip maestro bpmn init <Name> --output json` and take the project directory from its `Data.Path`; the commands below write it as `<Project>`.
   It is not always `<Name>/`: outside a solution, `init` scaffolds one and the project lands at `<Name>Solution/<Name>/`.
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
4. Do not upload, pack, debug or run anything.
   Those are separate decisions, and the user has not approved the shape yet.

### Expected findings — do not chase them

A skeleton validates as **Valid** with one warning per variable a decision reads: `Variable "vars.<id>" is read but never assigned; it will be empty at run time`.
That is correct for a skeleton, whose producers are blank boxes.
Act only on errors.

## Show the shape and stop

Reply in this shape, and end the turn:

```text
<Name>: outline ready (draft mode).
<the local <Project>/<Name>.bpmn path>

- <each box's label, in order>

Is this the process you want?
1. **Build it**: make every step work.
2. **Change it**: tell me what to add, remove, or move.
3. **Keep it**: stop here with this outline.
```

List every task box, in order, and nothing else: not the start event, a gateway or the end event.
Add no drawn diagram, no table and no step log; the file is the picture.
Ask the question in the message, not with a pick-list or question tool, and wait for the user's answer.

## After the answer

- **Change it**: edit the skeleton and run the loop again.
  In a sequence scope, deleting a `.task()` line removes the box and rewires its neighbours; read `check --graph` after the edit.
- **Build it**: replace each `.task()` with the typed method its label names, keeping its id, and author the real payloads as the rest of this skill describes — registry calls, bindings and connections included.
  A real start trigger, a renamed start event or a new entry point now needs `uip maestro bpmn refresh` before `validate`, as [SKILL.md](../SKILL.md#workflow) step 7 says.
- **Keep it**: stop, and report the file as an outline, not a working process.

Only *Build it* authorizes the build.
Until then the skeleton is an outline, and calling it a finished process misreports it.
