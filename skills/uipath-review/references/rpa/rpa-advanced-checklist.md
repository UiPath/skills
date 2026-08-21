# RPA Advanced Review Checklist

Advanced review criteria for UiPath RPA projects. Use with the core [rpa-review-checklist.md](rpa-review-checklist.md) for pre-production gates, inherited-project audits, and performance-sensitive automations beyond structural validity and basic practices.

## 1. Project Organization and Modularity

**Structural metrics:** never use “lines” as a measure. For XAML count activities, root-scope variables, arguments, max nesting depth, and invoke-workflow count. For `.cs` coded workflows count methods, statements (LOC excluding blank/comment), and classes.

### Folder structure

- **Info:** Use logical folders such as `Framework/`, `BusinessLogic/`, `Utilities/`, and `Data/`. Run `ls` at the project root and inspect meaningful subdirectories.
- **Warning:** Do not dump workflow files at the project root except `Main.xaml` and framework files. Run `Glob *.xaml` at the root; only expected files should be present.
- **Info:** Separate data files from logic; keep `Config.xlsx` in `Data/` and templates in `Templates/`. Inspect placement.
- **Info:** Separate test files from production code. Check for a `Tests/` folder or test project.

### Main.xaml and workflow design

- **Warning:** Make `Main.xaml` an orchestrator containing mainly Invoke Workflow calls, not business logic. Read `Main.xaml`.
- **Warning:** Keep `Main.xaml` below 30 activities. Count activities.
- **Info:** Make the high-level flow understandable from `Main.xaml` alone.
- **Warning:** Give each workflow one clear responsibility; review names and contents.
- **Info:** Match layout to logic: Sequence for linear flows, Flowchart for branching, and State Machine for state-based logic.
- **Warning:** Keep each workflow at or below 50 activities. Count activities.
- **Info:** Extract reusable logic into workflows or libraries; identify library candidates used by 2+ projects.
- **Warning:** Separate navigation from page actions; a workflow should navigate to a page or act on it, not both. Review workflow boundaries and retry behavior.
- **Warning:** Separate data extraction from filtering/transformation.
- **Info:** When applicable, use a shared `Browser_NavigateToUrl.xaml` utility with a URL argument instead of app-specific `NavigateTo...` workflows.
- **Info:** Keep login inside the Launch workflow rather than a separate `Login.xaml`, so launch and authentication remain atomic.

### Activity project settings

- **Info:** Configure default UI-activity timeout and input method (`SimulateClick`, `SendWindowMessages`) in project settings → Activity defaults.
- **Info:** Use consistent timeout and retry values across similar activities.

## 2. Selector Robustness

### Modern UI descriptors and containers

- **Info:** Use the Modern design experience; check project settings.
- **Info:** Configure Unified Target with Strict Selector, Fuzzy Selector, Image, and Anchor. Grep `.xaml` for `NUnifiedTargetDefinition`.
- **Warning:** Configure anchors for elements in dynamic/data-driven UIs.
- **Info:** Enable fuzzy selectors for minor text changes and use image targeting only as a last-resort fallback.
- **Warning:** Use partial selectors inside `Use Application/Browser` containers.
- **Warning:** Do not use standalone full selectors when a container is available.
- **Warning:** Open each application scope once rather than reopening it per action.

### Selector resilience

- **Warning:** Do not make selectors dependent on screen resolution, DPI, or pixel-based attributes. Grep for pixel-based or resolution-specific values.
- **Info:** Use variables for dynamic selector portions rather than string concatenation.
- **Warning:** Handle frames/iFrames correctly in web selectors.
- **Warning:** Configure Citrix/RDP extensions or Computer Vision for applicable virtual environments.
- **Info:** Use Element Exists or Check App State before interacting with dynamic elements.

### Object Repository

When Object Repository is used:

