---
name: uipath-maestro-flow
description: "TRIGGER for `.flow` / `.flow.ts` files and UiPath Flow / Maestro Flow / Maestro Automate requests: build, edit, run, debug, fix, or evaluate a flow. Author with the TypeScript builder SDK (`@uipath/maestro-builder-sdk`): nodes, triggers, schedules, connectors, IXP document extraction (add or list IXP models), inline agents, HITL, chat/voice flows, bindings, brownfield edits, and the check/compile/validate loop. Operate: upload, publish, deploy, debug a real run, trigger a process, job status/traces, pause/resume/cancel/retry an instance. Diagnose: faulted runs, incidents, runtime variables, why validate passed but the run failed. Evaluate: eval sets, evaluators, simulations, eval runs. Case plans (`caseplan.json`) → uipath-maestro-case; BPMN (`.bpmn`, `.bpmn.ts`) → uipath-maestro-bpmn. DO NOT TRIGGER for raw IXP labelling or prompt tuning outside a Flow → uipath-ixp; standalone agents → uipath-agents; C#/XAML → uipath-rpa."
allowed-tools: Bash, Read, Write, Edit, Glob, Grep, AskUserQuestion
---
<!-- CANONICAL — edit here, not in UiPath/flow-builder-sdk. Why: docs/SKILLS_PROMOTION_PLAN.md in that repo. -->

# UiPath Flow — TypeScript Builder SDK

UiPath Flow orchestrations can be authored in TypeScript using the `@uipath/maestro-builder-sdk` package.
The SDK provides a builder API to construct a Flow graph, allowing developers to define inputs, outputs, steps, and control flow in a type-safe manner.
The graph is "compiled" down to a Flow JSON, which is the artifact used for executing the Flow on the UiPath platform.
An existing Flow JSON can also be decompiled back into TypeScript for editing.

## Project layout

`@uipath/maestro-builder-sdk` is installed globally (`npm install -g`); `examples/` contains authored examples, and `references/` contains the details routed from this guide.
A Flow is authored as `.flow-sdk/<Name>.flow.ts` inside its project folder `<Solution>/<Name>/`, and it imports the package directly.

**Authoring files live in `.flow-sdk/`; the compiled artifact does not.**
`.flow-sdk/` is the SDK's own work directory: the source, `bindings.json`, `connectors/` and `connectors-local/` all go there by default, relative to the directory you run `uip` from. Each Flow project keeps its own, so a solution can hold several flows; Studio Web never reads it, and `uip solution pack`/`upload` and `flow debug` leave it out.
**Run the SDK verbs (`flow check`, `compile`, `decompile`, `merge`, `registry pull`/`prepare`, `node .flow-sdk/*.pipeline.mjs`) from the project folder `<Solution>/<Name>/`**, as `( cd <Solution>/<Name> && … )` when your shell does not keep its directory between commands; every `.flow-sdk/` path in this guide and its references is relative to that folder. Everything else runs from the workspace root.
Scaffold the project first, seed the source from it, then emit back into it — `compile -o` is the authority over where the emitted file is written.
`<Solution>` and `<Name>` are the request's own names, used verbatim: a request that gives one name for both ("inside a solution of the same name") uses it for both, and a request that names only the Flow uses `<Name>` for both.
**Look for an existing solution before `uip solution init`:** run `find . -maxdepth 2 -name '*.uipx'`. If one exists and a user can answer, ask which to use (one option per solution, then "Create a new solution", then "Something else") and scaffold nothing until they do; never create a second solution silently. Headless, use the solution the request names, else the only one present, else a new one named as above, and record the choice in the final response.

```bash
uip solution init <Solution>
( cd <Solution> && uip maestro flow init <Name> --sdk-source )
# edit <Solution>/<Name>/.flow-sdk/<Name>.flow.ts, then run the Lifecycle loop below
```

