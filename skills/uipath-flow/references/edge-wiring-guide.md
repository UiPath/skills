# Edge Wiring Guide

How to wire edges across all node types, including the JSON format, port reference, connection constraints, dynamic ports, common patterns, and validation rules.

---

## Edge JSON Format

Every edge in `workflow.edges` is an object with these fields:

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `id` | string | Yes | Unique edge identifier. Convention: `{sourceNodeId}-{sourcePort}-{targetNodeId}-{targetPort}` |
| `sourceNodeId` | string | Yes | ID of the node the edge originates from |
| `sourcePort` | string | Yes | Handle ID on the source node (e.g., `output`, `success`, `true`) |
| `targetNodeId` | string | Yes | ID of the node the edge connects to |
| `targetPort` | string | Yes | Handle ID on the target node (e.g., `input`, `loopBack`) |
| `data` | `Record<string, string>` | No | Optional metadata. Common use: `{ "label": "..." }` |

```json
{
  "id": "start-output-myScript-input",
  "sourceNodeId": "start",
  "sourcePort": "output",
  "targetNodeId": "myScript",
  "targetPort": "input"
}
```

### Edge ID Generation

Format: `{sourceNodeId}-{sourcePort}-{targetNodeId}-{targetPort}`

Rules:
1. Use `default` if a port value is null.
2. Append `-2`, `-3`, etc. on collision with an existing edge ID.
3. Example: `start-output-httpRequest1-input`

---

## Port Quick Reference

Use this table when defining edges. Every edge requires a valid `sourcePort` and `targetPort` that match the node type's handle configuration.

### OOTB Node Types

| Node Type | Target Ports (left) | Source Ports (right) | Notes |
|-----------|---------------------|----------------------|-------|
| `core.trigger.manual` | -- | `output` | No input port. Always the first node. |
| `core.trigger.scheduled` | -- | `output` | No input port. Always the first node. |
| `core.action.script` | `input` | `success`, `error`* | Source port is `success`, NOT `output`. |
| `core.action.http` | `input` | `branch-{id}`, `default`, `error`* | Branches are dynamic. `default` is always present. |
| `core.action.transform` | `input` | `output`, `error`* | Source port is `output`, NOT `success`. |
| `core.action.transform.filter` | `input` | `output`, `error`* | Source port is `output`, NOT `success`. |
| `core.action.queue.create` | `input` | `success` | Fire-and-forget queue dispatch. |
| `core.action.queue.create-and-wait` | `input` | `success` | Waits for queue item result. |
| `core.logic.decision` | `input` | `true`, `false` | Both output ports require `minConnections: 1`. |
| `core.logic.switch` | `input` | `case-{id}`, `default` | Cases are dynamic. `default` only when `hasDefault: true`. |
| `core.logic.loop` | `input`, `loopBack` | `success`, `output`, `error`* | `output` goes to loop body. `loopBack` receives return. `success` fires after completion. |
| `core.logic.foreach` | `input` | `body`, `completed` | `body` goes to iteration logic. `completed` fires after all items. |
| `core.logic.while` | `input` | `body`, `exit` | `body` executes while condition is true. `exit` when condition is false. |
| `core.logic.merge` | `input` | `output` | `input` accepts multiple incoming edges. |
| `core.logic.delay` | `input` | `output` | Pauses execution for a duration or until a time. |
| `core.logic.mock` | `input` | `output` | Placeholder node for prototyping. |
| `core.logic.terminate` | `input` | -- | Terminal node. Aborts entire workflow immediately. |
| `core.control.end` | `input` | -- | Terminal node. Graceful completion of one path. |
| `core.subflow` | `input` | `output`, `error` | Groups steps into an isolated scope. |
| `uipath.human-in-the-loop` | `input` | `completed`, `cancelled`, `timeout` | Three distinct outcome ports. |
| `core.mock.blank` | `input` | `output` | Blank placeholder. |
| `core.mock.node` | `input` | `output`, `error`* | Mock with configurable error handling. |

*`error` ports are only visible when `supportsErrorHandling` / `errorHandlingEnabled` is enabled on the node instance. Error ports have `maxConnections: 1`.

