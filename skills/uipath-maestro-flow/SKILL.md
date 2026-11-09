---
name: uipath-maestro-flow
description: "UiPath Maestro Flow, UiPath Flow and Maestro Automate (`.flow` / `.flow.ts` files): build, edit, run, debug, fix, or evaluate a flow. Author with the TypeScript builder SDK (`@uipath/maestro-builder-sdk`): nodes, triggers, schedules, connectors, document extraction (published IXP models, or the Extract document node with an inline taxonomy), inline agents, HITL, chat/voice flows, bindings, brownfield edits, and the check/compile/validate loop. Operate: upload, publish, deploy, debug a real run, trigger a process, job status/traces, pause/resume/cancel/retry an instance. Diagnose: faulted runs, incidents, runtime variables, why validate passed but the run failed. Evaluate: eval sets, evaluators, simulations, eval runs. Case plans (`caseplan.case` / `caseplan.json`)→uipath-maestro-case; BPMN (`.bpmn`, `.bpmn.ts`)→uipath-maestro-bpmn. For raw IXP labelling or prompt tuning outside a Flow→uipath-ixp; standalone agents→uipath-agents; C#/XAML→uipath-rpa."
allowed-tools: Bash, Read, Write, Edit, Glob, Grep, AskUserQuestion
---

<!-- CANONICAL — edit here, not in UiPath/flow-builder-sdk. Why: docs/SKILLS_PROMOTION_PLAN.md in that repo. -->

# UiPath Flow — TypeScript Builder SDK

UiPath Flow uses `@uipath/maestro-builder-sdk` to type-safely build inputs, outputs, steps, control flow, executable Flow JSON, and TypeScript decompilations.

## Critical Rules

