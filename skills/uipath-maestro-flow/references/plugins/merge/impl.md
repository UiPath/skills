# Merge Node — Implementation

## Node Type

`core.logic.merge`

## Registry Validation

```bash
uip flow registry get core.logic.merge --output json
```

Confirm: input port `input` (accepts multiple connections), output port `output`.

## JSON Structure

```json
{
  "id": "joinBranches",
  "type": "core.logic.merge",
  "typeVersion": "1.0.0",
  "display": { "label": "Join Branches" },
  "inputs": {},
  "model": { "type": "bpmn:ParallelGateway" }
}
```

## Adding / Editing

For step-by-step add, delete, and wiring procedures, see [flow-editing-operations.md](../../flow-editing-operations.md). Use the JSON structure above for the node-specific `inputs` and `model` fields.

## Wiring

- `input` — accepts multiple incoming edges (one per parallel branch). All branches must reach the merge before it continues.
- `output` — single outgoing edge to the next downstream node.

See [flow-editing-operations.md](../../flow-editing-operations.md) for edge add procedures.

## Debug

| Error | Cause | Fix |
| --- | --- | --- |
| Merge never completes | One parallel branch has no path to the merge node | Ensure all forked branches reach the merge |
| Unexpected execution order | Branches assumed to complete in order | Merge waits for all — don't depend on arrival order |
