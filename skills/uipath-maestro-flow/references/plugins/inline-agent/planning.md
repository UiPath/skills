# Inline Agent Node — Planning

Inline agent nodes embed an autonomous AI agent **inside** the flow project. The agent definition lives as a subdirectory of the flow project and is published together with the flow — no separate agent project, no tenant publishing step. Unlike [published agents](../agent/planning.md), the node type is fixed and the agent is bound to the flow via a local `projectId` rather than a registry-resolved resource key.

## Node Type

`uipath.agent.autonomous`

This is a fixed, OOTB node type (no `{key}` suffix). Inline agents do not appear in `registry search` — the single node type accepts any inline agent via its `model.source` field.

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
| `error` | right | source | Implicit error port (shared with all action nodes) — see [Implicit error port on action nodes](../../flow-file-format.md#implicit-error-port-on-action-nodes) |
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

This creates a `<FlowProjectDir>/<projectId-uuid>/` directory containing `agent.json`, `flow-layout.json`, and empty `evals/`, `features/`, `resources/` subdirectories. Record the returned `ProjectId` — the flow node's `model.source` must match it exactly.

No `uip login` or registry refresh is required for this workflow.

## Planning Annotation

In the architectural plan:

- `inline-agent: <description>` with a `<projectId-placeholder>` — the UUID is assigned during Phase 2 when `uip agent init --inline-in-flow` runs
- If an existing published agent already covers the use case, prefer the [published agent](../agent/planning.md) annotation instead
