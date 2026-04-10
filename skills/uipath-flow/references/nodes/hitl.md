# Human in the Loop (`uipath.human-in-the-loop`)

**Type:** `uipath.human-in-the-loop`  **Version:** `1.0.0`  **Category:** human-task
**BPMN Model:** `bpmn:UserTask`

## When to Use

Use a Human in the Loop node when the flow needs to pause for human input, approval, or review.

| Situation | Use HITL? |
|-----------|-----------|
| Manager approval before processing | Yes |
| Human reviews extracted data before submission | Yes |
| Human resolves items the automation cannot handle | Yes |
| Fully automated processing with no human involvement | No |
| App not yet published | No -- use `core.logic.mock` as a placeholder |

## Ports

| Direction | Port ID | Notes |
|-----------|---------|-------|
| left | `input` | target, `handleType: input`. Forbids connections from trigger-category nodes |
| right | `completed` | source, `handleType: output`, `showButton: true`. Forbids connections to trigger-category nodes |
| right | `cancelled` | source, `handleType: output`, `showButton: true`. Forbids connections to trigger-category nodes |
| right | `timeout` | source, `handleType: output`, `showButton: true`. Forbids connections to trigger-category nodes |

## Inputs

| Field | Type | Required | Notes |
|-------|------|----------|-------|
| `type` | select | No | Task type: `"quick"` (quick approval or review) or `"custom"` (custom approval). Default: `"quick"` |
| `recipient` | custom | No | Delivery channels for the task (component: `hitl-channel-selector`) |
| `schema` | custom | No | Input/output parameter schema for the task (component: `hitl-schema-editor`) |
| `app` | custom | No | Coded action app for custom approval tasks (component: `hitl-app-picker`) |

## Outputs

| Key | Type | Source Expression |
|-----|------|-------------------|
| `result` | object | `=result` |
| `status` | string | `=status` |

`status` is one of: `completed`, `cancelled`, or `timeout`.

## Definition

```json
{
  "nodeType": "uipath.human-in-the-loop",
  "version": "1.0.0",
  "category": "human-task",
  "tags": ["human-task", "hitl", "human-in-the-loop", "approval"],
  "sortOrder": 50,
  "display": {
    "label": "Human in the Loop",
    "icon": "users",
    "shape": "rectangle"
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
            "forbiddenSourceCategories": ["trigger"],
            "validationMessage": "Human tasks cannot be directly triggered"
          }
        }
      ],
      "visible": true
    },
    {
      "position": "right",
      "handles": [
        {
          "id": "completed",
          "label": "Completed",
          "type": "source",
          "handleType": "output",
          "showButton": true,
          "constraints": {
            "forbiddenTargetCategories": ["trigger"]
          }
        },
        {
          "id": "cancelled",
          "label": "Cancelled",
          "type": "source",
          "handleType": "output",
          "showButton": true,
          "constraints": {
            "forbiddenTargetCategories": ["trigger"]
          }
        },
        {
          "id": "timeout",
          "label": "Timeout",
          "type": "source",
          "handleType": "output",
          "showButton": true,
          "constraints": {
            "forbiddenTargetCategories": ["trigger"]
          }
        }
      ],
      "visible": true
    }
  ],
  "model": {
    "type": "bpmn:UserTask"
  },
  "inputDefinition": {
    "type": "quick",
    "channels": [],
    "schema": {
      "inputs": [],
      "outputs": [],
      "inOuts": [],
      "outcomes": [{ "name": "Submit", "type": "string" }]
    }
  },
  "outputDefinition": {
    "result": {
      "type": "object",
      "description": "Task result data",
      "source": "=result",
      "var": "result"
    },
    "status": {
      "type": "string",
      "description": "Task completion status (completed, cancelled, timeout)",
      "source": "=status",
      "var": "status"
    }
  },
  "form": {
    "id": "hitl-properties",
    "title": "Human Task Configuration",
    "sections": [
      {
        "id": "task-type",
        "title": "Task Type",
        "collapsible": false,
        "defaultExpanded": true,
        "fields": [
          {
            "name": "inputs.type",
            "type": "select",
            "label": "Type",
            "options": [
              { "label": "Quick approval or review", "value": "quick" },
              { "label": "Custom approval", "value": "custom" }
            ]
          }
        ]
      },
      {
        "id": "delivery",
        "title": "Task Delivery",
        "collapsible": true,
        "defaultExpanded": true,
        "fields": [
          {
            "name": "inputs.recipient",
            "type": "custom",
            "component": "hitl-channel-selector",
            "label": "Delivery Channels",
            "description": "Select where the task should be sent"
          }
        ]
      },
      {
        "id": "schema",
        "title": "Schema",
        "collapsible": true,
        "defaultExpanded": false,
        "fields": [
          {
            "name": "inputs.schema",
            "type": "custom",
            "component": "hitl-schema-editor",
            "label": "Task Schema",
            "description": "Define the input and output parameters for this task"
          }
        ]
      },
      {
        "id": "app",
        "title": "Custom Approval App",
        "collapsible": true,
        "defaultExpanded": true,
        "fields": [
          {
            "name": "inputs.app",
            "type": "custom",
            "component": "hitl-app-picker",
            "label": "Action App",
            "description": "Select the coded action app for this task"
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
  "id": "approveRequest1",
  "type": "uipath.human-in-the-loop",
  "typeVersion": "1.0.0",
  "ui": {
    "position": { "x": 640, "y": 200 },
    "size": { "width": 96, "height": 96 },
    "collapsed": false
  },
  "display": {
    "label": "Manager Approval",
    "icon": "users",
    "shape": "rectangle"
  },
  "inputs": {
    "type": "quick",
    "schema": {
      "inputs": [],
      "outputs": [],
      "inOuts": [],
      "outcomes": [{ "name": "Submit", "type": "string" }]
    }
  },
  "outputs": {
    "result": {
      "type": "object",
      "description": "Task result data",
      "source": "=result",
      "var": "result"
    },
    "status": {
      "type": "string",
      "description": "Task completion status (completed, cancelled, timeout)",
      "source": "=status",
      "var": "status"
    }
  },
  "model": {
    "type": "bpmn:UserTask"
  }
}
```

## Common Mistakes

1. Not handling all three output ports (`completed`, `cancelled`, `timeout`). Each port represents a distinct task outcome and should be wired to appropriate downstream logic or a terminal node.
2. Wiring a trigger node directly into the `input` port. The constraint `forbiddenSourceCategories: ["trigger"]` blocks this -- place an action or control node between the trigger and the HITL node.
3. Omitting the `schema.outcomes` array. Even for quick approvals, at least one outcome (default `"Submit"`) must be defined.
4. Using `output` as the right-side port name. Unlike most nodes, HITL has three named output ports: `completed`, `cancelled`, and `timeout` -- there is no generic `output` port.
5. Confusing this OOTB node (`uipath.human-in-the-loop`) with dynamic tenant-specific human task nodes (`uipath.core.human-task.{key}`). Dynamic human task nodes are resource nodes discovered via registry pull and have different port and model configurations.
