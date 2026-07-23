---
direct-json: supported
---

# stages — JSON Implementation

Cross-cutting direct-JSON rules live in [`case-editing-operations.md`](../../case-editing-operations.md).

## Input spec (from `tasks.md`)

| Field | Required | Notes |
|---|---|---|
| `displayName` (from T-entry title) | yes | Stage label |
| `description` | yes | Always emit, sourced from the T-entry's description field in `sdd.md`. |
| `isRequired` | yes | From `sdd.md`; fall back to `false` when the T-entry does not specify. Consumed by later case-exit rule `required-stages-completed`. |
| Stage kind | yes | `primary` or `secondary` — determined by the T-entry plugin (`Create stage …` vs `Create secondary stage …`) |

## ID generation

- Prefix: `Stage_` (same for primary and secondary stages)
- Suffix length: 6
- Algorithm: per [`case-editing-operations.md § ID Generation`](../../case-editing-operations.md#id-generation)

Record `T<n> → Stage_xxxxxx` in `id-map.json` for downstream cross-reference.

## Layout fields

Do NOT emit node-level `position`, `style`, `measured`, `width`, `height`, `zIndex` (Rule 18 layout-strip). FE auto-layouts on canvas load.

## Recipe — Primary Stage

Append (or prepend) this object to `nodes` — both orderings are valid for the frontend:

```json
{
  "id": "<Stage_xxxxxx>",
  "type": "case-management:Stage",
  "data": {
    "label": "<displayName>",
    "description": "<description from sdd.md>",
    "isRequired": <true|false from sdd.md; false if unspecified>,
    "parentElement": { "id": "root", "type": "case-management:root" },
    "isInvalidDropTarget": false,
    "isPendingParent": false,
    "tasks": []
  }
}
```

> **`parentElement.id` stays `"root"`** even though there is no `"root"` node on disk. The literal `"root"` is canvas-side — `transformCaseInMemoryJsonToDiskJson` keeps the reference intact.

**Do not initialize `entryConditions` or `exitConditions` on a primary Stage at creation time.** Primary stages acquire those keys later when the condition plugins (stage-entry-conditions / stage-exit-conditions) write them — do not create the keys here.

> **Do NOT author edges (Rule 20) — adding a stage node NEVER adds an edge.** Model an SDD "A → B" arrow as B's `entryConditions` (plus A's `exitConditions` when A diverges), never as an edge. See [stages/planning.md § Wiring constraints](planning.md).

## Recipe — Secondary Stage

Same as a primary Stage, with `data.stageType: "secondary"` and two additional `data` fields initialized empty:

```json
{
  "id": "<Stage_xxxxxx>",
  "type": "case-management:Stage",
  "data": {
    "stageType": "secondary",
    "label": "<displayName>",
    "description": "<description from sdd.md>",
    "isRequired": <true|false from sdd.md; false if unspecified>,
    "parentElement": { "id": "root", "type": "case-management:root" },
    "isInvalidDropTarget": false,
    "isPendingParent": false,
    "tasks": [],
    "entryConditions": [],
    "exitConditions": []
  }
}
```

## Semantic position

The new node is added to the top-level `nodes` array. Append or prepend — both are valid for the frontend. Append is preferred for simpler diffing.

## Post-write validation

After writing, confirm:

- `nodes` contains the new node with the generated ID
- `nodes[].type` is always `case-management:Stage`
- `nodes[].data.label` matches the T-entry's displayName
- `nodes[].data.isRequired` is present and boolean
- NO `position`, `style`, `measured`, `width`, `height`, `zIndex` at the node level (Rule 18). Only `data.parentElement`, `data.isInvalidDropTarget`, `data.isPendingParent` remain
- For a secondary stage: `data.stageType == "secondary"`, and `data.entryConditions: []` and `data.exitConditions: []` are present (initialized as empty arrays at creation time)
- For a primary Stage at creation time: `data.entryConditions` / `data.exitConditions` are absent — the conditions plugins will create and populate them later if the sdd.md calls for it
- **`schema.edges` is still `[]`** (Rule 20). If non-empty, an edge was authored in error: remove it per [case-editing-operations.md § Delete an edge](../../case-editing-operations.md#delete-an-edge--defensive-only) before proceeding.

Run `uip maestro case validate <file> --output json` after all stages for this plugin's batch are added.

