# Loop Node — Implementation

## Node Type

`core.logic.loop`

## Registry Validation

```bash
uip maestro flow registry get core.logic.loop --output json
```

Confirm the handles, required input `collection`, and the `outputDefinition` keys. Set the node instance `typeVersion` to the `version` field from this response — do not hardcode it.

The loop is a **container** node, so its handles split across two boundaries:

| Boundary | Handle | Direction | Purpose |
| --- | --- | --- | --- |
| outer | `input` | target | Entry from upstream |
| outer | `success` | source | Exit after all iterations complete |
| outer | `error` | source | Error path (when `errorHandlingEnabled`) |
| inner | `start` | source | Into the loop body (first body node) |
| inner | `continue` | target | Return from last body node |
| inner | `break` | target | Early exit (when `breakEnabled`) |

> There is no `output` port and no `loopBack` port. `output` is an output **variable** (`$vars.<loopId>.output`), not a handle. Wiring either name is a hard `flow validate` error — `Edge references undeclared source handle "output" on node "<loopId>" … rewire to one of: success, error, start`.

## JSON Structure

### Loop node

```json
{
  "id": "loop1",
  "type": "core.logic.loop",
  "typeVersion": "<DEFINITION_VERSION>",
  "display": { "label": "Loop over items" },
  "inputs": {
    "collection": "=js:$vars.fetchData.output.body.items",
    "parallel": false
  }
}
```

> **Collection source shape depends on the node type.** Connector `list` activities return the bare array — `"collection": "=js:$vars.searchIssuesByJql1.output"`, NOT `.output.issues` / `.output.items`. HTTP nodes differ — envelope preserved: `.output.body.<key>` as above. See [connector/impl.md — Connector output shape](../connector/impl.md).

Set `"parallel": true` to execute all iterations concurrently.

### Loop body nodes — `parentId` required

Every node inside the loop body **must** have `"parentId"` set to the loop node's ID. Without this, the runtime does not know the node is part of the loop and variableUpdates will not fire per-iteration.

```json
{
  "id": "processItem",
  "type": "core.action.script",
  "typeVersion": "1.0",
  "display": { "label": "Process item" },
  "inputs": {
    "script": "return $vars.product * $vars.loop1.currentItem"
  },
  "parentId": "loop1"
}
```

> **Critical:** If you omit `parentId`, the node executes outside the loop context. State variables will not update across iterations and loop outputs like `currentItem` will be inaccessible.

## Adding / Editing

For step-by-step add, delete, and wiring procedures, see [editing-operations.md](../../editing-operations.md). Use the JSON structure above for the node-specific `inputs` and `parentId`.

### CLI carve-out nodes inside a loop

When adding a CLI carve-out node (connector, connector trigger, or managed HTTP) inside a loop, pass `--parent` to set `parentId` automatically:

```bash
uip maestro flow node add <FLOW_PATH> core.action.http.v2 --label "Fetch data" --parent <LOOP_ID> --output json
uip maestro flow node add <FLOW_PATH> <CONNECTOR_NODE_TYPE> --label "Get record" --parent <LOOP_ID> --output json
```

`--parent` validates the parent node exists and sets `parentId` on the new node. For non-carve-out node types (script, end, etc.), set `"parentId"` directly in the JSON — see the examples above.

## Wiring

Loop nodes have a specific wiring pattern — four edges:

| Edge | Source | Source port | Target | Target port |
| --- | --- | --- | --- | --- |
| Enter the loop | upstream node | `success` | `<loopId>` | `input` |
| Into the body | `<loopId>` | `start` | first body node | `input` |
| Back from the body | last body node | `success` | `<loopId>` | `continue` |
| Exit the loop | `<loopId>` | `success` | downstream node | `input` |

See [editing-operations.md](../../editing-operations.md) for edge add procedures.

## Accessing Loop Variables Inside Body

Inside the loop body, access the current item via `$vars.<loopId>.currentItem`:

