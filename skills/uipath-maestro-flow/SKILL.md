---
name: uipath-maestro-flow
description: "[PREVIEW] Create, edit, validate, debug, and run UiPath Flow projects (.flow files) using the uip CLI. Supports scaffolding flows, adding/connecting nodes, managing variables and expressions, subflows, scheduled triggers, and orchestrating external resources (RPA, agents, apps, other flows). TRIGGER when: user mentions Flow, .flow files, flow nodes, flow orchestration, uip flow CLI commands, or wants to compose multiple UiPath automations. DO NOT TRIGGER when: user is working with XAML/RPA workflows (use uipath-rpa-workflows), coded C# workflows (use uipath-coded-workflows), Python agents (use uipath-coded-agents), or web apps (use uipath-coded-apps) — unless they want to orchestrate these from a flow."
metadata:
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

1. **Do NOT `registry get` built-in nodes during Phase 1 (architectural planning).** The planning guide and node reference already document all OOTB node types with their ports, inputs, and output variables — sufficient for designing flow topology. However, **Phase 2 (implementation resolution) REQUIRES registry validation of all node types**, even OOTB nodes, to confirm ports and inputs match the current product state. Only run connector/resource `registry get` during Phase 1 if needed for decision-making. **Exception:** When building the flow (Step 6), you DO need `registry get` for any node type to populate the `definitions` array in the `.flow` file — definitions must be copied from registry output, never hand-written.
2. **ALWAYS follow the relevant node guide in `references/nodes/` for every connector node.** The guide covers capability discovery, connection binding, and field resolution — required before planning. Without this, node configuration will be wrong — errors that `flow validate` does not catch.
3. **ALWAYS check for existing connections** before using a connector node — if no connection exists, tell the user before proceeding. See the relevant node guide in `references/nodes/` for the connection check command.
4. **ALWAYS use `--output json`** on all `uip` commands when parsing output programmatically.
5. **Edit `<ProjectName>.flow` only** — other generated files (`bindings_v2.json`, `entry-points.json`, `operate.json`, `package-descriptor.json`) are managed by the CLI and may be overwritten. To declare flow inputs/outputs, add variables in the `.flow` file (see [references/flow-file-format.md](references/flow-file-format.md)).
6. **`targetPort` is required on every edge** — `validate` rejects edges without it.
7. **Every node type needs a `definitions` entry** — copy from `uip flow registry get <nodeType>` output. Never hand-write definitions.
8. **Script nodes must `return` an object** — `return { key: value }`, not a bare scalar.
9. **Do NOT run `flow debug` without explicit user consent** — debug executes the flow for real (sends emails, posts messages, calls APIs).
10. **Validate after every change** — run `uip flow validate` after each edit to the `.flow` file. Do not batch multiple edits before validating.
11. **Manage variables by editing `.flow` JSON directly** — there are no CLI commands for variable management. Add/remove/update variables in the `variables` section of the `.flow` file. See [references/variables-and-expressions.md](references/variables-and-expressions.md).
12. **Every `out` variable must be mapped on every reachable End node** — missing output mappings cause runtime errors. See [references/variables-and-expressions.md](references/variables-and-expressions.md).
13. **Use `=js:` prefix for all expressions** — the runtime uses a Jint-based JavaScript engine (ES2020 subset). See [references/variables-and-expressions.md](references/variables-and-expressions.md) for supported features and constraints.
14. **For resources not yet published, use mock placeholders** — add a `core.logic.mock` node, tell the user which skill to use for creation, then replace the mock after publishing. See [references/orchestration-guide.md](references/orchestration-guide.md).
15. **Never invoke other skills automatically** — when a flow needs an RPA process, agent, or app, identify the gap and provide handoff instructions. Let the user decide when to switch skills.

## Common Edits (existing flows)

For targeted changes to an existing flow, use the recipes below instead of the full Quick Start pipeline. Always run `uip flow validate` after editing.

### Change a script body

Edit the `inputs.script` string on the target node in `<ProjectName>.flow`. Script nodes must return an object (`return { key: value }`), not a scalar.

### Add a node between two existing nodes

