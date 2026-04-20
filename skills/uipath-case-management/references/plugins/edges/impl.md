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
  --source "trig0000001" \
  --target "stg00000001" \
  --label "Start" \
  --output json
```

## Example — Stage → next stage with label

```bash
uip maestro case edges add caseplan.json \
  --source "stg00000001" \
  --target "stg00000002" \
  --label "Approved" \
  --output json
```

## Example — Stage → exception stage with custom handles

```bash
uip maestro case edges add caseplan.json \
  --source "stg00000001" \
  --target "stg_exception_id" \
  --label "Rejected" \
  --source-handle bottom \
  --target-handle top \
  --output json
```

## Resulting JSON Shape

### TriggerEdge (Trigger → Stage)

```json
{
  "id": "edg00000001",
  "type": "case-management:TriggerEdge",
  "source": "trig0000001",
  "target": "stg00000001",
  "sourceHandle": "trig0000001____source____right",
  "targetHandle": "stg00000001____target____left",
  "data": { "label": "Start" }
}
```

### Edge (Stage → Stage)

```json
{
  "id": "edg00000002",
  "type": "case-management:Edge",
  "source": "stg00000001",
  "target": "stg00000002",
  "sourceHandle": "stg00000001____source____right",
  "targetHandle": "stg00000002____target____left",
  "data": { "label": "Approved" }
}
```

Handle values are formatted automatically as `<nodeId>____source____<direction>` (source) or `<nodeId>____target____<direction>` (target).

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
