# Microsoft 365 API Reference

Complete API reference for the `office365` service from `UiPath.MicrosoftOffice365.Activities` package.

**Required package:** `"UiPath.MicrosoftOffice365.Activities": "[3.6.10]"`

**Auto-imported namespaces:** `UiPath.MicrosoftOffice365.Activities.Api`

---

## IOffice365ConnectionsService

The root service accessor. Access via `office365` in coded workflows.

```csharp
public interface IOffice365ConnectionsService
{
    IMailService Mail(MailConnection connection);
    ICalendarService Calendar(MailConnection connection);
    IExcelService Excel(ExcelConnection connection);
    IOneDriveService OneDrive(OneDriveConnection connection);
    ISharepointService Sharepoint(OneDriveConnection connection);
}
```

---

## IMailService

Access: `office365.Mail(mailConnection)`

### Properties

| Name | Type | Description |
|------|------|-------------|
| `SystemFolders` | `MailSystemFolders` | Well-known folders: `Inbox`, `Sent`, `Drafts`, `DeletedItems`, `Archive`, `Spam`, `AllMail` |

### Methods

#### Send

```csharp
void SendEmail(string to, string subject, string body,
    string cc = null, string bcc = null, bool asDraft = false)

void SendEmail(SendEmailRequest sendEmailRequest)
```

#### Get Emails

```csharp
IReadOnlyCollection<IMail> GetEmails(
    IMailFolder folder = null,           // null = Inbox
    MailFilter filter = default,
    string account = null,               // shared mailbox
    OrderBy orderBy = OrderBy.NewestFirst,
    bool includeSubfolders = true,
    bool markAsRead = false,
    bool bodyAsHtml = false,
    int? maxResults = null)              // null = all

IMail GetNewestEmail(
    IMailFolder folder = null,
    MailFilter filter = default,
    string account = null,
    bool markAsRead = false,
    bool bodyAsHtml = false)

IMail GetEmail(string emailId, string account = null, bool bodyAsHtml = false)
```

> **Note:** `maxResults` is `int?` (nullable). Pass `null` to get all emails, or a specific number to limit results.

#### Folders

```csharp
IReadOnlyCollection<IMailFolder> GetMailFolders(string account = null)
```

#### Forward / Reply

```csharp
void ForwardEmail(IMail mail, string body,
    string newSubject = null, string to = null,
    string cc = null, string bcc = null, bool asDraft = false)
void ForwardEmail(IMail mail, ForwardEmailRequest forwardEmailRequest)

void ReplyToEmail(IMail mail, string body,
    string newSubject = null, string to = null,
    string cc = null, string bcc = null, bool asDraft = false)
void ReplyToEmail(IMail mail, ReplyToEmailRequest replyToEmailRequest)
```

#### Actions

```csharp
void DeleteEmail(IMail mail, bool deletePermanently = false)
void ArchiveEmail(IMail mail)
void MoveEmail(IMail mail, IMailFolder destination,
    string mailbox = null, bool bodyAsHtml = false)
void MarkEmailAsRead(IMail mail)
void MarkEmailAsUnread(IMail mail)
```

#### Categories

```csharp
void AddEmailCategories(IMail mail, IReadOnlyList<string> categories)
void RemoveEmailCategories(IMail mail, IReadOnlyList<string> categories)
```

#### Attachments

```csharp
IReadOnlyCollection<IMailAttachmentInfo> GetEmailAttachmentsInfo(IMail mail)
IReadOnlyDictionary<IMailAttachmentInfo, Stream> DownloadEmailAttachments(IMail mail)
Stream DownloadEmailAttachment(IMailAttachmentInfo info)
Stream DownloadEmail(IMail mail, bool bodyAsHtml = false)
```

#### Automatic Replies

```csharp
void TurnOnAutomaticReplies(string internalMessage, string externalMessage,
    DateTimeOffset startTime, DateTimeOffset endTime,
    bool sendRepliesOutsideOrganization = false,
    bool sendRepliesToContactsOnly = false)
void TurnOffAutomaticReplies()
```

