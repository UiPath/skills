---
name: uipath-maestro-flow
description: "UiPath Maestro Flow, UiPath Flow and Maestro Automate (`.flow` / `.flow.ts` files): build, edit, run, debug, fix, or evaluate a flow. Author with the TypeScript builder SDK (`@uipath/maestro-builder-sdk`): nodes, triggers, schedules, connectors, document extraction (published IXP models, or the Extract document node with an inline taxonomy), inline agents, HITL, chat/voice flows, bindings, brownfield edits, and the check/compile/validate loop. Operate: upload, publish, deploy, debug a real run, trigger a process, job status/traces, pause/resume/cancel/retry an instance. Diagnose: faulted runs, incidents, runtime variables, why validate passed but the run failed. Evaluate: eval sets, evaluators, simulations, eval runs. Case plans (`caseplan.case` / `caseplan.json`)→uipath-maestro-case; BPMN (`.bpmn`, `.bpmn.ts`)→uipath-maestro-bpmn. For raw IXP labelling or prompt tuning outside a Flow→uipath-ixp; standalone agents→uipath-agents; C#/XAML→uipath-rpa."
allowed-tools: Read, Glob, Grep
---

> **Claude directory edition:** each cited `<name>.md` wraps the file `<name>` in one fenced block. To copy one, write only the block's contents to the destination; never copy the Markdown file.


<!-- CANONICAL — edit here, not in UiPath/flow-builder-sdk. Why: docs/SKILLS_PROMOTION_PLAN.md in that repo. -->

# UiPath Flow — TypeScript Builder SDK

UiPath Flow uses `@uipath/maestro-builder-sdk` to build type-safe graphs compiled to executable Flow JSON; existing Flow JSON can be decompiled for editing.

## Critical Rules

