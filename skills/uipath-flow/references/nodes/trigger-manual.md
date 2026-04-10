# Manual Trigger (`core.trigger.manual`)

**Version:** `1.0.0` | **Category:** trigger | **BPMN Model:** `bpmn:StartEvent`

## When to Use

Use a Manual Trigger to start the flow on demand via user action or API call. This is the default trigger for flows that do not require a recurring schedule.

| Situation | Use Manual Trigger? |
|-----------|---------------------|
| Flow is started on demand by a user or API call | Yes |
| Flow must run on a recurring schedule (hourly, daily, weekly) | No -- use `core.trigger.scheduled` |

Every flow must have exactly one trigger node. Do not combine manual and scheduled triggers in the same flow.

## Ports

| Direction | Port ID | Notes |
|-----------|---------|-------|
| source | `output` | `handleType: output`, `showButton: true`, minConnections: 1 (severity: warning -- "Trigger must connect to at least one workflow node") |

No target (input) ports. Manual trigger is a start event and only has one right-side source port.

## Inputs

No configurable inputs. The manual trigger has no input fields.

## Outputs

| Key | Type | Source Expression |
|-----|------|-------------------|
| `output` | object | `null` |

## Definition

```json
{
  "nodeType": "core.trigger.manual",
  "version": "1.0.0",
  "category": "trigger",
  "description": "Start workflow manually",
  "tags": [
    "trigger",
    "start",
    "manual"
  ],
  "sortOrder": 40,
  "display": {
    "label": "Manual trigger",
    "icon": "play",
    "shape": "circle",
    "iconBackground": "linear-gradient(225deg, #FAFAFB 0%, #ECEDEF 100%)",
    "iconBackgroundDark": "linear-gradient(225deg, #526069 0%, rgba(50, 60, 66, 0.6) 100%)"
  },
  "handleConfiguration": [
    {
      "position": "right",
      "handles": [
        {
          "id": "output",
          "type": "source",
          "handleType": "output",
          "showButton": true,
          "constraints": {
            "minConnections": 1,
            "severity": "warning",
            "validationMessage": "Trigger must connect to at least one workflow node (not configuration nodes)"
          }
        }
      ],
      "visible": true
    }
  ],
  "model": {
    "type": "bpmn:StartEvent",
    "entryPointId": true
  },
  "outputDefinition": {
    "output": {
      "type": "object",
      "description": "Data passed when manually triggering the workflow.",
      "source": "null",
      "var": "output"
    }
  },
  "toolbarExtensions": {
    "design": {
      "actions": [
        {
          "id": "change-trigger-type",
          "icon": "replace",
          "label": "Change trigger type"
        }
      ]
    }
  }
}
```

## Instance Example

```json
{
  "id": "start",
  "type": "core.trigger.manual",
  "typeVersion": "1.0.0",
  "ui": {
    "position": { "x": 256, "y": 200 },
    "size": { "width": 96, "height": 96 },
    "collapsed": false
  },
  "display": {
    "label": "Manual trigger"
  },
  "inputs": {},
  "outputs": {
    "output": {
      "type": "object",
      "description": "Data passed when manually triggering the workflow.",
      "source": "null",
      "var": "output"
    }
  },
  "model": {
    "type": "bpmn:StartEvent",
    "entryPointId": "091d7427-2e67-4278-ad0f-22c0d3760da3"
  }
}
```

## Common Mistakes

1. Using a UUID for `model.entryPointId` in the definition. The definition always uses `true`; the instance uses the actual UUID.
2. Omitting the `outputs` block from the node instance. Even though manual trigger has no configurable inputs, its output definition must be present in each instance.
3. Adding a left-side (target/input) port. Manual trigger is a start event and only has one right-side source port.
4. Having both a manual trigger and a scheduled trigger in the same flow. A flow must have exactly one trigger node.
