<!--skill-flavor:runtime-description:start-->
JSON files conforming to **CNCF Serverless Workflow DSL 1.0.0** with UiPath task-type extensions. In Studio Web, validate them through the embedded static validator and execute them only through consent-gated, schema-inspected `proxy-tools-Api` / `RunProject`.
<!--skill-flavor:runtime-description:end-->

<!--skill-flavor:runtime-input-output:start-->
Runtime inputs come from fields declared by the freshly inspected `RunProject` schema or from the calling workflow. Read them as `$workflow.input.<name>` from any task; `$input.<name>` is only the current task input. Interpret outputs from the actual `RunProject` result and the workflow's final `Response`, following the live tool contract rather than assuming a desktop CLI envelope.
<!--skill-flavor:runtime-input-output:end-->

<!--skill-flavor:project-structure:start-->
## Project Structure in Studio Web

Studio Web owns the project scaffold and solution-level metadata. Create an API Workflow project through the live `proxy-tools-Solution` / `CreateProjects` schema, then treat the files exposed by the Studio Web workspace/VFS as the authoritative project tree.

- Do not run a CLI init command or recreate a desktop/local project layout by hand.
- Do not expect, search for, create, or edit a local `.uipx` solution metadata file.
- Do not hardcode `CreateProjects` parameters or project-type enum values; inspect the live schema immediately before invocation.
- `CreateProjects` does not switch the active designer project. After success, verify the generated `/solution/<projectName>` directory with `LsDirectory`; do not assume `CurrentProject` now names the new project.
- Edit `/solution/<projectName>/Workflow.json` explicitly, or open the new project and then use `CurrentProject.AbsolutePath`. For embedded CLI calls, set `workingDirectory` to that project root; commands otherwise start at `/solution` and can target the wrong project.
- Preserve `WorkflowStart` as the first task in the root sequence. Do not edit the host-generated `project.uiproj`, `entry-points.json`, `bindings_v2.json`, `resources/`, or `userProfile/` metadata.
- If the generated tree differs from a local CLI scaffold, keep the Studio Web-generated tree. Do not add local-only files merely to make it resemble the default flavor.

If `CreateProjects` or the API Workflow project type is not exposed, report the capability gap instead of fabricating solution metadata or a partial project.
<!--skill-flavor:project-structure:end-->
