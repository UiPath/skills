# UiPath.MicrosoftOffice365.Activities — Coded Workflow API

`UiPath.MicrosoftOffice365.Activities`

**Service accessor:** `office365`
**Service type:** `IOffice365ConnectionsService`

## Service Overview

The `office365` service accessor follows the **connection-based** pattern. Each call to the top-level service creates a sub-service bound to a specific Microsoft 365 connection. Connection objects are created using the activity designer connection UI, then passed to the coded workflow.

| Sub-service | Method | Connection type | Description |
|-------------|--------|-----------------|-------------|
| `IMailService` | `office365.Mail(connection)` | `MailConnection` | Outlook email operations |
| `ICalendarService` | `office365.Calendar(connection)` | `MailConnection` | Calendar event operations |
| `IOneDriveService` | `office365.OneDrive(connection)` | `OneDriveConnection` | OneDrive and SharePoint file operations |
| `ISharepointService` | `office365.Sharepoint(connection)` | `OneDriveConnection` | SharePoint list operations |
| `IExcelService` | `office365.Excel(connection)` | `ExcelConnection` | Excel Online workbook operations |

## Auto-Imported Namespaces

- `UiPath.MicrosoftOffice365.Activities.Api`

## API Pattern: Connection-Based

Each call to a sub-service method requires a connection object that was configured in UiPath Studio:

```csharp
// Connection objects come from the Studio connection manager
var mailService = office365.Mail(new MailConnection("MyMailConnection"));
var oneDriveService = office365.OneDrive(new OneDriveConnection("MyOneDriveConnection"));
var excelService = office365.Excel(new ExcelConnection("MyExcelConnection"));
var calendarService = office365.Calendar(new MailConnection("MyCalendarConnection"));
var sharepointService = office365.Sharepoint(new OneDriveConnection("MySharePointConnection"));
```

---

## IOffice365ConnectionsService

Top-level service interface. Access via the `office365` accessor.

| Method | Returns | Description |
|--------|---------|-------------|
| `Mail(MailConnection connection)` | `IMailService` | Creates a mail service for Outlook operations. |
| `Calendar(MailConnection connection)` | `ICalendarService` | Creates a calendar service for event operations. |
| `OneDrive(OneDriveConnection connection)` | `IOneDriveService` | Creates a OneDrive/SharePoint file service. |
| `Sharepoint(OneDriveConnection connection)` | `ISharepointService` | Creates a SharePoint list service. |
| `Excel(ExcelConnection connection)` | `IExcelService` | Creates an Excel Online workbook service. |

---

## IMailService

Returned by `office365.Mail(connection)`. Provides Outlook email operations.

### Properties

| Property | Type | Description |
|----------|------|-------------|
| `SystemFolders` | `MailSystemFolders` | Provides access to standard system mail folders (Inbox, Sent, Drafts, etc.). |

### Methods

#### Retrieve Emails

| Method | Returns | Description |
|--------|---------|-------------|
| `GetMailFolders(string account = null)` | `IReadOnlyCollection<IMailFolder>` | Retrieves the list of mail folders for the account. |
| `GetNewestEmail(IMailFolder folder, MailFilter filter, string account, bool markAsRead, bool bodyAsHtml)` | `IMail` | Retrieves the most recent email matching the criteria. |
| `GetEmail(string emailId, string account, bool bodyAsHtml)` | `IMail` | Retrieves a specific email by ID. |
| `GetEmails(IMailFolder folder, MailFilter filter, string account, OrderBy orderBy, bool includeSubfolders, bool markAsRead, bool bodyAsHtml, int? maxResults)` | `IReadOnlyCollection<IMail>` | Retrieves emails matching the criteria. |

#### Send & Reply

| Method | Returns | Description |
|--------|---------|-------------|
| `SendEmail(string to, string subject, string body, string cc, string bcc, bool asDraft)` | `void` | Sends an email to a recipient. |
| `SendEmail(SendEmailRequest request)` | `void` | Sends an email using a request configuration object. |
| `ReplyToEmail(IMail mail, string body, string newSubject, string to, string cc, string bcc, bool asDraft)` | `void` | Replies to an email. |
| `ReplyToEmail(IMail mail, ReplyToEmailRequest request)` | `void` | Replies to an email using a request configuration object. |
| `ForwardEmail(IMail mail, string body, string newSubject, string to, string cc, string bcc, bool asDraft)` | `void` | Forwards an email. |
| `ForwardEmail(IMail mail, ForwardEmailRequest request)` | `void` | Forwards an email using a request configuration object. |

#### Manage Emails

