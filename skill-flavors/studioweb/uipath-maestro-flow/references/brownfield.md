<!--skill-flavor:safe-project-loop:start-->
In Studio Web this loop is the round trip in
[SKILL.md — Lifecycle](../SKILL.md#lifecycle). The drafts sit in the
`.flow-sdk/` folder of the project, each intermediate `.flow` in a folder of
its own, and `merge -o` writes straight into the target `.flow`. There is
nothing to install with `cp`, and nothing to delete: the project file system
refuses deletes.

Never write or patch the `.flow` yourself. Merge renumbers every edge
(`edge_0`, `edge_1`, ...), may reorder nodes, and adds default fields: that is
its normal output, not drift to undo. The changes to act on are the
[merge warnings](#merge-warnings-what-the-round-trip-changed).

Validate the target `.flow`, not `.flow-sdk/edited/`: that folder holds only
the agent files merge changed. If validate fails, copy
`.flow-sdk/original/<Name>.flow` back over the target, fix the source, and
merge again.
<!--skill-flavor:safe-project-loop:end-->

<!--skill-flavor:merge-check-sdk-upgrade:start-->
so tell the user: Studio Web owns the SDK copy.
<!--skill-flavor:merge-check-sdk-upgrade:end-->

<!--skill-flavor:check-baseline-lowering:start-->
- **`(pre-existing)` worded as a probable SDK defect** (JSON
  `class: "lowering"`): `compile` refuses that node, so the round trip stops at
  the baseline compile (run this check before you edit to tell this case
  apart). Studio Web has no `merge --baseline-from` to keep the
  node as saved. Do not edit the node to get around it. Stop, name the node,
  and tell the user it is a probable SDK defect to report at
  <https://github.com/UiPath/builder-sdk/issues>.
<!--skill-flavor:check-baseline-lowering:end-->

<!--skill-flavor:check-baseline-sdk-upgrade:start-->
so tell the user: Studio Web owns the SDK copy.
<!--skill-flavor:check-baseline-sdk-upgrade:end-->

<!--skill-flavor:install-agent-files:start-->
`merge -o` into the target writes the `.flow` and every agent file merge
carried. Fields the round trip does not reproduce (such as `maxIterations`, or a
`description` on an agent input) keep the project's values.
<!--skill-flavor:install-agent-files:end-->

<!--skill-flavor:resource-install:start-->
- `merge -o` writes an added or changed resource into the project. A changed
  one keeps its original directory.
- A removed one stays: merge lists each such directory under `remove`
  (`Data.Removed` in `--output json`), and Studio Web cannot delete it. Ask the
  user to remove that resource from the agent on the canvas. Otherwise the
  agent keeps that resource.
<!--skill-flavor:resource-install:end-->

<!--skill-flavor:draft-nodes:start-->
A canvas-saved flow often holds **draft** nodes: a connector with no connection
yet, a required input left empty, or a generic operation with no object picked.
Decompile carries the definition of each draft the canvas saved, so `compile`
writes it with a warning (`⚠ [CONNECTOR_INPUT_MISSING] ... Written as a draft`)
and the round trip gets past it. A generic operation with no object
(`CONNECTOR_OBJECT_REQUIRED`) still stops the baseline compile. In a terminal
the fix is `merge --baseline-from` through the `flow-sdk` bin of the SDK;
Studio Web has neither. Name each draft node that the refusal lists, and ask
the user to finish it on the canvas, or to remove it. Then run the round trip
again.
<!--skill-flavor:draft-nodes:end-->

<!--skill-flavor:generated-pipeline:start-->
Studio Web has no generated pipeline: `decompile` writes no pipeline helper
here. Use the round trip in [SKILL.md — Lifecycle](../SKILL.md#lifecycle).
<!--skill-flavor:generated-pipeline:end-->

<!--skill-flavor:hand-loop:start-->
In Studio Web this loop is the round trip in
[SKILL.md — Lifecycle](../SKILL.md#lifecycle). It keeps every draft in
`.flow-sdk/` and merges straight into the target `.flow`.
<!--skill-flavor:hand-loop:end-->

<!--skill-flavor:resource-ids-sdk-upgrade:start-->
so tell the user: Studio Web owns the SDK copy.
<!--skill-flavor:resource-ids-sdk-upgrade:end-->

<!--skill-flavor:dup-step-sdk-upgrade:start-->
so tell the user: Studio Web owns the SDK copy.
<!--skill-flavor:dup-step-sdk-upgrade:end-->

<!--skill-flavor:strict-merge:start-->
- Pass `--strict` to make merge refuse (exit 1, no file written) instead of
  warning. The benign End line never refuses. `--strict` needs `--baseline`,
  which the Studio Web round trip always passes.
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
