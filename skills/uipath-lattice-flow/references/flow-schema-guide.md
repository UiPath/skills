# .flow File Schema Reference

Complete schema for every entity type in a UiPath `.flow` JSON file. Use this when reading, creating, or modifying flow files programmatically.

---

## Workflow (Top-Level)

The root object of every `.flow` file.

| Field | Type | Required | Notes |
|---|---|---|---|
| `id` | string (identifier) | Required | Unique workflow ID (UUID or timestamp-based) |
| `version` | string (semver) | Required | e.g., `"1.0.0"` |
| `name` | string (min 1) | Required | Human-readable name |
| `description` | string | Optional | |
| `runtime` | `'maestro' \| 'api-function'` | Optional | Defaults to `'maestro'` |
| `nodes` | `NodeInstance[]` | Required | All workflow nodes |
| `edges` | `EdgeInstance[]` | Required | All connections |
| `definitions` | `NodeManifest[]` | Required | Cached node type definitions |
| `bindings` | `any[]` | Optional | UiPath artifact bindings |
| `variables` | `WorkflowVariables` | Optional | Workflow-level variables |
| `connection` | `WorkflowConnection` | Optional | Execution/debug connection |
| `metadata` | `Metadata` | Optional | Authoring metadata |
| `subflows` | `Record<string, SubflowEntry>` | Optional | Keyed by parent node ID |

---

## NodeInstance

A single node placed on the canvas.

| Field | Type | Required | Notes |
|---|---|---|---|
| `id` | string | Required | Unique node identifier |
| `type` | string | Required | e.g., `'core.action.script'` |
| `typeVersion` | string | Required | e.g., `'1.0.0'` |
| `display` | `{ label?, description? }` | Optional | Display overrides |
| `inputs` | `Record<string, unknown>` | Optional | Input field values |
| `outputs` | `Record<string, Record<string, unknown>>` | Optional | Output mappings |
| `model` | object | Optional | BPMN type, serviceType, bindings, context |
| `variableUpdates` | `Record<string, unknown>[]` | Optional | Variable assignments |
| `parentId` | string | Optional | ID of parent loop node |
| `ui` | `{ position: {x, y}, size?: {width, height} }` | Optional | Canvas position |

---

## EdgeInstance

A connection between two nodes.

| Field | Type | Required | Notes |
|---|---|---|---|
| `id` | string | Required | Unique edge identifier |
| `sourceNodeId` | string | Required | Source node ID |
| `sourcePort` | string | Required | Handle ID (defaults to `'default'`) |
| `targetNodeId` | string | Required | Target node ID |
| `targetPort` | string | Required | Handle ID (defaults to `'default'`) |
| `data` | `Record<string, string>` | Optional | e.g., `{ label: '...' }` |

---

## NodeManifest (Definition Entry)

Cached node type definition. Every node type referenced by a `NodeInstance.type` must have a matching entry in `definitions`.

| Field | Type | Required | Notes |
|---|---|---|---|
| `nodeType` | string | Required | Must match a node's `type` |
| `version` | string (min 1) | Required | |
| `category` | string | Optional | e.g., `'data-operations'` |
| `display` | `{ label: string }` | Optional | |
| `handleConfiguration` | `Array<{ handles: HandleConfig[] }>` | Required | Port definitions |
| `inputDefinition` | `Record<string, unknown>` | Optional | JSON Schema for inputs |
| `inputDefaults` | `Record<string, unknown>` | Optional | Default input values |
| `outputDefinition` | `Record<string, unknown>` | Optional | Output schemas |
| `tags` | `string[]` | Optional | |
| `sortOrder` | number | Optional | |
| `form` | object | Optional | Properties panel layout |
| `model` | `{ type, serviceType?, expansion?, ... }` | Optional | BPMN mapping |

---

## HandleConfig

Defines a port (input or output handle) on a node type.

| Field | Type | Required | Notes |
|---|---|---|---|
| `id` | string | Required | e.g., `'input'`, `'success'`, `'true'` |
| `type` | `'target' \| 'source'` | Required | |
| `handleType` | string | Required | |
| `label` | string | Optional | Supports templates: `{inputs.trueLabel \|\| 'True'}` |
| `repeat` | string | Optional | Dynamic handles: `"inputs.branches"` |
| `constraints` | `ConnectionConstraint` | Optional | Connection validation |

---

## ConnectionConstraint

Validation rules for connections to/from a handle.

| Field | Type | Required | Notes |
|---|---|---|---|
| `minConnections` | number | Optional | |
| `maxConnections` | number | Optional | |
| `forbiddenSources` | `HandleTarget[]` | Optional | |
| `forbiddenTargets` | `HandleTarget[]` | Optional | |
| `forbiddenTargetCategories` | `string[]` | Optional | |
| `allowedTargetCategories` | `string[]` | Optional | |
| `customValidation` | string | Optional | Template expression |
| `validationMessage` | string | Optional | |

---

## WorkflowVariables

Container for all variable scopes in a workflow or subflow.