---

## ICalendarService

Access: `office365.Calendar(mailConnection)`

### Methods

```csharp
// Calendars
IReadOnlyCollection<ICalendar> GetCalendars()
ICalendar GetDefaultCalendar()

// Events
ICalendarEvent CreateEvent(ICalendar calendar, CreateEventRequest request)

IReadOnlyCollection<ICalendarEvent> GetEvents(
    DateTime startDate, DateTime endDate,
    ICalendar calendar = null,      // null = default calendar
    int top = 50,                   // max events to return
    string timeZone = "",
    string search = "")

ICalendarEvent UpdateEvent(ICalendarEvent calendarEvent, UpdateEventRequest changes)

void DeleteEvent(ICalendarEvent calendarEvent,
    string comment = "",
    DeleteEventMode deleteMode = DeleteEventMode.SingleEvent)

void ForwardEvent(ICalendarEvent calendarEvent,
    IEnumerable<string> attendees,
    string comment = "", bool forwardSeries = false)

void RespondToEvent(ICalendarEvent calendarEvent, RsvpRequest request)
```

---

## IExcelService (Cloud Excel)

Access: `office365.Excel(excelConnection)`

> **Note:** This is O365 cloud Excel (SharePoint/OneDrive workbooks), NOT desktop Excel. For desktop Excel, use the `excel` service from `UiPath.Excel.Activities`.

### Methods

```csharp
// Workbooks
IReadOnlyCollection<IWorkbook> GetWorkbooks(
    IDriveItem parentFolder = null, string search = "", int maxResults = 200)

IWorkbook AddWorkbook(string workbookName,
    IDriveItem parentFolder = null,
    string firstSheetName = "Sheet1",          // ExcelExtensions.DefaultSheetName
    ConflictBehavior conflictResolution = ConflictBehavior.Fail)

// Sheets
IReadOnlyCollection<IWorksheet> GetSheets(IWorkbook workbook)
IWorksheet AddSheet(IWorkbook workbook,
    string sheetName = null,
    ConflictBehavior conflictResolution = ConflictBehavior.Fail)
void DeleteSheet(IWorkbook workbook, string sheetName)
void RenameSheet(IWorkbook workbook, string replacedSheetName, string newSheetName)

// Ranges
IReadOnlyCollection<IRange> GetRanges(IWorkbook workbook)
IReadOnlyCollection<INamedRange> GetNamedRanges(IWorkbook workbook)

// Read
object ReadCell(IWorkbook workbook, IRange range, string cell,
    CellReadMode cellReadMode = CellReadMode.Values)
DataTable ReadRange(IWorkbook workbook, IRange range,
    bool hasHeaders = true,
    CellReadMode cellReadMode = CellReadMode.Values)

// Write
void WriteCell(IWorkbook workbook, IRange range, string cell, object value)
void WriteRange(IWorkbook workbook, IRange range, DataTable data,
    bool hasHeaders = true,
    RangeWriteMode writeMode = RangeWriteMode.Overwrite,
    int insertRowPosition = 0)
void WriteRow(IWorkbook workbook, IRange range, DataRow data,
    RangeWriteMode writeMode = RangeWriteMode.Append, int insertRowPosition = 0)
void WriteRow(IWorkbook workbook, IRange range, IEnumerable<object> data,
    RangeWriteMode writeMode = RangeWriteMode.Append, int insertRowPosition = 0)
void WriteColumn(IWorkbook workbook, IRange range, DataColumn data,
    RangeWriteMode writeMode = RangeWriteMode.AppendRight, int overwriteColumnIndex = 0)
void WriteColumn(IWorkbook workbook, IRange range, IEnumerable<object> data,
    RangeWriteMode writeMode = RangeWriteMode.AppendRight, int overwriteColumnIndex = 0)

// Delete
void DeleteRange(IWorkbook workbook, IRange range,
    RangeDeleteMode deleteMode = RangeDeleteMode.Rows)
void DeleteRows(IWorkbook workbook, IRange range, string rows,
    RowsDeleteMode deleteMode = RowsDeleteMode.Delete)
void DeleteRows(IWorkbook workbook, IRange range, IEnumerable<int> rowIndices,
    RowsDeleteMode deleteMode = RowsDeleteMode.Delete)
void DeleteColumn(IWorkbook workbook, IRange range, string columnName,
    bool hasHeaders = true, ColumnDeleteMode deleteMode = ColumnDeleteMode.Delete)
void DeleteColumn(IWorkbook workbook, IRange range, int columnIndex,
    bool hasHeaders = true, ColumnDeleteMode deleteMode = ColumnDeleteMode.Delete)
```

