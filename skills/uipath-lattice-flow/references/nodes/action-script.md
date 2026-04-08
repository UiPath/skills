# Script

**Type:** `core.action.script`  **Version:** `1.0.0`  **Category:** data-operations
**BPMN Model:** `bpmn:ScriptTask`

`supportsErrorHandling: true`

## Ports

| Position | Handle ID | Type | Notes |
|----------|-----------|------|-------|
| left | `input` | target | `handleType: input` |
| right | `success` | source | `handleType: output` -- main output path |
| right | `error` | source | `handleType: output` -- visible only when `inputs.errorHandlingEnabled` is true, max 1 connection |

## Inputs

| Field | Type | Required | Default | Description |
|-------|------|----------|---------|-------------|
| `script` | string | **Yes** (minLength 1) | `""` | JavaScript expression that returns a result object. |

## Outputs

| Key | Type | Description | Source Expression |
|-----|------|-------------|-------------------|
| `output` | object | The return value of the script. | `=result.response` |
| `error` | object | Error information if the script fails (has `code`, `message`, `detail`, `category`, `status` fields). | `=result.Error` |

## Definition Block

Copy this verbatim into the `definitions` array (do not modify):

```json
{
  "nodeType": "core.action.script",
  "version": "1.0.0",
  "category": "data-operations",
  "description": "Run custom JavaScript code",
  "tags": [
    "code",
    "javascript",
    "python"
  ],
  "sortOrder": 35,
  "supportsErrorHandling": true,
  "display": {
    "label": "Script",
    "icon": "code",
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
      ]
    },
    {
      "position": "right",
      "handles": [
        {
          "id": "success",
          "type": "source",
          "handleType": "output"
        },
        {
          "id": "error",
          "label": "Error",
          "type": "source",
          "handleType": "output",
          "visible": "{inputs.errorHandlingEnabled}",
          "constraints": {
            "maxConnections": 1
          }
        }
      ]
    }
  ],
  "debug": {
    "runtime": "bpmnEngine"
  },
  "model": {
    "type": "bpmn:ScriptTask"
  },
  "inputDefinition": {
    "type": "object",
    "properties": {
      "script": {
        "type": "string",
        "minLength": 1,
        "errorMessage": "A script function is required",
        "validationSeverity": "warning"
      }
    },
    "required": [
      "script"
    ]
  },
  "inputDefaults": {
    "script": ""
  },
  "outputDefinition": {
    "output": {
      "type": "object",
      "description": "The return value of the script",
      "source": "=result.response",
      "var": "output"
    },
    "error": {
      "type": "object",
      "description": "Error information if the script fails",
      "source": "=result.Error",
      "var": "error",
      "schema": {
        "$schema": "http://json-schema.org/draft-07/schema#",
        "type": "object",
        "required": [
          "code",
          "message",
          "detail",
          "category",
          "status"
        ],
        "properties": {
          "code": {
            "type": "string",
            "description": "Error code as a string"
          },
          "message": {
            "type": "string",
            "description": "High-level error message"
          },
          "detail": {
            "type": "string",
            "description": "Detailed error description"
          },
          "category": {
            "type": "string",
            "description": "Error category"
          },
          "status": {
            "type": "integer",
            "description": "HTTP status code"
          }
        },
        "additionalProperties": false
      }
    }
  },
  "form": {
    "id": "script-properties",
    "title": "Script configuration",
    "sections": [
      {
        "id": "script",
        "title": "Script",
        "collapsible": true,
        "defaultExpanded": true,
        "fields": [
          {
            "name": "inputs.script",
            "type": "custom",
            "component": "script-editor",
            "componentProps": {
              "language": "javascript",
              "returnType": "any",
              "minHeight": 200,
              "placeholder": " // Return an object with your result\nreturn {\n  message: \"Web request response\",\n  data: $vars.httpRequest1.output\n                  };"
            },
            "label": "Code",
            "description": "JavaScript expression that returns a result object"
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
  "id": "rollDice",
  "type": "core.action.script",
  "typeVersion": "1.0.0",
  "ui": {
    "position": { "x": 450, "y": 200 },
    "size": { "width": 96, "height": 96 },
    "collapsed": false
  },
  "display": {
    "label": "Roll Dice"
  },
  "inputs": {
    "script": "return { diceResult: Math.floor(Math.random() * 6) + 1 };"
  },
  "outputs": {
    "output": {
      "type": "object",
      "description": "The return value of the script",
      "source": "=result.response",
      "var": "output"
    },
    "error": {
      "type": "object",
      "description": "Error information if the script fails",
      "schema": {
        "$schema": "http://json-schema.org/draft-07/schema#",
        "type": "object",
        "required": [
          "code",
          "message",
          "detail",
          "category",
          "status"
        ],
        "properties": {
          "code": {
            "type": "string",
            "description": "Error code as a string"
          },
          "message": {
            "type": "string",
            "description": "High-level error message"
          },
          "detail": {
            "type": "string",
            "description": "Detailed error description"
          },
          "category": {
            "type": "string",
            "description": "Error category"
          },
          "status": {
            "type": "integer",
            "description": "HTTP status code"
          }
        },
        "additionalProperties": false
      },
      "source": "=result.Error",
      "var": "error"
    }
  },
  "model": {
    "type": "bpmn:ScriptTask"
  }
}
```

## Common Mistakes

- Using `output` as the source port when wiring edges -- the correct port is `success`. The `output` handle does not exist; the right-side source handle is named `success`.
- Returning a scalar instead of an object from the script. The runtime expects `return { key: value };`, not `return 42;`.
- Using `console.log` -- the Jint runtime does not have `console`. Remove all `console.*` calls.
- Leaving the `script` input as an empty string. The field has `minLength: 1` and will trigger a validation warning.
- Accessing other node outputs incorrectly. Use `$vars.<nodeId>.output.<field>` to read data from upstream nodes.