| Method | Returns | Description |
|--------|---------|-------------|
| `MoveEmail(IMail mail, IMailFolder destination, string mailbox, bool bodyAsHtml)` | `void` | Moves an email to the specified folder. |
| `ArchiveEmail(IMail mail)` | `void` | Archives an email. |
| `DeleteEmail(IMail mail, bool deletePermanently)` | `void` | Deletes an email (permanently or to trash). |
| `DownloadEmail(IMail mail, bool bodyAsHtml)` | `Stream` | Downloads the email as a stream. |
| `MarkEmailAsRead(IMail mail)` | `void` | Marks an email as read. |
| `MarkEmailAsUnread(IMail mail)` | `void` | Marks an email as unread. |

#### Attachments

| Method | Returns | Description |
|--------|---------|-------------|
| `GetEmailAttachmentsInfo(IMail mail)` | `IReadOnlyCollection<IMailAttachmentInfo>` | Retrieves attachment metadata for an email. |
| `DownloadEmailAttachment(IMailAttachmentInfo info)` | `Stream` | Downloads a single attachment. |
| `DownloadEmailAttachments(IMail mail)` | `IReadOnlyDictionary<IMailAttachmentInfo, Stream>` | Downloads all attachments for an email. |

#### Categories & Automatic Replies

| Method | Returns | Description |
|--------|---------|-------------|
| `AddEmailCategories(IMail mail, IReadOnlyList<string> categories)` | `void` | Adds categories to an email. |
| `RemoveEmailCategories(IMail mail, IReadOnlyList<string> categories)` | `void` | Removes categories from an email. |
| `TurnOnAutomaticReplies(string internalMessage, string externalMessage, DateTimeOffset startTime, DateTimeOffset endTime, bool sendRepliesOutsideOrganization, bool sendRepliesToContactsOnly)` | `void` | Activates automatic out-of-office replies. |
| `TurnOffAutomaticReplies()` | `void` | Deactivates automatic out-of-office replies. |

---

## ICalendarService

Returned by `office365.Calendar(connection)`. Provides calendar event operations.

### Methods

| Method | Returns | Description |
|--------|---------|-------------|
| `GetCalendars()` | `IReadOnlyCollection<ICalendar>` | Returns all calendars for the authenticated account. |
| `GetDefaultCalendar()` | `ICalendar` | Returns the default calendar. |
| `GetEvents(DateTime startDate, DateTime endDate, ICalendar calendar, int top, string timeZone, string search)` | `IReadOnlyCollection<ICalendarEvent>` | Returns events in the specified date range. |
| `CreateEvent(ICalendar calendar, CreateEventRequest request)` | `ICalendarEvent` | Creates a new calendar event. |
| `UpdateEvent(ICalendarEvent calendarEvent, UpdateEventRequest changes)` | `ICalendarEvent` | Updates an existing calendar event. |
| `DeleteEvent(ICalendarEvent calendarEvent, string comment, DeleteEventMode deleteMode)` | `void` | Deletes or cancels a calendar event. |
| `ForwardEvent(ICalendarEvent calendarEvent, IEnumerable<string> attendees, string comment, bool forwardSeries)` | `void` | Forwards an event to additional attendees. |
| `RespondToEvent(ICalendarEvent calendarEvent, RsvpRequest request)` | `void` | Responds to an event invitation (Accept/Tentative/Decline). |

### `DeleteEventMode` Enum

| Value | Description |
|-------|-------------|
| `SingleEvent` | Deletes only this occurrence (default). |
| `AllEvents` | Deletes all events in the series. |
| `ThisAndFollowing` | Deletes this and all following events. |

---

## IOneDriveService

Returned by `office365.OneDrive(connection)`. Provides OneDrive and SharePoint file operations.

### Retrieve Files and Folders

| Method | Returns | Description |
|--------|---------|-------------|
| `GetFilesAndFolders(IFolder parent, bool trimDuplicates, string simpleSearchQuery, int maxResults)` | `IReadOnlyCollection<IDriveItem>` | Lists files and folders in a location. |
| `GetFilesAndFolders(DriveItemFilter filter, IFolder parent, bool trimDuplicates, bool includeSubfolders, int maxResults)` | `IReadOnlyCollection<IDriveItem>` | Lists files and folders with advanced filter. |
| `GetFiles(IFolder parent, bool trimDuplicates, string simpleSearchQuery, int maxResults)` | `IReadOnlyCollection<IFile>` | Lists only files in a location. |
| `GetFolders(IFolder parent, bool trimDuplicates, string simpleSearchQuery, int maxResults)` | `IReadOnlyCollection<IFolder>` | Lists only folders in a location. |
| `GetItem(string url)` | `IDriveItem` | Gets a file or folder by URL. |
| `GetItem(string id, string siteUrl, string libraryName)` | `IDriveItem` | Gets a file or folder by ID and SharePoint site. |
| `GetItem(IFolder parent, string relativePath)` | `IDriveItem` | Gets a file or folder by relative path. |
| `GetFile(string url)` | `IFile` | Gets a file by URL. |
| `GetFolder(string url)` | `IFolder` | Gets a folder by URL (null = root). |

