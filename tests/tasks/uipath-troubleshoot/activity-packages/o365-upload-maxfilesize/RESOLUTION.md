**Root Cause:** The file the workflow tried to upload exceeds the OneDrive/SharePoint per-file upload maximum — Microsoft Graph rejected the upload outright at session creation.

**What went wrong:** The last job in folder Shared — process **ERN_O365_UploadQuotaSize** (job 7fd5e890-f162-4591-a895-e649b09aea02, run 2026-06-11 08:15 UTC, machine MOCK-HOST) — faulted after ~7 seconds in the **Upload File** activity (legacy `UploadFile`) in `O365_UploadQuotaSize.xaml`.

**Why:** The activity initiated a Microsoft Graph chunked upload (`LargeFileUploadTask`/`UploadSliceRequest`). Graph rejected it with `Code: invalidRequest — "The payload of the request was too large"`, inner error `Code: maxFileSizeExceeded` — the documented over-size rejection: the file's declared size exceeds the per-file limit, refused before any bytes transferred. Raw `ServiceException` (no Office365Exception wrapper) confirms the legacy code path. NOT a storage-quota problem (no `quotaLimitReached`), NOT a transient upload-session break, NOT throttling — wording for all three verified absent; deterministic on every run with the same file.

**Immediate fix:** Compress or split the file before upload, or store it where the limit allows and share a link instead; restart the job only after the file is reduced. Source: `references/activity-packages/o365-activities/playbooks/upload-file-quota-or-size.md` § Resolution ("If file too large").

**Preventive fix:** Add a pre-upload file-size check in the workflow and route oversize files to the split/compress/share-link path.
