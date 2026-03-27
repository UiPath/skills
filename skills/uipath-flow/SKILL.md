---
name: uipath-flow
description: "[EXPERIMENTAL] This skill should be used when the user wants to 'create a new Flow project', 'scaffold a flow with uip flow init', 'add a node to my flow', 'connect nodes in my flow', 'validate a .flow file', 'debug a flow', 'run a flow', 'discover flow node types', or when the user is editing a .flow file, wiring nodes and edges, working with definitions or ports, or asks about the .flow JSON format or uip flow CLI commands."
metadata:
   allowed-tools: Bash, Read, Write, Edit, Glob, Grep
disable-model-invocation: true
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

1. **ALWAYS query the registry before building.** Run `uip flow registry pull` then `uip flow registry get <nodeType> --format json` for every node type you plan to use. Copy the `Data.Node` object into `definitions` verbatim — do not guess node schemas, port names, or input fields from memory.
2. **ALWAYS discover connector capabilities via IS before planning.** For every connector node, run `uip is activities list <connector-key>` and `uip is resources describe <connector-key> <resource>` to learn the exact operations, required fields, and field types. Without this, `inputs.detail` will be wrong and `$vars` references will be unresolvable — errors that `flow validate` does not catch.
3. **ALWAYS check for existing connections** before using a connector node. Run `uip is connections list <connector-key>` — if no connection exists, tell the user before proceeding.
4. **ALWAYS use `--format json`** on all `uip` commands when parsing output programmatically.
5. **Edit `flow_files/*.flow` only** — `content/*.bpmn` is auto-generated and will be overwritten.
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

1. Get the new node's schema: `uip flow registry get <nodeType> --format json`
2. Add its `Data.Node` to the `definitions` array (skip if that type already has a definition)
3. Add the node instance to `nodes` with a unique `id` and correct `ui.position`
4. Find the edge connecting the two existing nodes — update it to point to the new node instead:
   - Change `targetNodeId` to the new node's `id` and `targetPort` to the new node's incoming port (usually `input`)
5. Add a new edge (with a unique `id`) from the new node to the original target:
   - `sourceNodeId`: new node's `id`, `sourcePort`: `success` (or the appropriate port)
   - `targetNodeId`: original target's `id`, `targetPort`: `input`
6. Check ports: see [references/flow-file-format.md — Standard ports](references/flow-file-format.md) for source/target ports by node type

### Add a branch (decision node)

1. Get the definition: `uip flow registry get core.logic.decision --format json` and add `Data.Node` to `definitions`
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
uip login status --format json
```

If not logged in and you need cloud features:
```bash
uip login                                          # interactive OAuth (opens browser)
uip login --authority https://alpha.uipath.com     # non-production environments
```

### Step 2 — Create a new Flow project

```bash
uip flow init <ProjectName>
```

This scaffolds a complete project. See [references/flow-file-format.md](references/flow-file-format.md) for the full project structure.

### Step 3 — Discover available node types

Before editing the `.flow` file, check what nodes are available:

```bash
uip flow registry pull                          # refresh local cache (expires after 30 min)
uip flow registry list --format json            # list all cached node types
uip flow registry search <keyword>              # search by name, tag, or category
uip flow registry search --filter "category=agent"
```

> **Auth note**: Without `uip login`, registry shows OOTB nodes only. After login, tenant-specific connector nodes are also available.

At this point you know **which connector node types** to use (e.g., `uipath.connector.uipath-atlassian-jira.create-issue`). Do **not** run `registry get` yet — you need a connection ID first to get enriched metadata. For OOTB nodes (scripts, HTTP, branching), you can call `registry get` immediately since they don't need a connection.

### Step 4 — Bind connections, fetch metadata, and resolve references (when using connectors)

**Skip this step if the flow only uses OOTB nodes.** When the flow uses Integration Service connectors (e.g., Jira, Slack, Salesforce), follow these sub-steps in order:

#### 4a. Fetch and bind connections

For each connector used in the flow, extract the connector key from the node type (`uipath.connector.<connector-key>.<activity-name>`) and fetch a connection.

**Read [/uipath:uipath-platform — Integration Service — connections.md](/uipath:uipath-platform) for the full connection selection workflow**, including:
- Native connector selection (default + enabled preference)
- HTTP fallback connector matching (name-based substring match for `uipath-uipath-http`)
- Multi-connection disambiguation (present options to user)
- No-connection recovery (prompt user to create)
- Ping verification (always ping before using — a connection can be `Enabled` but expired)
- Re-authentication via `uip is connections edit`

Quick reference:
```bash
# 1. List available connections
uip is connections list "<connector-key>" --format json

