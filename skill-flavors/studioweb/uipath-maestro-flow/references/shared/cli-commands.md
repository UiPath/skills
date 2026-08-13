<!--skill-flavor:project-creation:start-->
<a id="uip-maestro-flow-init"></a>

## Creating a Flow project in Studio Web

`uip maestro flow init` and the corresponding solution-init commands are not supported project-creation paths in Studio Web. The host must create and register the project in the current solution.

1. Inspect the live ProxyTool schema for `proxy-tools-Solution` and its `CreateProjects` operation.
2. Invoke `CreateProjects` with the Flow project type, using exactly the fields and enum values declared by the current schema. Do not copy or hardcode a request shape from this reference.
3. After the operation succeeds, inspect the project files exposed by the Studio Web workspace/VFS and edit the generated `.flow` entrypoint.

Do not run `uip solution init`, `uip solution new`, or `uip maestro flow init`; do not create project support files or `.uipx` metadata manually. If the tool or Flow project type is unavailable, report the capability gap rather than falling back to a local scaffold.
<!--skill-flavor:project-creation:end-->
