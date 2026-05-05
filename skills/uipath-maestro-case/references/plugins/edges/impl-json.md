---
direct-json: supported
---

# edges — JSON Implementation

Cross-cutting direct-JSON rules live in [`case-editing-operations.md`](../../case-editing-operations.md).

## Purpose

Connect two nodes (Trigger → Stage or Stage → Stage) by appending an edge object to `edges`. Edge type is **inferred from the source node** — never specified explicitly.

The same recipe covers add / edit / remove — direct JSON writes state declaratively: "make `edges` match the desired set."

> **Schema neutrality.** Edge shape is **identical across v19 and v20** — both use the top-level `edges[]` array, same per-edge fields. Per Rule 18 in v20, do NOT emit `data.waypoints` (lifted to top-level `layout.edges[<edgeId>].waypoints`); skill never authored waypoints anyway, so this is a no-op. `zIndex` is NOT in the layout-strip list; edge-level `zIndex` (when sdd.md requests one) stays at the edge level in both schemas.

## Input spec (from `tasks.md`)

| Field | Required | Notes |
|---|---|---|
| `source` | yes | Trigger ID (e.g., `trigger_1`) or Stage ID. Resolved from `id-map.json`. |
| `target` | yes | Stage ID. Resolved from `id-map.json`. Never an ExceptionStage — see Guardrails. |
| `label` | yes | Display label on the connector (Studio Web "Name"). Always present — planning auto-derives when sdd.md does not state one. See [`planning.md` § Labels](planning.md#labels). |
| `sourceHandle` direction | no | `right` (default) \| `left` \| `top` \| `bottom` |
| `targetHandle` direction | no | `left` (default) \| `right` \| `top` \| `bottom` |
| `zIndex` | no | Integer. Omit the key entirely when unset. |

## Guardrails (enforce before writing)

1. **Both endpoints exist in `schema.nodes`.** If either `source` or `target` is missing, halt — do not write a dangling edge.
2. **Neither endpoint is an `case-management:ExceptionStage`.** Exception stages have no edges (see [`planning.md` § Wiring Constraints](planning.md#wiring-constraints)). They are reached via an interrupting `stage-entry-conditions` rule and exited via a `return-to-origin` `stage-exit-conditions` rule. Reject the write and flag to the user.
3. **`target` is not a Trigger.** Edges always flow into a Stage (regular Stage only).
4. **No duplicate edge with the same `source`+`target` pair** unless the sdd.md explicitly declares parallel edges. Warn if one already exists.

## ID generation

- Prefix: `edge_`
- Suffix length: 6
- Algorithm: per [`case-editing-operations.md § ID Generation`](../../case-editing-operations.md#id-generation)

Record `T<n> → edge_xxxxxx` in `id-map.json` for the audit trail, even though no downstream node references edges by ID.

## Edge-type inference

```text
sourceNode = schema.nodes.find(n => n.id === source)
edgeType   = sourceNode.type === "case-management:Trigger"
             ? "case-management:TriggerEdge"
             : "case-management:Edge"
```

Do NOT accept a caller-supplied `type` — always derive it from the source node.

## Handle strings

Exactly **four underscores** each side:

```text
sourceHandle = `${source}____source____${sourceDir}`   # sourceDir default: "right"
targetHandle = `${target}____target____${targetDir}`   # targetDir default: "left"
```

## Recipe — Add

Append this object to `schema.edges` — always append, never prepend.

### TriggerEdge (source is a Trigger)

```json
{
  "id": "<edge_xxxxxx>",
  "source": "<triggerId>",
  "target": "<stageId>",
  "sourceHandle": "<triggerId>____source____<sourceDir>",
  "targetHandle": "<stageId>____target____<targetDir>",
  "data": { "label": "<label>" },
  "type": "case-management:TriggerEdge"
}
```

### Edge (source is a Stage)

```json
{
  "id": "<edge_xxxxxx>",
  "source": "<sourceStageId>",
  "target": "<targetStageId>",
  "sourceHandle": "<sourceStageId>____source____<sourceDir>",
  "targetHandle": "<targetStageId>____target____<targetDir>",
  "data": { "label": "<label>" },
  "type": "case-management:Edge"
}
```

### Optional-field emission rules

Omitted inputs yield absent keys (matches `JSON.stringify`'s drop-undefined behavior):

| Input | Emission |
|---|---|
| `zIndex` unset | Omit the `zIndex` key entirely |
| `sourceHandle` direction unset | Still emit the key with default `right` |
| `targetHandle` direction unset | Still emit the key with default `left` |

Key insertion order (cosmetic — frontends accept any order):

```text
id, source, target, sourceHandle, targetHandle, [zIndex], data, type
```

## Recipe — Edit

Find the edge by `id` in `schema.edges` and mutate in place:

| Field | Mutable | Notes |
|---|---|---|
| `id` | no | Immutable. |
| `source` | no | Immutable. To rewire, remove + re-add. |
| `target` | no | Immutable. To rewire, remove + re-add. |
| `type` | no | Derived from `source`. Immutable. |
| `data.label` | yes | Mutable but never absent — must always carry a non-empty string. Replace with new value; do not delete. |
| `sourceHandle` | yes | Re-construct with new direction, keep same `source` ID. |
| `targetHandle` | yes | Re-construct with new direction, keep same `target` ID. |
| `zIndex` | yes | Set or `delete` to clear. |

> To re-wire an edge (change `source` or `target`), **remove and re-add**. This preserves the invariant that `sourceHandle`/`targetHandle` always reference the current endpoints.

## Recipe — Remove

```text
schema.edges = schema.edges.filter(e => e.id !== edgeId)
```

Nothing references edges by ID in `caseplan.json`, so no cascade cleanup is needed. A stage removal still cascades to its edges — that logic lives in the stages JSON recipe (`Delete a node` in [`case-editing-operations.md`](../../case-editing-operations.md#delete-a-node)), not here.

## Semantic position

Edges live in the top-level `schema.edges` array. Always append new edges to the end.

## Post-write validation

After writing, confirm:

- `schema.edges` contains the new edge with the generated ID
- `edges[].type` matches the inference (`TriggerEdge` iff source is a Trigger)
- `edges[].sourceHandle` and `edges[].targetHandle` use exactly 4 underscores each side
- `edges[].source` and `edges[].target` resolve to existing `schema.nodes` entries
- `edges[].data.label` is present and non-empty (planning guarantees every edge has a label)
- `edges[].zIndex` is present iff the T-entry declared one

Run `uip maestro case validate <file> --output json` after all edges for this plugin's batch are added.

