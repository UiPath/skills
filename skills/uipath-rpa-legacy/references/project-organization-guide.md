# Project Organization Guide

Best practices for structuring, naming, and organizing legacy UiPath RPA projects.

For project.json schema and package dependencies, see [project-structure.md](./project-structure.md).
For REFramework file structure, see [activity-docs/_REFRAMEWORK.md](./activity-docs/_REFRAMEWORK.md).

---

## 1. Architecture Selection

Before creating any files, decide the project architecture based on what the automation needs to accomplish:

| Scenario | Architecture | Why |
|---|---|---|
| Simple linear task (read file, transform, write) | **Sequence** | No transaction concept, no retry needed, runs once |
| Process multiple independent items with retry/logging | **REFramework** (Performer) | Transaction-based, built-in retry, Orchestrator monitoring |
| Collect data from a source and load it into a queue | **Dispatcher** (simple Sequence) | Reads input, creates queue items — no REFramework needed |
| Collect data AND process it with retry | **Dispatcher + Performer** (two separate projects) | Dispatcher loads the queue, Performer processes with REFramework |
| Multi-step process with distinct phases | **StateMachine** (custom or REFramework) | Explicit states and transitions for complex flows |
| Small utility (< 5 activities, no error handling) | **Single Sequence** | Flat structure, no folders needed |

### Rules

1. **Default to REFramework for production automations** — unless the process is genuinely linear with no retry needs
2. **Dispatcher and Performer are SEPARATE projects** — never combine both in one project
3. **Dispatcher does NOT need REFramework** — a simple Sequence that loops and calls Add Queue Item is sufficient
4. **Ask the user if unclear** — "Will this process multiple items independently?" determines REFramework vs Sequence

---

## 2. Folder Structure

Organize workflows into logical folders based on their purpose:

```
{projectRoot}/
├── project.json
├── Main.xaml                    # Entry point only — orchestrates, does not contain business logic
├── Framework/                   # Framework/infrastructure workflows
│   ├── InitAllSettings.xaml     # Configuration loading
│   ├── InitAllApplications.xaml # App open/login
│   ├── CloseAllApplications.xaml
│   └── KillAllProcesses.xaml
├── BusinessLogic/               # Core automation workflows
│   ├── ProcessInvoice.xaml
│   ├── ValidateInput.xaml
│   └── GenerateReport.xaml
├── Utilities/                   # Reusable helper workflows
│   ├── SendNotificationEmail.xaml
│   ├── LookupCustomer.xaml
│   └── FormatCurrency.xaml
├── Data/
│   ├── Input/                   # Input files (Excel, CSV, config)
│   ├── Output/                  # Generated output files
│   └── Temp/                    # Temporary files (cleared each run)
├── Tests/                       # Test case workflows
│   └── Test_ProcessInvoice_ValidData.xaml
└── Config.xlsx                  # Configuration file (REFramework pattern)
```

### Rules

1. **Main.xaml is the orchestrator only** — it calls sub-workflows, it does NOT contain business logic
2. **Framework/ for infrastructure** — initialization, cleanup, app management
3. **BusinessLogic/ for automation** — the actual work the robot does
4. **Utilities/ for reusable helpers** — email, lookups, formatting, logging wrappers
5. **Data/ with Input/Output/Temp** — never write outputs to Input folder, clear Temp on each run
6. **Tests/ for test cases** — see [testing-guide.md](./testing-guide.md)

### Simple Projects

For small automations (< 5 workflows), a flat structure is acceptable:

```
{projectRoot}/
├── project.json
├── Main.xaml
├── ProcessData.xaml
└── SendResults.xaml
```

Introduce folders when the project reaches 5+ workflows.

---

## 3. Naming Conventions

### Workflow Files

| Convention | Pattern | Examples |
|---|---|---|
| Case | **PascalCase** | `ProcessInvoice.xaml`, `ValidateInput.xaml` |
| Pattern | **VerbNoun** | `SendEmail.xaml`, `ReadConfig.xaml`, `ExtractTableData.xaml` |
| Avoid | Abbreviations, underscores | NOT `ProcInv.xaml`, NOT `process_invoice.xaml` |

### Common Verb Prefixes

| Verb | Meaning |
|---|---|
| `Process` | Execute business logic on an item |
| `Validate` | Check data against rules |
| `Extract` | Pull data from a source |
| `Transform` | Convert data format |
| `Send` | Transmit data (email, API, queue) |
| `Get` | Retrieve a single value or record |
| `Read` | Load data from file/database |
| `Write` | Save data to file/database |
| `Init` | Initialize resources |
| `Close` | Gracefully close resources |
| `Kill` | Force-terminate processes |

