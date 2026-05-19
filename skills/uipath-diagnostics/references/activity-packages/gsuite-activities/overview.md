# Google Workspace Activities

Activities from the `UiPath.GSuite.Activities` package for automating Google Workspace services: Gmail, Google Calendar, Google Drive, Google Sheets, Google Docs, Google Tasks, Google Forms, and Apps Script. Modern activities call Google REST APIs through OAuth-authenticated connections managed by Integration Service; legacy XAML activities use a `GSuiteApplicationScope` container (Windows only).

## How Connections Work

Modern activities are suffixed `*Connections` (e.g., `GetNewestEmailConnections`). When the activity executes, it:

1. Resolves the configured Integration Service connection to obtain an OAuth access token
2. Issues a Google REST API request (Gmail, Drive, Sheets, Calendar, Docs, Tasks, Forms, or Apps Script)
3. Maps the Google API response back into the activity output, or throws on error

Failures can originate at any of those layers — connection resolution (Integration Service), token validation (Google OAuth), the API call itself (Google service), or post-processing inside the activity. Knowing which layer produced the error narrows the investigation.

## Key Activity Types

### Gmail

- **Get Newest Email** (`GetNewestEmailConnections`) — retrieves the single most recent message matching a configured filter.
- **Send / Reply / Forward Email** (`SendEmailConnections`, `ReplyToEmailConnections`, `ForwardEmailConnections`) — send, reply, or forward a Gmail message. Uploads attachments via Gmail multipart upload, so they share Drive-class quota failures.

### Drive

- **Item write operations** (`CreateFolderConnections`, `CopyFileConnections`, `MoveFileConnections`, `RenameFileFolderConnections`, `UploadFilesConnections`, `CreateSpreadsheetConnections`, `CreateDocumentConnections`) — create, copy, move, rename, or upload Drive items; behavior on duplicate name in the destination is governed by the `ConflictResolution` enum (`Replace`, `Fail`, `Rename`, `AddSeparate`, `UseExisting`).
- **Item resolution by ID, URL, or path** (most Drive activities, e.g., `GetFileFolderConnections`, `GetFileFolderInfoConnections`, `DownloadFileConnections`, `DeleteFileOrFolderConnections`, `ShareFileFolderConnections`, plus the write operations above) — resolve a target file or folder against the Drive API; fails with HTTP 404 when the identifier no longer resolves.
- **Upload Files** (`UploadFilesConnections`, legacy `UploadFile`) — upload local files into Drive via multipart upload; subject to user storage quota and shared-drive file-count limit.

### Sheets

- **Add Sheet** (`AddSheetConnections`) — add a new sheet (tab) to an existing spreadsheet; behavior on duplicate sheet name is governed by `ConflictResolution` (`Fail`, `Replace`, `Rename`).
- **Cell-writing / grid-expanding activities** (`WriteRangeConnections`, `WriteCellConnections`, `WriteRowConnections`, `WriteColumnConnections`, `AutoFillRangeConnections`, `CopyPasteRangeConnections`, `AddSheetConnections`, plus legacy `WriteCell`, `WriteRange`, `AppendRow`, `AddNewSheet`, `AddDeleteColumns`, `AddDeleteRows`, `AutoFillRange`, `CopyPasteRange`, `CopySheet`, `BatchUpdateValuesScope`) — write cells or expand the bounded grid; auto-expansion makes them subject to the spreadsheet-wide 10,000,000-cell cap. `CopySheet` is legacy-only and the most aggressive trigger.
- **Range-addressed activities** (`ReadCellConnections`, `ReadRangeConnections`, `ReadRowConnections`, `ReadColumnConnections`, `WriteCellConnections`, `WriteRangeConnections`, `WriteRowConnections`, `WriteColumnConnections`, `AutoFillRangeConnections`, `CopyPasteRangeConnections`, `DeleteRangeConnections`, `ForEachRowConnections`, `SetRangeColorConnections`, `GetCellColorConnections`, plus legacy `ReadCell`, `ReadRange`, `ReadRow`, `ReadColumn`, `WriteCell`, `WriteRange`, `AutoFillRange`, `CopyPasteRange`, `ClearRange`, `DeleteRange`, `ForEachSheetRow`, `GetCellColor`) — accept a range or cell address in A1 notation; the supplied range is forwarded to the Google Sheets API and validated server-side.

## Common Failure Patterns

### Gmail

- **Filter returns no matching email** — Gmail mailbox contains zero messages matching the configured filter at the moment the activity runs. `Get Newest Email` throws `GmailException: No email matching the search criteria has been found` synchronously, with no retry or wait.

### Drive

- **Item name conflict** — Drive write activity throws `GSuiteException: Multiple items with the name <name> found in the specified folder.` when the target folder already contains an item with that name and `ConflictResolution` cannot resolve the duplicate. Affects Create Folder, Copy File, Move File, Rename, Upload, Create Spreadsheet, and Create Document.
- **404 — file or folder not found** — A Drive activity fails to resolve the configured ID, URL, or path because the resource was deleted, trashed, or is not accessible to the connection. Surfaces as one of: `File not found: <id>. [404]` (raw `Google.GoogleApiException`), `The service drive has thrown an exception. HttpStatusCode is NotFound. ...` (wrapped form), or `The resource was not found.` (translated form).
- **Upload storage quota or shared drive file limit exceeded** — Drive or Gmail attachment upload throws `GSuiteException: Upload failed after <N> bytes. ...` carrying a Google 403. Two underlying conditions: `storageQuotaExceeded` (user's Drive storage full) or `The file limit for this shared drive has been exceeded.` (shared drive at the 500K item cap). Affects `UploadFilesConnections`, legacy `UploadFile`, and Gmail send/reply/forward when the message has attachments.

### Sheets

- **Sheet name conflict** — `Add Sheet` throws `GSuiteException: A sheet with the same name already exists.` when the spreadsheet already contains a sheet with the configured `SheetName` (case-insensitive) and `ConflictResolution = Fail`. Restricted to `AddSheetConnections`.
- **10,000,000-cell limit exceeded** — Sheets write or grid-expand activity throws `GSuiteException` carrying a Google 400 BadRequest: `This action would increase the number of cells in the workbook above the limit of 10000000 cells.` The cap is the sum of the bounded grid (rows × columns) across every sheet in the spreadsheet, including empty cells. Hard Google quota; cannot be raised. Affects all cell-writing / grid-expanding Sheets activities.
- **Invalid range — unable to parse** — Range-addressed Sheets activity throws `GSuiteException` carrying a Google 400 BadRequest: `Invalid data[0]: Unable to parse range: <SheetName>!<CellRef>`. Common causes: 1-indexing mistake (`A0`), empty/null range variable, sheet name with spaces or special characters not single-quoted in A1 notation, stale sheet reference after a rename, or off-by-one in a dynamically-built address. Affects all range-addressed Sheets activities.

## Package

NuGet: `UiPath.GSuite.Activities`
