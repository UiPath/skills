# Resources Tool Guide

Comprehensive guide for the UiPath Resources CLI tool (`uip resources`) — managing assets, queues, queue items, storage buckets, and storage bucket files in Orchestrator.

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

Assets are key-value pairs stored in Orchestrator that automations can read at runtime. They externalize configuration so the same automation package works across environments.

### Asset Types

| Type | Description | Example |
|------|-------------|---------|
| **Text** | Plain text string | API URL, file path |
| **Bool** | Boolean value | Feature flag |
| **Integer** | Numeric value | Retry count, timeout |
| **Credential** | Username + password pair | Service account |
| **Secret** | Encrypted secret value | API key, token |
| **DBConnectionString** | Database connection string | SQL Server connection |
| **HttpConnectionString** | HTTP endpoint connection | REST API base URL |
| **WindowsCredential** | Windows credential pair | Domain login |

### Asset Scope

| Scope | Description |
|-------|-------------|
| **Global** | Same value for all robots (default) |
| **PerRobot** | Different value per robot (allows overrides) |

### `uip resources assets list <parent-folder-id>`

List all assets in a folder.

```bash
uip resources assets list <parent-folder-id> [options] --format json
```

| Option | Description | Default |
|--------|-------------|---------|
| `-t, --tenant <name>` | Tenant override | Current tenant |
| `-f, --filter <filter>` | OData filter expression | -- |
| `-c, --count <number>` | Number of items to return | 50 |

**Examples:**
```bash
# List all assets in folder 12345
uip resources assets list 12345 --format json

# Filter by name
uip resources assets list 12345 --filter "Name eq 'ApiKey'" --format json

# Return more items
uip resources assets list 12345 --count 100 --format json
```

### `uip resources assets get <parent-folder-id> <asset-id>`

Get a specific asset by ID.

```bash
uip resources assets get <parent-folder-id> <asset-id> [options] --format json
```

| Option | Description | Default |
|--------|-------------|---------|
| `-t, --tenant <name>` | Tenant override | Current tenant |

### `uip resources assets create <parent-folder-id> <name> <value>`

Create a new asset.

```bash
uip resources assets create <parent-folder-id> <name> <value> [options] --format json
```

| Option | Description | Default |
|--------|-------------|---------|
| `-t, --tenant <name>` | Tenant override | Current tenant |
| `--type <type>` | Asset type (see Asset Types table) | Text |
| `-s, --scope <scope>` | Asset scope (Global, PerRobot) | Global |
| `-d, --description <desc>` | Asset description | -- |
| `--has-default` | Asset has a default value | true |
| `--tags <tags>` | Comma-separated tag names | -- |

**Examples:**
```bash
# Text asset
uip resources assets create 12345 "ApiBaseUrl" "https://api.example.com" --format json

# Secret asset
uip resources assets create 12345 "ApiKey" "sk-abc123" --type Secret --format json

# Integer asset with description and tags
uip resources assets create 12345 "MaxRetries" "3" --type Integer -d "Max retry attempts" --tags "config,performance" --format json

# Credential asset (username:password)
uip resources assets create 12345 "ServiceAccount" "user:password" --type Credential --format json

# Boolean asset
uip resources assets create 12345 "FeatureEnabled" "true" --type Bool --format json
```

### `uip resources assets update <parent-folder-id> <asset-id> [value]`

Update an existing asset.

```bash
uip resources assets update <parent-folder-id> <asset-id> [value] [options] --format json
```

| Option | Description | Default |
|--------|-------------|---------|
| `-t, --tenant <name>` | Tenant override | Current tenant |
| `--type <type>` | Change asset type | -- |
| `-s, --scope <scope>` | Change asset scope | -- |
| `-n, --name <name>` | Rename asset | -- |
| `-d, --description <desc>` | Update description | -- |
| `--tags <tags>` | Update tags (comma-separated) | -- |

**Examples:**
```bash
# Update value only
uip resources assets update 12345 67890 "https://new-api.example.com" --format json

# Update name and description
uip resources assets update 12345 67890 -n "NewApiUrl" -d "Updated API endpoint" --format json
```

### `uip resources assets delete <parent-folder-id> <asset-id>`

Delete an asset.

```bash
uip resources assets delete <parent-folder-id> <asset-id> [options] --format json
```

