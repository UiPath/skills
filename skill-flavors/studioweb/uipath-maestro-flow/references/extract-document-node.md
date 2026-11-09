<!--skill-flavor:extract-find-flow:start-->
0. **Find the flow.** The target `.flow` is the open file at `CurrentFile.AbsolutePath`, in the open solution — nothing to pull down ([Project layout](../SKILL.md#project-layout)).
<!--skill-flavor:extract-find-flow:end-->

<!--skill-flavor:extract-sdk-mixing:start-->
**A flow that holds this node skips the decompile round trip.** The baseline compile of the [Lifecycle](../SKILL.md#lifecycle) fails on this node, so for such a flow do not decompile at all: make every change with the direct commands on the target `.flow` — `nodes`, `edges`, `variables`, `nodes schema` — and finish with `validate`.
<!--skill-flavor:extract-sdk-mixing:end-->

<!--skill-flavor:extract-processor-sync:start-->
At run time the extraction service resolves which processor to use from `inputs.processorKey`, a solution resource holding its own copy of the taxonomy. The CLI provisions it while you author: `nodes create` mints the key and writes the processor's resource file into the open solution, and `nodes schema set` does the same for a node that has none. Saving the flow in the designer regenerates the resource from the node, so the deployed processor matches the taxonomy last written.
<!--skill-flavor:extract-processor-sync:end-->

<!--skill-flavor:extract-after-save:start-->
Re-read the target `.flow` at the start of each turn rather than reusing an earlier copy: the designer saves as the user edits, with no save button. The node keeps its type, its `processorKey` and its resource file across those saves. A node the user added as the processor variant (`uipath.ixp.processor.<key>`) is a different node type — `nodes schema set` refuses it, and its taxonomy is edited in the designer.
<!--skill-flavor:extract-after-save:end-->
