# stages — Implementation

## CLI Command

```bash
uip maestro case stages add <file> \
  --label "<label>" \
  --type <stage|exception> \
  --description "<description>" \
  --output json
```

### Flags

| Flag | Required | Notes |
|------|----------|-------|
| `--label` | no (recommended) | Display label. If omitted, the CLI uses a default. |
| `--type` | no | `stage` (default) \| `exception`. The `trigger` value exists in the schema but is reserved for the auto-created trigger node — do not pass it manually. |
| `--description` | no | Free-form description. |

There is **no `--is-required` flag**. `isRequired` from `tasks.md` is consumed by later case-exit-condition calls, not by `stages add` itself.

## Example — Regular Stage

```bash
uip maestro case stages add caseplan.json \
  --label "PO Receipt & Triage" \
  --type stage \
  --description "Receive incoming POs and classify for downstream processing" \
  --output json
```

## Example — Exception / Secondary Stage

```bash
uip maestro case stages add caseplan.json \
  --label "Exception Handling" \
  --type exception \
  --description "Fallback handler for POs that fail classification" \
  --output json
```

## Resulting JSON Shape

### Regular stage

```json
{
  "id": "stg00000001",
  "type": "case-management:Stage",
  "position": { "x": 600, "y": 200 },
  "data": {
    "label": "PO Receipt & Triage",
    "description": "Receive incoming POs and classify for downstream processing",
    "tasks": [],
    "entryConditions": [],
    "exitConditions": []
  }
}
```

### Exception stage

```json
{
  "id": "stg00000002",
  "type": "case-management:ExceptionStage",
  "position": { "x": 1100, "y": 200 },
  "data": {
    "label": "Exception Handling",
    "description": "Fallback handler for POs that fail classification",
    "tasks": [],
    "entryConditions": [],
    "exitConditions": [],
    "slaRules": []
  }
}
```

The only schema-level difference is the `type` literal (`Stage` vs `ExceptionStage`) and the presence of a `slaRules` array on exception stages (always empty after `stages add`; populated manually or by future CLI support).

## Post-Add Validation

Capture `StageId` from the `--output json` response. Store in the capture map:

```
stage_name → stage_id
```

Used by:
- **Edges** — `--source`, `--target`, `--exit-to-stage-id`
- **Tasks** — `<stage-id>` positional arg on `tasks add` and `tasks add-connector`
- **Conditions** — `<stage-id>` on all `stage-*-conditions` and `task-entry-conditions` commands
- **SLA** — `--stage-id` on `sla set`, `sla escalation add`

Confirm in `caseplan.json`:
- `nodes[].id` matches the returned `StageId`
- `nodes[].type` is `case-management:Stage` or `case-management:ExceptionStage` per the intended type
- `nodes[].data.label` matches what you passed

## Editing Stage Labels

```bash
uip maestro case stages edit <file> <stage-id> --label "<new-label>" --output json
```

Only the `--label` is editable via `stages edit`. For other changes, `remove` + re-`add` (note: removing a stage also removes its connected edges — downstream wiring must be redone).

## Removing a Stage

```bash
uip maestro case stages remove <file> <stage-id>
```

Removes the stage and all its connected edges. Does **not** remove tasks from other stages that referenced this one via cross-task refs — re-validate all cross-task references after a stage removal.
