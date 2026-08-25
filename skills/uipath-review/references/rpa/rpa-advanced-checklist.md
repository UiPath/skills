# RPA Advanced Review Checklist

Advanced review criteria for UiPath RPA projects. Use alongside the core [rpa-review-checklist.md](rpa-review-checklist.md) for in-depth reviews.

> Load this checklist when the review requires deeper analysis beyond structural validity and basic best practices — e.g., pre-production quality gates, inherited project audits, or performance-sensitive automations.

## 1. Project Organization and Modularity

> **Structural metrics — never use "lines" as a measure.** For XAML, count **activities**, **root-scope variables**, **arguments**, **max nesting depth**, and **invoke-workflow count**. For `.cs` coded workflows, count **methods**, **statements** (LOC excluding blank/comment), and **classes**. "2255 lines" is meaningless — "84 activities, 50 root-scope variables, 12 levels deep" is actionable.

### Folder Structure

| Check | Severity | How to Verify |
|---|---|---|
| Logical folder structure used (e.g., Framework/, BusinessLogic/, Utilities/, Data/) | Info | `ls` project root — check for meaningful subdirectories |
| No workflow files dumped at project root (except Main.xaml) | Warning | Glob `*.xaml` at root — only Main.xaml and framework files expected |
| Data files separated from logic (Config.xlsx in Data/, templates in Templates/) | Info | Check file placement |
| Test files separated from production code | Info | Check for Tests/ folder or test project |

### Main.xaml Quality

| Check | Severity | How to Verify |
|---|---|---|
| Main.xaml acts as orchestrator only (delegates to sub-workflows) | Warning | Read Main.xaml — should contain mostly Invoke Workflow calls, not business logic |
| Main.xaml has <30 activities | Warning | Count activities in Main.xaml |
| High-level flow is understandable from Main.xaml alone | Info | Review Main.xaml structure |

### Workflow Design

| Check | Severity | How to Verify |
|---|---|---|
| Each workflow has a single, clear responsibility | Warning | Review workflow names and content — one purpose per file |
| Workflow layout matches complexity: Sequence for linear, Flowchart for branching, State Machine for state-based | Info | Check layout type vs logic pattern |
| No workflows exceeding 50 activities | Warning | Count activities per workflow |
| Reusable logic extracted into separate workflows or libraries | Info | Look for duplicated logic across workflows |
| Library extraction candidates identified (logic used by 2+ projects) | Info | Check for workflows that could be shared |
| Navigation separated from page actions | Warning | A workflow should either navigate to a page OR perform actions on it — not both. Mixing means a navigation failure forces re-executing the action logic on retry. |
| Data extraction separated from data filtering/transformation | Warning | A workflow that scrapes a table AND filters it has two failure modes tangled together. Extract in one workflow, transform in another. |
| No app-specific NavigateTo workflows when a shared utility works | Info | If multiple workflows each have their own `NavigateToInvoicePage.xaml`, `NavigateToOrderPage.xaml` — extract a shared `Browser_NavigateToUrl.xaml` that takes a URL argument. |
| Login logic inside the Launch workflow (not a separate Login.xaml) | Info | Login is part of app initialization. Separating it from Launch creates a gap where the app is open but unauthenticated — a fragile state. Keep launch + login as one atomic step. |

### Activity Project Settings

| Check | Severity | How to Verify |
|---|---|---|
| Default timeout configured for UI activities | Info | Check project settings → Activity defaults |
| Default input method configured (SimulateClick, SendWindowMessages) | Info | Check activity default settings |
| Consistent timeout/retry values across similar activities | Info | Compare activity properties |

## 2. Selector Robustness

### Modern UI Descriptors (Unified Target Method)

| Check | Severity | How to Verify |
|---|---|---|
| Modern design experience used (not classic) | Info | Check project settings for design experience |
| Unified Target configured: Strict Selector + Fuzzy Selector + Image + Anchor | Info | Grep `.xaml` for `NUnifiedTargetDefinition` |
| Anchor configured for elements in dynamic/data-driven UIs | Warning | Check anchor definitions in UI activities |
| Fuzzy selector enabled as fallback for elements with minor text changes | Info | Check fuzzy selector configuration |
| Image targeting configured as last-resort fallback | Info | Check image targeting in descriptor |

### Container-Based Design

