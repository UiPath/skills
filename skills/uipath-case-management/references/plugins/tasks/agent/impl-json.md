# agent task — Implementation (Direct JSON Write)

> **Phase split.** Runs across both phases. Phase 2a writes shape: full `data.inputs[]` schema from `tasks describe`, each `value` empty (`""`). Phase 2b binds values via [`../../variables/io-binding/impl-json.md`](../../variables/io-binding/impl-json.md). See [`../../../phased-execution.md`](../../../phased-execution.md).

Cross check the agent task metadata via CLI, then write the task directly into `caseplan.json`. Field discovery and reference resolution are done during [planning](planning.md) — implementation reads resolved values from `tasks.md`.

## Task JSON Shape

> **ID and elementId format.** Task `id` is `t` + 8 random chars. `elementId` is the composite `${stageId}-${taskId}`.

```json
{
  "id": "tH3kLmNp9",
  "type": "agent",
  "displayName": "Classify Purchase Order",
  "elementId": "Stage_aB3kL9-tH3kLmNp9",
  "isRequired": true,
  "shouldRunOnlyOnce": true,
  "data": {
    "name": "PO Classifier",
    "folderPath": "Shared",
    "inputs": [ /* from planning enrichment */ ],
    "outputs": [ /* from planning enrichment */ ],
    "context": { "taskTypeId": "a1b2c3d4-5678-90ab-cdef-1234567890ab" }
  }
}
```

## All Attributes

Same shape as `ProcessTask` — see [process/impl-json.md § All Attributes](../process/impl-json.md#all-attributes). Only differences:

- `type` is `"agent"` (not `"process"`)
- `data.name` resolves from the agent registry (captured in `tasks.md` during planning), not the process registry

## Procedure

**Step 0 — Get enriched metadata + outputs:**

Run `tasks describe` against the resolved `entityKey` and save the JSON response — this is the source of truth for `data.inputs[]` / `data.outputs[]` in Step 1. For agents with multiple element bindings, also pass `--element-id`.

```bash
uip maestro case tasks describe --type agent --id "<entityKey>" --output json
# multi-element agents:
uip maestro case tasks describe --type agent --id "<entityKey>" --element-id "<elementId>" --output json
```

Capture the response (input/output schema with names, types, and ids). If `tasks describe` fails or returns no schema, fall back to the planning-captured schema from `tasks.md`; if that is also missing, treat the task as skeleton per [skeleton-tasks.md](../../../skeleton-tasks.md).

**Step 1 — Write task with populated data:**

1. Generate task ID: `t` + 8 alphanumeric chars (unique across all tasks)
2. Generate elementId: `<stageId>-<taskId>`
3. Set top-level fields (`type: "agent"`, `displayName`, `isRequired`, `shouldRunOnlyOnce`) from tasks.md per the Task JSON Shape above
4. Set `data.name` from tasks.md `name`
5. Set `data.folderPath` from tasks.md `folder-path`
6. Set `data.context.taskTypeId` to the agent `entityKey` from `tasks.md` (captured during planning per [planning.md § Registry Resolution](planning.md))
7. Write `data.inputs[]` / `data.outputs[]` using the schema captured in Step 0 (falling back to the planning-captured schema in tasks.md if Step 0 was unavailable). Each input is `{ name, type, id, var, elementId, value: "" }`; each output is `{ name, type, id, var, value, source, target, elementId }`. See [variables/io-binding/impl-json.md](../../variables/io-binding/impl-json.md) for shape details.
8. Write the task to the target stage's `tasks[]` array (in its own task set / lane)

> **Handled elsewhere.** Input value bindings happen in outer-workflow Step 9 — see [variables/io-binding/impl-json.md](../../variables/io-binding/impl-json.md). Entry conditions are added in Step 10.

## Post-Write Verification

Confirm the task exists in the correct stage with:

- `type: "agent"`
- `data.context.taskTypeId` non-empty (unless intentionally skeleton)
- `data.inputs` and `data.outputs` populated from the planning-captured schema (if empty, planning enrichment is missing — return to planning to re-run discovery)
