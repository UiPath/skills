# Inline Agent Node — Implementation

Inline agent nodes embed an autonomous agent inside the flow project. Node type: `uipath.agent.autonomous`. The agent is bound to a local subdirectory via `inputs.source = <projectId>`. The node's BPMN type (`bpmn:ServiceTask`) and `serviceType` (`Orchestrator.StartInlineAgentJob`) come from the definition.

## Prerequisite — Scaffold the Inline Agent

The inline agent directory must exist before the flow node can reference it. Run from the solution directory (or pass an absolute path):

```bash
uip agent init "<FlowProjectDir>" --inline-in-flow --output json
```

This creates `<FlowProjectDir>/<projectId-uuid>/` with:

- `agent.json` — agent definition (model, prompts, schemas)
- `flow-layout.json` — empty `{}`
- `evals/eval-sets/` — empty
- `features/` — empty
- `resources/` — empty (add tool resource files here later)

**Record the returned `ProjectId`** — the flow node's `--source` / `inputs.source` must match it exactly (and must match the subdirectory name and `agent.json.projectId`).

## Configure `agent.json`

Edit `<FlowProjectDir>/<projectId>/agent.json`:

1. Set `settings.model` (e.g., `"anthropic.claude-sonnet-4-6"`, `"gpt-4o-2024-11-20"`)
2. Set `settings.temperature`, `settings.maxTokens`, `settings.maxIterations`
3. Write system prompt in `messages[0].content` and rebuild `messages[0].contentTokens`
4. Write user prompt in `messages[1].content` and rebuild `messages[1].contentTokens`
5. Configure `inputSchema` and `outputSchema` if the agent needs structured I/O

Use `type: "simpleText"` with `rawString` for `contentTokens`:

```json
"contentTokens": [
  { "type": "simpleText", "rawString": "Your prompt text here" }
]
```

For detailed agent configuration (contentTokens format, model settings, resource files, tool bindings), use the `uipath-agents` skill.

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
- `inputDefinition` — typically empty (prompts live in `agent.json`, not on the node)
- `outputDefinition.output.schema` — contains `content` (string)
- `outputDefinition.error.schema` — contains `code`, `message`, `detail`, `category`, `status`

## Adding / Editing

For step-by-step add, delete, and wiring procedures, see [flow-editing-operations.md](../../flow-editing-operations.md). Use the `--source` flag to bind the node to the inline agent during `node add`.

### Add the node via CLI

```bash
uip maestro flow node add <FlowName>.flow uipath.agent.autonomous \
  --source <PROJECTID_UUID> \
  --label "<LABEL>" \
  --position <X>,<Y> \
  --output json
```

`--source` populates `inputs.source` with the inline agent's `projectId`. The command automatically:

- Adds the node to `nodes` with a generated `id`
- Adds the definition to `definitions` (if not already present)
- The definition carries `model.serviceType: "Orchestrator.StartInlineAgentJob"` — the instance does not

**Save the returned node ID** — you need it when wiring edges.

### Wire edges

```bash
# List nodes to get IDs
uip maestro flow node list <FlowName>.flow --output json

# Sequence input (upstream -> agent)
uip maestro flow edge add <FlowName>.flow <upstreamNodeId> <agentNodeId> \
  --source-port output --target-port input --output json

# Sequence output (agent success -> downstream)
uip maestro flow edge add <FlowName>.flow <agentNodeId> <nextNodeId> \
  --source-port success --target-port input --output json
```

Artifact ports (`tool`, `context`, `escalation`) connect to inline resource nodes rather than to sequence nodes — see the `uipath-agents` skill for the resource file format.

## JSON Structure

The instance carries only per-instance data (`inputs`, `outputs`, `display`). BPMN type, serviceType, version, and context templates come from the definition in `definitions[]`.

```json
{
  "id": "classifyIntent",
  "type": "uipath.agent.autonomous",
  "typeVersion": "1.0.0",
  "display": { "label": "Classify Intent" },
  "inputs": {
    "source": "<projectId-uuid>"
  },
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
  }
}
```

