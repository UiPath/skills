# Managing Context Grounding Indexes — `uip context-grounding` CLI

Operate context-grounding indexes from the terminal: list, create, ingest, poll status, search, and delete. Indexes support semantic search/RAG over organizational documents and are consumed by agents and flows as tools.

## Requirements

Every command needs a folder. Pass `--folder-path "<PATH>"` (for example, `"Shared"`), `--folder-key "<UUID>"`, or set `UIPATH_FOLDER_PATH`. Missing folder returns `400 "A folder is required for this action."`; missing index permission returns `403 "User is missing required index permissions."` Permissions are folder-scoped. Switch folders when needed; a personal workspace is the safe default for self-serve use.

Run `--output json` on commands whose output you parse. The equivalent per-command flag is `--format json`; `-o <FILE>` writes output to a file instead of stdout.

## List indexes

Run:

```bash
uip context-grounding list --folder-path "<FOLDER_PATH>" --output json
```

Use the returned index array (`id`, `name`, `last_ingestion_status`, `data_source`, …) to confirm an index exists and resolve its name before `retrieve`, `search`, or `ingest`.

## Create an index

Creation does **not** ingest; run ingestion separately.

For a bucket-backed index, run:

```bash
uip context-grounding create \
  --index-name "<INDEX_NAME>" \
  --bucket-source "<BUCKET_NAME>" \
  --folder-path "<FOLDER_PATH>" \
  --output json
```

Optional flags are `--description "<TEXT>"`, `--file-type pdf`, and `--extraction-strategy LLMV4|NativeV1` (default `LLMV4`).

For a connection-backed index, use one of `google_drive`, `onedrive`, `dropbox`, or `confluence`. First run:

```bash
uip context-grounding source-schema --type google_drive
```

Omit `--type` to print all schemas. Write the required source configuration to a file, then run:

```bash
uip context-grounding create \
  --index-name "<INDEX_NAME>" \
  --source-file "<CONFIG>.json" \
  --folder-path "<FOLDER_PATH>" \
  --output json
```

`--bucket-source` and `--source-file` are mutually exclusive; choose one.

## Trigger ingestion and poll status

When source documents change, run ingestion; it runs asynchronously:

```bash
uip context-grounding ingest --index-name "<INDEX_NAME>" --folder-path "<FOLDER_PATH>" --output json
```

Run `retrieve` to get the full index object and its ingestion status:

```bash
uip context-grounding retrieve --index-name "<INDEX_NAME>" --folder-path "<FOLDER_PATH>" --output json
```

Read `last_ingestion_status`:

| `last_ingestion_status` | Meaning | Action |
|---|---|---|
| `Successful` | Ready | Proceed with search |
| `Failed` | Ingestion failed | Stop and read `last_ingestion_failure_reason` |
| anything else | In progress | Keep polling |

Re-run `retrieve` until the status is terminal (`Successful` or `Failed`). Cap retries, for example at 30 polls with a fixed interval; abort with the failure reason if it never reaches `Successful`. Also inspect `last_ingested`, `index_health.overall_health_score`, and `data_source` when useful.

## Search an index

Search only after ingestion succeeds. Run:

```bash
uip context-grounding search \
  --index-name "<INDEX_NAME>" \
  --query "<NATURAL_LANGUAGE_QUERY>" \
  --folder-path "<FOLDER_PATH>" \
  --limit 5 \
  --output json
```

Optional flags are `--limit <N>` (default 10) and `--threshold <0.0-1.0>` (minimum similarity, default 0.0). Results contain ranked snippets with scores. If results are empty, broaden the query, lower `--threshold`, or confirm ingestion succeeded.

## Delete an index

Always preview the target first:

```bash
uip context-grounding delete --index-name "<INDEX_NAME>" --folder-path "<FOLDER_PATH>" --dry-run --output json
```

Then delete non-interactively:

```bash
uip context-grounding delete --index-name "<INDEX_NAME>" --folder-path "<FOLDER_PATH>" --confirm --output json
```

Run `--dry-run` first to confirm the target. Use `--confirm` in non-interactive or agent runs; otherwise the confirmation prompt can hang.

## End-to-end workflow

1. Run `create --index-name X --bucket-source B --folder-path F` to create an empty index.
2. Run `ingest --index-name X --folder-path F` to start ingestion.
3. Run `retrieve --index-name X --folder-path F` and poll `last_ingestion_status` until `Successful`.
4. Run `search --index-name X --query "..." --folder-path F`.

## Anti-patterns

- **Search before ingestion finishes:** `create` does not ingest and `ingest` is asynchronous. Poll `retrieve` until `last_ingestion_status: Successful`.
- **Omit the folder:** this returns `400 "A folder is required for this action."` Pass `--folder-path`/`--folder-key` or set `UIPATH_FOLDER_PATH`.
- **Delete without `--confirm` in an agent run:** the interactive prompt hangs. Run `--dry-run` first, then run with `--confirm`.