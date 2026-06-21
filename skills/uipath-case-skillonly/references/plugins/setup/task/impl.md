# Task — Common Fields and Lane Convention

## Lane Convention (v16)

Each task occupies its **own lane** — one task per array slot. Lane index increments by 1 for each task added to the stage, starting from 0.

```json
"tasks": [
  [ task0 ],   ← lane 0
  [ task1 ],   ← lane 1
  [ task2 ]    ← lane 2
]
```

> **Parallelism is controlled by entry conditions, not by lane grouping.** Two tasks with `"rule": "current-stage-entered"` both activate when the stage is entered and run in parallel — regardless of being in different lanes.

> **Never group multiple tasks in the same lane array.** `[[task0, task1]]` is deprecated.

## Common Task Fields

```json
{
  "id": "t<8chars>",
  "elementId": "<stageId>-t<8chars>",
  "displayName": "<Task Name>",
  "description": "<task description>",
  "type": "<taskType>",
  "isRequired": true,
  "shouldRunOnlyOnce": true,
  "data": { ... },
  "entryConditions": [
    {
      "id": "Condition_<6chars>",
      "displayName": "Stage entered",
      "rules": [[{ "rule": "current-stage-entered", "id": "Rule_<6chars>" }]]
    }
  ]
}
```

| Field | Notes |
|---|---|
| `id` | `t` + 8 random alphanumeric chars |
| `elementId` | `<stageId>-<taskId>` — must match exactly |
| `isRequired` | `true` → stage exit waits for this task |
| `shouldRunOnlyOnce` | `true` → task skipped on stage re-entry; `false` → re-runs |
| `entryConditions` | Always add at least one. Default: `current-stage-entered` |

> **Note:** Use `shouldRunOnlyOnce` (not `shouldRunOnReEntry`). The `shouldRunOnReEntry` field is deprecated.

## Reading from Planning (tasks.md)

```
## T08: Add rpa task "Book appraisal" to "Stage 1"
- taskTypeId: 17a61b30-d97e-4671-897c-58ec30231327
- description: Runs the Book appraisal RPA process to perform initial case assessment
- inputs: none
- outputs: none
- runOnlyOnce: true
- isRequired: true
```

### Field Mapping

| Planning field | JSON field | Notes |
|---|---|---|
| Task type in title (`rpa`, `agent`, etc.) | `type` | Use exact type string |
| Task name in title (`"Book appraisal"`) | `displayName` | |
| `taskTypeId` | Used for registry lookup | See below |
| `description` | `description` | |
| `runOnlyOnce: true` | `shouldRunOnlyOnce: true` | |
| `isRequired: true` | `isRequired: true` | |
| `inputs: none` | `"inputs": []` | |
| `inputs: fieldName (desc)` | input entry in `data.inputs` | Value empty if "currently unbound" |
| `outputs: none` | Error output only | |
| `outputs: varName (desc)` | output entry in `data.outputs` + global variable | |
| `taskTitle` | `data.taskTitle` | action tasks only |
| `recipient: email` | `data.recipient: { "Type": 2, "Value": email }` | action tasks only |
| `priority` | `data.priority` | action tasks only |

### taskTypeId → resourceKey Lookup

`taskTypeId` is a UUID from the planning doc. Use it to find the resource binding info:

```bash
uip case registry search "<task display name>" --output json
```

From the result, capture:
- `resourceKey` — e.g. `"Shared/[CM] Insurance.BookAppraisal"`
- `name` (display name) — for the `default` field in bindings
- `folderPath` — for the folderPath binding `default` field

Then declare two root bindings and reference them in the task. See [variables/bindings](../../variables/bindings/impl.md).

### Lane Assignment from Planning

Tasks are listed in planning order within each stage. Assign lane index sequentially:
- First task in the stage → lane 0
- Second task in the stage → lane 1
- Third task → lane 2
- And so on

Tasks with `"rule": "current-stage-entered"` entry condition run in parallel (all activate on stage entry). Tasks with `"rule": "selected-tasks-completed"` run after the specified tasks finish.

### Output Declaration

When `outputs: varName (description)` is listed:

1. Declare a global variable in `root.data.uipath.variables.inputOutputs`:
   ```json
   { "id": "varName", "name": "varName", "displayName": "varName", "type": "string" }
   ```

2. Add output wiring in task `data.outputs`:
   ```json
   {
     "name": "varName", "displayName": "varName", "value": "varName",
     "type": "string", "source": "=varName", "var": "varName",
     "id": "varName", "target": "=varName",
     "elementId": "<stageId>-<taskId>"
   }
   ```

When `outputs: none`, include only the standard Error output (see individual task type plugins).
