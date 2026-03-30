# Action Center Reference

## Import

```typescript
import { Tasks } from '@uipath/uipath-typescript/tasks';
```

## Scopes

- Read: `OR.Tasks` or `OR.Tasks.Read`
- Write: `OR.Tasks` or `OR.Tasks.Write`

## Types to Import

```typescript
import type {
  TaskGetResponse,
  RawTaskGetResponse,
  TaskCreateResponse,
  RawTaskCreateResponse,
  TaskMethods,
  TaskCreateOptions,
  TaskGetAllOptions,
  TaskGetByIdOptions,
  TaskGetUsersOptions,
  TaskAssignOptions,
  TaskAssignmentOptions,
  TaskAssignmentResponse,
  TaskCompleteOptions,
  TaskCompletionOptions,
  UserLoginInfo,
  TaskSlaDetail,
  TaskAssignment,
  TaskActivity,
  Tag,
  TaskSource,
} from '@uipath/uipath-typescript/tasks';
```

## Enums

```typescript
import {
  TaskType,          // Form = 'FormTask', External = 'ExternalTask', App = 'AppTask'
  TaskPriority,      // Low, Medium, High, Critical
  TaskStatus,        // Unassigned, Pending, Completed
  TaskSlaStatus,     // OverdueLater, OverdueSoon, Overdue, CompletedInTime
  TaskSlaCriteria,   // TaskCreated, TaskAssigned, TaskCompleted
  TaskActivityType,  // Created, Assigned, Reassigned, Unassigned, Saved, Forwarded, Completed, Commented, Deleted, BulkSaved, BulkCompleted, FirstOpened
  TaskSourceName,    // Agent, Workflow, Maestro, Default
} from '@uipath/uipath-typescript/tasks';
```

## Tasks Service

### create(options: TaskCreateOptions, folderId: number)

Returns `Promise<TaskCreateResponse>` (task data with attached methods). Options: `{ title: string, data?: Record<string, unknown>, priority?: TaskPriority }`. The `folderId` is required.

**Note:** `create()` only supports creating External tasks (`TaskType.External`). Form tasks and App tasks are created by the system through workflows.

### getAll(options?: TaskGetAllOptions)

Returns `NonPaginatedResponse<TaskGetResponse>` or `PaginatedResponse<TaskGetResponse>`. Options extend `RequestOptions & PaginationOptions & { folderId?: number, asTaskAdmin?: boolean }`. Supports `filter`, `orderby`, `expand`, `select`, pagination.

### getById(id: number, options?: TaskGetByIdOptions, folderId?: number)

Returns `Promise<TaskGetResponse>` with attached methods. For form tasks, `folderId` is required.

`TaskGetResponse` key fields: `id`, `title`, `status`, `type`, `priority`, `folderId`, `key`, `data`, `isDeleted`, `isCompleted`, `createdTime`, `assignedToUser`, `formLayout` (for form tasks), `taskAssignments`, `activities`, `tags`, `taskSource`, `parentOperationId`, `externalTag`.

**OData filtering:** `TaskGetAllOptions` supports `filter` (OData `$filter` string) and `orderby` for server-side filtering and sorting. Examples:
- Pending tasks only: `filter: "Status ne 'Completed'"`
- By external tag: `filter: "ExternalTag eq 'some-value'"`
- Combined: `filter: "Status ne 'Completed' and ExternalTag eq 'some-value'"`

### getUsers(folderId: number, options?: TaskGetUsersOptions)

Returns `NonPaginatedResponse<UserLoginInfo>` or `PaginatedResponse<UserLoginInfo>`. Each user has: `name`, `surname`, `userName`, `emailAddress`, `displayName`, `id`.

### assign(options: TaskAssignmentOptions | TaskAssignmentOptions[])

Returns `Promise<OperationResponse<TaskAssignmentOptions[] | TaskAssignmentResponse[]>>`. Each assignment requires `taskId` and either `userId` or `userNameOrEmail`.

### reassign(options: TaskAssignmentOptions | TaskAssignmentOptions[])

Same signature as assign. Reassigns tasks to new users.

### unassign(taskId: number | number[])

Returns `Promise<OperationResponse<{ taskId: number }[] | TaskAssignmentResponse[]>>`. Accepts single ID or array.

### complete(options: TaskCompletionOptions, folderId: number)

