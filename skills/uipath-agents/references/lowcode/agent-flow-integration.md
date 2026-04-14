# Agent Flow Integration Guide

How to embed an inline low-code agent inside a UiPath Flow project.
Validated against `ValidSolutions/FlowWithInlineAgent`.

---

## Inline Agent Node

### When to use

- Agent is tightly coupled to this specific flow
- No need for separate versioning, evaluation, or reuse across flows
- Fastest to set up — no separate agent project required

### Node type

| Node type | Description |
|-----------|-------------|
| `uipath.agent.autonomous` | Autonomous reasoning agent embedded in the flow |

### `.flow` node structure

```jsonc
{
  "id": "autonomousAgent1",
  "type": "uipath.agent.autonomous",
  "typeVersion": "1.0.0",
  "inputs": {},                          // Empty — prompts/settings live in agent.json
  "outputs": {
    "error": {
      "type": "object",
      "description": "Error information if the node fails",
      "source": "=Error",
      "var": "error"
    }
  },
  "model": {
    "source": "<projectId-uuid>",        // ← UUID linking to the inline agent directory
    "type": "bpmn:ServiceTask",
    "serviceType": "Orchestrator.StartInlineAgentJob",
    "version": "v2",
    "context": [
      { "name": "_label", "type": "string", "value": "" },
      { "name": "entryPoint", "type": "string", "value": "" }
    ]
  }
}
```

**Critical fields:**
- `model.source` — The inline agent's `projectId` UUID. Must match the subdirectory name and `agent.json.projectId` inside the flow project.
- `model.serviceType` — Must be `"Orchestrator.StartInlineAgentJob"` (not `"Orchestrator.StartAgentJob"` which is for solution/external agents).
- `inputs` — Empty object. Agent prompts, model settings, and guardrails are configured in `agent.json` inside the inline agent directory, not on the flow node.

### Handles

| Handle | Position | Allowed connections |
|--------|----------|---------------------|
| `escalation` | top | `uipath.agent.resource.escalation` |
| `context` | bottom | `uipath.agent.resource.context.*` |
| `tool` | bottom | `uipath.agent.resource.tool.*` |
| `input` | left | Previous flow node |
| `success` | right | Next flow node |
| `error` | right | Error handler (when enabled) |

### Resource nodes (tools, contexts, escalations)

Resources are separate canvas nodes wired to the agent via artifact handle edges:

```jsonc
// Edge connecting tool to agent:
// sourceNodeId: "autonomousAgent1", sourcePort: "tool"
// targetNodeId: "agentTool1", targetPort: "input"
```

| Resource type | Node type pattern |
|--------------|-------------------|
| RPA process | `uipath.agent.resource.tool.rpa` |
| Agent-as-tool | `uipath.agent.resource.tool.agent.<process-key>` |
| IS connector | `uipath.agent.resource.tool.connector` |
| Semantic index | `uipath.agent.resource.context.index` |
| Escalation | `uipath.agent.resource.escalation` |
| MCP server | `uipath.agent.resource.mcp.*` |
| Memory space | `uipath.agent.resource.memory.*` |

---

## Inline Agent Directory Structure

The inline agent lives inside the flow project, in a subdirectory named after its `projectId`:

```
<FlowProject>/
├── <FlowName>.flow
├── <projectId-uuid>/           # ← model.source points here
│   ├── agent.json              # Agent definition (prompts, model, schemas)
│   ├── flow-layout.json        # Empty: {}
│   ├── evals/
│   │   └── eval-sets/          # Empty
│   ├── features/               # Empty
│   └── resources/              # Agent tool resources
└── ...
```

See [embedding-in-flows.md](embedding-in-flows.md) for the full inline agent creation guide.

---

## What Happens at Pack Time

`flow-workbench` extracts inline agents during `uip solution bundle` / `uip solution pack`:

1. Reads the inline agent directory referenced by `model.source` UUID
2. Collects connected resource nodes via artifact handles
3. Packages the `AgentDefinition` from the inline agent's `agent.json`
4. Writes into package:

```
content/
├── process.bpmn
├── operate.json            # contentType: "Flow"
├── entry-points.json       # type: "processorchestration"
├── bindings_v2.json
└── agents/
    └── <agentProjectId>/
        ├── agent.json      # Extracted AgentDefinition
        └── .agent-builder/
            ├── agent.json  # Execution model
            └── bindings.json
```

---

## Node Type Quick Reference

```
uipath.agent.autonomous                               ← Inline agent node

uipath.agent.resource.tool.rpa                        ← Tool: RPA process
uipath.agent.resource.tool.agent.<process-key>        ← Tool: another agent
uipath.agent.resource.tool.connector                  ← Tool: IS connector
uipath.agent.resource.tool.api                        ← Tool: API
uipath.agent.resource.tool.builtin                    ← Tool: built-in
uipath.agent.resource.context.index                   ← Context: semantic index
uipath.agent.resource.escalation                      ← Escalation: HITL
uipath.agent.resource.mcp.*                           ← MCP server
uipath.agent.resource.memory.*                        ← Memory space
```

---

## BPMN Execution Engine Notes

- **Inline agents**: `ServiceTask` with `serviceType: "Orchestrator.StartInlineAgentJob"`. The agent definition is read from the inline agent directory (`model.source` UUID) and executed in-process.

The execution is asynchronous. The flow pauses at the agent node and resumes when the agent job completes.