1. Get the new node's schema: `uip flow registry get <nodeType> --output json`
2. Add its `Data.Node` to the `definitions` array (skip if that type already has a definition)
3. Add the node instance to `nodes` with a unique `id` and correct `ui.position`
4. Find the edge connecting the two existing nodes — update it to point to the new node instead:
   - Change `targetNodeId` to the new node's `id` and `targetPort` to the new node's incoming port (usually `input`)
5. Add a new edge (with a unique `id`) from the new node to the original target:
   - `sourceNodeId`: new node's `id`, `sourcePort`: `success` (or the appropriate port)
   - `targetNodeId`: original target's `id`, `targetPort`: `input`
6. Check ports: see [references/flow-file-format.md — Standard ports](references/flow-file-format.md) for source/target ports by node type

### Add a branch (decision node)

1. Get the definition: `uip flow registry get core.logic.decision --output json` and add `Data.Node` to `definitions`
2. Add a `core.logic.decision` node with an `expression` input
3. Redirect the incoming edge to the decision node — update `targetNodeId` and set `targetPort: "input"`
4. Add two outgoing edges from the decision — one from `sourcePort: "true"`, one from `sourcePort: "false"` — each wiring to the appropriate downstream node with `targetPort: "input"`

### Remove a node

1. Delete the node from the `nodes` array
2. Delete all edges where `sourceNodeId` or `targetNodeId` matches the removed node's `id`
3. Reconnect: add a new edge from the upstream node to the downstream node
4. Remove its definition from `definitions` only if no other node uses the same type

### Add a workflow variable

Edit `variables.globals` in the `.flow` file. See [references/variables-and-expressions.md](references/variables-and-expressions.md) for the full schema.

1. Add the variable object to `variables.globals` with the correct `direction` (`in`, `out`, or `inout`)
2. For `out` variables: add output mapping to every reachable End node's `outputs`
3. For `inout` variables: add `variableUpdates` entries on nodes that modify the state
4. Validate: `uip flow validate`

### Update a state variable on a node

Add a `variableUpdates` entry to update an `inout` variable when a specific node completes:

1. Ensure the variable exists in `variables.globals` with `direction: "inout"`
2. Add the update expression to `variables.variableUpdates.{nodeId}`:
   ```json
   { "variableId": "counter", "expression": "=js:$vars.counter + 1" }
   ```
3. Validate: `uip flow validate`

### Create a subflow

1. Add a `core.subflow` node to the parent flow's `nodes` array with `inputs` matching the subflow's `in` variables
2. Add a `subflows.{nodeId}` entry with its own `nodes`, `edges`, and `variables`
3. The subflow must have its own Start node (`core.trigger.manual`) and End node (`core.control.end`)
4. Define subflow inputs (`direction: "in"`) and outputs (`direction: "out"`) in `subflows.{nodeId}.variables.globals`
5. Map outputs on the subflow's End node
6. See [references/node-reference.md — Subflow](references/node-reference.md) for the full JSON structure

### Add a scheduled trigger

Replace `core.trigger.manual` with `core.trigger.scheduled`:

1. Change the start node's `type` to `core.trigger.scheduled`
2. Add timer inputs: `timerType: "timeCycle"`, `timerPreset: "R/PT1H"` (or custom)
3. Add the `eventDefinition` to `model`: `"eventDefinition": "bpmn:TimerEventDefinition"`
4. See [references/node-reference.md — Scheduled Trigger](references/node-reference.md) for presets

### Add a resource node (RPA process, agent, etc.)

See [references/orchestration-guide.md](references/orchestration-guide.md) for the full workflow. Summary:

1. `uip flow registry pull --force` to refresh
2. `uip flow registry search "<name>" --output json` to find the resource
3. `uip flow node add` with the discovered node type
4. Wire edges and validate
5. If the resource doesn't exist yet, use a `core.logic.mock` placeholder and tell the user which skill to use

## Quick Start

These steps are for **creating a new flow from scratch**. For existing projects, use the Common Edits section above or skip to the relevant step.

### Step 0 — Resolve the `uip` binary

The `uip` CLI is installed via npm. If `uip` is not on PATH (common in nvm environments), resolve it first:

```bash
UIP=$(command -v uip 2>/dev/null || npm root -g 2>/dev/null | sed 's|/node_modules$||')/bin/uip
$UIP --version
```