---

## IOneDriveService

Access: `office365.OneDrive(oneDriveConnection)`

### Methods

```csharp
// Get items
IFile GetFile(string url)
IFile GetFile(string id, string siteUrl, string libraryName)
IFile GetFile(IFolder parent, string relativePath)
IFolder GetFolder(string url = null)       // null = root
IFolder GetFolder(string id, string siteUrl, string libraryName)
IFolder GetFolder(IFolder parent, string relativePath)
IDriveItem GetItem(string url)
IDriveItem GetItem(string id, string siteUrl, string libraryName)
IDriveItem GetItem(IFolder parent, string relativePath)

// List items (simple — no filter)
IReadOnlyCollection<IFile> GetFiles(
    IFolder parent = null, bool trimDuplicates = false,
    string simpleSearchQuery = null, int maxResults = 200)
IReadOnlyCollection<IFolder> GetFolders(
    IFolder parent = null, bool trimDuplicates = false,
    string simpleSearchQuery = null, int maxResults = 200)
IReadOnlyCollection<IDriveItem> GetFilesAndFolders(
    IFolder parent = null, bool trimDuplicates = false,
    string simpleSearchQuery = null, int maxResults = 200)

// List items (with filter)
IReadOnlyCollection<IFile> GetFiles(DriveItemFilter filter,
    IFolder parent = null, bool trimDuplicates = false,
    bool includeSubfolders = false, int maxResults = 200)
IReadOnlyCollection<IFolder> GetFolders(DriveItemFilter filter,
    IFolder parent = null, bool trimDuplicates = false,
    bool includeSubfolders = false, int maxResults = 200)
IReadOnlyCollection<IDriveItem> GetFilesAndFolders(DriveItemFilter filter,
    IFolder parent = null, bool trimDuplicates = false,
    bool includeSubfolders = false, int maxResults = 200)

// Create / Upload
IFolder CreateFolder(string name, IFolder parent = null,
    ConflictBehavior conflictBehavior = ConflictBehavior.Fail)
IFile UploadFile(string path, IFolder destination = null,
    ConflictBehavior conflictBehavior = ConflictBehavior.Replace,
    DataTable metadata = null)
IFile UploadFile(Stream stream, string fileName, IFolder destination = null,
    ConflictBehavior conflictBehavior = ConflictBehavior.Replace,
    DataTable metadata = null)
IFile UploadFile(IResource file, IFolder destination = null,
    ConflictBehavior conflictBehavior = ConflictBehavior.Replace,
    DataTable metadata = null)
IReadOnlyCollection<IFile> UploadFiles(IEnumerable<string> paths,
    IFolder destination = null,
    ConflictBehavior conflictBehavior = ConflictBehavior.Replace,
    DataTable metadata = null)
IReadOnlyCollection<IFile> UploadFiles(IEnumerable<IResource> files,
    IFolder destination = null,
    ConflictBehavior conflictBehavior = ConflictBehavior.Replace,
    DataTable metadata = null)

// Download
Stream DownloadFile(IFile file, bool convertToPdf = false)

// Copy / Move / Delete
IFile CopyFile(IFile file, IFolder destination = null, string newName = null,
    ConflictBehavior conflictBehavior = ConflictBehavior.Fail)
IFile MoveFile(IFile file, IFolder destination = null, string newName = null,
    ConflictBehavior conflictBehavior = ConflictBehavior.Fail)
IFolder CopyFolder(IFolder folder, IFolder destination = null, string newName = null,
    ConflictBehavior conflictBehavior = ConflictBehavior.Fail)
IFolder MoveFolder(IFolder folder, IFolder destination = null, string newName = null,
    ConflictBehavior conflictBehavior = ConflictBehavior.Fail)
void DeleteItem(IDriveItem item)
void DeleteItem(string itemUrl)
void DeleteItem(string itemId, string siteUrl, string documentLibraryName)

// Share (anonymous link)
string ShareFile(IFile file, GranteePermission permission = GranteePermission.View)
string ShareFolder(IFolder folder, GranteePermission permission = GranteePermission.View)

// Share (specific recipients)
string ShareFile(IFile file, IEnumerable<string> recipients,
    string message = null, bool sendSharingInvitationEmail = true,
    bool requiresSignIn = false, GranteePermission permission = GranteePermission.View)
string ShareFolder(IFolder folder, IEnumerable<string> recipients,
    string message = null, bool sendSharingInvitationEmail = true,
    GranteePermission permission = GranteePermission.View)

// Share (password-protected link)
string ShareFile(IFile file, string passwordForSharingLink = null,
    DateTime? expirationDate = null, GranteePermission permission = GranteePermission.View)
string ShareFolder(IFolder folder, string passwordForSharingLink = null,
    DateTime? expirationDate = null, GranteePermission permission = GranteePermission.View)

// Refresh
IFile RefreshFile(IFile file)
IFolder RefreshFolder(IFolder folder)
IDriveItem RefreshItem(IDriveItem item)
```

