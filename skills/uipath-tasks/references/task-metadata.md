# Task Metadata, Comments & Labels Reference

Operations that annotate or reorganize an existing task. All are folder-scoped:
pass `--folder-id <id>`, or omit it on an interactive terminal to pick a folder
(required when stdout is not a TTY). Task IDs are numeric.

## Edit metadata

Change a task's title, priority, or catalog association. Pass only the fields to
change; unspecified fields keep their current value.

```bash
# Retitle and raise priority
uip tasks metadata <task-id> \
  --folder-id <folder-id> \
  --title "Urgent: invoice review" \
  --priority High \
  --output json

# Associate the task with a catalog
uip tasks metadata <task-id> --folder-id <folder-id> --catalog-id <catalog-id> --output json

# Remove the catalog association
uip tasks metadata <task-id> --folder-id <folder-id> --unset-catalog --output json
```

| Flag | Values |
|------|--------|
| `--title <text>` | New title |
| `--priority <p>` | `Low`, `Medium`, `High`, `Critical` |
| `--catalog-id <id>` | Associate a catalog (numeric ID) |
| `--unset-catalog` | Remove the catalog association |
| `--note <text>` | Comment recorded with the edit |

`--catalog-id` and `--unset-catalog` are opposites — do not pass both. Success
`Code: TaskMetadataEdited`.

## Comments

Comments are append-only, folder-scoped commentary on a task.

```bash
# List comments on a task
uip tasks comments list <task-id> --folder-id <folder-id> --output json

# Cap the number returned
uip tasks comments list <task-id> --folder-id <folder-id> --limit 50 --output json

# Add a comment (--text required)
uip tasks comments add <task-id> --folder-id <folder-id> --text "Escalated to finance" --output json
```

List → `Code: TaskCommentList` (array). Add → `Code: TaskCommentCreated`.

## Labels

Labels are name/value pairs on a task. `--labels` takes a JSON array and is
required. Saving **replaces** the full label set — pass every label you want to
keep. Use `[]` to clear all labels.

```bash
# Set labels
uip tasks labels <task-id> --folder-id <folder-id> --labels '[{"name":"urgent"}]' --output json

# Clear all labels
uip tasks labels <task-id> --folder-id <folder-id> --labels '[]' --output json
```

Success `Code: TaskLabelsSaved`.
