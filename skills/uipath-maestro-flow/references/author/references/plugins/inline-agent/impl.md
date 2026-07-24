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
3. **Write a real system prompt** in `messages[0].content` — bounded role, per-tool call/stop criteria, output contract, grounding. Skeleton + worked example: [`agent-prompting-guide.md`](../../../../../../uipath-agents/references/lowcode/prompting/agent-prompting-guide.md).
4. Write the user prompt in `messages[1].content`.
5. **Declare a typed `outputSchema`** — not a bare `content` string — so downstream nodes can consume the result.

After editing `content`, rebuild the matching `messages[].contentTokens` (`type: "simpleText"` / `type: "variable"`). Token mechanics are flow-specific — see § Wiring Flow Variables into Agent Prompts below; for prompt-quality structure see `agent-prompting-guide.md`.

> **Source of truth.** The prompt skeleton, the production-field checklist (`outputSchema` / `temperature` / `maxIterations` / `guardrails`), the model-discovery command, and the worked example all live in the `uipath-agents` guides linked above — this skill points at them rather than copying, to avoid cross-skill drift. The obligations in steps 1–5 are the build-time minimum; the *how* is one click away.

## Wiring Flow Variables into Agent Prompts

Passing flow data into an inline agent requires **three hand-authored, aligned** pieces. **The CLI does not derive the input wiring** — `uip agent refresh` does **not** scan prompts, derive `inputSchema`, or populate `agentInputVariables`; you author all three, and packaging ships them as-authored. (Refresh *does* regenerate `messages[].contentTokens` from `content` — that's the one derived part; see the invariant below.) The converter builds the runtime `JobArguments` from the **flow node's `inputs.agentInputVariables[]`** (not from `$vars` tokens in `agent.json`). Flatten rule: `$vars.<trigger>.output.<var>` → `<trigger>__output__<var>`.

The three pieces — **Delivery** (node `agentInputVariables[]`), **Contract** (`agent.json` `inputSchema`), and **Resolution** (`{{input.<key>}}` in `messages[].content`) — and their examples are in the table below. `flow validate` catches a Resolution↔Contract mismatch (a `{{input.K}}` that's malformed or names a key not in `inputSchema`), but a missing/wrong **Delivery** binding passes validate and only shows up as empty input at `flow debug`. Agent-side `inputSchema`/`contentTokens` mechanics: the `uipath-agents` skill's [inline-in-flow § Wiring Flow Inputs Into an Inline Agent](../../../../../../uipath-agents/references/lowcode/capabilities/inline-in-flow/inline-in-flow.md#wiring-flow-inputs-into-an-inline-agent-required).

> **Prerequisite — the bound value must actually exist as a variable.** A node binding `=$vars.X` resolves at runtime only if `$vars.X` is a declared variable. `flow validate` does **not** check that the path exists — a binding referencing an undeclared trigger field passes validate, then **faults at debug** with `JobArguments` empty. When the upstream node is a **trigger** (e.g. `core.trigger.manual`, id `start`), each field you bind must be declared in `variables.globals[]` as a trigger-associated input — `direction: "in"`, `triggerNodeId: "<triggerId>"` — and is then read as `$vars.<triggerId>.output.<id>`:
>
> ```json
> { "id": "invoiceNumber", "direction": "in", "type": "string", "triggerNodeId": "start" }
> ```
>
> Bind it on the agent node (`agentInputVariables[]`, `=$vars.start.output.invoiceNumber`) and reference it in the prompt as `{{input.start__output__invoiceNumber}}`. Likewise, flow outputs the agent feeds (e.g. `determination`, `rationale`) must be declared as `direction: "out"` globals and mapped on every reachable End node. Full schema and the `$vars.{triggerNodeId}.output.{id}` access rule: [../../../../shared/variables-and-expressions.md](../../../../shared/variables-and-expressions.md) (§ Input associated with a trigger); declaring/mapping mechanics: [../../editing-operations-json.md § Add a workflow variable](../../editing-operations-json.md#add-a-workflow-variable).

| Where | What | Example |
| --- | --- | --- |
| Flow node `inputs.agentInputVariables[]` | One entry per input — the delivery binding the converter turns into `JobArguments`. | `{ "id": "start__output__invoiceNumber", "type": "string", "binding": "=$vars.start.output.invoiceNumber", "description": "Bound from $vars.start.output.invoiceNumber" }` |
| `agent.json` `inputSchema.properties` | One `<trigger>__output__<var>` key per input — **mandatory**, binds `JobArguments` → the agent's `input`. | `"start__output__invoiceNumber": { "type": "string", "description": "Bound from $vars.start.output.invoiceNumber" }` |
| `agent.json` `messages[].content` | `{{input.<trigger>__output__<var>}}` (the `input.` form — never `$vars`). | `"Invoice: {{input.start__output__invoiceNumber}}"` |
| `agent.json` `messages[].contentTokens[]` | One `{ "type": "variable", "rawString": "input.<trigger>__output__<var>" }` per `{{ ... }}` token in `content` (brace-free `rawString`). | `{ "type": "variable", "rawString": "input.start__output__invoiceNumber" }` |

Each binding's source `$vars.<node>.output.<field>` must reference a real node `id` in the `.flow` file, with an edge path reaching the inline-agent node. See [../../../../shared/node-output-wiring.md](../../../../shared/node-output-wiring.md) for the full expression contract.

### The `content` ↔ `contentTokens` mirror invariant

`content` is the source of truth. **`uip agent refresh` regenerates `messages[].contentTokens` from `content`** (correct `simpleText`/`variable` types, brace-free `rawString`). So: author the prompt in `content`, run `refresh`, and **don't hand-author or hand-fix `contentTokens`**. `uip agent validate` is read-only — if it flags a token mismatch (`Expected type "simpleText"…`, `Expected "input.X" but got "{{input.X}}"`, or `contentTokens has N entries but content requires M`), **re-run `refresh`** to regenerate; don't edit `rawString`.

What `refresh` produces, for `content` = `"Invoice Number: {{input.start__output__invoiceNumber}}\n"`:

```json
"contentTokens": [
  { "type": "simpleText", "rawString": "Invoice Number: " },
  { "type": "variable",   "rawString": "input.start__output__invoiceNumber" },
  { "type": "simpleText", "rawString": "\n" }
]
```

### Worked example — end to end (repeat the triple per input)

Flow node (excerpt) — `binding` per input, typed `agentOutputVariables`:

```json
"agentInputVariables": [
  { "id": "emailReceived1__output__subject", "type": "string", "binding": "=$vars.emailReceived1.output.subject" },
  { "id": "emailReceived1__output__body",    "type": "string", "binding": "=$vars.emailReceived1.output.body" }
],
"agentOutputVariables": [{ "id": "category", "type": "string" }]
```

Matching `agent.json` — `inputSchema` keys mirror the bindings; the prompt uses the `input.` form, and `contentTokens` decompose `content` left-to-right (literals → `simpleText` verbatim incl. `\n`; each `{{ … }}` → brace-free `variable`):

```json
"inputSchema":  { "type": "object", "properties": {
  "emailReceived1__output__subject": { "type": "string" },
  "emailReceived1__output__body":    { "type": "string" }
} },
"outputSchema": { "type": "object", "properties": { "category": { "type": "string" } }, "required": ["category"] },
"messages": [
  { "role": "system", "content": "Triage the email.", "contentTokens": [{ "type": "simpleText", "rawString": "Triage the email." }] },
  { "role": "user",
    "content": "Subject: {{input.emailReceived1__output__subject}}\n\n{{input.emailReceived1__output__body}}",
    "contentTokens": [
      { "type": "simpleText", "rawString": "Subject: " },
      { "type": "variable",   "rawString": "input.emailReceived1__output__subject" },
      { "type": "simpleText", "rawString": "\n\n" },
      { "type": "variable",   "rawString": "input.emailReceived1__output__body" }
    ] }
]
```

Keep the flow-node `systemPrompt` / `userPrompt` as short generic placeholders — the canonical prompt lives in `agent.json messages[]`, and that system prompt should be a real structured one (see `agent-prompting-guide.md`), not a bare blob.

### When the source field name is unknown at authoring time

Connector-trigger output fields (e.g. email `subject`/`from`/`body`) aren't in the registry — only knowable after a real run. Author best-guess `{{input.<node>__output__<field>}}` paths with the matching `binding`/`inputSchema` key, **ask the user to confirm before upload** (don't invent field names silently), and correct the tokens + `contentTokens` mirrors after the first run.

### Anti-patterns

- **In `agent.json` prompts, use the `{{input.<trigger>__output__<var>}}` form** (the flattened key, `input.` prefix). Never use raw `{{ $vars.X }}` (the runtime can't resolve it — agent gets the literal token) or `{{plainName}}` (no prefix).
- **The `variable` `rawString` is exactly what sits between the braces** — `input.<trigger>__output__<var>`, brace-free, no added spaces.
- **Keep the flow-node `inputs.systemPrompt` / `inputs.userPrompt` as short generic placeholders** — the canonical prompt lives in `agent.json messages[]`, and delivery comes from `agentInputVariables[]`, not from tokens in the node prompts.
- **Each `agentInputVariables[]` entry uses `binding` (not `value`).** The converter builds `JobArguments` from `binding`; a `value: "=js:$vars…"` entry (Studio Web's internal canvas form) is **ignored** — the agent gets empty input and faults at debug (`AGENT_RUNTIME.TERMINATION_LLM_RAISED_ERROR`, "Template placeholders detected instead of actual values"). Write `{ "id": "<key>", "binding": "=$vars.<trigger>.output.<var>" }`. `binding` is what both the CLI converter and Studio Web's loader read.

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

`tool` is the inline agent's bottom artifact port; `context` is also bottom and `escalation` is the top port (see [§ Adding Resource Nodes](#adding-resource-nodes)). The target node's `input` port is a target-typed artifact handle.

## Adding Resource Nodes

An inline agent attaches resource nodes — tools (external or built-in), contexts, and escalations — to its three artifact ports. **All kinds wire into the `.flow` identically:** discover the node type, add a minimal node instance, copy its definition into `definitions[]`, add a placeholder layout entry, wire ONE artifact edge to the node's `input` port, then hand-author `resource.json` and run refresh + validate. Three things vary per kind — the **artifact port** the edge leaves, the **node type**, and whether the resource needs **solution-level files**. The `resource.json` body is owned by the `uipath-agents` skill (linked per row).

| Kind | Edge source port | Node type | `resource.json` discriminator | Needs `uip solution resources refresh`? | `resource.json` reference (uipath-agents) |
|------|------------------|-----------|-------------------------------|------------------------------------------|--------------------------------------------|
| RPA process tool | `tool` (bottom) | `uipath.agent.resource.tool.process.<release-key>` | `type: "process"` | Yes | `lowcode/capabilities/process/process.md` |
| Agent tool | `tool` (bottom) | `uipath.agent.resource.tool.agent.<release-key>` | `type: "agent"` | Yes | `lowcode/capabilities/process/process.md` |
| API workflow tool | `tool` (bottom) | `uipath.agent.resource.tool.api.<release-key>` | `type: "api"` | Yes | `lowcode/capabilities/process/process.md` |
| Process Orchestration tool | `tool` (bottom) | `uipath.agent.resource.tool.processorchestration.<release-key>` | `type: "processOrchestration"` | Yes | `lowcode/capabilities/process/process.md` |
| Built-in tool | `tool` (bottom) | `uipath.agent.resource.tool.builtin.<toolType>` | `type: "internal"` | **No** — self-contained at the agent level | `lowcode/capabilities/built-in-tools/built-in-tools.md` |
| Context (index / RAG) | `context` (bottom) | `uipath.agent.resource.context.index.<index-name>.<index-id>` | `$resourceType: "context"`, `contextType: "index"` | Yes | `lowcode/capabilities/context/index.md` |
| Escalation (HITL) | `escalation` (top) | `uipath.agent.resource.escalation` | `$resourceType: "escalation"` | Yes | `lowcode/capabilities/escalation/escalation.md` |

### 1. Discover the node type and generate a UUID

The four process-tool kinds and context carry a per-resource suffix (`<release-key>` or `<index-name>.<index-id>`) — `registry search` by the prefix (the node type minus the suffix), then `registry get` the matching `NodeType`. Escalation and built-in tools are exact strings — `registry get` directly.

```bash
# Suffix-bearing kinds (process/agent/api/processorchestration tools, context):
uip maestro flow registry search "<prefix>" --output json   # e.g. "uipath.agent.resource.tool.process"
uip maestro flow registry get "<NodeType>" --output json

# Exact-string kinds:
uip maestro flow registry get uipath.agent.resource.escalation --output json
uip maestro flow registry get "uipath.agent.resource.tool.builtin.<toolType>" --output json

# One resource UUID — used as both inputs.source and the resource.json directory/id
RES=$(uuidgen)
```

`<release-key>` is the resource's release-key GUID from `uip solution resources list` (the row's `Key`). `<toolType>` is the built-in's fixed kebab discriminator (e.g. `analyze-attachments`), identical to the `resource.json` `properties.toolType`.

### 2. Add the node and wire the artifact edge

Every resource node uses the same minimal instance — `inputs.source` only, no instance `model` block. The definition declares `model.source: true`; flow-core hoists that identity field onto `inputs.source` (same hoisting rule as `uipath.agent.autonomous`).

```json
{
  "id": "agentTool1",
  "type": "<NodeType>",
  "typeVersion": "<DEFINITION_VERSION>",
  "display": { "label": "<Label>" },
  "inputs": { "source": "<RES_UUID>" }
}
```

Also add:

- The node definition copied verbatim from `registry get` into `definitions[]`. Set `typeVersion` to its `version`.
- Top-level `bindings[]` entries when the definition declares `model.bindings` — process tools use `model.bindings.resourceKey` and `model.bindings.values[]` (`name`, `folderPath`, etc.); see [editing-operations-json.md — Resource nodes](../../editing-operations-json.md#add-a-node). Built-in tools declare none.
- A placeholder `layout.nodes.<nodeId>` entry.
- ONE artifact edge from the agent's port (per the matrix) to the node's `input` port. Substitute `tool` / `context` / `escalation` for `sourcePort`:

```json
{
  "id": "<EDGE_ID>",
  "sourceNodeId": "autonomousAgent1",
  "sourcePort": "tool",
  "targetNodeId": "agentTool1",
  "targetPort": "input"
}
```

### 3. Author `resource.json`

Hand-author `<FlowProjectDir>/<inlineAgentProjectId>/resources/<RES_UUID>/resource.json` using the matrix reference for the kind. Set `id` to `<RES_UUID>` (= the node's `inputs.source` and the resource directory name). A `resource.json` missing its `$resourceType` (or `type` for built-ins) is not recognized by `uip agent validate` — it reports `"resources": 0`, and the next refresh writes an empty `bindings_v2.json`.

**Process / agent / api / processOrchestration tools** share one shape — use the exact shape in the `uipath-agents` skill: `lowcode/capabilities/process/process.md` § Tool resource.json Shape (read it first). The subtype is the `type` field (§ Subtypes in `process.md`). RPA uses raw .NET arrays (Template A in `solution-files.md`); Agent / API / Process Orchestration use JSON Schema V2 (Template B). Run `uip solution resources list` + `uip solution resources get` to populate `referenceKey`, `folderPath`, `inputSchema`, `outputSchema`. Inline-in-flow specifics:

- Set `location` from the discovery `Source` field: `"solution"` when `Source: "Local"`, `"external"` when `Source: "Remote"` (same rule as standalone agents).
- Set `properties.folderPath` to the **literal folder path from discovery** (e.g., `"Shared/TestRPA"`) — do **not** leave it empty.
- `inputSchema.properties` must include `"guardrails": { "type": "array" }` alongside the process arguments.

**Built-in, context, and escalation** bodies follow their matrix reference.

### 4. Refresh, validate, refresh solution resources

Set prompts in `agent.json` (system + user `messages` with `contentTokens` of `type: "simpleText"` and `rawString`), then:

```bash
uip agent refresh "<FlowProjectDir>/<projectId>" --inline-in-flow \
  --bindings-target "<FlowProjectDir>/bindings_v2.json" --output json
uip agent validate "<FlowProjectDir>/<projectId>" --inline-in-flow --output json
# All kinds EXCEPT built-in tools:
uip solution resources refresh --output json
```

- **Process tools / context / escalation** resolve through `bindings_v2.json` (process / index / App binding). Pass `--bindings-target <FlowProjectDir>/bindings_v2.json` on refresh so `uip solution resources refresh` discovers the binding and writes the solution-level files. Do not hand-edit `bindings_v2.json` — refresh regenerates it.
- **Built-in tools** carry `referenceKey: null` and `type: "internal"` — no `bindings[]`, no solution-level files, no `uip solution resources refresh`.
- **Verify both refresh and validate report `"resources": N` where N > 0.** If either shows `"resources": 0`, the `resource.json` is malformed or missing required fields — fix it and re-run before proceeding.

For agent.json prompt configuration and solution resource mechanics, see the `uipath-agents` skill (`lowcode/capabilities/inline-in-flow/inline-in-flow.md`).

## Adding an IS Connector Tool Node

IS connector tool nodes let the inline agent call Integration Service connector activities (e.g., Web Search, Jira Create Issue, Slack Send Message) as tools.

### Discovery

```bash
uip maestro flow registry search "uipath.agent.resource.tool.connector" --output json
uip maestro flow registry get "uipath.agent.resource.tool.connector.<connector-key>.<operation>" --output json
```

Node type pattern: `uipath.agent.resource.tool.connector.<connector-key>.<operation>`

### Configuration — delegate to connector plugin

Configure the IS connector tool node using `uip maestro flow node configure` — see [connector/impl.md § Agent Tool Connector Nodes](../connector/impl.md#agent-tool-connector-nodes). This single command populates the complete `inputs.detail` including the request buckets `bodyParameters` / `queryParameters` / `pathParameters` (body fields as `{{prompt:}}` chips, static values for enum/query/path params with defaults), so that `uip agent refresh --inline-in-flow` can generate a complete `resource.json`. No `fieldsContainer` is written.

### Node instance

```json
{
  "id": "webSearch1",
  "type": "uipath.agent.resource.tool.connector.uipath-uipath-airdk.web-search",
  "typeVersion": "1.0.0",
  "display": { "label": "Web Search", "description": "<from definition>", "icon": "<from definition>", "shape": "circle" },
  "inputs": {
    "source": "<RESOURCE_UUID, set after agent refresh>",
    "detail": { "...configured per connector/impl.md § Agent Tool Connector Nodes..." }
  }
}
```

`inputs.source` is set to the resource UUID after `uip agent refresh --inline-in-flow` generates the `resource.json` (see Resource generation below). On first authoring it can be omitted — the CLI generates a UUID automatically.

### Flow-level bindings

IS tool nodes need Connection bindings (not process bindings) in the top-level `bindings[]`:

```json
{
  "id": "<UNIQUE_ID>",
  "name": "<connectorKey> connection",
  "type": "string",
  "resource": "Connection",
  "resourceKey": "<connectionId>",
  "default": "<connectionId>",
  "propertyAttribute": "ConnectionId"
},
{
  "id": "<UNIQUE_ID_2>",
  "name": "FolderKey",
  "type": "string",
  "resource": "Connection",
  "resourceKey": "<connectionId>",
  "default": "<connectionFolderKey>",
  "propertyAttribute": "FolderKey"
}
```

### Edge wiring

Same artifact edge pattern as RPA tools:

```json
{
  "id": "<EDGE_ID>",
  "sourceNodeId": "autonomousAgent1",
  "sourcePort": "tool",
  "targetNodeId": "webSearch1",
  "targetPort": "input"
}
```

### Resource generation and validation

After the IS tool node is fully configured in the flow (with `inputs.detail` request buckets populated), `uip agent refresh --inline-in-flow` **auto-generates** the corresponding `resource.json`, then regenerates `bindings_v2.json`. It **fetches the typed IS metadata** (field types, enum members, output schema) and joins it with the configured values from `inputs.detail` — `inputs.detail` alone has the values but not the types. No manual resource.json authoring is needed. `uip agent validate --inline-in-flow` is read-only: it confirms the expected `resource.json` files exist and reports drift (pointing back to refresh) if any are missing.

```bash
# Refresh generates the resource.json files and bindings (writes)
uip agent refresh "<FlowProjectDir>/<projectId>" --inline-in-flow \
  --bindings-target "<FlowProjectDir>/bindings_v2.json" --output json
# Validate checks (read-only) — fails with AgentValidationDrift if a resource.json is missing
uip agent validate "<FlowProjectDir>/<projectId>" --inline-in-flow --output json
uip solution resources refresh --output json
```

Verify `ConnectorToolsGenerated` in the refresh output (each entry carries `nodeId`, `name`, `connectorKey`, `resourceId`). If nothing is generated, the tool node isn't wired to the agent's `tool` port or `node configure` wasn't run — see [connector/impl.md § Agent Tool Connector Nodes](../connector/impl.md#agent-tool-connector-nodes). Keep the flow node's `inputs.source` equal to the returned `resourceId` (refresh reuses an existing `inputs.source`), then re-run validate to confirm no drift.

### Debug Tips

| Error | Cause | Fix |
| --- | --- | --- |
| `uip agent validate` shows `resources: 0` | No `resource.json` generated — tool node not wired to the agent's `tool` port, or `node configure` not run | Check the `tool` edge from the agent to the connector node, run `node configure`, then `uip agent refresh --inline-in-flow` |
| `AGENT_RUNTIME.HTTP_ERROR` / status 400 | A required param is missing from `inputs.detail` (e.g. a required query param like `send_as` not auto-filled) | Re-run `node configure`; if still missing, add it under `--detail.queryParameters` / `bodyParameters` and re-run refresh |
| Studio Web drops the tool / "value not found" for a static param | Static param (e.g. `send_as`) absent from the generated `resource.json` `inputSchema` | Re-run `uip agent refresh --inline-in-flow` to regenerate from `inputs.detail` (static params are added to `inputSchema.required`) |

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
- `inputs.agentInputVariables` carries one entry per flow input the agent reads — `{ id: "<trigger>__output__<var>", binding: "=$vars.<trigger>.output.<var>" }`. This is the only thing the converter turns into the runtime `JobArguments`; prompts then reference each input as `{{input.<trigger>__output__<var>}}` (see § Wiring Flow Variables into Agent Prompts above). Leave it `[]` only when the agent reads no flow data.
- **No `model` block on the inline-agent node instance.** The node inherits serviceType/version/context from `definitions[]`; `source` lives at `inputs.source`. Stale instance fields such as `model.serviceType`, `model.version`, or `model.context` override the inherited definition and can cause runtime mismatch.

## Accessing Output

How agent output surfaces depends on `agent.json` `outputSchema`:

- **Typed `outputSchema`** (the required form — step 5) — each property surfaces **flat** at `$vars.<nodeId>.output.<field>`. For `outputSchema.properties` `{ subject, body }`: read `$vars.<nodeId>.output.subject` and `$vars.<nodeId>.output.body`. **There is no `.content.` wrapper** — `$vars.<nodeId>.output.content.subject` resolves to undefined and silently yields a null flow output.
- **Untyped (single string)** — only when no typed schema is declared: `$vars.<nodeId>.output.content` holds the agent's text response.
- `$vars.<nodeId>.error` — error details if the agent fails.

To expose a typed field as a flow output, see § Wiring Agent Output Into Flow Outputs below.

## Wiring Agent Output Into Flow Outputs

Symmetric to input wiring — **three aligned pieces**, none CLI-derived:

| Where | What | Example |
| --- | --- | --- |
| `agent.json` `outputSchema.properties` | One typed key per field the agent returns. | `"subject": { "type": "string" }`, `"body": { "type": "string" }` |
| Flow node `inputs.agentOutputVariables[]` | **One entry per field** — NOT a single `content` object. | `[{ "id": "subject", "type": "string" }, { "id": "body", "type": "string" }]` |
| End node `outputs.<global>` | Maps each `out` global to the flat field path. | `"emailBody": { "source": "=js:$vars.<agentNodeId>.output.body" }` |

Plus: declare each flow output as a `direction: "out"` global in `variables.globals[]`, and map it on **every reachable End node**.

**Anti-pattern:** `agentOutputVariables: [{ "id": "content", "type": "object" }]` paired with End `=js:$vars.<node>.output.content.<field>`. The typed agent delivers fields flat at `output.<field>`; the `.content.` path resolves to undefined → `flow validate` passes, debug Completes, but the flow output is **null**.

## Refresh and Validate

Refresh the inline agent (writes `entry-points.json` and `bindings_v2.json`, and for tool-bearing agents, propagates bindings into the flow project's `bindings_v2.json`), then validate (read-only check), then validate the flow:

```bash
# 1. Refresh the inline agent (writes entry-points.json and bindings_v2.json)
uip agent refresh "<FlowProjectDir>/<projectId>" --inline-in-flow --output json

# 1b. For tool-bearing inline agents, refresh with --bindings-target to propagate tool bindings:
uip agent refresh "<FlowProjectDir>/<projectId>" --inline-in-flow \
  --bindings-target "<FlowProjectDir>/bindings_v2.json" --output json

# 2. Validate the inline agent (read-only schema check)
uip agent validate "<FlowProjectDir>/<projectId>" --inline-in-flow --output json

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
| Studio Web reports "System prompt is required" | Inline agent's `agent.json.messages[]` has empty `content`, OR derived files (`entry-points.json`, `bindings_v2.json`) are stale | Set prompts in `agent.json`, re-run `uip agent refresh --inline-in-flow` to regenerate derived files, then `uip agent validate --inline-in-flow` to check — see `uipath-agents` skill |
| Studio Web debug: "Could not find process for tool" | Flow project's `bindings_v2.json` is missing the tool's process binding, so `uip solution resources refresh` never created the solution-level resource | Re-run `uip agent refresh --inline-in-flow --bindings-target <FlowProjectDir>/bindings_v2.json` to propagate bindings, then `uip agent validate --inline-in-flow` to check schema, then `uip solution resources refresh`, then re-upload |
| `bindings_v2.json` is empty or missing tool bindings | Tool bindings were not propagated to the flow project level, or a later tool overwrote the file | Re-run `uip agent refresh --inline-in-flow --bindings-target <FlowProjectDir>/bindings_v2.json` after all flow node and edge edits are complete. Refresh is the verb that writes the file — do not hand-edit it |
| Agent tool (process / agent / api / processOrchestration) cannot resolve at runtime | Missing top-level `bindings[]` entries, mismatched tool-node `inputs.source` / `resource.json` id, stale solution resources, or missing project-level `bindings_v2.json` | Add the resource bindings from the tool definition, keep the tool node's `inputs.source` equal to the resource UUID, run `uip agent refresh --inline-in-flow --bindings-target <FlowProjectDir>/bindings_v2.json` to write bindings, then `uip agent validate --inline-in-flow` to check, then run `uip solution resources refresh` |
| `AGENT_RUNTIME.HTTP_ERROR` / "Integration service returned an error for tool" / status 400 | IS connector tool's `resource.json` has empty `inputSchema.properties` and/or `parameters[]`, or a required param is missing — the agent runtime cannot construct a valid IS request | The flow node's `inputs.detail` request buckets weren't populated (re-run `node configure`), or a required param like `send_as` is absent (add it under `--detail.queryParameters`). Then re-run `uip agent refresh --inline-in-flow` to regenerate. See § Adding an IS Connector Tool Node |
| `inputs.agentProjectId` unrecognized | Wrong field name | Use `inputs.source` — `agentProjectId` is not valid for inline agents |
| Inline agent rejected by `uip agent validate` | `entry-points.json` or `project.uiproj` present inside the inline agent dir | Delete those files — they belong only to standalone agent projects |
| Folder name is human-readable instead of UUID | Folder renamed after scaffolding | Rename to the original `projectId` UUID — the folder name must match `inputs.source` and the `projectId` field inside `agent.json` |
| Agent runs but returns empty `output.content` | Missing or malformed `contentTokens` in `agent.json` | Rebuild `messages[].contentTokens` using `{ "type": "simpleText", "rawString": "..." }` entries; see `uipath-agents` for detail |
| `flow validate` passes, debug Completes, but the `out` global (e.g. `emailBody`) is null | Typed agent output read with a `.content.` wrapper — `agentOutputVariables:[{content}]` + End `=js:$vars.<node>.output.content.<field>` — but typed fields surface flat at `output.<field>` | List each field in `agentOutputVariables[]` (`{id:"subject"},{id:"body"}`) and map End to `=js:$vars.<node>.output.<field>` (no `.content.`). See § Wiring Agent Output Into Flow Outputs. |
| `agent validate` flags `Expected type "simpleText" but got "text"` | Hand-edited `contentToken` written with `type: "text"` | Re-run `uip agent refresh` — it regenerates `contentTokens` from `content` (correct `simpleText`/`variable` types). Don't hand-edit the token. See § The `content` ↔ `contentTokens` mirror invariant. |
| `agent validate` flags `Expected "input.X" but got "{{input.X}}"` | Hand-edited `variable` token has the braces/extra spaces in its `rawString` | Re-run `uip agent refresh` to regenerate the tokens from `content` (brace-free `rawString`) — don't hand-fix it. See § The `content` ↔ `contentTokens` mirror invariant. |
| `agent validate` flags `contentTokens has N entries but content requires M. Rebuild contentTokens to match content.` | `content` and `contentTokens` drifted (e.g. tokens edited without `content`, or vice versa) | Re-run `uip agent refresh` to regenerate `contentTokens` from `content`. If the prompt itself is wrong, fix `content` first, then refresh. See § The `content` ↔ `contentTokens` mirror invariant. |
| Prompt shows literal `{{input.X}}` at runtime | `inputSchema.properties` missing the referenced key (`flow validate` flags this — run it) | Add the `<trigger>__output__<var>` key to `inputSchema`. |
| `flow validate` passes but debug faults `AGENT_RUNTIME.TERMINATION_LLM_RAISED_ERROR` (literal `input.<key>`) | Node `agentInputVariables` uses `value:` instead of `binding:` (or is missing) → empty `JobArguments` | Set `binding:"=$vars.<trigger>.output.<var>"` on the node entry; ensure the trigger global is declared (`direction:"in"`). |
| Debug faults `AGENT_RUNTIME.TERMINATION_LLM_RAISED_ERROR` "Template placeholders detected instead of actual values" — and the node *does* have `agentInputVariables[]` | Entries use `value: "=js:$vars…"` (Studio Web's canvas form) instead of `binding`; the converter only reads `binding`, so `JobArguments` are empty | Rename `value` → `binding` on each entry and strip the `=js:` prefix: `{ "id": "<key>", "binding": "=$vars.<trigger>.output.<var>" }`. See § Wiring Flow Variables into Agent Prompts. |

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
- **Do not skip `uip agent refresh --inline-in-flow` followed by `uip agent validate --inline-in-flow`** after editing `agent.json` or any `resources/*/resource.json`; for tool-bearing inline agents, pass `--bindings-target <FlowProjectDir>/bindings_v2.json` on the refresh call to propagate tool bindings.
