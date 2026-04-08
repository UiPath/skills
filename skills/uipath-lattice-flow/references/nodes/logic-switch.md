# Switch

**Type:** `core.logic.switch`  **Version:** `1.0.0`  **Category:** control-flow
**BPMN Model:** `bpmn:ExclusiveGateway`

## Ports

| Position | Handle ID | Type | Notes |
|----------|-----------|------|-------|
| left | `input` | target | Blocks connections from `uipath.agent.resource.*` nodes |
| right | `case-{item.id}` | source | Dynamic -- one port per entry in `inputs.cases`, label from `{item.label}` |
| right | `default` | source | Visible only when `inputs.hasDefault` is true |

All output ports forbid connections to trigger-category nodes and `uipath.agent.resource.*` nodes.

## Inputs

| Field | Type | Required | Default | Description |
|-------|------|----------|---------|-------------|
| `cases` | array | Yes | 2 empty cases | Array of case objects, each with `id`, `label`, and `expression`. Min 1 case. |
| `cases[].id` | string | No | -- | Unique identifier for the case (used in port handle ID `case-{id}`) |
| `cases[].label` | string | No | -- | Display label for the case port |
| `cases[].expression` | string | Yes | -- | JavaScript expression evaluated for this case |
| `hasDefault` | boolean | No | `true` | When true, adds a `default` output port as a fallback path |

## Outputs

| Key | Type | Description | Source Expression |
|-----|------|-------------|------------------|
| `matchedCase` | string | The label of the matched case | var: `matchedCase` |
| `matchedCaseId` | string | The ID of the matched case (null for default) | var: `matchedCaseId` |

## Definition Block

Copy this verbatim into the `definitions` array (do not modify):

```json
{
  "nodeType": "core.logic.switch",
  "version": "1.0.0",
  "category": "control-flow",
  "tags": ["control-flow", "switch"],
  "sortOrder": 2,
  "display": {
    "label": "Switch",
    "icon": "switch"
  },
  "handleConfiguration": [
    {
      "position": "left",
      "handles": [
        {
          "id": "input",
          "type": "target",
          "handleType": "input",
          "constraints": {
            "forbiddenSources": [
              {
                "nodeType": "uipath.agent.resource.*"
              }
            ],
            "validationMessage": "Control flow cannot be directly triggered or accept configuration nodes"
          }
        }
      ],
      "visible": true
    },
    {
      "position": "right",
      "handles": [
        {
          "id": "case-{item.id}",
          "type": "source",
          "handleType": "output",
          "label": "{item.label || 'Case ' + (index + 1)}",
          "repeat": "inputs.cases",
          "constraints": {
            "forbiddenTargetCategories": ["trigger"],
            "forbiddenTargets": [
              {
                "nodeType": "uipath.agent.resource.*"
              }
            ]
          }
        },
        {
          "id": "default",
          "type": "source",
          "handleType": "output",
          "label": "Default",
          "visible": "{inputs.hasDefault}",
          "constraints": {
            "forbiddenTargetCategories": ["trigger"],
            "forbiddenTargets": [
              {
                "nodeType": "uipath.agent.resource.*"
              }
            ]
          }
        }
      ],
      "visible": true
    }
  ],
  "debug": {
    "runtime": "clientScript"
  },
  "model": {
    "type": "bpmn:ExclusiveGateway"
  },
  "inputDefinition": {
    "type": "object",
    "properties": {
      "cases": {
        "type": "array",
        "minItems": 1,
        "errorMessage": "At least one case is required",
        "items": {
          "type": "object",
          "properties": {
            "id": {
              "type": "string"
            },
            "label": {
              "type": "string"
            },
            "expression": {
              "type": "string",
              "minLength": 1,
              "errorMessage": "A condition expression is required"
            }
          },
          "required": ["expression"]
        }
      },
      "hasDefault": {
        "type": "boolean"
      }
    },
    "required": ["cases"]
  },
  "outputDefinition": {
    "matchedCase": {
      "type": "string",
      "description": "The label of the matched case",
      "var": "matchedCase"
    },
    "matchedCaseId": {
      "type": "string",
      "description": "The ID of the matched case (null for default)",
      "var": "matchedCaseId"
    }
  },
  "inputDefaults": {
    "cases": [
      {
        "id": "default-1",
        "label": "Case 1",
        "expression": ""
      },
      {
        "id": "default-2",
        "label": "Case 2",
        "expression": ""
      }
    ],
    "hasDefault": true
  },
  "form": {
    "id": "switch-properties",
    "title": "Switch configuration",
    "sections": [
      {
        "id": "cases",
        "title": "Cases",
        "description": "Each case is evaluated in order. The first condition that returns true is taken.",
        "collapsible": true,
        "defaultExpanded": true,
        "fields": [
          {
            "name": "inputs.cases",
            "type": "custom",
            "label": "Switch cases",
            "component": "case-list-editor",
            "componentProps": {
              "minCases": 1,
              "maxCases": 10,
              "expressionPlaceholder": "e.g., $vars.value <= 30"
            }
          },
          {
            "name": "inputs.hasDefault",
            "type": "switch",
            "label": "Include default case",
            "description": "Add a fallback path when no conditions match",
            "defaultValue": true
          }
        ]
      }
    ]
  }
}
```

## Node Instance Example

```json
{
  "id": "switch_1",
  "type": "core.logic.switch",
  "position": { "x": 400, "y": 200 },
  "data": {
    "inputs": {
      "cases": [
        { "id": "low", "label": "Low", "expression": "$vars.priority <= 2" },
        { "id": "medium", "label": "Medium", "expression": "$vars.priority <= 5" },
        { "id": "high", "label": "High", "expression": "$vars.priority > 5" }
      ],
      "hasDefault": true
    }
  }
}
```

Edges for this node must reference the exact handle IDs:

```json
[
  { "source": "switch_1", "sourceHandle": "case-low", "target": "handleLow_1" },
  { "source": "switch_1", "sourceHandle": "case-medium", "target": "handleMedium_1" },
  { "source": "switch_1", "sourceHandle": "case-high", "target": "handleHigh_1" },
  { "source": "switch_1", "sourceHandle": "default", "target": "handleDefault_1" }
]
```

## Common Mistakes

- Forgetting to add an edge from the `default` port when `hasDefault` is true. The default port exists but is useless without a connection, and the flow will have a dead-end branch.
- Not matching case IDs in edges to the IDs in the `cases` array. The source handle is `case-{id}`, so a case with `"id": "low"` produces handle `case-low` -- not `case-Low` or `low`.
- Omitting the `expression` field on a case object. Every case requires a non-empty expression string.
- Cases are evaluated in order -- the first true match wins. Putting a broad condition before a narrow one means the narrow case is unreachable.
- Setting `hasDefault: false` without ensuring the case expressions are exhaustive. If no case matches and there is no default, the flow has no exit path.
