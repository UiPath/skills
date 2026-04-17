# Flow Node & Architecture Reference

Reference for discovering node types, selecting the right node for each job, wiring edges correctly, and applying common topology patterns. Use this while building a flow in Step 4 of [SKILL.md](../SKILL.md).

---

## Capability Discovery

**When to run:** The flow uses connector nodes (external services) or resource nodes (RPA processes, agents, other flows). **Skip** if the flow only uses OOTB nodes (scripts, HTTP, branching, loops).

Discovery answers "what can I work with?" before you commit to a topology. This prevents designing around a connector that doesn't exist, an operation the connector doesn't support, or an RPA process / agent that hasn't been published yet.

```bash
# Registry should already be refreshed (Step 3 in Quick Start runs `registry pull`)
uip flow registry search <keyword> --output json    # search by service, resource name, or category
uip flow registry search outlook --output json       # example: does an Outlook connector exist?
uip flow registry search "invoice process" --output json  # example: is an RPA process published?
uip flow registry search agent --output json         # example: what agents are available?
uip flow registry list --output json                 # list all available node types
```

> **Auth note:** Without `uip login`, the registry shows OOTB nodes only. After login, tenant-specific connector and resource nodes are also available. If the flow requires connectors or resources, verify login status first: `uip login status --output json`.

### Check Connector Connections

For each connector found in registry search, verify a healthy connection exists. See [plugins/connector/planning.md](plugins/connector/planning.md) for the full connection check workflow.

```bash
uip is connections list "<connector-key>" --output json
```

- If a default enabled connection exists (`IsDefault: Yes`, `State: Enabled`), record the connection ID for the build step.
- **If no connection exists**, tell the user and stop — they must create the connection (OAuth / admin approval may be needed) before the flow can use the connector.

**What to record from discovery:**
- **Connectors:** Whether a connector exists for each external service, available operations (from node type names), and whether a healthy connection exists. Field details require `registry get --connection-id` before adding the node.
- **Resources:** Whether a published node exists for each RPA process, agent, or flow referenced in the requirements (e.g., `uipath.core.rpa.invoice-abc123`). Input/output schemas require `registry get` before adding the node (no connection needed for resources).
- **Gaps:** Services with no connector → fall back to `core.action.http`. Resources not yet published → use `core.logic.mock` placeholder and flag the gap to the user.

