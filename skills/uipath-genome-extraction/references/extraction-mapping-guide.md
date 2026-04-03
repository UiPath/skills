# Extraction Mapping Guide

After analyzing project files with [project-analysis-guide.md](project-analysis-guide.md), use these tables to map extracted signals to genome sections. Each table maps signals to specific genome section content.

## Package-to-Target-Application Mapping

Maps `dependencies` keys from `project.json` to the Target Applications section of the genome.

| Package ID | Target Application | Role |
|------------|-------------------|------|
| `UiPath.UIAutomation.Activities` | Desktop/Browser apps | UI interaction |
| `UiPath.Excel.Activities` | Excel | Data source/target |
| `UiPath.Mail.Activities` | Email (generic) | Input/output |
| `UiPath.MicrosoftOffice365.Activities` | Outlook/Office 365 | Email, Calendar, OneDrive |
| `UiPath.GSuite.Activities` | Gmail/Google Workspace | Email, Drive, Sheets |
| `UiPath.Database.Activities` | Database (SQL) | Data source/target |
| `UiPath.WebAPI.Activities` | REST APIs | Integration |
| `UiPath.PDF.Activities` | PDF files | Document processing |
| `UiPath.Word.Activities` | Microsoft Word | Document generation |
| `UiPath.Presentations.Activities` | PowerPoint | Presentation generation |
| `UiPath.IntegrationService.Activities` | Integration Service | Connector runtime |
| `UiPath.IntelligentOCR.Activities` | Document Understanding | Document AI extraction |
| `UiPath.DocumentUnderstanding.ML.Activities` | Document Understanding | ML models |
| `UiPath.Cryptography.Activities` | Encryption/Security | Data protection |
| `UiPath.Testing.Activities` | Testing framework | Validation |
| `UiPath.Persistence.Activities` | Orchestrator queues/assets | Queue management |

**Target applications become configurable.** When a package maps to a target application, add both:
1. The application to the Target Applications table in the genome
2. A Configuration Question making the application choice configurable. The original application becomes the default.

Example: project uses `UiPath.MicrosoftOffice365.Activities` -> Target Applications lists "Outlook/Office 365" AND Configuration Questions gets "Which email provider? (source project used: Outlook)".

## Platform Feature Detection

Signals that indicate platform features beyond basic package dependencies. Map to Target Applications and Configuration Questions.

| Signal | Platform Feature | Where to Check | Genome Impact |
|--------|-----------------|----------------|---------------|
| `UiPath.IntelligentOCR.Activities` or `UiPath.DocumentUnderstanding.*` in dependencies | Document Understanding | project.json | Add to Target Applications |
| `UiPath.IntegrationService.Activities` in dependencies OR `ConnectionId` in XAML OR `connections.*` in .cs | Integration Service | project.json, .xaml, .cs | Add the specific service to Target Applications. Resolve from xmlns namespace or property name -- not generic "Integration Service" |
| `UiPath.Persistence.Activities` in dependencies OR queue activities in XAML | Orchestrator Queues | project.json, .xaml | Add Configuration Question: "Which Orchestrator queue? (source project used: X)" |
| `BuildClient("Orchestrator")` in .cs | Orchestrator API | .cs files | Add Configuration Question: "Which Orchestrator tenant/folder? (source project used: default)" |
| `globalHandler` field in project.json OR `GlobalHandler.xaml` exists in file listing | Global error handling | project.json, file listing | Document in Error Handling section |
| `entryPoints` array with multiple entries in project.json | Multi-entry-point project | project.json | Document all entry points in the Workflow section |
| `.flow` files present in file listing | Maestro orchestration | file listing | Add Maestro to Build With section |
| `runtimeOptions.isAttended: true` or `runtimeOptions.requiresUserInteraction: true` | Attended automation | project.json | Note in Overview and add Configuration Question: "Attended or unattended? (source project used: attended)" |

## Error Handling Pattern Mapping

