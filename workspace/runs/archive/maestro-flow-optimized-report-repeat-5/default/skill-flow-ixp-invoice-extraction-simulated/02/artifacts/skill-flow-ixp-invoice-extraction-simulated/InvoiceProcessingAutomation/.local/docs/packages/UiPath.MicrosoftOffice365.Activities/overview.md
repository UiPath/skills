# UiPath.MicrosoftOffice365.Activities — Overview

> **Agent instruction — read all linked docs before proceeding:** Follow and read every hyperlinked reference document on this page in full before generating XAML. XAML structural patterns (BackupSlots, StoredValue, x:Reference, all-null attributes, namespace declarations) are defined in the linked component, type, and filter docs — not repeated here. If those linked docs also contain hyperlinks to other reference docs, follow those too.

`UiPath.MicrosoftOffice365.Activities`

A set of activities for automating Microsoft 365 services including Outlook, Excel Online, OneDrive, SharePoint, and Calendar — using the Microsoft Graph API with modern connection-based authentication.

## Documentation

Per-activity reference documentation is in the [activities/](activities/) directory. Coded workflow API documentation is in [coded/coded-api.md](coded/coded-api.md).

### Reference Documentation

Detailed reference docs for shared types used across activities:

- **[Types](activities/types/)** — Complex input/output object types (O365DriveRemoteItem, O365EventItem, Office365Message, etc.)
- **[Components](activities/components/)** — Composition argument types with input modes and per-mode properties (DriveItemArgument, CalendarArgument, MailFolderArgument, etc.)
- **[Filters](activities/filtering/)** — Filter collection types with criteria, operators, and XAML examples

## Usage Guidance

> **Prefer `*Connections` activities outside of `Office365ApplicationScope`.** `*Connections` activities authenticate via Integration Service independently — place them directly in your workflow without a scope wrapper. `Office365ApplicationScope` is only needed for classic (non-`*Connections`) activities, or when Integration Service is unavailable and you must supply credentials directly (interactive token, username/password, certificate, or app secret flows). See [Office365ApplicationScope](activities/Office365ApplicationScope.md) for when to use the scope.

## Activities

### Microsoft 365 Scope

| Activity | Description |
|----------|-------------|
| [Office365ApplicationScope](activities/Office365ApplicationScope.md) | Authenticates every Office 365 activity in its body — classic and `*Connections` alike — via Interactive Token / Username+Password / IWA / App+Secret / App+Certificate. Provides full functionality without Integration Service. |

---

### Calendar

| Activity | Description |
|----------|-------------|
| [CreateEventConnections](activities/CreateEventConnections.md) | Adds an event to the indicated calendar. |
| [DeleteEventConnections](activities/DeleteEventConnections.md) | Cancels an event and sends cancellation notifications to all attendees. |
| [FindMeetingTimesConnections](activities/FindMeetingTimesConnections.md) | Returns possible time slots for a meeting between specified attendees. |
| [ForEachEventConnections](activities/ForEachEventConnections.md) | Iterates through calendar events matching the filter criteria. |
| [ForwardEventConnections](activities/ForwardEventConnections.md) | Forwards an event to specified attendees. |
| [GetCalendarsConnections](activities/GetCalendarsConnections.md) | Retrieves a list of calendars for the authenticated account. |
| [GetEventByIdConnections](activities/GetEventByIdConnections.md) | Retrieves an event by its ID. |
| [GetEventListConnections](activities/GetEventListConnections.md) | Retrieves a list of calendar events matching the filter criteria. |
| [ModifyEventConnections](activities/ModifyEventConnections.md) | Updates the properties of an existing calendar event. |
| [RsvpConnections](activities/RsvpConnections.md) | Responds to a calendar event invitation. |
| [WaitForEventCreated](activities/WaitForEventCreated.md) | Waits for a new calendar event to be created and resumes the workflow. |
| [WaitForEventInvitationReceived](activities/WaitForEventInvitationReceived.md) | Waits for a new event invitation to be received and resumes the workflow. |
| [WaitForEventReplied](activities/WaitForEventReplied.md) | Waits for someone to reply to a calendar event and resumes the workflow. |
| [WaitForEventUpdated](activities/WaitForEventUpdated.md) | Waits for an event to be updated and resumes the workflow. |
| [EventReplied](activities/EventReplied.md) | **Trigger** — fires when someone replies to a calendar event. |
| [EventUpdated](activities/EventUpdated.md) | **Trigger** — fires when a calendar event is updated. |
| [NewEventCreated](activities/NewEventCreated.md) | **Trigger** — fires when a new calendar event is created. |
| [NewEventInvitationReceived](activities/NewEventInvitationReceived.md) | **Trigger** — fires when a new event invitation is received. |

