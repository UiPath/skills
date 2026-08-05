<!-- skill-flavor:surface-routing:start -->
## Studio Web capability routing

Read `/skills/synthetic/studioweb-context/SKILL.md` before acting. Studio Web owns the open solution and project entities; project files are exposed under `/solution/<project name>/...`.

This Studio Web contract takes precedence over desktop/local command examples in every deeper reference. Never execute a standalone init, `.uipx` workflow, login/config command, CLI probe/install, local upload/pack/deploy sequence, or Python/Node helper merely because a shared reference shows one. Apply the Studio Web replacement stated here or report that the required capability is unavailable.

**Author**

- Create a standalone Flow only through the live `proxy-tools-Solution` / `CreateProjects` schema. Never run a solution or Flow init command.
- For an existing Flow, read [references/author/CAPABILITY.md](references/author/CAPABILITY.md), inspect the generated project tree, and edit the existing `.flow` file.
- Before a Flow CLI operation, use the current top-level prefix advertised in the per-turn browser-bundle list. Do not assume the desktop `uip maestro flow` prefix; use a flat `uip flow` prefix when that is what the live list exposes.

**Run, publish, and diagnose**

- Before a host-side project action, read `/skills/synthetic/proxy-tools-Flow/SKILL.md` only when the per-turn directives advertise it. Invoke listed tools through `ProxyTool` with the exact live schema.
- Preserve explicit consent before a run that can call real systems. Prefer the advertised `RunProject` host capability. If no relevant host capability is advertised, use only a Flow command exposed by the live browser bundle or report the capability gap.
- Publish the already-open solution through the Studio Web publish surface. Do not upload a local solution, create a local package, or run a local deployment workflow.
- For evaluations, use the live browser-bundle Flow eval surface only when advertised. The solution is already in Studio Web; do not run `uip solution upload` to satisfy an eval prerequisite.

For shared authoring details, use these references:

| Need | Read |
|---|---|
| Create or edit a Flow | [references/author/CAPABILITY.md](references/author/CAPABILITY.md) |
| Greenfield authoring after native project creation | [references/author/references/greenfield.md](references/author/references/greenfield.md) |
| `.flow` format | [references/shared/file-format.md](references/shared/file-format.md) |
| CLI conventions for the browser sandbox | [references/shared/cli-conventions.md](references/shared/cli-conventions.md) |
| Diagnose a failed run | [references/diagnose/CAPABILITY.md](references/diagnose/CAPABILITY.md), using only live-advertised commands/tools |
<!-- skill-flavor:surface-routing:end -->

<!-- skill-flavor:cli-output-handling:start -->
1. **Use `--output json` and prefer `--output-filter` for extraction** whenever the live browser CLI command accepts them. `registry search` returns a flat array of PascalCase objects. When JMESPath cannot express a transform, use the sandbox-provided `jq`; Python and Node are unavailable. Verify the response shape before parsing. See [cli-conventions.md §3](references/shared/cli-conventions.md#3-prefer---output-filter-for-extraction).
<!-- skill-flavor:cli-output-handling:end -->

<!-- skill-flavor:resource-discovery-order:start -->
3. **Search before creating or mocking a resource.** Use the Flow registry operation exposed by the live browser bundle for complete tenant discovery; authentication is inherited, so never run `uip login`. List `/solution` for sibling project entities and use a live local-registry list/search operation when available. Studio Web has no `.uipx`, and an empty keyword search alone is not proof of absence.

   For every named connector or external service, derive the connector key and node type from registry results. Require `--all-folders` for connection discovery, resolve reference IDs against the currently selected connection, and select in this order: curated connector → connector-mode managed HTTP → manual HTTP only after the search proves no connector exists → RPA only when no API is available. A raw token variable or manual HTTP call to a well-known connector-backed service is evidence that discovery was skipped.

   Only after complete discovery may the agent create a missing standalone sibling through the live `CreateProjects` schema, when that schema supports the required type. The sole CLI creation exception is an inline low-code agent inside an existing Flow: `uip agent init "/solution/<FlowProject>" --inline-in-flow`. If creation or local resource discovery is unavailable, report the capability gap or use an explicit mock; never manufacture a project folder, registration file, connector key, or credential.
<!-- skill-flavor:resource-discovery-order:end -->

<!-- skill-flavor:project-creation:start -->
6. **Create standalone Flow projects through Studio Web, never through filesystem scaffolding.** Read `/skills/synthetic/proxy-tools-Solution/SKILL.md`, confirm it advertises `CreateProjects`, and invoke it through `ProxyTool` with `toolName`, `method: "execute"`, and `params` copied from the live schema. Do not hardcode the parameter shape or project-type value. Do not run `uip solution init/new`, `uip flow init`, or `uip maestro flow init`; do not search for or create `.uipx`; and do not `mkdir /solution/<name>`. After creation, list `/solution`, inspect the generated project files, and preserve the host-owned scaffold. If `CreateProjects` or the required type is absent, ask the user to create the Flow in the Studio Web UI.
<!-- skill-flavor:project-creation:end -->

<!-- skill-flavor:node-ownership:start -->
9. **Give every node exactly one author.** Use file tools for user-owned `.flow` JSON and a live-advertised Flow CLI command for CLI-owned connector, connector-trigger, event, and managed-HTTP nodes. Preserve the existing project scaffold and generated sidecars. The inline-agent lifecycle exception remains `uip agent init / refresh / validate --inline-in-flow`; it does not authorize standalone Agent init. Use `jq`, `yq`, `awk`, or coreutils only when the file tools and Flow CLI cannot perform the transform. Python, Node, package managers, and local helper scripts are unavailable. See [author/CAPABILITY.md](references/author/CAPABILITY.md#node-ownership--who-authors-the-node).
<!-- skill-flavor:node-ownership:end -->

<!-- skill-flavor:greenfield-batching:start -->
10. **Batch independent work while respecting the Studio Web entity boundary.** A typical greenfield build is: (T1) inspect the live solution proxy, call `CreateProjects`, then list and read the generated project; (T2) perform registry discovery and edit the `.flow`; (T3) use live-advertised configure, validate, and format operations. Never combine project creation with manual folder creation or an init command. Split turns whenever a later action depends on the host-created entity or a live schema response.
<!-- skill-flavor:greenfield-batching:end -->

<!-- skill-flavor:parser-antipattern:start -->
- **Avoid external parsing for simple extraction.** Prefer `--output-filter`; use the sandbox-provided `jq` only for transforms JMESPath cannot express. Python is unavailable. Verify whether `Data` is an array or object before interpreting an empty result.
<!-- skill-flavor:parser-antipattern:end -->

<!-- skill-flavor:setup-batching-antipattern:start -->
- **Never batch a forbidden init command into setup.** Project creation is a separate host-tool action whose result must exist before file edits. After creation, batch independent registry reads and file operations when their inputs are known.
<!-- skill-flavor:setup-batching-antipattern:end -->
