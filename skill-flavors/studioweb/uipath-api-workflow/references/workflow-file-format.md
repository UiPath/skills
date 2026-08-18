<!--skill-flavor:runtime-description:start-->
JSON files conforming to **CNCF Serverless Workflow DSL 1.0.0** with UiPath task-type extensions. In Studio Web, validate them through the embedded static validator and, after explicit consent, execute them through the freshly inspected `proxy-tools-Api` / `RunProject` schema.
<!--skill-flavor:runtime-description:end-->

<!--skill-flavor:runtime-input-output:start-->
Runtime inputs come from fields declared by the freshly inspected `RunProject` schema or from the calling workflow. Read them as `$workflow.input.<name>` from any task; `$input.<name>` is the current task input. Interpret outputs from the actual `RunProject` result and the workflow's final `Response`, following the live tool contract.
<!--skill-flavor:runtime-input-output:end-->

<!--skill-flavor:project-structure:start-->
## Project Structure in Studio Web

Studio Web owns the project scaffold and solution-level metadata. Create an API Workflow project through the live `CreateProjects` schema, then treat the files exposed by the Studio Web workspace/VFS as the authoritative project tree.

- Inspect the live `CreateProjects` schema immediately before invocation and use exactly its declared parameters and project-type enum values.
- Verify the returned `/solution/<projectName>` directory with `LsDirectory`.
- Edit `/solution/<projectName>/Workflow.json` explicitly, or open the new project and then use `CurrentProject.AbsolutePath`.
- Set embedded CLI `workingDirectory` to the target project root.
- Preserve `WorkflowStart` as the first task in the root sequence and preserve all host-generated project and solution metadata.
- Treat the successful `CreateProjects` result and host-exposed tree as project-creation evidence.
- Report an unavailable creation operation or API Workflow project type as the exact host capability gap.
<!--skill-flavor:project-structure:end-->
