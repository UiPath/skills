---
name: uipath-flow
description: "Create, edit, validate UiPath Flow projects (.flow). Two modes: CLI (uip flow) or direct JSON authoring. OOTB + dynamic resource + connector nodes. For XAML->uipath-rpa."
allowed-tools: Read, Write, Edit, Glob, Grep, Bash
---

# UiPath Flow

Build and edit UiPath Flow projects (`.flow` files) using either the `uip` CLI or direct JSON authoring. Both modes share the same file format, node types, variables system, and validation rules — the difference is how you execute operations.

## Mode Selection

Determine the implementation mode before starting work. If the user does not specify, ask.

| Signal | Mode |
|--------|------|
| User says "use CLI" or references `uip` commands | **CLI** |
| User says "edit JSON directly" or "author the flow" | **JSON Authoring** |
| User provides a `.flow` file to edit | **JSON Authoring** |
| No explicit preference | Ask the user |
| Flow needs dynamic resource or connector nodes | Either — both need CLI for registry/IS discovery |
| Publishing or debugging | Always CLI (both modes converge) |

**Default recommendation when asked:** JSON Authoring for OOTB-only flows (no external dependencies), CLI when the user is already working with `uip` commands.

**Mode guides:**
- CLI: [cli/workflow-guide.md](references/cli/workflow-guide.md) + [cli/commands-reference.md](references/cli/commands-reference.md)
- JSON: [json/workflow-guide.md](references/json/workflow-guide.md) + [json/authoring-guide.md](references/json/authoring-guide.md)

## Critical Rules

1. **Every edge must have both `targetPort` and `sourcePort`.** Validation rejects edges without `targetPort`. Missing `sourcePort` causes silent wiring failures.
2. **Every node type needs a `definitions` entry.** CLI: copy from `uip flow registry get <nodeType> --output json`. JSON: copy from the node's reference file in `references/nodes/`. Never hand-write definitions.
3. **For multi-node flows, complete both planning phases with user approval gates before building.** Read [planning-guide.md](references/planning-guide.md). Only skip planning for small targeted edits to an existing flow.
4. **Phase 1: `registry search`/`list` only. Phase 2: `registry get` required for all node types.** The planning guide documents OOTB node ports and inputs — sufficient for topology design without registry calls.
5. **Script nodes must `return {}` — never a bare scalar.** Use `return { key: value }`.
6. **Use `=js:` prefix for all expressions.** The runtime uses a Jint-based JavaScript engine (ES2020 subset). See [variables-guide.md](references/variables-guide.md).
7. **Every `out` variable must be mapped on every reachable End node.** Missing output mappings cause silent runtime failures.
8. **Only edit `<ProjectName>.flow` and optionally `bindings_v2.json`.** Other project files are CLI-managed and may be overwritten.
9. **Node and edge IDs must be unique.** Follow the ID generation algorithms in [json/authoring-guide.md](references/json/authoring-guide.md).
10. **Regenerate `variables.nodes` after every node add/remove.** CLI: automatic. JSON: rebuild from scratch per [json/workflow-guide.md](references/json/workflow-guide.md).
11. **Validate after every structural change.** CLI: `uip flow validate <file> --output json`. JSON: run the 17-item checklist in [validation-guide.md](references/validation-guide.md), optionally also CLI validate.
12. **Use `core.logic.mock` as placeholder for missing dynamic resource nodes.** Replace after the resource is published and `registry pull` confirms availability.
13. **Do not run `uip flow debug` without explicit user consent.** Debug executes the flow for real — sends emails, posts messages, calls APIs.
14. **Dynamic resource and connector nodes require CLI for registry/IS discovery, regardless of mode.** Both modes use `uip flow registry pull/search/get` and `uip is connections` commands.
15. **Always use `--output json` on all `uip` commands when parsing output.** Never invoke other skills automatically — provide handoff instructions instead.

## Common Edits (Existing Flows)

For targeted changes to an existing flow, use these recipes instead of the full Quick Start.

### Add a Node

**CLI:**
1. `uip flow registry get <nodeType> --output json` — get the definition.
2. `uip flow node add <file> <nodeType> --output json --label "Name" --position x,y` — adds node + definition automatically.
3. `uip flow edge add <file> <sourceId> <newNodeId> --source-port <port> --target-port input --output json`
4. `uip flow validate <file> --output json`

