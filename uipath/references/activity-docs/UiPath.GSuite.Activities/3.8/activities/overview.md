# XAML GSuite Activities

Google Suite activity patterns for `UiPath.GSuite.Activities`. Always get full XAML from `uip rpa get-default-activity-xaml` — this file covers confirmed patterns from real workflows only.

## Package + Connection Pattern

Package: `UiPath.GSuite.Activities`

All GSuite activities authenticate via two attributes:
```xml
ConnectionId="<guid>" UseConnectionService="True"
```

Use `uip is connections list --format json` to obtain the connection GUID. If no GSuite connection exists, create one: `uip is connections create <gsuite-connector-key>`. Verify it's active: `uip is connections ping <connection-id>`. All activity names end in `Connections` (e.g., `GetNewestEmailConnections`, `ReadRangeConnections`).

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
| Full XAML | Always use `uip rpa get-default-activity-xaml` for complete activity XAML |
