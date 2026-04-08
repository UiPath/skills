# Transform

**Type:** `core.action.transform`  **Version:** `1.0.0`  **Category:** data-operations
**BPMN Model:** `bpmn:ScriptTask`

`supportsErrorHandling: true`

## Ports

| Position | Handle ID | Type | Notes |
|----------|-----------|------|-------|
| left | `input` | target | `handleType: input` |
| right | `output` | source | `handleType: output` -- main output path |
| right | `error` | source | `handleType: output` -- visible only when `inputs.errorHandlingEnabled` is true, max 1 connection |

## Inputs

| Field | Type | Required | Default | Description |
|-------|------|----------|---------|-------------|
| `operations` | array | No | `[]` | Array of transform operations (map, filter, groupBy, etc.). Each operation has `id`, `type`, `config`, and `isCollapsed` fields. Configured via the `data-transformer-editor` component. |

## Outputs

| Key | Type | Description | Source Expression |
|-----|------|-------------|-------------------|
| `output` | object | The transformed data result | `=result.response` |
| `error` | object | Error information if the node fails (has `code`, `message`, `detail`, `category`, `status` fields). | `=Error` |

## Definition Block

Copy this verbatim into the `definitions` array (do not modify):

```json
{
  "nodeType": "core.action.transform",
  "supportsErrorHandling": true,
  "version": "1.0.0",
  "category": "data-operations",
  "description": "Reshape and convert data with operations",
  "tags": [
    "data",
    "transformation"
  ],
  "sortOrder": 35,
  "display": {
    "label": "Transform",
    "icon": "a-large-small",
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
          "id": "output",
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
    "runtime": "clientScript"
  },
  "model": {
    "type": "bpmn:ScriptTask"
  },
  "inputDefinition": {
    "type": "object",
    "properties": {
      "operations": {
        "type": "array"
      }
    }
  },
  "inputDefaults": {
    "operations": []
  },
  "outputDefinition": {
    "output": {
      "type": "object",
      "description": "The transformed data result",
      "source": "=result.response",
      "var": "output"
    },
    "error": {
      "type": "object",
      "description": "Error information if the node fails",
      "source": "=Error",
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
    "id": "transform-data-form",
    "title": "Transform",
    "sections": [
      {
        "defaultExpanded": true,
        "id": "transform-section",
        "title": "Operation(s)",
        "fields": [
          {
            "name": "inputs",
            "type": "custom",
            "component": "data-transformer-editor",
            "componentProps": {},
            "label": "Transform Operations"
          }
        ],
        "collapsible": true
      }
    ]
  }
}
```

## Node Instance Example

```json
{
  "id": "transform1",
  "type": "core.action.transform",
  "typeVersion": "1.0.0",
  "ui": {
    "position": { "x": 560, "y": 144 },
    "size": { "width": 96, "height": 96 },
    "collapsed": false
  },
  "display": {
    "label": "Transform",
    "subLabel": "",
    "iconBackground": "linear-gradient(225deg, #FAFAFB 0%, #ECEDEF 100%)",
    "iconBackgroundDark": "linear-gradient(225deg, #526069 0%, rgba(50, 60, 66, 0.6) 100%)",
    "icon": "a-large-small"
  },
  "inputs": {
    "operations": [
      {
        "id": "map-1773949511405-wzfmw",
        "type": "map",
        "config": {
          "mappings": [
            {
              "id": "mapping-1773949514268-sf5vi",
              "field": "id",
              "transformation": "copy"
            },
            {
              "id": "mapping-1773949537769-s6xxo",
              "field": "fields.description",
              "transformation": "copy",
              "renameTo": "description"
            }
          ],
          "keepOriginalFields": false
        },
        "isCollapsed": false
      }
    ],
    "collection": "$vars.searchIssuesByJql1.output"
  },
  "outputs": {
    "output": {
      "type": "object",
      "description": "The transformed data result",
      "source": "=result.response",
      "var": "output"
    },
    "error": {
      "type": "object",
      "description": "Error information if the node fails",
      "source": "=Error",
      "var": "error",
      "schema": {
        "$schema": "http://json-schema.org/draft-07/schema#",
        "type": "object",
        "required": ["code", "message", "detail", "category", "status"],
        "properties": {
          "code": { "type": "string", "description": "Error code as a string" },
          "message": { "type": "string", "description": "High-level error message" },
          "detail": { "type": "string", "description": "Detailed error description" },
          "category": { "type": "string", "description": "Error category" },
          "status": { "type": "integer", "description": "HTTP status code" }
        },
        "additionalProperties": false
      }
    }
  },
  "model": {
    "type": "bpmn:ScriptTask"
  }
}
```

## Common Mistakes

- Confusing `core.action.transform` with `core.action.transform.filter`. The transform node supports multiple chained operations (map, filter, groupBy, etc.) in a single pipeline. The filter node is specialized for filtering only.
- Using `success` as the output port name. Unlike `core.action.script`, the transform node's main output port is named `output`, not `success`.
- Leaving the `operations` array empty and expecting output. Without at least one operation, the transform node passes data through without modification.
- Forgetting to set `collection` in the inputs. The transform operates on a collection of items -- specify the source data using `$vars.<nodeId>.output` syntax.
- Each operation object must have a unique `id` (format: `<type>-<timestamp>-<random>`), a `type` (e.g., `"map"`, `"filter"`, `"groupBy"`), and a `config` object containing the operation-specific settings.
