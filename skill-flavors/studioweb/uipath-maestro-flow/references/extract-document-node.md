<!--skill-flavor:extract-find-flow:start-->
0. **Find the flow.** The target `.flow` is the open file at `CurrentFile.AbsolutePath`, in the open solution — nothing to pull down ([Project layout](../SKILL.md#project-layout)).
<!--skill-flavor:extract-find-flow:end-->

<!--skill-flavor:extract-sdk-mixing:start-->
**A flow that holds this node skips the decompile round trip.** The baseline compile of the [Lifecycle](../SKILL.md#lifecycle) fails on this node, so for such a flow do not decompile at all: make every change with the direct commands on the target `.flow` — `nodes`, `edges`, `variables`, `nodes schema` — and finish with `validate`.
<!--skill-flavor:extract-sdk-mixing:end-->

<!--skill-flavor:extract-after-save:start-->
One thing to expect between turns. The user's save in the designer may convert the node to the processor variant (`uipath.ixp.processor.<key>`), which is a different node type. Re-read the target `.flow` at the start of each turn rather than reusing an earlier copy — and where the node has become the processor variant, `nodes schema set` refuses it, and the taxonomy is edited in the designer from then on.
<!--skill-flavor:extract-after-save:end-->
