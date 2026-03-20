# CodedWorkflow Base Class Reference

All workflow and test case files inherit from `CodedWorkflow`, which provides built-in methods and service access. The `CodedWorkflow` class is a **partial class** — you can extend it in a Coded Source File (see "Extending CodedWorkflow with Before/After Hooks" below).

## Built-in Methods (available in any workflow/test case via `this`)

| Method | Description |
|--------|-------------|
| `Log(string message, LogLevel level = LogLevel.Info, IDictionary<string, object> additionalLogFields = null)` | Output log messages with optional level and custom fields |
| `Delay(TimeSpan time)` / `Delay(int delayMs)` | Pause execution synchronously |
| `DelayAsync(TimeSpan time)` / `DelayAsync(int delayMs)` | Pause execution asynchronously |
| `BuildClient(string scope = "Orchestrator", bool force = true)` | Build an authenticated `HttpClient` for Orchestrator or custom scopes |
| `GetRunningJobInformation()` | Get info about the current running job (status, progress, parameters, timestamps) |
| `RunWorkflow(string workflowFilePath, IDictionary<string, object> inputArguments = null, TimeSpan? timeout = null, bool isolated = false, InvokeTargetSession targetSession = InvokeTargetSession.Current)` | **Fallback method:** Invoke workflow by string path. Use `workflows.MyWorkflow()` instead when possible |
| `RunWorkflowAsync(...)` | Async version of `RunWorkflow` (same limitations apply) |

## Invoking Other Workflows

**Recommended:** Use the strongly-typed `workflows` property to invoke other workflows in your project:

```csharp
// Invoke workflow with strongly-typed parameters
var result = workflows.ProcessInvoice(invoiceId: "INV-001", amount: 1500.00m);
Log($"Processing completed: {result.success}");
```

**Benefits of `workflows.MyWorkflow()`:**
- **Type-safe:** Compile-time checking of workflow names and parameters
- **IntelliSense:** Auto-completion for workflow names and parameters
- **Refactor-friendly:** Renaming workflows/parameters updates all references
- **Dynamic updates:** Automatically adapts when workflows change

**Default parameters:** Workflows with default parameter values can be invoked with or without those arguments — omitted parameters use their defaults:
```csharp
// If ProcessData has: Execute(string source, int maxRows = 100, bool verbose = false)
workflows.ProcessData(source: "invoices.csv");                          // maxRows=100, verbose=false
workflows.ProcessData(source: "invoices.csv", maxRows: 500);           // verbose=false
workflows.ProcessData(source: "invoices.csv", maxRows: 500, verbose: true);  // all explicit
```

**Fallback (string-based):** For dynamic scenarios where workflow name isn't known at compile time:

```csharp
// Only use when workflow name is determined at runtime
string workflowPath = GetWorkflowPathFromConfig();
var result = RunWorkflow(workflowPath, new Dictionary<string, object>
{
    { "invoiceId", "INV-001" },
    { "amount", 1500.00m }
});
```

## Service Properties (injected based on installed packages)

Services are accessed as properties on `this`: `system.GetAsset(...)`, `excel.ReadRange(...)`, `testing.VerifyExpression(...)`, etc. See the Service-to-Package mapping in SKILL.md.

## Integration Service Connections

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

## The `workflows` Property (Strongly-Typed Workflow Invocation)

The `workflows` property provides strongly-typed access to all workflows in your project:

```csharp
// Invoke workflows with IntelliSense and compile-time checking
var result1 = workflows.ReadInvoices(folderPath: "/data/invoices");
var result2 = workflows.ValidateInvoices(invoices: result1.invoiceList);
var result3 = workflows.PostToERP(validInvoices: result2.validInvoices);
```

Each workflow in your project becomes a method on the `workflows` object with parameters matching the workflow's input arguments and return values matching output arguments. This is the **recommended approach** for invoking workflows.

## The `services` Property

The `services` property provides access to:
- `services.Container` — dependency injection container for resolving custom services
- `OrchestratorClientService` (via `BuildClient`) — Orchestrator API interaction
- `WorkflowInvocationService` (via `RunWorkflow`) — fallback for dynamic workflow invocation
- `OutputLoggerService` (via `Log`) — logging

## Extending CodedWorkflow with Before/After Hooks

To add shared setup/teardown logic that runs before and after ALL test cases, create a base class that implements `IBeforeAfterRun`:

```csharp
// CodedWorkflowBase.cs — Coded Source File (NOT a workflow, NO .cs.json)
using UiPath.CodedWorkflows;

namespace MyProject
{
    public class CodedWorkflowBase : CodedWorkflow, IBeforeAfterRun
    {
        public void Before(BeforeRunContext context)
        {
            Log("Execution started for " + context.RelativeFilePath);
            // Setup: open app, log in, navigate to starting state
        }

        public void After(AfterRunContext context)
        {
            Log("Execution finished for " + context.RelativeFilePath);
            // Teardown: close app, clean up test data
        }
    }
}
```

Then change your workflows/test cases to inherit from `CodedWorkflowBase` instead of `CodedWorkflow`:

```csharp
// TestInvoiceCreation.cs — Test Case
using UiPath.CodedWorkflows;

namespace MyProject
{
    public class TestInvoiceCreation : CodedWorkflowBase  // Inherits from CodedWorkflowBase
    {
        [TestCase]
        public void Execute()
        {
            // Before() runs automatically before this method
            // ... test logic ...
            // After() runs automatically after this method
        }
    }
}
```

This approach ensures `Before()` and `After()` run for all workflows/test cases that inherit from `CodedWorkflowBase`.