1. **Before writing or editing any flow source, read [`references/author.md`](references/author.md) in full.** It contains separately numbered critical rules, the scope gate, and the completion report the final response must follow.
2. Before writing a node, read its `Reference` in [Supported node types](#supported-node-types), including signature, example, and hazards.
3. Choose every node from a registry search, never a brand name.
4. Ask whenever a finite decision remains open, including an input, range, or combination not covered by a stated rule; never fold it into a stated value. If nobody can answer (headless, CI), use the most defensible stated value and list it under Open questions as **[REQUIRED]**.
5. Bind every declared output on every path. `check` does not detect missing bindings; the run returns `undefined`.
6. Handle an error only when the request specifies the outcome.
7. Never re-run `flow debug` to inspect a failed run.
8. Simulate every side-effecting component before an eval set; never `solution upload` during evaluation without asking.
9. After the last edit, run the final pass selected by [Lifecycle](#lifecycle) for the workspace.

## Project layout

<!--skill-flavor:sdk-project-layout:start-->
Install `@uipath/maestro-builder-sdk` globally (`npm install -g`) unless already installed. Author `<Solution>/<Name>/.flow-sdk/<Name>.flow.ts`, importing the package directly; `examples/` contains authored examples and `references/` routed details. Relative to the directory running `uip`, each SDK work directory has source, `bindings.json`, `connectors/`, and `connectors-local/`; each project has its own. Authoring files belong in `.flow-sdk/`; compiled artifacts do not. Studio Web never reads it, and `uip solution pack`/`upload` and `flow debug` omit it. Run SDK verbs (`flow check`, `compile`, `decompile`, `merge`, `registry pull`/`prepare`, `node .flow-sdk/*.pipeline.mjs`) from `<Solution>/<Name>/`, using `( cd "<Solution>/<Name>" && … )` when needed; `.flow-sdk/` paths are relative there. Run other commands from the workspace root.

Scaffold first, seed the source, then emit into it; `compile -o` controls the emitted file. `<Solution>` and `<Name>` come from the request: one name given for both ("inside a solution of the same name"), or only the Flow's, serves both; `<Solution>` preserves spaces and `<Name>` keeps only letters, numbers, `_`, and `-` (`Headcount report form` → `HeadcountReportForm`).

**Before `uip solution init`, run:** `find . -maxdepth 2 -name '*.uipx'`. If a solution exists and a user can answer, ask which to use (one option per solution, then "Create a new solution", then "Something else") and scaffold nothing until answered; never silently create a second. Headless: use the named solution, otherwise the only existing one, otherwise a new one named above, and record the choice in the final response.

```bash
uip solution init "<Solution>"
( cd "<Solution>" && uip maestro flow init <Name> --sdk-source )
# edit <Solution>/<Name>/.flow-sdk/<Name>.flow.ts, then run the Lifecycle loop below
```

Do not hand-write the skeleton. `--sdk-source` decompiles the trigger-only artifact into `.flow-sdk/<Name>.flow.ts`, creates the folder, and preserves the product-assigned flow id/name; hand-written `flow('<name>')` invents an id. The stub is the seed; the first `compile -o` overwrites it. If `init` says “already exists and is not empty. Use --force to overwrite”, edit it and never pass `--force`. Omit `--sdk-source` for a Flow containing an Extract document node; it is CLI-authored ([`references/extract-document-node.md`](references/extract-document-node.md)).

For **Maestro Automate**, run `( cd "<Solution>" && uip maestro flow init <Name> --automate --sdk-source )`; a bare request such as “automate invoice intake” means a plain Flow. Nothing after `init` changes: the flag writes `runtimeOptions.profile` to `operate.json` and a `.maestro_automate` marker; `compile -o` rewrites only `.flow`, so both survive.

If `<Solution>/<Name>/` predates this turn, skip `init` and edit its `<Name>.flow` through [Editing an existing flow](#editing-an-existing-flow), never by compiling an earlier-turn source over it. Keep `.flow-sdk/<Name>.flow.ts`, the `<Name>` directory, and `<Name>.flow` aligned. Exactly one emitted `<Name>.flow` may exist at `<Solution>/<Name>/<Name>.flow`; never put a second copy at the workspace root. Root emission is only for packaged-SDK local gates, which do not scaffold; choose [Lifecycle](#lifecycle) first and do not mix loops.

See [`references/CLI-LOOP.md`](references/CLI-LOOP.md#installing-the-package) for installation checks and failure handling.
<!--skill-flavor:sdk-project-layout:end-->

<!--skill-flavor:sdk-connector-discovery:start-->
For an external service or data (weather, Slack, a REST API), run `uip maestro registry search '<brand or service name>'`: a hit is a connector, `"total": 0` is a miss and means `http()`. A `script()` returning fixed values is never a stand-in for that step.
For non-UiPath systems, **choose the node before writing it**. Unless the request names the transport (“over HTTP, not a connector” means `http()`), search the local connector library with `uip maestro registry search '<brand or service name>'`: a hit selects a connector, `"total": 0` means `http()` (not for an external agent; see the table), and a usage error means the library is uncached, so run `uip maestro registry pull`. For another tenant capability (agent, process), use the family’s `uip maestro flow registry search` ([`references/agent.md`](references/agent.md)). Default document extraction to a published IxP model ([`references/ixp.md`](references/ixp.md)); use the Extract document node only when named or already present ([`references/extract-document-node.md`](references/extract-document-node.md)). Never replace such a step with fixed-value `script()`; `mock()` only marks a capability the search proved absent.

Connectors require [`.flow-sdk/bindings.json`](references/bindings.md). `uip maestro registry pull` writes each referenced descriptor to `.flow-sdk/connectors/<key>.ts` and caches the library outside the project. Prepared modules are `.flow-sdk/connectors-local/<key>.ts`, with descriptor data at `.flow-sdk/connectors-local/descriptors/<key>/`; source imports `./connectors/<key>.ts` or `./connectors-local/<key>.ts`.

### The connector loop: author → check → prepare → check → compile

After search selects a node, author it without another discovery command. Use task wording for fields, `lookup()` for ids, and `{ object: '<name-as-the-task-said-it>' }` for generic operations. Then run `uip maestro flow check .flow-sdk/<Name>.flow.ts --source`.

Check names every required prepare exactly: `OBJECT_UNPREPARED` (unmaterialized object), `CUSTOM_FIELDS_UNPREPARED` (input outside the tenant-agnostic snapshot), `LOOKUP_UNRESOLVED` (lookup token without a recorded value), and `CONNECTOR_INPUT` (undeclared operation field). Run one `uip maestro registry prepare <connector-key> --action <action>`; `--object`, `--resolve`, and `-f` compose in one invocation. It finds the connection, writes `.flow-sdk/bindings.json`, repoints the import to `./connectors-local/<key>.ts`, then re-run `check` and compile. Where two flows import the same connector it names them instead of guessing, and asks for `--source`.

What `prepare` binds or refuses: [bindings.md](references/bindings.md#where-both-values-come-from). `CONNECTOR_NOT_IN_LIBRARY`, `CONNECTOR_OBJECT_REQUIRED`, and `CONNECTOR_OBJECT_NOT_GENERIC` require source fixes, not prepares: [connector-params.md](references/connector-params.md#author-first--check-names-every-prepare-you-owe). Schema-dynamic operations (`loadByDefault`, dependent dropdowns, `customFieldsRequestDetails`) require every `-f` named by prepare `check` and a post-compile cache check: [`references/connector-params.md`](references/connector-params.md#schema-dynamic-operations-the-parent-field-loop).
<!--skill-flavor:sdk-connector-discovery:end-->

### Hello world Flow

```ts
import { flow, script, input, out, types } from '@uipath/maestro-builder-sdk';
export default flow('hello').name('Hello')
  .input({ name: types.string }).output({ greeting: types.string })
  .step('greet', script({ code: 'return `Hello ${$vars.start.output.name}`;' }))
  .return({ greeting: out('greet') }).build();
```

A script is a first-class Flow node that runs inline JavaScript and returns a value. `start` is the default manual-trigger step and carries the flow's inputs; outputs return to the caller on success.

## Lifecycle

<!--skill-flavor:sdk-lifecycle:start-->
Choose one loop before any build command; never mix them or use one as a probe for the other:

- **Product-CLI loop (emit-only):** use when product validate/debug evidence is requested or the workspace is emit-only: a `package.json` containing `{ "flowSdk": { "emitOnly": true } }` (product-runtime eval sets it), or `FLOW_SDK_EMIT_ONLY=1`. Scaffold first ([Project layout](#project-layout)), then use the block below.
- **Packaged-SDK local gates:** otherwise use source `check`, `compile` to root, and `validate` — [`references/CLI-LOOP.md`](references/CLI-LOOP.md#local-authoring-hard-gates).

`uip maestro flow` delegates to installed `@uipath/maestro-builder-sdk`. Emit-only belongs to the project, not the working directory: the nearest ancestor `package.json` declaring `flowSdk.emitOnly` decides; a nested file omitting `flowSdk` inherits, and `emitOnly: false` opts out. There `compile` only serializes, both `flow check` modes refuse, and product `validate` verifies structure. A new flow’s pass is emit, required artifact bindings, then validate:

```bash
( cd "<Solution>/<Name>" && uip maestro flow compile .flow-sdk/<Name>.flow.ts -o <Name>.flow )
uip maestro flow validate "<Solution>/<Name>/<Name>.flow" --output json
# Greenfield only (never a merged or .layout() file), before upload/debug/a designer:
uip maestro flow format "<Solution>/<Name>/<Name>.flow" --output json
# Stated runtime claim; ask per references/operate.md
( cd "<Solution>" && uip solution resources refresh --solution-folder . --output json )
( cd "<Solution>" && uip maestro flow debug <Name> --log-level error \
  --output-filter "{status:finalStatus,instance:instanceId,url:studioWebUrl,failed:elementExecutions[?status!='Completed'].{id:elementId,status:status},<Out>:variables.globals.<Out>,incidents:incidents}" \
  --output json )
```

`<Out>` means each declared `out` variable, never all `variables.globals`. Re-run it from `compile` after the last source or binding edit. Valid requires top-level `Result` plus `Data.Status: "Valid"`; treat `Data.Warnings` as failures except the reviewed shared-connection advisory and `err()` diagnostics. `Completed` with expected globals and empty `failed` is runtime evidence; an exit code alone is not. Debug inputs, attachments, projections, and incidents: [`references/CLI-LOOP.md`](references/CLI-LOOP.md#refresh-debug-and-preserve-evidence).
<!--skill-flavor:sdk-lifecycle:end-->

## Editing an existing flow

<!--skill-flavor:sdk-editing:start-->
Preserve supplied source, step names, and unaffected wiring. Insert a step by routing the old edge through it, not by creating a second path. Unless source was supplied, freshly decompile the `.flow`, compile the baseline, edit narrowly, and merge the delta into the original. Decompiling overwrites supplied source; use [its loop](references/brownfield.md#a-supplied-source).

For a narrow edit, `decompile` writes `.flow-sdk/<Name>.pipeline.mjs`, which runs twice and keeps baseline, edited, and merged `.flow` files in `.flow-sdk/`:

```bash
( cd "<Solution>/<Name>" && [ ! -d .flow-sdk ] || find .flow-sdk -maxdepth 1 \( -name '<Name>.baseline' -o -name '<Name>.edited' -o -name '<Name>.merged.flow' -o -name '????????-????-????-????-????????????' \) -exec rm -rf {} + )
uip maestro flow decompile <Name>.flow -o .flow-sdk/<Name>.flow.ts
node .flow-sdk/<Name>.pipeline.mjs      # captures the pristine baseline
# edit .flow-sdk/<Name>.flow.ts narrowly; no .layout() for added steps (builder-sdk#1320)
uip maestro flow check .flow-sdk/<Name>.flow.ts --source --baseline <Name>.flow   # the gate: fix each (edited) error
node .flow-sdk/<Name>.pipeline.mjs      # compiles the edit and merges it back
```

Back up the project to `mktemp -d`, `cp` the merge output over it whole, validate it there (not the edited compile), then delete the backup. Never write or `compile` onto canonical `.flow`. Keep relative sidecars inside the project: [the safe project loop](references/brownfield.md#the-safe-project-loop). **True-brownfield procedure:** **[`references/brownfield.md`](references/brownfield.md)**.
<!--skill-flavor:sdk-editing:end-->

## Builder frame

The basic shape is `flow(id)`, declarations, nodes, `.return(...)`, `.build()`:

- `.var(name, types.*, default?)` declares a flow variable—state written or read by multiple steps. A step writes it with `{ updates: { name: <expr> } }`. `.input` and `.output` are caller contracts. Supported types are `types.string`, `types.number`, `types.boolean`, `types.object`, `types.array`, and `types.file`; `float`, `double`, `date`, `datetime`, and `jsonSchema` are refused: [variable types](references/author.md#variable-types). No node reads an Orchestrator asset; retain a setting as a var default or input.
- `.return(...)` ends a PATH; `.terminate(...)` ends the RUN. In a `.parallel` arm, terminate aborts sibling arms; return lets them continue.
- Expressions: `input(name)` reads a flow input; `v(name)` a variable; `out(step, path?)` a result or field; `err(step, field?)` a FAILED step’s error envelope only inside its handler; `ran(step)` whether a step ran; `lit(value)` an unambiguous constant; ``js`…` `` / ``tmpl`…` `` an authored expression or string. When arms converge, prefer one shared continuation; use `ran` to test whether its needed value was produced.

## API index

<!--skill-flavor:sdk-api-index:start-->
**Every signature, option shape and field is indexed in the installed `@uipath/maestro-builder-sdk` package**, not this guide. Paths are package-root-relative:

| you have | look in | a row gives |
| --- | --- | --- |
| a field or method — `outcomePorts`, `stepToList` (usual case) | `dist/api-members.md` | declaring shape and declaration lines |
| an exported symbol — `HitlInputs`, `hitl`, `FlowBuilder` | `dist/api-index.md` | kind, area, and declaration lines |

Match one name; do not read either file end to end. Then read the span (for example `dist/core/actions.d.ts:583-597`) containing the complete declaration and doc comment. Read `.d.ts`, never `dist/*.js` (no types or comments). A name in neither index is probably a RUNTIME output key, documented by the node reference. More lookup rules: [`references/author.md`](references/author.md#api-index-lookups).
<!--skill-flavor:sdk-api-index:end-->

## Supported node types

This table is the authoritative router; read a node’s `Reference` before writing it ([Critical Rule 2](#critical-rules)). `Example` names the complete flow to copy; `examples/` paths resolve inside this skill.

| Node or surface | Emitted node type | Builder | Reference | Example |
|---|---|---|---|---|
| Manual trigger | `core.trigger.manual` | omit `.trigger(...)` | [manual-trigger.md](references/manual-trigger.md) | `examples/GreenhouseWatering.flow.ts` |
| Entry points (multiple triggers) | one trigger node per extra root | `.entryPoint(id, trigger, { inputs?, version? }, prefixFn?)`; one var across roots: input `{ type, shared: '<var>' }` | [manual-trigger.md](references/manual-trigger.md#multiple-entry-points) | — |
| Scheduled trigger | `core.trigger.scheduled` | `scheduled(...)` | [scheduled-trigger.md](references/scheduled-trigger.md) | `examples/HerbariumDispatch.flow.ts` |
| Connector event trigger; a start by an HTTP call | `uipath.connector.trigger.<key>.<event>` | `onEvent(...)` | [event-trigger.md](references/event-trigger.md), [HTTP call](references/event-trigger.md#started-by-an-http-call) | `examples/DoorbellLog.flow.ts` |
| Connector event wait | `uipath.connector.event.<key>.<event>` | `waitForEvent(...)` | [event-trigger.md](references/event-trigger.md) | `examples/PlanetariumConfirmation.flow.ts` |
| Form trigger | `core.trigger.form` | `formTrigger(...)` | [form-trigger.md](references/form-trigger.md) | `examples/BakeOffEntryForm.flow.ts` |
| Conversation trigger | `core.trigger.conversation` | `conversationTrigger(...)` | [conversational.md](references/conversational.md) | `examples/LibraryDeskChat.flow.ts` |
| Voice trigger | `core.trigger.voice` | `voiceTrigger(...)` | [voice.md](references/voice.md) | `examples/HarbourRadioLine.flow.ts` |
| Standalone HTTP | `core.action.http` | `http({ managed: false, ... })` | [http.md](references/http.md) | `examples/LighthouseSignal.flow.ts` |
| Managed HTTP | `core.action.http.v2` | `http({ managed: true, ... })` | [http.md](references/http.md) | `examples/ObservatorySeeing.flow.ts` |
| Script | `core.action.script` | `script(fn)`, SDK ≥ 6.57.0 (`$metadata` parameter ≥ 6.72.0); `script({ code })` | [script.md](references/script.md) | `examples/GreenhouseWatering.flow.ts` |
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
| Human quick form | `uipath.human-in-the-loop.quick-form` (one exit per outcome: `.stepSwitch` routes them, plain `.step()` continues every outcome) | `hitl({ variant: 'quick-form', ... })` | [hitl.md](references/hitl.md) | `examples/FieldTripQuickForm.flow.ts` |
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
| Unknown node type | registry’s `nodeType` verbatim (never `uipath.connector.*`) | `rawNode(...)` | [placeholder.md](references/placeholder.md#unknown-node-types) | — |
| Error handler | `error` handle on an action node | `.onError(...)` | [error-handling.md](references/error-handling.md) | `examples/ObservatorySeeing.flow.ts` |
| Delay | `core.logic.delay` | `delay(...)` | [delay.md](references/delay.md) | `examples/LighthouseSignal.flow.ts` |
| API workflow | `uipath.core.api-workflow.<key>` | `apiWorkflow(...)` | [api-workflow.md](references/api-workflow.md) | `examples/BirdCountLookup.flow.ts` |
| Agentic process | `uipath.core.agentic-process.<key>` | `agenticProcess(...)` | [agentic-process.md](references/agentic-process.md) | `examples/NeighborhoodWalkPlanner.flow.ts` |
| Agent resource | `uipath.core.agent.<key>` | `agent(...)` | [agent.md](references/agent.md) | `examples/PlantNameAdvisor.flow.ts` |
| External agent or automation | `uipath.connector.<key>.<operation>` | `connector(...)`, or CLI when library lacks it | [external-agent.md](references/external-agent.md) | — |
| Inline agent | `uipath.agent.autonomous` | `inlineAgent(...)` | [inline-agent.md](references/inline-agent.md) | `examples/PostcardCaption.flow.ts` |
| IxP extraction | `uipath.ixp.<project>.<version>-<folder>` | `ixpExtract(...)` | [ixp.md](references/ixp.md) | `examples/ArchiveCardExtract.flow.ts` |
| Document classify | `uipath.document.classify` | `documentClassify(...)` | [document-pipeline.md](references/document-pipeline.md) | `examples/SeedPacketReader.flow.ts` |
| Extract document | `uipath.ixp.extract-document-builder` | — (CLI only) | [extract-document-node.md](references/extract-document-node.md) | `examples/SeedPacketReader.flow.ts` |
| Published function | `uipath.core.function.<key>` | `publishedFunction(...)` | [published-function.md](references/published-function.md) | `examples/TideTableConverter.flow.ts` |
| Conversation message wait | `uipath.conversational.wait-for-message` | `waitForMessage(...)` | [conversational.md](references/conversational.md) | `examples/LibraryDeskChat.flow.ts` |
| Conversational agent | `uipath.agent.conversational` | `conversationalAgent(...)` | [conversational.md](references/conversational.md) | `examples/LibraryDeskChat.flow.ts` |
| Conversation send message | `uipath.conversational.send-message` | `sendMessage(...)` | [conversational.md](references/conversational.md) | `examples/LibraryDeskChat.flow.ts` |
| Voice outgoing call | `uipath.conversational.voice.create-outgoing-call` | `createOutgoingCall(...)` | [voice.md](references/voice.md) | `examples/PotteryStudioCallback.flow.ts` |
| Voice agent | `uipath.agent.voice` | `voiceAgent(...)` | [voice.md](references/voice.md) | `examples/PotteryStudioCallback.flow.ts` |
| Voice end call | `uipath.conversational.voice.end-call` | `endCall(...)` | [voice.md](references/voice.md) | `examples/PotteryStudioCallback.flow.ts` |

## Authoring a flow

[Critical Rules](#critical-rules) govern node choice, open decisions, outputs, and errors. Details are in **[`references/author.md`](references/author.md)**. A request naming canvas arrangement uses `.layout()` with `at()`/`dim()`: [`references/operate.md`](references/operate.md#lay-out-from-source-instead-layout-at-dim).

## Operating a deployed flow

<!--skill-flavor:sdk-operate:start-->
Upload, deploy, debug, trigger, inspect jobs, and drive instance lifecycle only after `uip login`; run `uip solution resources refresh` before every upload, publish, or debug. `flow debug` is a REAL run, not validation: ask first. Read **[`references/operate.md`](references/operate.md)**.
<!--skill-flavor:sdk-operate:end-->

## Diagnosing a failed run

Triage in order: existing debug response, incidents, runtime variables, deployed artifact, then traces. The builder removes some classic `.flow` defects but leaves others, including expressions that are actually literals. Read **[`references/diagnose.md`](references/diagnose.md)**.

## Evaluating a flow

An inline agent creates no evaluators, eval sets, data points, or simulations; the Flow eval CLI manages them as project files. Read [`references/evaluate.md`](references/evaluate.md).
Read **[`references/evaluate.md`](references/evaluate.md)**.

## Final evidence

Product-resource truth is live evidence: verify plausible ids, argument names, scenario-named optional inputs, and warnings against the tenant. Static diagnostics own mechanically checkable structure; fix their causes rather than copying rules into this router.

Match proof to the request’s acceptance bar. If one wiring question remains, validate-only is complete when product validation is green and its required structural self-check passes; do not add debug merely for confidence. For each named behavior, plan at most one bounded product debug. If one wiring question remains, run one distinguishing bounded experiment, apply its answer, and stop; do not create scratch-solution families or repeat equivalent variants.