Use `$UIP` in place of `uip` for all subsequent commands if the plain `uip` command isn't found.

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

### Step 3 — Discover available node types

Before editing the `.flow` file, check what nodes are available:

```bash
uip flow registry pull                          # refresh local cache (expires after 30 min)
uip flow registry list --output json            # list all cached node types
uip flow registry search <keyword>              # search by name, tag, or category
uip flow registry search agent
```

> **Auth note**: Without `uip login`, registry shows OOTB nodes only. After login, tenant-specific connector nodes are also available.

At this point you know **which node types** to use. For OOTB nodes (scripts, HTTP, branching), you can call `registry get` immediately. For connector nodes, do **not** run `registry get` yet — proceed to Step 4 first.

### Step 4 — Bind connections, fetch metadata, and resolve references (when using connectors)

**Skip this step if the flow only uses OOTB nodes.** For each connector node, read the relevant node guide in `references/nodes/` and follow its Configuration Workflow. The guide covers:

1. Connection discovery and binding
2. Enriched metadata retrieval
3. Field and reference resolution
4. Node configuration via `uip flow node configure`

After completing these steps, you should have for each connector node: a bound connection, field metadata, and resolved values for all reference fields. Carry this information into the planning step.

### Step 5 — Plan the flow (two phases)

**Required when creating a new flow or adding multiple nodes.** Only skip this step for small targeted edits to an *existing* flow (e.g., changing a script body, renaming a node, tweaking one connection). When in doubt, plan.

Planning is split into two phases:
- **Phase 1 — Architectural Design:** Design the flow topology (nodes, edges, inputs/outputs) and produce a mermaid diagram. No registry lookups or connection binding.
- **Phase 2 — Implementation Resolution:** Resolve connector details, bind connections, resolve reference fields, and finalize the plan with implementation-ready details.

#### 5a. Architectural Design (Phase 1)

**Read [references/planning-phase-architectural.md](references/planning-phase-architectural.md)** for the node type catalog, selection heuristics, wiring rules, topology patterns, mermaid validation rules, and the full output format.

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

#### 5b. Implementation Resolution (Phase 2)

**Read [references/planning-phase-implementation.md](references/planning-phase-implementation.md)** for the implementation resolution process.

Phase 2 takes the approved architectural plan and resolves all implementation details:
- Validate all node types via `uip flow registry get` to confirm ports, inputs, and outputs
- Resolve connector and resource nodes using the relevant node guide in `references/nodes/`
- Validate required fields against user-provided values
- Replace `<PLACEHOLDER>` values with resolved IDs
- Replace `core.logic.mock` nodes with real resource nodes (if published)
- Write `<SolutionName>.impl.plan.md` with resolved details and mermaid diagram

#### 5c. Iterate until approved

**Do NOT proceed to Step 6 until the user explicitly approves the plan.** The iteration loop:

1. User reviews the plan and gives feedback in chat (e.g., "move the Slack notification before the filter", "add an error handler after the API call", "use Salesforce instead of HubSpot")
2. Update `<SolutionName>.impl.plan.md` with the changes
3. Summarize what changed in chat
4. Repeat until the user says the plan is approved

### Step 6 — Build the flow

Edit `<ProjectName>.flow` directly in the project root. The `bindings_v2.json` file is also in the project root for resource bindings.

**Prefer CLI commands for adding nodes and edges.** They handle definitions and port wiring automatically, eliminating the most common build errors. Fall back to direct JSON editing only for operations the CLI doesn't support yet (update, remove, rewire).

#### Adding nodes

```bash
uip flow node add <ProjectName>.flow <nodeType> --output json \
  --input '{"expression": "$vars.fetchData.output.statusCode === 200"}' \
  --label "Check Status" \
  --position 300,400
```

The command automatically adds the node to the `nodes` array and its definition to `definitions`. Use `--input` to set node-specific inputs (script body, expression, URL, etc.).

> **Shell quoting tip:** If `--input` JSON contains special characters (quotes, braces, `$vars`), write the JSON to a temp file and pass it: `uip flow node add <file> <nodeType> --input "$(cat /tmp/input.json)" --output json`

After adding nodes, list them to get the assigned IDs for wiring:

```bash
uip flow node list <ProjectName>.flow --output json
```

#### Adding edges

