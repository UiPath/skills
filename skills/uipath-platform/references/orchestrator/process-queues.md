# Process Queues

Create work queues, add items for distributed processing, track progress, and manage review cycles.

> For full option details, run `uip or queues create --help` or the relevant command with `--help`.

## When to Use

- Dispatcher-performer and distributed processing
- Queue-item review workflows

## Prerequisites

- Run `uip login status`. If not logged in, ask the user to run `uip login` (it opens an interactive browser flow).
- Run `uip or folders list` to verify the target folder exists.

## Queue Management

### Create

```bash
uip or queues create "<queue-name>" \
  --folder-path "<folder>" --max-retries 3 --auto-retry \
  --enforce-unique-reference --output json
```

`--max-retries <n>` sets retry attempts. `--auto-retry` / `--no-auto-retry` controls automatic retries for `ApplicationException` (default: true). `--enforce-unique-reference` rejects duplicate references. `--encrypted` encrypts item data. `--retention-action` and `--stale-retention-action` accept `Delete`, `Archive`, or `None` (defaults: `Delete`); `--retention-period <days>` defaults to 30 and `--stale-retention-period <days>` defaults to 180.

### List, Get, Update, Delete

```bash
uip or queues list --folder-path "<folder>" --output json
uip or queues get <queue-key> --output json
uip or queues update <queue-key> --max-retries 5 --no-auto-retry --output json
uip or queues delete <queue-key> --yes --output json
uip or queues delete <queue-key> --force --output json
```

Filter `list` with `--name` (contains match), `--limit`, and `--offset`. `get`, `update`, and `delete` are cross-folder and need no `--folder-path`. Delete refuses while items remain unless `--force`; `--force` deletes the queue and its items.

### Share Across Folders

```bash
uip or queues share <queue-key> --folder-path "<folder>" --output json
uip or queues get-folders <queue-key> --output json
uip or queues unshare <queue-key> --folder-path "<folder>" --output json
```

### Processing Stats

```bash
uip or queues get-stats --folder-path "<folder>" --key <queue-key> --output json
uip or queues get-stats --folder-path "<folder>" \
  --name "<name>" \
  --from "2026-04-01T00:00:00Z" --to "2026-04-30T23:59:59Z" \
  --output json
```

`get-stats` returns aggregate totals, successes, failures, exception counts, average handling time, and processing times. Without `--key` or `--name`, it covers every queue in the folder. `--from` and `--to` filter by last-processed date in ISO 8601.

## Queue Item Lifecycle

### Add Items

Run `add` with a queue **name**, not key:

```bash
uip or queue-items add "<queue-name>" \
  --folder-path "<folder>" \
  --specific-content '{"InvoiceId":"<id>","Amount":1500.00,"Vendor":"<vendor>"}' \
  --priority High --reference "<reference>" \
  --defer-date "2026-04-23T09:00:00Z" --due-date "2026-04-25T17:00:00Z" \
  --output json
```

`--specific-content` is required and must be flat key-value JSON. `--priority` is `High`, `Normal`, or `Low` (default `Normal`); `--reference` is at most 128 characters; `--defer-date` and `--due-date` use ISO 8601.

Run `bulk-add` with a queue **name**:

```bash
uip or queue-items bulk-add "<queue-name>" \
  --folder-path "<folder>" \
  --queue-items '[
    {"specificContent":{"InvoiceId":"<id>","Amount":2000},"priority":"High"},
    {"specificContent":{"InvoiceId":"<id>","Amount":750},"priority":"Normal"}
  ]' \
  --commit-type AllOrNothing --output json
```

`--commit-type` is `AllOrNothing` (roll back all if any fail), `StopOnFirstFailure` (commit until the first failure), or `ProcessAllIndependently` (default). Bulk add returns only a success flag and failed items, not created item keys. To obtain keys, run `add` one item at a time or run `list --queue-name` afterward.

### List and Get

```bash
uip or queue-items list --folder-path "<folder>" \
  --queue-name "<queue-name>" --status Failed --output json
uip or queue-items list --all-folders --status Failed --output json
uip or queue-items get <item-unique-key> --folder-path "<folder>" --output json
```

