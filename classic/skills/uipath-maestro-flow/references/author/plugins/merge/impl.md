# Merge Node — Implementation

## Node Type

`core.logic.merge`

## Registry Validation

Run:

```bash
uip maestro flow registry get core.logic.merge --output json
```

Confirm that input port `input` accepts multiple connections and output port `output` exists. Set the node instance `typeVersion` to the response's `version` field; do not hardcode it.

## JSON Structure

```json
{
  "id": "joinBranches",
  "type": "core.logic.merge",
  "typeVersion": "<DEFINITION_VERSION>",
  "display": { "label": "Join Branches" },
  "inputs": {}
}
```

## Adding, Editing, and Wiring

For add, delete, and wiring procedures, see [editing-operations.md](../../editing-operations.md). Use the JSON structure above for node-specific `inputs`.

- `input` accepts multiple incoming edges, one per parallel branch. All branches must reach the merge before execution continues.
- `output` has one outgoing edge to the next downstream node.

See [editing-operations.md](../../editing-operations.md) for edge-add procedures.

## Debug

| Error | Cause | Fix |
| --- | --- | --- |
| Merge never completes | One parallel branch has no path to the merge node | Ensure all forked branches reach the merge |
| Unexpected execution order | Branches are assumed to complete in order | Merge waits for all branches; do not depend on arrival order |