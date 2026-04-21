---
name: uipath-tasks
description: "[PREVIEW] Manage UiPath Action Center tasks via CLI. Use when: list/assign/complete tasks, manage assignments, or user mentions 'Action Center'/'tasks'/'uip tasks'. For Orchestrator-> uipath-platform, skip for Document Understanding, or codedapp."
user-invokable: true
---

# UiPath Tasks (Action Center) — Agent Skill

Action Center is UiPath's human-in-the-loop platform. Tasks represent work items
that require human input — form approvals, document validation, data labeling, and more.

All operations go through `uip tasks <verb> --output json`.

---

## Login & Tenant Setup

**Default to Production. Only switch environment/org/tenant when explicitly stated in the request.**

- If the request mentions no environment → use the current session (defaults to prod `cloud.uipath.com`)
- If the request explicitly names an environment/org/tenant → check `uip login status` and re-login if needed

When switching is required:
1. Check current login: `uip login status --output json` — verify `UIPATH_URL`, `Organization`, and `Tenant`
2. Re-login with `--authority` only if environment differs:
   - Alpha: `uip login --authority https://alpha.uipath.com --tenant <tenant>`
   - Staging: `uip login --authority https://staging.uipath.com --tenant <tenant>`
   - Production: `uip login --tenant <tenant>` (default, no `--authority` needed)
3. If already on the right environment but wrong tenant: `uip login tenant set <tenant-name>`

```bash
# Check current environment, org, and tenant
uip login status --output json

# Login to Alpha with a specific tenant
uip login --authority https://alpha.uipath.com --tenant MyTenant

# List all available tenants (after login)
uip login tenant list --output json

# Switch tenant within the same environment
uip login tenant set MyTenant
```

> **Critical:** The `--tenant` flag on `tasks` commands does NOT switch the active session tenant.
> The environment is determined by `UIPATH_URL` in the auth file — always confirm with `login status` before running `tasks` commands.

---

## When to Use

- Listing or inspecting Action Center tasks across folders
- Assigning, reassigning, or unassigning tasks to users
- Completing tasks with action outcomes and data payloads
- Querying which users have task permissions in a folder

> **Not in scope:** Orchestrator queues or queue items (use `uip or`), Document Understanding model training, or Action Center app development (use `uip codedapp`).

---

## Task Types

| Type | CLI value | Description |
|------|-----------|-------------|
| Form task | `FormTask` | Form-based approval/action task |
| External task | `ExternalTask` | Generic external task |
| App task | `AppTask` | Action Center app-based task |
| Document validation | `DocumentValidationTask` | Document Understanding validation |
| Document classification | `DocumentClassificationTask` | Document Understanding classification |
| Data labeling | `DataLabelingTask` | Data labeling task |

---

## Task Statuses & Priorities

| Status | Meaning |
|--------|---------|
| `Unassigned` | Created but not assigned to any user |
| `Pending` | Assigned, awaiting completion |
| `Completed` | Completed with an action/outcome |

| Priority | Level |
|----------|-------|
| `Low` | Low |
| `Medium` | Medium (default) |
| `High` | High |
| `Critical` | Critical |

---

## Quick Start

```bash
# Check login and active tenant
uip login status --output json

# Switch tenant if needed
uip login tenant set <tenant-name>

# List all tasks across folders
uip tasks list --output json

# Get details of a specific task
uip tasks get <task-id> --output json

# Assign a task to a user
uip tasks assign <task-id> --user alice@company.com --output json

# Complete a task
uip tasks complete <task-id> --type ExternalTask --folder-id <folder-id> --output json
```

---

## Critical Rules

1. **Always resolve org and tenant first.** If the user specifies an org/environment and tenant, run `uip login status` to check the active tenant, then `uip login tenant set <tenant>` to switch if needed. Never assume the active tenant matches the user's intent.

2. **Task IDs are numeric.** Unlike other UiPath services that use GUIDs, Action Center uses numeric task IDs. Use `tasks list` to discover task IDs.

3. **Folder ID is required for complete.** Tasks are scoped to folders. Use `--folder-id` when completing tasks.

4. **Complete requires `--type`.** The API routes to different endpoints per task type. Always include `--type` when completing a task. Use `tasks get` to check the task type first.

5. **FormTask and AppTask require `--action` and `--data` for completion.** Other task types allow optional action and data.

6. **Assign accepts `--user-id` or `--user` (email).** Use `tasks users <folder-id>` to discover assignable users and their IDs.

7. **Always discover before acting.** Use `tasks list` or `tasks get` to inspect task state before performing assign/complete operations.

8. **Do not complete already-completed tasks.** Check the task `status` field — if it is `Completed`, inform the user.

---

## Task Navigation

| Task | Commands to use |
|------|----------------|
| List all tasks | `tasks list` |
| List tasks in a folder | `tasks list --folder-id <id>` |
| List tasks as admin | `tasks list --as-admin` |
| Get task details | `tasks get <task-id>` |
| Get task with type hint | `tasks get <task-id> --task-type FormTask --folder-id <id>` |
| Assign a task | `tasks assign <task-id> --user <email>` |
| Assign by user ID | `tasks assign <task-id> --user-id <id>` |
| Reassign a task | `tasks reassign <task-id> --user <email>` |
| Unassign a task | `tasks unassign <task-id>` |
| Complete a task | `tasks complete <task-id> --type <type> --folder-id <id>` |
| Complete with action | `tasks complete <task-id> --type FormTask --folder-id <id> --action "Approve" --data '{...}'` |
| List assignable users | `tasks users <folder-id>` |

---

## Workflow: Discover → Plan → Act → Verify

**Always follow this pattern:**

1. **Discover** — list tasks, get details, find assignable users
2. **Plan** — determine the operation (assign, complete, etc.)
3. **Act** — execute the operation
4. **Verify** — re-read the task to confirm the state change

```bash
# 0. Ensure correct tenant
uip login status --output json
uip login tenant set <tenant-name>   # only if needed

# 1. Discover
uip tasks list --output json
uip tasks get <task-id> --output json

# 2. Plan — determine the task type, folder ID, and action needed

# 3. Act — assign a task
uip tasks assign <task-id> --user alice@company.com --output json

# 4. Verify
uip tasks get <task-id> --output json
```

---

## Troubleshooting

| Error | Cause | Fix |
|-------|-------|-----|
| `Not logged in` | Auth expired | `uip login` |
| `HTTP 401` | Invalid token | Re-login |
| `HTTP 403` | Permission denied | Ensure account has Action Center permissions in the folder |
| `Missing assignee` | Neither `--user-id` nor `--user` provided | Add `--user <email>` or `--user-id <id>` |
| `Task not found` | Wrong task ID | Run `tasks list` to get correct ID |
| Completion fails | Wrong `--type` | Use `tasks get` to check the actual task type |
| Completion fails for FormTask | Missing `--action` or `--data` | FormTask and AppTask require both `--action` and `--data` |
| Cannot assign | User lacks permissions in folder | Run `tasks users <folder-id>` to list eligible users |

---

## References

For deeper guidance, read these files only when needed:

- `references/task-lifecycle.md` — Assign and complete task workflows with examples
- `references/task-completion.md` — Completion endpoint routing, required fields per task type
- `references/task-assignment.md` — Assign, reassign, unassign patterns and user discovery