Maps source-code error patterns to the Error Handling section of the genome. Always translate to behavioral descriptions -- never include code-level detail in the genome. Associate each handler with the workflow step it protects.

| Source Pattern | XAML Signal | .cs Signal | Genome Description |
|----------------|------------|------------|-------------------|
| Retry on failure | `<RetryScope>` with `NumberOfRetries` attribute | `for` loop wrapping `try/catch` | "Retries Nx on [exception type]" |
| Catch and log | `<TryCatch>` with `<Catch>` containing `LogMessage` | `catch` block with `Log()` call | "Logs [error type] and continues" |
| Catch and rethrow | `<TryCatch>` with `<Catch>` containing `Rethrow` | `catch` block with `throw` | "Escalates [error type] to caller" |
| Global handler | `GlobalHandler.xaml` or `globalHandler` field in project.json | N/A (XAML only) | "Global error handler catches unhandled exceptions" |
| Catch specific types | `<Catch x:TypeArguments="s:TimeoutException">` | `catch (TimeoutException)` | "Handles timeout exceptions separately" |
| Queue exception | Queue-related exception activities | `system.AddQueueItem` with exception data | "Routes failed items to exception queue" |

**Rule:** Always translate to behavioral descriptions. Write "Retries 3x on timeout" not "RetryScope with NumberOfRetries=3 for TimeoutException".

### Step-Associated Error Handling Format

Associate error handlers with the workflow step they protect. This tells the rebuilding agent exactly where to place error handling.

```markdown
## Error Handling

### Step 2: Download attachments
- Email connectivity failure: retry 3x with backoff, then alert administrator
- Unreadable attachment (corrupt PDF, password-protected): flag and notify sender, skip to next email

### Step 4: Extract invoice fields
- DU extraction confidence below 80% for any field: route to human validation queue with extracted values shown
- Unsupported document format: log format type, skip, add to exception report

### Step 6: Post to ERP
- ERP posting failure: retry once, then log to exception report with full extracted data for manual entry
- Duplicate invoice detected: skip posting, log as duplicate, continue to next invoice

### Global
- Unhandled exception: log full error context, mark current item as failed, continue batch
```

## Complexity Inference from Project Signals

Determine genome complexity from project characteristics. This drives section depth per the population matrix in SKILL.md.

| Signal | Simple | Medium | Complex |
|--------|--------|--------|---------|
| Total workflow files (.xaml + .cs) | 1-3 | 4-8 | 9+ |
| Unique package dependencies | 1-3 | 4-6 | 7+ |
| Entry points | 1 | 1-2 | 3+ |
| Integration Service connections | 0 | 0-1 | 2+ |
| Error handling patterns found | 0-1 | 2-3 | 4+ |
| Orchestrator features (queues, assets) | None | Optional | Present |
| Flow files present | No | No | Yes |
| Document Understanding packages | No | Optional | Often |

**When ambiguous, default to the lower level** (same rule as the authoring skill). Complexity determines section depth per the population matrix in SKILL.md.

## Generalization Rules

Convert hardcoded values to Configuration Questions. Every configurable value gets a question with the original value as the default.

### What to Generalize

1. **Hardcoded paths** -- File paths, folder paths, network shares -> "Which file/folder path? (source project used: `C:\Invoices\Inbox`)"
2. **URLs** -- Server URLs, API endpoints, web addresses -> "Which URL/endpoint? (source project used: `https://erp.company.com/api`)"
3. **Email addresses** -- Sender, recipient, CC addresses -> "Which email address? (source project used: `invoices@company.com`)"
4. **Server and host names** -- Database servers, SMTP hosts -> "Which server? (source project used: `sql-prod-01`)"
5. **Credential names** -- Orchestrator asset names for credentials -> "Which credential asset? (source project used: `MyCredential`)"
6. **Queue names** -- Orchestrator queue names -> "Which queue? (source project used: `InvoiceQueue`)"
7. **Threshold values** -- Amounts, counts, dates, percentages -> "What threshold? (source project used: `$10,000`)"
8. **Column names** -- Excel column names, database field names -> "Which column/field names? (source project used: `VendorName, Amount, DueDate`)"
9. **Application choices** -- The specific application the project uses -> "Which [app category]? (source project used: [specific app])"