```bash
uip flow edge add <ProjectName>.flow <sourceNodeId> <targetNodeId> --output json \
  --source-port success \
  --target-port input
```

The command automatically adds `targetPort` and validates the edge structure.

#### Configuring connector nodes

After adding a connector node with `node add`, configure it using the resolved values from Step 4:

```bash
uip flow node configure <ProjectName>.flow <nodeId> \
  --detail '<JSON from node guide>'
```

The `--detail` JSON structure varies by node type — see the relevant node guide in `references/nodes/` for the exact schema and examples. The command populates `inputs.detail` and creates workflow-level `bindings` entries. Use **resolved IDs**, not display names.

> **Shell quoting tip:** For complex `--detail` JSON, write it to a temp file: `uip flow node configure <file> <nodeId> --detail "$(cat /tmp/detail.json)"`

#### When to fall back to JSON editing

The CLI does not yet support: removing nodes, removing edges, updating existing node inputs (e.g., changing a script body), or rewiring existing edges. For these operations, edit the `.flow` JSON directly — see [references/flow-file-format.md](references/flow-file-format.md) and the Common Edits section above.

### Step 7 — Validate loop

Run validation and fix errors iteratively until the flow is clean.

```bash
uip flow validate <ProjectName>.flow --output json
```

**Validation loop:**
1. Run `uip flow validate`
2. If valid → done, move to Step 8 (push to Studio Web)
3. If errors → read the error messages, fix the `.flow` file
4. Go to 1

Common error categories:
- **Missing targetPort** — every edge needs a `targetPort` string
- **Missing definition** — every `type:typeVersion` in nodes needs a matching `definitions` entry
- **Invalid node/edge references** — `sourceNodeId`/`targetNodeId` must reference existing node `id`s
- **Duplicate IDs** — node and edge `id`s must be unique

### Step 8 — Debug (cloud) — only when explicitly requested

After validation passes, the user may want to test the flow end-to-end. **Do not run this without explicit user consent** — debug executes the flow for real (sends emails, posts messages, calls APIs). See Critical Rule #9.

```bash
UIPCLI_LOG_LEVEL=info uip flow debug <path-to-project-dir>
```

The argument is the **project directory path** (the folder containing `project.uiproj`). Use `<ProjectName>/` from the solution dir, or `.` if already inside the project dir. This uploads the project to Studio Web, triggers a debug session in Orchestrator, and streams results.

> **Note:** Requires `uip login`. Debug is for **testing that the flow runs correctly** — not for publishing or viewing. To publish, use Step 9 instead.

### Step 9 — Publish to Studio Web

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
- **Never `registry get` built-in nodes during Phase 1 planning** — the planning guide already documents all OOTB node types with ports and inputs. Redundant lookups waste tokens. However, Phase 2 **requires** registry validation of all node types to confirm the current product state before building.
- **Never skip capability discovery for connector nodes** — the registry tells you a node exists; only the node guide's discovery workflow tells you what operations and fields it supports. Skipping this is the #1 cause of broken connector nodes.
- **Never edit `content/*.bpmn`** — it is auto-generated from the `.flow` file and will be overwritten.
- **Never run `flow debug` as a validation step** — debug executes the flow with real side effects. Use `flow validate` for checking correctness.
- **Never skip the planning step for multi-node flows** — jumping straight to building produces flows that need major rework.
- **Never chain skills automatically** — if the flow needs an RPA process, coded workflow, or agent, insert a `core.logic.mock` placeholder and tell the user which skill to use. Do not invoke other skills.
- **Never hand-write `definitions` entries** — always copy from registry output. Hand-written definitions have wrong port schemas and cause validation failures.
- **Never batch multiple edits before validating** — validate after each change to catch errors early.
- **Never use `console.log` in script nodes** — `console` is not available in the Jint runtime. Use `return { debug: value }` to inspect values.
- **Never forget output mapping on End nodes** — every `out` variable in `variables.globals` must have a `source` expression in every reachable End node's `outputs`. Missing mappings cause silent runtime failures.
- **Never update `in` variables** — only `inout` variables can be modified via `variableUpdates`. Input variables are read-only after flow start.
- **Never reference parent-scope `$vars` inside a subflow** — subflows have isolated scope. Pass values explicitly via subflow inputs.

