# Variables and Expressions

Complete reference for declaring variables, writing expressions, and managing data flow in `.flow` files.

> **Read this before** adding variables or writing expressions in any flow. Incorrect variable declarations cause silent runtime failures that `flow validate` does not catch.

---

## Variables Overview

Every flow has a `variables` object at the top level of the `.flow` file. It contains three sections:

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
| --- | --- |
| `globals` | Workflow-level variables: inputs, outputs, and state |
| `nodes` | Node output variables (auto-generated when using CLI `node add`) |
| `variableUpdates` | Per-node expressions that update state variables |

---

## Workflow Variables (`globals`)

Workflow variables are declared in `variables.globals`. Each has a **direction** that determines its role.

### Directions

| Direction | Role | Readable | Writable | Use case |
| --- | --- | --- | --- | --- |
| `in` | External input | Yes | No | Values passed when the flow is triggered or called |
| `out` | Workflow output | Yes | Mapped on End node | Values returned when the flow completes |
| `inout` | Internal state | Yes | Yes (via `variableUpdates`) | Counters, accumulators, flags shared across nodes |

### Schema

```typescript
{
  id: string              // Unique identifier, used in expressions as $vars.{id}
  direction: "in" | "out" | "inout"
  type?: string           // "string" (default), "number", "boolean", "object", "array"
  subType?: string        // Item type for arrays (e.g., "object", "string")
  schema?: object         // JSON Schema (draft-07) for complex types
  defaultValue?: unknown  // Initial value (must match type)
  description?: string    // Human-readable description
  triggerNodeId?: string  // Trigger node this input is associated with (works in both root flows and subflows)
}
```

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
| --- | --- | --- |
| `string` | `""` | Default type if omitted |
| `number` | `0` | Integer or float |
| `boolean` | `false` | |
| `object` | `{}` | Use `schema` for structured objects |
| `array` | `[]` | Use `subType` for typed arrays |

---

## Node Variables (`nodes`)

Node variables represent outputs produced by nodes during execution. They are read-only and referenced via `$vars.{nodeId}.{outputId}`.

When you add a node via `uip flow node add`, node variables are created automatically. When editing JSON directly, add them manually.

### Schema

```typescript
{
  id: string              // Format: "{nodeId}.{outputId}"
  type?: string           // Output type
  subType?: string        // For complex types
  schema?: object         // JSON Schema for structured outputs
  description?: string    // What this output contains
  binding: {
    nodeId: string        // Source node ID
    outputId: string      // Output port ID (e.g., "output", "error")
  }
}
```

### Example

```json
{
  "variables": {
    "nodes": [
      {
        "id": "fetchData.output",
        "type": "object",
        "description": "HTTP response body",
        "binding": {
          "nodeId": "fetchData",
          "outputId": "output"
        }
      },
      {
        "id": "fetchData.error",
        "type": "object",
        "description": "Error details if the request fails",
        "schema": {
          "$schema": "http://json-schema.org/draft-07/schema#",
          "type": "object",
          "required": ["code", "message"],
          "properties": {
            "code": { "type": "string" },
            "message": { "type": "string" },
            "detail": { "type": "string" },
            "category": { "type": "string" },
            "status": { "type": "integer" }
          }
        },
        "binding": {
          "nodeId": "fetchData",
          "outputId": "error"
        }
      }
    ]
  }
}
```

---

## Variable Updates (`variableUpdates`)

Variable updates assign new values to `inout` (state) variables at specific nodes. They execute when the node completes.

### Schema

```typescript
{
  "variableUpdates": {
    "{nodeId}": [
      {
        "variableId": string,    // ID of the inout variable to update
        "expression": string     // =js: expression to evaluate and assign
      }
    ]
  }
}
```

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

> **Only `inout` variables can be updated.** Updating an `in` or `out` variable is invalid.

> **Inside loops:** variableUpdate expressions cannot access loop iteration variables like `$vars.<loopId>.currentItem`. Those are only available inside the body node's script. The variableUpdate must reference the body node's output (e.g., `=js:$vars.bodyNode.output`).

---

## Output Mapping on End Nodes

Workflow output variables (`direction: "out"`) must be mapped on End nodes. The End node's `outputs` object maps each output variable ID to a source expression.

### Structure

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

> **Every `out` variable must have a mapping on every End node** that the flow can reach. Missing mappings cause runtime errors.

---

## Expression System

Flow uses a **Jint-based JavaScript engine** (ES2020 subset) for expressions. There are two expression formats.

### `=js:` Expressions (Full JavaScript)

Used for conditions, input values, variable updates, and output mappings. The `=js:` prefix tells the engine to evaluate the rest as JavaScript.

```
=js:$vars.order.amount > 1000 && $vars.order.status === "approved"
```

### Template Expressions (`{ }`)

Used for string interpolation in text fields. Expressions inside single braces are evaluated and converted to strings.