---

### Excel Online

| Activity | Description |
|----------|-------------|
| [AddSheetConnections](activities/AddSheetConnections.md) | Adds a new sheet to a workbook. |
| [CopyRangeConnections](activities/CopyRangeConnections.md) | Copies a range and pastes it to another location. |
| [CreateTableConnections](activities/CreateTableConnections.md) | Creates a table from the specified range. |
| [CreateWorkbookConnections](activities/CreateWorkbookConnections.md) | Creates a new Excel workbook in OneDrive or SharePoint. |
| [DeleteColumnConnections](activities/DeleteColumnConnections.md) | Deletes a specified column from a sheet, table, or range. |
| [DeleteRangeConnections](activities/DeleteRangeConnections.md) | Deletes a range from the selected Excel workbook. |
| [DeleteRowsConnections](activities/DeleteRowsConnections.md) | Deletes one or more rows from a specified position in a workbook range. |
| [DeleteSheetConnections](activities/DeleteSheetConnections.md) | Deletes a sheet from a workbook. |
| [ForEachRowConnections](activities/ForEachRowConnections.md) | Iterates through rows in a workbook range or table. |
| [ForEachSheetConnections](activities/ForEachSheetConnections.md) | Iterates through the sheets within a workbook. |
| [GetCellColorConnections](activities/GetCellColorConnections.md) | Gets the background color of a specified cell. |
| [ReadCellConnections](activities/ReadCellConnections.md) | Reads the value of a specified cell in an Excel workbook. |
| [ReadColumnConnections](activities/ReadColumnConnections.md) | Reads the values in a column from the first cell to the last completed value. |
| [ReadRangeConnections](activities/ReadRangeConnections.md) | Reads a range from an Excel workbook into a DataTable. |
| [ReadRowConnections](activities/ReadRowConnections.md) | Reads the values in a row from the first to the last completed cell. |
| [RenameSheetConnections](activities/RenameSheetConnections.md) | Renames a sheet in a workbook. |
| [SetRangeColorConnections](activities/SetRangeColorConnections.md) | Sets the background color of a specified range. |
| [VLookupRangeConnections](activities/VLookupRangeConnections.md) | Finds a value in a range using the VLOOKUP function. |
| [WaitForRowAddedToTableBottom](activities/WaitForRowAddedToTableBottom.md) | Waits for a new row to be added to the bottom of an Excel table and resumes the workflow. |
| [WaitForWorksheetCellUpdated](activities/WaitForWorksheetCellUpdated.md) | Waits for a cell in a worksheet to be updated and resumes the workflow. |
| [WaitForWorksheetCreated](activities/WaitForWorksheetCreated.md) | Waits for a new worksheet to be created in a workbook and resumes the workflow. |
| [WriteCellConnections](activities/WriteCellConnections.md) | Writes a value to a specified cell in an Excel workbook. |
| [WriteColumnConnections](activities/WriteColumnConnections.md) | Writes a column of data to an Excel workbook. |
| [WriteRangeConnections](activities/WriteRangeConnections.md) | Writes a DataTable to the indicated range in an Excel workbook. |
| [WriteRowConnections](activities/WriteRowConnections.md) | Writes a row of data to an Excel workbook. |
| [RowAddedToTableBottom](activities/RowAddedToTableBottom.md) | **Trigger** — fires when a new row is added to the bottom of an Excel table. |
| [WorksheetCellUpdated](activities/WorksheetCellUpdated.md) | **Trigger** — fires when a cell in a worksheet is updated. |
| [WorksheetCreated](activities/WorksheetCreated.md) | **Trigger** — fires when a new worksheet is created in a workbook. |

