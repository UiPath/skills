# Switch (`core.logic.switch`)

**Type:** `core.logic.switch`  **Version:** `1.0.0`  **Category:** control-flow
**BPMN Model:** `bpmn:ExclusiveGateway`

## When to Use

Use a Switch node for multi-way branching (3+ paths) based on ordered case expressions. Cases are evaluated in order; the first `true` case is taken.

| Situation | Use Switch? |
|-----------|-------------|
| Three or more paths based on different conditions | Yes |
| Simple true/false branch | No -- use Decision (`core.logic.decision`) |
| Branch on HTTP response status codes | No -- use HTTP node built-in branches |
| Branch requires reasoning on ambiguous input | No -- use an Agent node |

## Ports

| Direction | Port ID | Notes |
|-----------|---------|-------|
| input | `input` | Blocks connections from `uipath.agent.resource.*` nodes |
| output | `case-{item.id}` | Dynamic -- one port per entry in `inputs.cases`, label from `{item.label}`. Forbids connections to trigger-category and `uipath.agent.resource.*` nodes. |
| output | `default` | Visible only when `inputs.hasDefault` is true. Forbids connections to trigger-category and `uipath.agent.resource.*` nodes. |

Each case edge uses source handle `case-{id}` where `{id}` matches the case's `id` field.

## Inputs

| Field | Type | Required | Notes |
|-------|------|----------|-------|
| `cases` | array | Yes | Default: 2 empty cases. Array of case objects (min 1). Each case has `id`, `label`, and `expression`. |
| `cases[].id` | string | No | Unique identifier for the case (used in port handle ID `case-{id}`). |
| `cases[].label` | string | No | Display label for the case port. |
| `cases[].expression` | string | Yes | JavaScript expression evaluated for this case. |
| `hasDefault` | boolean | No | Default `true`. When true, adds a `default` output port as a fallback path. |

## Outputs

| Key | Type | Source Expression |
|-----|------|-------------------|
| `matchedCase` | string | var: `matchedCase` -- the label of the matched case |
| `matchedCaseId` | string | var: `matchedCaseId` -- the ID of the matched case (null for default) |

## Definition

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

## Instance Example

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

1. Forgetting to add an edge from the `default` port when `hasDefault` is true. The default port exists but is useless without a connection, and the flow will have a dead-end branch.
2. Not matching case IDs in edges to the IDs in the `cases` array. The source handle is `case-{id}`, so a case with `"id": "low"` produces handle `case-low` -- not `case-Low` or `low`.
3. Omitting the `expression` field on a case object. Every case requires a non-empty expression string.
4. Cases are evaluated in order -- the first true match wins. Putting a broad condition before a narrow one means the narrow case is unreachable.
5. Setting `hasDefault: false` without ensuring the case expressions are exhaustive. If no case matches and there is no default, the flow has no exit path.
6. Using the wrong port name in edge wiring. The port ID must be `case-{id}` matching the case's `id` field exactly -- not the label, not the index.
