# Managing Context Grounding Indexes — `uip context-grounding` CLI

Operate context-grounding indexes from the terminal: list, create, ingest, poll status, search, delete. Context-grounding indexes back semantic search / RAG over your organization's documents; agents and flows consume them as tools.

## Folder Targeting

Every command needs a folder. Pass `--folder-path "<PATH>"` (e.g. `"Shared"`) or `--folder-key "<UUID>"`, or set `UIPATH_FOLDER_PATH`. Missing folder → `400 "A folder is required for this action."` Permissions live on the folder; missing index permission → `403 "User is missing required index permissions."` (switch folders; personal workspace is the safe default for self-serve).

## JSON Output

Append `--output json` to any command whose output you parse — it is parsed throughout this guide. Equivalent per-command flag: `--format json`. `-o <FILE>` writes the result to a file instead of stdout.

## List Indexes

```bash
uip context-grounding list --folder-path "<FOLDER_PATH>" --output json
```

Returns an array of index objects (`id`, `name`, `last_ingestion_status`, `data_source`, …). Use to confirm an index exists and resolve its name before `retrieve` / `search` / `ingest`.

## Create an Index

Creation does **not** ingest — trigger ingestion separately (see [Ingest](#trigger-ingestion)).

### Bucket-backed

```bash
uip context-grounding create \
  --index-name "<INDEX_NAME>" \
  --bucket-source "<BUCKET_NAME>" \
  --folder-path "<FOLDER_PATH>" \
  --output json
```

Optional: `--description "<TEXT>"`, `--file-type pdf` (filter ingested files), `--extraction-strategy LLMV4|NativeV1` (default `LLMV4`).

### Connection-backed (Google Drive / OneDrive / Dropbox / Confluence)

1. Inspect the required JSON shape:

   ```bash
   uip context-grounding source-schema --type google_drive
   ```

   Omit `--type` to print all schemas. Types: `google_drive`, `onedrive`, `dropbox`, `confluence`.

2. Write the source config to a file, then:

   ```bash
   uip context-grounding create \
     --index-name "<INDEX_NAME>" \
     --source-file "<CONFIG>.json" \
     --folder-path "<FOLDER_PATH>" \
     --output json
   ```

`--bucket-source` and `--source-file` are mutually exclusive — pick one.

## Trigger Ingestion

Re-index after its source documents change. Runs asynchronously.

```bash
uip context-grounding ingest --index-name "<INDEX_NAME>" --folder-path "<FOLDER_PATH>" --output json
```

## Poll Status

`retrieve` returns the full index object including ingestion status. This is how you check whether an index is ready.

```bash
uip context-grounding retrieve --index-name "<INDEX_NAME>" --folder-path "<FOLDER_PATH>" --output json
```

Read `last_ingestion_status` from the JSON:

| `last_ingestion_status` | Meaning | Action |
|---|---|---|
| `Successful` | Ready | Proceed — search the index |
| `Failed` | Ingestion failed | Stop; read `last_ingestion_failure_reason` |
| anything else | In progress | Keep polling |

Polling loop — re-`retrieve` until the status is terminal (`Successful` or `Failed`); cap retries (e.g. 30 polls at a fixed interval) and abort with the failure reason if it never reaches `Successful`. Other useful fields: `last_ingested`, `index_health.overall_health_score`, `data_source`.

## Search an Index

Semantic search over a fully-ingested index.

```bash
uip context-grounding search \
  --index-name "<INDEX_NAME>" \
  --query "<NATURAL_LANGUAGE_QUERY>" \
  --folder-path "<FOLDER_PATH>" \
  --limit 5 \
  --output json
```

Optional: `--limit <N>` (default 10), `--threshold <0.0-1.0>` (minimum similarity, default 0.0). Returns ranked snippets with scores. Empty results → broaden the query, lower `--threshold`, or confirm ingestion succeeded.

## Delete an Index

```bash
# Preview without deleting
uip context-grounding delete --index-name "<INDEX_NAME>" --folder-path "<FOLDER_PATH>" --dry-run --output json

# Delete without the confirmation prompt
uip context-grounding delete --index-name "<INDEX_NAME>" --folder-path "<FOLDER_PATH>" --confirm --output json
```

Always `--dry-run` first to confirm the target. `--confirm` skips the interactive prompt — required for non-interactive/agent runs.

## End-to-End: Stand Up a Searchable Index

1. `create --index-name X --bucket-source B --folder-path F` — create empty index.
2. `ingest --index-name X --folder-path F` — start ingestion.
3. `retrieve --index-name X --folder-path F` — poll `last_ingestion_status` until `Successful`.
4. `search --index-name X --query "..." --folder-path F` — query.

## Anti-patterns

- **Searching before ingestion finishes.** `create` does not ingest, and `ingest` is async. Always poll `retrieve` for `last_ingestion_status: Successful` first.
- **Omitting the folder.** → `400 "A folder is required for this action."` Pass `--folder-path`/`--folder-key` or set `UIPATH_FOLDER_PATH`.
- **`delete` without `--confirm` in an agent run.** The interactive prompt hangs. Use `--dry-run` to preview, then `--confirm` to execute.
