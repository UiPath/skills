# CodedWorkflow Base Class Reference

All workflow and test case files inherit from `CodedWorkflow`, which provides built-in methods and service access. The `CodedWorkflow` class is a **partial class** — you can extend it in a Coded Source File (see "Extending CodedWorkflow with Before/After Hooks" below).

## Built-in Methods (available in any workflow/test case via `this`)

| Method | Description |
|--------|-------------|
| `Log(string message, LogLevel level = LogLevel.Info, IDictionary<string, object> additionalLogFields = null)` | Output log messages with optional level and custom fields. Valid `LogLevel` values: `Trace`, `Verbose`, `Info`, `Warn`, `Error`, `Fatal`. Note: `LogLevel.Warning` does not exist — use `LogLevel.Warn` |
| `Delay(TimeSpan time)` / `Delay(int delayMs)` | Pause execution synchronously |
| `DelayAsync(TimeSpan time)` / `DelayAsync(int delayMs)` | Pause execution asynchronously |
| `BuildClient(string scope = "Orchestrator", bool force = true)` | Build an authenticated `HttpClient` for Orchestrator or custom scopes |
| `GetRunningJobInformation()` | Returns `IRunningJobInformation` with current job context: job ID, process name/version, tenant, folder, organization, robot name, and more (see [IRunningJobInformation](#irunningjobinformation-properties) below) |
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

> **Return value:** `RunWorkflow` returns `IDictionary<string, object>`. Argument direction is determined by the `Execute` method signature:
>
> - **Single return value** (`public string Execute(int a, int b)`) — the result is stored under the key `"Output"`. Access it as `result["Output"]`.
> - **Multiple outputs via tuple** (`public (string a, string b) Execute()`) — each tuple member becomes a separate key: `result["a"]`, `result["b"]`. These are Out arguments.
> - **InOut arguments** — when a parameter name appears in both the input parameters and the return tuple, it is an InOut argument. Example: `public (string a, string b) Execute(string b, int c)` — `a` is Out, `b` is InOut (same name in input and output), `c` is In. The input and output types of an InOut argument must be identical — a mismatch fails analyzer rule ST-REL-001 (Error) at `analyze`/`build`/`pack`.
>
> For same-project workflows, prefer the type-safe `workflows.MyWorkflow()` property — it returns the declared return type directly and avoids this dictionary lookup.

## Service Properties (injected based on installed packages)

Services are accessed as properties on `this`: `system.GetAsset(...)`, `excel.ReadRange(...)`, `testing.VerifyExpression(...)`, etc. See the Service-to-Package mapping in SKILL.md.

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

Code templates: [assets/codedworkflow-template.md § Before/After Hooks Templates](../../assets/codedworkflow-template.md#beforeafter-hooks-templates)

---

## Inspect NuGet Package Tool (On-Demand API Discovery)

Use this when `.local/docs/packages/<PackageId>/coded/coded-api.md` doesn't cover an API, when the user has a different package version, or when you need ground-truth method signatures. Bundled fallback: `references/activity-docs/<PackageId>/<closest-version>/coded/` in this skill ships per-package coded docs (`<service>.md` overview, `api.md` / `windows-api.md` + `portable-api.md` signatures, `examples.md`) for the major UiPath packages — read those when `.local/docs` has no coded docs for the package, picking the version folder closest to the installed one.

### How to Run

The `packages inspect` verb is built into the UiPath CLI. No separate build step is needed.

#### Inspect a package from a NuGet feed
```bash
uip rpa packages inspect --package-name <PackageName> --package-version <Version> [--feed-url <NuGetV3FeedUrl>]
```

When `--feed-url` is omitted, the tool downloads from the UiPath Official feed first and falls back to nuget.org.

#### Inspect a local .nupkg file
```bash
uip rpa packages inspect --nupkg-path <path/to/package.nupkg>
```

Use this when the package is already cached locally (e.g. from a private feed) or when you have a `.nupkg` file on disk.

### Examples

```bash
# Inspect Excel activities from UiPath feed
uip rpa packages inspect --package-name UiPath.Excel.Activities --package-version 3.3.1
# Inspect a specific version the user has
uip rpa packages inspect --package-name UiPath.System.Activities --package-version 25.12.2
# Inspect from a custom feed
uip rpa packages inspect --package-name MyPackage --package-version 1.0.0 --feed-url https://my-feed/v3/index.json
# Inspect third-party package from nuget.org
uip rpa packages inspect --package-name CsvHelper --package-version 33.0.1
# Inspect a local .nupkg file directly
uip rpa packages inspect --nupkg-path ~/.nuget/packages/csvhelper/33.0.1/csvhelper.33.0.1.nupkg
```

### Finding the Latest Stable Version

When you don't know the version of a UiPath package, query the UiPath Official NuGet feed to find the latest stable (non-preview) version:

```bash
UIPATH_FEED="https://uipath.pkgs.visualstudio.com/5b98d55c-1b14-4a03-893f-7a59746f1246/_packaging/1c781268-d43d-45ab-9dfc-0151a1c740b7/nuget/v3/flat2" && bun -e "const p=process.argv[1];const r=await fetch(p+'/index.json');const d=await r.json();console.log(d.versions.find(v=>v.indexOf('preview')<0))" "$UIPATH_FEED/<package-name-lowercase>"
```

Replace `<package-name-lowercase>` with the package ID in lowercase (e.g. `uipath.microsoftoffice365.activities`).

**Examples:**
```bash
# Latest stable UiPath.MicrosoftOffice365.Activities → 3.6.10
... "$UIPATH_FEED/uipath.microsoftoffice365.activities"

# Latest stable UiPath.System.Activities → 25.12.2
... "$UIPATH_FEED/uipath.system.activities"
```

**Notes:**
- The feed returns versions in descending order (newest first); the one-liner picks the first non-preview entry
- Package names in the URL **must be lowercase**
- This feed is public for version listing but requires authentication for package downloads (Studio handles this automatically when restoring dependencies)

---

### When to Use

- **First**, check for pre-generated coded API docs at `{projectRoot}/.local/docs/packages/{PackageId}/coded/coded-api.md` — these contain service API signatures and usage for coded workflows. Use `packages inspect` only when these docs are missing or insufficient.
- You encounter an unknown activity/method not in reference files
- The user's `project.json` has a different package version than reference docs
- You need exact method signatures, parameter types, or enum values
- You're unsure about the correct API and want to verify against the actual package
- You need to find and evaluate a third-party NuGet package for use in a coded workflow

### Output

Structured markdown listing all public types, methods, properties, enums, delegates, and events from the package DLLs. The tool performs framework-aware DLL selection and recursive dependency resolution (up to depth 2).

### Requirements & Notes

- Requires `uip` to be available on PATH
- Downloads from the UiPath Official feed first, then falls back to nuget.org — so it works with **any** NuGet package, not just UiPath ones
- The tool automatically checks the local NuGet cache at `~/.nuget/packages/` when a package cannot be downloaded
- For local `.nupkg` files (e.g. packages from private feeds already cached locally), use `--nupkg-path` to skip the download entirely
- Some packages are metapackages with no DLLs (e.g. `Humanizer`). If you get "No DLLs found", try the `.Core` sub-package (e.g. `Humanizer.Core`)

---

## Third-Party NuGet Packages

When a user needs functionality that **no UiPath built-in activity provides** (e.g. PDF generation, barcode reading, advanced math, specific file formats), find and use a third-party NuGet package.

### Decision Flow

1. **Consider whether a built-in activity or plain .NET is the better fit** — prefer activities for Orchestrator integration, UI automation, and document handling; prefer .NET for data transforms, HTTP to external APIs, parsing, etc.
2. **If no built-in activity fits** — search for a well-known .NET NuGet package that provides the capability
3. **Inspect the package** — run the `uip rpa packages inspect` command with the appropriate flags in order to get exact API signatures before writing code
4. **Install it** — run `uip rpa packages install --project-dir "<PROJECT_DIR>" --packages 'id=<PACKAGE_ID>,version=<VERSION>' --output json`. Omit `,version=<VERSION>` to resolve the latest compatible. Do NOT hand-edit `project.json` `dependencies`. **There is no `uip rpa add-dependency` command.**
5. **Write C# code using the package** — use the package's API directly in the `Execute` method (no service proxy needed — just `using` + direct API calls)

### How Third-Party Packages Differ from UiPath Activity Packages

- UiPath packages provide services on the `CodedWorkflow` base class (e.g. `excel.ReadRange(...)`)
- Third-party packages are used as **plain C# libraries** — instantiate classes, call methods directly
- They do NOT get a service property on `CodedWorkflow`
- Add them to `project.json` `dependencies` just like UiPath packages: `"PackageName": "[version]"`

### Example — Using CsvHelper in a Coded Workflow

```csharp
using System;
using System.Globalization;
using System.IO;
using CsvHelper;
using UiPath.CodedWorkflows;

namespace MyProject
{
    public class ProcessCsv : CodedWorkflow
    {
        [Workflow]
        public void Execute(string inputPath)
        {
            using var reader = new StreamReader(inputPath);
            using var csv = new CsvReader(reader, CultureInfo.InvariantCulture);
            var records = csv.GetRecords<dynamic>().ToList();
            Log($"Read {records.Count} records from CSV");
        }
    }
}
```

With `project.json` dependency:
```json
{
  "dependencies": {
    "CsvHelper": "[33.0.1]"
  }
}
```

### How to Search for Packages

- Use web search to find the best .NET NuGet package for the task
- Look for packages with high download counts, active maintenance, and .NET 6+ support
- Common choices:
  - `CsvHelper` (CSV parsing)
  - `QuestPDF` (PDF generation)
  - `ClosedXML` (Excel without UiPath)
  - `HtmlAgilityPack` (HTML parsing)
  - `Dapper` (database access)
  - `RestSharp` (REST APIs)
  - `Polly` (retry/resilience patterns)
  - `Newtonsoft.Json` (JSON parsing - already included in most projects)
- After identifying a package, run the `uip rpa packages inspect` command to discover exact APIs before coding
