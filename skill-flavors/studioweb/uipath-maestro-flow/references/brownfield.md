<!--skill-flavor:safe-project-loop:start-->
In Studio Web this loop is the round trip in
[SKILL.md — Lifecycle](../SKILL.md#lifecycle), run from `/solution/<Project>`
with the source in `.flow-sdk/`. `decompile` stamps the source's first line,
and `merge` takes that source: it compiles it, derives the baseline from the
target in memory, and writes the merged flow, and every agent file it carries,
over the target. There is nothing to install with `cp`, and nothing to delete:
the project file system refuses deletes.

Only `merge` writes the `.flow`. Never write or patch it yourself. Merge renumbers every edge
(`edge_0`, `edge_1`, ...), may reorder nodes, and adds default fields, and moves
original nodes right or down to make room for an added one: that is its normal
output, not drift to undo. Never move them back. The changes to act on are the
[merge warnings](#merge-warnings-what-the-round-trip-changed).

Validate the target `.flow`. A refused merge writes nothing, so there is nothing
to restore. If validate fails, fix the source, `check` and `merge` again: merge
restamped it.

### Dropping an edit

To drop an edit that changed or
added, revert it in the source and merge again: the result is equivalent to the
target, not byte-identical. An edit that removed a node, agent or resource is
not restored that way: the source rebuilds it from SDK defaults and the
canvas-only fields are lost. Tell the user to undo it on the canvas, or in
Studio Web's version history if the page offers one. Make no copy of the
target.

### The stamp, and when merge refuses

The first line reads `// @decompiled-from <Name>.flow sha256:<64 hex> scripts=function`.
`merge` decompiles the target again the same way and compares, so it knows the
baseline it derives is the source you started from.

- `MERGE_ORIGINAL_CHANGED`: the `.flow` changed since the decompile (a canvas
  save, another merge, a moved node). Merging would revert that change, so
  nothing was written. Decompile again and redo the edit on the new source.
  Never edit the first line to get past it.
- `MERGE_SOURCE_STAMP_UNREADABLE`: the first line was edited. Decompile again.
- No stamp on the first line: the SDK is older than 6.96.0, and its `merge`
  writes `merged.flow` beside you, which cannot be deleted. Merge nothing, and
  tell the user: Studio Web owns the SDK copy.
<!--skill-flavor:safe-project-loop:end-->

<!--skill-flavor:merge-check-sdk-upgrade:start-->
so tell the user: Studio Web owns the SDK copy.
<!--skill-flavor:merge-check-sdk-upgrade:end-->

<!--skill-flavor:check-baseline-sdk-upgrade:start-->
and Studio Web owns the SDK copy, so tell the user. Until it is upgraded, run
`check --source` without `--baseline` and fix only the errors on nodes you
changed. If a compile then stops on a node you did not change, stop: name the
node and its code to the user.
<!--skill-flavor:check-baseline-sdk-upgrade:end-->

<!--skill-flavor:check-baseline-uip-version:start-->

<!--skill-flavor:check-baseline-uip-version:end-->

<!--skill-flavor:resource-install:start-->
- `merge` writes an added or changed resource into the project. A changed
  one keeps its original directory.
- A removed one stays (before `@uipath/maestro-builder-sdk` 6.112.0; later merges delete unreferenced directories, unverified on the Studio Web file system): merge lists each such directory under `remove`
  (`Data.Removed` in `--output json`), and Studio Web cannot delete it. Ask the
  user to remove that resource from the agent on the canvas. Otherwise the
  agent keeps that resource.
<!--skill-flavor:resource-install:end-->

<!--skill-flavor:swap-connection-finish:start-->
After step 2, and step 3 when it applies, add the new connection to the solution: [the connector loop](../SKILL.md#the-connector-loop-in-studio-web), step 7. No other step: do not compile a scratch copy.
<!--skill-flavor:swap-connection-finish:end-->

<!--skill-flavor:draft-nodes:start-->
A canvas-saved flow often holds **draft** nodes: a connector with no connection
yet, a required input left empty, a generic operation with no object picked, a
`waitForEvent` with no connection, a Transform with no collection, or a
decision with no condition (a draft trigger or connector tool still refuses and
must be finished first). Decompile carries the definition of each draft the
canvas saved and marks its step `{ draft: true }`, so `compile` writes it with a
warning (`⚠ [CONNECTOR_INPUT_MISSING] ... Written as a draft`) and the loops on
this page get past it. For instance a decision saved with no condition
decompiles as `.branch("decision1", undefined, (t) => ..., (e) => ..., { draft: true })`
and a Transform with no collection as `transform({ operations: [] })` with
`{ draft: true }`: leave those as written unless the user asked you to finish
the node. The `waitForEvent`, Transform and decision drafts need `@uipath/maestro-builder-sdk`
6.86.5 or later; an older one refuses them (`BINDING_MISSING`,
`TRANSFORM_COLLECTION_LITERAL`, `EXPR_SYNTAX`). Three cases still stop `compile`: a generic operation with no object
(`CONNECTOR_OBJECT_REQUIRED`), a draft you wrote yourself (no carried
definition), and an untouched node the SDK cannot compile (`check --baseline`
prints it as a probable SDK defect). The [safe project loop](#the-safe-project-loop)
runs no `compile`: merge compiles the edited source and the baseline it derives
itself, and both compiles tolerate drafts.

- A draft node you did **not** touch is restored exactly as saved, with
  `[DRAFT_NODE_KEPT]` on stderr. So is a draft inside a subflow the edit did
  not change: merge keeps that subflow from the original (6.44.4 or later; an
  older SDK takes every subflow from the edited source and refuses the draft).
- A draft node you **changed** gets the refusal a normal compile gives
  (`[BINDING_MISSING]`, `[CONNECTOR_INPUT_MISSING]` or
  `[CONNECTOR_OBJECT_REQUIRED]`) and nothing is written. Finish that node or
  revert the edit.
- An untouched node the SDK cannot compile is kept exactly as saved, with
  `⚠ [LOWERING_NODE_KEPT] "<node>" is untouched, so the original node is kept
  as is, but the SDK cannot compile it (<CODE>)` on stderr. Tell the user it is
  a probable SDK defect and that it should be filed at
  <https://github.com/UiPath/builder-sdk/issues>. The same refusal on a node the
  edit changed is `✗ [<CODE>] "<node>" is changed or new` and nothing is
  written: revert the edit to that node, or fix it. An untouched node that
  fails only because of an edit elsewhere (it reads a step the edit deleted)
  also stops the write. Needs `@uipath/maestro-builder-sdk` 6.64.0 or later.
- `--strict` works here too.
<!--skill-flavor:draft-nodes:end-->

<!--skill-flavor:generated-pipeline:start-->
Studio Web has no generated pipeline: `decompile` writes no pipeline helper
here. Use the round trip in [SKILL.md — Lifecycle](../SKILL.md#lifecycle).
<!--skill-flavor:generated-pipeline:end-->

<!--skill-flavor:resource-ids-sdk-upgrade:start-->
so tell the user: Studio Web owns the SDK copy.
<!--skill-flavor:resource-ids-sdk-upgrade:end-->

<!--skill-flavor:dup-step-sdk-upgrade:start-->
so tell the user: Studio Web owns the SDK copy.
<!--skill-flavor:dup-step-sdk-upgrade:end-->

<!--skill-flavor:strict-merge:start-->
- Pass `--strict` to make merge refuse (exit 1, no file written) instead of
  warning. The benign End line never refuses. `uip maestro flow merge
  .flow-sdk/<Name>.flow.ts --original <Name>.flow --strict`.
<!--skill-flavor:strict-merge:end-->

<!--skill-flavor:envelope-sdk-upgrade:start-->
— tell the user: Studio Web owns the SDK copy.
<!--skill-flavor:envelope-sdk-upgrade:end-->

<!--skill-flavor:fire-and-forget-sdk-upgrade:start-->
  — tell the user: Studio Web owns the SDK copy.
<!--skill-flavor:fire-and-forget-sdk-upgrade:end-->

<!--skill-flavor:subflow-layout-sdk-upgrade:start-->
so tell the user, since Studio Web owns the SDK copy).
<!--skill-flavor:subflow-layout-sdk-upgrade:end-->

<!--skill-flavor:fresh-decompile-cleanup:start-->
<!--skill-flavor:fresh-decompile-cleanup:end-->

<!--skill-flavor:supplied-source:start-->
In Studio Web the target `.flow` is the source: use the round trip in
[SKILL.md — Lifecycle](../SKILL.md#lifecycle).
<!--skill-flavor:supplied-source:end-->

<!--skill-flavor:placeholder-flag-sdk-upgrade:start-->
or tell the user this needs `@uipath/maestro-builder-sdk` 6.114.0 or later, since Studio Web owns the SDK copy).
<!--skill-flavor:placeholder-flag-sdk-upgrade:end-->

<!--skill-flavor:layout-edit-sdk-upgrade:start-->
tell the user this needs `@uipath/maestro-builder-sdk` 6.115.0 or later, since Studio Web owns the SDK copy and the merged `.flow` is never edited by hand.
<!--skill-flavor:layout-edit-sdk-upgrade:end-->