| Check | Severity | How to Verify |
|---|---|---|
| UI activities use partial selectors inside `Use Application/Browser` containers | Warning | Check for `NApplicationCard` containers wrapping UI activities |
| No standalone full selectors when a container is available | Warning | Check for full selectors outside containers |
| Application scope opened once, not reopened per action | Warning | Check for redundant `Use Application/Browser` blocks |

### Selector Resilience

| Check | Severity | How to Verify |
|---|---|---|
| No screen resolution or DPI dependencies in selectors | Warning | Grep for pixel-based attributes or resolution-specific values |
| Variables used for dynamic portions of selectors (not string concatenation) | Info | Check selector construction patterns |
| Frame/iFrame handling correct for web applications | Warning | Check for frame tags in web selectors |
| Virtual environment handling configured (Citrix/RDP extension, Computer Vision) | Warning | Check for Citrix/RDP-specific patterns if applicable |
| Element Exists / Check App State used before interactions with dynamic elements | Info | Check for pre-validation activities |

### Object Repository Organization

If the project uses Object Repository for centralized UI element management:

| Check | Severity | How to Verify |
|---|---|---|
| UI elements captured into Object Repository (not defined inline in activities) | Warning | Check `.objects/` folder usage vs inline selectors in `.xaml` |
| Elements organized hierarchically: Application → Screen → Element | Warning | Review `.objects/` structure |
| Naming hierarchical and business-meaningful (`SAP_GUI.SalesOrder.SubmitButton`, not `Button32`) | Warning | Review descriptor names |
| PascalCase used consistently across descriptors | Info | Check naming conventions |
| No duplicate descriptors for the same UI element | Warning | Search for duplicate selectors targeting same element |
| Reusable descriptors extracted into a UI Library (separate published artifact) | Info | Check for UI Library reference in `project.json` dependencies |
| Per-process descriptors kept local; org-wide descriptors in shared UI Library | Info | Compare local Object Repository to consumed UI Libraries |

### UI Library (Published Object Repository)

If the project consumes or is a UI Library:

| Check | Severity | How to Verify |
|---|---|---|
| UI Library versioned semantically (UI-shape changes = major, selector fixes = patch) | Warning | Check UI Library version history |
| Consumer projects pin to specific UI Library version | Warning | Check `project.json` dependencies for exact version brackets |
| Healing Agent fixes promoted into UI Library (so all consumers benefit) | Info | Check whether healed selectors are propagated to library |
| One UI Library per corporate application (SAP, Salesforce) — not mixed | Warning | Review UI Library scope |
| UI Library ownership clear (CoE for org-wide, team for team-specific) | Info | Check CODEOWNERS or library catalog |

## 3. Variable and Scope Hygiene

| Check | Severity | How to Verify |
|---|---|---|
| Variable scope minimized — variables scoped to innermost container that uses them | Warning | Review variable scope in XAML (check `Scope` property) |
| No project-wide variables used for inter-workflow communication (use arguments) | Warning | Check for variables with top-level scope passed implicitly |
| Specific types used instead of `Object` or `String` for typed data (Int32, Decimal, DateTime, Boolean) | Warning | Check variable types — flag `Object` or `String` for numeric/date/boolean data |
| Constants used for magic numbers and fixed values (not inline literals) | Info | Grep for repeated literal values in expressions |
| DataTable variables use typed columns (not generic Object) | Info | Check DataTable construction |
| No unused arguments on workflow interfaces | Warning | Workflow Analyzer rule ST-USG-009 covers variables; manually check arguments |
| Argument descriptions populated for public entry points | Info | Read argument metadata in entry point workflows |

## 4. Data Manipulation Patterns

| Check | Severity | How to Verify |
|---|---|---|
| Null/empty checks before string operations | Warning | Check for `.ToString()`, `.Split()`, `.Substring()` on potentially null values |
| Input data trimmed from external sources (`.Trim()` on user input, file data, web scrapes) | Info | Check data processing near input boundaries |
| DataTable columns use specific types (String, Int32, DateTime) not default Object | Info | Check `Build Data Table` or DataTable construction |
| LINQ queries preferred over nested For Each loops for filtering/searching | Info | Check for nested loops that could be LINQ |
| LINQ expressions are readable (not single-line 200-char chains) | Info | Review LINQ complexity |
| DateTime operations use `ParseExact` with explicit format strings (not `Parse`) | Warning | Grep for `DateTime.Parse` — should be `DateTime.ParseExact` |
| No DataTable modification during iteration (clone before modifying) | Warning | Check for `Remove Row` or `Add Row` inside `For Each Row` loops |
| String concatenation in loops uses `StringBuilder` for large volumes | Info | Check for `+=` string concatenation inside loops |