1. **Before writing or editing any flow source, read [`references/author.md`](references/author.md) in full.** It contains separately numbered critical rules, the scope gate, and the required completion report.
2. Before writing a node, read its `Reference` in [Supported node types](#supported-node-types), including signature, example, and hazards.
3. Choose every node from a registry search, never a brand name.
4. Ask when the request leaves a finite decision open, including an input value, range, or combination no stated rule covers; never fold it into a stated value. When the request says no one will answer (headless, CI), use the most defensible stated value and list it under Open questions as **[REQUIRED]**.
5. Handle an error only when the request specifies what should happen.
6. Never re-run `flow debug` to inspect a failed run.
7. Simulate every side-effecting component before an eval set; never `solution upload` in an eval workflow without asking.
8. Run the final pass with the workspace's selected [Lifecycle](#lifecycle) loop after the last edit.

## Project layout

Install `@uipath/maestro-builder-sdk` globally (`npm install -g`), unless present. Examples are in `examples/`; routed details are in `references/`.

A Flow source is `.flow-sdk/<Name>.flow.ts` under `<Solution>/<Name>/`; compiled `<Name>.flow` is not in `.flow-sdk/`. The SDK work directory contains source, `bindings.json`, `connectors/`, and `connectors-local/`, relative to the directory running `uip`; each project has its own. Studio Web does not read it, and `uip solution pack`/`upload` and `flow debug` omit it. Run SDK verbs (`flow check`, `compile`, `decompile`, `merge`, `registry pull`/`prepare`) from `<Solution>/<Name>/`, using `( cd "<Solution>/<Name>" && … )` when your shell does not keep its directory between commands; other commands run from the workspace root. Every `.flow-sdk/` path is project-relative.

Scaffold first, seed from the scaffold, and emit into it; `compile -o` determines the emitted file. `<Solution>` and `<Name>` come from the request: one name given for both ("inside a solution of the same name"), or only the Flow's, serves both. Preserve `<Solution>` exactly, including spaces; normalize `<Name>` to letters, numbers, `_`, and `-` (`Headcount report form` → `HeadcountReportForm`).

Before `uip solution init`, run `find . -maxdepth 2 -name '*.uipx'`. If solutions exist and a user can answer, ask which one (one option per solution, then "Create a new solution", then "Something else") and scaffold only after the answer; never silently create another. Headless: use the named solution, otherwise the only existing one, otherwise create one named above, and record the choice in the final response.

```bash
uip solution init "<Solution>"
( cd "<Solution>" && uip maestro flow init <Name> --sdk-source )
# edit <Solution>/<Name>/.flow-sdk/<Name>.flow.ts, then run the Lifecycle loop below
```

Do not hand-write the skeleton. `--sdk-source` decompiles the trigger-only artifact into `.flow-sdk/<Name>.flow.ts`, creates the folder, and preserves the product-assigned flow id/name; a hand-written `flow('<name>')` invents an id. The first `compile -o` overwrites the stub. `init` answering "already exists and is not empty. Use --force to overwrite" means it exists: never pass `--force`; edit it. An Extract document node is `dynamicExtract()` ([`references/document-pipeline.md`](references/document-pipeline.md)); it needs SDK 6.118.0 or later, else use the CLI.

When the request names **Maestro Automate** as the product, run `( cd "<Solution>" && uip maestro flow init <Name> --automate --sdk-source )`; bare "automate invoice intake" means a plain Flow. Nothing after `init` changes: it writes `runtimeOptions.profile` to `operate.json` and a `.maestro_automate` marker; `compile -o` rewrites only `.flow`, so both survive.

When `<Solution>/<Name>/` existed before this turn, skip `init`; edit its `<Name>.flow` via [Editing an existing flow](#editing-an-existing-flow), never by compiling an earlier turn's source over it. Keep `.flow-sdk/<Name>.flow.ts`, the `<Name>` directory, and `<Name>.flow` aligned. Exactly one `<Name>.flow` may exist at `<Solution>/<Name>/<Name>.flow`, never at the workspace root. Root emission is only for packaged-SDK local gates, which do not scaffold; choose [Lifecycle](#lifecycle) first and do not mix loops.

**Install the SDK first, once per machine:** `npm install -g @uipath/maestro-builder-sdk`; skip it when already installed, and see [`references/CLI-LOOP.md`](references/CLI-LOOP.md#installing-the-package) for the checks and failure handling.

For an external service or data (weather, Slack, a REST API), choose the node before writing it: run `uip maestro registry search '<brand or service name>'`, unless the request names the transport itself ("over HTTP, not a connector" means `http()`). A hit is a connector; `"total": 0` means `http()` (not for an external agent: see the table). With none pulled, `registry search` searches the tenant through `uip`. For capabilities outside the connector library (agent/process), run the family's `uip maestro flow registry search` ([`references/agent.md`](references/agent.md)). For document extraction, default to a published IXP model ([`references/ixp.md`](references/ixp.md)); use the Extract document node only when named or already present ([`references/extract-document-node.md`](references/extract-document-node.md)). Never replace such a step with fixed-value `script()`; `mock()` only marks a capability the search proved absent.

Connectors require [`.flow-sdk/bindings.json`](references/bindings.md). `uip maestro registry pull` writes descriptors to `.flow-sdk/connectors/<key>.ts` and caches the library outside the project. If download fails, `pull` fetches through `uip` into `connectors-local/`; with none pulled, so do `check` and `compile`. Prepared modules are `.flow-sdk/connectors-local/<key>.ts`, with descriptors under `.flow-sdk/connectors-local/descriptors/<key>/`; because the source sits in `.flow-sdk/` too, import pulled descriptors as `./connectors/<key>.ts` and prepared modules as `./connectors-local/<key>.ts`.

### The connector loop: author → check → prepare → check → compile

Authoring never waits on `prepare`: after search selects the node, no further discovery command precedes the source; write from the task's words: intended fields, `lookup()` id tokens, and `{ object: '<name-as-the-task-said-it>' }` for a generic operation. Then run `uip maestro flow check .flow-sdk/<Name>.flow.ts --source`.

`check` names every prepare you owe, with the exact command: `OBJECT_UNPREPARED` for an unmaterialized object, `CUSTOM_FIELDS_UNPREPARED` for an input outside the tenant-agnostic snapshot, `LOOKUP_UNRESOLVED` for a lookup token with no recorded value, `CONNECTOR_INPUT` for a field the operation does not declare. Run that one `uip maestro registry prepare <connector-key> --action <action>`; `--object`, `--resolve`, and `-f` compose in one invocation. It finds the connection, writes `.flow-sdk/bindings.json`, and repoints the import to `./connectors-local/<key>.ts`; then re-run `check` and compile. Where two flows import the same connector, `prepare` names them instead of guessing and asks for `--source`.

What `prepare` binds or refuses: [bindings.md](references/bindings.md#where-both-values-come-from). `CONNECTOR_NOT_IN_LIBRARY`, `CONNECTOR_OBJECT_REQUIRED`, and `CONNECTOR_OBJECT_NOT_GENERIC` require source fixes, not prepares: [connector-params.md](references/connector-params.md#author-first--check-names-every-prepare-you-owe). Schema-dynamic operations (`loadByDefault`, dependent dropdowns, `customFieldsRequestDetails`) need the prepare `check` names with every required `-f`, and a post-compile cache check: [`references/connector-params.md`](references/connector-params.md#schema-dynamic-operations-the-parent-field-loop).

### Hello world Flow

```ts
import { flow, script, input, out, types } from '@uipath/maestro-builder-sdk';
export default flow('hello').name('Hello')
  .input({ name: types.string }).output({ greeting: types.string })
  .step('greet', script({ code: 'return `Hello ${$vars.start.output.name}`;' }))
  .return({ greeting: out('greet') }).build();
```

## Lifecycle

Choose one loop before any build command; never mix loops or use one as the other's probe:

- **Product-CLI loop (emit-only):** use when product validate/debug evidence is requested or the workspace is emit-only: a `package.json` with `{ "flowSdk": { "emitOnly": true } }` (product-runtime eval sets it), or `FLOW_SDK_EMIT_ONLY=1`. Scaffold first ([Project layout](#project-layout)).
- **Packaged-SDK local gates:** otherwise, run source `check`, root `compile`, and `validate` — [`references/CLI-LOOP.md`](references/CLI-LOOP.md#local-authoring-hard-gates).

`uip maestro flow` delegates to the installed SDK. Emit-only is project-scoped: the nearest upward `package.json` declaring `flowSdk.emitOnly` decides it; a nested file without `flowSdk` inherits, and `emitOnly: false` opts out. In emit-only mode, `compile` only serializes source, both `flow check` modes refuse, and product `validate` verifies structure. A new flow's pass is emit, required artifact bindings, then validate:

```bash
( cd "<Solution>/<Name>" && uip maestro flow compile .flow-sdk/<Name>.flow.ts -o <Name>.flow )
uip maestro flow validate "<Solution>/<Name>/<Name>.flow" --output json
# Stated runtime claim; ask per references/operate.md
( cd "<Solution>" && uip solution resources refresh --solution-folder . --output json )
( cd "<Solution>" && uip maestro flow debug <Name> --log-level error \
  --output-filter "{status:finalStatus,instance:instanceId,url:studioWebUrl,failed:elementExecutions[?status!='Completed'].{id:elementId,status:status},<Out>:variables.globals.<Out>,incidents:incidents}" \
  --output json )
```

`<Out>` means each declared `out` variable, never all of `variables.globals`. Re-run from `compile` after the last source or binding edit. Valid means top-level `Result` plus `Data.Status: "Valid"`; treat `Data.Warnings` as failures except the reviewed shared-connection advisory and `err()` diagnostics. Runtime evidence requires `Completed`, expected globals, and empty `failed`; an exit code alone is insufficient. Debug inputs, attachments, other projections, and incidents per [`references/CLI-LOOP.md`](references/CLI-LOOP.md#refresh-debug-and-preserve-evidence).

## Editing an existing flow

Preserve supplied source, step names, and unaffected wiring. Insert a step by moving the old edge through it, not by creating a second path. Unless source was supplied, freshly decompile the `.flow`, edit narrowly, and merge back. Decompiling overwrites a supplied source: use [its loop](references/brownfield.md#a-supplied-source).

`decompile` stamps the source's first line; `merge` reads it, derives the baseline from the original, and writes over it:

```bash
( cd "<Solution>/<Name>" && [ ! -d .flow-sdk ] || find .flow-sdk -maxdepth 1 \( -name '<Name>.baseline' -o -name '<Name>.edited' -o -name '<Name>.merged.flow' -o -name baseline -o -name edited -o -name '????????-????-????-????-????????????' \) -exec rm -rf {} + )
uip maestro flow decompile <Name>.flow -o .flow-sdk/<Name>.flow.ts --no-pipeline
# edit .flow-sdk/<Name>.flow.ts narrowly; keep its first line; no .layout() for added steps (builder-sdk#1320)
uip maestro flow check .flow-sdk/<Name>.flow.ts --source --baseline <Name>.flow   # fix each (edited) error; `unknown option`: brownfield.md
( head -n 1 .flow-sdk/<Name>.flow.ts | grep -q '^// @decompiled-from ' || { echo 'no stamp (SDK<6.96.0): NOT merged' >&2; exit 1; }; uip maestro flow merge .flow-sdk/<Name>.flow.ts --original <Name>.flow )
```

Only `merge` writes the `.flow`; a refusal writes nothing. Validate as in [Lifecycle](#lifecycle); on failure, fix the source, `check` and `merge` again (it is restamped). `no stamp` or `MERGE_ORIGINAL_CHANGED`: [the stamp](references/brownfield.md#the-stamp-and-when-merge-refuses).
**True-brownfield procedure:** **[`references/brownfield.md`](references/brownfield.md)**.

## Builder frame

Use `flow(id)`, declarations, nodes, `.return(...)`, and `.build()`. The `start` step is the manual trigger's default name and carries the flow's inputs; outputs return to the caller only on success.

- `.var(name, types.*, default?)` declares state written/read by multiple steps; `.input` and `.output` are the caller contract. A step writes a var with `{ updates: { name: <expr> } }`. Inputs, outputs and vars allow only `types.string`, `types.number`, `types.boolean`, `types.object`, `types.array`, and `types.file`; `float`, `double`, `date`, `datetime`, and `jsonSchema` are refused: [variable types](references/author.md#variable-types). There is no node for an Orchestrator asset; use a var default or input.
- `.return(...)` ends a PATH; `.terminate(...)` ends the RUN. In a `.parallel` arm, terminate aborts sibling arms, while return lets them continue.
- **Expressions are how a step names something that is not a literal:** `input(name)` flow input; `v(name)` flow variable; `out(step, path?)` whole or field result; `err(step, field?)` failed-step error envelope only inside its handler; `ran(step)` whether a step ran; `lit(value)` a constant, where a raw value would be ambiguous; ``js`…` `` / ``tmpl`…` `` an authored expression/string. When arms converge, prefer one shared continuation over duplicating work per arm; `ran` tells it whether the value it wants was produced.

## API index

**Every signature, option shape and field is indexed in the installed `@uipath/maestro-builder-sdk` package**, not this guide; paths are relative to the package root:

| you have | look in | a row gives |
|---|---|---|
| a field or method — `outcomePorts`, `stepToList` | `dist/api-members.md` | declaring shape and declaration lines |
| an exported symbol — `HitlInputs`, `hitl`, `FlowBuilder` | `dist/api-index.md` | kind, area, and declaration lines |

Match one name; do not read either file end to end. Read the whole declaration and doc comment at the indicated span (for example, `dist/core/actions.d.ts:583-597`) from `.d.ts`, never `dist/*.js`. A name in neither index is probably a RUNTIME output key covered by node references. More rules: [`references/author.md`](references/author.md#api-index-lookups).

## Supported node types

This table is authoritative; read each node's `Reference` before writing it ([Critical Rule 2](#critical-rules)). `Example` names the one complete flow to copy from; paths under `examples/` resolve inside this skill folder.

| Node or surface | Emitted node type | Builder | Reference | Example |
|---|---|---|---|---|
| Manual trigger | `core.trigger.manual` | omit `.trigger(...)` | [manual-trigger.md](references/manual-trigger.md) | `examples/GreenhouseWatering.flow.ts.md` |
| Entry points (multiple triggers) | one trigger per extra root | `.entryPoint(id, trigger, { inputs?, version?, default? }, prefixFn?)`; shared var: input `{ type, shared: '<var>' }` | [manual-trigger.md](references/manual-trigger.md#multiple-entry-points) | — |
| Scheduled trigger | `core.trigger.scheduled` | `scheduled(...)` | [scheduled-trigger.md](references/scheduled-trigger.md) | `examples/HerbariumDispatch.flow.ts.md` |
| Connector event trigger; HTTP start | `uipath.connector.trigger.<key>.<event>` | `onEvent(...)` | [event-trigger.md](references/event-trigger.md), [HTTP call](references/event-trigger.md#started-by-an-http-call) | `examples/DoorbellLog.flow.ts.md` |
| Connector event wait | `uipath.connector.event.<key>.<event>` | `waitForEvent(...)` | [event-trigger.md](references/event-trigger.md) | `examples/PlanetariumConfirmation.flow.ts.md` |
| Form trigger | `core.trigger.form` | `formTrigger(...)` | [form-trigger.md](references/form-trigger.md) | `examples/BakeOffEntryForm.flow.ts.md` |
| Conversation trigger | `core.trigger.conversation` | `conversationTrigger(...)` | [conversational.md](references/conversational.md) | `examples/LibraryDeskChat.flow.ts.md` |
| Voice trigger | `core.trigger.voice` | `voiceTrigger(...)` | [voice.md](references/voice.md) | `examples/HarbourRadioLine.flow.ts.md` |
| HTTP (`managed: false` no longer runs) | `core.action.http.v2` | `http({ managed: true, ... })` | [http.md](references/http.md) | `examples/ObservatorySeeing.flow.ts.md` |
| Script | `core.action.script` | `script(fn)` SDK ≥ 6.57.0 (`$metadata` ≥ 6.72.0); `script({ code })` | [script.md](references/script.md) | `examples/GreenhouseWatering.flow.ts.md` |
| Transform | `core.action.transform` | `transform(...)` | [transform.md](references/transform.md) | `examples/TrailLogSummary.flow.ts.md` |
| Filter | `core.action.transform.filter` | `transform({ variant: 'filter', ... })` | [transform.md](references/transform.md) | `examples/TrailLogSummary.flow.ts.md` |
| Map | `core.action.transform.map` | `transform({ variant: 'map', ... })` | [transform.md](references/transform.md) | `examples/TrailLogSummary.flow.ts.md` |
| Group by | `core.action.transform.group-by` | `transform({ variant: 'group-by', ... })` | [transform.md](references/transform.md) | `examples/TrailLogSummary.flow.ts.md` |
| Integration Service action | `uipath.connector.<key>.<action>` (Data Fabric/Data Service native-family gaps include file fields/events: `uipath.connector.uipath-uipath-dataservice.*`) | `connector(...)` | [connector-params.md](references/connector-params.md) | `examples/ClubDirectory.flow.ts.md` |
| Data Fabric read | `core.datafabric.read` (`resultMode: 'multiple'` selects 1.4; `limit` max 1000) | `dataFabricRead(...)` | [data-fabric.md](references/data-fabric.md) | `examples/BeeHiveLedger.flow.ts.md` |
| Data Fabric create | `core.datafabric.create` | `dataFabricCreate(...)` | [data-fabric.md](references/data-fabric.md) | `examples/BeeHiveLedger.flow.ts.md` |
| Data Fabric update | `core.datafabric.update` | `dataFabricUpdate(...)` | [data-fabric.md](references/data-fabric.md) | `examples/BeeHiveLedger.flow.ts.md` |
| Data Fabric delete | `core.datafabric.delete` (NO outputs) | `dataFabricDelete(...)` | [data-fabric.md](references/data-fabric.md) | `examples/BeeHiveLedger.flow.ts.md` |
| Subflow | `core.subflow` | `subflow(...)` | [subflow.md](references/subflow.md) | `examples/RecipeScaler.flow.ts.md` |
| Human task | `uipath.human-in-the-loop` | `hitl(...)` | [hitl.md](references/hitl.md) | `examples/GallerySubmission.flow.ts.md` |
| Human quick form | `uipath.human-in-the-loop.quick-form` (one exit per outcome: `.stepSwitch` routes them; a plain `.step()` continues every outcome) | `hitl({ variant: 'quick-form', ... })` | [hitl.md](references/hitl.md) | `examples/FieldTripQuickForm.flow.ts.md` |
| Human action app | `uipath.human-in-the-loop.coded-action-app` | `hitl({ variant: 'action-app', ... })` | [hitl.md](references/hitl.md) | `examples/KilnReview.flow.ts.md` |
| RPA workflow | `uipath.core.rpa-workflow.<key>` | `rpaWorkflow(...)` | [rpa-workflow.md](references/rpa-workflow.md) | `examples/WorkshopInventory.flow.ts.md` |
| Queue item | `core.action.queue.create*` | `queueItem(...)` | [queue.md](references/queue.md) | `examples/HerbariumDispatch.flow.ts.md` |
| Summarize | `uipath.pattern.deep-rag` | `summarize(...)` | [summarize.md](references/summarize.md) | `examples/OralHistoryDigest.flow.ts.md` |
| Batch transform | `uipath.pattern.batch-transform` | `batchTransform(...)` | [batch-transform.md](references/batch-transform.md) | `examples/FossilCatalogEnrich.flow.ts.md` |
| Branch | `core.logic.decision` | `.branch(...)` | [branch.md](references/branch.md) | `examples/GreenhouseWatering.flow.ts.md` |
| Switch | `core.logic.switch` | `.switch(...)` | [switch.md](references/switch.md) | `examples/BeltProgression.flow.ts.md` |
| Parallel / Merge | `core.logic.merge` | `.parallel(...)` | [parallel-merge.md](references/parallel-merge.md) | `examples/ConcertSoundcheck.flow.ts.md` |
| Loop | `core.logic.loop` | `.loop(...)` | [loops.md](references/loops.md) | `examples/ClubDirectory.flow.ts.md` |
| Do while | `core.logic.dowhile` | `.doWhile(...)` | [loops.md](references/loops.md#do-while) | `examples/MeteorShowerPages.flow.ts.md` |
| Return / End | `core.control.end` | `.return(...)` | [return.md](references/return.md) | `examples/GreenhouseWatering.flow.ts.md` |
| Terminate | `core.logic.terminate` | `.terminate(...)` | [terminate.md](references/terminate.md) | `examples/AquariumSafetyStop.flow.ts.md` |
| Placeholder | `core.logic.mock` | `mock()` | [placeholder.md](references/placeholder.md) | `examples/FestivalMapScaffold.flow.ts.md` |
| Unknown node type | registry `nodeType` verbatim (never `uipath.connector.*`) | `rawNode(...)` | [placeholder.md](references/placeholder.md#unknown-node-types) | — |
| Error handler | `error` handle on action | `.onError(...)` | [error-handling.md](references/error-handling.md) | `examples/ObservatorySeeing.flow.ts.md` |
| Delay | `core.logic.delay` | `delay(...)` | [delay.md](references/delay.md) | `examples/LighthouseSignal.flow.ts.md` |
| API workflow | `uipath.core.api-workflow.<key>` | `apiWorkflow(...)` | [api-workflow.md](references/api-workflow.md) | `examples/BirdCountLookup.flow.ts.md` |
| Agentic process | `uipath.core.agentic-process.<key>` | `agenticProcess(...)` | [agentic-process.md](references/agentic-process.md) | `examples/NeighborhoodWalkPlanner.flow.ts.md` |
| Agent resource | `uipath.core.agent.<key>` | `agent(...)` | [agent.md](references/agent.md) | `examples/PlantNameAdvisor.flow.ts.md` |
| External agent or automation | `uipath.connector.<key>.<operation>` | `connector(...)`; `registry prepare` first when absent from library | [external-agent.md](references/external-agent.md) | — |
| Inline agent | `uipath.agent.autonomous` | `inlineAgent(...)` | [inline-agent.md](references/inline-agent.md) | `examples/PostcardCaption.flow.ts.md` |
| IxP extraction | `uipath.ixp.<project>.<version>-<folder>` | `ixpExtract(...)` | [ixp.md](references/ixp.md) | `examples/ArchiveCardExtract.flow.ts.md` |
| Document classify | `uipath.document.classify` | `documentClassify(...)` | [document-pipeline.md](references/document-pipeline.md) | `examples/SeedPacketReader.flow.ts.md` |
| Extract document | `uipath.ixp.extract-document-builder` | `dynamicExtract(...)` | [document-pipeline.md](references/document-pipeline.md), [extract-document-node.md](references/extract-document-node.md) | `examples/SeedPacketReader.flow.ts.md` |
| Published function | `uipath.core.function.<key>` | `publishedFunction(...)` | [published-function.md](references/published-function.md) | `examples/TideTableConverter.flow.ts.md` |
| Conversation message wait | `uipath.conversational.wait-for-message` | `waitForMessage(...)` | [conversational.md](references/conversational.md) | `examples/LibraryDeskChat.flow.ts.md` |
| Conversational agent | `uipath.agent.conversational` | `conversationalAgent(...)` | [conversational.md](references/conversational.md) | `examples/LibraryDeskChat.flow.ts.md` |
| Conversation send message | `uipath.conversational.send-message` | `sendMessage(...)` | [conversational.md](references/conversational.md) | `examples/LibraryDeskChat.flow.ts.md` |
| Voice outgoing call | `uipath.conversational.voice.create-outgoing-call` | `createOutgoingCall(...)` | [voice.md](references/voice.md) | `examples/PotteryStudioCallback.flow.ts.md` |
| Voice agent | `uipath.agent.voice` | `voiceAgent(...)` | [voice.md](references/voice.md) | `examples/PotteryStudioCallback.flow.ts.md` |
| Voice end call | `uipath.conversational.voice.end-call` | `endCall(...)` | [voice.md](references/voice.md) | `examples/PotteryStudioCallback.flow.ts.md` |

## Authoring a flow

[Critical Rules](#critical-rules) govern node choice, open decisions, and errors; details are in **[`references/author.md`](references/author.md)**. A requested canvas arrangement uses `.layout()` with `at()`/`dim()`: [`references/operate.md`](references/operate.md#lay-out-from-source-instead-layout-at-dim).

## Operating a deployed flow

Upload, deploy, debug, trigger, inspect jobs, and drive instance lifecycle only with `uip login`; run `uip solution resources refresh` before every upload, publish, or debug. `flow debug` is a REAL run, not a validation step: ask first, as it says. Read **[`references/operate.md`](references/operate.md)**.

## Diagnosing a failed run

Triage in order: existing debug response, incidents, runtime variables, deployed artifact, then traces. The builder removes some classic `.flow` defects but can leave expressions that are actually literals. Read [`references/diagnose.md`](references/diagnose.md).

## Evaluating a flow

An inline agent creates no evaluators, eval sets, data points, or simulations; the Flow eval CLI manages them as project files. Read [`references/evaluate.md`](references/evaluate.md).

## Final evidence

Product-resource truth is live evidence: confirm plausible ids, argument names, scenario-named optional inputs, and warnings against the tenant. Static diagnostics own mechanically checkable structure; fix causes rather than copying rules into this router.

Match proof to the request's acceptance bar. For one remaining wiring question, validate-only is complete when product validation is green and its required structural self-check passes; do not debug only for confidence. For each behavior claim the bar names, plan at most one bounded product debug that answers it. If one wiring question remains, run one bounded distinguishing experiment, apply the answer, and stop; do not create scratch-solution families or repeat equivalent variants.