Returns `Promise<OperationResponse<TaskCompletionOptions>>`. The `folderId` is required.

`TaskCompletionOptions` is a discriminated union:
- For `TaskType.External`: `{ type: TaskType.External, taskId: number, data?: any, action?: string }`
- For other types: `{ type: TaskType.Form | TaskType.App, taskId: number, data: any, action: string }`

## Task-Attached Methods (TaskMethods)

Returned by `getAll()`, `getById()`, and `create()` on each task:

- `task.assign(options: TaskAssignOptions)` -> requires `{ userId }` or `{ userNameOrEmail }`
- `task.reassign(options: TaskAssignOptions)` -> same options as assign
- `task.unassign()` -> no arguments needed, uses the task's own ID
- `task.complete(options: TaskCompleteOptions)` -> `{ type, data?, action? }` (no taskId needed, uses own ID)

`TaskAssignOptions` type: `{ userId: number } | { userNameOrEmail: string }` (mutually exclusive).

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

## Completing Tasks — Detailed Patterns

### Prefer task-attached `complete()` over service `complete()`

When you already have a `TaskGetResponse` from `getAll()` or `getById()`, **always use the task-attached method** — it's simpler because it doesn't need `taskId` or `folderId`:

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
await task.complete({
  type: task.type as TaskType,  // Already a TaskType value
  action: actionLabel,
  data: task.type === TaskType.External ? undefined : {},
});

// WRONG — comparing against string literals
if (task.type === 'FormTask') { ... }  // Don't do this
```

### `TaskCompleteOptions` discriminated union

The `type` field determines which other fields are required:

| Task Type | `data` | `action` | Example |
|-----------|--------|----------|---------|
| `TaskType.External` | Optional | Optional | `{ type: TaskType.External, action: 'Approve' }` |
| `TaskType.Form` | **Required** | **Required** | `{ type: TaskType.Form, action: 'Submit', data: formData }` |
| `TaskType.App` | **Required** | **Required** | `{ type: TaskType.App, action: 'Approve', data: {} }` |

For Maestro HITL tasks (approve/reject flows), tasks are typically `TaskType.App` or `TaskType.External`. Pass `data: {}` (empty object) for App tasks when there's no form data to submit.

### Action strings

The `action` parameter is a free-form string that maps to the workflow's expected action. Common patterns:
- **Approve/Reject**: `action: 'Approve'` or `action: 'Reject'`
- **Submit**: `action: 'Submit'`
- **Custom**: whatever the workflow designer configured

If the task has an `action` field set (`task.action`), that's the expected action string. For tasks with multiple possible actions (approve/reject), pass the action corresponding to the user's choice.

### Complete pattern for HITL approve/reject

**IMPORTANT:** `TaskCompleteOptions` is a discriminated union on `type`. TypeScript cannot narrow the union when you use conditional spreads like `...(condition ? { data: {} } : {})`. **Always use explicit if/else branching:**

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

## Usage Example

```typescript
import { useMemo, useEffect, useState } from 'react';
import { useAuth } from '../hooks/useAuth';
import { Tasks } from '@uipath/uipath-typescript/tasks';
import { TaskType, TaskPriority } from '@uipath/uipath-typescript/tasks';
import type { TaskGetResponse } from '@uipath/uipath-typescript/tasks';

function TaskInbox({ folderId }: { folderId: number }) {
  const { sdk } = useAuth();
  const tasks = useMemo(() => new Tasks(sdk), [sdk]);
  const [taskList, setTaskList] = useState<TaskGetResponse[]>([]);

  useEffect(() => {
    const load = async () => {
      const result = await tasks.getAll({ folderId, pageSize: 20 });
      setTaskList(result.items);
    };
    load();
  }, [tasks, folderId]);

  // Use task-attached complete — no taskId or folderId needed
  const handleComplete = async (task: TaskGetResponse, action: string) => {
    if (task.type === TaskType.External) {
      await task.complete({ type: TaskType.External, action });
    } else {
      await task.complete({ type: task.type, action, data: {} });
    }
  };

  const handleAssign = async (task: TaskGetResponse, userId: number) => {
    await task.assign({ userId });
  };

  const handleCreate = async () => {
    const newTask = await tasks.create({
      title: 'Review document',
      priority: TaskPriority.Medium,
    }, folderId);
  };
}
```
