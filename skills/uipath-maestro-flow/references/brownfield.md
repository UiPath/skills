# True-brownfield decompile, edit, and merge

Use this for an existing `.flow` unless its `.flow.ts` was supplied; a prior-turn `.flow.ts` does not count because the canvas may have changed the `.flow`.

<!--skill-flavor:fresh-decompile-cleanup:start-->
Decompile fresh after removing earlier-turn pipeline artifacts ([The generated pipeline](#the-generated-pipeline)).
<!--skill-flavor:fresh-decompile-cleanup:end-->

Never hand-transcribe the graph: decompile to builder source, edit it, and merge only its delta into the original. If adding a [pattern](author.md#patterns) (review gate, triage, batch loop, chat or voice front door, or panel of agents), read its guide and insert only what the flow lacks, as “Adapting it” says.
Inserting a pattern is still a narrow edit through this loop.

Canvas-inserted patterns are unfinished: replace each `core.logic.mock` labelled “(replace with …)” with the real node (rule 1 in [author.md](author.md#critical-rules)); rewrite every `PLACEHOLDER -` agent prompt for the request; do the setup sticky-note work; put builder-impossible items (such as attaching a tool to a voice agent) under Open questions; preserve all other inserted steps, ports, and names.

## The safe project loop

<!--skill-flavor:safe-project-loop:start-->
Keep authored source beside the canonical Flow so relative sidecars resolve; keep compiled artifacts outside the Flow project. Product validation must find exactly one `.flow` recursively.

```bash
PROJECT=Solution/Deployed
CANONICAL="$PROJECT/Deployed.flow"
WORK=.flow-work/Deployed
rm -rf "${WORK:?}" && mkdir -p "$WORK/baseline" "$WORK/edited" "$WORK/candidate"

uip maestro flow decompile "$CANONICAL" -o "$PROJECT/Deployed.flow.ts" --no-pipeline
uip maestro flow compile "$PROJECT/Deployed.flow.ts" -o "$WORK/baseline/Deployed.flow"
# If this stops, run the check below before editing; it identifies an old SDK or probable SDK defect.
# Edit $PROJECT/Deployed.flow.ts narrowly; preserve existing step ids.
# Leave added steps out of .layout(...): merge places them (builder-sdk#1320).
uip maestro flow check "$PROJECT/Deployed.flow.ts" --source --baseline "$CANONICAL"
uip maestro flow compile "$PROJECT/Deployed.flow.ts" -o "$WORK/edited/Deployed.flow"
uip maestro flow merge "$WORK/edited/Deployed.flow" --original "$CANONICAL" \
  -o "$WORK/candidate/Deployed.flow" --baseline "$WORK/baseline/Deployed.flow"

BACKUP=$(mktemp -d) && echo "backup: $BACKUP" && cp -r "$PROJECT/." "$BACKUP/"
cp -r "$WORK/candidate/." "$PROJECT/"
# Then delete each directory merge listed as `flow-merge: remove <dir> ...`.
uip maestro flow validate "$CANONICAL" --output json && rm -rf "${BACKUP:?}"
```

Run the displayed commands. Install the candidate wholesale with `cp`; never write or patch `.flow` yourself or copy only the change into the original. Merge renumbers every edge (`edge_0`, `edge_1`, ...), may reorder nodes, and adds default fields: that is its normal output, not drift to undo. Act on [merge warnings](#merge-warnings-what-the-round-trip-changed).

Validate in the project, not `candidate/` alone: it contains only changed files, so an unchanged inline agent’s `agent.json` may be absent ([builder-sdk#1318](https://github.com/UiPath/builder-sdk/issues/1318)). If validation fails, restore before merging again:
`test -d "${BACKUP:?}" && rm -rf "${PROJECT:?}" && mkdir "$PROJECT" && cp -r "$BACKUP/." "$PROJECT/" && rm -rf "$BACKUP"`.

Keep the `mktemp -d` backup outside the working directory; a project copy there is a second Flow project.
<!--skill-flavor:safe-project-loop:end-->

Compile the baseline before the edit, never after: merge diffs edited against it, so a baseline of the edited source drops your change. With edited `.flow.ts` and `--baseline-from`, `merge` runs `check` on the edited source and refuses the write on an error in a node or subflow the edit changed (`N error(s) in nodes merge takes from the edited flow`), and on one it cannot place that the edit introduced. Untouched-node/subflow errors print `DRAFT_NODE_KEPT`; an untouched node the SDK cannot compile prints `LOWERING_NODE_KEPT` (probable SDK defect; tell the user; 6.64.0 or later). A finding `merge` cannot place on a node, also reported by the original round trip, prints `CHECK_FINDING_UNPLACED`. Fix findings in edited nodes.

Requires `@uipath/maestro-builder-sdk` 6.44.4 or later. An older SDK refuses writes for an unplaceable error on an untouched root node.
<!--skill-flavor:merge-check-sdk-upgrade:start-->
Upgrade with `npm install -g @uipath/maestro-builder-sdk@latest`.
<!--skill-flavor:merge-check-sdk-upgrade:end-->

Do not copy `baseline/` or `edited/` into the project or leave an earlier `*.merged.flow` there: every `.flow` below the project is a deliverable.

### Check only what you changed: `check --baseline`

`compile` does not run `check`; run `check` after every edit, before edited `compile`, and treat errors as the gate. Pass the original `.flow`, not a compiled baseline, as `--baseline`; findings identify whether the edit caused them. In emit-only mode `check` refuses: skip it and use `validate`.

Requires `@uipath/maestro-builder-sdk` 6.64.0 or later. Older SDKs appear as a baseline compile stopping on a check code (for example pre-existing `HTTP_READ_WITHOUT_RETURNS`), `uip` refusing with `--baseline on flow check needs @uipath/maestro-builder-sdk >= 6.64.0; found <version>`, or older `uip` reporting `error: unknown option '--baseline'`; all mean the SDK is too old.
<!--skill-flavor:check-baseline-sdk-upgrade:start-->
Upgrade with `npm install -g @uipath/maestro-builder-sdk@latest`.
<!--skill-flavor:check-baseline-sdk-upgrade:end-->

```text
$ uip maestro flow check <Name>.flow.ts --source --baseline <original>.flow
✗ [UNKNOWN_REF] Reference to undeclared variable/step "lookup" in "report". (edited)
⚠ [HTTP_READ_WITHOUT_RETURNS] ... (pre-existing, not counted)
⚠ [CONNECTOR_INPUT] Connector step "notify": ... unknown input "designerOnly". ... (pre-existing)
  This node is unchanged from the baseline, so this is probably an SDK defect: ...

1 error(s) in edited nodes, 1 pre-existing SDK defect(s), 1 pre-existing warning(s)
```

- **`(edited)`** (JSON `origin: "edited"`): fix it, including an untouched node broken by the edit (such as a deleted `lookup`); exit code 1 remains while one exists.
- **`(pre-existing, not counted)`**: leave it unless requested; a deployed HTTP node without a body schema may have `HTTP_READ_WITHOUT_RETURNS` ([builder-sdk#1319](https://github.com/UiPath/builder-sdk/issues/1319)).
<!--skill-flavor:check-baseline-lowering:start-->
- **`(pre-existing)` probable SDK defect** (JSON `class: "lowering"`): `compile` refuses it and both loop compiles stop. Before editing, run this check to distinguish it; do not edit around it. Use [`merge --baseline-from`](#flows-with-draft-nodes-let-merge-compile), which keeps the node as saved (`LOWERING_NODE_KEPT`), and tell the user to report it at <https://github.com/UiPath/builder-sdk/issues>.
<!--skill-flavor:check-baseline-lowering:end-->
- **`CHECK_INCOMPLETE`**: fix the whole-flow refusal (for example two Ends whose names give one node id), even if pre-existing, then check again.

### Why three directories: inline agents

An inline agent has the `.flow` node plus prompts, model, and run settings in `<source>/agent.json`; prompt edits change only that file. Each compile writes output-side `agent.json`; merge compares baseline and edited copies, applies only the edit to the project copy, and writes it beside the candidate. Example messages include:

```text
flow-merge: wrote Deployed.flow (12 nodes, 13 edges)
flow-merge: wrote <source-uuid>/agent.json (carries messages[0].content)
```

<!--skill-flavor:install-agent-files:start-->
`cp -r "$WORK/candidate/."` installs the `.flow` and every carried agent file. Fields the round trip does not reproduce, such as `maxIterations` or an input `description`, retain project values.
<!--skill-flavor:install-agent-files:end-->

Merge warns, does not carry, and refuses under `--strict` when:

- baseline and edited flows share a directory: the second compile overwrites baseline `agent.json`, so merge cannot distinguish the edit (`the edited <source>/agent.json differs from the original's ... The change is NOT carried`); use separate directories;
- an agent resource is changed or removed and cannot be paired with a project resource because compile does not reproduce its node id or `resource.json` fields; make that change on the canvas;
- an older canvas save embeds prompts on the agent node; edit the canvas.

Never copy `$WORK/edited/<source>/` manually; it includes round-trip changes.

### Agent resources: added, changed, removed

An agent context index or tool is `<source>/resources/<dir>/resource.json`.

```text
flow-merge: wrote <source-uuid>/resources/<new-dir>/resource.json (carries added resource)
flow-merge: wrote <source-uuid>/resources/<dir>/resource.json (carries settings.resultCount)
flow-merge: remove <project>/<source-uuid>/resources/<dir> from the project: the edit removed this agent resource, and copying the candidate cannot delete it
flow-merge: wrote bindings_v2.json (the changed agents' resource rows, re-derived as compile does)
```

<!--skill-flavor:resource-install:start-->
- Install added or changed resources with `cp -r`; a changed resource retains its original directory.
- Do not install removed resources: delete every `remove` directory (`Data.Removed` in `--output json`), or it remains.
<!--skill-flavor:resource-install:end-->

A resource used by another project `.flow` is kept (`flow-merge: kept <source>/resources/<dir>: <Other>.flow still references it`); do not delete it. Merge writes `bindings_v2.json` with changed agents’ re-derived rows, so removed indexes are no longer declared.

## Flows with draft nodes: let merge compile

<!--skill-flavor:draft-nodes:start-->
Canvas-saved flows may contain draft nodes: unconnected connectors, empty required inputs, generic operations without objects, `waitForEvent` without a connection, Transform without a collection, or decisions without conditions (a draft trigger or connector tool still refuses and must be finished first). Decompile carries each definition and marks `{ draft: true }`; compile writes it with `⚠ [CONNECTOR_INPUT_MISSING] ... Written as a draft`. Leave it unless asked to finish it. A decision may decompile as `.branch("decision1", undefined, (t) => ..., (e) => ..., { draft: true })`; a Transform as `transform({ operations: [] })` with `{ draft: true }`. `waitForEvent`, Transform, and decision drafts need SDK 6.86.5 or later; older SDKs refuse with `BINDING_MISSING`, `TRANSFORM_COLLECTION_LITERAL`, or `EXPR_SYNTAX`.

If compile stops for `CONNECTOR_OBJECT_REQUIRED`, a draft written without a carried definition, or an untouched node the SDK cannot compile, use source merge:

```bash
rm -rf "${WORK:?}" && mkdir -p "$WORK/candidate"
uip maestro flow decompile "$CANONICAL" -o "$PROJECT/Deployed.flow.ts" --no-pipeline
# Edit $PROJECT/Deployed.flow.ts narrowly; preserve existing step ids.
flow-sdk flow merge "$PROJECT/Deployed.flow.ts" --original "$CANONICAL" \
  --baseline-from "$CANONICAL" -o "$WORK/candidate/Deployed.flow"
```

Set `PROJECT`, `CANONICAL`, and `WORK`; validate and replace as in [the safe project loop](#the-safe-project-loop). `--baseline-from <original.flow>` builds the baseline in memory, so skip baseline compile; edited `.flow.ts` is compiled by merge and both compiles tolerate drafts. It needs `@uipath/maestro-builder-sdk` 6.28.0 or later; older `flow-sdk` reports `unknown option '--baseline-from'`. Upgrade with `npm install -g @uipath/maestro-builder-sdk@latest`.

An untouched draft, including one in an unchanged subflow, is restored exactly with `[DRAFT_NODE_KEPT]` (6.44.4 or later; older SDKs take every subflow from edited source and refuse it). A changed draft refuses with `[BINDING_MISSING]`, `[CONNECTOR_INPUT_MISSING]`, or `[CONNECTOR_OBJECT_REQUIRED]`; finish or revert it. An untouched uncompileable node is kept with `⚠ [LOWERING_NODE_KEPT] "<node>" is untouched, so the original node is kept as is, but the SDK cannot compile it (<CODE>)`; tell the user it is a probable SDK defect and report it at <https://github.com/UiPath/builder-sdk/issues>. The same refusal on a changed/new node is `✗ [<CODE>] "<node>" is changed or new`; revert or fix it. A node failing because an edit elsewhere deleted a referenced step also stops the write. These behaviors need 6.64.0 or later.

Pass `--library` / `--bindings` as for `compile`; `--strict` works. Use the SDK `flow-sdk` binary because `uip maestro flow merge` does not yet forward `--baseline-from` (UiPath/cli#5214).
<!--skill-flavor:draft-nodes:end-->

## The generated pipeline

<!--skill-flavor:generated-pipeline:start-->
`decompile` writes `<Name>.pipeline.mjs` in `.flow-sdk/`. Prefer it for narrow edits: it captures the pristine baseline and chains all four steps.

```bash
uip maestro flow decompile Deployed.flow -o .flow-sdk/Deployed.flow.ts
node .flow-sdk/Deployed.pipeline.mjs    # compiles the pristine baseline; stops there
# Edit .flow-sdk/Deployed.flow.ts narrowly; preserve existing step ids.
uip maestro flow check .flow-sdk/Deployed.flow.ts --source --baseline Deployed.flow
node .flow-sdk/Deployed.pipeline.mjs --strict   # compiles the edit, merges into .flow-sdk/Deployed.merged.flow
```

Pipeline compiles do not run `check`; run [`check --baseline`](#check-only-what-you-changed-check---baseline) yourself before the second run, until no `(edited)` error remains. `--strict` makes merge refuse (exit 1, no file) instead of warning for unintended round-trip changes ([Merge warnings](#merge-warnings-what-the-round-trip-changed)); the Node stack trace after `flow-merge: refused (--strict)` is expected; read the refusal above it. Without `--strict`, warnings and a merged file are produced. If `grep -q STRICT .flow-sdk/Deployed.pipeline.mjs` fails, use [the same loop by hand](#the-same-loop-by-hand) with `merge --strict`.

Re-running after edits repeats compile and merge using the captured baseline. Before a later fresh decompile, remove prior artifacts and sidecars:
`[ ! -d .flow-sdk ] || find .flow-sdk -maxdepth 1 \( -name 'Deployed.baseline' -o -name 'Deployed.edited' -o -name 'Deployed.merged.flow' -o -name '????????-????-????-????-????????????' \) -exec rm -rf {} +`.

Pass `--no-pipeline` for the manual sequence. Keep pipeline `.flow` artifacts outside the canonical project because product validation treats every `.flow` below the project, hidden folders included, as a deliverable. Keep source in the project when relative sidecars require it; use [the safe project loop](#the-safe-project-loop).
<!--skill-flavor:generated-pipeline:end-->

## A supplied source

<!--skill-flavor:supplied-source:start-->
When the task supplies `.flow-sdk/Deployed.flow.ts`, do not decompile; decompilation overwrites it. Compile its baseline before editing, then merge:

```bash
[ ! -d .flow-sdk ] || find .flow-sdk -maxdepth 1 \( -name baseline -o -name edited -o -name 'Deployed.merged.flow' -o -name '????????-????-????-????-????????????' \) -exec rm -rf {} +
mkdir -p .flow-sdk/baseline .flow-sdk/edited
uip maestro flow compile .flow-sdk/Deployed.flow.ts -o .flow-sdk/baseline/Deployed.flow
# Edit .flow-sdk/Deployed.flow.ts narrowly; preserve existing step ids.
uip maestro flow check .flow-sdk/Deployed.flow.ts --source --baseline Deployed.flow
uip maestro flow compile .flow-sdk/Deployed.flow.ts -o .flow-sdk/edited/Deployed.flow
uip maestro flow merge .flow-sdk/edited/Deployed.flow --original Deployed.flow \
  -o .flow-sdk/Deployed.merged.flow --baseline .flow-sdk/baseline/Deployed.flow
```

Install `.flow-sdk/Deployed.merged.flow` using [the same loop by hand](#the-same-loop-by-hand).
<!--skill-flavor:supplied-source:end-->

## The same loop by hand

<!--skill-flavor:hand-loop:start-->
```bash
[ ! -d .flow-sdk ] || find .flow-sdk -maxdepth 1 \( -name baseline -o -name edited -o -name 'Deployed.merged.flow' -o -name '????????-????-????-????-????????????' \) -exec rm -rf {} +
uip maestro flow decompile Deployed.flow -o .flow-sdk/Deployed.flow.ts --no-pipeline
mkdir -p .flow-sdk/baseline .flow-sdk/edited
uip maestro flow compile .flow-sdk/Deployed.flow.ts -o .flow-sdk/baseline/Deployed.flow
# Edit .flow-sdk/Deployed.flow.ts narrowly; preserve existing step ids.
uip maestro flow check .flow-sdk/Deployed.flow.ts --source --baseline Deployed.flow
uip maestro flow compile .flow-sdk/Deployed.flow.ts -o .flow-sdk/edited/Deployed.flow
uip maestro flow merge .flow-sdk/edited/Deployed.flow --original Deployed.flow \
  -o .flow-sdk/Deployed.merged.flow --baseline .flow-sdk/baseline/Deployed.flow
```

Keep candidates in `.flow-sdk/`; back up the project, replace the original with `.flow-sdk/Deployed.merged.flow`, copy every `<source>/` file merge reports writing, then validate the original as in [the safe project loop](#the-safe-project-loop).
<!--skill-flavor:hand-loop:end-->

The baseline must come from pristine decompiled source before edits; otherwise merge takes the compiled graph wholesale, including layout. Decompile reconstructs branch, switch, loop, parallel, error/ref, and subflow structure and preserves node ids. Every SDK-authorable family is reconstructed through its factory, including human tasks, agents/resources, published resources, queue items, AI patterns, document, conversational, voice, and connector-event steps. Recovered agents retain their `source` UUID, so `agent.json` resolves.

Leave resource identity fields unchanged. A decompiled resource may carry `nodeId`, `source`, or `label`:

```ts
context: [{ name: "Example SOP Index", id: "11111111-2222-4333-8444-555555555555",
  folderPath: "Shared/Example", label: "SOP lookup",
  nodeId: "ctx_7f2a1b", source: "d84e2c17-6a3f-4c59-b0e2-7f1a9c5b3d28" }]
```

Removing them renames the resource node `<agent>Context` / `Tool` / `Escalation` (then `2`, `3`, ...) and creates a new directory. Do not add them to newly created or copied resources. `check` reports `FLOW_AGENT_RESOURCE_NODE_ID` (blank `nodeId`, or one another node has or compile derives for another resource), `FLOW_AGENT_RESOURCE_SOURCE_NOT_GUID` (`source` not a uuid), and `FLOW_AGENT_RESOURCE_SOURCE_DUP` (two resources on one agent with the same `source`: both would write one `resource.json`); SDKs older than 6.88.2 use `INLINE_AGENT_RESOURCE_*`. Delete both `nodeId` and `source` from a copied entry. Requires SDK 6.33.0 or later; older decompile omits these fields and compile creates a new directory.
<!--skill-flavor:resource-ids-sdk-upgrade:start-->
Upgrade with `npm install -g @uipath/maestro-builder-sdk@latest`.
<!--skill-flavor:resource-ids-sdk-upgrade:end-->

A step id is its name with every non-letter, non-digit, non-`_` character changed to `_` (`a b` → `a_b`); compile never makes it unique. A duplicate name is `DUP_STEP`; an id collision (`a b`/`a_b` or trigger id) is `STEP_ID_COLLISION`, in both `check` and `compile`. Rename the new step. Child-flow steps are checked separately and taken ids are prefixed `<caller>_<step>`. To send another path to an existing step, use `.stepToRef('<name>')`, not a duplicate step. Requires SDK 6.32.4 or later; older SDKs silently rename to `<name>2`.
<!--skill-flavor:dup-step-sdk-upgrade:start-->
Upgrade with `npm install -g @uipath/maestro-builder-sdk@latest`.
<!--skill-flavor:dup-step-sdk-upgrade:end-->

Unsupported node types still round-trip as `rawNode({ nodeType, version, manifest, inputs })`; leave them alone unless requested and edit `inputs`, not the hoisted `…Definition` manifest. If all exits are wired, a multi-exit definition such as `core.logic.agentic-switch` returns `.stepSwitch('<id>', rawNode(…), [{ value: 'case-returns', body: … }, …])`, one arm per port. Agentic switch has one `case-<id>` exit per choice in `inputs.criteria`, plus `default`; adding or removing a choice in `inputs.criteria` adds or removes its `case-<id>` exit: change the arms to match. If only some exits are wired, it returns `.step('<id>', rawNode(…))` on the main port (`default` for agentic switch), with other wired exits as `.stepToList('case-<id>', …)`; unwired exits remain unwired. `mock()` means an actual `core.logic.mock`; a missing definition degrades to `mock() /* TODO: unsupported node type … */`, which must remain untouched because merge restores it.

## Merge warnings: what the round trip changed

Merge prints `flow-merge: warning: …` for each change the merged file gets although you did not make it: added, dropped, or rewired nodes/edges; node type changes; switch-case or human-task outcome id changes; and binding rows added, dropped, or duplicated. With `--baseline` it also compares the baseline (the round trip with no edit) with the original. For example:

```
flow-merge: warning: the round trip rewires logFailure1@success from forEachItem1@continue to callApi1ErrorEnd@input; merge will write the new target.
flow-merge: warning: the merged edge route1@case-case_1 -> review1@input leaves handle "case-case_1", which node "route1" (core.logic.switch) does not declare …
```

Do not install an unintended candidate; fix `.flow.ts` and merge again. An invalid merged edge handle makes `validate` refuse.

`the round trip appends End "<id>" after …` is benign: compile adds an End where an original path stops without changing behavior. A flow using `.openTails()` gets this after a human task; see [A path without an End stays open](#a-path-without-an-end-stays-open).

An embedded-agent warning (`agent "<id>" carries its prompts, model and settings on the node (embedded) …`) means settings live in `.flow`, not `<source>/agent.json`; merge applies only node input/output/label edits. Make prompt, model, or settings edits on the canvas. `--strict` accepts input/output edits but refuses dropped/changed embedded configuration or a kept prompt still using `{{input.X}}` after input `X` was removed.
<!--skill-flavor:strict-merge:start-->
Pass `--strict` to refuse (exit 1, no file) instead of warn. The benign End never refuses. `--strict` needs `--baseline`: run `node .flow-sdk/<Name>.pipeline.mjs --strict` or add it to hand-loop merge. If `uip maestro flow merge` rejects it, or pipeline exits 2 with `--strict was asked for, but …`, use:

```bash
flow-sdk flow merge .flow-sdk/edited/Deployed.flow --original Deployed.flow \
  -o .flow-sdk/Deployed.merged.flow --baseline .flow-sdk/baseline/Deployed.flow --strict
```
<!--skill-flavor:strict-merge:end-->

## Scripts come back as functions

Decompiled scripts are named TypeScript functions after the flow and passed by name:

```ts
  .step("normalize", script(script_normalize, { returns: { amount: "number" } }), { version: "1.0.0" })
  // …
function script_normalize($vars: FlowVars) {
  const amount = Number($vars.start.output.amount);
  return { amount };
}
```

Edit the function body; unchanged bodies compile byte-for-byte. `$metadata` adds `$metadata: FlowMetadata`; if it reads an unset key, the type is `FlowMetadata & Record<string, any>`. SDKs older than 6.72.0 lack `FlowMetadata` in `dist/api-index.md` and retain `script({ code: "…" })`. Apply [script.md](script.md#writing-the-script-as-a-function): functions may read only runtime-provided values.

Scripts that cannot print as functions remain `script({ code: "…" })` with one warning each: `flow-decompile: warning: step "<id>": script kept as a string: <why>`. Reasons are unparsable bodies, TypeScript-only syntax, names outside the runtime list, trailing line comments, or module-loading errors. This is informational; strings lose nothing and `--strict` does not make it an error. Pass `--scripts string` to force string form: `uip maestro flow decompile <file> -o <file>.flow.ts --scripts string`. SDK 6.57.0 or later is required; older `uip` refuses the option and names the version. The SDK must expose `ScriptValue` in `dist/api-index.md`; older decompile prints every script as `script({ code })`.

## A Case-only variable type

A Studio Web or older-SDK global may use typed `date`, `datetime`, `float`, `double`, or `jsonSchema`; decompile warns once per variable.

- **`date` / `datetime`**: no action. Decompile prints `types.string` and warns recompilation writes `"type":"string"`; merge works. Without `--baseline-from`, merged `.flow` says `"type":"string"`; with it, an untouched variable retains its type. Runtime behavior is unchanged because `flow pack` writes dates as plain strings.
- **`float` / `double` / `jsonSchema`**: retype in the same round or compile/merge stops with `DECLARATION_TYPE_NOT_FLOW`. Use the warning’s type (`types.number`; for `jsonSchema`, `types.object` or `types.array` with `{ schema }`).

## The file's schema version comes back out

Decompile emits `.schemaVersion("<the file's version>")` first, preserving the file version rather than the SDK floor. Most deployed files are `1.8`; writable band is `1.6`–`1.10`. Leave it unless retargeting. `check` warns outside the `1.9` floor: `SCHEMA_VERSION_ABOVE_FLOOR` (lower-pinned readers refuse) or `SCHEMA_VERSION_BELOW_FLOOR` (readers migrate on open). Version changes belong to `uip maestro flow migrate`, not this call.

## Designer shapes decompile keeps

Leave each shape as decompile writes it. SDK 6.44.0 or later is required; older decompile writes `js\`[object Object]\`` for envelopes, drops fork arms and `variable` rows with `has no spelling` / `cannot write back`, and compile refuses.
<!--skill-flavor:envelope-sdk-upgrade:start-->
Upgrade with `npm install -g @uipath/maestro-builder-sdk@latest`.
<!--skill-flavor:envelope-sdk-upgrade:end-->

Preserved shapes include decision/switch conditions as `jsExpression` or `=js: …`; quick-form asked-field `variable` ([hitl.md](hitl.md)); `{ fork }`, `.stepToRef` arms, and pass-through `rawNode` merge ([parallel-merge.md](parallel-merge.md)); `core.logic.loop@1.0` `output`/`loopBack` handles through its carried definition; and subflow self-Start reads as `input('<name>')` plus the subflow `.onError()`.

Warnings are on stderr as `flow-decompile: warning: …`; `--strict` makes them errors. Edit `.flow` JSON directly only where indicated below; otherwise use merge.

- An unreachable node is omitted with `// TODO: node "<id>" … is not reachable`; recompilation drops it. If it is your edit target, connect it in `.flow` first or edit that node's JSON directly.
- If a bundled type/version is unavailable at that exact `(type, typeVersion)` and the file has no definition, source omits `{ version }` and compile uses the SDK default. Baseline merge keeps an untouched node at its file version; an edited node moves and warns `node "<id>" moved <type>@<old> -> <new>`. If it is your edit target, edit that node's JSON in the `.flow` directly, or tell the user the edit moves it to the SDK's default. A type bundled at no version (connector, published process/agent) keeps its pin. If the file carries the definition, decompile puts it in a `const`, passes it to `.definitions([...])`, and preserves the pin; leave both. For example `uipath.human-in-the-loop.quick-form@1.6`, written by `node add`, when the SDK ships `1.0` and `1.1`:

  ```ts
  const quickFormV1_6Definition = { nodeType: "uipath.human-in-the-loop.quick-form", version: "1.6", ... };
  export default flow("review")
    .definitions([quickFormV1_6Definition])
    .step("review1", hitl({ ... }), { version: "1.6" })
  ```

  The node keeps `1.6` even when you edit it. Without them, compile refuses the pin and names resolvable versions; registered families first report `NODE_VERSION_UNREGISTERED`. If carried inputs differ from the factory, warning is `node "<id>" keeps <type>@<version> from the file's definitions[]; its inputs differ from <sdk-version> (<fields>)`. If that node is your edit target, edit its inputs in the merged `.flow` JSON directly. `rawNode` cannot route human-task outcomes.
- A file-format version below `1.6` omits `.schemaVersion()` and recompiles as `1.9`; migrate first or merge into the original, which preserves its version.
- An unspellable edge warns with `<source>@<port> -> <target>@<port>` and marks `/* TODO: edge(s) … are NOT in this source */` (or a top `// TODO: edge …`); recompilation and merge drop it. Edit JSON directly if the target area is involved. Parallel fan-outs are represented per [parallel-merge.md](parallel-merge.md): converging plain-step arms use `.stepToRef(<step>)` (SDK 6.44.0+); arms ending at End/Terminate use named `<node>Fork` (SDK 6.46.6+). An arm with a step before Terminate (`TERMINATE_NOT_ARM_HEAD`) or loop fan-out leaving by `.break()`/`.continue()` remains TODO, with first arm behind `/* TODO: unstructured fan-out … */`.
- A context-index setting `context: [...]` cannot express. Decompile reads an index's retrieval settings (mode, query, threshold, result count, file extension) from `<agent source>/resources/<source>/resource.json`, so keep the agent's folder beside `.flow`. A few settings have no field, for example static plain-text query, agent-argument query, disabled deeprag citations, and folder-path prefix. Recompile writes SDK values beside `-o`; merge does not update the project copy. Do not copy it; if already copied, tell the user to reset the setting in Studio Web.
- Fire-and-forget process output schemas remain on the definition, but `agenticProcess()` refuses `returns` beside `completion: 'fire-and-forget'`; source omits it and warns the fields. SDK 6.44.0+ is required; older decompile writes `returns` and compile refuses.
<!--skill-flavor:fire-and-forget-sdk-upgrade:start-->
Upgrade with `npm install -g @uipath/maestro-builder-sdk@latest`.
<!--skill-flavor:fire-and-forget-sdk-upgrade:end-->

Recompilation omits the definition schema, but merge retains the original definition row. To read output, use `completion: 'wait'` and declare `returns`.

Pin added steps with a `{ version }` used by another non-warning node of that type; if all warned, leave unpinned. If no node retains a file version, merge drops its definition without warning. An End needs a fresh name; see [A path without an End stays open](#a-path-without-an-end-stays-open).

Validate only after installing the merged file, never the intermediate compile, as in [the safe project loop](#the-safe-project-loop). Do not run `uip maestro flow format` on it; that discards author layout.

Keep decompiled `.layout({ nodes })`. Added steps have no entry; compile places them on a placeholder and merge moves them beside neighbors. To choose a spot, add `<step>: at(x, y)` beside neighbors (`import { at } from '@uipath/maestro-builder-sdk'`); avoid any x where (x − 256) is a multiple of 288 on y = 144 or 304, which merge treats as a placeholder. Containers may still move it; keep the resulting position. Existing root positions/sizes come from original regardless of source, except merge may shift later nodes or grow containers. For other changes, set `layout.nodes.<id>.position` or `.size` in merged `.flow`; if no `layout.nodes`, use its `ui`. Subflow layout applies only when that subflow changed; merge otherwise keeps the original (6.44.4+, older SDK takes every subflow from edited compile). Remove a deleted step’s layout entry or compile fails on the unknown key. Grid and rules: [`operate.md`](operate.md#lay-out-from-source-instead-layout-at-dim).
<!--skill-flavor:subflow-layout-sdk-upgrade:start-->
Upgrade with `npm install -g @uipath/maestro-builder-sdk@latest`.
<!--skill-flavor:subflow-layout-sdk-upgrade:end-->
Only an added step's entry lands: a step the edit adds has none, so compile places it on its placeholder row and `merge` moves it next to its neighbours; a container the edit grows can still push that spot aside, so keep where it lands. At the root, an existing node's position and size come from the original whatever the source says, except that `merge` shifts later nodes and grows a container to fit added steps; moving or resizing one in the source does nothing.

## A path without an End stays open

Designer or `uip maestro flow node add` flows may end at a step without an End. Decompile emits `.openTails()` in the root and every subflow chain; leave it. Removing it adds Ends to open paths. Adding after an open tail leaves the new tail open. Use `.return({ ... })` to return outputs; open paths map no outputs. Human-task exits always end with End.

Name added Ends uniquely and use existing End `{ version }`: `.return({ ... }, { name: 'endSummary', version: '<END_VERSION>' })`. An added `name: 'end'` takes the id of an existing End that decompile wrote without a name; that End becomes `end2` with no warning.

## Split (`$ref`) artifacts

A deployed `.flow` may use sibling JSON References, such as `"definitions": { "$ref": "./definitions.json" }`, or layout/extracted-subflow equivalents. Point decompile at the main file; it resolves sidecars into one model. Do not inline or edit sidecars first.

Only relative paths resolve. Absolute paths, Windows drive letters, protocol URIs (`https://…`, `file:///…`), and traversal above the referencing root are refused because `.flow` is untrusted input. Same-document pointers (`{"$ref": "#/definitions/…"}`) remain. Missing/unreadable targets error with the filename.

Compile always writes one file; write-through splitting is unsupported. The output correctly inlines sidecar content and contains no `$ref`.