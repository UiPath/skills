# stages — JSON Implementation

Cross-cutting caseplan.json editing mechanics live in [`caseplan-editing.md`](../../caseplan-editing.md).

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
- Algorithm: per [`caseplan-editing.md § ID Generation`](../../caseplan-editing.md#id-generation)

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

Append this object to `schema.nodes`:

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

**Do not initialize `entryConditions` or `exitConditions` on a regular Stage at creation time.** Those fields are initialized only for `ExceptionStage`. Regular stages acquire them later via the stage-entry-conditions / stage-exit-conditions plugins, which create and append to `data.entryConditions` / `data.exitConditions` — do not create those keys here.

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

The new node is added to the top-level `schema.nodes` array. Both append and prepend are valid for the frontend. Append for simpler diffs.

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

## Design notes

- **`data.isRequired` is always emitted.** Always write `isRequired: <bool>` — downstream `required-stages-completed` logic needs an explicit value. Default to `false` when sdd.md does not specify.

## Validation

- [x] **Structural validity:** `uip maestro case validate` passes on output (with the expected failure profile for a stages-only fragment with no edges/tasks — full validation runs once after the full build per SKILL.md Rule #20).
- [ ] **Studio Web render:** `uip solution upload` and visual confirmation — not yet exercised.
