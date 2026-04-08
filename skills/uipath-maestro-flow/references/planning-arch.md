# Planning Phase 1: Discovery & Architectural Design

Discover available capabilities, then design the flow topology — select node types, define edges, and identify expected inputs and outputs. This phase produces a **mermaid diagram** and structured tables that can be reviewed before any implementation work begins.

> **Registry rules for this phase:**
> - **`registry search` and `registry list` are ALLOWED** — use them to discover what connectors, resources, and operations exist before committing to a topology.
> - **`registry get` is NOT allowed** — detailed metadata, connection binding, and reference field resolution are handled in [Planning Phase 2: Implementation](planning-impl.md).

---

## Process

1. Analyze the user's requirements
2. **Discover capabilities** — if the flow uses connector or resource nodes, run `registry search` / `registry list` to confirm they exist and identify available operations (see [Capability Discovery](#capability-discovery))
3. Select node types from the [Plugin Index](#plugin-index) below — read each relevant plugin's `planning.md` for selection heuristics, ports, and key inputs
4. Define edges (how nodes connect) — see [Wiring Rules](#wiring-rules) and each plugin's port documentation
5. Identify suspected inputs and outputs for each node
6. Generate a mermaid diagram
7. Validate the mermaid syntax (see [Mermaid Validation Rules](#mermaid-validation-rules))
8. Present the plan for user review
9. Iterate until approved, then hand off to [Planning Phase 2: Implementation](planning-impl.md)

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

- If a default enabled connection exists (`IsDefault: Yes`, `State: Enabled`), record the connection ID for Phase 2.
- **If no connection exists**, surface it in the **Open Questions** section of the architectural plan so the user can create it while reviewing. Creating a connection may involve OAuth flows or admin approval — front-loading this avoids blocking Phase 2.

> This is a lightweight existence check, not full connection binding. Phase 2 will ping the connection, fetch enriched metadata, and resolve reference fields.

**What to record from discovery:**
- **Connectors:** Whether a connector exists for each external service, available operations (from node type names), and whether a healthy connection exists. Field details require `registry get --connection-id` in Phase 2.
- **Resources:** Whether a published node exists for each RPA process, agent, or flow referenced in the requirements (e.g., `uipath.core.rpa.invoice-abc123`). Input/output schemas require `registry get` in Phase 2 (no connection needed for resources).
- **Gaps:** Services with no connector -> fall back to `core.action.http`. Resources not yet published -> use `core.logic.mock` placeholder. Connectors with no connection -> flag in Open Questions for the user to create.

Use these findings to select the right node types from the [Plugin Index](#plugin-index). If a connector doesn't exist, fall back to `core.action.http` or note it as a gap in Open Questions.

> **Do NOT run `registry get` during discovery.** Search results give you node type names — enough to know what connectors and operations exist. `is connections list` confirms connection availability. Detailed field metadata (required fields, types, enums, reference resolution) requires `registry get --connection-id` and belongs to Phase 2.

---

## Plugin Index

Each plugin has a `planning.md` with full selection heuristics, ports, key inputs, and wiring rules. **Read the relevant plugin's planning.md** when selecting that node type for your flow.

### Triggers

| Node Type | Plugin | When to Select |
| --- | --- | --- |
| `core.trigger.manual` | _(inline — no plugin)_ | Flow is started on demand by a user or API call |
| `core.trigger.scheduled` | [scheduled-trigger](plugins/scheduled-trigger/planning.md) | Flow runs on a recurring schedule |

**Rules:**
- Every flow must have exactly one trigger node
- The trigger is always the first node in the topology
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

**In this phase:** Use [Capability Discovery](#capability-discovery) to confirm the connector exists and note it as `connector: <service-name>` with the intended operation. Phase 2 resolves the exact type, connection, and fields via [connector/impl.md](plugins/connector/impl.md).

### Agent Nodes

Agent nodes invoke published UiPath AI agents. They are tenant-specific resources that appear in the registry after `uip login` + `uip flow registry pull`.

| Node Type Pattern | Plugin | When to Select |
| --- | --- | --- |
| `uipath.core.agent.{key}` | [agent](plugins/agent/planning.md) | Task requires reasoning, judgment, or natural language processing via a published agent |

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

---

## Output Format

Generate a `<SolutionName>.arch.plan.md` file in the **solution directory** (the folder containing the `.uipx` file, not the project subfolder). The plan covers the entire solution — which may contain multiple projects in the future.

### 1. Summary

2-3 sentences describing what the flow does end-to-end.

### 2. Flow Diagram (Mermaid)

A mermaid flowchart showing all nodes, edges, and branching logic.

**Requirements:**

- Use `graph TD` (top-down) for most flows; `graph LR` (left-right) only for very linear flows with few branches. Do NOT use `flowchart` — it is not supported by all mermaid renderers.
- Use `subgraph` blocks to group related sections — required for flows with 10+ nodes
- Label every edge with the port name (e.g., `-->|success|`, `-->|true|`, `-->|false|`)
- **Labels must be plain text only** — no special characters inside shape delimiters. The following break mermaid parsing:
  - `>` and `<` (interpreted as shape operators or HTML) — replace with words like "over" or "under"
  - `(`, `)`, `[`, `]`, `{`, `}` (conflict with shape delimiters)
  - `:`, `;`, `?`, `&`, `"` (unreliable across renderers)
  - Use plain alphanumeric text and spaces only
- Do NOT put node types in diagram labels — node types belong in the Node Table only
- Do NOT use quotes inside shape delimiters — use `[Text]` not `["Text"]`
- Use only these universally supported node shapes:
  - Triggers: rounded rectangle `(Trigger Name)`
  - Actions: rectangle `[Action Name]`
  - Control flow: diamond `{Decision Name}` for Decision/Switch
  - End/Terminate: rounded rectangle `(Done)`
  - Connectors: rectangle `[Connector Service Operation]`
  - Placeholders: rectangle `[Mock Description]`

**Example:**

````markdown
```mermaid
graph TD
    trigger(Manual Trigger)
    fetchOrders[Fetch Orders]
    checkStatus{Check Status}
    processOrder[Process Order]
    notifySlack[Slack Send Message]
    logSkip[Log Skip]
    doneSuccess(Done)
    doneSkip(Done)
    trigger -->|output| fetchOrders
    fetchOrders -->|default| checkStatus
    checkStatus -->|true| processOrder
    checkStatus -->|false| logSkip
    processOrder -->|success| notifySlack
    notifySlack -->|success| doneSuccess
    logSkip -->|success| doneSkip
```
````

### 3. Node Table

| # | Node ID | Name | Category | Node Type | Inputs | Outputs | Notes |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | trigger | Manual Trigger | trigger | `core.trigger.manual` | — | Trigger event | — |
| 2 | fetchOrders | Fetch Orders | action | `core.action.http` | `method: GET`, `url: <ORDERS_API_URL>` | `output.body` (order list), `output.statusCode` | Phase 2: confirm URL and auth |
| 3 | checkStatus | Check Status | control | `core.logic.decision` | `expression: =js:$vars.fetchOrders.output.statusCode === 200` | Routes to `true` or `false` | — |

**Column definitions:**

- **Node ID**: Short camelCase identifier used in the mermaid diagram and edge table
- **Inputs**: Best-guess input values based on user requirements. Use `<PLACEHOLDER>` for values Phase 2 must resolve (URLs, IDs, connection details)
- **Outputs**: What downstream nodes are expected to consume via `$vars.{nodeId}.*`
- **Notes**: Implementation concerns for Phase 2 (e.g., "Phase 2: resolve Jira project ID", "Phase 2: bind Slack connection")

### 4. Edge Table

| # | Source Node | Source Port | Target Node | Target Port | Condition/Label |
| --- | --- | --- | --- | --- | --- |
| 1 | trigger | output | fetchOrders | input | — |
| 2 | fetchOrders | default | checkStatus | input | — |
| 3 | checkStatus | true | processOrder | input | Status is 200 |
| 4 | checkStatus | false | logSkip | input | Status is not 200 |

**Rules:**

- Source/target ports must match the [Standard Port Reference](#standard-port-reference)
- Every node (except the trigger) must appear as a target at least once
- Every node (except End/Terminate) must appear as a source at least once

### 5. Inputs & Outputs

| Direction | Name | Type | Description |
| --- | --- | --- | --- |
| `in` | ordersApiUrl | `string` | Base URL for the orders API |
| `out` | processedCount | `number` | Number of orders successfully processed |
| `inout` | errorLog | `array` | Accumulates error messages across the flow |

### 6. Connector Summary (omit if no connectors)

| Node ID | Service | Intended Operation | Phase 2 Action |
| --- | --- | --- | --- |
| notifySlack | Slack | Send message to channel | Resolve connector key, bind connection, resolve channel ID |
| createTicket | Jira | Create issue | Resolve connector key, bind connection, resolve project/issue type IDs |

### 7. Open Questions (omit if none)

Prefix each with `**[REQUIRED]**` or `**[OPTIONAL]**`:

- **[REQUIRED]** Which Slack channel should notifications go to?
- **[OPTIONAL]** Should the error handler retry before terminating?

---

## Mermaid Validation Rules

LLM-generated mermaid frequently contains syntax errors. After generating the diagram, **check every rule below** before presenting it to the user. Fix violations before outputting.

### Syntax Rules

1. **First line must be `graph TD` or `graph LR`** — use `graph` not `flowchart` (the `flowchart` keyword is not supported by all renderers). `TD` = top-down, `LR` = left-right.
2. **Node IDs must be alphanumeric + underscores only** — no hyphens, dots, or spaces in IDs. Use `fetchData` not `fetch-data` or `fetch.data`
3. **Node IDs must not start with or equal a reserved word** — mermaid reserves these as keywords: `end`, `subgraph`, `graph`, `flowchart`, `direction`, `click`, `style`, `classDef`, `class`, `linkStyle`, `callback`, `default`. IDs that start with these (e.g., `endWarm`, `defaultPath`, `styleNode`) break the parser. Use alternatives like `warmEnd`, `pathDefault`, `nodeStyle` — or use a prefix like `done_warm`, `finish_warm`.
4. **Node labels must be plain text** — no quotes inside shape delimiters. Use `A[Fetch Data]` not `A["Fetch Data"]`.
5. **No special characters in labels** — these break mermaid parsing even when quoted:
   - `>` and `<` (interpreted as shape operators or HTML) — replace with words like "over" or "under"
   - `(`, `)`, `[`, `]`, `{`, `}` (conflict with shape delimiters)
   - `:`, `;`, `?`, `&`, `"` (unreliable across renderers)
   - Use plain alphanumeric text and spaces only
6. **Use only universally supported shapes** — `(text)` for rounded rectangle, `[text]` for rectangle, `{text}` for diamond. Do NOT use `([text])` (stadium), `{{text}}` (hexagon), or other extended shapes — they are not supported by all renderers.
7. **Edge labels use `|label|` between arrow and target** — `A -->|success| B` not `A -->success B` or `A --success--> B`
8. **No empty labels** — `A --> B` is fine, but `A -->|| B` is invalid
9. **Subgraph IDs must be unique** and not collide with node IDs
10. **Subgraph blocks must be closed** — every `subgraph` needs a matching `end`
11. **No semicolons** — mermaid uses newlines, not semicolons, to separate statements
12. **No blank lines inside the mermaid block** — blank lines between node definitions and edges can prevent rendering in some mermaid implementations. Keep all lines contiguous.

### Structural Rules

1. **Every node defined must be connected** — no orphan nodes floating in the diagram
2. **Edge directions must match the flow** — trigger at the top, End at the bottom (for TB layouts)
3. **Decision nodes must show both branches** — `true` and `false` edges, each labeled
4. **Switch nodes must show all case edges** — one per case plus optional default
5. **Loop structures**: show the loop body and the loopBack edge returning to the loop node
6. **Parallel branches** must visually fork from one node and converge at a Merge node

### Validation Procedure

After generating the mermaid block:

1. First line is `graph TD` or `graph LR` — not `flowchart`
2. Check each node ID contains only `[a-zA-Z0-9_]`
3. Check no node ID starts with or equals a reserved word (`end`, `subgraph`, `graph`, `flowchart`, `direction`, `click`, `style`, `classDef`, `class`, `linkStyle`, `callback`, `default`)
4. Check no labels contain `>`, `<`, `:`, `;`, `?`, `&`, `(`, `)`, or quotes — replace with plain words
5. Only `(text)`, `[text]`, and `{text}` shapes are used — no `([text])`, `{{text}}`, or other extended shapes
6. Check each edge has valid `-->`, `-->|label|` syntax
7. Check all subgraphs are closed
8. Verify every node in the node table appears in the diagram
9. Verify every edge in the edge table appears in the diagram
10. Check for blank lines inside the mermaid block — remove any empty lines between statements
11. If any rule is violated, fix it before outputting

---

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

### "The flow needs something outside flow capabilities"

1. Add a `core.logic.mock` placeholder
2. Note what needs to be created and which skill handles it:
   - Desktop/browser automation or coded workflow (C#) -> `uipath-rpa`
   - Agent -> `uipath-agents`
3. Phase 2 will check whether the resource has been published and replace the mock

---

## Handoff to Phase 2

When the architectural plan is approved, Phase 2 ([Planning Phase 2: Implementation](planning-impl.md)) takes over to:

1. Validate all node types via `uip flow registry get` — read each plugin's `impl.md` for registry validation steps
2. Resolve connector and resource nodes — see the relevant plugin's `impl.md` ([connector](plugins/connector/impl.md), [rpa](plugins/rpa/impl.md), [agent](plugins/agent/impl.md), etc.)
3. Resolve resource nodes (confirm published, get definitions)
4. Validate required fields against user-provided values
5. Replace `<PLACEHOLDER>` values in the node table with resolved IDs
6. Replace `core.logic.mock` nodes with real resource nodes (if now published)
7. Finalize the plan with implementation-ready details

**Do not proceed to Phase 2 until the user explicitly approves the architectural plan.**