### Activity DisplayNames

1. **ALWAYS set meaningful DisplayNames** — `Click "Submit Invoice"` not `Click`
2. **Describe the action and target** — `TypeInto "Invoice Number"`, `Read Range "Sales Data"`
3. **Use quotes for UI element names** — `Click "OK"`, `TypeInto "Username"`
4. **Prefix Assign with the variable** — `Assign totalAmount`, `Assign isValid`

### Variables

| Convention | Pattern | Examples |
|---|---|---|
| Case | **PascalCase** | `InvoiceNumber`, `TotalAmount`, `IsValid` |
| Scope | **Minimize scope** | Declare at the innermost scope where the variable is used |
| Type | **Use specific types** | `String`, `Int32`, `DataTable` — avoid `Object` and `GenericValue` |

### Arguments

| Direction | Prefix | Examples |
|---|---|---|
| In | `in_` | `in_FilePath`, `in_Config`, `in_TransactionItem` |
| Out | `out_` | `out_Result`, `out_DataTable`, `out_ErrorMessage` |
| In/Out | `io_` | `io_RetryCount`, `io_DataTable` |

---

## 4. Single Responsibility & Decomposition

Each workflow should do ONE thing well. This makes workflows testable, reusable, and debuggable.

### Guidelines

1. **One workflow = one task** — `ProcessInvoice.xaml` processes an invoice, it does not also send emails and update databases
2. **Keep workflows under ~30 activities** — if a workflow exceeds this, extract sub-sections into separate workflows
3. **Extract via InvokeWorkflowFile** — call sub-workflows with clear argument interfaces
4. **Each workflow has defined inputs and outputs** — use In/Out arguments, not global variables
5. **One UI scope per workflow file** — if a workflow interacts with two different applications (e.g., SAP and a web portal), split it into two workflows. Mixing Attach Browser for App A and Attach Window for App B in one file makes error recovery and retries unreliable.
6. **Application initialization stays together** — opening an application and logging in belong in the same workflow (e.g., `SAP_Launch.xaml`). Do not separate Open Application and Login into different files — if one fails, the other is useless.
7. **Retrieve credentials where they are used** — call Get Credential inside the workflow that performs the login, not in a parent that passes the SecureString down through multiple InvokeWorkflowFile layers. This avoids exposing credentials across argument boundaries and simplifies the call chain.

### Application-Based File Organization

For automations that interact with multiple applications, organize workflows by application:

```
BusinessLogic/
├── SAP/
│   ├── SAP_Launch.xaml              # Open SAP + login
│   ├── SAP_NavigateToTransaction.xaml
│   ├── SAP_FillForm.xaml
│   └── SAP_ExtractData.xaml
├── WebPortal/
│   ├── WebPortal_Launch.xaml        # Open browser + login
│   ├── WebPortal_SearchInvoice.xaml
│   └── WebPortal_SubmitApproval.xaml
└── Excel/
    ├── ReadInputData.xaml
    └── WriteResults.xaml
```

The `AppName_Action.xaml` pattern makes it immediately clear which application a workflow targets and what it does.

### Decomposition Example

**Bad: One monolithic workflow**
```
Main.xaml (200 activities)
  ├── Read Excel
  ├── Loop rows
  │   ├── Validate data
  │   ├── Login to portal
  │   ├── Enter invoice
  │   ├── Submit
  │   └── Log result
  ├── Send summary email
  └── Close applications
```

**Good: Decomposed into focused workflows**
```
Main.xaml (orchestrator — 10 activities)
  ├── InvokeWorkflowFile: Framework/InitAllSettings.xaml
  ├── InvokeWorkflowFile: Framework/InitAllApplications.xaml
  ├── InvokeWorkflowFile: BusinessLogic/ReadInputData.xaml
  ├── For Each Row:
  │   ├── InvokeWorkflowFile: BusinessLogic/ValidateInput.xaml
  │   └── InvokeWorkflowFile: BusinessLogic/ProcessInvoice.xaml
  ├── InvokeWorkflowFile: Utilities/SendSummaryEmail.xaml
  └── InvokeWorkflowFile: Framework/CloseAllApplications.xaml
```

---

## 5. Config.xlsx Management

The REFramework pattern uses `Config.xlsx` as a centralized configuration file. Apply this pattern to any production automation.

### Three Sheets

| Sheet | Purpose | Examples |
|---|---|---|
| **Settings** | Values that change between environments | URLs, file paths, queue names, thresholds |
| **Constants** | Values that never change | Timeout values, format strings, static labels |
| **Assets** | Names of Orchestrator assets to fetch at runtime | Credentials, API keys, environment-specific secrets |

