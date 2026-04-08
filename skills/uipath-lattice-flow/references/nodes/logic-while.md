# While

**Type:** `core.logic.while`  **Version:** `1.0.0`  **Category:** control-flow
**BPMN Model:** none

## Ports

| Position | Handle ID | Type | Notes |
|----------|-----------|------|-------|
| left | `input` | target | `handleType: input` |
| right | `body` | source | `handleType: output`, label `Body (while {condition \|\| 'true'})` |
| right | `exit` | source | `handleType: output`, label `Exit` |

## Definition Block

Copy this verbatim into the `definitions` array (do not modify):

```json
{
  "nodeType": "core.logic.while",
  "version": "1.0.0",
  "category": "control-flow",
  "tags": ["control-flow", "loop", "while"],
  "sortOrder": 4,
  "display": {
    "label": "While",
    "icon": "repeat"
  },
  "handleConfiguration": [
    {
      "position": "left",
      "handles": [
        {
          "id": "input",
          "type": "target",
          "handleType": "input"
        }
      ]
    },
    {
      "position": "right",
      "handles": [
        {
          "id": "body",
          "label": "Body (while {condition || 'true'})",
          "type": "source",
          "handleType": "output"
        },
        {
          "id": "exit",
          "label": "Exit",
          "type": "source",
          "handleType": "output"
        }
      ]
    }
  ]
}
```

## Node Instance Example

```json
{
  "id": "while_1",
  "type": "core.logic.while",
  "typeVersion": "1.0.0",
  "ui": {
    "position": { "x": 500, "y": 200 },
    "size": { "width": 256, "height": 96 },
    "collapsed": false
  },
  "display": {
    "label": "While"
  },
  "inputs": {},
  "outputs": {}
}
```

## Common Mistakes

- Not providing an exit condition. While loops without exit conditions run forever. The label template defaults to `while true` when no condition is set -- this is a signal that the condition is missing.
- Forgetting to connect the `exit` port. Without an edge from `exit`, the workflow has no path forward after the loop terminates. Always connect `exit` to the next downstream node.
- Confusing `body` and `exit` ports. The `body` port leads to the loop body (executed each iteration). The `exit` port leads to the continuation after the loop condition becomes false.
- Adding inputs or outputs that do not exist in the registration. This node has no `inputDefinition` or `outputDefinition` -- do not fabricate them.
