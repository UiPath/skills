# Inline Agent Node — Planning

Inline agent nodes embed an autonomous AI agent **inside** the flow file. The **full agent definition lives in the node's `inputs`** — prompts, model, schemas, and (per capability) every attached resource node's config. The GUID-named subdirectory (`<GUID>/agent.json` + `resources/` + `features/`) is a **derived artifact**: the flow canvas regenerates it from the `.flow` on every save. Never author it. Unlike [published agents](../agent/planning.md), the node type is fixed and the agent ships with the flow — no separate agent project, no tenant publishing step.

Authoring reference: [impl.md](impl.md). Prompt quality: [prompting/autonomous-agent-prompting-guide.md](prompting/autonomous-agent-prompting-guide.md). Model choice: [model-selection-guide.md](model-selection-guide.md). Mandatory constraints: [critical-rules.md](critical-rules.md).
For coded (Python) agents, use the [`agent`](../agent/planning.md) plugin (`uipath.core.agent.{key}`) — inline agents are low-code only.

## Node Type

`uipath.agent.autonomous`

Fixed OOTB node type (no `{key}` suffix). Inline agents do not appear in `registry search` — the single node type hosts any inline agent via its embedded `inputs`. Sibling types `uipath.agent.conversational` / `uipath.agent.voice` exist but are out of authoring scope — this plugin covers autonomous only.

## When to Use

Use an inline agent node when the reasoning/judgment task is tightly scoped to this specific flow and you want the fastest path to a working agent.

### Inline vs Published Agent Decision Table

| Situation | Inline (`uipath.agent.autonomous`) | Published ([`uipath.core.agent.{key}`](../agent/planning.md)) |
| --- | --- | --- |
| Agent is specific to this one flow | Yes | No |
| Agent will be reused across flows or solutions | No | Yes |
| Agent needs independent versioning | No | Yes |
| Prototyping — fastest path | Yes | No |
| Agent is already published in the tenant | No — use the published node | Yes |

### Anti-Pattern

Do not inline an agent you intend to reuse. Inline agents are private to the flow file — reusing the same agent from another flow means re-authoring it, diverging over time. Use a published agent for shared logic.

**Do NOT embed an inline agent to satisfy a prompt that names an existing agent.** If the prompt says "use the X agent" / "call the Y agent" / "invoke the Z coded agent" / "use the W low-code agent", the user is referring to a published agent. Search the tenant registry by name first: `uip maestro flow registry search "<name>" --output json`. Only embed inline when the user explicitly asks to **embed / inline / include / create** an agent inside this flow. The words "coded" and "low-code" describe the implementation style of a published agent — they are NOT synonyms for "inline".

### When NOT to Use

- **Agent already exists as a published tenant resource** — use the [published agent](../agent/planning.md) node instead
- **User references the agent by name** (existing agent) — search the tenant registry first; embed inline only if the user explicitly asks to embed/inline a new agent
- **Task is deterministic** — use [Script](../script/planning.md) or [Decision](../decision/planning.md)

## Ports