---

## ISharepointService

Access: `office365.Sharepoint(oneDriveConnection)`

### Methods

```csharp
ISharepointList GetList(string siteIdentifier, string listIdentifier,
    bool useDisplayNamesAsColumnNames = false)

DataRow CreateItem(ISharepointList list)
DataRow AddItem(ISharepointList list, DataRow row)
DataRow UpdateItem(ISharepointList list, DataRow row)
DataTable GetItems(ISharepointList list,
    IEnumerable<string> columns = null, SharepointItemFilter filter = null)
DataTable DeleteItems(ISharepointList list,
    IEnumerable<string> columns = null, SharepointItemFilter filter = null)
```

---

## Request Builder Classes

All request builders use a **fluent builder pattern** — chain `.With*()` methods.

### BasicEmailRequestBuilder\<T> (Base Class)

All email request builders inherit from this. Shared methods:

```csharp
T WithTo(string to)
T WithCc(string cc)
T WithBcc(string bcc)
T WithBody(string body, bool isHtml = false)
T WithHtmlBody(bool isBodyHtml = true)
T WithAttachment(string filePath)
T WithAttachment(IResource attachment)
T AsDraft(bool asDraft = true)
T WithAccount(string account)          // send from shared mailbox
```

### SendEmailRequest

Extends `BasicEmailRequestBuilder<SendEmailRequest>`. Additional methods:

```csharp
new SendEmailRequest()
    .WithTo("recipient@example.com")
    .WithCc("cc@example.com")
    .WithBcc("bcc@example.com")
    .WithSubject("Subject")
    .WithBody("HTML body", isHtml: true)
    .WithAttachment("C:\\path\\file.pdf")
    .WithImportance(MailImportance.High)
    .WithReplyTo("noreply@example.com")
    .AsDraft(false)
    .WithAccount("shared@company.com")
```

Additional methods on `SendEmailRequest`:
- `WithSubject(string subject)`
- `WithImportance(MailImportance importance)`
- `WithReplyTo(string replyTo)`

### ForwardEmailRequest

Extends `BasicEmailRequestBuilder<ForwardEmailRequest>`. Additional methods:

