# Merge (`core.logic.merge`)

**Type:** `core.logic.merge`  **Version:** `1.0.0`  **Category:** control-flow
**BPMN Model:** `bpmn:ParallelGateway`

## When to Use

Use a Merge node to synchronize parallel branches before continuing. It waits for all incoming paths to complete.

| Situation | Use Merge? |
|-----------|------------|
| Two or more parallel branches need to join before continuing | Yes |
| Sequential pipeline (no parallel branches) | No -- wire nodes directly |

## Ports

| Direction | Port ID | Notes |
|-----------|---------|-------|
| input | `input` | Accepts multiple incoming edges (parallel branches) |
| output | `output` | Single outgoing edge; fires after all incoming branches complete |

## Inputs

This node has no configurable inputs.

## Outputs

This node has no outputs. It acts purely as a synchronization barrier.

## Definition

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

## Instance Example

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

1. Connecting only one branch to the merge node. A merge with a single incoming edge adds no value -- it needs 2 or more incoming edges to synchronize parallel branches.
2. Using merge after a Decision or Switch node. Decision and Switch are exclusive (one branch fires); merge waits for ALL incoming branches. Use merge only after parallel splits, not conditional splits.
3. Placing merge without a preceding parallel split. The merge (`bpmn:ParallelGateway`) semantics require that all incoming branches will eventually fire. If any branch is conditional and might not execute, the merge will wait indefinitely.
4. One parallel branch has no path to the merge node. If a forked branch dead-ends without reaching the merge, the merge will never complete. Ensure all forked branches reach the merge.
5. Assuming branches arrive in a specific order. The merge waits for all incoming paths but does not guarantee any particular arrival order.
