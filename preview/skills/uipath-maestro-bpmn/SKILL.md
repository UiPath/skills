---
name: uipath-maestro-bpmn
description: "TRIGGER for authoring, operating or diagnosing UiPath Maestro BPMN. Author `<Name>.bpmn.ts` with the TypeScript builder SDK (`@uipath/maestro-builder-sdk/bpmn`) and run the `uip maestro bpmn` check/compile/format/validate loop. Operate: refresh package metadata, pack, upload to Studio Web, publish, debug a real run, run a deployed process, inspect jobs and instances, pause/resume/cancel/retry/migrate. Diagnose a failed or stuck run: job status, incidents, runtime variables, the deployed BPMN asset, element executions, cursors, traces. Covers events, gateways, tasks, sub-processes, sequence flows, bindings, static rules, semantic `.bpmn` output, boundary handlers and branching written by nesting, event sub-processes, Data Fabric (Data Service) record and file operations through `.dataService()`, and any registry-backed extension type through `.activity()` — including one the SDK ships no typed method for. Flow builder authoring → uipath-maestro-flow; case plans → uipath-maestro-case."
allowed-tools: Bash, Read, Write, Edit, Glob, Grep, AskUserQuestion
---
<!-- CANONICAL — edit here, not in UiPath/flow-builder-sdk. Why: docs/SKILLS_PROMOTION_PLAN.md in that repo. -->

# UiPath Maestro BPMN — TypeScript Builder SDK

Author a Maestro process as a typed BPMN graph and compile it to `.bpmn` XML.
Builder methods map directly to events, gateways, activities, sub-processes,
variables, bindings, and sequence flows.

Use this file as a router. Read only the reference named by the capability you
need, then let TypeScript and `bpmn check` provide the detailed contract.

<!--skill-flavor:host-setup:start-->

<!--skill-flavor:host-setup:end-->
## Workflow

