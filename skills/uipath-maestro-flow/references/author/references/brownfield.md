# Brownfield — Edit an Existing Flow

Recipe-driven journey for targeted changes to an existing `.flow` file. Author terminates at `validate` + `tidy`. To publish, run, or debug after edits, see [operate/CAPABILITY.md](../../operate/CAPABILITY.md).

> **Greenfield (creating a new flow) uses a different journey.** If the `.flow` file does not yet exist, see [greenfield.md](greenfield.md) instead.

## Read this first

**[editing-operations.md](editing-operations.md)** — Direct JSON is the default for all edits. CLI is used only for connector, connector-trigger, and inline-agent nodes (carve-outs), or when you explicitly request it. Read the strategy selection matrix before any modification.

## Common edits

For each edit, run `uip maestro flow validate` once after **all** edits are complete, then `uip maestro flow tidy`. Do not validate after each individual change — intermediate states are expected to be invalid.

| Edit | Description | Guide |
|------|-------------|-------|
| **Change a script body or node inputs** | Edit the node's `inputs` in-place in the `.flow` JSON. Do not delete + re-add — that changes the node ID and breaks `$vars` expressions. Script nodes must return an object (`return { key: value }`). | [JSON: Update node inputs](editing-operations-json.md#update-node-inputs) |
| **Add a node between two existing nodes** | Remove the connecting edge, add the new node, wire upstream → new → downstream. | [JSON: Insert a node](editing-operations-json.md#insert-a-node-between-two-existing-nodes) (default) or [CLI: Insert a node](editing-operations-cli.md#insert-a-node-between-two-existing-nodes) (opt-in) |
| **Add a branch (decision node)** | Remove an edge, add a decision node, wire true/false branches. | [JSON: Insert a decision branch](editing-operations-json.md#insert-a-decision-branch) (default) or [CLI: Insert a decision branch](editing-operations-cli.md#insert-a-decision-branch) (opt-in) |
| **Remove a node** | Delete the node, sweep edges/definitions/variables, reconnect upstream to downstream. | [JSON: Remove a node](editing-operations-json.md#remove-a-node-and-reconnect) (default) or [CLI: Remove a node](editing-operations-cli.md#remove-a-node-and-reconnect) (opt-in, auto-cascades) |
| **Remove an edge** | Find the edge ID, delete it. | [JSON: Delete an edge](editing-operations-json.md#delete-an-edge) (default) or [CLI: Delete an edge](editing-operations-cli.md#delete-an-edge) (opt-in) |
| **Add a workflow variable** | Edit `variables.globals` in the `.flow` file (JSON only). For `out` variables, map on every End node. See [shared/variables-and-expressions.md](../../shared/variables-and-expressions.md). | [JSON: Add a workflow variable](editing-operations-json.md#add-a-workflow-variable) |
| **Update a state variable** | Add a `variableUpdates` entry for `inout` variables (JSON only). See [shared/variables-and-expressions.md](../../shared/variables-and-expressions.md). | [JSON: Add a variable update](editing-operations-json.md#add-a-variable-update) |
| **Create a subflow** | Add a `core.subflow` parent node + `subflows.{nodeId}` with nested nodes/edges/variables (JSON only). | [JSON: Create a subflow](editing-operations-json.md#create-a-subflow) + [subflow/impl.md](plugins/subflow/impl.md) |
| **Add a scheduled trigger** | Replace `core.trigger.manual` with `core.trigger.scheduled`. | [JSON: Replace trigger](editing-operations-json.md#replace-manual-trigger-with-scheduled-trigger) (default) or [CLI: Replace trigger](editing-operations-cli.md#replace-manual-trigger-with-scheduled-trigger) (opt-in) + [scheduled-trigger/impl.md](plugins/scheduled-trigger/impl.md) |
| **Add a connector trigger** | Delete manual trigger, add connector trigger, configure with connection. | [CLI: Replace trigger](editing-operations-cli.md#replace-manual-trigger-with-connector-trigger) + [connector-trigger/impl.md](plugins/connector-trigger/impl.md) |
| **Add a resource node** | Discover via registry (`--local` for in-solution, or tenant registry for published), add via JSON (default) or CLI (opt-in), wire edges. | Relevant plugin's `impl.md` + [editing-operations-json.md](editing-operations-json.md) (default) or [editing-operations-cli.md](editing-operations-cli.md) (opt-in) |
| **Add an inline agent node** | Embed a `uipath.agent.autonomous` node with an inline agent definition living inside the flow project. | [inline-agent/planning.md](plugins/inline-agent/planning.md) for selection vs a published agent, [inline-agent/impl.md](plugins/inline-agent/impl.md) for scaffolding, CLI, JSON structure, and validation. |
| **Add a HITL QuickForm node** | Insert a human approval/review/enrichment checkpoint. Wire the `completed` port after adding. | [JSON: Add a node](editing-operations-json.md) (default) or [CLI: `uip maestro flow hitl add`](../../shared/cli-commands.md#uip-maestro-flow-hitl-add) (opt-in) + [hitl/impl.md](plugins/hitl/impl.md) |

## After edits

1. **Validate** — `uip maestro flow validate <ProjectName>.flow --output json`. Fix any errors and re-validate.
2. **Tidy** — `uip maestro flow tidy <ProjectName>.flow --output json`. Required before publish or debug (see "Always run `flow tidy` after edits" in [the Author capability index](../CAPABILITY.md)) — without tidy, hand-edited or stale `layout` data renders as misshapen rectangles in Studio Web.

## Completion Output

When you finish editing the flow, report to the user:

1. **File path** of the `.flow` file edited
2. **What changed** — summary of nodes/edges added, removed, or modified
3. **Validation status** — whether `flow validate` passes (or remaining errors if unresolvable)
4. **Tidy status** — confirm `flow tidy` was run
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