```csharp
new ForwardEmailRequest()
    .WithTo("forward-to@example.com")
    .WithBody("Forwarding this for your review.")
    .WithNewSubject("FW: Original Subject")
    .WithAttachment("C:\\extra-doc.pdf")
```

Additional method: `WithNewSubject(string newSubject)`

### ReplyToEmailRequest

Extends `BasicEmailRequestBuilder<ReplyToEmailRequest>`. Additional methods:

```csharp
new ReplyToEmailRequest()
    .WithBody("Thank you for the update.")
    .WithReplyToAll(true)
    .WithImportance(MailImportance.Normal)
    .WithNewSubject("RE: Updated Subject")
```

Additional methods:
- `WithNewSubject(string newSubject)`
- `WithReplyToAll(bool replyToAll)`
- `WithImportance(MailImportance importance)`

### BaseEventRequest\<T> (Base Class for Calendar Events)

All calendar event request builders inherit from this. Shared methods:

```csharp
T WithTitle(string title)
T WithStartDate(DateTime startDate)
T WithEndDate(DateTime endDate)
T WithTimezone(string timezone)
T WithPreferredReturnTimezone(string timezone)
T AllDayEvent(bool isAllDayEvent)
T WithDescription(string description, bool isHtml = false)
T AddRequiredAttendees(params string[] attendeeEmails)
T AddRequiredAttendees(IEnumerable<string> attendeeEmails)
T AddOptionalAttendees(params string[] attendeeEmails)
T AddOptionalAttendees(IEnumerable<string> attendeeEmails)
T AddResourceAttendees(params string[] attendeeEmails)
T AddResourceAttendees(IEnumerable<string> attendeeEmails)
T WithImportance(Importance importance)
T WithSensitivity(Sensitivity sensitivity)
T ShowAs(FreeBusyStatus transparency)
```

### CreateEventRequest

Extends `BaseEventRequest<CreateEventRequest>`. Default timezone: `"UTC"`.

```csharp
new CreateEventRequest()
    .WithTitle("Team Meeting")
    .WithStartDate(DateTime.Now.AddDays(1))
    .WithEndDate(DateTime.Now.AddDays(1).AddHours(1))
    .WithTimezone("Eastern Standard Time")
    .WithDescription("<p>Agenda items...</p>", isHtml: true)
    .AddRequiredAttendees("alice@company.com", "bob@company.com")
    .AddOptionalAttendees("charlie@company.com")
    .WithImportance(Importance.Normal)
    .ShowAs(FreeBusyStatus.Busy)
```

Additional methods:
- `WithAttachment(Stream attachment, string fileName)`
- `WithAttachment(IResource attachment)`

### UpdateEventRequest

Extends `BaseEventRequest<UpdateEventRequest>`. **Constructor requires `ICalendarEvent`:**

```csharp
new UpdateEventRequest(existingEvent)
    .WithTitle("Updated Meeting Title")
    .WithStartDate(newStartTime)
    .AddRequiredAttendees("dave@company.com")
    .RemoveOptionalAttendees("charlie@company.com")
```

> **Important:** `UpdateEventRequest` requires an `ICalendarEvent` in its constructor: `new UpdateEventRequest(calendarEvent)`.

Additional methods beyond base:
- `ClearRequiredAttendees()` / `OverwriteRequiredAttendees(...)` / `RemoveRequiredAttendees(...)`
- `ClearOptionalAttendees()` / `OverwriteOptionalAttendees(...)` / `RemoveOptionalAttendees(...)`
- `ClearResourceAttendees()` / `OverwriteResourceAttendees(...)` / `RemoveResourceAttendees(...)`
- `AddAttachment(Stream attachment, string fileName)` / `AddAttachment(IResource attachment)`
- `RemoveAttachment(IResource attachment)`
- `OverwriteAttachments(params IResource[] attachments)` / `OverwriteAttachments(IEnumerable<IResource> attachments)`

### RsvpRequest

Plain class with properties (not a builder):

