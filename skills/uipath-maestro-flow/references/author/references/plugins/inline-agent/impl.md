# Inline Agent Node — Implementation

This plugin covers **flow-specific** operations for inline agent nodes: adding the node, wiring edges, JSON structure, and flow validation. For agent-side concerns (agent.json configuration, resource.json authoring, solution resources, prompts), see the `uipath-agents` skill — specifically `lowcode/capabilities/inline-in-flow/inline-in-flow.md`.

Node type: `uipath.agent.autonomous`. The agent is bound to a local subdirectory via `inputs.source = <projectId>`. The node's BPMN type and `serviceType` (`Orchestrator.StartInlineAgentJob`) come from the definition in `definitions[]`.

For coded (Python) agents, use the [`agent`](../agent/impl.md) plugin (`uipath.core.agent.{key}`) — inline agents are low-code only.

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

`uip agent init --inline-in-flow` scaffolds `agent.json` with `settings.model: "gpt-4o-2024-11-20"` (stale) and empty `messages[].content` by design. **Both are placeholders — override them.** A scaffolded inline agent left on the default model with toy prompts is the single biggest quality gap a customer ships. Edit `<FlowProjectDir>/<projectId>/agent.json`:

1. **Override the model** — never ship `gpt-4o-2024-11-20`. Discover the tenant's models with `uip agent model list` and pick the newest GA model for the task; set `settings.maxTokens` ≤ its cap. Discovery command, GA filter, and task→model mapping: the `uipath-agents` skill's [`model-selection-guide.md`](../../../../../../uipath-agents/references/lowcode/model-selection-guide.md).
2. Set `settings.temperature` (0 for extraction/classification/judgment) and `settings.maxIterations` (default 25; lower for single-shot).
3. **Write a real system prompt** in `messages[0].content` — bounded role, per-tool call/stop criteria, output contract, grounding. Skeleton + worked example: [`agent-prompting-guide.md`](../../../../../../uipath-agents/references/lowcode/agent-prompting-guide.md).
4. Write the user prompt in `messages[1].content`.
5. **Declare a typed `outputSchema`** — not a bare `content` string — so downstream nodes can consume the result.

After editing `content`, rebuild the matching `messages[].contentTokens` (`type: "simpleText"` / `type: "variable"`). Token mechanics are flow-specific — see § Wiring Flow Variables into Agent Prompts below; for prompt-quality structure see `agent-prompting-guide.md`.

> **Source of truth.** The prompt skeleton, the production-field checklist (`outputSchema` / `temperature` / `maxIterations` / `guardrails`), the model-discovery command, and the worked example all live in the `uipath-agents` guides linked above — this skill points at them rather than copying, to avoid cross-skill drift. The obligations in steps 1–5 are the build-time minimum; the *how* is one click away.

## Wiring Flow Variables into Agent Prompts

Inline-agent prompts reference upstream flow nodes **directly** via `{{ $vars.<flowNodeId>.output[.<field>] }}` tokens in `agent.json messages[].content`. No agent-side input bridge, no `inputSchema` slot, no `agentInputVariables[]` binding.

| Where | What | Example |
| --- | --- | --- |
| `agent.json` `messages[].content` | Token referencing an upstream flow node's output | `"Email subject: {{ $vars.emailReceived1.output.subject }}"` |
| `agent.json` `messages[].contentTokens[]` | One `{ "type": "variable", "rawString": " $vars.<flowNodeId>.output[.<field>] " }` per `{{ ... }}` token in `content`. **`rawString` must include leading and trailing space** to match the spaced-brace form. | `{ "type": "variable", "rawString": " $vars.emailReceived1.output.subject " }` |
| Flow node `inputs.agentInputVariables` | `[]` for prompt-only flow-data references. | `"agentInputVariables": []` |
| `agent.json` `inputSchema.properties` | `{}` for prompt-only flow-data references. | `"inputSchema": { "type": "object", "properties": {} }` |

`<flowNodeId>` must exactly match a node `id` in the `.flow` file, with an edge path reaching the inline-agent node. See [../../../../shared/node-output-wiring.md](../../../../shared/node-output-wiring.md) for the full expression contract.

### Worked example — wire an email-trigger payload into the agent prompt

Flow node (excerpt):

```json
{
  "id": "autonomousAgent1",
  "type": "uipath.agent.autonomous",
  "inputs": {
    "systemPrompt": "Triage the inbound email.",
    "userPrompt": "Process the inbound email payload.",
    "source": "<projectId-uuid>",
    "agentInputVariables": [],
    "agentOutputVariables": [{ "id": "content", "type": "string" }]
  }
}
```

