# Delay (`core.logic.delay`)

**Type:** `core.logic.delay`  **Version:** `1.0.0`  **Category:** control-flow
**BPMN Model:** `bpmn:IntermediateCatchEvent` with `eventDefinition: "bpmn:TimerEventDefinition"`

## When to Use

Use a Delay node to pause execution for a fixed duration or until a specific date/time.

| Situation | Use Delay? |
|-----------|------------|
| Fixed duration pause (wait 15 minutes, wait 1 day) | Yes |
| Wait until a specific date/time | Yes |
| Wait for external work to complete | No -- use a Queue node (`create-and-wait`) |
| Wait for human input | No -- use a Human in the Loop node |

## Ports

| Direction | Port ID | Notes |
|-----------|---------|-------|
| left | `input` | target, `handleType: input` |
| right | `output` | source, `handleType: output` |

## Inputs

| Field | Type | Required | Notes |
|-------|------|----------|-------|
| `timerType` | string | Yes | Timer mode: `"timeDuration"` (wait for a duration) or `"timeDate"` (wait until a specific date). Default: `"timeDuration"` |
| `timerPreset` | string | Yes | Duration preset or `"custom"`. Default: `"PT15M"`. Valid presets: `PT5S`, `PT15S`, `PT30S`, `PT1M`, `PT5M`, `PT15M`, `PT30M`, `PT1H`, `PT6H`, `PT12H`, `P1D`, `P1W`, `custom` |
| `timerValue` | string | Conditional | Custom ISO 8601 duration. Required when `timerType` is `"timeDuration"` and `timerPreset` is `"custom"`. Pattern: `^P(?!$)(\d+Y)?(\d+M)?(\d+W)?(\d+D)?(T(?=\d)(\d+H)?(\d+M)?(\d+S)?)?$`. Examples: `PT30S` (30 seconds), `PT2H30M` (2.5 hours), `P3DT12H` (3 days 12 hours) |
| `timerDate` | string | Conditional | Target date/time. Required when `timerType` is `"timeDate"`. Accepts ISO 8601 datetime or `=js:` expression |

## Outputs

None.

## Definition

