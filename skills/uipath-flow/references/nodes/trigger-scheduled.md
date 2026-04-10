# Scheduled Trigger (`core.trigger.scheduled`)

**Version:** `1.0.0` | **Category:** trigger | **BPMN Model:** `bpmn:StartEvent` with `eventDefinition: "bpmn:TimerEventDefinition"`

## When to Use

Use a Scheduled Trigger to start the flow on a recurring schedule instead of manual invocation.

| Situation | Use Scheduled Trigger? |
|-----------|------------------------|
| Flow runs on a recurring schedule (hourly, daily, weekly) | Yes |
| Flow is started on demand by a user or API call | No -- use `core.trigger.manual` |

Every flow must have exactly one trigger node. A scheduled trigger replaces `core.trigger.manual` -- do not have both in the same flow. The trigger is always the first node in the topology.

## Ports

| Direction | Port ID | Notes |
|-----------|---------|-------|
| source | `output` | `handleType: output`, `showButton: true`, minConnections: 1 (severity: warning -- "Trigger must connect to at least one workflow node") |

No target (input) ports. Scheduled trigger is a start event.

## Inputs

| Field | Type | Required | Notes |
|-------|------|----------|-------|
| `timerType` | string | No | Always `"timeCycle"` for repeating schedules. Default: `"timeCycle"`. |
| `timerPreset` | string | Yes | ISO 8601 repeating interval preset, or `"custom"` for a custom interval. Default: `"R/PT1H"`. Validation error if omitted: "Frequency is required." |
| `timerValue` | string | When `timerPreset` is `"custom"` | Custom ISO 8601 repeating interval expression (e.g., `R/PT2H30M`). Must match pattern `^R\/P(?!$)(\d+Y)?(\d+M)?(\d+W)?(\d+D)?(T(?=\d)(\d+H)?(\d+M)?(\d+S)?)?(\/.+)?$`. |

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
| Custom | `custom` (requires `timerValue`) |

### ISO 8601 Repeating Interval Format

`R/P[duration]` -- `R` means repeat indefinitely, followed by duration.

Examples: `R/PT10M` (every 10 min), `R/P2D` (every 2 days), `R/PT2H30M` (every 2.5 hours).

## Outputs

The scheduled trigger has an `output` source port but no formal `outputDefinition` in the schema. The port carries event metadata at runtime.

## Definition

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

## Instance Example

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

1. Forgetting to set `timerPreset`. It is required. Omitting it causes a validation error: "Frequency is required."
2. Using cron syntax instead of ISO 8601 repeating intervals. The scheduler expects values like `R/PT1H` or `R/P1D`, not `0 * * * *`.
3. Setting `timerPreset` to `"custom"` without providing `timerValue`. When preset is `"custom"`, `timerValue` is conditionally required.
4. Writing bare durations like `PT1H` instead of repeating intervals `R/PT1H`. The `R/` prefix is mandatory.
5. Using a UUID for `model.entryPointId` in the definition. The definition always uses `true`; the instance uses the actual UUID.
6. Forgetting to add `"eventDefinition": "bpmn:TimerEventDefinition"` to the `model` object. Without it the engine treats the node as a plain start event, not a timer event.
7. Having both a manual trigger and a scheduled trigger in the same flow. A flow must have exactly one trigger node -- remove one.
