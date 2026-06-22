# Inline Agent in a Flow

Walkthrough for embedding a low-code autonomous agent directly inside a flow project. The agent lives as a UUID-named subdirectory inside the flow project and is published with the parent flow.

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

> The scaffold sets `settings.model: "gpt-4o-2024-11-20"` (stale) and empty prompts. **Override the model** (`uip agent model list` → [model-selection-guide.md](../../model-selection-guide.md)) and write robust prompts ([prompting/agent-prompting-guide.md](../../prompting/agent-prompting-guide.md)) before validating.

### Option B: Manual creation

#### Step 1: Start with an existing flow project

The flow project must already exist.

#### Step 2: Generate a UUID and create the agent subdirectory

Generate a unique UUID (e.g., `5029c8a8-799b-426a-803f-c4ec75255439`). Create a directory with that UUID as the name inside the flow project.

#### Step 3: Create agent.json

Same schema as a standalone agent (see [../../agent-definition.md](../../agent-definition.md)), with these conventions:
- `projectId` matches the folder name UUID
- `inputSchema.properties`: one `<triggerNodeId>__output__<global>` key per flow input — **mandatory**. See [§ Wiring Flow Inputs Into an Inline Agent](#wiring-flow-inputs-into-an-inline-agent-required).
- `messages[].content`: reference inputs as `{{input.<triggerNodeId>__output__<global>}}` (the `input.` form). Then run `uip agent refresh` to regenerate `contentTokens` from `content` — don't hand-author them. See [§ Wiring Flow Inputs Into an Inline Agent](#wiring-flow-inputs-into-an-inline-agent-required).
- `guardrails: []` at root level — can be populated with guardrail objects. See [../guardrails/guardrails.md](../guardrails/guardrails.md)
- No `metadata.targetRuntime` field

Example:
```json
{
  "version": "1.1.0",
  "settings": {
    "model": "anthropic.claude-sonnet-4-6",
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

## Wiring Flow Inputs Into an Inline Agent (required)

**The CLI does not derive the input wiring** — you author it; `refresh` only regenerates `contentTokens` from `content` (it does not fill `inputSchema` or `agentInputVariables`). `flow validate` *does* catch a prompt↔schema mismatch (a `{{input.K}}` that's malformed or names a key not in `inputSchema`), but **not** a missing/wrong node `agentInputVariables` binding — that delivery gap surfaces only at `flow debug`.

This skill authors the **`agent.json` side** (flatten rule: `$vars.<trigger>.output.<var>` → `<trigger>__output__<var>`):
- `inputSchema.properties` — one `<trigger>__output__<var>` key per input (mandatory; binds the delivered `JobArguments` into the agent's `input`). Empty schema → the agent sees the literal `input.<key>` token even when the value arrived.
- `messages[].content` — reference each input as `{{input.<trigger>__output__<var>}}` (the `input.` form, **not** `$vars`), plus a real system prompt. `content` is the source of truth; run `uip agent refresh` to generate the matching `contentTokens` from it (don't hand-author them).

```json
"inputSchema": { "properties": {
  "start__output__disputeSummary": { "type": "string", "description": "Bound from $vars.start.output.disputeSummary" }
} },
"messages": [{ "role": "user",
  "content": "Write a billing resolution email for this dispute:\n{{input.start__output__disputeSummary}}" }]
```

The **flow side** — the trigger global and the node `agentInputVariables[]` binding (the only thing the converter turns into `JobArguments`) — is authored through the `uipath-maestro-flow` skill (Critical Rule 15). The full four-piece contract, the converter behavior, and the `content`↔`contentTokens` invariant + validator errors all live there: [inline-agent prompt-wiring guide § Wiring Flow Variables into Agent Prompts](../../../../../uipath-maestro-flow/references/author/references/plugins/inline-agent/impl.md#wiring-flow-variables-into-agent-prompts).

## Refresh and Validate Inline Agent

```bash
uip agent refresh "<FlowProjectDir>/<projectId>" --inline-in-flow --output json
uip agent validate "<FlowProjectDir>/<projectId>" --inline-in-flow --output json
```

`--inline-in-flow` skips the `entry-points.json` / `project.uiproj` checks. In inline mode `refresh` regenerates `messages[].contentTokens` (from `content`) and `bindings_v2.json` — **not** `entry-points.json` (standalone only). `validate` is read-only (it flags `contentTokens` drift but doesn't repair it — fix by re-running `refresh`).

**Verify at `flow debug`, not after refresh:** `refresh` never fills `inputSchema` — it is non-empty only because you authored it (`DerivedFiles: 0` is normal and does **not** mean input is missing). The end-to-end check (run `uip maestro flow debug` and confirm the agent resolves the input rather than echoing the literal `input.<key>` token) is owned by the `uipath-maestro-flow` skill — see its [inline-agent guide § Debug](../../../../../uipath-maestro-flow/references/author/references/plugins/inline-agent/impl.md#debug).

For inline agents with external capabilities (tools, contexts, memory spaces, or escalations), pass `--bindings-target` to **`refresh`** after all flow graph edits:

```bash
uip agent refresh "<FlowProjectDir>/<projectId>" --inline-in-flow \
  --bindings-target "<FlowProjectDir>/bindings_v2.json" --output json
```

`--bindings-target` propagates the inline agent's bindings (process, connection, index, memorySpace, app, etc.) into the flow project's `bindings_v2.json`. This is required for `uip solution resources refresh` to discover the bindings and create solution-level resource files. Never hand-edit `bindings_v2.json`.

> **Ordering constraint:** run the final `uip agent refresh --inline-in-flow --bindings-target …` after all flow graph edits are complete. The `uipath-maestro-flow` skill owns direct `.flow` authoring for the inline-agent node, capability-resource nodes, and edges; refresh last so the generated bindings land in the flow project's `bindings_v2.json` before `uip solution resources refresh`. See the [Walkthrough](#walkthrough--end-to-end) for the correct sequence.

## Flow Wiring

After creating the inline agent, the flow needs a `uipath.agent.autonomous` node whose `inputs.source` is the inline agent's `projectId` UUID, plus edges connecting it to the rest of the flow.

**Hand off to the `uipath-maestro-flow` skill for the actual node and edge authoring.** Per Critical Rule 15, this skill does not invoke flow operations directly. Tell the user:

> The inline agent has been scaffolded at `<FlowProjectDir>/<projectId>/`. To wire it into the flow, use the `uipath-maestro-flow` skill — pass it `projectId = <uuid>` so it can add a `uipath.agent.autonomous` node with `inputs.source = <uuid>` and connect the input/success edges via direct `.flow` authoring. **After all flow graph edits are complete**, run `uip agent refresh --inline-in-flow`, then `uip agent validate --inline-in-flow`; for inline agents with external capabilities, include `--bindings-target <FlowProjectDir>/bindings_v2.json` on the refresh call.

The node JSON shape that the flow skill must produce is documented in § Flow Node Structure below — keep it as a reference, not as a CLI walkthrough.

## Inline-in-Flow Resource Paths

Inline-agent resources — `tool`, `context`, `escalation` — share one path convention. Memory spaces are features, not `resources/` files; add them with `uip agent memory add ... --path <FlowProjectDir>/<projectId>` and see [../memory/memory.md](../memory/memory.md).

**Path:** `<FlowProjectDir>/<projectId>/resources/<RES_UUID>/resource.json`

`<RES_UUID>` is a fresh UUID. It MUST match (a) the resource node's `inputs.source` in the flow and (b) the `id` field inside `resource.json`. The resource directory name is the UUID — never the human-readable resource name. Human-readable folder names are the standalone-agent convention; inline agents always use UUIDs.

Resource body shape is identical to the standalone-agent docs — only the folder name differs:
- Tools (`process` / `agent` / `api` / `processOrchestration`): [../process/process.md](../process/process.md) § Subtypes and § Tool resource.json Shape. Discovery is identical (`uip solution resources list` + `uip solution resources get`); subtype is selected by the `type` field.
- Context index: [../context/index.md](../context/index.md) § Agent-Level Resource Shape.
- Escalation: [../escalation/escalation.md](../escalation/escalation.md) § Agent-Level Resource.

### Tool-specific notes

- **`location`**: Follows the same rule as standalone agents — set `"solution"` when the row from `uip solution resources list` has `Source: "Local"`, set `"external"` when `Source: "Remote"`. See [../process/process.md](../process/process.md) and [../../critical-rules/critical-rules.md](../../critical-rules/critical-rules.md) Rule 12.
- **`properties.folderPath`**: Must be the **literal folder path from discovery** (e.g., `"Shared/Sales"`) — do **not** leave it empty. An empty `folderPath` prevents `uip solution resources refresh` from resolving the tool at runtime.
- **`inputSchema.properties`**: Must include `"guardrails": { "type": "array" }` alongside the tool arguments — the runtime expects it.
- **All fields from the template in [../process/process.md](../process/process.md) are required** — especially `$resourceType: "tool"`, `guardrail`, `properties.processName`, `properties.exampleCalls`, `isEnabled`, and `argumentProperties`. A `resource.json` missing `$resourceType` will not be recognized by `uip agent validate` (the tool reports `"resources": 0`); `uip agent refresh` will then write an empty `bindings_v2.json`.

## Inline-in-Flow IS Connector Tool resource.json

The `resource.json` for IS connector tools inside an inline-in-flow agent uses the **same format** as IS tools in standalone agents. See [../integration-service/integration-service.md](../integration-service/integration-service.md) for the full resource.json shape, properties, and field reference.

**Path:** `<FlowProjectDir>/<projectId>/resources/<RES_UUID>/resource.json`

**Auto-generation by `uip agent refresh --inline-in-flow`:** When the parent `.flow` file contains IS connector tool nodes wired to this agent via `tool` artifact edges, `uip agent refresh --inline-in-flow` automatically discovers them and generates the corresponding `resource.json` files. This means you do **not** need to hand-author IS tool resource.json files — just configure the connector tool node in the flow (via `uip maestro flow node configure`), then run refresh. `uip agent validate --inline-in-flow` is read-only: it checks the expected `resource.json` files exist and reports drift pointing back to refresh.

The auto-generation:
1. Navigates up from the inline agent directory to find the parent `.flow` file
2. Finds all `uipath.agent.resource.tool.connector.*` nodes connected to this agent's `tool` port
3. Reads each node's `inputs.detail` (connectionId, connectionFolderKey, endpoint, method, the `bodyParameters` / `queryParameters` / `pathParameters` request buckets, `multipartParameters`, `inputMetadata`) and its definition
4. **Fetches the typed IS object metadata** for the connector (transiently, via the connection) to recover field types, enum members, and the output schema — `inputs.detail` only carries the configured VALUES, not types/enums/output. (Offline / no connection → falls back to a value-only untyped build.)
5. Generates a `resource.json` with `type: "integration"` in `<projectDir>/resources/<UUID>/resource.json` by joining the metadata (types/enums/output) with the `inputs.detail` values
6. Skips nodes whose on-disk `resource.json` already matches (idempotent; overwrites on drift)

Additional notes for inline-in-flow IS tools:
- **`type`**: Always `"integration"` (not `"process"`)
- **`location`**: Always `"external"` for IS connector tools
- **`id`**: The generated UUID for the resource directory name
- **`properties.connection`**: Populated from `inputs.detail.connectionId`, `inputs.detail.connectionFolderKey`, and the connector key from the definition's `model.context[]`
- **`properties.parameters`** and **`inputSchema`**: field set + types/enums come from the fetched IS metadata; VALUES come from `inputs.detail` (`bodyParameters` → `fieldLocation: "body"`, `queryParameters` → `"query"`, `pathParameters` → `"path"`, `multipartParameters` → `"multipart"`). A `{{prompt: "..."}}` chip → `fieldVariant: "dynamic"` (agent-decided); a concrete value (e.g. `send_as=bot`) → `fieldVariant: "static"`.
- **`outputSchema`**: built (nested) from the metadata's response fields.
- **Enum fields**: `enum`/`oneOf` are emitted in `inputSchema` **only for dynamic fields**. A *static* field carrying an enum breaks the agent runtime's model build (`` `<Tool>` is not fully defined; __Dynamictype… ``). At configure, a **single-value enum** body field is written as a **static** constant (the agent can't be trusted to echo an exact obscure value like `GoogleCustomSearch`); a **multi-value enum** stays **dynamic** so the agent picks from the enum.
- **Dotted body fields are nested in `inputSchema`**: a field named `fields.project.key` becomes a nested object (`fields` → `project` → `key`), not a flat property keyed `"fields.project.key"`. The LLM's tool-call arguments follow `inputSchema`, so a flat key makes it emit `{"fields.project.key": "..."}` and the IS request body is malformed (e.g. Jira Create Issue fails with "Specify a valid project ID or key"). `parameters[]` keep the flat dotted `name` + `fieldLocation` — only `inputSchema` nests.
- **`bodyStructure`**: `{contentType:"multipart", jsonBodySection:<name>}` when `inputs.detail.inputMetadata.type === "multipart"` (e.g. Outlook Send Email), else `{contentType:"json"}`.
- **No `fieldsContainer`**: the CLI never writes `fieldsContainer` on the node; the typed metadata is fetched at refresh instead.
- **`iconUrl`**: Taken from the definition's `display.icon` (the type-cache URL)
- No `referenceKey` or `argumentProperties` (those are process-tool-only fields)
- **bindings_v2.json**: When using `--bindings-target`, refresh generates a `resource: "connection"` binding entry for the IS tool's connection (with `metadata.connector` set to the connector key)
- **Solution-level resources**: `uip solution resources refresh` creates `resources/solution_folder/connection/<connector-key>/<connection-name>.json` for IS tools (not `process/` + `package/` like RPA tools)

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

Resource nodes use the same `inputs.source` pattern as the autonomous agent — no instance `model` block. The `type` follows the per-kind patterns in § Resource nodes below — `uipath.agent.resource.tool.{process|agent|api|processorchestration}.<release-key>`, where `<release-key>` is the resource's release-key GUID returned by `uip solution resources list`:

```jsonc
{
  "id": "agentTool1",
  "type": "uipath.agent.resource.tool.<kind>.<release-key>",
  "typeVersion": "<DEFINITION_VERSION>",
  "display": { "label": "<ToolName>" },
  "inputs": {
    "source": "<RES_UUID>"
  }
}
```

The definition declares `model.source: true`; flow-core hoists that identity field onto the node instance as `inputs.source` (same hoisting rule as `uipath.agent.autonomous`). The same shape applies to `uipath.agent.resource.escalation.*` and `uipath.agent.resource.context.*` nodes.

### Handles

| Handle | Position | Allowed connections |
|--------|----------|---------------------|
| `escalation` | top | `uipath.agent.resource.escalation.*` |
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
| RPA process | `uipath.agent.resource.tool.process.<release-key>` |
| Agent-as-tool | `uipath.agent.resource.tool.agent.<release-key>` |
| API workflow | `uipath.agent.resource.tool.api.<release-key>` |
| Process Orchestration | `uipath.agent.resource.tool.processorchestration.<release-key>` |
| Built-in tool | `uipath.agent.resource.tool.builtin.<tool-name>` |
| IS connector | `uipath.agent.resource.tool.connector` |
| Semantic index | `uipath.agent.resource.context.index.<index-name>.<index-id>` |
| Escalation | `uipath.agent.resource.escalation.<variant>` (e.g. `.coded-action-app`; discover with `uip maestro flow registry search "escalation"`) |
| Memory space | `uipath.agent.resource.memory.*` canvas node, backed by `features/<FeatureName>/feature.json` from `uip agent memory` |

`<release-key>` is the resource's release-key GUID from `uip solution resources list` (the row's `Key` field). The four process-tool kinds share the same registry-discovery flow and the same `resource.json` shape — only the prefix in front of `<release-key>` and the `type` field in `resource.json` differ. See [../process/process.md](../process/process.md) § Subtypes.

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
# See § Inline-in-Flow Resource Paths above for the exact format

# 5. Hand off to the uipath-maestro-flow skill to add the
#    uipath.agent.autonomous node (inputs.source = <projectId>),
#    tool resource nodes, and wire all edges (input/success/tool).
#    Do NOT run uip maestro flow commands from this skill —
#    Critical Rule 15.

# 6. Refresh — regenerates entry-points.json and bindings_v2.json,
#    and (with --bindings-target) propagates capability bindings into the flow
#    project's bindings_v2.json so resource refresh can discover them.
#    MUST run AFTER flow graph edits (step 5).
uip agent refresh "<FlowProjectDir>/<projectId>" --inline-in-flow \
  --bindings-target "<FlowProjectDir>/bindings_v2.json" --output json

# 7. Validate the inline agent (read-only check).
uip agent validate "<FlowProjectDir>/<projectId>" --inline-in-flow --output json

# 8. Refresh solution resources and upload
uip solution resources refresh --output json
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
uipath.agent.autonomous                                        ← Inline agent node

uipath.agent.resource.tool.process.<release-key>               ← Tool: RPA process
uipath.agent.resource.tool.agent.<release-key>                 ← Tool: agent
uipath.agent.resource.tool.api.<release-key>                   ← Tool: API workflow
uipath.agent.resource.tool.processorchestration.<release-key>  ← Tool: process orchestration
uipath.agent.resource.tool.connector                           ← Tool: IS connector
uipath.agent.resource.tool.builtin.<tool-name>                 ← Tool: built-in
uipath.agent.resource.context.index.<index-name>.<index-id>    ← Context: semantic index
uipath.agent.resource.escalation.<variant>                     ← Escalation: HITL (e.g. .coded-action-app)
uipath.agent.resource.memory.*                                 ← Memory space canvas node; feature file lives under features/
```

## BPMN Execution Engine Notes

- **Inline agents**: `ServiceTask` with `serviceType: "Orchestrator.StartInlineAgentJob"`. The agent definition is read from the inline agent directory (`inputs.source` UUID) and executed in-process.

The execution is asynchronous. The flow pauses at the agent node and resumes when the agent job completes.

## Gotchas

See [../../critical-rules/autonomous-critical-rules.md](../../critical-rules/autonomous-critical-rules.md) Critical Rule 1. The skill explicitly defers flow authoring to `uipath-maestro-flow` — it does not invoke that skill automatically ([../../critical-rules/critical-rules.md](../../critical-rules/critical-rules.md) Critical Rule 15).

**Capability bindings must be propagated to the flow project's `bindings_v2.json`.** Only project-level bindings are scanned by `uip solution resources refresh`. Pass `--bindings-target <FlowProjectDir>/bindings_v2.json` to `uip agent refresh --inline-in-flow` — refresh is the command that writes the bindings. Without project-level propagation, Studio Web debug can fail because no solution-level resource file is created for the external capability.

Run the final `uip agent refresh --inline-in-flow --bindings-target …` as the **last step** before `uip solution resources refresh`, after all flow graph edits are complete. See the [Walkthrough](#walkthrough--end-to-end) for the correct sequence.

## References

- [../../agent-definition.md](../../agent-definition.md) — agent.json schema (same as standalone, with the inline-specific differences listed above)
- [../../critical-rules/autonomous-critical-rules.md](../../critical-rules/autonomous-critical-rules.md) Critical Rule 1
