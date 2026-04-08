# Scheduled Trigger

**Type:** `core.trigger.scheduled`  **Version:** `1.0.0`  **Category:** trigger
**BPMN Model:** `bpmn:StartEvent` with `eventDefinition: "bpmn:TimerEventDefinition"`

## Ports

| Position | Handle ID | Type | Notes |
|----------|-----------|------|-------|
| right | `output` | source | `handleType: output`, `showButton: true`, min 1 connection (warning) |

## Inputs

| Field | Type | Required | Default | Description |
|-------|------|----------|---------|-------------|
| `timerType` | string | No | `"timeCycle"` | Timer type identifier. Always `"timeCycle"` for repeating schedules. |
| `timerPreset` | string | **Yes** | `"R/PT1H"` | ISO 8601 repeating interval preset, or `"custom"` for a custom interval. |
| `timerValue` | string | When `timerPreset` is `"custom"` | -- | Custom ISO 8601 repeating interval expression (e.g., `R/PT2H30M`). |

### Timer Preset Values

| Label | Value |
|-------|-------|
| Every 5 minutes | `R/PT5M` |
| Every 15 minutes | `R/PT15M` |
| Every 30 minutes | `R/PT30M` |
| Every hour | `R/PT1H` |
| Every 6 hours | `R/PT6H` |
| Every 12 hours | `R/PT12H` |
| Daily | `R/P1D` |
| Weekly | `R/P1W` |
| Custom | `custom` |

When `timerPreset` is `"custom"`, `timerValue` is required and must match the ISO 8601 repeating interval pattern:

```
^R\/P(?!$)(\d+Y)?(\d+M)?(\d+W)?(\d+D)?(T(?=\d)(\d+H)?(\d+M)?(\d+S)?)?(\/.+)?$
```

## Definition Block

Copy this verbatim into the `definitions` array (do not modify):

```json
{
  "nodeType": "core.trigger.scheduled",
  "version": "1.0.0",
  "category": "trigger",
  "description": "Start workflow on a schedule or interval",
  "tags": [
    "trigger",
    "start",
    "event",
    "schedule",
    "timer",
    "cron"
  ],
  "sortOrder": 40,
  "display": {
    "label": "Scheduled trigger",
    "icon": "calendar-clock",
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
    "entryPointId": true,
    "eventDefinition": "bpmn:TimerEventDefinition",
    "values": {
      "timerType": "inputs.timerType",
      "timerValue": "inputs.timerValue",
      "timerPreset": "inputs.timerPreset"
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
  },
  "inputDefinition": {
    "type": "object",
    "properties": {
      "timerType": {
        "type": "string",
        "minLength": 1
      },
      "timerPreset": {
        "type": "string",
        "minLength": 1,
        "errorMessage": "Frequency is required"
      },
      "timerValue": {
        "type": "string"
      }
    },
    "required": [
      "timerPreset"
    ],
    "if": {
      "properties": {
        "timerPreset": {
          "const": "custom"
        }
      }
    },
    "then": {
      "required": [
        "timerValue"
      ],
      "properties": {
        "timerValue": {
          "type": "string",
          "minLength": 1,
          "pattern": "^R\\/P(?!$)(\\d+Y)?(\\d+M)?(\\d+W)?(\\d+D)?(T(?=\\d)(\\d+H)?(\\d+M)?(\\d+S)?)?(\\/.+)?$",
          "errorMessage": {
            "minLength": "Cycle expression is required",
            "pattern": "Cycle expression must be in ISO 8601 repeating interval format (e.g., R/PT1H, R/P1D)"
          }
        }
      }
    }
  },
  "inputDefaults": {
    "timerType": "timeCycle",
    "timerPreset": "R/PT1H"
  },
  "form": {
    "id": "scheduled-trigger-properties",
    "title": "Scheduled trigger",
    "sections": [
      {
        "id": "schedule",
        "title": "Schedule",
        "collapsible": false,
        "defaultExpanded": true,
        "fields": [
          {
            "name": "inputs.timerPreset",
            "type": "select",
            "label": "Frequency",
            "description": "Interval repeats from deployment time",
            "options": [
              {
                "label": "Every 5 minutes",
                "value": "R/PT5M"
              },
              {
                "label": "Every 15 minutes",
                "value": "R/PT15M"
              },
              {
                "label": "Every 30 minutes",
                "value": "R/PT30M"
              },
              {
                "label": "Every hour",
                "value": "R/PT1H"
              },
              {
                "label": "Every 6 hours",
                "value": "R/PT6H"
              },
              {
                "label": "Every 12 hours",
                "value": "R/PT12H"
              },
              {
                "label": "Daily",
                "value": "R/P1D"
              },
              {
                "label": "Weekly",
                "value": "R/P1W"
              },
              {
                "label": "Custom",
                "value": "custom"
              }
            ]
          },
          {
            "name": "inputs.timerValue",
            "type": "custom",
            "component": "iso-expression-field",
            "label": "Cycle expression",
            "placeholder": "R/PT1H",
            "description": "ISO 8601 repeating interval - use the AI button to generate from natural language",
            "componentProps": {
              "expressionType": "repeating-interval"
            },
            "rules": [
              {
                "id": "custom-cycle",
                "conditions": [
                  {
                    "when": "inputs.timerPreset",
                    "is": "custom"
                  }
                ],
                "effects": {
                  "visible": true
                }
              }
            ]
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
  "id": "scheduledTrigger1",
  "type": "core.trigger.scheduled",
  "typeVersion": "1.0.0",
  "ui": {
    "position": { "x": 0, "y": 128 },
    "size": { "width": 96, "height": 96 },
    "collapsed": false
  },
  "display": {
    "label": "Weekly trigger",
    "subLabel": "Execute weekly risk assessment",
    "shape": "circle",
    "iconBackground": "linear-gradient(225deg, #FAFAFB 0%, #ECEDEF 100%)",
    "iconBackgroundDark": "linear-gradient(225deg, #526069 0%, rgba(50, 60, 66, 0.6) 100%)",
    "icon": "calendar-clock"
  },
  "inputs": {
    "timerType": "timeCycle",
    "timerPreset": "R/P1W"
  },
  "model": {
    "type": "bpmn:StartEvent",
    "entryPointId": "a4d23734-8236-4515-99e3-ea075e2780b4",
    "eventDefinition": "bpmn:TimerEventDefinition",
    "values": {
      "timerType": "inputs.timerType",
      "timerValue": "inputs.timerValue",
      "timerPreset": "inputs.timerPreset"
    }
  }
}
```

## Common Mistakes

- Forgetting to set `timerPreset` -- it is required. Omitting it causes a validation error: "Frequency is required."
- Using cron syntax instead of ISO 8601 repeating intervals. The scheduler expects values like `R/PT1H` or `R/P1D`, not `0 * * * *`.
- Setting `timerPreset` to `"custom"` without providing `timerValue`. When preset is `"custom"`, `timerValue` is conditionally required.
- Writing bare durations like `PT1H` instead of repeating intervals `R/PT1H`. The `R/` prefix is mandatory.
- Using a UUID for `model.entryPointId` in the definition -- the definition always uses `true`, the instance uses the actual UUID.
