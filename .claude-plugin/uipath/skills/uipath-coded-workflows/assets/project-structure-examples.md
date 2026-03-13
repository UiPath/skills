# Designing Project Structure

When creating a project, **proactively design the right file structure** based on the task complexity. Do not put everything into a single `Main.cs` file. Use your best judgment to split the project into multiple files following good software engineering practices.

## Guidelines

- **Single simple task** (e.g. "read a CSV and log it") — one workflow file (`Main.cs`) is fine
- **Multi-step process** (e.g. "read invoices, validate, post to system") — split into multiple workflow files, each handling one step. `Main.cs` orchestrates by calling `workflows.StepName(...)` for each step
- **Shared data structures** — extract into a Coded Source File (e.g. `Models.cs` or `InvoiceData.cs`)
- **Repeated logic** — extract into helper Coded Source Files (e.g. `ValidationHelpers.cs`, `DataTransformations.cs`)
- **Test project** — one test case per scenario, shared setup in `CodedWorkflowBase.cs` with `IBeforeAfterRun`
- **Complex domain logic** — isolate business rules in source files so they can be unit-tested and reused

## Example — Well-Structured Invoice Processing Project

```
InvoiceProcessor/
├── project.json
├── Main.cs                    # Orchestrator: calls each step via workflows.StepName()
├── Main.cs.json
├── ReadInvoices.cs            # Step 1: reads invoices from Excel
├── ReadInvoices.cs.json
├── ValidateInvoices.cs        # Step 2: validates data
├── ValidateInvoices.cs.json
├── PostToERP.cs               # Step 3: posts to external system
├── PostToERP.cs.json
├── InvoiceData.cs             # Source file: data model
└── ValidationHelpers.cs       # Source file: validation utilities
```

### Main.cs Orchestrator Using Strongly-Typed Workflow Invocation

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
├── CodedWorkflowBase.cs             # Source file: base class with Before/After hooks (IBeforeAfterRun)
├── TestLoginFlow.cs            # Test case: login scenario (inherits from CodedWorkflowBase)
├── TestLoginFlow.cs.json
├── TestInvoiceCreation.cs      # Test case: create invoice scenario (inherits from CodedWorkflowBase)
├── TestInvoiceCreation.cs.json
├── TestInvoiceValidation.cs    # Test case: validation rules (inherits from CodedWorkflowBase)
├── TestInvoiceValidation.cs.json
├── TestData.cs                 # Source file: shared test constants/fixtures
└── PageHelpers.cs              # Source file: UI interaction helpers
```

## Project Structure Decision Tree

**Is it a single, simple task?**
- ✅ Yes → Single `Main.cs` workflow

**Is it a multi-step process?**
- ✅ Yes → Orchestrator `Main.cs` + separate workflow for each step

**Does it involve repeated data structures?**
- ✅ Yes → Extract to Coded Source File (e.g. `Models.cs`, `InvoiceData.cs`)

**Is there shared logic across workflows?**
- ✅ Yes → Extract to helper Coded Source File (e.g. `Helpers.cs`, `Utilities.cs`)

**Is it a test project?**
- ✅ Yes → One test case file per scenario + optional `CodedWorkflowBase.cs` for shared setup/teardown

**Does it have complex business rules?**
- ✅ Yes → Isolate in Coded Source Files for reusability and testability
