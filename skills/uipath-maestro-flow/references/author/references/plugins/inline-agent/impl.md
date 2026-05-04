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

**Record the returned `ProjectId`** — the flow node's `--source` flag (or `inputs.source` field for direct-JSON authoring) must match it exactly. The same UUID is also the subdirectory name and the `projectId` field inside `agent.json`.

For agent.json configuration and resource file setup, see the `uipath-agents` skill (`lowcode/agent-definition.md`, `lowcode/capabilities/inline-in-flow/inline-in-flow.md`).

## Configure `agent.json`

`uip agent init --inline-in-flow` scaffolds `agent.json` with empty `messages[].content` by design — you must populate prompts before `flow validate` passes. Edit `<FlowProjectDir>/<projectId>/agent.json`:

1. Set `settings.model` (e.g., `"anthropic.claude-sonnet-4-6"`, `"gpt-4o-2024-11-20"`)
2. Set `settings.temperature`, `settings.maxTokens`, `settings.maxIterations`
3. Write system prompt in `messages[0].content` (must be non-empty) and rebuild `messages[0].contentTokens`
4. Write user prompt in `messages[1].content` (must be non-empty) and rebuild `messages[1].contentTokens`
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

`--source` populates the inline-agent's `projectId` UUID on the node. `flow validate` accepts the UUID at either `inputs.source` or `model.source`; the skill convention is `inputs.source` (see [planning.md](planning.md) and [shared/file-format.md](../../../../shared/file-format.md)). The CLI and the current canvas write `model.source` today (per the workbench manifest); a unification to `inputs.source` is planned as a follow-up. **For directly hand-authored flows, write `inputs.source`** to match the skill convention. The command automatically:

- Adds the node to `nodes` with a generated `id`
- Adds the definition to `definitions` (if not already present)
- The definition carries `model.serviceType: "Orchestrator.StartInlineAgentJob"` — the runtime hydrates BPMN type and serviceType from the definition at emit time

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

The inline-agent node carries `inputs`, `outputs`, and `display`. The agent's `projectId` UUID lives at `inputs.source` per skill convention (`flow validate` also accepts `model.source`, which the CLI and current canvas write). Leave the prompt fields empty when authoring directly; the canvas / `flow validate` hydrates `inputs.systemPrompt` / `inputs.userPrompt` from the colocated `<projectId>/agent.json.messages[]` on load.

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

- `inputs.source` — the inline agent's `projectId` UUID; must match the subdirectory name and the `projectId` field inside `agent.json`. This is the skill convention; `flow validate` also accepts `model.source`, which the CLI and current canvas write. The validator hydrates prompts from the colocated `<projectId>/agent.json` at validate time.
- `inputs.systemPrompt` / `inputs.userPrompt` stay absent in directly-authored `.flow` files. The canvas writes them as a storage-backed mirror of `agent.json.messages[]`, but the runtime reads from `agent.json`, not the node. For direct authoring, populate `agent.json.messages[]` and let hydration fill the mirror.
- **No full `model` block on the instance.** BPMN type, `serviceType`, `version`, and per-instance `context` templates all come from the definition in `definitions[]` (copied verbatim from the `uip maestro flow registry get` output). The CLI's `--source` flag and the current canvas write a minimal `model: { source: <uuid> }` shape (matching the workbench manifest declaration); the validator accepts it. New direct-JSON authoring should write `inputs.source` to match the skill convention.
- Inline agents do not use process-style bindings (`resourceKey`, `folderPath`) — those are for resource nodes (rpa, agentic-process, etc.).

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

## Debug

