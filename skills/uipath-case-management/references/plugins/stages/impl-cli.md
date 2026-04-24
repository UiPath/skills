# stages — CLI Implementation

Authoritative when the matrix in [`case-editing-operations.md`](../../case-editing-operations.md) lists `stages = CLI`. For the direct-JSON path (the current default for this plugin), see [`impl-json.md`](impl-json.md).

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

There is **no `--is-required` flag**. `isRequired` from `tasks.md` is consumed by later case-exit-condition calls, not by `stages add` itself. The direct-JSON path fills this gap explicitly — see [`impl-json.md` § Known CLI divergences](impl-json.md#known-cli-divergences).

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

> **ID format.** Stage IDs are `Stage_` + 6 random chars from `[A-Za-z0-9]` (e.g. `Stage_aB3kL9`). Exception stages share the same `Stage_` prefix. See [case-schema.md](../../case-schema.md) for the full ID table.
>
> **Position is stateful.** The CLI computes `position = { x: 100 + existingStageCount * 500, y: 200 }` by counting stages already in `schema.nodes`. The first stage lands at `x: 100`, the second at `x: 600`, the third at `x: 1100`, etc.
>
> **Render fields are required.** The CLI hard-codes `style`, `measured`, `width`, `zIndex`, `data.parentElement`, `data.isInvalidDropTarget`, `data.isPendingParent`. All must be present for Studio Web to render correctly.

### Regular stage

```json
{
  "id": "Stage_aB3kL9",
  "type": "case-management:Stage",
  "position": { "x": 100, "y": 200 },
  "style": { "width": 304, "opacity": 0.8 },
  "measured": { "width": 304, "height": 128 },
  "width": 304,
  "zIndex": 1001,
  "data": {
    "label": "PO Receipt & Triage",
    "description": "Receive incoming POs and classify for downstream processing",
    "parentElement": { "id": "root", "type": "case-management:root" },
    "isInvalidDropTarget": false,
    "isPendingParent": false,
    "tasks": []
  }
}
```

> **Regular Stage has no `entryConditions`/`exitConditions` at creation time.** The CLI's `stages add` does not initialize these fields for `case-management:Stage`; only `ExceptionStage` gets empty arrays upfront. Regular stages gain these fields later when `stage-entry-conditions add` / `stage-exit-conditions add` runs against them.

### Exception stage

Same top-level render fields as regular stage. Adds `entryConditions` and `exitConditions` to `data`:

```json
{
  "id": "Stage_cD4mNt",
  "type": "case-management:ExceptionStage",
  "position": { "x": 600, "y": 200 },
  "style": { "width": 304, "opacity": 0.8 },
  "measured": { "width": 304, "height": 128 },
  "width": 304,
  "zIndex": 1001,
  "data": {
    "label": "Exception Handling",
    "description": "Fallback handler for POs that fail classification",
    "parentElement": { "id": "root", "type": "case-management:root" },
    "isInvalidDropTarget": false,
    "isPendingParent": false,
    "tasks": [],
    "entryConditions": [],
    "exitConditions": []
  }
}
```

Schema-level differences from regular Stage:
- `type` is `case-management:ExceptionStage`
- `data.entryConditions: []` and `data.exitConditions: []` are present (initialized empty by the CLI)
- `slaRules` may be added later by `sla rules add` — not emitted at `stages add` time

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
