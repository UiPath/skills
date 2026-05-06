# Designing Project Structure

When creating a project, **proactively design the right file structure** based on the task complexity. Do not put everything into a single root workflow file. Use your best judgment to split the project into multiple files following good software engineering practices.

> **This guide is mode-agnostic.** Examples are shown in coded form because the templates and snippets in this `assets/` folder are coded-specific, but the same structural principles apply to XAML projects (replace `Main.cs` with `Main.xaml`, step files with `.xaml` workflows, etc.). For new projects, default to XAML — see [../references/coded-vs-xaml-guide.md](../references/coded-vs-xaml-guide.md).

## Guidelines

- **Single simple task** (e.g. "read a CSV and log it") — one workflow file (`Main.xaml` for XAML projects, `Main.cs` for coded) is fine
- **Multi-step process** (e.g. "read invoices, validate, post to system") — split into multiple workflow files, each handling one step. The root workflow orchestrates by invoking each step
- **Shared data structures** — extract into a Coded Source File (e.g. `Models.cs` or `InvoiceData.cs`). XAML cannot define types, so a Coded Source File is the right home even in an otherwise XAML project
- **Repeated logic** — extract into helper Coded Source Files (e.g. `ValidationHelpers.cs`, `DataTransformations.cs`) or reusable XAML workflows
- **Test project** — one test case per scenario; coded test projects use `partial class CodedWorkflow : IBeforeAfterRun` in `CodedWorkflowHooks.cs` for shared setup
- **Complex domain logic** — isolate business rules in coded source files so they can be unit-tested and reused

## Example — Well-Structured Invoice Processing Project

```
InvoiceProcessor/
├── project.json
├── Main.cs                    # Root workflow: calls each step via workflows.StepName()
├── ReadInvoices.cs            # Step 1: reads invoices from Excel
├── ValidateInvoices.cs        # Step 2: validates data
├── PostToERP.cs               # Step 3: posts to external system
├── InvoiceData.cs             # Source file: data model
└── ValidationHelpers.cs       # Source file: validation utilities
```

### Main.cs Root Workflow Using Strongly-Typed Workflow Invocation

```csharp
[Workflow]
public void Execute(string inputFolder)
{
    // Step 1: Read invoices from Excel
    var readResult = workflows.ReadInvoices(folderPath: inputFolder);
    Log($"Read {readResult.count} invoices");

    // Step 2: Validate invoices
    var validateResult = workflows.ValidateInvoices(invoices: readResult.invoiceList);
    Log($"Valid: {validateResult.validCount}, Invalid: {validateResult.invalidCount}");

    // Step 3: Post valid invoices to ERP
    var postResult = workflows.PostToERP(validInvoices: validateResult.validInvoices);
    Log($"Posted {postResult.successCount} invoices to ERP");
}
```

## Example — Well-Structured Test Project

```
InvoiceTests/
├── project.json
├── CodedWorkflowHooks.cs             # Source file: partial class CodedWorkflow with Before/After hooks
├── TestLoginFlow.cs            # Test case: login scenario (hooks apply automatically via partial class merge)
├── TestInvoiceCreation.cs      # Test case: create invoice scenario (hooks apply automatically)
├── TestInvoiceValidation.cs    # Test case: validation rules (hooks apply automatically)
├── TestData.cs                 # Source file: shared test constants/fixtures
└── PageHelpers.cs              # Source file: UI interaction helpers
```

## Example — Hybrid Project (XAML Root + Coded Logic)

```
OrderProcessing/
├── project.json
├── Main.xaml                    # XAML root workflow: sequences steps, handles retries
├── ScrapeOrderPortal.xaml       # XAML: UI automation with visual selector builder
├── SendConfirmationEmail.xaml   # XAML: Mail activities (straightforward)
├── ProcessOrder.cs              # Coded workflow: 12 validation rules + LINQ transforms
├── OrderModels.cs               # Coded source file: Order, LineItem, ValidationResult DTOs
├── TransformHelpers.cs          # Coded source file: date parsing, currency conversion
└── TestProcessOrder.cs          # Coded test case: unit tests for ProcessOrder logic
```

### Why Hybrid Here

- **ScrapeOrderPortal.xaml** — UI automation benefits from XAML's visual selector builder and recording tools
- **ProcessOrder.cs** — Order validation has 12 business rules with nested conditions; coded C# is clearer and testable
- **OrderModels.cs** — Typed DTOs used by both XAML (via typed arguments) and coded workflows, eliminating DataTable column-name guessing
- **SendConfirmationEmail.xaml** — Simple Mail activity, no logic — XAML is the simpler choice
- **Main.xaml** — Orchestration is linear (scrape → process → email); XAML Sequence is readable

### Data Flow

1. `Main.xaml` invokes `ScrapeOrderPortal.xaml` → returns `DataTable` via Out argument
2. `Main.xaml` invokes `ProcessOrder.cs` via Invoke Workflow File → passes raw data, returns validated `Order` objects
3. `Main.xaml` invokes `SendConfirmationEmail.xaml` → passes validated order data

For the full decision framework on when to use coded vs XAML, see [../references/coded-vs-xaml-guide.md](../references/coded-vs-xaml-guide.md).

## Project Structure Decision Tree

**First — coded or XAML?** For new projects, default to XAML unless the user explicitly said "coded" or named a coded-specific trigger (custom data models, complex algorithms, unit tests on business logic). See [../references/coded-vs-xaml-guide.md](../references/coded-vs-xaml-guide.md). The root workflow file is `Main.xaml` for XAML projects and `Main.cs` for coded projects — substitute accordingly below.

**Is it a single, simple task?**
- ✅ Yes → Single root workflow

**Is it a multi-step process?**
- ✅ Yes → A root workflow that invokes each step + separate workflow files for each step

**Does it involve repeated data structures?**
- ✅ Yes → Extract to Coded Source File (e.g. `Models.cs`, `InvoiceData.cs`). Required even in XAML projects — XAML cannot define types

**Is there shared logic across workflows?**
- ✅ Yes → Extract to a reusable XAML workflow (XAML projects) or a helper Coded Source File (coded or hybrid projects)

**Is it a test project?**
- ✅ Yes → One test case file per scenario + optional `CodedWorkflowHooks.cs` (partial class CodedWorkflow) for shared setup/teardown in coded test projects

**Does it have complex business rules?**
- ✅ Yes → Isolate in Coded Source Files for reusability and testability (extracted from XAML via `Invoke Workflow File` if needed)

**Does it need both UI automation AND complex non-UI logic?**
- ✅ Yes → Hybrid: XAML for UI automation + orchestration, Coded for business logic + data models. See [../references/coded-vs-xaml-guide.md](../references/coded-vs-xaml-guide.md)
