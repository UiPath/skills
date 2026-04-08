# Proposal: `uipath-lattice-flow` Skill

> **Status:** Draft — pending review
> **Date:** 2026-04-07
> **Codename:** lattice (7 chars, matching "maestro")

## Summary

A new skill that teaches coding agents to **read, create, edit, and validate `.flow` files as pure JSON** — no CLI dependency for OOTB flows. The agent manipulates the JSON structure directly using embedded node schemas and example templates.

The name "lattice" reflects the graph of interconnected nodes that a `.flow` file represents.

## Motivation

The existing `uipath-maestro-flow` skill relies heavily on CLI commands (`uip flow node add`, `uip flow registry get`, etc.) for every operation. This creates several friction points:

1. **Definitions blocker** — The `definitions` array must be copied from `registry get` output. This is the #1 source of errors and the #1 reason agents need the CLI.
2. **Registry dependency** — Even for OOTB nodes (which never change), the agent must hit the registry every time.
3. **Offline impossibility** — Without `uip login` and network access, agents cannot author flows at all.
4. **Round-trip overhead** — CLI calls add latency and context window cost for operations that are fundamentally JSON edits.

The 14 OOTB `.registration.json` files in `flow-workbench` contain everything an agent needs — port definitions, input schemas, defaults, BPMN model types. By embedding these as reference docs, the agent can construct valid nodes without the registry.

## Feasibility Analysis

| Capability | maestro-flow (CLI) | lattice-flow (direct JSON) | Feasible? |
|---|---|---|---|
| OOTB nodes (14 types) | `uip flow registry get` + `node add` | Schemas bundled as reference docs — zero CLI calls | Yes |
| Edge wiring | `uip flow edge add` | Agent writes JSON directly using port definitions from schemas | Yes |
| Variables | Manual JSON editing (no CLI exists) | Same approach — already direct JSON in maestro-flow | Yes |
| Validation | `uip flow validate` | Agent follows structural rules from schema docs; optional CLI as final check | Yes |
| Dynamic nodes (connectors, resources) | `uip flow registry search/get` + `node configure` | Still needs registry for discovery + schema pull — but JSON construction is direct | Partial |
| Project scaffolding | `uip flow init` | Agent creates the 6 project files from templates | Yes |

**The hard constraint:** Dynamic nodes (connectors like Jira, Slack, Salesforce; resources like RPA processes, agents) still require the registry for schema discovery. Their definitions are tenant-specific and version-sensitive. The skill will include a guide for these cases but cannot eliminate the registry dependency.

## Source Material

The following resources in `flow-workbench` provide the ground truth for this skill:

| Resource | Location | What It Provides |
|---|---|---|
| OOTB node schemas | `packages/registry/src/registry/ootb/*.registration.json` | Complete definition blocks, port configs, input schemas, defaults |
| Zod schema | `packages/flow-schema/src/workflow.ts` | Canonical `.flow` file validation schema |
| flow-core factory API | `packages/flow-core/src/index.ts` | Programmatic workflow construction functions |
| Example `.flow` files | `packages/cli/test-data/` | 23 real flow files covering all patterns |
| Node categories | `packages/registry/src/util/categories.ts` | Category IDs, names, sort orders |
| Dynamic node generation | `packages/registry/src/registry/uipath-v1/index.ts` | How platform APIs produce node definitions |

## Proposed Skill Structure

```
skills/uipath-lattice-flow/
├── SKILL.md                              # Skill definition
├── references/
│   ├── flow-schema-guide.md              # .flow JSON structure, top-level keys, validation rules
│   ├── project-scaffolding-guide.md      # How to create the 6 project files from scratch
│   ├── edge-wiring-guide.md              # Edge rules, port mappings, standard ports by node type
│   ├── variables-guide.md                # Variables, expressions, output mapping, scoping
│   ├── subflow-guide.md                  # Subflow structure, isolated scope, input/output passing
│   ├── dynamic-nodes-guide.md            # How to use registry for connectors/resources
│   ├── bindings-guide.md                 # bindings_v2.json format, connection binding
│   ├── validation-checklist.md           # Structural validation rules (manual pre-flight)
│   └── nodes/                            # One file per OOTB node type
│       ├── trigger-manual.md             # core.trigger.manual
│       ├── trigger-scheduled.md          # core.trigger.scheduled
│       ├── action-script.md              # core.action.script
│       ├── action-http.md                # core.action.http
│       ├── action-hitl.md                # core.action.hitl
│       ├── logic-decision.md             # core.logic.decision
│       ├── logic-switch.md               # core.logic.switch
│       ├── logic-loop.md                 # core.logic.loop
│       ├── logic-while.md                # core.logic.while
│       ├── logic-foreach.md              # core.logic.foreach
│       ├── logic-merge.md                # core.logic.merge
│       ├── logic-mock.md                 # core.logic.mock (placeholder)
│       ├── control-end.md                # core.event.end
│       └── control-terminate.md          # core.event.terminate
├── assets/
│   └── templates/
│       ├── minimal-flow-template.json    # Smallest valid .flow (start -> script -> end)
│       ├── project-scaffold-template.json # All 6 project files structure
│       ├── decision-flow-template.json   # Branch pattern (decision + two paths)
│       ├── loop-flow-template.json       # Loop pattern (foreach over collection)
│       └── http-flow-template.json       # HTTP request with response branching
```

