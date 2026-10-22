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

<!--skill-flavor:merge-check-sdk-version:start-->
Needs `@uipath/maestro-builder-sdk` 6.44.4 or later; an older SDK refuses the write for any error it cannot place on an untouched root node. If Studio Web's SDK is older, tell the user.
<!--skill-flavor:merge-check-sdk-version:end-->

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
`compile` refuses them even with `--no-check`, so the round trip stops at the
baseline compile. In a terminal the fix is `merge --baseline-from` through the
`flow-sdk` bin of the SDK; Studio Web has neither. Name each draft node that the
refusal lists, and ask the user to finish it on the canvas, or to remove it.
Then run the round trip again.
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

<!--skill-flavor:resource-ids-sdk-version:start-->
Needs `@uipath/maestro-builder-sdk`
6.33.0 or later; an older SDK's decompile omits these fields and compile renames
the node with a new directory. If Studio Web's SDK is older, tell the user.
<!--skill-flavor:resource-ids-sdk-version:end-->

<!--skill-flavor:dup-step-sdk-version:start-->
Needs `@uipath/maestro-builder-sdk` 6.32.4 or
later; an older SDK silently renames the second step `<name>2`. If Studio Web's SDK is older, tell the user.
<!--skill-flavor:dup-step-sdk-version:end-->

<!--skill-flavor:strict-merge:start-->
- Pass `--strict` to make merge refuse (exit 1, no file written) instead of
  warning. The benign End line never refuses. `--strict` needs `--baseline`,
  which the Studio Web round trip always passes.
<!--skill-flavor:strict-merge:end-->

<!--skill-flavor:envelope-sdk-version:start-->
Needs `@uipath/maestro-builder-sdk` 6.44.0 or later: an older SDK's decompile writes `js\`[object Object]\`` for the envelope, drops the fork's arms and the `variable` rows with a `has no spelling` / `cannot write back` warning, and compile then refuses the source. If Studio Web's SDK is older, tell the user.
<!--skill-flavor:envelope-sdk-version:end-->

<!--skill-flavor:fire-and-forget-sdk-version:start-->
  Needs `@uipath/maestro-builder-sdk` 6.44.0 or later; an older SDK's
  decompile writes `returns` and compile refuses it. If Studio Web's SDK is older, tell the user.
<!--skill-flavor:fire-and-forget-sdk-version:end-->

<!--skill-flavor:subflow-layout-sdk-version:start-->
Inside a subflow the source's entries land only when the edit changed that subflow: `merge` then takes the subflow from the edited compile whole, and otherwise keeps the original subflow as it was (6.44.4 or later; an older SDK takes every subflow from the edited compile). If Studio Web's SDK is older, tell the user.
<!--skill-flavor:subflow-layout-sdk-version:end-->