Do not hand-write the skeleton.
`--sdk-source` decompiles the trigger-only artifact `flow init` writes into the project's `.flow-sdk/<Name>.flow.ts`, creating the folder; the source carries the flow id and name the product already assigned — a hand-written `flow('<name>')` invents an id instead.
So the stub is the seed rather than litter: the first `compile -o` overwrites it in place.
`init` refuses an existing source file unless `--force`; when the source is already there, drop `--sdk-source`.
**Maestro Automate is `--automate` on the same `flow init`:** when the request names **Maestro Automate** as the product, run `( cd <Solution> && uip maestro flow init <Name> --automate --sdk-source )`; the bare verb ("automate invoice intake") asks for a plain Flow.
Nothing after `init` changes; the flag writes `runtimeOptions.profile` into `operate.json` plus a `.maestro_automate` marker (how Orchestrator and Studio Web tell the two apart), and `compile -o` rewrites only the `.flow`, so both survive.

An existing project needs no `init`: skip the first two commands and seed from the `.flow` that is already there with `( cd <Solution>/<Name> && uip maestro flow decompile <Name>.flow -o .flow-sdk/<Name>.flow.ts --no-pipeline )` (`--no-pipeline` skips the brownfield helper, [`references/brownfield.md`](references/brownfield.md)); skip the decompile when the source already exists.
The three names stay aligned: `.flow-sdk/<Name>.flow.ts`, the `<Name>` project directory, and `<Name>.flow` inside it.
Exactly one emitted `<Name>.flow` may exist, at `<Solution>/<Name>/<Name>.flow`, and never a second copy at the workspace root — validators and evidence collectors cannot choose safely between duplicates.
Emitting to the root is correct only for the packaged-SDK local gates, which never scaffold a project; pick the loop first ([Lifecycle](#lifecycle)) and do not mix the two.

**Install the SDK first, once per machine:** `npm install -g @uipath/maestro-builder-sdk`; skip it when already installed, and see [`references/CLI-LOOP.md`](references/CLI-LOOP.md#installing-the-package) for the checks and failure handling.

Integrations with non-UiPath systems are handled through connectors. **Choose the node before writing it.** For an external service or data (weather, Slack, a REST API), run `uip maestro registry search '<brand or service name>'` over the local connector library, unless the request names the transport itself ("over HTTP, not a connector" means `http()`): a hit is a connector, `"total": 0` is a miss and means `http()`, and a usage error means the library is not cached, so run `uip maestro registry pull` first. For document extraction or another tenant capability (agent, process), which that library does not hold, run the family's `uip maestro flow registry search` ([`references/ixp.md`](references/ixp.md), [`references/agent.md`](references/agent.md)). A `script()` returning fixed values is never a stand-in for that step, and `mock()` only marks a capability the search proved absent.
Connectors require [`.flow-sdk/bindings.json`](references/bindings.md).
`uip maestro registry pull` writes a descriptor per referenced connector to `.flow-sdk/connectors/<key>.ts`, and caches the library itself outside the project.
Prepared connector modules live at `.flow-sdk/connectors-local/<key>.ts`; their descriptor data is kept separately below `.flow-sdk/connectors-local/descriptors/<key>/`.
Because the source sits in `.flow-sdk/` too, it imports them as `./connectors/<key>.ts` and `./connectors-local/<key>.ts`.

### The connector loop: author → check → prepare → check → compile

Authoring never waits on `prepare`: once the search above has chosen the node, no further discovery command precedes the source.
Write the connector step from the task's own words — the fields you intend, `lookup()` tokens for ids, `{ object: '<name-as-the-task-said-it>' }` for a generic operation — then run `uip maestro flow check .flow-sdk/<Name>.flow.ts --source`.
Check names every prepare you owe, with the exact command:
`OBJECT_UNPREPARED` for an unmaterialized object, `CUSTOM_FIELDS_UNPREPARED` for an input outside the tenant-agnostic snapshot, `LOOKUP_UNRESOLVED` for a lookup token with no recorded value, `CONNECTOR_INPUT` for a field the operation does not declare. Run that one `uip maestro registry prepare <connector-key> <action>` — `--object`, `--resolve` and `-f` compose in a single invocation, it finds the connection itself, writes `.flow-sdk/bindings.json`, and repoints your import at the generated `./connectors-local/<key>.ts` descriptor — then re-run `check` and compile.
Where two flows import the same connector it names them instead of guessing, and asks for `--source`.

Schema-dynamic operations (`loadByDefault`, dependent dropdowns, `customFieldsRequestDetails`) need the prepare `check` names with every required `-f`, and a post-compile cache check: [`references/connector-params.md`](references/connector-params.md#schema-dynamic-operations-the-parent-field-loop).

### Hello world Flow

```ts
import { flow, script, input, out, types } from '@uipath/maestro-builder-sdk';
export default flow('hello').name('Hello')
  .input({ name: types.string }).output({ greeting: types.string })
  .step('greet', script({ code: 'return `Hello ${$vars.start.output.name}`;' }))
  .return({ greeting: out('greet') }).build();
```

A script is a first-class Flow node; it runs inline JavaScript and returns a value.
The `start` step is the default name for a "manual trigger", which carries the flow's inputs.
A Flow can have outputs, which are returned to the caller when the flow completes successfully.

## Lifecycle

Pick one loop before any build command; never mix them in one workspace or use one as a probe for the other (their layouts and evidence contracts differ):

- **Product-CLI loop (emit-only)** when the task asks for product validate/debug evidence, or the workspace is emit-only: a `package.json` with `{ "flowSdk": { "emitOnly": true } }` (the product-runtime eval sets it), or `FLOW_SDK_EMIT_ONLY=1`. Scaffold first ([Project layout](#project-layout)), then run the block below.
- **Packaged-SDK local gates** otherwise: source `check`, `compile` to the root, `validate` — [`references/CLI-LOOP.md`](references/CLI-LOOP.md#local-authoring-hard-gates).

The `uip maestro flow` commands delegate their semantics to the installed `@uipath/maestro-builder-sdk`. Emit-only belongs to the project, not the directory you run from: the nearest `package.json` up the tree that declares `flowSdk.emitOnly` decides it, a nested one that does not mention `flowSdk` inherits, and `emitOnly: false` opts out. In that mode `compile` only serializes source, both `flow check` modes refuse, and product `validate` owns structural verification. The base pass is emit, any required artifact bindings, then validate:

```bash
( cd <Solution>/<Name> && uip maestro flow compile .flow-sdk/<Name>.flow.ts -o <Name>.flow )
uip maestro flow validate <Solution>/<Name>/<Name>.flow --output json
# Before anything opens the emitted file (upload, debug, a designer):
uip maestro flow format <Solution>/<Name>/<Name>.flow --output json
# Only for a stated runtime-behavior claim:
( cd <Solution> && uip solution resources refresh --solution-folder . --output json )
( cd <Solution> && uip maestro flow debug <Name> --log-level error \
  --output-filter "{status:finalStatus,instance:instanceId,url:studioWebUrl,failed:elementExecutions[?status!='Completed'].{id:elementId,status:status},globals:variables.globals,incidents:incidents}" \
  --output json )
```

Re-run it from `compile` after the last source or binding edit. Valid is top-level `Result` plus `Data.Status: "Valid"`; treat `Data.Warnings` as failures except the reviewed shared-connection advisory. `Completed` with the expected globals and an empty `failed` is runtime evidence; a bare exit code is not. Debug inputs, attachments, other projections and incidents: [`references/CLI-LOOP.md`](references/CLI-LOOP.md#refresh-debug-and-preserve-evidence).

## Editing an existing flow

In brownfield work, preserve the supplied source, step names, and unaffected wiring. Insert a step by moving the old edge through it, not by creating a second path. If only emitted `.flow` JSON exists, decompile it, compile the pristine baseline, edit narrowly, and merge the delta back into the original.
These are before/after judgments; no final-artifact checker can prove them.

For a narrow edit, `decompile` writes `.flow-sdk/<Name>.pipeline.mjs`, which runs the loop in two invocations and gets the baseline ordering right. It keeps its baseline, edited and merged `.flow` files in `.flow-sdk/` too:

```bash
uip maestro flow decompile <Name>.flow -o .flow-sdk/<Name>.flow.ts
node .flow-sdk/<Name>.pipeline.mjs      # captures the pristine baseline
# edit .flow-sdk/<Name>.flow.ts narrowly
node .flow-sdk/<Name>.pipeline.mjs      # compiles the edit and merges it back
uip maestro flow validate .flow-sdk/<Name>.merged.flow --output json
```

Validate the merged artifact, never the intermediate edited compile.
If the source must stay inside the Flow project (for example, to preserve relative sidecars), keep baseline, edited, and candidate `.flow` files in an external `.flow-work/` directory. Validate the candidate, replace the canonical artifact, and leave exactly one `.flow` under the project. The reference below contains the copyable safe-project sequence.

**True-brownfield procedure:**
**[`references/brownfield.md`](references/brownfield.md)**.

## Builder frame

The quick start above shows the shape — `flow(id)`, declarations, nodes, `.return(...)`, `.build()`. Three things it does not show:

- **`.var(name, types.*, default?)`** declares a flow VARIABLE: a value more than one step writes or reads. `.input` and `.output` are the flow's contract with its caller; a var is the state in between. A step writes one with `{ updates: { name: <expr> } }`. Inputs, outputs and vars use one of the six types the Flow CLI and Workbench offer: `types.string`, `types.number`, `types.boolean`, `types.object`, `types.array`, `types.file`. The other `types` members (`integer`, `float`, `double`, `date`, `datetime`, `jsonSchema`) come from the Case and BPMN builders; the Flow builder and `validate` accept them without an error, but Workbench does not offer them, so write a date as `types.string` and an integer as `types.number`.
- **`.return(...)` ends a PATH. `.terminate(...)` ends the RUN.** They look interchangeable on a straight chain and are not: inside a `.parallel` arm a terminate aborts the sibling arms mid-flight, where a return leaves them going.
- **Expressions are how a step names something that is not a literal.** There is one per kind of thing you can refer to:

  | | refers to |
  | --- | --- |
  | `input(name)` | a flow input |
  | `v(name)` | a flow variable |
  | `out(step, path?)` | a step's result, whole or one field |
  | `err(step, field?)` | a FAILED step's error envelope — only inside its handler |
  | `ran(step)` | whether a step ran at all, as a boolean |
  | `lit(value)` | a constant, where a raw value would be ambiguous |
  | ``js`…` `` / ``tmpl`…` `` | an expression, or a string, you write yourself |

  `ran(step)` earns an early mention: when arms converge, one shared continuation usually reads better than the same work duplicated per arm, and `ran` is how that continuation asks whether the value it wants was produced.

## API index

**Every signature, option shape and field is indexed in the installed `@uipath/maestro-builder-sdk` package**, not in this guide; a row's path is relative to the package root:

| you have | look in | a row gives you |
| --- | --- | --- |
| a field or method — `outcomePorts`, `stepToList` (the usual case) | `dist/api-members.md` | the shape that declares it, and the lines that do |
| an exported symbol — `HitlInputs`, `hitl`, `FlowBuilder` | `dist/api-index.md` | its kind, area, and the lines that declare it |

**Match one name; do not read either file end to end.** Then read the span (e.g. `dist/core/actions.d.ts:583-597`): the whole declaration with its doc comment, so one read answers the question. Read the `.d.ts`, never `dist/*.js` (no types, no comments). A name in neither index is probably a RUNTIME output key, which the node references carry. Why the index ships in the package, and more lookup rules: [`references/author.md`](references/author.md#api-index-lookups).

## Supported node types

The table is the authoritative router. Before writing a node, read its `Reference`: the signature, a worked example and the node's hazards live there, not here. `Example` names the one complete flow to copy from; paths under `examples/` resolve inside this skill folder.

| Node or surface | Emitted node type | Builder | Reference | Example |
|---|---|---|---|---|
| Manual trigger | `core.trigger.manual` | omit `.trigger(...)` | [manual-trigger.md](references/manual-trigger.md) | `examples/GreenhouseWatering.flow.ts` |
| Entry points (multiple triggers) | one trigger node per extra root | `.entryPoint(id, trigger, { inputs?, version? }, prefixFn?)`; one var across roots: input `{ type, shared: '<var>' }` | [manual-trigger.md](references/manual-trigger.md#multiple-entry-points) | — |
| Scheduled trigger | `core.trigger.scheduled` | `scheduled(...)` | [scheduled-trigger.md](references/scheduled-trigger.md) | `examples/HerbariumDispatch.flow.ts` |
| Connector event trigger | `uipath.connector.trigger.<key>.<event>` | `onEvent(...)` | [event-trigger.md](references/event-trigger.md) | `examples/DoorbellLog.flow.ts` |
| Connector event wait | `uipath.connector.event.<key>.<event>` | `waitForEvent(...)` | [event-trigger.md](references/event-trigger.md) | `examples/PlanetariumConfirmation.flow.ts` |
| Form trigger | `core.trigger.form` | `formTrigger(...)` | [form-trigger.md](references/form-trigger.md) | `examples/BakeOffEntryForm.flow.ts` |
| Conversation trigger | `core.trigger.conversation` | `conversationTrigger(...)` | [conversational.md](references/conversational.md) | `examples/LibraryDeskChat.flow.ts` |
| Voice trigger | `core.trigger.voice` | `voiceTrigger(...)` | [voice.md](references/voice.md) | `examples/HarbourRadioLine.flow.ts` |
| Standalone HTTP | `core.action.http` | `http({ managed: false, ... })` | [http.md](references/http.md) | `examples/LighthouseSignal.flow.ts` |
| Managed HTTP | `core.action.http.v2` | `http({ managed: true, ... })` | [http.md](references/http.md) | `examples/ObservatorySeeing.flow.ts` |
| Script | `core.action.script` | `script(...)` | [script.md](references/script.md) | `examples/GreenhouseWatering.flow.ts` |
| Transform | `core.action.transform` | `transform(...)` | [transform.md](references/transform.md) | `examples/TrailLogSummary.flow.ts` |
| Filter | `core.action.transform.filter` | `transform({ variant: 'filter', ... })` | [transform.md](references/transform.md) | `examples/TrailLogSummary.flow.ts` |
| Map | `core.action.transform.map` | `transform({ variant: 'map', ... })` | [transform.md](references/transform.md) | `examples/TrailLogSummary.flow.ts` |
| Group by | `core.action.transform.group-by` | `transform({ variant: 'group-by', ... })` | [transform.md](references/transform.md) | `examples/TrailLogSummary.flow.ts` |
| Integration Service action | `uipath.connector.<key>.<action>` (Data Fabric / Data Service — the ops the native family lacks: file record fields, events: `uipath.connector.uipath-uipath-dataservice.*`) | `connector(...)` | [connector-params.md](references/connector-params.md) | `examples/ClubDirectory.flow.ts` |
| Data Fabric read | `core.datafabric.read` (`resultMode: 'multiple'` selects its 1.4 definition; `limit` caps at 1000) | `dataFabricRead(...)` | [data-fabric.md](references/data-fabric.md) | `examples/BeeHiveLedger.flow.ts` |
| Data Fabric create | `core.datafabric.create` | `dataFabricCreate(...)` | [data-fabric.md](references/data-fabric.md) | `examples/BeeHiveLedger.flow.ts` |
| Data Fabric update | `core.datafabric.update` | `dataFabricUpdate(...)` | [data-fabric.md](references/data-fabric.md) | `examples/BeeHiveLedger.flow.ts` |
| Data Fabric delete | `core.datafabric.delete` (declares NO outputs) | `dataFabricDelete(...)` | [data-fabric.md](references/data-fabric.md) | `examples/BeeHiveLedger.flow.ts` |
| Subflow | `core.subflow` | `subflow(...)` | [subflow.md](references/subflow.md) | `examples/RecipeScaler.flow.ts` |
| Human task | `uipath.human-in-the-loop` | `hitl(...)` | [hitl.md](references/hitl.md) | `examples/GallerySubmission.flow.ts` |
| Human quick form | `uipath.human-in-the-loop.quick-form` (one exit per outcome: `.stepSwitch` routes them, a plain `.step()` continues every outcome) | `hitl({ variant: 'quick-form', ... })` | [hitl.md](references/hitl.md) | `examples/FieldTripQuickForm.flow.ts` |
| Human action app | `uipath.human-in-the-loop.coded-action-app` | `hitl({ variant: 'action-app', ... })` | [hitl.md](references/hitl.md) | `examples/KilnReview.flow.ts` |
| RPA workflow | `uipath.core.rpa-workflow.<key>` | `rpaWorkflow(...)` | [rpa-workflow.md](references/rpa-workflow.md) | `examples/WorkshopInventory.flow.ts` |
| Queue item | `core.action.queue.create*` | `queueItem(...)` | [queue.md](references/queue.md) | `examples/HerbariumDispatch.flow.ts` |
| Summarize | `uipath.pattern.deep-rag` | `summarize(...)` | [summarize.md](references/summarize.md) | `examples/OralHistoryDigest.flow.ts` |
| Batch transform | `uipath.pattern.batch-transform` | `batchTransform(...)` | [batch-transform.md](references/batch-transform.md) | `examples/FossilCatalogEnrich.flow.ts` |
| Branch | `core.logic.decision` | `.branch(...)` | [branch.md](references/branch.md) | `examples/GreenhouseWatering.flow.ts` |
| Switch | `core.logic.switch` | `.switch(...)` | [switch.md](references/switch.md) | `examples/BeltProgression.flow.ts` |
| Parallel / Merge | `core.logic.merge` | `.parallel(...)` | [parallel-merge.md](references/parallel-merge.md) | `examples/ConcertSoundcheck.flow.ts` |
| Loop | `core.logic.loop` | `.loop(...)` | [loops.md](references/loops.md) | `examples/ClubDirectory.flow.ts` |
| Do while | `core.logic.dowhile` | `.doWhile(...)` | [loops.md](references/loops.md#do-while) | `examples/MeteorShowerPages.flow.ts` |
| Return / End | `core.control.end` | `.return(...)` | [return.md](references/return.md) | `examples/GreenhouseWatering.flow.ts` |
| Terminate | `core.logic.terminate` | `.terminate(...)` | [terminate.md](references/terminate.md) | `examples/AquariumSafetyStop.flow.ts` |
| Placeholder | `core.logic.mock` | `mock()` | [placeholder.md](references/placeholder.md) | `examples/FestivalMapScaffold.flow.ts` |
| Unknown node type | the registry's `nodeType` verbatim (never `uipath.connector.*`) | `rawNode(...)` | [placeholder.md](references/placeholder.md#unknown-node-types) | — |
| Error handler | `error` handle on an action node | `.onError(...)` | [error-handling.md](references/error-handling.md) | `examples/ObservatorySeeing.flow.ts` |
| Delay | `core.logic.delay` | `delay(...)` | [delay.md](references/delay.md) | `examples/LighthouseSignal.flow.ts` |
| API workflow | `uipath.core.api-workflow.<key>` | `apiWorkflow(...)` | [api-workflow.md](references/api-workflow.md) | `examples/BirdCountLookup.flow.ts` |
| Agentic process | `uipath.core.agentic-process.<key>` | `agenticProcess(...)` | [agentic-process.md](references/agentic-process.md) | `examples/NeighborhoodWalkPlanner.flow.ts` |
| Agent resource | `uipath.core.agent.<key>` | `agent(...)` | [agent.md](references/agent.md) | `examples/PlantNameAdvisor.flow.ts` |
| Inline agent | `uipath.agent.autonomous` | `inlineAgent(...)` | [inline-agent.md](references/inline-agent.md) | `examples/PostcardCaption.flow.ts` |
| IxP extraction | `uipath.ixp.<project>.<version>-<folder>` | `ixpExtract(...)` | [ixp.md](references/ixp.md) | `examples/ArchiveCardExtract.flow.ts` |
| Document classify | `uipath.document.classify` | `documentClassify(...)` | [document-pipeline.md](references/document-pipeline.md) | `examples/SeedPacketReader.flow.ts` |
| Dynamic extract | `uipath.ixp.extract-document-builder` | `dynamicExtract(...)` | [document-pipeline.md](references/document-pipeline.md) | `examples/SeedPacketReader.flow.ts` |
| Published function | `uipath.core.function.<key>` | `publishedFunction(...)` | [published-function.md](references/published-function.md) | `examples/TideTableConverter.flow.ts` |
| Conversation message wait | `uipath.conversational.wait-for-message` | `waitForMessage(...)` | [conversational.md](references/conversational.md) | `examples/LibraryDeskChat.flow.ts` |
| Conversational agent | `uipath.agent.conversational` | `conversationalAgent(...)` | [conversational.md](references/conversational.md) | `examples/LibraryDeskChat.flow.ts` |
| Conversation send message | `uipath.conversational.send-message` | `sendMessage(...)` | [conversational.md](references/conversational.md) | `examples/LibraryDeskChat.flow.ts` |
| Voice outgoing call | `uipath.conversational.voice.create-outgoing-call` | `createOutgoingCall(...)` | [voice.md](references/voice.md) | `examples/PotteryStudioCallback.flow.ts` |
| Voice agent | `uipath.agent.voice` | `voiceAgent(...)` | [voice.md](references/voice.md) | `examples/PotteryStudioCallback.flow.ts` |
| Voice end call | `uipath.conversational.voice.end-call` | `endCall(...)` | [voice.md](references/voice.md) | `examples/PotteryStudioCallback.flow.ts` |

## Authoring a flow

Choose each node from a registry search, never a brand name; ask when the
request leaves a finite decision open; bind every declared output on every
path (`check` misses a missing one, and the run returns `undefined`); handle an
error only when the request says what should happen. The journeys, the
scope gate for a request that names no steps, when to plan first, and the
completion report are in
**[`references/author.md`](references/author.md)**.

## Operating a deployed flow

Upload, deploy, debug, trigger, inspect a job, and drive an instance's
lifecycle. All of it needs `uip login`, and `uip solution resources refresh`
comes before every upload, publish or debug. `flow debug` is a REAL run, not a
validation step. Read
**[`references/operate.md`](references/operate.md)**.

## Diagnosing a failed run

Triage in order — the debug response you already have, then incidents, runtime
variables, the deployed artifact, and traces last. Never re-run `flow debug` to
look again. The builder removes several classic `.flow` defects and leaves
others, including an expression that is really a literal. Read
**[`references/diagnose.md`](references/diagnose.md)**.

## Evaluating a flow

An inline agent does not create evaluators, eval sets, data points or
simulations — the Flow eval CLI manages them as project files. Simulate every
side-effecting component before running a set, and never `solution upload` as
part of an eval workflow without asking. Read
**[`references/evaluate.md`](references/evaluate.md)**.

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
