# Inline Agent in a Flow

Walkthrough for embedding a low-code agent directly inside a flow project. The agent lives as a UUID-named subdirectory inside the flow project and is published with the parent flow.

Flow authoring itself is the responsibility of the `uipath-maestro-flow` skill — this file covers only the inline-agent side (creating the agent subdirectory, configuring it, and the shape of the `uipath.agent.autonomous` flow node that references it).

## When to Use

- Agent is tightly coupled to this specific flow
- No need for separate versioning, evaluation, or reuse across flows
- Fastest to set up — no separate agent project required

## Standalone vs Inline

| Aspect | Standalone | Inline |
|--------|-----------|--------|
| Location | Own project in solution | Subdirectory inside flow project, named by projectId (UUID) |
| Files | agent.json, entry-points.json, project.uiproj, flow-layout.json, evals/ | agent.json, flow-layout.json (`{}`), evals/eval-sets/ (empty), features/, resources/ |
| Lifecycle | Independent publish | Published with parent flow |
| Best for | Agent runs on its own or is referenced externally | Agent is a step within a flow |

## Inline Agent Directory Structure

An inline agent lives in a subdirectory named after its `projectId` (a UUID). It contains `agent.json`, an empty `flow-layout.json`, and empty scaffold directories:

```
<FlowProject>/
├── <FlowName>.flow
├── project.uiproj              # Flow's project file
├── <projectId-uuid>/           # Inline agent subdirectory (UUID as folder name) ← model.source points here
│   ├── agent.json              # Agent definition (same schema as standalone — see ../../agent-definition.md)
│   ├── flow-layout.json        # Empty: {}
│   ├── evals/
│   │   └── eval-sets/          # Empty (no evaluators for inline agents)
│   ├── features/               # Empty
│   └── resources/              # Agent resources (tools, contexts, escalations)
└── ...
```

### Key differences from standalone agent

- **Folder name** is the agent's `projectId` UUID, not a human-readable name
- **`flow-layout.json`** is an empty JSON object `{}`
- **No `entry-points.json`** — the flow handles entry points
- **No `project.uiproj`** — governed by the parent flow project
- **`evals/`** contains only the `eval-sets/` subdirectory (empty) — no evaluators
- Has a root-level `guardrails: []` field
- No `metadata.targetRuntime`

## Creating an Inline Agent

### Option A: CLI command (recommended)

```bash
uip agent init "<FlowProjectDir>" --inline-in-flow --output json
```

This generates a UUID for the `projectId`, creates the subdirectory `<FlowProjectDir>/<uuid>/`, and scaffolds `agent.json`, `flow-layout.json`, and empty directories.

### Option B: Manual creation

#### Step 1: Start with an existing flow project

The flow project must already exist.

#### Step 2: Generate a UUID and create the agent subdirectory

Generate a unique UUID (e.g., `5029c8a8-799b-426a-803f-c4ec75255439`). Create a directory with that UUID as the name inside the flow project.

#### Step 3: Create agent.json

Same schema as a standalone agent (see [../../agent-definition.md](../../agent-definition.md)), with these conventions:
- `projectId` matches the folder name UUID
- `inputSchema.properties` is empty (flow wires data via node connections)
- `messages` have empty `content` and `contentTokens` initially (edit agent.json to set prompts with `type: "simpleText"` and `rawString`)
- `guardrails: []` at root level
- No `metadata.targetRuntime` field

Example:
```json
{
  "version": "1.1.0",
  "settings": {
    "model": "gpt-4o-2024-11-20",
    "maxTokens": 16384,
    "temperature": 0,
    "engine": "basic-v2",
    "maxIterations": 25,
    "mode": "standard"
  },
  "inputSchema": { "type": "object", "properties": {} },
  "outputSchema": {
    "type": "object",
    "properties": {
      "content": { "type": "string", "description": "Output content" }
    }
  },
  "metadata": {
    "storageVersion": "50.0.0",
    "isConversational": false,
    "showProjectCreationExperience": false
  },
  "type": "lowCode",
  "guardrails": [],
  "messages": [
    { "role": "system", "content": "", "contentTokens": [] },
    { "role": "user", "content": "", "contentTokens": [] }
  ],
  "projectId": "5029c8a8-799b-426a-803f-c4ec75255439"
}
```

#### Step 4: Create flow-layout.json

```json
{}
```

#### Step 5: Create empty directories

```
evals/eval-sets/
features/
resources/
```

## Validate Inline Agent

```bash
uip agent validate "<FlowProjectDir>/<projectId>" --inline-in-flow --output json
```

`--inline-in-flow` skips `entry-points.json` and `project.uiproj` checks, and does not generate `.agent-builder/` files.

## Flow Wiring

After creating the inline agent, add a `uipath.agent.autonomous` node to the flow that references it via `model.source = projectId`.

Use the `uip maestro flow node add` command with the `--source` parameter:

```bash
uip maestro flow node add <FlowName>.flow uipath.agent.autonomous \
  --source <projectId-uuid> \
  --label "Autonomous Agent" \
  --output json
```

Then wire edges using:

```bash
uip maestro flow edge add <FlowName>.flow <sourceNodeId> <agentNodeId> \
  --source-port success \
  --target-port input \
  --output json
```

Flow wiring details (edge ports, node IDs) are handled by the `uipath-maestro-flow` skill.

## Flow Node Structure

### Node type

| Node type | Description |
|-----------|-------------|
| `uipath.agent.autonomous` | Autonomous reasoning agent embedded in the flow |

### `.flow` node JSON

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

## Walkthrough — End-to-End

```bash
# 1. Ensure solution and flow project exist
# (use uipath-maestro-flow skill to create them, or start from existing)

# 2. Scaffold the inline agent inside the flow project
uip agent init "<FlowProjectDir>" --inline-in-flow --output json
# Returns the generated projectId (UUID) and path

# 3. Edit the agent.json inside <FlowProjectDir>/<projectId>/
# - Set system prompt in messages[0].content + rebuild contentTokens
# - Set model in settings.model
# - Configure outputSchema if needed

# 4. Add tools to <FlowProjectDir>/<projectId>/resources/ (optional)
# Same resource.json format as standalone agents

# 5. Validate the inline agent
uip agent validate "<FlowProjectDir>/<projectId>" --inline-in-flow --output json

# 6. Add the inline agent node to the flow
uip maestro flow node add <FlowName>.flow uipath.agent.autonomous \
  --source <projectId> \
  --label "Autonomous Agent" \
  --output json

# 7. Wire edges to connect the agent node
uip maestro flow edge add <FlowName>.flow <sourceNodeId> <agentNodeId> \
  --source-port success \
  --target-port input \
  --output json
```

## What Happens at Pack Time

`flow-workbench` extracts inline agents during `uip solution upload` / `uip solution pack`:

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

## BPMN Execution Engine Notes

- **Inline agents**: `ServiceTask` with `serviceType: "Orchestrator.StartInlineAgentJob"`. The agent definition is read from the inline agent directory (`model.source` UUID) and executed in-process.

The execution is asynchronous. The flow pauses at the agent node and resumes when the agent job completes.

## Gotchas

See [../../critical-rules.md](../../critical-rules.md) Critical Rule 15. The skill explicitly defers flow authoring to `uipath-maestro-flow` — it does not invoke that skill automatically (Critical Rule 16).

## References

- [../../agent-definition.md](../../agent-definition.md) — agent.json schema (same as standalone, with the inline-specific differences listed above)
- [../../critical-rules.md](../../critical-rules.md) Critical Rule 15
