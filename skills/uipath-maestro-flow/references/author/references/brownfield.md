# Brownfield — Edit an Existing Flow

Recipe-driven journey for targeted changes to an existing `.flow` file. Author terminates at `validate` + `tidy`. To publish, run, or debug after edits, see [operate/CAPABILITY.md](../../operate/CAPABILITY.md).

> **Greenfield (creating a new flow) uses a different journey.** If the `.flow` file does not yet exist, see [greenfield.md](greenfield.md) instead.

## Suggested initial todos

Pre-populate these via `TodoWrite` when entering this journey. The list is edit-shaped — adapt to the user's actual change (single edit → drop discovery rows; multi-node refactor → add per-node rows). See [shared/ux-narration-and-todos.md](../../shared/ux-narration-and-todos.md) for granularity, narration cadence, and pivot rules.

- [ ] Locate `.flow` file and read current structure
- [ ] Confirm what the user wants changed
- [ ] Discover any new node types via registry (if adding nodes)
- [ ] Apply edit(s) with `Edit` / `Write` per [editing-operations.md](editing-operations.md) (Flow CLI only for connector activity, connector-trigger, and managed HTTP carve-outs)
- [ ] Re-wire edges affected by the change
- [ ] Update variables / output mappings if scope changed
- [ ] Run `flow validate` and fix any errors
- [ ] Run `flow format` to normalize layout
- [ ] Report file path + change summary + remaining mocks/missing connections
- [ ] Ask "what's next" (publish / debug / deploy)

## Read this first

**[editing-operations.md](editing-operations.md)** — `Edit` / `Write` is required for non-carve-out `.flow` edits — the `Edit` tool for in-place changes, `Write` only when ≥70% of nodes change. Flow CLI is used only for connector activity, connector-trigger, and managed HTTP carve-outs. Read the strategy selection matrix before any modification.

> **Self-check before each mutation:** name the tool you're about to use. If the answer isn't `Edit`, `Write`, or `uip flow ...` — STOP and ask the user via `AskUserQuestion` (per the dropdown rule in [SKILL.md](../../../SKILL.md)). `python`, `node`, `jq`, `sed`, `awk`, and shell heredocs are a last resort and require explicit user approval after you've surfaced the trade-offs. See [editing-operations.md — Tool Selection Ladder](editing-operations.md#tool-selection-ladder).

## Common edits

For each edit, run `uip flow validate` once after **all** edits are complete, then `uip flow format`. Do not validate after each individual change — intermediate states are expected to be invalid.

