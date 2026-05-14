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
├── <projectId-uuid>/           # Inline agent subdirectory (UUID as folder name) ← inputs.source points here
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
- `inputSchema.properties` starts empty, but **must declare one slot per `{{input.<id>}}` token used in `messages[].content`**. Each slot's `<id>` and `type` must match the corresponding `agentInputVariables[]` entry on the flow node. See the `uipath-maestro-flow` skill's [inline-agent prompt-wiring guide](../../../../../uipath-maestro-flow/references/author/references/plugins/inline-agent/impl.md#wiring-flow-variables-into-agent-prompts) for the full four-place contract.
- `messages` have empty `content` and `contentTokens` initially (edit agent.json to set prompts with `type: "simpleText"` and `rawString`)
- `guardrails: []` at root level — can be populated with guardrail objects. See [../guardrails/guardrails.md](../guardrails/guardrails.md)
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

`--inline-in-flow` skips `entry-points.json` and `project.uiproj` checks.

For tool-bearing inline agents, check `uip agent validate --help`. If the installed CLI supports `--bindings-target`, run validation with it after all flow graph edits:

```bash
uip agent validate "<FlowProjectDir>/<projectId>" --inline-in-flow \
  --bindings-target "<FlowProjectDir>/bindings_v2.json" --output json
```

`--bindings-target` propagates the inline agent's tool bindings (process, connection, index, etc.) into the flow project's `bindings_v2.json`. This is required for `uip solution resource refresh` to discover tool bindings and create solution-level resource files. If the installed CLI does not expose `--bindings-target`, validate with the supported command and treat tool-binding propagation as a CLI capability blocker for tool-bearing inline agents; do not invent or hand-edit `bindings_v2.json`.

> **Ordering constraint:** run the final `uip agent validate --inline-in-flow` after all flow graph edits are complete. The `uipath-maestro-flow` skill owns direct `.flow` authoring for the inline-agent node, tool-resource nodes, and edges; validate last so generated tool bindings remain in the flow project's `bindings_v2.json` when the CLI supports `--bindings-target`. See the [Walkthrough](#walkthrough--end-to-end) for the correct sequence.

## Flow Wiring

After creating the inline agent, the flow needs a `uipath.agent.autonomous` node whose `inputs.source` is the inline agent's `projectId` UUID, plus edges connecting it to the rest of the flow.

**Hand off to the `uipath-maestro-flow` skill for the actual node and edge authoring.** Per Critical Rule 16, this skill does not invoke flow operations directly. Tell the user:

> The inline agent has been scaffolded at `<FlowProjectDir>/<projectId>/`. To wire it into the flow, use the `uipath-maestro-flow` skill — pass it `projectId = <uuid>` so it can add a `uipath.agent.autonomous` node with `inputs.source = <uuid>` and connect the input/success edges via direct `.flow` authoring. **After all flow graph edits are complete**, run `uip agent validate --inline-in-flow`; for tool-bearing inline agents, include `--bindings-target <FlowProjectDir>/bindings_v2.json` when the installed CLI supports it.

The node JSON shape that the flow skill must produce is documented in § Flow Node Structure below — keep it as a reference, not as a CLI walkthrough.

## Inline-in-Flow Process Tool resource.json

The `resource.json` for process tools inside an inline-in-flow agent uses the **same format** as external process tools in standalone agents. Follow the discovery workflow and resource.json shape in [../process/process.md](../process/process.md) — run `uip solution resource list` + `uip solution resource get` to populate `referenceKey`, `folderPath`, `inputSchema`, and `outputSchema` with real values.

**Path:** `<FlowProjectDir>/<projectId>/resources/<RES_UUID>/resource.json`

Additional notes for inline-in-flow:
- **`location`**: Follows the same rule as standalone agents — set `"solution"` when the row from `uip solution resource list` has `Source: "Local"`, set `"external"` when `Source: "Remote"`. See [../process/process.md](../process/process.md) and [../../critical-rules.md](../../critical-rules.md) Rule 12.
- **`id`**: Must match the `<RES_UUID>` used as the tool node's `model.source` in the flow and the resource directory name.
- **`properties.folderPath`**: Must be the **literal folder path from discovery** (e.g., `"Shared/TestRPA"`) — do **not** leave it empty. An empty `folderPath` prevents `uip solution resource refresh` from resolving the process at runtime.
- **`inputSchema.properties`**: Must include `"guardrails": { "type": "array" }` alongside the process arguments — the runtime expects it.
- **All fields from the template in [../process/process.md](../process/process.md) are required** — especially `$resourceType: "tool"`, `guardrail`, `properties.processName`, `properties.exampleCalls`, `isEnabled`, and `argumentProperties`. A `resource.json` missing `$resourceType` will not be recognized by `uip agent validate`, resulting in `"resources": 0` validated and an empty `bindings_v2.json`.

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
  "typeVersion": "1.0",
  "display": { "label": "Autonomous Agent" },
  "inputs": {
    "systemPrompt": "You are an agentic assistant.",
    "userPrompt": "What is the current date?",
    "source": "<projectId-uuid>",        // UUID linking to the inline agent directory
    "agentInputVariables": [],
    "agentOutputVariables": [
      { "id": "content", "type": "string" }
    ]
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

**Critical fields:**
- `inputs.source` — The inline agent's `projectId` UUID. Must match the subdirectory name and `agent.json.projectId` inside the flow project. The definition still declares `model.source: true`, but flow-core hoists that identity field onto `inputs.source` for the `uipath.agent.autonomous` node instance.
- `inputs.systemPrompt` / `inputs.userPrompt` — Current flow validation requires non-empty placeholders on the node. The canonical prompts still live in `agent.json.messages[]`.
- `definitions[]` — The `uipath.agent.autonomous` definition copied from the flow registry supplies `model.serviceType: "Orchestrator.StartInlineAgentJob"`, BPMN type, version, and context. Do not copy those fields into the node instance.
- No node instance `model` block — the inline-agent source lives at `inputs.source`.

Resource nodes use the same minimal `model.source` pattern:

```jsonc
{
  "id": "agentTool1",
  "type": "uipath.agent.resource.tool.rpa",
  "typeVersion": "<DEFINITION_VERSION>",
  "display": { "label": "<ToolName>" },
  "inputs": {},
  "model": {
    "source": "<RES_UUID>"
  }
}
```

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
# See § Inline-in-Flow Process Tool resource.json above for the exact format

# 5. Hand off to the uipath-maestro-flow skill to add the
#    uipath.agent.autonomous node (inputs.source = <projectId>),
#    tool resource nodes, and wire all edges (input/success/tool).
#    Do NOT run uip flow commands from this skill —
#    Critical Rule 16.

# 6. Validate the inline agent and propagate tool bindings to flow project.
#    MUST run AFTER flow graph edits (step 5), so generated tool bindings
#    are the last update to bindings_v2.json before resource refresh when
#    the installed CLI supports --bindings-target.
uip agent validate "<FlowProjectDir>/<projectId>" --inline-in-flow --output json

# For tool-bearing inline agents, when supported by `uip agent validate --help`:
# uip agent validate "<FlowProjectDir>/<projectId>" --inline-in-flow \
#   --bindings-target "<FlowProjectDir>/bindings_v2.json" --output json

# 7. Refresh solution resources and upload
uip solution resource refresh --output json
```

## What Happens at Pack Time

`flow-workbench` extracts inline agents during `uip solution upload` / `uip solution pack`:

1. Reads the inline agent directory referenced by `inputs.source` UUID
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
uipath.agent.resource.memory.*                        ← Memory space
```

## BPMN Execution Engine Notes

- **Inline agents**: `ServiceTask` with `serviceType: "Orchestrator.StartInlineAgentJob"`. The agent definition is read from the inline agent directory (`inputs.source` UUID) and executed in-process.

The execution is asynchronous. The flow pauses at the agent node and resumes when the agent job completes.

## Gotchas

See [../../critical-rules.md](../../critical-rules.md) Critical Rule 15. The skill explicitly defers flow authoring to `uipath-maestro-flow` — it does not invoke that skill automatically (Critical Rule 16).

**Tool bindings must be propagated to the flow project's `bindings_v2.json`.** Only project-level bindings are scanned by `uip solution resource refresh`. When the installed CLI supports `--bindings-target`, pass `--bindings-target <FlowProjectDir>/bindings_v2.json` while running `uip agent validate --inline-in-flow`. Without project-level propagation, Studio Web debug can fail with "Could not find process for tool" because no solution-level resource file is created for the tool process.

Run the final agent validation as the **last step** before `uip solution resource refresh`, after all flow graph edits are complete. See the [Walkthrough](#walkthrough--end-to-end) for the correct sequence.

## References

- [../../agent-definition.md](../../agent-definition.md) — agent.json schema (same as standalone, with the inline-specific differences listed above)
- [../../critical-rules.md](../../critical-rules.md) Critical Rule 15
