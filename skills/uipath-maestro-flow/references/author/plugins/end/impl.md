# End Node — Implementation

## Node Type

`core.control.end`

## Registry Validation

Run `uip maestro flow registry get core.control.end --output json`. Confirm input port `input` and no output ports. Set the node instance `typeVersion` to the response `version` field; do not hardcode it.

## JSON Structure

Without output variables:

```json
{
  "id": "<END_NODE_ID>",
  "type": "core.control.end",
  "typeVersion": "<DEFINITION_VERSION>",
  "display": { "label": "<LABEL>" },
  "inputs": {}
}
```

When the workflow declares `out` variables, map every one on every End node:

```json
{
  "id": "<END_NODE_ID>",
  "type": "core.control.end",
  "typeVersion": "<DEFINITION_VERSION>",
  "display": { "label": "<LABEL>" },
  "inputs": {},
  "outputs": {
    "<VAR_ID>": {
      "source": "=js:$vars.<UPSTREAM_NODE>.output.<FIELD>"
    }
  }
}
```

Each `outputs` key must match a variable `id` in `variables.globals` with `direction: "out"`.

## Adding / Editing

For step-by-step add, delete, and wiring procedures, see [editing-operations.md](../../editing-operations.md). Use the JSON structure above for node-specific `inputs` and `outputs`.

Add output mappings with `Edit` against the `.flow` file; see [Edit/Write: Add output mapping](../../editing-operations-json.md#add-output-mapping-on-an-end-node).

## Debug

| Error | Cause | Fix |
| --- | --- | --- |
| Missing output mapping | An `out` variable is not mapped on this End node | Add `outputs.{varId}.source` for every `out` variable |
| Output expression unresolvable | The `$vars` reference points to an unreachable node | Ensure the node is upstream and connected via edges |
| Runtime silent failure | A reachable End node lacks an output mapping | Check **all** End nodes, not just the primary path |