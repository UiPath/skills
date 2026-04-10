# Variables and Expressions

Complete reference for declaring variables, writing expressions, and managing data flow in `.flow` files.

> **Read this before** adding variables or writing expressions in any flow. Incorrect variable declarations cause silent runtime failures that validation does not catch.

---

## 1. Variable Directions

Every workflow variable has a **direction** that determines how it participates in the flow.

| Direction | Role | Readable | Writable | Use case |
|---|---|---|---|---|
| `in` | External input | Yes | No | Values passed when the flow is triggered or called |
| `out` | Workflow output | Yes | Mapped on End node | Values returned when the flow completes |
| `inout` | Internal state | Yes | Yes (via `variableUpdates`) | Counters, accumulators, flags shared across nodes |

**Constraints:**

- `in` variables cannot be modified during execution. They are fixed once the flow starts.
- `out` variables are assigned only on End nodes via output mappings.
- `inout` variables are the only direction that supports `variableUpdates`. Updating an `in` or `out` variable is invalid.
- `defaultValue` is only valid for `direction: "in"` and `direction: "inout"`.

---

## 2. WorkflowVariable Schema

Each entry in `variables.globals` conforms to this schema:

| Field | Type | Required | Notes |
|---|---|---|---|
| `id` | string | Required | Unique identifier, used in expressions as `$vars.<id>` |
| `direction` | `"in"` / `"out"` / `"inout"` | Required | Determines read/write behavior |
| `type` | string | Optional | `"string"` (default), `"number"`, `"boolean"`, `"object"`, `"array"`, `"file"` |
| `subType` | string | Optional | Item type for arrays (e.g., `"object"`, `"string"`) |
| `schema` | object | Optional | JSON Schema (draft-07) for complex types |
| `defaultValue` | any | Optional | Initial value (must match type). Valid for `in` and `inout` directions |
| `description` | string | Optional | Human-readable description |
| `triggerNodeId` | string | Optional | Trigger node this input is associated with (root flows only) |

---

## 3. Type Reference Table

| Type | Default Value | Notes |
|---|---|---|
| `string` | `""` | Default type if `type` is omitted |
| `number` | `0` | Integer or float |
| `boolean` | `false` | |
| `object` | `{}` | Use `schema` field for structured objects (JSON Schema draft-07) |
| `array` | `[]` | Use `subType` for typed arrays |
| `file` | `null` | Binary/file reference |

---

## 4. Concrete Variable Examples

### String input with default

```json
{
  "id": "customerName",
  "direction": "in",
  "type": "string",
  "defaultValue": "Unknown",
  "description": "Name of the customer to process"
}
```

### Number output

```json
{
  "id": "totalAmount",
  "direction": "out",
  "type": "number"
}
```

### Counter (inout state variable)

```json
{
  "id": "retryCount",
  "direction": "inout",
  "type": "number",
  "defaultValue": 0
}
```

### Object with JSON Schema

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

### Array with subType

```json
{
  "id": "emailList",
  "direction": "in",
  "type": "array",
  "subType": "string",
  "defaultValue": ["admin@example.com"]
}
```

### Input associated with a trigger

```json
{
  "id": "webhookPayload",
  "direction": "in",
  "type": "object",
  "triggerNodeId": "start"
}
```

---

## 5. Node Variables (`variables.nodes`)

Node variables represent outputs produced by nodes during execution. They are **read-only** and referenced via `$vars.<nodeId>.<outputId>`.

Every `.flow` file has a `variables` object containing three sections:

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
| `nodes` | Node output variables -- must be rebuilt after every node add/remove |
| `variableUpdates` | Per-node expressions that update state variables on node completion |

### Node Variable Schema

| Field | Type | Required | Notes |
|---|---|---|---|
| `id` | string | Required | Format: `<nodeId>.<outputId>` |
| `type` | string | Required | Output type (usually `"object"`) |
| `subType` | string | Optional | For complex types |
| `schema` | object | Optional | JSON Schema for structured outputs |
| `description` | string | Optional | What this output contains |
| `binding` | object | Required | `{ "nodeId": "<NODE_ID>", "outputId": "<OUTPUT_KEY>" }` |

### Regeneration Rule

