<!--skill-flavor:draft-steps:start-->
1. Draft into the target that [Studio Web](../SKILL.md#studio-web) defines; a new process goes where [Critical Rule 12](../SKILL.md#critical-rules) says.
2. Run step 1 of the [Validation loop](../SKILL.md#validation-loop) to seed `.flow-sdk/<Name>.bpmn.ts` from the target: the block's `cd` and `mkdir` lines and all of step 1's lines in one command, before you write the skeleton.
   When the target is empty, write the skeleton as the loop's empty-target rule says instead.
3. Rewrite the chain as the skeleton, in one write, keeping the seeded process id and start event id.
   When the seeded source has `.metadata({ entryPointId: false })` and the target is in a project, delete that key, or `refresh` fails. A [target outside a project](../SKILL.md#studio-web) keeps the key and skips `refresh`.
4. Run steps 2 to 4 of the [Validation loop](../SKILL.md#validation-loop): `check`, compile into `<Draft>/edited/`, `merge` into the target, `refresh` and `validate`.
   Merge keeps the shapes the user already has on the canvas. A template (one start event and at most one end event) or a process the user chose to *replace* ([Critical Rule 12](../SKILL.md#critical-rules) step 2) has none to keep. An empty target has nothing to merge into: compile straight over it instead of merging.
   For all three, then run `format <Name>.bpmn --relayout` (loop step 5a), then `refresh` and `validate` again.
   `validate` must report `Status: Valid`.
   When you ran step 5a, then run `mkdir -p .flow-sdk/gate && cp <Name>.bpmn .flow-sdk/gate/<Name>.bpmn`: *Build it* compares the target with that copy.
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
  When `.flow-sdk/gate/<Name>.bpmn` exists, compare the target with it: `node -e "const f=require('fs');console.log(f.readFileSync('<Name>.bpmn','utf8')===f.readFileSync('.flow-sdk/gate/<Name>.bpmn','utf8')?'same':'changed')"`.
  On `same`, nobody changed the canvas since the gate, and its layout is the one you drew: compile the source straight over the target, run `format <Name>.bpmn` (never `--relayout` here: it drops the CDATA of script arguments, and `validate` then reports `SCRIPT_ARGS_ENVELOPE_MISSING`), then `refresh` and `validate`.
  On `changed`, an error, or no gate copy, finish through the merge pipeline of the [Validation loop](../SKILL.md#validation-loop), as every turn does.
<!--skill-flavor:draft-build-merge:end-->
