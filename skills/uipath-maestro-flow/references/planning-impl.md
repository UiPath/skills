# Node Registry & Build Reference

Reference for validating node types against the registry, resolving connector and resource nodes, and applying product heuristics while building. Use this alongside [planning-arch.md](planning-arch.md) (which covers node selection, ports, and wiring) during Step 4 of [SKILL.md](../SKILL.md).

> **Always validate every node type with the registry** — even OOTB nodes. Port names, input requirements, and output schemas can change. Do not assume OOTB nodes match reference tables without verification.

---

## Validating Node Types with the Registry

For every node you add, identify its category and run the relevant registry check:

| Category          | How to identify                                                      | Action                                                                                                                                                                                                                                                                     |
| ----------------- | -------------------------------------------------------------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Connector nodes   | Node type starts with `uipath.connector.*` or Notes say "connector:" | Follow [connector/impl.md](plugins/connector/impl.md) — binding, enriched metadata, reference-field resolution                                                                                                                                                             |
| Resource nodes    | Node type starts with `uipath.core.*` or Notes say "resource:"       | Follow the relevant resource plugin: [rpa](plugins/rpa/impl.md), [agent](plugins/agent/impl.md), [agentic-process](plugins/agentic-process/impl.md), [flow](plugins/flow/impl.md), [api-workflow](plugins/api-workflow/impl.md), [hitl](plugins/hitl/impl.md) |
| Mock placeholders | Node type is `core.logic.mock`                                       | Re-check via `registry search` — replace with real node if now published                                                                                                                                                                                                   |
| OOTB nodes        | Everything else (Script, HTTP, Decision, Loop, etc.)                 | Run `registry get` + read the plugin's `impl.md`                                                                                                                                                                                                                            |

### Registry Validation Command

For every node type, run:

```bash
uip flow registry pull --force
uip flow registry get <nodeType> --output json
```

Read the relevant plugin's `impl.md` for the expected ports and inputs:

```bash
uip flow registry pull --force
uip flow registry get <nodeType> --output json
```

**Plugin impl.md files for registry validation:**

| Node Type                       | Plugin impl.md                                                 |
| ------------------------------- | -------------------------------------------------------------- |
| `core.action.script`            | [script/impl.md](plugins/script/impl.md)                       |
| `core.action.http`              | [http/impl.md](plugins/http/impl.md)                           |
| `core.action.transform`         | [transform/impl.md](plugins/transform/impl.md)                 |
| `core.logic.delay`              | [delay/impl.md](plugins/delay/impl.md)                         |
| `core.logic.decision`           | [decision/impl.md](plugins/decision/impl.md)                   |
| `core.logic.switch`             | [switch/impl.md](plugins/switch/impl.md)                       |
| `core.logic.loop`               | [loop/impl.md](plugins/loop/impl.md)                           |
| `core.logic.merge`              | [merge/impl.md](plugins/merge/impl.md)                         |
| `core.control.end`              | [end/impl.md](plugins/end/impl.md)                             |
| `core.logic.terminate`          | [terminate/impl.md](plugins/terminate/impl.md)                 |
| `core.subflow`                  | [subflow/impl.md](plugins/subflow/impl.md)                     |
| `core.trigger.scheduled`        | [scheduled-trigger/impl.md](plugins/scheduled-trigger/impl.md) |
| `core.action.queue.*`           | [queue/impl.md](plugins/queue/impl.md)                         |
| `uipath.agent.autonomous`       | [inline-agent/impl.md](plugins/inline-agent/impl.md)           |
| `uipath.core.agent.*`           | [agent/impl.md](plugins/agent/impl.md)                         |
| `uipath.core.rpa.*`             | [rpa/impl.md](plugins/rpa/impl.md)                             |
| `uipath.core.agentic-process.*` | [agentic-process/impl.md](plugins/agentic-process/impl.md)     |
| `uipath.core.flow.*`            | [flow/impl.md](plugins/flow/impl.md)                           |
| `uipath.core.api-workflow.*`    | [api-workflow/impl.md](plugins/api-workflow/impl.md)           |
| `uipath.core.hitl.*`            | [hitl/impl.md](plugins/hitl/impl.md)                           |
| `uipath.connector.*`            | [connector/impl.md](plugins/connector/impl.md)                 |
| `uipath.connector.trigger.*`    | [connector-trigger/impl.md](plugins/connector-trigger/impl.md) |

For each node type, confirm:

- Input port names (must match `targetPort` in edges)
- Output port names (must match `sourcePort` in edges)
- Required input fields (`required: true` in `inputDefinition`)
- Output variable schema (`outputDefinition`)

Copy the returned `definition` verbatim into the `.flow` file's `definitions` array — never hand-write it.

---

## Resolving Connector Nodes

