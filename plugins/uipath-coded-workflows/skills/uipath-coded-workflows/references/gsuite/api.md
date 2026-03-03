# Google Workspace (GSuite) API Reference

Full API reference for all services available via the `google` accessor (`IGoogleConnectionsService`).

**Namespace:** `UiPath.GSuite.Activities.Api`

---

## IGmailService

Access: `google.Gmail(gmailConnection)`

### Properties

| Name | Type | Description |
|------|------|-------------|
| `SystemFolders` | `MailSystemFolders` | System labels: `Inbox`, `Sent`, `Draft`, `Spam`, `Trash`, `Starred`, `Important`, `Unread`, `AllMail` |

### Methods

#### Send

```csharp
void SendEmail(string to, string subject, string body,
    string cc = null, string bcc = null, bool asDraft = false)

void SendEmail(SendEmailRequest sendEmailOptions)
```

#### Get Emails

```csharp
IReadOnlyCollection<IMail> GetEmails(
    IMailLabel folder = null,     // null = All Mail
    MailFilter filter = null,
    bool markAsRead = false,
    int? maxResults = null)       // null = unlimited

IMail GetNewestEmail(
    IMailLabel folder = null,     // null = All Mail
    MailFilter filter = null,
    bool markAsRead = false)

IMail GetEmail(string emailId)
```

#### Forward / Reply

```csharp
void ForwardEmail(IMail mail, string body,
    string newSubject = null, string to = null,
    string cc = null, string bcc = null, bool asDraft = false)
void ForwardEmail(IMail mail, ForwardEmailRequest forwardOptions)

void ReplyToEmail(IMail mail, string body,
    string newSubject = null, string to = null,
    string cc = null, string bcc = null, bool asDraft = false)
void ReplyToEmail(IMail mail, ReplyToEmailRequest replyOptions)
```

#### Actions

```csharp
void DeleteEmail(IMail mail, bool deletePermanently = false)
void DeleteEmail(string messageId, bool deletePermanently = false)
void ArchiveEmail(IMail mail)
void ArchiveEmail(string messageId)
void MoveEmail(IMail mail, IMailLabel source, IMailLabel destination)
void MarkEmailAsRead(IMail mail)
void MarkEmailAsRead(string messageId)
void MarkEmailAsUnread(IMail mail)
void MarkEmailAsUnread(string messageId)
```

#### Labels (Gmail-specific)

```csharp
IReadOnlyCollection<IMailLabel> GetMailLabels()
void ApplyLabels(IMail mail, IReadOnlyList<IMailLabel> labels)
void RemoveLabels(IMail mail, IReadOnlyList<IMailLabel> labels)
```

#### Attachments

```csharp
IReadOnlyCollection<IMailAttachmentInfo> GetEmailAttachmentsInfo(IMail mail)
IReadOnlyCollection<IMailAttachmentInfo> GetEmailAttachmentsInfo(string messageId)
IReadOnlyDictionary<IMailAttachmentInfo, Stream> DownloadEmailAttachments(IMail mail)
IReadOnlyDictionary<IMailAttachmentInfo, Stream> DownloadEmailAttachments(string messageId)
Stream DownloadEmailAttachment(IMailAttachmentInfo info)
Stream DownloadEmail(IMail mail)
Stream DownloadEmail(string messageId)
```

#### Automatic Replies

```csharp
void TurnOnAutomaticReplies(string subject, string body,
    DateTimeOffset startTime, DateTimeOffset endTime,
    bool sendRepliesOutsideOrganization = false,
    bool sendRepliesToContactsOnly = false)
void TurnOffAutomaticReplies()
```

---

## IGoogleCalendarService

Access: `google.Calendar(gmailConnection)` — note: uses `GmailConnection`

### Methods

