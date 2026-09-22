# Task Data Reference

Task data is the business/form field payload attached to a task: a JSON object of
key/value pairs whose keys are the task's schema fields (the values an approver
reviews). Folder-scoped: pass `--folder-id <id>` (or `--folder-path <path>` /
`--folder-key <guid>`), or omit them in an interactive terminal to pick a folder
(in a non-interactive run you must pass one). Task IDs are numeric.

## Get data

```bash
uip tasks data get <task-id> --folder-id <folder-id> --output json
```

Success `Code: TaskData`, `Data` holds the task's field values.

## Save data

`--data` is required and must be a JSON object of key/value pairs matching the
task's schema.

> **Save replaces the whole payload; it does not upsert or merge.** Any field you
> omit is dropped. Never save an empty or partial object unless the user explicitly
> asked for it, and confirm with the user first, otherwise you will overwrite the
> existing task data. Get the current data first (`tasks data get`) and edit from
> that.

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
you do not pass a type flag, just the task ID, folder, and `--data`.

> Save only fields the task's schema accepts. Saving unknown fields, or saving to
> a completed task, fails.
