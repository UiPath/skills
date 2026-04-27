# edges — Implementation

## CLI Command

```bash
uip maestro case edges add <file> \
  --source "<source-id>" \
  --target "<target-id>" \
  --label "<label>" \
  --source-handle <right|left|top|bottom> \
  --target-handle <right|left|top|bottom> \
  --z-index <n> \
  --output json
```

### Required flags

| Flag | Required | Notes |
|------|----------|-------|
| `--source` | yes | Trigger ID or stage ID |
| `--target` | yes | Stage ID |
| `--label` | no | Display label. |
| `--source-handle` | no | Default: `right` |
| `--target-handle` | no | Default: `left` |
| `--z-index` | no | Visual stacking order |

Edge type is inferred — do not pass a `--type` flag.

## Translation from tasks.md

- `source` name → ID via trigger-ID (from T01 and any triggers plugin) or stage capture map.
- `target` name → ID via stage capture map.

## Example — Trigger → first stage

```bash
uip maestro case edges add caseplan.json \
  --source "trigger_xY2mNp" \
  --target "Stage_aB3kL9" \
  --label "Start" \
  --output json
```

## Example — Stage → next stage with label

```bash
uip maestro case edges add caseplan.json \
  --source "Stage_aB3kL9" \
  --target "Stage_cD4mNt" \
  --label "Approved" \
  --output json
```

## Example — Stage → exception stage with custom handles

```bash
uip maestro case edges add caseplan.json \
  --source "Stage_aB3kL9" \
  --target "Stage_eF5pRk" \
  --label "Rejected" \
  --source-handle bottom \
  --target-handle top \
  --output json
```

## Resulting JSON Shape

> **ID format.** Edge `id` is `edge_` + 6 random chars (e.g. `edge_Qz7hVr`). See [case-schema.md](../../case-schema.md) for the full ID table.
>
> **Handle format.** Exactly **four underscores** on each side of `source` / `target`: `${nodeId}____source____${direction}` / `${nodeId}____target____${direction}`. Directions: `right`, `left`, `top`, `bottom`. Defaults: source=`right`, target=`left`.
>
> **`zIndex`** is omitted unless explicitly set via `--z-index`.

### TriggerEdge (Trigger → Stage)

```json
{
  "id": "edge_Qz7hVr",
  "type": "case-management:TriggerEdge",
  "source": "trigger_xY2mNp",
  "target": "Stage_aB3kL9",
  "sourceHandle": "trigger_xY2mNp____source____right",
  "targetHandle": "Stage_aB3kL9____target____left",
  "data": { "label": "Start" }
}
```

### Edge (Stage → Stage)

```json
{
  "id": "edge_pK2mLq",
  "type": "case-management:Edge",
  "source": "Stage_aB3kL9",
  "target": "Stage_cD4mNt",
  "sourceHandle": "Stage_aB3kL9____source____right",
  "targetHandle": "Stage_cD4mNt____target____left",
  "data": { "label": "Approved" }
}
```

Edge type is inferred from the source node: Trigger source → `TriggerEdge`; Stage source → `Edge`.

## Post-Add Validation

Capture `EdgeId` from `--output json`. Rarely needed downstream (nothing references edges by ID), but useful for the audit trail in `registry-resolved.json`.

Confirm in `caseplan.json`:

- `edges[].source` matches the source ID
- `edges[].target` matches the target ID
- `edges[].type` is `case-management:TriggerEdge` when source is a Trigger, else `case-management:Edge`
- `edges[].data.label` matches what you passed

## Editing Existing Edges

```bash
uip maestro case edges edit <file> <edge-id> \
  --label "<new-label>" \
  --source-handle <direction> \
  --target-handle <direction> \
  --z-index <n>
```

At least one flag required. Source and target are immutable — to rewire, `remove` + re-`add`.

## Removing Edges

```bash
uip maestro case edges remove <file> <edge-id>
```

Note: removing a stage (via `stages remove`) automatically cascades to connected edges. Only `edges remove` directly when you need to change wiring without touching the stage.
