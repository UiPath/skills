# Google Workspace (GSuite) Activities

Reference for the `google` service from `UiPath.GSuite.Activities` package.

**Required package:** `"UiPath.GSuite.Activities": "[3.6.10]"`

**Auto-imported namespaces:** `UiPath.GSuite.Activities.Api`

**Service accessor:** `google` (type `IGoogleConnectionsService`)

## Overview

The Google Workspace API provides coded workflow access to **Gmail, Google Calendar, Google Drive, Google Sheets, and Google Docs** via Google Workspace APIs. Uses **OAuth tokens managed by Integration Service** — no local installation needed.

### Architecture

```
google (IGoogleConnectionsService)
├── .Gmail(gmailConnection)       → IGmailService          (send, receive, manage emails)
├── .Calendar(gmailConnection)    → IGoogleCalendarService  (events, calendars, RSVP)
├── .Drive(driveConnection)       → IGoogleDriveService     (files, folders, sharing, labels)
├── .Sheets(sheetsConnection)     → IGoogleSheetsService    (spreadsheets, ranges, cells)
└── .Docs(docsConnection)         → IGoogleDocsService      (documents, text, templates)
```

### Prerequisites

1. **Integration Service connections** must be configured in UiPath Automation Cloud (Google OAuth)
2. Studio auto-generates `ConnectionsManager.cs` and `ConnectionsFactory.cs` in `.codedworkflows/` with typed connection accessors
3. Access connections via the `connections` property on `CodedWorkflow`

### Workflow Pattern

1. Get a connection from `connections.<FactoryName>.<ConnectionName>`
2. Get a sub-service: `google.Gmail(connection)`, `google.Calendar(connection)`, etc.
3. Call methods on the sub-service

```csharp
var gmailConn = connections.Gmail.My_Workspace_user_company_com;
var gmailService = google.Gmail(gmailConn);
gmailService.SendEmail("recipient@example.com", "Subject", "Body");
```

### Connection Types

| Connection Class | Used By | Connector Name |
|-----------------|---------|----------------|
| `GmailConnection` | `Gmail()`, `Calendar()` | `Gmail` |
| `DriveConnection` | `Drive()` | `Drive` |
| `SheetsConnection` | `Sheets()` | `GoogleSheets` |
| `DocsConnection` | `Docs()` | `GoogleDocs` |

All connection types extend `GoogleConnectionBase` → `ConnectionBase`.

> **Note:** `Calendar()` takes a `GmailConnection`, not a separate calendar connection.

## Reference Files

- **Full API reference** → [api.md](api.md) — all service interfaces, method signatures, parameters, return types, enums, filters, and builder classes
- **Code examples** → [examples.md](examples.md) — complete coded workflow examples for each service
