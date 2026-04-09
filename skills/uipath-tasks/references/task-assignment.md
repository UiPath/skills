# Task Assignment Reference

## Discovering Assignable Users

Before assigning a task, discover which users have task permissions in the folder:

```bash
uip tasks users <folder-id> --output json
```

Response includes user details:

```json
{
  "Result": "Success",
  "Code": "TaskUserList",
  "Data": [
    {
      "id": 12345,
      "name": "Alice",
      "surname": "Smith",
      "userName": "alice.smith@company.com",
      "emailAddress": "alice.smith@company.com",
      "displayName": "Alice Smith"
    }
  ]
}
```

Use either the `id` (with `--user-id`) or `emailAddress` (with `--user`) for assignment.

## Assigning a Task

Two ways to specify the assignee:

```bash
# By email (recommended — human-readable)
uip tasks assign <task-id> --user alice.smith@company.com --output json

# By user ID (useful when scripting)
uip tasks assign <task-id> --user-id 12345 --output json
```

- `--user` and `--user-id` are mutually exclusive — provide one or the other
- After assignment, task status changes from `Unassigned` to `Pending`

## Reassigning a Task

Move a task from one user to another:

```bash
uip tasks reassign <task-id> --user bob@company.com --output json
```

Reassignment works the same as assignment — accepts `--user` or `--user-id`.

## Unassigning a Task

Remove the current assignee, returning the task to `Unassigned` status:

```bash
uip tasks unassign <task-id> --output json
```

## Full Workflow: Find User → Assign → Verify

```bash
# 1. Find the folder ID from the task
uip tasks get <task-id> --output json
# → note "folderId" from response

# 2. List users with permissions in that folder
uip tasks users <folder-id> --output json
# → find the target user's email or ID

# 3. Assign the task
uip tasks assign <task-id> --user alice@company.com --output json

# 4. Verify assignment
uip tasks get <task-id> --output json
# → "status" should be "Pending"
# → "assignedToUser" should show the assigned user
```

## Assignment Errors

| Error | Cause | Fix |
|-------|-------|-----|
| `Missing assignee` | Neither `--user-id` nor `--user` provided | Add one of the two options |
| `User not found` | Email or ID doesn't match a valid user | Run `tasks users <folder-id>` to list valid users |
| `Permission denied` | User lacks Task.Edit permission in folder | Contact folder admin to grant permissions |
| `Task already completed` | Cannot assign a completed task | Check task status with `tasks get` first |
