# Microsoft 365 Activities

Reference for the `office365` service from `UiPath.MicrosoftOffice365.Activities` package.

**Required package:** `"UiPath.MicrosoftOffice365.Activities": "[3.6.10]"`

**Auto-imported namespaces:** `UiPath.MicrosoftOffice365.Activities.Api`

**Service accessor:** `office365` (type `IOffice365ConnectionsService`)

## Overview

The Microsoft 365 API provides coded workflow access to **Mail, Calendar, Excel (cloud), OneDrive, and SharePoint** via the Microsoft Graph API. Unlike the `mail` service (COM-based Outlook/IMAP/SMTP), `office365` uses **OAuth tokens managed by Integration Service** — no local Outlook installation needed.

### Architecture

```
office365 (IOffice365ConnectionsService)
├── .Mail(mailConnection)       → IMailService       (send, receive, manage emails)
├── .Calendar(mailConnection)   → ICalendarService   (events, calendars, RSVP)
├── .Excel(excelConnection)     → IExcelService      (cloud Excel workbooks)
├── .OneDrive(oneDriveConn)     → IOneDriveService   (files, folders, sharing)
└── .Sharepoint(oneDriveConn)   → ISharepointService (lists, items)
```

### Prerequisites

1. **Integration Service connections** must be configured in UiPath Automation Cloud
2. Studio auto-generates `ConnectionsManager.cs` and `ConnectionsFactory.cs` in `.codedworkflows/` with typed connection accessors
3. Access connections via the `connections` property on `CodedWorkflow`

### Workflow Pattern

1. Get a connection from `connections.<FactoryName>.<ConnectionName>`
2. Get a sub-service: `office365.Mail(connection)`, `office365.Calendar(connection)`, etc.
3. Call methods on the sub-service

```csharp
var mailConn = connections.O365Mail.My_Workspace_user_company_com;
var mailService = office365.Mail(mailConn);
mailService.SendEmail("recipient@example.com", "Subject", "Body");
```

### Connection Types

| Connection Class | Used By | Factory Name |
|-----------------|---------|--------------|
| `MailConnection` | `Mail()`, `Calendar()` | `O365Mail` |
| `ExcelConnection` | `Excel()` | `Excel` |
| `OneDriveConnection` | `OneDrive()`, `Sharepoint()` | `OneDrive` |

All connection types extend `Office365ConnectionBase` → `ConnectionBase`.

## Reference Files

- **Full API reference** → [api.md](api.md) — all service interfaces, method signatures, parameters, return types, enums, filters, and builder classes
- **Code examples** → [examples.md](examples.md) — complete coded workflow examples for each service
