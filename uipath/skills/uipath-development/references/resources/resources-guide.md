# Resources Tool Guide

Comprehensive guide for the UiPath Resources CLI tool (`uip resources`) — managing assets, queues, queue items, storage buckets, and storage bucket files in Orchestrator.

> **Tip:** For full option details on any command, use `--help` (e.g., `uip resources assets create --help`)

## Overview

The Resources tool provides CLI access to Orchestrator resource management. All commands use the `resources` prefix and require authentication (`uip login`).

**Important:** Assets use nested subcommands (`uip resources assets <action>`), while queues and storage buckets use flat hyphenated commands (`uip resources queues-create`, `uip resources storage-buckets-list`, etc.).

```
uip resources
  ├── assets                    ← Nested subcommands (assets list, assets create, etc.)
  │     ├── list
  │     ├── get
  │     ├── create
  │     ├── update
  │     └── delete
  ├── queues-create             ← Flat hyphenated commands
  ├── queues-delete
  ├── queues-add-items
  ├── queues-get-item
  ├── queues-set-result
  ├── queues-delete-item
  ├── storage-buckets-list      ← Flat hyphenated commands
  ├── storage-buckets-get
  ├── storage-buckets-create
  ├── storage-buckets-delete
  ├── storage-buckets-read-file
  ├── storage-buckets-write-file
  └── storage-buckets-delete-file
```

> **Always use `--format json`** when calling commands programmatically.

> **Note:** There is no `queues list` command. To discover queues, use the Orchestrator UI or REST API.

---

## Assets

Assets are key-value pairs stored in Orchestrator that automations can read at runtime.

| Command | Syntax | Description |
|---------|--------|-------------|
| **list** | `uip resources assets list <parent-folder-id> --format json` | List all assets in a folder |
| **get** | `uip resources assets get <parent-folder-id> <asset-id> --format json` | Get a specific asset by ID |
| **create** | `uip resources assets create <parent-folder-id> <name> <value> --format json` | Create a new asset |
| **update** | `uip resources assets update <parent-folder-id> <asset-id> [value] --format json` | Update an existing asset |
| **delete** | `uip resources assets delete <parent-folder-id> <asset-id> --format json` | Delete an asset |

**Asset types:** Text (default), Bool, Integer, Credential, Secret, DBConnectionString, HttpConnectionString, WindowsCredential

**Example:**
```bash
uip resources assets create 12345 "ApiKey" "sk-abc123" --type Secret --format json
```

---

## Queues

Queues enable distributed processing of work items across multiple robots using the dispatcher-performer pattern.

| Command | Syntax | Description |
|---------|--------|-------------|
| **create** | `uip resources queues-create <parent-folder-id> <name> --format json` | Create a new queue |
| **delete** | `uip resources queues-delete <parent-folder-id> <queue-id> --format json` | Delete a queue by ID |

**Example:**
```bash
uip resources queues-create 12345 "InvoiceQueue" --max-retries 3 --auto-retry --format json
```

---

## Queue Items

Individual work items within a queue.

| Command | Syntax | Description |
|---------|--------|-------------|
| **add-items** | `uip resources queues-add-items <parent-folder-id> <queue-name> --format json` | Add an item to a queue |
| **get-item** | `uip resources queues-get-item <parent-folder-id> <item-id> --format json` | Get a specific queue item |
| **set-result** | `uip resources queues-set-result <parent-folder-id> <item-id> --format json` | Set processing result of an item |
| **delete-item** | `uip resources queues-delete-item <parent-folder-id> <item-id> --format json` | Delete a queue item |

**Example:**
```bash
uip resources queues-add-items 12345 "InvoiceQueue" \
  --specific-content '{"InvoiceId":"INV-001","Amount":1500}' \
  -r "INV-001" \
  -p High \
  --format json
```

---

## Storage Buckets

Storage buckets provide file storage for automation data within Orchestrator folders.

| Command | Syntax | Description |
|---------|--------|-------------|
| **list** | `uip resources storage-buckets-list <parent-folder-id> --format json` | List all storage buckets |
| **get** | `uip resources storage-buckets-get <parent-folder-id> <bucket-id> --format json` | Get a specific bucket |
| **create** | `uip resources storage-buckets-create <parent-folder-id> <name> --format json` | Create a new bucket |
| **delete** | `uip resources storage-buckets-delete <parent-folder-id> <bucket-id> --format json` | Delete a bucket |

**Example:**
```bash
uip resources storage-buckets-create 12345 "InvoiceDocuments" \
  -d "Scanned invoice PDFs for processing" \
  --format json
```

---

## Storage Bucket Files

File operations within storage buckets.

| Command | Syntax | Description |
|---------|--------|-------------|
| **read-file** | `uip resources storage-buckets-read-file <parent-folder-id> <bucket-id> <path>` | Download a file |
| **write-file** | `uip resources storage-buckets-write-file <parent-folder-id> <bucket-id> <path> --format json` | Upload a file |
| **delete-file** | `uip resources storage-buckets-delete-file <parent-folder-id> <bucket-id> <path> --format json` | Delete a file |

**Example:**
```bash
uip resources storage-buckets-write-file 12345 67890 "invoices/INV-001.pdf" \
  --file ./INV-001.pdf \
  --format json
```

---

## Common Patterns

### Environment Setup with Assets

```bash
uip or folders list --format json
uip resources assets create 12345 "ApiBaseUrl" "https://api.example.com" --format json
uip resources assets create 12345 "ApiKey" "sk-production-key" --type Secret --format json
uip resources assets create 12345 "MaxRetries" "3" --type Integer --format json
uip resources assets create 12345 "DebugMode" "false" --type Bool --format json
```

### Dispatcher-Performer Queue Pattern

```bash
uip resources queues-create 12345 "InvoiceQueue" --max-retries 3 --auto-retry --format json

uip resources queues-add-items 12345 "InvoiceQueue" \
  --specific-content '{"InvoiceId":"INV-001","Amount":1500,"Vendor":"Acme"}' \
  -r "INV-001" -p Normal --format json

uip resources queues-add-items 12345 "InvoiceQueue" \
  --specific-content '{"InvoiceId":"INV-002","Amount":2300,"Vendor":"Globex"}' \
  -r "INV-002" -p High --format json

uip resources queues-set-result 12345 <item-id> \
  --success \
  --output '{"ProcessedAt":"2024-01-15","ApprovalStatus":"Approved"}' \
  --format json
```

### Storage Bucket Workflow

```bash
uip resources storage-buckets-create 12345 "ProcessedDocuments" \
  -d "Processed automation output files" --format json

uip resources storage-buckets-write-file 12345 99999 "reports/monthly-2024-01.pdf" \
  --file ./output/report.pdf --format json

uip resources storage-buckets-read-file 12345 99999 "reports/monthly-2024-01.pdf" \
  -o ./downloads/report.pdf

uip resources storage-buckets-delete-file 12345 99999 "reports/monthly-2024-01.pdf" --format json
```

---

## Known Limitations

- There is no `queues list` command to list queues in a folder. Use the Orchestrator UI or REST API to discover existing queues.
- There is no `queue-items list` command to list items in a queue. Use `queues-get-item` with a known item ID, or the Orchestrator UI.
- The `or` tool does NOT have asset commands. Use `resources assets` for all asset operations.

---

## Troubleshooting

If a command fails unexpectedly, try updating the tool: `uip tools install @uipath/resources-tool`
