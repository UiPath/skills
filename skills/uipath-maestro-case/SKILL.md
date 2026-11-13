---
name: uipath-maestro-case
description: "UiPath Maestro Case Management (`.case.ts`, `caseplan.case`, `caseplan.json`): build, edit or fix a case plan. Always invoke for those files, for a case `sdd.md`, or to build or create a case. Authors the `.case.ts` source with the TypeScript builder SDK (`@uipath/maestro-builder-sdk/case`), compiles it into the project's plan file, and runs the `uip maestro case` check/compile/validate loop. Covers stages, tasks, rules, triggers, SLAs, human action tasks, bindings, published-resource references (registry pull, sdd resolve), and brownfield decompile/edit/recompile. For .xaml→uipath-rpa, .flow/.flow.ts→uipath-maestro-flow, .bpmn/.bpmn.ts→uipath-maestro-bpmn. For standalone case SDD design, case `sdd.draft.md` finalization, PDD→SDD, or cross-product planning→uipath-planner."
allowed-tools: Bash, Read, Write, Edit, Glob, Grep, AskUserQuestion
---
<!-- CANONICAL — edit here, not in UiPath/flow-builder-sdk. Why: docs/SKILLS_PROMOTION_PLAN.md in that repo. -->
# UiPath Case Management — TypeScript Builder SDK

Author a Case plan as TypeScript and compile it to schema V30 into the project's plan file; a Case plan declares stages and conditions, not control-flow edges.

Use this as a router: read only the capability reference you need, then let TypeScript and `case check` provide the detailed contract.

<!--skill-flavor:host-setup:start-->

<!--skill-flavor:host-setup:end-->
## Workflow

**Stop rule, before any step:** when the request says design-only, Phase 1 only, review first, not to build, not to create the case plan, or to stop before tenant work, run no `solution init`, `case init`, `decompile` or `compile`. Write no `<Name>.case.ts`, `caseplan.case` or `caseplan.json`, and no `tasks/tasks.md` or other restatement of the SDD unless the request asks for one. When the request says Phase 1 only, review first, or not to build, or asks for registry or resource lookups, run step 0 for an approved `sdd.md` plus any lookup the request asks for, then stop. Otherwise (design-only, no case plan, stop before tenant work) run no registry or other tenant command. Report the deferred build work in the reply.

**Design first:** when the request is to build or create a case and no `sdd.md` exists, invoke `uipath-planner`'s `design` verb (Case Management) in this conversation (the Skill tool, never a subagent) before any other step. The lane owns the design, its one review, and the `sdd.md` write; then continue at step 0 with that `sdd.md`. Never overwrite an existing `sdd.md`. If the planner is unavailable, say so once, ask for an `sdd.md` or an approved design, and stop. A targeted edit of an existing plan or `<Name>.case.ts` needs no SDD. An `sdd.md` from an earlier session is approved when its `## Planner Handoff` table reads `Template validation` `passed`; otherwise send it back through the planner.

**Never use `sdd convert` as the build path.** Its output has flat connector inputs and unresolved references — `validate` rejects it. If convert was run, decompile its output and continue from step 5.

