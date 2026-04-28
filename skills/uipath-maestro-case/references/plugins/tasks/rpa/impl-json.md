# rpa task — Implementation (Direct JSON Write)

> **Phase split.** Runs across both phases. Phase 2a writes shape: full `data.inputs[]` schema from `tasks describe`, each `value` empty (`""`). Phase 2b binds values via [`../../variables/io-binding/impl-json.md`](../../variables/io-binding/impl-json.md). See [`../../../phased-execution.md`](../../../phased-execution.md).

Cross check the RPA task metadata via CLI, then write the task directly into `caseplan.json`. Field discovery and reference resolution are done during [planning](planning.md) — implementation reads resolved values from `tasks.md`. Shape is identical to `process` except `type: "rpa"`.

## Task JSON Shape

> **ID and elementId format.** Task `id` is `t` + 8 random chars. `elementId` is the composite `${stageId}-${taskId}`.

```json
{
  "id": "tQ2pVx7Lm",
  "type": "rpa",
  "displayName": "Extract Invoice Data",
  "elementId": "Stage_aB3kL9-tQ2pVx7Lm",
  "isRequired": true,
  "shouldRunOnlyOnce": true,
  "data": {
    "name": "InvoiceExtractor",
    "folderPath": "Finance",
    "inputs": [ /* from planning enrichment */ ],
    "outputs": [ /* from planning enrichment */ ],
    "context": { "taskTypeId": "b2c3d4e5-6789-01ab-cdef-234567890abc" }
  }
}
```

## All Attributes

Same shape as `ProcessTask` — see [process/impl-json.md § All Attributes](../process/impl-json.md#all-attributes). Only difference:

- `type` is `"rpa"` (never `"process"`, even though the registry entry shares the process registry)

## Procedure

**Step 0 — Get enriched metadata + outputs:**

Run `tasks describe` against the resolved `entityKey` and save the JSON response — this is the source of truth for `data.inputs[]` / `data.outputs[]` in Step 1. Use `--type rpa` even though the registry entry shares the process registry.

```bash
uip maestro case tasks describe --type rpa --id "<entityKey>" --output json
```

Capture the response (input/output schema with names, types, and ids). If `tasks describe` fails or returns no schema, fall back to the planning-captured schema from `tasks.md`; if that is also missing, treat the task as skeleton per [skeleton-tasks.md](../../../skeleton-tasks.md).

**Step 1 — Write task with populated data:**

1. Generate task ID: `t` + 8 alphanumeric chars (unique across all tasks)
2. Generate elementId: `<stageId>-<taskId>`
3. Set top-level fields (`type: "rpa"`, `displayName`, `isRequired`, `shouldRunOnlyOnce`) from tasks.md per the Task JSON Shape above
4. Set `data.name` from tasks.md `name`
5. Set `data.folderPath` from tasks.md `folder-path`
6. Set `data.context.taskTypeId` to the `entityKey` from `tasks.md` (captured during planning — RPA tasks share the process registry per [planning.md § Registry Resolution](planning.md))
7. Write `data.inputs[]` / `data.outputs[]` using the schema captured in Step 0 (falling back to the planning-captured schema in tasks.md if Step 0 was unavailable). Each input is `{ name, type, id, var, elementId, value: "" }`; each output is `{ name, type, id, var, value, source, target, elementId }`. See [variables/io-binding/impl-json.md](../../variables/io-binding/impl-json.md) for shape details.
8. Write the task to the target stage's `tasks[]` array (in its own task set / lane)

> **Handled elsewhere.** Input value bindings happen in outer-workflow Step 9 — see [variables/io-binding/impl-json.md](../../variables/io-binding/impl-json.md). Entry conditions are added in Step 10.

> **Do not flip to `type: "process"`** based on where the `entityKey` was found. The `rpa` vs `process` distinction comes from the sdd.md intent, not from the registry.

## Post-Write Verification

Confirm the task exists in the correct stage with:

- `type: "rpa"` (NOT `"process"`)
- `data.context.taskTypeId` non-empty (unless intentionally skeleton)
- `data.inputs` and `data.outputs` populated from the planning-captured schema
