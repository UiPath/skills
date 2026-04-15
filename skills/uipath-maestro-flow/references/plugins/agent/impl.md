# Agent Node — Implementation

Agent nodes invoke UiPath AI agents via node type `uipath.core.agent.{key}`. Coded (Python) agents always use this plugin; low-code (`agent.json`) agents use it only when they are a standalone project (in-solution sibling or published). Inline low-code agents (embedded as a UUID subdirectory inside the flow project) use `uipath.agent.autonomous` — see the [inline-agent plugin](../inline-agent/impl.md).

The agent lives in one of two places:

- **In this solution** — sibling project inside the current solution. `{key}` is the local `resource.key` minted by `uip solution project add` (written to `resources/solution_folder/process/agent/<CodedAgentProject>.json`). `model.section: "In this solution"`. The runtime resolves the node via the Studio Web projects API after `uip solution upload`.
- **Published** — deployed to Orchestrator as a tenant resource. `{key}` is the Orchestrator-assigned resource key. Discoverable via `uip flow registry search`.

The node shape is identical across the two variants except for how `{key}` and `model.section` are populated.

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

Requires `uip login`. Only published agents from the tenant appear in the registry.

Confirm from `registry get`:

- Input port: `input`
- Output port: `output`
- `outputDefinition.output.schema` — contains `content` (string)
- `outputDefinition.error.schema` — contains `code`, `message`, `detail`, `category`, `status`
- `model.serviceType` — `Orchestrator.StartAgentJob`
- `inputDefinition` — typically empty (agents accept free-form input via flow wiring)

## Adding / Editing

For step-by-step add, delete, and wiring procedures, see [flow-editing-operations.md](../../flow-editing-operations.md). Use the JSON structure below for the node-specific `inputs` and `model` fields.

## JSON Structure

### Node instance (inside `nodes[]`) — published variant

```json
{
  "id": "classifyIntent",
  "type": "uipath.core.agent.898947e5-957a-4539-9ece-bef59d428d15",
  "typeVersion": "1.0.0",
  "display": { "label": "Classify Intent" },
  "inputs": {},
  "outputs": {
    "output": { "type": "object", "description": "The return value of the agent", "source": "=result.response", "var": "output" },
    "error":  { "type": "object", "description": "Error information if the agent fails", "source": "=result.Error", "var": "error" }
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
      "values": { "name": "Apple Genius Agent", "folderPath": "Shared" }
    },
    "context": [
      { "name": "name",       "type": "string", "value": "=bindings.bClassifyIntentName",       "default": "Apple Genius Agent" },
      { "name": "folderPath", "type": "string", "value": "=bindings.bClassifyIntentFolderPath", "default": "Shared" },
      { "name": "_label",     "type": "string", "value": "Apple Genius Agent" }
    ]
  }
}
```

Two different identifiers show up in this shape — don't confuse them:
- The node `type` suffix (`898947e5-…`) is the Orchestrator-assigned UUID returned by `uip flow registry search "uipath.core.agent"` / `registry get` as the `nodeType`.
- `model.bindings.resourceKey` (`Shared.Apple Genius Agent`) is the composite `<FolderPath>.<AgentName>` that Orchestrator uses to resolve the process at runtime.

Confirm both values from `uip flow registry get <nodeType> --output json` before wiring.

### Node instance (inside `nodes[]`) — in-solution variant

