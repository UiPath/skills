# Script Node — Implementation

## Node Type

`core.action.script`

## Registry validation

```bash
uip maestro flow registry get core.action.script --output json
```

Confirm: input port `input`, output port `success`, required input `script` (string, non-empty). See [Action Node Structure — Registry validation](../../../../shared/action-nodes.md#registry-validation) for the shared pattern.

## JSON structure

Follow the [Action Node Structure — Standard JSON skeleton](../../../../shared/action-nodes.md#standard-json-skeleton). The script-specific input is a single `script` string:

```json
{
  "inputs": {
    "script": "const items = $vars.fetchData.output.body.items;\nconst total = items.reduce((sum, i) => sum + i.amount, 0);\nreturn { total, count: items.length };"
  }
}
```

## Adding and editing

See [Action Node Structure — Adding and editing procedures](../../../../shared/action-nodes.md#adding-and-editing-procedures). The script node uses the standard input port `input` and output port `success`; no plugin-specific wiring.

## Script rules

1. **Must `return` an object** — `return { key: value }`, not a bare scalar. The return value becomes `$vars.{nodeId}.output`.
2. **`$vars` is a global** — use it directly: `return { upper: $vars.input1.toUpperCase() }`
3. **JavaScript ES2020 (Jint engine)** — see [variables-and-expressions.md](../../../../shared/variables-and-expressions.md) for supported features and Jint constraints.
4. **No `console.log`** — `console` is not available. Use `return { debug: value }` to inspect values.
5. **No external calls** — use the HTTP node or a connector node for API calls.
6. **30-second timeout** — long-running computations will be killed.

## Common patterns

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

### Reading a file-typed variable

A `file` variable (bound via `uip maestro flow debug --attachment <id>=<path>`) hydrates as an **object**, not a string. Read the uploaded file's name from `.FullName`:

```javascript
const doc = $vars.start.output.inputDoc; // file variable → object
return { fileName: doc.FullName };        // .FullName, not .name/.fileName
```

Property access is **case-sensitive** — these casings resolve: `.FullName`, `.ID` (uppercase, not `.Id`), `.MimeType`, `.Metadata.size` (nested, lowercase `size`). `.name` / `.fileName` do not exist. See [variables-and-expressions.md — Runtime shape of a `file` variable](../../../../shared/variables-and-expressions.md#file-input).

## Debug

| Error | Cause | Fix |
| --- | --- | --- |
| Script did not return a value | Missing `return` statement | Add `return { ... }` |
| Return value is not an object | Returned a scalar (`return 42`) | Wrap in object: `return { value: 42 }` |
| `$vars.nodeId` is undefined | Upstream node not connected or wrong ID | Check edges and node IDs |
| Timeout after 30s | Script too expensive | Simplify logic or split into multiple scripts |
| `console is not defined` | Used `console.log()` | Remove — use `return { debug: val }` instead |
| `fetch is not defined` | Tried to make HTTP call | Use an HTTP node or connector node instead |
