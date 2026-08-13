<!--skill-flavor:project-creation-scope:start-->
- Create a new Flow project through Studio Web's solution-level project-creation capability
<!--skill-flavor:project-creation-scope:end-->

<!--skill-flavor:project-creation:start-->
6. **Create Flow projects with the Studio Web project tool — never with a CLI init command.** Before creating a project, inspect the live ProxyTool schema for `proxy-tools-Solution` and its `CreateProjects` operation. Invoke that operation with the Flow project type using exactly the fields and enum values present in the current schema. Do not hardcode the request shape or tool parameters in the skill; the live schema is the contract.

   **Let Studio Web own project scaffolding and solution metadata.** Do not run `uip solution init`, `uip solution new`, `uip maestro flow init`, or any other local project-setup command. Do not search for, create, edit, or repair a local `.uipx` file. After `CreateProjects` succeeds, inspect the project files exposed by the Studio Web workspace/VFS and edit the generated `.flow` entrypoint. If the creation tool or Flow project type is unavailable, report that capability gap instead of fabricating a local scaffold.
<!--skill-flavor:project-creation:end-->