> **Common mistakes:**
> - Script uses source port `success`, not `output`.
> - Transform and Transform Filter use source port `output`, not `success`.
> - Loop has TWO target ports (`input` and `loopBack`) and THREE source ports (`success`, `output`, `error`).
> - ForEach uses `body` / `completed`, not `output` / `success`.
> - While uses `body` / `exit`, not `output` / `success`.
> - HITL has three source ports (`completed`, `cancelled`, `timeout`), not a single `output`.

### Connector Node Types

Connector nodes call external services via Integration Service. Their exact type is `uipath.connector.*`.

| Node Type Pattern | Target Ports (left) | Source Ports (right) |
|-------------------|---------------------|----------------------|
| `uipath.connector.*` | `input` | `success` |

Connector source port is `success`, not `output`.

### Dynamic Resource Node Types

Resource nodes invoke published UiPath automations. All resource node types share identical ports:

| Node Type Pattern | Target Ports (left) | Source Ports (right) |
|-------------------|---------------------|----------------------|
| `uipath.core.rpa.{key}` | `input` | `output`, `error`* |
| `uipath.core.agent.{key}` | `input` | `output`, `error`* |
| `uipath.core.agentic-process.{key}` | `input` | `output`, `error`* |
| `uipath.core.flow.{key}` | `input` | `output`, `error`* |
| `uipath.core.api-workflow.{key}` | `input` | `output`, `error`* |
| `uipath.core.hitl.{key}` | `input` | `output`, `error`* |

*Resource node `error` ports are visible only when `errorHandlingEnabled` is enabled. Error ports have `maxConnections: 1`.

> **Key distinction:** Resource nodes use source port `output`. Connector nodes use source port `success`. Do not confuse the two.

---

## Connection Constraints

Some nodes enforce wiring rules via `constraints` on their handle configuration. Violating these constraints causes validation failures.

### Constraint Types

| Constraint | Meaning |
|------------|---------|
| `minConnections: N` | Handle must have at least N edges. Validation error if fewer. |
| `maxConnections: N` | Handle accepts at most N edges. Additional connections are rejected. |
| `forbiddenSources: [{ nodeType }]` | Cannot receive connections from the specified node type pattern. |
| `forbiddenSourceCategories: [category]` | Cannot receive connections from nodes in the specified category (e.g., `"trigger"`). |
| `forbiddenTargets: [{ nodeType }]` | Cannot connect output to the specified node type pattern. |
| `forbiddenTargetCategories: [category]` | Cannot connect output to nodes in the specified category (e.g., `"trigger"`). |
| `allowedTargetCategories: [category]` | Output can ONLY connect to nodes in the specified categories. |

### Constraints by Node Type

| Node Type | Port | Constraints |
|-----------|------|-------------|
| `core.trigger.manual` | `output` | `minConnections: 1` (warning) |
| `core.trigger.scheduled` | `output` | `minConnections: 1` (warning) |
| `core.logic.decision` | `input` | `forbiddenSources: [{ nodeType: "uipath.agent.resource.*" }]` |
| `core.logic.decision` | `true` | `minConnections: 1`, `forbiddenTargetCategories: ["trigger"]`, `forbiddenTargets: [{ nodeType: "uipath.agent.resource.*" }]` |
| `core.logic.decision` | `false` | `minConnections: 1`, `forbiddenTargetCategories: ["trigger"]`, `forbiddenTargets: [{ nodeType: "uipath.agent.resource.*" }]` |
| `core.logic.switch` | `input` | `forbiddenSources: [{ nodeType: "uipath.agent.resource.*" }]` |
| `core.logic.switch` | `case-{id}` | `forbiddenTargetCategories: ["trigger"]`, `forbiddenTargets: [{ nodeType: "uipath.agent.resource.*" }]` |
| `core.logic.switch` | `default` | `forbiddenTargetCategories: ["trigger"]`, `forbiddenTargets: [{ nodeType: "uipath.agent.resource.*" }]` |
| `uipath.human-in-the-loop` | `input` | `forbiddenSourceCategories: ["trigger"]` |
| `uipath.human-in-the-loop` | `completed` | `forbiddenTargetCategories: ["trigger"]` |
| `uipath.human-in-the-loop` | `cancelled` | `forbiddenTargetCategories: ["trigger"]` |
| `uipath.human-in-the-loop` | `timeout` | `forbiddenTargetCategories: ["trigger"]` |
| All nodes | `error` | `maxConnections: 1` |

