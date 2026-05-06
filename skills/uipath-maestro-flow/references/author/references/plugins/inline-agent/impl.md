# Inline Agent Node — Implementation

This plugin covers **flow-specific** operations for inline agent nodes: adding the node, wiring edges, JSON structure, and flow validation. For agent-side concerns (agent.json configuration, resource.json authoring, solution resources, prompts), see the `uipath-agents` skill — specifically `lowcode/capabilities/inline-in-flow/inline-in-flow.md`.

Node type: `uipath.agent.autonomous`. The agent is bound to a local subdirectory via `inputs.source = <projectId>`. The node's BPMN type and `serviceType` (`Orchestrator.StartInlineAgentJob`) come from the definition in `definitions[]`.

## Prerequisite — Scaffold the Inline Agent

```bash
uip agent init "<FlowProjectDir>" --inline-in-flow --output json
```

This creates `<FlowProjectDir>/<projectId-uuid>/` with:

- `agent.json` — agent definition (model, prompts, schemas)
- `flow-layout.json` — empty `{}`
- `evals/eval-sets/` — empty
- `features/` — empty
- `resources/` — empty (add tool resource files here later)

**Record the returned `ProjectId`** — the flow node's `inputs.source` must match it exactly. The same UUID is also the subdirectory name and the `projectId` field inside `agent.json`.

For agent.json configuration and resource file setup, see the `uipath-agents` skill (`lowcode/agent-definition.md`, `lowcode/capabilities/inline-in-flow/inline-in-flow.md`).

## Configure `agent.json`

`uip agent init --inline-in-flow` scaffolds `agent.json` with empty `messages[].content` by design. Edit `<FlowProjectDir>/<projectId>/agent.json`:

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
- The definition declares `model.source: true`; flow-core hoists that identity field onto the node instance as `inputs.source`
- `model.serviceType` — `Orchestrator.StartInlineAgentJob`
- `model.version` — `v2`

## Adding / Editing

For step-by-step add, delete, and wiring procedures, see [editing-operations.md](../../editing-operations.md). Inline-agent scaffolding uses `uip agent init --inline-in-flow`, but the flow graph is not a Flow CLI carve-out: add the `uipath.agent.autonomous` node, its `inputs.source`, outputs, variables, layout, and edges directly in the `.flow` JSON with `Edit` / `Write`.

### Add the node with Edit / Write

Use `Edit` to add a node instance to `nodes[]`. The instance carries only per-instance data (`inputs`, `outputs`, `display`). BPMN type, serviceType, version, and context templates come from the definition in `definitions[]`. Do not write a node instance `model` block for `uipath.agent.autonomous`: flow-core's `createNodeFromManifest` hoists manifest-declared `source` identity into `inputs.source` and returns a node with no `model`.

