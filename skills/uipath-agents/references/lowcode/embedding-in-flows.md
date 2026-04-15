# Inline Agents in Flow Projects

Agents can be embedded as a subdirectory inside a flow project instead of existing as standalone projects.

## Standalone vs Inline

| Aspect | Standalone | Inline |
|--------|-----------|--------|
| Location | Own project in solution | Subdirectory inside flow project, named by projectId (UUID) |
| Files | agent.json, entry-points.json, project.uiproj, flow-layout.json, evals/ | agent.json, flow-layout.json (`{}`), evals/eval-sets/ (empty), features/, resources/ |
| Lifecycle | Independent publish | Published with parent flow |
| Best for | Agent runs on its own or is referenced externally | Agent is a step within a flow |

## Inline Agent Structure

An inline agent lives in a subdirectory named after its `projectId` (a UUID). It contains `agent.json`, an empty `flow-layout.json`, and empty scaffold directories:

```
<FlowProject>/
├── <FlowName>.flow
├── project.uiproj              # Flow's project file
├── <projectId-uuid>/           # Inline agent subdirectory (UUID as folder name)
│   ├── agent.json              # Agent definition (same schema as standalone)
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

Same schema as a standalone agent (see [agent-json-format.md](agent-json-format.md)), with these conventions:
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

### Flow Wiring

After creating the inline agent, add a `uipath.agent.autonomous` node to the flow that references it via `model.source = projectId`.

Use the `uip flow node add` command with the `--source` parameter:

```bash
uip flow node add <FlowName>.flow uipath.agent.autonomous \
  --source <projectId-uuid> \
  --label "Autonomous Agent" \
  --output json
```

Then wire edges using:

```bash
uip flow edge add <FlowName>.flow <sourceNodeId> <agentNodeId> \
  --source-port success \
  --target-port input \
  --output json
```

See [agent-flow-integration.md](agent-flow-integration.md) for the node structure and handle details. Flow wiring is handled by the `uipath-maestro-flow` skill.