| Port | Position | Direction | Use |
| --- | --- | --- | --- |
| `input` | left | target | Flow sequence input |
| `success` | right | source | Normal flow output |
| `error` | right | source | Implicit error port (shared with all action nodes) — see [Implicit error port on action nodes](../../../../shared/file-format.md#implicit-error-port-on-action-nodes) |
| `tool` | bottom | source (artifact) | Tool resource nodes — process-family: [capabilities/process.md](capabilities/process.md); built-in: [capabilities/built-in-tools.md](capabilities/built-in-tools.md); IS connector: [capabilities/integration-service.md](capabilities/integration-service.md); MCP server: [capabilities/mcp.md](capabilities/mcp.md) |
| `context` | bottom | source (artifact) | Context resource nodes — [capabilities/context-index.md](capabilities/context-index.md) |
| `escalation` | top | source (artifact) | Escalation resource nodes — [capabilities/escalation.md](capabilities/escalation.md) |

The current autonomous manifest exposes no `memory` artifact handle — confirm via `registry get` before planning memory. There is no `mcp` handle either — MCP servers attach via the `tool` handle ([capabilities/mcp.md](capabilities/mcp.md)); note MCP greenfield authoring is gated on a registry gap (see that doc's callout).

## Output Variables

Declare typed outputs in `inputs.agentOutputVariables[]`; each field surfaces **flat**:

- `$vars.{nodeId}.output.{field}` — one per declared output variable (no `.content.` wrapper)
- `$vars.{nodeId}.output.content` — only when no typed outputs are declared (single text response)
- `$vars.{nodeId}.error` — error details if the agent fails (`code`, `message`, `detail`, `category`, `status`)

## Identity — Mint the UUIDs Yourself

Every inline agent node (and, per capability, most resource nodes) carries `inputs.source`: a **lowercase UUIDv4 you generate** (`python3 -c "import uuid; print(uuid.uuid4())"`). No scaffold command assigns it. It must be a real lowercase UUID because it becomes the derived sidecar's folder name, the packaging identity (`agent.json` `id` + `projectId`, package entry point), and the canvas file-watcher matches folders against a UUID regex — a human-readable or uppercase value breaks derivation. Author it explicitly: a node without `inputs.source` gets a fresh UUID minted by the canvas on open, orphaning any previously derived artifacts.

## Resource Nodes

The agent attaches resource nodes to its artifact ports (tools on `tool`, context on `context`, escalation on `escalation`). Each resource node carries its **full config in its own `inputs`** plus its own identity UUID (`inputs.source` for most kinds; built-ins vary — see [capabilities/built-in-tools.md § Identity](capabilities/built-in-tools.md#identity--two-patterns)), and connects via exactly one artifact edge. Decide which capabilities the agent needs at planning time; wiring mechanics live in [impl.md § Resource Nodes](impl.md#7-resource-nodes). Process-family tools: [capabilities/process.md](capabilities/process.md); built-in tools: [capabilities/built-in-tools.md](capabilities/built-in-tools.md); IS connector tools: [capabilities/integration-service.md](capabilities/integration-service.md); MCP server tools: [capabilities/mcp.md](capabilities/mcp.md) (greenfield gated on a registry gap — see that doc's callout); context grounding: [capabilities/context-index.md](capabilities/context-index.md); escalations: [capabilities/escalation.md](capabilities/escalation.md); remaining capability docs land per roadmap milestone.

## Planning Annotation

In the architectural plan:

- `inline-agent: <description>` — mint the `inputs.source` UUID during Phase 2 authoring
- `inline-agent-tool: <ToolName> (<kind>, solution|external) → <name> in <folder-path>` — one line per external tool. `<kind>` is one of `process` | `agent` | `api` | `processOrchestration` (annotation casing only — the node-type segment is lowercase: `…tool.processorchestration.<release-key>`).
- `inline-agent-escalation: <EscalationName> → <AppName> in <folder-path>` — one line per escalation (Action Center HITL) — [capabilities/escalation.md](capabilities/escalation.md).
- `inline-agent-context: <ContextName> (index) → <IndexName> in <folder-path>` — one line per context resource — [capabilities/context-index.md](capabilities/context-index.md).
- `inline-agent-builtin-tool: <ToolName> (<node-type suffix>)` — one line per built-in tool (`analyzefiles` | `summarize` | `batchtransform`); no folder (self-contained) — [capabilities/built-in-tools.md](capabilities/built-in-tools.md).
- `inline-agent-mcp: <ToolName> → <server-slug> in <folder-path>` — one line per MCP server tool — [capabilities/mcp.md](capabilities/mcp.md). Check the registry gap gate at planning time: `uip maestro flow registry search mcp` returning no `tool.mcp.*` entry means greenfield authoring is blocked — plan the canvas-attach path instead (see the doc's callout).
- If an existing published agent already covers the use case, prefer the [published agent](../agent/planning.md) annotation instead
