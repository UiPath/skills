# Queues

Orchestrator queues — distributed work item processing across multiple robots.

> **Concepts** are documented in [../orchestrator/orchestrator-guide.md - Queues](../orchestrator/orchestrator-guide.md). This file covers the `resources` CLI commands for queue management.

## How Queues Work

1. **Dispatcher** automation adds items to a queue
2. **Performer** automation(s) process items from the queue
3. Orchestrator handles distribution, retries, and status tracking

## CLI Commands

### Create Queue

```bash
uip resources queues-create --folder-id <folder-id> --name "InvoiceQueue" --format json
```

With retry and uniqueness options:
```bash
uip resources queues-create --folder-id <folder-id> --name "InvoiceQueue" \
  --max-retries 3 \
  --unique-reference \
  --description "Invoice processing queue" \
  --format json
```

### Add Items to Queue

Single item:
```bash
uip resources queues-add-items --folder-id <folder-id> --queue-name "InvoiceQueue" \
  --items '[{"SpecificContent":{"InvoiceId":"INV-001","Amount":1500.00,"CustomerName":"Acme Corp"},"Priority":"Normal"}]' \
  --format json
```

Bulk items:
```bash
uip resources queues-add-items --folder-id <folder-id> --queue-name "InvoiceQueue" \
  --items '[
    {"SpecificContent":{"InvoiceId":"INV-001","Amount":1500.00},"Priority":"High"},
    {"SpecificContent":{"InvoiceId":"INV-002","Amount":750.00},"Priority":"Normal"},
    {"SpecificContent":{"InvoiceId":"INV-003","Amount":3200.00},"Priority":"Low"}
  ]' \
  --format json
```

### Get Queue Item

```bash
uip resources queues-get-item --folder-id <folder-id> --item-id <queue-item-id> --format json
```

### Set Queue Item Result

Mark an item as successful:
```bash
uip resources queues-set-result --folder-id <folder-id> --item-id <queue-item-id> \
  --status Successful \
  --format json
```

Mark an item as failed:
```bash
uip resources queues-set-result --folder-id <folder-id> --item-id <queue-item-id> \
  --status Failed \
  --exception-type "BusinessException" \
  --exception-reason "Invoice amount exceeds limit" \
  --format json
```

### Delete Queue

```bash
uip resources queues-delete --folder-id <folder-id> --queue-id <queue-id> --format json
```

### Delete Queue Item

Soft delete — marks the item as Deleted:
```bash
uip resources queues-delete-item --folder-id <folder-id> --item-id <queue-item-id> --format json
```

## Queue Item States

| State | Description |
|---|---|
| **New** | Added to queue, awaiting processing |
| **InProgress** | Currently being processed by a robot |
| **Successful** | Completed successfully |
| **Failed** | Failed (may be retried based on queue config) |
| **Abandoned** | Exceeded max retry attempts |
| **Deleted** | Soft-deleted from the queue |

## Queue Item Properties

| Property | Description |
|---|---|
| **SpecificContent** | JSON payload with the data to process |
| **Priority** | `High`, `Normal`, `Low` |
| **Reference** | Optional unique reference for deduplication |
| **DeferDate** | Earliest date/time the item can be processed |
| **DueDate** | Deadline for processing the item |

## Dispatcher-Performer Pattern

A common automation pattern using queues:

```
Dispatcher Process                    Orchestrator Queue                   Performer Process(es)
┌─────────────────┐                  ┌──────────────────┐                 ┌───────────────────┐
│ Read data source │ ──add items──▶  │ InvoiceQueue     │ ──get item──▶  │ Process invoice   │
│ (Excel, DB, API) │                 │ • INV-001 (New)  │                 │ Set result        │
│ Add to queue     │                 │ • INV-002 (New)  │                 │ (Success/Fail)    │
└─────────────────┘                  │ • INV-003 (Done) │                 └───────────────────┘
                                     └──────────────────┘
```
