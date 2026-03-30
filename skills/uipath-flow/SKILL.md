---
name: uipath-flow
description: "This skill should be used when the user wants to 'create a new Flow project', 'scaffold a flow with uip flow init', 'add a node to my flow', 'connect nodes in my flow', 'validate a .flow file', 'debug a flow', 'run a flow', 'discover flow node types', or when the user is editing a .flow file, wiring nodes and edges, working with definitions or ports, or asks about the .flow JSON format or uip flow CLI commands."
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

## Critical Rules

1. **Do NOT `registry get` built-in nodes.** The planning guide already documents all OOTB node types (script, HTTP, decision, switch, loop, merge, end, terminate, transform, mock) with their ports, inputs, and output variables. Only run `uip flow registry get <nodeType> --output json` for **connector nodes** and **unknown/new node types** not in the planning guide. When editing JSON directly, copy the `Data.Node` object into `definitions` verbatim — do not guess node schemas.
2. **ALWAYS discover connector capabilities via IS before planning.** Follow Step 4 for every connector node: fetch a connection (4a), call `registry get --connection-id` for enriched metadata (4b), and resolve reference fields via `uip is resources execute list` (4c). Without this, `inputs.detail` will be wrong and `$vars` references will be unresolvable — errors that `flow validate` does not catch.
3. **ALWAYS check for existing connections** before using a connector node. Run `uip is connections list <connector-key>` — if no connection exists, tell the user before proceeding.
4. **ALWAYS use `--output json`** on all `uip` commands when parsing output programmatically.
5. **Edit `flow_files/*.flow` only** — `content/*.bpmn` and `entry-points.json` are auto-generated and will be overwritten. To declare flow inputs/outputs, add variables in the `.flow` file (see [references/flow-file-format.md](references/flow-file-format.md)).
6. **`targetPort` is required on every edge** — `validate` rejects edges without it.
7. **Every node type needs a `definitions` entry** — copy from `uip flow registry get <nodeType>` output. Never hand-write definitions.
8. **Script nodes must `return` an object** — `return { key: value }`, not a bare scalar.
9. **Do NOT run `flow debug` without explicit user consent** — debug executes the flow for real (sends emails, posts messages, calls APIs).
10. **Validate after every change** — run `uip flow validate` after each edit to the `.flow` file. Do not batch multiple edits before validating.

## Common Edits (existing flows)

For targeted changes to an existing flow, use the recipes below instead of the full Quick Start pipeline. Always run `uip flow validate` after editing.

### Change a script body

Edit the `inputs.script` string on the target node in `flow_files/<ProjectName>.flow`. Script nodes must return an object (`return { key: value }`), not a scalar.

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

At this point you know **which connector node types** to use (e.g., `uipath.connector.uipath-atlassian-jira.create-issue`). Do **not** run `registry get` yet — you need a connection ID first to get enriched metadata. For OOTB nodes (scripts, HTTP, branching), you can call `registry get` immediately since they don't need a connection.

### Step 4 — Bind connections, fetch metadata, and resolve references (when using connectors)

**Skip this step if the flow only uses OOTB nodes.** When the flow uses Integration Service connectors (e.g., Jira, Slack, Salesforce), follow these sub-steps in order:

#### 4a. Fetch and bind connections

For each connector used in the flow, extract the connector key from the node type (`uipath.connector.<connector-key>.<activity-name>`) and fetch a connection. **If a connector key fails**, list all available connectors to find the correct key: `uip is connectors list --output json`. Connector keys are often prefixed (e.g., `uipath-<service>`).

```bash
# 1. List available connections
uip is connections list "<connector-key>" --output json

# 2. Pick the default enabled connection (IsDefault: Yes, State: Enabled)

# 3. Verify the connection is healthy
uip is connections ping "<connection-id>" --output json
```

Once you have the connection ID, write it into `content/bindings_v2.json`. See [references/flow-file-format.md — Bindings](references/flow-file-format.md) for the schema and examples.

**Read [/uipath:uipath-platform — Integration Service — connections.md](/uipath:uipath-platform) for connection selection rules** (default preference, HTTP fallback, multi-connection disambiguation, no-connection recovery, ping verification).

#### 4b. Get enriched node definitions with connection

Call `registry get` with `--connection-id` to fetch connection-aware metadata including custom fields:

```bash
uip flow registry get <nodeType> --connection-id <connection-id> --output json
```

This returns enriched `inputDefinition.fields` and `outputDefinition.fields` with accurate type, required, description, enum, and `reference` info. Without `--connection-id`, only standard/base fields are returned.

#### 4c. Resolve reference fields

Check `inputDefinition.fields` from the `registry get` response for fields with a `reference` object — these require ID lookup from the connector's live data. Use `uip is resources execute list` to resolve them:

```bash
# Example: resolve Slack channel "#test-slack" to its ID
uip is resources execute list "uipath-salesforce-slack" "curated_channels?types=public_channel,private_channel" \
  --connection-id "<id>" --output json
# → { "id": "C1234567890", "name": "test-slack" }
```

