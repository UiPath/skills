# Task Assignment Reference

## Discovering Assignable Users

Before assigning a task, discover which users have task permissions in the folder:

```bash
uip tasks users <folder-id> --output json

# Or by folder path/key — the values `uip or folders list` prints.
# Quote the path: folder paths may contain spaces.
uip tasks users --folder-path "<folder-path>" --output json
uip tasks users --folder-key <folder-key> --output json
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

## Tasks Sent to a Group

`uip tasks assign`, `reassign` and `unassign` work on single users. A group can't be passed: its ID is refused with `2490` (see below).

A task that a flow or agent assigned to a group shows it in `tasks get`:

```bash
uip tasks get <task-id> --output json
# → "TaskAssignmentCriteria": "AllUsers", "AssignedToUser": { "Type": "DirectoryGroup", ... }
```

- **A quick form (`QuickFormTask`) assigned this way opens read-only.** The Action Center web UI lists it under Pending for every member but disables Approve and Reject, and offers no Claim button. Only a quick form assigned to one user can be completed in the UI (observed on Action Center 26.10). To let a member act on it, assign it to that person (`tasks assign <task-id> --user <email>`), or run `tasks unassign <task-id>` so a member can pick it up with **Assign to self**.
- **A group that can't be resolved leaves the task `Unassigned`**, and its members never see it. This happens, for example, when the group has no role in the task's folder. Run `tasks users --folder-path "<folder-path>"` and check that the group is listed.
- **A task can also be `Unassigned` because of who created it.** The identity that creates a task (for a Flow, the robot running the job) also assigns it. Without `TaskAssignment.Create` in the task's folder, the assignment is dropped with no error. See `2415` below.
- **`tasks list` also returns deleted tasks.** Check `IsDeleted` on each one before you count or act on pending work.

## Assignment Errors

| Error | Cause | Fix |
|-------|-------|-----|
| `2490` "A group entity cannot be used for a single user assignment" | A group's ID was passed to `tasks assign` | Assign one member by `--user`, or unassign the task so a member can self-assign |
| `2482` "Local group not found or the group has insufficient permissions in this folder" | The group has no role in the task's folder | Have a folder admin give the group a role with task permissions in that folder; don't re-create or re-import the group |
| `2415` "You do not have the required permissions to change the assignee of the action" | The calling identity (for a Flow, the robot running the job) lacks `TaskAssignment.Create` in the task's folder; Automation User doesn't include it | Have a folder admin give that identity a role with it (Automation Developer is the smallest built-in one); don't work around it with another identity's token |
| `2400` "Unable to change the assignee of the action at this time, please try again later" | Seen when a group was assigned by name after its folder membership had been re-created; retrying didn't help | Assign one member by `--user` |
| `Missing assignee` | Neither `--user-id` nor `--user` provided | Add one of the two options |
| `User not found` | Email or ID doesn't match a valid user | Run `tasks users <folder-id>` to list valid users |
| `Permission denied` | User lacks Task.Edit permission in folder | Contact folder admin to grant permissions |
| `Task already completed` | Cannot assign a completed task | Check task status with `tasks get` first |