```javascript
// In a Script node inside the loop body (parentId must be set to the loop node)
const item = $vars.loop1.currentItem;
const iteration = $vars.loop1.currentIteration;
return { processed: item.name.toUpperCase(), position: iteration };
```

| Variable | Description |
| --- | --- |
| `$vars.<loopId>.currentItem` | The item being processed in this iteration |
| `$vars.<loopId>.currentIteration` | 1-based iteration number |
| `$vars.<loopId>.collection` | The full collection being iterated |

> **Do not use `iterator.currentItem`.** The correct access pattern is `$vars.<loopId>.currentItem` where `<loopId>` is the loop node's `id` (e.g., `$vars.loop1.currentItem`).

> **There is no `currentIndex`.** The registry's `outputDefinition` for `core.logic.loop` exposes `currentIteration`, and it starts at 1 — not 0. Nothing rejects the wrong name: a `variables.nodes` entry bound to `outputId: "currentIndex"` passes `flow validate`, because bindings are not checked against the node's declared outputs. Confirm the output names with `uip maestro flow registry get core.logic.loop --output json`.

### Required node variables for loop outputs

For `$vars.<loopId>.currentItem` etc. to resolve, you must add corresponding entries to `variables.nodes`:

```json
{
  "variables": {
    "nodes": [
      {
        "id": "loop1.currentItem",
        "type": "any",
        "description": "The current item being iterated in the loop",
        "binding": { "nodeId": "loop1", "outputId": "currentItem" }
      },
      {
        "id": "loop1.currentIteration",
        "type": "number",
        "description": "The current iteration number (1-based)",
        "binding": { "nodeId": "loop1", "outputId": "currentIteration" }
      },
      {
        "id": "loop1.collection",
        "type": "array",
        "description": "The collection being iterated over",
        "binding": { "nodeId": "loop1", "outputId": "collection" }
      },
      {
        "id": "loop1.output",
        "type": "array",
        "description": "Aggregated results from all loop iterations",
        "binding": { "nodeId": "loop1", "outputId": "output" }
      }
    ]
  }
}
```

## Aggregated loop output (`$vars.<loopId>.output`)

After the loop completes, `$vars.<loopId>.output` is an array with **one entry per iteration**. Each entry is **keyed by body node id**, with that node's outputs nested underneath — it is NOT the body node's bare return value.

For a loop `multiplyNumbers` over `[13, 15, 17]` whose body node `multiplyCurrent` is a Script returning `{ number: <n> }`:

```json
[
  { "multiplyCurrent": { "output": { "number": 13 } } },
  { "multiplyCurrent": { "output": { "number": 15 } } },
  { "multiplyCurrent": { "output": { "number": 17 } } }
]
```

So a downstream Script reads a per-iteration value as `item.<bodyNodeId>.output.<field>`:

```javascript
// CORRECT
return { product: $vars.multiplyNumbers.output.reduce((p, item) => p * item.multiplyCurrent.output.number, 1) };

// WRONG — item.number is undefined; 1 * undefined === NaN
return { product: $vars.multiplyNumbers.output.reduce((p, item) => p * item.number, 1) };
```

With multiple body nodes, every node that ran in that iteration appears as a sibling key (`{ "fetchData1": { "output": … }, "processItem1": { "output": … } }`), alongside `<bodyNodeId>.error`.

> **`flow validate` cannot catch this.** The wrong accessor is valid JS over an `any`-typed array — it validates clean and silently produces `NaN`/`undefined` at runtime. Confirm the shape with one `uip maestro flow debug` run before wiring downstream consumers.

## State Accumulation with variableUpdates

To accumulate state across loop iterations (counters, running totals), use an `inout` variable with a `variableUpdate` on the body node:

```json
{
  "variables": {
    "globals": [
      {
        "id": "runningTotal",
        "direction": "inout",
        "type": "number",
        "defaultValue": 0
      }
    ],
    "variableUpdates": {
      "bodyNode": [
        {
          "variableId": "runningTotal",
          "expression": {
            "type": "jsExpression",
            "expression": "$vars.bodyNode.output",
            "fieldType": "number"
          }
        }
      ]
    }
  }
}
```