### Upload, Download, Copy, Move

| Method | Returns | Description |
|--------|---------|-------------|
| `UploadFile(IResource file, IFolder destination, ConflictBehavior conflictBehavior, DataTable metadata)` | `IFile` | Uploads a single file. |
| `UploadFiles(IEnumerable<IResource> files, IFolder destination, ConflictBehavior conflictBehavior, DataTable metadata)` | `IReadOnlyCollection<IFile>` | Uploads multiple files. |
| `UploadFile(string path, IFolder destination, ConflictBehavior conflictBehavior, DataTable metadata)` | `IFile` | Uploads a file from a local path. |
| `DownloadFile(IFile file, bool convertToPdf)` | `Stream` | Downloads a file (optionally as PDF). |
| `CopyFile(IFile file, IFolder destination, string newName, ConflictBehavior conflictBehavior)` | `IFile` | Copies a file to a new location. |
| `CopyFolder(IFolder folder, IFolder destination, string newName, ConflictBehavior conflictBehavior)` | `IFolder` | Copies a folder to a new location. |
| `MoveFile(IFile file, IFolder destination, string newName, ConflictBehavior conflictBehavior)` | `IFile` | Moves a file to a new location. |
| `MoveFolder(IFolder folder, IFolder destination, string newName, ConflictBehavior conflictBehavior)` | `IFolder` | Moves a folder to a new location. |
| `CreateFolder(string name, IFolder parent, ConflictBehavior conflictBehavior)` | `IFolder` | Creates a new folder. |
| `DeleteItem(IDriveItem item)` | `void` | Deletes a file or folder. |

### Share

| Method | Returns | Description |
|--------|---------|-------------|
| `ShareFile(IFile file, GranteePermission permission)` | `string` | Shares a file with organization; returns link URL. |
| `ShareFile(IFile file, IEnumerable<string> recipients, string message, bool sendSharingInvitationEmail, bool requiresSignIn, GranteePermission permission)` | `string` | Shares a file with specific people. |
| `ShareFolder(IFolder folder, GranteePermission permission)` | `string` | Shares a folder with organization; returns link URL. |

### `ConflictBehavior` Enum

| Value | Description |
|-------|-------------|
| `Fail` | Fails the operation if a conflict exists. |
| `Replace` | Replaces the existing item. |
| `Rename` | Renames the new item to avoid the conflict. |

### `GranteePermission` Enum

| Value | Description |
|-------|-------------|
| `View` | Read-only access. |
| `Edit` | Read and write access. |

---

## ISharepointService

Returned by `office365.Sharepoint(connection)`. Provides SharePoint list operations.

### Methods

| Method | Returns | Description |
|--------|---------|-------------|
| `GetList(string siteIdentifier, string listIdentifier, bool useDisplayNamesAsColumnNames)` | `ISharepointList` | Retrieves list metadata by site URL/ID and list title/ID. |
| `GetItems(ISharepointList list, IEnumerable<string> columns, SharepointItemFilter filter)` | `DataTable` | Retrieves list items as a DataTable. |
| `AddItem(ISharepointList list, DataRow row)` | `DataRow` | Adds a new item to a SharePoint list. |
| `UpdateItem(ISharepointList list, DataRow row)` | `DataRow` | Updates an existing list item (row must include `ID` column). |
| `DeleteItems(ISharepointList list, IEnumerable<string> columns, SharepointItemFilter filter)` | `DataTable` | Deletes list items matching the filter. |
| `CreateItem(ISharepointList list)` | `DataRow` | Creates an empty DataRow based on the list schema. |

---

## IExcelService

Returned by `office365.Excel(connection)`. Provides Excel Online workbook operations.

### Workbook & Sheet Management

