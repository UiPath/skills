# Author — Create and edit `.flow` files

Capability index for building new flows (greenfield) and editing existing flows (brownfield). Author owns everything that happens on disk, locally, without `uip login`. Authoring journeys terminate at `validate` + `tidy`; from there, hand off to [operate/CAPABILITY.md](../operate/CAPABILITY.md) to publish, run, or debug.

> **Where you came from / where to go next.** Author is upstream of Operate (build the flow → ship it) and upstream of Diagnose only via Operate (build → run → diagnose). Publish/run/lifecycle lives in [operate/CAPABILITY.md](../operate/CAPABILITY.md); fault triage lives in [diagnose/CAPABILITY.md](../diagnose/CAPABILITY.md).
>
> **Inherits universal rules from [SKILL.md](../../SKILL.md)** — `--output json`, no `flow debug` without consent, resource discovery order, never invoke other skills automatically, AskUserQuestion dropdown pattern, solution layout, **plain-English narration per logical step**, **granular `TodoWrite` list above the trivial threshold**. The rules below are author-scoped and apply on top.

## When to use this capability

- Create a new Flow project with `uip maestro flow init`
- Edit a `.flow` file — adding nodes, edges, or logic
- Explore available node types via the registry
- Validate a Flow file locally
- Manage variables, subflows, expressions, and output wiring
- Choose between Edit / Write and CLI editing strategies
- Configure connector, connector-trigger, or inline-agent nodes
- Plan a complex flow before building

## Critical rules

