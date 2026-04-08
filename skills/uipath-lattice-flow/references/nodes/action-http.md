# HTTP Request

**Type:** `core.action.http`  **Version:** `1.0.0`  **Category:** data-operations
**BPMN Model:** `bpmn:ServiceTask` (expands to SubProcess at compile time)

## Ports

| Position | Handle ID | Type | Notes |
|----------|-----------|------|-------|
| left | `input` | target | `handleType: input` |
| right | `branch-{item.id}` | source | Dynamic per branch. `repeat: "inputs.branches"`, label `{item.name}` |
| right | `default` | source | Always present. Label `Default` |
| right | `error` | source | Only when `supportsErrorHandling: true` and an edge is connected |

## Inputs

| Field | Type | Required | Default | Description |
|-------|------|----------|---------|-------------|
| `mode` | string | no | `"manual"` | `"manual"` or `"apiDefinition"` |
| `method` | string | yes | `"GET"` | HTTP method: `GET`, `POST`, `PUT`, `PATCH`, `DELETE` |
| `url` | string | yes | `""` | Request URL. Must be a valid URL or variable expression (`$vars.*`) |
| `headers` | object | no | `{}` | Key-value pairs for HTTP headers |
| `queryParams` | object | no | `{}` | Key-value pairs for URL query parameters |
| `body` | string | no | `""` | Request body (expression or literal) |
| `contentType` | string | no | `"application/json"` | MIME type: `application/json`, `application/xml`, `text/plain`, `application/x-www-form-urlencoded` |
| `timeout` | string | no | `"PT15M"` | ISO 8601 duration (e.g., `PT15M`, `PT1H`, `P1D`) |
| `retryCount` | number | no | `0` | Number of retry attempts on failure |
| `branches` | array | no | `[]` | Response-routing branches. Each object: `{ id, name, conditionExpression }` |
| `authenticationType` | string | no | `"manual"` | Authentication type |
| `application` | string | no | `""` | Application identifier (for connector auth) |
| `connection` | string | no | `""` | Connection identifier (for connector auth) |
| `swaggerDefinition` | object/null | no | `null` | OpenAPI definition (for `apiDefinition` mode) |

## Outputs

| Key | Type | Description | Source Expression |
|-----|------|-------------|-------------------|
| `response` | object | HTTP response with `body` (string), `statusCode` (number), `headers` (object) | `=response` |
| `error` | object | Error object with `code`, `message`, `detail`, `category`, `status` fields | `=Error` |

## Definition Block

Copy this verbatim into the `definitions` array (do not modify):

