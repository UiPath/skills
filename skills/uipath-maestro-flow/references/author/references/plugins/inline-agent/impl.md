# Inline Agent Node — Implementation

This plugin covers **flow-specific** operations for inline agent nodes: adding the node, wiring edges, JSON structure, and flow validation. For agent-side concerns (agent.json configuration, resource.json authoring, solution resources, prompts), see the `uipath-agents` skill — specifically `lowcode/capabilities/inline-in-flow/inline-in-flow.md`.

Node type: `uipath.agent.autonomous`. The agent is bound to a local subdirectory via `model.source = <projectId>`. The node's BPMN type and `serviceType` (`Orchestrator.StartInlineAgentJob`) come from the definition in `definitions[]`.

## Prerequisite — Scaffold the Inline Agent

```bash
uip agent init "<FlowProjectDir>" --inline-in-flow --output json
```

**Record the returned `ProjectId`** — the flow node's `model.source` must match it exactly (and must match the subdirectory name and `agent.json.projectId`).

For agent.json configuration and resource file setup, see the `uipath-agents` skill (`lowcode/agent-definition.md`, `lowcode/capabilities/inline-in-flow/inline-in-flow.md`).

## Registry Validation

Even though `uipath.agent.autonomous` is OOTB, validate it against the registry during Phase 2 to confirm the current product state:

```bash
uip maestro flow registry get uipath.agent.autonomous --output json
```

Confirm:

- Input port: `input`
- Output ports: `success`, `error`
- Artifact ports: `tool`, `context`, `escalation`
- `model.serviceType` — `Orchestrator.StartInlineAgentJob`
- `model.version` — `v2`

## Adding / Editing

For step-by-step add, delete, and wiring procedures, see [editing-operations.md](../../editing-operations.md). Inline-agent scaffolding uses `uip agent init --inline-in-flow`, but the flow graph is not a Flow CLI carve-out: add the `uipath.agent.autonomous` node, its `model.source`, outputs, variables, layout, and edges directly in the `.flow` JSON with `Edit` / `Write`.

### Add the node with Edit / Write

Use `Edit` to add a node instance to `nodes[]`. The instance carries only per-instance data (`inputs`, `outputs`, `display`). BPMN type, serviceType, version, and context templates come from the definition in `definitions[]`.

```json
{
  "id": "autonomousAgent1",
  "type": "uipath.agent.autonomous",
  "typeVersion": "1.0",
  "display": { "label": "Autonomous Agent" },
  "inputs": {
    "systemPrompt": "You are an agentic assistant.",
    "userPrompt": "What is the current date?",
    "agentInputVariables": [],
    "agentOutputVariables": [
      { "id": "content", "type": "string" }
    ]
  },
  "model": {
    "source": "<projectId-uuid>"
  },
  "outputs": {
    "output": {
      "type": "object",
      "description": "Agent response",
      "source": "=result.response",
      "var": "output"
    },
    "error": {
      "type": "object",
      "description": "Error information if the node fails",
      "source": "=Error",
      "var": "error"
    }
  }
}
```

Also add:

- A `definitions[]` entry copied verbatim from `uip maestro flow registry get uipath.agent.autonomous --output json` (`Data.Node` or the top-level node object, depending on CLI/plugin version). Set `typeVersion` to the copied definition's exact `version`.
- A `variables.nodes` entry for `output` and `error`.
- A placeholder `layout.nodes.<agentNodeId>` entry; `flow tidy` owns the final position.

### Wire edges with Edit / Write

Use `Edit` to add edge objects to `edges[]`:

```json
{
  "id": "<EDGE_ID>",
  "sourceNodeId": "<upstreamNodeId>",
  "sourcePort": "output",
  "targetNodeId": "autonomousAgent1",
  "targetPort": "input"
}
```

```json
{
  "id": "<EDGE_ID>",
  "sourceNodeId": "autonomousAgent1",
  "sourcePort": "success",
  "targetNodeId": "<nextNodeId>",
  "targetPort": "input"
}
```

For tool/resource nodes, wire the inline agent's bottom artifact port:

```json
{
  "id": "<EDGE_ID>",
  "sourceNodeId": "autonomousAgent1",
  "sourcePort": "tool",
  "targetNodeId": "<toolNodeId>",
  "targetPort": "input"
}
```

`tool` is the inline agent's bottom artifact port. The target node's `input` port is a target-typed artifact handle.

## Adding an External RPA Process Tool Node

Discover the tool via the flow registry, then add the tool resource node directly in the `.flow` JSON. Generate a resource UUID and use it as both the tool node's `model.source` and the `resource.json` directory/id.

```bash
# 1. Search for the process tool
uip maestro flow registry search "uipath.agent.resource.tool.process" --output json

# 2. Generate a resource UUID
RES=$(uuidgen)

# 3. Use Edit / Write to add the tool node, bindings, layout, and artifact edge
```

Tool node instance:

```json
{
  "id": "agentTool1",
  "type": "<NodeType>",
  "typeVersion": "<DEFINITION_VERSION>",
  "display": { "label": "<ToolName>" },
  "inputs": {},
  "model": {
    "source": "<RES_UUID>"
  }
}
```

Also add:

- The tool node definition copied verbatim from `registry get`.
- Top-level `bindings[]` entries for the process resource, using the definition's `model.bindings.resourceKey` and `model.bindings.values[]` (`name`, `folderPath`, etc.). See [editing-operations-json.md — Resource nodes](../../editing-operations-json.md#add-a-node).
- A placeholder `layout.nodes.<toolNodeId>` entry.
- The artifact edge from the inline agent's `tool` port to the tool node's `input` port, as shown above.

