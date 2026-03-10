# XAML GSuite Activities

Google Suite activity patterns for `UiPath.GSuite.Activities`. Always get full XAML from `uipcli rpa get-default-activity-xaml` — this file covers confirmed patterns from real workflows only.

## Package + Connection Pattern

Package: `UiPath.GSuite.Activities`

All GSuite activities authenticate via two attributes:
```xml
ConnectionId="<guid>" UseConnectionService="True"
```

Use `uipcli is connections list --format json` to obtain the connection GUID. If no GSuite connection exists, create one: `uipcli is connections create <gsuite-connector-key>`. Verify it's active: `uipcli is connections ping <connection-id>`. All activity names end in `Connections` (e.g., `GetNewestEmailConnections`, `ReadRangeConnections`).

## Model Types

| Variable Type | Description | Key Properties |
|--------------|-------------|----------------|
| `UiPath.GSuite.Models.GmailMessage` | Email object | `.FromAddress`, `.Subject`, `.Body`, `.Attachments` |
| `UiPath.GSuite.Gmail.Models.GmailAttachmentLocalItem[]` | Downloaded attachment files | array of local file references |
| `UiPath.GSuite.Drive.Models.GDriveRemoteItem` | Drive file or folder | `.IsFolder`, `.Url`, `.Name`, `.Id` |
| `UiPath.GSuite.Drive.Models.GDriveLocalItem` | Locally downloaded Drive file | `.FilePath`, `.Name` |
| `UiPath.GSuite.Calendar.Models.GSuiteEventItem` | Calendar event | `.Summary`, `.Description`, `.OrganizerEmail`, `.Organizer.DisplayName`, `.StartDateTime`, `.EndDateTime` |
| `UiPath.GSuite.Activities.Utilities.JobInformation` | Trigger job data variable | `.JobId`, `.TriggerTime` |
| `UiPath.GSuite.Sheets.Models.RangeInformation` | Spreadsheet range metadata | `.SheetName`, `.StartRow`, `.EndRow`, `.StartColumn`, `.EndColumn` |

## Gmail Activities

### GetNewestEmailConnections

Retrieves the most recent email matching the criteria.

Key attributes:
- `Folder` — folder selection; use `BrowserFolderId` + `BrowserFolder` for Browse mode (e.g., `BrowserFolderId="INBOX"`)
- `UnreadOnly` — `"True"` / `"False"`
- `WithAttachmentsOnly` — `"True"` / `"False"`
- `MarkAsRead` — `"True"` / `"False"`
- `ImportantOnly` — `"True"` / `"False"`
- `StarredOnly` — `"True"` / `"False"`
- Output: `Result` as `UiPath.GSuite.Models.GmailMessage`

### ForEachEmailConnections

Iterates over multiple emails. Uses a **three-argument** body delegate.

Key attributes:
- `Folder` — same Browse pattern as above
- `MaxResults` — integer cap on emails processed
- `ImportantOnly`, `UnreadOnly`, `WithAttachmentsOnly` — filter flags
- Body delegate arguments:
  - `Argument1`: `UiPath.GSuite.Models.GmailMessage` named `"CurrentEmail"`
  - `Argument2`: `x:Int32` named `"CurrentEmailIndex"` (index within current batch)
  - Outer scope also provides `CurrentIndex` / `Length` counters

### SendEmailConnections

Key attributes:
- `To`, `Cc`, `Bcc` — `IEnumerable<string>` (use `new string[]{"a@b.com"}` in CSharpValue)
- `Subject`, `Body` — string values
- `InputType` — `"HTML"` or `"PlainText"`
- `Importance` — enum (Normal / High / Low)
- `SaveAsDraft` — `"True"` / `"False"`
- `AttachmentInputMode` — `"Existing"` or other modes

### DownloadAttachmentsConnections

Downloads email attachments to disk.

