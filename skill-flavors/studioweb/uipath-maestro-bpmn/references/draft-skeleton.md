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
On *Build it*, a compile over the target keeps only what the source carries (names, boxes, flows); the Validation loop's *Build it* block merges instead when the target holds more.
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
  Do not `merge`: it keeps each box's `bpmn:task` tag, so a script step loses its script on the canvas. Write the target with this block in place of the loop's step 3 (it compiles over the target, and merges only when that would drop canvas content), then run `refresh` and `validate`, and report as the [Validation loop](../SKILL.md#validation-loop)'s *Build it* rule says:

  ```bash
  drop=$(node -e "const fs=require('fs');const c=f=>{const m={};for(const t of fs.readFileSync(f,'utf8').matchAll(/<((?:bpmn|uipath):[A-Za-z]+)([^>]*?)(\/?)>|(color:background-color)/g)){const k=t[1]||t[4];if(k==='bpmn:extensionElements'||(t[3]&&/^\s*version=\"[^\"]*\"\s*$/.test(t[2])))continue;m[k]=(m[k]||0)+1}return m};const o=c(process.argv[1]),b=c(process.argv[2]);console.log(Object.keys(o).filter(k=>o[k]>(b[k]||0)).join(' ')||'none')" .flow-sdk/original/<Name>.bpmn <Draft>/baseline/<Name>.bpmn) && echo "drops: $drop" &&
  if [ "$drop" = none ]; then
    uip maestro bpmn compile .flow-sdk/<Name>.bpmn.ts -o <Name>.bpmn && uip maestro bpmn format <Name>.bpmn
  else
    uip maestro bpmn compile .flow-sdk/<Name>.bpmn.ts -o <Draft>/edited/<Name>.bpmn && uip maestro bpmn merge <Draft>/edited/<Name>.bpmn --original <Name>.bpmn --baseline <Draft>/baseline/<Name>.bpmn -o <Name>.bpmn
  fi
  ```

<!--skill-flavor:draft-build-merge:end-->
