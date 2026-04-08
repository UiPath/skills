# Variables and Expressions

Complete reference for declaring variables, writing expressions, and managing data flow in `.flow` files via direct JSON authoring.

> **Read this before** adding variables or writing expressions in any flow. Incorrect variable declarations cause silent runtime failures that validation does not catch.

## Variables Overview

Every `.flow` file has a `variables` object at the workflow top level containing three sections:

```json
{
  "variables": {
    "globals": [],
    "nodes": [],
    "variableUpdates": {}
  }
}
```

| Section | Purpose |
|---|---|
| `globals` | Workflow-level variables: inputs, outputs, and internal state |
| `nodes` | Node output variables (auto-generated -- must be rebuilt after every node add/remove) |
| `variableUpdates` | Per-node expressions that update state variables on node completion |

---

## Workflow Variables (`globals`)

Workflow variables are declared in `variables.globals`. Each has a **direction** that determines its role.

### Directions

| Direction | Role | Readable | Writable | Use case |
|---|---|---|---|---|
| `in` | External input | Yes | No | Values passed when the flow is triggered or called |
| `out` | Workflow output | Yes | Mapped on End node | Values returned when the flow completes |
| `inout` | Internal state | Yes | Yes (via `variableUpdates`) | Counters, accumulators, flags shared across nodes |

### Schema

| Field | Type | Required | Notes |
|---|---|---|---|
| `id` | string | Required | Unique identifier, used in expressions as `$vars.<id>` |
| `direction` | `"in"` / `"out"` / `"inout"` | Required | |
| `type` | string | Optional | `"string"` (default), `"number"`, `"boolean"`, `"object"`, `"array"`, `"file"` |
| `subType` | string | Optional | Item type for arrays (e.g., `"object"`, `"string"`) |
| `schema` | object | Optional | JSON Schema (draft-07) for complex types |
| `defaultValue` | any | Optional | Initial value (must match type). Only valid for `direction: "in"` |
| `description` | string | Optional | Human-readable description |
| `triggerNodeId` | string | Optional | Trigger node this input is associated with (root flows only) |

### Examples

**String input with default:**

```json
{
  "id": "customerName",
  "direction": "in",
  "type": "string",
  "defaultValue": "Unknown",
  "description": "Name of the customer to process"
}
```

**Number output:**

```json
{
  "id": "totalAmount",
  "direction": "out",
  "type": "number"
}
```

**State variable (counter):**

```json
{
  "id": "retryCount",
  "direction": "inout",
  "type": "number",
  "defaultValue": 0
}
```

**Object with JSON Schema:**

```json
{
  "id": "orderData",
  "direction": "in",
  "type": "object",
  "schema": {
    "$schema": "http://json-schema.org/draft-07/schema#",
    "type": "object",
    "required": ["orderId", "amount"],
    "properties": {
      "orderId": { "type": "string" },
      "amount": { "type": "number" },
      "items": {
        "type": "array",
        "items": { "type": "object" }
      }
    },
    "additionalProperties": false
  }
}
```

**Array with subType:**

```json
{
  "id": "emailList",
  "direction": "in",
  "type": "array",
  "subType": "string",
  "defaultValue": ["admin@example.com"]
}
```

**Input associated with a trigger:**

```json
{
  "id": "webhookPayload",
  "direction": "in",
  "type": "object",
  "triggerNodeId": "start"
}
```

### Type Reference

| Type | Default Value | Notes |
|---|---|---|
| `string` | `""` | Default type if omitted |
| `number` | `0` | Integer or float |
| `boolean` | `false` | |
| `object` | `{}` | Use `schema` for structured objects |
| `array` | `[]` | Use `subType` for typed arrays |
| `file` | `null` | Binary/file reference |

---

## Node Variables (`nodes`)

Node variables represent outputs produced by nodes during execution. They are read-only and referenced via `$vars.<nodeId>.<outputId>`.

> **Node variables are auto-generated.** You MUST rebuild `variables.nodes` from scratch after every node add or remove. Stale node variables produce a broken flow that will not run.

### Schema

| Field | Type | Required | Notes |
|---|---|---|---|
| `id` | string | Required | Format: `<nodeId>.<outputId>` |
| `type` | string | Required | Output type (usually `"object"`) |
| `subType` | string | Optional | For complex types |
| `schema` | object | Optional | JSON Schema for structured outputs |
| `description` | string | Optional | What this output contains |
| `binding` | object | Required | `{ "nodeId": "<NODE_ID>", "outputId": "<OUTPUT_KEY>" }` |

### Regeneration Algorithm

After every node add or remove, regenerate `variables.nodes` completely. See [project-scaffolding-guide.md](project-scaffolding-guide.md) Section 3 for the full algorithm. Summary:

1. For each node in `workflow.nodes`, check if the node instance has `outputs` defined. If not, fall back to the matching definition's `outputDefinition`.
2. For each output key, emit a node variable entry with `id` set to `<nodeId>.<outputKey>`.
3. Replace `workflow.variables.nodes` entirely with the new array.

### Example

A flow with a manual trigger (`start`) and a script node (`myScript`):

```json
{
  "variables": {
    "nodes": [
      {
        "id": "start.output",
        "type": "object",
        "description": "Trigger output",
        "binding": { "nodeId": "start", "outputId": "output" }
      },
      {
        "id": "myScript.output",
        "type": "object",
        "description": "Script result",
        "binding": { "nodeId": "myScript", "outputId": "output" }
      },
      {
        "id": "myScript.error",
        "type": "object",
        "description": "Error output",
        "binding": { "nodeId": "myScript", "outputId": "error" }
      }
    ]
  }
}
```