Matching `agent.json` (excerpt):

```json
{
  "settings": { "model": "anthropic.claude-sonnet-4-6", "temperature": 0, "maxTokens": 4096, "maxIterations": 10 },
  "inputSchema": {
    "type": "object",
    "properties": {}
  },
  "outputSchema": {
    "type": "object",
    "properties": {
      "category":  { "type": "string",  "description": "billing | technical | sales | other" },
      "priority":  { "type": "string",  "description": "low | medium | high | urgent" },
      "needsHuman":{ "type": "boolean", "description": "true if the email requires human review" }
    },
    "required": ["category", "priority", "needsHuman"]
  },
  "messages": [
    {
      "role": "system",
      "content": "You are a support-email triage classifier for a SaaS product. Classify each inbound email; do not reply to the customer. category MUST be one of billing, technical, sales, other. Set needsHuman=true for legal threats, churn risk, or anything outside those categories. Never invent customer details not present in the email. If the email is empty or unintelligible, set category=\"other\" and needsHuman=true.",
      "contentTokens": [{ "type": "simpleText", "rawString": "You are a support-email triage classifier for a SaaS product. Classify each inbound email; do not reply to the customer. category MUST be one of billing, technical, sales, other. Set needsHuman=true for legal threats, churn risk, or anything outside those categories. Never invent customer details not present in the email. If the email is empty or unintelligible, set category=\"other\" and needsHuman=true." }]
    },
    {
      "role": "user",
      "content": "From {{ $vars.emailReceived1.output.from }}\nSubject: {{ $vars.emailReceived1.output.subject }}\n\n{{ $vars.emailReceived1.output.body }}",
      "contentTokens": [
        { "type": "simpleText", "rawString": "From " },
        { "type": "variable",   "rawString": " $vars.emailReceived1.output.from " },
        { "type": "simpleText", "rawString": "\nSubject: " },
        { "type": "variable",   "rawString": " $vars.emailReceived1.output.subject " },
        { "type": "simpleText", "rawString": "\n\n" },
        { "type": "variable",   "rawString": " $vars.emailReceived1.output.body " }
      ]
    }
  ]
}
```

The system prompt here is a real one (bounded role, output contract, grounding, uncertainty rule — structured per `agent-prompting-guide.md`) and `outputSchema` carries typed fields — not a bare `content` blob. The flow-node `inputs.systemPrompt` / `inputs.userPrompt` are short, generic validator placeholders — **do not copy the templated `agent.json` prompt with `{{ $vars.X }}` tokens here**. The contract: every `{{ $vars.<flowNodeId>.output[.<field>] }}` token in `agent.json content` has a matching `{ type: "variable", rawString: " $vars.<flowNodeId>.output[.<field>] " }` entry in the same message's `contentTokens[]` (leading and trailing spaces inside `rawString`).

### When the source field name is unknown at authoring time

Some upstream nodes (notably connector triggers like email-received) only expose their full output shape after a real run — `subject`, `from`, `body` are not knowable from the registry definition alone. In that case:

1. Write the prompt against your **best guess** of the upstream node's output paths based on the connector's documented output schema (e.g., `{{ $vars.emailReceived1.output.subject }}`).
2. Surface the assumption to the user with `AskUserQuestion` — list the referenced paths and ask the user to correct any wrong fields before they run or upload the flow. Do not invent field names silently.
3. After the first real run, the author can verify the actual output paths and update the prompt tokens (and matching `contentTokens[].rawString` mirrors).

### Anti-patterns

- **Never write `{{input.<id>}}` (or any `input.X` form) in `agent.json` prompts.** Use `{{ $vars.<flowNodeId>.output[.<field>] }}` referencing the upstream flow node directly.
- **Never write `{{plainName}}` (no prefix) in `agent.json` prompts.** Use the `{{ $vars.<flowNodeId>.output[.<field>] }}` form.
- **Never omit the leading and trailing space inside `contentTokens[].rawString` for variable tokens.** `rawString` is `" $vars.X "`, matching the `{{ $vars.X }}` spaced-brace form in `content`.
- **Never copy `{{ $vars.X }}` tokens into the flow-node `inputs.systemPrompt` / `inputs.userPrompt`.** Those fields are validator placeholders — keep them as short, generic strings. Canvas tokens belong in `agent.json messages[].content` only.
- **Never populate `agentInputVariables[]` on the flow node for prompt-data passing.** Use `{{ $vars.<flowNodeId>.output[.<field>] }}` in `agent.json messages[].content` instead. For prompt-only flow-data references, set `inputs.agentInputVariables: []` on the flow node.
- **Never declare an `inputSchema.properties.<id>` slot for prompt-data wiring.** For prompt-only flow-data references, leave `inputSchema.properties` as `{}`.

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
- A placeholder `layout.nodes.<agentNodeId>` entry; `flow format` owns the final position.

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

