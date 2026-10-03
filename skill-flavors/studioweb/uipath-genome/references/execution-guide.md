<!--skill-flavor:process-genome-solution:start-->
1. Studio Web works on one open solution, already scaffolded as the workspace root (`/solution`); never create another. Record `/solution` as `SOLUTION_DIR`.
2. Each non-test component becomes one project inside it: create it through its owning skill with that component's scaffolding answers (`uip <family> init <Name>` from `/solution`). The host registers every project it creates, so no registration command applies — `uip solution projects add` is Node-CLI-only. Studio Web cannot create function or coded-app projects; a component owned by `uipath-functions` or `uipath-coded-apps` is listed in the report for the user to create with the local CLI.
<!--skill-flavor:process-genome-solution:end-->
