# Loop Node — Implementation

## Node Type

`core.logic.loop`

## Registry Validation

```bash
uip flow registry get core.logic.loop --output json
```

Confirm: input ports `input` and `loopBack`, output ports `success` and `output`, required input `collection`.

## JSON Structure

```json
{
  "id": "processItems",
  "type": "core.logic.loop",
  "typeVersion": "1.0.0",
  "display": { "label": "Process Items" },
  "inputs": {
    "collection": "=js:$vars.fetchData.output.body.items"
  },
  "outputs": {
    "output": {
      "type": "object",
      "description": "The return value of the loop",
      "source": "=result.response",
      "var": "output"
    },
    "error": {
      "type": "object",
      "description": "Error information if the loop fails",
      "source": "=result.Error",
      "var": "error"
    }
  },
  "model": { "type": "bpmn:SubProcess" }
}
```

### Parallel Execution

```json
{
  "id": "processItemsParallel",
  "type": "core.logic.loop",
  "typeVersion": "1.0.0",
  "display": { "label": "Process Items (Parallel)" },
  "inputs": {
    "collection": "=js:$vars.fetchData.output.body.items",
    "parallel": true
  },
  "outputs": {
    "output": {
      "type": "object",
      "description": "The return value of the loop",
      "source": "=result.response",
      "var": "output"
    },
    "error": {
      "type": "object",
      "description": "Error information if the loop fails",
      "source": "=result.Error",
      "var": "error"
    }
  },
  "model": { "type": "bpmn:SubProcess" }
}
```

## Adding / Editing

For step-by-step add, delete, and wiring procedures, see [flow-editing-operations.md](../../flow-editing-operations.md). Use the JSON structure above for the node-specific `inputs` and `model` fields.

## Wiring

Loop nodes have a specific wiring pattern:

- `input` — entry from upstream
- `output` — into the loop body (first body node)
- `loopBack` — return from last body node back to loop
- `success` — exit after loop completes (to next downstream node)

See [flow-editing-operations.md](../../flow-editing-operations.md) for edge add procedures.

## Accessing Loop Variables Inside Body

Inside the loop body, use `iterator` to access the current item:

```javascript
// In a Script node inside the loop body
const item = iterator.currentItem;
const index = iterator.currentIndex;
return { processed: item.name.toUpperCase(), position: index };
```

## Debug

| Error | Cause | Fix |
| --- | --- | --- |
| Collection is empty or null | Expression evaluates to null/undefined | Check `collection` expression and upstream output |
| `iterator` is undefined | Referencing `iterator` outside loop body | `iterator` is only available inside the loop body |
| Infinite loop | Edges wired incorrectly | Ensure only `loopBack` creates the cycle, not arbitrary edges |
| No output after loop | Missing `success` edge | Wire the `success` port to the next downstream node |
