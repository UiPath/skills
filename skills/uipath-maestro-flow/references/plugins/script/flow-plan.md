# Script Node

## Node Type

`core.action.script`

## When to Use

Use a Script node for custom logic, data transformation, computation, or formatting that does not require an external call.

### Selection Heuristics

| Situation | Use Script? |
| --- | --- |
| Custom logic, string manipulation, computation | Yes |
| Standard map/filter/group-by on a collection | No — use [Transform](../transform/flow-plan.md) |
| Ambiguous input that needs reasoning or judgment | No — use [Agent](../agent/flow-plan.md) |
| Calling an external API | No — use [HTTP](../http/flow-plan.md) or [Connector Activity](../connector/flow-plan.md) |
| Natural language generation | No — use [Agent](../agent/flow-plan.md) |

## Ports

| Input Port | Output Port(s) |
| --- | --- |
| `input` | `success`, `error` |

- `success` — primary output; fires when the script returns normally.
- `error` — implicit error port shared with all action nodes. Fires on uncaught script exceptions, returned non-object values, or timeout. See [Implicit error port on action nodes](../../flow-file-format.md#implicit-error-port-on-action-nodes).

## Output Variables

- `$vars.{nodeId}.output` — the return value (must be an object)
- `$vars.{nodeId}.error` — error object if the script fails

## Key Constraints

- JavaScript only (ES2020 via Jint) — not TypeScript, not Python
- Must `return` an object: `return { key: value }` (not a bare scalar)
- No browser/DOM APIs (`fetch`, `document`, `window`, `setTimeout` are unavailable)
- Cannot make HTTP calls or access external systems
- 30-second execution timeout
- `$vars` is available as a global

## Registry Validation

```bash
uip flow registry get core.action.script --output json
```

Confirm: input port `input`, output port `success`, required input `script` (string, non-empty).

## Adding / Editing

For step-by-step add, delete, and wiring procedures, see [flow-editing-operations.md](../../flow-editing-operations.md). Use the JSON structure below for the node-specific `inputs` and `model` fields.

## JSON Structure

```json
{
  "id": "processData",
  "type": "core.action.script",
  "typeVersion": "1.0.0",
  "display": { "label": "Process Data" },
  "inputs": {
    "script": "const items = $vars.fetchData.output.body.items;\nconst total = items.reduce((sum, i) => sum + i.amount, 0);\nreturn { total, count: items.length };"
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
}
```

## Script Rules

1. **Must `return` an object** — `return { key: value }`, not a bare scalar. The return value becomes `$vars.{nodeId}.output`.
2. **`$vars` is a global** — use it directly: `return { upper: $vars.input1.toUpperCase() }`
3. **JavaScript ES2020 (Jint engine)** — see [variables-and-expressions.md](../../variables-and-expressions.md) for supported features and Jint constraints
4. **No `console.log`** — `console` is not available. Use `return { debug: value }` to inspect values.
5. **No external calls** — use HTTP node or connector nodes for API calls
6. **30-second timeout** — long-running computations will be killed

## Accessing Output

### Common Patterns

#### Transform and return

```javascript
const items = $vars.fetchData.output.body.items;
const filtered = items.filter(i => i.status === "active");
return { items: filtered, count: filtered.length };
```

#### Build a payload for a downstream node

```javascript
return {
  subject: `Order ${$vars.orderId} - Confirmation`,
  body: `Your order of ${$vars.orderTotal} has been processed.`,
  recipient: $vars.customerEmail
};
```

#### Error check from upstream

```javascript
const error = $vars.httpCall.error;
if (error) {
  return { hasError: true, message: error.message };
}
return { hasError: false, data: $vars.httpCall.output.body };
```

## Debug

| Error | Cause | Fix |
| --- | --- | --- |
| Script did not return a value | Missing `return` statement | Add `return { ... }` |
| Return value is not an object | Returned a scalar (`return 42`) | Wrap in object: `return { value: 42 }` |
| `$vars.nodeId` is undefined | Upstream node not connected or wrong ID | Check edges and node IDs |
| Timeout after 30s | Script too expensive | Simplify logic or split into multiple scripts |
| `console is not defined` | Used `console.log()` | Remove — use `return { debug: val }` instead |
| `fetch is not defined` | Tried to make HTTP call | Use an HTTP node or connector node instead |