---

### OneDrive & SharePoint

| Activity | Description |
|----------|-------------|
| [AssignSensitivityLabelConnections](activities/AssignSensitivityLabelConnections.md) | Assigns a sensitivity label to a specified file. |
| [CheckinCheckoutFileConnections](activities/CheckinCheckoutFileConnections.md) | Checks in or checks out a SharePoint file. |
| [CopyItemConnections](activities/CopyItemConnections.md) | Copies a file or folder to a specified destination in OneDrive or SharePoint. |
| [CreateFolderConnections](activities/CreateFolderConnections.md) | Creates a folder at the specified location in OneDrive or SharePoint. |
| [DeleteItemConnections](activities/DeleteItemConnections.md) | Deletes a file or folder from OneDrive or SharePoint. |
| [DownloadFileConnections](activities/DownloadFileConnections.md) | Downloads a file from OneDrive or SharePoint. |
| [ForEachFileFolderConnections](activities/ForEachFileFolderConnections.md) | Iterates over files and folders from OneDrive or SharePoint. |
| [GetFileFolderConnections](activities/GetFileFolderConnections.md) | Gets a file or folder from OneDrive or SharePoint for use in other activities. |
| [GetFileFolderMetadataConnections](activities/GetFileFolderMetadataConnections.md) | Retrieves metadata properties for a file or folder in OneDrive or SharePoint. |
| [GetFileListConnections](activities/GetFileListConnections.md) | Retrieves a list of files and folders from OneDrive or SharePoint. |
| [GetSensitivityLabelsConnections](activities/GetSensitivityLabelsConnections.md) | Gets the sensitivity labels assigned to a specified file. |
| [MoveItemConnections](activities/MoveItemConnections.md) | Moves a file or folder to a specified destination in OneDrive or SharePoint. |
| [RenameItemConnections](activities/RenameItemConnections.md) | Renames a file or folder in OneDrive or SharePoint. |
| [ShareItemConnections](activities/ShareItemConnections.md) | Shares a file or folder with specified recipients. |
| [UpdateFileFolderMetadataConnections](activities/UpdateFileFolderMetadataConnections.md) | Updates metadata properties for a file or folder in OneDrive or SharePoint. |
| [UploadFilesConnections](activities/UploadFilesConnections.md) | Uploads files to OneDrive or SharePoint. |
| [WaitForFileCreated](activities/WaitForFileCreated.md) | Waits for a new file to be created in a specified location and resumes the workflow. |
| [WaitForFileUpdated](activities/WaitForFileUpdated.md) | Waits for a file to be updated in a specified location and resumes the workflow. |
| [FileUpdated](activities/FileUpdated.md) | **Trigger** — fires when a file is updated in the specified location. |
| [NewFileCreated](activities/NewFileCreated.md) | **Trigger** — fires when a new file is created in the specified location. |

---

### Outlook