Use the resolved IDs (not display names) in the flow's node `inputs`. Present options to the user when multiple matches exist.

**Read [/uipath:uipath-platform — Integration Service — resources.md](/uipath:uipath-platform) for the full reference resolution workflow**, including: identifying reference fields, dependency chains (resolve parent fields before children), pagination, describe failures, and fallback strategies.

#### 4d. Validate required fields against user prompt

**Check every required field** in `inputDefinition.fields` against what the user provided. This is a hard gate — do NOT proceed to planning or building until all required fields have values.

1. Collect all fields where `required: true` from each connector node's metadata
2. For each required field, check if the user's prompt contains a value
3. If any required field is missing, **ask the user** before proceeding — list the missing fields with their `displayName` and what kind of value is expected
4. Only after all required fields are accounted for, proceed to planning

> **Do NOT guess or skip missing required fields.** A missing required field will cause a runtime error. It is always better to ask than to assume.

After completing Steps 4a–4d, you should have for each connector node: a bound connection ID, enriched field metadata, and resolved values for all reference fields. Carry this information into the planning step.

### Step 5 — Plan the flow (interactive)

**Required when creating a new flow or adding multiple nodes.** Only skip this step for small targeted edits to an *existing* flow (e.g., changing a script body, renaming a node, tweaking one connection). When in doubt, plan.

**Before planning, read [references/flow-planning-guide.md](references/flow-planning-guide.md)** for the complete node catalog, node selection heuristics (when to use Decision vs Switch, Loop vs ForEach, connector vs HTTP, End vs Terminate), expression/variable syntax, wiring rules, and common flow patterns.

Generate a plan as a **markdown file** with a mermaid diagram and structured details. This lets the user (and PMs) review the flow topology before any code is written.

#### 5a. Write the plan file

Write `flow-plan.md` in the project directory with the following sections. For subsequent updates (Step 5c), edit `flow-plan.md` directly.

**Required sections:**

1. **Summary** — 2-3 sentences describing what the flow does end-to-end
2. **Flow Diagram** — a mermaid diagram showing all nodes, edges, and branching logic. Use `subgraph` blocks to group related sections (e.g., "Data Ingestion", "Processing", "Notification"). For flows with 20+ nodes, subgraphs are essential for readability. Use direction TB (top-bottom) for most flows; LR (left-right) only for very linear flows with few branches.
3. **Node table** — markdown table with columns: `#`, `Name`, `Category`, `Node Type`, `Description`. Category is one of: trigger, action, script, control, connector, agent.
4. **Edges** — markdown table with columns: `#`, `Source Node`, `Source Port`, `Target Node`, `Target Port`, `Description`. One row per edge. Source/target ports must match the node type's standard ports (see [references/flow-file-format.md](references/flow-file-format.md)).
5. **Connector details** (omit if no connectors) — markdown table with columns: `Node`, `Connector Key`, `Operation`, `Required Inputs`, `Connection`. Mark connection status as found or not found.
6. **Inputs & Outputs** — markdown table with columns: `Direction`, `Name`, `Type`, `Description`
7. **Open questions** (omit if none) — bulleted list, each prefixed with `**[REQUIRED]**`

#### 5b. Present the plan for review

In chat, output a **short summary only** (goal + key nodes + any open questions). Tell the user to review the full plan in `flow-plan.md`.

#### 5c. Iterate until approved

**Do NOT proceed to Step 6 until the user explicitly approves the plan.** The iteration loop:

1. User reviews the plan and gives feedback in chat (e.g., "move the Slack notification before the filter", "add an error handler after the API call", "use Salesforce instead of HubSpot")
2. Update `flow-plan.md` with the changes
3. Summarize what changed in chat
4. Repeat until the user says the plan is approved

### Step 6 — Build the flow

Edit `flow_files/<ProjectName>.flow` and `content/bindings_v2.json`. Never edit `content/<ProjectName>.bpmn` — it is auto-generated.

**Prefer CLI commands for adding nodes and edges.** They handle definitions and port wiring automatically, eliminating the most common build errors. Fall back to direct JSON editing only for operations the CLI doesn't support yet (update, remove, rewire).

#### Adding nodes

```bash
uip flow node add flow_files/<ProjectName>.flow <nodeType> --output json \
  --input '{"expression": "$vars.fetchData.output.statusCode === 200"}' \
  --label "Check Status" \
  --position 300,400
```

The command automatically adds the node to the `nodes` array and its definition to `definitions`. Use `--input` to set node-specific inputs (script body, expression, URL, etc.).

> **Shell quoting tip:** If `--input` JSON contains special characters (quotes, braces, `$vars`), write the JSON to a temp file and pass it: `cat /tmp/input.json | uip flow node add <file> <nodeType> --input "$(cat /tmp/input.json)" --output json`

After adding nodes, list them to get the assigned IDs for wiring:

```bash
uip flow node list flow_files/<ProjectName>.flow --output json
```

#### Adding edges

```bash
uip flow edge add flow_files/<ProjectName>.flow <sourceNodeId> <targetNodeId> --output json \
  --source-port success \
  --target-port input
```

