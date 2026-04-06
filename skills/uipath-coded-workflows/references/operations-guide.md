# Operations Guide

Detailed step-by-step procedures for all operations on UiPath coded workflow projects.

## Initialize a New Project

Creates a complete UiPath coded automation project from scratch. **ALWAYS use `uip rpa create-project`** — never write `project.json`, `project.uiproj`, or other scaffolding files manually.

### Steps

**1. Create the project with `uip rpa create-project`:**

```bash
uip rpa create-project --name "<NAME>" --location "<PARENT_DIR>" --studio-dir "<STUDIO_DIR>" --output json --use-studio
```

**Template options:**
- `--template-id BlankTemplate` (default) — standard process project
- `--template-id TestAutomationProjectTemplate` — test project with testing dependencies
- `--template-id LibraryProcessTemplate` — reusable library

This scaffolds a valid project with `project.json`, `project.uiproj`, `Main.cs`, `Main.cs.json`, and all required metadata directories. The result includes the `projectDirectory` path.

**2. Read the scaffolded files — do NOT overwrite blindly:**

After `create-project` succeeds, read the generated files to understand the defaults:
```
Read: <PROJECT_DIR>/project.json
Read: <PROJECT_DIR>/Main.cs
```
These contain valid defaults (correct schema version, runtime options, dependencies, etc.) that you should build on rather than replace.

**3. Analyze the task and plan the file structure:**
- How many workflow files? (one per logical step or responsibility)
- Are there shared data models or helpers? (create Coded Source Files)
- Is this a test project? (create test cases with Given/When/Then structure, optionally add Before/After hooks)
- See `assets/project-structure-examples.md` for guidelines

**4. Add required dependencies to `project.json`** based on the Service-to-Package mapping. Edit the existing `project.json` — do NOT rewrite the entire file.

**5. Add workflow/test case/source files:**
- Generate `.cs` files (workflows, test cases, source files)
- Generate `.cs.json` metadata for each workflow/test case file (NOT for source files)
- Update `project.json` entry points for each workflow/test case file
- If test project and shared setup is needed, create a base class (e.g. `CodedWorkflowBase.cs`) that implements `IBeforeAfterRun`

