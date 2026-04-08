# Task Lifecycle Reference

## Listing Tasks

```bash
# List all tasks across folders
uip hitl tasks list --output json

# List tasks in a specific folder
uip hitl tasks list --folder-id <folder-id> --output json

# List tasks as admin (elevated access)
uip hitl tasks list --as-admin --output json
```

## Getting Task Details

```bash
# Basic get by ID
uip hitl tasks get <task-id> --output json

# Get with type hint (faster — uses type-specific endpoint)
uip hitl tasks get <task-id> --task-type FormTask --folder-id <folder-id> --output json
```

Type-specific endpoints are faster because they avoid the generic OData lookup:

| Task Type | Endpoint used |
|-----------|---------------|
| `FormTask` | `/forms/TaskForms/GetTaskFormById` |
| `AppTask` | `/tasks/AppTasks/GetAppTaskById` |
| Document types | `/tasks/GenericTasks/GetTaskDataById` |
| Not specified | `/odata/Tasks({id})` (generic) |

## Full Workflow: Discover → Assign → Complete

```bash
# 1. List tasks and discover folder users
uip hitl tasks list --output json
uip hitl tasks users <folder-id> --output json

# 2. Assign to a user
uip hitl tasks assign <task-id> --user alice@company.com --output json

# 3. Verify assignment
uip hitl tasks get <task-id> --output json
# → status should be "Pending", assignedToUser should show the user

# 4. Complete the task (when human has reviewed)
uip hitl tasks complete <task-id> \
  --type ExternalTask \
  --folder-id <folder-id> \
  --output json

# 5. Verify completion
uip hitl tasks get <task-id> --output json
# → status should be "Completed"
```

## Task Sources

Tasks can originate from different sources. The `taskSource` field indicates the origin:

| Source | Description |
|--------|-------------|
| `Agent` | Created by a coding agent |
| `Workflow` | Created by an RPA workflow |
| `Maestro` | Created by a Maestro orchestration |
| `Default` | Created manually or via API |
