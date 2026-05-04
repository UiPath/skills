# End Node — Implementation

## Node Type

`core.control.end`

## Registry Validation

```bash
uip maestro flow registry get core.control.end --output json
```

Confirm: input port `input`, no output ports.

## JSON Structure

### Without Output Mapping

```json
{
  "id": "doneSuccess",
  "type": "core.control.end",
  "typeVersion": "1.0.0",
  "display": { "label": "Done" },
  "inputs": {}
}
```

### With Output Mapping

When the workflow declares `out` variables, every End node must map all of them:

```json
{
  "id": "doneSuccess",
  "type": "core.control.end",
  "typeVersion": "1.0.0",
  "display": { "label": "Done" },
  "inputs": {},
  "outputs": {
    "processedCount": {
      "source": "=js:$vars.processData.output.count"
    },
    "resultSummary": {
      "source": "=js:$vars.formatOutput.output.summary"
    }
  }
}
```

Each key in `outputs` must match a variable `id` from `variables.globals` where `direction: "out"`.

## Adding / Editing

For step-by-step add, delete, and wiring procedures, see [editing-operations.md](../../editing-operations.md). Use the JSON structure above for the node-specific `inputs` and `outputs`.

Output mapping must be added with `Edit` against the `.flow` file — see [Edit/Write: Add output mapping](../../editing-operations-json.md#add-output-mapping-on-an-end-node).

## Debug

| Error | Cause | Fix |
| --- | --- | --- |
| Missing output mapping | `out` variable not mapped on this End node | Add `outputs.{varId}.source` expression for every `out` variable |
| Output expression unresolvable | `$vars` reference points to unreachable node | Ensure the node is upstream and connected via edges |
| Runtime silent failure | Output mapping missing on one reachable End node | Check **all** End nodes, not just the primary path |