```csharp
// Calendars
IReadOnlyCollection<ICalendar> GetCalendars()
ICalendar GetDefaultCalendar()

// Events
ICalendarEvent CreateEvent(ICalendar calendar, CreateCalendarItem eventInformation)
IReadOnlyCollection<ICalendarEvent> GetEvents(
    DateTimeOffset startDate, DateTimeOffset endDate,
    ICalendar calendar = null,   // null = default calendar
    int top = 0,                 // 0 = unlimited
    string timezone = "",
    string search = "")
ICalendarEvent UpdateEvent(ICalendarEvent calendarEvent, UpdateCalendarItem changes)
void DeleteEvent(ICalendarEvent calendarEvent,
    DeleteEventMode deleteMode = DeleteEventMode.SingleEvent)
void ForwardEvent(ICalendarEvent calendarEvent,
    IEnumerable<string> attendees, bool forwardSeries = false)
void RespondToEvent(ICalendarEvent calendarEvent, EventResponseType response,
    string comment = "", int? additionalGuests = null,
    bool allOccurrences = false, bool sendResponseNotification = false)
```

---

## IGoogleDriveService

Access: `google.Drive(driveConnection)`

### Methods

```csharp
// Get items (default maxResults = 200)
IFile GetFile(string identifier, IdentificationType type = IdentificationType.UrlOrId)
IFile GetFile(IFolder parent, string relativePath)
IFolder GetFolder(string identifier = null, IdentificationType type = IdentificationType.UrlOrId)
IFolder GetFolder(IFolder parent, string relativePath)
IDriveItem GetItem(string identifier, IdentificationType type = IdentificationType.UrlOrId)
IDriveItem GetItem(IFolder parent, string relativePath)

// List items (default maxResults = 200)
IReadOnlyCollection<IFile> GetFiles(
    IFolder parent = null, DriveItemFilter filter = null, int maxResults = 200)
IReadOnlyCollection<IFolder> GetFolders(
    IFolder parent = null, DriveItemFilter filter = null, int maxResults = 200)
IReadOnlyCollection<IDriveItem> GetFilesAndFolders(
    IFolder parent = null, DriveItemFilter filter = null, int maxResults = 200)

// Create / Upload
IFolder CreateFolder(string name,
    string description = null, IFolder parent = null,
    ConflictBehavior conflictBehavior = ConflictBehavior.AddSeparate)
IFile UploadFile(string path, IFolder destination,
    bool convertToGoogleTypes = false, ConflictBehavior conflictBehavior = ConflictBehavior.AddSeparate,
    bool uploadAsIsIfConvertFails = false)
IFile UploadFile(Stream stream, string fileName, IFolder destination,
    bool convertToGoogleTypes = false, ConflictBehavior conflictBehavior = ConflictBehavior.AddSeparate,
    bool uploadAsIsIfConvertFails = false)
IFile UploadFile(IResource file, IFolder destination,
    bool convertToGoogleTypes = false, ConflictBehavior conflictBehavior = ConflictBehavior.AddSeparate,
    bool uploadAsIsIfConvertFails = false)
IReadOnlyCollection<IFile> UploadFiles(IEnumerable<string> paths, IFolder destination,
    bool convertToGoogleTypes = false, ConflictBehavior conflictBehavior = ConflictBehavior.AddSeparate,
    bool uploadAsIsIfConvertFails = false)
IReadOnlyCollection<IFile> UploadFiles(IEnumerable<IResource> files, IFolder destination,
    bool convertToGoogleTypes = false, ConflictBehavior conflictBehavior = ConflictBehavior.AddSeparate,
    bool uploadAsIsIfConvertFails = false)

// Download (with export format options for Google-native files)
Stream DownloadFile(IFile file, DownloadOptions options = null)

// Copy / Move / Delete
IFile CopyFile(IFile file, IFolder destination, string newName = null,
    ConflictBehavior conflictBehavior = ConflictBehavior.AddSeparate)
IFile MoveFile(IFile file, IFolder destination, string newName = null,
    ConflictBehavior conflictBehavior = ConflictBehavior.AddSeparate)
IFolder MoveFolder(IFolder folder, IFolder destination, string newName = null,
    ConflictBehavior conflictBehavior = ConflictBehavior.AddSeparate)
void DeleteItem(IDriveItem item)
void DeleteItem(string urlOrId)

// Refresh
IDriveItem RefreshItem(IDriveItem item)
IFile RefreshFile(IFile file)
IFolder RefreshFolder(IFolder folder)

// Share (3 overloads each for files and folders)
string ShareFile(IFile file, Role role = Role.Reader, bool useDomainAdminAccess = false)
string ShareFile(IFile file, string domain, Role role = Role.Reader, bool useDomainAdminAccess = false)
string ShareFile(IFile file, GranteeType shareWith, string recipients,
    bool sendNotificationEmail = true, Role role = Role.Reader, bool useDomainAdminAccess = false)
string ShareFolder(IFolder folder, Role role = Role.Reader, bool useDomainAdminAccess = false)
string ShareFolder(IFolder folder, string domain, Role role = Role.Reader, bool useDomainAdminAccess = false)
string ShareFolder(IFolder folder, GranteeType shareWith, string recipients,
    bool sendNotificationEmail = true, Role role = Role.Reader, bool useDomainAdminAccess = false)

// Drive Labels
IReadOnlyCollection<ILabel> GetDriveLabels(DriveLabelType driveLabelType = DriveLabelType.All)
IReadOnlyCollection<ILabel> GetFileLabels(IFile file)
void ApplyFileLabels(IFile file, IEnumerable<ILabel> labels)
void RemoveFileLabels(IFile file, IEnumerable<ILabel> labels)
void ClearFileLabelFields(IFile file, string labelId, IEnumerable<GDriveLabelField> fields)
```