# 2. Pick the default enabled connection (IsDefault: Yes, State: Enabled)
#    Follow connections.md for selection rules and fallback

# 3. Verify the connection is healthy
uip is connections ping "<connection-id>" --format json
```

Once you have the connection ID, write it into **`content/bindings_v2.json`**. Add one `Connection` resource per unique connector:

```json
{
  "version": "2.0",
  "resources": [
    {
      "resource": "Connection",
      "key": "<connection-id>",
      "id": "Connection<connection-id>",
      "value": {
        "ConnectionId": {
          "defaultValue": "<connection-id>",
          "isExpression": false,
          "displayName": "<connector-key> connection"
        }
      },
      "metadata": {
        "ActivityName": "<activity-display-name>",
        "BindingsVersion": "2.2",
        "DisplayLabel": "<connector-key> connection",
        "UseConnectionService": "true",
        "Connector": "<connector-key>"
      }
    }
  ]
}
```

If a flow uses multiple connectors (e.g., Jira + Slack), add one `Connection` resource per connector to the `resources` array. See [references/flow-file-format.md — Bindings](references/flow-file-format.md) for the full schema and multi-connector examples.

#### 4b. Get enriched node definitions with connection

Now that you have a connection ID, call `registry get` with `--connection-id` to fetch connection-aware metadata. This returns the full field schema including custom fields specific to that connection/account:

```bash
uip flow registry get <nodeType> --connection-id <connection-id> --format json
```

The flow tool internally calls the Integration Service SDK's `getInstanceObjectMetadata` (instead of `getObjectMetadata`) when a connection ID is provided, returning enriched `inputDefinition.fields` and `outputDefinition.fields` with accurate type, required, description, enum, and `reference` info.

> **Without `--connection-id`**, `registry get` still returns metadata but only standard/base fields — custom fields and connection-specific reference data may be missing.

#### 4c. Resolve reference fields

Check the `inputDefinition.fields` from the `registry get` response for any field that has a `reference` object. These fields require their values to be looked up from the connector's live data.

**Read [/uipath:uipath-platform — Integration Service — resources.md](/uipath:uipath-platform) for the full reference resolution workflow**, including:
- How to identify reference fields (`reference.objectName`, `reference.lookupValue`)
- Resolving references via `uip is resources execute list`
- Inferring references without describe (fields ending in `Id` → base name convention)
- Describe failures and metadata gap recovery
- Read-only field recovery on create
- Pagination for large result sets

**How to identify reference fields** — look for the `reference` property in the `registry get` response:

```json
{
  "name": "fields.project.key",
  "displayName": "Project",
  "type": "string",
  "required": true,
  "reference": {
    "objectName": "project",
    "lookupValue": "key"
  }
}
```

This means the value for `fields.project.key` must be resolved by listing the `project` resource and using the `key` field from the results.

#### Field dependency chains

Some reference fields **depend on other fields** — e.g., Jira's `fields.issuetype.id` depends on `fields.project.key` (issue types are project-scoped). Resolving them in the wrong order returns duplicates across all projects.

**CRITICAL: If a parent field value is NOT in the user's prompt, you MUST ask the user for it BEFORE attempting to resolve any child fields.** Do not resolve child fields without a scoped parent — the results will be wrong or ambiguous.

**Resolution order:**
1. Identify which reference fields have parent dependencies (e.g., issue type depends on project)
2. Check if the user provided the parent field value in their prompt
3. **If the parent value is missing → ASK the user.** Do not skip, guess, or resolve the child unscoped.
4. Once you have the parent value, resolve the child field scoped to that parent

**Read [/uipath:uipath-platform — Integration Service — resources.md § Field Dependency Chains](/uipath:uipath-platform) for the full pattern**, including how to detect dependencies, the correct resolution order, and scoped path substitution.

**Example — user says "Create a Jira ticket with issue type Bug" (no project specified):**
1. Metadata shows `fields.issuetype.id` depends on `fields.project.key`
2. User did NOT provide a project → **ASK:** "Which Jira project should this be created in?"
3. User responds "ENGCE"
4. NOW resolve issue types scoped to ENGCE: `project/ENGCE/issuetypes`
5. Match "Bug" → ID `1`

**Do NOT resolve issue types globally without a project scope** — this returns issue types from ALL projects, leading to ambiguous or incorrect IDs.

Quick example — Jira project → issue type (when parent IS provided):
```bash
# Step 1: Resolve project (no dependency)
uip is resources execute list "uipath-atlassian-jira" "project" \
  --connection-id "<id>" --format json