| Field | Type | Required | Notes |
|---|---|---|---|
| `globals` | `WorkflowVariable[]` | Optional | Workflow inputs/outputs |
| `nodes` | `NodeVariable[]` | Optional | Node output capture |
| `variableUpdates` | `Record<string, VariableUpdate[]>` | Optional | Per-node assignments |

---

## WorkflowVariable (Global)

A workflow-level input, output, or bidirectional variable. Referenced in expressions as `$vars.{id}`.

| Field | Type | Required | Notes |
|---|---|---|---|
| `id` | string (min 1) | Required | Used as `$vars.{id}` |
| `direction` | `'in' \| 'out' \| 'inout'` | Required | |
| `type` | string | Required | `'string'`, `'number'`, `'boolean'`, `'object'`, `'array'`, `'file'` |
| `subType` | string | Optional | Array item type |
| `schema` | `Record<string, unknown>` | Optional | JSON Schema for complex types |
| `defaultValue` | unknown | Optional | Only for `direction='in'` |
| `description` | string | Optional | |
| `triggerNodeId` | string | Optional | Root workflow `direction='in'` only |

---

## NodeVariable

Captures a node's output as a reusable variable.

| Field | Type | Required | Notes |
|---|---|---|---|
| `id` | string (min 1) | Required | Format: `<nodeId>.<outputKey>` |
| `type` | string | Required | Default: `'string'` |
| `subType` | string | Optional | |
| `schema` | `Record<string, unknown>` | Optional | |
| `description` | string | Optional | |
| `binding` | `ArgumentBinding` | Required | Source node output |

---

## ArgumentBinding

Links a node variable to the output port that produces its value.

| Field | Type | Required | Notes |
|---|---|---|---|
| `nodeId` | string | Required | Source node ID |
| `outputId` | string | Required | Output port ID |

---

## VariableUpdate

An assignment expression that updates a variable after a node executes.

| Field | Type | Required | Notes |
|---|---|---|---|
| `variableId` | string | Required | Target variable ID |
| `expression` | string | Required | e.g., `"=js:$vars.counter + 1"` |

---

## SubflowEntry

A nested flow scope owned by a parent node (e.g., loop body, conditional branch).

| Field | Type | Required | Notes |
|---|---|---|---|
| `nodes` | `NodeInstance[]` | Required | Child nodes |
| `edges` | `EdgeInstance[]` | Required | Edges between child nodes |
| `variables` | `WorkflowVariables` | Optional | Subflow-scoped variables |

---

## WorkflowConnection

Execution/debug connection configuration.

| Field | Type | Required | Notes |
|---|---|---|---|
| `type` | `'cloud' \| 'local'` | Required | |
| `environment` | `'cloud' \| 'staging' \| 'alpha'` | Optional | Cloud only |
| `organizationId` | string | Optional | Cloud only |
| `tenantId` | string | Optional | Cloud only |
| `tenantName` | string | Optional | Cloud only |
| `localUrl` | string (URL) | Optional | Local only |

---

## Metadata

Authoring metadata attached to the workflow.

| Field | Type | Required | Notes |
|---|---|---|---|
| `createdAt` | string (ISO 8601) | Required | |
| `updatedAt` | string (ISO 8601) | Required | |
| `author` | string | Optional | |
| `tags` | `string[]` | Optional | |
| `description` | string | Optional | |

---

## Key Constants and Validation Rules

| Constant | Value | Usage |
|---|---|---|
| `VALID_IDENTIFIER_PATTERN` | `/^[a-zA-Z_][a-zA-Z0-9_]*$/` | Node/variable IDs |
| `RESERVED_WORDS` | JS/Python reserved words | Blocked as IDs |
| `BINDINGS_PATH_PREFIX` | `'=bindings.'` | Binding expressions |
| Expression prefix | `=js:` | All Jint expressions |
| Template syntax | `{{...}}` | Handle label templates |

---

## Minimal Example

A two-node flow with one edge. See `assets/templates/` for complete examples.

```json
{
  "id": "flow_1712345678",
  "version": "1.0.0",
  "name": "Two-Node Example",
  "runtime": "maestro",
  "nodes": [
    {
      "id": "node_start",
      "type": "core.control.start",
      "typeVersion": "1.0.0",
      "ui": { "position": { "x": 100, "y": 200 } }
    },
    {
      "id": "node_script",
      "type": "core.action.script",
      "typeVersion": "1.0.0",
      "inputs": {
        "code": "=js:console.log('hello')"
      },
      "ui": { "position": { "x": 400, "y": 200 } }
    }
  ],
  "edges": [
    {
      "id": "edge_1",
      "sourceNodeId": "node_start",
      "sourcePort": "default",
      "targetNodeId": "node_script",
      "targetPort": "default"
    }
  ],
  "definitions": [],
  "variables": {
    "globals": [],
    "nodes": []
  },
  "metadata": {
    "createdAt": "2025-01-15T10:00:00Z",
    "updatedAt": "2025-01-15T10:00:00Z"
  }
}
```