### DownloadOptions

For downloading Google-native files (Docs, Sheets, Slides, Drawings), specify the export format:

```csharp
var options = new DownloadOptions
{
    DocumentExportFormat = GDocExportFormat.Pdf,         // default: Word
    SpreadsheetExportFormat = GSheetExportFormat.Xlsx,   // default: Xlsx
    PresentationExportFormat = GSlideExportFormat.Ppt,   // default: Ppt
    DrawingExportFormat = GDrawingExportFormat.Png       // default: Jpeg
};
```

---

## IGoogleSheetsService

Access: `google.Sheets(sheetsConnection)`

### Methods

```csharp
// Spreadsheets
IReadOnlyCollection<ISpreadsheet> GetSpreadsheets(GDriveRemoteItem parentFolder = null)
ISpreadsheet AddSpreadsheet(GDriveRemoteItem parentFolder, string spreadsheetName,
    string firstSheetName = "Sheet1", ConflictBehavior conflictResolution = ConflictBehavior.Fail)

// Sheets
IReadOnlyCollection<ISheet> GetSheets(ISpreadsheet spreadsheet)
ISheet AddSheet(ISpreadsheet spreadsheet, string sheetName = null, int? positionIndex = null)
void DeleteSheet(ISpreadsheet spreadsheet, string sheetName)
void RenameSheet(ISpreadsheet spreadsheet, string replacedSheetName, string newSheetName)

// Ranges
IReadOnlyCollection<IRange> GetRanges(ISpreadsheet spreadsheet)
IReadOnlyCollection<INamedRange> GetNamedRanges(ISpreadsheet spreadsheet)

// Read
object ReadCell(ISpreadsheet spreadsheet, IRange range, string cell,
    CellReadMode cellReadMode = CellReadMode.Values)
DataTable ReadRange(ISpreadsheet spreadsheet, IRange range,
    bool hasHeaders = true, CellReadMode cellReadMode = CellReadMode.Values)

// Write
void WriteCell(ISpreadsheet spreadsheet, IRange range, string cell, object value)
void WriteRange(ISpreadsheet spreadsheet, IRange range, DataTable data,
    bool hasHeaders = true, RangeWriteMode writeMode = RangeWriteMode.Overwrite,
    int insertRowPosition = 0)
void WriteRow(ISpreadsheet spreadsheet, IRange range, DataRow data,
    bool hasHeaders = true, RangeWriteMode writeMode = RangeWriteMode.Append,
    int insertRowPosition = 0)
void WriteRow(ISpreadsheet spreadsheet, IRange range, IEnumerable<object> data,
    bool hasHeaders = true, RangeWriteMode writeMode = RangeWriteMode.Append,
    int insertRowPosition = 0)
void WriteColumn(ISpreadsheet spreadsheet, IRange range, DataColumn data,
    RangeWriteMode writeMode = RangeWriteMode.AppendRight, int overwriteColumnIndex = 0)
void WriteColumn(ISpreadsheet spreadsheet, IRange range, IEnumerable<object> data,
    RangeWriteMode writeMode = RangeWriteMode.AppendRight, int overwriteColumnIndex = 0)

// Delete
void DeleteRange(ISpreadsheet spreadsheet, IRange range,
    RangeDeleteMode deleteMode = RangeDeleteMode.Rows)
void DeleteRows(ISpreadsheet spreadsheet, IRange range, string rows,
    RowsDeleteMode deleteMode = RowsDeleteMode.Delete)
void DeleteRows(ISpreadsheet spreadsheet, IRange range, IEnumerable<int> rowIndices,
    RowsDeleteMode deleteMode = RowsDeleteMode.Delete)
void DeleteColumn(ISpreadsheet spreadsheet, IRange range, string columnName,
    bool hasHeaders = true, ColumnDeleteMode deleteMode = ColumnDeleteMode.Delete)
void DeleteColumn(ISpreadsheet spreadsheet, IRange range, int columnIndex,
    bool hasHeaders = true, ColumnDeleteMode deleteMode = ColumnDeleteMode.Delete)
```