The command automatically adds `targetPort` and validates the edge structure.

#### Configuring connector nodes

After adding a connector node with `node add`, configure it with the resolved connection and field values from Step 4:

```bash
uip flow node configure flow_files/<ProjectName>.flow <nodeId> \
  --detail '{"connectionId": "<id>", "folderKey": "<key>", "endpoint": "<endpoint>", "bodyParameters": {"fields.project.key": "ENGCE", "fields.issuetype.id": "10004"}}'
```

This populates `inputs.detail` (connection, endpoint, body/query/path parameters) and creates the workflow-level `bindings` entries automatically. Use **resolved IDs** from Step 4c, not display names.

> **Shell quoting tip:** For complex `--detail` JSON, write it to a temp file: `uip flow node configure <file> <nodeId> --detail "$(cat /tmp/detail.json)"`

#### When to fall back to JSON editing

The CLI does not yet support: removing nodes, removing edges, updating existing node inputs (e.g., changing a script body), or rewiring existing edges. For these operations, edit the `.flow` JSON directly — see [references/flow-file-format.md](references/flow-file-format.md) and the Common Edits section above.

### Step 7 — Validate loop

Run validation and fix errors iteratively until the flow is clean.

```bash
uip flow validate flow_files/<ProjectName>.flow --output json
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
- **Never `registry get` built-in nodes** — the planning guide already documents all OOTB node types with ports and inputs. Redundant registry calls waste tokens and time.
- **Never skip IS discovery for connector nodes** — the registry tells you a node exists; only IS tells you what operations and fields it supports. Skipping this is the #1 cause of broken connector nodes.
- **Never edit `content/*.bpmn`** — it is auto-generated from the `.flow` file and will be overwritten.
- **Never run `flow debug` as a validation step** — debug executes the flow with real side effects. Use `flow validate` for checking correctness.
- **Never skip the planning step for multi-node flows** — jumping straight to building produces flows that need major rework.
- **Never chain skills automatically** — if the flow needs an RPA process, coded workflow, or agent, insert a `core.logic.mock` placeholder and tell the user which skill to use. Do not invoke other skills.
- **Never hand-write `definitions` entries** — always copy from registry output. Hand-written definitions have wrong port schemas and cause validation failures.
- **Never batch multiple edits before validating** — validate after each change to catch errors early.

## Task Navigation

| I need to... | Read these |
|---|---|
| **Edit an existing flow** | Common Edits section |
| **Generate a flow plan** | [references/flow-planning-guide.md](references/flow-planning-guide.md) + Step 5 |
| **Choose the right node type** | [references/flow-planning-guide.md — Node Selection Guide](references/flow-planning-guide.md#node-selection-guide) |
| **Understand expressions and $vars** | [references/flow-planning-guide.md — Expressions](references/flow-planning-guide.md#expressions-and-variables) |
| **Understand the .flow JSON format** | [references/flow-file-format.md](references/flow-file-format.md) |
| **Know all CLI commands** | [references/flow-commands.md](references/flow-commands.md) |
| **Add a Script node** | [references/flow-file-format.md - Script node](references/flow-file-format.md) |
| **Wire nodes with edges** | [references/flow-file-format.md - Edges](references/flow-file-format.md) |
| **Find the right node type** | Run `uip flow registry search <keyword>` |
| **Bind connector connections** | Step 4a + [references/flow-file-format.md — Bindings](references/flow-file-format.md) |
| **Get enriched connector metadata** | Step 4b — `registry get --connection-id` |
| **Resolve reference fields** | Step 4c + [/uipath:uipath-platform — Integration Service — Resources](/uipath:uipath-platform) |
| **Discover connector capabilities** | Step 4 + [/uipath:uipath-platform — Integration Service](/uipath:uipath-platform) |
| **Check/create connections** | [/uipath:uipath-platform — Integration Service](/uipath:uipath-platform) |
| **Publish to Studio Web** | Step 9 (solution bundle + upload) |
| **Deploy to Orchestrator** (only if explicitly requested) | [references/flow-commands.md](references/flow-commands.md) + [/uipath:uipath-platform](/uipath:uipath-platform) |

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
5. **Missing connections** — any connector nodes that need IS connections the user must create
6. **Next step** — ask if the user wants to debug the flow (do not run debug automatically)
7. **Publish offer** — ask if the user wants to publish to Studio Web (do not publish automatically). If yes, run `solution bundle` + `solution upload` and share the Studio Web URL.

## References

- **[Flow Planning Guide](references/flow-planning-guide.md)** — Complete node catalog, expression system, wiring rules, node selection heuristics, validation rules, and common patterns. **Read this first when planning a new flow.**
- **[.flow File Format](references/flow-file-format.md)** — JSON schema, node/edge structure, definition requirements, and minimal working example
- **[CLI Command Reference](references/flow-commands.md)** — All `uip flow` subcommands with parameters
- **[Pack / Publish / Deploy](/uipath:uipath-platform)** — Orchestrator deployment only when explicitly requested (uipath-platform skill). Default publish path is Studio Web via `solution bundle` + `solution upload` (Step 9).