```csharp
new RsvpRequest
{
    Response = EventResponseType.Accept,       // required
    Comment = "I'll be there!",
    SendResponseNotification = false,          // default: false
    AllOccurrences = false,                    // default: false
    NewStart = newStartDateTime,               // for proposing new time
    NewEnd = newEndDateTime,
    NewTimezone = "Eastern Standard Time"
}
```

---

## Filter Classes

### MailFilter

Fluent filter builder for email queries. Implements `IFilterExpressionBuilder<MailFilter>`.

> **Important:** Mail string operators only support `Contains` and `NotContains`. Other `FilterStringOperator` values will throw `ArgumentException`.

```csharp
// Convenience methods
MailFilter ByFrom(FilterStringOperator stringOperator, string value)
MailFilter ByTo(FilterStringOperator stringOperator, string value)
MailFilter ByCc(FilterStringOperator stringOperator, string value)
MailFilter ByBcc(FilterStringOperator stringOperator, string value)
MailFilter BySubject(FilterStringOperator stringOperator, string value)
MailFilter ByBody(FilterStringOperator stringOperator, string value)
MailFilter ByCategories(FilterStringOperator stringOperator, string value)
MailFilter ByRecipients(FilterStringOperator stringOperator, string value)
MailFilter ByAttachment(FilterStringOperator stringOperator, string value)

// Date filter
MailFilter ByDate(FilterDateOperator dateOperator, DateTime value)

// Boolean filters
MailFilter ByUnread(bool value)
MailFilter WithAttachments(bool value)

// Type filter
MailFilter ByType(MailType value)
MailFilter ByType(FilterMailTypeOperator typeOperator, MailType value)

// Importance filter
MailFilter ByImportance(MailImportanceFilter value)

// Generic methods
MailFilter By(MailFilterField field, FilterStringOperator stringOperator, string value)
MailFilter By(MailFilterField field, FilterDateOperator dateOperator, DateTime value)
MailFilter By(MailFilterField field, FilterMailTypeOperator typeOperator, MailType value)

// Logical operators and sub-expressions
MailFilter And()
MailFilter Or()
MailFilter BySubExpression(MailFilter expressionBuilder)
MailFilter ByExpression(string expression)    // raw OData expression
```

Example:
```csharp
var filter = new MailFilter()
    .BySubject(FilterStringOperator.Contains, "Invoice")
    .And()
    .ByFrom(FilterStringOperator.Contains, "accounting")
    .And()
    .ByDate(FilterDateOperator.NewerThan, DateTime.Now.AddDays(-7));
```

### DriveItemFilter

Fluent filter builder for OneDrive file/folder queries.

> **Note:** String operators for drive items support `Contains`, `NotContains`, `Equals`. File extension supports `Equals`, `NotEquals` only.

```csharp
// Convenience methods
DriveItemFilter ByFileName(FilterStringOperator stringOperator, string value)
DriveItemFilter ByFileExtension(FilterStringOperator stringOperator, string value)
DriveItemFilter ByCreatedBy(FilterStringOperator stringOperator, string value)
DriveItemFilter ByLastModifiedBy(FilterStringOperator stringOperator, string value)
DriveItemFilter BySharedWithUser(FilterStringOperator stringOperator, string value)
DriveItemFilter ByCreationDate(FilterDateOperator dateOperator, DateTime value)
DriveItemFilter ByLastModifiedDate(FilterDateOperator dateOperator, DateTime value)
DriveItemFilter BySize(FilterIntOperator intOperator, int value)

// Generic methods
DriveItemFilter By(DriveItemFilterField field, FilterStringOperator stringOperator, string value)
DriveItemFilter By(DriveItemFilterField field, FilterDateOperator dateOperator, DateTime value)
DriveItemFilter By(DriveItemFilterField field, FilterIntOperator intOperator, int value)

// Logical operators and sub-expressions
DriveItemFilter And()
DriveItemFilter Or()
DriveItemFilter BySubExpression(DriveItemFilter expressionBuilder)
DriveItemFilter ByExpression(string expression)
```

