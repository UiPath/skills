---
name: uipath-lattice-flow
description: "[PREVIEW] Direct .flow JSON authoring — create, edit, validate UiPath Flow projects (.flow files). OOTB node schemas bundled. For XAML→uipath-rpa."
allowed-tools: Read, Write, Edit, Glob, Grep
---

# Direct Flow Authoring

Build and edit UiPath Flow projects by writing `.flow` JSON directly. OOTB node schemas are bundled — no CLI or registry calls needed for standard flows.

## When to Use This Skill

- Creating or editing `.flow` files as JSON
- Working offline or without the `uip` CLI installed
- Building flows using OOTB nodes (triggers, scripts, HTTP, decisions, loops, etc.)
- Rapid prototyping of flow structures
- Understanding the `.flow` file format in detail
- Adding, removing, or rewiring nodes in an existing `.flow` file
- Debugging `.flow` validation errors

## Critical Rules

1. **Always start from a template** — never construct `.flow` JSON from memory. Pick the closest template from `assets/templates/` and modify it.
2. **Copy definition blocks verbatim** from the node reference docs in `references/nodes/`. Never hand-write or modify definition entries.
3. **Every edge must have `targetPort`** — validation rejects edges without it. Check the target node's port table in its reference doc.
4. **Every edge must have `sourcePort`** — check the source node's port table. Script nodes use `success` (not `output`).
5. **Every `out` variable must be mapped on every reachable End node** — missing output mappings cause silent runtime failures.
6. **Regenerate `variables.nodes` after every node add/remove** — rebuild the entire array from scratch per [project-scaffolding-guide.md](references/project-scaffolding-guide.md) Section 3.
7. **For dynamic nodes (connectors, resources), use the registry** — read `references/dynamic-nodes/`. OOTB schemas do not cover tenant-specific nodes.
8. **Run the validation checklist after every edit** — walk through [validation-checklist.md](references/validation-checklist.md) before declaring the flow complete.
9. **Use `=js:` prefix for all expressions** — the runtime uses a Jint-based JavaScript engine (ES2020 subset).
10. **Script nodes must `return` an object** — `return { key: value }`, not a bare scalar.
11. **Do not edit generated files** — only edit `<ProjectName>.flow` and optionally `bindings_v2.json`. Other project files are managed by the CLI at pack/deploy time.
12. **Node and edge IDs must be unique** within the flow. Follow the ID generation algorithms in [project-scaffolding-guide.md](references/project-scaffolding-guide.md).
13. **Deduplicate definitions** — `workflow.definitions` is keyed by `nodeType:version`. Do not add duplicate entries. When removing a node, only remove its definition if no other node uses that type.
14. **Use `core.logic.mock` as a placeholder** — when prototyping, use mock nodes as stand-ins for dynamic nodes you do not have schemas for yet.

## Common Edits (Existing Flows)

### Add a Node

1. Read the node's reference doc from `references/nodes/` to get the definition block and port table.
2. Add the definition block to `workflow.definitions` (skip if the type already exists).
3. Add the node instance to `workflow.nodes` with a unique ID, correct `type`, `typeVersion`, `inputs`, and `ui.position`.
4. Add edges connecting the new node (check port IDs from the reference doc).
5. Regenerate `workflow.variables.nodes` (Critical Rule 6).
6. Run the validation checklist.

### Remove a Node

1. Remove the node from `workflow.nodes`.
2. Remove all edges referencing the node's `id` (as `sourceNodeId` or `targetNodeId`).
3. Remove the definition from `workflow.definitions` only if no other node uses the same `type:typeVersion`.
4. Rewire remaining edges if needed.
5. Regenerate `workflow.variables.nodes`.
6. Run the validation checklist.

### Add an Edge

1. Check both nodes' port tables in `references/nodes/`.
2. Generate the edge ID: `{sourceId}-{sourcePort}-{targetId}-{targetPort}`.
3. Add the edge to `workflow.edges` with all four port fields.
4. Run the validation checklist.

### Add a Variable

1. Add the variable to `workflow.variables.globals` with `id`, `direction`, `type`, and optionally `defaultValue`.
2. If `direction` is `"in"`, set `triggerNodeId` to the trigger node's ID.
3. If `direction` is `"out"` or `"inout"`, add output mappings on every reachable End node.
4. See [variables-guide.md](references/variables-guide.md) for the full type system and expression syntax.

## Quick Start: New Flow

1. **Scaffold the project** — read [project-scaffolding-guide.md](references/project-scaffolding-guide.md) and create the 2-file project structure.
2. **Pick a template** — choose the closest template from `assets/templates/`:

   | Pattern | Template |
   |---|---|
   | Minimal (trigger + script) | `minimal-flow-template.json` |
   | With input variables | `project-scaffold-template.json` |
   | Decision/branching | `decision-flow-template.json` |
   | Loop iteration | `loop-flow-template.json` |
   | HTTP request | `http-flow-template.json` |
   | Scheduled trigger | `scheduled-trigger-template.json` |
   | Script + connector | `connector-flow-template.json` |
   | Multi-agent with transforms | `multi-agent-template.json` |

