# Merge

**Type:** `core.logic.merge`  **Version:** `1.0.0`  **Category:** control-flow
**BPMN Model:** `bpmn:ParallelGateway`

## Ports

| Position | Handle ID | Type | Notes |
|----------|-----------|------|-------|
| left | `input` | target | Accepts multiple incoming edges (parallel branches) |
| right | `output` | source | Single outgoing edge; fires after all incoming branches complete |

## Definition Block

Copy this verbatim into the `definitions` array (do not modify):

```json
{
  "nodeType": "core.logic.merge",
  "version": "1.0.0",
  "category": "control-flow",
  "tags": ["control-flow", "merge"],
  "sortOrder": 2,
  "display": {
    "label": "Merge",
    "icon": "merge"
  },
  "handleConfiguration": [
    {
      "position": "left",
      "handles": [
        {
          "id": "input",
          "type": "target",
          "handleType": "input"
        }
      ],
      "visible": true
    },
    {
      "position": "right",
      "handles": [
        {
          "id": "output",
          "type": "source",
          "handleType": "output"
        }
      ],
      "visible": true
    }
  ],
  "model": {
    "type": "bpmn:ParallelGateway"
  }
}
```

## Node Instance Example

```json
{
  "id": "merge_1",
  "type": "core.logic.merge",
  "position": { "x": 800, "y": 200 },
  "data": {}
}
```

Typical wiring -- two parallel branches converging:

```json
[
  { "source": "branchA_1", "sourceHandle": "output", "target": "merge_1", "targetHandle": "input" },
  { "source": "branchB_1", "sourceHandle": "output", "target": "merge_1", "targetHandle": "input" },
  { "source": "merge_1", "sourceHandle": "output", "target": "nextNode_1", "targetHandle": "input" }
]
```

## Common Mistakes

- Connecting only one branch to the merge node. A merge with a single incoming edge adds no value -- it needs 2 or more incoming edges to synchronize parallel branches.
- Using merge after a Decision or Switch node. Decision and Switch are exclusive (one branch fires); merge waits for ALL incoming branches. Use merge only after parallel splits, not conditional splits.
- Placing merge without a preceding parallel split. The merge (ParallelGateway) semantics require that all incoming branches will eventually fire. If any branch is conditional and might not execute, the merge will wait indefinitely.