<!--skill-flavor:workflow-scaffold:start-->
1. Scaffold the project first with `uip maestro bpmn init <Name> --output json`, and take the project directory from `Data.Path`.
   Below, `<Project>` means that directory.
   It holds `<Name>.bpmn` plus `project.uiproj`, `operate.json`, `entry-points.json`, `bindings_v2.json`, and `package-descriptor.json` — the layout `bpmn pack` and product tooling require.
   `init` takes a name, not a path, and writes under the current directory:
   - inside a solution (a `.uipx` here or in a parent): `./<Name>/`, registered in that solution;
   - outside one: `./<Name>Solution/<Name>/`, inside a solution it scaffolds;
   - with `--skip-solution-registration`: `./<Name>/`, with no solution.

   **When the user names where the project or its `.bpmn` goes** (`A/B/B.bpmn` names project directory `A/B`), `mkdir -p A`, run `init B` from `A`, and pass `--skip-solution-registration` unless `A` or a parent already holds a `.uipx`.
   When the file name differs from its directory (`A/B/C.bpmn`), `init B` writes `B.bpmn`, so ask the user which of the two to rename before choosing.
   Check `Data.Path` against the requested path before writing anything, and compile to that path, not to a copy elsewhere.
   A project with no solution validates, refreshes and packs; to upload or deploy it later, see [Operate](references/operate.md#studio-web-upload).
2. Keep `<Name>.bpmn.ts` at the workspace root, beside `package.json`.
<!--skill-flavor:workflow-scaffold:end-->
3. Import from `@uipath/maestro-builder-sdk/bpmn` and default-export a chain ending in `.build()`.
<!--skill-flavor:workflow-seed:start-->
4. Seed the source by decompiling the stub `bpmn init` wrote —
   `uip maestro bpmn decompile <Project>/<Name>.bpmn -o <Name>.bpmn.ts --style nested` — rather than
   hand-writing the skeleton.
<!--skill-flavor:workflow-seed:end-->
   `--style nested` lifts an existing process's boundary events, gateways and event sub-processes into the nesting constructs, writes the top level in order (`flowMode('sequence')`), and leaves whatever it cannot prove flat with a printed reason; the compiled graph is verified identical before it is written. It KEEPS the flow ids the constructs now imply: an import's `edge_…` is pinned back onto the implied edge with a `.flowIds([…])` call at the top of the chain, so the recompile reproduces the ids the artifact arrived with. That matters for brownfield work — `bpmn merge` keys every element by id, flows included, so a renamed flow reads as a new one, the original is deleted with its diagram edge, and a gateway `default` left naming the old id produces a file `validate` rejects. `--keep-flow-ids` now only confines the lift to regions whose ids already match, for source with no pin table, at the cost of lifting far less. Without `--style nested` the whole process is written flat. It carries the process id and the `entryPointId` UUID the
   product assigned, which a hand-written chain cannot invent. An existing project needs
   no `init`: seed from the `.bpmn` already there. For shape, copy the closest staged
   `examples/*.bpmn.ts`.
   Two things it does to the declaration blocks, both reported: it DROPS bindings nothing
   references (`--keep-unused-bindings` keeps them) and it writes `.preserve({ … })` for
   state the document carried that nothing derives. Leave the `.preserve` call alone; see
   [Process contract](references/bpmn-runtime.md#variables-and-the-process-contract).
<!--skill-flavor:workflow-compile:start-->
5. Run `uip maestro bpmn check <Name>.bpmn.ts --source` before every compile, and fix
   every error it prints (it exits non-zero) before you compile. `compile` writes what
   the source says; `check` is what reports a probable mistake, such as a `vars.<id>`
   read of a variable nothing declares (`EXPR_UNDECLARED_REF`) or a declared variable
   read without `vars.` (`EXPR_BARE_VAR_REF`). For two of these, a read in an
   `errorMapping` condition and a bare `=amount`, `check` is the only offline gate:
   `bpmn validate` accepts both.
   Needs `@uipath/maestro-builder-sdk` 6.86.0 or later; an older `compile` refuses the read itself.
   When the installed package ships `dist/bpmn-api.md` (see [API index](#api-index)), `check` also type-checks the source: a `TS<code>` error at `file:line:col` is a wrong option name or value type, so fix it like any other `check` error.
   Node's runtime globals, top-level `await` and ES2024 APIs are accepted.
6. Compile **into the scaffolded project**, then `format` it, then `refresh` it, then
   run product validation — in that order, every time. `validate` refuses a file with
   no diagram (`BPMN_PARSE_ERROR: No diagrams found`), and `compile` writes none;
   `format` adds it.
   Exactly one emitted `<Name>.bpmn` may exist, at
   `<Project>/<Name>.bpmn`; do not leave a second copy at the workspace root, and do not
   leave the template `init` wrote in place of your compiled output.
<!--skill-flavor:workflow-compile:end-->
7. **`refresh` is part of the loop, not part of packaging.** `init` generates
   `entry-points.json` and `operate.json` once, naming the start event of the template
   it wrote (`Event_start`); they do not follow source edits. Author a start event with
   any other id — which authoring from your own chain always does — and step 6's
   validator fails on the mismatch:
   `entry-points.json references start event "Event_start" via filePath, but no
   <bpmn:startEvent id="Event_start"> exists`. `uip maestro bpmn refresh <project-path>`
   regenerates both from the compiled BPMN. Run it after any edit that changes a start
   event id or adds or removes an entry point. It validates before it writes, so lay
   the diagram out first (`format`) or it fails with `MISSING_DI_SHAPE`, and it needs an
   init-generated project — with no `project.uiproj` it has nothing to regenerate.
<!--skill-flavor:workflow-merge:start-->
8. Use the merge pipeline for targeted edits to an existing process.
<!--skill-flavor:workflow-merge:end-->

## Draft first

When the user asks to see the shape before it is built — *show me the shape*, *sketch it*, *what would it look like*, *before you build it*, or plan mode — build a skeleton of bare tasks and stop at an approval gate: read **[`references/draft-skeleton.md`](references/draft-skeleton.md)**.
Outside plan mode, a mermaid diagram or outline in chat is not the deliverable; the validated `<Name>.bpmn` in the project `init` wrote is.
The skeleton keeps the stub's `Event_start` id, so its loop skips `refresh` (step 7 above), and it makes no `registry` calls.

## API index

<!--skill-flavor:api-index-location:start-->
Indexed in the INSTALLED PACKAGE, not here, because a `.d.ts` line span is only true of the build that emitted it.

When the package ships `node_modules/@uipath/maestro-builder-sdk/dist/bpmn-api.md`, every BPMN builder method and option field is there, with its type and a one-line doc.
Search it for the name you have — a field (`outputVar`), a method (`humanTask`) or a shape (`HttpOpts`) — and read only the line it lands on: the row is the answer.
Do not read `dist/**/*.d.ts` with that package; `check --source` reports a wrong option name or value type with its line (step 5).
`dist/api-index.md` (by exported symbol, `BpmnBuilder`) gives a declaration's line span only when you need its long-form `@remarks` or `@example`.

A package without `bpmn-api.md` has `dist/api-members.md`, keyed by field or method name (`gateway`), and `dist/api-index.md`, keyed by exported symbol.
Match one name — do not read either end to end — then read the span it gives you: the whole declaration, doc comment included.
<!--skill-flavor:api-index-location:end-->

## Capability router

| Surface | Builder/API | Reference | Example |
|---|---|---|---|
| Show the shape before building it (sketch, draft, plan mode) | bare `task`, `choose` | [Draft first](references/draft-skeleton.md) | — |
| Process and nested scopes | `bpmn`, `subProcess` | [Builders](#api-index) | `examples/NotifyChannel.bpmn.ts` |
| Variables, inputs, and outputs | `vars`, `var`, `input`, `output`, `schemas`, `schema` | [Process contract](references/bpmn-runtime.md#variables-and-the-process-contract) | `examples/NotifyChannel.bpmn.ts` |
| A node's own output | the node's `outputRows` — **not** a `.var()` beside it | [Process contract](references/bpmn-runtime.md#variables-and-the-process-contract) | `examples/InvoiceApproval.bpmn.ts` |
| Carried-from-import state, not for editing | `preserve` | [Process contract](references/bpmn-runtime.md#variables-and-the-process-contract) | `examples/InvoiceApproval.bpmn.ts` |
| Start, end, catch, throw, boundary | event methods | [Events](references/bpmn-runtime.md#events-and-timers) | `examples/NotifyChannel.bpmn.ts` |
| Error, timer, or message ON an activity | the body callback of any activity method: `onError`, `onTimer`, `onMessage` | [ActivityBuilder](#api-index) | `examples/InvoiceEscalation.bpmn.ts` |
| Exclusive, inclusive, parallel, event-based | gateway methods | [GatewayOpts](#api-index) | `examples/NotifyChannel.bpmn.ts` |
| Decision, parallel split, or wait-for-first, written in place | `choose`, `fork`, `race`, `goto` | [ChooseArm](#api-index) | `examples/InvoiceEscalation.bpmn.ts` |
| Safety net for a whole scope | `eventSubProcess` | [Event sub-process scope](references/bpmn-runtime.md#events-and-timers) | `examples/InvoiceEscalation.bpmn.ts` |
| Script and assignment tasks | `scriptTask`, `task` | [ScopeBuilder](#api-index) | `examples/NotifyChannel.bpmn.ts` |
| HTTP requests | `http` | [HTTP](references/bpmn-runtime.md#http-and-orchestrator-work) | `examples/NotifyChannel.bpmn.ts` |
| Orchestrator jobs and queues | start/execute/queue methods | [Work dispatch](references/bpmn-runtime.md#http-and-orchestrator-work) | `examples/NotifyChannel.bpmn.ts` |
| A deployed business rule | `businessRule` | [Work dispatch](references/bpmn-runtime.md#http-and-orchestrator-work) | — |
| Human work — an inline form unless a deployed Action App is named | `humanTask` | [Human tasks](references/bpmn-runtime.md#human-task-outcomes) | `examples/InvoiceEscalation.bpmn.ts` |
| Connectors and external work | `connector`, `externalAgent`, `externalWorkflow` | [Connectors](references/connectors.md) | `examples/NotifyChannel.bpmn.ts` |
| A connector EVENT, as a start or a mid-flow wait | `eventTrigger`, `waitForEvent` | [Connector events](references/connectors.md#6-connector-events) | — |
| A connector step in a draft with no connection (offline, or no real ids allowed) | `connector` with symbolic bindings, or a bare `task` | [Unresolved connector draft](references/connectors.md#7-draft-with-an-unresolved-connector) | — |
| Data Fabric records and file fields | `dataService` | [Connections](references/bpmn-runtime.md#connectors-and-bindings) | `examples/ContractRegistry.bpmn.ts` |
| Any registry type, typed method or not | `activity` | [Registry extension types](references/bpmn-runtime.md#registry-extension-types) | `examples/InvoiceApproval.bpmn.ts` |
| Existing BPMN | `bpmn decompile`, `compile`, `merge` | [Brownfield](references/bpmn-runtime.md#brownfield-editing) | `examples/NotifyChannel.bpmn.ts` |
| Process metadata, package, and layout | `metadata`, project metadata, `bpmn format` | [Contract metadata](references/bpmn-runtime.md#contract-metadata) | `examples/NotifyChannel.bpmn.ts` |
| Package, upload, publish, debug, run, manage an instance | `uip maestro bpmn refresh` / `pack` / `debug` / `process run` / `instance …` | [Operate](references/operate.md) | — |
| Evaluate a process: evaluators, eval sets, data points, simulations, eval runs | `uip maestro bpmn eval` | [Evaluate](references/evaluate.md) | — |
| A run failed or is stuck | `uip maestro bpmn job status` / `instance incidents` / `instance variables` / `instance asset` | [Diagnose](references/diagnose.md) | — |
| Sanitize a file to share or commit; what notes and examples may contain | placeholders in the `.bpmn.ts`, then `decompile` / `merge` for an export | [Public safety](references/public-safety.md) | — |
| A recurring process shape: review gate, approval chain, triage, external wait, batch, failure net, queue | `choose`, `race`, `subProcess` with `loop`, `eventSubProcess` | [Patterns](#patterns) | — |

## Minimal shape

```ts
import { bpmn } from '@uipath/maestro-builder-sdk/bpmn';

export default bpmn('notify')
  .name('Notify')
  .flowMode('sequence')
  .var('status', 'string')
  .startEvent('start')
  .task('record', { set: { status: 'ready' } })
  .endEvent('done')
  .build();
```

In sequence mode each element continues to the next, so a process written top to bottom has no `.sequenceFlow()`; branch with `.choose()`, attach handlers in an activity's body, and read `bpmn check --graph` to see the wiring that resulted.
The explicit form — `.sequenceFlow('start', 'record')` after the elements, in the default mode — is what `bpmn decompile` writes for an import unless `--style nested` lifts it, and both forms mix freely.

## Structure by nesting

Where a relationship can be written by nesting, write it that way instead of by id.
Each form lowers to the same elements and flows the explicit methods produce, and the explicit `.sequenceFlow()` still works anywhere, mixed freely.
`examples/InvoiceEscalation.bpmn.ts` is a full process written this way, with no `.sequenceFlow()` at all; `examples/InvoiceApproval.bpmn.ts` is a real 71-element import lifted into this form by `bpmn decompile --style nested` — sixteen decisions as `.choose()`, five error handlers in their activities' bodies, and the seven `.sequenceFlow()` calls that remain are the merges and fan-outs no construct owns.

```ts
export default bpmn('approval')
  .var('action', 'string')
  .var('outcome', 'string', { default: 'RUNNING' })
  .startEvent('start')
  .humanTask('approve', { form: { fields: [], outcomes: ['Approved', 'Rejected'] }, outputs: { action: '=Action' } }, (t) => {
    t.onTimer('PT1H', { interrupting: false }, (b) => b.task('remind').endEvent('reminded'));
    t.onError(true, { errorVar: 'failure' }, (b) => b.endEvent('failed', { name: 'Approval failed' }));
  })
  .choose('approved', [
    { when: '=vars.action == "Approved"', label: 'Yes', body: (b) => b.task('post') },
    { otherwise: true, label: 'No', body: (b) => b.task('reject') },
  ])
  .endEvent('done')
  .sequenceFlow('start', 'approve')
  .sequenceFlow('approve', 'approved')
  .eventSubProcess('failures', { error: true }, (h) =>
    h.task('record', { set: { outcome: '=js:"FAILED: " + vars.failures_Error.message' } }).endEvent('recorded', { name: 'Failure recorded' }))
  .build();
```

- A boundary event is declared on the activity it guards, in that activity's body callback, so `attachedTo` is never written.
  An interrupting handler's path rejoins at the statement after the activity; a non-interrupting one runs beside the activity and must end its own path with an end event, `.goto()`, or an explicit flow.
- `choose` arms need `when` or `otherwise: true`; the fallback is the default flow, and no flow id is named.
  Arms rejoin at the next statement, through a join named `<id>_join` only when more than one arm reaches it.
- Inside an arm or a handler, consecutive elements are wired in order; branch there with `choose` / `fork` / `race`, not a bare gateway, and jump elsewhere with `.goto(id)`.
- An event sub-process guards the whole container it sits in, catching what nothing closer caught; a boundary handler guards one activity.
  To fail one iteration rather than the whole run, put the `eventSubProcess` inside the multi-instance sub-process.
  An error net captures the caught error on its start by default, into `vars.<net>_Error` — so `.eventSubProcess('failures', …)` gives you `vars.failures_Error`, and you classify on `.code` / `.message` / `.detail` / `.status` with nothing more written. That per-net id is what the designer writes: over the real exports measured, every error capture carries a unique id with the display name `Error`, and the bare `vars.Error` appears in none of them. The `Error` spelling that IS fixed is the capture row's `source="=Error"`, the key the engine seeds the payload under, which the SDK writes for you. `errorVar` names the variable something else; `errorVar: false` omits the capture.
  A boundary handler captures nothing by default; there `errorVar` is what makes the error readable, as `=vars.<errorVar>.code`.
- `check` warns `NO_DEFAULT_FLOW` on an exclusive gateway whose every flow is conditioned; give it an `otherwise` arm or a default.
- `.flowMode('sequence')`, called before the first element, wires consecutive elements of that scope in order, so a process written top to bottom needs no `.sequenceFlow()` at all; a `.subProcess()` body inherits it and may set its own.
  An element that already has an explicit outgoing flow is not also wired to the next one, a bare gateway is wired into but implies no outgoing flows, and an element nothing leads into or a path that does not end is refused at build.
- A step that two routes share is written ONCE, after the `.choose()`, with each arm that reaches it left to fall through; never repeat the step, or a downstream gate, inside each arm.
  The repeated form passes `check`, `compile` and `validate`, and it is the most common way a pattern comes out wrong.
  When fall-through cannot reach it, name the join: `.exclusiveGateway(id)`, `.goto(id)` from each route, `.sequenceFlow(id, next)`.
  See [Shared joins](references/patterns/composing-guide.md#shared-joins-the-mechanism-nesting-hides).
- `uip maestro bpmn check <Name>.bpmn.ts --graph` prints the wiring that resulted, `~>` for an implied edge and `->` for an explicit one, with `[NO INCOMING]` / `[NO OUTGOING]` where they apply.
  Read it after a structural edit in a sequence scope, because inserting a line there rewires the graph.

## Patterns

Read the guide for each pattern the process actually uses, and none for a pattern you are not building.

Every guide's node table marks each node **Entry** (omit when inserting into a process that already runs), **Mechanism** (changing it changes the pattern), or **Placeholder** (bind it, or skip it if the process already does this).

| Pattern | Reach for it when | Guide |
| --- | --- | --- |
| `ai-decision-review` | AI makes one call; act on it, or a human reviews it | [ai-decision-review-guide.md](references/patterns/ai-decision-review-guide.md) |
| `approval-chain` | A request needs sign-off from several people | [approval-chain-guide.md](references/patterns/approval-chain-guide.md) |
| `smart-triage` | Inbound work sorted into categories, each handled elsewhere | [smart-triage-guide.md](references/patterns/smart-triage-guide.md) |
| `external-wait` | The process waits on an outside party under an SLA | [external-wait-guide.md](references/patterns/external-wait-guide.md) |
| `high-volume-batch` | Many independent items processed in one run | [high-volume-batch-guide.md](references/patterns/high-volume-batch-guide.md) |
| `failure-escalation` | Unhandled failures must never disappear silently | [failure-escalation-guide.md](references/patterns/failure-escalation-guide.md) |
| `queue-distribution` | An Orchestrator queue hands work across runtimes | [queue-distribution-guide.md](references/patterns/queue-distribution-guide.md) |

**Do not reach for a pattern** when the ask is a short linear process, a single node, or a change that does not introduce one of these shapes.
A pattern is never a wrapper to retrofit onto work that does not need one.

Using more than one pattern in one process?
Read [references/patterns/composing-guide.md](references/patterns/composing-guide.md) first: which pattern keeps its start event, the four ways the rest join it, how variables cross a nesting boundary, and the two placements the engine constrains.

## Validation loop

<!--skill-flavor:validation-loop:start-->
```bash
uip maestro bpmn init <Name> --output json    # once; <Project> is Data.Path (see step 1)
uip maestro bpmn check <Name>.bpmn.ts --source
uip maestro bpmn check <Name>.bpmn.ts --graph   # the resolved wiring, implied edges marked ~>
uip maestro bpmn compile <Name>.bpmn.ts -o <Project>/<Name>.bpmn
uip maestro bpmn format <Project>/<Name>.bpmn
uip maestro bpmn refresh <Project> --output json   # entry-points.json + operate.json, from the BPMN
uip maestro bpmn validate <Project>/<Name>.bpmn --output json
```
<!--skill-flavor:validation-loop:end-->

`check` owns source and graph invariants. Product validation owns the compiled
BPMN contract. Change the TypeScript source and rebuild; do not patch emitted XML.

Skipping `refresh` is the most common way to fail `validate` on a process that is
otherwise correct: see step 7 above.

A process with connector nodes gives `check` more to work with. It reads the connector
library and the project's `bindings.json` when they are there, and reports a missing
required input, an unresolved `lookup()`, an unprepared object or a self-naming binding
*before* compile does — each with the one command that closes it. `--library <dir>` and
`--connectors-local <dir>` name them explicitly; both are auto-detected otherwise.

## Operating a process

<!--skill-flavor:operating:start-->
Refresh the package metadata, pack, upload to Studio Web (what "publish" means
unless the user names Orchestrator), debug a real run, run a deployed process,
inspect a job, and drive an instance's lifecycle. All of it needs `uip login`;
`uip maestro bpmn refresh <project-path>` comes before every cloud action, and
`bpmn debug` is a REAL run, not a validation step. Every mutation needs the
user's decision for that action. Read
**[`references/operate.md`](references/operate.md)**.
<!--skill-flavor:operating:end-->

## Evaluating a process

<!--skill-flavor:evaluating:start-->
Evaluators, eval sets, data points and simulations are project files that `uip maestro bpmn eval` writes; nothing in `<Name>.bpmn.ts` creates them.
Adding and listing them is local and needs no login.
Every `eval run` verb needs `uip login`, and `eval run start` packages the solution and **uploads it to Studio Web** before it runs, so it also needs the user's decision, like an upload.
Read **[`references/evaluate.md`](references/evaluate.md)**.
<!--skill-flavor:evaluating:end-->

## Diagnosing a failed run

Triage in order — job status, incidents, runtime variables, the deployed BPMN
asset, element executions and cursors, the generated package files, traces last
— with the CLI's exact verbs, every `instance` read carrying `-f <FOLDER_KEY>`.
Never mutate while diagnosing, and never guess a command shape: the reference
lists them. Read **[`references/diagnose.md`](references/diagnose.md)**.

## Evidence boundary

Static success does not prove tenant resource resolution, human outcomes, or
runtime-only values. Read [BPMN runtime decisions](references/bpmn-runtime.md)
when the requested outcome depends on those behaviors.