```json
{
  "id": "autonomousAgent1",
  "type": "uipath.agent.autonomous",
  "typeVersion": "1.0",
  "display": { "label": "Autonomous Agent" },
  "inputs": {
    "systemPrompt": "You are an agentic assistant.",
    "userPrompt": "What is the current date?",
    "source": "<projectId-uuid>",
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

Also add:

- A `definitions[]` entry copied verbatim from `uip maestro flow registry get uipath.agent.autonomous --output json` (`Data.Node` or the top-level node object, depending on CLI/plugin version). Set `typeVersion` to the copied definition's exact `version`.
- `variables.nodes[]` entries for `autonomousAgent1.output` and `autonomousAgent1.error` with `binding.nodeId = "autonomousAgent1"` and matching `binding.outputId` values.
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

- Hand-write the per-tool `resource.json` at `<FlowProjectDir>/<inlineAgentProjectId>/resources/<RES_UUID>/resource.json`. **Use the exact `resource.json` shape documented in the `uipath-agents` skill: `lowcode/capabilities/process/process.md` § Tool resource.json Shape.** Read that section before writing the file — it defines all required fields. Run `uip solution resource list` + `uip solution resource get` to populate `referenceKey`, `folderPath`, `inputSchema`, and `outputSchema` with real values. Key inline-in-flow notes:
  - Set `id` to `<RES_UUID>` (same value used as the tool node's `model.source` and as the resource directory name).
  - Set `location` based on the discovery `Source` field: `"solution"` when `Source: "Local"`, `"external"` when `Source: "Remote"` (same rule as standalone agents).
  - Set `properties.folderPath` to the **literal folder path from discovery** (e.g., `"Shared/TestRPA"`) — do **not** leave it empty.
  - `inputSchema.properties` must include `"guardrails": { "type": "array" }` alongside the process arguments.
  - A `resource.json` missing `$resourceType: "tool"` or other required fields will not be recognized by `uip agent validate`, resulting in `"resources": 0` and an empty `bindings_v2.json`.
- Set prompts in `agent.json` (system + user messages with `contentTokens` of `type: "simpleText"` and `rawString`)
- Run `uip agent validate --inline-in-flow` after the flow graph edits. For tool-bearing inline agents, first confirm the installed CLI supports `--bindings-target` with `uip agent validate --help`. When supported, pass it to propagate tool bindings to the flow project level:

  ```bash
  uip agent validate "<FlowProjectDir>/<projectId>" --inline-in-flow \
    --bindings-target "<FlowProjectDir>/bindings_v2.json" --output json
  ```

  If the installed CLI does not expose `--bindings-target`, run the supported validation command without that option and treat tool-binding propagation as a CLI capability blocker for tool-bearing inline agents; do not invent or hand-edit `bindings_v2.json`.
  **Verify the output shows `"resources": N` where N > 0.** If it shows `"resources": 0`, the `resource.json` is malformed or missing required fields — fix it and re-run before proceeding.
- Run `uip solution resource refresh` before upload

For agent.json prompt configuration and solution resource mechanics, see the `uipath-agents` skill (`lowcode/capabilities/inline-in-flow/inline-in-flow.md`).

## JSON Structure

The instance carries only per-instance data (`inputs`, `outputs`, `display`). BPMN type, serviceType, version, and context templates come from the definition in `definitions[]`.

```json
{
  "id": "autonomousAgent1",
  "type": "uipath.agent.autonomous",
  "typeVersion": "1.0",
  "display": { "label": "Autonomous Agent" },
  "inputs": {
    "systemPrompt": "You are an agentic assistant.",
    "userPrompt": "What is the current date?",
    "source": "<projectId-uuid>",
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

Notes:

- `inputs.source` — the inline agent's `projectId`; must match the subdirectory name and `agent.json.projectId`. The definition still declares `model.source: true`, but flow-core hoists that identity field onto `inputs.source` for the node instance.
- `inputs.systemPrompt` / `inputs.userPrompt` must be non-empty for current `flow validate`. Treat them as validator placeholders; the canonical inline-agent prompts live in `agent.json`.
- **No `model` block on the inline-agent node instance.** The node inherits serviceType/version/context from `definitions[]`; `source` lives at `inputs.source`. Stale instance fields such as `model.serviceType`, `model.version`, or `model.context` override the inherited definition and can cause runtime mismatch.

## Accessing Output

```javascript
// In a Script node after the agent
const response = $vars.autonomousAgent1.output.content;
return { classification: response };
```

- `$vars.{nodeId}.output.content` — the agent's text response
- `$vars.{nodeId}.error` — error details if the agent fails

## Validate

Validate the inline agent definition, then validate the flow:

```bash
# 1. Validate the inline agent
uip agent validate "<FlowProjectDir>/<projectId>" --inline-in-flow --output json

# For tool-bearing inline agents, when supported by `uip agent validate --help`:
# uip agent validate "<FlowProjectDir>/<projectId>" --inline-in-flow \
#   --bindings-target "<FlowProjectDir>/bindings_v2.json" --output json

# 2. Validate the flow
uip maestro flow validate <FlowName>.flow --output json
```

> Current validator requirement: `uip maestro flow validate` rejects flows whose `uipath.agent.autonomous` node lacks non-empty `inputs.systemPrompt` / `inputs.userPrompt`. Include placeholder values on the flow node, but keep the canonical prompts in the inline agent's `agent.json`.

## Debug

| Error | Cause | Fix |
| --- | --- | --- |
| `flow validate` reports `systemPrompt` / `userPrompt` required | The flow node lacks non-empty validator placeholders, the `inputs.source` UUID is missing, or the inline agent subdirectory cannot be found | Add non-empty `inputs.systemPrompt` / `inputs.userPrompt` placeholders, set `inputs.source` to the inline agent UUID, and verify `<FlowDir>/<projectId>/agent.json` exists |
| `inputs.source` UUID does not match any subdirectory | Wrong source value, or folder renamed | Set `inputs.source` to the exact UUID of the inline agent directory |
| Flow runs a different agent than expected | `inputs.source` points to a stale/leftover inline agent dir | Check subdirectory names — only one inline agent dir should correspond to each agent node |
| `Orchestrator.StartAgentJob` error at runtime | Stale instance `model` fields override the inherited inline-agent definition | Remove the inline-agent node's instance `model` block and keep the registry definition's `model.serviceType: "Orchestrator.StartInlineAgentJob"` in `definitions[]` |
| Studio Web reports "System prompt is required" | Inline agent's `agent.json.messages[]` has empty `content`, OR `.agent-builder/agent.json` is stale | Set prompts in `agent.json`, re-run `uip agent validate --inline-in-flow` — see `uipath-agents` skill |
| Studio Web debug: "Could not find process for tool" | Flow project's `bindings_v2.json` is missing the tool's process binding, so `uip solution resource refresh` never created the solution-level resource | If the installed CLI supports it, re-run `uip agent validate --inline-in-flow --bindings-target <FlowProjectDir>/bindings_v2.json`, then `uip solution resource refresh`, then re-upload; if unsupported, report the CLI capability blocker |
| `bindings_v2.json` is empty or missing tool bindings | Tool bindings were not propagated to the flow project level, or a later tool overwrote the file | Re-run validation with `--bindings-target <FlowProjectDir>/bindings_v2.json` after all flow node and edge edits are complete when supported; otherwise do not hand-edit the generated file |
| Agent tool process cannot resolve at runtime | Missing top-level `bindings[]` entries, mismatched tool-node `model.source` / `resource.json` id, stale solution resources, or missing project-level `bindings_v2.json` | Add the resource bindings from the tool definition, keep the tool node's `model.source` equal to the resource UUID, run `uip agent validate --inline-in-flow` with `--bindings-target` when supported, and run `uip solution resource refresh` |
| `inputs.agentProjectId` unrecognized | Wrong field name | Use `inputs.source` — `agentProjectId` is not valid for inline agents |
| Inline agent rejected by `uip agent validate` | `entry-points.json` or `project.uiproj` present inside the inline agent dir | Delete those files — they belong only to standalone agent projects |
| Folder name is human-readable instead of UUID | Folder renamed after scaffolding | Rename to the original `projectId` UUID — the folder name must match `inputs.source` and the `projectId` field inside `agent.json` |
| Agent runs but returns empty `output.content` | Missing or malformed `contentTokens` in `agent.json` | Rebuild `messages[].contentTokens` using `{ "type": "simpleText", "rawString": "..." }` entries; see `uipath-agents` for detail |

## Repair Recipes

Use direct JSON edits for inline-agent graph repairs. `uip maestro flow node update` does not exist, and the inline-agent graph is not a Flow CLI carve-out. If a bulk scripted rewrite is explicitly approved, use the `python3` heredoc pattern from [editing-operations-json.md — Edit Tooling](../../editing-operations-json.md#edit-tooling); otherwise apply the same transformations through `Edit` / `Write`.

### Replace a definition entry

Use when the `definitions[]` entry for a node type is wrong, stale, or hand-written. The fix is always: re-fetch from the registry, splice into `definitions[]` matching on `nodeType`, then keep the node instance minimal.

```bash
uip maestro flow registry get uipath.agent.autonomous --output json > /tmp/registry_response.json
python3 - <<'PY'
import json
new_def = json.load(open("/tmp/registry_response.json"))["Data"]["Node"]
flow = json.load(open("<FILE>.flow"))
for i, d in enumerate(flow["definitions"]):
    if d.get("nodeType") == "uipath.agent.autonomous":
        flow["definitions"][i] = new_def
        break
for node in flow["nodes"]:
    if node.get("type") == "uipath.agent.autonomous":
        model = node.pop("model", None) or {}
        if isinstance(model.get("source"), str):
            node.setdefault("inputs", {})["source"] = model["source"]
json.dump(flow, open("<FILE>.flow", "w"), indent=2)
PY
uip maestro flow validate <FILE>.flow --output json
```

Same pattern works for any node type — substitute the `nodeType` string in both the `registry get` command and the loop guard.

### Resolve a `[REQUIRED_FIELD] systemPrompt is required` validator error

Current flow validation requires non-empty placeholder prompts on the flow node and uses the inline agent directory referenced by `inputs.source`. Check in order:

1. **UUID at `inputs.source`** — the `projectId` UUID must be set at `inputs.source`. Diagnose:

    ```bash
    python3 - <<'PY'
    import json
    flow = json.load(open("<FILE>.flow"))
    for node in flow["nodes"]:
        if node.get("type") == "uipath.agent.autonomous":
            print("inputs.source:", node.get("inputs", {}).get("source"))
            print("model.source: ", node.get("model", {}).get("source"))
    PY
    ```

    If a stale flow has the UUID at `model.source`, move it to `inputs.source` and remove the instance `model` block:

    ```bash
    python3 - <<'PY'
    import json
    flow = json.load(open("<FILE>.flow"))
    for node in flow["nodes"]:
        if node.get("type") == "uipath.agent.autonomous":
            inputs = node.setdefault("inputs", {})
            model = node.pop("model", None) or {}
            uuid = model.get("source")
            if uuid:
                inputs["source"] = uuid
    json.dump(flow, open("<FILE>.flow", "w"), indent=2)
    PY
    ```

2. **Subdirectory** — confirm `<FlowDir>/<projectId>/` exists and contains `agent.json`. If not, re-run `uip agent init "<FlowDir>" --inline-in-flow --output json` and bind the returned `ProjectId` through `inputs.source`.

3. **Prompts in `agent.json`** — set `messages[0].content` (system) and `messages[1].content` (user) to real prompts before validate. Rebuild `messages[].contentTokens` to match — `[{ "type": "simpleText", "rawString": "<your prompt text>" }]` per message.

4. **Validator placeholders on the flow node** — add non-empty `inputs.systemPrompt` and `inputs.userPrompt` placeholders if they are missing. These are for current `flow validate`; keep the canonical prompt text in `agent.json`.

## What NOT to Do

- **Do not use Flow CLI `node add`, `edge add`, or `variable` commands for inline-agent graph edits** — inline-agent node, edge, variable, layout, and tool-resource node changes are non-carve-out structural `.flow` mutations and must be authored directly with `Edit` / `Write`.
- **Do not treat `inputs.systemPrompt` / `inputs.userPrompt` as canonical prompts** — current validation requires non-empty placeholders on the flow node, but prompts live in `agent.json`.
- **Do not put a `model` block on the inline-agent node instance** — the node inherits serviceType/version/context from `definitions[]`; the inline-agent source lives at `inputs.source`.
- **Do not use `model.agentProjectId`, `inputs.agentProjectId`, or `model.source`** — use `inputs.source` for the `uipath.agent.autonomous` node.
- **Do not create `entry-points.json` or `project.uiproj` inside the inline agent directory** — those belong only to standalone agent projects.
- **Do not name the inline agent folder with a human-readable name** — the folder name must be the `projectId` UUID.
- **Do not use `uip agent tool add`** for inline-in-flow agents — hand-author the tool's `resource.json` instead.
- **Do not skip `uip agent validate --inline-in-flow`** after editing `agent.json` or any `resources/*/resource.json`; for tool-bearing inline agents, use `--bindings-target <FlowProjectDir>/bindings_v2.json` when the installed CLI supports it.
