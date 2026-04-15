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

For agent.json configuration (prompts, model, schemas) and resource file authoring (tools, contexts, escalations), see the `uipath-agents` skill (`lowcode/agent-definition.md` and `lowcode/capabilities/`).

## Tools — Flow Registry Discovery

The autonomous agent's `tool` artifact port accepts inline tool resource nodes. **External RPA process tools** are the primary supported case. Discovery uses the flow registry:

```bash
uip maestro flow registry search "uipath.agent.resource.tool.process" --output json
```

Filter rows where `NodeType` starts with `uipath.agent.resource.tool.process.` and `DisplayName` matches. The `Description` field disambiguates same-named processes by folder. Fetch the full manifest:

```bash
uip maestro flow registry get "<NodeType>" --output json
```

For the tool's `resource.json` format and solution-level resource setup, see the `uipath-agents` skill (`lowcode/capabilities/process/`). Note the inline-in-flow convention: `location: "solution"` (not `"external"`), `properties.folderPath: ""`.

### Anti-pattern

Do not use `uip agent tool add` to attach the tool to an inline-in-flow agent. That command is designed for standalone agent projects. For inline-in-flow agents, hand-author the tool's `resource.json` and let `uip solution resource refresh` materialize the solution-level files.

## Planning Annotation

In the architectural plan:

- `inline-agent: <description>` with a `<projectId-placeholder>` — the UUID is assigned during Phase 2 when `uip agent init --inline-in-flow` runs
- `inline-agent-tool: <ToolName> (rpa, external) → <process-name> in <folder-path>` — one line per tool
- If an existing published agent already covers the use case, prefer the [published agent](../agent/planning.md) annotation instead
