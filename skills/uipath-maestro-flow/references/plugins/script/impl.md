# Script Node — Implementation

## Node Type

`core.action.script`

## Registry Validation

```bash
uip flow registry get core.action.script --output json
```

Confirm: input port `input`, output port `success`, required input `script` (string, non-empty).

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
  "model": { "type": "bpmn:ScriptTask" }
}
```

## Adding via CLI

```bash
uip flow node add <ProjectName>.flow core.action.script --output json \
  --input '{"script": "return { result: $vars.input1.toUpperCase() };"}' \
  --label "Process Data" \
  --position 300,200
```

> **Shell quoting tip:** If `--input` JSON contains special characters (quotes, braces, `$vars`), write the JSON to a temp file and pass it: `uip flow node add <file> core.action.script --input "$(cat /tmp/input.json)" --output json`

## Script Rules

1. **Must `return` an object** — `return { key: value }`, not a bare scalar. The return value becomes `$vars.{nodeId}.output`.
2. **`$vars` is a global** — use it directly: `return { upper: $vars.input1.toUpperCase() }`
3. **JavaScript ES2020 (Jint engine)** — see [variables-and-expressions.md](../../variables-and-expressions.md) for supported features and Jint constraints
4. **No `console.log`** — `console` is not available. Use `return { debug: value }` to inspect values.
5. **No external calls** — use HTTP node or connector nodes for API calls
6. **30-second timeout** — long-running computations will be killed

## Common Patterns

### Transform and return

```javascript
const items = $vars.fetchData.output.body.items;
const filtered = items.filter(i => i.status === "active");
return { items: filtered, count: filtered.length };
```

### Build a payload for a downstream node

```javascript
return {
  subject: `Order ${$vars.orderId} - Confirmation`,
  body: `Your order of ${$vars.orderTotal} has been processed.`,
  recipient: $vars.customerEmail
};
```

### Error check from upstream

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