| Method | Returns | Description |
|--------|---------|-------------|
| `GetWorkbooks(IDriveItem parentFolder, string search, int maxResults)` | `IReadOnlyCollection<IWorkbook>` | Lists workbooks in a location. |
| `AddWorkbook(string workbookName, IDriveItem parentFolder, string firstSheetName, ConflictBehavior conflictResolution)` | `IWorkbook` | Creates a new workbook. |
| `GetSheets(IWorkbook workbook)` | `IReadOnlyCollection<IWorksheet>` | Lists all sheets in a workbook. |
| `GetRanges(IWorkbook workbook)` | `IReadOnlyCollection<IRange>` | Lists all named ranges and sheets. |
| `GetNamedRanges(IWorkbook workbook)` | `IReadOnlyCollection<INamedRange>` | Lists named ranges. |
| `AddSheet(IWorkbook workbook, string sheetName, ConflictBehavior conflictResolution)` | `IWorksheet` | Adds a new sheet to a workbook. |
| `RenameSheet(IWorkbook workbook, string replacedSheetName, string newSheetName)` | `void` | Renames a sheet. |
| `DeleteSheet(IWorkbook workbook, string sheetName)` | `void` | Deletes a sheet. |

### Read & Write Data

| Method | Returns | Description |
|--------|---------|-------------|
| `ReadRange(IWorkbook workbook, IRange range, bool hasHeaders, CellReadMode cellReadMode)` | `DataTable` | Reads a range of cells as a DataTable. |
| `WriteRange(IWorkbook workbook, IRange range, DataTable data, bool hasHeaders, RangeWriteMode writeMode, int insertRowPosition)` | `void` | Writes a DataTable to a range. |
| `ReadCell(IWorkbook workbook, IRange range, string cell, CellReadMode cellReadMode)` | `object` | Reads a single cell value. |
| `WriteCell(IWorkbook workbook, IRange range, string cell, object value)` | `void` | Writes a value to a single cell. |
| `WriteRow(IWorkbook workbook, IRange range, DataRow data, RangeWriteMode writeMode, int insertRowPosition)` | `void` | Writes a DataRow to a range. |
| `WriteRow(IWorkbook workbook, IRange range, IEnumerable<object> data, RangeWriteMode writeMode, int insertRowPosition)` | `void` | Writes an array row to a range. |
| `WriteColumn(IWorkbook workbook, IRange range, DataColumn data, RangeWriteMode writeMode, int overwriteColumnIndex)` | `void` | Writes a DataColumn to a range. |
| `WriteColumn(IWorkbook workbook, IRange range, IEnumerable<object> data, RangeWriteMode writeMode, int overwriteColumnIndex)` | `void` | Writes an array column to a range. |
| `DeleteRange(IWorkbook workbook, IRange range, RangeDeleteMode deleteMode)` | `void` | Deletes a range from a workbook. |
| `DeleteRows(IWorkbook workbook, IRange range, string rows, RowsDeleteMode deleteMode)` | `void` | Deletes rows by index string (e.g., `"0, 2, 5-7"`). |
| `DeleteRows(IWorkbook workbook, IRange range, IEnumerable<int> rowIndices, RowsDeleteMode deleteMode)` | `void` | Deletes rows by index list. |
| `DeleteColumn(IWorkbook workbook, IRange range, string columnName, bool hasHeaders, ColumnDeleteMode deleteMode)` | `void` | Deletes a column by name. |
| `DeleteColumn(IWorkbook workbook, IRange range, int columnIndex, bool hasHeaders, ColumnDeleteMode deleteMode)` | `void` | Deletes a column by index (0-based). |

### Excel Enums

#### `CellReadMode`

| Value | Description |
|-------|-------------|
| `Values` | Reads the calculated cell values (default). |
| `Formulas` | Reads cell formulas. |

#### `RangeWriteMode`

| Value | Description |
|-------|-------------|
| `Overwrite` | Overwrites data starting at the range origin. |
| `Append` | Appends a new row below the last row (default for WriteRow). |
| `AppendRight` | Appends a new column to the right (default for WriteColumn). |
| `Insert` | Inserts a row at the specified position. |
| `InsertRight` | Inserts a column at the specified position. |

#### `RangeDeleteMode`

| Value | Description |
|-------|-------------|
| `Rows` | Deletes rows and shifts remaining rows up (default). |
| `Columns` | Deletes columns and shifts remaining columns left. |

#### `RowsDeleteMode`

| Value | Description |
|-------|-------------|
| `Delete` | Deletes rows and shifts cells up. |
| `Clear` | Clears cell content without removing the row. |

#### `ColumnDeleteMode`

| Value | Description |
|-------|-------------|
| `Delete` | Deletes the column and shifts remaining columns left. |
| `Clear` | Clears the column content without removing it. |

---

## Mail Enums and Filter Types

### `OrderBy` (email ordering)

| Value | Description |
|-------|-------------|
| `NewestFirst` | Most recent emails first (default). |
| `OldestFirst` | Oldest emails first. |

