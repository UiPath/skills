# Blank (`core.mock.blank`)

**Type:** `core.mock.blank`  **Version:** `1.0.0`  **Category:** mock
**BPMN Model:** `bpmn:Task`

## When to Use

- Pure pass-through placeholder with no error handling and no data outputs.
- Use when you need a minimal stub node that simply forwards execution from input to output.
- Prefer `core.mock.node` when you need error handling support (`supportsErrorHandling`).

## Ports

| Direction | Port ID | Notes |
|-----------|---------|-------|
| input | `input` | Standard input target |
| output | `output` | Standard output source |

## Inputs

No configurable inputs.

## Outputs

No data outputs.

## Definition

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

## Instance Example

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

1. Using `core.mock.blank` when `core.mock.node` is needed. `core.mock.node` supports error handling (`supportsErrorHandling: true`); `core.mock.blank` is a pure pass-through with no error port.
2. Using `core.mock.blank` as a general-purpose placeholder. Prefer `core.logic.mock` (category `control-flow`) for prototyping -- it is the recommended placeholder node and has an `outputDefinition`.
3. Expecting outputs from this node. `core.mock.blank` has no `outputDefinition` -- it produces no data. Downstream nodes cannot reference `$vars.blank1.output`.