The variableUpdate fires after each iteration, so the `inout` variable carries the accumulated value into the next iteration.

> **`expression` is an object, not a `=js:` string.** `{ "type": "jsExpression", "expression": "<bare JS, no =js: prefix>", "fieldType": "<target variable's type>" }`. The legacy string form fails `flow validate` with `[MIGRATION] Workflow migration failed at 1.9→1.10 … Offending field(s): variables.variableUpdates.<nodeId>.0.expression` and `"Retry": "RetryWillNotFix"`. `uip maestro flow variable-update add` still emits the legacy string form — write the object form with `Edit` instead. See [shared/variables-and-expressions.md § Variable Updates](../../../../shared/variables-and-expressions.md#variable-updates-variableupdates).

> **Critical:** The variableUpdate expression **cannot** access loop iteration variables like `$vars.<loopId>.currentItem`. These are only available inside the body node's script. The variableUpdate must reference the body node's output (e.g., `$vars.bodyNode.output`). If you need to compute using `currentItem`, do the computation in the script and reference the script's output in the variableUpdate.

## Complete Example — Loop with State Accumulation

A flow that iterates over a collection, accumulates a result in an `inout` variable via a Script body node, and outputs the final value.

```json
{
  "nodes": [
    {
      "id": "start",
      "type": "core.trigger.manual",
      "typeVersion": "1.0",
      "display": { "label": "Manual trigger" },
      "inputs": { "entryPointId": "..." }
    },
    {
      "id": "loop1",
      "type": "core.logic.loop",
      "typeVersion": "<DEFINITION_VERSION>",
      "display": { "label": "Loop" },
      "inputs": { "collection": "=js:$vars.inputItems", "parallel": false }
    },
    {
      "id": "bodyScript",
      "type": "core.action.script",
      "typeVersion": "<DEFINITION_VERSION>",
      "display": { "label": "Process item" },
      "inputs": {
        "script": "return $vars.accumulator + $vars.loop1.currentItem;"
      },
      "parentId": "loop1"
    },
    {
      "id": "end1",
      "type": "core.control.end",
      "typeVersion": "1.0",
      "display": { "label": "End" },
      "inputs": {},
      "outputs": {
        "result": { "source": "=js:$vars.accumulator" }
      }
    }
  ],
  "edges": [
    { "id": "e1", "sourceNodeId": "start", "sourcePort": "output", "targetNodeId": "loop1", "targetPort": "input" },
    { "id": "e2", "sourceNodeId": "loop1", "sourcePort": "start", "targetNodeId": "bodyScript", "targetPort": "input" },
    { "id": "e3", "sourceNodeId": "bodyScript", "sourcePort": "success", "targetNodeId": "loop1", "targetPort": "continue" },
    { "id": "e4", "sourceNodeId": "loop1", "sourcePort": "success", "targetNodeId": "end1", "targetPort": "input" }
  ],
  "variables": {
    "globals": [
      { "id": "inputItems", "direction": "in", "type": "array", "defaultValue": [] },
      { "id": "accumulator", "direction": "inout", "type": "number", "defaultValue": 0 },
      { "id": "result", "direction": "out", "type": "number" }
    ],
    "nodes": [
      { "id": "loop1.currentItem", "type": "any", "binding": { "nodeId": "loop1", "outputId": "currentItem" } },
      { "id": "loop1.currentIteration", "type": "number", "binding": { "nodeId": "loop1", "outputId": "currentIteration" } },
      { "id": "loop1.collection", "type": "array", "binding": { "nodeId": "loop1", "outputId": "collection" } },
      { "id": "loop1.output", "type": "array", "binding": { "nodeId": "loop1", "outputId": "output" } },
      { "id": "bodyScript.output", "type": "object", "binding": { "nodeId": "bodyScript", "outputId": "output" } },
      { "id": "bodyScript.error", "type": "object", "binding": { "nodeId": "bodyScript", "outputId": "error" } }
    ],
    "variableUpdates": {
      "bodyScript": [
        {
          "variableId": "accumulator",
          "expression": {
            "type": "jsExpression",
            "expression": "$vars.bodyScript.output",
            "fieldType": "number"
          }
        }
      ]
    }
  }
}
```

Key points in this pattern:
- `bodyScript` has `"parentId": "loop1"` — places it inside the loop
- Script accesses `$vars.loop1.currentItem` for the current iteration value
- `variableUpdate` on `bodyScript` writes the script's return value back to `accumulator`, using the object `expression` form with `fieldType` matching `accumulator`'s declared `number` type
- `accumulator` is `inout` so it persists across iterations
- End node maps the final accumulated value to the `out` variable — also map `accumulator` itself, or `flow validate` warns `MISSING_OUTPUT_MAPPING` for the unmapped `inout` global
- Body edges use the loop's inner handles — `start` out, `continue` back — not `output`/`loopBack`

> **Prefer this pattern over post-processing `$vars.loop1.output`** when you need a running total. If you do consume the aggregate array instead, read each entry as `item.<bodyNodeId>.output.<field>` — see [Aggregated loop output](#aggregated-loop-output-varsloopidoutput).

## Complete Example — Multi-Node Loop Body (HTTP + Script)

Loop over items, fetch data per-iteration via HTTP, process with a script. Both body nodes have `parentId`.

```json
{
  "nodes": [
    {
      "id": "start",
      "type": "core.trigger.manual",
      "typeVersion": "1.0",
      "display": { "label": "Manual trigger" },
      "inputs": { "entryPointId": "..." }
    },
    {
      "id": "loop1",
      "type": "core.logic.loop",
      "typeVersion": "<DEFINITION_VERSION>",
      "display": { "label": "For each item" },
      "inputs": {
        "collection": "=js:[{ name: 'A', id: 1 }, { name: 'B', id: 2 }]",
        "parallel": false
      }
    },
    {
      "id": "fetchData1",
      "type": "core.action.http.v2",
      "typeVersion": "<DEFINITION_VERSION>",
      "display": { "label": "Fetch data" },
      "inputs": { "branches": [], "timeout": "PT15M", "retryCount": 0, "detail": {} },
      "parentId": "loop1"
    },
    {
      "id": "processItem1",
      "type": "core.action.script",
      "typeVersion": "<DEFINITION_VERSION>",
      "display": { "label": "Process item" },
      "inputs": {
        "script": "return { name: $vars.loop1.currentItem.name, value: $vars.fetchData1.output.body.result };"
      },
      "parentId": "loop1"
    },
    {
      "id": "end1",
      "type": "core.control.end",
      "typeVersion": "1.0",
      "display": { "label": "End" },
      "inputs": {},
      "outputs": { "results": { "source": "=js:$vars.loop1.output" } }
    }
  ],
  "edges": [
    { "id": "e1", "sourceNodeId": "start", "sourcePort": "output", "targetNodeId": "loop1", "targetPort": "input" },
    { "id": "e2", "sourceNodeId": "loop1", "sourcePort": "start", "targetNodeId": "fetchData1", "targetPort": "input" },
    { "id": "e3", "sourceNodeId": "fetchData1", "sourcePort": "default", "targetNodeId": "processItem1", "targetPort": "input" },
    { "id": "e4", "sourceNodeId": "processItem1", "sourcePort": "success", "targetNodeId": "loop1", "targetPort": "continue" },
    { "id": "e5", "sourceNodeId": "loop1", "sourcePort": "success", "targetNodeId": "end1", "targetPort": "input" }
  ],
  "variables": {
    "globals": [
      { "id": "results", "direction": "out", "type": "array" }
    ],
    "nodes": [
      { "id": "loop1.currentItem", "type": "any", "binding": { "nodeId": "loop1", "outputId": "currentItem" } },
      { "id": "loop1.currentIteration", "type": "number", "binding": { "nodeId": "loop1", "outputId": "currentIteration" } },
      { "id": "loop1.collection", "type": "array", "binding": { "nodeId": "loop1", "outputId": "collection" } },
      { "id": "loop1.output", "type": "array", "binding": { "nodeId": "loop1", "outputId": "output" } },
      { "id": "fetchData1.output", "type": "object", "binding": { "nodeId": "fetchData1", "outputId": "output" } },
      { "id": "fetchData1.error", "type": "object", "binding": { "nodeId": "fetchData1", "outputId": "error" } },
      { "id": "processItem1.output", "type": "any", "binding": { "nodeId": "processItem1", "outputId": "output" } },
      { "id": "processItem1.error", "type": "object", "binding": { "nodeId": "processItem1", "outputId": "error" } }
    ]
  }
}
```

- Both `fetchData1` and `processItem1` have `"parentId": "loop1"` — omitting it on either causes null outputs at runtime while validation passes
- HTTP body uses `start`/`default` ports; script returns via `success`/`continue`
- `detail` on HTTP node is abbreviated — populate via `uip maestro flow node configure`
- `results` receives the aggregate array verbatim, so each entry looks like `{ "fetchData1": { "output": … }, "processItem1": { "output": … } }` — both body nodes as sibling keys. Flatten it in a Script node after the loop if the consumer expects bare values. See [Aggregated loop output](#aggregated-loop-output-varsloopidoutput).

## Debug

| Error | Cause | Fix |
| --- | --- | --- |
| Collection is empty or null | Expression evaluates to null/undefined | Check `collection` expression and upstream output |
| `$vars.loop1.currentItem` is undefined | Missing node variable binding or missing `parentId` | Add `loop1.currentItem` to `variables.nodes` and set `parentId` on body nodes |
| `$vars.loop1.currentIndex` is undefined | The output is named `currentIteration` (1-based); there is no `currentIndex`, and a binding to it still validates | Use `$vars.<loopId>.currentIteration` and subtract 1 if you need a 0-based index |
| `flow validate` fails: `[MIGRATION] … 1.9→1.10 … Offending field(s): variables.variableUpdates.<nodeId>.0.expression` | `variableUpdates[].expression` written as a legacy `=js:` string (including by `uip maestro flow variable-update add`) | Rewrite with `Edit` as `{ "type": "jsExpression", "expression": "<bare JS>", "fieldType": "<target variable type>" }` |
| `flow validate` fails: `[variables.variableUpdates.<nodeId>[0].expression] Invalid input` | The expression object is malformed — missing one of the three keys, carrying an extra key, or an unknown `type` | Use exactly `type` + `expression` + `fieldType`; the object is strict |
| `flow validate` fails: `Edge references undeclared source handle "output"` / `target handle "loopBack"` | Loop body wired to ports that do not exist | Use the inner handles: `start` out of the loop, `continue` back into it |
| State variable not updating across iterations | Body node missing `parentId` | Add `"parentId": "<loopId>"` to every node inside the loop body |
| State variable becomes `NaN` | variableUpdate expression uses `$vars.<loopId>.currentItem` | Loop variables are not available in variableUpdate expressions. Do the computation in the script and reference `$vars.<bodyNodeId>.output` in the variableUpdate |
| Downstream value is `NaN`/`undefined` after reducing `$vars.<loopId>.output` | Entries are keyed by body node id, not the body's bare return value | Read `item.<bodyNodeId>.output.<field>`, not `item.<field>` — see [Aggregated loop output](#aggregated-loop-output-varsloopidoutput) |
| Infinite loop | Edges wired incorrectly | Ensure only the body's `continue` edge creates the cycle, not arbitrary edges |
| No output after loop | Missing `success` edge | Wire the `success` port to the next downstream node |
