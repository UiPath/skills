# RPA Project Review Checklist

Quality checklist for UiPath RPA projects: coded workflows (C#), XAML workflows, and hybrid projects.

> For advanced review criteria (project organization, selector robustness, variable hygiene, data manipulation, error handling depth, testing maturity, idempotent processing), see [rpa-advanced-checklist.md](rpa-advanced-checklist.md).

## 1. Project Structure

### project.json

| Check | Severity | Verify |
|---|---|---|
| `project.json` exists at project root | Critical | Run `ls project.json` |
| `name` is non-empty; `main` points to an existing file | Critical | Read project.json and verify |
| `entryPoints` is non-empty and every `filePath` exists | Critical | Read project.json and verify |
| `expressionLanguage` is `VisualBasic` or `CSharp` | Warning | Read project.json |
| `designOptions.outputType` is `Process`, `Library`, or `Tests` as appropriate | Warning | Read project.json |
| Compatibility is Windows or Cross-platform, not Windows-Legacy | Info / Warning | Check `targetFramework: "Windows"` or `"Portable"`; apply the Windows-Legacy severity matrix below |
| `dependencies` has no empty version strings or duplicate keys | Critical | Read project.json |

### Files and organization

| Check | Severity | Verify |
|---|---|---|
| No workflow files exceed 2 nesting levels | Info | Glob `**/*.xaml` and `**/*.cs` |
| No XAML exceeds 5MB | Critical | Run `find . -name "*.xaml" -size +5M` |
| No XAML exceeds 500KB | Warning | Run `find . -name "*.xaml" -size +500k` |
| `.local/`, `.codedworkflows/`, and `.objects/` are not manually modified | Info | Check git diff |
| No leftover debug/test data files in project root (`.csv`, `.xlsx`, `.json`) | Warning | Inspect root |
| Use logical folders such as `Framework/`, `BusinessLogic/`, `Utilities/`, and `Data/` | Info | Inspect root |
| Main.xaml is an orchestrator: no direct UI/business logic, mostly `InvokeWorkflowFile` calls, and fewer than 30 activities | Warning | Grep Main.xaml for `NClick`, `NTypeInto`, `NGetText`, `Click`, `TypeInto`, `GetText`, `SendHotkey`, `NCheckAppState` |
| No production breakpoints | Warning | Grep `.xaml` for breakpoint metadata |
| No workflow exceeds 50 activities, 30 root-scope variables, or 7 nesting levels (ST-MRD-009 default) | Warning | Count activities, `Variables` elements, and maximum indentation depth per `.xaml`; report counts, never “lines” |

### Workflow dependency graph

| Check | Severity | Verify |
|---|---|---|
| No circular `InvokeWorkflowFile` dependencies | Critical | Trace all references recursively |
| No orphaned workflows unreachable from Main.xaml | Warning | Traverse from Main.xaml and report unreached `.xaml` files |
| Every `InvokeWorkflowFile` target exists | Critical | Verify paths on disk |
| Every app opened in `InitAllApplications.xaml` by Open Application/Open Browser has a corresponding close in `CloseAllApplications.xaml`; launch and close counts match | Warning | Compare workflows |

### Config.xlsx cross-reference (REFramework)

| Check | Severity | Verify |
|---|---|---|
| Every `Config("key")` in XAML exists in Config.xlsx Name column | Critical | Grep all XAML for `Config("`; compare keys; missing keys cause runtime `KeyNotFoundException` |
| No unused Config.xlsx entries | Warning | Compare keys with all XAML and `.cs` references |
| No duplicate keys across Settings, Constants, and Assets sheets | Critical | All populate one Dictionary and duplicates silently overwrite |

### Dependencies

| Check | Severity | Verify |
|---|---|---|
| All referenced packages resolve | Critical | Run `uip rpa build "<PROJECT_DIR>" --output json`; do NOT run `uip rpa packages install` because review is read-only |
| No unused packages | Warning | Run/check Workflow Analyzer rule ST-USG-010 |
| Version constraints use `[1.0.0]` or `[1.0.0, 2.0.0)` syntax | Warning | Read project.json |
| No package-version conflicts | Critical | Check package families |

## 2. Coded Workflow Quality (C#)

### Structure

| Check | Severity | Verify |
|---|---|---|
| Every `.cs` workflow has a companion `.cs.json` | Critical | Glob `**/*.cs` and verify |
| Workflow classes inherit from `CodedWorkflow` and have `[Workflow]` | Critical | Grep for `class.*:.*CodedWorkflow` and `\[Workflow\]` |
| Test case classes have `[TestCase]` | Critical | Grep for `\[TestCase\]` |
| One class per file; class and file names match | Warning | Read `.cs` files |
| Namespace matches sanitized project name | Warning | Compare with project.json `name` |

### Code and errors

| Check | Severity | Verify |
|---|---|---|
| No unused `using` statements | Warning | Compare imports and usage |
| Service methods use correct accessors (`system.*`, `uiAutomation.*`) | Critical | Inspect calls |
| No hardcoded paths or URLs (`C:\\`, `/Users/`, `http://localhost`) | Warning | Grep source |
| No hardcoded credentials/secrets; inspect string literals containing `password`, `secret`, `apikey`, `token` | Critical | Grep source |
| Utility classes without `CodedWorkflow` use Coded Source Files | Info | Inspect organization |
| Use strongly typed `workflows.MyWorkflow()` rather than string-based `RunWorkflow()` | Warning | Grep for `RunWorkflow` |
| Use Object Repository descriptors rather than hardcoded selectors | Warning | Check `using *.ObjectRepository` |
| External API, file-I/O, and UI calls have Try-catch handling; catches log context before rethrowing; no empty catches | Warning | Inspect code; check ST-DBP-003 |

## 3. XAML Workflow Quality

### Structure and analyzer checks

| Check | Severity | Verify |
|---|---|---|
| Every `.xaml` validates | Critical | Run `uip rpa validate --file-path "<FILE>" --project-dir "<PROJECT_DIR>" --output json` |
| XAML expression language matches project.json | Critical | Compare all files |
| VisualBasic projects contain no C# syntax: `!=`, `&&`, `\|\|`, `null`, `$"`, `=>`, `//`, `typeof()` | Warning | Grep all `.xaml`; VB uses `Nothing` and `GetType()` |
| No default display names (`Sequence`, `Assign`, `If`) | Warning | Check ST-MRD-002 |
| No nesting over 7 levels | Warning | Check ST-MRD-009 |
| No empty Catch blocks | Warning | Check ST-DBP-003 |
| No empty Sequences | Info | Check ST-MRD-008 |
| No unreachable activities | Warning | Check ST-MRD-004 |
| Use Log Message, not Write Line | Warning | Check ST-MRD-011 |

### Naming

| Check | Severity | Verify |
|---|---|---|
| Variables use PascalCase/camelCase | Warning | Check ST-NMG-001; default regex: `^([A-Z]|[a-z])+([0-9])*$` |
| DataTables use `dt_` prefix | Info | Check ST-NMG-009; it is not part of ST-NMG-001 |
| Arguments use `in_`, `out_`, `io_` prefixes | Warning | Check ST-NMG-002 |
| No variable/argument shadowing | Warning | Check ST-NMG-005 and ST-NMG-006 |
| Activity display names are descriptive | Warning | Check ST-MRD-002 |
| Workflow names use Verb + Object PascalCase | Info | Manual check, e.g. `GetTransactionData.xaml`, `ProcessInvoice.xaml` |

### Required containers

| Activity | Required container | Severity if missing |
|---|---|---|
| Excel | `ExcelApplicationScope` or `ExcelApplicationCard` | Critical |
| UI Automation | `Use Application/Browser` (`NApplicationCard`) | Critical |
| Word | `WordApplicationScope` | Critical |
| Office 365 | Office 365 scope activity | Critical |
| GSuite | GSuite scope activity | Critical |

### Conflicting properties

Set only one property in each pair: `Password` / `SecurePassword` (Critical); `EditPassword` / `SecureEditPassword` (Critical); `SimulateClick` / `SendWindowMessages` (Warning).

### Selectors

Assess the majority tier: Tier 1 `id`, `automationid` (highest; no finding); Tier 2 `name` + `role`, `name` + `controltype` (high; no finding); Tier 3 `aaname`, `innertext` (medium; Info if majority); Tier 4 `tag` + `parentid`, `class` (low; Warning if majority); Tier 5 `idx`, `tableRow`, or position-based (worst; Warning per occurrence).

| Check | Severity | Verify |
|---|---|---|
| No `idx=` selectors | Warning | Grep `.xaml` |
| No environment-specific selector data (qa/uat/prod URLs, ports) | Warning | Grep selectors |
| Dynamic attributes use wildcards where appropriate | Info | Inspect selectors |
| Use Object Repository instead of hardcoded selectors | Warning | Check `.objects/` usage |
| Element Exists / Check App State precedes interactions where appropriate | Info | Inspect patterns |
| Modern UI Descriptors use Strict + Fuzzy + Image + Anchor | Info | Grep `.xaml` for `NUnifiedTargetDefinition` |
| Selector depth is minimal; prefer 2–3 levels | Info | Inspect `.xaml` |

### Security and performance

| Check | Severity | Verify |
|---|---|---|
| Password variables use `SecureString` | Critical | Check ST-SEC-007 and ST-SEC-008 |
| No `SecureString` conversion to plain `String` | Warning | Check ST-SEC-009 |
| Credentials come from Orchestrator assets/Credential Store, not literals | Critical | Check `Get Credential` and literals |
| No sensitive data in logs | Warning | Inspect messages |
| No PII in queue-item specific data, or encrypt it | Warning | Inspect queue creation |
| No hardcoded Delay activities | Warning | Check ST-DBP-026 and ST-PRR-004 |
| Use Simulate Click / SendWindowMessages where possible | Info | Inspect UI properties |
| Avoid nested For Each loops over large DataTables; use LINQ | Warning | Inspect loops |
| Filter large DataTables before processing | Info | Inspect data flow |
| Avoid excessive logging in tight loops | Warning | Inspect placement |

## 4. Hybrid Projects

| Check | Severity | Verify |
|---|---|---|
| Separate XAML UI automation from coded business logic | Info | Review organization |
| No duplicated logic across coded and XAML workflows | Warning | Compare behavior |
| Cross-mode invocation uses `InvokeWorkflowFile` correctly | Warning | Inspect invocations |
| Shared data models are in Coded Source Files, not duplicated | Info | Inspect models |

## 5. REFramework Compliance (Queue-Based Projects)

> **Transaction Granularity:** REFramework correctness requires that the queue item's declared unit of work matches the unit of work `ProcessTransaction.xaml` actually performs. Run Step 3a (Unit of Work Discovery) in SKILL.md before this section — classify the shape as one-to-one / one-to-many / unclear. Strong signal of a one-to-many shape: presence of `CheckIf<X>Exists.xaml` or `Verify<X>Exists.xaml` in the project (homegrown idempotency guards compensating for bulk-in-transaction). See [rpa-common-issues.md](rpa-common-issues.md) → "Transaction Shape: One-to-Many" for the full signals, severity matrix, fixes, and the "When it cannot be split — hardening checklist" subsection.

Apply this section when the project uses or should use REFramework.

### Architecture and transaction flow

| Check | Severity | Verify |
|---|---|---|
| State machine has Init, GetTransactionData, ProcessTransaction, EndProcess | Warning | Read Main.xaml |
| All 7 stock transitions exist: Init→GetTx, Init→End, GetTx→ProcessTx, GetTx→End, ProcessTx→GetTx on Success, ProcessTx→GetTx on BusinessRuleException, ProcessTx→Init on SystemException | Warning | Trace transitions |
| Init has SystemException → Init self-retry; stock template's Init → End is insufficient | Warning | Trace transient-failure handling |
| Queue projects fetch items per-item in GetTransactionData, not Init; non-queue projects load bulk data in Init | Warning | Inspect InitAllApplications / InitAllSettings for Read Range, Get Queue Items, and Data Scraping |
| Do not force REFramework onto single-shot/stateless processes | Info | Use a linear workflow when there is no real transaction iteration |
| Non-queue `SetTransactionStatus` handles `QueueRetry` correctly and does not retain queue-only `in_TransactionItem.RetryNo` logic | Critical | Grep for `QueueRetry` and retry logic |
| DataTable GetTransactionData uses `dt.Rows(in_TransactionNumber - 1)` | Warning | Check 0-index/1-index handling |
| `Process.xaml` processes exactly one transaction per invocation | Critical | Review Process.xaml |
| Framework/ files are unmodified: InitAllSettings, framework GetTransactionData, framework SetTransactionStatus | Warning | Check Framework/ |
| Business logic is only in root-level Process.xaml, root GetTransactionData.xaml, and root SetTransactionStatus.xaml | Warning | Review locations |

### Failure paths

| Path | Required behavior | Severity |
|---|---|---|
| System Exception → Retry | ProcessTransaction propagates, state machine transitions to Init, apps reopen, same item retries | Critical |
| Business Exception → Skip | `BusinessRuleException` is caught without retry; status becomes Failed-Business; transition goes to GetTransactionData | Warning |
| Queue Empty → Clean Exit | GetTransactionData returns Nothing/null; transition reaches EndProcess; CloseAllApplications runs | Warning |
| Max Retries Exceeded → Fail Item | After N system exceptions, `MaxRetryNumber` is reached; item is Failed and processing continues in GetTransactionData | Critical |
| Init Failure → Retry or Stop | Init self-retries while `ProcessRetries` is below max, then transitions to EndProcess | Warning |

### Config.xlsx

| Check | Severity | Verify |
|---|---|---|
| `Data/Config.xlsx` exists with Settings, Constants, Assets sheets | Warning | Check file |
| No duplicate keys across sheets | Critical | Read workbook; all keys share one Dictionary |
| No credentials/tokens in Settings or Constants | Critical | Inspect values |
| Assets sheet contains Orchestrator Asset names, not values | Warning | Inspect sheet |
| `OrchestratorQueueName` is in Settings, not hardcoded | Warning | Inspect workflows and Settings |
| `OrchestratorQueueFolder` is set when using modern folders | Warning | Inspect Settings |

### Retry configuration

| Check | Severity | Verify |
|---|---|---|
| `MaxRetryNumber` = 0 with Orchestrator queue retries | Critical | Check Constants; double retry can produce multiplicative attempts (e.g., 3x3=9) |
| `MaxRetryNumber` > 0 for Excel, DataTable, or API sources | Warning | Check Constants |
| `MaxConsecutiveSystemExceptions` is configured and not 0 | Warning | Check Constants; 0 disables the circuit breaker |
| Queue `Max # of Retries` is 1–50, typically 3 | Warning | Check queue settings |
| Queue auto-retry is enabled for Application Exceptions | Warning | Check queue settings |

### Exceptions and lifecycle

| Check | Severity | Verify |
|---|---|---|
| Data/validation issues throw `BusinessRuleException`, not `System.Exception` | Critical | Grep usage |
| Business exceptions transition to GetTransactionData, not Init | Critical | Trace handling |
| Application/System exceptions recover via CloseAll → KillAll → re-init | Warning | Trace flow |
| `SetTransactionStatus` runs on Success, Business Exception, and Application Exception paths | Critical | Trace every exit |
| Application Exceptions capture a screenshot | Warning | Check configuration |
| Transaction reference is set and within the 128-character limit | Info | Inspect field |
| CloseAllApplications.xaml and KillAllProcesses.xaml are implemented, not empty | Warning | Read files |
| InitAllApplications.xaml retrieves credentials from Orchestrator assets | Warning | Read file |
| InitAllApplications.xaml checks whether apps are already open | Info | Inspect app-state validation |
| First Init calls KillAllProcesses.xaml for a clean state | Info | Trace Init |
| GetTransactionData handles Orchestrator Stop/Terminate signals | Warning | Inspect workflow |

### Non-Queue REFramework (Excel/DataTable/API)

| Check | Severity | Verify |
|---|---|---|
| `TransactionItem` changes from `QueueItem` to `DataRow`, `Dictionary`, or appropriate type | Critical | Check Main.xaml |
| `TransactionData` changes from default to `DataTable` or appropriate collection | Critical | Check Main.xaml |
| Data loads during Init, not GetTransactionData | Warning | Trace states |
| GetTransactionData uses `io_TransactionNumber` as index and returns Nothing when exhausted | Critical | Read root workflow |
| SetTransactionStatus updates source data, such as an Excel status column | Warning | Read root workflow |
| `MaxRetryNumber` > 0 for local retries | Warning | Check Constants |

## 6. Logging

| Check | Severity | Verify |
|---|---|---|
| Use Log Message, not Write Line | Warning | Check ST-MRD-011 |
| Minimum logging exists in each workflow | Warning | Check ST-USG-020 |
| More than 80% of invoked sub-workflows have LogMessage near first and last activity | Warning | Count `(workflows with bookends / total invoked workflows)`; below 80% is a finding |
| Every Catch block has an error-level log | Warning | Inspect catches |
| Production configuration has no Verbose/Trace logging | Info | Inspect log levels |
| Business context uses custom log fields via Add Log Fields | Info | Inspect usage |
| Logs contain no PII, credentials, or other sensitive data | Critical | Review content |

## 7. Test Coverage

| Check | Severity | Verify |
|---|---|---|
| Critical workflows have tests | Warning | Glob `**/*[Tt]est*` |
| Coded tests use `[TestCase]`; other tests use a Test Case project type | Warning | Inspect organization |
| Assertions verify outcomes, not merely successful execution | Info | Read assertions |
| Data-driven tests use `.variations/` | Info | Check parameterization |
| Tests are independent | Info | Check shared state |
| Tests use synthetic/test data, never production connections/data | Warning | Inspect sources |

## 8. Workflow Analyzer

Run Workflow Analyzer and verify no Error-level violations.

### Must pass (Error level)

- ST-ANA-005: project.json exists
- ST-ANA-006: Main workflow exists
- ST-DBP-023: No empty workflows
- ST-SEC-007: SecureString for password arguments
- ST-SEC-008: SecureString for password variables
- ST-USG-009: No unused variables
- ST-NMG-006: No variable-argument name conflicts

### Should pass (Warning level)

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

| Check | Severity | Verify |
|---|---|---|
| All project.json entry points are correctly defined | Critical | Verify `entryPoints` |
| Dependencies are pinned to specific versions | Warning | Read project.json |
| No hardcoded environment-specific URLs or paths | Warning | Grep project |
| No debug artifacts or test data | Info | Inspect project |
| Global Exception Handler is configured | Info | Check project settings |
| Every entry point validates with 0 errors | Critical | Run `uip rpa validate --file-path "<ENTRY_FILE>" --project-dir "<PROJECT_DIR>" --output json` |
| Project builds cleanly | Critical | Run `uip rpa build "<PROJECT_DIR>" --output json`; build catches unknown member names and invalid enum values that `validate` misses (SKILL.md Critical Rule 2) |
| Recent successful-run evidence exists | Info | Check job history/test results; do NOT run the automation during review because `uip rpa run` executes UI actions and writes; route runtime verification to `uipath-rpa` |

## 10. Windows-Legacy Compatibility

### Support status

Windows-Legacy is supported indefinitely in Studio LTS. Studio LTS 2024.10, 2025.10, 2026.10, and **all future LTS releases** continue to support creating, opening, and editing Windows-Legacy projects. Studio LTS provides 24 months Mainstream + 12 months Extended support per release. Legacy projects validate, run, and deploy correctly and are **not** deployment blockers. Studio STS does not support Legacy; Legacy teams must stay on LTS. Deprecation means no new features are added to Legacy, not that Legacy will be removed.

> **NEVER flag Windows-Legacy as Critical based on framework alone.** Route Legacy-specific deep validation to `uipath-rpa` (Legacy mode).

The decision is what the project gives up by staying on Legacy, not whether it can continue using Legacy.

### Features unavailable to Legacy

When recommending migration, lead with the 2–3 features most relevant to the project; do not list the whole menu.

| Rank | Category | Feature and impact |
|---|---|---|
| 1 | Maintenance | **Healing Agent**: runtime selector self-healing; Legacy requires tickets and redeployments |
| 2 | UI Automation resilience | **Unified Target Method** (Strict + Fuzzy + Image + Anchor); Legacy has classic single-strategy selectors |
| 3 | Reusable UI management | **Object Repository + UI Libraries**: centralized, hierarchical, versioned descriptors; Legacy has limited Object Repository support and no shared UI Library consumption |
| 4 | Testing quality | **Coded test cases (C#)** + **Test Manager integration**; Legacy has only Studio Test Activity testing, with limited assertions and no mocking framework |
| 5 | Development velocity | **Autopilot**; unavailable to Legacy |
| 6 | ScreenPlay / modern UI orchestration | **ScreenPlay**; available only for Modern projects |
| 7 | Platform capabilities | **AI Agents + Maestro orchestration + Agentic Automation**; Legacy cannot participate as an actor or invoke/be invoked by these |
| 8 | Code-based logic | **Coded workflows (C#)** alongside XAML: type safety, unit testing, and IDE refactoring |
| 9 | Performance and security | **Modern .NET (6+)**; Legacy uses .NET Framework 4.6.1 with aging security libraries |
| 10 | Platform reach | **Cross-platform execution** including Linux robots |
| 11 | Studio cadence | **Studio STS** two-month releases; Legacy is limited to annual Studio LTS |
| 12 | Developer ergonomics | New design experience, Data Manager globals/constants, customizable library activity layouts |

### Tailored recommendations

| Project context | Lead with |
|---|---|
| Heavy UI automation, many selectors, high maintenance | Healing Agent + Unified Target + Object Repository |
| No tests or weak tests | Coded test cases + Test Manager |
| Long XAML or complex business logic | Coded workflows (C#) |
| Human-in-the-loop or multi-actor orchestration | Maestro + Agentic Automation + Agents |
| One environment or scaling concerns | Cross-platform execution + Studio STS |
| Many similar projects | Object Repository + UI Libraries (shared descriptors) + Autopilot |

### Severity matrix

| Condition | Severity |
|---|---|
| Legacy with team intentionally using Studio LTS | Info |
| Legacy and the team would benefit from top-ranked features (heavy UI maintenance, missing tests, AI/agent use cases, or coded-logic complexity) | Warning |
| Legacy required for SOAP web services | Info — valid design; document reason |
| Greenfield project started on Legacy without technical justification | Warning |
| Legacy library consumed by Windows/Cross-platform project | Warning — migrate library first |

### Migration blockers

When migration is being considered, scan for activities that cannot be auto-migrated; they require manual rework.

**UI Automation blockers (Activity Migrator cannot convert):**

| Activity/pattern | Severity |
|---|---|
| All Computer Vision activities (CV Click, CV Check, CV Get Text, CV Screen Scope, etc.) | Warning |
| All Trigger activities (Click Trigger, Hotkey Trigger, Element State Change Trigger, Monitor Events, Key Press Trigger, Mouse Trigger, System Trigger) | Warning |
| Anchor Base | Warning — manually replace with modern anchor pattern |
| Context Aware Anchor; Element Scope | Warning |
| Double Click / Double Click Image / Double Click OCR Text / Double Click Text | Warning |
| Classic OCR engines (Microsoft OCR, Tesseract OCR, Google Cloud Vision OCR, Microsoft Azure Computer Vision OCR) | Warning |
| Callout / Tooltip | Warning |
| Set Clipping Region / Set Web Attribute | Warning |
| Block User Input / Indicate On Screen / Inject .NET Code / Invoke ActiveX Method | Warning |
| Find Image Matches / Load Image / Save Image / Get Source Element | Warning |

**Mail blockers (Classic Outlook Desktop → M365):**

| Activity/pattern | Severity |
|---|---|
| `Outlook Desktop Mail Messages Trigger` — skipped entirely; M365 has no folder-monitoring equivalent | Critical — fundamental capability loss without rework |
| `Get Outlook Desktop Mail Messages` with filter options — filters do not migrate | Warning — recreate manually |
| Other Classic Outlook activities (Send, Reply, Move, Delete, Mark Read, Set Categories, Save) | Info — auto-migrate but require ConnectionId configuration |

### Migration tool

| Scenario | Tool |
|---|---|
| Single project, framework-only (W-L → W) | Studio's built-in Converter |
| Multiple projects / bulk conversion | **Activity Migrator** (`UiPath.Upgrade.exe bulk`) |
| Classic UI Automation | **Activity Migrator** — also migrates Classic → Modern UIA |
| Classic Outlook Desktop mail | **Activity Migrator** — also migrates to M365 Mail |
| Activity-level migration | **Activity Migrator** |

> Studio's built-in Converter does framework-only conversion. For most real-world Legacy projects (which use Classic UIA), **Activity Migrator** is the right tool.

### Migration version requirements

| Check | Severity |
|---|---|
| Planned migration uses `UiPath.UIAutomation.Activities` at an Activity-Migrator-supported version; check current UiPath docs | Warning |
| Planned M365 mail migration uses `UiPath.MicrosoftOffice365.Activities` at a Migrator-supported version | Warning |
| Studio 2024.10+ is available to open the migrated project | Warning |
| Studio supports ST-AMG-001 post-migration rule; use recent LTS/STS and check current docs | Info |

### Migration pre-flight

| Check | Severity |
|---|---|
| Create a project/library backup | Warning |
| Run Activity Migrator `analyze` first as a dry run and review the SARIF report before commit | Warning |
| Migrate libraries before consumer projects | Critical |
| Do not change project/library names | Warning |
| Verify NuGet feeds in `NuGet.config`, or configure Orchestrator PAT/OAuth | Warning |
| For M365 mail, prepare a `--config` file with ConnectionId mappings | Warning |
| Pilot one project before `bulk` | Info |

### Post-migration

If `.upgrade` exists, modern activities coexist with Legacy-originated naming, or synthetic `Use Application/Browser` scopes appear, check:

| Check | Severity |
|---|---|
| ST-AMG-001 passes with post-migration annotations | Warning |
| SARIF report from `.upgrade` is reviewed and archived | Info |
| Organic application scopes are preserved and synthetic scopes merged correctly | Warning |
| Migrated M365 activities have populated ConnectionId values | Critical — empty ConnectionIds cause runtime failures |
| End-to-end tests pass | Warning |
| Execution time is monitored because modern activities may initially be slower | Info |