### Configuration Question Format

```
N. {Question}? (source project used: {original value})
```

Examples:
- `1. Which email provider? (source project used: Outlook)`
- `2. Which credential asset for ERP login? (source project used: ERPCredential)`
- `3. What invoice amount threshold for manager approval? (source project used: $10,000)`

## Workflow Depth Rules

The Workflow section must contain enough detail that an agent can rebuild the solution without seeing the original project. Every step that does something distinct gets its own entry. Non-trivial steps get substeps.

### When to Use Substeps

Add substeps (a, b, c...) when a step involves:
- **Multiple fields or data points** being read, written, or transformed
- **Conditional logic** (if/switch) that branches behavior
- **Data validation** with specific rules
- **Data transformation** (mapping, calculating, formatting)

### Workflow Step Format

```markdown
N. **Step name**: One-sentence summary of the business action.
   a. [Substep with specific field/data detail]
   b. [Substep with specific field/data detail]
   c. [Conditional: if {condition}, then {action}; otherwise {action}]
```

### Data Flow Annotations

For each step, include what data enters and what comes out when this is not obvious:
- **Input data**: What fields/records this step reads (from prior step, file, or application)
- **Output data**: What fields/records this step produces for downstream steps
- **Transformations**: Any calculations, mappings, or reformatting

### Example: Shallow vs Deep

**Shallow (insufficient for replication):**
```
3. **Validate**: Check the invoice against the purchase order.
```

**Deep (sufficient for replication):**
```
3. **Validate invoice against purchase order**:
   a. Match vendor_id from extracted invoice fields to vendor master lookup
   b. Match PO number (if present in invoice) to open POs for that vendor
   c. For each line item: verify description, quantity, and unit_price match the PO line
   d. Calculate line totals (quantity x unit_price) and verify they sum to invoice subtotal
   e. Verify subtotal + tax = invoice total (tolerance: configurable, default 1%)
   f. If any mismatch exceeds tolerance, flag the invoice with the specific discrepancy field and values
```

### Example: Data Flow

```
4. **Extract invoice fields** (input: PDF attachment; output: structured invoice record):
   a. Extract: invoice_number, invoice_date, vendor_name, vendor_id, PO_number
   b. Extract line items: description, quantity, unit_price, line_total (one per row)
   c. Extract totals: subtotal, tax_amount, total_amount, currency
   d. If any field has extraction confidence below 80%, flag it with *[Inferred from project signals]*
```

## Business Rule Extraction

Translate code constructs to natural-language business rules for the Business Rules section of the genome. Never include programming syntax in the genome.

### Step-Associated Format

Associate every business rule with the workflow step where it applies. This lets the rebuilding agent know exactly where each rule fires.

```markdown
## Business Rules

### Step 3: Validate invoice
- If invoice amount exceeds $10,000 and category is Premium, route to manager approval queue
- Duplicate detection: skip if invoice_number + vendor_id already exists in ERP
- Three-way match required when PO is present: PO line items, goods receipt, invoice line items

### Step 5: Route exceptions
- Invoices without a PO number go to manual review (not auto-rejected)
- Tolerance threshold for amount mismatches: configurable (default 1%)
```

If a business rule applies globally (not to a specific step), group under a "General" heading.

### Translation Rules

