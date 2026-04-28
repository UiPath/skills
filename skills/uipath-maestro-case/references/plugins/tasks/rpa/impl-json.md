# rpa task — Implementation (Direct JSON Write)

> **Phase split.** Phase 2a writes shape with empty input values. Phase 2b binds values per [io-binding/impl-json.md](../../variables/io-binding/impl-json.md). See [phased-execution.md](../../../phased-execution.md).

## Task JSON Shape

```json
{
  "id": "tQ2pVx7Lm",
  "type": "rpa",
  "displayName": "Extract Invoice Data",
  "elementId": "Stage_aB3kL9-tQ2pVx7Lm",
  "isRequired": true,
  "shouldRunOnlyOnce": true,
  "data": {
    "name": "=bindings.bG0SraLpg",
    "folderPath": "=bindings.bH1iJK2lm",
    "inputs": [],
    "outputs": []
  }
}
```

- `id`: `t` + 8 alphanumeric chars. `elementId`: `${stageId}-${taskId}`.
- `data.name` / `data.folderPath` MUST be `=bindings.<id>` references — never literals.
- **Do not flip to `type: "process"`** based on registry. The `rpa` vs `process` distinction comes from sdd.md intent.

## Procedure

**Step 0 — Get inputs/outputs schema:**

```bash
uip maestro case tasks describe --type rpa --id "<entityKey>" --output json
```

Fallback: planning-captured schema from tasks.md. If unavailable, skeleton per [skeleton-tasks.md](../../../skeleton-tasks.md).

**Step 1 — Root-level bindings:**

Create 2 entries in `root.data.uipath.bindings[]` per [bindings/impl-json.md](../../variables/bindings/impl-json.md):

| `propertyAttribute` | `resource` | `resourceSubType` | `default` |
|---|---|---|---|
| `"name"` | `"process"` | — | `name` from tasks.md |
| `"folderPath"` | `"process"` | — | `folder-path` from tasks.md |

Both share `resourceKey` = `<folderPath>.<name>`. ID: `b` + 8 chars. Deduplicate by `default + resource + resourceKey`.

**Step 2 — Write task:**

1. Generate `id` (`t` + 8 chars) and `elementId` (`<stageId>-<taskId>`)
2. Set `data.name` = `=bindings.<nameBindingId>`, `data.folderPath` = `=bindings.<folderPathBindingId>`
3. Write `data.inputs[]` / `data.outputs[]` from Step 0 schema. Each input: `{ name, type, id, var, elementId, value: "" }`. Each output: `{ name, type, id, var, value, source, target, elementId }`.
4. Append to target stage's `tasks[laneIndex][]`

> Entry conditions added in Step 10. Input value bindings in Phase 2b per [io-binding/impl-json.md](../../variables/io-binding/impl-json.md).

## Post-Write Verification

- `type: "rpa"` (NOT `"process"`)
- `data.name` and `data.folderPath` start with `=bindings.`
- `root.data.uipath.bindings[]` has 2 entries: `resource: "process"`, no `resourceSubType`, `propertyAttribute` = `name` / `folderPath`
- `data.inputs` and `data.outputs` populated (unless skeleton)
- `id` captured in `id-map.json`