```json
{
  "id": "codedAgent",
  "type": "uipath.core.agent.<resourceKey>",
  "typeVersion": "1.0.0",
  "display": { "label": "<Label>", "icon": "coded-agent" },
  "inputs": {},
  "outputs": {
    "output": { "type": "object", "description": "The return value of the agent", "source": "=result.response", "var": "output" },
    "error":  { "type": "object", "description": "Error information if the agent fails", "source": "=result.Error", "var": "error" }
  },
  "model": {
    "type": "bpmn:ServiceTask",
    "serviceType": "Orchestrator.StartAgentJob",
    "version": "v2",
    "section": "In this solution",
    "bindings": {
      "resource": "process",
      "resourceSubType": "Agent",
      "resourceKey": "<resourceKey>",
      "orchestratorType": "agent",
      "values": { "name": "<agent-folder-name>", "folderPath": "" }
    },
    "projectId": "<resourceKey>",
    "projectName": "<agent-folder-name>",
    "context": [
      { "name": "name",       "type": "string", "value": "=bindings.<nameBindingId>",       "default": "<agent-folder-name>" },
      { "name": "folderPath", "type": "string", "value": "=bindings.<folderPathBindingId>", "default": "" },
      { "name": "_label",     "type": "string", "value": "<Label>" }
    ]
  }
}
```

In this variant, `resourceKey` and `model.projectId` are both the local `resource.key` written by `uip solution project add` to `resources/solution_folder/process/agent/<CodedAgentProject>.json` — read it from that file or from `uip maestro flow registry list --local`.

### Top-level `bindings[]` entries (sibling of `nodes`/`edges`/`definitions`)

Add one entry per `(resourceKey, propertyAttribute)` pair. Share entries across node instances that reference the same agent — no duplicates.

```json
"bindings": [
  {
    "id": "bClassifyIntentName",
    "name": "name",
    "type": "string",
    "resource": "process",
    "resourceKey": "<resourceKey>",
    "default": "<agent-name>",
    "propertyAttribute": "name",
    "resourceSubType": "Agent"
  },
  {
    "id": "bClassifyIntentFolderPath",
    "name": "folderPath",
    "type": "string",
    "resource": "process",
    "resourceKey": "<resourceKey>",
    "default": "<folder-path-or-empty>",
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

Create the agent first, then wire it. Three paths:

- **In-solution (sibling project, coded or low-code)** — scaffold via `uipath-agents`, register with `uip solution project add` to mint the local `resource.key`, then discover via `uip maestro flow registry list --local`. For the coded pipeline, see [coded/embedding-in-flows.md](../../../../uipath-agents/references/coded/embedding-in-flows.md).
- **Published coded agent** — `uip codedagent deploy`, then `uip maestro flow registry pull --force`.
- **Published low-code agent** — `uip solution deploy`, then `uip maestro flow registry pull --force`.

## Using an Agent as a Tool Resource

To use a published agent (coded or low-code) as a **tool for another agent** rather than a standalone flow node, add it as a `uipath.agent.resource.tool.agent` resource node wired to the parent agent's `tool` handle. This lives within the agent's canvas, not at the top level of the flow.

For the resource file format and wiring details, see the `uipath-agents` skill:
- Coded agents: [coded/flow-integration.md § Pattern 3](../../../../uipath-agents/references/coded/flow-integration.md#pattern-3-tool-resource-for-another-agent)
- Low-code agents: [lowcode/agent-flow-integration.md](../../../../uipath-agents/references/lowcode/agent-flow-integration.md)

## Debug

| Error | Cause | Fix |
| --- | --- | --- |
| Node type not found in registry | Agent not published, or registry stale | If in same solution: run `registry list --local`. Otherwise: run `uip login` then `uip maestro flow registry pull --force`. For coded agents, ensure `uip codedagent deploy` completed successfully |
| In-solution node doesn't resolve | `resourceKey` was hand-invented rather than read from the resource file, or `uip solution project add` was never run for the agent project | Run `uip maestro flow registry list --local` and use the returned `resourceKey` (same value as `resource.key` in `resources/solution_folder/process/agent/<CodedAgentProject>.json`) |
| Agent execution failed | Underlying agent errored | Check `$vars.{nodeId}.error` for details. For coded agents, test locally first with `uip codedagent run` |
| Empty `output.content` | Agent returned no response | Verify the agent is configured correctly (published: in Orchestrator; in-solution: in Studio Web) |
| `inputDefinition` is empty | Expected — agents accept input via flow wiring, not typed fields | Wire upstream data to the agent via `$vars` expressions |
