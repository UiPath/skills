# Resources Tool Guide

CLI tool for managing Orchestrator assets, queues, queue items, storage buckets, and files (`uip resources`).

> Use `uip resources --help` to discover all commands and options. Use `--format json` when calling programmatically.

## Overview

All commands require authentication (`uip login`). All subcommands use **nested syntax**.

```
uip resources
  ├── assets              ← list, get, create, update, delete
  ├── queues              ← list, create, delete
  ├── queue-items         ← list, create, get, set-result, delete
  ├── storage-buckets     ← list, get, create, delete
  └── storage-bucket-files ← read, write, delete
```

---

## Key Commands

### Assets

| Command | Description |
|---------|-------------|
| `uip resources assets list <folder-id>` | List assets in a folder |
| `uip resources assets create <folder-id> <name> <value>` | Create an asset |
| `uip resources assets update <folder-id> <asset-id> [value]` | Update an asset |
| `uip resources assets delete <folder-id> <asset-id>` | Delete an asset |

**Asset types:** Text (default), Bool, Integer, Credential, Secret, DBConnectionString, HttpConnectionString, WindowsCredential

```bash
uip resources assets create 12345 "ApiKey" "sk-abc123" --type Secret --format json
```

### Queues & Queue Items

| Command | Description |
|---------|-------------|
| `uip resources queues list <folder-id>` | List queues in a folder |
| `uip resources queues create <folder-id> <name>` | Create a queue |
| `uip resources queues delete <folder-id> <queue-id>` | Delete a queue |
| `uip resources queue-items list <folder-id>` | List queue items (use --filter to narrow, e.g. `"QueueDefinitionId eq 123"`) |
| `uip resources queue-items create <folder-id> <queue-name>` | Add item to queue |
| `uip resources queue-items get <folder-id> <item-id>` | Get queue item |
| `uip resources queue-items set-result <folder-id> <item-id>` | Set item result (--success or --fail) |
| `uip resources queue-items delete <folder-id> <item-id>` | Delete queue item |

```bash
uip resources queue-items create 12345 "InvoiceQueue" \
  --specific-content '{"InvoiceId":"INV-001","Amount":1500}' \
  -r "INV-001" -p High --format json
```

### Storage Buckets & Files

| Command | Description |
|---------|-------------|
| `uip resources storage-buckets list <folder-id>` | List storage buckets |
| `uip resources storage-buckets create <folder-id> <name>` | Create a bucket |
| `uip resources storage-buckets delete <folder-id> <bucket-id>` | Delete a bucket |
| `uip resources storage-bucket-files read <folder-id> <bucket-id> <path>` | Download a file |
| `uip resources storage-bucket-files write <folder-id> <bucket-id> <path>` | Upload a file |
| `uip resources storage-bucket-files delete <folder-id> <bucket-id> <path>` | Delete a file |

```bash
uip resources storage-bucket-files write 12345 67890 "invoices/INV-001.pdf" \
  --file ./INV-001.pdf --format json
```

---

## Common Patterns

### Environment Setup with Assets

```bash
uip or folders list --format json
uip resources assets create 12345 "ApiBaseUrl" "https://api.example.com" --format json
uip resources assets create 12345 "ApiKey" "sk-production-key" --type Secret --format json
uip resources assets create 12345 "MaxRetries" "3" --type Integer --format json
```

### Dispatcher-Performer Queue Pattern

```bash
uip resources queues create 12345 "InvoiceQueue" --max-retries 3 --auto-retry --format json

uip resources queue-items create 12345 "InvoiceQueue" \
  --specific-content '{"InvoiceId":"INV-001","Amount":1500}' \
  -r "INV-001" -p High --format json

uip resources queue-items set-result 12345 <item-id> \
  --success --output '{"Status":"Approved"}' --format json
```

---

## Troubleshooting

If a command fails unexpectedly:
1. Verify the command syntax: `uip resources <command> --help`
2. Check authentication: `uip login status`
3. As a last resort, update the tool: `uip tools install @uipath/resources-tool`