### General Rules

- Trigger nodes can only have outgoing connections (no input port exists).
- End and Terminate nodes can only have incoming connections (no output port exists).
- Control flow outputs cannot loop back to trigger nodes.
- Decision and Switch nodes cannot receive connections from agent resource nodes.

---

## Dynamic Ports

Some nodes create ports dynamically based on their configuration. The port IDs are generated from the configuration and must match exactly in edge definitions.

### HTTP Branches

`core.action.http` creates one source port per entry in `inputs.branches`:

- Port ID: `branch-{item.id}` where `item.id` is the branch object's `id` field.
- The `default` port is always present regardless of branch configuration.
- Each branch has a `conditionExpression` that routes based on response status, headers, or body.

### Switch Cases

`core.logic.switch` creates one source port per entry in `inputs.cases`:

- Port ID: `case-{item.id}` where `item.id` is the case object's `id` field.
- The `default` port is only present when `inputs.hasDefault` is `true`.
- Each case has an `expression` evaluated in order; first match wins.

### Loop

`core.logic.loop` has a fixed set of ports but uses two target ports and three source ports:

- **Target port `input`**: Main entry point from upstream nodes.
- **Target port `loopBack`**: Receives the edge returning from the last node in the loop body.
- **Source port `output`**: Connects to the first node inside the loop body.
- **Source port `success`**: Fires after all iterations complete. Connects to the next node after the loop.
- **Source port `error`**: Fires on error (only when error handling is enabled).

### ForEach

`core.logic.foreach` has fixed ports:

- **Source port `body`**: Connects to the first node in the iteration body.
- **Source port `completed`**: Fires after all items have been processed.

### While

`core.logic.while` has fixed ports:

- **Source port `body`**: Connects to the first node in the loop body (executes while condition is true).
- **Source port `exit`**: Fires when the condition evaluates to false.

---

## Common Wiring Patterns

### Linear Flow (Trigger to Action to End)

```
trigger.output --> script.input
script.success --> end.input
```

```json
[
  {
    "id": "start-output-myScript-input",
    "sourceNodeId": "start",
    "sourcePort": "output",
    "targetNodeId": "myScript",
    "targetPort": "input"
  },
  {
    "id": "myScript-success-end1-input",
    "sourceNodeId": "myScript",
    "sourcePort": "success",
    "targetNodeId": "end1",
    "targetPort": "input"
  }
]
```

### Decision Branch (True Path / False Path)

```
trigger.output     --> decision.input
decision.true      --> handlerA.input
decision.false     --> handlerB.input
handlerA.success   --> endA.input
handlerB.success   --> endB.input
```

```json
[
  {
    "id": "trigger-output-decision1-input",
    "sourceNodeId": "trigger",
    "sourcePort": "output",
    "targetNodeId": "decision1",
    "targetPort": "input"
  },
  {
    "id": "decision1-true-handlerA-input",
    "sourceNodeId": "decision1",
    "sourcePort": "true",
    "targetNodeId": "handlerA",
    "targetPort": "input"
  },
  {
    "id": "decision1-false-handlerB-input",
    "sourceNodeId": "decision1",
    "sourcePort": "false",
    "targetNodeId": "handlerB",
    "targetPort": "input"
  },
  {
    "id": "handlerA-success-endA-input",
    "sourceNodeId": "handlerA",
    "sourcePort": "success",
    "targetNodeId": "endA",
    "targetPort": "input"
  },
  {
    "id": "handlerB-success-endB-input",
    "sourceNodeId": "handlerB",
    "sourcePort": "success",
    "targetNodeId": "endB",
    "targetPort": "input"
  }
]
```

### Loop (with loopBack Wiring)

