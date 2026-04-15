---
name: uipath-maestro-flow
description: "[PREVIEW] UiPath Flow projects (.flow files) — orchestrate RPA, agents, apps. Create, edit, validate, run flows via uip CLI: nodes, variables, subflows, triggers. For XAML or C# workflows→uipath-rpa."
allowed-tools: Bash, Read, Write, Edit, Glob, Grep
---

# UiPath Flow Authoring Assistant

Comprehensive guide for creating, editing, validating, and debugging UiPath Flow projects using the `uip` CLI and `.flow` file format.

## When to Use This Skill

- User wants to **create a new Flow project** with `uip flow init`
- User is **editing a `.flow` file** — adding nodes, edges, or logic
- User wants to **explore available node types** via the registry
- User wants to **validate** a Flow file locally
- User wants to **debug** a Flow (cloud)
- User asks about the **`.flow` JSON format**, nodes, edges, definitions, or ports
- User asks **how to implement logic** in a Flow (scripts, HTTP calls, branching, etc.)
- User wants to **orchestrate multiple automations** — RPA processes, agents, apps, other flows
- User wants to **manage variables** — inputs, outputs, state, expressions
- User wants to **create subflows** for reusable grouped logic
- User wants to **add data transforms** — filter, map, group-by operations
- User wants to **schedule a flow** with a recurring trigger
- User wants to **integrate with queues** — creating queue items for robot work distribution

## Critical Rules

