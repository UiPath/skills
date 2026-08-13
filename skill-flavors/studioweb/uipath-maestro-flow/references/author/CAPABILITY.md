<!--skill-flavor:project-creation-scope:start-->
- Create a new Flow project through Studio Web's live `proxy-tools-Solution` / `CreateProjects` capability
<!--skill-flavor:project-creation-scope:end-->

<!--skill-flavor:project-creation-antipatterns:start-->
- **Do NOT** run `uip solution init`, `uip solution new`, `uip maestro flow init`, or any local setup command in Studio Web. Inspect and call the live `proxy-tools-Solution` / `CreateProjects` schema instead.
- **Do NOT** search for, create, edit, or repair `.uipx` solution metadata in Studio Web; the host owns that metadata.
- **Do NOT** hand-assemble a replacement Flow project when `CreateProjects` or the Flow project type is unavailable. Report the missing capability so the user can choose how to proceed.
- **Do NOT** use a locally constructed directory layout as evidence that a project was created correctly in Studio Web. The `CreateProjects` result and host-exposed project tree are authoritative.
<!--skill-flavor:project-creation-antipatterns:end-->
