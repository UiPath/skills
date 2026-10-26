# Process Queues

Create queues, add distributed work, track progress, and manage review cycles.

> For full option details, run `uip or queues create --help` (or the relevant command with `--help`).

## When to Use

- Dispatcher-performer distributed processing
- Queue-item review workflows

## Prerequisites

- Run `uip login status`; if unauthenticated, ask the user to run `uip login` (interactive browser flow).
- Target folder exists (`uip or folders list`)

## Queue Management

### Create a Queue

```bash
uip or queues create "InvoiceQueue" \
  --folder-path "Finance" --max-retries 3 --auto-retry \
  --enforce-unique-reference --output json
```

`--max-retries <n>` sets retry attempts. `--auto-retry`/`--no-auto-retry` control automatic `ApplicationException` retries (default: true). `--enforce-unique-reference` rejects duplicate references; `--encrypted` encrypts item data. `--retention-action` and `--stale-retention-action` are `Delete`, `Archive`, or `None` (default: `Delete`); their periods default to 30 and 180 days. `--retention-bucket <bucket-key>` archives completed items; it is required with `--retention-action Archive` and rejected with other actions. `--stale-retention-bucket <bucket-key>` archives uncompleted items and is required with `--stale-retention-action Archive`. Bucket keys are storage-bucket **GUIDs**.

For `Archive`, export occurs before deletion. Get the bucket key from `uip or buckets list --folder-path <folder> --output json` (`Key` column; numeric IDs are rejected). The bucket must be in or shared to the queue folder; otherwise Orchestrator returns `404 Bucket does not exist`. Share it with `uip or buckets share <bucket-key> --folder-path <queue-folder>`. A tenant may require `--encrypted` on every new queue.

```bash
uip or queues create "InvoiceQueue" --folder-path "Finance" \
  --retention-action Archive --retention-bucket <bucket-key> \
  --stale-retention-action Archive --stale-retention-bucket <bucket-key> \
  --output json
```

### List Queues

```bash
uip or queues list --folder-path "Finance" --output json
```

Use `--name` for contains matching and `--limit`/`--offset` for pagination.

### Get, Update, Delete

```bash
uip or queues get <queue-key> --output json
uip or queues update <queue-key> --max-retries 5 --no-auto-retry --output json
uip or queues update <queue-key> --retention-action Delete --output json
uip or queues update <queue-key> --retention-action Archive --retention-bucket <bucket-key> --output json
uip or queues delete <queue-key> --yes --output json
uip or queues delete <queue-key> --force --output json
```

`get`, `update`, and `delete` are cross-folder and need no `--folder-path`. Unprovided update flags retain stored values. Existing archive paths retain their bucket on unrelated edits; `Delete`/`None` clears it. `Archive` requires `--retention-bucket`/`--stale-retention-bucket` unless already stored. Delete refuses while items remain; `--force` deletes the queue and its items.

### Share a Queue Across Folders

```bash
uip or queues share <queue-key> --folder-path "Production" --output json
uip or queues get-folders <queue-key> --output json
uip or queues unshare <queue-key> --folder-path "Production" --output json
```

### Queue Processing Stats

```bash
uip or queues get-stats --folder-path "Finance" --key <queue-key> --output json
uip or queues get-stats --folder-path "Finance" \
  --name "Invoice" \
  --from "2026-04-01T00:00:00Z" --to "2026-04-30T23:59:59Z" \
  --output json
```

`get-stats` returns aggregate totals, successes, failures, and average handling time. Without `--key` or `--name`, it covers every queue in the folder. `--from`/`--to` filter last-processed dates in ISO 8601.

## Queue Item Lifecycle

### Add Items

```bash
uip or queue-items add "InvoiceQueue" \
  --folder-path "Finance" \
  --specific-content '{"InvoiceId":"INV-001","Amount":1500.00,"Vendor":"Acme"}' \
  --priority High --reference "INV-001" \
  --defer-date "2026-04-23T09:00:00Z" --due-date "2026-04-25T17:00:00Z" \
  --output json

uip or queue-items bulk-add "InvoiceQueue" \
  --folder-path "Finance" \
  --queue-items '[
    {"specificContent":{"InvoiceId":"INV-002","Amount":2000},"priority":"High"},
    {"specificContent":{"InvoiceId":"INV-003","Amount":750},"priority":"Normal"}
  ]' \
  --commit-type AllOrNothing \
  --output json
```

`add` and `bulk-add` take a queue **name**, not key. `--specific-content` is required and must be flat key-value JSON. `--priority` is `High`, `Normal`, or `Low` (default `Normal`); `--reference` allows 128 characters; dates use ISO 8601. `--commit-type` is `AllOrNothing` (rollback all on failure), `StopOnFirstFailure` (commit through first failure), or `ProcessAllIndependently` (default). Bulk output has only a success flag and failed items, not created keys; run `add` individually for created items or run `list --queue-name` afterward.

### List and Get Items

```bash
uip or queue-items list --folder-path "Finance" \
  --queue-name "InvoiceQueue" --status Failed --output json
uip or queue-items list --all-folders --status Failed --output json
uip or queue-items get <item-unique-key> --folder-path "Finance" --output json
```

