# Agent Node — Planning

Agent nodes invoke published UiPath AI agents from within a flow. They are tenant-specific resources that appear in the registry after `uip login` + `uip flow registry pull`.

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

- **Agent not yet published** — use `core.logic.mock` placeholder and tell the user to create the agent with `uipath-agents`
- **Task is deterministic** — use [Script](../script/planning.md) or [Decision](../decision/planning.md)
- **Need to call an external service API** — use [Connector](../connector/planning.md) or [HTTP](../http/planning.md)

## Ports

| Input Port | Output Port(s) |
| --- | --- |
| `input` | `output` |

## Output Variables

- `$vars.{nodeId}.output` — the agent's response (contains `content` string)
- `$vars.{nodeId}.error` — error details if the agent fails (`code`, `message`, `detail`, `category`, `status`)

## Discovery

```bash
uip flow registry pull --force
uip flow registry search "uipath.core.agent" --output json
```

Requires `uip login`. Only published agents from your tenant appear.

## Planning Annotation

In the architectural plan:
- If the agent exists: note as `resource: <agent-name> (agent)`
- If it does not exist: note as `[CREATE NEW] <description>` with skill `uipath-agents`
