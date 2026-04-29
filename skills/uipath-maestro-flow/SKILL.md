---
name: uipath-maestro-flow
description: "[PREVIEW] ALWAYS invoke for .flow / UiPath Maestro Flow tasks (read, edit, author, debug, or Q&A) — spec evolves. Leverages uip CLI: nodes, edges, subflows, scripts, variables, triggers, End nodes, registry."
allowed-tools: Bash, Read, Write, Edit, Glob, Grep
---

# UiPath Flow Authoring Assistant

Comprehensive guide for creating, editing, validating, and debugging UiPath Flow projects using the `uip` CLI and `.flow` file format.

## When to Use This Skill

- User wants to **create a new Flow project** with `uip maestro flow init`
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

1. **Always validate node types against the registry before building.** Use `registry search`/`list` for discovery and `registry get` for detailed metadata and definitions.
2. **ALWAYS follow the relevant plugin in `references/plugins/` for every node type.** Each plugin has a `planning.md` (when to use, selection heuristics, ports) and `impl.md` (registry validation, JSON structure, CLI commands, configuration, debug). For connector nodes, the [connector](references/plugins/connector/impl.md) plugin covers connection binding, enriched metadata, and field resolution — required before building. Without this, node configuration will be wrong — errors that `flow validate` does not catch.
3. **ALWAYS check for existing connections** before using a connector node — if no connection exists, tell the user before proceeding. See [connector/impl.md](references/plugins/connector/impl.md) for connection binding details.
4. **ALWAYS use `--output json`** on all `uip` commands when parsing output programmatically.
5. **Edit `<ProjectName>.flow` only** — other generated files (`bindings_v2.json`, `entry-points.json`, `operate.json`, `package-descriptor.json`) are managed by the CLI and may be overwritten. To declare flow inputs/outputs, add variables in the `.flow` file (see [references/flow-file-format.md](references/flow-file-format.md)).
6. **`targetPort` is required on every edge** — `validate` rejects edges without it.
7. **Every node type needs a `definitions` entry** — copy from `uip maestro flow registry get <nodeType>` output. Never hand-write definitions. The definition is the sole source for BPMN type (`model.type`), serviceType, event definitions, and binding/context templates — none of that belongs on the instance.
8. **Script nodes must `return` an object** — `return { key: value }`, not a bare scalar.
9. **Do NOT run `flow debug` without explicit user consent** — debug executes the flow for real (sends emails, posts messages, calls APIs).
10. **Validate once at the end** — run `uip maestro flow validate` only after all nodes, edges, and configuration are complete (Step 5). Do not validate after each individual node add or edit — intermediate states are expected to be invalid.
11. **Manage variables by editing `.flow` JSON directly** — there are no CLI commands for variable management. Add/remove/update variables in the `variables` section of the `.flow` file. See [references/variables-and-expressions.md](references/variables-and-expressions.md).
12. **Every `out` variable must be mapped on every reachable End node** — missing output mappings cause runtime errors. See [references/variables-and-expressions.md](references/variables-and-expressions.md).
13. **`=js:` prefix is REQUIRED on every `$vars`/`$metadata`/`$self` reference in a value field.** That includes connector node `inputs.detail.bodyParameters` / `queryParameters` / `pathParameters`, HTTP `url`/`headers`/`body`, end node output `source`, variable update `expression`, loop `collection`, and subflow `inputs.<id>.source`. Without `=js:`, the BPMN runtime sees a literal string (e.g. `"vars.X.output.Id"`) — `flow validate` does not catch this; it manifests at runtime as the wrong value bound to the activity input (MST-9107). Do NOT use `=js:` on condition expressions (decision `expression`, switch case `expression`, HTTP branch `conditionExpression`) — those are always evaluated as JS automatically. See [references/node-output-wiring.md](references/node-output-wiring.md) for the canonical rule and per-node-type field reference, and [references/variables-and-expressions.md](references/variables-and-expressions.md) for the underlying expression system.
14. **Resource discovery order — search before creating.** When the prompt references an existing resource by name ("use the X agent", "call the Y API workflow", "invoke the Z RPA process"), follow this order strictly before deciding the resource doesn't exist:
    1. **Tenant registry search** — `uip maestro flow registry search "<name>" --output json`. Requires `uip login`; returns published resources.
    2. **In-solution local discovery** — `uip maestro flow registry list --local --output json`. No login required; returns sibling projects in the same `.uipx` solution.
    3. **Only then create/scaffold** — scaffold an inline agent, mock, or create-new-resource only when both searches return no match AND either the user explicitly asks to embed/inline/create, or no published resource can satisfy the requirement.

    The words "coded" and "low-code" describe the *implementation style* of a published agent — they are NOT synonyms for "inline". `uipath.agent.autonomous` (inline) is only correct when the user explicitly asks to embed/inline/create a new agent inside this flow. `node add` auto-falls back to local discovery when a node type is not found in the cached registry. Only use `core.logic.mock` when the resource is **not** in the same solution and not yet published. See the relevant resource plugin's `impl.md` (e.g., [rpa](references/plugins/rpa/impl.md), [agent](references/plugins/agent/impl.md)).