0. When the input is an approved `sdd.md` that names published resources, resolve them first: `registry pull`, then `sdd resolve` into `tasks/registry-resolved.json`, then ask the user about what it leaves ([Registry resolution](references/registry-resolution.md)). Stop there when the request is Phase 1 only.
<!--skill-flavor:workflow-scaffold:start-->
1. Scaffold once, running `case init` **from inside the solution dir**: `uip solution init <SolutionName> && cd <SolutionName> && uip maestro case init <CaseName>`. It walks UP for the enclosing `.uipx`; run from anywhere else it finds none, silently creates a SECOND solution `<CaseName>Solution/`, registers the project there, and leaves the first empty with two `project.uiproj` on disk — so check the reply carries no `Data.AutoCreatedSolution`. Exactly one `project.uiproj` declaring `ProjectType: "CaseManagement"` may survive, because `uip solution projects import` copies rather than moves and validators cannot choose between duplicates; if a bare `<CaseName>/` project already exists outside the solution, import it and delete the original rather than leaving both.
2. Install the SDK first, once per machine: `npm install -g @uipath/maestro-builder-sdk` (6.70.7 or later; `npm ls -g @uipath/maestro-builder-sdk` shows the installed version). Skip it when a recent enough version is installed. Write `<Name>.case.ts` in the solution dir (the working directory after step 1), beside the Case project folder, not inside it; no `package.json` is needed. Do not add one: an `npm init -y` `package.json` sets `"type": "commonjs"`, and then `check` and `compile` fail with `Cannot use import statement outside a module`.
<!--skill-flavor:workflow-scaffold:end-->
3. If the request requires `tasks/tasks.md`, write it before code and treat explicit stage/task rules, required flags, routing, and unresolved resources as authoritative and pre-approved.
4. Import from `@uipath/maestro-builder-sdk/case`; default-export a chain ending in `.build()`.
<!--skill-flavor:workflow-build:start-->
5. Seed the source by decompiling the plan `case init` seeded (`caseplan.case`, or an older `caseplan.json`) instead of hand-writing the skeleton: `uip maestro case decompile <project>/<plan> -o <Name>.case.ts --no-pipeline`. It carries the case id, `.name`, `.identifier` and `trigger_1` the product already assigned; `entry-points.json` references that trigger id. Compile back into that same `<plan>`, never a second plan beside it: pack and debug read only one. Compile with plain `-o <project>/<plan>` and no `--bindings <plan>`; it needs `@uipath/maestro-builder-sdk` 6.50.1 or later to keep a Designer-saved plan's binding map ([Brownfield](references/case-runtime.md#brownfield-editing)). Author inside the chain; the trailing `preserveCaseJson(...)` is decompiler-owned wire data — never hand-edit it, and leave it in place. For shape, copy the closest staged `examples/*.case.ts`.
6. Run `uip maestro case check <Name>.case.ts --source` before every compile, gate edits included (`skipWhen`, a rule `expression`); fix every error (non-zero exit) first. For instance, `check` reports a `vars.<id>` read of an undeclared variable as `EXPR_UNDECLARED_REF`.
7. Compile into the scaffolded Case project, then validate. Compile syncs existing sidecars; refresh added bindings and remove orphaned resources before refreshing.
8. Run live debug only when requested and tenant resources are available.
<!--skill-flavor:workflow-build:end-->

## API index

<!--skill-flavor:api-index-location:start-->
Indexed in the INSTALLED PACKAGE, not here, because a `.d.ts` line span is only
true of the build that emitted it. `@uipath/maestro-builder-sdk` ships
`dist/api-members.md` (keyed by field or method — `sla`) and `dist/api-index.md`
(keyed by exported symbol — `CaseBuilder`). Match one name, not the whole file,
then read the span: the whole declaration, doc comment included. Both cover all
three entry points; each file's header spells the paths its rows resolve against.
<!--skill-flavor:api-index-location:end-->

## Capability router