For each connector node, follow the Configuration Workflow in [connector/impl.md](plugins/connector/impl.md). The guide covers connection binding, metadata retrieval, field resolution, and validation. Record the connection ID and resolved field values before adding the node.

---

## Resolving Resource Nodes

For each resource node (RPA process, agent, flow, API workflow, human task), follow the discovery and validation steps in the relevant resource plugin's `impl.md`.

```bash
uip flow registry get "<node-type>" --output json
```

Read `inputDefinition` and `outputDefinition` from the output.

If `registry search` earlier did not find the resource, re-check — it may have been published since:

```bash
uip flow registry pull --force
uip flow registry search "<resource-name>" --output json
```

If still not found, use a `core.logic.mock` placeholder and tell the user which skill to use to create the resource.

---

## Handling Mock Placeholders

For each `core.logic.mock` node:

1. Check if the resource is now published: `uip flow registry search "<name>" --output json`
2. If published: replace the mock with the real resource node type, update inputs/outputs
3. If not published: keep the mock and flag it to the user in the completion report

---

## Product Heuristics

These are org-wide "when to use what" rules that can't be encoded in individual node descriptions. They reflect how UiPath's products fit together and which approach to prefer for a given task.

### Connecting to External Services

See [planning-arch.md — Selecting External Service Nodes](planning-arch.md#selecting-external-service-nodes) for the 4-tier decision order (connector -> HTTP within connector -> standalone HTTP -> RPA).

### Agent Nodes vs Workflow Logic

See [agent/planning.md](plugins/agent/planning.md) for the full decision table. Summary:

- **Agent nodes** for ambiguous input, reasoning, judgment, NLG
- **Script/Decision/Switch** for structured input, deterministic logic, data transformation

**Anti-pattern:** Don't use an agent node for tasks that can be done with a Decision + Script. Agents are slower, more expensive (LLM tokens), and less predictable.

**Hybrid pattern:** Use workflow nodes for the deterministic parts (fetch data, transform, route) and agent nodes for the ambiguous parts (classify intent, draft response, extract entities). The flow orchestrates; the agent reasons.

---

## Expressions and Variables

For the **complete reference** on variables (declaration, types, scoping, variable updates) and expressions (`=js:`, templates, Jint constraints), see [variables-and-expressions.md](variables-and-expressions.md).

### Quick Reference

Nodes communicate data through `$vars`. Every node's output is accessible downstream via `$vars.{nodeId}.{outputProperty}`.

```javascript
$vars.rollDice.output.roll              // Script return value
$vars.fetchData.output.body             // HTTP response body
$vars.fetchData.output.statusCode       // HTTP status code
$vars.someNode.error.message            // Error information
iterator.currentItem                     // Loop item (inside loop body)
````

**Expression prefixes:**

- `=js:` — Full JavaScript expression evaluated by Jint: `=js:$vars.count > 10`
- `{ }` — Template interpolation for string fields: `Order {$vars.orderId} is {$vars.status}`

**Variable directions** (`variables.globals`):

- `in` — External input (read-only after start)
- `out` — Workflow output (must be mapped on End nodes)
- `inout` — State variable (updated via `variableUpdates`)

---

## Wiring Rules

### Port Compatibility

- Edges connect a **source** port (output) on one node to a **target** port (input) on another
- Source handles have `type: "source"`, target handles have `type: "target"`
- You cannot wire two source ports together or two target ports together

### Connection Constraints

Some nodes enforce connection rules via `constraints` in their handle configuration:

| Constraint                               | Meaning                                                         |
| ---------------------------------------- | --------------------------------------------------------------- |
| `minConnections: N`                      | Handle must have at least N edges (validation error if not met) |
| `maxConnections: N`                      | Handle accepts at most N edges                                  |
| `forbiddenSourceCategories: ["trigger"]` | Cannot receive connections from trigger nodes                   |
| `forbiddenTargetCategories: ["trigger"]` | Cannot connect output to trigger nodes                          |

**Key rules:**

- Trigger nodes can only have outgoing connections (no input port)
- End/Terminate nodes can only have incoming connections (no output port)
- Control flow outputs generally cannot loop back to triggers
- Decision and Switch nodes cannot receive connections from agent resource nodes

### Dynamic Ports

Some nodes create ports based on their configuration:

- **HTTP Request** — One port per `branches` entry: `branch-{id}`. See [http/impl.md](plugins/http/impl.md).
- **Switch** — One port per `cases` entry: `case-{id}`. See [switch/impl.md](plugins/switch/impl.md).
- **Loop** — `success` port fires after completion, `output` port carries aggregated results. See [loop/impl.md](plugins/loop/impl.md).

When wiring to dynamic ports, the port ID must match the configured item's `id`.
