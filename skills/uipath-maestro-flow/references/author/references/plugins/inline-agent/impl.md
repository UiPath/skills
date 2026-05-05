# Inline Agent Node — Implementation

This plugin covers **flow-specific** operations for inline agent nodes: adding the node, wiring edges, JSON structure, and flow validation. For agent-side concerns (agent.json configuration, resource.json authoring, solution resources, prompts), see the `uipath-agents` skill — specifically `lowcode/capabilities/inline-in-flow/inline-in-flow.md`.

Node type: `uipath.agent.autonomous`. The agent is bound to a local subdirectory via `inputs.source = <projectId>`. The node's BPMN type and `serviceType` (`Orchestrator.StartInlineAgentJob`) come from the definition in `definitions[]`.

## Prerequisite — Scaffold the Inline Agent

```bash
uip agent init "<FlowProjectDir>" --inline-in-flow --output json
```

**Record the returned `ProjectId`** — the flow node's `--source` / `inputs.source` must match it exactly (and must match the subdirectory name and `agent.json.projectId`).

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

For step-by-step add, delete, and wiring procedures, see [editing-operations.md](../../editing-operations.md). Use the `--source` flag to bind the node to the inline agent during `node add`.

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
# Sequence input (upstream -> agent)
uip maestro flow edge add <FlowName>.flow <upstreamNodeId> <agentNodeId> \
  --source-port output --target-port input --output json

# Sequence output (agent success -> downstream)
uip maestro flow edge add <FlowName>.flow <agentNodeId> <nextNodeId> \
  --source-port success --target-port input --output json
```

### Wire tool artifact edge

```bash
uip maestro flow edge add <FlowName>.flow <agentNodeId> <toolNodeId> \
  --source-port tool --target-port input --output json
```

`tool` is the inline agent's bottom artifact port. The target node's `input` port is a target-typed artifact handle.

## Adding an External RPA Process Tool Node

Discover the tool via the flow registry, then add it with `--source` pointing to a new resource UUID:

```bash
# 1. Search for the process tool
uip maestro flow registry search "uipath.agent.resource.tool.process" --output json

# 2. Generate a resource UUID
RES=$(uuidgen)

# 3. Add the tool node
uip maestro flow node add <FlowName>.flow "<NodeType>" \
  --source "$RES" \
  --label "<ToolName>" \
  --position <X>,<Y> \
  --output json

# 4. Wire agent → tool artifact edge
uip maestro flow edge add <FlowName>.flow <agentNodeId> <toolNodeId> \
  --source-port tool --target-port input --output json
```

The CLI auto-generates `bindings[]` entries and rewrites `bindings_v2.json`.

After adding the flow node, you must also:
- Hand-write the per-tool `resource.json` at `<FlowProjectDir>/<inlineAgentProjectId>/resources/<RES_UUID>/resource.json` — **use the exact format from the `uipath-agents` skill: `lowcode/capabilities/inline-in-flow/inline-in-flow.md` § Inline-in-Flow Process Tool resource.json.** The inline-in-flow convention differs from standalone agents: `location: "solution"`, `properties.folderPath: ""`, `referenceKey: ""`. Getting these wrong causes silent runtime failures.
- Set prompts in `agent.json` (system + user messages with `contentTokens` of `type: "simpleText"`)
- Run `uip agent validate --inline-in-flow` to regenerate `.agent-builder/`
- Run `uip solution resource refresh` before upload

For agent.json prompt configuration and solution resource mechanics, see the `uipath-agents` skill (`lowcode/capabilities/inline-in-flow/inline-in-flow.md`).

## JSON Structure

The instance carries only per-instance data (`inputs`, `display`). BPMN type, serviceType, version, and context templates come from the definition in `definitions[]`.

```json
{
  "id": "autonomousAgent1",
  "type": "uipath.agent.autonomous",
  "typeVersion": "1.0.0",
  "display": { "label": "Autonomous Agent" },
  "inputs": {
    "source": "<projectId-uuid>",
    "agentInputVariables": [],
    "agentOutputVariables": [
      { "id": "content", "type": "string" }
    ]
  }
}
```

Notes:

- `inputs.source` — the inline agent's `projectId`; must match the subdirectory name and `agent.json.projectId`. Without it the node form falls back to expecting `inputs.systemPrompt` / `inputs.userPrompt` and reports "System prompt is required" on upload.
- `inputs.systemPrompt` / `inputs.userPrompt` are **never set on the node** — prompts live in `agent.json`.
- **No `model` block on the instance.** The node inherits `model` from `definitions[]`. A stale `model.serviceType` on the instance overrides the inheritance and causes runtime mismatch.

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

> Known caveat: `uip maestro flow validate` rejects flows whose `uipath.agent.autonomous` node lacks `inputs.systemPrompt` / `inputs.userPrompt`, but Studio Web's reference solutions emit them ONLY in the inline agent's `agent.json` (not on the node). If `flow validate` fails on this rule, the flow is still uploadable to Studio Web — `uip solution upload` does not enforce this check. Treat the failure as advisory until the manifest's `required` set is relaxed for inline agents.

## Debug

| Error | Cause | Fix |
| --- | --- | --- |
| `flow validate` reports `systemPrompt` / `userPrompt` required | Known caveat — prompts live in `agent.json`, not on node | Advisory only; flow is uploadable despite this error |
| `inputs.source` UUID does not match any subdirectory | Wrong `--source` value, or folder renamed | Set `--source` to the exact UUID of the inline agent directory |
| Flow runs a different agent than expected | `inputs.source` points to a stale/leftover inline agent dir | Check subdirectory names — only one inline agent dir should correspond to each agent node |
| `Orchestrator.StartAgentJob` error at runtime | Stale `model` block on the instance overrides the inherited definition | Re-add the node with the current CLI (`node add` drops the model block automatically) |
| Studio Web reports "System prompt is required" | Inline agent's `agent.json.messages[]` has empty `content`, OR `.agent-builder/agent.json` is stale | Set prompts in `agent.json`, re-run `uip agent validate --inline-in-flow` — see `uipath-agents` skill |
| Studio Web debug: "Could not find process for tool" | `uip solution resource refresh` not run before upload | Run `uip solution resource refresh <SolutionRoot>` — see `uipath-agents` skill (`lowcode/solution-resources.md`) |
| `bindings_v2.json` is empty after `node add` of an agent-tool process | CLI did not auto-generate bindings | Re-add the agent-tool node via `node add` (which auto-regenerates the file) |

## What NOT to Do

- **Do not set `inputs.systemPrompt` or `inputs.userPrompt` on the flow node** — prompts live in `agent.json`.
- **Do not put a `model` block on the instance** — the node inherits `model` from `definitions[]`.
- **Do not use `model.agentProjectId`** — use `inputs.source`.
- **Do not create `entry-points.json` or `project.uiproj` inside the inline agent directory** — those belong only to standalone agent projects.
- **Do not name the inline agent folder with a human-readable name** — the folder name must be the `projectId` UUID.
- **Do not use `uip agent tool add`** for inline-in-flow agents — hand-author the tool's `resource.json` instead.
- **Do not skip `uip agent validate --inline-in-flow`** after editing `agent.json` or any `resources/*/resource.json`.