```
trigger.output       --> loop1.input
loop1.output         --> bodyNode.input
bodyNode.success     --> loop1.loopBack
loop1.success        --> afterLoop.input
afterLoop.success    --> end1.input
```

```json
[
  {
    "id": "trigger-output-loop1-input",
    "sourceNodeId": "trigger",
    "sourcePort": "output",
    "targetNodeId": "loop1",
    "targetPort": "input"
  },
  {
    "id": "loop1-output-bodyNode-input",
    "sourceNodeId": "loop1",
    "sourcePort": "output",
    "targetNodeId": "bodyNode",
    "targetPort": "input"
  },
  {
    "id": "bodyNode-success-loop1-loopBack",
    "sourceNodeId": "bodyNode",
    "sourcePort": "success",
    "targetNodeId": "loop1",
    "targetPort": "loopBack"
  },
  {
    "id": "loop1-success-afterLoop-input",
    "sourceNodeId": "loop1",
    "sourcePort": "success",
    "targetNodeId": "afterLoop",
    "targetPort": "input"
  },
  {
    "id": "afterLoop-success-end1-input",
    "sourceNodeId": "afterLoop",
    "sourcePort": "success",
    "targetNodeId": "end1",
    "targetPort": "input"
  }
]
```

### Parallel Merge (Fork to Branches to Merge to Continue)

```
decision.true       --> branchA.input
decision.false      --> branchB.input
branchA.success     --> merge1.input
branchB.success     --> merge1.input
merge1.output       --> next.input
next.success        --> end1.input
```

```json
[
  {
    "id": "decision1-true-branchA-input",
    "sourceNodeId": "decision1",
    "sourcePort": "true",
    "targetNodeId": "branchA",
    "targetPort": "input"
  },
  {
    "id": "decision1-false-branchB-input",
    "sourceNodeId": "decision1",
    "sourcePort": "false",
    "targetNodeId": "branchB",
    "targetPort": "input"
  },
  {
    "id": "branchA-success-merge1-input",
    "sourceNodeId": "branchA",
    "sourcePort": "success",
    "targetNodeId": "merge1",
    "targetPort": "input"
  },
  {
    "id": "branchB-success-merge1-input",
    "sourceNodeId": "branchB",
    "sourcePort": "success",
    "targetNodeId": "merge1",
    "targetPort": "input"
  },
  {
    "id": "merge1-output-next-input",
    "sourceNodeId": "merge1",
    "sourcePort": "output",
    "targetNodeId": "next",
    "targetPort": "input"
  },
  {
    "id": "next-success-end1-input",
    "sourceNodeId": "next",
    "sourcePort": "success",
    "targetNodeId": "end1",
    "targetPort": "input"
  }
]
```

---

## Edge Validation Rules

1. **Node existence.** Both `sourceNodeId` and `targetNodeId` must reference nodes that exist in `workflow.nodes`.
2. **Port non-empty.** Both `sourcePort` and `targetPort` must be non-empty strings.
3. **Port match.** Port IDs must match the node type's handle configuration exactly (see Port Quick Reference above). A `sourcePort` must correspond to a handle with `type: "source"` on the source node; a `targetPort` must correspond to a handle with `type: "target"` on the target node.
4. **No duplicate edge IDs.** Every `id` in `workflow.edges` must be unique.
5. **Respect maxConnections.** Do not exceed `maxConnections` on any port. For example, `error` ports allow at most 1 outgoing connection.
6. **Respect minConnections.** Ports with `minConnections: N` must have at least N edges. Decision `true` and `false` ports each require at least 1 outgoing edge.
7. **Respect forbidden rules.** Do not create edges that violate `forbiddenSources`, `forbiddenTargets`, `forbiddenSourceCategories`, or `forbiddenTargetCategories` constraints.
8. **No dangling nodes.** Every node must be connected by at least one edge. A node with no incoming and no outgoing edges is invalid.
9. **No cycles except loopBack.** Do not create cycles in the edge graph except through the Loop node's `loopBack` mechanism.
10. **Every non-trigger node must have at least one incoming edge.** Trigger nodes are the only valid entry points.
11. **Every non-terminal node must have at least one outgoing edge.** End and Terminate nodes are the only valid terminal points.