Key attributes:
- `Email` — `GmailMessage` variable
- `ExcludeInlineAttachments` — `"True"` / `"False"`
- `SearchMode` — attachment filter mode
- Output: `NewResult` as `UiPath.GSuite.Gmail.Models.GmailAttachmentLocalItem[]`

### ArchiveEmailConnections

Archives an email (removes from Inbox, keeps in All Mail).

Key attributes:
- `Email` — `GmailMessage` variable

### DeleteEmailConnections

Key attributes:
- `Email` — `GmailMessage` variable
- `PermanentlyDelete` — `"True"` to bypass Trash

### MoveEmailConnections

Key attributes:
- `Email` — `GmailMessage` variable
- `Folder` — destination folder with `BrowserFolderId` / `BrowserFolder` Browse pattern
- Output: `Result` as `GmailMessage`

### MarkAsReadUnreadConnections

Key attributes:
- `Email` — `GmailMessage` variable
- `MarkAs` — `"Read"` or `"Unread"`

### ApplyEmailLabelsConnections

Key attributes:
- `Email` — `GmailMessage` variable
- `SelectedLabels` — base64-encoded JSON string representing label selection
- `LabelSelectionMode` — selection mode enum

### RemoveEmailLabelsConnections

Key attributes:
- `Email` — `GmailMessage` variable
- `SelectedLabels` — base64-encoded JSON string (same format as Apply)

### TurnOnAutomaticRepliesConnections

Key attributes:
- `StartTime` — `DateTime`
- `EndTime` — `DateTime`
- `MessageBodyHtml` — HTML body string
- `MessageSubject` — subject string

### TurnOffAutomaticRepliesConnections

No configurable parameters — disables vacation auto-reply.

## Gmail Triggers

### NewEmailReceived

Fully qualified name: `UiPath.GSuite.Activities.Gmail.Triggers.NewEmailReceived`

Key attributes:
- `Filter` — child element with `LogicalOperator` and `Criteria`/`StringValue` conditions
- `IncludeAttachments` — `"True"` / `"False"`
- `MarkAsRead` — `"True"` / `"False"`
- `WithAttachmentsOnly` — `"True"` / `"False"`
- Output: `Result` as `UiPath.GSuite.Models.GmailMessage`, `JobData` as `UiPath.GSuite.Activities.Utilities.JobInformation`

### EmailSent

Fully qualified name: `UiPath.GSuite.Activities.Gmail.Triggers.EmailSent`

Key attributes:
- `IncludeAttachments` — `"True"` / `"False"`
- `WithAttachmentsOnly` — `"True"` / `"False"`
- Output: `Result` as `UiPath.GSuite.Models.GmailMessage`, `JobData` as `UiPath.GSuite.Activities.Utilities.JobInformation`

## Google Sheets Activities

### ReadRangeConnections

Generic type parameter: `System.Data.DataTable`

Key attributes:
- `Item` — spreadsheet selector; use Browse mode with `BrowserItemId` + `BrowserItem`
- `Range` — sheet name (e.g., `"Sheet1"`) or specific range (e.g., `"Sheet1!A1:D10"`)
- `HasHeaders` — `"True"` / `"False"`
- `ReadAs` — read mode (e.g., `"DataTable"`)
- Output: `Result` as `System.Data.DataTable`, `RangeInformation` as `UiPath.GSuite.Sheets.Models.RangeInformation`

### WriteRangeConnections

Key attributes:
- `Item` — spreadsheet selector (Browse or UrlOrId mode)
- `Range` — sheet name or range string
- `Source` — `System.Data.DataTable` variable
- `WriteMode` — `"Append"` or `"Overwrite"`
- `IncludeHeaders` — `"True"` / `"False"`
- `RowPosition` — row index when mode is Overwrite
- `WorkingWithTemplateSpreadsheet` — `"True"` / `"False"`

### WriteRowConnections

