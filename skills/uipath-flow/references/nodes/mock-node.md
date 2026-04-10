# Mock (`core.mock.node`)

**Type:** `core.mock.node`  **Version:** `1.0.0`  **Category:** mock
**BPMN Model:** `bpmn:Task`

`supportsErrorHandling: true`

## When to Use

- Placeholder node with error handling support.
- Use when you need a stub that can route errors via a dedicated error port.
- Prefer `core.mock.blank` when error handling is not needed.
- Prefer `core.logic.mock` (category `control-flow`) for general prototyping -- it has an `outputDefinition` and is the recommended placeholder node.

## Ports

| Direction | Port ID | Notes |
|-----------|---------|-------|
| input | `input` | Standard input target |
| output | `output` | Standard output source |
| output | `error` | Runtime-injected when `errorHandlingEnabled` is true. Not in definition JSON. Max 1 connection |

## Inputs

| Field | Type | Required | Notes |
|-------|------|----------|-------|
| `errorHandlingEnabled` | boolean | No | When `true`, the runtime injects the `error` output port. Default: `false` |

## Outputs

No data outputs.

## Definition

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

## Instance Example

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

1. Using `core.mock.node` for all placeholders. Use `core.logic.mock` instead -- it is the recommended prototyping placeholder. `core.logic.mock` is in the `control-flow` category and has an `outputDefinition`, making it more suitable for flow prototyping.
2. Expecting the `error` port to appear in the handle configuration by default. The error port is only visible when `inputs.errorHandlingEnabled` is set to `true` on the node instance. The registration JSON does not include the `error` handle explicitly; the runtime injects it because `supportsErrorHandling` is `true`.
3. Confusing with `core.mock.blank`. The key difference is that `core.mock.node` supports error handling; `core.mock.blank` does not.
