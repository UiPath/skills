# Work with Storage

Create buckets, upload/download files, and generate presigned URLs. For options, run `uip or <command> --help`.

## When to Use

- Store automation data or workflow files.
- Share files through temporary presigned URLs.

## Prerequisites

- Run `uip login status`. If not logged in, ask the user to run `uip login` (it opens an interactive browser flow).
- Run `uip or folders list` and verify that the target folder exists.

## Bucket Management

### Create

Run:

```bash
uip or buckets create "invoices" --folder-path "Finance" \
  --description "Invoice attachments and reports" --output json
```

Use Orchestrator built-in storage by default. Supported options:

| Option | Values/description |
|---|---|
| `--storage-provider` | `Azure`, `Amazon`, `Minio`, `S3Compatible`, `FileSystem`; omit for built-in storage |
| `--storage-parameters` | Provider-specific connection string; use `$Password` for the secret |
| `--storage-container` | Provider-specific container, such as an AWS bucket or Azure container |
| `--credential-store-key` | Credential-store GUID; required for Azure and Amazon |
| `--password` | Secret substituted for `$Password` |
| `--options` | `None` (default), `ReadOnly`, `AuditReadAccess`, `AccessDataThroughOrchestrator` |
| `--tags` | JSON array, for example `'[{"name":"env","value":"prod"}]'` |

For Azure or Amazon, run:

```bash
uip or buckets create "cloud-reports" --folder-path "Finance" \
  --storage-provider Azure \
  --storage-parameters "DefaultEndpointsProtocol=https;AccountName=myaccount;AccountKey=$Password" \
  --storage-container "reports-container" \
  --credential-store-key <credential-store-key> --password "my-storage-account-key" \
  --output json
```

### List, Get, Update, Delete, and Share

Run:

```bash
uip or buckets list --folder-path "Finance" --output json
uip or buckets list --all-folders --name "invoice" --output json
uip or buckets get <bucket-key> --folder-path "Finance" --output json
uip or buckets update <bucket-key> --folder-path "Finance" \
  --name "invoices-2026" --description "Updated invoice store" --output json
uip or buckets delete <bucket-key> --folder-path "Finance" --yes --output json
uip or buckets delete <bucket-key> --folder-path "Finance" --force --output json
uip or buckets share <bucket-key> --folder-path "Production" --output json
uip or buckets list-folders <bucket-key> --folder-path "Finance" --output json
uip or buckets unshare <bucket-key> --folder-path "Production" --output json
```

Run `buckets list` with `--folder-path`/`--folder-key` or `--all-folders`; it supports `--name`, `--limit`, `--offset`, and `--sort-by`. With `--all-folders`, use `--exclude-folder-path` or `--exclude-folder-key`. Delete a bucket containing files with `--force`; `--force` deletes the bucket and its files.

## File Operations

### Upload and List

Run:

```bash
uip or bucket-files upload <bucket-key> "reports/summary.csv" \
  --folder-path "Finance" --file ./summary.csv --output json
uip or bucket-files upload <bucket-key> "data/config.json" \
  --folder-path "Finance" --file ./config.json \
  --content-type "application/json" --output json
uip or bucket-files list <bucket-key> --folder-path "Finance" --output json
uip or bucket-files list <bucket-key> --folder-path "Finance" \
  --prefix "reports/" --output json
```

Require `--file` for uploads. Auto-detect `--content-type` when omitted. Use continuation-token pagination for `bucket-files list`, not offset/limit. Read the response token and run:

```bash
uip or bucket-files list <bucket-key> --folder-path "Finance" \
  --continuation-token "<token-from-previous-response>" --output json
```

Use `--take-hint <n>` for page size (default 500, maximum 1000) and `--expiry-in-minutes` for presigned URLs included in the response.

### List Directories

Run:

```bash
uip or bucket-files list-dirs <bucket-key> --folder-path "Finance" --output json
uip or bucket-files list-dirs <bucket-key> --folder-path "Finance" \
  --directory "reports/" --file-name-glob "*.csv" --output json
```

