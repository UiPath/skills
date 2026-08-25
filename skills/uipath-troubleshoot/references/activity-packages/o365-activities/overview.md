# Microsoft Office 365 Activities

Activities from the `UiPath.MicrosoftOffice365.Activities` package for automating Microsoft 365 services covered by current diagnostics: Outlook (Mail), OneDrive and SharePoint document libraries (Files), and Excel. Modern activities call Microsoft Graph through OAuth-authenticated connections managed by Integration Service; legacy XAML activities use an Office 365 application-scope container (Windows only).

## How Connections Work

When a modern activity executes, it:

1. Resolves the configured Integration Service connection to obtain an OAuth access token
2. Issues a Microsoft Graph REST API request (Outlook, OneDrive, SharePoint, or Excel)
3. Maps the Graph response back into the activity output, or throws on error

Failures can originate at any of those layers — connection resolution (Integration Service), token validation (Microsoft Identity), the Graph call itself, or post-processing inside the activity. Knowing which layer produced the error narrows the investigation.

## Key Activity Types

### Mail (Outlook)

- **Get Newest Email** (`GetNewestEmail`) — retrieves the single most recent message matching a configured filter from a configured mail folder.
- **Folder-scoped read activities** (`GetEmailListConnections`, `ForEachEmailConnections`, plus the persistence and trigger pair `WaitForEmailReceived` / `NewEmailReceived`, and the outbound pair `WaitForEmailSent` / `EmailSent`) — read or wait for messages in a configured mail folder; folder is resolved by ID, path, or browse selection.
- **Move Email** (`MoveEmailConnections`, legacy `MoveMail`) — move a message into a destination mail folder selected by ID or by path. `MoveEmailConnections` exposes `CreateFolderIfMissing` for path-based input.
- **Download operations** (`DownloadEmailConnections`, `DownloadEmailAttachments`) — write a message body or its attachments to a local destination folder; behavior on duplicate local filename is governed by the `ConflictBehavior` enum (`Replace`, `Fail`, `Rename`).

### Files (OneDrive / SharePoint)

- **Item write operations** (`CreateFolderConnections`, `CopyItemConnections`, `MoveItemConnections`, `RenameItemConnections`, `UploadFilesConnections`, plus legacy `CreateFolder` and `UploadFile`) — create, copy, move, rename, or upload Drive items; behavior on duplicate name in the destination is governed by the `ConflictBehavior` enum (`Replace`, `Fail`, `Rename`).
- **Item resolution by ID, URL, path, or browse selection** (most Files activities, e.g., `GetFileFolderConnections`, `GetFileFolderMetadataConnections`, `GetFileListConnections`, `DownloadFileConnections`, `DeleteItemConnections`, `ShareItemConnections`, `UpdateFileFolderMetadataConnections`, `CheckinCheckoutFileConnections`, `ForEachFileFolderConnections`, `AssignSensitivityLabelConnections`, `GetSensitivityLabelsConnections`, persistence `WaitForFileCreated` / `WaitForFileUpdated`, plus the write operations above) — resolve a target Drive item against Microsoft Graph.
- **Download File** (`DownloadFileConnections`, legacy `DownloadFile`, legacy `ExportAsPdf`) — write a Drive item to a local destination; behavior on duplicate local filename is governed by `ConflictResolution`.

### Excel

- **Create Workbook** (`CreateWorkbookConnections`, legacy `CreateWorkbook`) — create a new `.xlsx` in OneDrive or a SharePoint document library; behavior on duplicate workbook name is governed by `ConflictBehavior`.
- **Sheet operations** (`AddSheetConnections`, `RenameSheetConnections`, legacy `AddSheet`) — add or rename a sheet (tab) inside a workbook; `AddSheetConnections` honors `ConflictBehavior` on duplicate sheet name.

## Common Failure Patterns

### Mail