Notes:

- `inputs.source` — the inline agent's `projectId`; must match the subdirectory name and `agent.json.projectId`. This is the **only** per-instance input — prompts and model config live in `agent.json`, not on the node.
- No `model` block — inline agents do not use process-style bindings (no `resourceKey`, no `folderPath`), and BPMN/serviceType fields live in the definition only.

## Accessing Output

The agent's response is available downstream:

```javascript
// In a Script node after the agent
const response = $vars.classifyIntent.output.content;
return { classification: response };
```

- `$vars.{nodeId}.output.content` — the agent's text response
- `$vars.{nodeId}.error` — error details if the agent fails

## Tool / Context / Escalation Resources

Create resource files inside `<FlowProjectDir>/<projectId>/resources/<ResourceName>/resource.json`. Format is identical to standalone agent resources — see the `uipath-agents` skill for the `$resourceType`, `type`, and schema structure.

## Validate

Validate the inline agent definition, then the flow:

```bash
uip agent validate "<FlowProjectDir>/<projectId>" --inline-in-flow --output json
uip maestro flow validate <FlowName>.flow --output json
```

The agent validate step checks `agent.json`, `contentTokens`, schemas, and resource files. The flow validate step checks the node wiring and definitions. Both must pass before publishing.

## Directory Structure

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
│       └── <ResourceName>/
│           └── resource.json
└── ...
```

## Debug

| Error | Cause | Fix |
| --- | --- | --- |
| `inputs.source` UUID does not match any subdirectory | Wrong `--source` value, or folder renamed | Set `--source` to the exact UUID of the inline agent directory; rename folder back to the UUID if renamed |
| Flow runs a different agent than expected | `inputs.source` points to a stale/leftover inline agent dir | Check subdirectory names — only one inline agent dir should correspond to each agent node |
| `Orchestrator.StartAgentJob` error at runtime | Wrong definition (published-agent definition attached to inline-agent node) | Replace the `definitions[]` entry with the one from `uip maestro flow registry get uipath.agent.autonomous --output json` — it carries `model.serviceType: "Orchestrator.StartInlineAgentJob"` |
| Prompts placed on `inputs.systemPrompt` / `inputs.userPrompt` are ignored | Prompts don't belong on the node | Move prompts to `agent.json.messages[]`; `inputs` on the node only carries `source` |
| `inputs.agentProjectId` unrecognized | Wrong field name | Use `inputs.source` — `agentProjectId` is not valid for inline agents |
| Inline agent rejected by `uip agent validate` | `entry-points.json` or `project.uiproj` present inside the inline agent dir | Delete those files — they belong only to standalone agent projects |
| Folder name is human-readable instead of UUID | Folder renamed after scaffolding | Rename to the original `projectId` UUID — the folder name must match `inputs.source` and `agent.json.projectId` |
| Agent runs but returns empty `output.content` | Missing or malformed `contentTokens` in `agent.json` | Rebuild `messages[].contentTokens` using `{ "type": "simpleText", "rawString": "..." }` entries; see `uipath-agents` for detail |

## What NOT to Do

- **Do not set `inputs.systemPrompt` or `inputs.userPrompt` on the flow node** — prompts live in `agent.json`. The only `inputs` field on the node is `source`.
- **Do not use `inputs.agentProjectId` or `model.agentProjectId`** — use `inputs.source`.
- **Do not put a `model` block on the instance** — `serviceType`, BPMN type, and context live in the definition only (copied from the registry). A published-agent node's definition uses `Orchestrator.StartAgentJob`; an inline-agent node must use the `uipath.agent.autonomous` definition with `Orchestrator.StartInlineAgentJob`.
- **Do not create `entry-points.json` or `project.uiproj` inside the inline agent directory** — those belong only to standalone agent projects.
- **Do not name the inline agent folder with a human-readable name** — the folder name must be the `projectId` UUID.
- **Do not create `bindings_v2.json` entries for inline agent nodes** — inline agents do not use process-style bindings (no `resourceKey`, no `folderPath`).
