# Edge — Implementation

## Edge Types

| Type | When source is | JSON `type` value |
|---|---|---|
| TriggerEdge | A Trigger node | `"case-management:TriggerEdge"` |
| Edge | A Stage node | `"case-management:Edge"` |

## Edge Skeleton

```json
{
  "id": "edge_<6chars>",
  "source": "<sourceNodeId>",
  "target": "<targetNodeId>",
  "sourceHandle": "<sourceNodeId>____source____right",
  "targetHandle": "<targetNodeId>____target____left",
  "data": {},
  "type": "case-management:TriggerEdge"
}
```

`"data": {}` is required — never omit it.

## Edge Data Fields

| Field | Required | Notes |
|-------|----------|-------|
| `data` | ✓ | Must be present, at minimum `{}` |
| `data.label` | optional | Text label displayed on the edge in the canvas (e.g., `"Rework : missing reports"`) |
| `data.parentElement` | optional | FE-generated reference to root — omit when writing |
| `data.waypoints` | optional | FE-generated array of `{x, y}` coordinates for edge routing — omit when writing |
| `data.isIntersecting` | optional | FE-generated layout flag — omit when writing |

### Edge Labels

Use `data.label` to annotate an edge with a human-readable description. This is especially useful for:
- Re-entry loop edges (e.g., "Rework : missing reports")
- Conditional routing (e.g., "Approved", "Rejected")
- Exception stage branches (e.g., "Customer response required")

```json
{
  "id": "edge_hEKkGK",
  "source": "Stage_xCv7s5",
  "target": "stage-1",
  "sourceHandle": "Stage_xCv7s5____source____bottom",
  "targetHandle": "stage-1____target____left",
  "data": {
    "label": "Rework : missing reports"
  },
  "type": "case-management:Edge"
}
```

### FE-Generated Fields (Omit When Writing)

The FE adds these fields automatically when the user drags edges in the canvas. They are valid in caseplan.json but the agent should **not** write them:

- `data.waypoints` — array of `{x, y}` coordinates for visual edge routing
- `data.parentElement` — reference to `{id: "root", type: "case-management:root"}`
- `data.isIntersecting` — layout collision flag
- `style` — stroke styling
- `zIndex` — layer ordering

These are preserved if present but not required for validation or execution.

## Handle Format

`<nodeId>____source____<direction>` (4 underscores on each side of `source` or `target`)

| Direction | Use when |
|---|---|
| `right` | Standard left-to-right main flow (source) |
| `left` | Standard left-to-right main flow (target) |
| `bottom` | Source-side handle for vertical edges: stage branching DOWN to an exception stage, OR a downstream stage looping BACK to an upstream stage (re-entry) |
| `top` | Target-side handle for vertical edges: exception stage receiving from above |

### Re-entry loop edge (downstream stage → upstream stage)

When a stage routes back to an earlier stage in the flow (for re-work, customer follow-up loops, etc.), the edge uses `bottom` on the source side and `left` on the target side — the visual loops below the row of stages and re-enters the upstream stage from its left:

```json
{
  "id": "edge_<6chars>",
  "source": "Stage_review",
  "target": "Stage_intake",
  "sourceHandle": "Stage_review____source____bottom",
  "targetHandle": "Stage_intake____target____left",
  "data": {},
  "type": "case-management:Edge"
}
```

The upstream stage (`Stage_intake`) needs a corresponding entry condition keyed off `selected-stage-exited` from the downstream stage to actually re-activate — the edge alone is the visual wiring, the entry condition is the runtime gate.

## Standard Flow Pattern

Trigger → Stage 1 → Stage 2 → Stage 3:

```json
[
  {
    "id": "edge_<6chars>",
    "source": "trigger_<6chars>",
    "target": "Stage_aaa111",
    "sourceHandle": "trigger_<6chars>____source____right",
    "targetHandle": "Stage_aaa111____target____left",
    "data": {},
    "type": "case-management:TriggerEdge"
  },
  {
    "id": "edge_<6chars>",
    "source": "Stage_aaa111",
    "target": "Stage_bbb222",
    "sourceHandle": "Stage_aaa111____source____right",
    "targetHandle": "Stage_bbb222____target____left",
    "data": {},
    "type": "case-management:Edge"
  },
  {
    "id": "edge_<6chars>",
    "source": "Stage_bbb222",
    "target": "Stage_ccc333",
    "sourceHandle": "Stage_bbb222____source____right",
    "targetHandle": "Stage_ccc333____target____left",
    "data": {},
    "type": "case-management:Edge"
  }
]
```

## Exception Stage Branch Pattern

Main Stage → Exception Stage (vertical branch):

```json
{
  "id": "edge_<6chars>",
  "source": "Stage_aaa111",
  "target": "Stage_excXXX",
  "sourceHandle": "Stage_aaa111____source____bottom",
  "targetHandle": "Stage_excXXX____target____top",
  "data": {},
  "type": "case-management:Edge"
}
```

## Reading from Planning (tasks.md)

```
## T05: Add edge "Trigger" → "Stage 1"
## T06: Add edge "Stage 1" → "Stage 2"
```

Maps directly — source name resolves to the node ID captured when that node was created:
- `"Trigger"` → the trigger node ID (e.g. `trigger_aB3cD4`)
- `"Stage 1"` → the stage ID captured when Stage 1 was created (e.g. `Stage_f95rff`)
- Source is Trigger → `type: "case-management:TriggerEdge"`
- Source is Stage → `type: "case-management:Edge"`
