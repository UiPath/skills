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
  "model": { "type": "bpmn:SubProcess" }
}
```

## Adding via CLI

```bash
uip flow node add <ProjectName>.flow core.logic.loop --output json \
  --input '{"collection": "=js:$vars.fetchData.output.body.items"}' \
  --label "Process Items" \
  --position 400,300
```

## Wiring Pattern

```bash
# Into the loop
uip flow edge add <ProjectName>.flow upstreamNode processItems --output json \
  --source-port success --target-port input

# Loop body: loop -> first body node
uip flow edge add <ProjectName>.flow processItems bodyAction --output json \
  --source-port output --target-port input

# Loop body: last body node -> loopBack
uip flow edge add <ProjectName>.flow bodyAction processItems --output json \
  --source-port success --target-port loopBack

# After loop completes
uip flow edge add <ProjectName>.flow processItems nextNode --output json \
  --source-port success --target-port input
```

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
