# action task — Implementation (Direct JSON Write)

> **Phase split.** Runs across both phases. Phase 2a writes shape: `data.taskTitle` + full `data.inputs[]` / `data.outputs[]` schema from `tasks describe`, each `value` empty (`""`). Phase 2b binds values via [`../../variables/io-binding/impl-json.md`](../../variables/io-binding/impl-json.md). See [`../../../phased-execution.md`](../../../phased-execution.md).

Cross check the action (HITL) task metadata via CLI, then write the task directly into `caseplan.json`. Field discovery and reference resolution are done during [planning](planning.md) — implementation reads resolved values from `tasks.md`.

## Task JSON Shape

> **ID and elementId format.** Task `id` is `t` + 8 random chars. `elementId` is the composite `${stageId}-${taskId}`.

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
    "actionCatalogName": "<deploymentTitle from planning>",
    "labels": "<labels string from tasks.md (captured during planning)>",
    "inputs": [ /* form-field inputs, from planning enrichment */ ],
    "outputs": [ /* decision, comments, form outputs, from planning enrichment */ ],
    "context": { "taskTypeId": "act_app_9876543210" }
  }
}
```

## All Attributes

Inherits the full `ProcessTask` shape — see [process/impl-json.md § All Attributes](../process/impl-json.md#all-attributes) for top-level fields and base `data` fields. Action-specific differences:

- `type` is `"action"` (not `"process"`)
- `data` carries the additional fields below

`data` — extra fields for `ActionTask`:

| Field | Type | Notes |
|---|---|---|
| `data.taskTitle` | string | HITL task title shown to the assignee (required, even on skeletons) |
| `data.labels` | string | Label set from `tasks.md` (captured during planning) |
| `data.priority` | string | `"Low"`, `"Medium"` (default), `"High"`, or `"Critical"` |
| `data.actionCatalogName` | string | `deploymentTitle` from `tasks.md` (captured during planning) |
| `data.recipient` | string \| `ActionTaskAssignee` | User email string, or assignee object for group/role |
| `data.startCriteria` | string \| number | Expression/value that starts the action |
| `data.endCriteria` | string \| number | Expression/value that ends the action |
| `data.timer` | string \| number | Timer expression/value for the action |
| `data.actionDataOutcome` | string \| number | Outcome payload selector |
| `data.actionData` | string | Serialized action data payload |

`ActionTaskAssignee` (when `data.recipient` is an object):

| Field | Type | Notes |
|---|---|---|
| `Type` | `0 \| 1 \| 2 \| 3` | Assignee kind (see mapping below) |
| `Value` | string | Assignee identifier (format depends on `Type`) |
| `originalEntry` | unknown | Original entry payload |

`Type` / `Value` mapping:

| `Type` | `Value` format | Meaning |
|---|---|---|
| `0` | User UUID | Assign by user ID |
| `1` | Group UUID | Assign to any group member |
| `2` | Email string | Assign by email address |
| `3` | `"=vars.<varId>"` | Resolved from variable at runtime |

## Procedure

**Step 0 — Get enriched metadata + outputs:**

Run `tasks describe` against the resolved action-app `id` and save the JSON response — this is the source of truth for the form-field `data.inputs[]` / `data.outputs[]` (including standard `decision` / `comments`) in Step 1.

```bash
uip maestro case tasks describe --type action --id "<action-app-id>" --output json
```

Capture the response (input/output schema with names, types, and ids). If `tasks describe` fails or returns no schema, fall back to the planning-captured schema from `tasks.md`; if that is also missing, treat the task as skeleton per [skeleton-tasks.md](../../../skeleton-tasks.md).

**Step 1 — Write task with populated data:**

1. Generate task ID: `t` + 8 alphanumeric chars (unique across all tasks)
2. Generate elementId: `<stageId>-<taskId>`
3. Set top-level fields (`type: "action"`, `displayName`, `isRequired`, `shouldRunOnlyOnce`) from tasks.md per the Task JSON Shape above
4. Set `data.taskTitle` from tasks.md `task-title` (always emit — validator requires it; fall back per [planning.md § Task Title Fallback](planning.md))
5. Set `data.priority` from tasks.md (default `"Medium"`)
6. Set `data.recipient` from tasks.md only when a user email is supplied. Omit the key entirely for group/role assignment or when the user chose `Skip`
7. Set `data.context.taskTypeId` to the action-app `id` from `tasks.md` (captured during planning)
8. Set `data.actionCatalogName` to the action-app `deploymentTitle` and `data.labels` to the label set — both read from `tasks.md` (captured during planning)
9. Write `data.inputs[]` / `data.outputs[]` using the schema captured in Step 0 (falling back to the planning-captured schema in tasks.md if Step 0 was unavailable). Each input is `{ name, type, id, var, elementId, value: "" }`; each output is `{ name, type, id, var, value, source, target, elementId }`. See [variables/io-binding/impl-json.md](../../variables/io-binding/impl-json.md) for shape details.
10. Write the task to the target stage's `tasks[]` array (in its own task set / lane)

> **Handled elsewhere.** Input value bindings happen in outer-workflow Step 9 — see [variables/io-binding/impl-json.md](../../variables/io-binding/impl-json.md). Entry conditions are added in Step 10.

## Post-Write Verification

Confirm the task exists in the correct stage with:

- `type: "action"`
- `data.taskTitle` non-empty
- `data.recipient` matches the sdd.md assignee when one is specified (absent when group-assigned)
- `data.context.taskTypeId` non-empty (unless intentionally skeleton)
