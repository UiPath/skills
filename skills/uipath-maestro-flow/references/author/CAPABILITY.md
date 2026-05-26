# Author — Create and edit `.flow` files

Capability index for building new flows (greenfield) and editing existing flows (brownfield). Author owns everything that happens on disk, locally, without `uip login`. Authoring journeys terminate at `validate` + `format`; from there, hand off to [operate/CAPABILITY.md](../operate/CAPABILITY.md) to publish, run, or debug.

> **Where you came from / where to go next.** Author is upstream of Operate (build the flow → ship it) and upstream of Diagnose only via Operate (build → run → diagnose). Publish/run/lifecycle lives in [operate/CAPABILITY.md](../operate/CAPABILITY.md); fault triage lives in [diagnose/CAPABILITY.md](../diagnose/CAPABILITY.md).
>
> **Inherits universal rules from [SKILL.md](../../SKILL.md)** — `--output json`, no `flow debug` without consent, resource discovery order, never invoke other skills automatically, AskUserQuestion dropdown pattern, solution layout, **plain-English narration per logical step**, **granular `TodoWrite` list above the trivial threshold**. The rules below are author-scoped and apply on top.

## When to use this capability

- Create a new Flow project with `uip maestro flow init`
- Edit a `.flow` file — adding nodes, edges, or logic
- Explore available node types via the registry
- Validate a Flow file locally
- Manage variables, subflows, expressions, and output wiring
- Apply Node ownership — who authors the node (see § below)
- Configure connector, connector-trigger, or managed HTTP nodes; scaffold inline-agent projects
- Plan a complex flow before building

## Node ownership — who authors the node

Every node in a `.flow` file has exactly one author. The validator enforces this.

**User-owned nodes (Edit / Write directly):**

| Category | Node types |
| --- | --- |
| Triggers | `core.trigger.manual`, `core.trigger.scheduled` |
| Control flow | `core.logic.decision`, `core.logic.switch`, `core.logic.loop`, `core.logic.merge`, `core.control.end`, `core.logic.terminate`, `core.subflow` |
| Logic | `core.action.script`, `core.action.transform`, `core.logic.delay`, `core.logic.mock` |
| Human-in-the-loop | `uipath.human-in-the-loop` (inline + app-task forms) |
| Patterns | `uipath.pattern.batch-transform`, `uipath.pattern.deep-rag` |
| Agents | `uipath.agent.autonomous` (inline; after `uip agent init --inline-in-flow`) |
| Resource nodes | `uipath.core.rpa-workflow.*`, `uipath.core.agent.*`, `uipath.core.flow.*`, `uipath.core.agentic-process.*`, `uipath.core.api-workflow.*`, `uipath.core.human-task.*` |
| Queue | `core.action.queue.create`, `core.action.queue.create-and-wait` |

**CLI-owned nodes (`uip maestro flow node add` + `uip maestro flow node configure`):**