### `MailImportance`

| Value | Description |
|-------|-------------|
| `Low` | Low importance. |
| `Normal` | Normal importance. |
| `High` | High importance. |

### `MailFilter` (email filter criteria)

Build filters using the `MailFilter` builder. Supports filtering by:
- `From`, `To`, `Cc`, `Bcc`, `Subject`, `Body` — string fields
- `Date` — date range fields
- `Categories` — collection field
- `Attachment` — bool field
- `Type` — `MailType` enum (`Email`, `Meeting`, `Task`, etc.)

---

## Common Patterns

### Send an Email with Attachments

```csharp
[Workflow]
public void Execute()
{
    var mail = office365.Mail(new MailConnection("MyConnection"));

    var request = new SendEmailRequest
    {
        To = "recipient@example.com",
        Subject = "Monthly Report",
        Body = "<p>Please find the report attached.</p>",
        IsBodyHtml = true,
        Attachments = new[] { "C:\\Reports\\monthly.xlsx" }
    };
    mail.SendEmail(request);
}
```

### Read and Process Emails with Filter

```csharp
[Workflow]
public void Execute()
{
    var mail = office365.Mail(new MailConnection("MyConnection"));

    var filter = new MailFilter()
        .Where(MailFilterField.From, FilterStringOperator.Contains, "boss@company.com")
        .And()
        .Where(MailFilterField.Subject, FilterStringOperator.StartsWith, "Urgent");

    var emails = mail.GetEmails(
        folder: mail.SystemFolders.Inbox,
        filter: filter,
        orderBy: OrderBy.NewestFirst,
        maxResults: 10,
        markAsRead: true
    );

    foreach (var email in emails)
    {
        Log(email.Subject);
    }
}
```

### Upload and Share a File on OneDrive

```csharp
[Workflow]
public void Execute()
{
    var oneDrive = office365.OneDrive(new OneDriveConnection("MyOneDriveConnection"));

    var uploadFolder = oneDrive.GetFolder("https://mycompany-my.sharepoint.com/personal/user_company_com/Documents/Shared");
    var uploaded = oneDrive.UploadFile("C:\\Reports\\report.pdf", uploadFolder, ConflictBehavior.Replace);

    var shareLink = oneDrive.ShareFile(uploaded, GranteePermission.View);
    Log($"File shared: {shareLink}");
}
```

### Create and Update a Calendar Event

```csharp
[Workflow]
public void Execute()
{
    var calendar = office365.Calendar(new MailConnection("MyCalendarConnection"));

    var defaultCalendar = calendar.GetDefaultCalendar();
    var request = new CreateEventRequest
    {
        Subject = "Team Sync",
        Start = DateTime.Now.AddHours(2),
        End = DateTime.Now.AddHours(3),
        Attendees = new[] { "colleague@company.com" },
        Body = "Weekly sync meeting"
    };

    var createdEvent = calendar.CreateEvent(defaultCalendar, request);

    // Update the event
    var changes = new UpdateEventRequest { Subject = "Team Sync (Updated)" };
    calendar.UpdateEvent(createdEvent, changes);
}
```

### Read Excel Data and Process

```csharp
[Workflow]
public void Execute()
{
    var excel = office365.Excel(new ExcelConnection("MyExcelConnection"));

    var workbooks = excel.GetWorkbooks(search: "Sales2024");
    var workbook = workbooks.First();

    var sheets = excel.GetSheets(workbook);
    var sheet = sheets.First(s => s.Name == "Q1");

    var data = excel.ReadRange(workbook, sheet, hasHeaders: true, cellReadMode: CellReadMode.Values);
    Log($"Read {data.Rows.Count} rows from Q1 sheet");

    // Write back a summary
    var summarySheet = excel.AddSheet(workbook, "Summary");
    excel.WriteCell(workbook, summarySheet, "A1", $"Total rows: {data.Rows.Count}");
}
```

### Work with SharePoint Lists

```csharp
[Workflow]
public void Execute()
{
    var sp = office365.Sharepoint(new OneDriveConnection("MySharePointConnection"));

    var list = sp.GetList(
        siteIdentifier: "https://mycompany.sharepoint.com/sites/Projects",
        listIdentifier: "Tasks",
        useDisplayNamesAsColumnNames: true
    );

    // Get all items
    var items = sp.GetItems(list);
    Log($"Found {items.Rows.Count} tasks");

    // Add a new item
    var newItem = sp.CreateItem(list);
    newItem["Title"] = "New Task";
    newItem["Status"] = "In Progress";
    sp.AddItem(list, newItem);
}
```
