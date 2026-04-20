# Agent Node — Implementation

Agent nodes invoke published UiPath AI agents. They are tenant-specific resources with pattern `uipath.core.agent.{key}`.

## Discovery

```bash
uip flow registry pull --force
uip flow registry search "uipath.core.agent" --output json
```

Requires `uip login`. Only published agents from your tenant appear.

## Registry Validation

```bash
uip flow registry get "uipath.core.agent.{key}" --output json
```

Confirm:

- Input port: `input`
- Output port: `output`
- `outputDefinition.output.schema` — contains `content` (string)
- `outputDefinition.error.schema` — contains `code`, `message`, `detail`, `category`, `status`
- `model.serviceType` — `Orchestrator.StartAgentJob`
- `inputDefinition` — typically empty (agents accept free-form input via the flow's wiring)

## Adding / Editing

For step-by-step add, delete, and wiring procedures, see [flow-editing-operations.md](../../flow-editing-operations.md). Use the JSON structure below for the node-specific `inputs` and `model` fields.

**This node type needs top-level `bindings[]` entries.** `uipath.core.agent.*` is a resource node — it invokes a published Orchestrator agent, and the runtime resolves the target via two process-style bindings in the flow's top-level `bindings[]` array (regenerated into `bindings_v2.json` at `flow debug`/`flow pack` time). The CLI's `flow node add` wires these automatically; when hand-writing JSON, follow the [Resource Node Bindings](../../flow-editing-operations-json.md#resource-node-bindings-direct-json) procedure. **For agent nodes:** `resourceSubType = "Agent"`, `orchestratorType = "agent"`.

## JSON Structure

A complete agent node requires three pieces in the `.flow` file:

1. The **node entry** in `nodes[]` (with `model.bindings` and `model.context[]`)
2. Two **top-level bindings** in `bindings[]` (one for `name`, one for `folderPath`)
3. The **definition** in `definitions[]` (copied verbatim from `uip flow registry get`)

### Node entry

```json
{
  "id": "classifyIntent",
  "type": "uipath.core.agent.ffa33d88-8a85-4570-933c-9a69aa2dfbb5",
  "typeVersion": "1.0.0",
  "display": { "label": "Classify Intent" },
  "inputs": {},
  "model": {
    "type": "bpmn:ServiceTask",
    "serviceType": "Orchestrator.StartAgentJob",
    "version": "v2",
    "section": "Published",
    "bindings": {
      "resource": "process",
      "resourceSubType": "Agent",
      "resourceKey": "Shared.Apple Genius Agent",
      "orchestratorType": "agent",
      "values": {
        "name": "Apple Genius Agent",
        "folderPath": "Shared"
      }
    },
    "context": [
      { "name": "name", "type": "string", "value": "=bindings.bKEFLMRB2", "default": "Apple Genius Agent" },
      { "name": "folderPath", "type": "string", "value": "=bindings.bwSwZQsvT", "default": "Shared" },
      { "name": "_label", "type": "string", "value": "Apple Genius Agent" }
    ]
  }
}
```

- `resourceKey`, `name`, `folderPath` come from `Data.Node.model.bindings` in `uip flow registry get` — copy verbatim, don't paraphrase the path.
- `context[]` values must use `=bindings.<id>` where `<id>` matches an entry in the flow's top-level `bindings[]` (next block).
- `inputs` takes whatever the agent expects — check `Data.Node.inputDefinition.properties` from `registry get`.
- The node instance does not need an `outputs` block; downstream `$vars.{nodeId}.output` resolves from `variables.nodes[]` + the definition's `outputDefinition`.

### Top-level `bindings[]` entries

Append these two entries to the flow's top-level `bindings[]` array (sibling of `nodes`, `edges`, `definitions`):

```json
{
  "id": "bKEFLMRB2",
  "name": "name",
  "type": "string",
  "resource": "process",
  "resourceKey": "Shared.Apple Genius Agent",
  "default": "Apple Genius Agent",
  "propertyAttribute": "name",
  "resourceSubType": "Agent"
},
{
  "id": "bwSwZQsvT",
  "name": "folderPath",
  "type": "string",
  "resource": "process",
  "resourceKey": "Shared.Apple Genius Agent",
  "default": "Shared",
  "propertyAttribute": "folderPath",
  "resourceSubType": "Agent"
}
```

- The two `id`s must match the `=bindings.<id>` references inside the node's `model.context[]`.
- `resourceKey` must equal the `resourceKey` in the node's `model.bindings`.
- If another agent node in the same flow targets the same published agent (same `resourceKey`), reuse these two binding entries — do not duplicate.

See [Resource Node Bindings](../../flow-editing-operations-json.md#resource-node-bindings-direct-json) for the general procedure shared across agent / rpa-workflow / api-workflow nodes.

## Accessing Output

The agent's response is available downstream:

```javascript
// In a Script node after the agent
const response = $vars.classifyIntent.output.content;
return { classification: response };
```

- `$vars.{nodeId}.output.content` — the agent's text response
- `$vars.{nodeId}.error` — error details if the agent fails

## If the Agent Does Not Exist Yet

Add a `core.logic.mock` placeholder and tell the user to create and publish the agent using `uipath-agents`. After publishing, follow the [mock replacement procedure](../../flow-editing-operations-cli.md#replace-a-mock-with-a-real-resource-node) to swap the mock for the real resource node.

## Debug

| Error | Cause | Fix |
| --- | --- | --- |
| Node type not found in registry | Agent not published, or registry stale | Run `uip login` then `uip flow registry pull --force` |
| Agent execution failed | Underlying agent errored | Check `$vars.{nodeId}.error` for details |
| Empty `output.content` | Agent returned no response | Verify agent is configured correctly in Orchestrator |
| `inputDefinition` is empty | Expected — agents typically accept input via flow wiring, not typed fields | Wire upstream data to the agent via `$vars` expressions |
