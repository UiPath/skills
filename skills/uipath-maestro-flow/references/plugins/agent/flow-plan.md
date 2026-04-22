# Agent Node

Agent nodes invoke UiPath AI agents from within a flow. Published agents appear in the registry after `uip login` + `uip maestro flow registry pull`. **In-solution** (unpublished) agents in sibling projects are discovered via `--local` — no login or publish required.

> **Published vs Inline:** This plugin covers the published/tenant-resource case. For agents defined inside the flow project itself (scaffolded via `uip agent init --inline-in-flow`), see [inline-agent/flow-plan.md](../inline-agent/flow-plan.md). Pick the published path when the agent is reused across flows or needs independent versioning; pick inline when the agent is tightly coupled to one flow.

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

- **Agent in the same solution but not yet published** — use `--local` discovery (see below)
- **Agent does not exist yet** — tell the user to create it in the same solution with `uipath-agents`, then use `--local` discovery
- **Task is deterministic** — use [Script](../script/planning.md) or [Decision](../decision/flow-plan.md)
- **Need to call an external service API** — use [Connector](../connector/flow-plan.md) or [HTTP](../http/flow-plan.md)

## Ports

| Input Port | Output Port(s) |
| --- | --- |
| `input` | `output`, `error` |

The `error` port is the implicit error port shared with all action nodes — see [Implicit error port on action nodes](../../flow-file-format.md#implicit-error-port-on-action-nodes).

## Output Variables

- `$vars.{nodeId}.output` — the agent's response (contains `content` string)
- `$vars.{nodeId}.error` — error details if the agent fails (`code`, `message`, `detail`, `category`, `status`)

## Discovery

**Published (tenant registry):**

```bash
uip maestro flow registry pull --force
uip maestro flow registry search "uipath.core.agent" --output json
```

Requires `uip login`. Only published agents from your tenant appear.

**In-solution (local, no login required):**

```bash
uip maestro flow registry list --local --output json
uip maestro flow registry get "<nodeType>" --local --output json
```

Run from inside the flow project directory. Discovers sibling agent projects in the same `.uipx` solution.

## Registry Validation

```bash
uip maestro flow registry get "uipath.core.agent.{key}" --output json
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

> `resourceKey` takes the form `<FolderPath>.<AgentName>` — confirm the exact value from `uip maestro flow registry get` output.

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

> **Why both are required.** The registry's `Data.Node.model.context[].value` fields ship as template placeholders (`<bindings.name>`, `<bindings.folderPath>`) — not runtime-resolvable expressions. The runtime reads the node instance's `model.context` and resolves `=bindings.<id>` against the top-level `bindings[]` array. Without these two pieces, `uip maestro flow validate` passes but `uip maestro flow debug` fails with "Folder does not exist or the user does not have access to the folder."

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

Tell the user to create the agent project inside the same solution using `uipath-agents`. Once the project exists as a sibling in the `.uipx` solution, discover it with `uip maestro flow registry list --local --output json` and wire it directly — no publish required.

## Debug

| Error | Cause | Fix |
| --- | --- | --- |
| Node type not found in registry | Agent not published, or registry stale | If in same solution: run `registry list --local`. Otherwise: run `uip login` then `uip maestro flow registry pull --force` |
| Agent execution failed | Underlying agent errored | Check `$vars.{nodeId}.error` for details |
| Empty `output.content` | Agent returned no response | Verify agent is configured correctly in Orchestrator |
| `inputDefinition` is empty | Expected — agents typically accept input via flow wiring, not typed fields | Wire upstream data to the agent via `$vars` expressions |
