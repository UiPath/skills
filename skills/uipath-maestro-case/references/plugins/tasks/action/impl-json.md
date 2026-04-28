# action task — Implementation (Direct JSON Write)

> **Phase split.** Phase 2a writes shape with empty input values. Phase 2b binds values per [io-binding/impl-json.md](../../variables/io-binding/impl-json.md). See [phased-execution.md](../../../phased-execution.md).

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
| `data.recipient` | User email string. Omit for group/role assignment. |
| `data.actionCatalogName` | `deploymentTitle` from tasks.md |
| `data.labels` | Label set from tasks.md |

`recipient` as object (`ActionTaskAssignee`): `{ Type: 0|1|2|3, Value: "<id-or-email>" }`. Type 3 = `"=vars.<varId>"` for runtime resolution.

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

> Entry conditions added in Step 10. Input value bindings in Phase 2b per [io-binding/impl-json.md](../../variables/io-binding/impl-json.md).

## Post-Write Verification

- `type: "action"`
- `data.taskTitle` non-empty
- `data.name` and `data.folderPath` start with `=bindings.`
- `root.data.uipath.bindings[]` has 2 entries: `resource: "app"`, no `resourceSubType`, `propertyAttribute` = `name` / `folderPath`
- `data.inputs` and `data.outputs` populated (unless skeleton)
- `id` captured in `id-map.json`
