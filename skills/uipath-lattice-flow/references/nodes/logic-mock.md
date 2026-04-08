# Mock

**Type:** `core.logic.mock`  **Version:** `1.0.0`  **Category:** control-flow
**BPMN Model:** `bpmn:Task`

This is the **recommended placeholder node** for prototyping flows. Use it when you need a stand-in node that will be replaced later with real logic.

## Ports

| Position | Handle ID | Type | Notes |
|----------|-----------|------|-------|
| left | `input` | target | `handleType: input` |
| right | `output` | source | `handleType: output` |

## Outputs

| Key | Type | Description | Source Expression |
|-----|------|-------------|-------------------|
| `output` | object | Mock output value (always `null`) | `null` |

## Definition Block

Copy this verbatim into the `definitions` array (do not modify):

```json
{
  "nodeType": "core.logic.mock",
  "version": "1.0.0",
  "category": "control-flow",
  "description": "Placeholder node for prototyping",
  "tags": [
    "blank",
    "todo"
  ],
  "sortOrder": 20,
  "display": {
    "label": "Mock",
    "icon": "square-dashed",
    "iconBackground": "linear-gradient(225deg, #FAFAFB 0%, #ECEDEF 100%)",
    "iconBackgroundDark": "linear-gradient(225deg, #526069 0%, rgba(50, 60, 66, 0.6) 100%)"
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
  },
  "outputDefinition": {
    "output": {
      "type": "object",
      "description": "Mock output value",
      "source": "null",
      "var": "output"
    }
  }
}
```

## Node Instance Example

```json
{
  "id": "mock1",
  "type": "core.logic.mock",
  "typeVersion": "1.0.0",
  "ui": {
    "position": { "x": 1184, "y": 144 },
    "size": { "width": 96, "height": 96 },
    "collapsed": false
  },
  "display": {
    "label": "Receive documents",
    "subLabel": "",
    "iconBackground": "linear-gradient(225deg, #FAFAFB 0%, #ECEDEF 100%)",
    "iconBackgroundDark": "linear-gradient(225deg, #526069 0%, rgba(50, 60, 66, 0.6) 100%)",
    "icon": "square-dashed"
  },
  "inputs": {},
  "model": {
    "type": "bpmn:Task"
  }
}
```

## Common Mistakes

- Confusing with `core.mock.node` or `core.mock.blank`. Those are in the `mock` category and have different icons (`square` and `construction` respectively). `core.logic.mock` uses icon `square-dashed` and belongs to the `control-flow` category.
- Trying to read meaningful data from `$vars.<mockId>.output`. The output is always `null`. Mock nodes are placeholders -- replace them with real nodes before expecting data flow.
- Omitting the `outputDefinition` from the definition block. Even though the output is `null`, the definition must include it so downstream nodes can reference the output schema during flow validation.
