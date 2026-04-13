# Stage — Implementation

## Stage Node Skeleton

```json
{
  "id": "Stage_<6chars>",
  "type": "case-management:Stage",
  "position": { "x": 100, "y": 200 },
  "style": { "width": 304, "opacity": 0.8 },
  "measured": { "width": 304, "height": 128 },
  "width": 304,
  "zIndex": 1001,
  "data": {
    "label": "<Stage Name>",
    "parentElement": { "id": "root", "type": "case-management:root" },
    "isInvalidDropTarget": false,
    "isPendingParent": false,
    "description": "<stage description>",
    "isRequired": true,
    "tasks": [],
    "entryConditions": [],
    "exitConditions": [],
    "slaRules": []
  }
}
```

## Fixed Fields

These fields are always the same — do not change them:

| Field | Always |
|---|---|
| `style` | `{ "width": 304, "opacity": 0.8 }` |
| `measured` | `{ "width": 304, "height": 128 }` |
| `width` | `304` |
| `zIndex` | `1001` |
| `parentElement` | `{ "id": "root", "type": "case-management:root" }` |
| `isInvalidDropTarget` | `false` |
| `isPendingParent` | `false` |

## Position Layout

Place stages left-to-right along the main flow:

| Stage index | `x` | `y` |
|---|---|---|
| 1st stage | `100` | `200` |
| 2nd stage | `600` | `200` |
| 3rd stage | `1100` | `200` |
| Nth stage | `100 + (N-1) × 500` | `200` |

Exception stages branch vertically below the stage that triggers them:
- Same `x` as the triggering stage
- `y`: `600` (or lower to avoid overlap)

## Reading from Planning (tasks.md)

```
## T02: Create stage "Stage 1"
- isRequired: true
- description: Performs initial processing...
```

Maps to:
- `data.label` ← `"Stage 1"`
- `data.isRequired` ← `true`
- `data.description` ← the description string
- `data.tasks` ← `[]` (populated when tasks are added)
- `data.entryConditions` / `data.exitConditions` ← `[]` (populated from condition tasks)
