---
confidence: high
---

# O365 — The specified item name already exists

## Context

What this looks like:
- An activity from `UiPath.MicrosoftOffice365.Activities` throws `Office365Exception`
- Error message: `The specified item name already exists.`
- Job faults synchronously the moment the activity runs

What activities can produce this error:
- **Create Folder** (`CreateFolderConnections`) — folder with that name already exists in the destination and `ConflictBehavior = Fail`
- **Copy Item** (`CopyItemConnections`) — destination already contains an item with the target name and `ConflictBehavior = Fail`
- **Move Item** (`MoveItemConnections`) — destination already contains an item with the target name and `ConflictBehavior = Fail`
- **Rename Item** (`RenameItemConnections`) — an item with the new name already exists in the same parent
- **Upload Files** (`UploadFilesConnections`) — destination already contains an item with the target name and `ConflictBehavior = Fail`
- **Create Workbook** (`CreateWorkbookConnections`) — a workbook with that name already exists in the destination and `ConflictBehavior = Fail`
- **Add Sheet** (`AddSheetConnections`) — target workbook already contains a sheet with that name and `ConflictBehavior = Fail`
- **Rename Sheet** (`RenameSheetConnections`) — a sheet with the new name already exists in the workbook
- Legacy activities equivalents: `CreateFolder`, `UploadFile`, `CreateWorkbook`, `AddSheet`

What can cause it:
- The destination already contains an item (folder, file, workbook, or sheet) with the same name as the new/target item, and the configured `ConflictBehavior` is `Fail`.

## Resolution

The error is unambiguous; no further investigation is needed. Stop the investigation and ask the user to do one of the following:

1. **Change the name** of the new/target item (e.g., `FolderName`, `NewName`, `WorkbookName`, `SheetName`) so it is unique within the destination.
2. **Ensure the destination contains no item with that name** — rename, delete, or move the existing folder/file/workbook/sheet before re-running the workflow.
3. **Change the `ConflictBehavior`** on the activity to a value that handles the duplicate:
   - `Rename` — automatically rename the new item to a unique name
   - `Replace` — replace the existing item

   `Fail` is the value that surfaces this error. `RenameItemConnections` and `RenameSheetConnections` operate on existing items and do not expose the full enum — for those, only options 1 and 2 apply.
