# Inline Agent Node — Planning

Inline agent nodes embed an autonomous AI agent **inside** the flow. The agent is authored on the `.flow` itself — prompts, model, settings, and guardrails on the agent node; each tool / context / escalation / memory on its own resource node — and is published together with the flow: no separate agent project, no tenant publishing step. `uip agent refresh --inline-in-flow` generates the `<projectId>/` folder that packaging reads; it is never edited by hand. Unlike [published agents](../agent/planning.md), the node type is fixed and the agent is bound to the flow via a local `projectId` rather than a registry-resolved resource key.

For agent design (prompts, model choice, per-capability discovery) and solution-resource mechanics, see the `uipath-agents` skill — specifically `lowcode/capabilities/inline-in-flow/inline-in-flow.md`.
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
| `error` | right | source | Implicit error port (shared with all action nodes) — see [Implicit error port on action nodes](../../../shared/file-format.md#implicit-error-port-on-action-nodes) |
| `tool` | bottom | source (artifact) | Connect tool resource nodes |
| `context` | bottom | source (artifact) | Connect context resource nodes |
| `escalation` | top | source (artifact) | Connect escalation resource nodes |
| `memory` | top | source (artifact) | Connect memory space resource nodes |

## Output Variables

- `$vars.{nodeId}.output.<field>` — one per `inputs.agentOutputVariables[]` entry (typed output; the default)
- `$vars.{nodeId}.output.content` — the agent's text response, only when the node declares the single untyped `content` output
- `$vars.{nodeId}.error` — error details if the agent fails (`code`, `message`, `detail`, `category`, `status`)

## Scaffolding Prerequisite

Unlike published agents, inline agents are **not** discovered through the registry — the agent is created locally inside the flow project before (or during) flow build:

```bash
uip agent init "<FlowProjectDir>" --inline-in-flow --output json
```

Record the returned `ProjectId` — the agent node's `inputs.source` must match it exactly.

During Phase 2 author the agent **on the node**: a real `model` (`uip agent model list` → newest GA per task), a robust `systemPrompt` + `userPrompt` that reference flow data as `{{ $vars.<nodeId>.output.<field> }}`, and one typed `agentOutputVariables[]` entry per output field — see [impl.md § Agent node inputs](impl.md#agent-node-inputs). The prompt skeleton, model-discovery command, and production checklist live in the `uipath-agents` skill's `model-selection-guide.md` and `agent-prompting-guide.md` (source of truth). Never edit the scaffolded `<projectId>/agent.json` — refresh regenerates it from the node.

## Resource Nodes

The autonomous agent attaches resource nodes to its artifact ports: tools (external, connector, MCP, or built-in) on `tool` (bottom), context on `context` (bottom), escalation and memory on `escalation` / `memory` (top). Decide which the agent needs at planning time. Each resource's configuration lives on its node's `inputs`, seeded from the definition's `inputDefaults`. Full wiring — node JSON, inputs per kind, edges, refresh — is in [impl.md § Adding Resource Nodes](impl.md#adding-resource-nodes); discovery and design per capability live in the `uipath-agents` skill (`lowcode/capabilities/`).

- **External tool** (`tool` port) — agent calls a deployed automation. Four kinds; discover via the registry below. Needs `uip solution resources refresh`.
- **Built-in tool** (`tool` port) — platform-shipped tool, e.g. analyze-attachments. `registry get uipath.agent.resource.tool.builtin.<toolType>`. Self-contained — no bindings, no solution-level files, no `uip solution resources refresh`.
- **Context** (`context` port) — RAG retrieval from a Context Grounding index. `registry search "uipath.agent.resource.context"`, then `get` the matching `NodeType`. Needs `uip solution resources refresh`.
- **Escalation** (`escalation` port) — human-in-the-loop approval/review mid-run via a deployed Action Center app. `registry get uipath.agent.resource.escalation`. Needs `uip solution resources refresh`.

### External tools — registry discovery

The four external tool kinds share discovery, node inputs, and refresh — only the node-type prefix differs (the generated `resource.json.type` follows from it). Pick the prefix per kind:

| Kind | Registry-search prefix | Generated `resource.json.type` | What it calls |
|------|------------------------|--------------------------------|---------------|
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

Seed the tool node's `inputs` from the manifest's `inputDefaults`, then set `referenceKey`, `folderPath`, and `properties.folderPath` to the **literal folder path from discovery** — parse it from the registry `Description` field (e.g., `(Shared/Sales)` → `"Shared/Sales"`) or from `uip solution resources get`. Do **not** leave `folderPath` empty — an empty `folderPath` prevents `uip solution resources refresh` from resolving the tool at runtime. Node inputs per kind: [impl.md § 3. Set the resource inputs](impl.md#3-set-the-resource-inputs).

### Anti-pattern

Do not use `uip agent tool add` or `uip agent memory add` for an inline-in-flow agent, and do not hand-author a `resource.json` under `<projectId>/resources/`. Both write the generated folder: refresh deletes an entry that has no resource node and overwrites one that has. Add the resource node to the `.flow`; refresh writes the `resource.json`, and `uip solution resources refresh` materializes the solution-level files.

## Planning Annotation

In the architectural plan:

- `inline-agent: <description>` with a `<projectId-placeholder>` — the UUID is assigned during Phase 2 when `uip agent init --inline-in-flow` runs
- `inline-agent-tool: <ToolName> (<kind>, solution|external) → <name> in <folder-path>` — one line per external tool. `<kind>` is one of `process` | `agent` | `api` | `processOrchestration`.
- `inline-agent-escalation: <EscalationName> → <AppName> in <folder-path>` — one line per escalation (Action Center HITL).
- `inline-agent-context: <ContextName> (index) → <IndexName> in <folder-path>` — one line per context resource.
- `inline-agent-builtin-tool: <ToolName> (<toolType>)` — one line per built-in tool; no folder (self-contained).
- `inline-agent-memory: <MemoryName> → <MemorySpaceName> in <folder-path>` — one line per memory space.
- If an existing published agent already covers the use case, prefer the [published agent](../agent/planning.md) annotation instead