```
Order {$vars.orderId} is {$vars.status} — total: {$vars.amount}
```

### Comparison

| Feature | `=js:` | `{ }` template |
| --- | --- | --- |
| Return type | Any (boolean, number, object, array) | Always string |
| Use case | Conditions, inputs, mappings | Text/prompt fields |
| Full JS | Yes | Expression-only (no statements) |
| Prefix | `=js:` required | No prefix, braces inline |

---

## Available Globals

These variables are available in all expression contexts:

| Global | Description | Access pattern |
| --- | --- | --- |
| `$vars` | All workflow and node variables | `$vars.{variableId}` or `$vars.{nodeId}.{outputId}` |
| `$metadata` | Workflow metadata (instanceId, executionId) | `$metadata.instanceId` |
| `$self` | Current node's output (HTTP branch conditions only) | `$self.output.statusCode` |
| `$vars.<loopId>.*` | Loop iteration context (inside loops only) | `$vars.loop1.currentItem`, `$vars.loop1.currentIndex` |

### `$vars` Access Patterns

```javascript
// Workflow input variable
$vars.customerName

// State variable
$vars.counter

// Node output (script node)
$vars.script1.output
$vars.script1.output.someField

// Node output (HTTP node)
$vars.fetchData.output.body
$vars.fetchData.output.statusCode
$vars.fetchData.output.headers

// Node error
$vars.fetchData.error.message
$vars.fetchData.error.code
```

---

## Expression Contexts

Expressions behave differently depending on where they appear.

### Script Node Body

The `inputs.script` field contains a function body. Full JavaScript statements are allowed (variables, loops, conditionals). The returned value becomes `$vars.{nodeId}.output`.

Scripts can return any value — objects, numbers, strings, arrays, or booleans:

```javascript
// Returning an object (multiple fields)
const items = $vars.fetchData.output.body.items;
const filtered = items.filter(i => i.active);
return { count: filtered.length, names: filtered.map(i => i.name) };

// Returning a bare value (useful for accumulators in loops)
return $vars.total + $vars.loop1.currentItem;
```

### Decision Node (`inputs.expression`)

A single boolean expression. Result is coerced to `Boolean()`.

```
=js:$vars.order.amount > 1000 && $vars.order.verified === true
```

Determines which port fires: `true` or `false`.

### Switch Node (`inputs.cases[].expression`)

Each case has an expression evaluated in order. First truthy result wins; otherwise the `default` port fires.

```json
{
  "inputs": {
    "cases": [
      { "label": "Low", "expression": "$vars.score <= 30" },
      { "label": "Medium", "expression": "$vars.score <= 70" },
      { "label": "High", "expression": "$vars.score > 70" }
    ]
  }
}
```

### HTTP Branch Condition (`inputs.branches[].conditionExpression`)

Uses `$self` to reference the current HTTP node's response.

```
$self.output.statusCode >= 200 && $self.output.statusCode < 300
```

### Variable Update Expressions

Evaluate to the new value for the target variable.

```
=js:$vars.counter + 1
=js:$vars.items.concat([$vars.newItem.output])
```

### Loop Collection Expression

The `inputs.collection` field on a Loop node resolves to an array to iterate over.

```
=js:$vars.fetchData.output.body.items
=js:$vars.inputArray.filter(x => x.active)
```

Inside the loop body, use `$vars.<loopId>.currentItem` and `$vars.<loopId>.currentIndex` (e.g., `$vars.loop1.currentItem`).

---

## Jint Engine Constraints

The production runtime uses **Jint** (a .NET JavaScript interpreter, ES2020 subset). Key constraints:

### Supported

- Arithmetic: `+`, `-`, `*`, `/`, `%`
- Comparison: `===`, `!==`, `==`, `!=`, `>`, `<`, `>=`, `<=`
- Logical: `&&`, `||`, `!`
- Ternary: `condition ? a : b`
- String methods: `.toUpperCase()`, `.toLowerCase()`, `.trim()`, `.split()`, `.includes()`, `.startsWith()`, `.slice()`, `.substring()`
- Array methods: `.filter()`, `.map()`, `.reduce()`, `.find()`, `.some()`, `.every()`, `.concat()`, `.length`
- Object: `Object.keys()`, `Object.values()`, `Object.entries()`
- Math: `Math.floor()`, `Math.ceil()`, `Math.round()`, `Math.abs()`, `Math.min()`, `Math.max()`, `Math.random()`
- JSON: `JSON.parse()`, `JSON.stringify()`
- Template literals: `` `Hello ${name}` ``
- Destructuring: `const { a, b } = obj` (in script bodies)
- Spread operator: `[...arr1, ...arr2]` (in script bodies)
- Arrow functions: `items.filter(x => x.active)` (inline callbacks)

### Not Supported