## 5. Error Handling Depth

### Finally Block Usage

| Check | Severity | How to Verify |
|---|---|---|
| Try-Catch blocks include Finally for resource cleanup | Warning | Check Try-Catch activities for Finally sections |
| File handles closed in Finally blocks (not just in Try) | Warning | Check file I/O patterns — Excel, text files, CSV |
| Application scopes closed in Finally blocks when not using `Use Application/Browser` | Warning | Check application lifecycle management |
| Database connections disposed in Finally blocks | Warning | Check database activity patterns |

### Exception Handling Patterns

| Check | Severity | How to Verify |
|---|---|---|
| Exception logged with context before re-throwing or handling | Warning | Check Catch blocks — log should precede Rethrow |
| Specific exception types caught (not only generic `System.Exception`) | Warning | Check Catch block exception types |
| Retry Scope wraps activities prone to transient UI failures (Click, Type Into) | Info | Check for Retry Scope around UI activities |
| Retry Scope configured with appropriate count (2-3) and interval | Warning | Check Retry Scope properties |
| ContinueOnError used only with explicit annotation explaining why | Warning | Grep for `ContinueOnError="True"` — each instance should have a comment |
| No silent exception swallowing (catch + ignore without logging) | Warning | Workflow Analyzer rule ST-DBP-003 covers empty catch; also check Catch blocks that only have Assign activities |

## 6. Testing Maturity

### Test Design Quality

| Check | Severity | How to Verify |
|---|---|---|
| Coded tests follow Arrange-Act-Assert pattern | Info | Read `[TestCase]` methods — verify three-phase structure |
| Test names describe scenario and expected outcome (e.g., `Test_ProcessInvoice_ValidData_ReturnsSuccess`) | Info | Review test naming patterns |
| Each test verifies specific outcomes (not just "no exception thrown") | Warning | Check assertions — `Assert.AreEqual`, `Verify Expression`, not empty |
| Tests are independent — no shared state between test cases | Warning | Check for setup/teardown that resets state |
| Screenshot captured on test failure for debugging | Info | Check for screenshot activity in test Catch blocks |

### Test Data Management

| Check | Severity | How to Verify |
|---|---|---|
| Tests use synthetic/test data — never production data | Warning | Check test data sources for production DB/API connections |
| Test data is parameterized via `.variations/` files or external data sources | Info | Check for `.variations/` directory or data-driven test patterns |
| Test state reset before each test run (known starting state) | Warning | Check for setup/initialization in test workflows |
| Test data does not contain PII or sensitive information | Critical | Review test data files for personal data |

### CI/CD Integration

| Check | Severity | How to Verify |
|---|---|---|
| Smoke tests exist and can run on every commit | Warning | Check for tagged smoke tests |
| Regression test suite defined for deployment validation | Info | Check for tagged regression tests |
| Test results tracked in UiPath Test Manager | Info | Check Test Manager configuration |
| Test failure blocks production deployment | Info | Check CI/CD pipeline configuration |

## 7. Idempotent Processing

### Queue Item Processing Safety

