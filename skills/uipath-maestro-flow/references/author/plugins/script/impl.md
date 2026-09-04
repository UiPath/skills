# Script Node — Implementation

## Node Type

`core.action.script`

## Registry validation

```bash
uip maestro flow registry get core.action.script --output json
```

Confirm: input port `input`, output port `success`, required input `script` (string, non-empty). See [Action Node Structure — Registry validation](../../../shared/action-nodes.md#registry-validation) for the shared pattern.

## JSON structure

Follow the [Action Node Structure — Standard JSON skeleton](../../../shared/action-nodes.md#standard-json-skeleton). The script-specific input is a single `script` string:

```json
{
  "inputs": {
    "script": "const items = $vars.fetchData.output.body.items;\nconst total = items.reduce((sum, i) => sum + i.amount, 0);\nreturn { total, count: items.length };"
  }
}
```

## Adding and editing

See [Action Node Structure — Adding and editing procedures](../../../shared/action-nodes.md#adding-and-editing-procedures). The script node uses the standard input port `input` and output port `success`; no plugin-specific wiring.

## Script rules

1. **Top-level body — no `function main()` wrapper.** Node runs the `script` text directly (as a function body); a wrapper is never called → `output` null. Read workflow variables via `$vars.<variableId>` and upstream node outputs via `$vars.<nodeId>.output`; end with top-level `return {…}`. Not a coded Function: no `main`, no injected args.
   - Correct: `const n = $vars.ixp1.output.field; return { n };`
   - Wrong: `function main({ ixp1 }) { … }`
2. **Must `return` an object** — `return { key: value }`, not a bare scalar. The return value becomes `$vars.<nodeId>.output`.
3. **`$vars` is a global** — use it directly: `return { upper: $vars.customerName.toUpperCase() }`
4. **JavaScript ES2020 (Jint engine)** — see [variables-and-expressions.md](../../../shared/variables-and-expressions.md) for supported features and Jint constraints.
5. **No `console.log`** — `console` is not available. Use `return { debug: value }` to inspect values.
6. **No external calls** — use the HTTP node or a connector node for API calls.
7. **30-second timeout** — long-running computations will be killed.
8. **Never name a variable `aggregate`** — reserved host global. On any `Identifier 'X' has already been declared`, rename `X`.
9. **Run the body against the real upstream payload before shipping it.** Any script that indexes, slices, splits, or maps is one off-by-one away from a fault that `flow validate` cannot see and a syntax check passes. You already have the payload: the `uip is resources run` / `registry get` call that told you the field names is the same shape `$vars.<nodeId>.output` carries at runtime. Feed it to the body.

   ```bash
   # $vars is a global at runtime; supply it as the one parameter to test.
   node -e '
     const payload = require("/tmp/upstream.json");                    # the real response, not a hand-written stub
     const body    = require("fs").readFileSync("/tmp/script.js", "utf8");
     console.log(new Function("$vars", body)({ myNode: { output: payload } }));
   '
   ```

   A hand-written stub tests the script against what you assumed the field held, which is the thing being checked. `"700 Bellevue Way NE, Suite 2000, Bellevue, WA 98004".split(",")[length - 3]` is `"Suite 2000"`, not the city — correct-looking, syntactically fine, and a runtime fault two nodes later when the lookup it feeds finds nothing.

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

Property access is **case-sensitive** — these casings resolve: `.FullName`, `.ID` (uppercase, not `.Id`), `.MimeType`, `.Metadata.size` (nested, lowercase `size`). `.name` / `.fileName` do not exist. See [variables-and-expressions.md — Runtime shape of a `file` variable](../../../shared/variables-and-expressions.md#file-input).

## Debug

| Error | Cause | Fix |
| --- | --- | --- |
| Script did not return a value | Missing `return` statement | Add `return { ... }` |
| `output` is `null` but script has a `return` | `return` is inside an uncalled `function main(){}` wrapper | Remove wrapper; code + `return` at top level (rule 1) |
| Return value is not an object | Returned a scalar (`return 42`) | Wrap in object: `return { value: 42 }` |
| `$vars.nodeId` is undefined | Upstream node not connected or wrong ID | Check edges and node IDs |
| Timeout after 30s | Script too expensive | Simplify logic or split into multiple scripts |
| `[300501] Error invoking script task` with **no** `Unexpected token` | Logic, not syntax: an index, key, or guard that is wrong for the real payload. The script parses, runs, and throws — or returns a value that faults a downstream node | Run the body against the real upstream response (rule 9), not a stub |
| `console is not defined` | Used `console.log()` | Remove — use `return { debug: val }` instead |
| `fetch is not defined` | Tried to make HTTP call | Use an HTTP node or connector node instead |
| `[300501] Error invoking script task` with `Unexpected token` | Malformed JavaScript — `flow validate` does not parse script bodies, so syntax errors surface only at runtime. Common slip: one missing `)` in chained `(((a \|\| {}).b \|\| {}).c \|\| [])` guards | Balance parentheses; check with `node -e "new Function(<script>)"` before validate |
| `Identifier 'X' has already been declared` | `X` collides with a runtime-injected global (known: `aggregate`) | Rename `X` (e.g. `agg`) |
