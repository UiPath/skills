# Designing Project Structure

When creating a project, **proactively design the right file structure** based on the task complexity. Do not put everything into a single root workflow file. Use your best judgment to split the project into multiple files following good software engineering practices.

For the coded vs XAML decision, see [coded-vs-xaml-guide.md](coded-vs-xaml-guide.md). For new projects, the default is XAML — examples below lead with XAML and note where the coded equivalent differs.

## Guidelines

- **Single simple task** (e.g. "read a CSV and log it") — one workflow file (`Main.xaml` for XAML projects, `Main.cs` for coded) is fine
- **Multi-step process** (e.g. "read invoices, validate, post to system") — split into multiple workflow files, each handling one step. The root workflow invokes each step
- **Shared data structures** — extract into a Coded Source File (e.g. `Models.cs`, `InvoiceData.cs`). XAML cannot define types, so a Coded Source File is the right home even in an otherwise XAML project
- **Repeated logic** — in XAML projects, extract into a reusable XAML workflow. In coded or hybrid projects, extract into a helper Coded Source File (e.g. `ValidationHelpers.cs`)
- **Test project** — one test case per scenario. Coded test projects optionally use `partial class CodedWorkflow : IBeforeAfterRun` in `CodedWorkflowHooks.cs` for shared setup. XAML test projects use Test Activities for shared setup
- **Complex domain logic** — isolate business rules so they can be unit-tested and reused (Coded Source File for typed logic, or a separate workflow for activity-driven logic)

## Designing for Reuse

Structure decisions that keep components extractable later.

### Single responsibility

One workflow file = one meaningful action, named for it (`ProcessInvoice.xaml`, `LoginToApplication.xaml`). Split a workflow when it exceeds ~20-30 activities.

### Standard folder shape

For multi-step processes, organize by layer:

```
Project/
├── Main.xaml              # High-level orchestration only
├── Framework/             # Init, cleanup, error handling, app open/close
├── BusinessLogic/         # Process-specific rules and transactions
├── Utilities/             # Process-agnostic helpers (formatters, screenshots)
└── Data/                  # Config files, templates
```

### Separate business logic from UI components

UI workflows interact with applications and carry zero business rules; business-logic workflows decide and never touch the UI. Make read and write distinct invocable components — `GetCustomerInfo.xaml` and `ChangeCustomerInfo.xaml`, not one `HandleCustomer.xaml`. When the target application's UI changes, only the UI workflows need fixing; when a business rule changes, the UI workflows are untouched. Process-agnostic UI components are also the ones worth promoting to a shared library later.

### Composition and argument naming

Compose via `Invoke Workflow File` (coded: `workflows.StepName()`). Process workflow arguments use directional prefixes — `in_InvoiceId`, `out_Result`, `io_Browser` — so data flow is visible at every invocation site. Exception: library public workflows drop the prefixes ([library-authoring-guide.md § The Public-Workflow Contract](library-authoring-guide.md)).

### Layout and scale-out

- Sequence vs Flowchart vs State Machine per workflow: Workflow Types table in SKILL.md § XAML Workflows Quick Reference
- High-volume transactional work: dispatcher/performer split via queues — [reframework-guide.md § Execution Mode: Queue-Driven](reframework-guide.md)

### Promotion ladder

Promote logic only as reuse materializes:

1. **Inline** — used once in one workflow
2. **Separate workflow file** — reused within the project
3. **Shared library** — reused across projects ([library-authoring-guide.md](library-authoring-guide.md))
4. **UI Library** — selectors shared across projects ([ui-automation-guide.md § Object Repository as a Published UI Library](ui-automation-guide.md))

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

**Is it a single, simple task?**
- ✅ Yes → Single root workflow

**Is it a multi-step process?**
- ✅ Yes → A root workflow that invokes each step + separate workflow files for each step

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