---

## IGoogleDocsService

Access: `google.Docs(docsConnection)`

### Methods

```csharp
// Documents
IReadOnlyCollection<IDocument> GetDocuments(GDriveRemoteItem parentFolder = null)
IDocument AddDocument(GDriveRemoteItem parentFolder, string documentName,
    ConflictBehavior conflictResolution = ConflictBehavior.Fail)

// Read text
string ReadText(IDocument document,
    string sectionName = null, bool matchCase = false,
    TextMatchMode textMatchMode = TextMatchMode.Contains)

// Write text
void WriteText(IDocument document, string text,
    TextStyle style = TextStyle.NormalText,
    TextLocation location = TextLocation.Beginning,
    string sectionName = null, bool matchCase = false,
    TextMatchMode textMatchMode = TextMatchMode.Contains)

// Find and replace
void FindAndReplaceText(IDocument document, string searchTerm, string replacement,
    bool matchCase = false, TextRecurrences recurrences = TextRecurrences.Once)

// Delete text (by text content)
void DeleteText(IDocument document, string text,
    bool matchCase = false, TextRecurrences recurrences = TextRecurrences.Once)

// Delete text (by section name)
void DeleteText(IDocument document, string sectionName,
    bool matchCase = false, TextMatchMode textMatchMode = TextMatchMode.Contains)

// Template fill (replace placeholders with values)
void FillDocumentTemplate(IDocument document,
    IReadOnlyDictionary<string, string> fields,
    string symbol = "{{ }}")
```

> **Note on `FillDocumentTemplate`:** The `symbol` parameter is a string representing the delimiter pattern (e.g., `"{{ }}"` for `{{fieldName}}`). Common patterns: `"{{ }}"`, `"{ }"`, `"[[ ]]"`, `"< >"`, `"<< >>"`.

---

## Request Builder Classes

### SendEmailRequest

Extends `BasicEmailRequestBuilder<SendEmailRequest>`.