## Adding an External Tool Node

Inline tool nodes come in four kinds. Discovery, node-add, edge-wire, and `resource.json` authoring are identical across kinds — only the registry-search prefix on the flow side and the `type` field in `resource.json` differ.

| Kind | Registry-search prefix | `resource.json.type` | What it calls |
|------|------------------------|----------------------|---------------|
| RPA process | `uipath.agent.resource.tool.process` | `process` | RPA workflow (XAML / coded) |
| Agent | `uipath.agent.resource.tool.agent` | `agent` | Low-code or coded agent |
| API workflow | `uipath.agent.resource.tool.api` | `api` | Coded API workflow |
| Process Orchestration | `uipath.agent.resource.tool.processorchestration` | `processOrchestration` | Agentic / orchestrated process |

Discover the tool via the flow registry, then add the tool resource node directly in the `.flow` JSON. Generate a resource UUID and use it as both the tool node's `inputs.source` and the `resource.json` directory/id.

```bash
# 1. Search the registry, picking the prefix from the matrix above
uip maestro flow registry search "<prefix>" --output json

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
  "inputs": {
    "source": "<RES_UUID>"
  }
}
```

The definition declares `model.source: true`; flow-core hoists that identity field onto the node instance as `inputs.source` (same hoisting rule as `uipath.agent.autonomous`). No instance `model` block is written.

Also add:

- The tool node definition copied verbatim from `registry get`.
- Top-level `bindings[]` entries for the process resource, using the definition's `model.bindings.resourceKey` and `model.bindings.values[]` (`name`, `folderPath`, etc.). See [editing-operations-json.md — Resource nodes](../../editing-operations-json.md#add-a-node).
- A placeholder `layout.nodes.<toolNodeId>` entry.
- The artifact edge from the inline agent's `tool` port to the tool node's `input` port, as shown above.

After adding the tool node, you must also:

