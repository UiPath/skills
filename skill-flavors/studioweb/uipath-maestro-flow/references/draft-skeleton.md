<!--skill-flavor:draft-steps:start-->
1. Draft into the target that [SKILL.md — Project layout](../SKILL.md#project-layout) chooses. Create a project only as it says.
2. Seed the source as [Lifecycle](../SKILL.md#lifecycle) says for a new flow: `cd /solution/<Project>`, `decompile new.flow -o .flow-sdk/new.flow.ts --no-pipeline`, and delete the source's `.layout()` call. Keep the seeded header and trigger.
   For a new `<Name>.flow` beside a flow that has steps, write `.flow-sdk/<Name>.flow.ts` from [Hello world](../SKILL.md#hello-world-flow) instead.
   Then rewrite the chain after the trigger as the skeleton, in one write. Keep the seeded flow id.
3. Run the loop from `/solution/<Project>`. `<Name>` is `new` for `new.flow`.

   ```bash
   uip maestro flow check .flow-sdk/<Name>.flow.ts --source
   uip maestro flow compile .flow-sdk/<Name>.flow.ts -o <Name>.flow
   uip maestro flow validate <Name>.flow --output json
   ```

   `validate` must report `Data.Status: "Valid"`.
<!--skill-flavor:draft-steps:end-->

<!--skill-flavor:draft-upload:start-->
4. **Show it.** There is nothing to upload. The canvas shows the target when it is the open flow. A new `<Name>.flow` beside an open flow that has steps shows only after the user opens it from the Explorer.
   Do not publish, debug or run anything. Those are separate decisions, and the user has not approved the shape yet.
<!--skill-flavor:draft-upload:end-->

<!--skill-flavor:lookup-no-login:start-->
Run every lookup in **one** Bash call.
<!--skill-flavor:lookup-no-login:end-->

<!--skill-flavor:lookup-not-checked-rule:start-->
Mark a box `not checked` only when its lookup ran and exited non-zero. Never write it for a lookup you did not run.
<!--skill-flavor:lookup-not-checked-rule:end-->

<!--skill-flavor:gate-one-round:start-->
This gate is the one round for structure and resource questions.
<!--skill-flavor:gate-one-round:end-->

<!--skill-flavor:draft-cloud-copy:start-->
The user may have changed the outline on the canvas before answering.
Each turn starts again at a fresh `decompile` of the target ([Lifecycle](../SKILL.md#lifecycle)), so their edits are the base. Say so in the reply's one sentence.
<!--skill-flavor:draft-cloud-copy:end-->

<!--skill-flavor:draft-change-it:start-->
- **Change it**: the target now has steps, so run the edit round trip of [Lifecycle](../SKILL.md#lifecycle): `decompile` it afresh, edit the source narrowly, `check --baseline`, `merge`, `validate`. Then show it again as the gate does.
<!--skill-flavor:draft-change-it:end-->

<!--skill-flavor:draft-build-merge:start-->
  Finish through the edit round trip of [Lifecycle](../SKILL.md#lifecycle), as every turn does. `merge` of an unchanged source writes nothing and prints no error. Confirm the source changed before you merge.
<!--skill-flavor:draft-build-merge:end-->