```csharp
new SendEmailRequest()
    .WithTo("recipient@example.com")
    .WithCc("cc@example.com")
    .WithBcc("bcc@example.com")
    .WithSubject("Subject")
    .WithBody("HTML body", isHtml: true)
    .WithHtmlBody(true)
    .WithAttachment("C:\\path\\file.pdf")       // string path overload
    .WithAttachment(someIResource)              // IResource overload
    .WithImportance(GMailImportance.High)
    .WithReplyTo("noreply@example.com")
    .AsDraft(false)
```

### ReplyToEmailRequest

Extends `BasicEmailRequestBuilder<ReplyToEmailRequest>`.

```csharp
new ReplyToEmailRequest()
    .WithTo("extra-recipient@example.com")
    .WithBody("Reply body")
    .WithNewSubject("Updated Subject")
    .WithReplyToAll(true)
    .WithImportance(GMailImportance.Normal)
    .WithAttachment("C:\\path\\file.pdf")
    .AsDraft(false)
```

### ForwardEmailRequest

Extends `BasicEmailRequestBuilder<ForwardEmailRequest>`.

```csharp
new ForwardEmailRequest()
    .WithTo("forward-to@example.com")
    .WithBody("Forwarding this email")
    .WithNewSubject("FW: Original Subject")
    .WithAttachment("C:\\path\\file.pdf")
    .AsDraft(false)
```

### CreateCalendarItem

```csharp
new CreateCalendarItem()
    .WithTitle("Team Standup")
    .WithStartDate(DateTimeOffset.Now.AddDays(1).AddHours(9))
    .WithEndDate(DateTimeOffset.Now.AddDays(1).AddHours(9).AddMinutes(30))
    .WithTimezone("America/New_York")           // default: "UTC"
    .AllDayEvent(false)                         // default: false
    .NewDescription("Daily standup meeting")
    .AddRequiredAttendees("alice@company.com", "bob@company.com")
    .AddOptionalAttendees("charlie@company.com")
    .AddResourceAttendees("room@company.com")
    .ShowAs(EventTransparency.Opaque)           // default: Opaque
    .WithVisibility(EventVisibility.DEFAULT)    // default: DEFAULT
    .WithConferenceData(true)                   // default: false
    .WithPreferredReturnTimezone("UTC")
    .SendNotification(SendUpdates.ALL)          // default: ALL
    .CanModifyEvent(false)                      // default: false
    .CanInviteOthers(true)                      // default: true
    .CanSeeAttendeesList(true)                  // default: true
```

### UpdateCalendarItem

**Important:** Constructor requires the `ICalendarEvent` being updated.

```csharp
new UpdateCalendarItem(existingEvent)
    .WithTitle("Updated Standup")
    .WithStartDate(newStartDate)
    .WithEndDate(newEndDate)
    .WithTimezone("America/New_York")
    .AllDayEvent(false)
    .NewDescription("Updated agenda")
    .AddRequiredAttendees("dave@company.com")
    .RemoveRequiredAttendees("bob@company.com")
    .ClearOptionalAttendees()
    .OverwriteOptionalAttendees("newperson@company.com")
    .AddOptionalAttendees("charlie@company.com")
    .AddResourceAttendees("room@company.com")
    .RemoveResourceAttendees("oldroom@company.com")
    .ClearResourceAttendees()
    .OverwriteResourceAttendees("newroom@company.com")
    .WithConferenceData(true)
    .ShowAs(EventTransparency.Opaque)
    .WithVisibility(EventVisibility.DEFAULT)
    .WithPreferredReturnTimezone("UTC")
    .SendNotification(SendUpdates.ALL)
    .CanModifyEvent(false)
    .CanInviteOthers(true)
    .CanSeeAttendeesList(true)
```

> **UpdateCalendarItem attendee methods:** For each attendee type (Required, Optional, Resource), the following operations are available: `Add...`, `Remove...`, `Clear...`, `Overwrite...` (each with `IEnumerable<string>` and `params string[]` overloads).

