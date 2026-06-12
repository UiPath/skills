# CodedWorkflow Base Class Reference

All workflow and test case files inherit from `CodedWorkflow`. The class is a **partial class** — extend it in a Coded Source File (see "Extending CodedWorkflow with Before/After Hooks" below). Built-in method surface, service-to-package mapping, and workflow invocation: [critical-rules-coded.md](critical-rules-coded.md). This file covers Integration Service connections, the `services` property, job context (`IRunningJobInformation`), and Before/After hooks. Services are accessed as properties on `this`: `system.GetAsset(...)`, `excel.ReadRange(...)`, `testing.VerifyExpression(...)`, etc.

## Integration Service Connections

> **Two IS connection patterns exist in coded workflows.** This section covers first-party package connections (Office365, GSuite) where Studio auto-generates `ConnectionsManager.cs` / `ConnectionsFactory.cs`. For raw IS connectors (Jira, Salesforce, custom) that use `CodedConnectorConfiguration` + agent-generated `ISConnections.cs`, see [integration-service-guide.md](integration-service-guide.md).

When packages that use Integration Service connections are installed (e.g. `UiPath.MicrosoftOffice365.Activities`, `UiPath.GSuite.Activities`), Studio auto-generates two files in `.codedworkflows/`:

- **`ConnectionsManager.cs`** — Exposes a typed property for each connection category (e.g. `O365Mail`, `Excel`, `OneDrive`, `Gmail`, etc.)
- **`ConnectionsFactory.cs`** — Contains factory classes with typed properties for each configured connection instance

These are injected via the `connections` property on `CodedWorkflow`.

### How It Works

1. **Configure connections** in UiPath Automation Cloud → Integration Service
2. **Studio detects them** and generates typed accessors in `.codedworkflows/`
3. **Access in code** via `connections.<FactoryName>.<ConnectionName>`

### Example: ConnectionsManager.cs (auto-generated)

```csharp
public class ConnectionsManager
{
    public ExcelFactory Excel { get; set; }
    public O365MailFactory O365Mail { get; set; }
    public OneDriveFactory OneDrive { get; set; }

    public ConnectionsManager(ICodedWorkflowsServiceContainer resolver)
    {
        Excel = new ExcelFactory(resolver);
        O365Mail = new O365MailFactory(resolver);
        OneDrive = new OneDriveFactory(resolver);
    }
}
```

### Example: ConnectionsFactory.cs (auto-generated)

```csharp
public class O365MailFactory
{
    // Connection name derived from Integration Service display name
    public MailConnection My_Workspace_user_company_com { get; set; }

    public O365MailFactory(ICodedWorkflowsServiceContainer resolver)
    {
        My_Workspace_user_company_com = new MailConnection("9e26a554-...", resolver);
    }
}

public class OneDriveFactory
{
    public OneDriveConnection Shared_tenant_onmicrosoft_com { get; set; }

    public OneDriveFactory(ICodedWorkflowsServiceContainer resolver)
    {
        Shared_tenant_onmicrosoft_com = new OneDriveConnection("22530bcf-...", resolver);
    }
}
```

### Usage Pattern

```csharp
// Step 1: Get the connection from the auto-generated factory
var mailConnection = connections.O365Mail.My_Workspace_user_company_com;

// Step 2: Get a sub-service from the connection-based service
var mailService = office365.Mail(mailConnection);

// Step 3: Call methods on the sub-service
mailService.SendEmail("recipient@example.com", "Subject", "Body");
```

### Connection Types by Package

| Package | Connection Class | Factory Name | Used By |
|---------|-----------------|--------------|---------|
| `UiPath.MicrosoftOffice365.Activities` | `MailConnection` | `O365Mail` | `office365.Mail()`, `office365.Calendar()` |
| `UiPath.MicrosoftOffice365.Activities` | `ExcelConnection` | `Excel` | `office365.Excel()` |
| `UiPath.MicrosoftOffice365.Activities` | `OneDriveConnection` | `OneDrive` | `office365.OneDrive()`, `office365.Sharepoint()` |
| `UiPath.GSuite.Activities` | `GmailConnection` | `Gmail` | `google.Gmail()`, `google.Calendar()` |
| `UiPath.GSuite.Activities` | `DriveConnection` | `GoogleDrive` | `google.Drive()` |
| `UiPath.GSuite.Activities` | `SheetsConnection` | `GoogleSheets` | `google.Sheets()` |
| `UiPath.GSuite.Activities` | `DocsConnection` | `GoogleDocs` | `google.Docs()` |

### Important Notes