Node variables must be regenerated from scratch after every node add or remove. Stale node variables produce a broken flow. For each node, check if the node instance has `outputs` defined; if not, fall back to the matching definition's `outputDefinition`. For each output key, emit a node variable entry with `id` set to `<nodeId>.<outputKey>`. Replace `workflow.variables.nodes` entirely with the new array.

### Example

A flow with an HTTP node (`fetchData`) producing both output and error node variables:

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

## 6. Variable Updates (`variableUpdates`)

Variable updates assign new values to `inout` (state) variables when a specific node completes. They are keyed by node ID.

### Schema

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

> Only `inout` variables can be updated. Updating an `in` or `out` variable is invalid.

> The `=js:` prefix is auto-added if missing when the runtime processes the expression, but always include it explicitly for clarity.

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

## 7. Expression Syntax

Flow uses a **Jint-based JavaScript engine** (ES2020 subset) for expressions. There are two expression formats.

### `=js:` Expressions

Used for conditions, input values, variable updates, and output mappings. The `=js:` prefix tells the engine to evaluate the rest as JavaScript. Return type can be any value (boolean, number, object, array, string).

```
=js:$vars.order.amount > 1000 && $vars.order.status === "approved"
```

### Template Expressions (`{ }`)

Used for string interpolation in text fields (such as prompts). Expressions inside single braces are evaluated and converted to strings. No prefix is needed -- braces appear inline.

```
Order {$vars.orderId} is {$vars.status} — total: {$vars.amount}
```

### Comparison

| Feature | `=js:` expression | `{ }` template |
|---|---|---|
| Return type | Any (boolean, number, object, array) | Always string |
| Use case | Conditions, inputs, mappings, variable updates | Text/prompt fields |
| Full JS | Yes | Expression-only (no statements) |
| Prefix | `=js:` required | No prefix, braces inline |

### Expression Contexts

Expressions behave differently depending on where they appear:

- **Script Node Body** (`inputs.script`): Contains a function body with full JavaScript statements. Must return an object. The returned object becomes `$vars.<nodeId>.output`. Returning a primitive (e.g., `return 42`) will fail -- use `return { value: 42 }`.
- **Decision Node** (`inputs.expression`): A single boolean expression. Result is coerced to `Boolean()`. Determines which port fires: `true` or `false`.
- **Switch Node** (`inputs.cases[].expression`): Each case has an expression evaluated in order. First truthy result wins; otherwise the `default` port fires.
- **HTTP Branch Condition** (`inputs.branches[].conditionExpression`): Uses `$self` to reference the current HTTP node's response.
- **Variable Update Expressions**: Evaluate to the new value for the target `inout` variable.
- **Loop Collection** (`inputs.collection`): Resolves to an array to iterate over. Inside the loop body, use `iterator.currentItem` and `iterator.currentIndex`.

---

## 8. Available Expression Globals

These variables are available in all expression contexts:

| Global | Description | Example |
|---|---|---|
| `$vars` | All workflow and node variables | `$vars.customerName`, `$vars.script1.output` |
| `$metadata` | Workflow metadata (instanceId, executionId) | `$metadata.instanceId` |
| `$self` | Current node's output (HTTP branch conditions only) | `$self.output.statusCode` |
| `iterator` | Loop iteration context (inside loops only) | `iterator.currentItem`, `iterator.currentIndex` |

### Loop Scope Details

Inside a loop body, you have access to:

