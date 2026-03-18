# Storage Buckets

Orchestrator storage buckets — file storage for automation data, reports, and intermediate artifacts.

## Overview

Storage buckets provide a file storage abstraction in Orchestrator. Automations can upload, download, and manage files within buckets. Files are accessed via presigned URIs for secure, time-limited access.

## CLI Commands

### List Storage Buckets

```bash
uip resources storage-buckets-list --folder-id <folder-id> --format json
```

With OData filter:
```bash
uip resources storage-buckets-list --folder-id <folder-id> --filter "Name eq 'ExportFiles'" --format json
```

### Get Storage Bucket

```bash
uip resources storage-buckets-get --folder-id <folder-id> --bucket-id <bucket-id> --format json
```

### Create Storage Bucket

```bash
uip resources storage-buckets-create --folder-id <folder-id> --name "ExportFiles" --format json
```

The bucket ID is auto-generated as a UUID.

### Write (Upload) File

```bash
uip resources storage-buckets-write-file --folder-id <folder-id> --bucket-id <bucket-id> \
  --file-path "./reports/monthly-report.pdf" \
  --blob-path "reports/2026/march/monthly-report.pdf" \
  --format json
```

The command obtains a presigned URI from Orchestrator and uploads the file.

### Read (Download) File

```bash
uip resources storage-buckets-read-file --folder-id <folder-id> --bucket-id <bucket-id> \
  --blob-path "reports/2026/march/monthly-report.pdf" \
  --output-path "./downloads/monthly-report.pdf" \
  --format json
```

### Delete File

Idempotent — no error if the file doesn't exist:
```bash
uip resources storage-buckets-delete-file --folder-id <folder-id> --bucket-id <bucket-id> \
  --blob-path "reports/2026/march/monthly-report.pdf" \
  --format json
```

### Delete Storage Bucket

```bash
uip resources storage-buckets-delete --folder-id <folder-id> --bucket-id <bucket-id> --format json
```

## Common Patterns

### File Exchange Between Processes

Use a shared storage bucket for processes that need to exchange files:

```bash
# Process A: Upload generated report
uip resources storage-buckets-write-file --folder-id 12345 --bucket-id <id> \
  --file-path "./output/report.xlsx" \
  --blob-path "shared/report.xlsx" \
  --format json

# Process B: Download and process the report
uip resources storage-buckets-read-file --folder-id 12345 --bucket-id <id> \
  --blob-path "shared/report.xlsx" \
  --output-path "./input/report.xlsx" \
  --format json
```

### Organize Files with Blob Paths

Use folder-like blob paths for organization:

```
bucket/
├── invoices/
│   ├── 2026-01/
│   │   ├── INV-001.pdf
│   │   └── INV-002.pdf
│   └── 2026-02/
│       └── INV-003.pdf
├── reports/
│   └── monthly-summary.xlsx
└── temp/
    └── processing-batch-42.json
```