---

## Filter Classes

### MailFilter (Gmail)

```csharp
var filter = new MailFilter()
    .BySubject(FilterStringOperator.Contains, "Invoice")
    .And()
    .ByUnread(true)
    .And()
    .ByDateAndTime(FilterDateOperator.NewerThan, DateTime.Now.AddDays(-7));
```

Available filter methods:
- `.ByFrom(FilterStringOperator, string)` — filter by sender
- `.ByTo(FilterStringOperator, string)` — filter by recipient
- `.ByCc(FilterStringOperator, string)` — filter by CC
- `.ByBcc(FilterStringOperator, string)` — filter by BCC
- `.BySubject(FilterStringOperator, string)` — filter by subject
- `.ByBody(FilterStringOperator, string)` — filter by body content
- `.ByDateAndTime(FilterDateOperator, DateTime)` — filter by date
- `.ByFilename(FilterStringOperator, string)` — filter by attachment filename
- `.ByLabels(FilterCollectionOperator, string[])` — filter by labels
- `.ByCategories(FilterStringOperator, string)` — filter by categories
- `.ByImportant(bool)` — filter important emails
- `.ByStarred(bool)` — filter starred emails
- `.ByUnread(bool)` — filter unread emails
- `.WithAttachments(bool)` — filter emails with attachments
- `.And()` / `.Or()` — logical operators
- `.BySubExpression(Action<MailFilter>)` — nested sub-expressions

### DriveItemFilter

```csharp
var filter = new DriveItemFilter()
    .ByName(FilterStringOperator.Contains, "report")
    .And()
    .ByType(FilterListOptionOperator.Is, FileTypes.GoogleSpreadsheet)
    .And()
    .ByCreationDate(FilterDateOperator.NewerThan, DateTime.Now.AddDays(-30));
```

Available filter methods:
- `.ByName(FilterStringOperator, string)` — filter by name
- `.ByTextInFile(FilterStringOperator, string)` — filter by text content in file
- `.ByCreationDate(FilterDateOperator, DateTime)` — filter by creation date
- `.ByLastModifiedDate(FilterDateOperator, DateTime)` — filter by last modified date
- `.ByOwner(FilterCollectionOperator, string)` — filter by owner email
- `.ByType(FilterListOptionOperator, FileTypes)` — filter by file type
- `.ByStarred(bool)` — filter starred items
- `.And()` / `.Or()` — logical operators
- `.BySubExpression(Action<DriveItemFilter>)` — nested sub-expressions

---

## Key Enums