```json
{
  "nodeType": "core.logic.delay",
  "version": "1.0.0",
  "category": "control-flow",
  "description": "Pause execution for a duration or until a date",
  "tags": [
    "control",
    "flow",
    "logic",
    "delay",
    "timer",
    "wait"
  ],
  "sortOrder": 20,
  "display": {
    "label": "Delay",
    "icon": "timer"
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
      ]
    },
    {
      "position": "right",
      "handles": [
        {
          "id": "output",
          "type": "source",
          "handleType": "output"
        }
      ]
    }
  ],
  "model": {
    "type": "bpmn:IntermediateCatchEvent",
    "eventDefinition": "bpmn:TimerEventDefinition",
    "values": {
      "timerType": "inputs.timerType",
      "timerValue": "inputs.timerValue",
      "timerPreset": "inputs.timerPreset",
      "timerDate": "inputs.timerDate"
    }
  },
  "inputDefinition": {
    "type": "object",
    "properties": {
      "timerType": {
        "type": "string",
        "minLength": 1,
        "errorMessage": "Timer type is required"
      },
      "timerPreset": {
        "type": "string",
        "minLength": 1,
        "errorMessage": "Duration is required"
      },
      "timerValue": {
        "type": "string"
      },
      "timerDate": {
        "type": "string"
      }
    },
    "required": [
      "timerType",
      "timerPreset"
    ],
    "allOf": [
      {
        "if": {
          "properties": {
            "timerType": {
              "const": "timeDuration"
            },
            "timerPreset": {
              "const": "custom"
            }
          },
          "required": [
            "timerType",
            "timerPreset"
          ]
        },
        "then": {
          "properties": {
            "timerValue": {
              "type": "string",
              "minLength": 1,
              "pattern": "^P(?!$)(\\d+Y)?(\\d+M)?(\\d+W)?(\\d+D)?(T(?=\\d)(\\d+H)?(\\d+M)?(\\d+S)?)?$",
              "errorMessage": "Custom duration is required (ISO 8601 format, e.g., PT15M, PT1H, P1D)"
            }
          },
          "required": [
            "timerValue"
          ]
        }
      },
      {
        "if": {
          "properties": {
            "timerType": {
              "const": "timeDate"
            }
          },
          "required": [
            "timerType"
          ]
        },
        "then": {
          "properties": {
            "timerDate": {
              "type": "string",
              "minLength": 1,
              "errorMessage": "Date is required"
            }
          },
          "required": [
            "timerDate"
          ]
        }
      }
    ]
  },
  "inputDefaults": {
    "timerType": "timeDuration",
    "timerPreset": "PT15M"
  },
  "form": {
    "id": "delay-properties",
    "title": "Delay",
    "sections": [
      {
        "id": "timer",
        "title": "Timer",
        "collapsible": true,
        "defaultExpanded": true,
        "fields": [
          {
            "name": "inputs.timerType",
            "type": "select",
            "label": "Type",
            "options": [
              {
                "label": "Duration",
                "value": "timeDuration"
              },
              {
                "label": "Date",
                "value": "timeDate"
              }
            ]
          },
          {
            "name": "inputs.timerPreset",
            "type": "select",
            "label": "Duration",
            "options": [
              {
                "label": "5 seconds",
                "value": "PT5S"
              },
              {
                "label": "15 seconds",
                "value": "PT15S"
              },
              {
                "label": "30 seconds",
                "value": "PT30S"
              },
              {
                "label": "1 minute",
                "value": "PT1M"
              },
              {
                "label": "5 minutes",
                "value": "PT5M"
              },
              {
                "label": "15 minutes",
                "value": "PT15M"
              },
              {
                "label": "30 minutes",
                "value": "PT30M"
              },
              {
                "label": "1 hour",
                "value": "PT1H"
              },
              {
                "label": "6 hours",
                "value": "PT6H"
              },
              {
                "label": "12 hours",
                "value": "PT12H"
              },
              {
                "label": "1 day",
                "value": "P1D"
              },
              {
                "label": "1 week",
                "value": "P1W"
              },
              {
                "label": "Custom",
                "value": "custom"
              }
            ],
            "rules": [
              {
                "id": "duration-presets",
                "conditions": [
                  {
                    "when": "inputs.timerType",
                    "is": "timeDuration"
                  }
                ],
                "effects": {
                  "visible": true
                }
              }
            ]
          },
          {
            "name": "inputs.timerValue",
            "type": "custom",
            "component": "iso-expression-field",
            "label": "Custom duration",
            "placeholder": "PT15M",
            "description": "ISO 8601 duration - use the AI button to generate from natural language",
            "componentProps": {
              "expressionType": "duration",
              "supportsExpressions": true
            },
            "rules": [
              {
                "id": "custom-duration",
                "conditions": [
                  {
                    "when": "inputs.timerType",
                    "is": "timeDuration"
                  },
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
          },
          {
            "name": "inputs.timerDate",
            "type": "datetime",
            "label": "Value",
            "description": "The date and time when the workflow should continue",
            "rules": [
              {
                "id": "date-format",
                "conditions": [
                  {
                    "when": "inputs.timerType",
                    "is": "timeDate"
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
  "id": "delay2",
  "type": "core.logic.delay",
  "typeVersion": "1.0.0",
  "ui": {
    "position": { "x": 3136, "y": 48 },
    "size": { "width": 96, "height": 96 },
    "collapsed": false
  },
  "display": {
    "label": "Delay 2",
    "subLabel": "Wait till 1 week before the DOJ",
    "icon": "timer"
  },
  "inputs": {
    "timerType": "timeDuration",
    "timerPreset": "PT5S"
  },
  "model": {
    "type": "bpmn:IntermediateCatchEvent",
    "eventDefinition": "bpmn:TimerEventDefinition",
    "values": {
      "timerType": "inputs.timerType",
      "timerValue": "inputs.timerValue",
      "timerPreset": "inputs.timerPreset",
      "timerDate": "inputs.timerDate"
    }
  }
}
```

## Common Mistakes

1. Using cron syntax (e.g., `0 */5 * * *`) instead of ISO 8601 duration format. The delay node requires ISO 8601 durations like `PT5M` (5 minutes), `PT1H` (1 hour), or `P1D` (1 day).
2. Confusing the delay node with a scheduled trigger. A delay pauses mid-flow after the workflow has started; a scheduled trigger (`core.trigger.scheduled`) starts the flow on a schedule.
3. Setting `timerPreset` to `"custom"` without providing `timerValue`. When using a custom duration, both fields are required and `timerValue` must match the ISO 8601 pattern.
4. Writing `5M` instead of `PT5M`. ISO 8601 durations must start with `P` and use `T` before time components (hours, minutes, seconds).
5. Omitting the `model.values` block from the node instance. The model must include the `values` mapping (`timerType`, `timerValue`, `timerPreset`, `timerDate`) so the BPMN engine can resolve timer configuration from inputs.
6. Missing `eventDefinition` in the model. The node instance must include `"eventDefinition": "bpmn:TimerEventDefinition"` in the `model` block. Omitting it produces an invalid BPMN model.
