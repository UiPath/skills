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
restamped it. To drop the edit, revert it in the source and merge again. The
result is equivalent to the target, not byte-identical.

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
- A removed one stays: merge lists each such directory under `remove`
  (`Data.Removed` in `--output json`), and Studio Web cannot delete it. Ask the
  user to remove that resource from the agent on the canvas. Otherwise the
  agent keeps that resource.
<!--skill-flavor:resource-install:end-->

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