After adding the tool node, you must also:
- Hand-write the per-tool `resource.json` at `<FlowProjectDir>/<inlineAgentProjectId>/resources/<RES_UUID>/resource.json` — **use the exact format from the `uipath-agents` skill: `lowcode/capabilities/inline-in-flow/inline-in-flow.md` § Inline-in-Flow Process Tool resource.json.** The inline-in-flow convention differs from standalone agents: `location: "solution"`, `properties.folderPath: ""`, `referenceKey: ""`. Getting these wrong causes silent runtime failures.
- Set prompts in `agent.json` (system + user messages with `contentTokens` of `type: "simpleText"`)
- Run `uip agent validate --inline-in-flow` to validate the inline agent project
- Run `uip solution resource refresh` before upload

For agent.json prompt configuration and solution resource mechanics, see the `uipath-agents` skill (`lowcode/capabilities/inline-in-flow/inline-in-flow.md`).

## JSON Structure

The instance carries only per-instance data (`inputs`, `outputs`, `display`, and the minimal `model.source`). BPMN type, serviceType, version, and context templates come from the definition in `definitions[]`.

```json
{
  "id": "autonomousAgent1",
  "type": "uipath.agent.autonomous",
  "typeVersion": "1.0",
  "display": { "label": "Autonomous Agent" },
  "inputs": {
    "systemPrompt": "You are an agentic assistant.",
    "userPrompt": "What is the current date?",
    "agentInputVariables": [],
    "agentOutputVariables": [
      { "id": "content", "type": "string" }
    ]
  },
  "model": {
    "source": "<projectId-uuid>"
  },
  "outputs": {
    "output": {
      "type": "object",
      "description": "Agent response",
      "source": "=result.response",
      "var": "output"
    },
    "error": {
      "type": "object",
      "description": "Error information if the node fails",
      "source": "=Error",
      "var": "error"
    }
  }
}
```

Notes:

- `model.source` — the inline agent's `projectId`; must match the subdirectory name and `agent.json.projectId`. This is the only field that belongs in the node instance's `model` block.
- `inputs.systemPrompt` / `inputs.userPrompt` must be non-empty for current `flow validate`. Treat them as validator placeholders; the canonical inline-agent prompts live in `agent.json`.
- **No full `model` block on the instance.** The node inherits serviceType/version/context from `definitions[]`. The only instance `model` field is `source`; a stale `model.serviceType` on the instance overrides the inheritance and causes runtime mismatch.

## Accessing Output

```javascript
// In a Script node after the agent
const response = $vars.autonomousAgent1.output.content;
return { classification: response };
```

- `$vars.{nodeId}.output.content` — the agent's text response
- `$vars.{nodeId}.error` — error details if the agent fails

## Validate

Validate the inline agent definition, then the flow:

```bash
uip agent validate "<FlowProjectDir>/<projectId>" --inline-in-flow --output json
uip maestro flow validate <FlowName>.flow --output json
```

> Current validator requirement: `uip maestro flow validate` rejects flows whose `uipath.agent.autonomous` node lacks non-empty `inputs.systemPrompt` / `inputs.userPrompt`. Include placeholder values on the flow node, but keep the canonical prompts in the inline agent's `agent.json`.

## Debug

| Error | Cause | Fix |
| --- | --- | --- |
| `flow validate` reports `systemPrompt` / `userPrompt` required | The flow node lacks non-empty validator placeholders | Add non-empty `inputs.systemPrompt` / `inputs.userPrompt` placeholders; keep canonical prompts in `agent.json` |
| `model.source` UUID does not match any subdirectory | Wrong source value, or folder renamed | Set `model.source` to the exact UUID of the inline agent directory |
| Flow runs a different agent than expected | `model.source` points to a stale/leftover inline agent dir | Check subdirectory names — only one inline agent dir should correspond to each agent node |
| `Orchestrator.StartAgentJob` error at runtime | Stale `model` block on the instance overrides the inherited definition | Remove the instance `model` block and keep the registry definition's `model.serviceType: "Orchestrator.StartInlineAgentJob"` in `definitions[]` |
| Studio Web reports "System prompt is required" | Inline agent's `agent.json.messages[]` has empty `content`, OR `.agent-builder/agent.json` is stale | Set prompts in `agent.json`, re-run `uip agent validate --inline-in-flow` — see `uipath-agents` skill |
| Studio Web debug: "Could not find process for tool" | `uip solution resource refresh` not run before upload | Run `uip solution resource refresh <SolutionRoot>` — see `uipath-agents` skill (`lowcode/solution-resources.md`) |
| Agent tool process cannot resolve at runtime | Missing top-level `bindings[]` entries, mismatched `model.source` / `resource.json` id, or stale solution resources | Add the resource bindings from the tool definition, keep `model.source` equal to the resource UUID, and run `uip solution resource refresh` |

## What NOT to Do

- **Do not treat `inputs.systemPrompt` / `inputs.userPrompt` as canonical prompts** — current validation requires non-empty placeholders on the flow node, but prompts live in `agent.json`.
- **Do not put a full `model` block on the instance** — the node inherits serviceType/version/context from `definitions[]`; the instance model contains only `source`.
- **Do not use `model.agentProjectId` or `inputs.source`** — use `model.source`.
- **Do not create `entry-points.json` or `project.uiproj` inside the inline agent directory** — those belong only to standalone agent projects.
- **Do not name the inline agent folder with a human-readable name** — the folder name must be the `projectId` UUID.
- **Do not use `uip agent tool add`** for inline-in-flow agents — hand-author the tool's `resource.json` instead.
- **Do not skip `uip agent validate --inline-in-flow`** after editing `agent.json` or any `resources/*/resource.json`.
