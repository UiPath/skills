# End

**Type:** `core.control.end`  **Version:** `1.0.0`  **Category:** control-flow
**BPMN Model:** `bpmn:EndEvent`

## Ports

| Position | Handle ID | Type | Notes |
|----------|-----------|------|-------|
| left | `input` | target | `handleType: input`. No right-side ports -- this is a terminal node. |

## Definition Block

Copy this verbatim into the `definitions` array (do not modify):

```json
{
  "nodeType": "core.control.end",
  "version": "1.0.0",
  "category": "control-flow",
  "tags": ["control-flow", "end", "finish", "complete"],
  "sortOrder": 20,
  "display": {
    "label": "End",
    "icon": "circle-check",
    "shape": "circle"
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
    }
  ],
  "model": {
    "type": "bpmn:EndEvent"
  }
}
```

## Node Instance Example

```json
{
  "id": "end_1",
  "type": "core.control.end",
  "typeVersion": "1.0.0",
  "ui": {
    "position": { "x": 900, "y": 200 },
    "size": { "width": 96, "height": 96 },
    "collapsed": false
  },
  "display": {
    "label": "End"
  },
  "inputs": {},
  "outputs": {},
  "model": {
    "type": "bpmn:EndEvent"
  }
}
```

## Common Mistakes

- Forgetting to map `out` variables on End nodes. Every variable in `variables.globals` with direction `out` or `inOut` must have an output mapping on every reachable End node. Missing mappings cause silent runtime failures where the workflow completes but returns no data.
- Confusing End with Terminate. End (`core.control.end`) stops a single branch. Terminate (`core.logic.terminate`) stops the entire workflow immediately, killing all parallel branches. Use End when other branches should continue executing.
- Adding right-side (source/output) ports. End is a terminal node with only one left-side target port. It has no outgoing connections.
- Omitting `model.type` from the node instance. The instance must include `"model": { "type": "bpmn:EndEvent" }` to compile correctly.
