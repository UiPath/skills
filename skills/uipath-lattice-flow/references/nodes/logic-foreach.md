# For Each

**Type:** `core.logic.foreach`  **Version:** `1.0.0`  **Category:** control-flow
**BPMN Model:** none

## Ports

| Position | Handle ID | Type | Notes |
|----------|-----------|------|-------|
| left | `input` | target | `handleType: input` |
| right | `body` | source | `handleType: output`, label `Body (Item {currentIndex + 1} of {collection.length \|\| '?'})` |
| right | `completed` | source | `handleType: output`, label `Completed` |

## Definition Block

Copy this verbatim into the `definitions` array (do not modify):

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

## Node Instance Example

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

- Confusing For Each with Loop. Loop (`core.logic.loop`) is the primary iteration node with a `collection` input and `currentItem` output. For Each (`core.logic.foreach`) is a simpler alternative with no inputs or outputs defined in its registration.
- Forgetting to connect the `completed` port. The `body` port drives the iteration body, but the `completed` port is needed for the flow to continue after the loop finishes. An unconnected `completed` port means the workflow stalls after iteration.
- Adding inputs or outputs that do not exist in the registration. This node has no `inputDefinition` or `outputDefinition` -- do not fabricate them.