- **Warning:** Capture UI elements in Object Repository instead of defining them inline. Compare `.objects/` usage with inline selectors in `.xaml`.
- **Warning:** Organize elements as Application → Screen → Element.
- **Warning/Info:** Use hierarchical, business-meaningful PascalCase names such as `SAP_GUI.SalesOrder.SubmitButton`, not `Button32`.
- **Warning:** Do not duplicate descriptors for the same UI element.
- **Info:** Extract reusable descriptors into a UI Library, a separate published artifact; check `project.json` dependencies.
- **Info:** Keep per-process descriptors local and organization-wide descriptors in shared UI Libraries.

### Published UI Libraries

When a project consumes or publishes a UI Library:

- **Warning:** Version libraries semantically: UI-shape changes are major; selector fixes are patch.
- **Warning:** Pin consumer projects to a specific library version; check `project.json` dependencies for exact version brackets.
- **Info:** Promote Healing Agent fixes into the UI Library so consumers benefit.
- **Warning:** Maintain one UI Library per corporate application, such as SAP or Salesforce; do not mix applications.
- **Info:** Make ownership clear: CoE for organization-wide libraries and the team for team-specific libraries. Check CODEOWNERS or the library catalog.

## 3. Variable and Scope Hygiene

- **Warning:** Scope variables to the innermost container that uses them. Review XAML `Scope`.
- **Warning:** Do not use project-wide variables for inter-workflow communication; use arguments.
- **Warning:** Use specific types instead of `Object` or `String` for numeric, date, and Boolean data (`Int32`, `Decimal`, `DateTime`, `Boolean`).
- **Info:** Use constants for magic numbers and fixed values rather than repeated inline literals.
- **Info:** Give DataTable columns specific types rather than generic `Object`.
- **Warning:** Remove unused workflow arguments. Apply Workflow Analyzer rule ST-USG-009 and inspect manually.
- **Info:** Populate argument descriptions for public entry points.

## 4. Data Manipulation Patterns

- **Warning:** Check for null or empty values before `.ToString()`, `.Split()`, `.Substring()`, and similar string operations on potentially null data.
- **Info:** Trim external input from users, files, and web scrapes at input boundaries; inspect boundary processing for `.Trim()`.
- **Info:** Use specific DataTable column types (`String`, `Int32`, `DateTime`), not default `Object`, including in `Build Data Table` and construction code.
- **Info:** Prefer readable LINQ over nested `For Each` loops for filtering/searching; avoid single-line 200-character chains.
- **Warning:** Use `DateTime.ParseExact` with explicit formats instead of `DateTime.Parse`.
- **Warning:** Do not modify a DataTable during iteration; clone before `Remove Row` or `Add Row`.
- **Info:** Use `StringBuilder` for large-volume string construction inside loops instead of `+=`.

## 5. Error Handling Depth

### Finally blocks

- **Warning:** Include `Finally` for resource cleanup in Try-Catch blocks.
- **Warning:** Close Excel, text-file, and CSV handles in `Finally`, not only in `Try`.
- **Warning:** Close application scopes in `Finally` when not using `Use Application/Browser`.
- **Warning:** Dispose database connections in `Finally`.

### Exception patterns

- **Warning:** Log exception context before rethrowing or handling; logging must precede `Rethrow`.
- **Warning:** Catch specific exception types rather than only generic `System.Exception`.
- **Info:** Use Retry Scope around transient UI failures such as Click and Type Into.
- **Warning:** Configure Retry Scope with an appropriate count of 2-3 and interval.
- **Warning:** Use `ContinueOnError` only with an explicit explanatory comment.
- **Warning:** Do not silently swallow exceptions; log Catch blocks that ignore errors or contain only Assign activities. Apply Workflow Analyzer rule ST-DBP-003.

## 6. Testing Maturity

### Test design

- **Info:** Structure coded tests as Arrange-Act-Assert.
- **Info:** Name tests for scenario and expected outcome, such as `Test_ProcessInvoice_ValidData_ReturnsSuccess`.
- **Warning:** Assert specific outcomes, not merely absence of exceptions; check `Assert.AreEqual`, `Verify Expression`, and equivalent assertions.
- **Warning:** Keep tests independent and reset shared state; inspect setup/teardown.
- **Info:** Capture a screenshot on test failure; check test Catch blocks.

