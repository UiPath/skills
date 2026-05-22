# Designing Project Structure

When creating a project, **proactively design the right file structure** based on the task complexity. Do not put everything into a single root workflow file. Use your best judgment to split the project into multiple files following good software engineering practices.

For the coded vs XAML decision, see [coded-vs-xaml-guide.md](coded-vs-xaml-guide.md). For new projects, the default is XAML — examples below lead with XAML and note where the coded equivalent differs.

## Guidelines

- **Default to decomposition: a `Main` orchestrator + small focused sub-workflows, one per business step.** The root (`Main.xaml` for XAML, `Main.cs` for coded) only sequences and passes arguments; each step lives in its own file invoked via `Invoke Workflow File` (XAML) or `workflows.StepName(...)` (coded). Benefits: independent validation and testing, isolated merge conflicts, readable orchestrator, **and — because each sub-workflow has a self-contained In/Out contract — every sub-workflow can be authored in parallel by a separate agent.** Size each sub-workflow to one cohesive business step (typically tens of activities, never approaching the ~500-activity ceiling from [xaml/common-pitfalls.md](xaml/common-pitfalls.md)).
- **Single-activity task** (e.g. "read a CSV and log it", "send one email") — one workflow file is fine. Use this exception only when the entire automation is genuinely one step.
- **Shared data structures** — extract into a Coded Source File (e.g. `Models.cs`, `InvoiceData.cs`). XAML cannot define types, so a Coded Source File is the right home even in an otherwise XAML project
- **Repeated logic** — in XAML projects, extract into a reusable XAML workflow. In coded or hybrid projects, extract into a helper Coded Source File (e.g. `ValidationHelpers.cs`)
- **Test project** — one test case per scenario. Coded test projects optionally use `partial class CodedWorkflow : IBeforeAfterRun` in `CodedWorkflowHooks.cs` for shared setup. XAML test projects use Test Activities for shared setup
- **Complex domain logic** — isolate business rules so they can be unit-tested and reused (Coded Source File for typed logic, or a separate workflow for activity-driven logic)

## Example — Invoice Processing Project (XAML)

```
InvoiceProcessor/
├── project.json
├── Main.xaml                  # Root workflow: sequences each step via Invoke Workflow File
├── ReadInvoices.xaml          # Step 1: reads invoices from Excel
├── ValidateInvoices.xaml      # Step 2: validates data
├── PostToERP.xaml             # Step 3: posts to external system
└── InvoiceData.cs             # Coded source file: typed data model used across XAML steps
```

`Main.xaml` invokes each step via `Invoke Workflow File`, passing arguments In/Out. `InvoiceData.cs` is included even in this otherwise-XAML project because XAML cannot define types — typed DTOs eliminate `DataTable` column-name guessing.

### Coded equivalent

```
InvoiceProcessor/
├── project.json
├── Main.cs                    # Root workflow: calls each step via workflows.StepName()
├── ReadInvoices.cs            # Step 1
├── ValidateInvoices.cs        # Step 2
├── PostToERP.cs               # Step 3
├── InvoiceData.cs             # Coded source file: data model
└── ValidationHelpers.cs       # Coded source file: validation utilities
```

`Main.cs` uses strongly-typed workflow invocation:

```csharp
[Workflow]
public void Execute(string inputFolder)
{
    var readResult = workflows.ReadInvoices(folderPath: inputFolder);
    Log($"Read {readResult.count} invoices");

    var validateResult = workflows.ValidateInvoices(invoices: readResult.invoiceList);
    Log($"Valid: {validateResult.validCount}, Invalid: {validateResult.invalidCount}");

    var postResult = workflows.PostToERP(validInvoices: validateResult.validInvoices);
    Log($"Posted {postResult.successCount} invoices to ERP");
}
```

## Example — Test Project

```
InvoiceTests/
├── project.json
├── CodedWorkflowHooks.cs      # Coded test projects only: partial class CodedWorkflow with Before/After hooks
├── TestLoginFlow.cs           # Test case: login scenario (hooks apply automatically via partial class merge)
├── TestInvoiceCreation.cs     # Test case: create invoice scenario
├── TestInvoiceValidation.cs   # Test case: validation rules
└── TestData.cs                # Source file: shared test constants/fixtures
```

XAML test projects use `.xaml` test cases instead of `.cs` and Test Activities for shared setup; the rest of the layout is the same.

## Example — Hybrid Project (XAML Root + Coded Logic)

```
OrderProcessing/
├── project.json
├── Main.xaml                  # XAML root workflow: sequences steps, handles retries
├── ScrapeOrderPortal.xaml     # XAML: UI automation with visual selector builder
├── SendConfirmationEmail.xaml # XAML: Mail activities (straightforward)
├── ProcessOrder.cs            # Coded workflow: 12 validation rules + LINQ transforms
├── OrderModels.cs             # Coded source file: Order, LineItem, ValidationResult DTOs
├── TransformHelpers.cs        # Coded source file: date parsing, currency conversion
└── TestProcessOrder.cs        # Coded test case: unit tests for ProcessOrder logic
```

### Why hybrid here

- **ScrapeOrderPortal.xaml** — UI automation benefits from XAML's visual selector builder and recording tools
- **ProcessOrder.cs** — Order validation has 12 business rules with nested conditions; coded C# is clearer and testable
- **OrderModels.cs** — Typed DTOs used by both XAML (via typed arguments) and coded workflows, eliminating DataTable column-name guessing
- **SendConfirmationEmail.xaml** — Simple Mail activity, no logic — XAML is the simpler choice
- **Main.xaml** — Orchestration is linear (scrape → process → email); XAML Sequence is readable

### Data flow

1. `Main.xaml` invokes `ScrapeOrderPortal.xaml` → returns `DataTable` via Out argument
2. `Main.xaml` invokes `ProcessOrder.cs` via Invoke Workflow File → passes raw data, returns validated `Order` objects
3. `Main.xaml` invokes `SendConfirmationEmail.xaml` → passes validated order data

## Project Structure Decision Tree

**First — coded or XAML?** For new projects, default to XAML unless the user explicitly said "coded" or named a coded-specific trigger (custom data models, complex algorithms, unit tests on business logic). See [coded-vs-xaml-guide.md](coded-vs-xaml-guide.md). The root workflow is `Main.xaml` for XAML projects and `Main.cs` for coded projects — substitute accordingly below.

**Is the entire automation a single activity/step?** (e.g. one CSV read, one email send)
- ✅ Yes → Single root workflow
- ❌ No → Default to a root orchestrator + one sub-workflow per business step. Each sub-workflow has an explicit In/Out contract and can be authored in parallel by separate agents.

**Does it involve repeated data structures?**
- ✅ Yes → Extract to Coded Source File (e.g. `Models.cs`, `InvoiceData.cs`). Required even in XAML projects — XAML cannot define types

**Is there shared logic across workflows?**
- ✅ Yes → Extract to a reusable XAML workflow (XAML projects) or a helper Coded Source File (coded or hybrid projects)

**Is it a test project?**
- ✅ Yes → One test case file per scenario. Coded test projects optionally use `CodedWorkflowHooks.cs` (partial class CodedWorkflow) for shared setup/teardown

**Does it have complex business rules?**
- ✅ Yes → Isolate in Coded Source Files for reusability and testability (extract from XAML via `Invoke Workflow File` if needed)

**Does it need both UI automation AND complex non-UI logic?**
- ✅ Yes → Hybrid: XAML for UI automation + orchestration, Coded for business logic + data models. See [coded-vs-xaml-guide.md](coded-vs-xaml-guide.md)
