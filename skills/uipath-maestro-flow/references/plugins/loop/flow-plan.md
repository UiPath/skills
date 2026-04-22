# Loop Node

## Node Type

`core.logic.loop`

## When to Use

Use a Loop node to iterate over a collection of items. Supports sequential and parallel execution.

### Selection Heuristics

| Situation | Use Loop? |
| --- | --- |
| Process each item in an array | Yes |
| Run the same operation on multiple inputs concurrently | Yes (with `parallel: true`) |
| Simple data transformation on a collection | No — use [Transform](../transform/flow-plan.md) |
| Distribute work items to robots | No — use [Queue](../queue/flow-plan.md) |

## Ports

| Input Port(s) | Output Port(s) |
| --- | --- |
| `input`, `loopBack` | `success`, `output`, `error` |

- `loopBack` — receives the edge returning from the last node inside the loop body
- `success` — fires after all iterations complete
- `output` — carries aggregated results from all iterations
- `error` — implicit error port shared with all action nodes; fires when the loop or an iteration throws. See [Implicit error port on action nodes](../../flow-file-format.md#implicit-error-port-on-action-nodes).

## Key Inputs

| Input | Required | Description |
| --- | --- | --- |
| `collection` | Yes | Expression pointing to an array (e.g., `$vars.fetchData.output.body.items`) |
| `parallel` | No | `true` to execute all iterations concurrently (default: sequential) |

## Wiring Rules

- The loop body starts from the `output` port of the loop node
- The last node in the loop body connects back to the loop's `loopBack` port
- After all iterations, execution continues from the `success` port
- Do not create cycles except through the `loopBack` mechanism
- **Every node inside the loop body must have `"parentId": "<loopId>"`** — without this, variableUpdates will not fire per-iteration and loop variables will be inaccessible

## Registry Validation

```bash
uip flow registry get core.logic.loop --output json
```

Confirm: input ports `input` and `loopBack`, output ports `success` and `output`, required input `collection`.

## Adding / Editing

For step-by-step add, delete, and wiring procedures, see [flow-editing-operations.md](../../flow-editing-operations.md). Use the JSON structure below for the node-specific `inputs` and `model` fields.

## JSON Structure

### Loop node

```json
{
  "id": "loop1",
  "type": "core.logic.loop",
  "typeVersion": "1.0.0",
  "display": { "label": "Loop over items" },
  "inputs": {
    "collection": "=js:$vars.fetchData.output.body.items",
    "parallel": false
  },
  "model": { "type": "bpmn:SubProcess" }
}
```

Set `"parallel": true` to execute all iterations concurrently.

### Loop body nodes — `parentId` required

Every node inside the loop body **must** have `"parentId"` set to the loop node's ID. Without this, the runtime does not know the node is part of the loop and variableUpdates will not fire per-iteration.

```json
{
  "id": "processItem",
  "type": "core.action.script",
  "typeVersion": "1.0.0",
  "display": { "label": "Process item" },
  "inputs": {
    "script": "return $vars.product * $vars.loop1.currentItem"
  },
  "model": { "type": "bpmn:ScriptTask" },
  "parentId": "loop1"
}
```

> **Critical:** If you omit `parentId`, the node executes outside the loop context. State variables will not update across iterations and loop outputs like `currentItem` will be inaccessible.

## Accessing Output

### Loop Variables Inside Body

Inside the loop body, access the current item via `$vars.<loopId>.currentItem`:

```javascript
// In a Script node inside the loop body (parentId must be set to the loop node)
const item = $vars.loop1.currentItem;
const index = $vars.loop1.currentIndex;
return { processed: item.name.toUpperCase(), position: index };
```

| Variable | Description |
| --- | --- |
| `$vars.<loopId>.currentItem` | The item being processed in this iteration |
| `$vars.<loopId>.currentIndex` | 0-based iteration index |
| `$vars.<loopId>.collection` | The full collection being iterated |

> **Do not use `iterator.currentItem`.** The correct access pattern is `$vars.<loopId>.currentItem` where `<loopId>` is the loop node's `id` (e.g., `$vars.loop1.currentItem`).

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
        "id": "loop1.currentIndex",
        "type": "number",
        "description": "The current iteration index (0-based)",
        "binding": { "nodeId": "loop1", "outputId": "currentIndex" }
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
          "expression": "=js:$vars.bodyNode.output"
        }
      ]
    }
  }
}
```

The variableUpdate fires after each iteration, so the `inout` variable carries the accumulated value into the next iteration.

> **Critical:** The variableUpdate expression **cannot** access loop iteration variables like `$vars.<loopId>.currentItem`. These are only available inside the body node's script. The variableUpdate must reference the body node's output (e.g., `=js:$vars.bodyNode.output`). If you need to compute using `currentItem`, do the computation in the script and reference the script's output in the variableUpdate.

## Complete Example — Loop with State Accumulation

A flow that iterates over a collection, accumulates a result in an `inout` variable via a Script body node, and outputs the final value.

```json
{
  "nodes": [
    {
      "id": "start",
      "type": "core.trigger.manual",
      "typeVersion": "1.0.0",
      "display": { "label": "Manual trigger" },
      "inputs": {},
      "model": { "type": "bpmn:StartEvent", "entryPointId": "..." }
    },
    {
      "id": "loop1",
      "type": "core.logic.loop",
      "typeVersion": "1.0.0",
      "display": { "label": "Loop" },
      "inputs": { "collection": "=js:$vars.inputItems", "parallel": false },
      "model": { "type": "bpmn:SubProcess" }
    },
    {
      "id": "bodyScript",
      "type": "core.action.script",
      "typeVersion": "1.0.0",
      "display": { "label": "Process item" },
      "inputs": {
        "script": "return $vars.accumulator + $vars.loop1.currentItem;"
      },
      "model": { "type": "bpmn:ScriptTask" },
      "parentId": "loop1"
    },
    {
      "id": "end1",
      "type": "core.control.end",
      "typeVersion": "1.0.0",
      "display": { "label": "End" },
      "inputs": {},
      "outputs": {
        "result": { "source": "=js:$vars.accumulator" }
      },
      "model": { "type": "bpmn:EndEvent" }
    }
  ],
  "edges": [
    { "id": "e1", "sourceNodeId": "start", "sourcePort": "output", "targetNodeId": "loop1", "targetPort": "input" },
    { "id": "e2", "sourceNodeId": "loop1", "sourcePort": "output", "targetNodeId": "bodyScript", "targetPort": "input" },
    { "id": "e3", "sourceNodeId": "bodyScript", "sourcePort": "success", "targetNodeId": "loop1", "targetPort": "loopBack" },
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
      { "id": "loop1.currentIndex", "type": "number", "binding": { "nodeId": "loop1", "outputId": "currentIndex" } },
      { "id": "loop1.collection", "type": "array", "binding": { "nodeId": "loop1", "outputId": "collection" } },
      { "id": "loop1.output", "type": "array", "binding": { "nodeId": "loop1", "outputId": "output" } },
      { "id": "bodyScript.output", "type": "object", "binding": { "nodeId": "bodyScript", "outputId": "output" } },
      { "id": "bodyScript.error", "type": "object", "binding": { "nodeId": "bodyScript", "outputId": "error" } }
    ],
    "variableUpdates": {
      "bodyScript": [
        { "variableId": "accumulator", "expression": "=js:$vars.bodyScript.output" }
      ]
    }
  }
}
```

Key points in this pattern:
- `bodyScript` has `"parentId": "loop1"` — places it inside the loop
- Script accesses `$vars.loop1.currentItem` for the current iteration value
- `variableUpdate` on `bodyScript` writes the script's return value back to `accumulator`
- `accumulator` is `inout` so it persists across iterations
- End node maps the final accumulated value to the `out` variable

## Debug

| Error | Cause | Fix |
| --- | --- | --- |
| Collection is empty or null | Expression evaluates to null/undefined | Check `collection` expression and upstream output |
| `$vars.loop1.currentItem` is undefined | Missing node variable binding or missing `parentId` | Add `loop1.currentItem` to `variables.nodes` and set `parentId` on body nodes |
| State variable not updating across iterations | Body node missing `parentId` | Add `"parentId": "<loopId>"` to every node inside the loop body |
| State variable becomes `NaN` | variableUpdate expression uses `$vars.<loopId>.currentItem` | Loop variables are not available in variableUpdate expressions. Do the computation in the script and reference `$vars.<bodyNodeId>.output` in the variableUpdate |
| Infinite loop | Edges wired incorrectly | Ensure only `loopBack` creates the cycle, not arbitrary edges |
| No output after loop | Missing `success` edge | Wire the `success` port to the next downstream node |
