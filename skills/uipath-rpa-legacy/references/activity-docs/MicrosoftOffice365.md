# UiPath Microsoft Office 365 Activities - Legacy Reference

## Overview
Office 365 integration via Microsoft Graph API: Mail, Calendar, Excel Online, OneDrive, SharePoint, Planner, Groups. Package: `UiPath.MicrosoftOffice365.Activities`.

---

## Authentication Types
| Type | Use Case |
|------|----------|
| InteractiveToken | User-interactive OAuth (browser popup) - default |
| UsernameAndPassword | Direct credentials (limited by Azure policy) |
| IntegratedWindowsAuthentication | Windows SSPI/Kerberos |
| ApplicationIdAndSecret | App-only OAuth (client credentials) |
| ApplicationIdAndCertificate | Certificate-based app auth |
| IntegrationService | UiPath Orchestrator Connection Service |

**Required**: Azure App Registration with Client ID, appropriate permissions granted

---

## Activity Groups

### Mail (6 activities)
SendMail, DeleteMail, ForwardMail, ReplyToMail, MoveMail, SetMailCategories

### Calendar (10 activities)
CreateEvent, ModifyEvent, DeleteEvent, AddAttendee, AddLocation, AddAttachment, SearchEvents, GetCalendars, FindMeetingTimes, Rsvp

### Excel Online (15+ activities)
ReadRange, WriteCell, WriteRange, ReadCell, ReadRow, ReadColumn, AppendRange, PasteRange, ClearRange, CopyRange, DeleteRows, InsertRows, CreateTable, GetSheets, VLookupRange, etc.

### OneDrive/SharePoint Files (10 activities)
UploadFile, DownloadFile, DeleteItem, CreateFolder, FindFilesAndFolders, GetItem, CopyItem, MoveItem, ShareItem, ExportAsPdf

### SharePoint Lists (5 activities)
GetListInfo, GetListItems, AddListItems, UpdateListItem, DeleteListItem

### Planner (11 activities)
CreatePlan, GetPlan, ListPlans, CreateTask, GetTask, ListTasks, UpdateTask, DeleteTask, CreateBucket, DeleteBucket, ListBuckets

### Groups (4 activities)
CreateGroup, DeleteGroup, GetGroup, ListGroups

---

## Critical Gotchas

### Scope (Container)
1. **All activities MUST be inside Office365ApplicationScope** (Classic design) - enforced via HasParentType constraint. Modern portable activities use Integration Service connections instead.
2. **Scope auto-calculates minimum required permissions** from child activities
3. **Token cache stored encrypted** at `%APPDATA%\UiPath\authentication\office365.tokens.msalcache.bin3` (DPAPI encrypted). Other caches: `drive.graph.tokens.msalcache.bin3`, `graph.tokens.msalcache.bin3`

### Authentication
4. **Personal accounts have limited functionality** - no Search API (Microsoft Graph platform limit, enforced server-side), limited Graph endpoints
5. **Shared mailbox uses `UseSharedMailbox` boolean + `Mailbox` property** on the activity (NOT separate ".Shared" scope names as sometimes documented)
6. **User.Read typically required** for Graph /me endpoint
7. **Token refresh automatic** via MSAL library

### Excel Online
8. **Sheet references by name** (not ID)
9. **Range notation must be Excel format** (A1:D10)
10. **ValuesType** affects formula preservation: Values, Formulas, Text
11. **Default sheet name "Sheet1"** assumed if not specified

### OneDrive/SharePoint
12. **ConflictBehavior**: Replace, Fail, Rename for name conflicts
13. **Checkin property** enables version control for SharePoint documents
14. **Metadata DataTable** for adding SharePoint column metadata
15. **Search API not supported for personal accounts** - SupportsSearchApi() checks account type

### Graph API Batching
16. **BatchingService handles max 20 items per batch** (Graph API limit)
17. **ForEach loop optimization** via IO365ForEachBatchingServiceManager
18. **Reduces API calls** for bulk operations

### Mail Governance
19. **Email blocklist enforcement** on SendMail (same as other mail activities)
20. **ConfigLocation property** controls where activity configuration stored

### Multi-Account Support
21. **Account parameter** available on File and Mail activities for delegated access
22. **Defaults to connection user** if not specified
23. **Shared mailbox** specified via connection metadata