**JSON:**
1. Read `references/nodes/<type>.md` for the definition block and port table.
2. Add the definition to `workflow.definitions` (skip if type already exists).
3. Add the node instance to `workflow.nodes` with unique ID, correct `type`, `typeVersion`, `inputs`, and `ui.position`.
4. Add edges to `workflow.edges` (check port IDs from the reference doc).
5. Regenerate `workflow.variables.nodes`.
6. Run the validation checklist.

### Remove a Node

Both modes edit the `.flow` JSON directly (CLI does not support node removal):

1. Remove the node from `workflow.nodes`.
2. Remove all edges referencing the node's `id`.
3. Remove its definition from `workflow.definitions` only if no other node uses that `type:typeVersion`.
4. Rewire remaining edges if needed.
5. Regenerate `workflow.variables.nodes` (JSON mode) or validate (CLI mode).
6. Validate.

### Add an Edge

**CLI:**
```bash
uip flow edge add <file> <sourceId> <targetId> --source-port <port> --target-port input --output json
```

**JSON:**
1. Check both nodes' port tables in `references/nodes/`.
2. Generate edge ID: `{sourceId}-{sourcePort}-{targetId}-{targetPort}`.
3. Add the edge to `workflow.edges` with all four port fields.
4. Run the validation checklist.

### Add a Variable

Both modes edit `.flow` JSON directly (no CLI commands for variables):

1. Add the variable to `workflow.variables.globals` with `id`, `direction`, `type`, and optionally `defaultValue`.
2. If `direction` is `"in"`, set `triggerNodeId` to the trigger node's ID.
3. If `direction` is `"out"` or `"inout"`, add output mappings on every reachable End node.
4. See [variables-guide.md](references/variables-guide.md) for the full type system and expression syntax.

### Add a Resource Node (RPA Workflow, Agent, API Workflow, Agentic Process)

Requires `uip` CLI + `uip login`. Read [resource-node-guide.md](references/dynamic-nodes/resource-node-guide.md) for the full procedure.

**CLI:**
1. `uip flow registry pull --force` to refresh.
2. `uip flow registry search "<NAME>" --output json` to find it.
3. `uip flow node add <file> <nodeType> --output json` to add node + definition.
4. Wire edges and validate.

**JSON:**
1. `uip flow registry pull --force` then `registry search` then `registry get "<NODE_TYPE>" --output json`.
2. Copy the definition from registry output into `workflow.definitions`.
3. Create the node instance using the type-specific guide.
4. Generate 2 binding entries, add to `workflow.bindings`, update `model.context`.
5. Add edges, regenerate `variables.nodes`, validate.

If the resource is not published yet, use `core.logic.mock` placeholder.

### Add a Connector Node

Requires `uip` CLI + `uip login`. Read [connector-guide.md](references/connectors/connector-guide.md) for the full 6-step workflow. Discovery and resource description always use CLI; the final wiring step differs by mode.

## Quick Start: New Flow

### Step 1 — Determine mode

Ask the user or detect from context. See Mode Selection above.

### Step 2 — Project setup

**CLI:**
```bash
uip solution new "<SolutionName>" --output json
cd <SolutionDir> && uip flow init <ProjectName>
uip solution project add <ProjectDir> <SolutionFile.uipx>
```

**JSON:**
1. Create the project directory and `project.uiproj` file.
2. Pick the closest template from `assets/templates/` and copy as `<ProjectName>.flow`.
3. Update `name`, `id` (new UUID), and `metadata` timestamps.
4. See [project-setup-guide.md](references/project-setup-guide.md) for full details.

### Step 3 — Plan the flow (multi-node flows)

Required for new flows with 3+ nodes. Skip for small edits. Read [planning-guide.md](references/planning-guide.md).

**Phase 1 — Discovery & Architecture:**
- Discover capabilities via `registry search`/`list` (no `registry get`).
- Design topology: nodes, edges, variables.
- Produce `<SolutionName>.arch.plan.md` with mermaid diagram, node/edge tables, open questions.
- **GATE: Explicit user approval before Phase 2.**

**Phase 2 — Implementation Resolution:**
- Run `registry get` for all node types.
- Resolve connectors, resources, reference fields.
- Replace placeholders and mocks.
- Produce `<SolutionName>.impl.plan.md`.
- **GATE: Explicit user approval before building.**

### Step 4 — Build the flow

For each node in the approved plan:
1. Read the node's reference in `references/nodes/<type>.md` for ports, inputs, and definition.
2. **CLI:** `uip flow node add` + `uip flow edge add` (handles definitions and wiring automatically).
3. **JSON:** Insert into `workflow.nodes[]`, `workflow.definitions[]`, `workflow.edges[]`. Regenerate `variables.nodes`.

