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

## Adding via CLI

```bash
uip flow node add <ProjectName>.flow "uipath.core.agent.{key}" --output json \
  --label "Classify Intent" \
  --position 400,300
```

## JSON Structure

```json
{
  "id": "classifyIntent",
  "type": "uipath.core.agent.ffa33d88-8a85-4570-933c-9a69aa2dfbb5",
  "typeVersion": "1.0.0",
  "ui": { "position": { "x": 400, "y": 300 } },
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

## If the Agent Does Not Exist Yet

1. Add a `core.logic.mock` placeholder in the flow
2. Tell the user to create and publish the agent using `uipath-agents`
3. After publishing, refresh the registry and replace the mock:

```bash
uip flow registry pull --force
uip flow registry search "<agent-name>" --output json
```

See [rpa/impl.md](../rpa/impl.md) for the full mock replacement workflow.

## Debug

| Error | Cause | Fix |
| --- | --- | --- |
| Node type not found in registry | Agent not published, or registry stale | Run `uip login` then `uip flow registry pull --force` |
| Agent execution failed | Underlying agent errored | Check `$vars.{nodeId}.error` for details |
| Empty `output.content` | Agent returned no response | Verify agent is configured correctly in Orchestrator |
| `inputDefinition` is empty | Expected — agents typically accept input via flow wiring, not typed fields | Wire upstream data to the agent via `$vars` expressions |
