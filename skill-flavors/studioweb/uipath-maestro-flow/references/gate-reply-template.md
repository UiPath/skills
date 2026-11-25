<!--skill-flavor:gate-first-line:start-->
<Name>: outline ready (draft mode). <One sentence if a lookup failed or you kept the user's canvas edits.>
<!--skill-flavor:gate-first-line:end-->

<!--skill-flavor:gate-path-line:start-->
<"The outline is on the canvas." when the target is the open flow, else "Open <Name>.flow from the Explorer to see the outline.">
<!--skill-flavor:gate-path-line:end-->

<!--skill-flavor:gate-uploaded-rule:start-->
<!--skill-flavor:gate-uploaded-rule:end-->

<!--skill-flavor:gate-not-checked-rule:start-->
Write `not checked` only for a box whose lookup ran and failed. A box you have not looked up is not a reply line yet: run its lookup first.
<!--skill-flavor:gate-not-checked-rule:end-->

<!--skill-flavor:gate-retry:start-->
When a box is missing, run the edit round trip of [Lifecycle](../SKILL.md#lifecycle) once more and search again. When one is still missing, send no gate reply. Tell the user in one sentence that the outline did not reach the flow file.
<!--skill-flavor:gate-retry:end-->
