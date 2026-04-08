# Resources Tool Guide

CLI tool for managing Orchestrator assets, queues, queue items, storage buckets, and files (`uip resource`).

> Use `uip resource --help` to discover all commands and options. Use `--output json` when calling programmatically.

## Overview

All commands require authentication (`uip login`). All subcommands use **nested syntax**.

```
uip resource
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
| `uip resource assets list <folder-id>` | List assets in a folder |
| `uip resource assets create <folder-id> <name> <value>` | Create an asset |
| `uip resource assets update <folder-id> <asset-id> [value]` | Update an asset |
| `uip resource assets delete <folder-id> <asset-id>` | Delete an asset |

**Asset types:** Text (default), Bool, Integer, Credential, Secret, DBConnectionString, HttpConnectionString, WindowsCredential

```bash
uip resource assets create 12345 "ApiKey" "sk-abc123" --type Secret --output json
```

### Queues & Queue Items

| Command | Description |
|---------|-------------|
| `uip resource queues list <folder-id>` | List queues in a folder |
| `uip resource queues create <folder-id> <name>` | Create a queue |
| `uip resource queues delete <folder-id> <queue-id>` | Delete a queue |
| `uip resource queue-items list <folder-id>` | List queue items (use --filter to narrow, e.g. `"QueueDefinitionId eq 123"`) |
| `uip resource queue-items create <folder-id> <queue-name>` | Add item to queue |
| `uip resource queue-items get <folder-id> <item-id>` | Get queue item |
| `uip resource queue-items set-result <folder-id> <item-id>` | Set item result (--success or --fail) |
| `uip resource queue-items delete <folder-id> <item-id>` | Delete queue item |

```bash
uip resource queue-items create 12345 "InvoiceQueue" \
  --specific-content '{"InvoiceId":"INV-001","Amount":1500}' \
  -r "INV-001" -p High --output json
```

### Storage Buckets & Files

| Command | Description |
|---------|-------------|
| `uip resource storage-buckets list <folder-id>` | List storage buckets |
| `uip resource storage-buckets create <folder-id> <name>` | Create a bucket |
| `uip resource storage-buckets delete <folder-id> <bucket-id>` | Delete a bucket |
| `uip resource storage-bucket-files read <folder-id> <bucket-id> <path>` | Download a file |
| `uip resource storage-bucket-files write <folder-id> <bucket-id> <path>` | Upload a file |
| `uip resource storage-bucket-files delete <folder-id> <bucket-id> <path>` | Delete a file |

```bash
uip resource storage-bucket-files write 12345 67890 "invoices/INV-001.pdf" \
  --file ./INV-001.pdf --output json
```

---

## Common Patterns

### Environment Setup with Assets

```bash
uip or folders list --output json
uip resource assets create 12345 "ApiBaseUrl" "https://api.example.com" --output json
uip resource assets create 12345 "ApiKey" "sk-production-key" --type Secret --output json
uip resource assets create 12345 "MaxRetries" "3" --type Integer --output json
```

### Dispatcher-Performer Queue Pattern

```bash
uip resource queues create 12345 "InvoiceQueue" --max-retries 3 --auto-retry --output json

uip resource queue-items create 12345 "InvoiceQueue" \
  --specific-content '{"InvoiceId":"INV-001","Amount":1500}' \
  -r "INV-001" -p High --output json

uip resource queue-items set-result 12345 <item-id> \
  --success --output '{"Status":"Approved"}' --output json
```

---

## Troubleshooting

If a command fails unexpectedly:
1. Verify the command syntax: `uip resource <command> --help`
2. Check authentication: `uip login status`
3. As a last resort, update the tool: `uip tools install @uipath/resources-tool`