Use these findings to select the right node types from the [Plugin Index](#plugin-index). If a connector doesn't exist, fall back to `core.action.http`.

---

## Plugin Index

Each plugin has a `planning.md` with full selection heuristics, ports, key inputs, and wiring rules. **Read the relevant plugin's planning.md** when selecting that node type for your flow.

### Triggers

| Node Type | Plugin | When to Select |
| --- | --- | --- |
| `core.trigger.manual` | _(inline — no plugin)_ | Flow is started on demand by a user or API call |
| `core.trigger.scheduled` | [scheduled-trigger](plugins/scheduled-trigger/planning.md) | Flow runs on a recurring schedule |
| IS connector trigger | [connector-trigger](plugins/connector-trigger/planning.md) | Flow starts when an external event fires (e.g., email received, issue created). Node type: `uipath.connector.trigger.<key>.<trigger>` |

**Rules:**
- Every flow must have exactly one trigger node
- The trigger is always the first node in the topology
- IS connector triggers replace the manual trigger as the start node — they cannot coexist with `core.trigger.manual` or `core.trigger.scheduled`
- `core.trigger.manual` has no inputs and outputs on port `output` — it is simple enough to use without a plugin reference

### Actions

| Node Type | Plugin | When to Select |
| --- | --- | --- |
| `core.action.script` | [script](plugins/script/planning.md) | Custom logic, data transformation, computation, formatting |
| `core.action.http` | [http](plugins/http/planning.md) | Call a REST API where no connector exists, or quick prototyping |
| `core.action.transform` | [transform](plugins/transform/planning.md) | Declarative map, filter, or group-by on a collection |
| `core.logic.delay` | [delay](plugins/delay/planning.md) | Pause execution for a duration or until a specific date |
| `core.action.queue.create` | [queue](plugins/queue/planning.md) | Distribute work to robots — fire-and-forget |
| `core.action.queue.create-and-wait` | [queue](plugins/queue/planning.md) | Distribute work to robots — wait for result |

### Control Flow

| Node Type | Plugin | When to Select |
| --- | --- | --- |
| `core.logic.decision` | [decision](plugins/decision/planning.md) | Binary branching (if/else) based on a boolean condition |
| `core.logic.switch` | [switch](plugins/switch/planning.md) | Multi-way branching (3+ paths) based on ordered case expressions |
| `core.logic.loop` | [loop](plugins/loop/planning.md) | Iterate over a collection of items |
| `core.logic.merge` | [merge](plugins/merge/planning.md) | Synchronize parallel branches before continuing |
| `core.control.end` | [end](plugins/end/planning.md) | Graceful flow completion (one per terminal path) |
| `core.logic.terminate` | [terminate](plugins/terminate/planning.md) | Abort entire flow immediately on fatal error |
| `core.subflow` | [subflow](plugins/subflow/planning.md) | Group related steps into a reusable container with isolated scope |

### Connector Nodes

Connector nodes call external services via Integration Service. They are **not** built-in — they come from the registry after `uip login` + `uip flow registry pull`.

| When to Select | Plugin |
| --- | --- |
| A pre-built connector exists for the target service (Jira, Slack, Salesforce, etc.) | [connector](plugins/connector/planning.md) |

**How to use:** Run [Capability Discovery](#capability-discovery) to confirm the connector exists and identify the operation, then resolve the exact node type, connection, and fields via [connector/impl.md](plugins/connector/impl.md) while building.

### Agent Nodes

Agent nodes invoke AI agents for reasoning, judgment, or natural language tasks. Two kinds exist — pick based on reuse and lifecycle:

| Node Type Pattern | Plugin | When to Select |
| --- | --- | --- |
| `uipath.agent.autonomous` | [inline-agent](plugins/inline-agent/planning.md) | Agent is defined **inside** this flow project (scaffolded via `uip agent init --inline-in-flow`), tightly coupled to this flow, no separate versioning or cross-flow reuse |
| `uipath.core.agent.{key}` | [agent](plugins/agent/planning.md) | Agent is a **published tenant resource** (appears in the registry after `uip login` + `uip flow registry pull`); reusable across flows, independently versioned |

See [inline-agent/planning.md — Inline vs Published Agent Decision Table](plugins/inline-agent/planning.md#inline-vs-published-agent-decision-table) for the full decision matrix.

### Resource Nodes (External Automations)

Resource nodes invoke published UiPath automations. They are tenant-specific and appear in the registry after `uip login` + `uip flow registry pull`.

| Category | Node Type Pattern | Plugin |
| --- | --- | --- |
| RPA Process | `uipath.core.rpa.{key}` | [rpa](plugins/rpa/planning.md) |
| Agent | `uipath.core.agent.{key}` | [agent](plugins/agent/planning.md) |
| Agentic Process | `uipath.core.agentic-process.{key}` | [agentic-process](plugins/agentic-process/planning.md) |
| Flow | `uipath.core.flow.{key}` | [flow](plugins/flow/planning.md) |
| API Workflow | `uipath.core.api-workflow.{key}` | [api-workflow](plugins/api-workflow/planning.md) |
| Human Task | `uipath.core.hitl.{key}` | [hitl](plugins/hitl/planning.md) |

### Placeholders

| Node Type | When to Select |
| --- | --- |
| `core.logic.mock` | Step is TBD, resource doesn't exist yet, or prototyping. Placeholder with `input` -> `output` |

---

## Selecting External Service Nodes

When the flow needs to call an external service, use this decision order — prefer higher tiers:

1. **Pre-built Integration Service connector** — Use when a connector exists and covers the use case. See [connector](plugins/connector/planning.md).
2. **HTTP Request within a connector** — Use when a connector exists but lacks the specific endpoint. See [connector](plugins/connector/planning.md) HTTP Fallback section.
3. **Standalone HTTP Request** (`core.action.http`) — Use for one-off API calls to services without connectors. See [http](plugins/http/planning.md).
4. **RPA workflow node** — Use only when the target system has no API (legacy desktop apps, terminals). See [rpa](plugins/rpa/planning.md).

---

## Standard Port Reference

Use this when defining edges. Every edge requires a `sourcePort` and `targetPort`.

| Node Type | Input Port(s) | Output Port(s) |
| --- | --- | --- |
| `core.trigger.manual` | — | `output` |
| `core.trigger.scheduled` | — | `output` |
| `uipath.connector.trigger.*` | — | `output` |
| `core.action.script` | `input` | `success` |
| `core.action.http` | `input` | `default`, `branch-{id}` (dynamic per branch) |
| `core.action.transform` | `input` | `output` |
| `core.logic.delay` | `input` | `output` |
| `core.logic.decision` | `input` | `true`, `false` |
| `core.logic.switch` | `input` | `case-{id}` (dynamic per case), `default` |
| `core.logic.loop` | `input`, `loopBack` | `success`, `output` |
| `core.logic.merge` | `input` (multiple) | `output` |
| `core.control.end` | `input` | — |
| `core.logic.terminate` | `input` | — |
| `core.subflow` | `input` | `output`, `error` |
| `core.logic.mock` | `input` | `output` |
| `uipath.agent.autonomous` | `input` | `success`, `error`, `tool`, `context`, `escalation` |
| `uipath.core.agent.*` | `input` | `output` |
| `core.action.queue.create` | `input` | `success` |
| `core.action.queue.create-and-wait` | `input` | `success` |

---

## Wiring Rules

Apply these when defining edges in the topology:

1. Edges connect a **source port** (output) on one node to a **target port** (input) on another
2. Trigger nodes have no input port — they are always edge sources, never targets
3. End/Terminate nodes have no output port — they are always edge targets, never sources
4. Every non-trigger node must have at least one incoming edge
5. Every non-terminal node must have at least one outgoing edge
6. Decision nodes produce exactly two outgoing edges: one from `true`, one from `false`
7. Switch nodes produce one outgoing edge per case + optionally one from `default`
8. Loop nodes: the `loopBack` port receives the edge returning from the last node inside the loop body; `success` fires after all iterations
9. Merge nodes accept multiple incoming edges (one per parallel path being synchronized)
10. Do not create cycles except through Loop's `loopBack` mechanism
11. **No dangling nodes** — every node must be connected by at least one edge. A node with no incoming and no outgoing edges is invalid. Verify every node in the node table appears in the edge table as either a source or target.

---

## Common Topology Patterns

Use these as building blocks when designing your flow.

### Linear Pipeline

```
Trigger -> Action A -> Action B -> Action C -> End
```

### Conditional Branch

```
Trigger -> Fetch Data -> Decision
  |-- true -> Process -> End
  |-- false -> Log Skip -> End
```

### Parallel Execution with Merge

```
Trigger -> Prepare
  |-- Call API A --+
  |-- Call API B --+
                   +-- Merge -> Combine -> End
```

### Loop Over Collection

```
Trigger -> Fetch List -> Loop
  |-- [loop body] Process Item -> (loopBack)
  |-- success -> Summarize -> End
```

### Error Handling

```
Trigger -> HTTP Request -> Decision (error?)
  |-- true -> Log Error -> Terminate
  |-- false -> Process -> End
```

### Orchestration (Mixed Resources)

```
Trigger -> Script (prepare) -> RPA Process (extract) -> Agent (classify) -> Decision
  |-- approved -> Script (format) -> End
  |-- rejected -> Human Task (review) -> End
```

### Scheduled Batch Processing

```
Scheduled Trigger -> HTTP (fetch batch) -> Loop
  |-- Queue Create (per item) -> (loopBack)
  |-- success -> Script (summary) -> End
```


## Node Selection Heuristics

Quick decision guide. For full details, read the linked plugin's `planning.md`.

### "I need to call an external service"

1. Is there a connector? -> [connector](plugins/connector/planning.md)
2. No connector, but has a REST API? -> [http](plugins/http/planning.md)
3. No API at all (desktop app, terminal)? -> [rpa](plugins/rpa/planning.md) or `core.logic.mock` if unpublished

### "I need to branch"

- Two paths -> [decision](plugins/decision/planning.md)
- Three or more paths -> [switch](plugins/switch/planning.md)
- Branch on HTTP response status -> [http](plugins/http/planning.md) built-in branches

### "I need to transform data"

- Standard map/filter/group-by -> [transform](plugins/transform/planning.md)
- Custom logic, string manipulation, computation -> [script](plugins/script/planning.md)

### "I need to end the flow"

- Normal completion -> [end](plugins/end/planning.md) (one per terminal path)
- Fatal error, abort everything -> [terminate](plugins/terminate/planning.md)

### "I need to wait"

- Fixed duration -> [delay](plugins/delay/planning.md)
- Wait until a specific time -> [delay](plugins/delay/planning.md)
- Wait for external work to complete -> [queue](plugins/queue/planning.md) (`create-and-wait`)

### "I need human involvement"

- Human approval or data entry -> [hitl](plugins/hitl/planning.md) or `core.logic.mock` if the app doesn't exist

### "I need an AI agent"

- Agent is tightly coupled to this flow, not reused -> [inline-agent](plugins/inline-agent/planning.md) (`uipath.agent.autonomous`)
- Agent is a published tenant resource, reused across flows -> [agent](plugins/agent/planning.md) (`uipath.core.agent.{key}`)

### "The flow needs something outside flow capabilities"

1. Add a `core.logic.mock` placeholder
2. Note what needs to be created and which skill handles it:
   - Desktop/browser automation or coded workflow (C#) -> `uipath-rpa`
   - Agent -> `uipath-agents`
3. Re-check `registry search` before finalizing the flow — replace the mock if the resource has since been published
