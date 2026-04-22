# Switch Node — Implementation

## Node Type

`core.logic.switch`

## Registry Validation

```bash
uip maestro flow registry get core.logic.switch --output json
```

Confirm: input port `input`, dynamic output ports `case-{id}` + `default`, required input `cases`.

## JSON Structure

```json
{
  "id": "routeByPriority",
  "type": "core.logic.switch",
  "typeVersion": "1.0.0",
  "display": { "label": "Route by Priority" },
  "inputs": {
    "cases": [
      {
        "id": "high",
        "label": "High Priority",
        "expression": "$vars.classify.output.priority === 'high'"
      },
      {
        "id": "medium",
        "label": "Medium Priority",
        "expression": "$vars.classify.output.priority === 'medium'"
      },
      {
        "id": "low",
        "label": "Low Priority",
        "expression": "$vars.classify.output.priority === 'low'"
      }
    ]
  },
  "model": { "type": "bpmn:ExclusiveGateway" }
}
```

## Adding / Editing

For step-by-step add, delete, and wiring procedures, see [flow-editing-operations.md](../../flow-editing-operations.md). Use the JSON structure above for the node-specific `inputs` and `model` fields.

## Wiring

Each case creates a dynamic output port `case-{id}`. An optional `default` port handles unmatched values. Ensure edge `sourcePort` matches `case-{id}` exactly. See [flow-editing-operations.md](../../flow-editing-operations.md) for edge add procedures.

## Debug

| Error | Cause | Fix |
| --- | --- | --- |
| No case matched, no default wired | All case expressions false and no default edge | Add a `default` edge or ensure cases are exhaustive |
| Case expression error | Invalid JavaScript in case expression | Check `=js:` expression syntax |
| Wrong port name in edge | Port ID doesn't match case ID | Ensure edge `sourcePort` is `case-{id}` matching the case's `id` field |
| `$vars.nodeId` is undefined | Upstream node not connected or wrong ID | Check edges and node IDs |