**6. Validate each file** (Critical Rule #14) — run the validation loop on every `.cs` file until it compiles cleanly

> **Why `create-project` instead of manual files?** It generates correct schema versions, metadata directories, and default dependencies — manual creation risks subtle errors. See [json-template.md](../assets/json-template.md) for reference-only templates.

## Add a Workflow File to Existing Project

**Steps:**
1. Read existing `project.json` to get project name (for namespace) and current entry points
2. Create the new `.cs` file:
   - Use the project name as namespace
   - Class name = file name (without .cs)
   - Inherit from `CodedWorkflow`
   - Add `[Workflow]` attribute on `Execute` method
   - Add appropriate `using` statements based on which activities are needed
3. Create the companion `.cs.json` metadata file with `DisplayName` and `Arguments`:
   - For each input parameter: `ArgumentType: 0` (Input)
   - For each output/return value: `ArgumentType: 1` (Output)
   - For in/out parameters: `ArgumentType: 2` (InOut)
4. Update `project.json`:
   - Add new entry to `entryPoints` array with `filePath`, unique `uniqueId`, `input`, and `output` definitions
   - If the workflow has parameters, define them in `input`/`output` with `name`, `type`, and `required`
5. **Validate the file** — Run the validation loop (Critical Rule #14) until the file compiles cleanly before proceeding

## Add a Test Case File

Coded test cases automate and validate application behavior using a structured **Given-When-Then** (Arrange/Act/Assert) pattern. They inherit from `CodedWorkflow` just like workflows, but use the `[TestCase]` attribute.

**Test cases can exist in any project type** — not just `"Tests"` projects. It's common to add test cases directly inside a `"Process"` project for testing purposes.

**Steps:**
1. Read existing `project.json` to get project name and current entry points
2. Create the `.cs` file following the same rules as workflows, but with:
   - `[TestCase]` attribute instead of `[Workflow]` on the `Execute` method
   - Structured code in three phases: **Arrange**, **Act**, **Assert**
3. Create the companion `.cs.json` metadata file (same format as workflows)
4. Update `project.json`:
   - Add entry to `entryPoints` array
   - Add entry to `designOptions.fileInfoCollection` with `testCaseType: "TestCase"`, `publishAsTestCase: true`
5. For data-driven tests, add default parameter values: `public void Execute(string browser = "chrome.exe")`
   - Optionally create `.variations/` data file for parameterized test data
6. **Validate the file** — Run the validation loop (Critical Rule #14) until the file compiles cleanly before proceeding

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
- `testing.VerifyIsTrue(bool condition, string outputMessage = null)` — alias for VerifyExpression
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
Create a base class (e.g. `CodedWorkflowBase.cs`) that implements `IBeforeAfterRun`, then have all test cases inherit from it instead of `CodedWorkflow`. See `references/codedworkflow-reference.md#extending-with-hooks` for details.

## Add a Coded Source File (Helper Class / Model / Utility)

Coded Source Files are plain `.cs` files that contain reusable classes, models, enums, or utility methods. They are **not** entry points — they cannot be executed independently. Workflows and test cases consume them.

**Key differences from workflow files:**
- **NO** `CodedWorkflow` base class — they are plain C# classes
- **NO** `[Workflow]` or `[TestCase]` attribute
- **NO** companion `.cs.json` metadata file
- **NO** entry in `project.json` `entryPoints`
- Can contain multiple classes per file if logically related (e.g. a models file)

**Steps:**
1. Read existing `project.json` to get the project name (for namespace)
2. Create the `.cs` file:
   - Use the project name as namespace
   - Class name = file name (without .cs)
   - Add only the `using` statements the class needs (typically just `System` namespaces)
   - Do NOT inherit from `CodedWorkflow`
3. No `.cs.json` file needed
4. No `project.json` changes needed

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
3. If parameters changed (added/removed/renamed/retyped):
   - Update the companion `.cs.json` `Arguments` array
   - Update `project.json` `entryPoints` input/output definitions for this file
4. **Validate the file** — Run the validation loop (Critical Rule #14) until the file compiles cleanly before proceeding

## Remove a Workflow File

**Steps:**
1. Delete the `.cs` file
2. Delete the companion `.cs.json` file
3. Update `project.json`:
   - Remove from `entryPoints` array
   - If it was the `main` file, update `main` field to another entry point
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

**Full configure-target workflow and rules:** [uia-configure-target-workflows.md](../../shared/uia-configure-target-workflows.md)
**Target configuration and selector recovery:** [ui-automation-guide.md](ui-automation-guide.md)

**Key reminders:**
- Add `using <ProjectNamespace>.ObjectRepository;` to any file referencing `Descriptors.*`
- After target configuration, re-read `ObjectRepository.cs` — Studio regenerates it. Search for the reference IDs returned by `uia-configure-target` to find the exact `Descriptors.<App>.<Screen>.<Element>` paths.

---

## Add a Dependency

**Steps:**
1. Read `project.json` to check existing dependencies
2. Add the package to `dependencies` with version in bracket notation: `"PackageName": "[version]"`
3. Only add packages the project actually needs. Available UiPath packages and their latest v25.x versions:
   - `"UiPath.System.Activities": "[25.12.2]"` — system activities (assets, queues, credentials)
   - `"UiPath.Testing.Activities": "[25.10.0]"` — testing and assertions
   - `"UiPath.UIAutomation.Activities": "[25.10.21]"` — UI automation
   - `"UiPath.Excel.Activities": "[3.3.1]"` — Excel automation
   - `"UiPath.Word.Activities": "[2.3.1]"` — Word automation
   - `"UiPath.Presentations.Activities": "[2.3.1]"` — PowerPoint automation
   - `"UiPath.Mail.Activities": "[2.5.10]"` — Mail automation
   - `"UiPath.MicrosoftOffice365.Activities": "[3.6.10]"` — Microsoft 365 (Graph API: mail, calendar, Excel cloud, OneDrive, SharePoint)
   - `"UiPath.GSuite.Activities": "[3.6.10]"` — Google Workspace (Gmail, Calendar, Drive, Sheets, Docs)
4. Third-party NuGet packages can also be added — same bracket notation (see [third-party-packages-guide.md](third-party-packages-guide.md))