### SharepointItemFilter

Fluent filter builder for SharePoint list items. Created via `list.CreateFilter()`.

> **Note:** SharePoint string operators only support `Equals` and `NotEquals`.

```csharp
SharepointItemFilter By(string field, FilterStringOperator stringOperator, string value)
SharepointItemFilter By(string field, FilterDateOperator dateOperator, DateTime value)
SharepointItemFilter By(string field, FilterIntOperator intOperator, int value)
SharepointItemFilter By(string field, FilterBoolOperator boolOperator, bool value)

// Logical operators and sub-expressions
SharepointItemFilter And()
SharepointItemFilter Or()
SharepointItemFilter BySubExpression(SharepointItemFilter expressionBuilder)
SharepointItemFilter ByExpression(string expression)
```

Example:
```csharp
var filter = list.CreateFilter()
    .By("Status", FilterStringOperator.Equals, "Active")
    .And()
    .By("Priority", FilterIntOperator.GreaterThan, 3);
```

---

## Enums

### Mail Enums

| Enum | Values |
|------|--------|
| `OrderBy` | `NewestFirst`, `OldestFirst` |
| `MailImportance` | `Low`, `Normal`, `High` |
| `MailType` | `Email`, `Im`, `Meeting`, `Voicemail`, `RssFeed`, `Task` |
| `FilterMailTypeOperator` | `Equals` |
| `MailImportanceFilter` | `Low`, `Normal`, `High`, `NotLow`, `NotNormal`, `NotHigh` |
| `MailFilterField` | `From`, `To`, `Date`, `Cc`, `Bcc`, `Subject`, `Body`, `Categories`, `Recipients`, `Attachment`, `Type` |

### Calendar Enums

| Enum | Values |
|------|--------|
| `Importance` | `Low`, `Normal`, `High` |
| `Sensitivity` | `Normal`, `Personal`, `Private`, `Confidential` |
| `FreeBusyStatus` | `Free`, `Tentative`, `Busy`, `Oof`, `WorkingElsewhere`, `Unknown` |
| `EventResponseType` | `Accept`, `TentativelyAccept`, `Decline` |
| `DeleteEventMode` | `SingleEvent`, `FutureOnly`, `PastAndFuture` |

### Excel Enums

| Enum | Values |
|------|--------|
| `CellReadMode` | `Values`, `Formulas`, `Text` |
| `RangeWriteMode` | `Overwrite`, `Append`, `AppendRight`, `Insert`, `InsertRight` |
| `RangeDeleteMode` | `None` (clear), `Rows`, `Columns` |
| `RowsDeleteMode` | `Clear`, `Delete` |
| `ColumnDeleteMode` | `Clear`, `Delete` |
| `RangeType` | `Sheet`, `NamedRange`, `GlobalNamedRange`, `Any` |
| `ConflictBehavior` | `Replace`, `Fail`, `Rename` |

### OneDrive Enums

| Enum | Values |
|------|--------|
| `ConflictBehavior` | `Replace`, `Fail`, `Rename` |
| `GranteePermission` | `View`, `Edit` |

### Filter Enums (Shared)

| Enum | Values |
|------|--------|
| `FilterStringOperator` | `Contains`, `NotContains`, `Equals`, `NotEquals`, `StartsWith`, `EndsWith`, `IsEmpty`, `IsNotEmpty` |
| `FilterDateOperator` | `NewerThan`, `OlderThan` |
| `FilterIntOperator` | `Equals`, `NotEqual`, `GreaterThan`, `GreaterThanOrEqual`, `LessThanOrEqual`, `LessThan` |
| `FilterBoolOperator` | `NotEqual`, `Equals` |
| `FilterCollectionOperator` | `In`, `NotIn`, `AllIn`, `NotAllIn`, `IsEmpty`, `IsNotEmpty` |
| `DriveItemFilterField` | `FileExtension`, `FileName`, `CreatedBy`, `CreationDate`, `LastModifiedBy`, `LastModifiedDate`, `SharedWithUser`, `Size` |

