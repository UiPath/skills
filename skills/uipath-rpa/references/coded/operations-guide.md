# Operations Guide

Detailed step-by-step procedures for all operations on UiPath coded workflow projects.

## Initialize a New Coded Project

Use this procedure ONLY when the user explicitly asked for a coded project ("coded", ".cs", "C# workflow"). For ambiguous "create a workflow" / "automate X" requests, default to XAML — see [../coded-vs-xaml-guide.md](../coded-vs-xaml-guide.md).

There is no "create a coded project" command. `init` always scaffolds XAML; coded mode is a post-scaffold step (add `.cs` files, update `entryPoints`). For the canonical `init` documentation — flag semantics, scaffolding behavior, how `--expression-language` works — see [../environment-setup.md § Step 0.3: Creating a New Project](../environment-setup.md#step-03-creating-a-new-project).

### Steps

**1. Scaffold the project** following [../environment-setup.md § Step 0.3](../environment-setup.md#step-03-creating-a-new-project). The command is the same as for an XAML project — the scaffolding is XAML either way. The result is a project with `project.json`, `project.uiproj`, the template's XAML root file (`Main.xaml` / `TestCase.xaml`), and all required metadata directories.

**2. Read the scaffolded files — do NOT overwrite blindly:**

After `init` succeeds, read the generated files to understand the defaults:
```
Read: <PROJECT_DIR>/project.json
Read: <PROJECT_DIR>/Main.xaml          # or TestCase.xaml for test projects
```
`project.json` contains valid defaults (correct schema version, runtime options, dependencies) that you should build on rather than replace. Leave the scaffolded XAML in place — `.xaml` and `.cs` workflows coexist freely in the same project.

**3. Analyze the task and plan the file structure:**
- How many workflow files? (one per logical step or responsibility)
- Are there shared data models or helpers? (create Coded Source Files)
- Is this a test project? (create test cases with Given/When/Then structure, optionally add Before/After hooks)
- See [../project-structure-guide.md](../project-structure-guide.md) for guidelines

**4. Add required dependencies to `project.json`** based on the Service-to-Package mapping. Edit the existing `project.json` — do NOT rewrite the entire file.

**5. Add `.cs` workflow / test case / source files:**
- Generate `.cs` files (workflows, test cases, source files) — respect the four Error-severity coded analyzer rules while authoring: [§ Coded Workflow Analyzer Rules](#coded-workflow-analyzer-rules)
- For each `.cs` **workflow** file, add an entry to `entryPoints` in `project.json` (**Process projects only** — Tests and Library projects do NOT use `entryPoints`). The existing scaffolded XAML entry can stay alongside.
- For each `.cs` **test case** file, add an entry to `designOptions.fileInfoCollection` in `project.json` with `editingStatus: "InProgress"`, `testCaseType: "TestCase"`, `publishAsTestCase: true`. Test cases do NOT go in `entryPoints` regardless of project type.
- If test project and shared setup is needed, create a `partial class CodedWorkflow` source file that implements `IBeforeAfterRun` (see before-after-hooks-template.md)

**6. Validate each file** (Critical Rule #14) — run the validation loop on every `.cs` file until it compiles cleanly

> **Why `init` instead of manual files?** It generates correct schema versions, metadata directories, and default dependencies — manual creation risks subtle errors. See [json-template.md](../../assets/json-template.md) for reference-only templates.

## Add a Workflow File to Existing Project

**Steps:**
1. Read existing `project.json` to get project name (for namespace), `outputType`, and current entry points
2. Create the new `.cs` file:
   - Use the project name as namespace
   - Class name = file name (without .cs). The class name must **not** equal the project name — a class named like the project's default namespace fails analyzer rule ST-NMG-017 (Error) at `analyze`/`build`/`pack`. When the natural name collides (e.g. workflow `Invoicing` in project `Invoicing`), pick a variant like `InvoicingWorkflow`
   - Inherit from `CodedWorkflow`
   - Add `[Workflow]` attribute on the entry-point method. Method name does not have to be `Execute` — any name works. `Execute` is convention; keep it unless the user asks otherwise. **One `[Workflow]`/`[TestCase]` attribute per file** — a second one in the same file fails analyzer rule ST-DBP-010 (Error)
   - Add appropriate `using` statements based on which activities are needed
3. Argument direction is determined by the entry-point method signature. Single-return OutArgument is named **`"Output"`**. Tuple returns produce one OutArgument per element, named after the element. A tuple element name matching an input parameter name — or, for single returns, an input parameter literally named `"Output"` — collapses into one **`InOutArgument`**:

   | Signature | Example | Argument directions |
   |-----------|---------|---------------------|
   | Single return | `public string Execute(int a, int b)` | `a` = In, `b` = In, return = Out named `"Output"` |
   | Tuple return | `public (string Test, int A) Execute()` | `Test` = Out, `A` = Out |
   | Tuple + name collision | `public (string a, string b) Execute(string b, int c)` | `a` = Out, `b` = InOut (same name in input and tuple), `c` = In |
   | Single return + `Output` input | `public string Execute(string Output, int c)` | `Output` = InOut (input named `"Output"` collides with implicit return name), `c` = In |
   | No return | `public void Execute(string input)` | `input` = In |

   > **NEVER use C# `out` or `ref` keywords** on `Execute` parameters — the auto-generated `*+Activity.cs` wrapper does not handle them correctly. Symptoms: analyzer error ST-USG-017 at `analyze`/`build`/`pack`, compile error `CS1620`, or runtime `Using 'out' and 'ref' modifiers is not allowed for Coded Workflows executions.` Studio regenerates the wrapper on every save, so manual fixes are reverted. Use return values or tuples for outputs instead.

   > **InOut collapse requires matching types.** When a name collision turns a parameter into an `InOutArgument` (rows 3–4 above), the input parameter type and the returned type must be identical — a mismatch (e.g. input `string b` vs tuple element `int b`) fails analyzer rule ST-REL-001 (Error) at `analyze`/`build`/`pack`.
4. Update `project.json` (**Process projects only** — skip `entryPoints` for Tests and Library projects):
   - Add new entry to `entryPoints` array with `filePath`, unique `uniqueId`, `input`, and `output` definitions
   - If the workflow has parameters, define them in `input`/`output` with `name`, `type`, and `required`
5. **Validate the file** — Run the validation loop (Critical Rule #14) until the file compiles cleanly before proceeding

## Add a Test Case File

Coded test cases automate and validate application behavior using a structured **Given-When-Then** (Arrange/Act/Assert) pattern. They inherit from `CodedWorkflow` just like workflows, but use the `[TestCase]` attribute.

**Test cases can exist in any project type** — not just `"Tests"` projects. It's common to add test cases directly inside a `"Process"` project for testing purposes.

**Steps:**
1. Read existing `project.json` to get project name, `outputType`, and current entry points
2. Create the `.cs` file following the same rules as workflows, but with:
   - `[TestCase]` attribute instead of `[Workflow]` on the entry-point method (method name does not have to be `Execute` — any name works; keep `Execute` unless the user asks otherwise)
   - Structured code in three phases: **Arrange**, **Act**, **Assert**
3. Update `project.json`:
   - Add entry to `entryPoints` array (**Process projects only** — skip `entryPoints` for Tests and Library projects)
   - Add entry to `designOptions.fileInfoCollection` with `editingStatus: "InProgress"`, `testCaseType: "TestCase"`, `publishAsTestCase: true`
4. For data-driven tests, add default parameter values: `public void Execute(string browser = "chrome.exe")`
   - Optionally create `.variations/` data file for parameterized test data
   - For CLI-based data sources (variations files, Test Data Queues, Data Service), see [../testing-guide.md § Data-Driven Testing](../testing-guide.md)
5. **Validate the file** — Run the validation loop (Critical Rule #14) until the file compiles cleanly before proceeding
6. **Update `editingStatus`** — When the user asks to mark a test case as ready/publishable, update its `editingStatus` in `fileInfoCollection` from `"InProgress"` to `"Publishable"`. Do NOT change this automatically — only when explicitly requested

**Test case structure — Given/When/Then:**

For test cases that validate non-UI logic (most common — call workflows and assert on results):
```csharp
using System;
using UiPath.CodedWorkflows;

namespace MyTestProject
{
    public class TestInvoiceCreation : CodedWorkflow
    {
        [TestCase]
        public void Execute()
        {
            // GIVEN (Arrange) — set up test data
            string invoiceId = "INV-001";
            decimal amount = 1500.00m;
            Log($"Testing invoice creation for {invoiceId}");

            // WHEN (Act) — call the workflow under test
            var result = workflows.CreateInvoice(invoiceId: invoiceId, amount: amount);

            // THEN (Assert) — verify expected results
            testing.VerifyExpression(result.success, "Invoice creation should succeed");
            testing.VerifyAreEqual("POSTED", result.status, "Invoice should be in POSTED status");
        }
    }
}
```

For test cases that validate UI behavior (requires descriptors from the Object Repository — read `ObjectRepository.cs` first and add `using <ProjectNamespace>.ObjectRepository;`):
```csharp
using System;
using UiPath.CodedWorkflows;
using UiPath.UIAutomationNext.API.Contracts;
using MyTestProject.ObjectRepository;

namespace MyTestProject
{
    public class TestInvoiceFormUI : CodedWorkflow
    {
        [TestCase]
        public void Execute()
        {
            // GIVEN (Arrange) — open the application to the invoice form
            // uiAutomation.Open() returns a screen handle; all interactions go through it
            var formScreen = uiAutomation.Open(Descriptors.InvoiceApp.CreateInvoiceForm);
            Log("Navigated to invoice creation form");

            // WHEN (Act) — fill in details and submit
            formScreen.TypeInto(Descriptors.InvoiceApp.CreateInvoiceForm.InvoiceNumberField, "INV-001");
            formScreen.TypeInto(Descriptors.InvoiceApp.CreateInvoiceForm.AmountField, "1500.00");
            formScreen.Click(Descriptors.InvoiceApp.CreateInvoiceForm.SubmitButton);

            // THEN (Assert) — attach to confirmation screen and verify message
            var confirmScreen = uiAutomation.Attach(Descriptors.InvoiceApp.ConfirmationScreen);
            string message = confirmScreen.GetText(Descriptors.InvoiceApp.ConfirmationScreen.MessageLabel);
            testing.VerifyExpression(message.Contains("successfully"), "Confirmation message should indicate success");
        }
    }
}
```

**Assertion methods (via `testing` service):**
- `testing.VerifyExpression(bool condition, string outputMessage = null)` — assert a boolean condition is true
- `testing.VerifyAreEqual<T>(T expected, T actual, string outputMessage = null)` — assert equality
- `testing.VerifyAreNotEqual<T>(T notExpected, T actual, string outputMessage = null)` — assert inequality
- `testing.VerifyContains(string full, string part, string outputMessage = null)` — assert string containment
- `testing.VerifyRange(double value, double min, double max, string outputMessage = null)` — assert value in range
- `testing.SetTestDataQueueItems(...)` — set up test data from data queues
- `testing.GetTestDataQueueItem(...)` — get next test data item

**Test cases can invoke other workflows:**
```csharp
[TestCase]
public void Execute()
{
    // Arrange — call a setup workflow using strongly-typed invocation
    var setupResult = workflows.SetupTestData(environment: "staging");

    // Act — call the workflow under test
    var result = workflows.ProcessInvoice(invoiceId: "INV-001");

    // Assert — verify the result with type-safe property access
    testing.VerifyExpression(result.success, "Invoice processing should succeed");
    testing.VerifyAreEqual("POSTED", result.status, "Invoice should be posted");
}
```

**Shared Before/After hooks for all test cases:**
Create a Coded Source File (e.g. `CodedWorkflowHooks.cs`) with `public partial class CodedWorkflow : IBeforeAfterRun` — the compiler merges it with the auto-generated CodedWorkflow partial, so all workflows and test cases get the hooks automatically. See `assets/before-after-hooks-template.md` for the full template.

## Add a Coded Source File (Helper Class / Model / Utility)

Coded Source Files are plain `.cs` files that contain reusable classes, models, enums, or utility methods. They are **not** entry points — they cannot be executed independently. Workflows and test cases consume them.

**Key differences from workflow files:**
- **NO** `CodedWorkflow` base class — they are plain C# classes
- **NO** `[Workflow]` or `[TestCase]` attribute
- **NO** entry in `project.json` `entryPoints`
- Can contain multiple classes per file if logically related (e.g. a models file)

**Steps:**
1. Read existing `project.json` to get the project name (for namespace)
2. Create the `.cs` file:
   - Use the project name as namespace
   - Name each class after what it contains (for a single-class file, that matches the file name). Never use the project name as a class name — analyzer rule ST-NMG-017 applies to every class in the default namespace, source files included
   - Add only the `using` statements the class needs (typically just `System` namespaces)
   - Do NOT inherit from `CodedWorkflow`
3. No `project.json` changes needed

**When to create Coded Source Files:**
- **Data models / DTOs** — classes that represent structured data (e.g. `InvoiceData`, `CustomerRecord`)
- **Helper/utility classes** — static methods for string manipulation, data transformation, validation
- **Custom enums** — project-specific enumerations
- **Constants** — centralized configuration values or magic strings
- **Extension methods** — reusable extensions for built-in types
- **Business logic** — complex logic that should be testable/reusable independently from the workflow orchestration

**Example — Data model source file (`InvoiceData.cs`):**
```csharp
using System;

namespace MyProject
{
    public class InvoiceData
    {
        public string InvoiceNumber { get; set; }
        public string CustomerName { get; set; }
        public decimal Amount { get; set; }
        public DateTime DueDate { get; set; }
        public bool IsOverdue => DueDate < DateTime.Now;
    }
}
```

**Example — Utility source file (`StringHelpers.cs`):**
```csharp
using System;
using System.Text.RegularExpressions;

namespace MyProject
{
    public static class StringHelpers
    {
        public static string ExtractInvoiceNumber(string text)
        {
            var match = Regex.Match(text, @"INV-\d{6}");
            return match.Success ? match.Value : string.Empty;
        }

        public static string NormalizeName(string name)
        {
            return name?.Trim().ToUpperInvariant() ?? string.Empty;
        }
    }
}
```

**Using source files from a workflow:**
```csharp
// In ProcessInvoices.cs (a workflow)
[Workflow]
public void Execute()
{
    var invoice = new InvoiceData  // from InvoiceData.cs
    {
        InvoiceNumber = StringHelpers.ExtractInvoiceNumber(rawText),  // from StringHelpers.cs
        CustomerName = StringHelpers.NormalizeName(customerField),
        Amount = parsedAmount,
        DueDate = dueDate
    };
    Log($"Processing invoice {invoice.InvoiceNumber}, overdue: {invoice.IsOverdue}");
}
```

## Edit an Existing Workflow File

**Steps:**
1. Read the existing `.cs` file to understand current structure
2. Apply requested changes while preserving:
   - Namespace (must match project name)
   - Class structure and base class (`CodedWorkflow`)
   - Attribute (`[Workflow]` or `[TestCase]`)
   - Method name (`Execute`)
3. If parameters changed (added/removed/renamed/retyped) and this is a **Process** project:
   - Update `project.json` `entryPoints` input/output definitions for this file (Tests and Library projects do not use `entryPoints`)
4. **Validate the file** — Run the validation loop (Critical Rule #14) until the file compiles cleanly before proceeding

## Remove a Workflow File

**Steps:**
1. Delete the `.cs` file
2. Update `project.json`:
   - **Process projects:** Remove from `entryPoints` array. If it was the `main` file, update `main` field to another entry point
   - **Tests and Library projects:** No `entryPoints` to update
   - If Tests project, remove from `fileInfoCollection`

## API Discovery (Before Creating Workflows)

**MANDATORY before generating any C# code**: Learn from existing project patterns first.

This operation helps you understand the project's existing code style, API usage patterns, and conventions before creating new workflows. This ensures consistency across the project.

**Steps:**

1. **Search for existing C# files:**
   ```
   Glob pattern: "**/*.cs"
   Path: <PROJECT_DIR>
   ```

2. **Count and filter results:**
   - Count total .cs files returned
   - Exclude files in `.local\.codedworkflows\` and `.codedworkflows\` from your count
   - Note: Generated/temporary files in these folders can still be read for API information

3. **Read example files:**
   - **If 5+ files found**: Read at least 5 diverse examples
   - **If fewer than 5**: Read all of them
   - **If 0 files**: Proceed using generic CodedWorkflow patterns from templates

4. **Read generated API files** (if they exist):
   - `<PROJECT_DIR>\.local\.codedworkflows\ObjectRepository.cs` — UI element descriptors
   - `<PROJECT_DIR>\.local\.codedworkflows\CodedWorkflow.cs` — available service definitions

5. **Extract patterns:**
   - Common `using` statements (e.g., `using UiPath.CodedWorkflows;`)
   - Namespace patterns (e.g., `namespace ProjectName`)
   - Class structure (inheritance from `CodedWorkflow`)
   - Service usage patterns (e.g., `excel.UseExcelFile()`, `mail.Outlook()`)
   - Argument patterns (input parameters, return tuples)
   - Logging patterns (e.g., `Log("message")`)
   - Error handling patterns (try-catch blocks)
   - UI Automation patterns (Object Repository descriptor usage: `Descriptors.App.Screen.Element`)

**Example patterns to look for:**

```csharp
// Common using statements
using System;
using System.Collections.Generic;
using UiPath.CodedWorkflows;

// Namespace pattern
namespace MyProjectName
{
    // Class structure
    public class MyWorkflow : CodedWorkflow
    {
        [Workflow]
        public void Execute(string inputParam)
        {
            // Logging pattern
            Log("Starting workflow...");

            // Service usage pattern
            using (var workbook = excel.UseExcelFile(inputParam))
            {
                // Implementation
            }

            // Error handling pattern
            try
            {
                // Operations
            }
            catch (Exception ex)
            {
                Log($"Error: {ex.Message}");
                throw;
            }
        }
    }
}
```

**Why API discovery matters:**
- Ensures code consistency across the project
- Prevents using incorrect method names or patterns
- Identifies available services and their usage
- Discovers project-specific conventions
- Finds Object Repository selectors for UI automation
- Reduces compilation errors from wrong API usage

---

## Configure UI Targets (Object Repository)

**This operation applies when writing UI automation code** (any workflow that uses `uiAutomation.*` calls). UI automation uses **Object Repository descriptors** (`Descriptors.App.Screen.Element`) — if required elements are missing, configure them through the `uia-configure-target` skill flow.

**When to use:**
- The workflow needs a UI element that doesn't exist in `ObjectRepository.cs`
- The user asks to automate something involving a screen or element not yet in the Object Repository

**Workflow order:** Configure ALL missing targets FIRST, then write the workflow code using real descriptor paths.

[ui-automation-guide.md](../ui-automation-guide.md) MUST be read IN FULL first, and [uia-configure-target-workflows.md](../uia-configure-target-workflows.md) MUST be read IN FULL first — they cover target configuration rules, selector recovery, indication fallback, and multi-step UI flows.

**Key reminders:**
- Add `using <ProjectNamespace>.ObjectRepository;` to any file referencing `Descriptors.*`
- After target configuration, re-read `ObjectRepository.cs` — Studio regenerates it. Search for the reference IDs returned by `uia-configure-target` to find the exact `Descriptors.<App>.<Screen>.<Element>` paths.

---

## Add a Dependency

Canonical CLI: `uip rpa packages install`. Do NOT hand-edit `project.json` `dependencies`. **There is no `uip rpa add-dependency` command** — agents that try it get `error: unknown command 'add-dependency'`. See [cli-reference.md § packages install](../cli-reference.md).

**Steps:**
1. Read `project.json` to check existing dependencies — skip packages already at the desired version.
2. Run:
   ```bash
   uip rpa packages install --project-dir "<PROJECT_DIR>" --packages 'id=<PACKAGE_ID>,version=<VERSION>' --output json
   ```
   Omit `,version=<VERSION>` to resolve the latest compatible. Pin a version only when there is a known compatibility constraint (see pinned versions below). The CLI writes `project.json` and runs restore — re-read `project.json` afterward if subsequent steps need it.
3. Only install packages the project actually needs.

**Pinned versions for UiPath activity packages (current v25.x):**
- `UiPath.System.Activities` → `25.12.2` — system activities (assets, queues, credentials)
- `UiPath.Testing.Activities` → `25.10.2` — testing and assertions. Pin this exact patch — `25.10.0` and `25.10.1` synthesize a bootloader under `.local/install/` that references `UiPath.Robot.Activities.Api` and breaks the build with CS0234.
- `UiPath.UIAutomation.Activities` → `25.10.21` — UI automation
- `UiPath.Excel.Activities` → `3.3.1` — Excel automation
- `UiPath.Word.Activities` → `2.3.1` — Word automation
- `UiPath.Presentations.Activities` → `2.3.1` — PowerPoint automation
- `UiPath.Mail.Activities` → `2.5.10` — Mail automation
- `UiPath.MicrosoftOffice365.Activities` → `3.6.10` — Microsoft 365 (Graph API: mail, calendar, Excel cloud, OneDrive, SharePoint)
- `UiPath.GSuite.Activities` → `3.6.10` — Google Workspace (Gmail, Calendar, Drive, Sheets, Docs)

**Third-party NuGet packages:** same CLI — pass the public NuGet package ID as `id`. See [third-party-packages-guide.md](third-party-packages-guide.md).

---

## Coding Guidelines

Detailed coding rules, best practices, anti-patterns, and troubleshooting for coded workflows.

### Using Statements Rules

**CRITICAL: Only include `using` statements for namespaces actually used in the file.** Adding usings for packages not in `project.json` will cause compile errors.

**Minimal using statements** (always safe in any workflow/test case file):
```csharp
using System;
using System.Collections.Generic;
using UiPath.CodedWorkflows;
```

**Add based on actual usage** — only include these when the file uses the corresponding types/services AND the package is in `project.json`:
```csharp
// If using system.* service (UiPath.System.Activities package):
using UiPath.Core;
using UiPath.Core.Activities.Storage;       // only if using storage APIs
using UiPath.Orchestrator.Client.Models;    // only if using Orchestrator models

// If using testing.* service (UiPath.Testing.Activities package):
using UiPath.Testing;
using UiPath.Testing.Enums;                 // only if using testing enums
using UiPath.Testing.Activities.TestData;   // only if using test data queues

// If using uiAutomation.* service (UiPath.UIAutomation.Activities package):
using UiPath.UIAutomationNext.API.Contracts;
using UiPath.UIAutomationNext.API.Models;
using UiPath.UIAutomationNext.Enums;

// If using Object Repository descriptors (Descriptors.App.Screen.Element):
using <ProjectNamespace>.ObjectRepository;  // e.g. using RoboticEnterpriseFramework.ObjectRepository;
// OR if descriptors come from a UILibrary NuGet package (not the project's own OR):
// using <PackageNamespace>.ObjectRepository;  // e.g. using MultipleApps.Descriptors.ObjectRepository;
// CRITICAL: Without this, you get CS0103: The name 'Descriptors' does not exist in the current context
// NOTE: When descriptors come from a UILibrary package, use the PACKAGE namespace, not the project namespace

// If using excel.* service (UiPath.Excel.Activities package):
using UiPath.Excel;
using UiPath.Excel.Activities;
using UiPath.Excel.Activities.API;
using UiPath.Excel.Activities.API.Models;

// If using word.* service (UiPath.Word.Activities package):
using UiPath.Word;
using UiPath.Word.Activities;
using UiPath.Word.Activities.API;
using UiPath.Word.Activities.API.Models;

// If using powerpoint.* service (UiPath.Presentations.Activities package):
using UiPath.Presentations;
using UiPath.Presentations.Activities;
using UiPath.Presentations.Activities.API;
using UiPath.Presentations.Activities.API.Models;

// If using mail.* service (UiPath.Mail.Activities package):
using UiPath.Mail.Activities.Api;

// If using office365.* service (UiPath.MicrosoftOffice365.Activities package):
using UiPath.MicrosoftOffice365.Activities.Api;

// If using google.* service (UiPath.GSuite.Activities package):
using UiPath.GSuite.Activities.Api;

// Standard .NET (add as needed):
using System.Data;           // DataTable
using System.Linq;           // LINQ
using System.IO;             // file operations
using System.Text.RegularExpressions;  // regex
```

**When adding a file that uses a service:**
1. Check `project.json` to confirm the required package is listed in `dependencies` — add it if missing
2. Add only the `using` statements needed for the types actually referenced in the file
3. Add the entry point to `project.json` (**Process projects only** — Tests and Library projects do not use `entryPoints`). Add `fileInfoCollection` for test case files (all project types)

### Platform types — do not reinvent

UiPath ships first-class types for the patterns coded workflows most commonly need (exceptions, queue items, credentials, OR descriptors). **Always import the platform type instead of defining a project-local equivalent.** A project-local `BusinessRuleException`, custom queue-item record, or hand-rolled credential helper diverges from Orchestrator behaviour and breaks integration with platform features that expect the canonical types.

| Platform type | Namespace / package | Use for | Do NOT do this instead |
|---|---|---|---|
| **`UiPath.Core.BusinessRuleException`** | `UiPath.Core` (in `UiPath.System.Activities`) | Business-rule violations that must NOT be retried by REFramework / Orchestrator (e.g., invalid input data, validation failure, missing required field). Orchestrator marks the queue item as `Failed` with no retry. | Define a project-local `class BusinessRuleException : Exception { … }`. |
| **`UiPath.Robot.Activities.BusinessException`** | `UiPath.Robot.Activities` | Same role as `BusinessRuleException` in robot-side custom activity packages. | Same — do not define your own. |
| **`UiPath.Core.Activities.Storage.IResource` / `ILocalResource`** | `UiPath.Core.Activities.Storage` (in `UiPath.System.Activities`) | File / folder handles passed to activities that need an `IResource`. | Pass raw `string` paths or hand-roll a `LocalResource` constructor (the constructor is internal — see § IResource / ILocalResource below). |
| **`UiPath.Orchestrator.Client.Models.QueueItemDto`** and related | `UiPath.Orchestrator.Client.Models` (in `UiPath.System.Activities`) | Queue-item shape returned by `GetTransactionItem` / pushed via `AddQueueItem`. | Define a project-local queue-item record that diverges from Orchestrator's schema. |
| **OR descriptors `Descriptors.<App>.<Screen>.<Element>`** | Generated into `<PROJECT_DIR>/.local/.codedworkflows/ObjectRepository.cs` | UI element targeting in coded UI automation. | Hand-roll selector strings or `TargetAppModel` instances; bypass the Object Repository. |
| **`UiPath.CodedWorkflows.CodedWorkflow`** | `UiPath.CodedWorkflows` (built into the runtime) | Base class for `[Workflow]` and `[TestCase]` classes. | Inherit from a custom base; the Studio wrapper generation depends on this exact type. |

#### Throwing `BusinessRuleException` correctly

```csharp
using UiPath.Core;     // brings BusinessRuleException into scope

if (!System.Text.RegularExpressions.Regex.IsMatch(hash, @"^[0-9a-f]{40}$"))
{
    throw new BusinessRuleException(
        $"Computed hash '{hash}' does not match expected SHA1 format (40 lowercase hex chars).");
}
```

`BusinessRuleException` is recognised by REFramework's `SetTransactionStatus` and by Orchestrator's queue-item lifecycle — items failed with this exception are marked **Failed** and not retried automatically. A project-local exception with the same name is just an `Exception` from REFramework's point of view and triggers the system-error retry path instead.

#### When you MAY define a project-local type

Project-local types are appropriate for **domain DTOs** that have no platform equivalent — `InvoiceLineItem`, `CustomerRecord`, `WorkItem` — and belong in Coded Source Files. The rule above applies to platform-provided types only: do not reinvent exceptions, queue-item shapes, credential handles, file-resource handles, or OR descriptors.

### Coded Workflow Analyzer Rules

Four built-in Workflow Analyzer rules with scope `Coded Workflow` run as Roslyn analyzers over the project's `.cs` files. All four are **Error** severity and enabled by default — a violation fails `uip rpa analyze`, `build`, and `pack`, and Studio flags the same violations as validation errors. Author to satisfy them up front:

| Rule | Trigger | Fix |
|------|---------|-----|
| **ST-NMG-017** — Class name matches default namespace | A class declared inside the project's default namespace has the same name as that namespace (generated from the project name) — e.g. class `Invoicing` in project `Invoicing`. Applies to every class, including Coded Source Files. | Rename the class (and its file to match) — e.g. `InvoicingWorkflow` |
| **ST-DBP-010** — Multiple `[Workflow]`/`[TestCase]` | More than one `[Workflow]` or `[TestCase]` attribute in the same **file** (the two attribute kinds count together) | One entry-point attribute per file — move each extra entry point to its own file |
| **ST-REL-001** — Mismatched InOut argument types | An entry-point input parameter collapses into an InOut argument (its name matches a return-tuple element, or it is literally named `Output` with a single non-void return) but the input and returned types differ | Make the input parameter type and the returned type identical |
| **ST-USG-017** — Invalid parameter modifier | `out` or `ref` modifier on a `[Workflow]`/`[TestCase]` method parameter | Use return values or tuples for outputs instead |

> Older CLI versions listed these rules in `analyzer-rules list` but did not execute them headlessly — only Studio flagged the violations. Do not treat a clean `analyze`/`build`/`pack` from an older CLI as proof these rules pass; fix violations at authoring time regardless.

### Best Practices

### API Discovery
- **ALWAYS search for existing .cs files BEFORE generating new code** — Learn from existing patterns
- Read at least 5 existing workflow files (or all if fewer) to understand project conventions
- **When writing UI automation code** — [ui-automation-guide.md](../ui-automation-guide.md) MUST be read IN FULL first. Follow the **Finding Descriptors** hierarchy in strict order. Do NOT write any UI code until descriptors are resolved:
  1. Read `ObjectRepository.cs` — use existing descriptors if present
  2. Inspect UILibrary/descriptor NuGet packages in `project.json` (e.g. `*.Descriptors`, `*.UILibrary`) using `uip rpa packages inspect`. The tool checks the local NuGet cache automatically. If the package is still not found, read `.metadata` files manually at `~/.nuget/packages/<package-name>/<version>/contentFiles/any/any/.objects/` to discover App/Screen/Element hierarchy
  3. If descriptors are still missing — use the `uia-configure-target` skill flow (found in the UIA activity-docs) to create targets. This handles capturing the application, discovering elements, generating selectors, improving them, and registering them in the OR. Do NOT manually call the internal `uip rpa uia` CLIs outside of the skill flow. Fallback: the indication commands (see UIA docs) when elements appear only after user interaction (e.g., a compose form that opens after clicking a button)
  4. UITask (ScreenPlay) is ONLY for when selectors are genuinely brittle/unreliable — NEVER as a first approach
  5. NEVER bypass Object Repository by constructing `TargetAppModel` with raw URL/BrowserType
- Use `uip rpa packages inspect` for API discovery when documentation is unclear

### IResource / ILocalResource — Converting File Paths

Many activities (O365, GSuite, Mail, file operations) require `IResource` or `ILocalResource` instead of a string path. NEVER pass a raw string where `IResource` is expected — it will fail at runtime. NEVER try to construct `LocalResource(string)` directly — the constructor is internal.

| Method | Signature | Use when |
|--------|-----------|----------|
| `GetResourceForLocalPath` | `system.GetResourceForLocalPath(string path, PathType pathType)` → `IResource` | You have a path and need an `IResource` (no existence check needed) |
| `PathExists` (with out param) | `system.PathExists(string path, PathType pathType, out ILocalResource resource)` → `bool` | You need to verify the file exists AND get an `ILocalResource` |

```csharp
// Direct conversion — preferred when you know the file exists
IResource file = system.GetResourceForLocalPath(@"C:\Reports\report.pdf", PathType.File);
IResource folder = system.GetResourceForLocalPath(@"C:\Archive", PathType.Folder);

// With existence check
if (system.PathExists(@"C:\Reports\report.pdf", PathType.File, out ILocalResource localFile))
{
    // use localFile
}
```

`PathType` values: `PathType.File`, `PathType.Folder`

### Code Quality
- **Start simple, iterate** — Create minimal working version first, then refine
- **NEVER use C# `out` or `ref` keywords in `[Workflow]` methods** — The auto-generated `*+Activity.cs` wrapper does not handle them correctly. Symptoms: analyzer error ST-USG-017 at `analyze`/`build`/`pack`, compile error `CS1620`, or runtime `Using 'out' and 'ref' modifiers is not allowed for Coded Workflows executions.` Studio regenerates the wrapper on every save, so manual fixes are reverted. Use return values or tuples for outputs instead
- **Only include using statements for packages in project.json** — Adding unused usings causes compile errors
- **Match input parameter names exactly** — Execute method signature must match `--input` arguments (case-sensitive)
- **Escape backslashes in paths** — Use `C:\\path\\file.txt` not `C:\path\file.txt` in input arguments

### Validation Loop (Critical Rule #14)
uip rpa validate --file-path "<FILE>" --project-dir "<PROJECT_DIR>" --output json
@../validation-guide.md

### Error Handling
- **Fix compilation errors methodically** — Categorize: Syntax → Type → Logic. Use the validation loop above to iterate until clean.
- **Retry on execution failures** — Attempt to fix and retry up to 2 times before asking user
- **Analyze errors carefully** — Read error messages, identify root cause, make targeted fixes
- **Fix one thing at a time** — When a runtime error occurs, identify the root cause, fix ONLY that, and re-run. Never bundle a speculative "improvement" (e.g., switching from TypeInto to KeyboardShortcut) with the actual fix (e.g., correcting a selector). Changing two things at once makes it impossible to verify which change resolved the issue — or whether the speculative change introduced a new one.
- **Don't give up too early** — But stop after 2 failed retries and present the user with options:
```
Workflow execution failed after 2 retry attempts.

**Error Details:** <specific error message and location>
**Suggested Fix:** <analysis of what went wrong>
**Next Steps:** Would you like me to:
A) <recommended fix approach>
B) <alternative approach>
C) <user-driven approach>
```

### File Operations
- **ALWAYS use Read tool before Edit tool** — Understand current state before making changes
- **Prefer editing over creating new files** — Build on existing work, avoid file bloat
- **Use Glob for file discovery** — Never guess file locations

### Anti-Patterns (What NOT to Do)

> Many of these reinforce SKILL.md Critical Rules. They are grouped by category for quick scanning.

### Project & Code Structure

- Never manually write `project.json` or `project.uiproj` when creating a new project — use `uip rpa init` (Critical Rule #1)
- Never generate C# code without first searching for existing .cs files (API Discovery)
- Never edit files without reading them first
- Never skip the `[Workflow]` or `[TestCase]` attribute on the Execute method (Critical Rule #4)
- Never put more than one `[Workflow]`/`[TestCase]` attribute in the same file — analyzer error ST-DBP-010 (see § Coded Workflow Analyzer Rules)
- Never name a class the same as the project — analyzer error ST-NMG-017 (see § Coded Workflow Analyzer Rules)
- Never forget to inherit from `CodedWorkflow` (except Coded Source Files) (Critical Rule #3)
- Never add `using` statements for packages not in `project.json` — causes CS errors
- Never guess service method names — verify with existing code or `uip rpa packages inspect`

### UI Automation

- Never hardcode UI selectors — use Object Repository descriptors
- Never write UI code referencing descriptors without first reading `ObjectRepository.cs`
- Never manually craft UI selectors by calling the internal `uip rpa uia` CLIs outside of the `uia-configure-target` skill flow — this skips selector improvement and OR registration
- Never skip the target configuration step when a descriptor is missing — use the `uia-configure-target` skill flow (fallback: indication commands per the UIA docs)
- Never use UITask (ScreenPlay) as the primary approach — resolve descriptors via Finding Descriptors hierarchy first (Critical Rule #15)
- Never skip configuring targets because it "seems tedious" — configure ALL missing elements
- Never construct `TargetAppModel` with raw URL/BrowserType to bypass Object Repository
- Never skip checking UILibrary/descriptor NuGet packages in `project.json`
- Never use an element descriptor on the wrong screen handle — each `UiTargetApp` is bound to its screen. Wrong handle gives `"Target name 'X' is not part of the current screen."`
- Never use `SelectItem` on web dropdowns without a `TypeInto` fallback — web `<select>` elements often fail with `"Cannot select item"`
- Never forget `using <ProjectNamespace>.ObjectRepository;` (or `using <PackageName>.ObjectRepository;` for UILibrary packages) when referencing `Descriptors.*`

### Object Repository / Indicate Commands

- Never assume `.objects/` subdirectories mean a valid App exists — verify `.metadata` files are present
- Never cache or reuse AppVersion references across OR resets — always re-read `.objects/` metadata
- Never run indicate commands from outside the project directory — cwd must contain `project.json`
- Never use camelCase flags — all `uip rpa` CLI flags use kebab-case (e.g., `--foo-bar`, not `--fooBar`)

### Validation & Execution

- Never assume create/edit succeeded without running the validation loop (Critical Rule #14)
- Never continue retrying indefinitely — stop after 5 validation fix attempts or 2 runtime execution retries
- Never make unrelated changes during retry — identify the root cause, fix only that, re-run and verify. Never bundle a speculative "improvement" with the actual fix (e.g., fixing a broken selector AND switching from TypeInto to KeyboardShortcut in the same edit). One change, one re-run.
- Never execute a workflow with parameters without providing `--input` arguments
- Never use parameter names in `--input` that don't match the Execute method signature (case-sensitive)

### Shell & Environment

- Never redirect output to `nul` — use `> /dev/null 2>&1` instead (`nul` creates a literal file on Windows)
- Never use Windows shell commands (`del`, `dir`, `copy`) in bash — use `rm`, `ls`, `cp`

### Common Issues and Fixes

| Issue | Cause | Fix |
|-------|-------|-----|
| **"Studio X.X.X does not have interop support"** | Surfaces only when running against Studio Desktop and the auto-detected install is too old (< 26.2). Headless Studio is unaffected. | Pass `--studio-dir "<STUDIO_DIR>"` pointing to a 26.2+ build, or drop the Studio Desktop override and let the command run headless |
| **No Studio instances found** | Only relevant for `diff` / `focus-activity` — they need Studio Desktop. Every other command runs headless and doesn't need a Desktop instance. | Run `uip rpa studio start --project-dir "<PROJECT_DIR>"` if you actually need Studio Desktop; otherwise re-run the command — headless Studio relaunches automatically |
| **Stale pipe / ENOENT** | Studio instance crashed or was closed | The tool retries automatically; if persistent, re-run the command (headless) or restart Studio Desktop |
| **Workflow cannot be found** | Entrypoint not in project.json | Verify project.json entrypoint has the file listed (Process projects only — Tests and Library projects do not use `entryPoints`) |
| **Service property not available** | Missing package dependency | Install the required package via `uip rpa packages install --project-dir "<PROJECT_DIR>" --packages id=<PACKAGE_ID> --output json` (no `add-dependency` command exists; do not hand-edit `project.json`) |
| **Timeout** | Studio took too long to start. First headless call on a cold NuGet cache can take 30–90 s. | Increase timeout: `--timeout 600` |
| **"Target name 'X' is not part of the current screen"** | Element descriptor used on wrong screen handle | Use the `UiTargetApp` handle from `Open`/`Attach` for the screen that owns the element |
| **"Cannot select item. It was not found among existing items"** | The `Item` value doesn't match any option (wrong text/casing) — not a control-type limitation | Read the control's `items` attribute (via the interact CLI, see the UIA cli-reference) and pass one of those values verbatim. `SelectItem` drives any control whose `items` lists options (any UI stack); use `TypeInto` only for type-ahead combos or controls with no `items`. |
| **`packages inspect` cannot find UILibrary package** | Package is on a private/local NuGet feed | Use `--nupkg-path` to inspect the local `.nupkg` directly, or read `.metadata` files manually from `~/.nuget/packages/<name>/<version>/contentFiles/any/any/.objects/` |
| **Studio rejects manually created project** | Missing metadata dirs, wrong schema/version | Always use `uip rpa init` instead of writing `project.json` manually |