| Activity | Description |
|----------|-------------|
| [ArchiveEmailConnections](activities/ArchiveEmailConnections.md) | Archives an email. |
| [AssignSensitivityLabelToEmailConnections](activities/AssignSensitivityLabelToEmailConnections.md) | Assigns a sensitivity label to a specified email. |
| [DeleteEmailConnections](activities/DeleteEmailConnections.md) | Deletes an email. |
| [DownloadEmailAttachments](activities/DownloadEmailAttachments.md) | Downloads email attachments. |
| [DownloadEmailConnections](activities/DownloadEmailConnections.md) | Downloads an email message. |
| [ForEachEmailConnections](activities/ForEachEmailConnections.md) | Iterates over emails matching the filter criteria. |
| [ForwardEmailConnections](activities/ForwardEmailConnections.md) | Forwards an email to new recipients. |
| [GetEmailByIdConnections](activities/GetEmailByIdConnections.md) | Retrieves an email by its ID. |
| [GetEmailFoldersListConnections](activities/GetEmailFoldersListConnections.md) | Retrieves the list of email folders for the selected account. |
| [GetEmailListConnections](activities/GetEmailListConnections.md) | Retrieves a list of emails matching the filter criteria. |
| [GetEmailThreadConnections](activities/GetEmailThreadConnections.md) | Retrieves all emails in a conversation thread. |
| [GetMail](activities/GetMail.md) | Returns all emails from the inbox. **Windows only.** |
| [GetNewestEmail](activities/GetNewestEmail.md) | Returns the most recent email matching the search criteria. |
| [MarkAsReadUnreadConnections](activities/MarkAsReadUnreadConnections.md) | Marks an email as read or unread. |
| [MoveEmailConnections](activities/MoveEmailConnections.md) | Moves an email to a folder within the same mailbox. |
| [ReplyToEmailConnections](activities/ReplyToEmailConnections.md) | Replies to an email. |
| [SendDraftEmailConnections](activities/SendDraftEmailConnections.md) | Sends an email saved as a draft. |
| [SendMailConnections](activities/SendMailConnections.md) | Sends an email message. |
| [SetEmailCategoriesConnections](activities/SetEmailCategoriesConnections.md) | Assigns or removes categories on an email. |
| [TurnOffAutomaticRepliesConnections](activities/TurnOffAutomaticRepliesConnections.md) | Turns off automatic out-of-office replies. |
| [TurnOnAutomaticRepliesConnections](activities/TurnOnAutomaticRepliesConnections.md) | Configures and activates automatic out-of-office replies. |
| [WaitForEmailReceived](activities/WaitForEmailReceived.md) | Waits for a new email to be received and resumes the workflow. |
| [WaitForEmailSent](activities/WaitForEmailSent.md) | Waits for an email to be sent and resumes the workflow. |
| [EmailSent](activities/EmailSent.md) | **Trigger** — fires when an email is sent. |
| [NewEmailReceived](activities/NewEmailReceived.md) | **Trigger** — fires when a new email is received. |

---

### SharePoint Lists

| Activity | Description |
|----------|-------------|
| [AddListItemConnections](activities/AddListItemConnections.md) | Adds a new item to a SharePoint list. |
| [BulkAddListItemsConnections](activities/BulkAddListItemsConnections.md) | Adds multiple items to a SharePoint list. |
| [DeleteSharepointListItemsConnections](activities/DeleteSharepointListItemsConnections.md) | Deletes items from a SharePoint list. |
| [ForEachListConnections](activities/ForEachListConnections.md) | Iterates through the lists of a SharePoint site. |
| [ForEachListItemConnections](activities/ForEachListItemConnections.md) | Iterates through items in a SharePoint list. |
| [GetListInfo](activities/GetListInfo.md) | Retrieves information about a specified SharePoint list. |
| [GetListItemsConnections](activities/GetListItemsConnections.md) | Retrieves items from a SharePoint list. |
| [GetSingleSharepointListItemConnections](activities/GetSingleSharepointListItemConnections.md) | Retrieves a single item from a SharePoint list. |
| [UpdateListItemConnections](activities/UpdateListItemConnections.md) | Updates an existing item in a SharePoint list. |
| [WaitForListItemAdded](activities/WaitForListItemAdded.md) | Waits for a new item to be added to a SharePoint list and resumes the workflow. |
| [WaitForListItemUpdated](activities/WaitForListItemUpdated.md) | Waits for an item to be updated in a SharePoint list and resumes the workflow. |
| [SharepointListItemAdded](activities/SharepointListItemAdded.md) | **Trigger** — fires when a new item is added to a SharePoint list. |
| [SharepointListItemUpdated](activities/SharepointListItemUpdated.md) | **Trigger** — fires when an item is updated in a SharePoint list. |

---

### General

