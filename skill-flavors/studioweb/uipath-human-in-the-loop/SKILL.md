<!--skill-flavor:flow-project-creation:start-->
**If no `.flow` file exists and surface is Flow**, create the Flow project through Studio Web's solution-level project capability:

1. Inspect the live ProxyTool schema for `proxy-tools-Solution` and its `CreateProjects` operation.
2. Invoke `CreateProjects` for a Flow project using only the fields and enum values declared by that live schema. Never guess or hardcode the ProxyTool request shape.
3. After creation succeeds, inspect the project files exposed by the Studio Web workspace/VFS, locate the generated `.flow` entrypoint, and use that host-exposed tree as the source of truth for the HITL edit.

Do not run `uip solution init`, `uip solution new`, `uip maestro flow init`, or any other local project-setup command. Do not search for, create, edit, or repair `.uipx`, `project.uiproj`, or generated support files. If `CreateProjects` or the Flow project type is unavailable, report the capability gap instead of fabricating a local scaffold.
<!--skill-flavor:flow-project-creation:end-->
