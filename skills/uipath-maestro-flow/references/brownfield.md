# True-brownfield decompile, edit, and merge

Use this for an existing `.flow` unless the task supplied its `.flow.ts`; an earlier-turn `.flow.ts` is not supplied because the canvas may have changed the `.flow`.

<!--skill-flavor:fresh-decompile-cleanup:start-->
Decompile fresh, after deleting any `.flow` an older loop left under `.flow-sdk/`
([The generated pipeline](#the-generated-pipeline)).

<!--skill-flavor:fresh-decompile-cleanup:end-->

Never hand-transcribe the graph. Decompile to builder source, edit that source, and merge only its delta into the original.

An edit that adds a [pattern](author.md#patterns) (review gate, triage, batch loop, chat or voice front door, or panel of agents) reads its guide first and inserts only what the flow lacks, per "Adapting it"; inserting a pattern is still a narrow edit through this loop. A pattern the canvas inserted arrives unfinished; finishing it means: replace each `core.logic.mock` labelled "(replace with …)" with the real node, rewrite every `PLACEHOLDER -` prompt for the request, and do the setup sticky note's tasks. Put builder-impossible items (for example attaching a tool to a voice agent) under Open questions. Preserve every other inserted step, port, and name.

## The safe project loop

<!--skill-flavor:safe-project-loop:start-->
Run it from the project folder `Solution/Deployed/`, the source in
`.flow-sdk/`. `decompile` stamps the source's first line, and `merge` takes
that source: it compiles it, derives the baseline from the original in memory,
and writes the merged flow, and every agent file it carries, over the original.
It writes no compiled working artifact, so the project keeps exactly one
`.flow` file, which product validation needs when it discovers it recursively.

```bash
uip maestro flow decompile Deployed.flow -o .flow-sdk/Deployed.flow.ts --no-pipeline
# Edit .flow-sdk/Deployed.flow.ts narrowly; preserve existing step ids and its first line.
# Leave added steps out of .layout(...): merge places them (builder-sdk#1320).
# Check against the original until no (edited) error is left:
uip maestro flow check .flow-sdk/Deployed.flow.ts --source --baseline Deployed.flow
# Merge only a stamped source (no stamp: the SDK is too old, below), then validate:
( head -n 1 .flow-sdk/Deployed.flow.ts | grep -q '^// @decompiled-from ' \
    || { echo "no stamp: SDK older than 6.96.0, the edit was NOT merged" >&2; exit 1; }
  uip maestro flow merge .flow-sdk/Deployed.flow.ts --original Deployed.flow ) \
  && uip maestro flow validate Deployed.flow --output json
# Then delete each path merge listed as `flow-merge: remove <path> ...`.
```

For example, after an edit to one script step:

```text
flow-merge: wrote Deployed.flow (10 nodes, 9 edges)
flow-merge: compiled Deployed.flow.ts and derived the baseline from Deployed.flow in memory; no intermediate file written
flow-merge: restamped Deployed.flow.ts for the merged Deployed.flow, so it merges again after the next edit
```

Only `merge` writes the `.flow`; never write, patch, or copy only a change into it. Merge may renumber edges (`edge_0`, `edge_1`, ...), reorder nodes, add default fields, or move original nodes right/down; accept these and follow [merge warnings](#merge-warnings-what-the-round-trip-changed).

A refused merge writes nothing, so there is nothing to restore. A merge that
fails after it printed `flow-merge: wrote Deployed.flow` (an I/O error on an
agent file or `bindings_v2.json`) is not a refusal: the `.flow` already holds
the edit, the agent files may not, and the source is not restamped, so the
next merge refuses with `MERGE_ORIGINAL_CHANGED`. Decompile again and reapply
the edit, or `git checkout` the project
([builder-sdk#2043](https://github.com/UiPath/builder-sdk/issues/2043)).
If validate fails after a merge, fix `.flow-sdk/Deployed.flow.ts` and run `check` and
`merge` again: merge restamped the source, so the same command merges the fix.
To drop the edit instead, revert it in the source and merge again. The result
is equivalent to the original, not byte-identical (edges renumbered, nodes
moved for the edit stay moved); for a byte-exact undo of a project under
version control, `git checkout -- Deployed.flow`.

### The stamp, and when merge refuses

The first line is `// @decompiled-from Deployed.flow sha256:<64 hex> scripts=function`; `sha256` is the `decompile` source digest and the remainder records decompilation. `merge` decompiles the original the same way and compares, so it knows the baseline it derives is the source you started from.

- `MERGE_ORIGINAL_CHANGED`: the `.flow` changed after decompile (a canvas save, another merge, a moved node); merging would revert that change, so nothing was written. Decompile again and redo the edit; never alter the first line.
- `MERGE_SOURCE_STAMP_UNREADABLE`: the first line was edited; decompile again.
- A split original (`$ref` part files) is written as one file; delete every part under `remove`.
- After merge, `merge` rewrites the source's first line for the merged `.flow`; further edits use the same command.
- Needs `@uipath/maestro-builder-sdk` 6.96.0 or later. An older `decompile`
  writes no first line, and an older `merge` writes `merged.flow` beside you and
  leaves the original unchanged while every later check passes. So the loop
  merges only a stamped source and otherwise exits 1 with `no stamp: ... NOT
  merged`: upgrade with `npm install -g @uipath/maestro-builder-sdk@latest`
  and decompile again.
<!--skill-flavor:safe-project-loop:end-->

Wherever you compile a baseline yourself ([a supplied source](#a-supplied-source)), compile it before the edit, never after:
merge diffs edited against it, so a baseline of the edited source drops your change.

With an edited `.flow.ts` and `--baseline-from`, `merge` checks the edited source and refuses an error in a changed node/subflow (`N error(s) in nodes merge takes from the edited flow`) or an unplaceable error introduced by the edit. An untouched-node/subflow error prints `DRAFT_NODE_KEPT` and the original is kept; an untouched node the SDK cannot compile is kept as saved too, printing `LOWERING_NODE_KEPT` (probable SDK defect; tell the user; 6.64.0 or later); an unplaceable finding also reported by the original round trip is `CHECK_FINDING_UNPLACED`. Fix findings in edited nodes. Require `@uipath/maestro-builder-sdk` 6.44.4 or later; older SDKs refuse writes for any unplaceable error on an untouched root node,
<!--skill-flavor:merge-check-sdk-upgrade:start-->
so upgrade with `npm install -g @uipath/maestro-builder-sdk@latest`.
<!--skill-flavor:merge-check-sdk-upgrade:end-->

Do not leave a compiled `.flow` below the project directory (an earlier
`*.merged.flow`, `baseline/` or `edited/`): the project validator treats every
`.flow` there, hidden folders included, as a deliverable.

### Check only what you changed: `check --baseline`

`compile` does not run `check`: it writes any flow it can serialize. So run
`check` after each edit, before the merge, and treat its errors as the gate.
Pass the original `.flow` (not a compiled baseline) as `--baseline`, and each
finding says whether your edit caused it. In emit-only mode `check` refuses:
skip it there, `validate` is the gate.

Require `@uipath/maestro-builder-sdk` 6.64.0 or later. If baseline compile stops on a check code (for example pre-existing `HTTP_READ_WITHOUT_RETURNS`), `uip` reports `--baseline on flow check needs @uipath/maestro-builder-sdk >= 6.64.0; found <version>`, or older `uip` reports `error: unknown option '--baseline'`, the SDK is too old,
<!--skill-flavor:check-baseline-sdk-upgrade:start-->
so upgrade with `npm install -g @uipath/maestro-builder-sdk@latest`.
<!--skill-flavor:check-baseline-sdk-upgrade:end-->
<!--skill-flavor:check-baseline-uip-version:start-->
For `unknown option '--baseline'`, check the SDK with `npm ls -g @uipath/maestro-builder-sdk` or the project's `node_modules`. Below 6.64.0, upgrade it. With 6.64.0+ and the same error, `uip` is too old (1.205.0 is): run the same check through the SDK's own bin, which takes the same flags and exits the same way:
`flow-sdk flow check .flow-sdk/Deployed.flow.ts --source --baseline Deployed.flow` (global SDK), or `npx --no-install flow-sdk flow check .flow-sdk/Deployed.flow.ts --source --baseline Deployed.flow` when the SDK is in the project's `node_modules`.
The bin finds the connector library itself (`--library`, `FLOW_SDK_LIBRARY_JSON`, or the cache `uip maestro registry pull` fills), not through `uip`, so a library only `uip` passes is not used and connector findings (`CONNECTOR_INPUT`, `LOOKUP_UNRESOLVED`) can be missing. If you used a library other than the pulled one, pass it: `--library <dir>`.
<!--skill-flavor:check-baseline-uip-version:end-->

```text
$ uip maestro flow check <Name>.flow.ts --source --baseline <original>.flow
✗ [UNKNOWN_REF] Reference to undeclared variable/step "lookup" in "report". (edited)
⚠ [HTTP_READ_WITHOUT_RETURNS] ... (pre-existing, not counted)
⚠ [CONNECTOR_INPUT] Connector step "notify": ... unknown input "designerOnly". ... (pre-existing)
  This node is unchanged from the baseline, so this is probably an SDK defect: ...

1 error(s) in edited nodes, 1 pre-existing SDK defect(s), 1 pre-existing warning(s)
```

- **`(edited)`** (JSON `origin: "edited"`): fix it, including an untouched node broken by the edit (like `report` above, which reads the deleted `lookup` step). Exit code is 1 only while one is left.
- **`(pre-existing, not counted)`**: leave it unless requested; deployed HTTP nodes without body schemas can produce `HTTP_READ_WITHOUT_RETURNS` ([builder-sdk#1319](https://github.com/UiPath/builder-sdk/issues/1319)).
<!--skill-flavor:check-baseline-lowering:start-->
- **`(pre-existing)` worded as a probable SDK defect** (JSON
  `class: "lowering"`): `compile` refuses that node, so the baseline compile
  of [a supplied source](#a-supplied-source) stops on it. Do not edit the node to get around it. The
  [safe project loop](#the-safe-project-loop)'s merge compiles without
  stopping and keeps the node as saved (`LOWERING_NODE_KEPT`); tell the user it
  is a probable SDK defect to report at
  <https://github.com/UiPath/builder-sdk/issues>.
<!--skill-flavor:check-baseline-lowering:end-->
- **`CHECK_INCOMPLETE`**: fix the whole-flow refusal first (for example two Ends whose names produce one node id), even if pre-existing, then check again.

### Inline agents: merge carries `agent.json`

An inline agent is two files: the node in the `.flow`, and its prompts, model
and run settings in `<source>/agent.json` beside it. An edit to a prompt
changes only that file. Merge compares the baseline's copy with the edited
copy, applies only your change to the project's `agent.json`, and writes the
result beside the merged `.flow`:

```text
flow-merge: wrote Deployed.flow (12 nodes, 13 edges)
flow-merge: wrote <source-uuid>/agent.json (carries messages[0].content)
```

To add an instruction to a prompt, write it as a new line. Keep every existing
line exactly as it is: add no words to it, and do not re-wrap it.

<!--skill-flavor:install-agent-files:start-->
Merge writes the `.flow` and every agent file it carried into the project;
there is nothing to copy. Fields the round trip does not reproduce (such as
`maxIterations`, or a `description` on an agent input) keep the project's values.
<!--skill-flavor:install-agent-files:end-->

Merge warns, omits carrying, and refuses with `--strict` when:

- a `--baseline` file and the edited flow were compiled into ONE directory. The
  second compile overwrote the baseline's `agent.json`, so merge cannot tell
  your edit from the round trip's own changes (`the edited <source>/agent.json
  differs from the original's ... The change is NOT carried`). Keep a baseline
  file in a directory of its own, as [a supplied source](#a-supplied-source) does.
- an agent resource changed/removed cannot pair with a project resource because the canvas gave its node an id compile does not reproduce and its `resource.json` has fields compile does not write; make the change on the canvas;
- with an SDK older than 6.117.2, an older canvas save embeds prompts on the agent node, so an `agent.json` edit would not change runtime behavior; edit on the canvas. From 6.117.2, merge carries a prompt, model or settings edit onto such a node; see [the embedded-agent warning](#merge-warnings-what-the-round-trip-changed).

Never copy a compiled `<source>/` directory into the project by hand: it
carries the round trip's changes along with yours.

### Agent resources: added, changed, removed

An agent context index or tool is `<source>/resources/<dir>/resource.json`.

```text
flow-merge: wrote <source-uuid>/resources/<new-dir>/resource.json (carries added resource)
flow-merge: wrote <source-uuid>/resources/<dir>/resource.json (carries settings.resultCount)
flow-merge: remove <project>/<source-uuid>/resources/<dir> from the project: the edit removed this agent resource, and copying the candidate cannot delete it
flow-merge: wrote bindings_v2.json (connection and agent resource rows, re-derived as compile does)
```

<!--skill-flavor:resource-install:start-->
- Merge writes an added or changed resource into the project. A changed one
  keeps its original directory.
- A removed resource is not deleted automatically: delete every directory listed under `remove` (`Data.Removed` in `--output json`), or the agent retains it.
<!--skill-flavor:resource-install:end-->
- Keep a resource used by another project `.flow` (`flow-merge: kept <source>/resources/<dir>: <Other>.flow still references it`); do not delete it.
- In a Flow project, copy `bindings_v2.json` with the merged `.flow`; it contains re-derived connection and agent rows, so removed indexes or swapped connections are no longer declared.
- A stub connection label (`connection: "jira"`) resolves through edited-source `bindings.json`. Edit it to the connection id or fill `bindings.json`; merge writes the id and drops stub rows.

### Swapping a connection

A swap edits only the step's `connection:` and `folder:`:

1. `uip is connections list <CONNECTOR_KEY> --all-folders --output json`: take the requested connection's `Id` and `FolderKey`. A folder name or several matches: [where both values come from](bindings.md#where-both-values-come-from).
2. Decompile, set that step's `connection:` to the `Id` and `folder:` to the `FolderKey`, then check, merge and validate as in [the safe project loop](#the-safe-project-loop). Merge rewrites the step's `bindings[]` rows and `bindings_v2.json`.
3. An input holding an id looked up through the old connection (a Slack channel, a Jira issue type) may not exist behind the new one: re-run `uip maestro registry prepare <CONNECTOR_KEY> --action <ACTION> --connection-id <ID>`, picking each such value again by name (`--resolve <field>:name=<display name>`, [connector-params.md](connector-params.md#resolving-connection-scoped-reference-values)); the decompiled source holds only the old id.

<!--skill-flavor:swap-connection-finish:start-->
No other step: do not read solution resource files or compile a scratch copy.
<!--skill-flavor:swap-connection-finish:end-->

## Flows with draft nodes: let merge compile

<!--skill-flavor:draft-nodes:start-->
A canvas flow may contain draft nodes: connector without connection, empty required input, generic operation without object, `waitForEvent` without connection, Transform without collection, or decision without condition. A draft trigger or connector tool still must be finished. Decompile carries each saved definition and marks `{ draft: true }`; compile warns `⚠ [CONNECTOR_INPUT_MISSING] ... Written as a draft`. Leave drafts unless requested. Examples: decision becomes `.branch("decision1", undefined, (t) => ..., (e) => ..., { draft: true })`; Transform becomes `transform({ operations: [] })` with `{ draft: true }`. `waitForEvent`, Transform, and decision drafts require SDK 6.86.5+; older SDKs refuse with `BINDING_MISSING`, `TRANSFORM_COLLECTION_LITERAL`, or `EXPR_SYNTAX`.

Three cases still stop `compile`, and with it
the baseline compile of [a supplied source](#a-supplied-source): a generic operation with no object
(`CONNECTOR_OBJECT_REQUIRED`), a draft you wrote yourself (no carried
definition), and an untouched node the SDK cannot compile (`check --baseline`
prints it as a probable SDK defect). The [safe project loop](#the-safe-project-loop)
runs no `compile`: merge compiles the edited source and the baseline it derives
itself, and both compiles tolerate drafts.

- For a supplied source whose baseline compile stops, pass
  `--baseline-from <original>.flow` to its merge in place of `--baseline`, and
  merge runs both compiles itself (6.28.0 or later).
- An untouched draft is restored exactly with `[DRAFT_NODE_KEPT]`; the same applies inside an untouched subflow (6.44.4+; older SDKs take every subflow from edited source and refuse it).
- A changed draft gets normal compile refusal (`[BINDING_MISSING]`, `[CONNECTOR_INPUT_MISSING]`, or `[CONNECTOR_OBJECT_REQUIRED]`); finish or revert it.
- An untouched lowering failure is kept with `⚠ [LOWERING_NODE_KEPT] "<node>" is untouched, so the original node is kept as is, but the SDK cannot compile it (<CODE>)`; tell the user it is a probable SDK defect that should be filed at <https://github.com/UiPath/builder-sdk/issues>. A changed/new failure is `✗ [<CODE>] "<node>" is changed or new`; revert or fix it. An untouched node failing because an edit elsewhere deleted a referenced step also stops the write. Require SDK 6.64.0+.
- Pass `--bindings` to `merge` as to `compile`; pass `--library` only to name a library other than the pulled one (with none, merge fetches through `uip`); `--strict` also works.
<!--skill-flavor:draft-nodes:end-->

## The generated pipeline

<!--skill-flavor:generated-pipeline:start-->
Pass `--no-pipeline` to `decompile`. Without it, `decompile` also writes
`.flow-sdk/<Name>.pipeline.mjs`, a helper for the older loop that compiled a
baseline and an edited copy and merged them into `.flow-sdk/<Name>.merged.flow`.
The safe project loop needs none of it. Do not run it: the `.flow` files it
writes under `.flow-sdk/` are extra deliverables to the project validator.
Delete any it, or an earlier turn, left there before you decompile:
`[ ! -d .flow-sdk ] || find .flow-sdk -maxdepth 1 \( -name 'Deployed.baseline' -o -name 'Deployed.edited' -o -name baseline -o -name edited -o -name 'Deployed.merged.flow' -o -name '????????-????-????-????-????????????' \) -exec rm -rf {} +`.
<!--skill-flavor:generated-pipeline:end-->

## A supplied source

<!--skill-flavor:supplied-source:start-->
When the task supplied `.flow-sdk/Deployed.flow.ts`, do not decompile: it
overwrites that source. A supplied source has no stamp, so compile its baseline
before the edit, outside the project, and pass it to merge:

```bash
[ ! -d .flow-sdk ] || find .flow-sdk -maxdepth 1 \( -name 'Deployed.baseline' -o -name 'Deployed.edited' -o -name baseline -o -name edited -o -name 'Deployed.merged.flow' -o -name '????????-????-????-????-????????????' \) -exec rm -rf {} +
rm -rf /tmp/flow-baseline-Deployed && mkdir -p /tmp/flow-baseline-Deployed
uip maestro flow compile .flow-sdk/Deployed.flow.ts -o /tmp/flow-baseline-Deployed/Deployed.flow
# Edit .flow-sdk/Deployed.flow.ts narrowly; preserve existing step ids.
uip maestro flow check .flow-sdk/Deployed.flow.ts --source --baseline Deployed.flow
uip maestro flow merge .flow-sdk/Deployed.flow.ts --original Deployed.flow \
  --baseline /tmp/flow-baseline-Deployed/Deployed.flow -o Deployed.flow \
  && uip maestro flow validate Deployed.flow --output json && rm -rf /tmp/flow-baseline-Deployed
```

Merge compiles the edited source itself and writes over the original, agent
files included, as in [the safe project loop](#the-safe-project-loop). The
baseline directory is a fixed path, so it survives the separate shell calls
before and after the edit. Keep it outside the project: a `.flow` there is a
second deliverable.
<!--skill-flavor:supplied-source:end-->

## What decompile reconstructs

Decompile reconstructs branches, switches, loops, parallels, error/ref, and subflows while preserving node ids. Every SDK-authorable family uses its factory, including human tasks, agents/resources, published resources, queue items, AI patterns, document, conversational/voice, and connector event subscription steps. Recovered agents retain `source` UUIDs so `agent.json` resolves.

An agent context index, tool, or escalation retains identity through `nodeId` (the resource node's id), `source` (its `resources/<source>/` directory), or `label` (a context index's canvas label) in decompiled entries. Leave these unchanged. Removing them makes compile rename nodes `<agent>Context` / `Tool` / `Escalation` (then `2`, `3`, ...) and create a new directory, causing merge to drop the old node and add another. Do not add them to newly created or copied resources. `check` reports `FLOW_AGENT_RESOURCE_NODE_ID` (blank or duplicate `nodeId`), `FLOW_AGENT_RESOURCE_SOURCE_NOT_GUID` (non-uuid `source`), and `FLOW_AGENT_RESOURCE_SOURCE_DUP` (two resources on one agent share `source`: both would write one `resource.json`); older than 6.88.2 names them `INLINE_AGENT_RESOURCE_*`. Delete both `nodeId` and `source` from a copied entry. Require SDK 6.33.0+; older decompile omits these fields and compile renames nodes with new directories,
<!--skill-flavor:resource-ids-sdk-upgrade:start-->
so upgrade with
`npm install -g @uipath/maestro-builder-sdk@latest`.
<!--skill-flavor:resource-ids-sdk-upgrade:end-->

A step id is its name with non-letter/digit/`_` characters replaced by `_` (`a b` → `a_b`); compile never uniquifies it. Duplicate names give `DUP_STEP`; colliding ids (`a b`/`a_b` or trigger id) give `STEP_ID_COLLISION`; give the new step a name of its own. Child-flow ids are checked separately and copied ids are prefixed `<caller>_<step>`. Route another path to an existing step with `.stepToRef('<name>')`. Require SDK 6.32.4+; older SDKs silently rename duplicates `<name>2`,
<!--skill-flavor:dup-step-sdk-upgrade:start-->
so upgrade with
`npm install -g @uipath/maestro-builder-sdk@latest`.
<!--skill-flavor:dup-step-sdk-upgrade:end-->

Unsupported factory types round-trip as `rawNode({ nodeType, version, manifest, inputs })`; preserve them unless requested and edit `inputs`, not the hoisted `…Definition` manifest. If all declared exits are wired, a multi-exit definition (for example `core.logic.agentic-switch`, with `case-<id>` per `inputs.criteria` plus `default`) becomes `.stepSwitch('<id>', rawNode(…), [{ value: 'case-returns', body: … }, …])`, one arm per port; add/remove arms when choices change. If only some exits are wired, it becomes `.step('<id>', rawNode(…))` on the main port (`default` for agentic switch), with other wired exits as `.stepToList('case-<id>', …)` and unwired exits unwired. `mock()` means the flow really contains `core.logic.mock`, except one case: a node whose definition is missing from the file lowers to `mock() /* TODO: unsupported node type … */`; leave it untouched and merge restores the original.

## Merge warnings: what the round trip changed

Merge prints `flow-merge: warning: …` for each change the merged file gets
although you did not make it. It also compares the baseline (the round trip
with no edit) with the original. For example:

```
flow-merge: warning: the round trip rewires logFailure1@success from forEachItem1@continue to callApi1ErrorEnd@input; merge will write the new target.
flow-merge: warning: the merged edge route1@case-case_1 -> review1@input leaves handle "case-case_1", which node "route1" (core.logic.switch) does not declare …
```

- Each warning names a change you did not author: a node or edge added,
  dropped or rewired, a node's type changed, a switch case id or human-task
  outcome id renamed, or a binding row added, dropped or duplicated. Merge has
  already written it: if the spot is one you did not mean to change, fix the
  `.flow.ts` and merge again, or merge with `--strict` to refuse before
  writing. A warning about a merged edge's handle means `validate` will refuse
  the merged file.

`node "<id>" spells <bindings.NAME> but the original has no binding row for it, … merge writes the row …` is a repair, not a failure: the original lacked a row Studio Web needs to publish. Keep it; `validate` is the check.

`the round trip appends End "<id>" after …` is benign: compile caps a path that simply stops and does not change behavior. A `.openTails()` flow gets it only after a human task; see [A path without an End stays open](#a-path-without-an-end-stays-open).

`agent "<id>" carries its prompts, model and settings on the node (embedded) …` means configuration is in `.flow`, not `<source>/agent.json`; merge keeps it embedded and applies node edits (input, output, label).
From SDK 6.117.2, merge also writes a prompt, model or settings edit to an embedded agent onto the node and prints `flow-merge: carried the agent.json edit onto embedded agent "<id>"`.
If merge prints no such line for your edit, the SDK does not carry it; edit it on the canvas.
Deleting a setting from the source is carried as its default value when compile writes one (for example `maxTokenPerResponse` becomes 16384); to keep a value, leave the setting in the source.
A deletion merge cannot carry, such as `model`, warns `NOT carried`, and the node keeps its value.
`--strict` refuses an edit merge cannot carry onto the node, a merged node that drops or changes configuration you did not edit, a prompt you edited that uses a new `{{input.X}}` the node does not declare, or a prompt that still uses an input your edit removed.
An undeclared placeholder the original prompt already had is not refused.
<!--skill-flavor:strict-merge:start-->
- Pass `--strict` to make merge refuse (exit 1, no file written) instead of
  warning. The benign End line never refuses. Every merge on this page has a
  baseline, which `--strict` needs: `uip maestro flow merge
  .flow-sdk/Deployed.flow.ts --original Deployed.flow --strict`. If `uip`
  rejects `--strict`, run the same command as `flow-sdk flow merge`, the
  globally installed SDK's bin.
<!--skill-flavor:strict-merge:end-->

## Scripts come back as functions

`decompile` prints script steps as named TypeScript functions after the flow and passes them by name. Edit the function body; its braces contain exactly the node script, so an untouched script recompiles byte-for-byte. A script reading `$metadata` gets `$metadata: FlowMetadata`; reading a key outside the five engine keys gives `FlowMetadata & Record<string, any>`. SDK older than 6.72.0 lacks `FlowMetadata` in `dist/api-index.md` and keeps a `$metadata`-reading script as `script({ code: "…" })`, warning about `$metadata`. Apply [script.md](script.md#writing-the-script-as-a-function): the function may read only what the script runtime has.

Scripts that cannot print as functions remain `script({ code: "…" })`, with one warning per script: `flow-decompile: warning: step "<id>": script kept as a string: <why>`. Reasons are unparsable body, TypeScript-only syntax, non-runtime name, trailing line comment, or module-loading error. This is informational; `--strict` does not make it an error. Edit the string. To print every script as a string, run `uip maestro flow decompile <file> -o <file>.flow.ts --scripts string`. With an SDK older than 6.57.0, `uip` refuses the option and names the version to install. Needs SDK 6.57.0+ (its `dist/api-index.md` lists `ScriptValue`); an older SDK's decompile prints every script as `script({ code })`.

## A Case-only variable type

A `.flow` written by Studio Web or an older SDK can carry a global typed `date`, `datetime`, `float`, `double` or `jsonSchema`.
None of them needs a retype: decompile prints a Flow type, and compile and merge take it.

- **`float` / `double`: nothing to do.** Decompile prints the file's own width, `{ type: types.number, format: "float" }` or `format: "double"`, and the recompile writes that type back (`"type":"float"` / `"type":"double"`). No warning: nothing changes. Keep the `format` as decompile printed it when you edit the variable, and never change `"float"` to `"double"`: `flow pack` writes it into the entry point's schema (`"format":"float"` / `"format":"double"`).
- **`date` / `datetime`: nothing to do.** Decompile prints `types.string` and warns `... The source declares it types.string, so a recompile writes "type":"string" in its place`. `flow pack` writes a date as a plain string either way.
- **`jsonSchema`: nothing to do.** Decompile prints `types.object` (or `types.array` when the schema is an array's) with the file's schema in `{ schema }`, and warns that a recompile writes `"type":"object"`. The engine reads both as JSON.

Merge goes through for all five and keeps an untouched variable's own type.
Needs `@uipath/maestro-builder-sdk` 6.107.0 or later (its `dist/api-index.md` lists `NumberFormat`); an older SDK keeps `types.float` / `types.double` / `types.jsonSchema` instead, and `compile`/`merge` stop with `DECLARATION_TYPE_NOT_FLOW` until you retype that declaration (`types.number`; for `jsonSchema`, `types.object` or `types.array` with `{ schema }`).

## The file's schema version comes back out

`decompile` emits `.schemaVersion("<the file's version>")` as the chain's first line, preserving file version rather than the SDK floor. Most deployed flows are `1.8`; writable band is `1.6`–`1.10`. Leave it unless intentionally retargeting. `check` warns outside the `1.9` floor: `SCHEMA_VERSION_ABOVE_FLOOR` means a lower-pinned reader refuses it; `SCHEMA_VERSION_BELOW_FLOOR` means readers migrate it on open. Use `uip maestro flow migrate`, not this call, to change versions.

## Designer shapes decompile keeps

Leave each shape below as decompile writes it. SDK 6.44.0+ is required; older versions write `js\`[object Object]\`` for envelopes, drop fork arms and `variable` rows with `has no spelling` / `cannot write back`, and compile refuses,
<!--skill-flavor:envelope-sdk-upgrade:start-->
— upgrade with `npm install -g @uipath/maestro-builder-sdk@latest`.
<!--skill-flavor:envelope-sdk-upgrade:end-->

Preserved shapes include:

- decision/switch conditions as `jsExpression` envelopes or `=js: …`;
- quick-form asked-field `variable` ([hitl.md](hitl.md));
- `{ fork }`, `.stepToRef` arms, and pass-through `rawNode` merge ([parallel-merge.md](parallel-merge.md));
- `core.logic.loop@1.0` `output`/`loopBack` handles through its carried definition;
- subflow reads of its Start node as `input('<name>')` and subflow `.onError()`;
- a process step's `inputSchema` (its saved argument schema; edit a `properties` entry only when you change that argument's type).

Findings the source cannot carry print on stderr as `flow-decompile: warning: …`; `--strict` turns each into an error. Edit `.flow` JSON directly only when decompile printed one of these warnings and its case below says to; otherwise edit through merge:

- **Unreachable node:** source omits it and marks `// TODO: node "<id>" … is not reachable`; recompilation drops it. If it is your edit target, connect it in `.flow` first or edit its JSON directly.
- **Unbundled `(type, typeVersion)` of a type bundled at other versions, with no file definition:** source omits `{ version }`, so edited nodes compile at SDK default; `merge` preserves untouched file versions but warns edited nodes `node "<id>" moved <type>@<old> -> <new>`. If it is your edit target, edit its `.flow` JSON directly, or tell the user the edit moves it to the SDK's default. A type bundled at no version (connector, published process, agent) keeps its pin. When the file has a definition (the normal case), decompile copies it to a `const`, passes it to `.definitions([...])`, and preserves the pin even when you edit the node; leave both intact or compile refuses and lists resolvable versions (registered families first report `NODE_VERSION_UNREGISTERED`). For carried definitions whose inputs differ from the SDK factory, warning is `node "<id>" keeps <type>@<version> from the file's definitions[]; its inputs differ from <sdk-version> (<fields>)`; edit merged JSON if that node is the target. `rawNode` cannot route a human-task outcome.
- **File version below `1.6`:** source omits `.schemaVersion()`, marks `// TODO:`, and recompilation writes `1.9`; migrate first or merge into the original, which preserves its declared version.
- **Unspellable edge:** for example two edges leave one port while one path stops without successor/End. Other fan-outs become `.parallel` ([parallel-merge.md](parallel-merge.md)); converging arms use `.stepToRef(<step>)` (SDK 6.44.0+), and arms ending in End/Terminate use a `<node>Fork` with all arms ending (SDK 6.46.6+). An arm with a step before Terminate (`TERMINATE_NOT_ARM_HEAD`) or fan-out inside a loop whose arms use `.break()`/`.continue()` keeps only its first arm behind `/* TODO: unstructured fan-out … */`. Warning names `<source>@<port> -> <target>@<port>` and source marks `/* TODO: edge(s) … are NOT in this source */` or a top `// TODO: edge …`; recompilation drops it, and `merge` writes the loss into the original. If your edit touches that part of the flow, edit its `.flow` JSON directly instead of round-tripping it.
- **Unexpressible context-index `context: [...]` setting:** retrieval settings (mode, query, threshold, result count, file extension) come from `<agent source>/resources/<source>/resource.json`; retain that folder beside the `.flow`. Static plain-text query, agent-argument query, disabled deeprag citations, and folder-path prefix may lack fields. Warning names the setting; compiled output writes SDK values beside `-o`; merge does not update the project copy. Do not copy the compiled file over it; if already done, tell the user to set the setting again in Studio Web.
- **Fire-and-forget process output schema:** `agenticProcess()` refuses `returns` beside `completion: 'fire-and-forget'`, so source omits fields and warns. Require SDK 6.44.0+; older decompile writes `returns` and compile refuses,
<!--skill-flavor:fire-and-forget-sdk-upgrade:start-->
— upgrade with `npm install -g @uipath/maestro-builder-sdk@latest`.
<!--skill-flavor:fire-and-forget-sdk-upgrade:end-->
  Recompile drops the schema; merge keeps the original's definition row, so a no-edit round trip loses nothing. To read output, use `completion: 'wait'` and declare `returns`.

Pin added steps with `{ version }` used by another non-warned node of that type. If all nodes warned, leave unpinned; if none retains the file version, merge drops its definition silently. An added End needs a fresh name; see [A path without an End stays open](#a-path-without-an-end-stays-open).

Validate the merged `.flow` as in [the safe project loop](#the-safe-project-loop).

Do not run `uip maestro flow format` on the merged file; it discards author layout.

Decompiled source carries that layout as a `.layout({ nodes })` block, one long-hand entry per node.
Keep it.
A step the edit adds has no entry, so compile places it on its placeholder row and `merge` moves it next to its neighbours; to choose the spot yourself, add `<step>: at(x, y)` beside the neighbouring entries (`import { at } from '@uipath/maestro-builder-sdk'`); `merge` keeps a step you placed and moves only the ones compile left unplaced (`@uipath/maestro-builder-sdk` 6.114.0 or later; an older SDK also moves an `at()` where (x − 256) is a multiple of 288 on y = 144 or 304, so avoid those spots,
<!--skill-flavor:placeholder-flag-sdk-upgrade:start-->
or upgrade with `npm install -g @uipath/maestro-builder-sdk@latest`).
<!--skill-flavor:placeholder-flag-sdk-upgrade:end-->
A container the edit grows can still push that spot aside, so keep where it lands.
To move or resize an existing node, change or add its entry in the source (decompile writes none while every node of that flow or subflow is still where compile put it) and merge again: `merge` applies an entry whose position, size or collapsed state differs from the baseline to the original node, at the root and in subflows, and every other node keeps the original's geometry. For example, `review: at(640, 144)` changed to `at(640, 304)` moves only `review`. No hand edit of the merged `.flow` is needed.
This needs `@uipath/maestro-builder-sdk` 6.115.0 or later. An older SDK keeps the original's position and size whatever the source says;
<!--skill-flavor:layout-edit-sdk-upgrade:start-->
with it, set `layout.nodes.<id>.position` or `.size` in the merged `.flow` instead (the node's `ui` only when the file has no `layout.nodes` map), or upgrade with `npm install -g @uipath/maestro-builder-sdk@latest`.
<!--skill-flavor:layout-edit-sdk-upgrade:end-->
`merge` still shifts later nodes and grows a container to fit added steps. A subflow the edit changed is taken from the edited compile whole; any other subflow keeps the original, plus the entries you changed (6.44.4 or later; an older SDK takes every subflow from the edited compile,
<!--skill-flavor:subflow-layout-sdk-upgrade:start-->
so upgrade with
`npm install -g @uipath/maestro-builder-sdk@latest`.
<!--skill-flavor:subflow-layout-sdk-upgrade:end-->
Remove the entry of a step the edit removes. A leftover key does not fail compile: compile drops it and warns `LAYOUT_UNKNOWN_KEY`, and `check` reports the same warning (`@uipath/maestro-builder-sdk` 6.115.0 or later; an older SDK fails compile on it).
Grid and rules: [`operate.md`](operate.md#lay-out-from-source-instead-layout-at-dim).

## A path without an End stays open

Designer or `uip maestro flow node add` flows may end at a step without an End. `decompile` emits `.openTails()` near the top of the root and every subflow chain; leave it. It preserves open paths; removing it adds End nodes. Adding after an open tail makes the new step the open tail. To return outputs, end with `.return({ ... })`; an open path maps no outputs. Human-task exits always receive an End.

Name added Ends uniquely and use existing End `{ version }`: `.return({ ... }, { name: 'endSummary', version: '<END_VERSION>' })`. `name: 'end'` collides with an unnamed existing End, which becomes `end2` without warning.

## Split (`$ref`) artifacts

A deployed `.flow` may split definitions, layout, or subflows into sibling files, such as `"definitions": { "$ref": "./definitions.json" }`. Point decompile at the main file; it resolves sidecars. Do not inline or edit sidecars first. Only relative paths resolve. Absolute paths, Windows drive letters, protocol URIs (`https://`, `file:///`), and traversal above the referencing root are refused because `.flow` is untrusted input. Same-document pointers (`{"$ref": "#/definitions/…"}`) remain. Missing/unreadable targets error by filename.

Compile always writes one file; write-through splitting is unsupported. Recompiled output contains sidecar content inline and no `$ref`; this is correct.