| Option | Description | Default |
|--------|-------------|---------|
| `-t, --tenant <name>` | Tenant override | Current tenant |

---

## Queues

Queues enable distributed processing of work items across multiple robots using the dispatcher-performer pattern.

### Queue Concepts

1. **Dispatcher** automation adds items to a queue
2. **Performer** automation(s) process items from the queue
3. Orchestrator handles distribution, retries, and status tracking

### `uip resources queues-create <parent-folder-id> <name>`

Create a new queue.

```bash
uip resources queues-create <parent-folder-id> <name> [options] --format json
```

| Option | Description | Default |
|--------|-------------|---------|
| `-t, --tenant <name>` | Tenant override | Current tenant |
| `-d, --description <text>` | Queue description | -- |
| `--max-retries <number>` | Maximum retry attempts | -- |
| `--auto-retry` | Auto-retry items that fail with ApplicationException | Off |
| `--enforce-unique-reference` | Enforce unique reference values | Off |

**Examples:**
```bash
# Simple queue
uip resources queues-create 12345 "InvoiceQueue" --format json

# Queue with retries and unique references
uip resources queues-create 12345 "OrderQueue" \
  -d "Order processing queue" \
  --max-retries 3 \
  --auto-retry \
  --enforce-unique-reference \
  --format json
```

### `uip resources queues-delete <parent-folder-id> <queue-id>`

Delete a queue by ID.

```bash
uip resources queues-delete <parent-folder-id> <queue-id> [options] --format json
```

| Option | Description | Default |
|--------|-------------|---------|
| `-t, --tenant <name>` | Tenant override | Current tenant |

---

## Queue Items

Individual work items within a queue.

### Queue Item States

| Status | Description |
|--------|-------------|
| **New** | Waiting to be processed |
| **InProgress** | Currently being processed by a robot |
| **Successful** | Completed successfully |
| **Failed** | Processing failed |
| **Abandoned** | Exceeded retry limit |
| **Deleted** | Removed from queue |

### `uip resources queues-add-items <parent-folder-id> <queue-name>`

Add an item to a queue.

```bash
uip resources queues-add-items <parent-folder-id> <queue-name> [options] --format json
```

| Option | Description | Default |
|--------|-------------|---------|
| `-t, --tenant <name>` | Tenant override | Current tenant |
| `-r, --reference <ref>` | User-defined identifier (max 128 chars) | -- |
| `-p, --priority <priority>` | Priority: High, Normal, Low | Normal |
| `--specific-content <json>` | Custom data payload as flat JSON object (values must be simple types — no nested objects/arrays) | -- |
| `--defer-date <datetime>` | Earliest processing date (ISO 8601) | -- |
| `--due-date <datetime>` | Latest processing date (ISO 8601) | -- |

**Examples:**
```bash
# Simple queue item
uip resources queues-add-items 12345 "InvoiceQueue" \
  --specific-content '{"InvoiceId":"INV-001","Amount":1500}' \
  --format json

# High-priority item with reference and due date
uip resources queues-add-items 12345 "OrderQueue" \
  -r "ORD-2024-001" \
  -p High \
  --specific-content '{"OrderId":"ORD-001","CustomerName":"Acme Corp"}' \
  --due-date "2024-12-31T23:59:59Z" \
  --format json

# Deferred item (process after a specific date)
uip resources queues-add-items 12345 "ScheduledQueue" \
  --specific-content '{"TaskId":"TASK-001"}' \
  --defer-date "2024-06-01T08:00:00Z" \
  --format json
```

### `uip resources queues-get-item <parent-folder-id> <item-id>`

Get a specific queue item by ID.

```bash
uip resources queues-get-item <parent-folder-id> <item-id> [options] --format json
```

| Option | Description | Default |
|--------|-------------|---------|
| `-t, --tenant <name>` | Tenant override | Current tenant |

### `uip resources queues-set-result <parent-folder-id> <item-id>`

Set the processing result of a queue item.

```bash
uip resources queues-set-result <parent-folder-id> <item-id> [options] --format json
```

| Option | Description | Default |
|--------|-------------|---------|
| `-t, --tenant <name>` | Tenant override | Current tenant |
| `--success` | Mark as successfully processed | -- |
| `--fail` | Mark as failed | -- |
| `--reason <text>` | Reason for failure (used with --fail) | -- |
| `--details <text>` | Additional failure details (used with --fail) | -- |
| `--exception-type <type>` | ApplicationException (retryable) or BusinessException (non-retryable) | ApplicationException |
| `--output <json>` | Result data as flat JSON | -- |
| `--progress <text>` | Business flow progress tracking | -- |

