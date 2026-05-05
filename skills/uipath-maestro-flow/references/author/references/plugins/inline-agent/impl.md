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

The CLI auto-generates `bindings[]` entries in the `.flow` file when nodes are added via `node add`.

After adding the flow node, you must also:
- Hand-write the per-tool `resource.json` at `<FlowProjectDir>/<inlineAgentProjectId>/resources/<RES_UUID>/resource.json`. **You MUST follow the exact `resource.json` shape documented in the `uipath-agents` skill: `lowcode/capabilities/process/process.md` § Tool resource.json Shape.** Read that section before writing the file — it defines all required fields. Run `uip solution resource list` + `uip solution resource get` to populate `referenceKey`, `folderPath`, `inputSchema`, and `outputSchema` with real values. Key inline-in-flow notes:
  - Set `id` to the `<RES_UUID>` (same value used as `--source` when adding the tool node and as the resource directory name).
  - Set `location` based on the discovery `Source` field: `"solution"` when `Source: "Local"`, `"external"` when `Source: "Remote"` (same rule as standalone agents).
  - Set `properties.folderPath` to the **literal folder path from discovery** (e.g., `"Shared/TestRPA"`) — do **not** leave it empty.
  - `inputSchema.properties` must include `"guardrails": { "type": "array" }` alongside the process arguments.
  - A `resource.json` missing `$resourceType: "tool"` or other required fields will not be recognized by `uip agent validate`, resulting in `"resources": 0` and an empty `bindings_v2.json`.
- Set prompts in `agent.json` (system + user messages with `contentTokens` of `type: "simpleText"` and `rawString`)
- Run `uip agent validate --inline-in-flow` with `--bindings-target` pointing to the flow project's `bindings_v2.json` to regenerate `.agent-builder/` **and** propagate tool bindings to the flow project level:
  ```bash
  uip agent validate "<FlowProjectDir>/<projectId>" --inline-in-flow \
    --bindings-target "<FlowProjectDir>/bindings_v2.json" --output json
  ```
  **Without `--bindings-target`, the inline agent's tool bindings stay in `.agent-builder/bindings.json` only — `uip solution resource refresh` will NOT discover them** because it only reads project-level `bindings_v2.json` files.
  **Verify the output shows `"resources": N` where N > 0.** If it shows `"resources": 0`, the `resource.json` is malformed or missing required fields — fix it and re-run before proceeding.
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

Validate the inline agent definition, propagate tool bindings, then validate the flow:

```bash
# 1. Validate and propagate tool bindings
uip agent validate "<FlowProjectDir>/<projectId>" --inline-in-flow \
  --bindings-target "<FlowProjectDir>/bindings_v2.json" --output json

# 2. Validate the flow
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
| Studio Web debug: "Could not find process for tool" | Flow project's `bindings_v2.json` is missing the tool's process binding, so `uip solution resource refresh` never created the solution-level resource | Re-run `uip agent validate --inline-in-flow --bindings-target <FlowProjectDir>/bindings_v2.json`, then `uip solution resource refresh`, then re-upload |
| `bindings_v2.json` is empty or missing tool bindings | `uip agent validate --inline-in-flow` was run without `--bindings-target`, so bindings were only written to `.agent-builder/bindings.json` (not the flow project level) | Re-run with `--bindings-target <FlowProjectDir>/bindings_v2.json` |

## What NOT to Do

- **Do not set `inputs.systemPrompt` or `inputs.userPrompt` on the flow node** — prompts live in `agent.json`.
- **Do not put a `model` block on the instance** — the node inherits `model` from `definitions[]`.
- **Do not use `model.agentProjectId`** — use `inputs.source`.
- **Do not create `entry-points.json` or `project.uiproj` inside the inline agent directory** — those belong only to standalone agent projects.
- **Do not name the inline agent folder with a human-readable name** — the folder name must be the `projectId` UUID.
- **Do not use `uip agent tool add`** for inline-in-flow agents — hand-author the tool's `resource.json` instead.
- **Do not skip `uip agent validate --inline-in-flow`** after editing `agent.json` or any `resources/*/resource.json`.