Key attributes:
- `Item` — spreadsheet selector
- `Range` — sheet name or range
- `ArrayRow` — `object[]` variable containing row values
- `DataType` — `"ArrayRow"`
- `HasHeaders` — `"True"` / `"False"`
- `WriteMode` — `"Append"` or `"Overwrite"`
- `RowPosition` — target row index

### CreateSpreadsheetConnections

Key attributes:
- `SpreadsheetName` — name for the new spreadsheet
- `Item` — parent folder (Browse mode with `BrowserItemId` + `BrowserItem`)
- `ParentFolderInputMode` — folder selection mode
- `FirstSheetName` — name for the first sheet tab
- `ConflictResolution` — behavior when file with same name exists
- Output: `NewSpreadsheet` as `UiPath.GSuite.Drive.Models.GDriveRemoteItem`

## Google Sheets Triggers

### RowAddedToSheetBottom

Fully qualified name: `UiPath.GSuite.Activities.Sheets.Triggers.RowAddedToSheetBottom<System.Data.DataRow>`

Key attributes:
- `Item` — spreadsheet (Browse mode)
- `SheetName` — name of the sheet tab to watch
- `HasHeaders` — `"True"` / `"False"`
- Output: `AddedRow` as `System.Data.DataRow`, `Spreadsheet` as `UiPath.GSuite.Drive.Models.GDriveRemoteItem`, `JobData` as `UiPath.GSuite.Activities.Utilities.JobInformation`

## Google Drive Activities

### GetFileFolderConnections

Key attributes:
- `Item` — file/folder selector with `InputMode` (`"Browse"`, `"UrlOrId"`, or `"FullPath"`)
- Output: `Result` as `UiPath.GSuite.Drive.Models.GDriveRemoteItem`

### GetFileListConnections

Key attributes:
- `Item` / `ManualEntryLocation` — folder to list contents of
- `LocationInputMode` — `"EnterId"` or `"Browse"`
- `MaxResults` — integer cap on results
- `StarredOnly` — `"True"` / `"False"`
- `WhatToReturn` — `"Files"`, `"Folders"`, or `"FilesAndFolders"`
- `Filter` — child block for name/type filtering conditions
- Output: `Result` as `UiPath.GSuite.Drive.Models.GDriveRemoteItem[]`

### ForEachFileFolderConnections

Iterates items inside a Drive folder.

Key attributes:
- `Item` — folder selector (Browse mode)
- `MaxResults` — cap on items iterated
- `WhatToReturn` — `"Files"`, `"Folders"`, or `"FilesAndFolders"`
- Body delegate argument: `CurrentItem` as `UiPath.GSuite.Drive.Models.GDriveRemoteItem`

### UploadFilesConnections

Key attributes:
- `MultipleFilesToUpload` — `IEnumerable<string>` of local file paths
- `FilesInputMode` — `"MultipleByVariable"` when using a variable
- `Folder` — destination folder with `FolderInputMode` (`"Browse"` or `"UrlOrId"`)
- `ConflictResolution` — behavior on name conflict
- `Convert` — `"True"` to convert to Google Workspace format
- Output: `FirstResult` as `GDriveRemoteItem`, `AllResults` as `UiPath.GSuite.Drive.Models.GDriveRemoteItem[]`

### DownloadFileConnections

Key attributes:
- `Item` / `File` — file selector with `FileInputMode` (`"Browse"`, `"UrlOrId"`)
- `DownloadSpreadsheetAs` — export format for Sheets (e.g., `"xlsx"`, `"csv"`)
- `DownloadDocumentAs` — export format for Docs (e.g., `"docx"`, `"pdf"`)
- `DownloadPresentationAs` — export format for Slides (e.g., `"pptx"`, `"pdf"`)
- `DownloadDrawingAs` — export format for Drawings (e.g., `"png"`, `"svg"`)
- Output: `NewResult` as `UiPath.GSuite.Drive.Models.GDriveLocalItem`

## Google Drive Triggers

### NewFileCreated

Fully qualified name: `UiPath.GSuite.Activities.Drive.Triggers.NewFileCreated`

