# Blank

**Type:** `core.mock.blank`  **Version:** `1.0.0`  **Category:** mock
**BPMN Model:** `bpmn:Task`

## Ports

| Position | Handle ID | Type | Notes |
|----------|-----------|------|-------|
| left | `input` | target | `handleType: input` |
| right | `output` | source | `handleType: output` |

## Definition Block

Copy this verbatim into the `definitions` array (do not modify):

```json
{
  "nodeType": "core.mock.blank",
  "version": "1.0.0",
  "category": "mock",
  "tags": ["blank", "todo"],
  "sortOrder": 2,
  "display": {
    "label": "Blank",
    "icon": "construction"
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
  "id": "blank1",
  "type": "core.mock.blank",
  "typeVersion": "1.0.0",
  "ui": {
    "position": { "x": 450, "y": 200 },
    "size": { "width": 96, "height": 96 },
    "collapsed": false
  },
  "display": {
    "label": "Blank",
    "icon": "construction"
  },
  "inputs": {},
  "model": {
    "type": "bpmn:Task"
  }
}
```

## Common Mistakes

- Using `core.mock.blank` when `core.mock.node` is needed. `core.mock.node` supports error handling (`supportsErrorHandling: true`); `core.mock.blank` is a pure pass-through with no error port.
- Using `core.mock.blank` as a general-purpose placeholder. Prefer `core.logic.mock` (category `control-flow`) for prototyping -- it is the recommended placeholder node per the skill's critical rules.
- Expecting outputs from this node. `core.mock.blank` has no `outputDefinition` -- it produces no data. Downstream nodes cannot reference `$vars.blank1.output`.
