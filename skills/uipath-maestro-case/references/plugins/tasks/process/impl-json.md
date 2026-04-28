# process task — Implementation (Direct JSON Write)

> **Phase split.** Runs across both phases. Phase 2a writes shape: full `data.inputs[]` schema from `tasks describe`, each `value` empty (`""`). Phase 2b binds values via [`../../variables/io-binding/impl-json.md`](../../variables/io-binding/impl-json.md). See [`../../../phased-execution.md`](../../../phased-execution.md).

Cross check the process task metadata via CLI, then write the task directly into `caseplan.json`. Field discovery and reference resolution are done during [planning](planning.md) — implementation reads resolved values from `tasks.md`.

## Task JSON Shape

> **ID and elementId format.** Task `id` is `t` + 8 random chars (e.g. `t8GQTYo8O`). `elementId` is the composite `${stageId}-${taskId}` (e.g. `Stage_aB3kL9-t8GQTYo8O`).

```json
{
  "id": "t8GQTYo8O",
  "type": "process",
  "displayName": "Run KYC",
  "elementId": "Stage_aB3kL9-t8GQTYo8O",
  "isRequired": true,
  "shouldRunOnlyOnce": true,
  "data": {
    "name": "KYC",
    "folderPath": "Shared",
    "inputs": [ /* from planning enrichment */ ],
    "outputs": [ /* from planning enrichment */ ],
    "context": { "taskTypeId": "f1b2c3d4-1234-5678-abcd-ef1234567890" }
  }
}
```

## All Attributes

Top-level fields:

| Field | Type | Notes |
|---|---|---|
| `id` | string | `t` + 8 alphanumeric chars (unique across all tasks) |
| `elementId` | string | Composite `${stageId}-${taskId}` |
| `type` | `"process"` | Discriminator — always `"process"` |
| `displayName` | string | Human-readable task name |
| `description` | string | Free-form task description |
| `isRequired` | boolean | Marks task as required for stage completion |
| `shouldRunOnlyOnce` | boolean | Prevents re-execution on stage re-entry |
| `skipCondition` | string | Expression that causes the task to be skipped |
| `entryConditions` | `TaskEntryCondition[]` | Entry condition rules (populated in Step 10) |
| `data` | object | Process-specific data (see below) |

`data` fields:

| Field | Type | Notes |
|---|---|---|
| `data.name` | string | Registry-resolved process name |
| `data.folderPath` | string | Orchestrator folder path |
| `data.inputs` | `UiPathVariable[]` | Populated from planning enrichment |
| `data.outputs` | `UiPathVariable[]` | Populated from planning enrichment |
| `data.context` | `UiPathVariable[]` | Carries the resolved `taskTypeId` |

## Procedure

**Step 0 — Get enriched metadata + outputs:**

Run `tasks describe` against the resolved `entityKey` and save the JSON response — this is the source of truth for `data.inputs[]` / `data.outputs[]` in Step 1. Use `processOrchestration` as the `--type` for `AGENTIC_PROCESS`; otherwise use `process`.

```bash
uip maestro case tasks describe --type process --id "<entityKey>" --output json
```

Capture the response (input/output schema with names, types, and ids). If `tasks describe` fails or returns no schema, fall back to the planning-captured schema from `tasks.md`; if that is also missing, treat the task as skeleton per [skeleton-tasks.md](../../../skeleton-tasks.md).

**Step 1 — Write task with populated data:**

1. Generate task ID: `t` + 8 alphanumeric chars (unique across all tasks)
2. Generate elementId: `<stageId>-<taskId>`
3. Set top-level fields (`type: "process"`, `displayName`, `isRequired`, `shouldRunOnlyOnce`) from tasks.md per the Task JSON Shape above
4. Set `data.name` from tasks.md `name`
5. Set `data.folderPath` from tasks.md `folder-path`
6. Set `data.context.taskTypeId` to the process `entityKey` from `tasks.md` (captured during planning per [planning.md § Registry Resolution](planning.md) — includes `AGENTIC_PROCESS` entries)
7. Write `data.inputs[]` / `data.outputs[]` using the schema captured in Step 0 (falling back to the planning-captured schema in tasks.md if Step 0 was unavailable). Each input is `{ name, type, id, var, elementId, value: "" }`; each output is `{ name, type, id, var, value, source, target, elementId }`. See [variables/io-binding/impl-json.md](../../variables/io-binding/impl-json.md) for shape details.
8. Write the task to the target stage's `tasks[]` array (in its own task set / lane)

> **Handled elsewhere.** Input value bindings happen in outer-workflow Step 9 — see [variables/io-binding/impl-json.md](../../variables/io-binding/impl-json.md). Entry conditions are added in Step 10.

## Post-Write Verification

Confirm the task exists in the correct stage with:

- `type: "process"`
- `data.context.taskTypeId` non-empty (unless intentionally skeleton)
- `data.inputs` and `data.outputs` populated from the planning-captured schema

Capture the generated `id` in `id-map.json` so downstream cross-task references can resolve.
