<!--skill-flavor:cli-bookends:start-->
Project creation (`uip maestro case init "<ProjectName>"` from `/solution`) is CLI — see [implementation.md Step 6](../../implementation.md); the open Studio Web solution is the only solution and Studio Web owns its manifest, so there is no registration step. Edit-after-create is out of scope (SKILL regenerates from scratch — see SKILL.md Rule 6); this recipe writes all case fields directly into the initial `caseplan.json`.
<!--skill-flavor:cli-bookends:end-->

<!--skill-flavor:preflight-solution-exists:start-->
1. **Solution is the open one.** `<SolutionDir>` is `/solution`; Studio Web owns the manifest, so there is no `.uipx` to check.
<!--skill-flavor:preflight-solution-exists:end-->

<!--skill-flavor:purpose-intro:start-->
Complete the project on disk in a single plugin invocation — whichever of the 5 scaffold files Studio Web did not seed at Step 6.0 (`uip maestro case init`), plus `caseplan.json`. Runs exactly once per project, right after Step 6.0. Two sections:
<!--skill-flavor:purpose-intro:end-->

<!--skill-flavor:purpose-scaffold-item:start-->
1. **§ Scaffold** — inventory the seeded project dir and write only the missing boilerplate files (`project.uiproj`, `operate.json`, `entry-points.json`, `bindings_v2.json`, `package-descriptor.json`) directly.
<!--skill-flavor:purpose-scaffold-item:end-->

<!--skill-flavor:scaffold-intro:start-->
Runs before § Write caseplan.json. Studio Web seeds some or all of the 5 static JSON files when `uip maestro case init` creates the project; write only the ones that are missing, directly. All substitution is name-for-name — no subprocess.
<!--skill-flavor:scaffold-intro:end-->

<!--skill-flavor:preflight-target-clean:start-->
3. **Inventory the seeded scaffold.** List `<SolutionDir>/<ProjectName>/`. Every one of the 5 scaffold files that already exists was seeded by Studio Web at Step 6.0 — keep it untouched and skip its entry under § Files to write. Write only the missing ones. Do not merge into a seeded file. `caseplan.json` is governed by § Pre-write checks (an existing one is overwritten there), not by this item.
<!--skill-flavor:preflight-target-clean:end-->