**Examples:**
```bash
# Mark as successful with output data
uip resources queues-set-result 12345 67890 \
  --success \
  --output '{"ProcessedAt":"2024-01-15","Status":"Approved"}' \
  --format json

# Mark as failed with business exception (no retry)
uip resources queues-set-result 12345 67890 \
  --fail \
  --reason "Invalid invoice format" \
  --exception-type BusinessException \
  --format json

# Mark as failed with application exception (eligible for retry)
uip resources queues-set-result 12345 67890 \
  --fail \
  --reason "API timeout" \
  --details "Connection to payment gateway timed out after 30s" \
  --exception-type ApplicationException \
  --format json
```

### `uip resources queues-delete-item <parent-folder-id> <item-id>`

Delete a queue item by ID.

```bash
uip resources queues-delete-item <parent-folder-id> <item-id> [options] --format json
```

| Option | Description | Default |
|--------|-------------|---------|
| `-t, --tenant <name>` | Tenant override | Current tenant |

---

## Storage Buckets

Storage buckets provide file storage for automation data within Orchestrator folders.

### `uip resources storage-buckets-list <parent-folder-id>`

List all storage buckets in a folder.

```bash
uip resources storage-buckets-list <parent-folder-id> [options] --format json
```

| Option | Description | Default |
|--------|-------------|---------|
| `-t, --tenant <name>` | Tenant override | Current tenant |
| `-f, --filter <filter>` | OData filter expression | -- |
| `-c, --count <number>` | Number of items to return | 50 |

### `uip resources storage-buckets-get <parent-folder-id> <bucket-id>`

Get a specific storage bucket by ID.

```bash
uip resources storage-buckets-get <parent-folder-id> <bucket-id> [options] --format json
```

| Option | Description | Default |
|--------|-------------|---------|
| `-t, --tenant <name>` | Tenant override | Current tenant |

### `uip resources storage-buckets-create <parent-folder-id> <name>`

Create a new storage bucket.

```bash
uip resources storage-buckets-create <parent-folder-id> <name> [options] --format json
```

| Option | Description | Default |
|--------|-------------|---------|
| `-t, --tenant <name>` | Tenant override | Current tenant |
| `-d, --description <text>` | Bucket description | -- |

**Example:**
```bash
uip resources storage-buckets-create 12345 "InvoiceDocuments" \
  -d "Scanned invoice PDFs for processing" \
  --format json
```

### `uip resources storage-buckets-delete <parent-folder-id> <bucket-id>`

Delete a storage bucket by ID.

```bash
uip resources storage-buckets-delete <parent-folder-id> <bucket-id> [options] --format json
```

| Option | Description | Default |
|--------|-------------|---------|
| `-t, --tenant <name>` | Tenant override | Current tenant |

---

## Storage Bucket Files

File operations within storage buckets.

### `uip resources storage-buckets-read-file <parent-folder-id> <bucket-id> <path>`

Download a file from a storage bucket.

```bash
uip resources storage-buckets-read-file <parent-folder-id> <bucket-id> <path> [options]
```

| Option | Description | Default |
|--------|-------------|---------|
| `-t, --tenant <name>` | Tenant override | Current tenant |
| `-o, --output <file>` | Local file path to save to | stdout |

**Examples:**
```bash
# Download to file
uip resources storage-buckets-read-file 12345 67890 "invoices/INV-001.pdf" \
  -o ./downloads/INV-001.pdf

# Output to stdout
uip resources storage-buckets-read-file 12345 67890 "config/settings.json"
```

### `uip resources storage-buckets-write-file <parent-folder-id> <bucket-id> <path>`

Upload a file to a storage bucket.

```bash
uip resources storage-buckets-write-file <parent-folder-id> <bucket-id> <path> [options] --format json
```

| Option | Description | Default |
|--------|-------------|---------|
| `-t, --tenant <name>` | Tenant override | Current tenant |
| `--file <local-file>` | Path to local file to upload | -- |
| `--content-type <mime>` | MIME type | Auto-detected |