- Hand-write the per-tool `resource.json` at `<FlowProjectDir>/<inlineAgentProjectId>/resources/<RES_UUID>/resource.json`. **Use the exact `resource.json` shape documented in the `uipath-agents` skill: `lowcode/capabilities/process/process.md` § Tool resource.json Shape.** Read that section before writing the file — it defines all required fields. The subtype is selected by the `type` field (`process` | `agent` | `api` | `processOrchestration`) — see § Subtypes in `process.md`. For RPA the schema uses raw .NET arrays (Template A in `solution-files.md`); for Agent / API / Process Orchestration it uses JSON Schema V2 (Template B). Run `uip solution resource list` + `uip solution resource get` to populate `referenceKey`, `folderPath`, `inputSchema`, and `outputSchema` with real values. Key inline-in-flow notes:
  - Set `id` to `<RES_UUID>` (same value used as the tool node's `inputs.source` and as the resource directory name).
  - Set `location` based on the discovery `Source` field: `"solution"` when `Source: "Local"`, `"external"` when `Source: "Remote"` (same rule as standalone agents).
  - Set `properties.folderPath` to the **literal folder path from discovery** (e.g., `"Shared/TestRPA"`) — do **not** leave it empty.
  - `inputSchema.properties` must include `"guardrails": { "type": "array" }` alongside the process arguments.
  - A `resource.json` missing `$resourceType: "tool"` or other required fields will not be recognized by `uip agent validate` (it reports `"resources": 0`); the subsequent `uip agent migrate` will then write an empty `bindings_v2.json`.
- Set prompts in `agent.json` (system + user messages with `contentTokens` of `type: "simpleText"` and `rawString`)
- Run `uip agent validate --inline-in-flow` after the flow graph edits to check the agent schema. Then run `uip agent migrate --inline-in-flow` to apply the migration and regenerate `.agent-builder/`; for tool-bearing inline agents, pass `--bindings-target <FlowProjectDir>/bindings_v2.json` on the migrate call to propagate tool bindings to the flow project level:

  ```bash
  uip agent validate "<FlowProjectDir>/<projectId>" --inline-in-flow --output json
  uip agent migrate "<FlowProjectDir>/<projectId>" --inline-in-flow \
    --bindings-target "<FlowProjectDir>/bindings_v2.json" --output json
  ```

  Do not hand-edit `bindings_v2.json` — it is regenerated by `uip agent migrate`.
  **Verify both validate and migrate report `"resources": N` where N > 0.** If either shows `"resources": 0`, the `resource.json` is malformed or missing required fields — fix it and re-run before proceeding.
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
- `inputs.agentInputVariables` is `[]` for prompt-only flow-data references — which covers the common case. The canvas does not read this array when resolving prompt tokens; flow values flow into prompts directly via `{{ $vars.<flowNodeId>.output[.<field>] }}` in `agent.json messages[].content` (see § Wiring Flow Variables into Agent Prompts above). Populate `agentInputVariables[]` only for non-prompt typed-schema uses.
- **No `model` block on the inline-agent node instance.** The node inherits serviceType/version/context from `definitions[]`; `source` lives at `inputs.source`. Stale instance fields such as `model.serviceType`, `model.version`, or `model.context` override the inherited definition and can cause runtime mismatch.

## Accessing Output

```javascript
// In a Script node after the agent
const response = $vars.autonomousAgent1.output.content;
return { classification: response };
```

- `$vars.{nodeId}.output.content` — the agent's text response
- `$vars.{nodeId}.error` — error details if the agent fails

## Validate and Migrate

Validate the inline agent (read-only check), migrate it (writes `.agent-builder/` and, for tool-bearing agents, propagates bindings into the flow project's `bindings_v2.json`), then validate the flow:

```bash
# 1. Validate the inline agent (read-only schema check)
uip agent validate "<FlowProjectDir>/<projectId>" --inline-in-flow --output json

# 2. Migrate the inline agent (writes .agent-builder/ and applies migrations)
uip agent migrate "<FlowProjectDir>/<projectId>" --inline-in-flow --output json

# 2b. For tool-bearing inline agents, migrate with --bindings-target to propagate tool bindings:
uip agent migrate "<FlowProjectDir>/<projectId>" --inline-in-flow \
  --bindings-target "<FlowProjectDir>/bindings_v2.json" --output json

# 3. Validate the flow
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
| Studio Web reports "System prompt is required" | Inline agent's `agent.json.messages[]` has empty `content`, OR `.agent-builder/agent.json` is stale | Set prompts in `agent.json`, re-run `uip agent validate --inline-in-flow` to check, then `uip agent migrate --inline-in-flow` to regenerate `.agent-builder/agent.json` — see `uipath-agents` skill |
| Studio Web debug: "Could not find process for tool" | Flow project's `bindings_v2.json` is missing the tool's process binding, so `uip solution resource refresh` never created the solution-level resource | Re-run `uip agent validate --inline-in-flow` to check schema, then `uip agent migrate --inline-in-flow --bindings-target <FlowProjectDir>/bindings_v2.json` to propagate bindings, then `uip solution resource refresh`, then re-upload |
| `bindings_v2.json` is empty or missing tool bindings | Tool bindings were not propagated to the flow project level, or a later tool overwrote the file | Re-run `uip agent migrate --inline-in-flow --bindings-target <FlowProjectDir>/bindings_v2.json` after all flow node and edge edits are complete. Migrate is the verb that writes the file — do not hand-edit it |
| Agent tool (process / agent / api / processOrchestration) cannot resolve at runtime | Missing top-level `bindings[]` entries, mismatched tool-node `inputs.source` / `resource.json` id, stale solution resources, or missing project-level `bindings_v2.json` | Add the resource bindings from the tool definition, keep the tool node's `inputs.source` equal to the resource UUID, run `uip agent validate --inline-in-flow` to check, then `uip agent migrate --inline-in-flow --bindings-target <FlowProjectDir>/bindings_v2.json` to write bindings, then run `uip solution resource refresh` |
| `inputs.agentProjectId` unrecognized | Wrong field name | Use `inputs.source` — `agentProjectId` is not valid for inline agents |
| Inline agent rejected by `uip agent validate` | `entry-points.json` or `project.uiproj` present inside the inline agent dir | Delete those files — they belong only to standalone agent projects |
| Folder name is human-readable instead of UUID | Folder renamed after scaffolding | Rename to the original `projectId` UUID — the folder name must match `inputs.source` and the `projectId` field inside `agent.json` |
| Agent runs but returns empty `output.content` | Missing or malformed `contentTokens` in `agent.json` | Rebuild `messages[].contentTokens` using `{ "type": "simpleText", "rawString": "..." }` entries; see `uipath-agents` for detail |
| `Prompt references "$vars.<id>" but that variable is not available in this scope` | Token written as `{{input.<id>}}` or `{{<id>}}` | Rewrite to `{{ $vars.<flowNodeId>.output[.<field>] }}` and mirror in `contentTokens[]` as `{ "type": "variable", "rawString": " $vars.<flowNodeId>.output[.<field>] " }`. See § Wiring Flow Variables into Agent Prompts. |
| `uip agent validate` fails with `Expected " $vars.X " but got "$vars.X"` | Variable `contentToken` `rawString` missing leading/trailing space | Add one leading and one trailing space inside `rawString`. The `content` field is `{{ $vars.X }}` (spaced braces); `rawString` is `" $vars.X "` (spaced). |
| Agent prompt receives literal `{{X}}` text instead of flow data | Bare `{{plainName}}` (no `$vars.`), or `<flowNodeId>` typo not matching any node `id` | Use `{{ $vars.<flowNodeId>.output[.<field>] }}` with an exact upstream node `id`. |

## Repair Recipes

Use direct JSON edits for inline-agent graph repairs. The Flow CLI has no node-update command (see [editing-operations-cli.md § Operations Not Supported by CLI](../../editing-operations-cli.md#operations-not-supported-by-cli)), and the inline-agent graph is not a Flow CLI carve-out. If a bulk scripted rewrite is explicitly approved, use the `python3` heredoc pattern from [editing-operations-json.md — Edit Tooling](../../editing-operations-json.md#edit-tooling); otherwise apply the same transformations through `Edit` / `Write`.

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
INLINE_TYPES = ("uipath.agent.autonomous", "uipath.agent.resource.")
for node in flow["nodes"]:
    t = node.get("type", "")
    if t == "uipath.agent.autonomous" or t.startswith("uipath.agent.resource."):
        model = node.pop("model", None) or {}
        if isinstance(model.get("source"), str):
            node.setdefault("inputs", {})["source"] = model["source"]
json.dump(flow, open("<FILE>.flow", "w"), indent=2)
PY
uip maestro flow validate <FILE>.flow --output json
```

Same pattern works for any node type — substitute the `nodeType` string in both the `registry get` command and the loop guard. The `model.source` → `inputs.source` rewrite above is applied to both the inline agent node and every attached resource node (tool, escalation, context) — all of them carry source identity at `inputs.source` and never on an instance `model` block.

### Resolve a `[REQUIRED_FIELD] systemPrompt is required` validator error

Current flow validation requires non-empty placeholder prompts on the flow node and uses the inline agent directory referenced by `inputs.source`. Check in order:

1. **UUID at `inputs.source`** — the `projectId` UUID must be set at `inputs.source`. Diagnose:

    ```bash
    python3 - <<'PY'
    import json
    flow = json.load(open("<FILE>.flow"))
    for node in flow["nodes"]:
        t = node.get("type", "")
        if t == "uipath.agent.autonomous" or t.startswith("uipath.agent.resource."):
            print(t, "inputs.source:", node.get("inputs", {}).get("source"))
            print(t, "model.source: ", node.get("model", {}).get("source"))
    PY
    ```

    If a stale flow has the UUID at `model.source` on the inline agent node **or any attached resource node** (tool, escalation, context), move it to `inputs.source` and remove the instance `model` block:

    ```bash
    python3 - <<'PY'
    import json
    flow = json.load(open("<FILE>.flow"))
    for node in flow["nodes"]:
        t = node.get("type", "")
        if t == "uipath.agent.autonomous" or t.startswith("uipath.agent.resource."):
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
- **Do not use `model.agentProjectId`, `inputs.agentProjectId`, or `model.source` on any inline-agent-related node instance** — both `uipath.agent.autonomous` and every attached resource node (`uipath.agent.resource.tool.*`, `uipath.agent.resource.escalation`, `uipath.agent.resource.context.*`) carry source identity at `inputs.source` and have no instance `model` block.
- **Do not create `entry-points.json` or `project.uiproj` inside the inline agent directory** — those belong only to standalone agent projects.
- **Do not name the inline agent folder with a human-readable name** — the folder name must be the `projectId` UUID.
- **Do not use `uip agent tool add`** for inline-in-flow agents — hand-author the tool's `resource.json` instead.
- **Do not skip `uip agent validate --inline-in-flow` followed by `uip agent migrate --inline-in-flow`** after editing `agent.json` or any `resources/*/resource.json`; for tool-bearing inline agents, pass `--bindings-target <FlowProjectDir>/bindings_v2.json` on the migrate call to propagate tool bindings.
