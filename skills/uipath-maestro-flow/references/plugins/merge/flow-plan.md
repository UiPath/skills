# Merge Node

## Node Type

`core.logic.merge`

## When to Use

Use a Merge node to synchronize parallel branches before continuing. It waits for all incoming paths to complete.

### Selection Heuristics

| Situation | Use Merge? |
| --- | --- |
| Two or more parallel branches need to join before continuing | Yes |
| Sequential pipeline (no parallel branches) | No — wire nodes directly |

## Ports

| Input Port | Output Port(s) |
| --- | --- |
| `input` (accepts multiple connections) | `output` |

## Wiring Rules

- Connect each parallel branch's terminal node to the Merge node's `input` port
- Merge accepts multiple incoming edges on the same `input` port
- Execution continues from `output` only after all incoming paths complete
- Use after forking from a single node to multiple downstream nodes

## Registry Validation

```bash
uip flow registry get core.logic.merge --output json
```

Confirm: input port `input` (accepts multiple connections), output port `output`.

## Adding / Editing

For step-by-step add, delete, and wiring procedures, see [flow-editing-operations.md](../../flow-editing-operations.md). Use the JSON structure below for the node-specific `inputs` and `model` fields.

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

## Debug

| Error | Cause | Fix |
| --- | --- | --- |
| Merge never completes | One parallel branch has no path to the merge node | Ensure all forked branches reach the merge |
| Unexpected execution order | Branches assumed to complete in order | Merge waits for all — don't depend on arrival order |