---

## Variable Updates (`variableUpdates`)

Variable updates assign new values to `inout` (state) variables when a specific node completes. They are keyed by node ID.

### Schema

The `variableUpdates` object maps each node ID to an array of update entries:

```json
{
  "variableUpdates": {
    "<nodeId>": [
      {
        "variableId": "<inout_variable_id>",
        "expression": "=js:<expression>"
      }
    ]
  }
}
```

| Field | Type | Required | Notes |
|---|---|---|---|
| `variableId` | string | Required | ID of the `inout` variable to update |
| `expression` | string | Required | `=js:` expression that evaluates to the new value |

> **Only `inout` variables can be updated.** Updating an `in` or `out` variable is invalid.

> The `=js:` prefix is auto-added if missing when the runtime processes the expression, but always include it explicitly for clarity and to pass validation.

### Example

```json
{
  "variables": {
    "globals": [
      {
        "id": "counter",
        "direction": "inout",
        "type": "number",
        "defaultValue": 0
      },
      {
        "id": "lastStatus",
        "direction": "inout",
        "type": "string",
        "defaultValue": "pending"
      }
    ],
    "variableUpdates": {
      "processItem": [
        {
          "variableId": "counter",
          "expression": "=js:$vars.counter + 1"
        },
        {
          "variableId": "lastStatus",
          "expression": "=js:$vars.processItem.output.status"
        }
      ]
    }
  }
}
```

---

## Expression Syntax

All expressions in `.flow` files use the `=js:` prefix. The runtime evaluates the rest as JavaScript using a **Jint-based engine** (ES2020 subset).

### Access Patterns

| Pattern | What it accesses | Example |
|---|---|---|
| `$vars.<variableId>` | Global variable (input, output, or state) | `$vars.customerName` |
| `$vars.<nodeId>.<outputId>` | Node output variable | `$vars.script1.output` |
| `$vars.<nodeId>.<outputId>.<field>` | Nested field on node output | `$vars.fetchData.output.body.items` |
| `$vars.<nodeId>.error` | Node error output | `$vars.fetchData.error.message` |

### Additional Globals

| Global | Description | Example |
|---|---|---|
| `$metadata` | Workflow metadata (instanceId, executionId) | `$metadata.instanceId` |
| `$self` | Current node's output (HTTP branch conditions only) | `$self.output.statusCode` |
| `iterator` | Loop iteration context (inside loops only) | `iterator.currentItem`, `iterator.currentIndex` |

### Supported

Arithmetic, comparison, logical, ternary, optional chaining (`?.`), nullish coalescing (`??`), template literals, arrow functions, destructuring (in script bodies), spread operator (in script bodies).

| Category | Available |
|---|---|
| String | `.toUpperCase()`, `.toLowerCase()`, `.trim()`, `.split()`, `.includes()`, `.startsWith()`, `.slice()` |
| Array | `.filter()`, `.map()`, `.reduce()`, `.find()`, `.some()`, `.every()`, `.concat()`, `.length` |
| Object | `Object.keys()`, `Object.values()`, `Object.entries()` |
| Math | `Math.floor()`, `Math.ceil()`, `Math.round()`, `Math.abs()`, `Math.min()`, `Math.max()` |
| JSON | `JSON.parse()`, `JSON.stringify()` |
| Date | Limited -- prefer ISO 8601 strings |

### NOT Supported

`async`/`await`, generators, `Proxy`, `WeakRef`, `import`/`require`, `fetch`, `setTimeout`, `document`, `window`, `console`, `eval`, `Function` constructor.

> **Keep expressions simple.** Put complex data processing in Script nodes where you have full statement support, not in one-line expressions.

---

## Output Mapping on End Nodes

Every `out` and `inout` variable MUST be mapped on every reachable End (`core.control.end`) node. The mapping goes in the End node's `outputs` field.

> **Missing output mappings cause silent runtime failures.** This is one of the most common flow authoring errors. Always check validation item 11 in [validation-checklist.md](validation-checklist.md).

### Example

```json
{
  "id": "end1",
  "type": "core.control.end",
  "typeVersion": "1.0.0",
  "inputs": {},
  "outputs": {
    "totalAmount": {
      "source": "=js:$vars.calculateTotal.output.amount"
    },
    "summary": {
      "source": "=js:$vars.formatResult.output.text"
    }
  },
  "model": { "type": "bpmn:EndEvent" }
}
```

Each key in `outputs` must match the `id` of a global variable with `direction: "out"` or `"inout"`. The `source` field is a `=js:` expression that resolves to the value to return.

---

## Common Patterns

**Pass trigger input to a script:**

```
=js:$vars.start.output.myField
```

**Chain node outputs:**

```
=js:$vars.scriptNode.output.result
```

**Accumulate in a loop** (variableUpdate incrementing a counter):

```json
{
  "variableUpdates": {
    "processItem": [
      {
        "variableId": "processedCount",
        "expression": "=js:$vars.processedCount + 1"
      }
    ]
  }
}
```

**Conditional expression** (ternary in a decision node input):

```
=js:$vars.order.amount > 1000 ? "high" : "standard"
```

**Build an object from multiple node outputs** (End node output mapping):

```json
{
  "outputs": {
    "result": {
      "source": "=js:({ status: $vars.lastStatus, count: $vars.processedCount, data: $vars.transform1.output })"
    }
  }
}
```

**Filter and transform in a script node:**

```javascript
const items = $vars.fetchData.output.body.items;
const active = items.filter(i => i.active);
return { count: active.length, names: active.map(i => i.name) };
```
