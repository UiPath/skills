# Switch Node

## Node Type

`core.logic.switch`

## When to Use

Use a Switch node for multi-way branching (3+ paths) based on ordered case expressions. Cases are evaluated in order; the first `true` case is taken.

### Selection Heuristics

| Situation | Use Switch? |
| --- | --- |
| Three or more paths based on different conditions | Yes |
| Simple true/false branch | No — use [Decision](../decision/flow-plan.md) |
| Branch on HTTP response status codes | No — use [HTTP](../http/flow-plan.md) built-in branches |
| Branch requires reasoning on ambiguous input | No — use [Agent](../agent/flow-plan.md) |

## Ports

| Input Port | Output Port(s) |
| --- | --- |
| `input` | `case-{id}` (dynamic per case), `default` |

## Key Inputs

| Input | Required | Description |
| --- | --- | --- |
| `cases` | Yes | Array of `{ id, label, expression }` (min 1 item) |

Each case creates a dynamic output port: `case-{item.id}`. An optional `default` port handles unmatched cases.

## Wiring Rules

- Switch nodes produce one outgoing edge per case + optionally one from `default`
- Each case edge uses `sourcePort: "case-{id}"` where `{id}` matches the case's `id` field
- Every case branch must lead to a downstream node

## Registry Validation

```bash
uip flow registry get core.logic.switch --output json
```

Confirm: input port `input`, dynamic output ports `case-{id}` + `default`, required input `cases`.

## Adding / Editing

For step-by-step add, delete, and wiring procedures, see [flow-editing-operations.md](../../flow-editing-operations.md). Use the JSON structure below for the node-specific `inputs` and `model` fields.

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

## Wiring

Each case creates a dynamic output port `case-{id}`. An optional `default` port handles unmatched values. Ensure edge `sourcePort` matches `case-{id}` exactly. See [flow-editing-operations.md](../../flow-editing-operations.md) for edge add procedures.

## Debug

| Error | Cause | Fix |
| --- | --- | --- |
| No case matched, no default wired | All case expressions false and no default edge | Add a `default` edge or ensure cases are exhaustive |
| Case expression error | Invalid JavaScript in case expression | Check `=js:` expression syntax |
| Wrong port name in edge | Port ID doesn't match case ID | Ensure edge `sourcePort` is `case-{id}` matching the case's `id` field |
| `$vars.nodeId` is undefined | Upstream node not connected or wrong ID | Check edges and node IDs |
