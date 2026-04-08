# Task Completion Reference

## Basic Completion

```bash
uip hitl tasks complete <task-id> \
  --type <task-type> \
  --folder-id <folder-id> \
  --output json
```

Response: `{ "Result": "Success", "Code": "TaskCompleted", "Data": { "success": true, ... } }`

## Required Fields by Task Type

Different task types route to different API endpoints and have different requirements:

| Task Type | `--action` | `--data` | Endpoint |
|-----------|-----------|----------|----------|
| `FormTask` | **Required** | **Required** | `POST /forms/TaskForms/CompleteTask` |
| `AppTask` | **Required** | **Required** | `POST /tasks/AppTasks/CompleteAppTask` |
| `ExternalTask` | Optional | Optional | `POST /tasks/GenericTasks/CompleteTask` |
| `DocumentValidationTask` | Optional | Optional | `POST /tasks/GenericTasks/CompleteTask` |
| `DocumentClassificationTask` | Optional | Optional | `POST /tasks/GenericTasks/CompleteTask` |
| `DataLabelingTask` | Optional | Optional | `POST /tasks/GenericTasks/CompleteTask` |

## Completing a Form Task

Form tasks require both `--action` (the button/outcome name) and `--data` (form field values):

```bash
uip hitl tasks complete <task-id> \
  --type FormTask \
  --folder-id <folder-id> \
  --action "Approve" \
  --data '{"comments": "Looks good", "approved": true}' \
  --output json
```

Common actions for form tasks: `"Approve"`, `"Reject"`, `"Submit"`, `"Escalate"`.

## Completing an App Task

```bash
uip hitl tasks complete <task-id> \
  --type AppTask \
  --folder-id <folder-id> \
  --action "Complete" \
  --data '{"result": "verified"}' \
  --output json
```

## Completing a Generic/External Task

External tasks do not require action or data:

```bash
# Minimal completion
uip hitl tasks complete <task-id> \
  --type ExternalTask \
  --folder-id <folder-id> \
  --output json

# With optional action and data
uip hitl tasks complete <task-id> \
  --type ExternalTask \
  --folder-id <folder-id> \
  --action "Done" \
  --data '{"notes": "Processed manually"}' \
  --output json
```

## Pre-Completion Checklist

Before completing a task, always verify:

1. **Task exists and is not already completed:**
   ```bash
   uip hitl tasks get <task-id> --output json
   # Check: status should be "Unassigned" or "Pending", not "Completed"
   ```

2. **Task type is correct:**
   ```bash
   # The "type" field in the response tells you which --type to use
   # e.g., "type": "FormTask" → --type FormTask
   ```

3. **Folder ID matches:**
   ```bash
   # The "folderId" field in the response gives you the --folder-id value
   ```

## SLA Tracking

Completed tasks may include SLA status in the response:

| SLA Status | Meaning |
|------------|---------|
| `CompletedInTime` | Completed within the SLA window |
| `Overdue` | Completed after the SLA deadline |
| `OverdueSoon` | Was close to SLA deadline when completed |
