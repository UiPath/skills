# Coded vs XAML Decision Guide

When to use coded workflows (C#), XAML workflows (low-code), Coded Source Files, or InvokeCode — and how they interact in hybrid projects.

## Decision Flowchart

Follow top-down. Stop at the first match.

0. **Did the user specify a mode?** ("coded workflow", "XAML workflow", "create a .cs file", "low-code") → **Use what they asked for. Do not second-guess.**
1. **Check the project's existing mode.** Match it unless there is a clear reason not to:
   - **XAML-only project** → default to XAML. Only go coded if steps 3-6 below apply.
   - **Coded-only project** → default to coded. Activities (Excel, Mail, UI automation) are available via services on `CodedWorkflow`.
   - **Hybrid project** → either mode is fine; pick the one that fits the task best using steps 2-8.
   - **New project** → continue to step 2.
2. **Can existing activities handle the task directly?** (read Excel, send email, move file, UI click/type, queue processing, connector calls) → **Use the project's current mode.** Both XAML activities and coded services can do these. No mode switch needed.
3. **Does it define data models, DTOs, enums, or custom classes?** → **Coded Source File** (plain `.cs`, no `CodedWorkflow` base). XAML cannot define types — this is the one case where going hybrid is always justified.
4. **Does it involve complex logic?** (5+ branches, LINQ queries, regex, algorithms, REST API calls with pagination/retry) → **Coded Workflow**. Both modes can handle logic, but coded is significantly clearer past 3-4 decision nodes.
5. **Does it need unit tests or assertions on business logic?** → **Coded Workflow** + **Coded Test Case**.
6. **Is it reusable utility code?** (helpers, formatters, validators, extension methods) → **Coded Source File**.
7. **Is it a new project and still ambiguous?** → Ask the user. If they have no preference, default to XAML — it is the more common mode in UiPath projects.
8. **Default** → match the project's dominant mode.

---

## Use Coded Workflows When

1. **Custom data models** — You need classes with properties to represent business entities (`InvoiceLineItem`, `CustomerRecord`). Without coded source files, you're stuck with `DataTable` or `Dictionary<string, object>` and lose type safety.
   ```csharp
   // Coded Source File: OrderModels.cs
   public class OrderLine { public string ProductId; public decimal Price; public int Qty; }
   ```

2. **Complex data transformation** — JSON deserialization into typed objects, CSV parsing with conditional logic, LINQ aggregation, regex extraction. Coded gives you full `System.Text.Json`, LINQ, and string interpolation without nested InvokeCode activities.

3. **Heavy branching logic** — Nested if/else-if chains, switch statements with 5+ cases, loops with `break`/`continue`. XAML flowcharts become unreadable past 3-4 decision nodes.

4. **REST API integrations** — Building HTTP requests, handling pagination, managing auth tokens with retry logic. `HttpClient` patterns in C# are far cleaner than chaining HTTP Request + Deserialize JSON activities.

5. **Reusable utility libraries** — Date formatting, validation helpers, encryption, file path manipulation. Define as a Coded Source File, callable from any workflow.

6. **Unit-testable business logic** — Pure functions (input → output, no UI) that need automated assertions. Coded Test Cases can call coded workflows directly.

7. **Algorithm-heavy work** — Sorting, deduplication, fuzzy matching, tree traversal — anything that would require dozens of Assign + If activities in XAML.

---

## Use XAML Workflows When

1. **UI automation with interactive selector configuration** — When you need the visual selector builder, element recording, or indication tools. Note: coded workflows also support UI automation via Object Repository + `uiAutomation` service, but XAML's visual tooling is more convenient for building selectors interactively.

2. **Simple linear processes** — Read Excel → filter rows → send email → move file. When the process is a straight pipeline of 5-10 activities with minimal branching, XAML is readable and fast to build.

3. **Activity-rich integrations** — SAP, Salesforce, ServiceNow, and other connectors where pre-built activity packages handle authentication, pagination, and error handling out of the box.

4. **Process orchestration** — REFramework, queue-based transaction processing, retry patterns. The XAML templates for these are battle-tested.

5. **Activities are straightforward** — If every step maps directly to an available activity and the logic between them is trivial, XAML is the simpler choice.

---

## InvokeCode: When to Extract

InvokeCode embeds C#/VB code inline in a XAML activity. It works for small snippets but becomes a maintenance problem quickly.

### Extraction Rules

1. **Code exceeds ~15 lines** → extract to a Coded Source File (utility) or Coded Workflow (if it needs `CodedWorkflow` services).
2. **Code defines classes or types** → extract to a Coded Source File. InvokeCode cannot define reusable types.
3. **Same code is copy-pasted across multiple XAML files** → extract to a Coded Workflow and invoke it via `Invoke Workflow File`.
4. **Code needs unit tests** → extract to a Coded Workflow + Coded Test Case.
5. **Code uses complex .NET APIs** (HttpClient, LINQ, JSON serialization) → extract to a Coded Workflow for better readability and error handling.

### Comparison Table

| Criterion | InvokeCode | Coded Source File | Coded Workflow |
|-----------|-----------|-------------------|----------------|
| **Where it lives** | Inline in XAML activity | Standalone `.cs` file | `.cs` file |
| **Inherits CodedWorkflow** | No | No | Yes |
| **Access to services** (`excel`, `mail`, etc.) | No | No | Yes |
| **Can define classes/types** | No | Yes | No (one class per file, must be workflow) |
| **Reusable across workflows** | No (copy-paste) | Yes (import namespace) | Yes (invoke from any workflow) |
| **Unit testable** | No | Indirectly | Yes (via Coded Test Case) |
| **Recommended max size** | ~15 lines | No limit | No limit |
| **Entry point in project.json** | N/A | No | Process only |

---

## Hybrid Project Patterns

Hybrid projects mix coded and XAML files. The `workflows` property provides strongly-typed access to **all** workflows — both `.cs` and `.xaml` — so there is no friction in cross-invocation.

### Interop Mechanisms

| From | To | Mechanism | Notes |
|------|----|-----------|-------|
| XAML | Coded Workflow | Invoke Workflow File (path to `.cs` file) | Arguments via In/Out parameters |
| Coded | XAML Workflow | `workflows.XamlName()` | Strongly typed, same as coded-to-coded |
| Coded | Coded Workflow | `workflows.Name()` | Strongly typed |
| Any | Any (dynamic) | `RunWorkflow("path", dict)` | String-based fallback — use only when path is determined at runtime |

### Pattern 1: XAML Orchestrator + Coded Logic

XAML handles sequencing and simple activities. Coded workflows handle complex business logic. Coded Source Files define shared data models.

```
OrderProcessing/
├── project.json
├── Main.xaml                    # XAML: orchestrates the full process
├── ScrapeOrderPortal.xaml       # XAML: UI automation with selectors
├── SendConfirmationEmail.xaml   # XAML: Mail activities (straightforward)
├── ValidateAndTransform.cs      # Coded workflow: 12 validation rules + LINQ transforms
├── OrderModels.cs               # Coded source file: Order, LineItem, ValidationResult
└── TransformHelpers.cs          # Coded source file: date parsing, currency conversion
```

**When to use:** The process has a clear linear flow (orchestrate in XAML) but contains pockets of complex logic (coded workflows) and needs typed data models (coded source files).

### Pattern 2: Coded Orchestrator + XAML for Activities

Coded workflow drives the process. XAML workflows wrap activity-heavy steps that are simpler to express visually.

```
InvoiceProcessor/
├── project.json
├── Main.cs                      # Coded: orchestrates, calls all steps
├── ExtractInvoiceData.cs        # Coded: PDF parsing + JSON deserialization
├── PostToSAP.xaml               # XAML: SAP connector activities
├── GenerateReport.xaml           # XAML: Excel activities (write range, format, save)
├── InvoiceModels.cs             # Coded source file: Invoice, LineItem DTOs
└── TestExtractInvoice.cs        # Coded test case
```

**When to use:** The core logic is algorithmic (coded) but some steps are best expressed with pre-built activity packages (SAP, Excel).

### Pattern 3: Shared Data Models

Coded Source Files define typed models that both XAML and coded workflows use via arguments.

```
// OrderModels.cs — Coded Source File (no CodedWorkflow, no entry point)
namespace OrderProcessing
{
    public class Order
    {
        public string OrderId { get; set; }
        public string CustomerName { get; set; }
        public List<LineItem> Items { get; set; }
        public decimal Total => Items?.Sum(i => i.Price * i.Quantity) ?? 0;
    }

    public class LineItem
    {
        public string ProductId { get; set; }
        public decimal Price { get; set; }
        public int Quantity { get; set; }
    }
}
```

Both XAML workflows (via typed arguments) and coded workflows (via direct reference) can use these types, eliminating `DataTable` column-name guessing and `Dictionary` key typos.

---

## Anti-Patterns

1. **50+ lines of C# in InvokeCode.** Extract to a Coded Source File or Coded Workflow.
2. **Using `RunWorkflow("path")` when `workflows.*` is available.** The `workflows` property is strongly typed and works for both `.cs` and `.xaml` files.
3. **Duplicating logic in both XAML and coded form.** Pick one, invoke it from the other.
4. **Using `DataTable` or `Dictionary<string, object>` when a typed class would prevent errors.** Create a Coded Source File with a proper class.
5. **Assuming UI automation requires XAML.** Coded workflows support UI automation via Object Repository + `uiAutomation` service. Use XAML only when the visual selector builder is specifically needed.
6. **Overriding the user's explicit choice.** If the user says "coded workflow", create a coded workflow — do not suggest XAML instead.

---

## Related References

- [coded/operations-guide.md](coded/operations-guide.md) — How to create coded workflows, test cases, and source files
- [coded/coding-guidelines.md](coded/coding-guidelines.md) — C# coding rules and common issues
- [xaml/workflow-guide.md](xaml/workflow-guide.md) — XAML workflow creation and editing
- [xaml/common-pitfalls.md](xaml/common-pitfalls.md) — InvokeCode language property gotcha
- [../assets/project-structure-examples.md](../assets/project-structure-examples.md) — Project layout examples including hybrid