- All parent-scope `$vars` (read-only from the loop's perspective)
- `iterator.currentItem` -- current array element
- `iterator.currentIndex` -- zero-based index
- `iterator.collection` -- the original array

After loop completion, `$vars.<loopId>.output` contains aggregated results from all iterations.

### Subflow Scope

Subflows have their own variable scope. Parent variables are **not** automatically visible inside a subflow. Pass values explicitly via subflow `inputs` and receive results via subflow `outputs`.

---

## 9. `$vars` Access Patterns

### Global Variables (inputs, outputs, state)

```javascript
// Workflow input variable
$vars.customerName

// State variable (inout)
$vars.counter
```

### Node Outputs

```javascript
// Script node output
$vars.script1.output
$vars.script1.output.someField

// HTTP node output
$vars.fetchData.output.body
$vars.fetchData.output.statusCode
$vars.fetchData.output.headers
```

### Nested Fields

```javascript
$vars.fetchData.output.body.items
$vars.fetchData.output.body.items[0].name
```

### Error Outputs

```javascript
$vars.fetchData.error.message
$vars.fetchData.error.code
```

### Node Output Availability

A node's output (`$vars.<nodeId>.output`) is available to **all downstream nodes** connected via edges. If a node has not executed (e.g., on an untaken branch), its `$vars` entry is `undefined`. Use optional chaining (`?.`) to guard against undefined node outputs.

---

## 10. Supported JavaScript Features

The runtime uses **Jint** (a .NET JavaScript interpreter, ES2020 subset).

| Category | Available |
|---|---|
| Arithmetic | `+`, `-`, `*`, `/`, `%` |
| Comparison | `===`, `!==`, `==`, `!=`, `>`, `<`, `>=`, `<=` |
| Logical | `&&`, `\|\|`, `!` |
| Ternary | `condition ? a : b` |
| Optional chaining | `?.` |
| Nullish coalescing | `??` |
| Template literals | `` `Hello ${name}` `` |
| Arrow functions | `items.filter(x => x.active)` (inline callbacks) |
| Destructuring | `const { a, b } = obj` (in script bodies) |
| Spread operator | `[...arr1, ...arr2]` (in script bodies) |
| String | `.toUpperCase()`, `.toLowerCase()`, `.trim()`, `.split()`, `.includes()`, `.startsWith()`, `.slice()`, `.substring()` |
| Array | `.filter()`, `.map()`, `.reduce()`, `.find()`, `.some()`, `.every()`, `.concat()`, `.length` |
| Object | `Object.keys()`, `Object.values()`, `Object.entries()` |
| Math | `Math.floor()`, `Math.ceil()`, `Math.round()`, `Math.abs()`, `Math.min()`, `Math.max()`, `Math.random()` |
| JSON | `JSON.parse()`, `JSON.stringify()` |
| Date | Limited -- prefer ISO 8601 strings |

---

## 11. Unsupported Features

The following are **not available** in the Jint expression engine:

- `async`/`await`, `Promise` -- no async operations
- Generators, `Proxy`, `WeakRef` -- advanced runtime features
- `fetch`, `XMLHttpRequest`, `setTimeout`, `setInterval` -- no network or timers
- `document`, `window`, `console` -- no DOM or browser globals
- `require`, `import` -- no module system
- `eval`, `Function` constructor -- no dynamic code generation

> **Keep expressions simple.** Complex data processing should go in Script nodes where you have full statement support, not in one-line expressions.

---

## 12. Output Mapping on End Nodes

Every `out` and `inout` variable **must** be mapped on every reachable End (`core.control.end`) node. Missing output mappings cause silent runtime failures.

Each key in the End node's `outputs` object must match the `id` of a global variable with `direction: "out"` or `"inout"`. The `source` field is a `=js:` expression that resolves to the value to return.

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

---

## 13. Common Expression Patterns

**Pass trigger input to a downstream node:**

```
=js:$vars.start.output.myField
```

**Chain node outputs:**

```
=js:$vars.scriptNode.output.result
```

**Conditional expression (ternary):**

```
=js:$vars.order.amount > 1000 ? "high" : "standard"
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

**Switch node with ordered cases:**

```json
{
  "inputs": {
    "cases": [
      { "label": "Low", "expression": "=js:$vars.score <= 30" },
      { "label": "Medium", "expression": "=js:$vars.score <= 70" },
      { "label": "High", "expression": "=js:$vars.score > 70" }
    ]
  }
}
```

**HTTP branch condition using `$self`:**

```
=js:$self.output.statusCode >= 200 && $self.output.statusCode < 300
```

**Loop collection with inline filter:**

```
=js:$vars.fetchData.output.body.items.filter(x => x.active)
```

**Append to an array in a variable update:**

```
=js:$vars.items.concat([$vars.newItem.output])
```

**Filter and transform in a script node:**

```javascript
const items = $vars.fetchData.output.body.items;
const active = items.filter(i => i.active);
return { count: active.length, names: active.map(i => i.name) };
```
