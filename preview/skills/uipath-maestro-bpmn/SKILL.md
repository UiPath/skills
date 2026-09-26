---
name: uipath-maestro-bpmn
description: "TRIGGER for authoring UiPath Maestro BPMN as `<Name>.bpmn.ts` with the TypeScript builder SDK (`@uipath/maestro-builder-sdk/bpmn`) and running the `uip maestro bpmn` check/compile/format/validate loop. Covers events, gateways, tasks, sub-processes, sequence flows, bindings, static rules, semantic `.bpmn` output, boundary handlers and branching written by nesting, event sub-processes, and any registry-backed extension type through `.activity()` — including one the SDK ships no typed method for. Flow builder authoring → uipath-maestro-flow; case plans → uipath-maestro-case."
allowed-tools: Bash, Read, Write, Edit, Glob, Grep, AskUserQuestion
---
<!-- CANONICAL — edit here, not in UiPath/flow-builder-sdk. Why: docs/SKILLS_PROMOTION_PLAN.md in that repo. -->

# UiPath Maestro BPMN — TypeScript Builder SDK

Author a Maestro process as a typed BPMN graph and compile it to `.bpmn` XML.
Builder methods map directly to events, gateways, activities, sub-processes,
variables, bindings, and sequence flows.

Use this file as a router. Read only the reference named by the capability you
need, then let TypeScript and `bpmn check` provide the detailed contract.

## Workflow

1. Scaffold the project first: `uip maestro bpmn init <Name>`. It writes
   `<Name>/<Name>.bpmn` plus `project.uiproj`, `operate.json`, `entry-points.json`,
   `bindings_v2.json`, and `package-descriptor.json` — the layout `bpmn pack` and
   product tooling require. Run it inside a solution to join that solution; run it
   outside one and a parent `<Name>Solution` is scaffolded around it.
2. Keep `<Name>.bpmn.ts` at the workspace root, beside `package.json`.
3. Import from `@uipath/maestro-builder-sdk/bpmn` and default-export a chain ending in `.build()`.
4. Seed the source by decompiling the stub `bpmn init` wrote —
   `uip maestro bpmn decompile <Name>/<Name>.bpmn -o <Name>.bpmn.ts` — rather than
   hand-writing the skeleton. It carries the process id and the `entryPointId` UUID the
   product assigned, which a hand-written chain cannot invent. An existing project needs
   no `init`: seed from the `.bpmn` already there. For shape, copy the closest staged
   `examples/*.bpmn.ts`.
5. Run `uip maestro bpmn check <Name>.bpmn.ts --source` after structural changes.
6. Compile **into the scaffolded project**, format only when layout is needed, and run
   product validation. Exactly one emitted `<Name>.bpmn` may exist, at
   `<Name>/<Name>.bpmn`; do not leave a second copy at the workspace root, and do not
   leave the template `init` wrote in place of your compiled output.
7. Use the merge pipeline for targeted edits to an existing process.

## API index

Indexed in the INSTALLED PACKAGE, not here, because a `.d.ts` line span is only
true of the build that emitted it. The `@uipath/maestro-builder-sdk` package
ships `dist/api-members.md`, keyed by field or method name (`gateway`), and
`dist/api-index.md`, keyed by exported symbol (`BpmnBuilder`). Match one name — do not
read either end to end — then read the span it gives you: the whole declaration,
doc comment included. Both cover all three entry points; each file's own header
spells the paths its rows are relative to.

## Capability router

