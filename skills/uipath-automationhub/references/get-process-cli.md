# Get a Process from Automation Hub — `uip ah` CLI flow

Fetches one process (by id or search) and its documents, and downloads document bytes on request. Read-only. Auth is handled by the CLI — you never touch a token.

> **Use this flow only after the preflight in [`cli-commands.md`](cli-commands.md) passed.** All commands: append `--output json`.

## Step 1: Resolve the process

- Caller gave an **id** → use it.
- Otherwise search:
  ```bash
  uip ah automations list --search "<name>" --limit 20 --output json
  ```
  One clear match → its `Id`. Several → show name + id + owner, ask. None → say so and stop.

## Step 2: Fetch the process

```bash
uip ah automations get $PROCESS_ID --output json
```

`Data` is the projected record (`Id`, `Name`, `Phase`, `PhaseStatus`, `Tags`, …). Add `--all-fields` only when you need the raw record (e.g. `process_slug` for the deep link). `Failure` with not-found → no such process; auth error → `uip login`.

## Step 3: Fetch the documents

```bash
uip ah documents list $PROCESS_ID --output json
```

Each entry carries `Id` (document id), `Title`, `TypeId`, and **either** a `FileId` (file-backed — downloadable) **or** an `EmbedLink` (link-backed — show the URL; nothing to download).

## Step 3b: Download a document (when the caller wants the bytes)

Only file-backed documents download, and the command takes the **`FileId`** — not the document `Id`:

```bash
uip ah documents download $FILE_ID --destination "<path>" --output json
```

- `Data` reports `Destination` and `Bytes` — confirm the file exists and is non-empty before reporting success.
- Link-backed documents: present the `EmbedLink` instead. Never invent a download path.

## Step 4: Present

```
Process: <name>  (process_id: <id>)
  Status:   <phase/status>
  Category: <category>
  Owner:    <owner>
  View:     {baseUrl}/{org}/{tenant}/automationhub_/automation-profile/{process_slug}/documentation
Documents:
  - PDD  (document_id 12, file_id 42 — downloadable)
  - SDD  (document_id 13, embed_link — link only)
```

`process_slug` comes from `automations get --all-fields`; the base URL from `uip ah auth-info get` (`Data.Tenant.Url`). Offer the raw JSON, downloads, or components (`uip ah components list --automation-id <id>`) if relevant.
