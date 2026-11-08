<!--skill-flavor:draft-upload:start-->
4. Never run `uip solution upload`: the canvas renders the open solution, and it shows the skeleton as soon as the file is written.
   Do not pack, debug or run anything.
   Those are separate decisions, and the user has not approved the shape yet.
<!--skill-flavor:draft-upload:end-->

<!--skill-flavor:gate-first-line:start-->
<Name>: outline ready (draft mode).
<!--skill-flavor:gate-first-line:end-->

<!--skill-flavor:gate-path-line:start-->
<the local <Project>/<Name>.bpmn path>
<!--skill-flavor:gate-path-line:end-->

<!--skill-flavor:gate-uploaded-rule:start-->
<!--skill-flavor:gate-uploaded-rule:end-->

<!--skill-flavor:draft-cloud-copy:start-->
The open `.bpmn` is the only copy, and the user may have changed it on the canvas before answering: decompile it fresh before you edit it again ([Studio Web](../SKILL.md#studio-web)).
Never run `uip solution download`.
<!--skill-flavor:draft-cloud-copy:end-->

<!--skill-flavor:final-upload:start-->
Never run `uip solution upload` or ask about one: the canvas already shows the finished process from the open solution's files.
<!--skill-flavor:final-upload:end-->

<!--skill-flavor:final-first-line:start-->
<Name>: built, validated (draft mode). <One sentence if you kept the user's canvas edits.>
<!--skill-flavor:final-first-line:end-->

<!--skill-flavor:final-path-line:start-->
The process is on the canvas
<!--skill-flavor:final-path-line:end-->
