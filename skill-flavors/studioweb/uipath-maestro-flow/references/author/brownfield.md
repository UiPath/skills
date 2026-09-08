<!--skill-flavor:brownfield-convert-resolve-executors:start-->
4. Publish executors or keep them in-solution, then find the in-solution ones with `uip solution resources list --kind Process --output json` (`solutionResources`).
<!--skill-flavor:brownfield-convert-resolve-executors:end-->

<!--skill-flavor:brownfield-common-edits-table:start-->
| Edit | Required operation and guide |
|---|---|
| **Change a script body or node inputs** | Use `Edit` on `inputs`; do not delete/re-add because node IDs and `$vars` expressions must remain stable. Script nodes must return an object (`return { key: value }`). See [Edit/Write: Update node inputs](editing-operations-json.md#update-node-inputs). |
| **Add a node between two existing nodes** | Remove the connecting edge; add the node; wire upstream → new → downstream. See [Edit/Write: Insert a node](editing-operations-json.md#insert-a-node-between-two-existing-nodes). |
| **Move / reorder a node** | Re-wire the edges, then re-point every `$vars.<node>` read inside the moved node (a Decision's `expression`, a script body, input fields) to a node that still runs **before** it; a reference to a node that now runs later evaluates against nothing at runtime (`[400302]`/`[400300]`) even though `flow validate` passes. Nodes the branches rejoin at read the Decision as `$vars.<decisionId>.matchedCaseId` (see [decision/impl.md — Outputs](plugins/decision/impl.md#outputs)). See [Edit/Write: Delete an edge](editing-operations-json.md#delete-an-edge) and [Edit/Write: Update node inputs](editing-operations-json.md#update-node-inputs). |
| **Add a branch (decision node)** | Remove an edge; add the decision; wire true/false branches. See [Edit/Write: Insert a decision branch](editing-operations-json.md#insert-a-decision-branch). |
| **Remove a node** | Remove the node; sweep edges/definitions/variables; reconnect upstream to downstream. See [Edit/Write: Remove a node](editing-operations-json.md#remove-a-node-and-reconnect). |
| **Remove an edge** | Find and remove its edge ID. See [Edit/Write: Delete an edge](editing-operations-json.md#delete-an-edge). |
| **Add a workflow variable** | Use `Edit` on `variables.globals` (Edit-only). For `out` variables, map every End node. See [shared/variables-and-expressions.md](../shared/variables-and-expressions.md) and [Edit/Write: Add a workflow variable](editing-operations-json.md#add-a-workflow-variable). |
| **Update a state variable** | Use `Edit` to add a `variableUpdates` entry for `inout` variables (Edit-only). See [shared/variables-and-expressions.md](../shared/variables-and-expressions.md) and [Edit/Write: Add a variable update](editing-operations-json.md#add-a-variable-update). |
| **Create a subflow** | Add a `core.subflow` parent and `subflows.{nodeId}` with nested nodes, edges, and variables (`Edit`-only, or `Write` for template scaffolding). See [Edit/Write: Create a subflow](editing-operations-json.md#create-a-subflow) and [subflow/impl.md](plugins/subflow/impl.md). |
| **Add a scheduled trigger** | Replace `core.trigger.manual` with `core.trigger.scheduled`. See [Edit/Write: Replace trigger](editing-operations-json.md#replace-manual-trigger-with-scheduled-trigger) and [scheduled-trigger/impl.md](plugins/scheduled-trigger/impl.md). |
| **Add a connector trigger** | Remove the manual trigger; add and configure the connector trigger with a connection. Use [CLI: Replace trigger](editing-operations-cli.md#replace-manual-trigger-with-connector-trigger) and [connector-trigger/impl.md](plugins/connector-trigger/impl.md). |
| **Add a resource node** | Discover in-solution projects with `uip solution resources list --kind Process --output json` (`solutionResources`), or the tenant registry for published resources; add with `Edit`; wire edges. Use the relevant plugin's `impl.md` and [editing-operations-json.md](editing-operations-json.md). |
| **Add an inline agent node** | Embed `uipath.agent.autonomous` with an inline agent definition in the flow project. See [inline-agent/planning.md](plugins/inline-agent/planning.md) for inline versus published selection and [inline-agent/impl.md](plugins/inline-agent/impl.md) for scaffolding, JSON, and validation. |
| **Add voice nodes** | Turn a flow into a phone conversation: a `uipath.agent.voice` inline conversational agent wired to a live call, plus the trigger, create-call, and end-call nodes. Binding an inbound number happens at deploy time, not in the `.flow`. See [inline-voice-agent/planning.md](plugins/inline-voice-agent/planning.md) for the two topologies and trunk requirements, and [inline-voice-agent/impl.md](plugins/inline-voice-agent/impl.md) for node JSON, `callContext` wiring, and number binding. |
| **Add a HITL QuickForm node** | Insert the human approval/review/enrichment checkpoint and wire its `completed` port. See [Edit/Write: Add a node](editing-operations-json.md) and [hitl/impl.md](plugins/hitl/impl.md). |
<!--skill-flavor:brownfield-common-edits-table:end-->

<!--skill-flavor:brownfield-after-edits:start-->
1. Run `uip maestro flow validate new.flow --output json`. Fix errors and re-validate.
2. Run `uip maestro flow format new.flow --output json`. Run it before publish or debug (see "Always run `flow format` after edits" in [the Author capability index](CAPABILITY.md)); without it, stale or hand-edited `layout` data renders as misshapen rectangles in Studio Web.
<!--skill-flavor:brownfield-after-edits:end-->

<!--skill-flavor:brownfield-migrate-section:start-->
If `flow format` fails with `[inMemoryWorkflowToFileFormat] Refusing to serialize a vX workflow to the v<current> file format`, run:

```bash
uip maestro flow migrate new.flow --output json
```

`migrate` is lossless, walks the per-version migration chain (for example, `=js:` expression strings become rich expression objects), and bumps the file to the current version. Then run `flow format` and `flow validate`; both should pass. `flow validate` does not re-serialize and therefore does not check the version guard enforced by `format`. When this refusal appears, always migrate; do not assume the edit was wrong.
<!--skill-flavor:brownfield-migrate-section:end-->

<!--skill-flavor:brownfield-whats-next-dropdown:start-->
| Option | What it does |
|---|---|
| **Publish** | Publish the open solution with `uip solution publish --location "<key or name>"`. Read the destinations from `uip solution publish --help` (`PublishLocations`) and ask the user which one when more than one exists and none was named; with no `--location` the host publishes to the personal workspace immediately and without a second confirmation. |
| **Debug** | Run the saved project with `uip flow debug` (two-token verb). Consent comes from the mandate, not from this menu — see the `flow debug` rule in [SKILL.md](../../SKILL.md). Selecting it here is the user asking for a run. |
| **Something else** | Last option. Accept free-form string input and act on it. |
<!--skill-flavor:brownfield-whats-next-dropdown:end-->
