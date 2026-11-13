<!--skill-flavor:draft-steps:start-->
1. Draft into the target: the `.bpmn` the user names, else the open one ([Studio Web](../SKILL.md#studio-web)).
   Run `uip maestro bpmn init <Project>` from `/solution` only when the user asks for a new project, then draft into its `.bpmn`.
2. Run step 1 of the [Validation loop](../SKILL.md#validation-loop) to seed `.flow-sdk/<Name>.bpmn.ts` from the target.
   When the target is empty, write the skeleton as the loop's empty-target rule says instead.
3. Rewrite the chain as the skeleton, in one write, keeping the seeded process id and start event id.
   When the seeded source has `.metadata({ entryPointId: false })`, delete that key, or `refresh` fails.
4. Run steps 2 to 5 of the [Validation loop](../SKILL.md#validation-loop): `check`, compile into `<Draft>/edited/`, `merge` into the target, `refresh` and `validate`.
   Merge keeps the shapes the user already has on the canvas. An empty target is the one exception: compile straight over it, then lay it out with `format`.
   `validate` must report `Status: Valid`.
<!--skill-flavor:draft-steps:end-->

<!--skill-flavor:draft-upload:start-->
5. The canvas shows the target when the turn ends, so there is nothing to upload.
   Do not publish, debug or run anything.
   Those are separate decisions, and the user has not approved the shape yet.
<!--skill-flavor:draft-upload:end-->

<!--skill-flavor:gate-first-line:start-->
<Name>: outline ready (draft mode). <One sentence if you kept the user's canvas edits.>
<!--skill-flavor:gate-first-line:end-->

<!--skill-flavor:gate-path-line:start-->
<the target path, such as /solution/<Project>/<Name>.bpmn, as plain text, never a link>
<!--skill-flavor:gate-path-line:end-->

<!--skill-flavor:gate-uploaded-rule:start-->
<!--skill-flavor:gate-uploaded-rule:end-->

<!--skill-flavor:draft-cloud-copy:start-->
The user may have changed the outline on the canvas before answering.
Each turn starts again at step 1 of the [Validation loop](../SKILL.md#validation-loop), which decompiles the target, so their edits are the base; say so in the reply's one sentence.
<!--skill-flavor:draft-cloud-copy:end-->

<!--skill-flavor:draft-change-it:start-->
- **Change it**: start again at step 2 of [Steps](#steps), edit the fresh source, run the loop, and show it again as the gate does.
<!--skill-flavor:draft-change-it:end-->

<!--skill-flavor:final-upload:start-->
When the built process validates, the canvas shows it, so there is nothing to upload.
<!--skill-flavor:final-upload:end-->

<!--skill-flavor:final-first-line:start-->
<Name>: built, validated (draft mode). <One sentence if you kept the user's canvas edits.>
<!--skill-flavor:final-first-line:end-->

<!--skill-flavor:final-path-line:start-->
<the target path, such as /solution/<Project>/<Name>.bpmn>
<!--skill-flavor:final-path-line:end-->