- `fetch`, `XMLHttpRequest`, `setTimeout`, `setInterval` — no network or timers
- `document`, `window`, `console` — no DOM or browser globals
- `require`, `import` — no module system
- `eval`, `Function` constructor — no dynamic code generation
- `async`/`await`, `Promise` — no async operations
- `Date` constructor may have limited support — prefer ISO 8601 strings

> **When in doubt, keep expressions simple.** Complex data processing should go in Script nodes where you have full statement support, not in one-line expressions.

---

## Scoping Rules

### Node Output Availability

A node's output (`$vars.{nodeId}.output`) is available to **all downstream nodes** connected via edges. If a node has not executed (e.g., on an untaken branch), its `$vars` entry is `undefined`.

### Loop Scope

Inside a loop body, you have access to:
- All parent-scope `$vars` (read-only from loop's perspective)
- `$vars.<loopId>.currentItem` — current array element
- `$vars.<loopId>.currentIndex` — zero-based index
- `$vars.<loopId>.collection` — the original array

Where `<loopId>` is the loop node's `id` (e.g., `$vars.loop1.currentItem`).

> **Important:** Loop body nodes must have `"parentId": "<loopId>"` set in their JSON. Without this, the runtime does not know the node is inside the loop and `$vars.<loopId>.currentItem` will be undefined.

After loop completion, `$vars.<loopId>.output` contains aggregated results from all iterations.

### Subflow Scope

Subflows have their own variable scope. Parent variables are **not** automatically visible inside a subflow. Pass values explicitly via subflow `inputs` and receive results via subflow `outputs`.

---

## Variable Management via CLI

There are **no CLI commands** for adding or removing variables. Manage variables by editing the `.flow` JSON directly.

### Adding a workflow input variable

1. Open `<ProjectName>.flow`
2. Add the variable object to `variables.globals`
3. Run `uip flow validate` to check for errors

### Adding node variables after manual node insertion

When adding nodes via direct JSON edit (not CLI), you must also add corresponding entries to `variables.nodes`:

```json
{
  "id": "myScript.output",
  "type": "object",
  "binding": { "nodeId": "myScript", "outputId": "output" }
},
{
  "id": "myScript.error",
  "type": "object",
  "binding": { "nodeId": "myScript", "outputId": "error" }
}
```

> **When using `uip flow node add`**, node variables are handled automatically. Only add them manually when editing JSON directly.

### Mapping outputs on End nodes

For every `out` variable, add a mapping in each End node's `outputs`:

```json
"outputs": {
  "result": {
    "source": "=js:$vars.processData.output"
  }
}
```

---

## Complete Example

A flow with input, state, and output variables:

```json
{
  "variables": {
    "globals": [
      {
        "id": "inputItems",
        "direction": "in",
        "type": "array",
        "subType": "object",
        "defaultValue": [],
        "description": "Items to process"
      },
      {
        "id": "processedCount",
        "direction": "inout",
        "type": "number",
        "defaultValue": 0
      },
      {
        "id": "result",
        "direction": "out",
        "type": "object",
        "description": "Processing summary"
      }
    ],
    "nodes": [
      {
        "id": "transform1.output",
        "type": "object",
        "binding": { "nodeId": "transform1", "outputId": "output" }
      }
    ],
    "variableUpdates": {
      "transform1": [
        {
          "variableId": "processedCount",
          "expression": "=js:$vars.processedCount + $vars.transform1.output.count"
        }
      ]
    }
  },
  "nodes": [
    {
      "id": "start",
      "type": "core.trigger.manual",
      "typeVersion": "1.0.0",
      "inputs": {},
      "outputs": {
        "output": {
          "type": "object",
          "description": "The return value of the trigger.",
          "source": "=result.response",
          "var": "output"
        }
      },
      "model": { "type": "bpmn:StartEvent" }
    },
    {
      "id": "transform1",
      "type": "core.action.script",
      "typeVersion": "1.0.0",
      "inputs": {
        "script": "const items = $vars.inputItems.filter(i => i.active);\nreturn { count: items.length, items: items };"
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
          "source": "=result.Error",
          "var": "error"
        }
      },
      "model": { "type": "bpmn:ScriptTask" }
    },
    {
      "id": "end1",
      "type": "core.control.end",
      "typeVersion": "1.0.0",
      "inputs": {},
      "outputs": {
        "result": {
          "source": "=js:({ total: $vars.processedCount, data: $vars.transform1.output })"
        }
      },
      "model": { "type": "bpmn:EndEvent" }
    }
  ],
  "edges": [
    {
      "id": "e1",
      "sourceNodeId": "start",
      "sourcePort": "output",
      "targetNodeId": "transform1",
      "targetPort": "input"
    },
    {
      "id": "e2",
      "sourceNodeId": "transform1",
      "sourcePort": "success",
      "targetNodeId": "end1",
      "targetPort": "input"
    }
  ]
}
```
