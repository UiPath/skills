<!-- skill-flavor:project-structure:start -->
## Project Structure in Studio Web

Studio Web owns the project scaffold and solution-level metadata. Create an API Workflow project through the live `proxy-tools-Solution` / `CreateProjects` schema, then treat the files exposed by the Studio Web workspace/VFS as the authoritative project tree.

- Do not run a CLI init command or recreate a desktop/local project layout by hand.
- Do not expect, search for, create, or edit a local `.uipx` solution metadata file.
- Do not hardcode `CreateProjects` parameters or project-type enum values; inspect the live schema immediately before invocation.
- After creation, locate the generated workflow entrypoint from the files/tool result and edit that file. Preserve `WorkflowStart` as the first task in the root sequence.
- If the generated tree differs from a local CLI scaffold, keep the Studio Web-generated tree. Do not add local-only files merely to make it resemble the default flavor.

If `CreateProjects` or the API Workflow project type is not exposed, report the capability gap instead of fabricating solution metadata or a partial project.
<!-- skill-flavor:project-structure:end -->