| Error | Cause | Fix |
| --- | --- | --- |
| `flow validate` returns `[REQUIRED_FIELD] "systemPrompt" is required` and `[REQUIRED_FIELD] "userPrompt" is required` on an inline-agent node | Validator's hydration step short-circuited — the `projectId` UUID source key is missing entirely, or the `<projectId>/` directory doesn't exist, or `agent.json.messages[]` has empty `content` | Verify the UUID is set at `inputs.source` (skill convention) or `model.source` (also accepted) and matches the colocated subdirectory; verify `<FlowDir>/<projectId>/agent.json` exists; verify `agent.json.messages[]` has non-empty `content` for both `system` and `user` roles. **Do not** insert placeholder strings into `inputs.systemPrompt`/`userPrompt` — they round-trip into `agent.json` via the storage bridge and corrupt the agent definition. See [Resolve a `[REQUIRED_FIELD] systemPrompt is required` validator error](#resolve-a-required_field-systemprompt-is-required-validator-error) for the diagnosis recipe |
| `inputs.source` UUID does not match any subdirectory | Wrong `--source` value, or folder renamed | Set `--source` to the exact UUID of the inline agent directory |
| Flow runs a different agent than expected | `inputs.source` points to a stale/leftover inline agent dir | Check subdirectory names — only one inline agent dir should correspond to each agent node |
| `Orchestrator.StartAgentJob` error at runtime | Wrong definition (published-agent definition attached to inline-agent node) | Replace the `definitions[]` entry with the one from `uip maestro flow registry get uipath.agent.autonomous --output json` — it carries `model.serviceType: "Orchestrator.StartInlineAgentJob"`. See [Replace a definition entry](#replace-a-definition-entry) for the exact mechanic |
| Prompts authored on `inputs.systemPrompt` / `inputs.userPrompt` get clobbered on next save | Those fields are a canvas-side mirror of `agent.json.messages[]` — `inputsToStorage` rewrites `agent.json` from the node, then `storageToInputs` rewrites the node from `agent.json` on next load | Author prompts in `agent.json.messages[]`; leave `inputs` empty for direct authoring |
| Studio Web reports "System prompt is required" | Inline agent's `agent.json.messages[]` has empty `content`, OR `.agent-builder/agent.json` is stale | Set prompts in `agent.json`, re-run `uip agent validate --inline-in-flow` — see `uipath-agents` skill |
| Studio Web debug: "Could not find process for tool" | `uip solution resource refresh` not run before upload | Run `uip solution resource refresh <SolutionRoot>` — see `uipath-agents` skill (`lowcode/solution-resources.md`) |
| `bindings_v2.json` is empty after `node add` of an agent-tool process | CLI did not auto-generate bindings | Re-add the agent-tool node via `node add` (which auto-regenerates the file) |
| `inputs.agentProjectId` unrecognized | Wrong field name | Use `inputs.source` — `agentProjectId` is not valid for inline agents |
| Inline agent rejected by `uip agent validate` | `entry-points.json` or `project.uiproj` present inside the inline agent dir | Delete those files — they belong only to standalone agent projects |
| Folder name is human-readable instead of UUID | Folder renamed after scaffolding | Rename to the original `projectId` UUID — the folder name must match `inputs.source` and the `projectId` field inside `agent.json` |
| Agent runs but returns empty `output.content` | Missing or malformed `contentTokens` in `agent.json` | Rebuild `messages[].contentTokens` using `{ "type": "simpleText", "rawString": "..." }` entries; see `uipath-agents` for detail |

## Repair Recipes

Direct JSON repairs for scenarios that don't have a CLI shortcut (`uip maestro flow node update` does not exist — see [editing-operations-cli.md § Update node inputs](../../editing-operations-cli.md#update-node-inputs-expression-script-body-label-etc)). Recipes use the `python3` heredoc pattern from [editing-operations-json.md — Edit Tooling](../../editing-operations-json.md#edit-tooling); copy verbatim and substitute `<FILE>.flow`.

### Replace a definition entry

Use when the `definitions[]` entry for a node type is wrong, stale, or hand-written. The fix is always: re-fetch from the registry, splice into `definitions[]` matching on `nodeType`.

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
json.dump(flow, open("<FILE>.flow", "w"), indent=2)
PY
uip maestro flow validate <FILE>.flow --output json
```

Same pattern works for any node type — substitute the `nodeType` string in both the `registry get` command and the loop guard.

### Resolve a `[REQUIRED_FIELD] systemPrompt is required` validator error

The validator hydrates prompts from `<FlowDir>/<projectId>/agent.json` at validate time. When this error fires, hydration short-circuited. Check in order:

1. **UUID source key** — the `projectId` UUID must be set at `inputs.source` (skill convention) or `model.source` (the location used by the CLI and the current canvas):

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

    If neither key is set, add `inputs.source`:

    ```bash
    python3 - <<'PY'
    import json
    flow = json.load(open("<FILE>.flow"))
    for node in flow["nodes"]:
        if node.get("type") == "uipath.agent.autonomous":
            node.setdefault("inputs", {}).setdefault("source", "<projectId-uuid>")
    json.dump(flow, open("<FILE>.flow", "w"), indent=2)
    PY
    ```

    Substitute `<projectId-uuid>` with the UUID returned by `uip agent init --inline-in-flow`. If only `model.source` is set, leave it — the validator accepts it. To align with the skill convention, move the value to `inputs.source`:

    ```bash
    python3 - <<'PY'
    import json
    flow = json.load(open("<FILE>.flow"))
    for node in flow["nodes"]:
        if node.get("type") == "uipath.agent.autonomous":
            model = node.get("model") or {}
            uuid = model.pop("source", None)
            if uuid:
                node.setdefault("inputs", {})["source"] = uuid
                if not model:
                    node.pop("model", None)
    json.dump(flow, open("<FILE>.flow", "w"), indent=2)
    PY
    ```

2. **Subdirectory** — confirm `<FlowDir>/<projectId>/` exists and contains `agent.json`. If not, re-run `uip agent init "<FlowDir>" --inline-in-flow --output json`.

3. **Prompts in `agent.json`** — `agent init --inline-in-flow` scaffolds `agent.json` with empty `messages[].content` by design. Edit `messages[0].content` (system) and `messages[1].content` (user) to real prompts before validate. Rebuild `messages[].contentTokens` to match — `[{ "type": "simpleText", "rawString": "<your prompt text>" }]` per message. Validation passes once both `content` strings are non-empty.

> **Do not** patch `inputs.systemPrompt` / `inputs.userPrompt` on the node. The storage bridge writes node `inputs` back into `agent.json.messages[]` on every canvas save — placeholders inserted on the node corrupt the agent definition on the next round-trip.

## What NOT to Do

- **Do not author prompts on `inputs.systemPrompt` / `inputs.userPrompt`** — those fields are a canvas-side mirror of `agent.json.messages[]`. The storage bridge (`inputsToStorage` / `storageToInputs`) round-trips between the two; whatever you write on the node will overwrite `agent.json.messages[]` on next save, then be overwritten by `agent.json` on next load. Author prompts in `agent.json.messages[]` only.
- **Do not write the `projectId` UUID to a custom or invented key** — set `inputs.source` per skill convention. `model.source` is also accepted by the validator (the CLI and current canvas write there); a unification refactor is tracked separately.
- **Do not use `inputs.agentProjectId` or `model.agentProjectId`** — use `inputs.source`.
- **Do not put a full `model` block on the instance** — `serviceType`, BPMN type, and context live in the definition only (copied from the registry). A published-agent node's definition uses `Orchestrator.StartAgentJob`; an inline-agent node must use the `uipath.agent.autonomous` definition with `Orchestrator.StartInlineAgentJob`. The CLI and current canvas write a minimal `model: { source: <uuid> }` shape (per the workbench manifest); for direct-JSON authoring, prefer `inputs.source`.
- **Do not create `entry-points.json` or `project.uiproj` inside the inline agent directory** — those belong only to standalone agent projects.
- **Do not name the inline agent folder with a human-readable name** — the folder name must be the `projectId` UUID.
- **Do not use `uip agent tool add`** for inline-in-flow agents — hand-author the tool's `resource.json` instead.
- **Do not skip `uip agent validate --inline-in-flow`** after editing `agent.json` or any `resources/*/resource.json`.
