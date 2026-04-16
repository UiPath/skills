# RPA Project Review Checklist

Comprehensive quality checklist for UiPath RPA projects — coded workflows (C#), XAML workflows, and hybrid projects.

> For advanced review criteria (project organization, selector robustness, variable hygiene, data manipulation, error handling depth, testing maturity, idempotent processing), see [rpa-advanced-checklist.md](rpa-advanced-checklist.md).

## 1. Project Structure

### project.json Validation

| Check | Severity | How to Verify |
|---|---|---|
| `project.json` exists at project root | Critical | `ls project.json` |
| `name` field is set and non-empty | Critical | Read project.json |
| `main` field points to an existing file | Critical | Read project.json → verify file exists |
| `entryPoints` array is non-empty and all `filePath` values exist | Critical | Read project.json → verify each path |
| `expressionLanguage` is set (`VisualBasic` or `CSharp`) | Warning | Read project.json |
| `designOptions.outputType` is correct (`Process`, `Library`, or `Tests`) | Warning | Read project.json |
| Project compatibility is Windows or Cross-platform (not Windows-Legacy) | Info / Warning | Check `project.json` for `targetFramework: "Windows"` or `"Portable"`. See "Windows-Legacy Compatibility" section below for severity matrix. |
| `dependencies` object contains no empty version strings | Critical | Read project.json |
| No duplicate keys in `dependencies` | Critical | Read project.json |

### File Organization

| Check | Severity | How to Verify |
|---|---|---|
| No workflow files at >2 levels of nesting | Info | Glob `**/*.xaml` and `**/*.cs` |
| No files >5MB (XAML) | Critical | `find . -name "*.xaml" -size +5M` |
| No files >500KB (XAML) | Warning | `find . -name "*.xaml" -size +500k` |
| `.local/`, `.codedworkflows/`, `.objects/` are not manually modified | Info | Check git diff for these dirs |
| No leftover debug/test data files in project root | Warning | Look for .csv, .xlsx, .json data files |
| Logical folder structure used (Framework/, BusinessLogic/, Utilities/, Data/) | Info | `ls` project root — check for meaningful subdirectories |
| Main.xaml acts as orchestrator only (no direct UI or business logic) | Warning | Grep Main.xaml for UI activities (`NClick`, `NTypeInto`, `NGetText`, `Click`, `TypeInto`, `GetText`, `SendHotkey`, `NCheckAppState`). If any are found, Main.xaml is doing work it should delegate. Should contain mostly `InvokeWorkflowFile` calls, <30 activities total. |
| No leftover breakpoints in production code | Warning | Grep `.xaml` for breakpoint metadata |
| No workflow exceeds 80 activities OR 30 root-scope variables OR 10 nesting levels | Warning | Count activities, Variables elements, and max indentation depth per .xaml. Report these counts in the review (never "lines") |

### Workflow Dependency Graph

| Check | Severity | How to Verify |
|---|---|---|
| No circular dependencies between workflows | Critical | Trace `InvokeWorkflowFile` references across all XAML files — A invokes B invokes A is a cycle |
| No orphaned workflows (files unreachable from Main.xaml) | Warning | Starting from Main.xaml, follow all `InvokeWorkflowFile` references recursively. Any .xaml not reached is orphaned. |
| No missing invocation targets | Critical | Every `InvokeWorkflowFile` path must point to a file that exists on disk |
| Init/Close symmetry | Warning | Every app launched in `InitAllApplications.xaml` (via Open Application/Open Browser) must have a corresponding close in `CloseAllApplications.xaml`. Count launch invocations vs close invocations — they must match. |

### Config.xlsx Cross-Reference (REFramework projects)

| Check | Severity | How to Verify |
|---|---|---|
| Every `Config("key")` reference in XAML has a matching key in Config.xlsx | Critical | Grep all XAML for `Config("` patterns, collect keys, compare against Config.xlsx Name column. Missing key = runtime `KeyNotFoundException`. |
| No unused Config.xlsx entries | Warning | Keys in Config.xlsx that are never referenced in any XAML or .cs file. Dead config adds confusion. |
| No duplicate keys across Settings/Constants/Assets sheets | Critical | All three sheets populate one Dictionary — duplicate keys silently overwrite. |

### Dependencies

| Check | Severity | How to Verify |
|---|---|---|
| All referenced packages are installable | Critical | `uip rpa install-or-update-packages --use-studio` |
| No unused packages | Warning | Workflow Analyzer rule ST-USG-010 |
| Version constraints use proper syntax (`[1.0.0]`, `[1.0.0, 2.0.0)`) | Warning | Read project.json dependencies |
| No package version conflicts | Critical | Check for multiple versions of same package family |

## 2. Coded Workflow Quality (C# Projects)

### Structural Checks

| Check | Severity | How to Verify |
|---|---|---|
| Every `.cs` workflow has a companion `.cs.json` metadata file | Critical | Glob `**/*.cs` → verify `.cs.json` exists |
| Workflow classes inherit from `CodedWorkflow` | Critical | Grep for `class.*:.*CodedWorkflow` |
| Workflow classes have `[Workflow]` attribute | Critical | Grep for `\[Workflow\]` |
| Test case classes have `[TestCase]` attribute | Critical | Grep for `\[TestCase\]` |
| One class per file, class name matches file name | Warning | Read each .cs file |
| Namespace matches sanitized project name | Warning | Compare namespace to project.json `name` |

### Code Quality

| Check | Severity | How to Verify |
|---|---|---|
| No unused `using` statements | Warning | Check imports vs usage |
| Service methods called via correct service accessor (`system.*`, `uiAutomation.*`) | Critical | Verify service patterns |
| No hardcoded file paths or URLs | Warning | Grep for `C:\\`, `/Users/`, `http://localhost` |
| No hardcoded credentials or secrets | Critical | Grep for `password`, `secret`, `apikey`, `token` in string literals |
| Coded Source Files (no `CodedWorkflow` base) used for utility classes | Info | Check class organization |
| Strongly-typed `workflows.MyWorkflow()` used instead of string-based `RunWorkflow()` | Warning | Grep for `RunWorkflow` |
| Object Repository descriptors used (no hardcoded selectors) | Warning | Check for `using *.ObjectRepository` |

### Error Handling

| Check | Severity | How to Verify |
|---|---|---|
| Try-catch blocks around external calls (API, file I/O, UI automation) | Warning | Check error handling patterns |
| Exceptions logged with context before re-throwing | Warning | Check catch blocks |
| No empty catch blocks | Warning | Workflow Analyzer rule ST-DBP-003 |

## 3. XAML Workflow Quality

### Structural Checks

| Check | Severity | How to Verify |
|---|---|---|
| All `.xaml` files pass validation | Critical | `uip rpa get-errors --file-path "<FILE>" --project-dir "<DIR>" --output json --use-studio` |
| Expression language in all XAML files matches `project.json` setting | Critical | Check `expressionLanguage` consistency |
| No C# syntax in VB.NET projects | Warning | If `expressionLanguage` is `VisualBasic`, grep all `.xaml` for C# patterns: `!=`, `&&`, `\|\|`, `null` (VB uses `Nothing`), `$"` (interpolated strings), `=>` (lambda), `//` (comments), `typeof()` (VB uses `GetType()`). These compile-fail or silently misbehave. |
| No activities with default display names ("Sequence", "Assign", "If") | Warning | Workflow Analyzer rule ST-MRD-002 |
| No deeply nested activities (>5 levels) | Warning | Workflow Analyzer rule ST-MRD-009 |
| No empty Catch blocks | Warning | Workflow Analyzer rule ST-DBP-003 |
| No empty Sequences | Info | Workflow Analyzer rule ST-MRD-008 |
| No unreachable activities | Warning | Workflow Analyzer rule ST-MRD-004 |
| No Write Line usage (use Log Message instead) | Warning | Workflow Analyzer rule ST-MRD-011 |

### Naming Conventions

| Check | Severity | How to Verify |
|---|---|---|
| Variables follow PascalCase/camelCase | Warning | Workflow Analyzer rule ST-NMG-001 (regex: `^(dt_)?([A-Z]\|[a-z])+([0-9])*$`) |
| DataTable variables prefixed with `dt_` | Info | Workflow Analyzer rule ST-NMG-009 |
| Arguments use directional prefixes (`in_`, `out_`, `io_`) | Warning | Workflow Analyzer rule ST-NMG-002 |
| No variable-argument name conflicts (shadowing) | Warning | Workflow Analyzer rules ST-NMG-005, ST-NMG-006 |
| Activity display names are descriptive | Warning | Workflow Analyzer rule ST-MRD-002 |
| Workflow file names use Verb + Object (PascalCase) | Info | Manual check (e.g., `GetTransactionData.xaml`, `ProcessInvoice.xaml`) |

### Container and Scope Requirements

Activities that require specific parent containers:

| Activity Type | Required Container | Severity if Missing |
|---|---|---|
| Excel activities | `ExcelApplicationScope` or `ExcelApplicationCard` | Critical |
| UI Automation activities | `Use Application/Browser` (`NApplicationCard`) | Critical |
| Word activities | `WordApplicationScope` | Critical |
| Office 365 activities | Office 365 scope activity | Critical |
| GSuite activities | GSuite scope activity | Critical |

### Conflicting Property Pairs

Only ONE of each pair may be set:

| Property A | Property B | Severity |
|---|---|---|
| `Password` | `SecurePassword` | Critical |
| `EditPassword` | `SecureEditPassword` | Critical |
| `SimulateClick` | `SendWindowMessages` | Warning |

### Selector Quality

Selectors are ranked by attribute stability. When reviewing, assess which tier the majority of selectors fall into:

| Tier | Attributes Used | Stability | Review Action |
|---|---|---|---|
| 1 (best) | `id`, `automationid` | Highest — set by developer, rarely change | No finding |
| 2 | `name` + `role`, `name` + `controltype` | High — stable across sessions | No finding |
| 3 | `aaname`, `innertext` | Medium — stable if text doesn't change | Info if majority |
| 4 | `tag` + `parentid`, `class` | Low — changes with DOM restructuring | Warning if majority |
| 5 (worst) | `idx`, `tableRow`, position-based | Brittle — changes whenever sibling order changes | Warning per occurrence |

| Check | Severity | How to Verify |
|---|---|---|
| No `idx`-based selectors (index-based, brittle) | Warning | Grep for `idx=` in .xaml files |
| No environment-specific data in selectors (qa/uat/prod URLs, ports) | Warning | Grep for environment-specific strings |
| Wildcards used for dynamic attributes | Info | Check selector patterns |
| Object Repository used instead of hardcoded selectors | Warning | Check for `.objects/` usage |
| Element Exists / Check App State used before interactions | Info | Check for pre-validation patterns |
| Modern UI Descriptors used (Strict + Fuzzy + Image + Anchor) | Info | Grep `.xaml` for `NUnifiedTargetDefinition` |
| Selector depth minimal (2-3 levels preferred, not deep chains) | Info | Check selector nesting depth in `.xaml` |

### Security

| Check | Severity | How to Verify |
|---|---|---|
| `SecureString` used for all password variables | Critical | Workflow Analyzer rule ST-SEC-007, ST-SEC-008 |
| No `SecureString` converted to plain `String` | Warning | Workflow Analyzer rule ST-SEC-009 |
| Credentials retrieved from Orchestrator assets or Credential Store (not hardcoded) | Critical | Grep for `Get Credential` vs hardcoded strings |
| No sensitive data in Log Messages | Warning | Check log message content |
| No PII in queue item specific data (or encrypted) | Warning | Check queue item creation patterns |

### Performance

| Check | Severity | How to Verify |
|---|---|---|
| No hardcoded Delay activities | Warning | Workflow Analyzer rules ST-DBP-026, ST-PRR-004 |
| Simulate Click / SendWindowMessages used where possible | Info | Check UI activity properties |
| No nested For Each loops over large DataTables (use LINQ) | Warning | Check loop patterns |
| Filter Data Table used before processing large datasets | Info | Check data processing patterns |
| No excessive logging inside tight loops | Warning | Check log placement |

## 4. Hybrid Project Quality

| Check | Severity | How to Verify |
|---|---|---|
| Clear separation — XAML for UI automation, coded for business logic | Info | Review file organization |
| No duplicated logic between coded and XAML workflows | Warning | Compare functionality |
| InvokeWorkflowFile used correctly for cross-mode invocation | Warning | Check invocation patterns |
| Shared data models in Coded Source Files (not duplicated) | Info | Check for model consistency |

## 5. REFramework Compliance (Queue-Based Projects)

> **Transaction Granularity:** REFramework correctness requires that the queue item's declared unit of work matches the unit of work `ProcessTransaction.xaml` actually performs. Run Step 3a (Unit of Work Discovery) in SKILL.md before this section — any mismatch is a Granularity Mismatch finding. Strong signal that a mismatch exists: presence of `CheckIf<X>Exists.xaml` or `Verify<X>Exists.xaml` in the project (homegrown idempotency guards compensating for bulk-in-transaction). See [rpa-common-issues.md](rpa-common-issues.md) → "Granularity Mismatch" for the full signals, severity matrix, and fixes.


If the project uses or should use the REFramework pattern:

### State Machine Architecture

| Check | Severity | How to Verify |
|---|---|---|
| State Machine with 4 states: Init, GetTransactionData, ProcessTransaction, EndProcess | Warning | Read Main.xaml structure |
| All 7 transitions present (Init→GetTx, Init→End, GetTx→ProcessTx, GetTx→End, ProcessTx→GetTx, ProcessTx→Init, Init→Init retry) | Warning | Check transitions |
| Init state has SystemException → Init self-retry transition (not just Init → End) | Warning | Transient login/app failures should retry, not terminate the process |
| Init state does NOT fetch transaction data (data fetched in GetTransactionData) | Warning | Check InitAllApplications / InitAllSettings — no Read Range / Get Queue Items / Data Scraping |
| REFramework not forced onto single-shot / stateless processes | Info | If no real transaction iteration (one execution per run), REFramework is overkill — use a linear workflow |
| If using non-queue data source: `QueueRetry` flag in SetTransactionStatus properly handled (not left at queue default) | Critical | Grep SetTransactionStatus for `QueueRetry` or `in_TransactionItem.RetryNo` logic that only applies to QueueItems |
| If using DataTable: `GetTransactionData` uses `dt.Rows(in_TransactionNumber - 1)` (DataTable is 0-indexed; transaction counter is 1-indexed) | Warning | Off-by-one skips first row, errors on last |
| `Process.xaml` processes exactly ONE transaction per invocation | Critical | Review Process.xaml |
| Framework/ folder files NOT modified (InitAllSettings, framework GetTransactionData, framework SetTransactionStatus) | Warning | Check Framework/ folder |
| Business logic only in root-level files (Process.xaml, root GetTransactionData.xaml, root SetTransactionStatus.xaml) | Warning | Review file locations |

### REFramework Failure-Path Validation

Beyond structural checks, verify each state transition path is wired correctly by tracing the logic:

| Path | What to Trace | Severity if Broken |
|---|---|---|
| **System Exception → Retry** | In ProcessTransaction: system exception propagates (not swallowed by Try-Catch) → state machine catches it → transitions to Init → Init re-opens apps → transitions back to GetTransactionData → same item retried | Critical — broken retry means failed items are silently marked successful |
| **Business Exception → Skip** | In ProcessTransaction: `BusinessRuleException` thrown → caught and NOT retried → `SetTransactionStatus` marks item as Failed-Business → transitions to GetTransactionData → next item | Warning — wrong exception type causes unnecessary retries |
| **Queue Empty → Clean Exit** | GetTransactionData returns Nothing/null when no items → transitions to EndProcess → `CloseAllApplications` runs → process ends cleanly | Warning — missing Nothing check causes infinite loop or crash |
| **Max Retries Exceeded → Fail Item** | After N system exceptions on same item: retry counter reaches `MaxRetryNumber` → item marked as Failed → transitions to GetTransactionData for next item (not EndProcess) | Critical — exceeded retries should skip item, not terminate process |
| **Init Failure → Retry or Stop** | Init state throws exception → if `ProcessRetries` < max, self-transitions back to Init → if exceeded, transitions to EndProcess | Warning — Init failure without retry terminates on first transient login failure |

### Config.xlsx Validation

| Check | Severity | How to Verify |
|---|---|---|
| `Config.xlsx` exists in Data/ folder with Settings, Constants, Assets sheets | Warning | Check for Data/Config.xlsx |
| No duplicate keys across sheets (all go into one Dictionary) | Critical | Read Config.xlsx |
| No sensitive data (credentials, tokens) in Settings or Constants sheets | Critical | Review Config.xlsx values |
| Assets sheet references Orchestrator Asset names (not actual values) | Warning | Check Assets sheet |
| `OrchestratorQueueName` set in Settings (not hardcoded in workflows) | Warning | Check Settings sheet |
| `OrchestratorQueueFolder` set if using modern folders | Warning | Check Settings sheet |

### Retry Configuration

| Check | Severity | How to Verify |
|---|---|---|
| `MaxRetryNumber` = 0 when using Orchestrator queue retries | Critical | Check Constants sheet — double-retry causes multiplicative behavior (e.g., 3x3=9 attempts) |
| `MaxRetryNumber` > 0 for non-queue scenarios (Excel, DataTable, API) | Warning | Check Constants sheet |
| `MaxConsecutiveSystemExceptions` configured (not 0) | Warning | Check Constants sheet — 0 disables the circuit breaker, bot runs forever even if every transaction fails |
| Orchestrator queue `Max # of Retries` configured (1-50, typically 3) | Warning | Check queue settings |
| Auto-retry enabled on queue for Application Exceptions | Warning | Check queue settings |

### Exception Handling

| Check | Severity | How to Verify |
|---|---|---|
| `BusinessRuleException` thrown for data/validation issues (NOT `System.Exception`) | Critical | Grep for `BusinessRuleException` usage |
| Business exceptions NOT retried (transitions to GetTransactionData, not Init) | Critical | Check ProcessTransaction exception handling |
| Application/System exceptions trigger app recovery (CloseAll → KillAll → re-Init) | Warning | Check ProcessTransaction exception flow |
| `SetTransactionStatus` called on ALL paths (Success, Business Exception, Application Exception) | Critical | Check all transaction exit paths |
| Screenshot captured on Application Exception | Warning | Check screenshot configuration |
| Transaction reference set (128-char limit) | Info | Check reference field usage |

### Application Lifecycle

| Check | Severity | How to Verify |
|---|---|---|
| `CloseAllApplications.xaml` properly implemented (NOT left empty) | Warning | Read CloseAllApplications.xaml |
| `KillAllProcesses.xaml` properly implemented (NOT left empty) | Warning | Read KillAllProcesses.xaml |
| `InitAllApplications.xaml` includes credential retrieval from Orchestrator assets | Warning | Read InitAllApplications.xaml |
| `InitAllApplications.xaml` checks if app is already open before re-opening | Info | Check for app-state validation |
| `KillAllProcesses.xaml` called during first Init to ensure clean state | Info | Check Init flow |
| Orchestrator Stop/Terminate signals handled in GetTransactionData | Warning | Check for stop signal handling |

### Non-Queue REFramework (Excel/DataTable/API)

If the project uses REFramework with non-queue data sources:

| Check | Severity | How to Verify |
|---|---|---|
| `TransactionItem` type changed from `QueueItem` to appropriate type (`DataRow`, `Dictionary`, etc.) | Critical | Check Main.xaml variable types |
| `TransactionData` type changed from default to `DataTable` or appropriate collection | Critical | Check Main.xaml variable types |
| Data loaded during Init state (not in GetTransactionData) | Warning | Check data loading location |
| GetTransactionData uses `io_TransactionNumber` as index, returns Nothing when exhausted | Critical | Read root GetTransactionData.xaml |
| SetTransactionStatus updates the source data (e.g., Excel status column) | Warning | Read root SetTransactionStatus.xaml |
| `MaxRetryNumber` > 0 (local retries needed without queue) | Warning | Check Constants sheet |

## 6. Logging Quality

| Check | Severity | How to Verify |
|---|---|---|
| Log Message used (not Write Line) | Warning | Workflow Analyzer rule ST-MRD-011 |
| Minimum logging present in each workflow | Warning | Workflow Analyzer rule ST-USG-020 |
| Log bookends: >80% of invoked sub-workflows have LogMessage near first and last activity | Warning | For each workflow invoked from Main.xaml, check if it starts and ends with a LogMessage. Count coverage: (workflows with bookends / total invoked workflows). Below 80% = finding. |
| Error-level logs in all Catch blocks | Warning | Check catch blocks |
| No Verbose/Trace logging in production configuration | Info | Check log levels |
| Custom log fields for business context (Add Log Fields) | Info | Check for Add Log Fields usage |
| No sensitive data (PII, credentials) in log messages | Critical | Review log content |

## 7. Test Coverage

| Check | Severity | How to Verify |
|---|---|---|
| Test cases exist for critical workflows | Warning | Glob `**/*[Tt]est*` files |
| Test cases use `[TestCase]` attribute (coded) or Test Case project type | Warning | Check test organization |
| Assertions verify expected outcomes (not just "runs without error") | Info | Check assertion content |
| Data-driven tests use `.variations/` for parameterization | Info | Check for variation files |
| Tests are independent of each other | Info | Check for shared state |
| Tests use synthetic/test data — never production data | Warning | Check test data sources for production connections |

## 8. Workflow Analyzer Summary

Run Workflow Analyzer and verify no Error-level violations. Key rules to check:

### Must Pass (Error Level)

- ST-ANA-005: project.json exists
- ST-ANA-006: Main workflow exists
- ST-DBP-023: No empty workflows
- ST-SEC-007: SecureString for password arguments
- ST-SEC-008: SecureString for password variables
- ST-USG-009: No unused variables
- ST-NMG-006: No variable-argument name conflicts

### Should Pass (Warning Level)

- ST-DBP-002: Argument count not excessive
- ST-DBP-003: No empty Catch blocks
- ST-DBP-026: No Delay activities
- ST-MRD-002: No default activity names
- ST-MRD-007: No deeply nested If clauses
- ST-MRD-009: No deeply nested activities
- ST-MRD-011: No Write Line usage
- ST-NMG-001: Variable naming convention
- ST-NMG-002: Argument naming convention
- ST-SEC-009: No SecureString misuse
- ST-USG-005: No hardcoded activity arguments
- ST-USG-010: No unused dependencies
- ST-REL-006: No infinite loops

## 9. Deployment Readiness

| Check | Severity | How to Verify |
|---|---|---|
| All entry points correctly defined in project.json | Critical | Verify entryPoints array |
| Dependencies pinned to specific versions | Warning | Check version constraints |
| No hardcoded environment-specific values (URLs, paths) | Warning | Grep for hardcoded values |
| No debug artifacts or test data included | Info | Check for leftover files |
| Global Exception Handler configured | Info | Check project settings |
| Project builds and validates clean | Critical | `uip rpa get-errors` returns 0 errors |
| Smoke test passes | Warning | `uip rpa run-file` completes successfully |

## 10. Windows-Legacy Compatibility

### Support Status (Important Context)

Windows-Legacy is supported **indefinitely** in Studio LTS:
- Studio LTS 2024.10, 2025.10, 2026.10, and **all future LTS releases** continue to support creating, opening, and editing Windows-Legacy projects
- Studio LTS provides 24 months Mainstream + 12 months Extended support per release
- Legacy projects **validate, run, and deploy correctly** — they are NOT a deployment blocker
- Studio STS does **not** support Legacy — teams using Legacy must stay on LTS
- **Deprecation means "no new features added to Legacy," not "Legacy will be removed"**

> **NEVER flag Windows-Legacy as Critical based on framework alone.** Route Legacy-specific deep validation to the dedicated `uipath-rpa-legacy` skill.

### The Real Question

Not "Can we keep using Legacy?" (yes) but **"What are we giving up by staying on Legacy?"**

### What Legacy Projects Cannot Access

Ordered by developer-impact for a real production RPA team. **When recommending migration, lead with the top 2-3 features most relevant to what THIS project does today** — don't list the whole menu.

| Rank | Category | Feature and why it matters |
|---|---|---|
| 1 | Maintenance | **Healing Agent** — AI-powered selector self-healing at runtime. When a selector drifts (app update, DOM change, resolution shift), Healing Agent recovers automatically. Legacy projects have NO self-healing — every broken selector is a ticket and a deploy. |
| 2 | UI Automation resilience | **Unified Target Method** (Strict + Fuzzy + Image + Anchor) — modern multi-strategy targeting. Legacy uses only classic single-strategy selectors, which break on minor UI changes. |
| 3 | Reusable UI management | **Object Repository + UI Libraries** — centralized, hierarchical, versioned UI descriptors. Legacy has limited Object Repository support and no shared UI Library consumption. |
| 4 | Testing quality | **Coded test cases (C#)** + **Test Manager integration** — write real unit/integration tests for workflows. Legacy testing is Studio Test Activity only — limited assertions, no mocking framework. |
| 5 | Development velocity | **Autopilot™** — AI-assisted Studio (generate activities from description, fix workflows, explain code). Legacy projects cannot use Autopilot. |
| 6 | ScreenPlay / modern UI orchestration | **ScreenPlay** — modern scripted UI interaction / recording experience. Available only for Modern projects. |
| 7 | Platform capabilities | **AI Agents + Maestro orchestration + Agentic Automation** — participate as actors in multi-agent/multi-robot BPMN processes. Legacy processes cannot be invoked from / cannot invoke these. |
| 8 | Code-based logic | **Coded workflows (C#)** alongside XAML — type safety, unit testability, IDE refactoring for complex business logic. |
| 9 | Performance and security | **JIT-compiled .NET 6+** — faster execution, modern GC, modern encryption/TLS. Legacy runs on .NET Framework 4.6.1 with incremental performance and EOL security libraries. |
| 10 | Platform reach | **Cross-platform execution** (Linux robots) — deployment flexibility for cloud-native environments. |
| 11 | Studio cadence | **Studio STS** (2-month release cycle) — access to new activities and features as they ship. Legacy locks the team to Studio LTS (annual). |
| 12 | Developer ergonomics | New design experience, Data Manager globals/constants, customizable library activity layouts. |

### Tailoring the Migration Recommendation

The review should pick the **2-3 most relevant features for this project's context**, not enumerate the list. Heuristics:

| If the project has... | Lead the recommendation with... |
|---|---|
| Heavy UI automation (many selectors, high maintenance load) | Healing Agent + Unified Target + Object Repository |
| No tests or weak tests | Coded test cases + Test Manager |
| Long XAML files, complex business logic | Coded workflows (C#) |
| Human-in-the-loop / multi-actor orchestration | Maestro + Agentic Automation + Agents |
| Runs only in one environment, scaling concerns | Cross-platform execution + Studio STS |
| Team maintains many similar RPA projects | Object Repository + UI Libraries (shared descriptors) + Autopilot |

### Severity Matrix

| Condition | Severity |
|---|---|
| Legacy in use, team on Studio LTS by organizational choice | Info |
| Legacy in use AND team would benefit from the top-ranked features above (heavy UI maintenance, missing tests, AI/agent use cases, coded-logic complexity) | Warning |
| Legacy in use because of SOAP web services (only supported in Legacy) | Info — valid design, document reason |
| Greenfield project started on Legacy without technical justification | Warning |
| Legacy library consumed by a Windows/Cross-platform project | Warning — migrate library first |

### Migration Blocker Detection

When Legacy is detected and migration is on the table, scan for **activities that cannot be auto-migrated** — these represent manual rework effort:

**UI Automation blockers (Activity Migrator cannot convert these):**

| Activity / Pattern | Severity |
|---|---|
| All Computer Vision activities (CV Click, CV Check, CV Get Text, CV Screen Scope, etc.) | Warning |
| All Trigger activities (Click Trigger, Hotkey Trigger, Element State Change Trigger, Monitor Events, Key Press Trigger, Mouse Trigger, System Trigger) | Warning |
| Anchor Base | Warning — manually replace with modern anchor pattern |
| Context Aware Anchor | Warning |
| Element Scope | Warning |
| Double Click / Double Click Image / Double Click OCR Text / Double Click Text | Warning |
| Classic OCR engines (Microsoft OCR, Tesseract OCR, Google Cloud Vision OCR, Microsoft Azure Computer Vision OCR) | Warning |
| Callout / Tooltip | Warning |
| Set Clipping Region / Set Web Attribute | Warning |
| Block User Input / Indicate On Screen / Inject .NET Code / Invoke ActiveX Method | Warning |
| Find Image Matches / Load Image / Save Image / Get Source Element | Warning |

**Mail blockers (Classic Outlook Desktop → M365):**

| Activity / Pattern | Severity |
|---|---|
| `Outlook Desktop Mail Messages Trigger` — skipped entirely during migration; no folder-monitoring equivalent in M365 | Critical — fundamental capability loss without rework |
| `Get Outlook Desktop Mail Messages` with filter options — filters not migrated | Warning — manual recreation needed |
| Other Classic Outlook activities (Send, Reply, Move, Delete, Mark Read, Set Categories, Save) | Info — auto-migrate but require ConnectionId configuration |

### Migration Tool Decision

| Scenario | Recommended Tool |
|---|---|
| Single project, framework-only (W-L → W) | Studio's built-in Converter |
| Multiple projects / bulk conversion | **Activity Migrator** (`UiPath.Upgrade.exe bulk`) |
| Project uses Classic UI Automation | **Activity Migrator** — also migrates Classic → Modern UIA |
| Project uses Classic Outlook Desktop mail | **Activity Migrator** — also migrates to M365 Mail |
| Project needs activity-level migration (not just framework) | **Activity Migrator** |

> Studio's built-in Converter does framework-only conversion. For most real-world Legacy projects (which use Classic UIA), **Activity Migrator** is the right tool.

### Migration Version Requirements

| Check | Severity |
|---|---|
| If planning migration: `UiPath.UIAutomation.Activities` target >= 25.10.21 | Warning |
| If planning migration: `UiPath.MicrosoftOffice365.Activities` target >= 3.6.10 (if Mail migration needed) | Warning |
| Studio 2024.10+ available to open migrated project | Warning |
| For ST-AMG-001 post-migration rule: Studio 2025.10.8 LTS or 2026.0.189+ STS | Info |

### Migration Pre-Flight Checklist

| Pre-flight check | Severity |
|---|---|
| Project/library backup created | Warning |
| Activity Migrator `analyze` run first (dry-run) — SARIF report reviewed before commit | Warning |
| Libraries migrated **BEFORE** consumer projects | Critical |
| Project/library names NOT changed during migration | Warning |
| NuGet feeds verified in `NuGet.config` (or Orchestrator PAT/OAuth configured) | Warning |
| For M365 mail migration: `--config` file with ConnectionId mappings prepared | Warning |
| Pilot on single project before `bulk` command | Info |

### Post-Migration Validation

If the project shows signs of recent migration (`.upgrade` folder present, mix of modern activities with Legacy-originated naming, synthetic `Use Application/Browser` scopes):

| Check | Severity |
|---|---|
| Workflow Analyzer rule **ST-AMG-001** passes (post-migration annotations present) | Warning |
| SARIF report from `.upgrade` folder reviewed and archived | Info |
| Application scopes validated (organic preserved, synthetic merged correctly) | Warning |
| ConnectionId values populated for migrated M365 activities | Critical — empty ConnectionIds cause runtime failures |
| End-to-end tests passed post-migration | Warning |
| Execution time monitored (modern activities may initially be slower) | Info |
