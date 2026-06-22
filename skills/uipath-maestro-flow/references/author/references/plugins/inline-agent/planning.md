# Inline Agent Node — Planning

Inline agent nodes embed an autonomous AI agent **inside** the flow project. The agent definition lives as a subdirectory of the flow project and is published together with the flow — no separate agent project, no tenant publishing step. Unlike [published agents](../agent/planning.md), the node type is fixed and the agent is bound to the flow via a local `projectId` rather than a registry-resolved resource key.

For agent configuration, prompts, resource files, and solution-resource mechanics, see the `uipath-agents` skill — specifically `lowcode/capabilities/inline-in-flow/inline-in-flow.md`.
For coded (Python) agents, use the [`agent`](../agent/planning.md) plugin (`uipath.core.agent.{key}`) — inline agents are low-code only.

## Node Type

`uipath.agent.autonomous`

This is a fixed, OOTB node type (no `{key}` suffix). Inline agents do not appear in `registry search` — the single node type accepts any inline agent via its `inputs.source` field.

## When to Use

Use an inline agent node when the reasoning/judgment task is tightly scoped to this specific flow and you want the fastest path to a working agent.

### Inline vs Published Agent Decision Table

| Situation | Inline (`uipath.agent.autonomous`) | Published ([`uipath.core.agent.{key}`](../agent/planning.md)) |
| --- | --- | --- |
| Agent is specific to this one flow | Yes | No |
| Agent will be reused across flows or solutions | No | Yes |
| Agent needs independent versioning | No | Yes |
| Prototyping — fastest scaffolding | Yes | No |
| Agent is already published in the tenant | No — use the published node | Yes |

### Anti-Pattern

Do not inline an agent you intend to reuse. Inline agents are private to the flow project — if you later need to call the same agent from another flow, you must re-scaffold and re-configure it, diverging over time. Use a published agent for shared logic.

**Do NOT scaffold an inline agent to satisfy a prompt that names an existing agent.** If the prompt says "use the X agent" / "call the Y agent" / "invoke the Z coded agent" / "use the W low-code agent", the user is referring to a published agent. Search the tenant registry by name first: `uip maestro flow registry search "<name>" --output json`. Only scaffold inline when the user explicitly asks to **embed / inline / include / create** an agent inside this flow. The words "coded" and "low-code" describe the implementation style of a published agent — they are NOT synonyms for "inline".

### When NOT to Use

- **Agent already exists as a published tenant resource** — use the [published agent](../agent/planning.md) node instead
- **User references the agent by name** (existing agent) — search the tenant registry first; scaffold inline only if the user explicitly asks to embed/inline a new agent
- **Task is deterministic** — use [Script](../script/planning.md) or [Decision](../decision/planning.md)

## Ports

