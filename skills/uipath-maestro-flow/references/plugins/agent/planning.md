# Agent Node — Planning

Agent nodes invoke UiPath AI agents from within a flow. Published agents appear in the registry after `uip login` + `uip maestro flow registry pull`. **In-solution** (unpublished) agents in sibling projects are discovered via `--local` — no login or publish required. Both **coded** (Python) and **low-code** (agent.json) agents appear here once deployed — the flow treats them identically.

> **Related plugin:** [inline-agent](../inline-agent/planning.md) covers low-code agents embedded as a UUID subdirectory **inside** the flow project (`uipath.agent.autonomous`). Coded agents always use this `agent` plugin, not `inline-agent`.

> **Choosing between coded and low-code, or wiring them into a flow:** see the `uipath-agents` skill — [coded-vs-lowcode-guide.md](../../../../uipath-agents/references/coded-vs-lowcode-guide.md) for the comparison, [coded/flow-integration.md](../../../../uipath-agents/references/coded/flow-integration.md) for coded-agent Flow patterns.

> **If the user names an existing agent, it is a published agent — not inline.** When a prompt says "use the X agent" / "call the Y agent" / "invoke the Z coded agent" / "use the W low-code agent", the user is referring to an agent that already exists in the tenant (or in-solution). ALWAYS run `uip maestro flow registry search "<name>" --output json` BEFORE deciding to scaffold an inline agent. The words "coded" and "low-code" describe the *implementation style* of a published agent — they do NOT mean "inline". Inline (`uipath.agent.autonomous`) is only correct when the user explicitly asks to embed, inline, or create a new agent from scratch inside this flow.

## Node Type Pattern

`uipath.core.agent.{key}`

The `{key}` is the agent's unique identifier (typically a GUID) from Orchestrator.

## When to Use

Use an Agent node when the flow needs to invoke a published AI agent for reasoning, judgment, or natural language processing.

### Agent vs Script/Decision Decision Table

| Use an Agent node when... | Use Script/Decision/Switch when... |
| --- | --- |
| Input is ambiguous or unstructured (free text, emails, support tickets) | Input is structured and well-defined (JSON, form data) |
| Task requires reasoning or judgment (triage, classification, summarization) | Task is deterministic (if X then Y, map/filter/transform) |
| Branching depends on context that can't be reduced to simple conditions | Branching conditions are explicit and enumerable |
| You need natural language generation (draft emails, summaries) | You need data transformation or computation |

### Anti-Pattern

Don't use an agent node for tasks that can be done with a Decision + Script. Agents are slower, more expensive (LLM tokens), and less predictable. Use them where their flexibility is actually needed.

### Hybrid Pattern

Use workflow nodes for the deterministic parts (fetch data, transform, route) and agent nodes for the ambiguous parts (classify intent, draft response, extract entities). The flow orchestrates; the agent reasons.

### When NOT to Use

- **Agent in the same solution but not yet published** — use `--local` discovery (see below)
- **Agent does not exist yet** — tell the user to create it in the same solution with `uipath-agents`, then use `--local` discovery
- **Task is deterministic** — use [Script](../script/planning.md) or [Decision](../decision/planning.md)
- **Need to call an external service API** — use [Connector](../connector/planning.md) or [HTTP](../http/planning.md)
- **Agent should be a tool for another agent** — don't use this node; instead add the agent as a tool resource (`uipath.agent.resource.tool.agent`) wired to a parent agent node. See the `uipath-agents` skill for the resource file format

## Ports

| Input Port | Output Port(s) |
| --- | --- |
| `input` | `output`, `error` |

The `error` port is the implicit error port shared with all action nodes — see [Implicit error port on action nodes](../../flow-file-format.md#implicit-error-port-on-action-nodes).

## Output Variables

- `$vars.{nodeId}.output` — the agent's response (contains `content` string)
- `$vars.{nodeId}.error` — error details if the agent fails (`code`, `message`, `detail`, `category`, `status`)

## Discovery

**Published (tenant registry):**

```bash
uip maestro flow registry pull --force
uip maestro flow registry search "uipath.core.agent" --output json
```

Requires `uip login`. Returns published tenant resources only — for in-solution sibling projects, use the `--local` discovery below.

**In-solution (local, no login required):**

```bash
uip maestro flow registry list --local --output json
uip maestro flow registry get "<nodeType>" --local --output json
```

Run from inside the flow project directory. Discovers sibling agent projects in the same `.uipx` solution.

## Planning Annotation

In the architectural plan:
- If the agent exists: note as `resource: <agent-name> (agent)`
- If it does not exist: note as `[CREATE NEW] <description>` with skill `uipath-agents`
