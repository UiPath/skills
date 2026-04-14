# Resources Tool Guide

CLI tool for managing Orchestrator resources: assets, queues, queue items, storage buckets, files, triggers, libraries, and webhooks (`uip resource`).

> Use `uip resource --help` to discover all commands and options. Use `--output json` when calling programmatically.

## Overview

All commands require authentication (`uip login`). Folder-scoped commands use `--folder-path` or `--folder-key` to target a folder.

```
uip resource
  ├── assets               ← list, get, create, update, delete, share, unshare, get-asset-value
  ├── queues               ← list, get, create, update, delete, share, unshare
  ├── queue-items          ← list, get, add, bulk-add, update, set-result, start-transaction, delete, delete-bulk, history, reviews
  ├── triggers             ← list, get, create, update, delete, enable, disable (time/queue/API)
  ├── storage-buckets      ← list, get, create, update, delete
  ├── storage-bucket-files ← list, read, write, delete
  ├── libraries            ← list, versions, upload, download, delete
  └── webhooks             ← list, get, create, update, delete, ping, event-types
```

---

## Key Commands

### Assets

| Command | Description |
|---------|-------------|
| `uip resource assets list` | List assets in folder (`--folder-path` or `--folder-key`) |
| `uip resource assets get <key>` | Get asset details by key (GUID) |
| `uip resource assets create <name>` | Create asset (`--folder-path`, `--type`, `--scope`) |
| `uip resource assets update <key>` | Update asset properties |
| `uip resource assets delete <key>` | Delete asset |
| `uip resource assets get-asset-value <key>` | Get decrypted asset value |
| `uip resource assets get-folders <key>` | Get all folders where asset is shared |
| `uip resource assets share <key>` | Share asset with folder (`--folder-path`) |
| `uip resource assets unshare <key>` | Remove asset from folder (`--folder-path`) |

**Asset types:** Text (default), Bool, Integer, Credential, Secret, DBConnectionString, HttpConnectionString, WindowsCredential

```bash
uip resource assets list --folder-path "Finance" --output json
uip resource assets create "ApiKey" "sk-abc123" --type Secret --folder-path "Finance" --output json
```

### Queues & Queue Items

| Command | Description |
|---------|-------------|
| `uip resource queues list` | List queues (`--folder-path` or `--folder-key`) |
| `uip resource queues get <key>` | Get queue details by key (GUID) |
| `uip resource queues create <name>` | Create queue (`--folder-path`, `--max-retries`, `--auto-retry`) |
| `uip resource queues update <key>` | Update queue properties |
| `uip resource queues delete <key>` | Delete queue |
| `uip resource queues share <key>` | Share queue with folder |
| `uip resource queues get-folders <key>` | Get all folders where queue is shared |
| `uip resource queue-items list` | List items (`--folder-path`, `--queue-name`, `--status`) |
| `uip resource queue-items get <key>` | Get queue item details |
| `uip resource queue-items add <queue-name>` | Add item to queue (`--specific-content` for JSON payload, `--reference`, `--priority`) |
| `uip resource queue-items bulk-add <queue-key>` | Add items from CSV/JSON (`--file`) |
| `uip resource queue-items update <key>` | Update item priority/reference |
| `uip resource queue-items set-result <key>` | Set item result (`--status`, `--output`) |
| `uip resource queue-items set-progress <key>` | Update progress text (`--progress-text` required) |
| `uip resource queue-items start-transaction <key>` | Mark item as InProgress |
| `uip resource queue-items delete <key>` | Delete queue item |
| `uip resource queue-items delete-bulk <keys>` | Delete multiple items |
| `uip resource queue-items get-history <key>` | Get status change history |
| `uip resource queue-items get-last-retry <key>` | Get last retry info for failed items |
| `uip resource queue-items has-video <key>` | Check if item has video recording |
| `uip resource queue-items set-review-status <key>` | Set review status (Approved/Rejected) |
| `uip resource queue-items set-reviewer <key>` | Assign reviewer |
| `uip resource queue-items unset-reviewer <key>` | Remove reviewer |
| `uip resource queue-items get-reviewers <key>` | Get assigned reviewers |

```bash
uip resource queues list --folder-path "Finance" --output json
uip resource queue-items add "InvoiceQueue" \
  --folder-path "Finance" --specific-content '{"InvoiceId":"INV-001","Amount":1500}' \
  --reference "INV-001" --priority High --output json
```

### Triggers

| Command | Description |
|---------|-------------|
| `uip resource triggers list` | List triggers (`--type time\|queue\|api`, `--folder-path`) |
| `uip resource triggers get <key>` | Get trigger details (`--type` required) |
| `uip resource triggers create` | Create trigger (`--type`, `--name`, `--release-key`, `--cron` for time triggers, `--queue-key` for queue triggers) |
| `uip resource triggers update <key>` | Update trigger properties |
| `uip resource triggers delete <key>` | Delete trigger (`--type` required) |
| `uip resource triggers enable <key>` | Enable trigger(s) |
| `uip resource triggers disable <key>` | Disable trigger(s) |
| `uip resource triggers history <key>` | Get trigger execution logs (`--folder-path` required) |