1. **Always validate node types against the registry before building.** Use `registry search`/`list` for discovery and `registry get` for detailed metadata and definitions.
2. **Default to `Edit` / `Write` for every `.flow` mutation.** Use the `uip maestro flow node` / `edge` / `variable` CLI **only** for the carve-outs called out in [editing-operations.md](references/editing-operations.md) (connector, connector-trigger, inline-agent), or when the user explicitly requests CLI. Edit/Write produces a reviewable line-by-line diff; the CLI returns an opaque "node added" response.
3. **ALWAYS follow the relevant plugin in [plugins/](references/plugins/) for every node type.** Each plugin has a `planning.md` (when to use, selection heuristics, ports) and `impl.md` (registry validation, JSON structure, CLI commands, configuration, debug). For connector nodes, the [connector](references/plugins/connector/impl.md) plugin covers connection binding, enriched metadata, and field resolution — required before building. Without this, node configuration will be wrong — errors that `flow validate` does not catch.
4. **ALWAYS check for existing connections** before using any node that requires one — connector activities, connector triggers, and managed HTTP nodes in connector mode. **If no healthy connection exists for the target connector, STOP.** Surface it in **Open Questions** during planning. See the relevant plugin for recovery steps: [connector/impl.md](references/plugins/connector/impl.md), [connector-trigger/impl.md](references/plugins/connector-trigger/impl.md), [http/impl.md](references/plugins/http/impl.md).
5. **Edit `<ProjectName>.flow` only** — other generated files (`bindings_v2.json`, `entry-points.json`, `operate.json`, `package-descriptor.json`) are managed by the CLI and may be overwritten. To declare flow inputs/outputs, add variables in the `.flow` file (see [shared/file-format.md](../shared/file-format.md)).
6. **`targetPort` is required on every edge** — `validate` rejects edges without it.
7. **Every node type needs a `definitions` entry** — copy from `uip maestro flow registry get <nodeType>` output. Never hand-write definitions. The definition is the sole source for BPMN type (`model.type`), serviceType, event definitions, and binding/context templates — none of that belongs on the instance.
8. **Script nodes must `return` an object** — `return { key: value }`, not a bare scalar.
9. **Validate once at the end** — run `uip maestro flow validate` only after all nodes, edges, and configuration are complete. Do not validate after each individual node add or edit — intermediate states are expected to be invalid.
10. **Manage variables with `Edit` against the `.flow` file** — there are no CLI commands for variable management. Use `Edit` to add/remove/update entries in the `variables` section of the `.flow` file. See [shared/variables-and-expressions.md](../shared/variables-and-expressions.md).
11. **Every `out` variable must be mapped on every reachable End node** — missing output mappings cause runtime errors. See [shared/variables-and-expressions.md](../shared/variables-and-expressions.md).
12. **`=js:` prefix is REQUIRED on every `$vars`/`$metadata`/`$self` reference in a value field.** That includes connector node `inputs.detail.bodyParameters` / `queryParameters` / `pathParameters`, HTTP `url`/`headers`/`body`, end node output `source`, variable update `expression`, loop `collection`, and subflow `inputs.<id>.source`. Without `=js:`, the BPMN runtime sees a literal string (e.g. `"vars.X.output.Id"`) — `flow validate` does not catch this; it manifests at runtime as the wrong value bound to the activity input (MST-9107). Do NOT use `=js:` on condition expressions (decision `expression`, switch case `expression`, HTTP branch `conditionExpression`) — those are always evaluated as JS automatically. See [shared/node-output-wiring.md](../shared/node-output-wiring.md) for the canonical rule and per-node-type field reference, and [shared/variables-and-expressions.md](../shared/variables-and-expressions.md) for the underlying expression system.
13. **Always run `flow tidy` after edits** — `uip maestro flow tidy <ProjectName>.flow` is the canonical layout step. Tidy arranges nodes horizontally, sets every node's `size` to `{ "width": 96, "height": 96 }`, and recurses into subflows (`subflows[<id>].layout`). Skipping tidy is the most common cause of misshapen rectangles in Studio Web.
14. **Don't hand-write `layout.nodes` or `subflows[<id>].layout`** — these are owned by `flow tidy`. When authoring nodes, any placeholder `position` is fine (e.g. `{ x: 0, y: 0 }`); tidy rewrites it on save. Sticky notes (`type: "stickyNote"`) are the one exception — tidy preserves their custom size and position. See [shared/file-format.md — Layout](../shared/file-format.md#layout).
15. **Every node that produces data MUST have `outputs` on the node instance** — Without an `outputs` block, downstream `$vars` references will not resolve at runtime. Action nodes need `output` + `error`; trigger nodes need `output` only; end/terminate nodes do not use this pattern. See [shared/file-format.md — Node outputs](../shared/file-format.md#node-outputs). **Wrong:** relying on `outputDefinition` in `definitions` alone. **Right:** `outputs` on the node instance itself.
16. **Node instances have no `model` block** — BPMN type, serviceType, version, event definitions, and all binding/context templates live in the node's **definition** (in the top-level `definitions[]` array, copied verbatim from `registry get`). The runtime hydrates these from the definition at serialization time. Instance-specific identity fields live under `inputs`: `entryPointId`, `isDefaultEntryPoint` (triggers), `source` (inline agents), `color`/`content` (sticky notes).

## Workflow

| Journey | Read |
| --- | --- |
| Create a new flow from scratch | [greenfield.md](references/greenfield.md) |
| Edit an existing flow | [brownfield.md](references/brownfield.md) |

## Common tasks

| I need to... | Read these |
| --- | --- |
| **Create a new flow** | [greenfield.md](references/greenfield.md) |
| **Edit an existing flow** | [brownfield.md](references/brownfield.md) + [editing-operations.md](references/editing-operations.md) |
| **Add/delete/wire nodes and edges** | [editing-operations.md](references/editing-operations.md) (strategy selection) + relevant plugin's `impl.md` (node-specific inputs) |
| **Generate a flow plan** | [planning-arch.md](references/planning-arch.md) + [planning-impl.md](references/planning-impl.md) |
| **Choose the right node type** | [planning-arch.md — Plugin Index](references/planning-arch.md#plugin-index) + relevant plugin's `planning.md` |
| **Understand the .flow JSON format** | [shared/file-format.md](../shared/file-format.md) |
| **Look up CLI commands** | [shared/cli-commands.md](../shared/cli-commands.md) |
| **Add a Script node** | [plugins/script/impl.md](references/plugins/script/impl.md) |
| **Wire nodes with edges** | [editing-operations.md](references/editing-operations.md) + [shared/file-format.md — Standard ports](../shared/file-format.md) |
| **Find the right node type** | Run `uip maestro flow registry search <keyword>` |
| **Work with connector nodes** | [plugins/connector/](references/plugins/connector/) + [/uipath:uipath-platform](/uipath:uipath-platform) for Integration Service |
| **Manage variables and expressions** | [shared/variables-and-expressions.md](../shared/variables-and-expressions.md) + [Edit/Write: Variable Operations](references/editing-operations-json.md#variable-operations) |
| **Write `=js:` expressions** | [shared/variables-and-expressions.md](../shared/variables-and-expressions.md) |
| **Wire one node's output into another node's input** | [shared/node-output-wiring.md](../shared/node-output-wiring.md) |
| **Orchestrate RPA, agents, apps** | Relevant resource plugin: [rpa](references/plugins/rpa/), [agent](references/plugins/agent/), [agentic-process](references/plugins/agentic-process/), [flow](references/plugins/flow/), [api-workflow](references/plugins/api-workflow/), [hitl](references/plugins/hitl/) |
| **Embed an AI agent tightly coupled to this flow** | [plugins/inline-agent/](references/plugins/inline-agent/) |
| **Create a resource that doesn't exist yet** | Use `core.logic.mock` placeholder — see [editing-operations-cli.md](references/editing-operations-cli.md#replace-a-mock-with-a-real-resource-node) + relevant plugin's `impl.md` |
| **Add data transform nodes** | [plugins/transform/impl.md](references/plugins/transform/impl.md) |
| **Create a subflow** | [plugins/subflow/impl.md](references/plugins/subflow/impl.md) + [Edit/Write: Create a subflow](references/editing-operations-json.md#create-a-subflow) |
| **Add a delay or scheduled trigger** | [plugins/delay/](references/plugins/delay/) or [plugins/scheduled-trigger/](references/plugins/scheduled-trigger/) |
| **Use queue nodes** | [plugins/queue/impl.md](references/plugins/queue/impl.md) |

## Anti-patterns

- **Never run `uip maestro flow init` outside a solution directory** — the resulting `.flow` file MUST sit at `<Solution>/<Project>/<Project>.flow` (double-nested). Running `flow init` from a bare cwd, from the user's home, or from the parent of `<Solution>/` produces a single-nested `<Project>/<Project>.flow` layout that fails Studio Web upload, packaging, and the `uip solution project add` wiring. Always complete the solution scaffold first, `cd` into the solution dir, then init. Run the self-check (`ls <Solution>/<Project>/<Project>.flow`) before continuing.
- **Never guess node schemas** — use `registry get` for all node types. Guessed port names or input fields cause silent wiring failures.
- **Never skip capability discovery for connector nodes** — run `registry search` to confirm the connector exists and what operations it supports before building. See [connector/planning.md](references/plugins/connector/planning.md). Skipping this is the #1 cause of designing around a connector that doesn't exist or an operation it doesn't support.
- **Never edit `content/*.bpmn`** — it is auto-generated from the `.flow` file and will be overwritten.
- **Never use `core.logic.mock` when the resource is in the same solution** — use `--local` discovery instead. Mock placeholders are only for resources that are not in the current solution and not yet published.
- **Never hand-write `definitions` entries** — always copy from registry output. Hand-written definitions have wrong port schemas and cause validation failures.
- **Never put a `model` block on node instances** — BPMN type, serviceType, event definition, binding templates, and context templates all live in the node's **definition** (copied verbatim from `registry get` into `definitions[]`). Instances carry only per-instance data: `inputs`, `outputs`, `display`. Identity fields like `entryPointId` / `isDefaultEntryPoint` (triggers), `source` (inline agents), and `color` / `content` (sticky notes) live under `inputs`.
- **Never author `model.context[]` on resource-node instances** — resource-node instances have no `model` block. For `uipath.core.*` resource nodes (rpa, agent, flow, agentic-process, api-workflow, hitl), the definition (from `registry get`) already carries `model.context[]` with `<bindings.{name}>` placeholders. Your job is to add matching entries to the top-level `bindings[]` array — two entries per resource node (`name` + `folderPath`) with `resourceKey` matching the definition's `model.bindings.resourceKey`. At BPMN emit, the runtime rewrites `<bindings.{name}>` → `=bindings.{id}` via `(resourceKey, name)` matching. Without the top-level `bindings[]` entries, `uip maestro flow validate` passes but `uip maestro flow debug` fails with "Folder does not exist or the user does not have access to the folder." See the resource plugin's `impl.md`.
- **Never put a `ui` block on node instances** — position and size belong in the top-level `layout.nodes` object. Nodes with `"ui": { "position": ... }` use the wrong format and may not render correctly in Studio Web.
- **Never skip `flow tidy` before publish or debug** — tidy is the only thing that guarantees square 96×96 nodes and a clean horizontal layout in Studio Web. Hand-written `layout` data with non-96 sizes (e.g., `{ width: 200, height: 80 }`) renders as misshapen rectangles until tidy normalizes the file (the MST-9061 failure mode). See rule #13 above.
- **Never omit `outputs` on nodes that produce data** — action nodes need `output` + `error`, trigger nodes need `output`. The `outputDefinition` in `definitions` is for the registry schema, not for runtime binding — without `outputs` on the node instance, `$vars` references downstream will fail silently.
- **Never validate after every individual edit** — intermediate flow states (e.g., node added but not yet wired) are expected to be invalid. Run `uip maestro flow validate` once after the full build is complete.
- **Never use `console.log` in script nodes** — `console` is not available in the Jint runtime. Use `return { debug: value }` to inspect values.
- **Never forget output mapping on End nodes** — every `out` variable in `variables.globals` must have a `source` expression in every reachable End node's `outputs`. Missing mappings cause silent runtime failures.
- **Never update `in` variables** — only `inout` variables can be modified via `variableUpdates`. Input variables are read-only after flow start.
- **Never reference parent-scope `$vars` inside a subflow** — subflows have isolated scope. Pass values explicitly via subflow inputs.
- **Never use `core.action.http` (v1) for connector-authenticated requests** — the v1 node's `authenticationType: "connection"` input does not pass IS credentials at runtime. Use `core.action.http.v2` (Managed HTTP Request) instead. See [http/planning.md](references/plugins/http/planning.md).
- **Never hand-write `inputs.detail` for managed HTTP nodes** — run `uip maestro flow node configure` to populate the `inputs.detail` structure, generate `bindings_v2.json`, and create the connection resource file. Hand-written configurations miss the `essentialConfiguration` block and fail at runtime.
- **Never write `$vars.X` (or `$metadata.X`, `$self.X`) without `=js:`** in any connector `bodyParameters`/`queryParameters`/`pathParameters`, HTTP input field, end-node output `source`, variable update, loop collection, or subflow input. The serializer rewrites `$vars` → `vars` whether or not the prefix is present, so a missing prefix yields a literal string `"vars.X.output.Y"` at runtime — `flow validate` passes, the failure shows up only in `flow debug`. There is no `nodes.X.output.Y` syntax — it is invented and silently produces a literal string. See [shared/node-output-wiring.md](../shared/node-output-wiring.md) for the per-node-type field reference (MST-9107).
- **Never reuse a reference ID (mailbox folder, Slack channel, Jira project, Google Sheet, etc.) from a prior flow or session** — reference IDs are scoped to the specific authenticated account behind the connection. A `parentFolderId` from one Outlook mailbox is invalid in another; a Slack channel ID from one workspace is invalid in another. A reused ID passes `flow validate` and `node configure` cleanly, then faults silently at runtime with no resolvable error. Always re-resolve via `uip is resources execute list <connector-key> <objectName> --connection-id <CURRENT_CONNECTION_ID> --output json` against the connection bound to this flow — do not paste a value you saw in another flow. See [connector/impl.md — Step 4](references/plugins/connector/impl.md) and [connector-trigger/impl.md — Step 3](references/plugins/connector-trigger/impl.md).

## References

### Author-scoped

- [greenfield.md](references/greenfield.md) — create-new-flow journey
- [brownfield.md](references/brownfield.md) — edit-existing-flow journey
- [editing-operations.md](references/editing-operations.md) — strategy selection (Edit / Write default vs CLI carve-outs)
- [editing-operations-json.md](references/editing-operations-json.md) — Edit / Write recipes (default)
- [editing-operations-cli.md](references/editing-operations-cli.md) — CLI carve-outs and opt-in
- [planning-arch.md](references/planning-arch.md) — capability discovery, plugin index, topology design
- [planning-impl.md](references/planning-impl.md) — registry lookups, connection binding, wiring rules
- [plugins/](references/plugins/) — per-node-type planning + impl docs:
  - [connector](references/plugins/connector/) — IS connector nodes
    - [connector/data-fabric](references/plugins/connector/data-fabric/) — Data Fabric entity activities (Query / Create / Update / Delete / Get by ID)
  - [connector-trigger](references/plugins/connector-trigger/)
  - [script](references/plugins/script/) — Jint ES2020 JavaScript
  - [http](references/plugins/http/) — `core.action.http.v2` (Managed HTTP Request)
  - [decision](references/plugins/decision/) — binary if/else
  - [switch](references/plugins/switch/) — multi-way branching
  - [loop](references/plugins/loop/) — collection iteration
  - [merge](references/plugins/merge/) — parallel branch sync
  - [end](references/plugins/end/) — graceful flow completion
  - [terminate](references/plugins/terminate/) — abort on fatal error
  - [transform](references/plugins/transform/) — declarative filter/map/group-by
  - [delay](references/plugins/delay/) — duration or date-based pause
  - [subflow](references/plugins/subflow/) — reusable node groups
  - [scheduled-trigger](references/plugins/scheduled-trigger/) — recurring schedule
  - [rpa](references/plugins/rpa/) — published RPA processes
  - [agentic-process](references/plugins/agentic-process/) — published orchestration processes
  - [flow](references/plugins/flow/) — published flows as subprocesses
  - [api-workflow](references/plugins/api-workflow/) — published API functions
  - [hitl](references/plugins/hitl/) — human input via UiPath Apps
  - [agent](references/plugins/agent/) — published AI agent resources
  - [inline-agent](references/plugins/inline-agent/) — autonomous agent embedded in flow
  - [queue](references/plugins/queue/) — Orchestrator queue item creation

### Cross-capability (shared)

- [shared/file-format.md](../shared/file-format.md) — `.flow` JSON schema
- [shared/cli-commands.md](../shared/cli-commands.md) — flat CLI lookup
- [shared/cli-conventions.md](../shared/cli-conventions.md) — CLI mechanics every capability needs
- [shared/variables-and-expressions.md](../shared/variables-and-expressions.md) — variable system + `=js:` Jint expressions
- [shared/node-output-wiring.md](../shared/node-output-wiring.md) — canonical `=js:$vars.X.output.Y` rule
