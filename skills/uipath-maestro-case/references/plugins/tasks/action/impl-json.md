# action task — Implementation (Direct JSON Write)

> **Use the `uipath-human-in-the-loop` skill for HITL action tasks.** It owns the full implementation reference for Case HITL — JSON shape, field schema design, CLI opt-in (`uip case hitl add`), and downstream output access. See [hitl-casetask-action.md](../../../../../uipath-human-in-the-loop/references/hitl-casetask-action.md). The guide below covers the raw JSON shape for direct writes.

> **Phase split.** Phase 2 writes shape with empty input values. Phase 3 binds values per [io-binding/impl-json.md](../../variables/io-binding/impl-json.md). See [phased-execution.md](../../../phased-execution.md).

## Task JSON Shape

```json
{
  "id": "ty5UcykfU",
  "type": "action",
  "displayName": "Review Purchase Order",
  "elementId": "Stage_aB3kL9-ty5UcykfU",
  "isRequired": true,
  "shouldRunOnlyOnce": false,
  "data": {
    "taskTitle": "Please review this PO and approve or reject",
    "priority": "High",
    "recipient": "approver@corp.com",
    "actionCatalogName": "<deploymentTitle>",
    "labels": "<labels string>",
    "name": "=bindings.bG0SraLpg",
    "folderPath": "=bindings.bH1iJK2lm",
    "inputs": [],
    "outputs": []
  }
}
```

- `id`: `t` + 8 alphanumeric chars. `elementId`: `${stageId}-${taskId}`.
- `data.name` / `data.folderPath` MUST be `=bindings.<id>` references — never literals.

## Action-Specific Fields

| Field | Notes |
|---|---|
| `data.taskTitle` | Required, even on skeletons. Validator rejects empty. |
| `data.priority` | `"Low"` \| `"Medium"` (default) \| `"High"` \| `"Critical"` |
| `data.recipient` | `ActionTaskAssignee` object: `{ "Type": <int>, "Value": "<id-or-email>" }`. Omit for group/role assignment. |
| `data.actionCatalogName` | `deploymentTitle` from tasks.md |
| `data.labels` | Label set from tasks.md |

`recipient.Type` values: `0` = user ID, `1` = group ID, `2` = email address, `3` = `"=vars.<varId>"` for runtime resolution. Email recipients always use Type `2`.

## Procedure

**Step 0 — Get inputs/outputs schema:**

```bash
uip maestro case tasks describe --type action --id "<action-app-id>" --output json
```

Fallback: planning-captured schema from tasks.md. If unavailable, skeleton per [skeleton-tasks.md](../../../skeleton-tasks.md).

**Step 1 — Root-level bindings:**

Create 2 entries in `root.data.uipath.bindings[]` per [bindings/impl-json.md](../../variables/bindings/impl-json.md):

| `propertyAttribute` | `resource` | `resourceSubType` | `default` |
|---|---|---|---|
| `"name"` | `"app"` | — | `name` from tasks.md |
| `"folderPath"` | `"app"` | — | `folder-path` from tasks.md |

Both share `resourceKey` = `<folderPath>.<name>`. ID: `b` + 8 chars. Deduplicate by `default + resource + resourceKey`.

**Step 2 — Write task:**

1. Generate `id` (`t` + 8 chars) and `elementId` (`<stageId>-<taskId>`)
2. Set `data.taskTitle`, `data.priority`, `data.recipient`, `data.actionCatalogName`, `data.labels` from tasks.md
3. Set `data.name` = `=bindings.<nameBindingId>`, `data.folderPath` = `=bindings.<folderPathBindingId>`
4. Write `data.inputs[]` / `data.outputs[]` from Step 0 schema. Each input: `{ name, type, id, var, elementId, value: "" }`. Each output: `{ name, type, id, var, value, source, target, elementId }`.
5. Append to target stage's `tasks[laneIndex][]`

> Entry conditions added in Step 10. Input value bindings in Phase 3 per [io-binding/impl-json.md](../../variables/io-binding/impl-json.md).

## Post-Write Verification

- `type: "action"`
- `data.taskTitle` non-empty
- `data.name` and `data.folderPath` start with `=bindings.`
- `root.data.uipath.bindings[]` has 2 entries: `resource: "app"`, no `resourceSubType`, `propertyAttribute` = `name` / `folderPath`
- `data.inputs` and `data.outputs` populated (unless skeleton)
- `id` captured in `id-map.json`
