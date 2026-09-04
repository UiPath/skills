# Brownfield — Edit an Existing Flow

Recipe-driven journey for targeted changes to an existing `.flow` file. Authoring ends at `validate` + `format`. For publishing, running, or debugging, see [operate/CAPABILITY.md](../operate/CAPABILITY.md).

> **Greenfield (creating a new flow) uses a different journey.** If the `.flow` file does not exist, see [greenfield.md](greenfield.md).

## Converting an existing project to Maestro

There is no automatic project-to-flow conversion. Re-host only orchestration:

1. Keep coded/RPA components and agents as resource nodes; do not rewrite them into Maestro. Use `uipath.core.rpa-workflow.*` and `uipath.core.agent.*`; see the relevant plugin's `planning.md`.
2. Lift ordering, waits, and branches into explicit trigger → steps → decisions → end topology.
3. Make sleeps, polling, and "check again later" first-class Maestro wait, delay, HITL, or `create-and-wait` nodes.
4. Publish executors or keep them in-solution, then resolve them with `registry list --local` for in-solution projects.

The result should be a thin flow delegating work to existing artifacts. Author it as greenfield ([greenfield.md](greenfield.md)), discovering artifacts during [planning-arch.md](planning-arch.md). Apply [Is Maestro the Right Home?](planning-arch.md#before-you-build-is-maestro-the-right-home): migrate for long waits, human approvals, parallel branches, or per-case visibility; do not migrate short, fully automated, fire-once scripts when orchestration overhead is not worthwhile.

## Read this first

Before each node added or modified, classify it as user-owned or CLI-owned (see [CAPABILITY.md — Node ownership](CAPABILITY.md#node-ownership--who-authors-the-node)). Connector activities, connector triggers, and `core.action.http.v2` are CLI-only: run `uip maestro flow node add` + `uip maestro flow node configure`, never Edit. Hand-writing these will fail `flow validate`; this also applies when adding a connector node to an existing flow.

Read [editing-operations.md](editing-operations.md) and the strategy selection matrix before modifying. Use `Edit` for in-place user-owned changes; use `Write` only when ≥70% of nodes change. For CLI-owned nodes, follow the plugin's `impl.md` configuration workflow (`node add` + `node configure`).

**Self-check before every mutation:** name the tool. If it is not `Edit`, `Write`, or `uip maestro flow ...`, STOP and ask the user under the dropdown question rule in [SKILL.md](../../SKILL.md). Treat `python`, `node`, `jq`, `sed`, `awk`, and shell heredocs as last resorts requiring explicit user approval after surfacing trade-offs. See [editing-operations.md — Tool Selection Ladder](editing-operations.md#tool-selection-ladder).

## Common edits

Make all edits first. Then run `uip maestro flow validate` once, followed by `uip maestro flow format`; do not validate intermediate invalid states.

For edits touching multiple top-level arrays, follow [parallel same-file Edit rules](editing-operations.md#parallel-same-file-edits): anchor each Edit on its array's opening key, never on top-level key order.

| Edit | Required operation and guide |
|---|---|
| **Change a script body or node inputs** | Use `Edit` on `inputs`; do not delete/re-add because node IDs and `$vars` expressions must remain stable. Script nodes must return an object (`return { key: value }`). See [Edit/Write: Update node inputs](editing-operations-json.md#update-node-inputs). |
| **Add a node between two existing nodes** | Remove the connecting edge; add the node; wire upstream → new → downstream. See [Edit/Write: Insert a node](editing-operations-json.md#insert-a-node-between-two-existing-nodes). |
| **Add a branch (decision node)** | Remove an edge; add the decision; wire true/false branches. See [Edit/Write: Insert a decision branch](editing-operations-json.md#insert-a-decision-branch). |
| **Remove a node** | Remove the node; sweep edges/definitions/variables; reconnect upstream to downstream. See [Edit/Write: Remove a node](editing-operations-json.md#remove-a-node-and-reconnect). |
| **Remove an edge** | Find and remove its edge ID. See [Edit/Write: Delete an edge](editing-operations-json.md#delete-an-edge). |
| **Add a workflow variable** | Use `Edit` on `variables.globals` (Edit-only). For `out` variables, map every End node. See [shared/variables-and-expressions.md](../shared/variables-and-expressions.md) and [Edit/Write: Add a workflow variable](editing-operations-json.md#add-a-workflow-variable). |
| **Update a state variable** | Use `Edit` to add a `variableUpdates` entry for `inout` variables (Edit-only). See [shared/variables-and-expressions.md](../shared/variables-and-expressions.md) and [Edit/Write: Add a variable update](editing-operations-json.md#add-a-variable-update). |
| **Create a subflow** | Add a `core.subflow` parent and `subflows.{nodeId}` with nested nodes, edges, and variables (`Edit`-only, or `Write` for template scaffolding). See [Edit/Write: Create a subflow](editing-operations-json.md#create-a-subflow) and [subflow/impl.md](plugins/subflow/impl.md). |
| **Add a scheduled trigger** | Replace `core.trigger.manual` with `core.trigger.scheduled`. See [Edit/Write: Replace trigger](editing-operations-json.md#replace-manual-trigger-with-scheduled-trigger) and [scheduled-trigger/impl.md](plugins/scheduled-trigger/impl.md). |
| **Add a connector trigger** | Remove the manual trigger; add and configure the connector trigger with a connection. Use [CLI: Replace trigger](editing-operations-cli.md#replace-manual-trigger-with-connector-trigger) and [connector-trigger/impl.md](plugins/connector-trigger/impl.md). |
| **Add a resource node** | Discover through the registry (`--local` for in-solution, or tenant registry for published); add with `Edit`; wire edges. Use the relevant plugin's `impl.md` and [editing-operations-json.md](editing-operations-json.md). |
| **Add an inline agent node** | Embed `uipath.agent.autonomous` with an inline agent definition in the flow project. See [inline-agent/planning.md](plugins/inline-agent/planning.md) for inline versus published selection and [inline-agent/impl.md](plugins/inline-agent/impl.md) for scaffolding, JSON, and validation. |
| **Add voice nodes** | Turn a flow into a phone conversation: a `uipath.agent.voice` inline conversational agent wired to a live call, plus the trigger, create-call, and end-call nodes. Binding an inbound number happens at deploy time, not in the `.flow`. See [inline-voice-agent/planning.md](plugins/inline-voice-agent/planning.md) for the two topologies and trunk requirements, and [inline-voice-agent/impl.md](plugins/inline-voice-agent/impl.md) for node JSON, `callContext` wiring, and number binding. |
| **Add a HITL QuickForm node** | Insert the human approval/review/enrichment checkpoint and wire its `completed` port. See [Edit/Write: Add a node](editing-operations-json.md) and [hitl/impl.md](plugins/hitl/impl.md). |

OOTB structural CRUD uses Edit/Write only; there is no CLI opt-in path for other flow-graph edits.

## After edits

1. Run `uip maestro flow validate <ProjectName>.flow --output json`. Fix errors and re-validate.
2. Run `uip maestro flow format <ProjectName>.flow --output json`. Run it before publish or debug (see "Always run `flow format` after edits" in [the Author capability index](CAPABILITY.md)); without it, stale or hand-edited `layout` data renders as misshapen rectangles in Studio Web.

## "Refusing to serialize a vX workflow" — migrate first

If `flow format`, `flow debug`, or `flow pack` fails with `[inMemoryWorkflowToFileFormat] Refusing to serialize a vX workflow to the v<current> file format`, run:

```bash
uip maestro flow migrate <ProjectName>.flow --output json
```

`migrate` is lossless, walks the per-version migration chain (for example, `=js:` expression strings become rich expression objects), and bumps the file to the current version. Then run `flow format` and `flow validate`; both should pass. `flow validate` does not re-serialize and therefore does not check the version guard enforced by `format`/`debug`/`pack`. When this refusal appears, always migrate; do not assume the edit was wrong.

## Completion Output

When editing finishes, report:

1. **File path** of the edited `.flow` file
2. **What changed** — nodes/edges added, removed, or modified
3. **Validation status** — whether `flow validate` passes, or remaining unresolvable errors
4. **Format status** — confirm `flow format` was run
5. **Mock placeholders** — every `core.logic.mock` node needing replacement
6. **Missing connections** — connector nodes requiring connections the user must create
7. **What's next** — ask the user using the dropdown below (see the dropdown question rule in [SKILL.md](../../SKILL.md))

### What's next dropdown

Authoring ends here. For any selected option, read [operate/CAPABILITY.md](../operate/CAPABILITY.md) and follow that capability's flow; do not run operate commands from this document.

| Option | What it does |
|---|---|
| **Publish to Studio Web** | Push the solution to Studio Web so the user can visualize, edit, and publish from the browser. |
| **Debug the solution** | Execute the flow end-to-end against real systems. Consent comes from the mandate, not from this menu — see the `flow debug` rule in [SKILL.md](../../SKILL.md). Selecting it here is the user asking for a run. |
| **Deploy to Orchestrator** | Pack and publish directly to Orchestrator (bypasses Studio Web). Only when explicitly chosen; see [/uipath:uipath-platform](/uipath:uipath-platform). |
| **Something else** | Last option. Accept free-form string input and act on it. |

When the original request already named the next step ("publish it", "deploy to Orchestrator", "run debug and iterate"), that instruction **is** the selection — act on it and skip the menu. Show the menu only when the next step was left unspecified, and then do not run any option without explicit user selection.