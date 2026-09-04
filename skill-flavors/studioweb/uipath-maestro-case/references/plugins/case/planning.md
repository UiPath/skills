<!--skill-flavor:tree-uipx-line:start-->
<!--skill-flavor:tree-uipx-line:end-->

<!--skill-flavor:planning-contract:start-->
Planning-phase contract: T01 emits `caseplan.json` (and any scaffold file Studio Web did not seed) inside `<SolutionDir>/<ProjectName>/`, where `<SolutionDir>` is `/solution`. `uip maestro case init "<ProjectName>"` precedes T01 as Step 6.0; there is no Step 6.0b registration because Studio Web owns the solution manifest.
<!--skill-flavor:planning-contract:end-->

<!--skill-flavor:root-planning-intro:start-->
The root case definition — the top-level container that every other node lives inside. Created exactly once per project. In Studio Web, `uip maestro case init "<ProjectName>"` creates the project in the open solution and seeds its scaffold; T01 then writes `caseplan.json` (and any of the 5 boilerplate files Studio Web did not seed) — see [impl-json.md](impl-json.md).
<!--skill-flavor:root-planning-intro:end-->