| Category | Node types | Why |
| --- | --- | --- |
| Connector activities | `uipath.connector.<key>.<op>` | `inputs.detail` is a `=jsonString:essentialConfiguration` envelope. Validate rejects hand-authored shapes. |
| Connector triggers | `uipath.connector.trigger.<key>.<trigger>` | Same envelope + product-managed `bindings_v2.json` derivation. |
| Wait for events (mid-flow) | `uipath.connector.event.<key>.<event>` | Same envelope and event metadata as a trigger, but placed mid-flow (has an `input` port) instead of as the start node. See [connector-trigger/impl.md — Wait for events](references/plugins/connector-trigger/impl.md#wait-for-events-uipathconnectoreventkeyevent). |
| Managed HTTP | `core.action.http.v2` | Same envelope. |

For CLI-owned nodes:

- Use `uip maestro flow node add` to insert the node and copy the definition into `definitions[]`.
- Use `uip maestro flow node configure --detail '{...}'` to populate `inputs.detail` and `bindings[]`.
- Subsequent edits to `inputs.detail` are also CLI-only — re-run `node configure` (it's a full rebuild; see [connector/impl.md](references/plugins/connector/impl.md)).
- You may still `Edit` the node's `display.label`, edges, layout, and outputs — those are not part of the envelope.

If you find yourself hand-writing `inputs.detail`, a `=jsonString:` blob, or `bindings[]` entries for a connector node — stop. Use the CLI.

## Critical rules

1. **Always validate node types against the registry before building.** Use `registry search`/`list` for discovery and `registry get` for detailed metadata and definitions.
2. **ALWAYS follow the relevant plugin in [plugins/](references/plugins/) for every node type.** Each plugin has a `planning.md` (when to use, selection heuristics, ports) and `impl.md` (registry validation, JSON structure, CLI commands, configuration, debug). For connector nodes, the [connector](references/plugins/connector/impl.md) plugin covers connection binding, enriched metadata, and field resolution — required before building. Without this, node configuration will be wrong — errors that `flow validate` does not catch.
3. **Read [/uipath:uipath-platform — connections.md](../../../uipath-platform/references/integration-service/connections.md) before any `uip is connections ...` call.** Applies to every connector activity, connector trigger, and managed HTTP node in connected mode. Single source of truth for command syntax, selection (including the personal-workspace auto-select rule), folder scoping, BYOA filtering, empty-result recovery, and ping verification. **If no healthy connection exists after following its recovery flow, STOP** and surface it in **Open Questions** during planning. Plugin files cover node-specific configuration that follows connection binding: [connector/impl.md](references/plugins/connector/impl.md), [connector-trigger/impl.md](references/plugins/connector-trigger/impl.md), [http/impl.md](references/plugins/http/impl.md).
4. **Edit `<ProjectName>.flow` only** — other generated files (`bindings_v2.json`, `entry-points.json`, `operate.json`, `package-descriptor.json`) are managed by the CLI and may be overwritten. To declare flow inputs/outputs, add variables in the `.flow` file (see [shared/file-format.md](../shared/file-format.md)).
5. **`targetPort` is required on every edge** — `validate` rejects edges without it.
6. **Every node type needs a `definitions` entry** — copy from `uip maestro flow registry get <nodeType>` output. Never hand-write definitions. The definition is the sole source for BPMN type (`model.type`), serviceType, event definitions, and binding/context templates — none of that belongs on the instance.
7. **Script nodes must `return` an object** — `return { key: value }`, not a bare scalar.
8. **Validate once at the end** — run `uip maestro flow validate` only after all nodes, edges, and configuration are complete. Do not validate after each individual node add or edit — intermediate states are expected to be invalid.
9. **Manage variables with `Edit` against the `.flow` file** — there are no CLI commands for variable management. Use `Edit` to add/remove/update entries in the `variables` section of the `.flow` file. See [shared/variables-and-expressions.md](../shared/variables-and-expressions.md).
10. **Every `out` variable must be mapped on every reachable End node** — missing output mappings cause runtime errors. See [shared/variables-and-expressions.md](../shared/variables-and-expressions.md).
11. **`=js:` prefix is REQUIRED on every `$vars`/`$metadata`/`$self` reference in a value field** — not on condition expressions (decision, switch, HTTP branch), which are auto-evaluated as JS. Without it, the BPMN runtime sees a literal string and `flow validate` fails with MST-9107. See [shared/node-output-wiring.md](../shared/node-output-wiring.md) for the canonical rule and per-node-type field reference, and [shared/variables-and-expressions.md](../shared/variables-and-expressions.md) for the expression system.
12. **Always run `flow format` after edits** — `uip maestro flow format <ProjectName>.flow` is the canonical layout step. Format arranges nodes horizontally, sets every node's `size` to `{ "width": 96, "height": 96 }`, and recurses into subflows (`subflows[<id>].layout`). Skipping format is the most common cause of misshapen rectangles in Studio Web.
13. **Don't hand-write `layout.nodes` or `subflows[<id>].layout`** — these are owned by `flow format`. When authoring nodes, any placeholder `position` is fine (e.g. `{ x: 0, y: 0 }`); format rewrites it on save. Sticky notes (`type: "stickyNote"`) are the one exception — format preserves their custom size and position. See [shared/file-format.md — Layout](../shared/file-format.md#layout).
14. **Every data-producing node MUST have a matching `variables.nodes[]` entry — this is what makes `$vars.<sourceNodeId>.output` resolve.** The BPMN emitter walks `variables.nodes[]` to write the process-level `<uipath:inputOutput>` declarations the runtime needs. The instance `outputs` block is **only** consumed by BPMN serialization on end-style nodes (to map workflow-level `out` variables); for action / trigger nodes it is documentation, not behavior. Skipping `variables.nodes[]` produces a flow that passes `flow validate` but resolves `$vars.<sourceNodeId>.output` to `undefined` at runtime (MST-9972). **Always run `uip maestro flow format` after structural edits — it regenerates `variables.nodes[]` from `nodes[]` + `definitions[]`** (matching what `uip maestro flow node add` and the canvas save path do), so this becomes self-healing as long as you `format`. See [shared/file-format.md — Node outputs](../shared/file-format.md#node-outputs).
15. **Node instances have no `model` block** — BPMN type, serviceType, version, event definitions, and binding/context templates live in the node's **definition** (in the top-level `definitions[]` array, copied verbatim from `registry get`). The runtime hydrates these from the definition at serialization time. Instance-specific identity fields live under `inputs`: `entryPointId`, `isDefaultEntryPoint` (triggers), `color`/`content` (sticky notes), and `source` (every inline-agent-related node — both `uipath.agent.autonomous` and every attached `uipath.agent.resource.*` node use `inputs.source = <UUID>`; their definitions declare `model.source: true` and flow-core hoists onto the instance).

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
| **Add/remove/wire nodes and edges** | [editing-operations.md](references/editing-operations.md) (strategy selection) + relevant plugin's `impl.md` (node-specific inputs) |
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
| **Create a resource that doesn't exist yet** | Use `core.logic.mock` placeholder — see [Edit/Write: Replace a mock](references/editing-operations-json.md#replace-a-mock-with-a-real-resource-node) + relevant plugin's `impl.md` |
| **Add data transform nodes** | [plugins/transform/impl.md](references/plugins/transform/impl.md) |
| **Add an LLM batch transform over CSV rows** | [plugins/batch-transform/impl.md](references/plugins/batch-transform/impl.md) — `uipath.pattern.batch-transform`, gated by tenant flag `canvas.nodes.batch-transform` |
| **Summarize / synthesize one document with optional citations** | [plugins/summarize/impl.md](references/plugins/summarize/impl.md) — `uipath.pattern.deep-rag`, gated by tenant flag `canvas.nodes.summarize` |
| **Create a subflow** | [plugins/subflow/impl.md](references/plugins/subflow/impl.md) + [Edit/Write: Create a subflow](references/editing-operations-json.md#create-a-subflow) |
| **Add a delay or scheduled trigger** | [plugins/delay/](references/plugins/delay/) or [plugins/scheduled-trigger/](references/plugins/scheduled-trigger/) |
| **Use queue nodes** | [plugins/queue/impl.md](references/plugins/queue/impl.md) |

## Anti-patterns

- **Never run `uip maestro flow init` outside a solution directory** — see [SKILL.md rule #6](../../SKILL.md#critical-rules-universal) for the required double-nested `<Solution>/<Project>/<Project>.flow` layout and the self-check.
- **Never guess node schemas** — use `registry get` for all node types. Guessed port names or input fields cause silent wiring failures.
- **Never skip capability discovery for connector nodes** — run `registry search` to confirm the connector exists and what operations it supports before building. See [connector/planning.md](references/plugins/connector/planning.md). Skipping this is the #1 cause of designing around a connector that doesn't exist or an operation it doesn't support.
- **Never replace a registered connector operation with `core.logic.mock` because configuration cannot run** — if `registry search` / `registry get` finds `uipath.connector.<connector-key>.<operation>`, add that real connector node via `uip maestro flow node add`. Missing live connections, missing tenant access, or prompts that ask you to only plan `--detail` mean: run `node add`, write the planned `--detail` payload to a sidecar file (e.g. `<nodeId>.detail.json`), and surface "configure pending" as an Open Question. **Do not leave a partial `inputs.detail` on the node** — the validator rejects hand-authored envelopes, and the node will not pass `flow validate` until `node configure` is run. Studio Web and reviewers need the real connector key in the `.flow`; the agent must report this explicitly rather than letting the user discover it via a later validation failure. See [§ Node ownership](#node-ownership--who-authors-the-node) and [connector/impl.md — No-Live-Tenant / Planned Configuration](references/plugins/connector/impl.md#no-live-tenant--planned-configuration).
- **Never edit `content/*.bpmn`** — it is auto-generated from the `.flow` file and will be overwritten.
- **Never use `core.logic.mock` when the resource is in the same solution** — use `--local` discovery instead. Mock placeholders are only for resources that are not in the current solution and not yet published.
- **Never hand-write `definitions` entries** — always copy from registry output. Hand-written definitions have wrong port schemas and cause validation failures.
- **Never put any `model` block on node instances** — BPMN type, serviceType, event definition, binding templates, and context templates all live in the node's **definition** (copied verbatim from `registry get` into `definitions[]`). Instances carry only per-instance data: `inputs`, `outputs`, `display`. Identity fields like `entryPointId` / `isDefaultEntryPoint` (triggers) and `color` / `content` (sticky notes) live under `inputs`. This applies to every inline-agent-related node too: `uipath.agent.autonomous` plus every attached `uipath.agent.resource.*` node (tool, escalation, context) carries source identity at `inputs.source = <UUID>`. Their definitions declare `model.source: true`; flow-core hoists onto the instance.
- **Never author `model.context[]` on resource-node instances** — resource-node instances have no `model` block. For `uipath.core.*` resource nodes (rpa, agent, flow, agentic-process, api-workflow, hitl), the definition (from `registry get`) already carries `model.context[]` with `<bindings.{name}>` placeholders. Your job is to add matching entries to the top-level `bindings[]` array — two entries per resource node (`name` + `folderPath`) with `resourceKey` matching the definition's `model.bindings.resourceKey`. At BPMN emit, the runtime rewrites `<bindings.{name}>` → `=bindings.{id}` via `(resourceKey, name)` matching. Without the top-level `bindings[]` entries, `uip maestro flow validate` passes but `uip maestro flow debug` fails with "Folder does not exist or the user does not have access to the folder." See the resource plugin's `impl.md`.
- **Never put a `ui` block on node instances** — position and size belong in the top-level `layout.nodes` object. Nodes with `"ui": { "position": ... }` use the wrong format and may not render correctly in Studio Web.
- **Never skip `flow format` before publish or debug** — without it, hand-written `layout` data renders as misshapen rectangles in Studio Web (the MST-9061 failure mode). See rule #12 above for the format step.
- **Never validate after every individual edit** — intermediate flow states (e.g., node added but not yet wired) are expected to be invalid. Run `uip maestro flow validate` once after the full build is complete.
- **Never use `console.log` in script nodes** — `console` is not available in the Jint runtime. Use `return { debug: value }` to inspect values.
- **Never forget output mapping on End nodes** — every `out` variable in `variables.globals` must have a `source` expression in every reachable End node's `outputs`. Missing mappings cause silent runtime failures.
- **Never update `in` variables** — only `inout` variables can be modified via `variableUpdates`. Input variables are read-only after flow start.
- **Never reference parent-scope `$vars` inside a subflow** — subflows have isolated scope. Pass values explicitly via subflow inputs.
- **Never use `core.action.http` (v1)** — the v1 node is deprecated for all HTTP requests (both connector-authenticated and manual). For connector-auth, v1's `authenticationType: "connection"` input does not pass IS credentials at runtime. Use `core.action.http.v2` (Managed HTTP Request) for every HTTP node. See [http/planning.md](references/plugins/http/planning.md).
- **Never hand-write `inputs.detail` for managed HTTP nodes** — run `uip maestro flow node configure` to populate the `inputs.detail` structure, generate `bindings_v2.json`, and create the connection resource file. Hand-written configurations miss the `essentialConfiguration` block and fail at runtime.
- **Never write `$vars.X` (or `$metadata.X`, `$self.X`) without `=js:` in value fields** — `flow validate` flags this as MST-9107. See rule #11 above and [shared/node-output-wiring.md](../shared/node-output-wiring.md) for the per-node-type field reference.
- **Never reuse a reference ID (mailbox folder, Slack channel, Jira project, Google Sheet, etc.) from a prior flow or session** — reference IDs are scoped to the specific authenticated account behind the connection. A `parentFolderId` from one Outlook mailbox is invalid in another; a Slack channel ID from one workspace is invalid in another. A reused ID passes `flow validate` and `node configure` cleanly, then faults silently at runtime with no resolvable error. Always re-resolve via `uip is resources run list <connector-key> <objectName> --connection-id <CURRENT_CONNECTION_ID> --output json` against the connection bound to this flow — do not paste a value you saw in another flow. See [connector/impl.md — Step 4](references/plugins/connector/impl.md) and [connector-trigger/impl.md — Step 3](references/plugins/connector-trigger/impl.md).
- **Never include `[*]` literally in a connector `bodyParameters` / `queryParameters` / `pathParameters` key** — `[*]` in `requestFields[].name` is an array marker, not part of the wire key. Strip it and pass an array value of the field's `dataType` (e.g. `"fields.labels[*]"` → `"fields.labels": ["a", "b"]`). Supported only when `[*]` is the name suffix; `[*].` (segments after) is not authorable. `flow validate` misses this; runtime rejects the key. See [connector/impl.md — Step 6b](references/plugins/connector/impl.md) for the full table including expression-value handling.

## References

### Author-scoped

- [greenfield.md](references/greenfield.md) — create-new-flow journey
- [brownfield.md](references/brownfield.md) — edit-existing-flow journey
- [editing-operations.md](references/editing-operations.md) — strategy selection (user-owned nodes via Edit / Write vs CLI-owned nodes via `uip maestro flow node`)
- [editing-operations-json.md](references/editing-operations-json.md) — Edit / Write recipes (default)
- [editing-operations-cli.md](references/editing-operations-cli.md) — CLI-owned node procedures
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
  - [batch-transform](references/plugins/batch-transform/) — LLM-powered row-by-row CSV enrichment (`uipath.pattern.batch-transform`)
  - [summarize](references/plugins/summarize/) — single-document synthesis / Q&A with optional citations (`uipath.pattern.deep-rag`)
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
