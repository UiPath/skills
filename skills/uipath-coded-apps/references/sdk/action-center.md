# Action Center (Tasks) — Traps & Server Behavior

Signatures/params/examples: `dist/tasks/index.d.ts`. Per-method scopes: shipped `docs/oauth-scopes.md`. This file covers only what neither can express.

## Traps

### `create()` only makes External tasks

The server accepts only `TaskType.External` from `create()`. Form and App tasks are created by the system through workflows.

### Form task hydration

When `getById` hits the Form-specific endpoint (`taskType: TaskType.Form`), the SDK silently adds `expandOnFormLayout: true` so `formLayout` is populated — you don't pass it yourself.

### OData filtering — server-side field names

`filter` / `orderby` take raw server-side field names (not derivable from the `filter?: string` type):
- Pending tasks only: `filter: "Status ne 'Completed'"`
- By external tag: `filter: "ExternalTag eq 'some-value'"`
- Combined: `filter: "Status ne 'Completed' and ExternalTag eq 'some-value'"`

### Completing tasks

When you already hold a `TaskGetResponse`, use the task-attached `task.complete(...)` over the service `tasks.complete(...)` — no `taskId` / `folderId` to thread through.

**`TaskCompleteOptions` is a discriminated union on `type` — NEVER use conditional spread.** TypeScript cannot narrow the union through `...(condition ? { data: {} } : {})` (TS2345). Always branch explicitly:

```typescript
const handleTaskAction = async (task: TaskGetResponse, action: 'approve' | 'reject') => {
  const actionLabel = action === 'approve' ? 'Approve' : 'Reject';

  if (task.type === TaskType.External) {
    await task.complete({ type: TaskType.External, action: actionLabel });
  } else {
    // Form and App tasks require data and action
    await task.complete({ type: task.type, action: actionLabel, data: {} });
  }
};
```

### Action strings

`action` is free-form and must match what the workflow designer configured. If `task.action` is set, that's the expected string. Common patterns: `'Approve'` / `'Reject'`, `'Submit'`. Maestro HITL tasks are typically `TaskType.App` or `TaskType.External`; pass `data: {}` for App tasks with no form data.

For `TaskType.DocumentValidation`, the Validation Station widget owns the data contract — call `task.complete({ type: TaskType.DocumentValidation, action: 'Completed' })` from `onSaveComplete`. Do NOT pass `data` yourself; the widget already uploaded the validated payload to the bucket before firing the callback. See [../widgets/validation-station.md](../widgets/validation-station.md).

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