| Surface | Builder/API | Reference | Example |
|---|---|---|---|
| Process and nested scopes | `bpmn`, `subProcess` | [Builders](#api-index) | `examples/NotifyChannel.bpmn.ts` |
| Variables, inputs, and outputs | `var`, `input`, `output`, `schema` | [ScopeBuilder](#api-index) | `examples/NotifyChannel.bpmn.ts` |
| Start, end, catch, throw, boundary | event methods | [Events](references/bpmn-runtime.md#events-and-timers) | `examples/NotifyChannel.bpmn.ts` |
| Error, timer, or message ON an activity | the body callback of any activity method: `onError`, `onTimer`, `onMessage` | [ActivityBuilder](#api-index) | `examples/InvoiceEscalation.bpmn.ts` |
| Exclusive, inclusive, parallel, event-based | gateway methods | [GatewayOpts](#api-index) | `examples/NotifyChannel.bpmn.ts` |
| Decision, parallel split, or wait-for-first, written in place | `choose`, `fork`, `race`, `goto` | [ChooseArm](#api-index) | `examples/InvoiceEscalation.bpmn.ts` |
| Safety net for a whole scope | `eventSubProcess` | [Event sub-process scope](references/bpmn-runtime.md#events-and-timers) | `examples/InvoiceEscalation.bpmn.ts` |
| Script and assignment tasks | `scriptTask`, `task` | [ScopeBuilder](#api-index) | `examples/NotifyChannel.bpmn.ts` |
| HTTP requests | `http` | [HTTP](references/bpmn-runtime.md#http-and-orchestrator-work) | `examples/NotifyChannel.bpmn.ts` |
| Orchestrator jobs and queues | start/execute/queue methods | [Work dispatch](references/bpmn-runtime.md#http-and-orchestrator-work) | `examples/NotifyChannel.bpmn.ts` |
| Human work | `humanTask` | [Human tasks](references/bpmn-runtime.md#human-task-outcomes) | `examples/NotifyChannel.bpmn.ts` |
| Connectors and external work | `connector`, `externalAgent`, `externalWorkflow` | [Connections](references/bpmn-runtime.md#connectors-and-bindings) | `examples/NotifyChannel.bpmn.ts` |
| Any registry type, typed method or not | `activity` | [Registry extension types](references/bpmn-runtime.md#registry-extension-types) | `examples/InvoiceApproval.bpmn.ts` |
| Existing BPMN | `bpmn decompile`, `compile`, `merge` | [Brownfield](references/bpmn-runtime.md#brownfield-editing) | `examples/NotifyChannel.bpmn.ts` |
| Process metadata, package, and layout | `metadata`, project metadata, `bpmn format` | [Contract metadata](references/bpmn-runtime.md#contract-metadata) | `examples/NotifyChannel.bpmn.ts` |

## Minimal shape

```ts
import { bpmn } from '@uipath/maestro-builder-sdk/bpmn';

export default bpmn('notify')
  .name('Notify')
  .startEvent('start')
  .task('record', { set: { status: 'ready' } })
  .endEvent('done')
  .sequenceFlow('start', 'record')
  .sequenceFlow('record', 'done')
  .build();
```

## Structure by nesting

Where a relationship can be written by nesting, write it that way instead of by id.
Each form lowers to the same elements and flows the explicit methods produce, and the explicit `.sequenceFlow()` still works anywhere, mixed freely.
`examples/InvoiceEscalation.bpmn.ts` is a full process written this way; `examples/InvoiceApproval.bpmn.ts` is the same kind of process as a decompiled import, written flat, which is what a brownfield edit starts from.

```ts
export default bpmn('approval')
  .var('action', 'string')
  .startEvent('start')
  .humanTask('approve', { app: 'InvoiceApproval', actions: ['Approve', 'Reject'] }, (t) => {
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
  .eventSubProcess('failures', { error: true, errorVar: 'unhandled' }, (h) =>
    h.task('record').endEvent('recorded', { name: 'Failure recorded' }))
  .build();
```

- A boundary event is declared on the activity it guards, in that activity's body callback, so `attachedTo` is never written.
  An interrupting handler's path rejoins at the statement after the activity; a non-interrupting one runs beside the activity and must end its own path with an end event, `.goto()`, or an explicit flow.
- `choose` arms need `when` or `otherwise: true`; the fallback is the default flow, and no flow id is named.
  Arms rejoin at the next statement, through a join named `<id>_join` only when more than one arm reaches it.
- Inside an arm or a handler, consecutive elements are wired in order; branch there with `choose` / `fork` / `race`, not a bare gateway, and jump elsewhere with `.goto(id)`.
- An event sub-process guards the whole container it sits in, catching what nothing closer caught; a boundary handler guards one activity.
  To fail one iteration rather than the whole run, put the `eventSubProcess` inside the multi-instance sub-process.
  `errorVar` names the variable the caught error lands in; read it as `=vars.<errorVar>.code` and `.message`.
- `check` warns `NO_DEFAULT_FLOW` on an exclusive gateway whose every flow is conditioned; give it an `otherwise` arm or a default.

## Validation loop

```bash
uip maestro bpmn init <Name>                  # once, before authoring
uip maestro bpmn check <Name>.bpmn.ts --source
uip maestro bpmn compile <Name>.bpmn.ts -o <Name>/<Name>.bpmn
uip maestro bpmn format <Name>/<Name>.bpmn
uip maestro bpmn validate <Name>/<Name>.bpmn --output json
```

`check` owns source and graph invariants. Product validation owns the compiled
BPMN contract. Change the TypeScript source and rebuild; do not patch emitted XML.

## Evidence boundary

Static success does not prove tenant resource resolution, human outcomes, or
runtime-only values. Read [BPMN runtime decisions](references/bpmn-runtime.md)
when the requested outcome depends on those behaviors.
