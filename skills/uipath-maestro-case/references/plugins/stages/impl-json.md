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
| Stage kind | yes | `regular` or `exception` — determined by the T-entry plugin (`Create stage …` vs `Create exception stage …`) |

## ID generation

- Prefix: `Stage_` (same for regular and exception stages)
- Suffix length: 6
- Algorithm: per [`case-editing-operations.md § ID Generation`](../../case-editing-operations.md#id-generation)

Record `T<n> → Stage_xxxxxx` in `id-map.json` for downstream cross-reference.

## Position (stateful)

**Before writing**, count existing stages:

```text
existingStageCount = schema.nodes.filter(n =>
  n.type === "case-management:Stage" ||
  n.type === "case-management:ExceptionStage"
).length
```

Then compute:

```text
position.x = 100 + existingStageCount * 500
position.y = 200
```

Trigger nodes are NOT counted.

## Recipe — Regular Stage

Append (or prepend) this object to `schema.nodes` — both orderings are valid for the frontend:

```json
{
  "id": "<Stage_xxxxxx>",
  "type": "case-management:Stage",
  "position": { "x": <computed>, "y": 200 },
  "style": { "width": 304, "opacity": 0.8 },
  "measured": { "width": 304, "height": 128 },
  "width": 304,
  "zIndex": 1001,
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

**Do not initialize `entryConditions` or `exitConditions` on a regular Stage at creation time.** Regular stages acquire those keys later when the condition plugins (stage-entry-conditions / stage-exit-conditions) write them — do not create the keys here.

## Recipe — Exception Stage

Same as regular, with `type: "case-management:ExceptionStage"` and two additional `data` fields initialized empty:

```json
{
  "id": "<Stage_xxxxxx>",
  "type": "case-management:ExceptionStage",
  "position": { "x": <computed>, "y": 200 },
  "style": { "width": 304, "opacity": 0.8 },
  "measured": { "width": 304, "height": 128 },
  "width": 304,
  "zIndex": 1001,
  "data": {
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

The new node is added to the top-level `schema.nodes` array. Append or prepend — both are valid for the frontend. Append is preferred for simpler diffing.

## Post-write validation

After writing, confirm:

- `schema.nodes` contains the new node with the generated ID
- `nodes[].type` is `case-management:Stage` or `case-management:ExceptionStage` per the intended kind
- `nodes[].data.label` matches the T-entry's displayName
- `nodes[].data.isRequired` is present and boolean
- All render fields (`style`, `measured`, `width`, `zIndex`, `data.parentElement`, `data.isInvalidDropTarget`, `data.isPendingParent`) are present
- For ExceptionStage: `data.entryConditions: []` and `data.exitConditions: []` are present (initialized as empty arrays at creation time)
- For regular Stage at creation time: `data.entryConditions` / `data.exitConditions` are absent — the conditions plugins will create and populate them later if the sdd.md calls for it

Run `uip maestro case validate <file> --output json` after all stages for this plugin's batch are added.

