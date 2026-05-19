---
confidence: high
---

# O365 — Multiple items with the same name in the specified local folder

## Context

What this looks like:
- A download activity from `UiPath.MicrosoftOffice365.Activities` throws `Office365Exception`
- Error message: `Multiple items with the name <name> found in the specified folder.`
- Job faults synchronously the moment the activity runs

What activities can produce this error:
- **Download Email** (`DownloadEmailConnections`) — `ConflictResolution = Fail` and the **local** destination folder already contains a file with the target email's filename
- **Download File** (`DownloadFileConnections`) — `ConflictResolution = Fail` and the **local** destination folder already contains a file with the target file's name
- **Download Email Attachments** (`DownloadEmailAttachments`) — either:
  - `ConflictResolution = Fail` and the **local** destination folder already contains a file with one of the attachment names, OR
  - two or more attachments on the same email resolve to the same local destination filename

What can cause it:
- The **local** destination folder already contains a file with the same name as the file being written, and `ConflictResolution` is `Fail`. 
- For `DownloadEmailAttachments` only: two or more attachments on the same email share a filename (case-insensitive), so even an empty destination folder would end up with duplicates. With `ConflictResolution = Fail`, the activity detects this and throws before writing anything.

> **Conflict is on the local filesystem, not in OneDrive/SharePoint.** The wording "in the specified folder" refers to the **local** destination folder configured on the activity — not a remote Microsoft Graph location.
>
> **Different message, related cause:** when the conflict is on the **remote** OneDrive/SharePoint/Excel side (Create Folder, Copy/Move/Rename Item, Upload Files, Create Workbook, Add Sheet, Rename Sheet), the activity throws `The specified item name already exists.` instead. See [item-name-already-exists.md](./item-name-already-exists.md).

## Resolution

The error is unambiguous; no further investigation is needed. Stop the investigation and ask the user to do one of the following:

1. **Change the destination filename** so it is unique within the local destination folder (for `DownloadEmailConnections` and `DownloadFileConnections`, this means changing the file name in `Destination path`; for `DownloadEmailAttachments`, the attachment names are dictated by the email and cannot be changed — use option 2 or 3).
2. **Ensure the local destination folder contains no file with that name** — delete, rename, or move the existing file before re-running the workflow.
3. **Change the `ConflictResolution(conflict behavior)`** on the activity to a value that handles the duplicate:
   - `Rename` — automatically rename the new file to a unique name. For `DownloadEmailAttachments`, this also handles the genuine multiple-attachments-with-the-same-name case.
   - `Replace` — overwrite the existing local file.
