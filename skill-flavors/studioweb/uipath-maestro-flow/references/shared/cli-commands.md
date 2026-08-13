<!--skill-flavor:project-creation:start-->
<a id="uip-maestro-flow-init"></a>

## Creating a Flow project in Studio Web

Studio Web creates and registers Flow projects in the current host solution.

1. Inspect the live ProxyTool schema for `proxy-tools-Solution` and its `CreateProjects` operation.
2. Invoke `CreateProjects` with the Flow project type, using exactly the fields and enum values declared by the current schema. Treat the live schema as the request contract.
3. After the operation succeeds, inspect the project files exposed by the Studio Web workspace/VFS and edit the generated `.flow` entrypoint.

If the tool or Flow project type is unavailable, report the capability gap and await user direction.
<!--skill-flavor:project-creation:end-->