### File Descriptions

#### SKILL.md

The skill definition with frontmatter, critical rules, and two workflows (new flow, edit existing flow). See the [SKILL.md Draft](#skillmd-draft) section below.

#### Reference Docs

| File | Purpose | Source Material |
|---|---|---|
| `flow-schema-guide.md` | Complete `.flow` JSON structure — top-level keys, node shape, edge shape, definitions array format | `@uipath/flow-schema` Zod schemas |
| `project-scaffolding-guide.md` | How to create a valid project directory (`.flow`, `project.uiproj`, `bindings_v2.json`, `entry-points.json`, `operate.json`, `package-descriptor.json`) | `uip flow init` output + flow-workbench project structure |
| `edge-wiring-guide.md` | Standard ports by node type, edge JSON format, connection rules, constraint validation | `handleConfiguration` from `.registration.json` files |
| `variables-guide.md` | Variable declaration (in/out/inout), type system, `=js:` expressions, output mapping on End nodes, `variableUpdates` | `@uipath/flow-schema` variable schemas + maestro-flow's existing `variables-and-expressions.md` |
| `subflow-guide.md` | Subflow JSON structure, isolated scope, input/output passing, Start/End node requirements | Example subflow `.flow` files from test-data |
| `dynamic-nodes-guide.md` | When and how to use the registry for connector/resource nodes — the bridge to CLI when OOTB isn't enough | maestro-flow's orchestration and IS activity guides |
| `bindings-guide.md` | `bindings_v2.json` schema, connection resource entries, connector binding metadata | IS activity guide from maestro-flow |
| `validation-checklist.md` | Numbered checklist of structural rules the agent verifies after each edit (replaces `uip flow validate` for basic checks) | `uip flow validate` error categories + Zod schema constraints |

#### Node Reference Docs (14 files)

Each node doc follows a consistent structure:

```markdown
# <Node Display Name>

**Type:** `core.action.script`
**Category:** data-operations
**BPMN Model:** `bpmn:ScriptTask`

## Ports

| Position | Handle ID | Type | Notes |
|----------|-----------|------|-------|
| left | `input` | target | Single incoming connection |
| right | `success` | source | Output after execution |

## Inputs

| Field | Type | Required | Default | Description |
|-------|------|----------|---------|-------------|
| `script` | string | Yes | `""` | JavaScript body (must `return { key: value }`) |

## Definition Block

Copy this verbatim into the `definitions` array:

```json
{ ... exact content from .registration.json ... }
```

## Node Instance Example

```json
{
  "id": "myScript",
  "type": "core.action.script",
  "typeVersion": "1.0.0",
  ...
}
```

## Common Mistakes
- Returning a scalar instead of an object from the script
- ...
```

#### Templates

| Template | Pattern | Nodes | Purpose |
|---|---|---|---|
| `minimal-flow-template.json` | Start -> Script -> End | 3 | Smallest valid flow — starting point for any new flow |
| `project-scaffold-template.json` | N/A | N/A | All 6 project file structures with placeholder values |
| `decision-flow-template.json` | Start -> Script -> Decision -> [Path A, Path B] -> End | 6 | Branching logic pattern |
| `loop-flow-template.json` | Start -> ForEach -> [Script in loop body] -> End | 4 | Iteration pattern |
| `http-flow-template.json` | Start -> HTTP -> Decision (status check) -> End | 5 | API call with response handling |

Templates are sourced from the 23 example `.flow` files in `flow-workbench/packages/cli/test-data/`, distilled to minimal working examples.

## SKILL.md Draft

```yaml
---
name: uipath-lattice-flow
description: "[PREVIEW] Direct .flow JSON authoring — create, edit, validate flows without CLI. OOTB node schemas bundled. For CLI-based flow authoring->uipath-maestro-flow."
---
```

```markdown
# Direct Flow Authoring

Build and edit UiPath Flow projects by writing .flow JSON directly. OOTB node schemas are bundled — no CLI or registry calls needed for standard flows.

## When to Use This Skill

- Creating or editing .flow files as JSON
- Working offline or without the uip CLI installed
- Building flows using OOTB nodes (triggers, scripts, HTTP, decisions, loops, etc.)
- Rapid prototyping of flow structures
- Understanding the .flow file format in detail

## Critical Rules

1. **Always start from a template** — never construct .flow JSON from memory. Pick the closest template from `assets/templates/` and modify it.
2. **Copy definition blocks verbatim** from the node reference docs in `references/nodes/`. Never hand-write or modify definition entries.
3. **Every edge must have `targetPort`** — validation rejects edges without it. Check the target node's port table.
4. **Every `out` variable must be mapped on every reachable End node** — missing output mappings cause silent runtime failures.
5. **For dynamic nodes (connectors, resources), use the registry** — read `references/dynamic-nodes-guide.md`. OOTB schemas do not cover tenant-specific nodes.
6. **Run the validation checklist after every edit** — walk through `references/validation-checklist.md` before declaring the flow complete.
7. **Use `=js:` prefix for all expressions** — the runtime uses a Jint-based JavaScript engine (ES2020 subset).
8. **Script nodes must `return` an object** — `return { key: value }`, not a bare scalar.
9. **Do not edit generated files** — only edit `<ProjectName>.flow` and `bindings_v2.json`. Other project files (`entry-points.json`, `operate.json`, `package-descriptor.json`) are managed by the CLI.
10. **Node and edge IDs must be unique** within the flow. Use descriptive, kebab-case IDs.

## Workflow: New Flow

1. **Scaffold the project** — Read `references/project-scaffolding-guide.md` and create the project directory structure.
2. **Pick a template** — Choose the closest template from `assets/templates/` and copy it as `<ProjectName>.flow`.
3. **Plan your nodes** — Identify which node types you need. Read the reference doc for each in `references/nodes/`.
4. **Add nodes** — For each node, copy the definition block into `definitions` and add the node instance to `nodes`.
5. **Wire edges** — Connect nodes using the port IDs from each node's reference doc.
6. **Add variables** — Declare inputs/outputs in `variables.globals`. Map outputs on End nodes.
7. **Validate** — Walk through `references/validation-checklist.md`.
8. **(Optional) CLI validation** — If `uip` is available, run `uip flow validate <file> --output json` for a final check.

## Workflow: Edit Existing Flow

1. **Read the .flow file** — understand the current structure.
2. **Read the relevant node reference doc** — check ports, inputs, and definition format.
3. **Make the JSON edit** — add/modify/remove nodes, edges, or variables.
4. **Validate** — walk through `references/validation-checklist.md`.

## When to Fall Back to uipath-maestro-flow

Use `uipath-maestro-flow` (CLI-based) when you need:
- **Connector nodes** (Jira, Slack, Salesforce, etc.) — schemas are tenant-specific
- **Resource nodes** (RPA processes, agents, apps) — schemas come from Orchestrator
- **Registry discovery** — finding what connectors or resources exist in a tenant
- **Flow debugging** — `uip flow debug` uploads and executes the flow in the cloud
- **Publishing** — `uip solution bundle` + `uip solution upload` for Studio Web

## Reference Navigation

| I need to... | Read this |
|---|---|
| Understand the .flow JSON format | [references/flow-schema-guide.md](references/flow-schema-guide.md) |
| Create a new project from scratch | [references/project-scaffolding-guide.md](references/project-scaffolding-guide.md) |
| Wire nodes together | [references/edge-wiring-guide.md](references/edge-wiring-guide.md) |
| Add variables and expressions | [references/variables-guide.md](references/variables-guide.md) |
| Create a subflow | [references/subflow-guide.md](references/subflow-guide.md) |
| Use connector or resource nodes | [references/dynamic-nodes-guide.md](references/dynamic-nodes-guide.md) |
| Configure connector bindings | [references/bindings-guide.md](references/bindings-guide.md) |
| Validate my flow | [references/validation-checklist.md](references/validation-checklist.md) |
| Look up a specific node type | [references/nodes/](references/nodes/) — one file per OOTB node |

## Anti-Patterns

- **Never guess a definition block** — always copy from the node reference doc. Guessed definitions have wrong port schemas and cause validation failures.
- **Never skip the validation checklist** — common errors (missing targetPort, duplicate IDs, orphaned edges) are easy to miss in raw JSON.
- **Never construct connector/resource nodes without the registry** — their schemas are dynamic and tenant-specific. Use `references/dynamic-nodes-guide.md`.
- **Never use `console.log` in script nodes** — `console` is not available in the Jint runtime. Use `return { debug: value }` to inspect values.
- **Never reference parent-scope `$vars` inside a subflow** — subflows have isolated scope. Pass values explicitly via subflow inputs.
```

## Key Differences from maestro-flow

| Aspect | maestro-flow | lattice-flow |
|---|---|---|
| Primary approach | CLI commands (`uip flow node add`, etc.) | Direct JSON manipulation |
| Node schemas | Fetched from registry at runtime | Bundled as reference docs |
| Definitions array | Must `registry get` every time | Pre-baked in node reference docs |
| Planning model | 2-phase (architectural -> implementation) | Template-first (pick template -> customize) |
| Dynamic nodes | Full CLI workflow | Guide for when/how to use registry (fallback) |
| Offline capable | No (needs registry + auth) | Yes, for OOTB flows |
| Validation | `uip flow validate` (required) | Structural checklist + optional CLI validation |
| Best for | Full-featured flows with connectors/resources | OOTB-only flows, rapid prototyping, learning |

## Coexistence Strategy

Both skills would exist simultaneously:

- **lattice-flow** — default for OOTB flows, offline work, prototyping
- **maestro-flow** — required when connectors, resources, or cloud operations are involved
- The `description` fields use `->` redirects to steer agents between them

The `uipath-planner` skill would be updated to route to the appropriate skill based on whether the flow needs dynamic nodes.

## Example Prompts (Same Results, Different Approach)

These prompts would activate `uipath-lattice-flow` and produce the same `.flow` file content as `uipath-maestro-flow`:

**Creating flows:**
- "Create a new UiPath Flow that sends a Slack message when an email arrives" (OOTB nodes only -> lattice; if Slack connector needed -> hands off to maestro)
- "Build a .flow project that runs a script and branches based on the result"
- "Initialize a Flow project with a scheduled trigger that runs every hour"

**Editing flows:**
- "Add a decision branch after the HTTP node in my .flow file"
- "Add a script node that transforms the API response"
- "Wire a new node between the filter and the end node"

**Operations:**
- "Validate my .flow file"
- "Show me the schema for a decision node"
- "What ports does the HTTP Request node have?"

## Build Plan

### Phase 1: Foundation (SKILL.md + schema + scaffolding + validation)
1. Write `SKILL.md` with frontmatter and workflows
2. Write `flow-schema-guide.md` from `@uipath/flow-schema` Zod schemas
3. Write `project-scaffolding-guide.md` from `uip flow init` output analysis
4. Write `validation-checklist.md` from `uip flow validate` error categories
5. Create `minimal-flow-template.json` from test-data examples

### Phase 2: Node references (14 node docs)
6. Convert each `.registration.json` into an agent-readable markdown doc
7. Extract definition blocks, port tables, input schemas, examples
8. Create `edge-wiring-guide.md` summarizing all ports across all nodes

### Phase 3: Variables, subflows, templates
9. Write `variables-guide.md` (can reuse content from maestro-flow)
10. Write `subflow-guide.md` from test-data subflow examples
11. Create remaining templates (decision, loop, HTTP patterns)

### Phase 4: Dynamic nodes and bindings
12. Write `dynamic-nodes-guide.md` — bridge to registry/CLI
13. Write `bindings-guide.md` for connector connection configuration

### Phase 5: Integration
14. Update CODEOWNERS
15. Update README.md skill catalog
16. Update `uipath-planner` routing table (if applicable)

## Open Questions

1. **Scope of dynamic nodes** — Should lattice-flow handle connector/resource nodes at all, or explicitly hand off to maestro-flow for those? Current proposal includes a guide but makes the handoff clear.
2. **Template count** — 5 templates cover the most common patterns. The flow-workbench has 23 test `.flow` files we could mine for more.
3. **Long-term direction** — Should lattice-flow eventually replace maestro-flow, or permanently coexist?
