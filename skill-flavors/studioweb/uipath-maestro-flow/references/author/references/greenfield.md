<!--skill-flavor:project-creation:start-->
## Step 2 — Create the Flow project through Studio Web **[T1]**

Studio Web already supplies the target solution and owns its project scaffolding and metadata. Do not inspect the workspace for `.uipx` files, create a local solution, or run `uip maestro flow init`.

<a id="canonical-t1-chain--issue-this-as-one-bash-call"></a>

### Canonical T1 chain — issue setup in ONE assistant message

1. Inspect the live ProxyTool schema for `proxy-tools-Solution` and its `CreateProjects` operation.
2. Invoke `CreateProjects` for a Flow project using only the fields and enum values declared by that live schema. Never guess or hardcode the ProxyTool request shape.
3. In parallel, refresh the Flow registry as described in Step 3 and fetch any independent OOTB node definitions needed for authoring.
4. After project creation succeeds, inspect the Studio Web workspace/VFS, locate the generated project and `.flow` entrypoint, and use that host-exposed tree as the source of truth for every subsequent edit.

Do not create project folders, `project.uiproj`, generated support files, or solution registration metadata by hand. If `CreateProjects` or the Flow project type is not exposed, report the capability gap and stop project creation instead of falling back to a local CLI scaffold.
<!--skill-flavor:project-creation:end-->
