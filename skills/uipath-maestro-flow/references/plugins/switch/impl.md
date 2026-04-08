# Switch Node — Implementation

## Node Type

`core.logic.switch`

## Registry Validation

```bash
uip flow registry get core.logic.switch --output json
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
        "expression": "=js:$vars.classify.output.priority === 'high'"
      },
      {
        "id": "medium",
        "label": "Medium Priority",
        "expression": "=js:$vars.classify.output.priority === 'medium'"
      },
      {
        "id": "low",
        "label": "Low Priority",
        "expression": "=js:$vars.classify.output.priority === 'low'"
      }
    ]
  },
  "model": { "type": "bpmn:ExclusiveGateway" }
}
```

## Adding via CLI

```bash
uip flow node add <ProjectName>.flow core.logic.switch --output json \
  --input '{"cases": [{"id": "high", "label": "High", "expression": "=js:$vars.classify.output.priority === '\''high'\''"}, {"id": "low", "label": "Low", "expression": "=js:$vars.classify.output.priority === '\''low'\''"}]}' \
  --label "Route by Priority" \
  --position 400,300
```

## Wiring Example

```bash
# Case edges
uip flow edge add <ProjectName>.flow routeByPriority handleHigh --output json \
  --source-port case-high --target-port input

uip flow edge add <ProjectName>.flow routeByPriority handleMedium --output json \
  --source-port case-medium --target-port input

uip flow edge add <ProjectName>.flow routeByPriority handleLow --output json \
  --source-port case-low --target-port input

# Default fallback
uip flow edge add <ProjectName>.flow routeByPriority handleUnknown --output json \
  --source-port default --target-port input
```

## Debug

| Error | Cause | Fix |
| --- | --- | --- |
| No case matched, no default wired | All case expressions false and no default edge | Add a `default` edge or ensure cases are exhaustive |
| Case expression error | Invalid JavaScript in case expression | Check `=js:` expression syntax |
| Wrong port name in edge | Port ID doesn't match case ID | Ensure edge `sourcePort` is `case-{id}` matching the case's `id` field |
| `$vars.nodeId` is undefined | Upstream node not connected or wrong ID | Check edges and node IDs |
