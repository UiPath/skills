# For Each (`core.logic.foreach`)

**Type:** `core.logic.foreach`  **Version:** `1.0.0`  **Category:** control-flow
**BPMN Model:** none

## When to Use

- Iterate over a collection of items, executing the loop body once per element.
- Use when you need index-aware iteration (the label template shows `currentIndex`).
- Prefer `core.logic.loop` when you need a `collection` input and `currentItem` output -- For Each has neither.

## Ports

| Direction | Port ID | Notes |
|-----------|---------|-------|
| input | `input` | Standard input target |
| output | `body` | Loop body -- executes once per item. Label: `Body (Item {currentIndex + 1} of {collection.length \|\| '?'})` |
| output | `completed` | Fires after all iterations finish. Connect to the next downstream node |

## Inputs

No configurable inputs.

## Outputs

No data outputs.

## Definition

```json
{
  "nodeType": "core.logic.foreach",
  "version": "1.0.0",
  "category": "control-flow",
  "tags": ["control-flow", "loop", "iteration"],
  "sortOrder": 3,
  "display": {
    "label": "For Each",
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
          "label": "Body (Item {currentIndex + 1} of {collection.length || '?'})",
          "type": "source",
          "handleType": "output"
        },
        {
          "id": "completed",
          "label": "Completed",
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
  "id": "foreach_1",
  "type": "core.logic.foreach",
  "typeVersion": "1.0.0",
  "ui": {
    "position": { "x": 500, "y": 200 },
    "size": { "width": 256, "height": 96 },
    "collapsed": false
  },
  "display": {
    "label": "For Each"
  },
  "inputs": {},
  "outputs": {}
}
```

## Common Mistakes

1. Confusing For Each with Loop. `core.logic.loop` is the primary iteration node with a `collection` input and `currentItem` output. `core.logic.foreach` is a simpler alternative with no inputs or outputs defined in its registration.
2. Forgetting to connect the `completed` port. The `body` port drives the iteration body, but `completed` is required for the flow to continue after the loop finishes. An unconnected `completed` port means the workflow stalls after iteration.
3. Adding inputs or outputs that do not exist in the registration. This node has no `inputDefinition` or `outputDefinition` -- do not fabricate them.