- Connection names in the factory are sanitized versions of the Integration Service display name (spaces/special chars replaced with `_`)
- The connection ID (GUID) is embedded in the factory — it references the specific Integration Service connection
- If a connection is **not authorized** or the token is expired, you get `ConnectionHttpException: Connection [...] failed to authorize` at runtime — re-authorize in Automation Cloud → Integration Service
- The `connections` property is always available on `CodedWorkflow` regardless of installed packages, but the factory properties (`.O365Mail`, `.OneDrive`, etc.) only exist when the corresponding package is installed and connections are configured

## The `services` Property

The `services` property provides access to:
- `services.Container` — dependency injection container for resolving custom services
- `OrchestratorClientService` (via `BuildClient`) — Orchestrator API interaction
- `WorkflowInvocationService` (via `RunWorkflow`) — fallback for dynamic workflow invocation
- `OutputLoggerService` (via `Log`) — logging

## IRunningJobInformation Properties

`GetRunningJobInformation()` returns an `IRunningJobInformation` instance (from `UiPath.Robot.Activities.Api`). Key properties:

| Property | Type | Description |
|----------|------|-------------|
| `JobId` | `Guid` | Current job identifier |
| `ProcessName` | `string` | Running process name |
| `ProcessVersion` | `string` | Running process version |
| `OrganizationId` | `string` | Organization identifier |
| `TenantId` | `string` | Tenant identifier |
| `TenantName` | `string` | Tenant display name |
| `FolderId` | `long?` | Orchestrator folder numeric ID |
| `FolderName` | `string` | Orchestrator folder display name |
| `FolderKey` | `Guid` | Orchestrator folder GUID key |
| `RobotName` | `string` | Executing robot name |
| `UserEmail` | `string` | Logged-in user's email |
| `InitiatedBy` | `string` | What started the job (`"Orchestrator"`, `"Studio"`, `"Assistant"`, etc.) |

### Usage Example

```csharp
var jobInfo = GetRunningJobInformation();
Log($"Org: {jobInfo.OrganizationId}, Tenant: {jobInfo.TenantName}, Folder: {jobInfo.FolderName}");
```

## Before/After Hooks (IBeforeAfterRun)

Any class inheriting from `CodedWorkflow` can implement `IBeforeAfterRun` to add setup/teardown logic. Two approaches:

**Per-file:** Implement directly on a workflow or test case — hooks run only for that file:
```csharp
public class TestLoginFlow : CodedWorkflow, IBeforeAfterRun
{
    public void Before(BeforeRunContext context) { Log("Starting " + context.RelativeFilePath); }
    public void After(AfterRunContext context) { Log("Finished " + context.RelativeFilePath); }

    [TestCase]
    public void Execute() { /* Before() already ran, After() runs after */ }
}
```

**Project-wide:** Use a `partial class CodedWorkflow` — hooks apply to every workflow and test case:
```csharp
// CodedWorkflowHooks.cs — Coded Source File (no entry point)
using UiPath.CodedWorkflows;

namespace MyProject
{
    public partial class CodedWorkflow : IBeforeAfterRun
    {
        public void Before(BeforeRunContext context) { Log("Starting " + context.RelativeFilePath); }
        public void After(AfterRunContext context) { Log("Finished " + context.RelativeFilePath); }
    }
}
```

## Extending CodedWorkflow with Partial Classes

The auto-generated `CodedWorkflow` is a `partial class`. You can extend it to add shared methods, properties, or constants available to all workflows and test cases — with or without hooks:

```csharp
// CodedWorkflowExtensions.cs — Coded Source File (no entry point)
using UiPath.CodedWorkflows;

namespace MyProject
{
    public partial class CodedWorkflow
    {
        protected string GetEnvironmentUrl()
        {
            var env = system.GetAsset("Environment").ToString();
            return env == "prod" ? "https://app.example.com" : "https://staging.example.com";
        }
    }
}
```

### Key Points

- **`IBeforeAfterRun`** is an interface — any `CodedWorkflow`-derived class can implement it
- **`partial class CodedWorkflow`** is a C# feature — extends the auto-generated class for all files in the project
- **They combine:** use `partial class CodedWorkflow : IBeforeAfterRun` when you want hooks on every file
- **Use `IBeforeAfterRun` on individual files** when only specific workflows/test cases need setup/teardown
- **Use `partial class CodedWorkflow`** (without hooks) to add shared methods, properties, or constants
- **Context objects** (`BeforeRunContext`, `AfterRunContext`) provide `RelativeFilePath`, `WorkflowFilePath`, etc.
- **After() runs even on failure** — guaranteed cleanup

### When to Use Which

| Scenario | Pattern |
|----------|---------|
| One test case needs its own setup/teardown | `IBeforeAfterRun` on the class |
| All test cases share the same setup/teardown | `partial class CodedWorkflow : IBeforeAfterRun` |
| Shared helper methods for all workflows | `partial class CodedWorkflow` (no hooks) |
| All of the above | Combine patterns in one or more partial files |

Code templates: [assets/before-after-hooks-template.md](../../assets/before-after-hooks-template.md)