- **Filter returns no matching email** — Mailbox contains zero messages matching the configured filter at the moment the activity runs. `Get Newest Email` throws `Office365Exception: No email matching the filter criteria, received in the last 1 hour has been found...` synchronously.
- **Mail folder not found** — Mail activity (`MoveEmailConnections`, `GetNewestEmail`, `GetEmailListConnections`, `ForEachEmailConnections`, `WaitForEmailReceived`, `NewEmailReceived` trigger, legacy `MoveMail`) cannot resolve the configured `MailFolder`. Surfaces as one of: `Office365Exception: The resource could not be found.`, `Folder named '<name>' could not be found on this account.` , or `Cannot find item configured with connection <connection> at path <folder>.`.
- **Local-filesystem name conflict on download** — `DownloadEmailConnections` or `DownloadEmailAttachments` throws `Office365Exception: Multiple items with the name <name> found in the specified folder.` because the **local** destination folder already contains a file with that name and `ConflictResolution = Fail`, or because two attachments on the same email resolve to the same local filename. Conflict is on the local filesystem, not in OneDrive/SharePoint.
- **Message not found** — message-by-ID activity (forward, reply, mark, delete, archive, download, get-by-ID) cannot resolve the message: deleted/moved, or the mailbox-scoped ID was used against a different mailbox. Surfaces as `The resource could not be found.`, raw `ErrorItemNotFound`, or `ErrorInvalidMailboxItemId`.
- **Invalid OData filter query** — `Invalid Query. Please use OData format for filter queries. Press F1 for examples.` from `GetMail` / `GetNewestEmail` / list-and-iterate reads with a malformed `$filter`.
- **Send rejected** — invalid recipient, shared-mailbox send without Exchange Send As rights, message size exceeded (raw Graph wording), or `File does not exist: <path>` for a missing attachment.
- **Trigger connection event failure** — `NewEmailReceived` / `EmailSent` faults at the Integration Service connection layer (`ConnectionHttpException`, raw or wrapped) while fetching the event email, debug sample, or token.
- **Raw NullReferenceException from a legacy Mail activity** — null `Message` input or null recipient-array element dereferenced before the Graph call; raw NRE type always indicates a legacy activity.

### Files (OneDrive / SharePoint)

- **404 — file or folder not found** — Files activity fails to resolve the configured ID, URL, path, or browse selection because the Drive item was deleted, moved out of scope, or is not accessible to the connection. Surfaces as `Office365Exception: The resource could not be found.` or as the wrapping form `Cannot find item configured with connection <connection> at path <path>.`
- **Item name already exists** — Files write activity (`CreateFolderConnections`, `CopyItemConnections`, `MoveItemConnections`, `RenameItemConnections`, `UploadFilesConnections`) throws `Office365Exception: The specified item name already exists.` when the destination already contains an item with the target name and `ConflictBehavior = Fail`. Affects legacy activities equivalents as well (`CreateFolder`, `UploadFile`).
- **Local-filesystem name conflict on download** — `DownloadFileConnections` throws `Office365Exception: Multiple items with the name <name> found in the specified folder.` when the **local** destination folder already contains a file with that name and `ConflictResolution = Fail`. Conflict is on the local filesystem, not in OneDrive/SharePoint.
- **Create Folder invalid name/path** — `CreateFolderConnections` rejects its own input: null name/path/parent, empty or whitespace-padded path segments, or an intermediate path segment that exists as a file.
- **Download conversion or destination error** — folder bound where a file is required, unsupported PDF-conversion source extension, non-`.pdf` export destination, or unresolvable shared-item parent drive.
- **Upload quota / size / session failure** — target storage full (`The user has reached their quota limit.`), file over the per-file limit, or a chunked upload session broken mid-transfer.
- **Null `DriveItem` input on legacy Copy Item** — raw `ArgumentNullException: Value cannot be null. (Parameter 'DriveItem')` when an upstream search matched nothing.

### Excel

- **Workbook or sheet name already exists** — `CreateWorkbookConnections`, `AddSheetConnections`, or `RenameSheetConnections` throws `Office365Exception: The specified item name already exists.` when the target workbook or sheet name collides and `ConflictBehavior = Fail`. Affects legacy `CreateWorkbook` and `AddSheet` as well.

## Package

NuGet: `UiPath.MicrosoftOffice365.Activities`
