# True-brownfield decompile, edit, and merge

Use this for an existing `.flow` unless the task supplied its `.flow.ts`; an earlier-turn `.flow.ts` is not supplied because the canvas may have changed the `.flow`.

<!--skill-flavor:fresh-decompile-cleanup:start-->
Decompile fresh after removing earlier pipeline artifacts ([The generated pipeline](#the-generated-pipeline)).
<!--skill-flavor:fresh-decompile-cleanup:end-->

Never hand-transcribe the graph. Decompile to builder source, edit that source, and merge only its delta into the original.

For each [pattern](author.md#patterns) (review gate, triage, batch loop, chat or voice front door, or panel of agents), read its guide first and insert only what the flow lacks, per “Adapting it”. Finish every unfinished pattern: replace each `core.logic.mock` labelled “(replace with …)” with the real node, rewrite every `PLACEHOLDER -` prompt for the request, and do the setup sticky note’s tasks. Put builder-impossible items (for example attaching a tool to a voice agent) under Open questions. Preserve every other inserted step, port, and name.

## The safe project loop

<!--skill-flavor:safe-project-loop:start-->
Keep authored source beside the canonical Flow so relative sidecars resolve. `decompile` stamps the source’s first line. `merge` compiles it, derives the baseline from the original in memory, and writes the merged flow and carried agent files into the project; it writes no compiled working artifact. The project must therefore contain exactly one `.flow` for recursive product validation.

```bash
PROJECT=Solution/Deployed
CANONICAL="$PROJECT/Deployed.flow"

uip maestro flow decompile "$CANONICAL" -o "$PROJECT/Deployed.flow.ts" --no-pipeline
# Edit $PROJECT/Deployed.flow.ts narrowly; preserve existing step ids and its first line.
# Leave added steps out of .layout(...): merge places them (builder-sdk#1320).
uip maestro flow check "$PROJECT/Deployed.flow.ts" --source --baseline "$CANONICAL"

BACKUP=$(mktemp -d) && echo "backup: $BACKUP" && cp -r "$PROJECT/." "$BACKUP/"
# Merge only a stamped source and validate before deleting the backup:
( head -n 1 "$PROJECT/Deployed.flow.ts" | grep -q '^// @decompiled-from ' \
    || { echo "no stamp: SDK older than 6.96.0, the edit was NOT merged" >&2; exit 1; }
  uip maestro flow merge "$PROJECT/Deployed.flow.ts" --original "$CANONICAL" \
    && uip maestro flow validate "$CANONICAL" --output json && rm -rf "${BACKUP:?}" )
# Then delete each path merge listed as `flow-merge: remove <path> ...`.
```

Only `merge` writes the `.flow`; never write, patch, or copy only a change into it. Merge may renumber edges (`edge_0`, `edge_1`, ...), reorder nodes, add default fields, or move original nodes right/down; accept these and follow [merge warnings](#merge-warnings-what-the-round-trip-changed).

If validation fails, restore before merging again:
`test -d "${BACKUP:?}" && rm -rf "${PROJECT:?}" && mkdir "$PROJECT" && cp -r "$BACKUP/." "$PROJECT/" && rm -rf "$BACKUP"`.
Keep backups in `mktemp -d`, never under the working directory: a project copy there is a second Flow project.

### The stamp, and when merge refuses

The first line is `// @decompiled-from Deployed.flow sha256:<64 hex> scripts=function`; `sha256` is the `decompile` source digest and the remainder records decompilation. `merge` decompiles the original identically and compares the digest-derived baseline.

- `MERGE_ORIGINAL_CHANGED`: the `.flow` changed after decompile; nothing was written. Decompile again and redo the edit; never alter the first line.
- `MERGE_SOURCE_STAMP_UNREADABLE`: the first line was edited; decompile again.
- A split original (`$ref` part files) is written as one file; delete every part under `remove`.
- After merge, `merge` rewrites the merged `.flow` first line; further edits use the same command.
- Require `@uipath/maestro-builder-sdk` 6.96.0 or later. Older `decompile` writes no stamp; older `merge` given an unstamped source takes the edited graph without a baseline and writes `merged.flow` in the current directory, leaving the original unchanged while later checks pass. The loop therefore merges only when `grep` finds the stamp, otherwise prints `no stamp: ... the edit was NOT merged`, exits 1, and keeps the backup. Upgrade with `npm install -g @uipath/maestro-builder-sdk@latest` and decompile again, or use [the same loop by hand](#the-same-loop-by-hand).
<!--skill-flavor:safe-project-loop:end-->

In by-hand loops, compile the baseline before editing, never afterward: merge diffs the edit against that baseline, and an edited baseline drops the change.

With an edited `.flow.ts` and `--baseline-from`, `merge` checks the edited source and refuses an error in a changed node/subflow (`N error(s) in nodes merge takes from the edited flow`) or an unplaceable error introduced by the edit. An untouched-node/subflow error is `DRAFT_NODE_KEPT`; an untouched node the SDK cannot compile is `LOWERING_NODE_KEPT` (probable SDK defect; tell the user; 6.64.0 or later); an unplaceable finding also reported by the original round trip is `CHECK_FINDING_UNPLACED`. Fix findings in edited nodes. Require `@uipath/maestro-builder-sdk` 6.44.4 or later; older SDKs refuse writes for any unplaceable error on an untouched root node,
<!--skill-flavor:merge-check-sdk-upgrade:start-->
so upgrade with `npm install -g @uipath/maestro-builder-sdk@latest`.
<!--skill-flavor:merge-check-sdk-upgrade:end-->

Do not copy `baseline/` or `edited/` into the project or leave an earlier `*.merged.flow` there; every `.flow` below the project is a deliverable.

### Check only what you changed: `check --baseline`

`compile` does not run `check`; run `check` after each edit and before edited `compile`, using its errors as the gate. Compile the untouched decompile first; it must have none. Pass the original `.flow` (not a compiled baseline) as `--baseline`; findings identify edit-caused errors. In emit-only mode `check` refuses; skip it and use `validate`.

Require `@uipath/maestro-builder-sdk` 6.64.0 or later. If baseline compile stops on a check code (for example pre-existing `HTTP_READ_WITHOUT_RETURNS`), `uip` reports `--baseline on flow check needs @uipath/maestro-builder-sdk >= 6.64.0; found <version>`, or older `uip` reports `error: unknown option '--baseline'`, the SDK is too old,
<!--skill-flavor:check-baseline-sdk-upgrade:start-->
so upgrade with `npm install -g @uipath/maestro-builder-sdk@latest`.
<!--skill-flavor:check-baseline-sdk-upgrade:end-->
<!--skill-flavor:check-baseline-uip-version:start-->
For `unknown option '--baseline'`, check the SDK with `npm ls -g @uipath/maestro-builder-sdk` or the project’s `node_modules`. Below 6.64.0, upgrade it. Only with 6.64.0+ and the same error is `uip` too old (1.205.0 is). Until a newer `uip`, run `check --source` without `--baseline` and fix only errors on changed nodes.
<!--skill-flavor:check-baseline-uip-version:end-->

```text
$ uip maestro flow check <Name>.flow.ts --source --baseline <original>.flow
✗ [UNKNOWN_REF] Reference to undeclared variable/step "lookup" in "report". (edited)
⚠ [HTTP_READ_WITHOUT_RETURNS] ... (pre-existing, not counted)
⚠ [CONNECTOR_INPUT] Connector step "notify": ... unknown input "designerOnly". ... (pre-existing)
  This node is unchanged from the baseline, so this is probably an SDK defect: ...

1 error(s) in edited nodes, 1 pre-existing SDK defect(s), 1 pre-existing warning(s)
```

- **`(edited)`** (JSON `origin: "edited"`): fix it, including an untouched node broken by the edit (such as a deleted referenced step). Exit code is 1 while any remains.
- **`(pre-existing, not counted)`**: leave it unless requested; deployed HTTP nodes without body schemas can produce `HTTP_READ_WITHOUT_RETURNS` ([builder-sdk#1319](https://github.com/UiPath/builder-sdk/issues/1319)).
<!--skill-flavor:check-baseline-lowering:start-->
- **`(pre-existing)` probable SDK defect** (JSON `class: "lowering"`): `compile` refuses it, while the [safe project loop](#the-safe-project-loop) keeps it as `LOWERING_NODE_KEPT`; do not edit around it and tell the user to report it at <https://github.com/UiPath/builder-sdk/issues>.
<!--skill-flavor:check-baseline-lowering:end-->
- **`CHECK_INCOMPLETE`**: fix the whole-flow refusal first (for example two Ends whose names produce one node id), even if pre-existing, then check again.

### Why three directories: inline agents

An inline agent is the `.flow` node plus `<source>/agent.json`, containing prompts, model, and run settings. Prompt edits affect only that file. Each compile writes its own `<source>/agent.json`; merge compares baseline and edited copies, applies only the delta to the project’s `agent.json`, and writes it beside the candidate:

```text
flow-merge: wrote Deployed.flow (12 nodes, 13 edges)
flow-merge: wrote <source-uuid>/agent.json (carries messages[0].content)
```

<!--skill-flavor:install-agent-files:start-->
In the safe loop, merge writes the `.flow` and carried agent files into the project. In a candidate-directory loop, install them with `cp -r "$WORK/candidate/."`. Fields not reproduced by the round trip (such as `maxIterations` or an agent-input `description`) retain project values.
<!--skill-flavor:install-agent-files:end-->

Merge warns, omits carrying, and refuses with `--strict` when:

- baseline and edited flows share one directory: the second compile overwrote baseline `agent.json`, so edits cannot be distinguished (`the edited <source>/agent.json differs from the original's ... The change is NOT carried`); use separate directories;
- an agent resource changed/removed cannot pair with a project resource because compile does not reproduce the resource node id or `resource.json` fields; make the change on the canvas;
- an older canvas save embeds prompts on the agent node; editing `agent.json` would not change runtime behavior; edit on the canvas.

Never copy `$WORK/edited/<source>/` into the project; it contains round-trip changes.

### Agent resources: added, changed, removed

An agent context index or tool is `<source>/resources/<dir>/resource.json`.

```text
flow-merge: wrote <source-uuid>/resources/<new-dir>/resource.json (carries added resource)
flow-merge: wrote <source-uuid>/resources/<dir>/resource.json (carries settings.resultCount)
flow-merge: remove <project>/<source-uuid>/resources/<dir> from the project: the edit removed this agent resource, and copying the candidate cannot delete it
flow-merge: wrote bindings_v2.json (connection and agent resource rows, re-derived as compile does)
```

<!--skill-flavor:resource-install:start-->
- Safe-loop `merge` writes added/changed resources; candidate installation uses `cp -r`; a changed resource keeps its original directory.
- A removed resource is not deleted automatically: delete every directory listed under `remove` (`Data.Removed` in `--output json`), or the agent retains it.
<!--skill-flavor:resource-install:end-->
- Keep a resource used by another project `.flow` (`flow-merge: kept <source>/resources/<dir>: <Other>.flow still references it`); do not delete it.
- In a Flow project, copy `bindings_v2.json` with the merged `.flow`; it contains re-derived connection and agent rows, so removed indexes or swapped connections are no longer declared.
- A stub connection label (`connection: "jira"`) resolves through edited-source `bindings.json`. Edit it to the connection id or fill `bindings.json`; merge writes the id and drops stub rows.

## Flows with draft nodes: let merge compile

<!--skill-flavor:draft-nodes:start-->
A canvas flow may contain draft nodes: connector without connection, empty required input, generic operation without object, `waitForEvent` without connection, Transform without collection, or decision without condition. A draft trigger or connector tool still must be finished. Decompile carries each saved definition and marks `{ draft: true }`; compile warns `⚠ [CONNECTOR_INPUT_MISSING] ... Written as a draft`. Leave drafts unless requested. Examples: decision becomes `.branch("decision1", undefined, (t) => ..., (e) => ..., { draft: true })`; Transform becomes `transform({ operations: [] })` with `{ draft: true }`. `waitForEvent`, Transform, and decision drafts require SDK 6.86.5+; older SDKs refuse with `BINDING_MISSING`, `TRANSFORM_COLLECTION_LITERAL`, or `EXPR_SYNTAX`.

Compile still stops for generic operation without object (`CONNECTOR_OBJECT_REQUIRED`), a draft written by you (no carried definition), or an untouched SDK-uncompilable node (`check --baseline` calls it a probable SDK defect). The [safe project loop](#the-safe-project-loop) runs no `compile`; `merge` compiles edited source and its derived baseline and tolerates drafts, so use it for these flows.

- A by-hand loop can use `merge <edited>.flow.ts --original <original>.flow --baseline-from <original>.flow` and skip both compiles (6.28.0+).
- An untouched draft is restored exactly with `[DRAFT_NODE_KEPT]`; the same applies inside an untouched subflow (6.44.4+; older SDKs take every subflow from edited source and refuse it).
- A changed draft gets normal compile refusal (`[BINDING_MISSING]`, `[CONNECTOR_INPUT_MISSING]`, or `[CONNECTOR_OBJECT_REQUIRED]`); finish or revert it.
- An untouched lowering failure is kept with `⚠ [LOWERING_NODE_KEPT] "<node>" is untouched, so the original node is kept as is, but the SDK cannot compile it (<CODE>)`; tell the user it is a probable defect and report it at <https://github.com/UiPath/builder-sdk/issues>. A changed/new failure is `✗ [<CODE>] "<node>" is changed or new`; revert or fix it. An untouched node failing because an edit elsewhere deleted a referenced step also stops the write. Require SDK 6.64.0+.
- Pass `--bindings` to `merge` as to `compile`; pass `--library` only to name a library other than the pulled one (with none, merge fetches through `uip`); `--strict` also works.
<!--skill-flavor:draft-nodes:end-->

## The generated pipeline

<!--skill-flavor:generated-pipeline:start-->
Without `--no-pipeline`, `decompile` writes `<Name>.pipeline.mjs` into `.flow-sdk/` beside the source. The safe loop needs none. With SDK older than 6.96.0, prefer this pipeline to capture the pristine baseline and chain four operations:

```bash
uip maestro flow decompile Deployed.flow -o .flow-sdk/Deployed.flow.ts
node .flow-sdk/Deployed.pipeline.mjs    # compiles the pristine baseline; stops there
# Edit .flow-sdk/Deployed.flow.ts narrowly; preserve existing step ids.
uip maestro flow check .flow-sdk/Deployed.flow.ts --source --baseline Deployed.flow
node .flow-sdk/Deployed.pipeline.mjs --strict   # compiles the edit, merges into .flow-sdk/Deployed.merged.flow
```

Pipeline compiles do not check; run [`check --baseline`](#check-only-what-you-changed-check---baseline) before the second run until no `(edited)` error remains. `--strict` reaches merge and refuses (exit 1, no file) instead of warning on unauthored round-trip changes (see [Merge warnings](#merge-warnings-what-the-round-trip-changed)). Read the refusal before the expected Node stack trace. Without `--strict`, warnings and a merged file are produced. If `grep -q STRICT .flow-sdk/Deployed.pipeline.mjs` fails, the old pipeline silently ignores `--strict`; use the hand loop with `merge --strict`.

Rerunning repeats compile and merge against the captured baseline. Before a later fresh decompile, remove artifacts and sidecars:
`[ ! -d .flow-sdk ] || find .flow-sdk -maxdepth 1 \( -name 'Deployed.baseline' -o -name 'Deployed.edited' -o -name 'Deployed.merged.flow' -o -name '????????-????-????-????-????????????' \) -exec rm -rf {} +`.
Pass `--no-pipeline` for the manual sequence. Keep pipeline artifacts outside the canonical project because every `.flow`, including hidden ones, is a deliverable; when source must remain in-project for sidecars, use the safe loop.
<!--skill-flavor:generated-pipeline:end-->

## A supplied source

<!--skill-flavor:supplied-source:start-->
When the task supplied `.flow-sdk/Deployed.flow.ts`, do not decompile; decompiling overwrites it. Compile its baseline before editing, then merge:

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

Install `.flow-sdk/Deployed.merged.flow` as [the same loop by hand](#the-same-loop-by-hand) says.
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

Keep candidates in `.flow-sdk/`; back up the project, replace the original with `.flow-sdk/Deployed.merged.flow`, copy every `<source>/` path merge reports, then validate the original as in [the safe project loop](#the-safe-project-loop).
<!--skill-flavor:hand-loop:end-->

The baseline must come from pristine decompiled source before edits; otherwise merge takes compiled reconstruction wholesale, including layout.

Decompile reconstructs branches, switches, loops, parallels, error/ref, and subflows while preserving node ids. Every SDK-authorable family uses its factory, including human tasks, agents/resources, published resources, queue items, AI patterns, document, conversational/voice, and connector event subscription steps. Recovered agents retain `source` UUIDs so `agent.json` resolves.

An agent context index, tool, or escalation retains identity through `nodeId`, `source`, or `label` in decompiled entries. Leave these unchanged. Removing them makes compile rename nodes `<agent>Context` / `Tool` / `Escalation` (then `2`, `3`, ...) and create a new directory, causing merge to drop the old node and add another. Do not add them to newly created or copied resources. `check` reports `FLOW_AGENT_RESOURCE_NODE_ID`, `FLOW_AGENT_RESOURCE_SOURCE_NOT_GUID`, and `FLOW_AGENT_RESOURCE_SOURCE_DUP`; older than 6.88.2 names them `INLINE_AGENT_RESOURCE_*`. Delete both `nodeId` and `source` from a copied entry. Require SDK 6.33.0+; older decompile omits these fields and compile renames nodes with new directories,
<!--skill-flavor:resource-ids-sdk-upgrade:start-->
so upgrade with
`npm install -g @uipath/maestro-builder-sdk@latest`.
<!--skill-flavor:resource-ids-sdk-upgrade:end-->

A step id is its name with non-letter/digit/`_` characters replaced by `_` (`a b` → `a_b`); compile never uniquifies it. Duplicate names give `DUP_STEP`; colliding ids (`a b`/`a_b` or trigger id) give `STEP_ID_COLLISION`; rename the step. Child-flow ids are checked separately and copied ids are prefixed `<caller>_<step>`. Route another path to an existing step with `.stepToRef('<name>')`. Require SDK 6.32.4+; older SDKs silently rename duplicates `<name>2`,
<!--skill-flavor:dup-step-sdk-upgrade:start-->
so upgrade with
`npm install -g @uipath/maestro-builder-sdk@latest`.
<!--skill-flavor:dup-step-sdk-upgrade:end-->

Unsupported factory types round-trip as `rawNode({ nodeType, version, manifest, inputs })`; preserve them unless requested and edit `inputs`, not the hoisted `…Definition` manifest. If all declared exits are wired, a multi-exit definition (for example `core.logic.agentic-switch`, with `case-<id>` per `inputs.criteria` plus `default`) becomes `.stepSwitch('<id>', rawNode(…), [{ value: 'case-returns', body: … }, …])`, one arm per port; add/remove arms when choices change. If only some exits are wired, it becomes `.step('<id>', rawNode(…))` on the main port (`default` for agentic switch), with other wired exits as `.stepToList('case-<id>', …)` and unwired exits unwired. `mock()` means the flow contains `core.logic.mock`; a missing definition alone lowers to `mock() /* TODO: unsupported node type … */`; leave it untouched and merge restores the original.

## Merge warnings: what the round trip changed

Merge prints `flow-merge: warning: …` for every unauthored change. With `--baseline`, it also compares the no-edit round trip to the original. Warnings may identify added/dropped/rewired nodes or edges, type changes, renamed switch-case or human-task outcome ids, and binding-row changes. If unintended, do not install the candidate; fix `.flow.ts` and merge again. An invalid merged edge handle makes `validate` refuse.

`the round trip appends End "<id>" after …` is benign: compile caps a path that simply stops and does not change behavior. A `.openTails()` flow gets it only after a human task; see [A path without an End stays open](#a-path-without-an-end-stays-open).

`agent "<id>" carries its prompts, model and settings on the node (embedded) …` means configuration is in `.flow`, not `<source>/agent.json`; merge preserves it and applies only node edits (input, output, label). Prompt/model/settings edits in source do not affect embedded agents; edit them on the canvas. `--strict` accepts input/output edits but refuses dropped/changed embedded configuration or a kept prompt still using `{{input.X}}` after input `X` was removed.
<!--skill-flavor:strict-merge:start-->
Pass `--strict` to refuse (exit 1, no file) instead of warn. The benign End warning never refuses. `--strict` requires `--baseline`: run `node .flow-sdk/<Name>.pipeline.mjs --strict` or add it to the hand-loop merge. If `uip maestro flow merge` rejects it, or the pipeline exits 2 with `--strict was asked for, but …`, use the globally installed SDK bin:

```bash
flow-sdk flow merge .flow-sdk/edited/Deployed.flow --original Deployed.flow \
  -o .flow-sdk/Deployed.merged.flow --baseline .flow-sdk/baseline/Deployed.flow --strict
```
<!--skill-flavor:strict-merge:end-->

## Scripts come back as functions

`decompile` prints script steps as named TypeScript functions after the flow and passes them by name. Edit the function body; its braces contain exactly the node script, so an untouched script recompiles byte-for-byte. A script reading `$metadata` gets `$metadata: FlowMetadata`; reading an unset key gives `FlowMetadata & Record<string, any>`. SDK older than 6.72.0 lacks `FlowMetadata` in `dist/api-index.md` and retains `script({ code: "…" })`, warning about `$metadata`. Apply [script.md](script.md#writing-the-script-as-a-function): runtime-only reads.

Scripts that cannot print as functions remain `script({ code: "…" })`, with one warning per script: `flow-decompile: warning: step "<id>": script kept as a string: <why>`. Reasons are unparsable body, TypeScript-only syntax, non-runtime name, trailing line comment, or module-loading error. This is informational; `--strict` does not make it an error. Edit the string. To retain all strings, run `uip maestro flow decompile <file> -o <file>.flow.ts --scripts string`. SDK 6.57.0+ is required; older `uip` refuses the option and names the version to install.

## A Case-only variable type

Studio Web or older SDKs may carry global typed `date`, `datetime`, `float`, `double`, or `jsonSchema`; `decompile` warns once per variable.

- `date`/`datetime`: do nothing. Source prints `types.string` and warns recompilation writes `"type":"string"`; merge works. Without `--baseline-from`, merged type is string; with it, untouched variables retain their type. Runtime is unchanged because `flow pack` writes dates as plain strings.
- `float`/`double`/`jsonSchema`: retype in the same round or compile/merge stops with `DECLARATION_TYPE_NOT_FLOW`. Use the warning’s type (`types.number`; for `jsonSchema`, `types.object` or `types.array` with `{ schema }`).

## The file's schema version comes back out

`decompile` emits `.schemaVersion("<the file's version>")` as the chain’s first line, preserving file version rather than the SDK floor. Most deployed flows are `1.8`; writable band is `1.6`–`1.10`. Leave it unless intentionally retargeting. `check` warns outside the `1.9` floor: `SCHEMA_VERSION_ABOVE_FLOOR` means a lower-pinned reader refuses it; `SCHEMA_VERSION_BELOW_FLOOR` means readers migrate it on open. Use `uip maestro flow migrate`, not this call, to change versions.

## Designer shapes decompile keeps

Leave decompiled shapes unchanged. SDK 6.44.0+ is required; older versions write `js\`[object Object]\`` for envelopes, drop fork arms and `variable` rows with `has no spelling` / `cannot write back`, and compile refuses,
<!--skill-flavor:envelope-sdk-upgrade:start-->
— upgrade with `npm install -g @uipath/maestro-builder-sdk@latest`.
<!--skill-flavor:envelope-sdk-upgrade:end-->

Preserved shapes include:

- decision/switch conditions as `jsExpression` envelopes or `=js: …`;
- quick-form asked-field `variable` ([hitl.md](hitl.md));
- `{ fork }`, `.stepToRef` arms, and pass-through `rawNode` merge ([parallel-merge.md](parallel-merge.md));
- `core.logic.loop@1.0` `output`/`loopBack` handles through its carried definition;
- subflow reads of its Start node as `input('<name>')` and subflow `.onError()`.

Warnings are `flow-decompile: warning: …`; `--strict` turns each into an error. Edit `.flow` JSON directly only for these warned cases; otherwise edit through merge:

- **Unreachable node:** source omits it and marks `// TODO: node "<id>" … is not reachable`; recompilation drops it. Connect it in `.flow` first or edit its JSON directly.
- **Unsupported exact `(type, typeVersion)` with no file definition:** source omits `{ version }`, so edited nodes compile at SDK default; `merge --baseline` preserves untouched file versions but warns edited nodes `node "<id>" moved <type>@<old> -> <new>`. Edit JSON directly or tell the user. A type bundled at no version (connector, published process, agent) keeps its pin. When the file has a definition, decompile copies it to a `const`, passes it to `.definitions([...])`, and preserves the pin; leave both intact or compile refuses and lists resolvable versions (registered families first report `NODE_VERSION_UNREGISTERED`). For carried definitions whose inputs differ from the SDK factory, warning is `node "<id>" keeps <type>@<version> from the file's definitions[]; its inputs differ from <sdk-version> (<fields>)`; edit merged JSON if that node is the target. `rawNode` cannot route a human-task outcome.
- **File version below `1.6`:** source omits `.schemaVersion()`, marks `// TODO:`, and recompilation writes `1.9`; migrate first or merge into the original, which preserves its declared version.
- **Unspellable edge:** for example two edges leave one port while one path stops without successor/End. Other fan-outs become `.parallel` ([parallel-merge.md](parallel-merge.md)); converging arms use `.stepToRef(<step>)` (SDK 6.44.0+), and arms ending in End/Terminate use a `<node>Fork` with all arms ending (SDK 6.46.6+). An arm with a step before Terminate (`TERMINATE_NOT_ARM_HEAD`) or fan-out inside a loop whose arms use `.break()`/`.continue()` remains behind `/* TODO: unstructured fan-out … */`. Warning names `<source>@<port> -> <target>@<port>` and source marks `/* TODO: edge(s) … are NOT in this source */` or a top `// TODO: edge …`; recompilation drops it. Edit JSON directly if touching it.
- **Unexpressible context-index `context: [...]` setting:** retrieval settings (mode, query, threshold, result count, file extension) come from `<agent source>/resources/<source>/resource.json`; retain that folder beside the `.flow`. Static plain-text query, agent-argument query, disabled deeprag citations, and folder-path prefix may lack fields. Warning names the setting; compiled output writes SDK values beside `-o`; merge does not update the project copy. Do not copy it over; if already done, tell the user to reset it in Studio Web.
- **Fire-and-forget process output schema:** `agenticProcess()` refuses `returns` beside `completion: 'fire-and-forget'`, so source omits fields and warns. Require SDK 6.44.0+; older decompile writes `returns` and compile refuses,
<!--skill-flavor:fire-and-forget-sdk-upgrade:start-->
— upgrade with `npm install -g @uipath/maestro-builder-sdk@latest`.
<!--skill-flavor:fire-and-forget-sdk-upgrade:end-->
Recompile drops the schema while merge preserves the original definition row. To read output, use `completion: 'wait'` and declare `returns`.

Pin added steps with `{ version }` used by another non-warned node of that type. If all nodes warned, leave unpinned; if none retains the file version, merge drops its definition silently. An added End needs a fresh name; see [A path without an End stays open](#a-path-without-an-end-stays-open).

Validate only the installed merged file as in [the safe project loop](#the-safe-project-loop), never an intermediate edited compile. Do not run `uip maestro flow format` on the merged file; it discards author layout.

Decompiled source carries `.layout({ nodes })`; keep it. Added steps have no entry and merge places them by neighbours. To choose a spot, add `<step>: at(x, y)` beside neighbours (`import { at } from '@uipath/maestro-builder-sdk'`), avoiding any x where `(x − 256)` is a multiple of 288 on y = 144 or 304; these are compile placeholders. Containers may still move it; accept the result. At root, source position/size changes do nothing for existing nodes because merge uses original layout and shifts/grows for additions. For other changes edit `layout.nodes.<id>.position`/`.size` in merged `.flow`; if no `layout.nodes` map, edit the node’s `ui`. Subflow entries apply only when that subflow changed; otherwise original subflow remains (6.44.4+; older SDK takes every subflow from edited compile),
<!--skill-flavor:subflow-layout-sdk-upgrade:start-->
so upgrade with
`npm install -g @uipath/maestro-builder-sdk@latest`.
<!--skill-flavor:subflow-layout-sdk-upgrade:end-->
Grid and rules: [`operate.md`](operate.md#lay-out-from-source-instead-layout-at-dim).

## A path without an End stays open

Designer or `uip maestro flow node add` flows may end at a step without an End. `decompile` emits `.openTails()` near the top of the root and every subflow chain; leave it. It preserves open paths; removing it adds End nodes. Adding after an open tail makes the new step the open tail. To return outputs, end with `.return({ ... })`; an open path maps no outputs. Human-task exits always receive an End.

Name added Ends uniquely and use existing End `{ version }`: `.return({ ... }, { name: 'endSummary', version: '<END_VERSION>' })`. `name: 'end'` collides with an unnamed existing End, which becomes `end2` without warning.

## Split (`$ref`) artifacts

A deployed `.flow` may split definitions, layout, or subflows into sibling files, such as `"definitions": { "$ref": "./definitions.json" }`. Point decompile at the main file; it resolves sidecars. Do not inline or edit sidecars first. Only relative paths resolve. Absolute paths, Windows drive letters, protocol URIs (`https://`, `file:///`), and traversal above the referencing root are refused because `.flow` is untrusted input. Same-document pointers (`{"$ref": "#/definitions/…"}`) remain. Missing/unreadable targets error by filename.

Compile always writes one file; write-through splitting is unsupported. Recompiled output contains sidecar content inline and no `$ref`; this is correct.