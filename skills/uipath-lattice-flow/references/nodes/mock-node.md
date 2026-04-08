# Mock

**Type:** `core.mock.node`  **Version:** `1.0.0`  **Category:** mock
**BPMN Model:** `bpmn:Task`

`supportsErrorHandling: true`

## Ports

| Position | Handle ID | Type | Notes |
|----------|-----------|------|-------|
| left | `input` | target | `handleType: input` |
| right | `output` | source | `handleType: output` |
| right | `error` | source | `handleType: output` -- visible only when `inputs.errorHandlingEnabled` is true, max 1 connection |

## Definition Block

Copy this verbatim into the `definitions` array (do not modify):

```json
{
  "nodeType": "core.mock.node",
  "version": "1.0.0",
  "category": "mock",
  "tags": ["blank", "todo"],
  "sortOrder": 2,
  "supportsErrorHandling": true,
  "display": {
    "label": "Mock",
    "icon": "square"
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
      ],
      "visible": true
    },
    {
      "position": "right",
      "handles": [
        {
          "id": "output",
          "type": "source",
          "handleType": "output"
        }
      ],
      "visible": true
    }
  ],
  "model": {
    "type": "bpmn:Task"
  }
}
```

## Node Instance Example

```json
{
  "id": "mockNode1",
  "type": "core.mock.node",
  "typeVersion": "1.0.0",
  "ui": {
    "position": { "x": 450, "y": 200 },
    "size": { "width": 96, "height": 96 },
    "collapsed": false
  },
  "display": {
    "label": "Mock",
    "icon": "square"
  },
  "inputs": {},
  "model": {
    "type": "bpmn:Task"
  }
}
```

## Common Mistakes

- Using `core.mock.node` for all placeholders. Use `core.logic.mock` instead -- it is the recommended prototyping placeholder per the skill's critical rules. `core.logic.mock` is in the `control-flow` category and has an `outputDefinition`, making it more suitable for flow prototyping.
- Expecting the `error` port to appear in the handle configuration by default. The error port is only visible when `inputs.errorHandlingEnabled` is set to `true` on the node instance. The registration JSON does not include the `error` handle explicitly; the runtime injects it because `supportsErrorHandling` is `true`.
- Confusing with `core.mock.blank`. The key difference is that `core.mock.node` supports error handling; `core.mock.blank` does not.