1. **Phase 1 registry rules: `search`/`list` YES, `get` NO.** Use `registry search` and `registry list` during Phase 1 to discover what connectors and resources exist — this informs node selection. Do NOT run `registry get` in Phase 1 — detailed metadata, connection binding, and reference resolution belong to Phase 2. The planning guide documents all OOTB node types with ports and inputs — sufficient for topology design without registry calls. **Phase 2 REQUIRES `registry get` validation of all node types**, even OOTB nodes, to confirm the current product state. **Exception:** When building the flow (Step 5), you also need `registry get` for any node type to populate the `definitions` array — definitions must be copied from registry output, never hand-written.
2. **ALWAYS follow the relevant plugin in `references/plugins/` for every node type.** Each plugin has a `planning.md` (when to use, selection heuristics, ports) and `impl.md` (registry validation, JSON structure, CLI commands, configuration, debug). For connector nodes, the [connector](references/plugins/connector/impl.md) plugin covers connection binding, enriched metadata, and field resolution — required during Phase 2. Without this, node configuration will be wrong — errors that `flow validate` does not catch.
3. **ALWAYS check for existing connections** before using a connector node — if no connection exists, tell the user before proceeding. Phase 1 discovery checks connection availability to surface gaps early; Phase 2 pings and binds the connection via [connector/impl.md](references/plugins/connector/impl.md).
4. **ALWAYS use `--output json`** on all `uip` commands when parsing output programmatically.
5. **Edit `<ProjectName>.flow` only** — other generated files (`bindings_v2.json`, `entry-points.json`, `operate.json`, `package-descriptor.json`) are managed by the CLI and may be overwritten. To declare flow inputs/outputs, add variables in the `.flow` file (see [references/flow-file-format.md](references/flow-file-format.md)).
6. **`targetPort` is required on every edge** — `validate` rejects edges without it.
7. **Every node type needs a `definitions` entry** — copy from `uip flow registry get <nodeType>` output. Never hand-write definitions.
8. **Script nodes must `return` an object** — `return { key: value }`, not a bare scalar.
9. **Do NOT run `flow debug` without explicit user consent** — debug executes the flow for real (sends emails, posts messages, calls APIs).
10. **Validate once at the end** — run `uip flow validate` only after all nodes, edges, and configuration are complete (Step 6). Do not validate after each individual node add or edit — intermediate states are expected to be invalid.
11. **Manage variables by editing `.flow` JSON directly** — there are no CLI commands for variable management. Add/remove/update variables in the `variables` section of the `.flow` file. See [references/variables-and-expressions.md](references/variables-and-expressions.md).
12. **Every `out` variable must be mapped on every reachable End node** — missing output mappings cause runtime errors. See [references/variables-and-expressions.md](references/variables-and-expressions.md).
13. **`=js:` prefix rules** — Use `=js:` on value expressions (end node output `source`, variable updates, HTTP input fields). Do NOT use `=js:` on condition expressions (decision `expression`, switch case `expression`, HTTP branch `conditionExpression`) — those are always evaluated as JS automatically. See [references/variables-and-expressions.md](references/variables-and-expressions.md).
14. **For resources not yet published, use mock placeholders** — add a `core.logic.mock` node, tell the user which skill to use for creation, then replace the mock after publishing. See the relevant resource plugin's `impl.md` (e.g., [rpa](references/plugins/rpa/impl.md), [agent](references/plugins/agent/impl.md)).
15. **Never invoke other skills automatically** — when a flow needs an RPA process, agent, or app, identify the gap and provide handoff instructions. Let the user decide when to switch skills.
16. **Always use horizontal layout** — Flow uses a horizontal canvas. Place nodes left-to-right with increasing `x` values and the same `y` baseline (e.g., `y: 144`). Never stack nodes vertically.
17. **Node positioning goes in top-level `layout`, NOT on nodes** — Do not put a `ui` block on node instances. Store position/size in the `layout.nodes` object at the top level of the `.flow` file, keyed by node `id`. See [flow-file-format.md — Layout](references/flow-file-format.md#layout).
18. **Every node that produces data MUST have `outputs` on the node instance** — Without an `outputs` block, downstream `$vars` references will not resolve at runtime. Action nodes need `output` + `error`; trigger nodes need `output` only; end/terminate nodes do not use this pattern. See [flow-file-format.md — Node outputs](references/flow-file-format.md#node-outputs). **Wrong:** relying on `outputDefinition` in `definitions` alone. **Right:** `outputs` on the node instance itself.

## Common Edits (existing flows)

For targeted changes to an existing flow, use the recipes below instead of the full Quick Start pipeline. Each recipe links to the detailed step-by-step procedure in the [flow editing operations guide](references/flow-editing-operations.md). Run `uip flow validate` once after all edits are complete.

**Read [references/flow-editing-operations.md](references/flow-editing-operations.md) first** to choose between CLI and direct JSON strategies for each operation.

| Edit | Description | Guide |
|------|-------------|-------|
| **Change a script body or node inputs** | Edit the node's `inputs` in-place in the `.flow` JSON. Do not delete + re-add — that changes the node ID and breaks `$vars` expressions. Script nodes must return an object (`return { key: value }`). | [JSON: Update node inputs](references/flow-editing-operations-json.md#update-node-inputs) |
| **Add a node between two existing nodes** | Remove the connecting edge, add the new node, wire upstream → new → downstream. | [CLI: Insert a node](references/flow-editing-operations-cli.md#insert-a-node-between-two-existing-nodes) / [JSON: Insert a node](references/flow-editing-operations-json.md#insert-a-node-between-two-existing-nodes) |
| **Add a branch (decision node)** | Remove an edge, add a decision node, wire true/false branches. | [CLI: Insert a decision branch](references/flow-editing-operations-cli.md#insert-a-decision-branch) / [JSON: Insert a decision branch](references/flow-editing-operations-json.md#insert-a-decision-branch) |
| **Remove a node** | Delete the node (edges cascade in CLI), reconnect upstream to downstream. | [CLI: Remove a node](references/flow-editing-operations-cli.md#remove-a-node-and-reconnect) / [JSON: Remove a node](references/flow-editing-operations-json.md#remove-a-node-and-reconnect) |
| **Remove an edge** | Find the edge ID, delete it. | [CLI: Delete an edge](references/flow-editing-operations-cli.md#delete-an-edge) / [JSON: Delete an edge](references/flow-editing-operations-json.md#delete-an-edge) |
| **Add a workflow variable** | Edit `variables.globals` in the `.flow` file (JSON only). For `out` variables, map on every End node. See [variables-and-expressions.md](references/variables-and-expressions.md). | [JSON: Add a workflow variable](references/flow-editing-operations-json.md#add-a-workflow-variable) |
| **Update a state variable** | Add a `variableUpdates` entry for `inout` variables (JSON only). See [variables-and-expressions.md](references/variables-and-expressions.md). | [JSON: Add a variable update](references/flow-editing-operations-json.md#add-a-variable-update) |
| **Create a subflow** | Add a `core.subflow` parent node + `subflows.{nodeId}` with nested nodes/edges/variables (JSON only). | [JSON: Create a subflow](references/flow-editing-operations-json.md#create-a-subflow) + [subflow/impl.md](references/plugins/subflow/impl.md) |
| **Add a scheduled trigger** | Replace `core.trigger.manual` with `core.trigger.scheduled`. | [CLI: Replace trigger](references/flow-editing-operations-cli.md#replace-manual-trigger-with-scheduled-trigger) / [JSON: Replace trigger](references/flow-editing-operations-json.md#replace-manual-trigger-with-scheduled-trigger) + [scheduled-trigger/impl.md](references/plugins/scheduled-trigger/impl.md) |
| **Add a connector trigger** | Delete manual trigger, add connector trigger, configure with connection. | [CLI: Replace trigger](references/flow-editing-operations-cli.md#replace-manual-trigger-with-connector-trigger) + [connector-trigger/impl.md](references/plugins/connector-trigger/impl.md) |
| **Add a resource node** | Discover via registry, add with CLI or JSON, wire edges. Use `core.logic.mock` if unpublished. | [CLI: Replace a mock](references/flow-editing-operations-cli.md#replace-a-mock-with-a-real-resource-node) + relevant plugin's `impl.md` |
| **Add an inline agent node** | Embed a `uipath.agent.autonomous` node with an inline agent definition living inside the flow project. | [inline-agent/planning.md](references/plugins/inline-agent/planning.md) for selection vs a published agent, [inline-agent/impl.md](references/plugins/inline-agent/impl.md) for scaffolding, CLI, JSON structure, and validation. |


## Quick Start

These steps are for **creating a new flow from scratch**. For existing projects, use the Common Edits section above or skip to the relevant step.

### Step 0 — Resolve the `uip` binary

The `uip` CLI is installed via npm. If `uip` is not on PATH (common in nvm environments), resolve it first:

```bash
which uip || npm list -g @uipath/uipcli
```

If not found, install:
```bash
npm install -g @uipath/uipcli
```

Verify with `uip --version`. Use `uip` directly in all subsequent commands.

### Step 1 — Check login status

`uip flow debug` and process operations require authentication. `uip flow init`, `validate`, and `registry` commands work without login.

```bash
uip login status --output json
```

If not logged in and you need cloud features:
```bash
uip login                                          # interactive OAuth (opens browser)
uip login --authority https://alpha.uipath.com     # non-production environments
```

### Step 2 — Create a solution and Flow project

Every Flow project lives inside a solution. Check the current directory for existing `.uipx` files. If existing solutions are found, ask the user whether they want to use one of them or create a new solution. If no existing solutions are found, create a new one automatically.

- If the user specifies an existing `.uipx` file path or solution name, use that (skip to Step 2b)
- Otherwise, create a new solution (Step 2a)

#### 2a. Create a new solution

```bash
uip solution new "<SolutionName>" --output json
```

> **Naming convention:** Use the same name for both the solution and the project unless the user specifies otherwise. If the user only provides a project name, use it as the solution name too.

#### 2b. Create the Flow project inside the solution folder

```bash
cd <directory>/<SolutionName> && uip flow init <ProjectName>
```

#### 2c. Add the project to the solution

```bash
uip solution project add \
  <directory>/<SolutionName>/<ProjectName> \
  <directory>/<SolutionName>/<SolutionName>.uipx
```

This scaffolds a complete project inside a solution. See [references/flow-file-format.md](references/flow-file-format.md) for the full project structure.

### Step 3 — Refresh the registry

```bash
uip flow registry pull                          # refresh local cache (expires after 30 min)
```

> **Auth note**: Without `uip login`, registry shows OOTB nodes only. After login, tenant-specific connector and resource nodes are also available.

Discovery (`registry search`/`list`) and connector resolution (`registry get`, connection binding) happen during planning — see Step 4 below.

### Step 4 — Plan the flow (two phases)

**Required when creating a new flow or adding multiple nodes.** Only skip this step for small targeted edits to an *existing* flow (e.g., changing a script body, renaming a node, tweaking one connection). When in doubt, plan.

Planning is split into two phases:
- **Phase 1 — Discovery & Architectural Design:** Discover available capabilities and check connector connection availability, then design the flow topology (nodes, edges, inputs/outputs) and produce a mermaid diagram. No `registry get` or connection binding — only existence checks.
- **Phase 2 — Implementation Resolution:** Resolve connector details via `registry get`, bind connections, resolve reference fields, and finalize the plan with implementation-ready details.

#### 4a. Discovery & Architectural Design (Phase 1)

**Read [references/planning-arch.md](references/planning-arch.md)** for capability discovery, the node type catalog, selection heuristics, wiring rules, topology patterns, mermaid validation rules, and the full output format.

Follow the process in that guide to produce a `<SolutionName>.arch.plan.md` in the **solution directory** (the folder containing the `.uipx` file) containing:
1. Summary
2. Mermaid flow diagram (validated against the mermaid syntax rules in the guide)
3. Node table with suspected inputs/outputs
4. Edge table with source/target ports
5. Inputs & Outputs (workflow-level variables)
6. Connector summary (if applicable)
7. Open questions (if any)

Present a **short summary in chat** (goal + key nodes + open questions). Tell the user to review the full plan in `<SolutionName>.arch.plan.md`.

**Do NOT proceed to Phase 2 until the user explicitly approves the architectural plan.**

#### 4b. Implementation Resolution (Phase 2)

**Read [references/planning-impl.md](references/planning-impl.md)** for the implementation resolution process.

Phase 2 takes the approved architectural plan and resolves all implementation details:
- Validate all node types via `uip flow registry get` — read each plugin's `impl.md` for registry validation
- Resolve connector and resource nodes using the relevant plugin's `impl.md` ([connector](references/plugins/connector/impl.md), [rpa](references/plugins/rpa/impl.md), [agent](references/plugins/agent/impl.md), etc.)
- Validate required fields against user-provided values
- Replace `<PLACEHOLDER>` values with resolved IDs
- Replace `core.logic.mock` nodes with real resource nodes (if published)
- Write `<SolutionName>.impl.plan.md` with resolved details and mermaid diagram

#### 4c. Iterate until approved

**Do NOT proceed to Step 5 until the user explicitly approves the plan.** The iteration loop:

1. User reviews the plan and gives feedback in chat (e.g., "move the Slack notification before the filter", "add an error handler after the API call", "use Salesforce instead of HubSpot")
2. Update `<SolutionName>.impl.plan.md` with the changes
3. Summarize what changed in chat
4. Repeat until the user says the plan is approved

### Step 5 — Build the flow

Edit `<ProjectName>.flow` directly in the project root. The `bindings_v2.json` file is also in the project root for resource bindings.

**Read [references/flow-editing-operations.md](references/flow-editing-operations.md)** to choose between CLI and direct JSON strategies for each operation. Common approach: use CLI for node/edge CRUD, direct JSON for variables, variableUpdates, subflows, and output mapping.

For each node type, follow the relevant plugin's `impl.md` for node-specific inputs, JSON structure, and configuration. The operations guides cover the mechanics (how to add/delete/wire); the plugins cover the semantics (what inputs and model fields each node type needs).

### Step 6 — Validate loop

Run validation and fix errors iteratively until the flow is clean.

```bash
uip flow validate <ProjectName>.flow --output json
```

**Validation loop:**
1. Run `uip flow validate`
2. If valid → done, move to Step 7 (push to Studio Web)
3. If errors → read the error messages, fix the `.flow` file
4. Go to 1

Common error categories:
- **Missing targetPort** — every edge needs a `targetPort` string
- **Missing definition** — every `type:typeVersion` in nodes needs a matching `definitions` entry
- **Invalid node/edge references** — `sourceNodeId`/`targetNodeId` must reference existing node `id`s
- **Duplicate IDs** — node and edge `id`s must be unique

### Step 7 — Debug (cloud) — only when explicitly requested

After validation passes, the user may want to test the flow end-to-end. **Do not run this without explicit user consent** — debug executes the flow for real (sends emails, posts messages, calls APIs). See Critical Rule #9.

```bash
UIPCLI_LOG_LEVEL=info uip flow debug <path-to-project-dir>
```

The argument is the **project directory path** (the folder containing `project.uiproj`). Use `<ProjectName>/` from the solution dir, or `.` if already inside the project dir. This uploads the project to Studio Web, triggers a debug session in Orchestrator, and streams results.

> **Note:** Requires `uip login`. Debug is for **testing that the flow runs correctly** — not for publishing or viewing. To publish, use Step 8 instead.

### Step 8 — Publish to Studio Web

**This is the default publish target.** When the user wants to publish, view, or share the flow, upload it to Studio Web using `solution bundle` + `solution upload`:

```bash
# Bundle the solution directory into a .uis file
uip solution bundle <SolutionDir> --output .

# Upload the .uis to Studio Web
uip solution upload <SolutionName>.uis --output json
```

The `bundle` command requires a solution directory containing a `.uipx` file. If the project was created with `uip flow init`, it lives inside a solution directory already. The `upload` command pushes it to Studio Web where the user can visualize, inspect, edit, and publish from the browser. Share the Studio Web URL with the user.

**Do NOT run `uip flow pack` + `uip solution publish` unless the user explicitly asks to deploy to Orchestrator.** That path puts the flow directly into Orchestrator as a process, bypassing Studio Web — the user cannot visualize or edit it there. If the user asks to "publish" without specifying where, always default to the Studio Web path (`solution bundle` + `solution upload`).

For Orchestrator deployment when explicitly requested, see [references/flow-commands.md](references/flow-commands.md) for `uip flow pack` and the [/uipath:uipath-platform](/uipath:uipath-platform) skill for `uip solution publish`.

## Anti-Patterns

- **Never guess node schemas** — use the planning guide for OOTB nodes, `registry get` for connector/unknown nodes. Guessed port names or input fields cause silent wiring failures.
- **Never `registry get` during Phase 1 planning** — use `registry search`/`list` for discovery, but save `registry get` for Phase 2. The planning guide documents all OOTB node types with ports and inputs. Phase 2 **requires** `registry get` validation of all node types to confirm the current product state before building.
- **Never skip capability discovery for connector nodes** — run `registry search` during Phase 1 to confirm the connector exists and what operations it supports. See [connector/planning.md](references/plugins/connector/planning.md). Skipping this is the #1 cause of designing around a connector that doesn't exist or an operation it doesn't support.
- **Never edit `content/*.bpmn`** — it is auto-generated from the `.flow` file and will be overwritten.
- **Never run `flow debug` as a validation step** — debug executes the flow with real side effects. Use `flow validate` for checking correctness.
- **Never skip the planning step for multi-node flows** — jumping straight to building produces flows that need major rework.
- **Never chain skills automatically** — if the flow needs an RPA process, coded workflow, or agent, insert a `core.logic.mock` placeholder and tell the user which skill to use. Do not invoke other skills.
- **Never hand-write `definitions` entries** — always copy from registry output. Hand-written definitions have wrong port schemas and cause validation failures.
- **Never put a `ui` block on node instances** — position and size belong in the top-level `layout.nodes` object. Nodes with `"ui": { "position": ... }` use the wrong format and may not render correctly in Studio Web.
- **Never omit `outputs` on nodes that produce data** — action nodes need `output` + `error`, trigger nodes need `output`. The `outputDefinition` in `definitions` is for the registry schema, not for runtime binding — without `outputs` on the node instance, `$vars` references downstream will fail silently.
- **Never validate after every individual edit** — intermediate flow states (e.g., node added but not yet wired) are expected to be invalid. Run `uip flow validate` once after the full build is complete (Step 6).
- **Never use `console.log` in script nodes** — `console` is not available in the Jint runtime. Use `return { debug: value }` to inspect values.
- **Never forget output mapping on End nodes** — every `out` variable in `variables.globals` must have a `source` expression in every reachable End node's `outputs`. Missing mappings cause silent runtime failures.
- **Never update `in` variables** — only `inout` variables can be modified via `variableUpdates`. Input variables are read-only after flow start.
- **Never reference parent-scope `$vars` inside a subflow** — subflows have isolated scope. Pass values explicitly via subflow inputs.

## Task Navigation

| I need to... | Read these |
| --- | --- |
| **Edit an existing flow** | Common Edits section + [references/flow-editing-operations.md](references/flow-editing-operations.md) |
| **Add/delete/wire nodes and edges** | [references/flow-editing-operations.md](references/flow-editing-operations.md) (strategy selection) + relevant plugin's `impl.md` (node-specific inputs) |
| **Generate a flow plan** | [references/planning-arch.md](references/planning-arch.md) + [references/planning-impl.md](references/planning-impl.md) + Step 4 |
| **Choose the right node type** | [references/planning-arch.md — Plugin Index](references/planning-arch.md#plugin-index) + relevant plugin's `planning.md` |
| **Understand the .flow JSON format** | [references/flow-file-format.md](references/flow-file-format.md) |
| **Know all CLI commands** | [references/flow-commands.md](references/flow-commands.md) |
| **Add a Script node** | [references/plugins/script/impl.md](references/plugins/script/impl.md) |
| **Wire nodes with edges** | [references/flow-editing-operations.md](references/flow-editing-operations.md) + [references/flow-file-format.md — Standard ports](references/flow-file-format.md) |
| **Find the right node type** | Run `uip flow registry search <keyword>` |
| **Work with connector nodes** | [references/plugins/connector/](references/plugins/connector/) + [/uipath:uipath-platform — Integration Service](/uipath:uipath-platform) |
| **Publish to Studio Web** | Step 8 (solution bundle + upload) |
| **Deploy to Orchestrator** (only if explicitly requested) | [references/flow-commands.md](references/flow-commands.md) + [/uipath:uipath-platform](/uipath:uipath-platform) |
| **Manage variables and expressions** | [references/variables-and-expressions.md](references/variables-and-expressions.md) + [JSON: Variable Operations](references/flow-editing-operations-json.md#variable-operations) |
| **Write `=js:` expressions** | [references/variables-and-expressions.md — Expression System](references/variables-and-expressions.md) |
| **Orchestrate RPA, agents, apps** | Relevant resource plugin: [rpa](references/plugins/rpa/), [agent](references/plugins/agent/), [agentic-process](references/plugins/agentic-process/), [flow](references/plugins/flow/), [api-workflow](references/plugins/api-workflow/), [hitl](references/plugins/hitl/) |
| **Embed an AI agent tightly coupled to this flow** | [references/plugins/inline-agent/](references/plugins/inline-agent/) — scaffolded via `uip agent init --inline-in-flow`, node type `uipath.agent.autonomous` |
| **Create a resource that doesn't exist yet** | Use `core.logic.mock` placeholder — see [CLI: Replace a mock](references/flow-editing-operations-cli.md#replace-a-mock-with-a-real-resource-node) + relevant plugin's `impl.md` |
| **Add data transform nodes** | [references/plugins/transform/impl.md](references/plugins/transform/impl.md) |
| **Create a subflow** | [references/plugins/subflow/impl.md](references/plugins/subflow/impl.md) + [JSON: Create a subflow](references/flow-editing-operations-json.md#create-a-subflow) |
| **Add a delay or scheduled trigger** | [references/plugins/delay/](references/plugins/delay/) or [references/plugins/scheduled-trigger/](references/plugins/scheduled-trigger/) |
| **Use queue nodes** | [references/plugins/queue/impl.md](references/plugins/queue/impl.md) |

## Key Concepts

### validate vs debug

| Command | What it does | Auth needed |
|---------|-------------|-------------|
| `uip flow validate` | Local JSON schema + cross-reference check | No |
| `uip flow debug` | Converts to BPMN, uploads to Studio Web, runs in Orchestrator, streams results | Yes |

Always `validate` locally before `debug`. Validation is instant; debug is a cloud round-trip.

### CLI output format

All `uip` commands return structured JSON:
```json
{ "Result": "Success", "Code": "FlowValidate", "Data": { ... } }
{ "Result": "Failure", "Message": "...", "Instructions": "Found N error(s): ..." }
```

Always use `--output json` for programmatic use. The `--localstorage-file` warning in some environments is benign.

## Completion Output

When you finish building or editing a flow, report to the user:

1. **File path** of the `.flow` file created or edited
2. **What was built** — summary of nodes added, edges wired, and logic implemented
3. **Validation status** — whether `flow validate` passes (or remaining errors if unresolvable)
4. **Mock placeholders** — list any `core.logic.mock` nodes that need to be replaced, and which skill to use
5. **Missing connections** — any connector nodes that need connections the user must create
6. **Next step** — ask if the user wants to debug the flow (do not run debug automatically)
7. **Publish offer** — ask if the user wants to publish to Studio Web (do not publish automatically). If yes, run `solution bundle` + `solution upload` and share the Studio Web URL.

## References

- **[Flow Editing Operations](references/flow-editing-operations.md)** — Strategy selection matrix for CLI vs. direct JSON editing. Links to the two strategy guides below. **Read this before modifying any `.flow` file.**
  - [CLI Strategy](references/flow-editing-operations-cli.md) — All node/edge operations via `uip flow node` and `uip flow edge` commands
  - [Direct JSON Strategy](references/flow-editing-operations-json.md) — All operations via direct `.flow` file editing (variables, subflows, in-place updates)
- **[Planning Phase 1: Discovery & Architectural Design](references/planning-arch.md)** — Capability discovery (`registry search`/`list`), plugin index for node selection, topology design, mermaid diagram generation, wiring rules, and common patterns. **Read this first when planning a new flow.**
- **[Planning Phase 2: Implementation Resolution](references/planning-impl.md)** — Implementation resolution process (registry lookups, connection binding, reference field resolution), wiring rules, and flow patterns. **Read this after the architectural plan is approved.**
- **[.flow File Format](references/flow-file-format.md)** — JSON schema, node/edge structure, definition requirements, and minimal working example
- **[CLI Command Reference](references/flow-commands.md)** — All `uip flow` subcommands with flags and options
- **[Variables and Expressions](references/variables-and-expressions.md)** — Variable declaration (in/out/inout), type system, `=js:` Jint expressions, template syntax, scoping rules, output mapping, and variable updates
- **[Node Plugins](references/plugins/)** — Each node type has its own plugin folder with `planning.md` (selection heuristics, ports, key inputs) and `impl.md` (registry validation, JSON structure, configuration, debug):
  - [connector](references/plugins/connector/) — IS connector nodes: connection binding, enriched metadata, reference resolution, `bindings_v2.json`
  - [script](references/plugins/script/) — Custom JavaScript logic via Jint ES2020
  - [http](references/plugins/http/) — REST API calls, response branching, connection auth
  - [decision](references/plugins/decision/) — Binary if/else branching
  - [switch](references/plugins/switch/) — Multi-way branching (3+ paths)
  - [loop](references/plugins/loop/) — Collection iteration (sequential/parallel)
  - [merge](references/plugins/merge/) — Parallel branch synchronization
  - [end](references/plugins/end/) — Graceful flow completion with output mapping
  - [terminate](references/plugins/terminate/) — Abort entire flow on fatal error
  - [transform](references/plugins/transform/) — Declarative filter, map, group-by
  - [delay](references/plugins/delay/) — Duration or date-based pause
  - [subflow](references/plugins/subflow/) — Reusable node groups with isolated scope
  - [scheduled-trigger](references/plugins/scheduled-trigger/) — Recurring schedule triggers
  - [rpa](references/plugins/rpa/) — Published RPA processes (`uipath.core.rpa.{key}`)
  - [agentic-process](references/plugins/agentic-process/) — Published orchestration processes (`uipath.core.agentic-process.{key}`)
  - [flow](references/plugins/flow/) — Published flows as subprocesses (`uipath.core.flow.{key}`)
  - [api-workflow](references/plugins/api-workflow/) — Published API functions (`uipath.core.api-workflow.{key}`)
  - [hitl](references/plugins/hitl/) — Human input via UiPath Apps (`uipath.core.hitl.{key}`)
  - [agent](references/plugins/agent/) — Published AI agent resources (`uipath.core.agent.{key}`)
  - [inline-agent](references/plugins/inline-agent/) — Autonomous agent embedded inside the flow project (`uipath.agent.autonomous`), scaffolded via `uip agent init --inline-in-flow`
  - [queue](references/plugins/queue/) — Orchestrator queue item creation
- **[Pack / Publish / Deploy](/uipath:uipath-platform)** — Orchestrator deployment only when explicitly requested (uipath-platform skill). Default publish path is Studio Web via `solution bundle` + `solution upload` (Step 8).

> **Trouble?** If something didn't work as expected, use `/uipath-feedback` to send a report.
