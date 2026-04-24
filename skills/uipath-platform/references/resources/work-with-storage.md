# Work with Storage

Create storage buckets, upload and download files, and generate presigned URLs for direct client access.

> For full option details on any command, use `--help` (e.g., `uip resource buckets create --help`).

## When to Use

- Storing automation data, uploading/downloading files for workflows
- Sharing files via presigned URLs with external systems or users

## Prerequisites

- Authenticated (`uip login`)
- Target folder exists (`uip or folders list`)

## Flow

```mermaid
graph LR
    A[buckets create] --> B[bucket-files write]
    B --> C[bucket-files list]
    C --> D[bucket-files read]
    C --> E[bucket-files get-download-url]
    C --> F[bucket-files get-upload-url]
```

---

## Bucket Management

### Create a Bucket

```bash
uip resource buckets create "invoices" \
  --folder-path "Finance" \
  --description "Invoice attachments and reports" \
  --output json
```

This creates a bucket using the default Orchestrator built-in storage. No extra configuration needed.

Key options:

| Option | Description |
|--------|-------------|
| `--storage-provider` | `Azure`, `Amazon`, `Minio`, `S3Compatible`, `FileSystem`. Omit for Orchestrator built-in. |
| `--storage-parameters` | Provider-specific connection string. Use `$Password` as placeholder for the secret. |
| `--storage-container` | Provider-specific container name (e.g., AWS bucket or Azure container). |
| `--credential-store-key` | Key (GUID) of the credential store holding the provider secret. Required for Azure and Amazon. |
| `--password` | Provider-specific secret inserted at the `$Password` placeholder. |
| `--options` | `None` (default), `ReadOnly`, `AuditReadAccess`, `AccessDataThroughOrchestrator` |
| `--tags` | JSON array, e.g. `'[{"name":"env","value":"prod"}]'` |

For external providers (Azure, Amazon):

```bash
uip resource buckets create "cloud-reports" --folder-path "Finance" \
  --storage-provider Azure \
  --storage-parameters "DefaultEndpointsProtocol=https;AccountName=myaccount;AccountKey=$Password" \
  --storage-container "reports-container" \
  --credential-store-key <credential-store-key> --password "my-storage-account-key" \
  --output json
```

### List Buckets

```bash
# List buckets in a specific folder
uip resource buckets list --folder-path "Finance" --output json

# List across all accessible folders (with optional name filter)
uip resource buckets list --name "invoice" --output json
```

Paginate with `--limit` / `--offset`. Sort with `--order-by`. Use `--exclude-folder-path` to omit a folder from cross-folder listing.

### Get, Update, Delete

```bash
uip resource buckets get <bucket-key> --folder-path "Finance" --output json
uip resource buckets update <bucket-key> --folder-path "Finance" \
  --name "invoices-2026" --description "Updated invoice store" --output json
uip resource buckets delete <bucket-key> --folder-path "Finance" --output json
```

### Share Buckets Across Folders

```bash
# Share with another folder
uip resource buckets share <bucket-key> --folder-path "Production" --output json

# List folders that have access
uip resource buckets list-folders <bucket-key> --folder-path "Finance" --output json

# Remove from a folder
uip resource buckets unshare <bucket-key> --folder-path "Production" --output json
```

---

## File Operations

### Upload a File

```bash
uip resource bucket-files write <bucket-key> "reports/summary.csv" \
  --folder-path "Finance" --file ./summary.csv --output json

# Specify content type explicitly
uip resource bucket-files write <bucket-key> "data/config.json" \
  --folder-path "Finance" --file ./config.json \
  --content-type "application/json" --output json
```

`--file` is required. `--content-type` is auto-detected if omitted.

### List Files

```bash
# List all files in a bucket
uip resource bucket-files list <bucket-key> --folder-path "Finance" --output json

# Filter by path prefix
uip resource bucket-files list <bucket-key> --folder-path "Finance" \
  --prefix "reports/" --output json
```

File listing uses **continuation-token pagination** (not offset/limit). Check the response for a continuation token and pass it back:

```bash
# Fetch next page
uip resource bucket-files list <bucket-key> --folder-path "Finance" \
  --continuation-token "<token-from-previous-response>" --output json
```

Additional options: `--take-hint <n>` (items per page, default 500, max 1000), `--expiry-in-minutes` (presigned URL lifetime in the response).

