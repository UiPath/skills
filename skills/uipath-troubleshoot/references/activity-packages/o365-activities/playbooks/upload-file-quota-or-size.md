---
confidence: medium
---

# O365 Files — Upload quota, size, or session failure

## Context

What this looks like — an upload to OneDrive/SharePoint faults on storage limits or the chunked upload session. Friendly forms (`Office365Exception`, Connections activities):

- `The user has reached their quota limit.` — Graph `QuotaLimitReached`: the target OneDrive/SharePoint storage is full.
- `Max file size exceeded.` / `Maximum stream size exceeded.` — the file exceeds the service's per-file limit.
- `Upload session failed.` / `Upload session incomplete.` / `Upload session not found.` — the chunked upload session for a large file broke mid-transfer (network interruption, session expiry) or could not be completed.

Legacy `UploadFile` surfaces the same conditions as a raw `Microsoft.Graph.ServiceException` with Graph's own wording (message embeds the Graph error code, e.g. `Code: quotaLimitReached`) — match on the code/theme, not the friendly sentence. Verified raw over-size form: `Code: invalidRequest` / `The payload of the request was too large` with `Inner error: Code: maxFileSizeExceeded` — rejected at upload-session creation from the file's declared size, before any bytes are transferred.

What activities can produce this error:
- **Upload Files** (`UploadFilesConnections`), legacy **Upload File** (`UploadFile`).
- Attachment uploads on Mail/Calendar writes use the same upload-session mechanics for large attachments and can fault with the session messages.

What can cause it:
- **Target storage full** — the user's OneDrive or the SharePoint site collection hit its quota. Deterministic until space is freed; not fixed by retrying.
- **File over the per-file limit** — exceeds the Graph/SharePoint maximum upload size.
- **Interrupted upload session** — transient network failure or timeout during a large chunked upload; the session expires or loses chunks. Usually clears on retry.

What to look for:
- Target drive's free space and the file's size — distinguishes the deterministic limits from the transient session failures.
- Whether the failure repeats with the same file (limit) or only intermittently / for large files on slow links (session).

> **Different cause, do not apply this playbook:**
> - `Too many requests.` / `The app or user has been throttled.` — rate limiting, not storage; use [request-throttled.md](./request-throttled.md). The quota message here is a **storage** limit and is explicitly NOT a throttle — backing off does not fix it.
> - `The specified item name already exists.` — name conflict; use [item-name-already-exists.md](./item-name-already-exists.md).
> - `The resource could not be found.` — destination folder doesn't resolve; use [drive-item-not-found.md](./drive-item-not-found.md).
> - Local source path missing on the runtime machine — surfaces as a local file-not-found, not a Graph error; fix the source path. Note: `UploadFilesConnections` skips empty files with a warning rather than faulting.

## Investigation

1. Classify the message: quota, per-file size, or upload session.
2. For quota: check the target OneDrive / SharePoint site storage usage (site admin or OneDrive UI) — confirm it is at/near the limit.
3. For size: get the file's size and compare against the service's per-file upload maximum.
4. For session failures: check whether the failure reproduces — re-run once; correlate with network interruptions on the runtime machine and with file size (only large files use chunked sessions).

## Resolution

- **If quota reached:** free storage in the target OneDrive/site (empty recycle bin — items there still count), raise the site's storage quota, or upload to a different drive. Re-run after space is available.
- **If file too large:** compress or split the file, or store it where the limit allows and share a link instead.
- **If upload session failed/incomplete/not found:** transient — retry the upload (wrap in a Retry scope with backoff). If it reproduces consistently for the same large file, investigate the runtime machine's network stability (proxy idle timeouts on long uploads) before escalating.