15. **Never invoke other skills automatically** — when a flow needs an RPA process, agent, or app, identify the gap and provide handoff instructions. Let the user decide when to switch skills.
16. **Always run `flow tidy` after edits** — `uip maestro flow tidy <ProjectName>.flow` is the canonical layout step (Step 6). Tidy arranges nodes horizontally, sets every node's `size` to `{ "width": 96, "height": 96 }`, and recurses into subflows (`subflows[<id>].layout`). Skipping tidy is the most common cause of misshapen rectangles in Studio Web.
17. **Don't hand-write `layout.nodes` or `subflows[<id>].layout`** — these are owned by `flow tidy`. When authoring nodes, any placeholder `position` is fine (e.g. `{ x: 0, y: 0 }`); tidy rewrites it on save. Sticky notes (`type: "stickyNote"`) are the one exception — tidy preserves their custom size and position. See [flow-file-format.md — Layout](references/flow-file-format.md#layout).
18. **Every node that produces data MUST have `outputs` on the node instance** — Without an `outputs` block, downstream `$vars` references will not resolve at runtime. Action nodes need `output` + `error`; trigger nodes need `output` only; end/terminate nodes do not use this pattern. See [flow-file-format.md — Node outputs](references/flow-file-format.md#node-outputs). **Wrong:** relying on `outputDefinition` in `definitions` alone. **Right:** `outputs` on the node instance itself.
19. **Always present user questions as a dropdown with a "Something else" escape hatch** — Whenever this skill needs a decision from the user (which solution to use, publish vs debug vs deploy, which connector to pick, which trigger type, which resource to bind, etc.), use the `AskUserQuestion` tool with the enumerated choices as options AND include **"Something else"** as the last option so the user can supply free-form string input. Never ask open-ended questions in chat when a finite set of sensible defaults exists. If the user picks "Something else", parse their string answer and continue.
20. **A Flow project MUST live inside a solution** — always scaffold the solution first (`uip solution new <Name>`), then `cd <Name>` and run `uip maestro flow init <Name>`. The correct layout is **always** `<Solution>/<Project>/<Project>.flow` (double-nested). Running `uip maestro flow init` in a bare directory produces a single-nested `<Project>/<Project>.flow` layout that fails Studio Web upload, packaging, and downstream tooling. See Step 2.
21. **Node instances have no `model` block** — BPMN type, serviceType, version, event definitions, and all binding/context templates live in the node's **definition** (in the top-level `definitions[]` array, copied verbatim from `registry get`). The runtime hydrates these from the definition at serialization time. Instance-specific identity fields live under `inputs`: `entryPointId`, `isDefaultEntryPoint` (triggers), `source` (inline agents), `color`/`content` (sticky notes).

## Common Edits (existing flows)

For targeted changes to an existing flow, use the recipes below instead of the full Quick Start pipeline. Each recipe links to the detailed step-by-step procedure in the [flow editing operations guide](references/flow-editing-operations.md). Run `uip maestro flow validate` once after all edits are complete.

**Read [references/flow-editing-operations.md](references/flow-editing-operations.md) first** — Direct JSON is the default for all edits; CLI is used only for connector, connector-trigger, and inline-agent nodes, or when you explicitly request it.

| Edit | Description | Guide |
|------|-------------|-------|
| **Change a script body or node inputs** | Edit the node's `inputs` in-place in the `.flow` JSON. Do not delete + re-add — that changes the node ID and breaks `$vars` expressions. Script nodes must return an object (`return { key: value }`). | [JSON: Update node inputs](references/flow-editing-operations-json.md#update-node-inputs) |
| **Add a node between two existing nodes** | Remove the connecting edge, add the new node, wire upstream → new → downstream. | [JSON: Insert a node](references/flow-editing-operations-json.md#insert-a-node-between-two-existing-nodes) (default) or [CLI: Insert a node](references/flow-editing-operations-cli.md#insert-a-node-between-two-existing-nodes) (opt-in) |
| **Add a branch (decision node)** | Remove an edge, add a decision node, wire true/false branches. | [JSON: Insert a decision branch](references/flow-editing-operations-json.md#insert-a-decision-branch) (default) or [CLI: Insert a decision branch](references/flow-editing-operations-cli.md#insert-a-decision-branch) (opt-in) |
| **Remove a node** | Delete the node, sweep edges/definitions/variables, reconnect upstream to downstream. | [JSON: Remove a node](references/flow-editing-operations-json.md#remove-a-node-and-reconnect) (default) or [CLI: Remove a node](references/flow-editing-operations-cli.md#remove-a-node-and-reconnect) (opt-in, auto-cascades) |
| **Remove an edge** | Find the edge ID, delete it. | [JSON: Delete an edge](references/flow-editing-operations-json.md#delete-an-edge) (default) or [CLI: Delete an edge](references/flow-editing-operations-cli.md#delete-an-edge) (opt-in) |
| **Add a workflow variable** | Edit `variables.globals` in the `.flow` file (JSON only). For `out` variables, map on every End node. See [variables-and-expressions.md](references/variables-and-expressions.md). | [JSON: Add a workflow variable](references/flow-editing-operations-json.md#add-a-workflow-variable) |
| **Update a state variable** | Add a `variableUpdates` entry for `inout` variables (JSON only). See [variables-and-expressions.md](references/variables-and-expressions.md). | [JSON: Add a variable update](references/flow-editing-operations-json.md#add-a-variable-update) |
| **Create a subflow** | Add a `core.subflow` parent node + `subflows.{nodeId}` with nested nodes/edges/variables (JSON only). | [JSON: Create a subflow](references/flow-editing-operations-json.md#create-a-subflow) + [subflow/impl.md](references/plugins/subflow/impl.md) |
| **Add a scheduled trigger** | Replace `core.trigger.manual` with `core.trigger.scheduled`. | [JSON: Replace trigger](references/flow-editing-operations-json.md#replace-manual-trigger-with-scheduled-trigger) (default) or [CLI: Replace trigger](references/flow-editing-operations-cli.md#replace-manual-trigger-with-scheduled-trigger) (opt-in) + [scheduled-trigger/impl.md](references/plugins/scheduled-trigger/impl.md) |
| **Add a connector trigger** | Delete manual trigger, add connector trigger, configure with connection. | [CLI: Replace trigger](references/flow-editing-operations-cli.md#replace-manual-trigger-with-connector-trigger) + [connector-trigger/impl.md](references/plugins/connector-trigger/impl.md) |
| **Add a resource node** | Discover via registry (`--local` for in-solution, or tenant registry for published), add via JSON (default) or CLI (opt-in), wire edges. | Relevant plugin's `impl.md` + [JSON editing](references/flow-editing-operations-json.md) (default) or [CLI editing](references/flow-editing-operations-cli.md) (opt-in) |
| **Add an inline agent node** | Embed a `uipath.agent.autonomous` node with an inline agent definition living inside the flow project. | [inline-agent/planning.md](references/plugins/inline-agent/planning.md) for selection vs a published agent, [inline-agent/impl.md](references/plugins/inline-agent/impl.md) for scaffolding, CLI, JSON structure, and validation. |
| **Add a HITL QuickForm node** | Insert a human approval/review/enrichment checkpoint. Wire the `completed` port after adding. | [JSON: Add a node](references/flow-editing-operations-json.md) (default) or [CLI: `uip maestro flow hitl add`](references/flow-commands.md#uip-maestro-flow-hitl-add) (opt-in) + [hitl/impl.md](references/plugins/hitl/impl.md) |
| **Add a Batch Transform node** | Run an LLM over every row of a CSV attachment to append generated columns (classify, summarize, extract). Node type: `uipath.pattern.batch-transform`. Requires the tenant `canvas.nodes.patterns` feature flag. | [batch-transform/planning.md](references/plugins/batch-transform/planning.md) for selection vs Transform/Loop/Agent + [batch-transform/impl.md](references/plugins/batch-transform/impl.md) for `uip maestro flow node add`, JSON structure, and `outputColumns` shape. |
| **Add a Summarize node** | Comprehensive synthesis or Q&A over one attached document, with optional per-claim citations. Node type: `uipath.pattern.deep-rag`. Requires the tenant `canvas.nodes.patterns` feature flag. | [summarize/planning.md](references/plugins/summarize/planning.md) for selection vs Agent/Script + [summarize/impl.md](references/plugins/summarize/impl.md) for `uip maestro flow node add`, JSON structure, and `returnCitations`. |

## Planning (optional)

For complex flows, consider producing a plan before building. Reference [references/planning-arch.md](references/planning-arch.md) and [references/planning-impl.md](references/planning-impl.md) for the node type catalog, port reference, wiring rules, and topology patterns.

Planning is useful when:
- The flow has 5+ nodes with branching or parallel paths
- The flow uses connectors or resources that need discovery
- The user's requirements are ambiguous and you need to confirm the approach

Planning is NOT needed when:
- Adding/editing a single node in an existing flow
- The flow is a straightforward linear pipeline (trigger → action → action → end)
- The user has already described the exact topology they want

### Examples

**Plan:** "Build a flow that receives a Jira ticket, classifies it with an AI agent, routes urgent tickets to Slack and non-urgent to a queue, and logs everything to a Google Sheet."
→ Multiple services, branching logic, connector discovery needed. Plan first.

**Don't plan:** "Add a script node after the HTTP call that extracts the email field from the response."
→ Single targeted edit. Just do it.

**Don't plan:** "Create a flow that calls an API and sends the result to Slack."
→ Linear pipeline, user knows what they want. Build directly, ask questions inline if needed.

**Judgment call:** "Build me a flow that processes invoices."
→ Ambiguous requirements. But the right move is to ask clarifying questions, not produce a plan document. Plan if the answers reveal complexity.

## Quick Start

These steps are for **creating a new flow from scratch**. For existing projects, use the Common Edits section above or skip to the relevant step.

### Step 0 — Resolve the `uip` binary and detect command prefix

The `uip` CLI is installed via npm. Resolve the binary (it may not be on PATH in nvm environments) and detect the command namespace:

```bash
UIP=$(command -v uip 2>/dev/null || echo "$(npm root -g 2>/dev/null | sed 's|/node_modules$||')/bin/uip")
CURRENT=$($UIP --version 2>/dev/null | awk '{print $NF}')
```

If `uip` is not found at all, install it: `npm install -g @uipath/cli@latest`. If `npm install -g` fails with a permission error, prompt the user to re-run with appropriate privileges — do not retry automatically.

**Determine the command prefix based on installed version:**

| Installed version | Command prefix | Example |
|---|---|---|
| **≥ 0.3.4** | `uip maestro flow` | `uip maestro flow init MyProject` |
| **< 0.3.4** | `uip flow` | `uip flow init MyProject` |

```bash
MIN_VERSION="0.3.4"
if [ "$(printf '%s\n%s\n' "$MIN_VERSION" "$CURRENT" | sort -V | head -n1)" = "$MIN_VERSION" ]; then
  FLOW_CMD="uip maestro flow"
else
  FLOW_CMD="uip flow"
fi
echo "Using: $FLOW_CMD (CLI version $CURRENT)"
```

> **All commands in this skill are written as `uip maestro flow ...` (the ≥ 0.3.4 form).** If Step 0 detects a version below 0.3.4, replace `uip maestro flow` with `uip flow` when running any command. The arguments and flags are identical — only the prefix differs. See UiPath/cli#841 for background on the restructuring.

### Step 1 — Check login status

`uip maestro flow debug` and process operations require authentication. `uip maestro flow init`, `validate`, and `registry` commands work without login.

```bash
uip login status --output json
```

If not logged in and you need cloud features:
```bash
uip login                                          # interactive OAuth (opens browser)
uip login --authority https://alpha.uipath.com     # non-production environments
```

### Step 2 — Create a solution, THEN a Flow project inside it

> **A Flow project cannot exist outside a solution (Critical Rule #20).** You MUST scaffold or select a solution (Step 2a) BEFORE running `uip maestro flow init` (Step 2b). Skipping the solution step produces a single-nested `<Project>/<Project>.flow` layout that fails Studio Web upload and packaging. The correct layout is **always** `<Solution>/<Project>/<Project>.flow` (double-nested — see the tree after Step 2c).

Check the current directory for existing `.uipx` files. If existing solutions are found, use `AskUserQuestion` to present a dropdown with one option per discovered `.uipx`, a **"Create a new solution"** option, and **"Something else"** as the last option (for a custom path). If no existing solutions are found, create a new one automatically. See Critical Rule #19.

- If the user specifies an existing `.uipx` file path or solution name, use that (skip to Step 2b)
- Otherwise, create a new solution (Step 2a)

#### 2a. Create a new solution

```bash
uip solution new "<SolutionName>" --output json
```

This creates `<cwd>/<SolutionName>/<SolutionName>.uipx`. **You must `cd` into the new solution directory before Step 2b.**

> **Naming convention:** Use the same name for both the solution and the project unless the user specifies otherwise. If the user only provides a project name, use it as the solution name too.

#### 2b. Create the Flow project inside the solution folder

```bash
cd <directory>/<SolutionName> && uip maestro flow init <ProjectName>
```

The `cd` is required. Running `uip maestro flow init` from outside the solution directory (or from the parent of `<SolutionName>/`) is wrong — it produces a single-nested layout and breaks every later step.

#### 2c. Add the project to the solution

```bash
uip solution project add \
  <directory>/<SolutionName>/<ProjectName> \
  <directory>/<SolutionName>/<SolutionName>.uipx
```

#### Expected layout after Steps 2a–2c

```
<cwd>/
└── <SolutionName>/                    ← from `uip solution new`
    ├── <SolutionName>.uipx
    └── <ProjectName>/                 ← from `uip maestro flow init` (run from inside <SolutionName>/)
        ├── <ProjectName>.flow         ← the file you edit
        ├── project.uiproj
        ├── bindings_v2.json
        ├── entry-points.json
        ├── operate.json
        └── package-descriptor.json
```

**Self-check — run this before Step 3:**

```bash
ls "<directory>/<SolutionName>/<ProjectName>/<ProjectName>.flow"
```

If the file does not exist at that exact path (double-nested), Step 2 is wrong. Delete the partial scaffold and restart from Step 2a — do not try to patch the layout by hand.

See [references/flow-file-format.md](references/flow-file-format.md) for the full project structure.

### Step 3 — Refresh the registry

```bash
uip maestro flow registry pull                          # refresh local cache (expires after 30 min)
```

> **Auth note**: Without `uip login`, registry shows OOTB nodes only. After login, tenant-specific connector and resource nodes are also available. **In-solution sibling projects** are always available via `--local` without login — see below.

**In-solution discovery (no login required):**
```bash
uip maestro flow registry list --local --output json     # discover sibling projects in the same .uipx solution
uip maestro flow registry get "<nodeType>" --local --output json  # get full manifest for a local node
```
Run from inside the flow project directory. Returns the same manifest format as the tenant registry. Use `--local` to wire in-solution resources (RPA, agents, flows, API workflows) without publishing them first.

### Step 4 — Build the flow

For complex flows with multiple services or ambiguous requirements, consider planning first — see the Planning section above.

Edit `<ProjectName>.flow` directly in the project root. The `bindings_v2.json` file is also in the project root for resource bindings.

**Read [references/flow-editing-operations.md](references/flow-editing-operations.md).** Direct JSON is the default for all edits. CLI is used for connector, connector-trigger, and inline-agent nodes (see their plugin `impl.md`) or when the user explicitly opts in to CLI.

For each node type, follow the relevant plugin's `impl.md` for node-specific inputs, JSON structure, and configuration. The operations guides cover the mechanics (how to add/delete/wire); the plugins cover the semantics (what inputs and model fields each node type needs).

### Step 5 — Validate loop

Run validation and fix errors iteratively until the flow is clean.

```bash
uip maestro flow validate <ProjectName>.flow --output json
```

**Validation loop:**
1. Run `uip maestro flow validate`
2. If valid → done, move to Step 6 (tidy layout)
3. If errors → read the error messages, fix the `.flow` file
4. Go to 1

Common error categories:
- **Missing targetPort** — every edge needs a `targetPort` string
- **Missing definition** — every `type:typeVersion` in nodes needs a matching `definitions` entry
- **Invalid node/edge references** — `sourceNodeId`/`targetNodeId` must reference existing node `id`s
- **Duplicate IDs** — node and edge `id`s must be unique

### Step 6 — Tidy node layout

After validation passes, **always** run tidy before publishing or debugging — this is the canonical layout step (Critical Rule #16). Tidy:

- Arranges nodes horizontally (left-to-right) using ELK with `nodeSpacing: 96`, anchored to the leftmost node's original position
- Sets every non-stickyNote node's `size` to `{ "width": 96, "height": 96 }` so Studio Web renders square nodes (skipping this leaves any non-96 dimensions intact and produces misshapen rectangles — the MST-9061 failure mode)
- Recurses into subflows and rewrites `subflows[<id>].layout`
- Backfills missing `position`/`size` entries

```bash
uip maestro flow tidy <ProjectName>.flow --output json
```

### Step 7 — Debug (cloud) — only when explicitly requested

After validation passes, the user may want to test the flow end-to-end. **Do not run this without explicit user consent** — debug executes the flow for real (sends emails, posts messages, calls APIs). See Critical Rule #9.

**Always refresh solution resources before debug** so that connection and process resource declarations are in sync with the project bindings:

```bash
uip solution resource refresh <SolutionDir> --output json
UIPCLI_LOG_LEVEL=info uip maestro flow debug <path-to-project-dir> --output json
```

The argument to `resource refresh` is the **solution directory** (containing the `.uipx` file). The argument to `debug` is the **project directory path** (the folder containing `project.uiproj`). Use `<ProjectName>/` from the solution dir, or `.` if already inside the project dir. This uploads the project to Studio Web, triggers a debug session in Orchestrator, and streams results.

> **Note:** Requires `uip login`. Debug is for **testing that the flow runs correctly** — not for publishing or viewing. To publish, use Step 8 instead.

**Debug summary format:** Start the report with `Studio Web URL: <url>` and `Instance ID: <instanceId>` on the first two lines (parse `Data.studioWebUrl` / `Data.instanceId` from the JSON output). Use `<not returned by CLI>` if missing — never omit the line. See [flow-commands.md — uip maestro flow debug](references/flow-commands.md#uip-maestro-flow-debug).

### Step 7a — Troubleshoot failed flows

When a debug or process run fails, read **[references/troubleshooting-guide.md](references/troubleshooting-guide.md)**. Diagnostic priority: incidents → runtime variables → .flow correlation → traces (last resort).

### Step 8 — Publish to Studio Web

**This is the default publish target.** After tidy (Step 6), when the user wants to publish, view, or share the flow, **refresh solution resources first**, then upload:

```bash
# Sync resource declarations from project bindings
uip solution resource refresh <SolutionDir> --output json

# Upload the solution folder (containing the .uipx) to Studio Web
uip solution upload <SolutionDir> --output json
```

`uip solution upload` accepts the solution directory (the folder containing the `.uipx` file) directly — no intermediate bundling step is required. If the project was created with `uip maestro flow init`, it already lives inside a solution directory. The `upload` command pushes it to Studio Web where the user can visualize, inspect, edit, and publish from the browser. Share the Studio Web URL with the user.

**Do NOT run `uip maestro flow pack` + `uip solution publish` unless the user explicitly asks to deploy to Orchestrator.** That path puts the flow directly into Orchestrator as a process, bypassing Studio Web — the user cannot visualize or edit it there. If the user asks to "publish" without specifying where, always default to the Studio Web path (`uip solution upload <SolutionDir>`).

For Orchestrator deployment when explicitly requested, see [references/flow-commands.md](references/flow-commands.md) for `uip maestro flow pack` and the [/uipath:uipath-platform](/uipath:uipath-platform) skill for `uip solution publish`.

#### Post-build choice prompt

When the build completes, present the next-step dropdown described in the [Completion Output](#completion-output) section. See the detailed action table there for what each option runs.

## Anti-Patterns

- **Never run `uip maestro flow init` outside a solution directory** — the resulting `.flow` file MUST sit at `<Solution>/<Project>/<Project>.flow` (double-nested). Running `flow init` from a bare cwd, from the user's home, or from the parent of `<Solution>/` produces a single-nested `<Project>/<Project>.flow` layout that fails Studio Web upload, packaging, and the `uip solution project add` wiring. Always complete Step 2a first, `cd` into the solution dir, then Step 2b. Run the Step-2 self-check (`ls <Solution>/<Project>/<Project>.flow`) before continuing.
- **Never use `--format json` on any `uip` command** — the flag is `--output json` (Critical Rule #4). `--format` produces `error: unknown option '--format'` and exit code 3 on every `uip` subcommand, not a helpful message pointing you at `--output`.
- **Never guess node schemas** — use `registry get` for all node types. Guessed port names or input fields cause silent wiring failures.
- **Never skip capability discovery for connector nodes** — run `registry search` to confirm the connector exists and what operations it supports before building. See [connector/planning.md](references/plugins/connector/planning.md). Skipping this is the #1 cause of designing around a connector that doesn't exist or an operation it doesn't support.
- **Never edit `content/*.bpmn`** — it is auto-generated from the `.flow` file and will be overwritten.
- **Never run `flow debug` as a validation step** — debug executes the flow with real side effects. Use `flow validate` for checking correctness.
- **Never chain skills automatically** — if the flow needs an RPA process, coded workflow, or agent, identify the gap and tell the user which skill to use. Do not invoke other skills.
- **Never use `core.logic.mock` when the resource is in the same solution** — use `--local` discovery instead. Mock placeholders are only for resources that are not in the current solution and not yet published.
- **Never hand-write `definitions` entries** — always copy from registry output. Hand-written definitions have wrong port schemas and cause validation failures.
- **Never put a `model` block on node instances** — BPMN type, serviceType, event definition, binding templates, and context templates all live in the node's **definition** (copied verbatim from `registry get` into `definitions[]`). Instances carry only per-instance data: `inputs`, `outputs`, `display`. Identity fields like `entryPointId` / `isDefaultEntryPoint` (triggers), `source` (inline agents), and `color` / `content` (sticky notes) live under `inputs`.
- **Never author `model.context[]` on resource-node instances** — resource-node instances have no `model` block. For `uipath.core.*` resource nodes (rpa, agent, flow, agentic-process, api-workflow, hitl), the definition (from `registry get`) already carries `model.context[]` with `<bindings.{name}>` placeholders. Your job is to add matching entries to the top-level `bindings[]` array — two entries per resource node (`name` + `folderPath`) with `resourceKey` matching the definition's `model.bindings.resourceKey`. At BPMN emit, the runtime rewrites `<bindings.{name}>` → `=bindings.{id}` via `(resourceKey, name)` matching. Without the top-level `bindings[]` entries, `uip maestro flow validate` passes but `uip maestro flow debug` fails with "Folder does not exist or the user does not have access to the folder." See the resource plugin's `impl.md`.
- **Never put a `ui` block on node instances** — position and size belong in the top-level `layout.nodes` object. Nodes with `"ui": { "position": ... }` use the wrong format and may not render correctly in Studio Web.
- **Never skip `flow tidy` before publish or debug** — tidy is the only thing that guarantees square 96×96 nodes and a clean horizontal layout in Studio Web. Hand-written `layout` data with non-96 sizes (e.g., `{ width: 200, height: 80 }`) renders as misshapen rectangles until tidy normalizes the file (the MST-9061 failure mode). See Critical Rule #16 and Step 6.
- **Never omit `outputs` on nodes that produce data** — action nodes need `output` + `error`, trigger nodes need `output`. The `outputDefinition` in `definitions` is for the registry schema, not for runtime binding — without `outputs` on the node instance, `$vars` references downstream will fail silently.
- **Never validate after every individual edit** — intermediate flow states (e.g., node added but not yet wired) are expected to be invalid. Run `uip maestro flow validate` once after the full build is complete (Step 5).
- **Never use `console.log` in script nodes** — `console` is not available in the Jint runtime. Use `return { debug: value }` to inspect values.
- **Never forget output mapping on End nodes** — every `out` variable in `variables.globals` must have a `source` expression in every reachable End node's `outputs`. Missing mappings cause silent runtime failures.
- **Never update `in` variables** — only `inout` variables can be modified via `variableUpdates`. Input variables are read-only after flow start.
- **Never reference parent-scope `$vars` inside a subflow** — subflows have isolated scope. Pass values explicitly via subflow inputs.
- **Never use `core.action.http` (v1) for connector-authenticated requests** — the v1 node's `authenticationType: "connection"` input does not pass IS credentials at runtime. Use `core.action.http.v2` (Managed HTTP Request) instead. See [http/planning.md](references/plugins/http/planning.md).
- **Never hand-write `inputs.detail` for managed HTTP nodes** — run `uip maestro flow node configure` to populate the `inputs.detail` structure, generate `bindings_v2.json`, and create the connection resource file. Hand-written configurations miss the `essentialConfiguration` block and fail at runtime.
- **Never write `$vars.X` (or `$metadata.X`, `$self.X`) without `=js:`** in any connector `bodyParameters`/`queryParameters`/`pathParameters`, HTTP input field, end-node output `source`, variable update, loop collection, or subflow input. The serializer rewrites `$vars` → `vars` whether or not the prefix is present, so a missing prefix yields a literal string `"vars.X.output.Y"` at runtime — `flow validate` passes, the failure shows up only in `flow debug`. There is no `nodes.X.output.Y` syntax — it is invented and silently produces a literal string. See [references/node-output-wiring.md](references/node-output-wiring.md) for the per-node-type field reference (MST-9107).
- **Never reuse a reference ID (mailbox folder, Slack channel, Jira project, Google Sheet, etc.) from a prior flow or session** — reference IDs are scoped to the specific authenticated account behind the connection. A `parentFolderId` from one Outlook mailbox is invalid in another; a Slack channel ID from one workspace is invalid in another. A reused ID passes `flow validate` and `node configure` cleanly, then faults silently at runtime with no resolvable error. Always re-resolve via `uip is resources execute list <connector-key> <objectName> --connection-id <CURRENT_CONNECTION_ID> --output json` against the connection bound to this flow — do not paste a value you saw in another flow. See [connector/impl.md — Step 4](references/plugins/connector/impl.md) and [connector-trigger/impl.md — Step 3](references/plugins/connector-trigger/impl.md).

## Task Navigation

| I need to... | Read these |
| --- | --- |
| **Edit an existing flow** | Common Edits section + [references/flow-editing-operations.md](references/flow-editing-operations.md) |
| **Add/delete/wire nodes and edges** | [references/flow-editing-operations.md](references/flow-editing-operations.md) (strategy selection) + relevant plugin's `impl.md` (node-specific inputs) |
| **Generate a flow plan** | [references/planning-arch.md](references/planning-arch.md) + [references/planning-impl.md](references/planning-impl.md) + Planning section above |
| **Choose the right node type** | [references/planning-arch.md — Plugin Index](references/planning-arch.md#plugin-index) + relevant plugin's `planning.md` |
| **Understand the .flow JSON format** | [references/flow-file-format.md](references/flow-file-format.md) |
| **Know all CLI commands** | [references/flow-commands.md](references/flow-commands.md) |
| **Add a Script node** | [references/plugins/script/impl.md](references/plugins/script/impl.md) |
| **Wire nodes with edges** | [references/flow-editing-operations.md](references/flow-editing-operations.md) + [references/flow-file-format.md — Standard ports](references/flow-file-format.md) |
| **Find the right node type** | Run `uip maestro flow registry search <keyword>` |
| **Work with connector nodes** | [references/plugins/connector/](references/plugins/connector/) + [/uipath:uipath-platform — Integration Service](/uipath:uipath-platform) |
| **Publish to Studio Web** | Step 8 (`uip solution upload <SolutionDir>`) |
| **Deploy to Orchestrator** (only if explicitly requested) | [references/flow-commands.md](references/flow-commands.md) + [/uipath:uipath-platform](/uipath:uipath-platform) |
| **Manage variables and expressions** | [references/variables-and-expressions.md](references/variables-and-expressions.md) + [JSON: Variable Operations](references/flow-editing-operations-json.md#variable-operations) |
| **Write `=js:` expressions** | [references/variables-and-expressions.md — Expression System](references/variables-and-expressions.md) |
| **Wire one node's output into another node's input** | [references/node-output-wiring.md](references/node-output-wiring.md) — canonical `=js:$vars.<sourceNodeId>.output.<field>` pattern; per-node-type field reference; covers connector `bodyParameters`/`queryParameters`, HTTP, end-node `source`, variable updates |
| **Orchestrate RPA, agents, apps** | Relevant resource plugin: [rpa](references/plugins/rpa/), [agent](references/plugins/agent/), [agentic-process](references/plugins/agentic-process/), [flow](references/plugins/flow/), [api-workflow](references/plugins/api-workflow/), [hitl](references/plugins/hitl/) |
| **Embed an AI agent tightly coupled to this flow** | [references/plugins/inline-agent/](references/plugins/inline-agent/) — scaffolded via `uip agent init --inline-in-flow`, node type `uipath.agent.autonomous` |
| **Create a resource that doesn't exist yet** | Use `core.logic.mock` placeholder — see [CLI: Replace a mock](references/flow-editing-operations-cli.md#replace-a-mock-with-a-real-resource-node) + relevant plugin's `impl.md` |
| **Add data transform nodes** | [references/plugins/transform/impl.md](references/plugins/transform/impl.md) |
| **Apply an LLM to every row of a CSV** | [references/plugins/batch-transform/](references/plugins/batch-transform/) — node type `uipath.pattern.batch-transform`, appends LLM-generated columns to each row |
| **Summarize or answer questions over a document** | [references/plugins/summarize/](references/plugins/summarize/) — node type `uipath.pattern.deep-rag`, single-document synthesis with optional citations |
| **Create a subflow** | [references/plugins/subflow/impl.md](references/plugins/subflow/impl.md) + [JSON: Create a subflow](references/flow-editing-operations-json.md#create-a-subflow) |
| **Add a delay or scheduled trigger** | [references/plugins/delay/](references/plugins/delay/) or [references/plugins/scheduled-trigger/](references/plugins/scheduled-trigger/) |
| **Use queue nodes** | [references/plugins/queue/impl.md](references/plugins/queue/impl.md) |
| **Troubleshoot a failed flow** | [references/troubleshooting-guide.md](references/troubleshooting-guide.md) |

## Key Concepts

### validate vs debug

| Command | What it does | Auth needed |
|---------|-------------|-------------|
| `uip maestro flow validate` | Local JSON schema + cross-reference check | No |
| `uip maestro flow debug` | Converts to BPMN, uploads to Studio Web, runs in Orchestrator, streams results | Yes |

Always `validate` → `tidy` → `debug`. Validation is instant; tidy auto-layouts nodes; debug is a cloud round-trip.

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
4. **Tidy status** — confirm `flow tidy` was run
5. **Mock placeholders** — list any `core.logic.mock` nodes that need to be replaced, and which skill to use
6. **Missing connections** — any connector nodes that need connections the user must create
7. **Next step** — use `AskUserQuestion` to present a dropdown with these options (Critical Rule #19):

   | Option | Action |
   |--------|--------|
   | **Publish to Studio Web** (default) | Run `uip solution resource refresh <SolutionDir> --output json` then `uip solution upload <SolutionDir> --output json` and share the Studio Web URL. |
   | **Debug the solution** | Run `uip solution resource refresh <SolutionDir> --output json` then `UIPCLI_LOG_LEVEL=info uip maestro flow debug <ProjectDir> --output json` (see Step 7). Confirm consent first — debug executes the flow for real. |
   | **Deploy to Orchestrator** | Run `uip solution resource refresh <SolutionDir> --output json` then `uip maestro flow pack` + `uip solution publish` via the [/uipath:uipath-platform](/uipath:uipath-platform) skill. Only use when the user explicitly chooses this. |
   | **Something else** | Last option. Accept free-form string input and act on it (e.g., "just leave it", "pack but don't publish", "upload to a different tenant"). |

   Do not run any of these actions without an explicit user selection.

## References

- **[Flow Editing Operations](references/flow-editing-operations.md)** — Strategy selection matrix; **Direct JSON is the default**. Links to the two strategy guides below. **Read this before modifying any `.flow` file.**
  - [Direct JSON Strategy](references/flow-editing-operations-json.md) — Default for all `.flow` edits: node/edge CRUD, variables, subflows, output mapping, in-place input updates.
  - [CLI Strategy](references/flow-editing-operations-cli.md) — Carve-outs (connector, connector-trigger, inline-agent) and explicit user opt-in for `uip maestro flow node` and `uip maestro flow edge` commands.
- **[Planning: Discovery & Architectural Design](references/planning-arch.md)** — Capability discovery, plugin index, topology design, wiring rules, and common patterns.
- **[Planning: Implementation Resolution](references/planning-impl.md)** — Registry lookups, connection binding, reference field resolution, wiring rules, and flow patterns.
- **[.flow File Format](references/flow-file-format.md)** — JSON schema, node/edge structure, definition requirements, and minimal working example
- **[CLI Command Reference](references/flow-commands.md)** — All `uip flow` subcommands with flags and options
- **[Troubleshooting Guide](references/troubleshooting-guide.md)** — Diagnostic workflow for failed flows: incidents, runtime variables, definition correlation, traces, and `instance`/`incident` CLI reference
- **[Variables and Expressions](references/variables-and-expressions.md)** — Variable declaration (in/out/inout), type system, `=js:` Jint expressions, template syntax, scoping rules, output mapping, and variable updates
- **[Node Output Wiring](references/node-output-wiring.md)** — The single rule for wiring one node's output as another node's input. Per-node-type table of where `=js:` is required vs forbidden. Diagnoses the `vars.X.output.Y` literal-string failure mode (MST-9107).
- **[Node Plugins](references/plugins/)** — Each node type has its own plugin folder with `planning.md` (selection heuristics, ports, key inputs) and `impl.md` (registry validation, JSON structure, configuration, debug):
  - [connector](references/plugins/connector/) — IS connector nodes: connection binding, enriched metadata, reference resolution, `bindings_v2.json`
  - [script](references/plugins/script/) — Custom JavaScript logic via Jint ES2020
  - [http](references/plugins/http/) — REST API calls via `core.action.http.v2` (Managed HTTP Request — connector auth or manual mode)
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
  - [batch-transform](references/plugins/batch-transform/) — LLM-powered row-by-row CSV enrichment (`uipath.pattern.batch-transform`); appends generated columns to an attached file. Requires the tenant `canvas.nodes.patterns` feature flag.
  - [summarize](references/plugins/summarize/) — Single-document synthesis / Q&A (`uipath.pattern.deep-rag`) with optional per-claim citations. Requires the tenant `canvas.nodes.patterns` feature flag.
  - [queue](references/plugins/queue/) — Orchestrator queue item creation
- **[Pack / Publish / Deploy](/uipath:uipath-platform)** — Orchestrator deployment only when explicitly requested (uipath-platform skill). Default publish path is Studio Web via `uip solution upload <SolutionDir>` (Step 8).

> **Trouble?** If something didn't work as expected, use `/uipath-feedback` to send a report.