| Code Construct | Source | Genome Translation |
|----------------|--------|-------------------|
| `If` / `FlowDecision` | XAML | "If [condition in plain English], then [action]" |
| `Switch` / `FlowSwitch` | XAML | "Route based on [variable]: [case] -> [action], [case] -> [action]" |
| `if` / `switch` | .cs | Same patterns as XAML, using C# conditions |
| VB `AndAlso` | XAML (VB) | "and" |
| VB `OrElse` | XAML (VB) | "or" |
| VB `&` (string) | XAML (VB) | Concatenation (omit from genome, describe the result) |
| C# `&&` | .cs | "and" |
| C# `\|\|` | .cs | "or" |
| Comparison operators | XAML/C# | Natural language: `>` -> "exceeds", `<` -> "is less than", `=`/`==` -> "is", `<>` -> "is not" |

### Expression Language Awareness

Check `expressionLanguage` in `project.json` to know which syntax you are reading in XAML:
- **VisualBasic** -- Expressions use VB operators: `AndAlso`, `OrElse`, `&`, `=`, `<>`
- **CSharp** -- Expressions use C# operators: `&&`, `||`, `+`, `==`, `!=`

### Examples

- `Amount > 10000 AndAlso Category = "Premium"` -> "If amount exceeds $10,000 and category is Premium"
- `switch (status) { case "Approved": ... case "Rejected": ... }` -> "Route based on status: Approved -> [action], Rejected -> [action]"
- `invoiceDate < DateTime.Now.AddDays(-30)` -> "If invoice date is more than 30 days old"

## Acceptance Criteria Derivation

Generate acceptance criteria for the Acceptance Criteria section of the genome. Each criterion describes a functional outcome, not a code-level assertion. Include criteria that verify data transformations and field mappings — these are the most commonly missed.

### Derivation Sources

1. **Workflow steps** -- Each major workflow step produces at least one criterion
2. **Data transformations** -- Each field mapping, calculation, or format conversion produces one criterion
3. **Error handling patterns** -- Each error handling pattern produces one criterion
4. **Business rules** -- Each business rule produces one criterion

### Pattern

```
Given [specific input], [specific observable outcome]
```

### Criterion Categories

1. **Happy path** -- each workflow step completes and produces expected output
2. **Data fidelity** -- specific fields are extracted/mapped/transformed correctly
3. **Business rule enforcement** -- each rule triggers the correct behavior
4. **Error recovery** -- each error handler produces the correct fallback behavior
5. **Edge cases** -- empty inputs, duplicates, malformed data handled without crashing

### Ban List

Do not write acceptance criteria that reference code-level details. These patterns are banned:

- "Uses [activity name]" -- e.g., "Uses ReadPDF activity"
- "Calls [workflow file]" -- e.g., "Calls ProcessInvoice.xaml"
- "Reads [variable name]" -- e.g., "Reads invoiceData variable"
- "Assigns [value] to [variable]" -- e.g., "Assigns true to isValid"

### Good vs Bad Examples

| Bad (Code-level) | Good (Behavioral) |
|-------------------|-------------------|
| "Uses ReadPDF activity to process InvoiceFile variable" | "Given an invoice PDF, extracts vendor_name, invoice_number, line_items (description, qty, unit_price), tax, and total" |
| "Calls ValidateInvoice.xaml with in_Amount argument" | "Given extracted line items, verifies each line_total = qty x unit_price and sum of line_totals + tax = invoice total within configured tolerance" |
| "SendMail activity sends email to admin@company.com" | "When processing fails after retries, sends a notification to the configured administrator with the invoice_number and failure reason" |
| "ForEach loop iterates through dt_Invoices DataTable" | "Processes all invoices in the input batch sequentially, logging success/failure per invoice_number" |

## Build With Section

Map each workflow step to the appropriate skill using the decision tree in the [skill-mapping-guide.md](../../shared/genome/skill-mapping-guide.md). Do not duplicate the decision tree here -- reference it directly.

For mixed XAML + coded workflow projects: each genome workflow step maps to one file type and therefore one skill. If a `.xaml` workflow calls a `.cs` helper, the calling step uses the caller's skill. The helper becomes its own step if it represents a distinct business action.