3. **Copy the template** as `<ProjectName>.flow` and update `name`, `id` (new UUID), and `metadata` timestamps.
4. **Plan your nodes** — identify which OOTB node types you need. Read the reference doc for each in `references/nodes/`.
5. **Add nodes** — for each new node, copy the definition block into `definitions` (if not already present) and add the node instance to `nodes`.
6. **Wire edges** — connect nodes using the port IDs from each node's reference doc.
7. **Add variables** — declare inputs/outputs in `variables.globals`. Map outputs on End nodes.
8. **Regenerate `variables.nodes`** — rebuild from scratch per the scaffolding guide.
9. **Validate** — walk through [validation-checklist.md](references/validation-checklist.md).
10. **(Optional) CLI validation** — if `uip` is available, run `uip flow validate <FILE_PATH> --output json` as a final check.

## Anti-Patterns

- **Never guess a definition block** — always copy from the node reference doc (OOTB) or registry output (dynamic). Guessed definitions have wrong port schemas and cause validation failures.
- **Never skip the validation checklist** — common errors (missing `targetPort`, duplicate IDs, orphaned edges) are easy to miss in raw JSON.
- **Never construct dynamic resource nodes without the registry** — RPA workflow, agent, and API workflow nodes need registry data for `inputDefinition` and `outputDefinition`.
- **Never use `console.log` in script nodes** — `console` is not available in the Jint runtime. Use `return { debug: value }` to inspect values.
- **Never reference parent-scope `$vars` inside a subflow** — subflows have isolated scope. Pass values explicitly via subflow inputs.
- **Never use `output` as the source port for script nodes** — the correct port ID is `success`. The `output` handle is for trigger nodes.

## Reference Navigation

| I need to... | Read this |
|---|---|
| Understand the `.flow` JSON format | [references/flow-schema-guide.md](references/flow-schema-guide.md) |
| Create a new project from scratch | [references/project-scaffolding-guide.md](references/project-scaffolding-guide.md) |
| Wire nodes together | [references/edge-wiring-guide.md](references/edge-wiring-guide.md) |
| Add variables and expressions | [references/variables-guide.md](references/variables-guide.md) |
| Create a subflow | [references/subflow-guide.md](references/subflow-guide.md) |
| Use RPA workflow, agent, or API workflow nodes | [references/dynamic-nodes/](references/dynamic-nodes/) |
| Understand `bindings_v2.json` | [references/bindings-guide.md](references/bindings-guide.md) |
| Validate my flow | [references/validation-checklist.md](references/validation-checklist.md) |
| Look up a specific node type | [references/nodes/](references/nodes/) — one file per OOTB node |

## OOTB Node Types

| Category | Node | Type | Reference |
|---|---|---|---|
| Trigger | Manual trigger | `core.trigger.manual` | [trigger-manual.md](references/nodes/trigger-manual.md) |
| Trigger | Scheduled trigger | `core.trigger.scheduled` | [trigger-scheduled.md](references/nodes/trigger-scheduled.md) |
| Data | Script | `core.action.script` | [action-script.md](references/nodes/action-script.md) |
| Data | HTTP Request | `core.action.http` | [action-http.md](references/nodes/action-http.md) |
| Data | Transform | `core.action.transform` | [action-transform.md](references/nodes/action-transform.md) |
| Data | Filter | `core.action.transform.filter` | [action-transform-filter.md](references/nodes/action-transform-filter.md) |
| Logic | Decision (if/else) | `core.logic.decision` | [logic-decision.md](references/nodes/logic-decision.md) |
| Logic | Switch (multi-branch) | `core.logic.switch` | [logic-switch.md](references/nodes/logic-switch.md) |
| Logic | Loop (collection) | `core.logic.loop` | [logic-loop.md](references/nodes/logic-loop.md) |
| Logic | For Each | `core.logic.foreach` | [logic-foreach.md](references/nodes/logic-foreach.md) |
| Logic | While | `core.logic.while` | [logic-while.md](references/nodes/logic-while.md) |
| Logic | Merge (parallel join) | `core.logic.merge` | [logic-merge.md](references/nodes/logic-merge.md) |
| Logic | Delay | `core.logic.delay` | [logic-delay.md](references/nodes/logic-delay.md) |
| Logic | Mock (placeholder) | `core.logic.mock` | [logic-mock.md](references/nodes/logic-mock.md) |
| Control | Terminate (stop all) | `core.logic.terminate` | [control-terminate.md](references/nodes/control-terminate.md) |
| Control | End (stop branch) | `core.control.end` | [control-end.md](references/nodes/control-end.md) |
| Human | Human-in-the-Loop | `uipath.human-in-the-loop` | [hitl.md](references/nodes/hitl.md) |
| Mock | Blank (pass-through) | `core.mock.blank` | [mock-blank.md](references/nodes/mock-blank.md) |
| Mock | Mock (with error) | `core.mock.node` | [mock-node.md](references/nodes/mock-node.md) |

## Completion Output

When you finish building or editing a flow, report:

1. Project directory path and file list
2. Node count and edge count
3. Node types used
4. Variables declared (with directions)
5. Whether validation checklist passed
6. Any warnings or items that need manual review
