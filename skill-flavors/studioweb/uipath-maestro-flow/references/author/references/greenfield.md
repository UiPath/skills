<!-- skill-flavor:greenfield-setup:start -->
## Studio Web execution map

The project entity must exist before its files can be edited. Treat host creation and file authoring as separate dependency stages:

| Turn | Work |
|---|---|
| **T1 — Create** | Read `/skills/synthetic/proxy-tools-Solution/SKILL.md`; when it advertises `CreateProjects`, invoke it through `ProxyTool` using the exact live schema. If unavailable, ask the user to create the Flow in the UI and stop. |
| **T2 — Inspect and discover** | List `/solution`, locate the new project, read its generated `.flow` and metadata, inspect the live browser-bundle CLI prefix, and run independent registry discovery calls. |
| **T3 — Author and finalize** | Edit the existing `.flow`, configure CLI-owned nodes through the live Flow prefix, then validate and format when those operations are advertised. |

Do not probe or install `uip`; it is already registered. Do not run `uip login`; authentication comes from the active Studio Web session. Python, Node, npm, `uv`, and package installation are unavailable.

## Create the Flow project

1. Read `/skills/synthetic/proxy-tools-Solution/SKILL.md`.
2. Confirm the live skill exposes `CreateProjects` and inspect its parameter table/example.
3. Call it through `ProxyTool` with `toolName`, `method: "execute"`, and `params` derived only from that live schema. Do not hardcode the project-type enum or request shape.
4. List `/solution` and locate the created project by its returned or requested display name.
5. Inspect the generated tree and open the existing `.flow` file. Preserve `project.uiproj`, `entry-points.json`, and every other host-owned sidecar.

Never run `uip solution init/new`, `uip flow init`, or `uip maestro flow init`. Never search for `.uipx`, manually create a project folder, or reproduce a desktop scaffold. Studio Web solutions are backend entities and `/solution` is a project mount.

## Registry discovery

Use the Flow prefix advertised in the per-turn browser-bundle list, then inspect `--help` when exact subcommands or options are needed. Authentication is automatic. Use complete registry searches before selecting a connector or concluding a resource is absent. For sibling projects, combine `/solution` discovery with any live-advertised local registry list/search operation; there is no `.uipx` manifest to inspect.

For each named external service, search the complete registry first, then select in this order: curated connector activity → connector-authenticated managed HTTP → manual HTTP only when no connector exists → RPA only when the system exposes no usable API. Fetch the exact definition for every selected node type; never guess a node type, port, input field, connector key, or definition. Use `/solution` plus live local-registry operations for sibling resources.
<!-- skill-flavor:greenfield-setup:end -->

<!-- skill-flavor:authoring-execution:start -->
## Author the generated Flow

1. Read the `.flow` created by Studio Web and preserve its top-level version, IDs, generated trigger, and host-owned sidecars.
2. Classify each node as user-owned or CLI-owned using [Author — Node ownership](../CAPABILITY.md#node-ownership--who-authors-the-node).
3. Add user-owned nodes, definitions, edges, variables, and layout with targeted file edits anchored to the text just read. Fetch each definition from the live registry; never hand-author it.
4. Add and configure connector, connector-trigger, event, and managed-HTTP nodes only through the live-advertised Flow CLI operations.
5. Keep the inline-agent exception scoped to `uip agent init "/solution/<FlowProject>" --inline-in-flow`; edit the Flow node and wiring in the `.flow`.

Do not infer what an init scaffold would have contained, run helper scripts, or use Python/Node. If the generated Flow is incomplete or a required registry/node capability is missing, report that boundary instead of fabricating metadata.
<!-- skill-flavor:authoring-execution:end -->

<!-- skill-flavor:validation-format:start -->
## Validate and format

Use the Flow validation and format operations advertised by the current browser bundle or project ProxyTool. Use the live prefix and inspect `--help` for exact syntax. Configure every CLI-owned node before validation, resolve warnings as build defects, and format only after validation succeeds.

If validation fails, apply a targeted `.flow` edit and rerun the exposed validation. If validation or format is not exposed in this session, report that exact gap; do not install/update a CLI, invoke a desktop prefix, or treat a run as validation.
<!-- skill-flavor:validation-format:end -->

<!-- skill-flavor:completion-handoff:start -->
## Completion output

Report:

1. Absolute `.flow` path under `/solution/<project>/`.
2. Nodes, edges, and logic added.
3. Validation and format result, or the exact missing capability.
4. Mock placeholders and unresolved connections.
5. The selected next action.

### Next action

| Option | What it does |
|---|---|
| **Keep editing** | Leave the project in its current Studio Web state. |
| **Run the Flow** | Read the advertised `proxy-tools-Flow` skill and invoke `RunProject`, or use a live-advertised browser Flow debug command. Obtain explicit consent first because the Flow can call real systems. |
| **Publish** | Use the Studio Web publish surface, normally `uip solution publish` or a live-advertised Flow publish command. The request is asynchronous; direct the user to Publish history for final status. |
| **Something else** | Accept a free-form request and use only capabilities exposed in the current Studio Web session. |

Do not offer local upload, pack, or deploy actions. The solution is already open in Studio Web, packaging is handled by Studio Web publishing, and deployment outside the supported publish flow requires the UI or an external local environment.
<!-- skill-flavor:completion-handoff:end -->
