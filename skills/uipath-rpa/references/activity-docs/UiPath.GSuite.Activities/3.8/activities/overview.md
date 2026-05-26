# XAML GSuite Activities

Google Suite activity patterns for `UiPath.GSuite.Activities`. Always get full XAML from `uip rpa activities get-default-xaml --use-studio` — this file covers confirmed patterns from real workflows only.

## Triggers in this package

This package contains five **integration triggers** (their namespaces all contain `.Triggers`): [`NewEmailReceived`](NewEmailReceived.md) (Gmail), [`NewFileCreated`](NewFileCreated.md) (Drive), [`NewEventCreated`](NewEventCreated.md) and [`NewEventInvitationReceived`](NewEventInvitationReceived.md) (Calendar), and [`RowAddedToSheetBottom`](RowAddedToSheetBottom.md) (Sheets). All return `isTrigger: true, triggerType: "integration"` from `uip rpa activities find` and require a `ConnectionId`. **Placement: strict** — first activity of the workflow's root `Sequence`, never inside `ui:TriggerScope`. Orchestrator + Integration Service subscribe externally and dispatch a fresh job per event. The `Filter` child element narrows server-side which events fire — use it instead of an `If` inside the handler. See [trigger-pattern-guide.md](../../../../trigger-pattern-guide.md).

## Package + Connection Pattern

Package: `UiPath.GSuite.Activities`

All GSuite activities authenticate via two attributes:
```xml
ConnectionId="<guid>" UseConnectionService="True"
```

Use `uip is connections list --output json` to obtain the connection GUID. If no GSuite connection exists, create one: `uip is connections create <gsuite-connector-key>`. Verify it's active: `uip is connections ping <connection-id>`. All activity names end in `Connections` (e.g., `GetNewestEmailConnections`, `ReadRangeConnections`).

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
| Full XAML | Always use `uip rpa activities get-default-xaml --use-studio` for complete activity XAML |
