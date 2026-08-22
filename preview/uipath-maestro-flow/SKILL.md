---
name: uipath-maestro-flow
description: "TRIGGER for authoring or editing UiPath Maestro Flow sources as `<Name>.flow.ts` with the TypeScript builder SDK (`@uipath/flow-sdk`) and running the `uip maestro flow` check/compile/validate loop. Covers graph structure, expressions, nodes, bindings, connectors, brownfield edits, and emitted `.flow` validation. Case plans (`caseplan.json`, reference-mode) → uipath-maestro-case; structural-core BPMN (`.bpmn.ts`) → uipath-maestro-bpmn. DO NOT TRIGGER for C#/XAML automation → uipath-rpa."
allowed-tools: Bash, Read, Write, Edit, Glob, Grep, AskUserQuestion
---
<!--
Provenance: snapshot of UiPath/flow-builder-sdk
`typescript/sdk/skill/SKILL.md` @ c0cf591. Canonical source lives there;
edit upstream and re-sync (see UiPath/flow-builder-sdk#405).

This file is deliberately a router. Node-specific detail belongs in
`references/`; statically checkable rules belong in the SDK or flow-check.
-->

# UiPath Flow — TypeScript Builder SDK

Author a Flow as TypeScript that builds a graph. Use builder calls for runtime
control flow and expression helpers for runtime data; native TypeScript control
flow runs only while the graph is being constructed.

## Project layout

The workspace installs `@uipath/flow-sdk` in `node_modules/`; `examples/`
contains authored examples, and `references/` contains the details routed from
this guide. Author a root-level `<Name>.flow.ts` and import the package directly.
Connector flows also use a root-level
[`bindings.json`](references/bindings.md). Prepared connector modules live at
`connectors-local/<key>.ts`; their descriptor data is kept separately below
`connectors-local/descriptors/<key>/`.

```ts
import { flow, script, input, out, types } from '@uipath/flow-sdk';
export default flow('hello').name('Hello')
  .input({ name: types.string }).output({ greeting: types.string })
  .step('greet', script({ code: 'return `Hello ${$vars.start.output.name}`;' }))
  .return({ greeting: out('greet') }).build();
```

## Lifecycle

The `uip maestro flow` commands keep source checks, emission, and
compiled-artifact checks explicit while the installed `@uipath/flow-sdk` owns
their semantics. A workspace with `{ "flowSdk": { "emitOnly": true } }` in
`package.json`, or `FLOW_SDK_EMIT_ONLY=1`, makes `uip maestro flow compile`
emit-only and makes both `flow check` modes refuse. Product validate owns final
structural verification in that mode; use product debug only when the node
family and the requested evidence support it.

**Run the correct loop for your packaging mode:**
**[`references/CLI-LOOP.md`](references/CLI-LOOP.md)**.

## Editing an existing flow

In brownfield work, preserve the supplied source, step names, and unaffected
wiring. Insert a step by moving the old edge through it, not by creating a
second path. If only emitted `.flow` JSON exists, decompile it, compile the
pristine baseline, edit narrowly, and merge the delta back into the original.
These are before/after judgments; no final-artifact checker can prove them.

**True-brownfield procedure:**
**[`references/brownfield.md`](references/brownfield.md)**.

## Builder frame

Start with `flow(id)`, declare `.input({ name: types.* })`,
`.output({ name: types.* })`, and `.var(name, types.*, default?)`; add graph
nodes; use `.return(...)` when a path should answer and `.terminate(...)` when
the whole run should stop; call `.build()`.

Expressions: `lit(value)`, `input(name)`, `v(name)`, `out(step, path?)`,
`err(step, field?)`, `ran(step)`, ``js`...` ``, and ``tmpl`...` ``. A shared
continuation is often clearer than duplicating work in several arms; use
`ran(step)` when its value legitimately comes from only one arm.

Exact function signatures and option shapes:
[`references/api.md`](references/api.md) — the builders too (`FlowBuilder`,
`StepList`, `ArmBuilder`). The sibling authoring surfaces have their own skills:
`uipath-maestro-case` for `@uipath/flow-sdk/case` and `uipath-maestro-bpmn`
for `@uipath/flow-sdk/bpmn`. Neither is needed to build a Flow.

## Supported node types

The table is the authoritative router. `Section` identifies the governed H2;
`Reference` carries the details; `Example` names the one file to read. Paths
under `examples/` resolve inside this skill folder.

| Node or surface | Emitted node type | Builder | Section | Reference | Example |
|---|---|---|---|---|---|
| Manual trigger | `core.trigger.manual` | omit `.trigger(...)` | [Manual trigger](#manual-trigger) | [manual-trigger.md](references/manual-trigger.md) | `examples/GreenhouseWatering.flow.ts` |
| Scheduled trigger | `core.trigger.scheduled` | `scheduled(...)` | [Scheduled trigger](#scheduled-trigger) | [scheduled-trigger.md](references/scheduled-trigger.md) | `examples/HerbariumDispatch.flow.ts` |
| Connector event trigger | `uipath.connector.trigger.<key>.<event>` | `onEvent(...)` | [Connector events](#connector-events) | [event-trigger.md](references/event-trigger.md) | `examples/DoorbellLog.flow.ts` |
| Connector event wait | `uipath.connector.event.<key>.<event>` | `waitForEvent(...)` | [Connector events](#connector-events) | [event-trigger.md](references/event-trigger.md) | `examples/PlanetariumConfirmation.flow.ts` |
| Standalone HTTP | `core.action.http` | `http({ managed: false, ... })` | [HTTP](#http) | [http.md](references/http.md) | `examples/LighthouseSignal.flow.ts` |
| Managed HTTP | `core.action.http.v2` | `http({ managed: true, ... })` | [HTTP](#http) | [http.md](references/http.md) | `examples/ObservatorySeeing.flow.ts` |
| Script | `core.action.script` | `script(...)` | [Script](#script) | [script.md](references/script.md) | `examples/GreenhouseWatering.flow.ts` |
| Transform | `core.action.transform` | `transform(...)` | [Transform](#transform) | [transform.md](references/transform.md) | `examples/TrailLogSummary.flow.ts` |
| Filter | `core.action.transform.filter` | `transform({ variant: 'filter', ... })` | [Transform](#transform) | [transform.md](references/transform.md) | `examples/TrailLogSummary.flow.ts` |
| Map | `core.action.transform.map` | `transform({ variant: 'map', ... })` | [Transform](#transform) | [transform.md](references/transform.md) | `examples/TrailLogSummary.flow.ts` |
| Group by | `core.action.transform.group-by` | `transform({ variant: 'group-by', ... })` | [Transform](#transform) | [transform.md](references/transform.md) | `examples/TrailLogSummary.flow.ts` |
| Integration Service action | `uipath.connector.<key>.<action>` (Data Service: `uipath.connector.uipath-uipath-dataservice.*`) | `connector(...)` | [Integration Service connectors](#integration-service-connectors) | [connector-params.md](references/connector-params.md) | `examples/ClubDirectory.flow.ts` |
| Subflow | `core.subflow` | `subflow(...)` | [Subflow](#subflow) | [subflow.md](references/subflow.md) | `examples/RecipeScaler.flow.ts` |
| Human task | `uipath.human-in-the-loop` | `hitl(...)` | [Human task](#human-task) | [hitl.md](references/hitl.md) | `examples/GallerySubmission.flow.ts` |
| Human quick form | `uipath.human-in-the-loop.quick-form` | `hitl({ variant: 'quick-form', ... })` | [Human task](#human-task) | [hitl.md](references/hitl.md) | `examples/FieldTripQuickForm.flow.ts` |
| Human action app | `uipath.human-in-the-loop.coded-action-app` | `hitl({ variant: 'action-app', ... })` | [Human task](#human-task) | [hitl.md](references/hitl.md) | `examples/KilnReview.flow.ts` |
| RPA workflow | `uipath.core.rpa-workflow.<key>` | `rpaWorkflow(...)` | [RPA workflow](#rpa-workflow) | [rpa-workflow.md](references/rpa-workflow.md) | `examples/WorkshopInventory.flow.ts` |
| Queue item | `core.action.queue.create*` | `queueItem(...)` | [Queue item](#queue-item) | [queue.md](references/queue.md) | `examples/HerbariumDispatch.flow.ts` |
| Summarize | `uipath.pattern.deep-rag` | `summarize(...)` | [AI patterns](#ai-patterns) | [summarize.md](references/summarize.md) | `examples/OralHistoryDigest.flow.ts` |
| Batch transform | `uipath.pattern.batch-transform` | `batchTransform(...)` | [AI patterns](#ai-patterns) | [batch-transform.md](references/batch-transform.md) | `examples/FossilCatalogEnrich.flow.ts` |
| Branch | `core.logic.decision` | `.branch(...)` | [Branch](#branch) | [branch.md](references/branch.md) | `examples/GreenhouseWatering.flow.ts` |
| Switch | `core.logic.switch` | `.switch(...)` | [Switch](#switch) | [switch.md](references/switch.md) | `examples/BeltProgression.flow.ts` |
| Parallel / Merge | `core.logic.merge` | `.parallel(...)` | [Parallel branches](#parallel-branches) | [parallel-merge.md](references/parallel-merge.md) | `examples/ConcertSoundcheck.flow.ts` |
| Loop | `core.logic.loop` | `.loop(...)` | [Loops](#loops) | [loops.md](references/loops.md) | `examples/ClubDirectory.flow.ts` |
| Return / End | `core.control.end` | `.return(...)` | [Return and end](#return-and-end) | [return.md](references/return.md) | `examples/GreenhouseWatering.flow.ts` |
| Terminate | `core.logic.terminate` | `.terminate(...)` | [Terminate](#terminate) | [terminate.md](references/terminate.md) | `examples/AquariumSafetyStop.flow.ts` |
| Placeholder | `core.logic.mock` | `mock()` | [Placeholder](#placeholder) | [placeholder.md](references/placeholder.md) | `examples/FestivalMapScaffold.flow.ts` |
| Error handler | `error` handle on an action node | `.onError(...)` | [Error handling](#error-handling) | [error-handling.md](references/error-handling.md) | `examples/ObservatorySeeing.flow.ts` |
| Delay | `core.logic.delay` | `delay(...)` | [Delay](#delay) | [delay.md](references/delay.md) | `examples/LighthouseSignal.flow.ts` |
| API workflow | `uipath.core.api-workflow.<key>` | `apiWorkflow(...)` | [API workflow](#api-workflow) | [api-workflow.md](references/api-workflow.md) | `examples/BirdCountLookup.flow.ts` |
| Agentic process | `uipath.core.agentic-process.<key>` | `agenticProcess(...)` | [Agentic process](#agentic-process) | [agentic-process.md](references/agentic-process.md) | `examples/NeighborhoodWalkPlanner.flow.ts` |
| Agent resource | `uipath.core.agent.<key>` | `agent(...)` | [Agent resource](#agent-resource) | [agent.md](references/agent.md) | `examples/PlantNameAdvisor.flow.ts` |
| Inline agent | `uipath.agent.autonomous` | `inlineAgent(...)` | [Inline agent](#inline-agent) | [inline-agent.md](references/inline-agent.md) | `examples/PostcardCaption.flow.ts` |
| IxP extraction | `uipath.ixp.<project>.<version>-<folder>` | `ixpExtract(...)` | [Document extraction](#document-extraction) | [ixp.md](references/ixp.md) | `examples/ArchiveCardExtract.flow.ts` |

## Manual trigger

The default start node accepts on-demand caller input; omit `.trigger(...)`.

Signature: `flow(id).input({...}).step(...).build()`.

```ts
export default flow('lookup').input({ id: types.string }).output({ value: types.string })
  .step('read', script({ code: 'return $vars.start.output.id;' }))
  .return({ value: out('read') }).build();
```

Choose it when a caller, test, or another process should start each run.

**Reference: [`references/manual-trigger.md`](references/manual-trigger.md)**

## Scheduled trigger

A platform timer starts the flow on a recurring interval.

Signature: `.trigger(scheduled({ every: string }))`. `every` takes an ISO-8601
repeating interval, or a Quartz cron expression (e.g. `'0 0 2 * * ?'`), which
selects the trigger's 1.2 definition automatically.

```ts
export default flow('nightly')
  .trigger(scheduled({ every: 'R/P1D' }))
  .step('rollup', script({ code: 'return { ok: true };' }))
  .build();
```

Prefer self-contained variables because there may be no caller supplying inputs.

**Reference: [`references/scheduled-trigger.md`](references/scheduled-trigger.md)**

## Form trigger

A person starts the flow by submitting a form (`core.trigger.form`); the
submitted values ARE the flow's inputs.

Signature: `.trigger(formTrigger())` — no arguments; the form's fields are
derived from `.input()` (one per input, required unless it has a default).

```ts
export default flow('expense')
  .input({ amount: types.number, reason: types.string })
  .trigger(formTrigger())
  .step('log', script({ code: 'return $vars.start.output.amount;' }))
  .build();
```

Locally `--input` supplies the values; no rung renders a form.

**Reference: [`references/form-trigger.md`](references/form-trigger.md)**

## Entry points (multiple triggers)

A flow may have more than one root. `.trigger()` / `.input()` stay the DEFAULT
root; `.entryPoint(id, trigger, { inputs?, version? }, prefixFn?)` adds another
— its own trigger node, its own scoped inputs (read them with
`entryInput('<id>', '<name>')`), and an optional prefix that runs before the
root joins the first shared step. A prefix that ends terminally (or hands off
with `.stepToRef(...)`) joins nothing.

```ts
flow('order-intake')
  .input({ order: types.object })                       // default (manual) root
  .entryPoint('nightly', scheduled({ every: 'R/P1D' }), {
    inputs: { batchDate: types.string },
  }, (b) => b.step('loadBatch', script({
    code: 'return { note: $vars.nightly.output.batchDate };', returns: 'object' })))
  .step('normalize', script({ code: 'return 1;' }))     // shared body
```

## Connector events

Start on, or pause for, an Integration Service event subscription.

Signatures: `.trigger(onEvent(subscription))`; `.step(name, waitForEvent(subscription))`.

```ts
const mail = { connector: 'uipath-microsoft-outlook365',
  event: 'email-received', where: { parentFolderId: inboxId } };
export default flow('mail').trigger(onEvent(mail))
  .step('reply', script({ code: 'return $vars.start.output.subject;' })).build();
```

Resolve scope names and ids from the bound connection; preserve filter casing.
Use the reference's completion contract before debugging: an injected start
payload can exercise downstream wiring, but it is not a subscription witness.

**Reference: [`references/event-trigger.md`](references/event-trigger.md)**

## HTTP

Standalone HTTP keeps non-2xx responses on its success output. Managed HTTP routes
them through its error port. Both expose JSON response bodies as parsed values.

Signature: `http({ method?, url, managed, headers?, query?, body?, contentType?, timeout?, retryCount?, returns?, branches? })`.

```ts
.step('getPolicy', http({ method: 'GET', url: policyUrl,
  managed: true, returns: { limit: 'number' },
  branches: [{ name: 'throttled', condition: js`$vars.getPolicy.output.statusCode === 429` }] }))
.stepToList('branch-throttled', (b) => b.return({}))
.step('limit', script({ code: 'return $vars.getPolicy.output.body.limit;' }))
```

Match `managed` to the scenario's node. A branch is a `branch-<name>` side exit
routed with `.stepToList`; the main path continues from the default port.

**Reference: [`references/http.md`](references/http.md)**

## Script

Run inline JavaScript for computation that is not a first-class Flow node.

Signature: `script({ code: string })`; read the result with `out(step, path?)`.

```ts
.step('normalize', script({ code: `
  const amount = Number($vars.amount);
  return { amount, valid: Number.isFinite(amount) };
` }))
```

Use a first-class action when the scenario names one; use script for computation.

**Reference: [`references/script.md`](references/script.md)**

## AI patterns

Summarize reads a document; Batch transform enriches a CSV into a new file.

Signatures: `summarize({ attachment, prompt, returnCitations? })`;
`batchTransform({ attachment, prompt, outputColumns, enableWebSearchGrounding? })`.

```ts
.step('digest', summarize({ attachment: out('start', 'document'),
  prompt: 'Summarize the decisions and owners.',
  returnCitations: true }))
```

Request citations or web grounding only when the scenario needs them.

**Summarize: [`references/summarize.md`](references/summarize.md)**

**Batch transform: [`references/batch-transform.md`](references/batch-transform.md)**

## Document extraction

Run a published Intelligent eXtraction Platform project on an attachment.

Signature: `ixpExtract({ project, modelName, name, folderName, fileRef, pageRange?, versionTag?, folderPath? })`.

```ts
.step('extract', ixpExtract({ project: ixpNodeType,
  modelName: 'invoice-model', name: 'Invoice Extractor',
  folderName: 'Shared', fileRef: out('start', 'invoiceFile') }))
```

Copy identity fields from a freshly pulled tenant registry; never construct them.

**Reference: [`references/ixp.md`](references/ixp.md)**

## Document classify and Dynamic Extract

Classify a document (`uipath.document.classify`), or extract fields against an
INLINE schema (`uipath.ixp.extract-document-builder`) instead of a published
IxP project's trained fields.

Signatures: `documentClassify({ fileRef, pageRange?, splitPages?, modelConfig? })`;
`dynamicExtract({ fileRef, schema, model: { modelName, folderKey, ... }, pageRange? })`.

```ts
.step('classify', documentClassify({ fileRef: input('file'), splitPages: true }))
.step('extract', dynamicExtract({ fileRef: input('file'),
  schema: { type: 'object', properties: { total: { type: 'string' } } },
  model: { modelName: 'invoiceixp-cef0d447-ixp', folderKey: '<folder-guid>' } }))
```

Dynamic Extract still needs a model deployment identity — copy `modelName` and
`folderKey` from the tenant; never construct them.

**Reference: [`references/document-pipeline.md`](references/document-pipeline.md)**

## Delay

Pause this path for a duration — or until an absolute date-time — then continue.

Signature: `delay({ duration: string })` or `delay({ until: string })`
(exactly one; `until` is an ISO-8601 date-time, e.g. `'2026-09-01T09:00:00Z'`).

```ts
.step('cooldown', delay({ duration: 'PT30S' }))
.step('embargo', delay({ until: '2026-09-01T09:00:00Z' }))
.step('resumedAt', script({ code: 'return new Date().toISOString();' }))
```

Use a real-time rung when elapsed time itself is the requirement.

**Reference: [`references/delay.md`](references/delay.md)**

## RPA workflow

Run a deployed robotic process and wait for its job result.

Signature: `rpaWorkflow({ key, name, folderPath, inputs?, returns? })`.

```ts
.step('title', rpaWorkflow({ key: releaseKey,
  name: 'RPA Workflow', folderPath: 'Shared',
  inputs: { problemId: 123 }, returns: { title: 'string' } }))
```

Confirm identity and argument names against the same deployed tenant resource.

**Reference: [`references/rpa-workflow.md`](references/rpa-workflow.md)**

**Finding the key: [`references/or-processes.md`](references/or-processes.md)**

## API workflow

Run a deployed coded API workflow and wait for its job result.

Signature: `apiWorkflow({ key, name, folderPath, inputs?, returns? })`.

```ts
.step('age', apiWorkflow({ key: workflowKey,
  name: 'NameToAge', folderPath: 'Shared',
  inputs: { name: input('name') }, returns: { age: 'integer' } }))
```

Confirm identity and exact argument casing on the tenant; `.onError(...)` is supported.

**Reference: [`references/api-workflow.md`](references/api-workflow.md)**

**Finding the key: [`references/or-processes.md`](references/or-processes.md)**

## Published function

Run a deployed Orchestrator **Function** — a small unit of code published as its
own resource — as one step.

Signature: `publishedFunction({ key, name, folderPath, inputs?, returns? })`.

```ts
.step('echo', publishedFunction({ key: functionKey,
  name: 'acme-echo', folderPath: 'Shared/acme-echo',
  inputs: { message: input('message') }, returns: { echoed: 'string' } }))
```

A function is usually deployed into a folder of its OWN name — read `folderPath`
from the tenant rather than assuming `'Shared'`, since the binding's resourceKey
is `<folderPath>.<name>`.

**Reference: [`references/published-function.md`](references/published-function.md)**

## Agentic process

Run a deployed Maestro agentic process synchronously.

Signature: `agenticProcess({ key, name, folderPath, inputs?, returns?, form?, completion? })`.

```ts
.step('intake', agenticProcess({ key: processKey,
  name: 'ProcurementProcess', folderPath: 'Shared',
  inputs: { productId: 1 }, returns: { status: 'boolean' } }))
```

Confirm identity and argument names live; declared outputs may still be null;
`.onError(...)` is supported. `form: 'bpmn' | 'flow' | 'case'` picks the published
form; `completion: 'fire-and-forget'` waits for nothing — see the reference.

**Reference: [`references/agentic-process.md`](references/agentic-process.md)**

**Finding the key: [`references/or-processes.md`](references/or-processes.md)**

## Agent resource

Start a published coded/low-code agent, or a sibling agent registered in this
solution, and wait for its answer.

Signature: `agent({ key, name, folderPath?, location?, projectId?, inputs, returns?, flavour? })`.

```ts
.step('count', agent({ key: releaseKey, name: 'CountLetters',
  folderPath: 'Shared', inputs: { word: input('word') },
  returns: { count: 'integer' }, flavour: 'coded' }))
```

This references rather than creates an agent; scaffold and register a task-created
sibling before calling it. Verify resource identity and answer quality live.
`.onError(...)` is supported.

**Reference: [`references/agent.md`](references/agent.md)**

## Inline agent

Define an autonomous agent inside this Flow project, with optional resources.

Signature: `inlineAgent({ model, systemPrompt, userPrompt, inputs?, returns?, source?, context?, tools?, escalation?, guardrails?, mode?, ... })`.

```ts
.step('triage', inlineAgent({ model: 'gpt-5.4', systemPrompt: 'Return JSON with category.',
  userPrompt: 'Classify {{input.body}}', inputs: { body: input('body') },
  returns: { category: 'string' },
  guardrails: [{ id: 'no-pii', $guardrailType: 'custom', name: 'Block PII', selector: { scopes: ['Agent'] },
    enabledForEvals: true, action: { $actionType: 'block', reason: 'PII detected' },
    rules: [{ $ruleType: 'always', applyTo: 'inputAndOutput' }] }] }))
```

`tools` also takes `mcp`, `a2a`, `clientside`, `httpRequest` and `function` kinds; `memory: { name, id }` attaches an episodic memory; `escalation` takes `variant: 'quick-form'` for an inline form. `mode: 'advanced'` selects the Advanced harness.

**Reference: [`references/inline-agent.md`](references/inline-agent.md)** — resource families: [`references/agent-resources.md`](references/agent-resources.md)

## Queue item

Create an Orchestrator queue item, optionally waiting for its consumer.

Signature: `queueItem({ queue, folderPath, key, item, priority?, reference?, deferDate?, dueDate?, wait?, returns? })`.

```ts
.step('enqueue', queueItem({ queue: 'Invoices', folderPath: 'Shared',
  key: queueKey, item: { InvoiceId: input('invoiceId') },
  reference: input('invoiceId'), wait: false }))
```

Check tenant uniqueness/schema settings; wait only when a consumer exists and its result is needed.

**Reference: [`references/queue.md`](references/queue.md)**

## Data Fabric

Use native Data Fabric nodes only when the scenario names Data Fabric
(`core.datafabric.read` / `.update`). “Data Service” instead names the
`uipath-uipath-dataservice` connector; route it to `connector(...)`.
Signatures: `dataFabricRead({ entity, filters? })` and
`dataFabricUpdate({ entity, record, set })` — `record` is exactly one of
`{ byId }` or `{ fromRead: '<read step name>' }`.

```ts
.step('lookup', dataFabricRead({ entity: 'Invoices',
  filters: [{ field: 'InvoiceId', value: input('invoiceId') }] }))
.step('markPaid', dataFabricUpdate({ entity: 'Invoices',
  record: { fromRead: 'lookup' }, set: { Status: 'Paid' } }))
```

Filters default to `operator: '='`; `or: true` joins a row with OR. No local
rung reads a real entity — offline validate is the acceptance bar.

**Reference: [`references/data-fabric.md`](references/data-fabric.md)**

## Error handling

Route the immediately preceding action's failure through a handler path.

Signature: `.step(name, action).onError(handler => ... )`; handler may use `err(step, field)` and `stepToRef(target)`. `.stepToList(port, fn)` runs a path from any port; `.stepToRef(port, target)` is a side exit that leaves the success path running.

```ts
.step('fetch', http({ url, managed: true }))
.onError((h) => h.step('recover', script({ code: 'return "cached";' }))
  .stepToRef('useValue'))
.step('useValue', script({ code: 'return "done";' }))
```

Choose deliberately between handling, rejoining, returning, terminating, and failing loud; test success and failure.

**Reference: [`references/error-handling.md`](references/error-handling.md)**

## Terminate

Stop the entire Flow run, including sibling parallel arms.

Signature: `.terminate(name, label?)`.

```ts
.branch('fatal', input('fatal'),
  (yes) => yes.terminate('abort', 'Abort run'),
  (no) => no.step('continue', script({ code: 'return "ok";' })))
```

Use it only for stop-all intent; prove cancellation with an abort-specific witness.

**Reference: [`references/terminate.md`](references/terminate.md)**

## Placeholder

Mark where a real capability will be inserted later.

Signature: `mock()`.

```ts
.step('extractInvoice', mock())
.step('continueWithInput', script({
  code: 'return $vars.assumedInvoiceId;' }))
```

Use a script for stand-in data; use a placeholder only to expose a capability gap.

**Reference: [`references/placeholder.md`](references/placeholder.md)**

## Unknown node type

Place a node this SDK has no factory for, carrying its definition verbatim.

Signature: `rawNode({ nodeType, version, manifest, inputs?, outputs? })`.

```ts
.step('exotic', rawNode({ nodeType: 'uipath.exotic.thing', version: '2.1',
  manifest: exoticManifest,       // exactly what `registry get` returned
  inputs: { where: input('scope') } }))
```

`manifest` must be a real definition, copied from the registry — not one you
wrote. Prefer a typed factory when one exists: it carries the family's checks,
defaults and output contract. `decompile` emits this for a node type it cannot
name, so an unknown node keeps its type and version through a round trip.

**Reference: [`references/placeholder.md`](references/placeholder.md#unknown-node-types)**

## Branch

Split runtime control into true and false paths.

Signature: `.branch(name, condition, thenFn, elseFn?)`.

```ts
.branch('large', js`${input('amount')} > 1000`,
  (yes) => yes.step('review', script({ code: 'return "review";' })),
  (no) => no.step('approve', script({ code: 'return "approved";' })))
```

Use branch for a two-way decision; decide whether arms return or ref back into shared work.

**Reference: [`references/branch.md`](references/branch.md)**

## Switch

Split runtime control among cases of one discriminant.

Signature: `.switch(name, on, [{ value, label?, body }], defaultFn?)`.

```ts
.switch('priority', input('priority'), [
  { value: 'high', body: (b) => b.step('page', script({ code: 'return 1;' })) },
  { value: 'low', body: (b) => b.step('queue', script({ code: 'return 2;' })) },
])
```

Prefer switch when one value selects three or more paths; use branch for two.

**Reference: [`references/switch.md`](references/switch.md)**

## Parallel branches

Fan out independent arms and join them at a Merge.

Signature: `.parallel(name, [armFn, armFn, ...])`.

```ts
.parallel('ready', [
  (a) => a.step('weather', http({ url: weatherUrl, managed: false })),
  (b) => b.step('news', http({ url: newsUrl, managed: false })),
])
```

Use it only for independent arms; do not assume the local executor runs them concurrently.

**Reference: [`references/parallel-merge.md`](references/parallel-merge.md)**

## Subflow

Run a child Flow authored in the same file as one parent step.

Signature: `subflow(childFlow, { childInput: expression, ... })`.

```ts
const child = flow('normalize').input({ raw: types.string })
  .output({ clean: types.string })
  .step('trim', script({ code: js`return ${input('raw')}.trim();`.js, returns: { clean: 'string' } }))
  .return({ clean: out('trim', 'clean') }).build();
export default flow('parent').input({ text: types.string }).output({ clean: types.string })
  .step('normalized', subflow(child, { raw: input('text') })).return({ clean: out('normalized', 'clean') }).build();
```

Use a child for a meaningful contract or reuse boundary, not arbitrary splitting or speed.
Read a child's inputs with `input(...)`: its start node is named `<callerStepId>Start`, so a bare `$vars.raw` is wrong.

**Reference: [`references/subflow.md`](references/subflow.md)**

## Human task

Pause for a person: an inline form, quick form, deployed Action App, or a
document-validation station.

Signature: `hitl({ variant?, app?, document?, title?, priority?, labels?, recipient?, fields?, outcomes, outcomePorts?, exposeError? })`.

```ts
.step('review', hitl({ title: 'Review invoice',
  recipient: { assignee: { type: 'user', value: 'reviewer@acme.test' } },
  fields: [{ id: 'amount', type: 'number', direction: 'inOut', value: input('amount') }],
  outcomes: ['Approve', 'Reject'], outcomePorts: true }))
.stepToList('outcome-reject', (b) => b.return({ status: 'rejected' }))
.step('proceed', script({ code: 'return "approved";' }))
```

`outcomePorts` routes per outcome (`outcome-<slug>` exits; the FIRST continues the main path); without it, route on `out('review', 'Action')`.

**Reference: [`references/hitl.md`](references/hitl.md)**

## Conversational

Work a live CHAT: wait for the person's message, answer it, post a reply. Every
step is keyed by a `conversationId` — the conversation trigger publishes it.

Signatures: `.trigger(conversationTrigger())`; `waitForMessage({ conversationId, numExchanges? })`; `conversationalAgent({ model, systemPrompt, settings })`; `sendMessage({ conversationId, exchangeId, content, endExchange? })`; `conversationContext({ conversationId, exchangeLimit? })`.

```ts
.trigger(conversationTrigger())
.step('listen', waitForMessage({ conversationId: out('start', 'conversationId') }))
.step('reply', conversationalAgent({ model: 'gpt-5.4', systemPrompt: 'Answer briefly.',
  settings: { context: out('listen', 'conversationContext') } }))
```

`waitForMessage` SUSPENDS the flow (a catch event), it does not poll. Use `sendMessage` when the flow decides what to say, an agent when the model does.

**Reference: [`references/conversational.md`](references/conversational.md)**

## Voice

Talk to someone on a phone call. The call is identified by a `callContext`
OBJECT — pass the whole thing, never a field inside it.

Signatures: `.trigger(voiceTrigger())`; `createOutgoingCall({ from, to })`; `endCall({ callContext })`; `voiceAgent({ systemPrompt, callContext, voice?, maxIterations? })`.

```ts
.step('dial', createOutgoingCall({ from: '+15550001111', to: input('phone') }))
.step('talk', voiceAgent({ systemPrompt: 'Confirm the delivery window.',
  callContext: out('dial', 'callContext'),
  voice: { model: 'gemini-3.1-flash-live-preview', persona: 'Kore' } }))
.step('bye', endCall({ callContext: out('dial', 'callContext') }))
```

The incoming-call trigger publishes `out('start', 'callContext')`. A persona belongs to its voice model; `maxIterations` is capped at 8.

**Reference: [`references/voice.md`](references/voice.md)**

## Transform

Filter, map, group, or chain operations over an array without custom JavaScript.

Signature: `transform({ collection, operations, variant?: 'filter' | 'map' | 'group-by' })`.

```ts
.step('active', transform({ variant: 'filter', collection: input('rows'),
  operations: [{ type: 'filter', filters: [
    { field: 'status', condition: 'equals', value: 'active' },
  ] }] }))
```

Prefer a named variant for one operation and generic Transform for a chain; verify chain order against real fields.

**Reference: [`references/transform.md`](references/transform.md)**

## Integration Service connectors

Call a curated or generic connector operation using a generated descriptor or key/action pair.

Signatures: `connector(descriptor, inputs, opts?)`;
`connector(key, action, inputs?, { connection?, folder?, object?, version? })`.

```ts
.step('issue', connector('uipath-atlassian-jira', 'get-issue',
  { issueId: input('issueId'), project: 'IN', issuetype: 'Task' },
  { connection: 'jira', folder: 'shared' }))
```

Data Service uses connector key `uipath-uipath-dataservice`; never substitute
`dataFabricRead`. Discover tenant-specific fields and ids; preserve every scenario-named input.

**Reference: [`references/connector-params.md`](references/connector-params.md)**

**Bindings: [`references/bindings.md`](references/bindings.md)**

## Loops

Run a body once for each value in a collection.

Signature: `.loop(name, collection, bodyFn, options?)`.

```ts
.loop('eachOrder', input('orders'), (body) => body
  .step('handle', script({ code:
    'return { id: $vars.eachOrder.currentItem.id };' })))
```

Per-iteration flow-variable writes go through `{ updates }` on a body step.
Options select the richer loop contract: `parallel: true`, `completionCondition`
(checked after each iteration, stops early), and `body.break()` exits the whole
loop from inside an arm. See the reference for the option details and examples.

**Reference: [`references/loops.md`](references/loops.md)**

## Do while

Run a body, then repeat **while a condition is true** — checked AFTER each
pass, so the body always runs at least once (`core.logic.dowhile`). The
container publishes no data output: write results to a `.var()` from inside
the body with `{ updates }`. `limit` caps iterations (1–10,000; blank means
the platform default of 10,000), and `body.break()` works exactly as in
`.loop()`.

Signature: `.doWhile(name, condition, bodyFn, { limit?, breakEnabled? })`.

```ts
.var('page', types.number, 1)
.doWhile('paginate', js`$vars.fetch.output.hasNextPage === true`, (body) => body
  .step('fetch', http({ url: tmpl`https://api.example.test/items?page=${v('page')}`,
    method: 'GET', managed: false, returns: { hasNextPage: 'boolean' } }),
    { updates: { page: js`$vars.page + 1` } }),
  { limit: 50 })
```

## Return and end

End the current path and bind declared Flow outputs.

Signature: `.return({ outputName: expression, ... })`.

```ts
.branch('valid', out('check'),
  (yes) => yes.return({ status: 'accepted' }),
  (no) => no.return({ status: 'rejected' }))
```

Choose between arm-local returns and a shared continuation based on the graph the scenario needs.

**Reference: [`references/return.md`](references/return.md)**

## Final evidence

The final pass must use the loop appropriate to the packaging mode and run after
the last edit. Product-resource truth is live evidence: confirm plausible ids,
argument names, scenario-named optional inputs, and warnings against the tenant.
Static diagnostics own all mechanically checkable structure; fix their cause
rather than copying rules back into this router.

Match proof to the request's acceptance bar. If one wiring question remains,
a validate-only bar is complete when product validation is green and its
required structural self-check passes; do not add debug only for confidence.
For each behavior claim the bar names, plan at most one bounded product debug
that answers it. If one wiring question remains, run one bounded experiment
that distinguishes it, apply the answer, and stop; do not grow a family of
scratch solutions or repeat equivalent variants.
