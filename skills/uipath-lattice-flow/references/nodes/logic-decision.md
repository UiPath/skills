# Decision

**Type:** `core.logic.decision`  **Version:** `1.0.0`  **Category:** control-flow
**BPMN Model:** `bpmn:InclusiveGateway`

## Ports

| Position | Handle ID | Type | Notes |
|----------|-----------|------|-------|
| left | `input` | target | Blocks connections from `uipath.agent.resource.*` nodes |
| right | `true` | source | Label from `inputs.trueLabel` (default "True"). `minConnections: 1` |
| right | `false` | source | Label from `inputs.falseLabel` (default "False"). `minConnections: 1` |

Both output ports also forbid connections to trigger-category nodes and `uipath.agent.resource.*` nodes.

## Inputs

| Field | Type | Required | Default | Description |
|-------|------|----------|---------|-------------|
| `expression` | string | Yes | -- | JavaScript expression that evaluates to true or false |
| `trueLabel` | string | No | `"True"` | Label shown on the true branch port |
| `falseLabel` | string | No | `"False"` | Label shown on the false branch port |

## Outputs

| Key | Type | Description | Source Expression |
|-----|------|-------------|------------------|
| `matchedCase` | string | The label of the matched branch (true/false label) | var: `matchedCase` |
| `matchedCaseId` | string | The branch that was taken (`true` or `false`) | var: `matchedCaseId` |

## Definition Block

Copy this verbatim into the `definitions` array (do not modify):

```json
{
  "nodeType": "core.logic.decision",
  "version": "1.0.0",
  "category": "control-flow",
  "tags": ["control-flow", "if", "loop", "switch"],
  "sortOrder": 1,
  "display": {
    "label": "Decision",
    "icon": "decision"
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
          "id": "true",
          "type": "source",
          "handleType": "output",
          "label": "{inputs.trueLabel || 'True'}",
          "constraints": {
            "forbiddenTargetCategories": ["trigger"],
            "forbiddenTargets": [
              {
                "nodeType": "uipath.agent.resource.*"
              }
            ],
            "minConnections": 1
          }
        },
        {
          "id": "false",
          "type": "source",
          "handleType": "output",
          "label": "{inputs.falseLabel || 'False'}",
          "constraints": {
            "forbiddenTargetCategories": ["trigger"],
            "forbiddenTargets": [
              {
                "nodeType": "uipath.agent.resource.*"
              }
            ],
            "minConnections": 1
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
    "type": "bpmn:InclusiveGateway"
  },
  "inputDefinition": {
    "type": "object",
    "properties": {
      "expression": { "type": "string", "minLength": 1, "errorMessage": "A condition expression is required" },
      "trueLabel": { "type": "string" },
      "falseLabel": { "type": "string" }
    },
    "required": ["expression"]
  },
  "outputDefinition": {
    "matchedCase": {
      "type": "string",
      "description": "The label of the matched branch (true/false label)",
      "var": "matchedCase"
    },
    "matchedCaseId": {
      "type": "string",
      "description": "The branch that was taken (true or false)",
      "var": "matchedCaseId"
    }
  },
  "inputDefaults": {
    "trueLabel": "True",
    "falseLabel": "False"
  },
  "form": {
    "id": "decision-properties",
    "title": "Decision configuration",
    "sections": [
      {
        "id": "condition",
        "title": "Condition",
        "fields": [
          {
            "name": "inputs.expression",
            "type": "custom",
            "component": "script-editor",
            "componentProps": {
              "language": "javascript",
              "returnType": "boolean",
              "minHeight": 100,
              "placeholder": "e.g., $vars.data.status === \"approved\" && $vars.data.amount > 1000"
            },
            "label": "Expression",
            "description": "JavaScript expression that evaluates to true or false",
            "validation": {
              "required": true,
              "messages": {
                "required": "A condition expression is required"
              }
            }
          },
          {
            "name": "inputs.trueLabel",
            "type": "text",
            "label": "True branch label",
            "description": "Label shown when condition is true"
          },
          {
            "name": "inputs.falseLabel",
            "type": "text",
            "label": "False branch label",
            "description": "Label shown when condition is false"
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
  "id": "decision_1",
  "type": "core.logic.decision",
  "position": { "x": 400, "y": 200 },
  "data": {
    "inputs": {
      "expression": "$vars.order.total > 500",
      "trueLabel": "High Value",
      "falseLabel": "Standard"
    }
  }
}
```

## Common Mistakes

- Leaving `expression` empty -- the node requires a non-empty JavaScript expression that evaluates to a boolean.
- Forgetting that both the `true` and `false` output ports require at least one outgoing edge (`minConnections: 1`). The flow will fail validation if either branch is unwired.
- Wiring a `uipath.agent.resource.*` node directly into the `input` port -- resource nodes are forbidden sources for control-flow nodes.
- Using non-boolean expressions -- the expression must resolve to `true` or `false`; truthy/falsy coercion behavior depends on the runtime.
