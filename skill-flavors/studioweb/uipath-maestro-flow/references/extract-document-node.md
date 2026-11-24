<!--skill-flavor:extract-find-flow:start-->
0. **Find the flow.** The target `.flow` is the open file at `CurrentFile.AbsolutePath`, in the open solution — nothing to pull down ([Project layout](../SKILL.md#project-layout)).
<!--skill-flavor:extract-find-flow:end-->

<!--skill-flavor:extract-sdk-mixing:start-->
**A flow that holds this node takes the decompile round trip** of the [Lifecycle](../SKILL.md#lifecycle): the node decompiles to `dynamicExtract()`, its `processorKey` and taxonomy with it. Studio Web owns the SDK copy, and two floors apply: authoring or compiling this node needs `@uipath/maestro-builder-sdk` 6.119.0 or later, and a merge that repairs an existing node with no `processorKey` needs 6.124.16 or later. Report an old SDK only on evidence, never from a failure alone: an envelope's `requiresSdkVersion` names the version itself; a repair merge that prints no `named no IDP processor … gave it <key>` line and leaves the node keyless means older than 6.124.16; `check` reporting no `EXTRACT_TAXONOMY_*` code for a broken taxonomy means older than 6.119.0. Then tell the user which version the step needs, and stop. A failure that names a code or a field is a source problem: fix the source.
<!--skill-flavor:extract-sdk-mixing:end-->

<!--skill-flavor:extract-processor-sync:start-->
At run time the extraction service resolves which processor to use from `inputs.processorKey`, a solution resource holding its own copy of the taxonomy. This host has no `.uipx`, so `compile` and `merge` add the processor of each Extract document node they write to the open solution instead of writing a file under `resources/`. Nothing else creates it: the designer provisions only nodes without a key. So a `ResourcePending` list in the compile or merge output (`Data.ResourcePending`: the host could not add the processor) means the node has no processor. When the message names a retry ("Compile again to retry"), run it once; otherwise, or if it reports `ResourcePending` again, report the message and stop.
<!--skill-flavor:extract-processor-sync:end-->

<!--skill-flavor:extract-after-save:start-->
Re-read the target `.flow` at the start of each turn rather than reusing an earlier copy: the designer saves as the user edits, with no save button. The node keeps its type, its `processorKey` and its resource file across those saves. A node the user added as the processor variant (`uipath.ixp.processor.<key>`) is a different node type, not `dynamicExtract()`: its taxonomy is edited in the designer.
<!--skill-flavor:extract-after-save:end-->