# → { "key": "ENGCE", "id": "10845" }

# Step 2: Resolve issue types scoped to that project
uip is resources execute list "uipath-atlassian-jira" "project/ENGCE/issuetypes" \
  --connection-id "<id>" --format json
# → { "id": "10004", "name": "Bug" }  ← only issue types for ENGCE
```

#### Simple reference fields (no dependencies)

For fields with no parent dependency, resolve directly:

```bash
# Resolve Slack channel "#test-slack" to its channel ID
uip is resources execute list "uipath-salesforce-slack" "curated_channels?types=public_channel,private_channel" \
  --connection-id "<id>" --format json
# → { "id": "C1234567890", "name": "test-slack" }
```

**Present options to the user** when multiple matches exist. Use the resolved IDs (not display names) in the flow's node `inputs`.

#### Pagination for resource resolution

`uip is resources execute list` may not return all results in a single call (e.g., Slack channels, Jira users). **Always check for pagination** and fetch all pages when searching for a specific item.

**Pagination parameters:**
```bash
uip is resources execute list "<connector-key>" "<resource>" \
  --connection-id "<id>" \
  --page 1 --page-size 100 \
  --format json
```

**Pagination response headers** (available in the response):
- `elements-has-more`: `true` or `false` — indicates if more pages exist
- `elements-next-page-token`: opaque token to pass as `--next-page` for the next request

**Pagination loop:**
```bash
# First page
uip is resources execute list "<connector-key>" "<resource>" \
  --connection-id "<id>" --page-size 100 --format json
# → Check response: elements-has-more=true, elements-next-page-token="abc123"

# Next page (pass the token)
uip is resources execute list "<connector-key>" "<resource>" \
  --connection-id "<id>" --page-size 100 --next-page "abc123" --format json