For connector nodes, follow [connector-guide.md](references/connectors/connector-guide.md).
For dynamic resource nodes, follow [resource-node-guide.md](references/dynamic-nodes/resource-node-guide.md).

### Step 5 — Variables

Both modes edit `.flow` JSON directly (no CLI commands for variables):
1. Declare inputs/outputs in `variables.globals`.
2. Map outputs on End nodes.
3. Add `variableUpdates` for state variables.
4. See [variables-guide.md](references/variables-guide.md).

### Step 6 — Validate

**CLI:** `uip flow validate <file> --output json` — fix errors, repeat until clean.

**JSON:** Walk through the 17-item checklist in [validation-guide.md](references/validation-guide.md). Optionally also run CLI validate if `uip` is available.

### Step 7 — Debug (only when explicitly requested)

Requires `uip login`. Executes the flow for real.

```bash
UIPCLI_LOG_LEVEL=info uip flow debug <project-dir>
```

See [publish-debug-guide.md](references/publish-debug-guide.md).

### Step 8 — Publish

Default target is Studio Web:
```bash
uip solution bundle <SolutionDir> --output .
uip solution upload <SolutionName>.uis --output json
```

Do NOT use `uip flow pack` + `uip solution publish` unless the user explicitly asks for Orchestrator deployment. See [publish-debug-guide.md](references/publish-debug-guide.md).

## Anti-Patterns

- **Never guess node schemas** — use the node reference files (JSON mode), `registry get` (CLI mode), or the planning guide for OOTB nodes. Guessed port names or input fields cause silent wiring failures.
- **Never `registry get` during Phase 1 planning** — use `registry search`/`list` for discovery. Save `registry get` for Phase 2.
- **Never skip capability discovery for connector nodes** — run `registry search` to confirm the connector exists and what operations it supports. Skipping this is the #1 cause of designing around a connector that doesn't exist.
- **Never edit `content/*.bpmn`** — auto-generated from the `.flow` file and will be overwritten.
- **Never run `flow debug` as a validation step** — debug executes the flow with real side effects. Use `flow validate` for checking correctness.
- **Never skip the planning step for multi-node flows** — jumping straight to building produces flows that need major rework.
- **Never chain skills automatically** — if the flow needs an RPA process, coded workflow, or agent, insert a `core.logic.mock` placeholder and tell the user which skill to use. Do not invoke other skills.
- **Never hand-write `definitions` entries** — always copy from reference files (JSON mode) or registry output (CLI mode).
- **Never batch multiple edits before validating** — validate after each change to catch errors early.
- **Never use `console.log` in script nodes** — `console` is not available in the Jint runtime. Use `return { debug: value }` to inspect values.
- **Never forget output mapping on End nodes** — every `out` variable must have a `source` expression in every reachable End node's `outputs`.
- **Never update `in` variables** — only `inout` variables can be modified via `variableUpdates`. Input variables are read-only after flow start.
- **Never reference parent-scope `$vars` inside a subflow** — subflows have isolated scope. Pass values explicitly via subflow inputs.
- **Never use `output` as the source port for script nodes** — the correct port is `success`.

## Reference Navigation

| I need to... | Read this |
|---|---|
| Understand the `.flow` JSON format | [flow-schema.md](references/flow-schema.md) |
| Create a new project from scratch | [project-setup-guide.md](references/project-setup-guide.md) |
| Plan a flow (node selection, topology) | [planning-guide.md](references/planning-guide.md) |
| Wire nodes together | [edge-wiring-guide.md](references/edge-wiring-guide.md) |
| Add variables and expressions | [variables-guide.md](references/variables-guide.md) |
| Validate my flow | [validation-guide.md](references/validation-guide.md) |
| Create a subflow | [subflow-guide.md](references/subflow-guide.md) |
| Understand bindings | [bindings-guide.md](references/bindings-guide.md) |
| Add a connector node | [connectors/connector-guide.md](references/connectors/connector-guide.md) |
| Add a resource node (shared structure) | [dynamic-nodes/resource-node-guide.md](references/dynamic-nodes/resource-node-guide.md) |
| Look up a specific OOTB node | [nodes/](references/nodes/) — one file per node type |
| Know all CLI commands | [cli/commands-reference.md](references/cli/commands-reference.md) |
| CLI workflow step-by-step | [cli/workflow-guide.md](references/cli/workflow-guide.md) |
| JSON authoring patterns | [json/authoring-guide.md](references/json/authoring-guide.md) |
| JSON workflow step-by-step | [json/workflow-guide.md](references/json/workflow-guide.md) |
| Publish or debug | [publish-debug-guide.md](references/publish-debug-guide.md) |

