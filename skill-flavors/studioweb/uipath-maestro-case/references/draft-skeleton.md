<!--skill-flavor:draft-steps:start-->
1. Draft into the target that [Studio Web](../SKILL.md#studio-web) chooses: the plan of the open project when it has no stages yet, else the plan of a new project the user asks for (`uip maestro case init <Project>` from `/solution`). Never create a solution.
2. Run the seed of the [Validation loop](../SKILL.md#validation-loop) from `/solution/<Project>`: the undo copy, then the fresh decompile into `.flow-sdk/<Project>.case.ts`.
   Then rewrite the chain between `.trigger(...)` and `.build()` as the skeleton, in one write.
   Keep the first comment line, the case id, `.schemaVersion(...)`, `.name(...)`, `.identifier(...)`, the trigger and the trailing `preserveCaseJson(...)`.
   Replace the trigger only for a schedule or an outside event.
3. Run the loop from `/solution/<Project>`.

   ```bash
   uip maestro case check .flow-sdk/<Project>.case.ts --source
   uip maestro case compile .flow-sdk/<Project>.case.ts -o <Plan>
   uip maestro case validate <Plan> --strict --output json
   ```

   `validate` must report `Data.Status: "Valid"`.
<!--skill-flavor:draft-steps:end-->

<!--skill-flavor:draft-upload:start-->
4. **Show it.** There is nothing to upload: the designer re-renders the open plan after the compile. The plan of a new project shows only after the user opens it from the Explorer.
   Do not publish, debug or run anything. Those are separate decisions, and the user has not approved the shape yet.
<!--skill-flavor:draft-upload:end-->

<!--skill-flavor:lookup-no-login:start-->
Run every lookup in **one** Bash call.
<!--skill-flavor:lookup-no-login:end-->

<!--skill-flavor:lookup-not-checked-rule:start-->
Mark a box `not checked` only when its lookup ran and exited non-zero. Never write it for a lookup you did not run.
<!--skill-flavor:lookup-not-checked-rule:end-->

<!--skill-flavor:draft-cloud-copy:start-->
The user may have changed the outline on the canvas before answering.
Each turn starts again at a fresh seed of the target ([Validation loop](../SKILL.md#validation-loop)), so their edits are the base. Say so in the reply's one sentence.
<!--skill-flavor:draft-cloud-copy:end-->

<!--skill-flavor:draft-change-it:start-->
- **Change it**: the target now has stages, so run the round trip of the [Validation loop](../SKILL.md#validation-loop): the seed, a narrow edit of the source, `check --baseline`, `compile`, `validate --strict`. Then show it again as the gate does.
<!--skill-flavor:draft-change-it:end-->

<!--skill-flavor:draft-build-loop:start-->
  Finish through the round trip of the [Validation loop](../SKILL.md#validation-loop), as every turn does: the seed first, then `check --baseline`, `compile` into `<Plan>` and `validate --strict`, with `--sdd` when an `sdd.md` exists.
<!--skill-flavor:draft-build-loop:end-->