| Enum | Values | Used In |
|------|--------|---------|
| `GMailImportance` | `Low`, `Normal`, `High` | Email importance |
| `EventResponseType` | `Declined`, `Tentative`, `Accepted` | Calendar RSVP |
| `DeleteEventMode` | `SingleEvent`, `FutureOnly`, `PastAndFuture` | Recurring event deletion |
| `ConflictBehavior` | `Replace`, `Fail`, `Rename`, `AddSeparate` | File/folder conflicts |
| `Role` | `Owner`, `Writer`, `Commenter`, `Reader` | Sharing permissions |
| `GranteeType` | `User`, `Group` | Share target type |
| `IdentificationType` | `UrlOrId`, `FullPath` | Drive item lookup |
| `FileTypes` | `GoogleDocs`, `PDF`, `ZIP`, `PlainText`, `RichText`, `MSWord`, `OpenOfficeDoc`, `GoogleSlides`, `MSPowerPoint`, `OpenOfficePresentation`, `GoogleSpreadsheet`, `MSExcel`, `OpenOfficeSheet`, `CSV`, `Images`, `GoogleDrawing`, `Videos`, `Audio` | Drive file type filter |
| `CellReadMode` | `Values`, `Formulas`, `Text` | Sheets cell reading |
| `RangeWriteMode` | `Overwrite`, `Append`, `AppendRight`, `Insert`, `InsertRight` | Sheets range writing |
| `RangeDeleteMode` | `None`, `Rows`, `Columns` | Sheets range deletion |
| `RowsDeleteMode` | `Clear`, `Delete` | Sheets row deletion |
| `ColumnDeleteMode` | `Clear`, `Delete` | Sheets column deletion |
| `TextStyle` | `NormalText`, `Title`, `Subtitle`, `Heading1`–`Heading6` | Docs text styling |
| `TextLocation` | `Beginning`, `End` | Docs text insertion |
| `TextMatchMode` | `Contains`, `Equals` | Docs text matching |
| `TextRecurrences` | `Once`, `AllRecurrences` | Docs find/replace/delete scope |
| `GDocExportFormat` | `Word`, `OpenDocument`, `RichText`, `Pdf`, `PlainText`, `WebPage`, `EPub` | Download Docs |
| `GSheetExportFormat` | `Xlsx`, `Ods`, `Pdf`, `WebPage`, `Csv`, `Tsv` | Download Sheets |
| `GSlideExportFormat` | `Ppt`, `Odp`, `Pdf`, `PlainText`, `Jpeg`, `Png`, `Svg` | Download Slides |
| `GDrawingExportFormat` | `Odp`, `Pdf`, `Jpeg`, `Png`, `Svg` | Download Drawings |
| `DriveLabelType` | `Badged`, `Standard`, `All` | Drive label queries |
| `FilterStringOperator` | `Contains`, `NotContains`, `Equals`, `NotEquals`, `StartsWith`, `EndsWith`, `IsEmpty`, `IsNotEmpty` | Filter expressions |
| `FilterDateOperator` | `NewerThan`, `OlderThan` | Date filters |
| `FilterCollectionOperator` | `In`, `NotIn`, `AllIn`, `NotAllIn`, `IsEmpty`, `IsNotEmpty` | Collection filters |
| `FilterListOptionOperator` | `Is`, `IsNot` | Type filters |

---

## Key Interfaces (Return Types)

### IMail

Properties: `Id` (string), `Subject` (string), `Body` (string), `Item` (GmailMessage — with `FromAddress`, `ToAddressList`, `LabelIds`, `ThreadId`, etc.)

Methods: `Reply(body, ...)`, `Reply(ReplyToEmailRequest)`, `Forward(body, ...)`, `Forward(ForwardEmailRequest)`, `Move(source, destination)`, `Archive()`, `Delete(deletePermanently)`, `Download()`, `GetAttachmentsInfo()`, `DownloadAttachments()`, `MarkAsRead()`, `MarkAsUnread()`, `ApplyLabels(labels)`, `RemoveLabels(labels)`

### IMailLabel

Properties: `Id` (string), `Name` (string), `IsUserDefined` (bool)

Methods: `GetNewestEmail(filter, markAsRead)`, `GetEmails(filter, markAsRead, maxResults)`, `ApplyTo(mail)`, `RemoveFrom(mail)`

### IMailAttachmentInfo

Properties: `Id` (string), `Name` (string)

Methods: `Download()` → Stream

### ICalendar

Properties: `Id` (string), `IsDefault` (bool), `Item` (GSuiteCalendarItem — with Summary, Description, TimeZone)

Methods: `CreateEvent(eventInformation)`, `GetEvents(startDate, endDate, top, timezone, search)`, `UpdateEvent(calendarEvent, changes)`, `DeleteEvent(calendarEvent, deleteMode)`, `ForwardEvent(calendarEvent, attendees, forwardSeries)`, `RespondToEvent(calendarEvent, response, comment, additionalGuests, allOccurrences, sendResponseNotification)`

### ICalendarEvent

Properties: `Id` (string), `Calendar` (ICalendar), `Item` (GSuiteEventItem — with Summary, Start/EndDateTime, Location, Attendees, WebLink)