> **Important — Supported operators per filter class:**
> - **MailFilter** string operators: only `Contains`, `NotContains`
> - **DriveItemFilter** string operators: `Contains`, `NotContains`, `Equals` (file extension: `Equals`, `NotEquals` only)
> - **SharepointItemFilter** string operators: only `Equals`, `NotEquals`

---

## Key Interfaces (Return Types)

### IMail
Properties: `Id`, `Subject`, `Body`, `Account`, `Item` (Office365Message)
Methods: `Delete(bool deletePermanently = false)`, `Archive()`, `Forward(...)`, `Reply(...)`, `MoveTo(IMailFolder destination, ...)`, `MarkAsRead()`, `MarkAsUnread()`, `GetAttachmentsInfo()`, `DownloadAttachments()`, `Download(bool bodyAsHtml = false)`, `AddEmailCategories(...)`, `RemoveEmailCategories(...)`

### IMailFolder
Properties: `Id`, `Name`
Methods: `GetEmails(...)`, `GetNewestEmail(...)`

### IMailAttachmentInfo
Properties: `Name`, `Id`
Methods: `Download()` → `Stream`

### ICalendar
Properties: `Id`, `IsDefault`, `Item` (O365CalendarItem)
Methods: `CreateEvent(...)`, `GetEvents(...)`, `UpdateEvent(...)`, `DeleteEvent(...)`, `ForwardEvent(...)`, `RespondToEvent(...)`

### ICalendarEvent
Properties: `Id`, `Calendar` (ICalendar), `Item` (O365EventItem with Subject, StartDateTime, EndDateTime, Location, Attendees, etc.)
Methods: `Update(...)`, `Delete(...)`, `Forward(...)`, `Respond(...)`

### IDriveItem
Properties: `Id`, `Name`, `FullName`, `IsFolder`, `Item` (O365DriveRemoteItem)
Methods: `Copy(...)`, `Move(...)`, `Delete()`, `Share(...)`, `Refresh()`

### IFile (extends IDriveItem)
Methods: `Copy(...)` → IFile, `Move(...)` → IFile, `Download(bool convertToPdf = false)`, `Upload(...)`

### IFolder (extends IDriveItem)
Methods: `Copy(...)` → IFolder, `Move(...)` → IFolder, `CreateFolder(...)`, `GetFile(...)`, `GetFiles(...)`, `GetFolders(...)`, `GetFilesAndFolders(...)`, `GetItem(...)`

### IWorkbook
Properties: `Id`, `Name`, `Item` (O365DriveRemoteItem)
Methods: `GetSheets()`, `AddSheet(...)`, `DeleteSheet(...)`, `RenameSheet(...)`, `GetRanges()`, `GetNamedRanges()`

### IWorksheet (extends IRange)
Properties: `Name`, `Type` (RangeType.Sheet)
Methods: `ReadCell(...)`, `WriteCell(...)`, `Delete()`, `Rename(...)`, plus all IRange methods

### IRange
Properties: `Name`, `Type` (RangeType)
Methods: `ReadRange(...)`, `WriteRange(...)`, `WriteRow(...)`, `WriteColumn(...)`, `DeleteRange(...)`, `DeleteRows(...)`, `DeleteColumn(...)`

### INamedRange (extends IRange)
No additional members.

### IGlobalNamedRange (extends IRange)
No additional members.

### ISharepointList
Properties: `Id`, `Name`, `SiteIdentifier`, `UseDisplayNamesAsColumnNames`, `Item` (Office365SharepointList)
Methods: `CreateItem()`, `AddItem(...)`, `UpdateItem(...)`, `GetItems(...)`, `DeleteItems(...)`, `CreateFilter()`

### MailSystemFolders
Properties: `Inbox`, `Sent`, `Drafts`, `DeletedItems`, `Archive`, `Spam`, `AllMail` (all `IMailFolder`)