**Examples:**
```bash
# Upload a PDF
uip resources storage-buckets-write-file 12345 67890 "invoices/INV-001.pdf" \
  --file ./INV-001.pdf \
  --format json

# Upload with explicit content type
uip resources storage-buckets-write-file 12345 67890 "data/export.csv" \
  --file ./export.csv \
  --content-type "text/csv" \
  --format json
```

### `uip resources storage-buckets-delete-file <parent-folder-id> <bucket-id> <path>`

Delete a file from a storage bucket.

```bash
uip resources storage-buckets-delete-file <parent-folder-id> <bucket-id> <path> [options] --format json
```

| Option | Description | Default |
|--------|-------------|---------|
| `-t, --tenant <name>` | Tenant override | Current tenant |

---

## Common Patterns

### Environment Setup with Assets

```bash
# 1. Get folder ID
uip or folders list --format json
# Note folder ID, e.g., 12345

# 2. Create configuration assets
uip resources assets create 12345 "ApiBaseUrl" "https://api.example.com" --format json
uip resources assets create 12345 "ApiKey" "sk-production-key" --type Secret --format json
uip resources assets create 12345 "MaxRetries" "3" --type Integer --format json
uip resources assets create 12345 "DebugMode" "false" --type Bool --format json
```

### Dispatcher-Performer Queue Pattern

```bash
# 1. Create the queue
uip resources queues-create 12345 "InvoiceQueue" \
  --max-retries 3 --auto-retry \
  --format json

# 2. Dispatcher: Add items to process
uip resources queues-add-items 12345 "InvoiceQueue" \
  --specific-content '{"InvoiceId":"INV-001","Amount":1500,"Vendor":"Acme"}' \
  -r "INV-001" \
  -p Normal \
  --format json

uip resources queues-add-items 12345 "InvoiceQueue" \
  --specific-content '{"InvoiceId":"INV-002","Amount":2300,"Vendor":"Globex"}' \
  -r "INV-002" \
  -p High \
  --format json

# 3. Performer processes items and reports results
uip resources queues-set-result 12345 <item-id> \
  --success \
  --output '{"ProcessedAt":"2024-01-15","ApprovalStatus":"Approved"}' \
  --format json
```

### Storage Bucket Workflow

```bash
# 1. Create a bucket for document storage
uip resources storage-buckets-create 12345 "ProcessedDocuments" \
  -d "Processed automation output files" \
  --format json
# Note bucket ID, e.g., 99999

# 2. Upload files
uip resources storage-buckets-write-file 12345 99999 "reports/monthly-2024-01.pdf" \
  --file ./output/report.pdf \
  --format json

# 3. Download files
uip resources storage-buckets-read-file 12345 99999 "reports/monthly-2024-01.pdf" \
  -o ./downloads/report.pdf

# 4. Clean up
uip resources storage-buckets-delete-file 12345 99999 "reports/monthly-2024-01.pdf" --format json
```

---

## Known Limitations

- There is no `queues list` command to list queues in a folder. Use the Orchestrator UI or REST API to discover existing queues.
- There is no `queue-items list` command to list items in a queue. Use `queues-get-item` with a known item ID, or the Orchestrator UI.
- The `or` tool does NOT have asset commands. Use `resources assets` for all asset operations.

---

## Troubleshooting

| Error | Cause | Fix |
|-------|-------|-----|
| Asset not found | Asset ID doesn't exist in the folder | Use `assets list` to verify the asset exists |
| Queue name already exists | Duplicate queue name in folder | Use a unique name or delete the existing queue first |
| Invalid specific-content | JSON format is incorrect | Ensure flat JSON object with string keys and simple values (no nested objects/arrays) |
| BusinessException vs ApplicationException | Wrong exception type for retry behavior | Use `BusinessException` for no-retry failures, `ApplicationException` for retryable |
| Bucket file not found | File path doesn't exist in bucket | Verify the exact path using bucket file listing |
| unknown command 'queues' | Using nested syntax for queue commands | Queue commands are flat hyphenated: `queues-create`, not `queues create` |
| The user name or external name cannot be null or empty | Updating a Credential-type asset without providing username | When updating Credential assets, include the full `username:password` value, not just metadata changes |
| Error setting queue item result / This queue item has not been processed yet | Calling `queues-set-result` on a "New" item | Items must be in "InProgress" state before setting results. Items transition to InProgress when a robot picks them up for processing |
