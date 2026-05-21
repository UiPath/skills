# UiPath GSuite Activities - Legacy Reference

## Overview
Google Workspace integration: Gmail, Drive, Sheets, Docs, Calendar, Tasks, Forms, Apps Script. Package: `UiPath.GSuite.Activities`.

---

## Activity Counts by Service
- **Gmail**: 18 activities (send, receive, delete, archive, labels, triggers)
- **Google Drive**: 25 activities (upload, download, share, labels, permissions)
- **Google Sheets**: 25 activities (read/write range/cell/row/column, format, iterate)
- **Google Docs**: 7 activities (read/write/replace text, insert image, template fill)
- **Google Calendar**: 8+ activities (create/modify/delete events, RSVP, calendars)
- **Google Tasks**: 10 activities (create/complete/delete tasks and lists)
- **Google Forms**: 2 activities + 2 triggers (form info, responses)
- **Apps Script**: 1 activity (RunScript)

---

## Authentication
- All activities use **Connection Service** pattern (ConnectionId argument)
- **OAuth2 scopes** declared per activity via `RequiredScopes` property
- **Connector types**: GmailConnector, GoogleDriveConnector, GoogleSpreadsheetsConnector, GoogleDocsConnector, GoogleTasksConnector, GoogleWorkspaceConnector

---

## Critical Gotchas

### Gmail
1. **GmailMessage.Attachments property is OBSOLETE and never populated** - must use DownloadAttachments activity separately
2. **Labels stored as base64-encoded JSON** - AllLabels property is serialized GmailLabel[]
3. **Email governance** - validates recipients against organization blocklists (skipped for drafts)
4. **Address format**: Standard email format, parsed by Google API

### Google Drive
5. **ConflictResolution has 5 values**: Replace, Fail, Rename, AddSeparate (allows duplicate names in Drive), UseExisting (return existing item)
6. **OverwriteExistingFile property is OBSOLETE** - use ConflictResolution enum instead
7. **SingleFileToUpload is OBSOLETE** - use MultipleFilesToUpload
8. **Drive label operations** require enterprise workspace (not personal accounts)

### Google Sheets
9. **A1 notation for ranges** - same as Excel (e.g., "Sheet1!A1:B10")
10. **WriteMode**: Overwrite, Append (add below), Insert (insert rows)
11. **Cell color format**: RGB hex "#RRGGBB"
12. **HeaderRow boolean** affects DataTable column naming

### Google Docs
13. **ReadMode options**: AllText, ParagraphIndex, ParagraphContent, TextAfterIndex
14. **WriteMode options**: End, Index, ReplaceAll
15. **FindAndReplace MatchMode**: ExactMatch, Contains, RegularExpression

### Google Calendar
16. **Recurrence uses RRULE format** (RFC 5545) - complex string syntax
17. **SendUpdates enum**: None, Owner, All - controls notification behavior
18. **DeleteEventType**: ThisEvent, ThisAndFollowing, AllInstances (recurring events)

### Apps Script
19. **DevMode uses script PROJECT ID** vs production uses DEPLOYMENT ID - completely different IDs
20. **Scopes are user-specified** (not predefined like other services)

### Connection Service
21. **Bindings version locked at V2.1** - breaking changes require major version bump
22. **Legacy non-connection-service activities still exist** in Non-Portable folder
23. **BackupSlot<T> pattern** for migrating obsolete properties to new ones

### Persistence Activities (Triggers/Waits)
24. **WaitFor* activities** use bookmark resumption pattern (long-running workflows)
25. **Marked with [PersistentActivity]** attribute
26. **Different from NewEmailReceived triggers** (ITriggerActivity vs IPersistenceActivity)

### Item Arguments
27. **DriveItemArgument** for file/folder selection - supports BrowserItemId (from remote browser) and ManualEntryId
28. **FolderArgument** for Gmail folders
29. **GTaskArgument** for task list/parent references