Use `--limit`/`--offset` pagination for `list-dirs`.

### Metadata, Download, and Delete

Run:

```bash
uip or bucket-files get <bucket-key> "reports/summary.csv" \
  --folder-path "Finance" --output json
uip or bucket-files download <bucket-key> "reports/summary.csv" \
  --folder-path "Finance" --destination ./summary.csv --output json
uip or bucket-files download <bucket-key> "reports/summary.csv" \
  --folder-path "Finance" | jq .
uip or bucket-files delete <bucket-key> "reports/summary.csv" \
  --folder-path "Finance" --output json
```

Without `--destination`, `download` writes to stdout; `-d` is its shorthand. Always use `--destination` for binary files.

## Presigned URLs

Use presigned URLs for unauthenticated temporary downloads or uploads. Run:

```bash
uip or bucket-files get-download-url <bucket-key> "reports/summary.csv" \
  --folder-path "Finance" --expiry-in-minutes 15 --output json
uip or bucket-files get-upload-url <bucket-key> "uploads/new-report.csv" \
  --folder-path "Finance" --expiry-in-minutes 30 \
  --content-type "text/csv" --output json
```

Use download URLs with GET and upload URLs with PUT. Include every returned required header, such as `x-ms-blob-type` for Azure. Use these URLs for temporary sharing, external uploads, and time-limited CI/CD access.

### Upload via REST

Prefer `bucket-files upload`, which performs presign plus PUT. If a non-CLI system must upload, run both steps:

```bash
# 1. Get a presigned PUT URL (GetWriteUri). Single-URL-encode the path.
curl -s -H "Authorization: Bearer $TOKEN" \
  -H "X-UIPATH-OrganizationUnitId: $FOLDER_ID" \
  "https://cloud.uipath.com/$ORG/$TENANT/orchestrator_/odata/Buckets($BUCKET_ID)/UiPath.Server.Configuration.OData.GetWriteUri?path=reports%2Fsummary.csv&contentType=text%2Fcsv"

# 2. PUT with every header listed under RequiredHeaders.
curl -s -X PUT -H "x-ms-blob-type: BlockBlob" -H "Content-Type: text/csv" \
  --data-binary @./summary.csv "$PRESIGNED_URI"
```

The URI is short-lived (default 5–15 minutes). `RequiredHeaders` vary by provider. `GetWriteUri` corrupts paths containing `&`, `+`, `%`, or `?`; avoid these characters. Double-URL-encoding is the temporary REST workaround, but it will break after the server-side fix; prefer renaming.

## Storage Providers

| Provider | Required configuration |
|---|---|
| Orchestrator (default) | None; built-in storage |
| Azure / Amazon | `--credential-store-key`, `--storage-parameters`, `--storage-container` |
| Minio / S3Compatible | `--storage-parameters`, `--storage-container` |
| FileSystem | `--storage-parameters` (local/network path) |

Run `uip or credential-stores list` to find credential-store keys.

## Common Pitfalls

- Run `buckets list` with `--folder-path`/`--folder-key` or `--all-folders`; there is no implicit cross-folder default.
- The CLI rejects `&`, `+`, `%`, and `?` in paths for `upload`, `download`, `delete`, `get`, `get-download-url`, and `get-upload-url`. The storage API can silently corrupt such names: `a&b.txt` may truncate to `a`, while `+` and `%xx` may decode to other characters. This also applies to direct REST calls.
- Bucket keys are GUIDs: use the `identifier` field from list/create output, not numeric `id`.
- File paths always use forward slashes, for example `reports/2026/summary.csv`.

## Pagination

- `bucket-files list`: `--continuation-token`, `--take-hint`.
- `bucket-files list-dirs` and `buckets list`: `--offset`, `--limit`.

## Related

- [resources.md](resources.md) — Orchestrator resources overview and libraries
- Credential stores used by external storage providers → [`uipath-orchestrator`](tenant-admin.md)
- Folder setup → [`uipath-orchestrator`](setup-environment.md)