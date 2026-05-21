---
confidence: high
---

# GSuite Drive — Multiple items with the same name in the specified folder

## Context

What this looks like:
- An activity from `UiPath.GSuite.Activities` (Drive operations) throws `GSuiteException`
- Error message: `Multiple items with the name <name> found in the specified folder.`
- Job faults synchronously the moment the activity runs

What activities can produce this error:
- **Create Folder** (`CreateFolderConnections`) — `ConflictResolution = Fail` and a folder with that name already exists in the parent; or `ConflictResolution = UseExisting` and more than one folder with that name exists
- **Copy File** (`CopyFileConnections`) — destination already contains an item with the target name (`Fail`) or contains more than one (`Replace`)
- **Move File** (`MoveFileConnections`) — destination already contains an item with the target name (`Fail`) or more than one (`Replace`)
- **Rename File or Folder** (`RenameFileFolderConnections`) — `ConflictResolution = Fail` and an item with the new name already exists in the same parent
- **Upload Files** (`UploadFilesConnections`) — destination already contains an item with the target name (`Fail`) or more than one (`Replace`)
- **Create Spreadsheet** (`CreateSpreadsheetConnections`) — a spreadsheet with that name already exists in the parent
- **Create Document** (`CreateDocumentConnections`) — a document with that name already exists in the parent

What can cause it:
- The target Google Drive folder already contains one or more items with the same name as the new/target item, and the configured `ConflictResolution` ("conflict behavior") cannot resolve the conflict on its own. This is the only cause — the activity issues a name lookup against the Drive API in the parent folder and refuses to proceed.

> **Different cause, same message:** `DownloadAttachmentsConnections` (Gmail) throws the same message when two attachments on the same email resolve to the same **local** destination path. That is unrelated to Drive `ConflictResolution`. If the faulted activity is `DownloadAttachmentsConnections`, do not apply this playbook.

## Resolution

The error is unambiguous; no further investigation is needed. Stop the investigation and ask the user to do one of the following:

1. **Change the name** of the new/target item so it is unique within the destination folder.
2. **Ensure the destination folder contains no item with that name** (rename, delete, or move the existing item).
3. **Change the `ConflictResolution` (conflict behavior)** on the activity to a value that handles the duplicate:
   - `Rename` — automatically rename the new item to a unique name
   - `Replace` — replace the existing item (only when exactly one match exists; throws again if multiple matches)
   - `AddSeparate` — always create a new copy alongside the existing item(s)
   - `UseExisting` (Create Folder only) — return the existing folder instead of creating a new one (only when exactly one match exists)

   `RenameFileFolderConnections` only supports `Fail` and `AddSeparate`. The other Drive activities support the full enum.