### Access Pattern

After `InitAllSettings.xaml` loads the config:

```vb
' Read a setting
in_Config("OrchestratorQueueName").ToString()

' Read with default value
If(in_Config.ContainsKey("MaxRetryNumber"), CInt(in_Config("MaxRetryNumber")), 3)
```

### No Hardcoded Values Rule

**NEVER hardcode** these in workflows:

| Value Type | Where It Goes |
|---|---|
| URLs (portal, API, web app) | Config.xlsx → Settings |
| File paths (input, output, temp) | Config.xlsx → Settings |
| Credentials (username, password) | Orchestrator Credential Asset → Config.xlsx Assets sheet |
| API keys, tokens | Orchestrator Credential Asset → Config.xlsx Assets sheet |
| Thresholds, limits | Config.xlsx → Settings or Constants |
| Email recipients | Config.xlsx → Settings |
| Queue names | Config.xlsx → Settings |
| Application paths | Config.xlsx → Settings |

**Exceptions:** Format strings (`"yyyy-MM-dd"`), literal constants that never change across any environment (`";"` as separator), and log messages.

---

## 6. Library Projects

Libraries are reusable packages of workflows published as NuGet packages. Other projects consume them as activity packages.

### When to Create a Library

1. **Shared business logic** — the same validation/processing logic used across 2+ projects
2. **Common integrations** — wrappers around specific applications (SAP, portal, database)
3. **Standard practices** — email notification templates, logging wrappers, error handling utilities
4. **UI automation wrappers** — Object Repository + workflows for a specific application

### When NOT to Create a Library

1. **Project-specific logic** — automation logic used by only one project
2. **Rapidly changing interfaces** — unstable APIs or frequently redesigned UIs (versioning overhead too high)
3. **Tightly coupled workflows** — logic that depends on specific project state or global variables

### Library Project Configuration

In `project.json`, set `outputType` to `"Library"`:

```json
{
  "designOptions": {
    "outputType": "Library"
  }
}
```

See [project-structure.md](./project-structure.md) for the full Library project.json template.

### Key Differences from Process Projects

| Aspect | Process | Library |
|---|---|---|
| `outputType` | `"Process"` | `"Library"` |
| Entry point | `Main.xaml` required | No Main.xaml — all workflows are callable |
| Workflow visibility | N/A | **Public** (exposed as activities) or **Private** (internal helpers) |
| Arguments | Used for workflow communication | Become **activity properties** when consumed |
| Publishing | Deployed to Orchestrator | Published to **NuGet feed** |

### Semantic Versioning

| Version Change | When | Example |
|---|---|---|
| **Major** (X.0.0) | Breaking changes — renamed arguments, removed workflows, changed behavior | 1.0.0 → 2.0.0 |
| **Minor** (0.X.0) | New features — new workflows, new optional arguments | 1.0.0 → 1.1.0 |
| **Patch** (0.0.X) | Bug fixes — selector fix, logic correction, no interface change | 1.0.0 → 1.0.1 |

### Library Naming

`[Company].[Domain].[Functionality]` — e.g., `Acme.Finance.InvoiceProcessing`, `Acme.Email.Notifications`

### Library Rules

1. **NEVER use ContinueOnError=True** — library consumers cannot know which errors you swallow. Always propagate exceptions.
2. **Throw meaningful exceptions** — `BusinessRuleException("Invoice amount negative: " & amount)` not `Exception("Error")`
3. **Don't swallow System Exceptions** — let them propagate so the consumer can retry/handle
4. **Design arguments as the public API** — clear names, specific types (not Object), In/Out directions as needed
5. **Test in isolation before publishing** — create a test harness project that invokes every public workflow
6. **Pin versions in production** — consumers should use exact version constraints `[1.2.3]`, not ranges

### Library Design Patterns

| Pattern | Purpose | Example |
|---|---|---|
| **Wrapper** | Wrap an external service with retry/error handling | `SendEmailWithRetry.xaml` wrapping SMTP activities |
| **Connector** | Encapsulate all interactions with one system | `SAPConnector` library with Login, GetOrder, CreateInvoice workflows |
| **Data Access** | Centralize database/API queries | `CustomerDB` library with GetCustomer, UpdateStatus workflows |
| **Framework** | Provide scaffolding for common patterns | Custom REFramework variant for the organization |

### Feed Management

1. **Publish to a shared NuGet feed** — Orchestrator tenant feed, host feed, or custom NuGet server
2. **Test library upgrades in Dev first** — never upgrade directly in production
3. **Keep older versions available** — consumers may need to roll back
4. **Restrict publishing permissions** — only maintainers can publish new versions