Key attributes:
- `Item` / `BrowserLocation` — folder to watch (Browse mode)
- `Filter` — child block for name/type filtering conditions
- Output: `Result` as `UiPath.GSuite.Drive.Models.GDriveRemoteItem`, `JobData` as `UiPath.GSuite.Activities.Utilities.JobInformation`

## Google Calendar Activities

### CreateEventConnections

Key attributes:
- `CalendarArgument` — calendar selector; use Browse mode with `BrowserId` set to the **email address** (Google account) owning the calendar
- `CalendarInputMode` — `"Browse"` or `"UrlOrId"`
- `Title` — event title string
- `StartDateTime` — `DateTime`
- `EndDateTime` — `DateTime`
- `AllDayEvent` — `"True"` / `"False"`
- `Timezone` — IANA timezone string (e.g., `"Europe/London"`)
- `PreferredReturnTimezone` — timezone for returned event times
- `ShowAs` — free/busy status (`"Busy"`, `"Free"`)
- `Visibility` — `"Default"`, `"Public"`, or `"Private"`
- `SendNotification` — `"True"` / `"False"`
- `GuestCanInviteOthers` — `"True"` / `"False"`
- `GuestCanModifyEvent` — `"True"` / `"False"`
- `GuestCanSeeAttendeesList` — `"True"` / `"False"`
- `AddConferenceData` — `"True"` to add Google Meet link
- Output: `Result` as `UiPath.GSuite.Calendar.Models.GSuiteEventItem`

## Google Calendar Triggers

### NewEventCreated

Fully qualified name: `UiPath.GSuite.Activities.Calendar.Triggers.NewEventCreated`

Key attributes:
- `BrowserCalendarFriendlyName` — display name of the calendar to watch
- Output: `Result` as `UiPath.GSuite.Calendar.Models.GSuiteEventItem`, `JobData` as `UiPath.GSuite.Activities.Utilities.JobInformation`

### NewEventInvitationReceived

Fully qualified name: `UiPath.GSuite.Activities.Calendar.Triggers.NewEventInvitationReceived`

Output: `Result` as `UiPath.GSuite.Calendar.Models.GSuiteEventItem`, `JobData` as `UiPath.GSuite.Activities.Utilities.JobInformation`

## Key Patterns

| Pattern | Notes |
|---------|-------|
| Connection | `ConnectionId="<guid>" UseConnectionService="True"` on every activity |
| Activity naming | All activity names end in `Connections` (e.g., `GetNewestEmailConnections`) |
| Folder selection (Gmail) | `BrowserFolderId="INBOX"` + `BrowserFolder="Inbox"` for Browse mode |
| Item selection (Drive/Sheets) | `BrowserItemId="<drive-id>"` + `BrowserItem="<name>"` for Browse mode |
| Calendar Browse | `BrowserId` = Google account email address (not a Drive ID) |
| Output variable binding | Declare variable of correct model type; bind via `Result="[varName]"` attribute |
| `GmailMessage` access | `.FromAddress`, `.Subject`, `.Body`, `.Attachments` |
| `GDriveRemoteItem` access | `.IsFolder`, `.Url`, `.Name`, `.Id` |
| `GSuiteEventItem` access | `.Summary`, `.Description`, `.OrganizerEmail`, `.Organizer.DisplayName` |
| Trigger outputs | Always two: primary result (email/file/event) + `JobData: JobInformation` |
| `ForEachEmailConnections` | Three-arg body: `Argument1` (`GmailMessage` `"CurrentEmail"`), `Argument2` (`Int32` `"CurrentEmailIndex"`) |
| `ForEachFileFolderConnections` | One-arg body: `CurrentItem` as `GDriveRemoteItem` |
| `RowAddedToSheetBottom` | Generic type param `System.Data.DataRow`; output `AddedRow: DataRow` |
| Full XAML | Always use `uipcli rpa get-default-activity-xaml` for complete activity XAML |
