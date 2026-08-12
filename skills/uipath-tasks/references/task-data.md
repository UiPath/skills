# Task Data Reference

Task data is the business/form field payload attached to a task (e.g. the values
an approver reviews). Folder-scoped: pass `--folder-id <id>`, or omit it on an
interactive terminal to pick a folder (required when stdout is not a TTY). Task
IDs are numeric.

## Get data

```bash
uip tasks data get <task-id> --folder-id <folder-id> --output json
```

Success `Code: TaskData`, `Data` holds the task's field values.

## Save data

`--data` is required and must be a JSON object.

```bash
uip tasks data save <task-id> \
  --folder-id <folder-id> \
  --data '{"amount":1200,"approved":true}' \
  --output json
```

Success `Code: TaskDataSaved`.

## Type routing

Save routes to a type-specific endpoint: App tasks, Form tasks, and generic
tasks each save through a different Orchestrator path. The command resolves the
task type for you (it looks the task up when the type is not already known), so
you do not pass a type flag — just the task ID, folder, and `--data`.

> Save only fields the task's schema accepts. Saving unknown fields, or saving to
> a completed task, fails — get the task first (`tasks data get <task-id>`) to see the
> current shape.