| Activity | Description |
|----------|-------------|
| [HttpRequestConnections](activities/HttpRequestConnections.md) | Runs HTTP calls against Microsoft 365 using the Microsoft Graph API. |

---

## Composition Patterns for AI Workflow Generation

O365 activities use **composition argument objects** to select files, calendars, mail folders, mailboxes, and SharePoint lists. Each argument has an `InputMode`/`ItemSelectionMode` enum that determines which sub-properties are required. Understanding these patterns is essential for generating valid XAML.

### Item Selection Pattern

See the [components reference](activities/components/) for full details on each argument type.

| Argument Type | Available Modes | Details |
|--------------|----------------|---------|
| [`DriveItemArgument`](activities/components/DriveItemArgument.md) | Browse, ItemId, UseExisting, ItemUrl, FullPath, RelativePath | File/folder selection |
| [`CalendarArgument`](activities/components/CalendarArgument.md) | Browse, UseExisting | Calendar selection |
| [`MailFolderArgument`](activities/components/MailFolderArgument.md) | Browse, EnterPath | Outlook folder selection |
| [`MailboxArgument`](activities/components/MailboxArgument.md) | UseSharedMailbox | Shared mailbox selection |
| [`ListArgument`](activities/components/ListArgument.md) | Browse, Manually | SharePoint list selection |

### Model Types Quick Reference

Activities return these model types as `OutArgument<T>`. See the [types reference](activities/types/) for full property lists.

- [`O365DriveRemoteItem`](activities/types/O365DriveRemoteItem.md) — Drive file/folder with ID, Name, FullName, Extension, Url, MimeType, IsFolder, SizeInBytes
- [`O365EventItem`](activities/types/O365EventItem.md) — Calendar event with Id, Subject, Body, Start, End, Location, Attendees, Organizer
- [`DateTimeTimeZone`](activities/types/DateTimeTimeZone.md) — Date/time value paired with timezone identifier
- [`EventAttendee`](activities/types/EventAttendee.md) — Event attendee with DisplayName, Email, ResponseStatus, Type
- [`EventBody`](activities/types/EventBody.md) — Event body content with Content, ContentType
- [`OnlineMeeting`](activities/types/OnlineMeeting.md) — Online meeting info with JoinUrl, ConferenceId, DialInNumbers
- [`O365CalendarItem`](activities/types/O365CalendarItem.md) — Calendar with Id, Name, Color, IsDefault, CanShare, CanEdit, Owner
- [`Office365Message`](activities/types/Office365Message.md) — Email with MessageId, Subject, BodyPreview, From, To, CC, Importance, IsRead
- [`Office365SharepointList`](activities/types/Office365SharepointList.md) — SharePoint list with Id, Name, DisplayName, Description, WebUrl, Columns
- [`Office365SharepointListItem`](activities/types/Office365SharepointListItem.md) — List item with Id, Fields, CreatedDateTime, LastModifiedDateTime
- [`O365MailFolder`](activities/types/O365MailFolder.md) — Mail folder metadata

### Filter Pattern

See the [filtering reference](activities/filtering/) for full details.

- [`FileFilterArgument`](activities/filtering/FileFilterArgument.md) — Drive file filtering by name, extension, dates, size (Graph API OData)
- [`FileFolderFilterArgument`](activities/filtering/FileFolderFilterArgument.md) — Drive file search by name, extension, author, dates, shared users (Search API KQL)
- [`MailFilterCollection`](activities/filtering/MailFilterCollection.md) — Outlook message filtering by subject, sender, recipient, date, type
- [`FilenameFilterCollection`](activities/filtering/FilenameFilterCollection.md) — Email attachment filename filtering
- [`EventFilterCollection`](activities/filtering/EventFilterCollection.md) — Calendar event filtering by subject, attendees, importance, show-as, type
- [`ColumnFilterCollection`](activities/filtering/ColumnFilterCollection.md) — SharePoint list item filtering by column values (string, date, bool, number)
- [`ColumnByNameFilterCollection`](activities/filtering/ColumnByNameFilterCollection.md) — SharePoint list item filtering by column name (string-based)
