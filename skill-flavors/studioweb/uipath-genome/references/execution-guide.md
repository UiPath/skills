<!--skill-flavor:process-genome-solution:start-->
1. Studio Web works on one open solution, already scaffolded as the workspace root (`/solution`); never create another. Record `/solution` as `SOLUTION_DIR`.
2. Each non-test component becomes one project inside it: create it through its owning skill with that component's scaffolding answers, from `/solution`, using the creation step that skill gives. The host registers every project it creates, so no registration command applies — `uip solution projects add` is Node-CLI-only. Studio Web cannot create function projects; a component owned by `uipath-functions` is listed in the report for the user to create with the local CLI.
<!--skill-flavor:process-genome-solution:end-->

<!--skill-flavor:process-genome-test-project:start-->
3. **All test components share one test project** ([genome-reading-guide.md § Two Levels](genome-reading-guide.md) rule 1). Create `<ProcessName>.Tests` once through `uipath-rpa`'s test-project creation step inside `/solution`, where the host registers it and seeds its own scaffold — no template applies here — and give every test component the same `PROJECT_DIR`: its test cases and data files in a folder named after it (`<ComponentSlug>/`), or at their source objects' paths when the run keeps the source's shape ([source-migration-guide.md § Source steps that are not UI actions](source-migration-guide.md)). The test cases, their failure capture and cleanup, and the shared configuration are authored where the owning skill's Studio Web scope sends RPA authoring.
<!--skill-flavor:process-genome-test-project:end-->

<!--skill-flavor:process-genome-pack:start-->
The host keeps the open solution's resources in sync and packages it only when it is published (`uip solution publish`, the user's call): resource refresh and pack, the dry run included, are Node-CLI-only. Validate and build per project are the last local gate.
<!--skill-flavor:process-genome-pack:end-->

<!--skill-flavor:capability-discovery-scratch:start-->
   - **When that discovery needs a project** (the docs an installed package brings), read the docs of the packages the open solution's projects already install, and the owning skill's own guidance otherwise: Studio Web works on its one open solution, so discovery makes no scratch project.
<!--skill-flavor:capability-discovery-scratch:end-->

<!--skill-flavor:platform-resources-gain:start-->
What the Platform resources options give and rule out: created, the resources and the entities' records are in the tenant, with the build's values, before the user publishes the solution, and an entity exists for the workflows that use it; under None each is left to whoever deploys the solution, and a workflow that uses an entity waits until it exists.
<!--skill-flavor:platform-resources-gain:end-->

<!--skill-flavor:deploy-on-answer:start-->
Publishing the open solution (`uip solution publish`) is the user's call. Once the hand-off is written, the final message says so, and names `open-items.md` as what the tenant it is deployed to still needs.
<!--skill-flavor:deploy-on-answer:end-->
