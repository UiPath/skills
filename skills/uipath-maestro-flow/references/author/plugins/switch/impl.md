# Switch Node — Implementation

## Node Type

`core.logic.switch`

## Registry Validation

```bash
uip maestro flow registry get core.logic.switch --output json
```

Confirm: input port `input`, dynamic output ports `case-{id}` + `default`, required input `cases`. Set the node instance `typeVersion` to the `version` field from this response — do not hardcode it.

## JSON Structure

```json
{
  "id": "routeByPriority",
  "type": "core.logic.switch",
  "typeVersion": "<DEFINITION_VERSION>",
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
  }
}
```

## Adding / Editing

For step-by-step add, delete, and wiring procedures, see [editing-operations.md](../../editing-operations.md). Use the JSON structure above for the node-specific `inputs`.

## Wiring

Each case creates a dynamic output port `case-{id}`. An optional `default` port handles unmatched values. Ensure edge `sourcePort` matches `case-{id}` exactly. See [editing-operations.md](../../editing-operations.md) for edge add procedures.

## Outputs

A Switch is **not readable from downstream at all**, exactly as a Decision is not — see [decision/impl.md — Outputs](../decision/impl.md#outputs) for the rule and the two supported ways to act on which branch ran. `$vars.<switchId>.matchedCaseId` and `.matchedCase` resolve to `undefined` from every downstream node, merge or no merge, and `flow validate` reports `[EXPRESSION_DIAGNOSTIC] Property '<switchId>' does not exist on type '{…}'`.

With three or more outcomes the condition is usually not worth recomputing per branch: prefer the `inout` global written on each branch.

## Debug

| Error | Cause | Fix |
| --- | --- | --- |
| No case matched, no default wired | All case expressions false and no default edge | Add a `default` edge or ensure cases are exhaustive |
| Case expression error | Invalid JavaScript in case expression | Check `=js:` expression syntax |
| Wrong port name in edge | Port ID doesn't match case ID | Ensure edge `sourcePort` is `case-{id}` matching the case's `id` field |
| `$vars.nodeId` is undefined | Upstream node not connected or wrong ID | Check edges and node IDs |
