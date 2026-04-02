# Agent Nodes

Flow has two categories of agent nodes: **built-in agents** (OOTB, always available) and **published agent resources** (appear in registry after login).

## Implementation

### Built-in Agent Nodes

| Node Type | Description | Use Case |
|---|---|---|
| `uipath.agent.autonomous` | Reasons and acts independently | Classification, triage, summarization, multi-step reasoning |
| `uipath.agent.conversational` | Interactive multi-turn dialogue | Chat-based workflows, user Q&A |

These are OOTB nodes — available without publishing anything:

```bash
uip flow registry search "uipath.agent" --output json
```

### Published Agent Resources

Published agents appear as resource nodes:

| Node Type Pattern | Service Type | Category |
|---|---|---|
| `uipath.core.agent.{key}` | `Orchestrator.StartAgentJob` | `agent` |

Discovery:

```bash
uip flow registry pull --force
uip flow registry search agent --output json
uip flow registry get "uipath.core.agent.{key}" --output json
```

The `{key}` is the resource's unique identifier from Orchestrator.

### When to Use Agent vs Script/Decision

| Use an Agent node when... | Use Script/Decision/Switch when... |
|---|---|
| Input is ambiguous or unstructured (free text, emails, support tickets) | Input is structured and well-defined (JSON, form data) |
| The task requires reasoning or judgment (triage, classification, summarization) | The task is deterministic (if X then Y, map/filter/transform) |
| Branching depends on context that can't be reduced to simple conditions | Branching conditions are explicit and enumerable |
| You need natural language generation (draft emails, summaries) | You need data transformation or computation |

**Anti-pattern:** Don't use an agent node for tasks that can be done with a Decision + Script. Agents are slower, more expensive (LLM tokens), and less predictable.

**Hybrid pattern:** Use workflow nodes for the deterministic parts (fetch data, transform, route) and agent nodes for the ambiguous parts (classify intent, draft response, extract entities). The flow orchestrates; the agent reasons.

### Ports

Both built-in and resource agents share the same port structure:

| Input Port | Output Port(s) |
|---|---|
| `input` | `success` |

### Output Variables

- `$vars.{nodeId}.output` — the agent's response (structure depends on the agent)
- `$vars.{nodeId}.error` — error details if execution fails (`code`, `message`, `detail`, `category`, `status`)

### Creating a New Agent

If the flow needs a published agent that doesn't exist yet:

1. Add a `core.logic.mock` placeholder in the flow
2. Tell the user to use `uipath-coded-agents` (Python) to create and publish the agent
3. After publishing, refresh registry and replace the mock:

```bash
uip flow registry pull --force
uip flow registry search "<agent-name>" --output json
```

## Debug

### Common Errors

| Error | Cause | Fix |
|---|---|---|
| Agent resource not found in registry | Agent not published to Orchestrator | Publish the agent first, then `registry pull --force` |
| Agent times out | Agent processing takes too long | Check agent implementation for efficiency; consider breaking into smaller tasks |
| Agent returns unexpected output schema | Agent output doesn't match expected `$vars` references | Check `outputDefinition` from `registry get` and update downstream expressions |
| Input schema mismatch | Flow passes inputs the agent doesn't expect | Check `inputDefinition` from `registry get` for expected input names and types |

### Debug Tips

1. **Built-in agents don't need publishing** — `uipath.agent.autonomous` and `uipath.agent.conversational` are always available after login
2. **Resource agents need Orchestrator** — `uipath.core.agent.{key}` nodes require the agent to be published and the user to be logged in
3. **Agent output is unstructured** — unlike script nodes that return predictable JSON, agent output depends on the agent's implementation. Always check `outputDefinition` from registry before referencing `$vars.{nodeId}.output.*`
4. **Decision and Switch nodes cannot receive connections from agent resource nodes** — if you need to branch on agent output, route through a Script node first to extract the relevant value
