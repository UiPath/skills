---
direct-json: supported
---

# stages — JSON Implementation

Authoritative when the matrix in [`case-editing-operations.md`](../../case-editing-operations.md) lists `stages = JSON`. Cross-cutting direct-JSON rules live in [`case-editing-operations-json.md`](../../case-editing-operations-json.md). For the CLI fallback, see [`impl-cli.md`](impl-cli.md).

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
- Algorithm: per [`case-editing-operations-json.md § ID Generation`](../../case-editing-operations-json.md#id-generation)

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

Append (or prepend — CLI uses `.unshift()`) this object to `schema.nodes`:

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

**Do not initialize `entryConditions` or `exitConditions` on a regular Stage at creation time.** The CLI's `stages add` emits those fields only for `ExceptionStage`. Regular stages acquire them later via `stage-entry-conditions add` / `stage-exit-conditions add`, which create and append to `data.entryConditions` / `data.exitConditions` — do not create those keys here.

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

The new node is added to the top-level `schema.nodes` array. CLI prepends (`.unshift()`) — direct-JSON-write MAY prepend for byte-equivalence or append (both are valid for the frontend). Choose append for simpler diffing against evolving CLI output.

## Post-write validation

After writing, confirm:

- `schema.nodes` contains the new node with the generated ID
- `nodes[].type` is `case-management:Stage` or `case-management:ExceptionStage` per the intended kind
- `nodes[].data.label` matches the T-entry's displayName
- `nodes[].data.isRequired` is present and boolean
- All render fields (`style`, `measured`, `width`, `zIndex`, `data.parentElement`, `data.isInvalidDropTarget`, `data.isPendingParent`) are present
- For ExceptionStage: `data.entryConditions: []` and `data.exitConditions: []` are present (CLI initializes both as empty arrays at creation time)
- For regular Stage at creation time: `data.entryConditions` / `data.exitConditions` are absent — the conditions plugins will create and populate them later if the sdd.md calls for it

Run `uip maestro case validate <file> --output json` after all stages for this plugin's batch are added.

## Known CLI divergences

Direct-JSON-write is a superset of the CLI's `stages add`. The divergences below are deliberate — they fill gaps the CLI cannot express at stage creation time.

- **`data.isRequired` is always emitted.** `stages add` has no `--is-required` flag, so the CLI omits the key entirely. The JSON recipe always writes `isRequired: <bool>` because downstream `required-stages-completed` logic needs an explicit value and there is no other CLI path to set it at creation time. The golden diff normalizes `isRequired: false` ↔ absent so equivalence still holds.
- **CLI `.unshift()`s new stages** so most-recent-added appears first in `schema.nodes`. Direct-JSON-write matches this ordering for byte-closer diffs. Both append and prepend are semantically valid for the frontend.

## Compatibility

Captured against CLI version `0.1.21`. See [`docs/uipath-case-management/migration-fixtures/stages/`](../../../../../docs/uipath-case-management/migration-fixtures/stages/) for fixtures.

- [x] **Golden diff:** normalized `json-write-output.json` matches `cli-output.json` after ID normalization — `docs/uipath-case-management/migration-fixtures/stages/diff.sh` passes
- [x] **Validation parity:** both outputs produce the same set of 3 errors + 3 warnings from `uip maestro case validate` (the expected failure profile for a stages-only fragment with no edges/tasks)
- [ ] **Downstream CLI mutation append:** `uip maestro case edges add --source <json-written-stage-id>` and `uip maestro case tasks add <file> <json-written-stage-id>` both succeed — not yet exercised (edges plugin not migrated)
- [ ] **Round-trip:** CLI-written stage → direct-JSON-write adds a second stage → `uip maestro case validate` passes with only the expected failures — not yet exercised
- [ ] **Studio Web render:** `uip solution upload` and visual confirmation — not yet exercised
