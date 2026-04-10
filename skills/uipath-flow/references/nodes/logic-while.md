# While (`core.logic.while`)

**Type:** `core.logic.while`  **Version:** `1.0.0`  **Category:** control-flow
**BPMN Model:** none

## When to Use

- Loop while a condition remains true, executing the body each iteration.
- Use when the number of iterations is unknown and depends on a runtime condition.
- Prefer `core.logic.loop` or `core.logic.foreach` when iterating over a known collection.

## Ports

| Direction | Port ID | Notes |
|-----------|---------|-------|
| input | `input` | Standard input target |
| output | `body` | Loop body -- executes each iteration while condition is true. Label: `Body (while {condition \|\| 'true'})` |
| output | `exit` | Fires when the condition becomes false. Connect to the next downstream node |

## Inputs

No configurable inputs.

## Outputs

No data outputs.

## Definition

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

## Instance Example

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

1. Not providing an exit condition. While loops without exit conditions run forever. The label template defaults to `while true` when no condition is set -- this signals a missing condition.
2. Forgetting to connect the `exit` port. Without an edge from `exit`, the workflow has no path forward after the loop terminates. Always connect `exit` to the next downstream node.
3. Confusing `body` and `exit` ports. The `body` port leads to the loop body (executed each iteration). The `exit` port leads to the continuation after the loop condition becomes false.
4. Adding inputs or outputs that do not exist in the registration. This node has no `inputDefinition` or `outputDefinition` -- do not fabricate them.
