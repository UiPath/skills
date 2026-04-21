# Agent Node

Agent nodes invoke **published** UiPath AI agents from within a flow. They are tenant-specific resources that appear in the registry after `uip login` + `uip flow registry pull`.

> **Published vs Inline:** This plugin covers the published/tenant-resource case. For agents defined inside the flow project itself (scaffolded via `uip agent init --inline-in-flow`), see [inline-agent/planning.md](../inline-agent/planning.md). Pick the published path when the agent is reused across flows or needs independent versioning; pick inline when the agent is tightly coupled to one flow.

## Node Type Pattern

`uipath.core.agent.{key}`

The `{key}` is the agent's unique identifier (typically a GUID) from Orchestrator.

## When to Use

Use an Agent node when the flow needs to invoke a published AI agent for reasoning, judgment, or natural language processing.

### Agent vs Script/Decision Decision Table

| Use an Agent node when... | Use Script/Decision/Switch when... |
| --- | --- |
| Input is ambiguous or unstructured (free text, emails, support tickets) | Input is structured and well-defined (JSON, form data) |
| Task requires reasoning or judgment (triage, classification, summarization) | Task is deterministic (if X then Y, map/filter/transform) |
| Branching depends on context that can't be reduced to simple conditions | Branching conditions are explicit and enumerable |
| You need natural language generation (draft emails, summaries) | You need data transformation or computation |

### Anti-Pattern

Don't use an agent node for tasks that can be done with a Decision + Script. Agents are slower, more expensive (LLM tokens), and less predictable. Use them where their flexibility is actually needed.

### Hybrid Pattern

Use workflow nodes for the deterministic parts (fetch data, transform, route) and agent nodes for the ambiguous parts (classify intent, draft response, extract entities). The flow orchestrates; the agent reasons.

### When NOT to Use

- **Agent not yet published** — use `core.logic.mock` placeholder and tell the user to create the agent with `uipath-agents`
- **Task is deterministic** — use [Script](../script/planning.md) or [Decision](../decision/planning.md)
- **Need to call an external service API** — use [Connector](../connector/planning.md) or [HTTP](../http/planning.md)

## Ports

| Input Port | Output Port(s) |
| --- | --- |
| `input` | `output` |

## Output Variables

- `$vars.{nodeId}.output` — the agent's response (contains `content` string)
- `$vars.{nodeId}.error` — error details if the agent fails (`code`, `message`, `detail`, `category`, `status`)

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

## JSON Structure

### Node instance (inside `nodes[]`)

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
    },
    "context": [
      { "name": "name",       "type": "string", "value": "=bindings.bClassifyIntentName",       "default": "Apple Genius Agent" },
      { "name": "folderPath", "type": "string", "value": "=bindings.bClassifyIntentFolderPath", "default": "Shared" },
      { "name": "_label",     "type": "string", "value": "Apple Genius Agent" }
    ]
  }
}
```

> `resourceKey` takes the form `<FolderPath>.<AgentName>` — confirm the exact value from `uip flow registry get` output.

### Top-level `bindings[]` entries (sibling of `nodes`/`edges`/`definitions`)

Add one entry per `(resourceKey, propertyAttribute)` pair. Share entries across node instances that reference the same agent — do NOT create duplicates.

```json
"bindings": [
  {
    "id": "bClassifyIntentName",
    "name": "name",
    "type": "string",
    "resource": "process",
    "resourceKey": "Shared.Apple Genius Agent",
    "default": "Apple Genius Agent",
    "propertyAttribute": "name",
    "resourceSubType": "Agent"
  },
  {
    "id": "bClassifyIntentFolderPath",
    "name": "folderPath",
    "type": "string",
    "resource": "process",
    "resourceKey": "Shared.Apple Genius Agent",
    "default": "Shared",
    "propertyAttribute": "folderPath",
    "resourceSubType": "Agent"
  }
]
```

> **Why both are required.** The registry's `Data.Node.model.context[].value` fields ship as template placeholders (`<bindings.name>`, `<bindings.folderPath>`) — not runtime-resolvable expressions. The runtime reads the node instance's `model.context` and resolves `=bindings.<id>` against the top-level `bindings[]` array. Without these two pieces, `uip flow validate` passes but `uip flow debug` fails with "Folder does not exist or the user does not have access to the folder."

> **Definition stays verbatim.** Do NOT rewrite `<bindings.*>` placeholders inside the `definitions` entry — it is a schema copy, not a runtime input. Critical Rule #7 applies unchanged.

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