```json
{
  "nodeType": "core.action.http",
  "version": "1.0.0",
  "category": "data-operations",
  "tags": ["connector", "http", "api", "rest", "request"],
  "sortOrder": 1,
  "supportsErrorHandling": true,
  "display": {
    "label": "HTTP Request",
    "icon": "globe"
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
      ],
      "visible": true
    },
    {
      "position": "right",
      "handles": [
        {
          "id": "branch-{item.id}",
          "type": "source",
          "handleType": "output",
          "label": "{item.name}",
          "repeat": "inputs.branches"
        },
        {
          "id": "default",
          "label": "Default",
          "type": "source",
          "handleType": "output"
        }
      ],
      "visible": true
    }
  ],
  "model": {
    "type": "bpmn:ServiceTask",
    "expansion": {
      "processLevelVariables": [
        {
          "id": "{nodeId}.output",
          "name": "output",
          "type": "jsonSchema",
          "elementId": "{nodeId}",
          "custom": true
        },
        {
          "condition": "hasEdgeFromHandle('error')",
          "id": "{nodeId}.error",
          "name": "error",
          "type": "jsonSchema",
          "elementId": "{nodeId}",
          "custom": true
        },
        {
          "condition": "!hasEdgeFromHandle('error')",
          "id": "{nodeId}.boundaryError",
          "name": "Error",
          "type": "jsonSchema",
          "elementId": "_Implicit_SubprocessBoundaryError_{nodeId}"
        }
      ],
      "nodes": [
        {
          "id": "{nodeId}",
          "type": "bpmn:SubProcess",
          "replaceOriginal": true,
          "data": {
            "label": "{node.data.label}",
            "isExpanded": true,
            "model": {
              "serviceType": "BPMN.Variables",
              "subprocessVariables": {
                "inputOutputs": [
                  {
                    "id": "response",
                    "name": "response",
                    "type": "jsonSchema",
                    "variableType": "inputOutput"
                  },
                  {
                    "id": "error",
                    "name": "error",
                    "type": "jsonSchema",
                    "variableType": "inputOutput"
                  }
                ]
              },
              "outputs": [
                {
                  "name": "output",
                  "type": "jsonSchema",
                  "source": "=vars.response",
                  "var": "{nodeId}.output",
                  "custom": true
                },
                {
                  "name": "Error",
                  "type": "jsonSchema",
                  "source": "=vars.error",
                  "var": "{nodeId}.error",
                  "custom": true
                }
              ]
            }
          },
          "nodes": [
            {
              "id": "_Implicit_StartEvent_{nodeId}",
              "type": "bpmn:StartEvent",
              "parentId": "{nodeId}",
              "position": { "x": 0, "y": 0 },
              "data": {
                "label": "HTTP Request Start"
              }
            },
            {
              "id": "_Implicit_HttpTask_{nodeId}",
              "type": "bpmn:SendTask",
              "parentId": "{nodeId}",
              "position": { "x": 0, "y": 0 },
              "propagate": {
                "retry": {
                  "condition": "node.data.inputs.retryCount > 0",
                  "maxRetryCount": "node.data.inputs.retryCount",
                  "retryBackoff": "node.data.inputs.timeout",
                  "retryBackoffDefault": "PT1S",
                  "retryAllErrors": "true",
                  "retryBackoffType": "Static"
                }
              },
              "data": {
                "label": "{node.data.label}",
                "model": {
                  "serviceType": "Intsvc.HttpExecution",
                  "version": "v1",
                  "context": [
                    { "name": "mode", "type": "string", "source": "node.data.inputs.mode" },
                    { "name": "method", "type": "string", "source": "node.data.inputs.method" },
                    { "name": "url", "type": "string", "source": "node.data.inputs.url" },
                    { "name": "headers", "type": "json", "source": "node.data.inputs.headers", "format": "json" },
                    { "name": "parameters", "type": "json", "source": "node.data.inputs.queryParams", "format": "json" },
                    { "name": "body", "type": "json", "source": "node.data.inputs.body", "format": "json" }
                  ],
                  "outputs": [{ "name": "response", "type": "json", "source": "=response", "var": "response", "internal": true }]
                }
              }
            },
            {
              "id": "_Implicit_EndEvent_Default_{nodeId}",
              "type": "bpmn:EndEvent",
              "parentId": "{nodeId}",
              "position": { "x": 0, "y": 0 },
              "data": {
                "label": "Default"
              }
            },
            {
              "condition": "hasEdgeFromHandle('error')",
              "id": "_Implicit_EndEvent_Failure_{nodeId}",
              "type": "bpmn:EndEvent",
              "parentId": "{nodeId}",
              "position": { "x": 0, "y": 0 },
              "data": {
                "label": "Failure"
              }
            },
            {
              "condition": "hasEdgeFromHandle('error')",
              "id": "_Implicit_BoundaryError_{nodeId}",
              "type": "bpmn:BoundaryEvent",
              "parentId": "{nodeId}",
              "position": { "x": 0, "y": 0 },
              "data": {
                "label": "Error",
                "attachedToId": "_Implicit_HttpTask_{nodeId}",
                "eventDefinition": {
                  "type": "bpmn:ErrorEventDefinition",
                  "id": "_Implicit_BoundaryError_{nodeId}_Error"
                },
                "model": {
                  "outputs": [{ "name": "Error", "type": "jsonSchema", "source": "=Error", "var": "error", "internal": true }]
                }
              }
            }
          ],
          "edges": [
            {
              "id": "_Implicit_Edge__Implicit_StartEvent_{nodeId}__Implicit_HttpTask_{nodeId}",
              "source": "_Implicit_StartEvent_{nodeId}",
              "target": "_Implicit_HttpTask_{nodeId}",
              "type": "bpmn:SequenceFlow",
              "data": {}
            },
            {
              "id": "_Implicit_Edge__Implicit_HttpTask_{nodeId}__Implicit_EndEvent_Default_{nodeId}",
              "source": "_Implicit_HttpTask_{nodeId}",
              "target": "_Implicit_EndEvent_Default_{nodeId}",
              "type": "bpmn:SequenceFlow",
              "data": {}
            },
            {
              "condition": "hasEdgeFromHandle('error')",
              "id": "_Implicit_Edge__Implicit_BoundaryError_{nodeId}__Implicit_EndEvent_Failure_{nodeId}",
              "source": "_Implicit_BoundaryError_{nodeId}",
              "target": "_Implicit_EndEvent_Failure_{nodeId}",
              "type": "bpmn:SequenceFlow",
              "data": {}
            }
          ]
        },
        {
          "condition": "!hasEdgeFromHandle('error')",
          "id": "_Implicit_SubprocessBoundaryError_{nodeId}",
          "type": "bpmn:BoundaryEvent",
          "parentId": null,
          "position": { "x": 0, "y": 0 },
          "data": {
            "label": "",
            "attachedToId": "{nodeId}",
            "eventDefinition": {
              "type": "bpmn:ErrorEventDefinition",
              "id": "_Implicit_SubprocessBoundaryError_{nodeId}_Error"
            },
            "model": {
              "outputs": [{ "name": "Error", "type": "jsonSchema", "source": "=Error", "var": "{nodeId}.boundaryError" }]
            }
          }
        },
        {
          "id": "_Implicit_PostSubprocessGateway_{nodeId}",
          "type": "bpmn:ExclusiveGateway",
          "condition": "(node.data.inputs.branches.length > 0 || hasEdgeFromHandle('error')) && originalEdges.length > 0",
          "parentId": null,
          "position": { "x": 0, "y": 0 },
          "data": {
            "label": "Post-Subprocess Branch"
          }
        }
      ],
      "edges": [
        {
          "condition": "(node.data.inputs.branches.length > 0 || hasEdgeFromHandle('error')) && originalEdges.length > 0",
          "id": "_Implicit_Edge_{nodeId}__Implicit_PostSubprocessGateway_{nodeId}",
          "source": "{nodeId}",
          "target": "_Implicit_PostSubprocessGateway_{nodeId}",
          "type": "bpmn:SequenceFlow",
          "data": {}
        },
        {
          "forEach": "node.data.inputs.branches",
          "condition": "node.data.inputs.branches.length > 0",
          "matchOriginalEdgeByHandle": "branch-{branch.id}",
          "preserveEdgeId": true,
          "source": "_Implicit_PostSubprocessGateway_{nodeId}",
          "type": "bpmn:SequenceFlow",
          "data": {
            "conditionExpression": "{branch.conditionExpression}",
            "label": "{branch.name}"
          }
        },
        {
          "condition": "node.data.inputs.branches.length > 0 || hasEdgeFromHandle('error')",
          "matchOriginalEdgeByHandle": "default",
          "preserveEdgeId": true,
          "source": "_Implicit_PostSubprocessGateway_{nodeId}",
          "type": "bpmn:SequenceFlow",
          "data": {
            "label": "Default"
          }
        },
        {
          "condition": "hasEdgeFromHandle('error')",
          "matchOriginalEdgeByHandle": "error",
          "preserveEdgeId": true,
          "source": "_Implicit_PostSubprocessGateway_{nodeId}",
          "type": "bpmn:SequenceFlow",
          "data": {
            "conditionExpression": "=js:vars.{nodeId}.error != null || (vars.{nodeId}.output != null && vars.{nodeId}.output.statusCode >= 400)",
            "label": "Error"
          }
        },
        {
          "condition": "node.data.inputs.branches.length === 0 && !hasEdgeFromHandle('error')",
          "matchOriginalEdgeByHandle": "default",
          "preserveEdgeId": true,
          "source": "{nodeId}",
          "type": "bpmn:SequenceFlow"
        }
      ]
    }
  },
  "inputDefinition": {
    "type": "object",
    "properties": {
      "mode": {
        "type": "string"
      },
      "method": {
        "type": "string",
        "minLength": 1,
        "errorMessage": "Method is required"
      },
      "url": {
        "type": "string",
        "minLength": 1,
        "pattern": "^(.*\\.\\S.*|.*\\$vars.*)$",
        "errorMessage": {
          "minLength": "URL is required",
          "pattern": "URL must be a valid URL or variable expression"
        }
      },
      "swaggerDefinition": {
        "type": ["object", "null"]
      },
      "authenticationType": {
        "type": "string"
      },
      "application": {
        "type": "string"
      },
      "connection": {
        "type": "string"
      },
      "headers": {
        "type": "object"
      },
      "queryParams": {
        "type": "object"
      },
      "body": {
        "type": "string"
      },
      "contentType": {
        "type": "string"
      },
      "timeout": {
        "type": "string",
        "pattern": "^P(?!$)(\\d+Y)?(\\d+M)?(\\d+W)?(\\d+D)?(T(?=\\d)(\\d+H)?(\\d+M)?(\\d+S)?)?$",
        "errorMessage": {
          "pattern": "Timeout must be in ISO 8601 duration format (e.g., PT15M, PT1H, P1D)"
        }
      },
      "retryCount": {
        "type": "number"
      },
      "branches": {
        "type": "array",
        "items": {
          "type": "object",
          "properties": {
            "id": {
              "type": "string"
            },
            "name": {
              "type": "string"
            },
            "conditionExpression": {
              "type": "string"
            }
          }
        }
      }
    },
    "required": ["method", "url"]
  },
  "inputDefaults": {
    "mode": "manual",
    "method": "GET",
    "url": "",
    "swaggerDefinition": null,
    "authenticationType": "manual",
    "application": "",
    "connection": "",
    "headers": {},
    "queryParams": {},
    "body": "",
    "contentType": "application/json",
    "timeout": "PT15M",
    "retryCount": 0,
    "branches": []
  },
  "outputDefinition": {
    "response": {
      "type": "object",
      "description": "HTTP response object",
      "source": "=response",
      "var": "response",
      "properties": {
        "body": {
          "type": "string",
          "description": "Response body content"
        },
        "statusCode": {
          "type": "number",
          "description": "HTTP status code"
        },
        "headers": {
          "type": "object",
          "description": "Response headers",
          "additionalProperties": {
            "type": "string"
          }
        }
      }
    },
    "error": {
      "type": "object",
      "description": "Error message if request failed",
      "source": "=Error",
      "var": "error",
      "schema": {
        "$schema": "http://json-schema.org/draft-07/schema#",
        "type": "object",
        "required": ["code", "message", "detail", "category", "status"],
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
    "id": "http-properties",
    "title": "HTTP Request",
    "sections": [
      {
        "id": "implementation",
        "title": "Implementation",
        "collapsible": true,
        "defaultExpanded": true,
        "fields": [
          {
            "name": "inputs._httpToolbar",
            "type": "custom",
            "component": "http-curl-buttons",
            "label": ""
          },
          {
            "name": "inputs.mode",
            "type": "select",
            "label": "Mode",
            "options": [
              {
                "label": "Manual",
                "value": "manual"
              },
              {
                "label": "API Definition",
                "value": "apiDefinition"
              }
            ]
          },
          {
            "name": "inputs.swaggerDefinition",
            "type": "custom",
            "component": "http-swagger-section",
            "label": "",
            "rules": [
              {
                "id": "show-swagger",
                "conditions": [{ "when": "inputs.mode", "is": "apiDefinition" }],
                "effects": { "visible": true }
              }
            ]
          },
          {
            "name": "inputs.method",
            "type": "select",
            "label": "HTTP Method",
            "options": [
              {
                "label": "GET",
                "value": "GET"
              },
              {
                "label": "POST",
                "value": "POST"
              },
              {
                "label": "PUT",
                "value": "PUT"
              },
              {
                "label": "PATCH",
                "value": "PATCH"
              },
              {
                "label": "DELETE",
                "value": "DELETE"
              }
            ]
          },
          {
            "name": "inputs.url",
            "type": "custom",
            "component": "http-url-field",
            "label": "URL"
          }
        ]
      },
      {
        "id": "headers",
        "title": "Headers",
        "collapsible": true,
        "defaultExpanded": false,
        "fields": [
          {
            "name": "inputs.headers",
            "type": "custom",
            "component": "key-value-editor",
            "label": "HTTP Headers",
            "componentProps": {
              "keyLabel": "Header Name",
              "valueLabel": "Header Value",
              "keyOptions": [
                "Accept",
                "Accept-Encoding",
                "Accept-Language",
                "Authorization",
                "Cache-Control",
                "Connection",
                "Content-Encoding",
                "Content-Length",
                "Content-Type",
                "Cookie",
                "Host",
                "If-Modified-Since",
                "If-None-Match",
                "Origin",
                "Referer",
                "User-Agent",
                "X-Requested-With",
                "X-Forwarded-For",
                "X-Api-Key"
              ]
            }
          }
        ]
      },
      {
        "id": "parameters",
        "title": "Query Parameters",
        "collapsible": true,
        "defaultExpanded": false,
        "fields": [
          {
            "name": "inputs.queryParams",
            "type": "custom",
            "component": "key-value-editor",
            "label": "Query Parameters",
            "componentProps": {
              "keyLabel": "Parameter Name",
              "valueLabel": "Parameter Value"
            }
          }
        ]
      },
      {
        "id": "body",
        "title": "Body",
        "collapsible": true,
        "defaultExpanded": false,
        "fields": [
          {
            "name": "inputs.contentType",
            "type": "select",
            "label": "Content Type",
            "options": [
              {
                "label": "application/json",
                "value": "application/json"
              },
              {
                "label": "application/xml",
                "value": "application/xml"
              },
              {
                "label": "text/plain",
                "value": "text/plain"
              },
              {
                "label": "application/x-www-form-urlencoded",
                "value": "application/x-www-form-urlencoded"
              }
            ]
          },
          {
            "name": "inputs.body",
            "type": "custom",
            "component": "code-editor",
            "label": "Body",
            "componentProps": {
              "language": "javascript",
              "mode": "expression",
              "expectedType": "any",
              "minHeight": 150,
              "placeholder": "{\n  \"key\": \"value\"\n}"
            }
          }
        ]
      },
      {
        "id": "branches",
        "title": "Branches",
        "collapsible": true,
        "defaultExpanded": false,
        "fields": [
          {
            "name": "inputs.branches",
            "type": "custom",
            "component": "http-branch-editor",
            "label": "Response Branches",
            "description": "Define conditional branches based on response status or properties"
          }
        ]
      },
      {
        "id": "advanced",
        "title": "Advanced",
        "collapsible": true,
        "defaultExpanded": false,
        "fields": [
          {
            "name": "inputs.timeout",
            "type": "text",
            "label": "Timeout",
            "description": "ISO 8601 duration format (e.g., PT15M for 15 minutes, PT1H for 1 hour)"
          },
          {
            "name": "inputs.retryCount",
            "type": "number",
            "label": "Retry Count",
            "description": "Number of times to retry on failure"
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
  "id": "http_1",
  "type": "core.action.http",
  "typeVersion": "1.0.0",
  "ui": {
    "position": { "x": 500, "y": 200 },
    "size": { "width": 256, "height": 96 },
    "collapsed": false
  },
  "display": {
    "label": "HTTP Request"
  },
  "inputs": {
    "mode": "manual",
    "method": "POST",
    "url": "https://api.example.com/data",
    "headers": {
      "Authorization": "Bearer $vars.token"
    },
    "queryParams": {},
    "body": "={ \"name\": $vars.userName }",
    "contentType": "application/json",
    "timeout": "PT15M",
    "retryCount": 0,
    "branches": [
      {
        "id": "success-2xx",
        "name": "Success",
        "conditionExpression": "=js:vars.http_1.output.statusCode >= 200 && vars.http_1.output.statusCode < 300"
      }
    ],
    "authenticationType": "manual",
    "swaggerDefinition": null,
    "application": "",
    "connection": ""
  },
  "outputs": {
    "response": {
      "type": "object",
      "description": "HTTP response object",
      "source": "=response",
      "var": "response"
    },
    "error": {
      "type": "object",
      "description": "Error message if request failed",
      "source": "=Error",
      "var": "error"
    }
  },
  "model": {
    "type": "bpmn:ServiceTask"
  }
}
```

## Common Mistakes

- Forgetting branch port edges. Every entry in `inputs.branches` creates a dynamic right-side port `branch-{id}`. Each port must have an edge connected to a downstream node or the branch is unreachable.
- Using the wrong port ID format for branches. Branch port IDs must be `branch-{caseId}` where `{caseId}` matches the `id` field inside the corresponding `inputs.branches` entry. A typo means the edge won't bind.
- Not setting `contentType` when sending a body. The default is `application/json`, but if you switch to XML or form-urlencoded and forget to update `contentType`, the server may reject the payload.
- Omitting `method` or `url`. Both are required fields with validation. `url` must match the pattern `^(.*\\.\\S.*|.*\\$vars.*)$`.
- Confusing `response` output with `error` output. On success, the `response` object contains `body`, `statusCode`, and `headers`. The `error` output is only populated on failure and has a different schema (`code`, `message`, `detail`, `category`, `status`).
- Forgetting that this node expands to a SubProcess at compile time. The BPMN model is `bpmn:ServiceTask` on the node instance, but the expansion template replaces it with a full SubProcess containing implicit start/end events, a SendTask, and conditional boundary error handling.