### Test data

- **Warning:** Use synthetic/test data, never production data. Check data sources for production DB/API connections.
- **Info:** Parameterize test data through `.variations/` files or external sources.
- **Warning:** Reset test state before every run to a known starting state.
- **Critical:** Do not store PII or sensitive information in test data.

### CI/CD

- **Warning:** Provide smoke tests runnable on every commit.
- **Info:** Define a regression suite for deployment validation.
- **Info:** Track test results in UiPath Test Manager.
- **Info:** Block production deployment on test failure.

## 7. Idempotent Processing

### Queue items

- **Warning:** Make queue-item processing retry-safe and prevent duplicate records.
- **Warning:** Check status before writes and do not reprocess completed items.
- **Warning:** Make external writes idempotent or guard them with unique keys.
- **Info:** Check whether output files already exist before creating them.

### Non-queue REFramework tracking

- **Warning:** Update the source status column after each transaction; read `SetTransactionStatus.xaml`.
- **Warning:** Distinguish `Success`, `Business Exception`, and `System Exception`.
- **Info:** Resume from the last incomplete item after interruption; read `GetTransactionData.xaml` and verify completed items are skipped.
- **Info:** Document how data refreshes during processing are handled; check staleness handling.

## 8. Debugging Hygiene

- **Warning:** Remove breakpoints from production code. Grep `.xaml` for breakpoint metadata, including `sap2010:WorkflowViewState.IdRef` with breakpoint settings.
- **Warning:** Use `Log Message` instead of `Write Line`. Apply Workflow Analyzer rule ST-MRD-011.
- **Warning:** Remove debug-only variables and hardcoded test values, including names such as `debug_*` and `test_*`.
- **Info:** Remove active debug configuration and `Is Debug` switches. Check `Config.xlsx` and project settings.
- **Info:** Remove commented-out activities and dead code paths, including disabled activities in XAML.

## 9. Logging Completeness

### Workflow boundaries

- **Warning:** Log the start and end of every invoked workflow.
- **Info:** Include workflow name and key input argument values.
- **Warning:** Log full exception details at Error level in every Catch: Message, StackTrace, and Source.
- **Info:** Do not configure Verbose/Trace logging for production; use Info in PROD and Trace in DEV.

### Correlation and traceability

- **Warning:** Include transaction reference or queue-item ID in transaction logs; check `ProcessTransaction` messages.
- **Info:** Pass a correlation ID between Dispatcher and Performer, embedding it in queue-item SpecificContent.
- **Info:** Use `Add Log Fields` for business context such as transaction type and customer ID.
- **Info:** Make log output compatible with Orchestrator monitoring, dashboards, and alert filters.

## 10. Output Verification

- **Warning:** Verify critical writes by read-back, count check, or status code after `Write Range`, HTTP POST, database INSERT, and equivalent operations.
- **Warning:** Validate HTTP response status codes after every API call; check `HTTP Request` follow-up If/Switch logic.
- **Info:** Log record counts before and after filtering or transformation, including `Filter Data Table` and LINQ flows.
- **Info:** Verify file existence after Move File and Copy File operations with File Exists activities.

## 11. Annotations and Documentation

- **Info:** Annotate complex business logic with why it exists, not what it does; inspect If, Switch, and complex expressions.
- **Info:** Add top-level annotations to Main.xaml and entry points describing purpose and parameters.
- **Info:** Annotate Invoke Workflow activities with the invoked workflow’s purpose at the call site.
- **Warning:** Document REFramework customizations, including what changed from the template and why. Check root-level files such as `Process.xaml` and `GetTransactionData.xaml`.

## 12. Computer Vision and VDI/Citrix Automation

For Citrix, VMware Horizon, or RDP projects:

