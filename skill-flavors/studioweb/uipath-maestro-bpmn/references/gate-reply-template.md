<!--skill-flavor:gate-first-line:start-->
<Name>: outline ready (draft mode). <One sentence if a lookup failed or you kept the user's canvas edits.>
<!--skill-flavor:gate-first-line:end-->

<!--skill-flavor:gate-path-line:start-->
<the target path, such as /solution/<Project>/<Name>.bpmn, as plain text, never a link or in backticks>
<!--skill-flavor:gate-path-line:end-->

<!--skill-flavor:gate-uploaded-rule:start-->
<!--skill-flavor:gate-uploaded-rule:end-->

<!--skill-flavor:gate-not-checked-rule:start-->
Write `not checked` only for a box whose lookup ran and failed; a box you have not looked up is not a reply line yet, so run its lookup first.
<!--skill-flavor:gate-not-checked-rule:end-->

<!--skill-flavor:gate-retry:start-->
When a box is missing, rebuild the baseline as the [Validation loop](../SKILL.md#validation-loop) says, run its steps 3 and 4 once more and search again; when one is still missing, send no gate reply and tell the user in one sentence that the outline did not reach the process file.
<!--skill-flavor:gate-retry:end-->
