# Mock (`core.logic.mock`)

**Type:** `core.logic.mock`  **Version:** `1.0.0`  **Category:** control-flow
**BPMN Model:** `bpmn:Task`

## When to Use

Use a Mock node as a placeholder when prototyping flows. It stands in for real logic that will be added later.

| Situation | Use Mock? |
|-----------|-----------|
| Prototyping a flow before all nodes are available | Yes |
| Reserving a slot for logic to be implemented later | Yes |
| Need a node that actually processes data | No -- use the appropriate logic or action node |

## Ports

| Direction | Port ID | Notes |
|-----------|---------|-------|
| left | `input` | target, `handleType: input` |
| right | `output` | source, `handleType: output` |

## Inputs

None.

## Outputs

| Key | Type | Source Expression |
|-----|------|-------------------|
| `output` | object | `null` |

## Definition

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

## Instance Example

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

1. Confusing with `core.mock.node` or `core.mock.blank`. Those are in the `mock` category and have different icons (`square` and `construction` respectively). `core.logic.mock` uses icon `square-dashed` and belongs to the `control-flow` category.
2. Trying to read meaningful data from `$vars.<mockId>.output`. The output is always `null`. Mock nodes are placeholders -- replace them with real nodes before expecting data flow.
3. Omitting the `outputDefinition` from the definition block. Even though the output is `null`, the definition must include it so downstream nodes can reference the output schema during flow validation.