Filter with `--queue-name` (exact match), `--queue-definition-key` (GUID), or `--status`: `New`, `InProgress`, `Failed`, `Successful`, `Abandoned`, `Retried`, or `Deleted`. All queue-item commands require `--folder-path` or `--folder-key`, except `list`, which may use `--all-folders`.

### Update and Delete

```bash
uip or queue-items update <item-unique-key> --folder-path "<folder>" \
  --priority High --output json
uip or queue-items delete <item-unique-key> --folder-path "<folder>" --yes --output json
uip or queue-items delete-bulk <key1> <key2> --folder-path "<folder>" --yes --output json
```

`update` changes only supplied fields: `--priority`, `--due-date`, `--defer-date`, and `--specific-content`. Progress is a work-in-progress message reported by a running robot and cannot be set by the CLI. `delete` and `delete-bulk` are soft deletes: they change status to `Deleted`, not permanently remove items.

### History and Retry Information

```bash
uip or queue-items get-history <item-unique-key> --folder-path "<folder>" --output json
uip or queue-items get-last-retry <item-key> --folder-path "<folder>" --output json
uip or queue-items has-video <item-unique-key> --folder-path "<folder>" --output json
```

`get-last-retry` requires the item `Key`, shared across retries, not `UniqueKey`. Curated list/get output includes both.

## Review Cycle

For failed items, inspect history, assign a reviewer, then retry, abandon, or delete:

```bash
uip or queue-items get-reviewers --folder-path "<folder>" --output json
uip or queue-items set-reviewer <key1> <key2> \
  --folder-path "<folder>" --user-key <reviewer-key> --output json
uip or queue-items set-review-status Retried <key1> <key2> \
  --folder-path "<folder>" --output json
uip or queue-items unset-reviewer <key1> <key2> \
  --folder-path "<folder>" --output json
```

Valid review statuses are `None`, `InReview`, `Verified`, and `Retried`. `set-review-status` takes the status first, followed by one or more item keys. `set-reviewer` requires `--user-key` (a GUID, not a numeric ID); obtain reviewer keys with `get-reviewers`.

## States, Exceptions, and Keys

Items progress as follows:

```text
New --> InProgress --> Successful
                  --> Failed (retryable via ApplicationException)
                  --> Abandoned (manually abandoned)
                  --> Retried (auto-retry created a new attempt)
                  --> Deleted
```

| Exception type | Retryable | Use |
|---|---|---|
| `ApplicationException` | Yes (auto-retry) | Transient failures such as timeout or network error |
| `BusinessException` | No | Invalid data or business-rule violations |

With `--auto-retry`, `ApplicationException` failures retry automatically up to `--max-retries`. Review status flows `None --> InReview (reviewer assigned) --> Verified | Retried`.

| Field | Scope | Use with |
|---|---|---|
| `UniqueKey` | Unique per attempt | `get`, `update`, `delete`, `get-history`, `has-video` |
| `Key` | Shared across retries | `get-last-retry` |
| Queue definition key | Queue identifier | `list --queue-definition-key`, `queues get` |

Curated queue-item rows expose `Key` and `UniqueKey` (PascalCase). With `--all-fields`, raw DTO fields are `key` and `uniqueKey`.

## Common Pitfalls

- Keep `--specific-content` flat; do not use nested objects or arrays.
- Use `--folder-path` or `--folder-key` for queue-item commands; `list` may instead use `--all-folders`.
- Put the review status before item keys in `set-review-status`.
- Pass a GUID to `set-reviewer --user-key`, not a numeric ID.
- Queue `get`, `update`, and `delete` are cross-folder; queue-item commands are folder-scoped.
- `--auto-retry` is enabled by default; disable it with `--no-auto-retry`.

## Related

- [resources.md](resources.md) -- Orchestrator resources overview and libraries
- [Triggers & Webhooks](triggers-and-webhooks.md) -- Queue triggers fire automations when item count exceeds a threshold
- [Setup Environment](setup-environment.md) -- Folder and machine setup