| Check | Severity | How to Verify |
|---|---|---|
| Queue item processing is safe to retry (no duplicate records on re-execution) | Warning | Review Process.xaml — check if re-processing creates duplicates |
| Status checks before write operations (don't re-process already-completed items) | Warning | Check for "already processed" guards before mutations |
| External system writes are idempotent or guarded by unique keys | Warning | Check API calls and database writes for idempotency patterns |
| File operations check for existing output before creating new (no duplicate files) | Info | Check file write operations for existence checks |

### Non-Queue REFramework Status Tracking

| Check | Severity | How to Verify |
|---|---|---|
| Source data status column updated after each transaction | Warning | Read SetTransactionStatus.xaml — verify source data update |
| Status values distinguish Success, Business Exception, System Exception | Warning | Check status value assignments |
| Process can resume from last incomplete item after interruption | Info | Check GetTransactionData.xaml — verify it skips completed items |
| Data refresh handling documented (what if source data changes during processing) | Info | Check for data staleness handling |

## 8. Debugging Hygiene

| Check | Severity | How to Verify |
|---|---|---|
| No leftover breakpoints in production code | Warning | Grep `.xaml` for breakpoint metadata (`sap2010:WorkflowViewState.IdRef` with breakpoint settings) |
| No `Write Line` activities (use `Log Message` instead) | Warning | Workflow Analyzer rule ST-MRD-011 |
| No debug-only variables or hardcoded test values | Warning | Check for variables named `debug_*`, `test_*`, or hardcoded test data |
| Debug configuration removed (no `Is Debug` switches left active) | Info | Check for debug flags in Config.xlsx or project settings |
| No commented-out activities or dead code paths | Info | Check for disabled activities in XAML |

## 9. Logging Completeness

### Workflow Boundary Logging

| Check | Severity | How to Verify |
|---|---|---|
| Log Message at start and end of each invoked workflow | Warning | Check first/last activities in each workflow |
| Logs include workflow name and key input argument values | Info | Review Log Message content |
| Error-level log in every Catch block with full exception details (Message + StackTrace + Source) | Warning | Check Catch blocks — verify exception properties logged, not just `Exception.Message` |
| No Verbose/Trace-level logging configured for production | Info | Check log level settings — PROD should be Info, DEV should be Trace |

### Correlation and Traceability

| Check | Severity | How to Verify |
|---|---|---|
| Transaction reference / queue item ID included in log messages | Warning | Check Log Message content in ProcessTransaction for reference field |
| Cross-process correlation ID passed between Dispatcher and Performer | Info | Check if Dispatcher embeds a correlation ID in queue item SpecificContent |
| Add Log Fields used for business context (transaction type, customer ID) | Info | Grep for `Add Log Fields` activity usage |
| Log output matches Orchestrator monitoring expectations | Info | Verify log structure supports dashboard/alert filtering |

## 10. Output Verification

### Write Operation Verification

| Check | Severity | How to Verify |
|---|---|---|
| Critical data writes followed by verification step (read-back, count check, status code) | Warning | After Write Range, HTTP POST, database INSERT — check for verification activity |
| HTTP response status codes validated after API calls (not just assumed success) | Warning | After HTTP Request — check for status code check in If/Switch |
| Record counts logged before and after data transformations | Info | After Filter Data Table or LINQ — check for row count logging |
| File existence verified after file creation/move operations | Info | After Move File, Copy File — check for File Exists verification |

## 11. Annotations and Documentation

| Check | Severity | How to Verify |
|---|---|---|
| Complex business logic annotated with explanation of *why* (not *what*) | Info | Check annotations on If, Switch, and complex expression activities |
| Entry point workflows have top-level annotations describing purpose and parameters | Info | Read annotations on Main.xaml and entry point workflows |
| Invoked workflows annotated with purpose at call site | Info | Check Invoke Workflow activities for annotations |
| REFramework customizations documented (what was changed from template and why) | Warning | Check root-level files (Process.xaml, GetTransactionData.xaml) for annotations |

## 12. Computer Vision and VDI/Citrix Automation

For projects automating virtual desktop environments (Citrix, VMware Horizon, RDP):

| Check | Severity | How to Verify |
|---|---|---|
| Computer Vision used only where standard selectors are unavailable (VDI, legacy apps) | Info | Check if CV activities are used on native apps where selectors would work |
| CV activities wrapped in `CV Screen Scope` for consistent configuration | Warning | Check for orphaned CV activities outside scope |
| Anchors used for element identification (not pixel coordinates) | Warning | Review CV activity targeting — no position-based targeting |
| Screen resolution and DPI standardized across all environments | Warning | Verify resolution/DPI match between dev and production VDI |
| `CV Element Exists` used before interactions with dynamic elements | Warning | Check for existence checks before CV Click/Type Into |
| CV activities wrapped in Try-Catch (visual matching can fail on theme/font changes) | Warning | Check error handling around CV activities |
| Hybrid approach used — standard selectors for native elements, CV only where needed | Info | Verify CV is not used unnecessarily on accessible elements |
| Citrix Remote Runtime or UiPath Extension installed and configured | Critical | Check VDI extension prerequisites |
| Citrix custom virtual channel allowlisted (blocked by default since Citrix 7 2109) | Critical | Verify Citrix virtual channel configuration |

## 13. PDF, Email, and Excel Patterns

### PDF Handling

| Check | Severity | How to Verify |
|---|---|---|
| PDF type detected before choosing extraction method (native text vs scanned image) | Warning | Check for PDF type detection logic before Read PDF activities |
| `Read PDF Text` used for native/digital PDFs (not OCR) | Info | Verify OCR is not used unnecessarily on native PDFs |
| RegEx used for structured field extraction from text PDFs | Info | Check extraction patterns |
| Multi-page documents handled correctly | Warning | Verify page iteration or concatenation logic |

### Email Processing

| Check | Severity | How to Verify |
|---|---|---|
| Integration Service connectors used instead of IMAP/SMTP where available | Info | Check for `Get Mail Messages` vs Integration Service activities |
| Emails filtered server-side (not fetching all then filtering locally) | Warning | Check mail filter parameters |
| Emails marked as read or moved after processing (idempotent processing) | Warning | Check for `Mark as Read` or `Move Message` after processing |
| Attachments validated before opening (check file type, size) | Warning | Check for attachment validation logic |
| Email sending uses templates (not hardcoded body strings) | Info | Check for template-based email composition |

### Excel Usage

| Check | Severity | How to Verify |
|---|---|---|
| Modern Excel activities used (not Classic) unless macros/pivots needed | Warning | Check for `Use Excel File` (Modern) vs `Excel Application Scope` (Classic) |
| `Read Range` used to load data into DataTable (not cell-by-cell reading) | Warning | Check for `Read Cell` in loops — should be `Read Range` |
| Data processed in-memory via DataTable (not reading/writing Excel repeatedly) | Warning | Check for repeated Excel read/write operations |
| Files closed before processing (no file lock conflicts) | Warning | Check for file handle management |
| Large files (>50K rows) handled with chunking strategy | Warning | Check for out-of-memory risk on large files |

## 14. Healing Agent Configuration

If the project uses or should use UiPath's self-healing capability:

| Check | Severity | How to Verify |
|---|---|---|
| Healing Agent enabled for appropriate processes | Info | Check robot/Orchestrator Healing Agent settings |
| Governance policies configured (global and per-process levels) | Warning | Check Automation Ops for healing policies |
| Critical/regulated processes have stricter healing approval | Warning | Check if sensitive processes require human approval before healing |
| Healing logs reviewed regularly (healing may mask design issues) | Info | Check Insights dashboards for healing frequency |
| Frequently-healed elements flagged for selector refactoring | Warning | Review healing patterns — repeated healing = bad selector |
| Error handling remains as fallback (healing does not replace Try-Catch) | Warning | Verify Try-Catch still exists around UI activities |
| Performance impact acceptable (healing adds AI analysis overhead) | Info | Check for time-sensitive processes where healing delay is problematic |

## 15. Mock Testing

For projects with test cases that need external system isolation:

| Check | Severity | How to Verify |
|---|---|---|
| Mock testing used to isolate workflows from external dependencies | Info | Check for mock implementations in test cases |
| Mocks simulate both success and failure responses | Warning | Review mock data — verify error scenarios are covered |
| Mock responses match real system response schemas | Warning | Compare mock data structure to actual API/system responses |
| Mock calls verified (correct activities called with correct parameters) | Info | Check test assertions for mock call verification |
| External systems NOT mocked in integration tests (only in unit tests) | Warning | Verify integration tests use real connections |

## 16. Configuration Safety — Kill Switches for Risky Operations

For automations that perform high-impact or irreversible actions (writes to financial systems, sending emails, posting to external APIs, deleting records, budget updates), a runtime kill switch should exist.

| Check | Severity | How to Verify |
|---|---|---|
| Each risky operation class (write, send, delete, post) has a boolean Orchestrator asset gating it (e.g., `Configuration_Flag_EPM_WriteBudgetValues`, `Feature_Flag_SendEmails`) | Warning | Check Config.xlsx Assets sheet and workflow code for feature-flag / kill-switch assets wrapping risky activity invocations |
| Kill switches default to OFF in non-production environments | Warning | Verify per-environment asset values |
| Workflow explicitly checks the kill switch before executing risky actions (not just at startup) | Warning | Check for `If Config("Feature_Flag_X")` gating around risky activities, evaluated at action time |
| Disabling the kill switch results in clean skip + audit log (not a failure / exception) | Info | Verify the else-branch logs "skipped due to feature flag OFF" rather than erroring |
| Kill switches documented in the PDD or operations runbook | Info | Check documentation for a list of runtime-controllable flags and their effect |

**Rationale:** When a regression surfaces in production, operations should be able to disable the risky action via asset toggle (no code change, no redeploy) while the team investigates. Without kill switches, the only options are "process runs" or "process is disabled entirely" — both harmful when the automation's non-risky steps still have value.
