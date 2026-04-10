# Transform (`core.action.transform`)

**Version:** `1.0.0` | **Category:** data-operations | **BPMN Model:** `bpmn:ScriptTask`

`supportsErrorHandling: true`

## When to Use

Use a Transform node for declarative map, filter, or group-by on a collection -- no custom code needed. Multiple operations can be chained in a single node; each operation feeds into the next.

| Situation | Use Transform? |
|-----------|----------------|
| Standard filter/map/group-by on an array | Yes |
| Custom logic, string manipulation, computation | No -- use `core.action.script` |
| Iterate and perform actions per item (API calls, etc.) | No -- use a Loop node |

Specialized single-operation variants also exist: `core.action.transform.filter`, `core.action.transform.map`, and `core.action.transform.group-by`. Use the generic `core.action.transform` when chaining multiple operations in one node.

### Operation Types

**Filter** -- conditions: `equals`, `not_equals`, `greater`, `greater_equal`, `less`, `less_equal`, `contains`, `not_contains`, `starts_with`, `ends_with`. Combine with `"operation": "and"` (all match) or `"or"` (any match).

**Map** -- transformations: `copy` (no change), `uppercase`, `lowercase`, or a custom expression. Set `keepOriginalFields: false` to output only mapped fields; `true` passes unmapped fields through. Use `renameTo` for field renaming (empty string `""` keeps the original name).

**Group By** -- aggregation operations:

| Operation | Description | `field` required |
|-----------|-------------|------------------|
| `count` | Number of items in group | No |
| `sum` | Sum of numeric field | Yes |
| `average` | Average of numeric field | Yes |
| `min` | Minimum value | Yes |
| `max` | Maximum value | Yes |
| `collect` | Array of all field values | Yes |
| `first` | First item's field value | Yes |
| `last` | Last item's field value | Yes |

## Ports

| Direction | Port ID | Notes |
|-----------|---------|-------|
| target | `input` | `handleType: input` |
| source | `output` | `handleType: output` -- main output path |
| source | `error` | `handleType: output` -- visible only when `inputs.errorHandlingEnabled` is true, maxConnections: 1 |

## Inputs

| Field | Type | Required | Notes |
|-------|------|----------|-------|
| `operations` | array | No | Array of transform operations. Each operation has `id`, `type`, `config`, and `isCollapsed` fields. Default: `[]`. |
| `collection` | string | Yes | `$vars` reference to the input array (e.g., `$vars.fetchData.output.body.items`). The `=js:` prefix is optional -- both `$vars.x` and `=js:$vars.x` work. |

Each operation object requires:
- `id` -- unique identifier (format: `<type>-<timestamp>-<random>`)
- `type` -- `"filter"`, `"map"`, or `"groupBy"`
- `config` -- operation-specific settings
- `isCollapsed` -- boolean for UI state

## Outputs

| Key | Type | Source Expression |
|-----|------|-------------------|
| `output` | object | `=result.response` |
| `error` | object | `=Error` |

The `error` output has fields: `code` (string), `message` (string), `detail` (string), `category` (string), `status` (integer).

## Definition

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

## Instance Example

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

1. Confusing `core.action.transform` with `core.action.transform.filter`. The generic transform node supports multiple chained operations (map, filter, groupBy) in a single pipeline. The filter node is specialized for filtering only.
2. Using `success` as the output port name. Unlike `core.action.script`, the transform node's main output port is named `output`, not `success`.
3. Leaving the `operations` array empty and expecting output. Without at least one operation, the transform node passes data through without modification.
4. Forgetting to set `collection` in the inputs. The transform operates on a collection of items -- specify the source data using `$vars.<nodeId>.output` syntax.
5. Each operation object must have a unique `id` (format: `<type>-<timestamp>-<random>`), a `type` (e.g., `"map"`, `"filter"`, `"groupBy"`), and a `config` object containing the operation-specific settings.
6. Using `keepOriginalFields: false` in a map operation without including all desired fields in `mappings`. Only mapped fields appear in the output when this setting is false.
7. Referencing a `collection` whose `$vars` path evaluates to null. Verify the upstream node is connected and its output contains the expected array.
8. Using an invalid filter condition name. Valid conditions are: `equals`, `not_equals`, `greater`, `greater_equal`, `less`, `less_equal`, `contains`, `not_contains`, `starts_with`, `ends_with`.
