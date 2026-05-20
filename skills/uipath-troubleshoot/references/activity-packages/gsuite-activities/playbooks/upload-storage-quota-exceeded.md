---
confidence: high
---

# GSuite Upload — Drive storage quota or shared drive file limit exceeded

## Context

What this looks like — `GSuiteException` with the format `Upload failed after {bytesUploaded} bytes. {googleError}`. The `{googleError}` portion comes verbatim from the Google API and indicates a 403 quota condition. Common observed forms:

- `Upload failed after 0 bytes. The service drive has thrown an exception. HttpStatusCode is Forbidden. The file limit for this shared drive has been exceeded.`
- `Upload failed after 0 bytes. Google.Apis.Requests.RequestError`
  `The user's Drive storage quota has been exceeded. [403]`
  `Errors [`
  `Message[The user's Drive storage quota has been exceeded.] Location[ - ] Reason[storageQuotaExceeded] Domain[usageLimits]`
  `]`

`bytesUploaded` is typically `0` when the limit is exceeded before the upload starts, but can be non-zero if the limit is hit mid-upload.

What activities can produce this error:
- **Drive uploads** — `UploadFilesConnections` (modern), legacy `UploadFile`
- **Gmail attachment uploads** — `SendEmailConnections`, `ReplyToEmailConnections`, `ForwardEmailConnections` when the email carries an attachment large enough to require a multipart upload

What can cause it — two underlying quota conditions, both surfaced as Google 403:
- **`storageQuotaExceeded`** — the authenticated user's Drive storage is full. Applies to the entire account quota (free tier, Workspace plan storage, or pooled storage).
- **Shared drive file count limit** — the destination shared drive has hit Google's hard limit of items it can hold (currently 500,000). Typical wording: `The file limit for this shared drive has been exceeded.` Bytes do not matter here — every file/folder counts toward the limit, including trashed items not yet permanently deleted.

These are the only two causes that can produce the messages above. They are not transient and will not resolve themselves on retry.

## Resolution

The error is unambiguous; no further investigation is needed. The storage is full. Stop the investigation and ask the user to free space (or escalate the quota) before running the workflow again:

1. **Confirm which limit was hit** by reading the Google error portion of the message:
   - `storageQuotaExceeded` / `The user's Drive storage quota has been exceeded.` → user account storage is full
   - `The file limit for this shared drive has been exceeded.` → shared drive has hit the 500K item cap
2. **Ask the user to make space:**
   - For account storage: empty Drive Trash, delete or transfer-out large files, or upgrade the Google Workspace storage plan.
   - For shared drive file limit: delete unused items from the shared drive (including emptying the shared drive Trash — trashed items still count), move items to a different shared drive, or split the workload across multiple shared drives.
3. **Do not retry the workflow** until the user confirms space has been freed. Re-running against a still-full quota will produce the same exception.
