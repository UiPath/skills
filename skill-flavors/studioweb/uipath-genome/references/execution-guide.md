<!--skill-flavor:process-genome-solution:start-->
1. Studio Web works on one open solution, already scaffolded as the workspace root (`/solution`); never create another. Record `/solution` as `SOLUTION_DIR`.
2. Each non-test component becomes one project inside it: create it through its owning skill with that component's scaffolding answers (`uip <family> init <Name>` from `/solution`). The host registers every project it creates, so no registration command applies — `uip solution projects add` is Node-CLI-only. Studio Web cannot create function or coded-app projects; a component owned by `uipath-functions` or `uipath-coded-apps` is listed in the report for the user to create with the local CLI.
<!--skill-flavor:process-genome-solution:end-->

<!--skill-flavor:process-genome-test-project:start-->
3. **All test components share one test project** ([genome-format-guide.md § Two Levels](genome-format-guide.md) rule 1). Create `<ProcessName>.Tests` once through `uipath-rpa`'s test-project creation step inside `/solution`, where the host registers it, and give every test component the same `PROJECT_DIR`: its test cases and data files in a folder named after it (`<ComponentSlug>/`), or at their source objects' paths when the run keeps the source's shape ([source-migration-guide.md § Source steps that are not UI actions](source-migration-guide.md)), plus a shared `Config/` folder for the configuration workflow.
<!--skill-flavor:process-genome-test-project:end-->

<!--skill-flavor:process-genome-pack:start-->
The host keeps the open solution's resources in sync and packages it only when it is published (`uip solution publish`, the user's call): resource refresh and pack, the dry run included, are Node-CLI-only. Validate and build per project are the last local gate.
<!--skill-flavor:process-genome-pack:end-->

<!--skill-flavor:report-gate:start-->
Gate: validate + build per project (errors / warnings), libraries packed to <feed>; runs performed or "compile only — no reachable application"
<!--skill-flavor:report-gate:end-->
