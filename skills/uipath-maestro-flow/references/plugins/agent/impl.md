# Agent Node — Implementation

Agent nodes invoke UiPath AI agents. Pattern: `uipath.core.agent.{key}`.

## Discovery

**Published (tenant registry):**
```bash
uip maestro flow registry pull --force
uip maestro flow registry search "uipath.core.agent" --output json
```

**In-solution (local, no login required):**
```bash
uip maestro flow registry list --local --output json
```
Run from inside the flow project directory. Discovers sibling agent projects in the same `.uipx` solution.

## Registry Validation

```bash
# Published resource:
uip maestro flow registry get "uipath.core.agent.{key}" --output json

# In-solution resource:
uip maestro flow registry get "uipath.core.agent.{key}" --local --output json
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

## JSON Structure

```json
{
  "id": "classifyIntent",
  "type": "uipath.core.agent.ffa33d88-8a85-4570-933c-9a69aa2dfbb5",
  "typeVersion": "1.0.0",
  "display": { "label": "Classify Intent" },
  "inputs": {},
  "outputs": {
    "output": {
      "type": "object",
      "description": "The return value of the agent",
      "source": "=result.response",
      "var": "output"
    },
    "error": {
      "type": "object",
      "description": "Error information if the agent fails",
      "source": "=result.Error",
      "var": "error"
    }
  },
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
    }
  }
}
```

## Accessing Output

The agent's response is available downstream:

```javascript
// In a Script node after the agent
const response = $vars.classifyIntent.output.content;
return { classification: response };
```

- `$vars.{nodeId}.output.content` — the agent's text response
- `$vars.{nodeId}.error` — error details if the agent fails

## In-Solution Reference (Preferred Over Mock)

If the agent exists as a sibling project in the same solution but is not yet published, use `--local` discovery instead of a mock placeholder. Run `uip maestro flow registry list --local --output json` from the flow project directory to discover it, then `registry get --local` to get the full node manifest.

## Mock Placeholder (If Not in Solution)

If the agent is not in the same solution and not yet published, add a `core.logic.mock` placeholder and tell the user to create and publish the agent using `uipath-agents`. After publishing, follow the [mock replacement procedure](../../flow-editing-operations-cli.md#replace-a-mock-with-a-real-resource-node) to swap the mock for the real resource node.

## Debug

| Error | Cause | Fix |
| --- | --- | --- |
| Node type not found in registry | Agent not published, or registry stale | If in same solution: run `registry list --local`. Otherwise: run `uip login` then `uip maestro flow registry pull --force` |
| Agent execution failed | Underlying agent errored | Check `$vars.{nodeId}.error` for details |
| Empty `output.content` | Agent returned no response | Verify agent is configured correctly in Orchestrator |
| `inputDefinition` is empty | Expected — agents typically accept input via flow wiring, not typed fields | Wire upstream data to the agent via `$vars` expressions |
