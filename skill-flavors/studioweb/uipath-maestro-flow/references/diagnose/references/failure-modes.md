<!--skill-flavor:project-creation-recovery-index:start-->
| [Single-nested layout](#single-nested-layout) | A requested Flow project is absent from the host workspace/VFS | `CreateProjects` failed, its result has not propagated, or the Flow project capability is unavailable |
<!--skill-flavor:project-creation-recovery-index:end-->

<!--skill-flavor:project-creation-recovery:start-->
## Single-nested layout

Local single- versus double-nested scaffold recovery does not apply to projects created inside Studio Web. The host owns the solution metadata and generated project tree.

If a requested Flow project is absent, inspect the live ProxyTool schema for `proxy-tools-Solution` and `CreateProjects`, then retry only with schema-declared fields and enum values when the previous request was invalid. Do not run `uip solution init`, `uip maestro flow init`, create or repair `.uipx` metadata, move project folders, or hand-assemble missing generated files.

If `CreateProjects` succeeds but the generated project is still not exposed by the Studio Web workspace/VFS, or if the tool or Flow project type is unavailable, report the host capability/state gap instead of fabricating a local scaffold.
<!--skill-flavor:project-creation-recovery:end-->
