---
name: uipath-maestro-case
description: "TRIGGER for authoring UiPath Maestro Case plans as `<Name>.case.ts` with the reference-mode TypeScript builder SDK (`@uipath/flow-sdk/case`), compiling to `caseplan.json`, and running the `uip maestro case` check/compile/validate loop. Covers stages, tasks, rules, bindings, published-resource references, and brownfield decompile/edit/recompile. Flow builder authoring → uipath-maestro-flow; structural-core BPMN → uipath-maestro-bpmn. DO NOT TRIGGER for C#/XAML automation → uipath-rpa."
allowed-tools: Bash, Read, Write, Edit, Glob, Grep, AskUserQuestion
---
<!--
Provenance: snapshot of UiPath/flow-builder-sdk
`typescript/sdk/skill/SKILL-case.md` @ 965313a. Canonical source lives there;
edit upstream and re-sync (see UiPath/flow-builder-sdk#405).

This is a snapshot of a generated file. In flow-builder-sdk,
`typescript/sdk/scripts/gen-case-skill.mjs` renders it from
`typescript/sdk/skill/SKILL-case.template.md` and the built `.d.ts`; edits
belong upstream.
-->
# UiPath Case Management — TypeScript Builder SDK

Author a Case plan as TypeScript and compile it to schema V30 `caseplan.json`; a Case plan declares stages and conditions, not control-flow edges.

Use this as a router: read only the capability reference you need, then let TypeScript and `case check` provide the detailed contract.

## Workflow

1. Scaffold with `uip solution init <SolutionName>`, then run `uip maestro case init <CaseName>` inside it. Scaffold once: exactly one `project.uiproj` declaring `ProjectType: "CaseManagement"` may survive, because `uip solution projects import` copies rather than moves and validators cannot choose between duplicates. If a bare `<CaseName>/` project already exists outside the solution, import it and delete the original rather than leaving both.
2. Keep `<Name>.case.ts` beside this `SKILL.md` and the workspace `package.json`.
3. If the request requires `tasks/tasks.md`, write it before code and treat explicit stage/task rules, required flags, routing, and unresolved resources as authoritative and pre-approved.
4. Import from `@uipath/flow-sdk/case`; default-export a chain ending in `.build()`.
5. Start from the closest staged `examples/*.case.ts`; change only scenario data.
6. Run `uip maestro case check <Name>.case.ts --source` after each structural change.
7. Compile into the scaffolded Case project, then validate. Compile syncs existing sidecars; refresh added bindings and remove orphaned resources before refreshing.
8. Run live debug only when requested and tenant resources are available.

## Capability router

| Surface | Builder/API | Reference | Example |
|---|---|---|---|
| Case, stages, and completion | `casePlan`, `stage`, `completeWhen` | [CaseBuilder](references/api.md#casebuilder-class) | `examples/ClaimReviewSLA.case.ts` |
| Variables and arguments | `var`, `input`, `output`, `jsonSchema` | [CaseBuilder](references/api.md#casebuilder-class) | `examples/IntakeBinding.case.ts` |
| Manual, timer, and event starts | `manualTrigger`, `timerTrigger`, `eventTrigger` | [Trigger decisions](references/case-runtime.md#triggers-and-live-payloads) | `examples/NightlyRollup.case.ts` |
| Entry, exit, and data gates | `rule`, `when` | [Rules](references/api.md#rule-function) | `examples/ClaimReviewSLA.case.ts` |
| Published UiPath work | `process`, `agent`, `rpa`, `apiWorkflow`, `caseManagement`, `flowProcess`, `unresolved` | [TaskBuilder](references/api.md#taskbuilder-class) | `examples/ClaimReviewSLA.case.ts` |
| Human work | `action` | [Human tasks](references/case-runtime.md#human-and-on-demand-work) | `examples/NotifyOnApproval.case.ts` |
| Connector work and waits | `connector`, `waitForConnector` | [Connections](references/case-runtime.md#connections-and-external-work) | `examples/NotifyOnApproval.case.ts` |
| External agents and workflows | `externalAgent`, `externalWorkflow` | [Connections](references/case-runtime.md#connections-and-external-work) | `examples/NotifyOnApproval.case.ts` |
| Timers | `waitForTimer` | [TimerSpecData](references/api.md#timerspecdata-type) | `examples/NightlyRollup.case.ts` |
| Deadlines and escalation | `sla`, `escalation`, `toUser`, `toGroup` | [SLA](references/case-runtime.md#sla-and-runtime-semantics) | `examples/ClaimReviewSLA.case.ts` |
| Case App and layout | `caseApp`, `layout` | [CaseBuilder](references/api.md#casebuilder-class) | `examples/ClaimReviewSLA.case.ts` |
| Existing Case plans | `case decompile` and generated pipeline | [Brownfield](references/case-runtime.md#brownfield-editing) | `examples/ClaimReviewSLA.case.ts` |

## Minimal shape

```ts
import { casePlan, rule } from '@uipath/flow-sdk/case';

export default casePlan('loan-approval')
  .name('Loan Approval')
  .identifier('LOAN')
  .stage('Review', s => s
    .required()
    .entryWhen(rule('case-entered'), { displayName: 'Case entered' })
    .exitWhen(rule('required-tasks-completed'), { displayName: 'All done', marksStageComplete: true })
    .task('Check Policy', t => t
      .process('check-policy', { folder: 'Shared' })
      .required()
      .entryWhen(rule('current-stage-entered')))
    .task('Manager Approval', t => t
      .action({ title: 'Approve loan', priority: 'High', recipient: 'manager@corp.com' })
      .entryWhen(rule('selected-tasks-completed', { tasks: ['Check Policy'] }))))
  .stage('Decision', s => s
    .required()
    .entryWhen(rule('selected-stage-completed', { stage: 'Review' }), { displayName: 'After review' })
    .exitWhen(rule('required-tasks-completed'), { marksStageComplete: true })
    .task('Notify', t => t.process('notify').required().entryWhen(rule('current-stage-entered'))))
  .completeWhen(rule('required-stages-completed'), { displayName: 'Case resolved' })
  .build();
```

## Validation loop

```bash
uip maestro case check <Name>.case.ts --source
uip maestro case compile <Name>.case.ts -o <project>/caseplan.json
uip maestro case validate <project>/caseplan.json --output json
uip solution resources remove <orphan-key> --solution-folder <solution> --output json
uip solution resources refresh --solution-folder <solution> --output json
```

`check` owns source-level invariants and emits teaching diagnostics. Product
validation owns the compiled Case contract. Do not repair emitted JSON by hand;
change the TypeScript source and rebuild.

Use `.unresolved('<kind>')` for an explicitly unresolved process, agent, RPA,
API workflow, or sub-case; never fabricate a name or folder. A destination's
`selected-stage-completed` entry does not imply a source `exitToStage` hand-off.

## Evidence boundary

Static success proves the source and artifact contracts. It proves neither live
behavior (resource resolution, human outcomes, timers, skipped-task completion,
business calendars) nor the design decisions no schema checks: lane routing,
non-completing exits, declared optionality, SDD fidelity. Read [Case runtime decisions](references/case-runtime.md) before authoring, not only when a rung fails.
