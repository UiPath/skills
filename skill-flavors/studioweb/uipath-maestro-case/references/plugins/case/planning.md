<!--skill-flavor:planning-contract:start-->
Planning-phase contract: T01 emits `caseplan.json` (and any scaffold file Studio Web did not seed) inside `<SolutionDir>/<ProjectName>/`, where `<SolutionDir>` is `/solution`. `uip maestro case init "<ProjectName>"` precedes T01 as Step 6.0; there is no Step 6.0b registration because Studio Web owns the solution manifest.
<!--skill-flavor:planning-contract:end-->

<!--skill-flavor:root-planning-intro:start-->
The root case definition — the top-level container that every other node lives inside. Created exactly once per project. In Studio Web, `uip maestro case init "<ProjectName>"` creates the project in the open solution and seeds its scaffold; T01 then writes `caseplan.json` (and any of the 5 boilerplate files Studio Web did not seed) — see [impl-json.md](impl-json.md).
<!--skill-flavor:root-planning-intro:end-->

<!--skill-flavor:project-tree:start-->
/solution/                         ← the open Studio Web solution (no .uipx on disk)
  <ProjectName>/                   ← created by `uip maestro case init` (Step 6.0, CLI)
    project.uiproj                 ← seeded by Studio Web, else § Scaffold writes
    operate.json                   ← seeded by Studio Web, else § Scaffold writes
    entry-points.json              ← seeded by Studio Web, else § Scaffold writes (empty entryPoints[])
    bindings_v2.json               ← seeded by Studio Web, else § Scaffold writes
    package-descriptor.json        ← seeded by Studio Web, else § Scaffold writes
    caseplan.json                  ← § Write caseplan.json writes
<!--skill-flavor:project-tree:end-->

<!--skill-flavor:naming-canonical:start-->
**Naming (canonical) — the solution identity is fixed and reused by every step.** `<SolutionDir>` = `/solution`, the open Studio Web solution — the same for Step 6.0 and for the Rule-17 Create prerequisite ([registry-discovery.md § Create-on-Missing → 0](../../registry-discovery.md#create-on-missing-build-and-rediscovery)), so nothing can fork. `<ProjectName>` = the case Name (SDD §1 Metadata), sanitized to a valid directory name; Step 6.0 passes it to `uip maestro case init` and T01 reuses it under `/solution/<ProjectName>/`.
<!--skill-flavor:naming-canonical:end-->