| Port | Position | Direction | Use |
| --- | --- | --- | --- |
| `input` | left | target | Flow sequence input |
| `success` | right | source | Normal flow output |
| `error` | right | source | Implicit error port (shared with all action nodes) — see [Implicit error port on action nodes](../../../../shared/file-format.md#implicit-error-port-on-action-nodes) |
| `tool` | bottom | source (artifact) | Connect tool resource nodes |
| `context` | bottom | source (artifact) | Connect context resource nodes |
| `escalation` | top | source (artifact) | Connect escalation resource nodes |

## Output Variables

- `$vars.{nodeId}.output.content` — the agent's text response
- `$vars.{nodeId}.error` — error details if the agent fails (`code`, `message`, `detail`, `category`, `status`)

## Scaffolding Prerequisite

Unlike published agents, inline agents are **not** discovered through the registry — they are created locally inside the flow project before (or during) flow build:

```bash
uip agent init "<FlowProjectDir>" --inline-in-flow --output json
```

Record the returned `ProjectId` — the flow node's `inputs.source` must match it exactly.

The scaffold sets `settings.model: "gpt-4o-2024-11-20"` (stale) and empty prompts — both are placeholders. During Phase 2 you MUST override the model (`uip agent model list` → newest GA per task) and author a robust system prompt + typed `outputSchema` per the obligations in [impl.md § Configure `agent.json`](impl.md#configure-agentjson). The skeleton, model-discovery command, and production checklist live in the `uipath-agents` skill's `model-selection-guide.md` and `agent-prompting-guide.md` (source of truth).

For agent.json configuration (prompts, model, schemas) and resource file authoring (tools, contexts, escalations), see the `uipath-agents` skill (`lowcode/agent-definition.md` and `lowcode/capabilities/`).

## Resource Nodes

The autonomous agent attaches resource nodes to its three artifact ports: tools (external or built-in) on `tool` (bottom), context on `context` (bottom), escalation on `escalation` (top). Decide which the agent needs at planning time. Full wiring — node JSON, edges, refresh, a single matrix covering all kinds — is in [impl.md § Adding Resource Nodes](impl.md#adding-resource-nodes); `resource.json` bodies are owned by the `uipath-agents` skill (`lowcode/capabilities/`).

- **External tool** (`tool` port) — agent calls a deployed automation. Four kinds; discover via the registry below. Needs `uip solution resources refresh`.
- **Built-in tool** (`tool` port) — platform-shipped tool, e.g. analyze-attachments. `registry get uipath.agent.resource.tool.builtin.<toolType>`. Self-contained — no bindings, no solution-level files, no `uip solution resources refresh`.
- **Context** (`context` port) — RAG retrieval from a Context Grounding index. `registry search "uipath.agent.resource.context"`, then `get` the matching `NodeType`. Needs `uip solution resources refresh`.
- **Escalation** (`escalation` port) — human-in-the-loop approval/review mid-run via a deployed Action Center app. `registry get uipath.agent.resource.escalation`. Needs `uip solution resources refresh`.

### External tools — registry discovery

The four external tool kinds share discovery, `resource.json` shape, and refresh — only the `type` field and the schema flavor differ (see § Subtypes in `process.md`). Pick the prefix per kind:

| Kind | Registry-search prefix | `resource.json.type` | What it calls |
|------|------------------------|----------------------|---------------|
| RPA process | `uipath.agent.resource.tool.process` | `process` | RPA workflow (XAML / coded) |
| Agent | `uipath.agent.resource.tool.agent` | `agent` | Low-code or coded agent |
| API workflow | `uipath.agent.resource.tool.api` | `api` | Coded API workflow |
| Process Orchestration | `uipath.agent.resource.tool.processorchestration` | `processOrchestration` | Agentic / orchestrated process |

```bash
uip maestro flow registry search "<prefix>" --output json
```

Filter rows where `NodeType` starts with `<prefix>.` and `DisplayName` matches. The `Description` field disambiguates same-named resources by folder. Fetch the full manifest:

```bash
uip maestro flow registry get "<NodeType>" --output json
```

For the tool's `resource.json` format and solution-level resource setup, see the `uipath-agents` skill (`lowcode/capabilities/process/`). Set `location` based on the discovery `Source` field: `"solution"` when `Source: "Local"`, `"external"` when `Source: "Remote"` (same rule as standalone agents — see `critical-rules.md` Rule 12). Set `properties.folderPath` to the **literal folder path from discovery** — parse it from the registry `Description` field (e.g., `(Shared/Sales)` → `"Shared/Sales"`) or from `uip solution resources get`. Do **not** leave `folderPath` empty — an empty `folderPath` prevents `uip solution resources refresh` from resolving the tool at runtime.

### IS Connector Tools

Use IS connector tools when the agent needs to call SaaS / API integrations exposed via UiPath Integration Service (Jira, Slack, Salesforce, ServiceNow, etc.).

Discovery:

```bash
uip maestro flow registry search "uipath.agent.resource.tool.connector" --output json
```

Filter rows where `NodeType` starts with `uipath.agent.resource.tool.connector.` and `DisplayName` matches. Fetch the full manifest:

```bash
uip maestro flow registry get "<NodeType>" --output json
```

IS connector tool nodes differ from RPA tools:
- **Configuration**: Use `uip maestro flow node configure` (same CLI carve-out as regular connector nodes) — see [connector/impl.md § Agent Tool Connector Nodes](../connector/impl.md#agent-tool-connector-nodes). The CLI auto-populates the `inputs.detail` request buckets (`bodyParameters` / `queryParameters` / `pathParameters`) for agent tool connector nodes — no `fieldsContainer`
- **Definition**: `bpmn:SendTask` / `Intsvc.ActivityExecution` / `bindings.resource: "Connection"` instead of process-style bindings
- **Flow bindings**: Connection bindings (ConnectionId + FolderKey) instead of process bindings (name + folderPath)
- **resource.json**: Auto-generated by `uip agent validate --inline-in-flow` from the flow node's `inputs.detail` — no manual authoring needed, but the flow node must be fully configured first

For detailed implementation, see [impl.md § Adding an IS Connector Tool Node](impl.md#adding-an-is-connector-tool-node).

### Anti-pattern

Do not use `uip agent tool add` to attach the tool to an inline-in-flow agent. That command is designed for standalone agent projects. For inline-in-flow RPA/process/agent/api tools, hand-author the tool's `resource.json` and let `uip solution resources refresh` materialize the solution-level files. For inline-in-flow IS connector tools, the `resource.json` is auto-generated by `uip agent refresh --inline-in-flow` from the configured flow node.

## Planning Annotation

In the architectural plan:

- `inline-agent: <description>` with a `<projectId-placeholder>` — the UUID is assigned during Phase 2 when `uip agent init --inline-in-flow` runs
- `inline-agent-tool: <ToolName> (<kind>, solution|external) → <name> in <folder-path>` — one line per external tool. `<kind>` is one of `process` | `agent` | `api` | `processOrchestration`.
- `inline-agent-tool: <ToolName> (connector, solution|external) → <connector-key>/<operation> via <connection-name>` — one line per IS connector tool
- `inline-agent-escalation: <EscalationName> → <AppName> in <folder-path>` — one line per escalation (Action Center HITL).
- `inline-agent-context: <ContextName> (index) → <IndexName> in <folder-path>` — one line per context resource.
- `inline-agent-builtin-tool: <ToolName> (<toolType>)` — one line per built-in tool; no folder (self-contained).
- If an existing published agent already covers the use case, prefer the [published agent](../agent/planning.md) annotation instead