`queue-items list` is filtered `GET /odata/QueueItems`, rate-limited per tenant. Do not poll tightly; keep `--limit` at 100 or below and `SpecificContent` under 256,000 characters. See [api-limits.md](api-limits.md).

Filter with `--queue-name` (exact), `--queue-definition-key` (GUID), or `--status` (`New`, `InProgress`, `Failed`, `Successful`, `Abandoned`, `Retried`, `Deleted`). All item commands require `--folder-path` or `--folder-key`, except `list`, which may use `--all-folders`.

### Update and Delete Items

```bash
uip or queue-items update <item-unique-key> --folder-path "Finance" \
  --priority High --output json
uip or queue-items delete <item-unique-key> --folder-path "Finance" --yes --output json
uip or queue-items delete-bulk <key1> <key2> --folder-path "Finance" --yes --output json
```

`update` changes only supplied `--priority`, `--due-date`, `--defer-date`, and `--specific-content` fields. Progress is a running-robot work-in-progress message; the CLI cannot set it. `delete` and `delete-bulk` soft-delete by setting status `Deleted`; they do not permanently remove items.

### History and Retry Info

```bash
uip or queue-items get-history <item-unique-key> --folder-path "Finance" --output json
uip or queue-items get-last-retry <item-key> --folder-path "Finance" --output json
uip or queue-items has-video <item-unique-key> --folder-path "Finance" --output json
```

`get-last-retry` uses `Key` (shared across retries), not `UniqueKey`; curated list/get output includes both.

## Review Cycle

When items fail, inspect and choose retry, abandon, or delete.

### Assign, Set, and Remove Reviewers

```bash
uip or queue-items get-reviewers --folder-path "Finance" --output json
uip or queue-items set-reviewer <key1> <key2> \
  --folder-path "Finance" --user-key <reviewer-key> --output json
uip or queue-items set-review-status Retried <key1> <key2> \
  --folder-path "Finance" --output json
uip or queue-items unset-reviewer <key1> <key2> \
  --folder-path "Finance" --output json
```

`--user-key` is a reviewer GUID, not numeric ID; find it with `get-reviewers`. Valid review statuses are `None`, `InReview`, `Verified`, and `Retried`; status is first, followed by one or more item keys.

## Complete Example

1. Create: run `uip or queues create "InvoiceQueue" --folder-path "Finance" --max-retries 3 --auto-retry --enforce-unique-reference --output json`.
2. Dispatch: run `uip or queue-items add "InvoiceQueue" --folder-path "Finance" --specific-content '{"InvoiceId":"INV-001","Amount":1500}' --reference "INV-001" --priority High --output json`.
3. After performer execution, run `uip or queue-items list --folder-path "Finance" --queue-name "InvoiceQueue" --status Failed --output json`.
4. Investigate: run `uip or queue-items get-history <failed-item-key> --folder-path "Finance" --output json`.
5. Review: run `uip or queue-items set-reviewer <failed-item-key> --folder-path "Finance" --user-key <reviewer-key> --output json`, then run `uip or queue-items set-review-status Retried <failed-item-key> --folder-path "Finance" --output json`.

## Variations and Gotchas

### Queue Item States

`New --> InProgress --> Successful`; `InProgress` may become `Failed` (retryable via `ApplicationException`), `Abandoned` (manually abandoned), `Retried` (auto-retry created a new attempt), or `Deleted`.

### Exception Types

| Type | Retryable | When to use |
|------|-----------|-------------|
| `ApplicationException` | Yes (auto-retry) | Transient failures (timeout, network error) |
| `BusinessException` | No | Invalid data, business rule violations |

With `--auto-retry`, `ApplicationException` failures retry up to `--max-retries`.

### Review Status Flow

`None --> InReview (reviewer assigned) --> Verified | Retried`

### Key Types

| Field | Scope | Use with |
|-------|-------|----------|
| `UniqueKey` | Unique per attempt | `get`, `update`, `delete`, `get-history`, `has-video` |
| `Key` | Shared across retries | `get-last-retry` |
| Queue definition key | Queue identifier | `list --queue-definition-key`, `queues get` |

Curated queue-item rows expose `Key` and `UniqueKey` (PascalCase); with `--all-fields`, raw DTO fields are `key`/`uniqueKey`.

### Common Pitfalls

- `--specific-content` must be flat key-value JSON: no nested objects or arrays.
- `set-review-status` takes status first, then item key(s).
- `set-reviewer` requires `--user-key` (GUID, not numeric ID).
- Queue `get`, `update`, and `delete` are cross-folder; queue-item commands are not.
- `--auto-retry` is enabled by default; run with `--no-auto-retry` to disable.

## Related

- [resources.md](resources.md) -- Orchestrator resources overview and libraries
- [Triggers & Webhooks](triggers-and-webhooks.md) -- Queue triggers fire automations when item count exceeds a threshold
- [Business ROI](business-roi.md) -- `uip or queue-roi`: the manual time, volume and cost a queue saves
- [Setup Environment](setup-environment.md) -- Folder and machine setup