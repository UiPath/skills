---
name: uipath-maestro-bpmn
description: "TRIGGER for authoring structural-core UiPath Maestro BPMN as `<Name>.bpmn.ts` with the TypeScript builder SDK (`@uipath/flow-sdk/bpmn`) and running the `uip maestro bpmn` check/compile/format/validate loop. Covers events, gateways, tasks, sub-processes, sequence flows, bindings, static rules, and semantic `.bpmn` output. Flow builder authoring → uipath-maestro-flow; case plans → uipath-maestro-case. DO NOT TRIGGER for registry-backed typed BPMN nodes beyond the structural core."
allowed-tools: Bash, Read, Write, Edit, Glob, Grep, AskUserQuestion
---
<!--
Provenance: snapshot of UiPath/flow-builder-sdk
`typescript/sdk/skill/SKILL-bpmn.md` @ 48e87bc. Canonical source lives there;
edit upstream and re-sync (see UiPath/flow-builder-sdk#405).
-->

# UiPath Maestro BPMN — TypeScript Builder SDK

Author a Maestro process as a typed BPMN graph and compile it to `.bpmn` XML.
Builder methods map directly to events, gateways, activities, sub-processes,
variables, bindings, and sequence flows.

Use this file as a router. Read only the reference named by the capability you
need, then let TypeScript and `bpmn check` provide the detailed contract.

## Workflow

1. Keep `<Name>.bpmn.ts` beside this `SKILL.md` and the workspace `package.json`.
2. Import from `@uipath/flow-sdk/bpmn` and default-export a chain ending in `.build()`.
3. Start from the closest staged `examples/*.bpmn.ts`.
4. Run `uip maestro bpmn check <Name>.bpmn.ts --source` after structural changes.
5. Compile, format only when layout is needed, and run product validation.
6. Use the merge pipeline for targeted edits to an existing process.

## Capability router

| Surface | Builder/API | Reference | Example |
|---|---|---|---|
| Process and nested scopes | `bpmn`, `subProcess` | [Builders](references/api.md#bpmnbuilder-class) | `examples/NotifyChannel.bpmn.ts` |
| Variables, inputs, and outputs | `var`, `input`, `output`, `schema` | [ScopeBuilder](references/api.md#scopebuilder-class) | `examples/NotifyChannel.bpmn.ts` |
| Start, end, catch, throw, boundary | event methods | [Events](references/bpmn-runtime.md#events-and-timers) | `examples/NotifyChannel.bpmn.ts` |
| Exclusive, inclusive, parallel, event-based | gateway methods | [GatewayOpts](references/api.md#gatewayopts-interface) | `examples/NotifyChannel.bpmn.ts` |
| Script and assignment tasks | `scriptTask`, `task` | [ScopeBuilder](references/api.md#scopebuilder-class) | `examples/NotifyChannel.bpmn.ts` |
| HTTP requests | `http` | [HTTP](references/bpmn-runtime.md#http-and-orchestrator-work) | `examples/NotifyChannel.bpmn.ts` |
| Orchestrator jobs and queues | start/execute/queue methods | [Work dispatch](references/bpmn-runtime.md#http-and-orchestrator-work) | `examples/NotifyChannel.bpmn.ts` |
| Human work | `humanTask` | [Human tasks](references/bpmn-runtime.md#human-task-outcomes) | `examples/NotifyChannel.bpmn.ts` |
| Connectors and external work | `connector`, `externalAgent`, `externalWorkflow` | [Connections](references/bpmn-runtime.md#connectors-and-bindings) | `examples/NotifyChannel.bpmn.ts` |
| Generic registry activity | `activity` | [ActivityNodeOpts](references/api.md#activitynodeopts-interface) | `examples/NotifyChannel.bpmn.ts` |
| Existing BPMN | `bpmn decompile`, `compile`, `merge` | [Brownfield](references/bpmn-runtime.md#brownfield-editing) | `examples/NotifyChannel.bpmn.ts` |
| Project package and layout | project metadata, `bpmn format` | [Packaging](references/bpmn-runtime.md#packaging-and-layout) | `examples/NotifyChannel.bpmn.ts` |

## Minimal shape

```ts
import { bpmn } from '@uipath/flow-sdk/bpmn';

export default bpmn('notify')
  .name('Notify')
  .startEvent('start')
  .task('record', { set: { status: 'ready' } })
  .endEvent('done')
  .sequenceFlow('start', 'record')
  .sequenceFlow('record', 'done')
  .build();
```

## Validation loop

```bash
uip maestro bpmn check <Name>.bpmn.ts --source
uip maestro bpmn compile <Name>.bpmn.ts -o <Name>.bpmn
uip maestro bpmn format <Name>.bpmn
uip maestro bpmn validate <Name>.bpmn --output json
```

`check` owns source and graph invariants. Product validation owns the compiled
BPMN contract. Change the TypeScript source and rebuild; do not patch emitted XML.

## Evidence boundary

Static success does not prove tenant resource resolution, human outcomes, or
runtime-only values. Read [BPMN runtime decisions](references/bpmn-runtime.md)
when the requested outcome depends on those behaviors.
