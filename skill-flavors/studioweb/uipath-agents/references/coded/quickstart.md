<!--skill-flavor:flow-project-creation:start-->
1. **Use the current Studio Web solution and create the Flow project through the host.** Inspect the live ProxyTool schema for `proxy-tools-Solution` and its `CreateProjects` operation, then invoke it with the Flow project type using only schema-declared fields and enum values.

2. **Locate the generated Flow project.** Inspect the Studio Web workspace/VFS and use the host-exposed project directory and `.flow` entrypoint for all later wiring steps. Do not run `uip solution init` or `uip maestro flow init`; do not create `.uipx`, `project.uiproj`, or generated support files manually. If `CreateProjects` or the Flow project type is unavailable, report the capability gap and stop rather than fabricating a local scaffold.
<!--skill-flavor:flow-project-creation:end-->
