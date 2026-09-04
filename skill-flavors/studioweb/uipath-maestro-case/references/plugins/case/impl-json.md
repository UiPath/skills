<!--skill-flavor:cli-bookends:start-->
Project creation (`uip maestro case init "<ProjectName>"` from `/solution`) is CLI — see [implementation.md Step 6](../../implementation.md); the open Studio Web solution is the only solution and Studio Web owns its manifest, so there is no registration step. Edit-after-create is out of scope (SKILL regenerates from scratch — see SKILL.md Rule 6); this recipe writes all case fields directly into the initial `caseplan.json`.
<!--skill-flavor:cli-bookends:end-->

<!--skill-flavor:preflight-solution-exists:start-->
1. **Solution is the open one.** `<SolutionDir>` is `/solution`; Studio Web owns the manifest, so there is no `.uipx` to check.
<!--skill-flavor:preflight-solution-exists:end-->
