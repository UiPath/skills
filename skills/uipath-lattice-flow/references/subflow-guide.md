# Subflow Guide

Subflows are embedded workflows that live inside loop or container nodes. Most flows do not require manual subflow manipulation -- they are created automatically when you place nodes inside a loop.

---

## Structure

Subflows live in `workflow.subflows`, keyed by the parent node's ID:

```json
{
  "subflows": {
    "<PARENT_NODE_ID>": {
      "nodes": [],
      "edges": [],
      "variables": {
        "globals": [],
        "nodes": []
      }
    }
  }
}
```

Each subflow is a self-contained workflow with its own nodes, edges, and variables arrays.

---

## Isolated Scope

Subflow variables are **completely separate** from the parent flow's variables. You cannot reference `$vars` from the parent scope inside a subflow. To pass data into a subflow, use the parent node's inputs explicitly.

---

## Loop Subflows

When using `core.logic.loop`, child nodes go in `subflows.<LOOP_NODE_ID>`. The loop node exposes two internal-scope outputs available inside the subflow:

| Variable | Type | Description |
|----------|------|-------------|
| `$vars.currentItem` | any | The current element from the collection being iterated |
| `$vars.currentIndex` | number | The zero-based index of the current iteration |

These are the only parent-provided values accessible within the loop body.

---

## Child Nodes

Every node inside a subflow must have its `parentId` field set to the parent loop/container node's ID:

```json
{
  "id": "processItem1",
  "type": "core.action.script",
  "typeVersion": "1",
  "parentId": "<PARENT_NODE_ID>",
  "inputs": { ... }
}
```

Nodes without a correct `parentId` will not be recognized as part of the subflow.

---

## Edges

Subflow edges connect child nodes within the subflow. They follow the same ID generation and validation rules as top-level edges:

- Format: `{sourceId}-{sourcePort}-{targetId}-{targetPort}`
- Both source and target nodes must exist in the subflow's `nodes` array
- Port IDs must match the node type's handle configuration

Subflow edges are stored in the subflow's own `edges` array, not in the top-level `workflow.edges`.

---

## When to Use

Subflows are automatically created when you place nodes inside a loop. You rarely need to construct them manually. For simple loop bodies:

1. Wire the loop node's `output` port to the first body node
2. Wire the last body node back to the loop's `loopBack` port
3. The runtime handles subflow creation

Only manipulate `workflow.subflows` directly when you need multiple nodes inside a loop body or complex internal branching.

---

## Validation

When a subflow exists, confirm:

1. Every child node has `parentId` set to the correct parent node ID
2. All subflow edges reference nodes that exist in that subflow's `nodes` array
3. The subflow's `variables.nodes` is regenerated following the same algorithm as the top-level flow (see [project-scaffolding-guide.md](project-scaffolding-guide.md) Section 3)
4. No references to parent-scope `$vars` appear in subflow node expressions
