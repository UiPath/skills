# Inline Agent Node Guide

How to add an inline `uipath.agent.autonomous` node to a flow. The agent definition lives as a subdirectory inside the flow project and is published with the flow.

---

## When to Use

- Agent is tightly coupled to this specific flow
- No need for separate versioning, evaluation, or reuse across flows
- Fastest to set up — no separate agent project required

For reusable agents (separate versioning, evals, shared across flows), use a solution or external agent node instead. See the `uipath-lowcode-agents` skill for details.

---

## Step-by-Step Workflow

### Step 1 — Scaffold the inline agent

Run from the solution directory (or pass an absolute path):

```bash
uip low-code-agent init "<FlowProjectDir>" --inline-in-flow --output json
```

This creates `<FlowProjectDir>/<projectId-uuid>/` with:
- `agent.json` — Agent definition (model, prompts, schemas)
- `flow-layout.json` — Empty `{}`
- `evals/eval-sets/` — Empty
- `features/` — Empty
- `resources/` — Empty (add tool resources here later)

**Save the returned `ProjectId`** — you need it for the flow node's `model.source`.

### Step 2 — Configure the agent

Edit `<FlowProjectDir>/<projectId>/agent.json`:

1. Set `settings.model` (e.g., `"anthropic.claude-sonnet-4-6"`, `"gpt-4o-2024-11-20"`)
2. Set `settings.temperature`, `settings.maxTokens`, `settings.maxIterations`
3. Write system prompt in `messages[0].content` and rebuild `messages[0].contentTokens`
4. Write user prompt in `messages[1].content` and rebuild `messages[1].contentTokens`
5. Configure `inputSchema` and `outputSchema` if the agent needs structured I/O

**Important:** Use `type: "simpleText"` with `rawString` for contentTokens:

```json
"contentTokens": [
  {
    "type": "simpleText",
    "rawString": "Your prompt text here"
  }
]
```

Use the `uipath-lowcode-agents` skill for detailed agent configuration guidance (contentTokens format, resource files, model settings).

### Step 3 — Get the node definition from registry (optional)

```bash
uip flow registry get uipath.agent.autonomous --output json
```

This is optional - the `node add` command will handle the definition automatically.

### Step 4 — Add the node to the `.flow` file

Use the CLI to add the inline agent node with the `--source` parameter:

```bash
uip flow node add <FlowName>.flow uipath.agent.autonomous \
  --source <PROJECTID_UUID> \
  --label "Autonomous Agent" \
  --position 400,144 \
  --output json
```

The `--source` parameter populates `model.source` with the inline agent's projectId. The command automatically:
- Adds the node to the `nodes` array
- Adds the definition to the `definitions` array (if not already present)
- Assigns a unique node ID

**Save the returned node ID** for wiring edges in the next step.

### Step 5 — Wire edges

Connect the inline agent node using the CLI:

```bash
# List nodes to get IDs
uip flow node list <FlowName>.flow --output json

# Add edge from start to agent
uip flow edge add <FlowName>.flow start <agentNodeId> \
  --source-port output \
  --target-port input \
  --output json

# Add edge from agent to next node
uip flow edge add <FlowName>.flow <agentNodeId> <nextNodeId> \
  --source-port success \
  --target-port input \
  --output json
```

#### Ports

| Port | Position | Direction | Use |
|------|----------|-----------|-----|
| `input` | left | target | Flow sequence input |
| `success` | right | source | Normal flow output |
| `error` | right | source | Error handler (when `errorHandlingEnabled`) |
| `tool` | bottom | source (artifact) | Connect tool resource nodes |
| `context` | bottom | source (artifact) | Connect context resource nodes |
| `escalation` | top | source (artifact) | Connect escalation resource nodes |

### Step 6 — Add tool resources (optional)

Create resource files inside `<FlowProjectDir>/<projectId>/resources/<ToolName>/resource.json`. Same format as standalone agent resources. Use the `uipath-lowcode-agents` skill for resource file formats.

### Step 7 — Validate

Validate the inline agent definition:

```bash
uip low-code-agent validate "<FlowProjectDir>/<projectId>" --inline-in-flow --output json
```

Then validate the flow file:

```bash
uip flow validate <FlowName>.flow --output json
```

---

## Node Model Fields

| Field | Value | Description |
|-------|-------|-------------|
| `model.source` | UUID | The inline agent's `projectId`. Must match the subdirectory name and `agent.json.projectId`. |
| `model.type` | `"bpmn:ServiceTask"` | BPMN execution type |
| `model.serviceType` | `"Orchestrator.StartInlineAgentJob"` | Distinguishes inline agents from solution/external agents (`StartAgentJob`) |
| `model.version` | `"v2"` | API version |
| `model.context` | Array | Runtime context entries (`_label`, `entryPoint`) |

---

## Inline Agent Directory Structure

```
<FlowProject>/
├── <FlowName>.flow
├── project.uiproj
├── <projectId-uuid>/               # Inline agent (folder name = projectId)
│   ├── agent.json                   # Agent definition
│   ├── flow-layout.json             # Empty: {}
│   ├── evals/
│   │   └── eval-sets/               # Empty
│   ├── features/                    # Empty
│   └── resources/                   # Tool resources (optional)
│       └── <ToolName>/
│           └── resource.json
└── ...
```

---

## What NOT to Do

- **Do not set `inputs.systemPrompt` or `inputs.userPrompt` on the flow node** — prompts are configured in `agent.json`, not on the node. The node's `inputs` should be `{}`.
- **Do not use `model.agentProjectId`** — use `model.source` for inline agents.
- **Do not use `serviceType: "Orchestrator.StartAgentJob"`** — that is for solution/external agents. Inline agents use `"Orchestrator.StartInlineAgentJob"`.
- **Do not create `entry-points.json` or `project.uiproj` inside the inline agent directory** — those are only for standalone agent projects.
- **Do not name the inline agent folder with a human-readable name** — the folder name must be the agent's `projectId` UUID.
- **Do not create process bindings for inline agent nodes** — inline agents do not use process-style bindings (no `resourceKey`, no `folderPath` binding entries).
