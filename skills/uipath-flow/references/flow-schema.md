# .flow File Schema Reference

Complete schema for every entity type in a UiPath `.flow` JSON file. This is a format-only reference -- no CLI commands or authoring workflow instructions.

---

## 1. Top-Level Workflow Fields

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
| `connection` | `WorkflowConnection` | Optional | Execution/debug connection config (`type`, `environment`, org/tenant IDs, `localUrl`) |
| `metadata` | `Metadata` | Optional | Authoring metadata |
| `subflows` | `Record<string, SubflowEntry>` | Optional | Keyed by parent node ID |

---

## 2. NodeInstance

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
| `ui` | object | Required | Canvas layout (see below) |

### `ui` object

| Field | Type | Required | Notes |
|---|---|---|---|
| `position` | `{ x: number, y: number }` | Required | Canvas coordinates |
| `size` | `{ width: number, height: number }` | Optional | Node dimensions |
| `collapsed` | boolean | Optional | Whether the node panel is collapsed |

---

## 3. EdgeInstance

A connection between two nodes.

| Field | Type | Required | Notes |
|---|---|---|---|
| `id` | string | Required | Unique edge identifier |
| `sourceNodeId` | string | Required | Source node ID |
| `sourcePort` | string | Required | Handle ID (e.g., `'output'`, `'success'`, `'true'`) |
| `targetNodeId` | string | Required | Target node ID |
| `targetPort` | string | Required | Handle ID (e.g., `'input'`, `'default'`) |
| `data` | `Record<string, string>` | Optional | e.g., `{ label: '...' }` |

All four node/port fields are required. Omitting any port field causes a validation error.

---

## 4. NodeManifest (Definition Entry)

Cached node type definition. Every node type referenced by a `NodeInstance.type` must have a matching entry in `definitions`. The array needs exactly one entry per unique `type` value -- not one per node instance. If two nodes share the same type, one definition covers both.

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

## 5. HandleConfiguration (Ports)

Defines a port (input or output handle) on a node type. These appear inside `NodeManifest.handleConfiguration[].handles[]`.

| Field | Type | Required | Notes |
|---|---|---|---|
| `id` | string | Required | e.g., `'input'`, `'success'`, `'true'` |
| `type` | `'target' \| 'source'` | Required | `target` = incoming, `source` = outgoing |
| `handleType` | string | Required | |
| `label` | string | Optional | Supports templates: `{inputs.trueLabel \|\| 'True'}` |
| `repeat` | string | Optional | Dynamic handles: `"inputs.branches"` |
| `constraints` | `ConnectionConstraint` | Optional | Connection validation rules |

---

## 6. ConnectionConstraints

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

## 7. WorkflowVariables

Container for all variable scopes in a workflow or subflow.

| Field | Type | Required | Notes |
|---|---|---|---|
| `globals` | `WorkflowVariable[]` | Optional | Workflow inputs/outputs (`direction`: `in`, `out`, `inout`). Referenced as `$vars.{id}` |
| `nodes` | `NodeVariable[]` | Optional | Captures a node's output as a reusable variable. ID format: `<nodeId>.<outputKey>` |
| `variableUpdates` | `Record<string, VariableUpdate[]>` | Optional | Per-node assignment expressions that update variables after execution |

Global variables support types: `string`, `number`, `boolean`, `object`, `array`, `file`. Node variables include an `ArgumentBinding` (`nodeId` + `outputId`) linking them to the source output port.

For the full variable schema (WorkflowVariable fields, NodeVariable fields, ArgumentBinding, VariableUpdate, direction semantics, and expression syntax), see [variables-guide.md](variables-guide.md).

---

## 8. SubflowEntry

A nested flow scope owned by a parent node (e.g., loop body, conditional branch). Stored in the top-level `subflows` object, keyed by the parent node's ID.

| Field | Type | Required | Notes |
|---|---|---|---|
| `nodes` | `NodeInstance[]` | Required | Child nodes |
| `edges` | `EdgeInstance[]` | Required | Edges between child nodes |
| `variables` | `WorkflowVariables` | Optional | Subflow-scoped variables |

For patterns on building subflows (loop bodies, branch scoping, variable inheritance), see [subflow-guide.md](subflow-guide.md).

---

## 9. Bindings

The `bindings` array at the top level holds UiPath artifact bindings that connect flow nodes to authenticated platform resources (connectors, queues, etc.). When a flow uses connector nodes, the runtime needs to know which authenticated connection to use for each connector instance.

For the full bindings schema, `bindings_v2.json` structure, and the connection-binding workflow, see [bindings-guide.md](bindings-guide.md).

---

## 10. Metadata

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

## Minimal Working Example

A two-node flow with one edge.

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