# → Continue until elements-has-more=false or target item is found
```

**When to paginate:**
- When searching for a specific item by name (e.g., Slack channel "test-slack") and it's not in the first page
- When listing all items for user selection and the first page is incomplete

**Stop early:** If you find the target item in the current page, no need to fetch remaining pages.

> **Exception — HTTP connectors and http-request activities:** Connectors with key `uipath-uipath-http` and any connector's `*-http-request` activity do NOT use the `elements-*` pagination headers. These depend directly on vendor-specific pagination (e.g., `offset`/`limit` query params, `cursor` fields in the response body). Handle these on a case-by-case basis based on the vendor API docs.

> **Fallback when resolution fails:** If `execute list` returns empty or errors, fall back to using the user-provided display name as-is. The connector runtime may still resolve it. Note this as a risk in the plan. See the **Inferring References Without Describe** section in [resources.md](/uipath:uipath-platform) for naming-convention-based inference as a secondary fallback.

#### 4d. Validate required fields against user prompt

After fetching node metadata (Steps 4b/4c), **check every required field** in `inputDefinition.fields` against what the user provided in their prompt. This is a hard gate — do NOT proceed to planning or building until all required fields have values.

**Process:**
1. Collect all fields where `required: true` from each connector node's `inputDefinition.fields`
2. For each required field, check if the user's prompt contains a value for it
3. If any required field is missing, **ask the user** before proceeding:
   - List the missing fields with their `displayName` and `description`
   - For reference fields, explain what kind of value is expected (e.g., "Which Jira project should this issue be created in?")
   - Wait for the user's response before continuing
4. Only after all required fields are accounted for, proceed to reference resolution and planning

**Example — user says "Create a Jira ticket with issue type Bug":**
- Required fields from metadata: `fields.project.key` (Project), `fields.issuetype.id` (Issue type)
- User provided: issue type = Bug
- User did NOT provide: project
- **Ask:** "Which Jira project should this Bug be created in? (e.g., ENGCE, PROJ, etc.)"
- Wait for response, then continue

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

#### 6a. Build the .flow file

For each node:
1. Get the full node schema: `uip flow registry get <nodeType> --format json`
2. Copy the `Data.Node` object into the `definitions` array
3. Add the node instance to the `nodes` array with correct inputs (use resolved field values from Step 4c)
4. Add edges to the `edges` array with correct `sourcePort` and `targetPort`

For connector nodes, the node `inputs` should use **resolved IDs** from Step 4c, not display names:
```json
"inputs": {
  "fields.project.key": "ENGCE",
  "fields.issuetype.id": "10004",
  "fields.assignee.id": "5f4abc..."
}
```

#### 6b. Write bindings_v2.json

If the flow uses connector nodes, update `content/bindings_v2.json` with the Connection resources gathered in Step 4a. This file is what the runtime uses to resolve `<bindings.{connector-key} connection>` placeholders in node model context.

See [references/flow-file-format.md — Bindings](references/flow-file-format.md) for the full schema and multi-connector examples.

### Step 7 — Validate loop

Run validation and fix errors iteratively until the flow is clean.

```bash
uip flow validate flow_files/<ProjectName>.flow --format json
```

**Validation loop:**
1. Run `uip flow validate`
2. If valid → done, move to Step 8
3. If errors → read the error messages, fix the `.flow` file
4. Go to 1

Common error categories:
- **Missing targetPort** — every edge needs a `targetPort` string
- **Missing definition** — every `type:typeVersion` in nodes needs a matching `definitions` entry
- **Invalid node/edge references** — `sourceNodeId`/`targetNodeId` must reference existing node `id`s
- **Duplicate IDs** — node and edge `id`s must be unique

### Step 8 — Debug (cloud) — only when explicitly requested

```bash
uip flow debug flow_files/<ProjectName>.flow
```

Requires `uip login`. Uploads to Studio Web, triggers a debug session in Orchestrator, and streams results. Always `validate` first — debug is a cloud round-trip with real side effects (see Critical Rule #9).

## Anti-Patterns

- **Never guess node schemas** — always `uip flow registry get` first. Guessed port names or input fields cause silent wiring failures.
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
| **Pack / publish / deploy** | [/uipath:uipath-platform](/uipath:uipath-platform) |

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

Always use `--format json` for programmatic use. The `--localstorage-file` warning in some environments is benign.

## Completion Output

When you finish building or editing a flow, report to the user:

1. **File path** of the `.flow` file created or edited
2. **What was built** — summary of nodes added, edges wired, and logic implemented
3. **Validation status** — whether `flow validate` passes (or remaining errors if unresolvable)
4. **Mock placeholders** — list any `core.logic.mock` nodes that need to be replaced, and which skill to use
5. **Missing connections** — any connector nodes that need IS connections the user must create
6. **Next step** — ask if the user wants to debug the flow (do not run debug automatically)

## References

- **[Flow Planning Guide](references/flow-planning-guide.md)** — Complete node catalog, expression system, wiring rules, node selection heuristics, validation rules, and common patterns. **Read this first when planning a new flow.**
- **[.flow File Format](references/flow-file-format.md)** — JSON schema, node/edge structure, definition requirements, and minimal working example
- **[CLI Command Reference](references/flow-commands.md)** — All `uip flow` subcommands with parameters
- **[Pack / Publish / Deploy](/uipath:uipath-platform)** — Packaging and Orchestrator deployment (uipath-platform skill)