| Surface | Builder/API | Reference | Example |
|---|---|---|---|
| Case, stages, and completion | `casePlan`, `stage`, `completeWhen` | [CaseBuilder](#api-index) | `examples/ClaimReviewSLA.case.ts` |
| Variables and arguments | `var`, `input`, `output`, `jsonSchema` | [CaseBuilder](#api-index) | `examples/IntakeBinding.case.ts` |
| Manual, timer, and event starts | `manualTrigger`, `timerTrigger`, `eventTrigger` | [Trigger decisions](references/case-runtime.md#triggers-and-live-payloads) | `examples/NightlyRollup.case.ts` |
| A task's outputs, and reading them from a later task or gate (SDK 6.70.7+) | `outputs`: a key equal to the source's last segment (`app_id: '=response.app_id'`) keeps the output on the task, with no case variable, unless a `.var()` of that name exists or another task uses the same key (then both write one shared case variable; give the second task the suffixed key, `Result2: '=Result'`, to keep it on its task); `taskOutput('<stage>', '<task>', '<output>')`, or the SDD's `vars.$xref(...)` as written, reads it, where `<output>` is the result field it reads or its `outputs` key, and an unknown name is refused (`TASK_OUTPUT_REF_UNRESOLVED`) | [TaskBuilder, taskOutput](#api-index) | — |
| Entry, exit, and data gates | `rule`, `when` | [Rules](#api-index) | `examples/ClaimReviewSLA.case.ts` |
| Business events an outside system sends to a running case | `businessEvent`, `rule('api-event', { businessEvent })` (SDK 6.47.0+) | [CaseBuilder, Rules](#api-index) | — |
| Published UiPath work | `process`, `agent`, `rpa`, `apiWorkflow`, `caseManagement`, `flowProcess`, `unresolved` | [TaskBuilder](#api-index) | `examples/ClaimReviewSLA.case.ts` |
| Business rules (decision tables) | `businessRule` (SDK 6.34.0+) | [TaskBuilder](#api-index) | `examples/CreditDecision.case.ts` |
| Deployed Coded Functions | `function` (SDK 6.47.1+) | [TaskBuilder](#api-index) | — |
| Script tasks | `script(fn \| body)` (SDK 6.81.0+) | [Script tasks](references/case-runtime.md#script-tasks) | `examples/ScriptCase.case.ts` |
| Resolving SDD resources against the tenant | `uip maestro case registry pull`, `uip maestro case sdd resolve` | [Registry resolution](references/registry-resolution.md) | — |
| Human work and its Action App | `action`; `app: { name, folder }` (SDK 6.46.4+) names the app (`actionCatalogName` is a task catalog, not the app) | [Human tasks](references/case-runtime.md#human-and-on-demand-work) | `examples/NotifyOnApproval.case.ts` |
| HTTP requests | `httpRequest({ method, url or path, headers?, query?, body?, connector? })` (SDK 6.82.1+) | [HTTP requests](references/case-runtime.md#http-requests) | `examples/HttpRequestSingleCase.case.ts` |
| Connector work and waits | `connector`, `waitForConnector` | [Connections](references/case-runtime.md#connections-and-external-work) | `examples/NotifyOnApproval.case.ts` |
| External agents and workflows | `externalAgent`, `externalWorkflow` | [Connections](references/case-runtime.md#connections-and-external-work) | `examples/NotifyOnApproval.case.ts` |
| Timers | `waitForTimer` | [TimerSpecData](#api-index) | `examples/NightlyRollup.case.ts` |
| Deadlines and escalation | `sla`, `escalation`, `toUser`, `toGroup` | [SLA](references/case-runtime.md#sla-and-runtime-semantics) | `examples/ClaimReviewSLA.case.ts` |
| Case App and layout | `caseApp`, `layout` | [CaseBuilder](#api-index) | `examples/ClaimReviewSLA.case.ts` |
| Existing Case plans | `case decompile --no-pipeline`, then `compile -o <plan>` | [Brownfield](references/case-runtime.md#brownfield-editing) | `examples/ClaimReviewSLA.case.ts` |
| Task activation modes (parallel, parallel-after-predecessor, sequential) | `rule('runs-sequentially')`, `.task(name, fn, { lane })` | [Activation modes](#activation-modes) | — |
| Document extraction (IXP model on a case document) | `.documentExtraction(model, spec)` | [Document extraction](#document-extraction) | — |

## Activation modes

For an SDD `Activation Mode` column, use the SDK's `runs-sequentially` rule and the `lane` parameter on `.task()`. Within a stage, task-set grouping controls ordering:

| SDD Activation Mode | SDK entry rule | `lane` param | Effect |
|---|---|---|---|
| `parallel` | `rule('current-stage-entered')` | omit | Task starts when the stage enters. Each task gets its own set. |
| `parallel-after-predecessor` | `rule('runs-sequentially')` | shared index across siblings | Siblings share one set and start together after the predecessor set completes. |
| `sequential` | `rule('runs-sequentially')` | unique index per task | Strict chain: each task waits for the previous set. |

`lane` is the set index in `data.tasks[][]`. **Omitting `lane` defaults to set 0** (`lane ?? 0` in the SDK). Tasks that share the same set index start together after the predecessor set completes. A task without `runs-sequentially` always gets its own set regardless of `lane`. To place a `runs-sequentially` task in a distinct set, give it a unique `lane` value.

Pass `{ lane: N }` as the second argument to `.task()` (after the builder callback). Every task with `runs-sequentially` needs an explicit `lane` — omitting it defaults to 0:

```ts
.stage('Issuing Permit', s => s
  // Set 0: predecessor alone
  .task('Collect Fees', t => t.process('collect').required()
    .entryWhen(rule('runs-sequentially')), { lane: 0 })
  // Set 1: two siblings start together after set 0
  .task('Wait For Confirmation', t => t.waitForTimer({ duration: 'PT1H' }).required()
    .entryWhen(rule('runs-sequentially')), { lane: 1 })
  .task('Track Deadline', t => t.waitForTimer({ duration: 'P5D' }).required()
    .entryWhen(rule('runs-sequentially')), { lane: 1 })
  // Set 2: downstream, waits for set 1
  .task('Generate Permit', t => t.process('generate').required()
    .entryWhen(rule('runs-sequentially')), { lane: 2 }))
```

Emits `tasks: [[Collect Fees], [Wait, Track], [Generate]]` — three sets. The two siblings sharing `{ lane: 1 }` merge into set 1. Collect Fees (`lane: 0`) and Generate Permit (`lane: 2`) each occupy their own set.

**Anti-pattern:** omitting `lane` on all `runs-sequentially` tasks — they all default to set 0 and start together, losing the sequential structure. Giving every task the same explicit `lane` has the same effect.

## Document extraction

A document-extraction task runs a deployed IXP model against a case document. IXP deployments are NOT in the case registry cache (`registry pull` does not find them). Discover and add them separately:

```bash
# List all IXP deployments on the tenant
uip solution resources list --kind IxpDeployment --source remote --output json
# Add the deployment to the solution (required for bindings)
uip solution resources add --source remote --kind IxpDeployment --cloud-key <KEY> --output json
```

The deployment row gives `Key` (deploymentKey), `Name` (DeploymentTitle), `Folder`, and `FolderKey`. The model's `DeploymentName` (`<slug>-<hash>-ixp`) comes from:

```bash
uip ixp deployments list <IXP_PROJECT_NAME> --output json
```

Use the deployment's **DeploymentName**, not the IXP project's name, as `modelName`.

### Builder

`.documentExtraction(model, spec)` on `TaskBuilder`:

```ts
.task('Extract Receipt', t => t
  .documentExtraction('invoice-model-0a1b2c3d-ixp', {
    deployment: 'Invoice Extractor',
    deploymentKey: '<DEPLOYMENT_KEY>',
    folderKey: '<FOLDER_KEY>',
    folder: 'Shared',
    file: '=vars.invoice',
  })
  .required()
  .entryWhen(rule('current-stage-entered')))
```

If `check --source` refuses `documentExtraction` as unknown, the installed SDK predates the builder. Use `sdd convert` to seed the plan, then decompile and author the remaining TypeScript from the seeded source (step 5 of the Workflow).

### Shape

The compiled task carries `type: "document-extraction"`, `data.serviceType: "IXP.Extraction"`, `data.version: "v2"`, and `data.context[]` in the Designer's field order:

| # | context name | value |
|---|---|---|
| 1 | `solutionResourceKey` | deploymentKey (the `Key` from `resources list`) |
| 2 | `name` | `=bindings.<ixpDeployment-binding-id>` (a root binding, `resource: "ixpDeployment"`, `resourceKey: <deploymentKey>`, `default: <DeploymentTitle>`) |
| 3 | `folderKey` | FolderKey from the deployment row |
| 4 | `folderName` | folder path (e.g. `Shared`) |
| 5 | `modelName` | DeploymentName (`<slug>-<hash>-ixp`) |
| 6 | `modelDisplayName` | DeploymentTitle |
| 7 | `digitizationMode` | `fileUpload` |

Inputs: `fileRef` (file, required) and `pageRange` (string). Outputs: `output` (`=result`, the extracted fields) and `error` (`=Error`).

After compile, add the deployment to the solution and sync bindings:

```bash
uip solution resources add --source remote --kind IxpDeployment --cloud-key <KEY> --output json
```

Verify the deployment appears in `bindings_v2.json` and in `uip solution resources list --source local`.

## Minimal shape

```ts
import { casePlan, rule } from '@uipath/maestro-builder-sdk/case';

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
      .action({ title: 'Approve loan', priority: 'High', recipient: 'manager@corp.com', app: { name: 'LoanApproval', folder: 'Shared' } })
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

<!--skill-flavor:validation-loop:start-->
```bash
uip maestro case check <Name>.case.ts --source
uip maestro case compile <Name>.case.ts -o <project>/<plan>
uip maestro case validate <project>/<plan> --strict --sdd <sdd.md> --output json  # SDD supplied
uip maestro case validate <project>/<plan> --strict --output json                 # no SDD
uip solution resources remove <orphan-key> --solution-folder <solution> --output json
uip solution resources refresh --solution-folder <solution> --output json
```
<!--skill-flavor:validation-loop:end-->

`check` owns source-level invariants and emits teaching diagnostics. Product
validation owns the compiled Case contract. Do not repair emitted JSON by hand;
change the TypeScript source and rebuild.

> **`sdd convert` is a seed, not a build path** — see the Workflow section above.

The build is complete only when `validate --strict` passes. When the request
supplies an `sdd.md`, add `--sdd <path>`: it audits the plan against the SDD.
Without an SDD, run `--strict` alone. A default-profile `Valid` whose
`Data.Suppressed.Errors` is above 0 is not completion; run the command its
`Instructions` names. Fix each finding in the TypeScript source and recompile.
If a finding persists after a source fix and recompile, stop and report its
code as unfinished; never patch emitted JSON.

`check` also reads the connector library, the same one `compile` resolves
against: `$FLOW_SDK_LIBRARY_JSON`, else the `uip maestro registry pull`
snapshot, plus `.flow-sdk/connectors-local` when `registry prepare` wrote it.
A connector task, external task, event trigger or wait-for-connector that
`compile` cannot resolve fails `check` first, with compile's code and text.

<!--skill-flavor:library-pull:start-->
Before `check` on a Case with connector work, run `uip maestro registry pull`:
with no library cached these rules stay silent, so a clean `check` proves
nothing about the connector. To use another library, set
`$FLOW_SDK_LIBRARY_JSON` for both `check` and `compile`, not `--library`, so
both resolve against the same one.
<!--skill-flavor:library-pull:end-->

Use `.unresolved('<kind>')` for an explicitly unresolved process, agent, RPA,
API workflow, Coded Function, or sub-case; never fabricate a name or folder. A destination's
`selected-stage-completed` entry does not imply a source `exitToStage` hand-off.
An unresolved connector is `.unresolved('connector')` or
`.unresolved('wait-for-connector')`; never pick a real connector to stand in,
and a placeholder takes no outputs.

## Evidence boundary

Static success proves the source and artifact contracts. It proves neither live
behavior (resource resolution, human outcomes, timers, skipped-task completion,
business calendars) nor the design decisions no schema checks: lane routing,
non-completing exits, declared optionality, and SDD intent beyond what the
`--sdd` audit compares. Read [Case runtime decisions](references/case-runtime.md) before authoring, not only when a rung fails.
