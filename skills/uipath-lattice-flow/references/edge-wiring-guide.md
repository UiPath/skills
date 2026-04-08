# Edge Wiring Guide

How to wire edges across all OOTB node types, including the JSON format, port reference, common patterns, and validation rules.

---

## Edge JSON Format

```json
{
  "id": "<SOURCE_ID>-<SOURCE_PORT>-<TARGET_ID>-<TARGET_PORT>",
  "sourceNodeId": "<SOURCE_NODE_ID>",
  "sourcePort": "<SOURCE_PORT_ID>",
  "targetNodeId": "<TARGET_NODE_ID>",
  "targetPort": "<TARGET_PORT_ID>"
}
```

All four fields (`sourceNodeId`, `sourcePort`, `targetNodeId`, `targetPort`) are required. Missing any field causes a validation failure.

---

## Port Quick Reference

| Node Type | Target Ports (left) | Source Ports (right) |
|-----------|---------------------|----------------------|
| `core.trigger.manual` | -- | `output` |
| `core.trigger.scheduled` | -- | `output` |
| `core.action.script` | `input` | `success`, `error`* |
| `core.action.http` | `input` | `branch-{id}`, `default`, `error`* |
| `core.action.transform` | `input` | `success` |
| `core.action.transform.filter` | `input` | `success` |
| `core.logic.decision` | `input` | `true`, `false` |
| `core.logic.switch` | `input` | `case-{id}`, `default` |
| `core.logic.loop` | `input`, `loopBack` | `success`, `output`, `error`* |
| `core.logic.foreach` | `input` | `body`, `completed` |
| `core.logic.while` | `input` | `body`, `exit` |
| `core.logic.merge` | `input` | `output` |
| `core.logic.delay` | `input` | `output` |
| `core.logic.mock` | `input` | `output` |
| `core.logic.terminate` | `input` | -- |
| `core.control.end` | `input` | -- |
| `uipath.human-in-the-loop` | `input` | `completed`, `cancelled`, `timeout` |
| `core.mock.blank` | `input` | `output` |
| `core.mock.node` | `input` | `output`, `error`* |

*`error` ports are only visible when `supportsErrorHandling` is enabled on the node instance.

---

## Common Wiring Patterns

### Linear Flow

```
trigger.output --> script.input
script.success --> end.input
```

```json
[
  { "id": "start-output-myScript-input", "sourceNodeId": "start", "sourcePort": "output", "targetNodeId": "myScript", "targetPort": "input" },
  { "id": "myScript-success-end1-input", "sourceNodeId": "myScript", "sourcePort": "success", "targetNodeId": "end1", "targetPort": "input" }
]
```

### Decision Branch

```
decision.true  --> handlerA.input
decision.false --> handlerB.input
```

```json
[
  { "id": "decision1-true-handlerA-input", "sourceNodeId": "decision1", "sourcePort": "true", "targetNodeId": "handlerA", "targetPort": "input" },
  { "id": "decision1-false-handlerB-input", "sourceNodeId": "decision1", "sourcePort": "false", "targetNodeId": "handlerB", "targetPort": "input" }
]
```

### Loop

```
loop.output       --> bodyNode.input
bodyNode.success  --> loop.loopBack
loop.success      --> afterLoop.input
```

```json
[
  { "id": "loop1-output-bodyNode-input", "sourceNodeId": "loop1", "sourcePort": "output", "targetNodeId": "bodyNode", "targetPort": "input" },
  { "id": "bodyNode-success-loop1-loopBack", "sourceNodeId": "bodyNode", "sourcePort": "success", "targetNodeId": "loop1", "targetPort": "loopBack" },
  { "id": "loop1-success-afterLoop-input", "sourceNodeId": "loop1", "sourcePort": "success", "targetNodeId": "afterLoop", "targetPort": "input" }
]
```

### Parallel Merge

```
decision.true  --> branchA.input
decision.false --> branchB.input
branchA.success --> merge.input
branchB.success --> merge.input
merge.output    --> next.input
```

```json
[
  { "id": "decision1-true-branchA-input", "sourceNodeId": "decision1", "sourcePort": "true", "targetNodeId": "branchA", "targetPort": "input" },
  { "id": "decision1-false-branchB-input", "sourceNodeId": "decision1", "sourcePort": "false", "targetNodeId": "branchB", "targetPort": "input" },
  { "id": "branchA-success-merge1-input", "sourceNodeId": "branchA", "sourcePort": "success", "targetNodeId": "merge1", "targetPort": "input" },
  { "id": "branchB-success-merge1-input", "sourceNodeId": "branchB", "sourcePort": "success", "targetNodeId": "merge1", "targetPort": "input" },
  { "id": "merge1-output-next-input", "sourceNodeId": "merge1", "sourcePort": "output", "targetNodeId": "next", "targetPort": "input" }
]
```

---

## Edge ID Generation

Format: `{sourceId}-{sourcePort}-{targetId}-{targetPort}`

Rules:
1. Use `default` if a port value is null
2. Append `-2`, `-3`, etc. on collision with an existing edge ID
3. Example: `start-output-httpRequest1-input`

See [project-scaffolding-guide.md](project-scaffolding-guide.md) for the full ID generation algorithm.

---

## Validation Rules

1. Both `sourceNodeId` and `targetNodeId` must exist in `workflow.nodes`
2. Both `sourcePort` and `targetPort` must be non-empty strings
3. Port IDs must match the node type's handle configuration (see Port Quick Reference above)
4. No duplicate edge IDs within `workflow.edges`
5. Respect `maxConnections` constraints (e.g., `error` port allows max 1 outgoing connection)

See [validation-checklist.md](validation-checklist.md) for the full list of structural checks.