**Trigger types:**
- **time** — Cron-based scheduling (use `--cron`, `--time-zone`, optional `--calendar-key` to skip holidays)
- **queue** — Fires when queue item count exceeds threshold (`--queue-key`, `--items-threshold`, `--max-jobs`)
- **api** — HTTP webhook trigger (`--slug`, `--method`, `--calling-mode`)

```bash
# List time triggers in a folder
uip resource triggers list --type time --folder-path "Finance" --output json

# Create a time trigger (every weekday at 9 AM UTC)
uip resource triggers create --type time --name "DailyInvoice" \
  --release-key <process-key> --cron "0 9 * * 1-5" --time-zone "UTC" \
  --runtime-type Unattended --job-priority Normal \
  --folder-path "Finance" --output json

# Create a queue trigger
uip resource triggers create --type queue --name "InvoiceQueueTrigger" \
  --release-key <process-key> --queue-key <queue-key> \
  --items-threshold 1 --max-jobs 3 \
  --runtime-type Unattended --job-priority Normal \
  --folder-path "Finance" --output json
```

### Storage Buckets & Files

| Command | Description |
|---------|-------------|
| `uip resource storage-buckets list` | List buckets (`--folder-path` or `--folder-key`) |
| `uip resource storage-buckets get <key>` | Get bucket details |
| `uip resource storage-buckets create <name>` | Create bucket (`--folder-path`) |
| `uip resource storage-buckets update <key>` | Update bucket |
| `uip resource storage-buckets delete <key>` | Delete bucket |
| `uip resource storage-bucket-files list <bucket-key>` | List files in bucket |
| `uip resource storage-bucket-files read <bucket-key> <path>` | Download file (`--destination`) |
| `uip resource storage-bucket-files write <bucket-key> <path>` | Upload file (`--file`) |
| `uip resource storage-bucket-files delete <bucket-key> <path>` | Delete file |

```bash
uip resource storage-buckets list --folder-path "Finance" --output json
uip resource storage-bucket-files write <bucket-key> "invoices/INV-001.pdf" \
  --folder-path "Finance" --file ./INV-001.pdf --output json
```

### Libraries

| Command | Description |
|---------|-------------|
| `uip resource libraries list` | List libraries in tenant feed |
| `uip resource libraries versions <package-id>` | List all versions of a library |
| `uip resource libraries upload` | Upload .nupkg library to feed (`--file`) |
| `uip resource libraries download <key>` | Download library .nupkg (`--destination`) |
| `uip resource libraries delete <key>` | Delete library version |

### Webhooks

| Command | Description |
|---------|-------------|
| `uip resource webhooks list` | List webhooks in tenant |
| `uip resource webhooks get <key>` | Get webhook details |
| `uip resource webhooks create` | Create webhook (`--name`, `--url`, `--events`) |
| `uip resource webhooks update <key>` | Update webhook |
| `uip resource webhooks delete <key>` | Delete webhook |
| `uip resource webhooks ping <key>` | Send test ping |
| `uip resource webhooks event-types` | List available event types |

---

## Common Patterns

### Environment Setup with Assets

```bash
uip or folders list --output json
uip resource assets create "ApiBaseUrl" "https://api.example.com" --folder-path "Finance" --output json
uip resource assets create "ApiKey" "sk-production-key" --type Secret --folder-path "Finance" --output json
uip resource assets create "MaxRetries" "3" --type Integer --folder-path "Finance" --output json
```

### Dispatcher-Performer Queue Pattern

```bash
uip resource queues create "InvoiceQueue" --folder-path "Finance" --max-retries 3 --auto-retry --output json

uip resource queue-items add <queue-key> "INV-001" \
  --folder-path "Finance" --data '{"InvoiceId":"INV-001","Amount":1500}' \
  --priority High --output json
```

### Schedule a Time Trigger

```bash
uip resource triggers create --type time --name "NightlyReport" \
  --release-key <process-key> --cron "0 2 * * *" --time-zone "Europe/Bucharest" \
  --runtime-type Unattended --job-priority Normal \
  --folder-path "Finance" --output json
```

---

## Output Behavior

Resource tool commands return **full API responses** (all fields) by default — no `--all-fields` flag needed.

List commands include a `Pagination` block:

```json
{
  "Pagination": { "Returned": 50, "Limit": 50, "Offset": 0, "HasMore": true },
  "Data": [...]
}
```

When `HasMore` is `true`, increase `--offset` to fetch the next page.

---

## Troubleshooting

If a command fails unexpectedly:
1. Verify the command syntax: `uip resource <command> --help`
2. Check authentication: `uip login status`
3. As a last resort, update the tool: `uip tools install @uipath/resources-tool`