- **Info:** Use Computer Vision only where standard selectors are unavailable; use standard selectors for accessible native elements.
- **Warning:** Wrap CV activities in `CV Screen Scope`; check for orphaned CV activities.
- **Warning:** Use anchors, not pixel coordinates, for CV targeting.
- **Warning:** Standardize screen resolution and DPI across development and production VDI.
- **Warning:** Use `CV Element Exists` before dynamic CV interactions.
- **Warning:** Wrap CV activities in Try-Catch because visual matching can fail on theme/font changes.
- **Info:** Use a hybrid approach: standard selectors for native elements and CV only where needed.
- **Critical:** Install and configure Citrix Remote Runtime or UiPath Extension.
- **Critical:** Allowlist the Citrix custom virtual channel, blocked by default since Citrix 7 2109.

## 13. PDF, Email, and Excel Patterns

### PDF

- **Warning:** Detect PDF type before choosing native-text extraction or OCR.
- **Info:** Use `Read PDF Text` for native/digital PDFs rather than unnecessary OCR.
- **Info:** Use RegEx for structured field extraction from text PDFs.
- **Warning:** Handle multi-page documents through correct iteration or concatenation.

### Email

- **Info:** Use Integration Service connectors instead of IMAP/SMTP where available.
- **Warning:** Filter emails server-side rather than fetching all messages first.
- **Warning:** Mark emails read or move them after processing for idempotency.
- **Warning:** Validate attachment type and size before opening.
- **Info:** Compose email bodies from templates rather than hardcoded strings.

### Excel

- **Warning:** Use Modern Excel activities, not Classic, unless macros or pivots require Classic.
- **Warning:** Load data with `Read Range` into a DataTable rather than reading cells in loops.
- **Warning:** Process data in memory through DataTables instead of repeated Excel reads/writes.
- **Warning:** Close files before processing to prevent locks.
- **Warning:** Use chunking for files larger than 50K rows.

## 14. Healing Agent Configuration

For projects using or intended to use UiPath self-healing:

- **Info:** Enable Healing Agent only for appropriate processes.
- **Warning:** Configure global and per-process governance policies in Automation Ops.
- **Warning:** Require stricter healing approval, including human approval where appropriate, for critical or regulated processes.
- **Info:** Review healing logs regularly because healing can mask design issues.
- **Warning:** Flag frequently healed elements for selector refactoring.
- **Warning:** Retain Try-Catch as a fallback; Healing Agent does not replace error handling.
- **Info:** Confirm healing overhead is acceptable for time-sensitive processes.

## 15. Mock Testing

For tests requiring external-system isolation:

- **Info:** Use mocks to isolate workflows from external dependencies.
- **Warning:** Simulate both success and failure responses.
- **Warning:** Match mock responses to real system response schemas.
- **Info:** Verify mock calls and their parameters.
- **Warning:** Do not mock external systems in integration tests; mock only in unit tests.

## 16. Configuration Safety — Kill Switches for Risky Operations

For high-impact or irreversible operations, including financial writes, email sending, external API posts, record deletion, and budget updates:

- **Warning:** Gate each risky operation class (`write`, `send`, `delete`, `post`) with a Boolean Orchestrator asset, such as `Configuration_Flag_EPM_WriteBudgetValues` or `Feature_Flag_SendEmails`. Check the Config.xlsx Assets sheet and workflow code for feature-flag/kill-switch assets around risky activity invocations.
- **Warning:** Default kill switches to OFF outside production. Verify per-environment asset values.
- **Warning:** Check each kill switch immediately before its risky action, not only at startup. Inspect `If Config("Feature_Flag_X")` gates around the action.
- **Info:** When OFF, skip cleanly and write an audit log stating the action was skipped because the feature flag is OFF; do not fail or throw an exception. Verify the else branch.
- **Info:** Document every kill switch and its effect in the PDD or operations runbook.

A runtime kill switch lets operations disable a risky action through an asset without code changes or redeployment while retaining non-risky process steps.