---
direct-json: supported
---

# edges — JSON Implementation

Authoritative when the matrix in [`case-editing-operations.md`](../../case-editing-operations.md) lists `edges = JSON`. Cross-cutting direct-JSON rules live in [`case-editing-operations-json.md`](../../case-editing-operations-json.md). For the CLI fallback, see [`impl-cli.md`](impl-cli.md).

## Purpose

Connect two nodes (Trigger → Stage or Stage → Stage) by appending an edge object to `schema.edges`. Edge type is **inferred from the source node** — never specified explicitly.

The same recipe covers add / edit / remove — direct JSON writes state, so the three CLI commands collapse into a single declarative operation: "make `schema.edges` match the desired set."

## Input spec (from `tasks.md`)

| Field | Required | Notes |
|---|---|---|
| `source` | yes | Trigger ID (e.g., `trigger_1`) or Stage ID. Resolved from `id-map.json`. |
| `target` | yes | Stage ID. Resolved from `id-map.json`. Never an ExceptionStage — see Guardrails. |
| `label` | no | Display label on the connector. Omit the key from `data` when unset. |
| `sourceHandle` direction | no | `right` (default) \| `left` \| `top` \| `bottom` |
| `targetHandle` direction | no | `left` (default) \| `right` \| `top` \| `bottom` |
| `zIndex` | no | Integer. Omit the key entirely when unset. |

## Guardrails (enforce before writing)

1. **Both endpoints exist in `schema.nodes`.** Match the CLI's pre-check (`cli/packages/case-tool/src/commands/edges.ts:99-123`). If either `source` or `target` is missing, halt — do not write a dangling edge.
2. **Neither endpoint is an `case-management:ExceptionStage`.** Exception stages have no edges (see [`planning.md` § Wiring Constraints](planning.md#wiring-constraints)). They are reached via an interrupting `stage-entry-conditions` rule and exited via a `return-to-origin` `stage-exit-conditions` rule. Reject the write and flag to the user.
3. **`target` is not a Trigger.** Edges always flow into a Stage (regular Stage only).
4. **No duplicate edge with the same `source`+`target` pair** unless the sdd.md explicitly declares parallel edges. Warn if one already exists.

## ID generation

- Prefix: `edge_`
- Suffix length: 6
- Algorithm: per [`case-editing-operations-json.md § ID Generation`](../../case-editing-operations-json.md#id-generation)

Record `T<n> → edge_xxxxxx` in `id-map.json` for the audit trail, even though no downstream node references edges by ID.

## Edge-type inference

```text
sourceNode = schema.nodes.find(n => n.id === source)
edgeType   = sourceNode.type === "case-management:Trigger"
             ? "case-management:TriggerEdge"
             : "case-management:Edge"
```

Matches `cli/packages/case-tool/src/commands/edges.ts:44-50`. Do NOT accept a caller-supplied `type` — always derive it.

## Handle strings

Exactly **four underscores** each side:

```text
sourceHandle = `${source}____source____${sourceDir}`   # sourceDir default: "right"
targetHandle = `${target}____target____${targetDir}`   # targetDir default: "left"
```

## Recipe — Add

Append this object to `schema.edges`. CLI uses `.push()` — always append, never prepend (differs from stages which uses `.unshift()`).

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

Mirror CLI exactly — `JSON.stringify` drops `undefined` values, so omitted inputs yield absent keys:

| Input | Emission |
|---|---|
| `label` unset | Omit the `label` key; emit `data: {}` |
| `zIndex` unset | Omit the `zIndex` key entirely |
| `sourceHandle` direction unset | Still emit the key with default `right` |
| `targetHandle` direction unset | Still emit the key with default `left` |

Key insertion order (CLI output, preserved by `JSON.stringify(..., null, 4)`):

```text
id, source, target, sourceHandle, targetHandle, [zIndex], data, type
```

The golden diff normalizer sorts keys alphabetically — so exact insertion order is cosmetic for equivalence.

## Recipe — Edit

Find the edge by `id` in `schema.edges` and mutate in place:

| Field | Mutable | Notes |
|---|---|---|
| `id` | no | Immutable. |
| `source` | no | Immutable. To rewire, remove + re-add. |
| `target` | no | Immutable. To rewire, remove + re-add. |
| `type` | no | Derived from `source`. Immutable. |
| `data.label` | yes | Set or clear. To clear, `delete edge.data.label` (don't set to `null`). |
| `sourceHandle` | yes | Re-construct with new direction, keep same `source` ID. |
| `targetHandle` | yes | Re-construct with new direction, keep same `target` ID. |
| `zIndex` | yes | Set or `delete` to clear. |

> To re-wire an edge (change `source` or `target`), **remove and re-add**. This matches the CLI contract (`edges edit` rejects source/target changes) and preserves the invariant that `sourceHandle`/`targetHandle` always reference the current endpoints.

## Recipe — Remove

```text
schema.edges = schema.edges.filter(e => e.id !== edgeId)
```

Nothing references edges by ID in `caseplan.json`, so no cascade cleanup is needed. A stage removal still cascades to its edges — that logic lives in the stages JSON recipe (`Delete a node` in [`case-editing-operations-json.md`](../../case-editing-operations-json.md#delete-a-node)), not here.

## Semantic position

Edges live in the top-level `schema.edges` array. CLI appends (`.push()`) — direct-JSON-write matches: always append new edges to the end.

## Post-write validation

After writing, confirm:

- `schema.edges` contains the new edge with the generated ID
- `edges[].type` matches the inference (`TriggerEdge` iff source is a Trigger)
- `edges[].sourceHandle` and `edges[].targetHandle` use exactly 4 underscores each side
- `edges[].source` and `edges[].target` resolve to existing `schema.nodes` entries
- `edges[].data.label` is present iff the T-entry declared a label
- `edges[].zIndex` is present iff the T-entry declared one

Run `uip maestro case validate <file> --output json` after all edges for this plugin's batch are added.

## Known CLI divergences

None. Direct-JSON-write is a structural mirror of `edges add`. `JSON.stringify`'s drop-undefined behavior is reproduced by omitting keys for unset optional fields.

The one subtle point: CLI `edges edit` refuses to touch `source`/`target`. Direct-JSON-write honors the same contract by documenting them as immutable — even though the JSON format itself imposes no such constraint.

## Compatibility

Captured against CLI version `0.1.21`.

- [x] **Golden parity (ad-hoc):** manual side-by-side comparison of `uip maestro case edges add` output against direct-JSON-write output passed after ID normalization at the time this plugin was migrated.
- [ ] **Validation parity:** both outputs produce the same set of validation errors/warnings — not yet run against the installed binary
- [ ] **Downstream CLI mutation append:** `uip maestro case edges edit <json-written-edge-id>` and `uip maestro case edges remove <json-written-edge-id>` both succeed — not yet exercised
- [ ] **Round-trip:** CLI-written edge coexists with direct-JSON-written edge in the same file; validate passes — not yet exercised
- [ ] **Studio Web render:** `uip solution upload` and visual confirmation — not yet exercised
