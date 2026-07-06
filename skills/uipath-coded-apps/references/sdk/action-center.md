# Action Center Reference — Scopes, Conventions, Traps

Method signatures, parameters, return types, and usage examples: read the installed types — `node_modules/@uipath/uipath-typescript/dist/tasks/index.d.ts` (full JSDoc; matches your installed SDK version). This file covers ONLY what the `.d.ts` cannot tell you.

## Imports

```typescript
import { Tasks } from '@uipath/uipath-typescript/tasks';
```

Types, options, and enums export from the same subpath as their service class.

## Scopes

- Read: `OR.Tasks` or `OR.Tasks.Read`
- Write: `OR.Tasks` or `OR.Tasks.Write`

## Traps

### `create()` only makes External tasks

`create()` only supports creating External tasks (`TaskType.External`). Form tasks and App tasks are created by the system through workflows.

### `getById()` — pass `taskType` to skip the discovery round-trip

`TaskGetByIdOptions.taskType` is an optimization. Without it, the SDK issues a generic GET, inspects `type`, then issues a second type-specific GET. With it, the SDK skips the discovery call and goes straight to the type-specific endpoint — **`folderId` then becomes required** (throws `ValidationError` otherwise). Use for any non-`External` task when you already know the type:

```typescript
// Faster — single round-trip. Required pattern for Validation Station hydration.
const dvTask = await tasks.getById(taskId, { taskType: TaskType.DocumentValidation }, folderId);
```

For `TaskType.Form`, the SDK auto-adds `expandOnFormLayout: true` so `formLayout` is populated.

### OData filtering — server-side field names

`TaskGetAllOptions` supports `filter` (OData `$filter` string) and `orderby` for server-side filtering and sorting. Examples:
- Pending tasks only: `filter: "Status ne 'Completed'"`
- By external tag: `filter: "ExternalTag eq 'some-value'"`
- Combined: `filter: "Status ne 'Completed' and ExternalTag eq 'some-value'"`

### Prefer task-attached `complete()` over service `complete()`

Tasks returned by `getAll()`, `getById()`, and `create()` carry attached methods (`task.assign()`, `task.reassign()`, `task.unassign()`, `task.complete()`). When you already have a `TaskGetResponse`, **always use the task-attached method** — it's simpler because it doesn't need `taskId` or `folderId`:

```typescript
// PREFERRED — task-attached method (no taskId, no folderId needed)
await task.complete({ type: task.type as TaskType, action: 'Approve', data: {} });

// AVOID — service method (requires both taskId and folderId)
await tasks.complete({ type: TaskType.External, taskId: task.id, action: 'Approve' }, folderId);
```

### Task type discrimination — use the enum, don't compare strings

The `task.type` field on `TaskGetResponse` is a `TaskType` enum value. **Always use the enum for comparison and when passing to `complete()`:**

```typescript
import { TaskType } from '@uipath/uipath-typescript/tasks';

// CORRECT — use the enum directly from the task
if (task.type === TaskType.External) { ... }

// WRONG — comparing against string literals
if (task.type === 'FormTask') { ... }  // Don't do this
```

### `TaskCompleteOptions` discriminated union — NEVER use conditional spread

`TaskCompleteOptions` is a discriminated union on `type`. TypeScript cannot narrow the union when you use conditional spreads like `...(condition ? { data: {} } : {})`. **Always use explicit if/else branching:**

```typescript
const handleTaskAction = async (task: TaskGetResponse, action: 'approve' | 'reject') => {
  const actionLabel = action === 'approve' ? 'Approve' : 'Reject';

  // Branch by type — TypeScript narrows the discriminated union correctly
  if (task.type === TaskType.External) {
    await task.complete({ type: TaskType.External, action: actionLabel });
  } else {
    // Form and App tasks require data and action
    await task.complete({ type: task.type, action: actionLabel, data: {} });
  }
};
```

**NEVER use conditional spread for discriminated unions:**
```typescript
// WRONG — TS2345: TypeScript can't narrow the union through a spread
await task.complete({
  type: task.type as TaskType,
  action: actionLabel,
  ...(task.type !== TaskType.External ? { data: {} } : {}),  // Breaks type narrowing
});
```

For Maestro HITL tasks (approve/reject flows), tasks are typically `TaskType.App` or `TaskType.External`. Pass `data: {}` (empty object) for App tasks when there's no form data to submit.

For `TaskType.DocumentValidation`, the Validation Station widget owns the data contract — call `task.complete({ type: TaskType.DocumentValidation, action: 'Completed' })` from `onSaveComplete`. Do NOT pass `data` yourself; the widget already uploaded the validated payload to the bucket before firing the callback. See [../widgets/validation-station.md](../widgets/validation-station.md).

### Action strings

The `action` parameter is a free-form string that maps to the workflow's expected action. Common patterns:
- **Approve/Reject**: `action: 'Approve'` or `action: 'Reject'`
- **Submit**: `action: 'Submit'`
- **Custom**: whatever the workflow designer configured

If the task has an `action` field set (`task.action`), that's the expected action string. For tasks with multiple possible actions (approve/reject), pass the action corresponding to the user's choice.

## Linking Tasks to Maestro Process Instances

When a process instance is waiting on a HITL task (detected via `getVariables()` + `getBpmn()` — see [../patterns.md](../patterns.md) "HITL Detection"), use the `CreatorJobKey` OData filter to find the task for that instance.

### Pattern: Find the pending task for a process instance

```typescript
import { Tasks } from '@uipath/uipath-typescript/tasks';
import type { TaskGetResponse } from '@uipath/uipath-typescript/tasks';

// Filter tasks by CreatorJobKey — the instanceId IS the CreatorJobKey
const result = await tasks.getAll({
  filter: `CreatorJobKey eq ${instanceId}`,
  pageSize: 10,
});

// The matching task (if the instance has a pending HITL task)
const pendingTask = result.items.find(t => !t.isCompleted) ?? null;
```

**Why `CreatorJobKey`:** When Maestro creates an Action Center task for a process instance, it stamps the task with the instance ID as the `CreatorJobKey`. This is the only reliable server-side filter for instance-to-task correlation. Do NOT use `taskSource`, `taskSourceMetadata`, `tags`, or `parentOperationId` — these are unreliable for this purpose.

**IMPORTANT:** There is NO shortcut from `latestRunStatus` — a process waiting on HITL still shows as `"Running"`. Always use `getVariables()` + `getBpmn()` to detect HITL first, then use the `CreatorJobKey` filter to get the task details.

### If no task is found — show an error, don't widen the search

**NEVER fall back to "pick the first pending task" or "pick any Maestro task" if the `CreatorJobKey` filter returns no results.** This risks completing the wrong task. Instead:

```typescript
const result = await tasks.getAll({
  filter: `CreatorJobKey eq ${instanceId}`,
  pageSize: 10,
});
const pendingTask = result.items.find(t => !t.isCompleted) ?? null;

if (!pendingTask) {
  // Show clear error — do NOT widen the search
  setError('No pending task found for this instance. The task may have already been completed.');
  return;
}
```