Methods: `Update(changes)`, `Delete(deleteMode)`, `Forward(attendees, forwardSeries)`, `Respond(response, comment, additionalGuests, allOccurrences, sendResponseNotification)`

### IDriveItem

Properties: `Id` (string), `FullName` (string), `IsFolder` (bool), `Item` (GDriveRemoteItem)

Methods: `Move(destination, newName, conflictBehavior)`, `Delete()`, `Refresh()`, `Share(role, useDomainAdminAccess)`, `Share(domain, role, ...)`, `Share(shareWith, recipients, sendNotificationEmail, role, ...)`

Extension methods: `.ToFile()` → IFile, `.ToFolder()` → IFolder

### IFile (extends IDriveItem)

Methods: `Copy(destination, newName, conflictBehavior)`, `Move(destination, newName, conflictBehavior)` → IFile, `Download(downloadOptions)`, `Upload(destination, convertToGoogleType, conflictBehavior, uploadAsIsIfConvertFails)`, `GetLabels()`, `ApplyLabels(labels)`, `RemoveLabels(labels)`, `ClearLabelFields(labelId, fields)`

### IFolder (extends IDriveItem)

Methods: `Move(destination, newName, conflictBehavior)` → IFolder, `GetItem(relativePath)`, `GetFile(relativePath)`, `GetFolder(relativePath)`, `GetFiles(filter, maxResults)`, `GetFolders(filter, maxResults)`, `GetFilesAndFolders(filter, maxResults)`, `CreateFolder(name, description, conflictBehavior)`

### ILabel (Drive Labels)

Properties: `Id` (string), `Name` (string), `LabelItem` (GDriveLabel), `Fields` (GDriveLabelFieldCollection), `FieldValues` (Dictionary<string, object>)

Indexer: `label["fieldName"]` — get/set field values

Methods: `UpdateTextFieldValue(fieldName, string)`, `UpdateNumberFieldValue(fieldName, long)`, `UpdateDateFieldValue(fieldName, DateTime)`, `UpdateChoiceFieldValue(fieldName, List<string>)`, `UpdateUserFieldValue(fieldName, string)`, `ApplyToFile(file)`

### ISpreadsheet

Properties: `Id` (string), `Name` (string), `Item` (GDriveRemoteItem)

Methods: `GetSheets()`, `AddSheet(name, positionIndex)`, `DeleteSheet(sheetName)`, `RenameSheet(replacedSheetName, newSheetName)`, `GetRanges()`, `GetNamedRanges()`

### IRange

Properties: `Name` (string), `Type` (RangeType — Sheet or NamedRange)

Methods: `ReadRange(hasHeaders, cellReadMode)`, `WriteRange(data, hasHeaders, writeMode, insertRowPosition)`, `WriteRow(DataRow, ...)`, `WriteRow(IEnumerable<object>, ...)`, `WriteColumn(DataColumn, ...)`, `WriteColumn(IEnumerable<object>, ...)`, `DeleteRange(deleteMode)`, `DeleteRows(string rows, deleteMode)`, `DeleteRows(IEnumerable<int>, deleteMode)`, `DeleteColumn(int columnIndex, hasHeaders, deleteMode)`, `DeleteColumn(string columnName, hasHeaders, deleteMode)`

### ISheet (extends IRange)

Methods: `Delete()`, `Rename(newName)`, `ReadCell(cell, cellReadMode)`, `WriteCell(cell, value)`

### INamedRange (extends IRange)

No additional methods.

### IDocument

Properties: `Id` (string), `Name` (string), `Item` (GDriveRemoteItem)

Methods: `ReadText(sectionName, matchCase, textMatchMode)`, `WriteText(text, style, location, sectionName, matchCase, textMatchMode)`, `DeleteText(text, matchCase, recurrences)`, `DeleteText(sectionName, matchCase, textMatchMode)`, `FillDocumentTemplate(fields, symbol)`, `FindAndReplaceText(searchTerm, replacement, matchCase, recurrences)`