## Task Navigation

| I need to... | Read these |
|---|---|
| **Edit an existing flow** | Common Edits section |
| **Generate a flow plan** | [references/planning-phase-architectural.md](references/planning-phase-architectural.md) + [references/planning-phase-implementation.md](references/planning-phase-implementation.md) + Step 5 |
| **Choose the right node type** | [references/planning-phase-architectural.md — Node Selection Heuristics](references/planning-phase-architectural.md#node-selection-heuristics) |
| **Understand the .flow JSON format** | [references/flow-file-format.md](references/flow-file-format.md) |
| **Know all CLI commands** | [references/flow-commands.md](references/flow-commands.md) |
| **Add a Script node** | [references/flow-file-format.md - Script node](references/flow-file-format.md) |
| **Wire nodes with edges** | [references/flow-file-format.md - Edges](references/flow-file-format.md) |
| **Find the right node type** | Run `uip flow registry search <keyword>` |
| **Work with connector/resource nodes** | Relevant node guide in `references/nodes/` + [/uipath:uipath-platform — Integration Service](/uipath:uipath-platform) |
| **Publish to Studio Web** | Step 9 (solution bundle + upload) |
| **Deploy to Orchestrator** (only if explicitly requested) | [references/flow-commands.md](references/flow-commands.md) + [/uipath:uipath-platform](/uipath:uipath-platform) |
| **Manage variables and expressions** | [references/variables-and-expressions.md](references/variables-and-expressions.md) |
| **Write `=js:` expressions** | [references/variables-and-expressions.md — Expression System](references/variables-and-expressions.md) |
| **Orchestrate RPA, agents, apps** | [references/orchestration-guide.md](references/orchestration-guide.md) |
| **Create a resource that doesn't exist yet** | [references/orchestration-guide.md — Create New Workflow](references/orchestration-guide.md) |
| **Add data transform nodes** | [references/node-reference.md — Data Transform](references/node-reference.md) |
| **Create a subflow** | [references/node-reference.md — Subflow](references/node-reference.md) + Common Edits |
| **Add a delay or scheduled trigger** | [references/node-reference.md](references/node-reference.md) |
| **Use queue nodes** | [references/orchestration-guide.md — Queue Integration](references/orchestration-guide.md) |

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
8. **Trouble?** — if the user hit issues during this session, mention: "If something didn't work as expected, say `/report-issue` to file a bug report."

## References

- **[Planning Phase 1: Architectural Design](references/planning-phase-architectural.md)** — Node type catalog, topology design, mermaid diagram generation, wiring rules, and common patterns. **Read this first when planning a new flow.**
- **[Planning Phase 2: Implementation Resolution](references/planning-phase-implementation.md)** — Implementation resolution process (registry lookups, connection binding, reference field resolution), plus the full node catalog, wiring rules, and flow patterns needed for building. **Read this after the architectural plan is approved.**
- **[.flow File Format](references/flow-file-format.md)** — JSON schema, node/edge structure, definition requirements, and minimal working example
- **[CLI Command Reference](references/flow-commands.md)** — All `uip flow` subcommands with parameters
- **[Variables and Expressions](references/variables-and-expressions.md)** — Variable declaration (in/out/inout), type system, `=js:` Jint expressions, template syntax, scoping rules, output mapping, and variable updates
- **[Orchestration Guide](references/orchestration-guide.md)** — How to orchestrate RPA processes, agents, apps, other flows, and API workflows. Includes resource node types, "create new" workflow, queue integration, and human task patterns
- **[Node Reference](references/node-reference.md)** — Complete catalog of OOTB nodes not in the planning guide: data transforms, delay, subflow, scheduled trigger, queue nodes
- **[IS Activity Nodes](references/nodes/is-activity.md)** — Complete guide for IS connector activity nodes: connection binding, enriched metadata, reference resolution, `bindings_v2.json` schema, IS CLI commands, and debugging. See [contribution template](references/nodes/_contribution-template.md) for adding new node category guides
- **[Pack / Publish / Deploy](/uipath:uipath-platform)** — Orchestrator deployment only when explicitly requested (uipath-platform skill). Default publish path is Studio Web via `solution bundle` + `solution upload` (Step 9).
