# Filter

**Type:** `core.action.transform.filter`  **Version:** `1.0.0`  **Category:** data-operations
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
| `operations` | array | No | `[]` | Array containing a single filter operation. Each operation has `id`, `type` (`"filter"`), `config`, and `isCollapsed` fields. Configured via the `filter-operation-editor` component. |

The filter operation `config` contains:
- `operation`: Logical combinator -- `"and"` (all conditions must match) or `"or"` (any condition matches)
- `filters`: Array of filter rules, each with `id`, `field`, `condition`, `value`, and optional `fieldType`
- `script`: Auto-generated JavaScript function that applies the filter

Supported conditions: `equals`, `not_equals`, `greater_than`, `less_than`, `greater_equal`, `less_equal`, `contains`, `starts_with`, `ends_with`, `is_null`, `is_not_null`.

## Outputs

| Key | Type | Description | Source Expression |
|-----|------|-------------|-------------------|
| `output` | object | The filtered data result | `=result.response` |
| `error` | object | Error information if the node fails (has `code`, `message`, `detail`, `category`, `status` fields). | `=Error` |

## Definition Block

Copy this verbatim into the `definitions` array (do not modify):

```json
{
  "nodeType": "core.action.transform.filter",
  "supportsErrorHandling": true,
  "version": "1.0.0",
  "category": "data-operations",
  "description": "Filter data by conditions",
  "tags": [
    "data",
    "transformation",
    "filter"
  ],
  "sortOrder": 35,
  "display": {
    "label": "Filter",
    "icon": "list-filter",
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
    "id": "data-transform-filter-form",
    "title": "Filter",
    "sections": [
      {
        "defaultExpanded": true,
        "id": "filter-section",
        "title": "Filter configuration",
        "fields": [
          {
            "name": "inputs",
            "type": "custom",
            "component": "filter-operation-editor",
            "componentProps": {},
            "label": "Filter configuration"
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
  "id": "filter1",
  "type": "core.action.transform.filter",
  "typeVersion": "1.0.0",
  "ui": {
    "position": { "x": 960, "y": 16 },
    "size": { "width": 96, "height": 96 },
    "collapsed": false
  },
  "display": {
    "label": "Filter",
    "subLabel": "",
    "iconBackground": "linear-gradient(225deg, #FAFAFB 0%, #ECEDEF 100%)",
    "iconBackgroundDark": "linear-gradient(225deg, #526069 0%, rgba(50, 60, 66, 0.6) 100%)",
    "icon": "list-filter"
  },
  "inputs": {
    "operations": [
      {
        "id": "filter-1773950362435-6psm7",
        "type": "filter",
        "config": {
          "operation": "and",
          "filters": [
            {
              "id": "filter-1773950383008-hl43d",
              "field": "autonomousAgent1.requiresReleaseNote",
              "condition": "equals",
              "value": "true",
              "fieldType": "boolean"
            }
          ]
        },
        "isCollapsed": false
      }
    ],
    "collection": "$vars.loop1.output"
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
      },
      "source": "=Error",
      "var": "error"
    }
  },
  "model": {
    "type": "bpmn:ScriptTask"
  }
}
```

## Common Mistakes

- Using `core.action.transform.filter` when `core.action.transform` with a filter operation would be more appropriate. For complex pipelines that chain filter + map + groupBy, use the transform node with multiple operations. The filter node is specialized for simple single-filter use cases.
- Omitting the `collection` input. The filter must know which data to filter -- set `collection` to a `$vars.<nodeId>.output` expression pointing to the upstream data source.
- Using `success` as the output port name. Like the transform node, the filter's main output port is `output`, not `success`.
- Forgetting that the `config.script` field is auto-generated by the editor. Do not write the filter script manually -- define the filter rules in `config.filters` and let the editor generate the script. If generating programmatically, the script must match the filter rules exactly.
- Setting `config.operation` to an unsupported value. Only `"and"` and `"or"` are valid logical combinators.
