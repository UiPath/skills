# Script (`core.action.script`)

**Version:** `1.0.0` | **Category:** data-operations | **BPMN Model:** `bpmn:ScriptTask`

`supportsErrorHandling: true`

## When to Use

Use a Script node for custom logic, data transformation, computation, or formatting that does not require an external call.

| Situation | Use Script? |
|-----------|-------------|
| Custom logic, string manipulation, computation | Yes |
| Standard map/filter/group-by on a collection | No -- use `core.action.transform` |
| Ambiguous input that needs reasoning or judgment | No -- use an Agent node |
| Calling an external API | No -- use `core.action.http` or a connector activity |
| Natural language generation | No -- use an Agent node |

### Runtime Constraints

- JavaScript only (ES2020 via Jint engine) -- not TypeScript, not Python.
- Must `return` an object: `return { key: value }` (not a bare scalar).
- No browser/DOM APIs (`fetch`, `document`, `window`, `setTimeout` are unavailable).
- No `console` object (`console.log` is unavailable).
- Cannot make HTTP calls or access external systems.
- 30-second execution timeout.
- `$vars` is available as a global for accessing upstream node outputs.

## Ports

| Direction | Port ID | Notes |
|-----------|---------|-------|
| target | `input` | `handleType: input` |
| source | `success` | `handleType: output` -- main output path |
| source | `error` | `handleType: output` -- visible only when `inputs.errorHandlingEnabled` is true, maxConnections: 1 |

## Inputs

| Field | Type | Required | Notes |
|-------|------|----------|-------|
| `script` | string | Yes (minLength: 1) | JavaScript expression that returns a result object. Default: `""`. Validation warning if empty. |

## Outputs

| Key | Type | Source Expression |
|-----|------|-------------------|
| `output` | object | `=result.response` |
| `error` | object | `=result.Error` |

The `error` output has fields: `code` (string), `message` (string), `detail` (string), `category` (string), `status` (integer).

## Definition

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

## Instance Example

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

1. Using `output` as the source port when wiring edges. The correct port is `success`. The `output` handle does not exist; the right-side source handle is named `success`.
2. Returning a scalar instead of an object from the script. The runtime expects `return { key: value };`, not `return 42;`.
3. Using `console.log`. The Jint runtime does not have `console`. Remove all `console.*` calls; use `return { debug: value }` to inspect values instead.
4. Leaving the `script` input as an empty string. The field has `minLength: 1` and will trigger a validation warning.
5. Accessing other node outputs incorrectly. Use `$vars.<nodeId>.output.<field>` to read data from upstream nodes.
6. Attempting to use `fetch`, `XMLHttpRequest`, or any other browser/DOM API. The Jint engine does not provide these; use an HTTP node or connector node for external calls.
7. Writing TypeScript or Python syntax. The engine supports JavaScript ES2020 only.
8. Omitting the `return` statement. The script must explicitly return an object or the output will be undefined.
