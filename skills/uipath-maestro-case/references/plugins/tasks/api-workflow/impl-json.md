# api-workflow task — Implementation (Direct JSON Write)

> **Phase split.** Phase 2 writes shape with empty input values. Phase 3 binds values per [io-binding/impl-json.md](../../variables/io-binding/impl-json.md). See [phased-execution.md](../../../phased-execution.md).

## Task JSON Shape

```json
{
  "id": "tK7nRs3Wp",
  "type": "api-workflow",
  "displayName": "Monitor Order Inbox",
  "elementId": "Stage_aB3kL9-tK7nRs3Wp",
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

## Procedure

**Step 0 — Get inputs/outputs schema:**

```bash
uip maestro case tasks describe --type api-workflow --id "<entityKey>" --output json
```

Fallback: planning-captured schema from tasks.md. If unavailable, placeholder per [placeholder-tasks.md](../../../placeholder-tasks.md).

**Step 1 — Root-level bindings:**

Read [bindings/impl-json.md § Full binding shape — non-connector tasks](../../variables/bindings/impl-json.md) for the canonical 7-field shape (all required — omitting any causes Studio Web render failure). Per-task overrides:

- `resource`: `"process"`
- `resourceSubType`: `"Api"`
- `name` / `folderPath` defaults: from `tasks.md` `name` / `folder-path` fields. `folder-path` is the resolved registry `folders[0].fullyQualifiedName` (per [planning.md § Registry Resolution](planning.md#registry-resolution)) — never the raw sdd.md "Folder", which may be a parent path and faults the job at runtime.

Dedup per [§ Deduplication](../../variables/bindings/impl-json.md).

**Step 2 — Write task:**

1. Generate `id` (`t` + 8 chars) and `elementId` (`<stageId>-<taskId>`)
2. Set `data.name` = `=bindings.<nameBindingId>`, `data.folderPath` = `=bindings.<folderPathBindingId>`
3. Write `data.inputs[]` / `data.outputs[]` from Step 0 schema. Each input: `{ name, type, id, var, elementId, value: "" }`. Each output: `{ name, type, id, var, value, source, target, elementId }`.

   **Output binding.** Apply [io-binding/impl-json.md § Output Binding Shapes](../../variables/io-binding/impl-json.md#output-binding-shapes). The Step 0 schema for this plugin is the `tasks describe` output (Step 0 above).
4. Append to target stage's `tasks[laneIndex][]`

> Entry conditions added in Step 10. Input value bindings in Phase 3 per [io-binding/impl-json.md](../../variables/io-binding/impl-json.md).

## Post-Write Verification

- `type: "api-workflow"`
- `data.name` and `data.folderPath` start with `=bindings.`
- the bindings array has 2 entries: `resource: "process"`, `resourceSubType: "Api"`, `propertyAttribute` = `name` / `folderPath`
- `data.inputs` and `data.outputs` populated (unless placeholder)
- `id` captured in `id-map.json`
