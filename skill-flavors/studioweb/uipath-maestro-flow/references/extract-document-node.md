<!--skill-flavor:extract-find-flow:start-->
0. **Find the flow.** The target `.flow` is the open file at `CurrentFile.AbsolutePath`, in the open solution — nothing to pull down ([Project layout](../SKILL.md#project-layout)).
<!--skill-flavor:extract-find-flow:end-->

<!--skill-flavor:extract-sdk-mixing:start-->
**A flow that holds this node takes the decompile round trip** of the [Lifecycle](../SKILL.md#lifecycle): the node decompiles to `dynamicExtract()`, its `processorKey` and taxonomy with it. Studio Web owns the SDK copy, and two floors apply: authoring or compiling this node needs `@uipath/maestro-builder-sdk` 6.119.0 or later, and a merge that edits or repairs an existing node (its taxonomy, its draft, or a missing `processorKey`) needs 6.124.16 or later. Name an SDK version as the cause only when `uip` reports it: a message of the form `… needs @uipath/maestro-builder-sdk >= <version>; found <installed>` gives both, and then tell the user which version the step needs, and stop. Do not guess the version from what a command did not do. A merge that leaves a repaired node without `processorKey` and prints no `named no IDP processor … gave it <key>` line: tell the user the repair needs 6.124.16 or later and that the node is still keyless, and stop. A failure that names a code or a field is a source problem: fix the source.
<!--skill-flavor:extract-sdk-mixing:end-->

<!--skill-flavor:extract-processor-sync:start-->
At run time the extraction service resolves which processor to use from `inputs.processorKey`, a solution resource holding its own copy of the taxonomy. This host has no `.uipx`, so `compile` and `merge` add the processor of each Extract document node they write to the open solution instead of writing a file under `resources/`. Nothing else creates it: the designer provisions only nodes without a key. So a `ResourcePending` list in the compile or merge output (`Data.ResourcePending`: the host could not add the processor) means the node has no processor. When the message names a retry ("Compile again to retry"), run it once; otherwise, or if it reports `ResourcePending` again, report the message and stop.
<!--skill-flavor:extract-processor-sync:end-->

<!--skill-flavor:extract-after-save:start-->
Re-read the target `.flow` at the start of each turn rather than reusing an earlier copy: the designer saves as the user edits, with no save button. The node keeps its type, its `processorKey` and its resource file across those saves. A node the user added as the processor variant (`uipath.ixp.processor.<key>`) is a different node type, not `dynamicExtract()`: its taxonomy is edited in the designer.
<!--skill-flavor:extract-after-save:end-->

<!--skill-flavor:extract-report:start-->
8. **Report** what was added, where it reads its file from, which fields it extracts, and its processor: the `processorKey` the node carries, which compile and merge add to the open solution. A `ResourcePending` list in their output means the host could not add it ([Making it actually extract](#making-it-actually-extract)). Taking the flow live is the user's step.
<!--skill-flavor:extract-report:end-->

<!--skill-flavor:extract-sdk-version:start-->
Studio Web owns the SDK copy, so the user upgrades it, not you ([the round trip note](#adding-the-node) names which version each step needs and when to report one).
<!--skill-flavor:extract-sdk-version:end-->

<!--skill-flavor:extract-keyless-repair:start-->
A node from before processors were provisioned, or written by hand, arrives without a processor; `validate` reports an error at `inputs.processorKey`. Repair it with the decompile round trip and no edit: decompile, then `merge`. Merge gives every Extract document node that authors a processor but names none the key compile minted for it, printing `named no IDP processor … gave it <key>`, and adds its processor to the open solution; a `ResourcePending` list means the host could not add it (see above). If the node is still keyless after the merge, tell the user the repair needs SDK 6.124.16 or later, and stop. If `validate`'s message suggests another command, do not run it: the round trip is the repair.
<!--skill-flavor:extract-keyless-repair:end-->