### List Directories

```bash
uip resource bucket-files list-dirs <bucket-key> --folder-path "Finance" --output json
uip resource bucket-files list-dirs <bucket-key> --folder-path "Finance" \
  --directory "reports/" --file-name-glob "*.csv" --output json
```

Unlike `list`, `list-dirs` uses standard `--limit` / `--offset` pagination.

### Get Metadata, Download, Delete

```bash
# Get file metadata (no download)
uip resource bucket-files get <bucket-key> "reports/summary.csv" \
  --folder-path "Finance" --output json

# Download to a local file
uip resource bucket-files read <bucket-key> "reports/summary.csv" \
  --folder-path "Finance" --destination ./summary.csv --output json

# Write to stdout (pipe to another command)
uip resource bucket-files read <bucket-key> "reports/summary.csv" \
  --folder-path "Finance" | jq .

# Delete a file
uip resource bucket-files delete <bucket-key> "reports/summary.csv" \
  --folder-path "Finance" --output json
```

Without `--destination`, `read` writes content to stdout. Use `-d` as shorthand.

---

## Presigned URLs

Presigned URLs allow external systems or users to upload/download files directly without CLI authentication.

### Get a Download URL

```bash
uip resource bucket-files get-download-url <bucket-key> "reports/summary.csv" \
  --folder-path "Finance" --expiry-in-minutes 15 --output json
```

Returns a presigned URL (GET verb). The URL expires after `--expiry-in-minutes`.

### Get an Upload URL

```bash
uip resource bucket-files get-upload-url <bucket-key> "uploads/new-report.csv" \
  --folder-path "Finance" --expiry-in-minutes 30 \
  --content-type "text/csv" --output json
```

Returns a presigned URL (PUT verb) and any required headers (e.g., `x-ms-blob-type` for Azure). The caller must include those headers when uploading.

Use cases: share temporary download links, allow external systems to upload directly, time-limited CI/CD access.

---

## Complete Example

```bash
# 1. Create the bucket
uip resource buckets create "monthly-reports" \
  --folder-path "Finance" --description "Monthly financial reports" --output json

# 2. Upload files
uip resource bucket-files write <bucket-key> "2026/04/revenue.csv" \
  --folder-path "Finance" --file ./revenue.csv --output json
uip resource bucket-files write <bucket-key> "2026/04/expenses.pdf" \
  --folder-path "Finance" --file ./expenses.pdf --output json

# 3. List files in the April directory
uip resource bucket-files list <bucket-key> \
  --folder-path "Finance" --prefix "2026/04/" --output json

# 4. Download a file
uip resource bucket-files read <bucket-key> "2026/04/revenue.csv" \
  --folder-path "Finance" --destination ./downloaded-revenue.csv --output json

# 5. Generate a presigned download URL for sharing
uip resource bucket-files get-download-url <bucket-key> "2026/04/expenses.pdf" \
  --folder-path "Finance" --expiry-in-minutes 60 --output json
```

---

## Variations and Gotchas

### Storage Providers

| Provider | Config needed |
|----------|---------------|
| Orchestrator (default) | None -- built-in storage |
| Azure / Amazon | `--credential-store-key`, `--storage-parameters`, `--storage-container` |
| Minio / S3Compatible | `--storage-parameters`, `--storage-container` |
| FileSystem | `--storage-parameters` (local/network path) |

### Pagination Differences

- `bucket-files list` -- continuation-token based (`--continuation-token`, `--take-hint`)
- `bucket-files list-dirs` and `buckets list` -- offset/limit based (`--offset`, `--limit`)

### Common Pitfalls

- **`list` without `--folder-path`** returns buckets across all accessible folders -- may return more results than expected.
- **`read` without `--destination`** writes to stdout. For binary files, always use `--destination`.
- **External providers** (Azure, Amazon) require `--credential-store-key`. Use `uip or credential-stores list` to find keys.
- **Bucket keys** are GUIDs (the `identifier` field from list/create output). Do not confuse with numeric `id`.
- **File paths** use forward slashes regardless of OS (e.g., `"reports/2026/summary.csv"`).

---

## Related

- [resources.md](resources.md) -- Resource tool overview and libraries
- [Tenant Admin](../orchestrator/tenant-admin.md) -- Credential stores used by external storage providers
- [Setup Environment](../orchestrator/setup-environment.md) -- Folder setup