## OOTB Node Types

| Category | Node | Type | Reference |
|---|---|---|---|
| Trigger | Manual trigger | `core.trigger.manual` | [trigger-manual.md](references/nodes/trigger-manual.md) |
| Trigger | Scheduled trigger | `core.trigger.scheduled` | [trigger-scheduled.md](references/nodes/trigger-scheduled.md) |
| Data | Script | `core.action.script` | [action-script.md](references/nodes/action-script.md) |
| Data | HTTP Request | `core.action.http` | [action-http.md](references/nodes/action-http.md) |
| Data | Transform | `core.action.transform` | [action-transform.md](references/nodes/action-transform.md) |
| Data | Filter | `core.action.transform.filter` | [action-transform-filter.md](references/nodes/action-transform-filter.md) |
| Data | Queue Create | `core.action.queue.create` | [action-queue-create.md](references/nodes/action-queue-create.md) |
| Data | Queue Create and Wait | `core.action.queue.create-and-wait` | [action-queue-create-and-wait.md](references/nodes/action-queue-create-and-wait.md) |
| Logic | Decision (if/else) | `core.logic.decision` | [logic-decision.md](references/nodes/logic-decision.md) |
| Logic | Switch (multi-branch) | `core.logic.switch` | [logic-switch.md](references/nodes/logic-switch.md) |
| Logic | Loop (collection) | `core.logic.loop` | [logic-loop.md](references/nodes/logic-loop.md) |
| Logic | For Each | `core.logic.foreach` | [logic-foreach.md](references/nodes/logic-foreach.md) |
| Logic | While | `core.logic.while` | [logic-while.md](references/nodes/logic-while.md) |
| Logic | Merge (parallel join) | `core.logic.merge` | [logic-merge.md](references/nodes/logic-merge.md) |
| Logic | Delay | `core.logic.delay` | [logic-delay.md](references/nodes/logic-delay.md) |
| Logic | Mock (placeholder) | `core.logic.mock` | [logic-mock.md](references/nodes/logic-mock.md) |
| Control | End (stop branch) | `core.control.end` | [control-end.md](references/nodes/control-end.md) |
| Control | Terminate (stop all) | `core.logic.terminate` | [control-terminate.md](references/nodes/control-terminate.md) |
| Human | Human-in-the-Loop | `uipath.human-in-the-loop` | [hitl.md](references/nodes/hitl.md) |
| Mock | Blank (pass-through) | `core.mock.blank` | [mock-blank.md](references/nodes/mock-blank.md) |
| Mock | Mock (with error) | `core.mock.node` | [mock-node.md](references/nodes/mock-node.md) |

## Dynamic Resource Node Types

These nodes reference external Orchestrator resources. They require `uip` CLI + `uip login` + registry data.

| Category | Node | Type Pattern | Guide |
|---|---|---|---|
| RPA | RPA Workflow | `uipath.core.rpa-workflow.<KEY>` | [rpa-workflow-guide.md](references/dynamic-nodes/rpa-workflow-guide.md) |
| Agent | Autonomous Agent | `uipath.core.agent.<KEY>` | [agent-guide.md](references/dynamic-nodes/agent-guide.md) |
| API | API Workflow | `uipath.core.api-workflow.<KEY>` | [api-workflow-guide.md](references/dynamic-nodes/api-workflow-guide.md) |
| Orchestration | Agentic Process | `uipath.core.agentic-process.<KEY>` | [agentic-process-guide.md](references/dynamic-nodes/agentic-process-guide.md) |
| Connector | IS Connector | `uipath.connector.<key>.<activity>` | [connector-guide.md](references/connectors/connector-guide.md) |

All resource nodes share the same ports (`input`, `output`, `error`), `model` shape, and bindings pattern. See [resource-node-guide.md](references/dynamic-nodes/resource-node-guide.md).

## Completion Output

When you finish building or editing a flow, report:

1. **File path** of the `.flow` file created or edited
2. **What was built** — summary of nodes added, edges wired, and logic implemented
3. **Node count and edge count**
4. **Validation status** — whether validation passes (or remaining errors if unresolvable)
5. **Mock placeholders** — list any `core.logic.mock` nodes that need replacing, and which skill to use
6. **Missing connections** — any connector nodes that need connections the user must create
7. **Next step** — ask if the user wants to debug (do not run automatically) or publish to Studio Web (do not publish automatically)
