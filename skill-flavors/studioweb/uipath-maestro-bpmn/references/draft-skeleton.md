<!--skill-flavor:draft-steps:start-->
1. Draft into the target: the `.bpmn` the user names, else the open one ([Studio Web](../SKILL.md#studio-web)).
   Run `uip maestro bpmn init <Project>` from `/solution` only when the user asks for a new project, then draft into its `.bpmn`.
2. Run step 1 of the [Validation loop](../SKILL.md#validation-loop) to seed `.flow-sdk/<Name>.bpmn.ts` from the target: the block's `cd` and `mkdir` lines and all of step 1's lines in one command, before you write the skeleton.
   When the target is empty, write the skeleton as the loop's empty-target rule says instead.
3. Rewrite the chain as the skeleton, in one write, keeping the seeded process id and start event id.
   When the seeded source has `.metadata({ entryPointId: false })` and the target is in a project, delete that key, or `refresh` fails. A [target outside a project](../SKILL.md#studio-web) keeps the key and skips `refresh`.
4. Run steps 2 to 5 of the [Validation loop](../SKILL.md#validation-loop): `check`, compile into `<Draft>/edited/`, `merge` into the target, `refresh` and `validate`.
   Merge keeps the shapes the user already has on the canvas. An empty target is the one exception at the gate: compile straight over it, then lay it out with `format` (*Build it* is the other, below).
   `validate` must report `Status: Valid`.
<!--skill-flavor:draft-steps:end-->

<!--skill-flavor:draft-steps-no-refresh:start-->
<!--skill-flavor:draft-steps-no-refresh:end-->

<!--skill-flavor:draft-upload:start-->
   The canvas shows the target when the turn ends, so there is nothing to upload.
   Do not publish, debug or run anything.
   Those are separate decisions, and the user has not approved the shape yet.
<!--skill-flavor:draft-upload:end-->

<!--skill-flavor:draft-cloud-copy:start-->
The user may have changed the outline on the canvas before answering.
Each turn starts again at step 1 of the [Validation loop](../SKILL.md#validation-loop), which decompiles the target, so their edits are the base; say so in the reply's one sentence.
On *Build it* the base is what the source carries (names, boxes, flows): the same sentence also says the layout was reset and names the canvas content the rebuild removed.
<!--skill-flavor:draft-cloud-copy:end-->

<!--skill-flavor:draft-change-it:start-->
- **Change it**: start again at step 2 of [Steps](#steps), edit the fresh source, run the loop, look the resources up again as step 5 says, and show it again as the gate does.
<!--skill-flavor:draft-change-it:end-->

<!--skill-flavor:lookup-no-login:start-->
Run every lookup in **one** Bash call.
<!--skill-flavor:lookup-no-login:end-->

<!--skill-flavor:lookup-not-checked-rule:start-->
Mark a box `not checked` only when its lookup ran and exited non-zero; never write it for a lookup you did not run.
<!--skill-flavor:lookup-not-checked-rule:end-->

<!--skill-flavor:gate-one-round:start-->
This gate is the one round for structure and resource questions.
<!--skill-flavor:gate-one-round:end-->

<!--skill-flavor:draft-build-merge:start-->
  *Build it* changes every box's BPMN tag, which `merge` keeps, so finish as the [Validation loop](../SKILL.md#validation-loop)'s *Build it* rule says: compile over the target, `format`, `refresh` and `validate`, and in the report's one sentence say the canvas layout was reset and name any pools, lanes, notes, colors or other canvas content the rebuild removed.
<!--skill-flavor:draft-build-merge:end-->
