# Edge — Implementation

## Edge Skeleton

```json
{
  "id": "edge_<6chars>",
  "source": "<sourceNodeId>",
  "target": "<targetNodeId>",
  "sourceHandle": "<sourceNodeId>____source____<direction>",
  "targetHandle": "<targetNodeId>____target____<direction>",
  "data": {},
  "type": "<edge-type>"
}
```

`"data": {}` is required — never omit it.

## Edge Type

| Source node | `type` value |
|---|---|
| Trigger | `"case-management:TriggerEdge"` |
| Stage | `"case-management:Edge"` |

## Handle Format

`<nodeId>____source____<direction>` / `<nodeId>____target____<direction>` (4 underscores each side)

| Direction | When to use |
|---|---|
| `right` (source) / `left` (target) | Standard left-to-right main flow |
| `bottom` (source) / `top` (target) | Stage branching DOWN to an exception stage |
| `bottom` (source) / `left` (target) | Re-entry loop: downstream stage routing BACK to an upstream stage |

## Patterns

### Standard flow: Trigger → Stage 1 → Stage 2

Each consecutive pair gets one edge. First edge from Trigger uses `TriggerEdge`; all subsequent Stage→Stage edges use `Edge`:

```json
{ "source": "trigger_<6chars>", "target": "Stage_aaa111",
  "sourceHandle": "trigger_<6chars>____source____right",
  "targetHandle": "Stage_aaa111____target____left",
  "data": {}, "type": "case-management:TriggerEdge" }
```
```json
{ "source": "Stage_aaa111", "target": "Stage_bbb222",
  "sourceHandle": "Stage_aaa111____source____right",
  "targetHandle": "Stage_bbb222____target____left",
  "data": {}, "type": "case-management:Edge" }
```

### Exception stage branch (vertical)

```json
{ "source": "Stage_aaa111", "target": "Stage_excXXX",
  "sourceHandle": "Stage_aaa111____source____bottom",
  "targetHandle": "Stage_excXXX____target____top",
  "data": {}, "type": "case-management:Edge" }
```

### Re-entry loop (downstream → upstream)

```json
{ "source": "Stage_review", "target": "Stage_intake",
  "sourceHandle": "Stage_review____source____bottom",
  "targetHandle": "Stage_intake____target____left",
  "data": {}, "type": "case-management:Edge" }
```

The upstream stage needs a corresponding `selected-stage-exited` entry condition to actually re-activate — the edge is the visual wiring, the entry condition is the runtime gate.

## Reading from Planning (tasks.md)

```
## T05: Add edge "Trigger" → "Stage 1"
## T06: Add edge "Stage 1" → "Stage 2"
```

Source name resolves to the node ID captured when that node was created. Source is Trigger → `TriggerEdge`; source is Stage → `Edge`.