| Edit | Description | Guide |
|------|-------------|-------|
| **Change a script body or node inputs** | Use `Edit` to modify the node's `inputs` in-place. Do not delete + re-add — that changes the node ID and breaks `$vars` expressions. Script nodes must return an object (`return { key: value }`). | [Edit/Write: Update node inputs](editing-operations-json.md#update-node-inputs) |
| **Add a node between two existing nodes** | Remove the connecting edge, add the new node, wire upstream → new → downstream. | [Edit/Write: Insert a node](editing-operations-json.md#insert-a-node-between-two-existing-nodes) |
| **Add a branch (decision node)** | Remove an edge, add a decision node, wire true/false branches. | [Edit/Write: Insert a decision branch](editing-operations-json.md#insert-a-decision-branch) |
| **Remove a node** | Delete the node, sweep edges/definitions/variables, reconnect upstream to downstream. | [Edit/Write: Remove a node](editing-operations-json.md#remove-a-node-and-reconnect) |
| **Remove an edge** | Find the edge ID, delete it. | [Edit/Write: Delete an edge](editing-operations-json.md#delete-an-edge) |
| **Add a workflow variable** | Use `Edit` to modify `variables.globals` in the `.flow` file (Edit-only). For `out` variables, map on every End node. See [shared/variables-and-expressions.md](../../shared/variables-and-expressions.md). | [Edit/Write: Add a workflow variable](editing-operations-json.md#add-a-workflow-variable) |
| **Update a state variable** | Use `Edit` to add a `variableUpdates` entry for `inout` variables (Edit-only). See [shared/variables-and-expressions.md](../../shared/variables-and-expressions.md). | [Edit/Write: Add a variable update](editing-operations-json.md#add-a-variable-update) |
| **Create a subflow** | Add a `core.subflow` parent node + `subflows.{nodeId}` with nested nodes/edges/variables (`Edit`-only, or `Write` if scaffolding from template). | [Edit/Write: Create a subflow](editing-operations-json.md#create-a-subflow) + [subflow/impl.md](plugins/subflow/impl.md) |
| **Add a scheduled trigger** | Replace `core.trigger.manual` with `core.trigger.scheduled`. | [Edit/Write: Replace trigger](editing-operations-json.md#replace-manual-trigger-with-scheduled-trigger) + [scheduled-trigger/impl.md](plugins/scheduled-trigger/impl.md) |
| **Add a connector trigger** | Delete manual trigger, add connector trigger, configure with connection. | [CLI: Replace trigger](editing-operations-cli.md#replace-manual-trigger-with-connector-trigger) + [connector-trigger/impl.md](plugins/connector-trigger/impl.md) |
| **Add a resource node** | Discover via registry (`--local` for in-solution, or tenant registry for published), add via `Edit`, wire edges. | Relevant plugin's `impl.md` + [editing-operations-json.md](editing-operations-json.md) |
| **Add an inline agent node** | Embed a `uipath.agent.autonomous` node with an inline agent definition living inside the flow project. | [inline-agent/planning.md](plugins/inline-agent/planning.md) for selection vs a published agent, [inline-agent/impl.md](plugins/inline-agent/impl.md) for scaffolding, direct `.flow` JSON structure, and validation. |
| **Add a HITL QuickForm node** | Insert a human approval/review/enrichment checkpoint. Wire the `completed` port after adding. | [Edit/Write: Add a node](editing-operations-json.md) + [hitl/impl.md](plugins/hitl/impl.md) |

The table intentionally routes OOTB structural CRUD to Edit/Write only. There is no CLI opt-in path for non-carve-out flow graph edits.

## After edits

1. **Validate** — `uip flow validate <ProjectName>.flow --output json`. Fix any errors and re-validate.
2. **Tidy** — `uip flow format <ProjectName>.flow --output json`. Required before publish or debug (see "Always run `flow format` after edits" in [the Author capability index](../CAPABILITY.md)) — without tidy, hand-edited or stale `layout` data renders as misshapen rectangles in Studio Web.

## Completion Output

When you finish editing the flow, report to the user:

1. **File path** of the `.flow` file edited
2. **What changed** — summary of nodes/edges added, removed, or modified
3. **Validation status** — whether `flow validate` passes (or remaining errors if unresolvable)
4. **Tidy status** — confirm `flow format` was run
5. **Mock placeholders** — list any `core.logic.mock` nodes that need to be replaced
6. **Missing connections** — any connector nodes that need connections the user must create
7. **What's next** — use `AskUserQuestion` to present the dropdown below (see the AskUserQuestion dropdown rule in [SKILL.md](../../../SKILL.md))

### What's next dropdown

Authoring terminates here. Each option below hands off to Operate — read [operate/CAPABILITY.md](../../operate/CAPABILITY.md) for the command sequence.

| Option | What it does |
| --- | --- |
| **Publish to Studio Web** (default) | Push the solution to Studio Web so the user can visualize, edit, and publish from the browser. |
| **Debug the solution** | Execute the flow end-to-end against real systems. Confirm consent first — debug has real side effects (see the consent-before-debug rule in [SKILL.md](../../../SKILL.md)). |
| **Deploy to Orchestrator** | Pack and publish directly to Orchestrator (bypasses Studio Web). Only when explicitly chosen — see [/uipath:uipath-platform](/uipath:uipath-platform). |
| **Something else** | Last option. Accept free-form string input and act on it. |

Do not run any of these actions without explicit user selection. Once the user picks an option, read [operate/CAPABILITY.md](../../operate/CAPABILITY.md) and follow that capability's flow — do not run operate commands from inside this doc.
