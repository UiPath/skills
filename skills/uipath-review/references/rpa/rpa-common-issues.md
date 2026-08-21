# RPA Common Issues

Catalog of frequently found UiPath RPA project issues, with detection methods, severity guidance, and fixes.

## Structural Issues

### Missing .cs.json Metadata Files

**Symptom:** Coded workflow `.cs` files lack companion `.cs.json` files.

**Impact:** The workflow is absent from Studio entry points, cannot be invoked reliably, and has undiscoverable arguments.

**Detection:** Run:
```bash
# Find .cs files that should have .cs.json companions
# (files with [Workflow] or [TestCase] attributes)
grep -rl "\[Workflow\]\|\[TestCase\]" --include="*.cs" . | while read f; do
  [ ! -f "${f}.json" ] && echo "Missing: ${f}.json"
done
```

**Fix:** Use `uipath-rpa` skill to regenerate metadata, or run `uip rpa validate` to flag missing metadata.

### Broken Entry Points

**Symptom:** `project.json` `entryPoints` references missing or renamed files.

**Detection:** Read `project.json` → `entryPoints` and verify every `filePath` exists.

**Fix:** Update `entryPoints` to actual workflow files or remove stale entries.

### Windows-Legacy Compatibility Lock-In

**Symptom:** `project.json` lacks `targetFramework` or has `targetFramework: "Legacy"`; this is the reliable marker. Expression language is usually VisualBasic, but Legacy C# projects exist.

**Support status:** Legacy is supported **indefinitely** in Studio LTS (2024.10, 2025.10, 2026.10, and all future LTS releases). It is NOT a deployment blocker or mid-term support risk. Deprecation means no new Legacy features, not removal.

**Severity:** NEVER flag as Critical based on framework alone. Use Warning when it blocks desired modern features, or Info when Studio LTS is the organizational standard.

**Migration guidance:** Lead with the 2-3 features relevant to actual pain points: heavy UI maintenance → Healing Agent + Unified Target + Object Repository; weak testing → coded tests + Test Manager; AI use cases → Autopilot + Agents. SOAP web services are a valid reason to stay on Legacy because they are supported only in Legacy.

**Tooling:** Route Legacy-specific deep validation to `uipath-rpa` (Legacy mode). Standard `uip rpa` tooling targets Windows/Cross-platform projects; Legacy mode in `uipath-rpa` uses the `uip rpa-legacy` CLI internally.

Ranked feature list, severity matrix, migration tooling and blockers, pre-flight order, and post-migration checks: [rpa-review-checklist.md §10 "Windows-Legacy Compatibility"](rpa-review-checklist.md).

### Wrong Expression Language

**Symptom:** XAML expressions do not match the project's `expressionLanguage`.

**Impact:** Expressions fail to compile.

**Detection:** Read `project.json` `expressionLanguage`, then inspect XAML for mismatched syntax.

**Fix:** Rewrite expressions in the configured language, or change the project setting and rewrite all expressions.

## Performance Issues

### Oversized XAML Files

**Symptom:** XAML exceeds 500KB; files above 5MB are critical and files above 7MB can hang Studio.

**Impact:** Studio is slow to open, edit, and save.

**Detection:** Run:
```bash
find . -name "*.xaml" -size +500k -exec ls -lh {} \\
;
```

**Fix:** Split workflows with Invoke Workflow File and extract reusable sequences.

### Hardcoded Delay Activities

**Symptom:** Fixed-time `Delay` activities replace element-based waits.

**Impact:** Delays waste time on fast systems and fail on slow systems.

**Detection:** Run Workflow Analyzer rules ST-DBP-026 and ST-PRR-004; also grep XAML for `Delay` activities.

**Fix:** Use `Element Exists`, `Check App State`, `On Element Appear`, or `Retry Scope` with element-based conditions.

### Progressive Slowdown in Long-Running Processes

**Symptom:** Processing slows progressively after 1+ hours without crashing.

**Root causes:** Orphaned `EXCEL.EXE`, browser DOM growth, uncleared DataTables, and per-iteration logging.

**Detection:** For loops over 50 iterations, verify `KillAllProcesses.xaml` kills Excel/browser processes; verify browsers close and reopen every 50-100 web iterations; check for growing DataTables and `Log Message` inside tight loops.

**Fix:** Clean resources periodically; kill Excel in Finally blocks; close/reopen browsers every N iterations; clear temporary variables; log summaries before/after loops instead of every iteration.

### Nested Loops Over Large DataTables

**Symptom:** Nested `For Each Row` or `For Each` activities process large datasets.

**Impact:** O(n^2) work; 1000 rows can produce 1,000,000 iterations.

**Detection:** Search XAML for nested `ForEachRow` or `ForEach` activities.

**Fix:** Use LINQ, `Filter Data Table`, `Join Data Table`, or `Dictionary`/`HashSet` lookups.

### Excessive Logging in Loops

**Symptom:** `Log Message` runs on every iteration of a tight loop.

**Impact:** Orchestrator log flooding, slower execution, and higher storage cost.

**Detection:** Inspect `For Each` and `While` loops for `Log Message` activities.

**Fix:** Log summaries before/after loops, or counters at intervals such as every 100 items. Set production logging to Info.

### Unoptimized Selectors

**Symptom:** Selectors use unstable attributes such as `idx`, dynamic IDs, or session-specific values.

**Impact:** Intermittent, flaky runs.

**Detection:** Run:
```bash
grep -r 'idx=' --include="*.xaml" .
```

**Fix:** Prefer stable `id`, `name`, and `automationid`; wildcard dynamic portions; use Anchor Base and Object Repository.

## Security Issues

### Hardcoded Credentials

**Symptom:** Passwords, API keys, or connection strings are embedded in XAML, `Config.xlsx`, or source code.

**Impact:** Credentials may appear in source control, logs, and packages. **Severity: Critical.**

**Detection:** Run:
```bash
# Check for common credential patterns in all project files
grep -ri "password\s*=\|" --include="*.xaml" --include="*.cs" --include="*.json" .
grep -ri "apikey\|api_key\|secret\|token" --include="*.xaml" --include="*.cs" --include="*.json" .
```

**Fix:** Use Orchestrator Credential Assets, CyberArk, Azure Key Vault, HashiCorp Vault, or Windows Credential Manager. Retrieve with `Get Credential`.

### SecureString Misuse

**Symptom:** `SecureString` becomes plain `String` through `.ToString()` or `new NetworkCredential("", secureString).Password`.

**Impact:** Protection is defeated and the password may enter memory or logs.

**Detection:** Run Workflow Analyzer rule ST-SEC-009 and grep for `NetworkCredential` or `SecureStringToString` patterns.

**Fix:** Keep passwords as `SecureString`; use `Type Secure Text` and `SecureString` arguments.

### Sensitive Data in Logs

**Symptom:** Logs contain PII, credentials, or business-sensitive values.

**Impact:** Sensitive information is exposed through Orchestrator logs.

**Detection:** Review all `Log Message` interpolations for sensitive fields.

**Fix:** Redact or mask values, use Add Log Fields selectively, and review Orchestrator output after testing.

## Maintainability Issues

### God Workflows

**Symptom:** One file has 50+ activities and deeply nested logic; >200KB is suspicious.

**Impact:** Difficult understanding, debugging, testing, and safe modification.

**Detection:** Count activities and nesting depth; run ST-MRD-009.

**Fix:** Extract logical sections into single-responsibility sub-workflows. Target 15-30 activities per workflow.

### Default Activity Names

**Symptom:** Names remain `Sequence`, `Assign`, `If`, `Click`, or `Type Into`.

**Impact:** Logic cannot be understood without opening properties.

**Detection:** Run Workflow Analyzer rule ST-MRD-002.

**Fix:** Rename activities by purpose, such as `Click 'Login' Button`, `Assign Invoice Total`, or `Check if Customer Exists`.

### Magic Strings and Numbers

**Symptom:** Repeated literals such as column indices, status codes, paths, and email addresses are scattered through workflows.

**Impact:** Changes require error-prone manual replacement.

**Detection:** Run ST-USG-005 and review repeated literals.

**Fix:** Use variables, `Config.xlsx`, Orchestrator assets, and named constants.

### Unused Variables and Dependencies

**Symptom:** Variables are never referenced or packages provide no used activities.

**Impact:** Clutter, confusion, and slower package restore.

**Detection:** Run ST-USG-009 and ST-USG-010.

**Fix:** Remove unused variables and packages.

### Deep Nesting

**Symptom:** More than three nested If-Else levels or deeply nested loops.

**Impact:** Logic is difficult to follow and modify.

**Detection:** Run ST-MRD-007 and ST-MRD-009.

**Fix:** Extract workflows, use Switch/Flowchart, and use early-return decision nodes.

## Error Handling Issues

### Throw Used Instead of Rethrow (Stack Trace Lost)

**Symptom:** A Catch uses `Throw` with `New Exception(exception.Message)` instead of `Rethrow`.

**Impact:** Original stack trace is lost. **Severity: Warning.**

**Detection:** Inspect `<Throw>` inside `<Catch>` that creates a new exception. It should use argument-free `Rethrow`.

**Fix:** Replace with `Rethrow`; if wrapping is required, use `Throw New Exception("context", exception)`.

### Global Exception Handler Causing Cascading Retry Storms

**Symptom:** `GlobalHandler.xaml` unconditionally sets `result = Retry`.

**Impact:** Parent handlers multiply nested retries and may loop indefinitely. **Severity: Warning.**

**Detection:** Read `GlobalHandler.xaml`; flag unconditional retry without activity- or exception-type filtering.

**Fix:** Exclude Throw, Rethrow, Try-Catch, and Retry Scope. Retry only selected transient-prone activities such as HTTP and UI actions.

### Global Exception Handler + REFramework (Redundant and Conflicting)

**Symptom:** Both `Framework/` and `GlobalHandler.xaml` exist.

**Impact:** The global handler interferes with REFramework state transitions and recovery. **Severity: Warning.**

**Detection:** Check for both paths.

**Fix:** Remove `GlobalHandler.xaml` from REFramework projects and use `SetTransactionStatus` and `RetryCurrentTransaction`.

### Empty Catch Blocks

**Symptom:** Catch body is empty.

**Impact:** Errors are silently swallowed.

**Detection:** Run ST-DBP-003.

**Fix:** At minimum log the exception; then handle, rethrow, or escalate deliberately.

### No Business vs System Exception Distinction

**Symptom:** All exceptions are treated identically.

**Impact:** Business errors are retried and system errors are not appropriately retried.

**Detection:** Grep `.xaml` and `.cs` for `BusinessRuleException`; inspect REFramework status handling.

**Fix:** Throw `BusinessRuleException` for data/validation issues, such as `Throw New BusinessRuleException("Invoice amount is negative")`; let system exceptions propagate for transient retry.

### ContinueOnError Overuse

**Symptom:** Multiple activities use `ContinueOnError=True` or `ContinueOnError="{x:Null}"` as blanket suppression.

**Impact:** Invalid state continues downstream.

**Detection:** Grep XAML for `ContinueOnError="True"` or `ContinueOnError="{x:Null}"`.

**Fix:** Remove it and use Try-Catch. Retain only with an explicit reason annotation.

### Missing Finally Blocks for Resource Cleanup

**Symptom:** Resource-wrapping Try-Catch lacks Finally cleanup.

**Impact:** Files, database connections, and applications leak across retries and Init cycles.

**Detection:** Inspect Try-Catch around file I/O, database, and application scopes for a cleanup-containing Finally.

**Fix:** Close/dispose resources in Finally: `Close Application`, `Kill Process`, or `Close Workbook`. This is critical in REFramework `Process.xaml` and `SetTransactionStatus`.

### Generic Exception Catching

**Symptom:** Every Catch handles only `System.Exception`.

**Impact:** Transient, business, and application failures receive inappropriate handling.

**Detection:** Inspect Catch types; generic-only handling is a code smell.

**Fix:** Catch specific types first, such as `TimeoutException`, `SelectorNotFoundException`, and `BusinessRuleException`. Add a final `System.Exception` safety catch that logs full details and rethrows.

### Missing Retry Logic for External Calls

**Symptom:** HTTP, API, or database operations are outside Retry Scope.

**Impact:** Transient failures become permanent failures.

**Detection:** Inspect HTTP Request, Invoke Method, and database activities.

**Fix:** Use Retry Scope with suitable count and interval; use exponential backoff for API rate limiting.

## Queue and Transaction Issues

### No Queue for High-Volume Processing

**Symptom:** More than 50 independent items are processed sequentially without Orchestrator queues.

**Impact:** No per-item retry, audit trail, or distributed processing.

**Detection:** Check whether a dataset is read and looped without queue use.

**Recommendation:** For volume >50 items/run AND independent items, recommend Dispatcher-Performer with queues. Flag **Info** because low-volume or dependent processing may be intentional.

### Hardcoded Queue Names

**Symptom:** Queue names are literal strings in `Add Queue Item` or `Get Transaction Item`.

**Impact:** Environment changes require republishing.

**Detection:** Inspect those activities for literal names.

**Fix:** Store names in `Config.xlsx` or Orchestrator assets and use `Config("QueueName")`.

### Missing Transaction Status Updates

**Symptom:** `Set Transaction Status` is absent on success or failure paths.

**Impact:** Items remain In Progress for ~24 hours before abandonment.

**Detection:** Inspect every `ProcessTransaction` path.

**Fix:** Set status on success and failure/catch paths, using Finally where appropriate.

### Queue Items Stuck "In Progress" After Bot Crash

**Symptom:** A crash leaves an item In Progress for 24 hours; HITL work may be abandoned while legitimately waiting.

**Detection:** Check Init for orphan cleanup querying old In Progress items and resetting them; check long-running/HITL workflows for the long-running workflow template.

**Fix:** In Init, run `Get Queue Items` filtered by `InProgress` and age >2 hours, then set stale items to Failed for retry. Use the long-running workflow framework for HITL.

## REFramework-Specific Issues

### Double-Retry Configuration

**Symptom:** `MaxRetryNumber > 0` in `Config.xlsx` and `Max # of Retries > 0` on the Orchestrator Queue.

**Impact:** Retries multiply; values of 3 and 3 allow up to 9 attempts.

**Detection:** Read `Config.xlsx` Constants and the queue configuration.

**Fix:** Use one mechanism. For queue-based processing set `MaxRetryNumber=0` and configure queue retries; otherwise use `MaxRetryNumber`.

### Transaction Shape: One-to-Many (Bulk-in-Transaction / Thick Transaction)

**Definition:** A declared input represents one entity, but the execution body iterates over a collection of business entities and performs external effects per sub-item. This applies to RPA queues, flows, agents, and API workflows.

**Mechanical classification:** Both conditions must hold:
1. The body uses `ForEach`, `While`, `for`, or `foreach` over a collection field of the declared input.
2. The loop body performs an external effect: side-effecting workflow invocation, HTTP call, queue operation, DB write, persistent UI action, file write outside Temp, or email send.

Session scope, shared credentials, one-portal framing, and PDD wording do not change the shape.

**Question A — Are sub-units independently splittable?**
- **Yes:** Invoices, orders, records, and files are free-standing; use dispatcher/performer so each is one atomic item.
- **No:** Sequential domains such as carrier group-plan enrollment, SAP multi-step transactions, or bank wire setup require in-place partial-failure hardening.
- If unclear, default to “yes, probably splittable” and recommend investigation.

**Question B — What recovery exists?** Count any of these as an idempotency or progress guard:
- Read-check-before-write: `Get X`, SELECT, HTTP GET, or `File Exists` immediately before the corresponding write.
- Conditional skip based on already exists/processed state.
- Queue dedup with `UniqueReference`.
- SQL `MERGE`, `INSERT ... ON CONFLICT`, `UPSERT`, or `INSERT ... WHERE NOT EXISTS`.
- HTTP `Idempotency-Key`, `If-Match`, or `If-None-Match` ETag.
- Status filter such as `WHERE Status != 'Processed'`.
- Pre-check workflow invocation whose display name or purpose contains, case-insensitively, `check`, `verify`, `exists`, `processed`, `already`, `idempoten`, or `skip`.
- Persistent per-sub-item progress written to queue `Output`, Data Service, or external state.

**Severity and finding framing:**

| Splittable? | Recovery posture | Severity | Finding framing |
|---|---|---|---|
| Yes | No guards + `MaxRetryNumber` < 2 | **Critical** | Split into dispatcher/performer; current architecture risks partial-state corruption on transient failure. |
| Yes | Guards + weak progress output | **Warning** | Consider dispatcher/performer for better analytics and retry isolation. |
| No | No guards, no progress tracking | **Warning** | Add idempotency guards and per-sub-item progress markers; replay currently repeats prior work. |
| No | Guards + adequate retry but no per-sub-item progress output | **Info** | Add per-sub-item progress markers to queue Output for observability. |
| Yes | Guards + retry + per-sub-item output | **Info** | Working with compensation; consider dispatcher/performer if volume grows. |

#### When it cannot be split — hardening checklist

Verify every safeguard below. Report each missing safeguard as a separate numbered finding:

| # | Safeguard | Verification | Severity if missing |
|---|---|---|---|
| 1 | **Per-sub-item try-catch** | Each sub-item write has its own Try-Catch, not one Try-Catch around the loop. | Critical |
| 2 | **Per-sub-item status tracking** | Each success/failure is persisted in queue Output, Data Service, database, status column, or equivalent. | Warning |
| 3 | **Resumability after crash** | Retry resumes after the last completed sub-item rather than replaying from the beginning. | Warning |
| 4 | **Idempotency on each sub-item write** | Re-execution cannot create duplicates: check-before-write, UPSERT, UniqueReference, or conditional skip. | Critical |
| 5 | **Error classification per sub-item** | Business errors skip/move on; system errors retry or abort; they are not treated identically. | Warning |
| 6 | **Bounded retry per sub-item** | Failed sub-items have a maximum retry count; no infinite inner retry. | Warning |
| 7 | **Screenshot/evidence on sub-item failure** | Capture screenshot and error details before moving to the next item. | Info |
| 8 | **Summary logging after loop** | Report total, succeeded, failed, and skipped counts. | Warning |
| 9 | **Application state recovery between sub-items** | Return the application to a known state after failure before processing the next item. | Critical |
| 10 | **Timeout per sub-item** | Each item has a reasonable timeout independent of only the global job timeout. | Info |

Anchor findings on activity display names, never XAML line numbers. Use formats such as:
- `[W-005] One-to-many loop in Process.xaml (For Each 'Process Employees'): no per-sub-item status tracking — partial progress invisible after crash`
- `[C-003] One-to-many loop in Process.xaml (For Each 'Process Employees'): no idempotency guard on sub-item write — retry creates duplicate records`

**Why weak remediation matters:** One failure makes the invocation non-atomic; retries replay prior work; Orchestrator analytics report one transaction instead of N operations; `SetTransactionStatus` captures only the first inner failure; and long transactions lose work on host failure while occupying a robot.

**Misreadings that do not change the shape:** Portal transaction framing, one `Use Application/Browser`, shared credentials or connections, PDD terminology, and the existence of guards. Guards affect severity and remediation, not classification.

### System Exception Swallowed by Try-Catch in ProcessTransaction

**Symptom:** A Try-Catch in `Process.xaml` catches `System.Exception` without rethrowing.

**Impact:** REFramework marks the transaction Success instead of retrying; this is a common production failure.

**Detection:** Inspect every Catch in `Process.xaml`.

**Fix:** Rethrow system exceptions so they reach the state machine, or catch only `BusinessRuleException` without rethrowing.

### Config.xlsx Environment-Specific Values in Wrong Sheet

**Symptom:** URLs, paths, queue names, or credentials are in Settings or Constants instead of Assets.

**Impact:** Environment deployment requires editing and republishing; secrets may enter source control.

**Detection:** Verify Constants contains only true constants such as `MaxRetryNumber` and timeouts; Settings contains environment-agnostic settings; Assets contains environment-specific values referencing Orchestrator asset names.

**Fix:** Move environment-specific values to Assets, create assets per environment, and use `Config("AssetName")`.

### MaxConsecutiveSystemExceptions Disabled

**Symptom:** `MaxConsecutiveSystemExceptions` is `0` in `Config.xlsx` Constants.

**Impact:** The bot can process indefinitely while every transaction fails.

**Detection:** Read the Constants sheet.

**Fix:** Set a circuit-breaker value, typically 3-5.

### Empty CloseAllApplications and KillAllProcesses

**Symptom:** `Framework/CloseAllApplications.xaml` or `Framework/KillAllProcesses.xaml` contains only the default empty Sequence.

**Impact:** Applications accumulate, causing leaks, session conflicts, and stale selectors.

**Detection:** Read both files.

**Fix:** Implement graceful `Close Application` activities and `Kill Process` for each required application process.

### Business Logic in Framework Folder

**Symptom:** Custom logic is added to `Framework/` files such as `InitAllSettings.xaml`, framework-level `GetTransactionData.xaml`, or similar.

**Impact:** Template upgrades can overwrite it and the project becomes non-standard.

**Detection:** Compare Framework files with the original REFramework template on GitHub.

**Fix:** Move customizations to root-level `Process.xaml`, root `GetTransactionData.xaml`, or root `SetTransactionStatus.xaml`.

## Production Environment Issues

### Unattended Robot Session Failures

**Symptom:** Production-only desktop, selector, or foreground errors.

**Causes:** Screen resolution/DPI differences, RDP disconnects or Group Policy timeouts, UAC prompts, or the Windows “Display information about previous logons” policy.

**Detection:** Inspect production logs and compare development/production resolution and DPI.

**Fix:** Develop at production resolution; disable idle session timeouts through Group Policy; prevent UAC-triggering auto-start programs; align RDP settings.

### Excel Process Hanging

**Symptom:** Excel scope completes but `EXCEL.EXE` remains and the robot hangs.

**Detection:** Check for orphaned `EXCEL.EXE` and Excel activity timeouts.

**Fix:** Add `Kill Process` for `EXCEL.EXE` in `KillAllProcesses.xaml` and Finally blocks. In coded workflows use `System.Diagnostics.Process.GetProcessesByName("EXCEL")` to force-kill.

### Selector Breakage After Deployment

**Symptom:** Development selectors fail in production.

**Causes:** Browser, OS, application-version, resolution, or DPI differences.

**Detection:** Compare all those versions and settings.

**Fix:** Validate on production machines; use automationId, name, and role; avoid idx; use Object Repository and consider Healing Agent.

### Large Output Data Failures

**Symptom:** Large DataTables or JSON outputs cause message-size failures.

**Impact:** Output arguments exceed `maxMessageSizeInMegabytes`.

**Detection:** Inspect large output arguments.

**Fix:** Store large outputs in Storage Buckets or Data Service and process in batches.

### Browser Auto-Update Breaking Selectors

**Symptom:** Browser updates break AA-mode selectors, including known Chrome v114 and v117 failures involving iFrames and PDFs.

**Detection:** Check whether browser updates are controlled and inspect browser selectors for `aaname` or `role`.

**Fix:** Pin production browser versions by disabling auto-update; prefer UIA over AA; consider `--force-renderer-accessibility=complete`; configure Unified Target Method (Strict + Fuzzy + Image + Anchor).

## Silent Failure Patterns

### No Output Verification After Data Writes

**Symptom:** Excel, database, web-form, or API writes are not verified.

**Impact:** The bot reports success despite missing or duplicate records.

**Detection:** After every `Write Range`, `Submit Form`, HTTP POST, or database INSERT, check for read-back, count, or status-code validation. APIs require specific success-code validation, not merely 2xx.

**Fix:** Add verification; read back Excel and compare row counts, validate API response codes, and verify database affected-row counts.

### No Record Count Validation After Data Processing

**Symptom:** Filters, LINQ, or DataTable transformations do not compare input and output counts.

**Impact:** Dropped rows are reported as complete.

**Detection:** Check for count comparison after `Filter Data Table`, LINQ `.Where()`, and other transformations.

**Fix:** Log input and output counts after every transformation and flag unexplained output < input.

## Coded Workflow Pitfalls (C#)

### Namespace Clashes with Activity Packages

**Symptom:** Classes are named `Mail`, `Excel`, `Http`, `Browser`, `SAP`, or `PDF` and conflict with package namespaces.

**Impact:** Cryptic compilation errors.

**Detection:** Check class names and run:
```bash
grep -r "class (Mail|Excel|Http|Browser|SAP|PDF)[\\s{]" --include="*.cs" .
```

**Fix:** Use project-specific prefixes and avoid single-word package names.

### Global Using Directives Break Publishing

**Symptom:** C# 10 `global using` directives reference complex types.

**Impact:** Local compilation succeeds but NuGet packaging/publishing fails.

**Detection:** Grep `*.cs` for `global using` statements referencing non-primitive types.

**Fix:** Remove such global directives and use regular `using` statements per file; primitive `System` and `System.Linq` imports are acceptable.

### Library Invocation NullReferenceException

**Symptom:** A coded workflow works internally but fails from an external library consumer because `CodedWorkflow` accessors such as `system` or `uiAutomation` are uninitialized.

**Detection:** Test external invocation and inspect service accessor use.

**Fix:** Bootstrap the library correctly and invoke through generated strongly typed `workflows.<NAME>()` accessors, not direct class instantiation.

## Concurrency Issues

### Parallel Activity With Shared UI Resources

**Symptom:** `Parallel` branches interact with the same UI, keyboard, mouse, or application.

**Impact:** Branches share one desktop session; clicks and typing target incorrectly. `Isolated = True` does not fix this. **Severity: Warning.**

**Detection:** Inspect `Parallel` children for `Click`, `TypeInto`, or `UseApplicationBrowser` targeting the same application.

**Fix:** Use `Parallel` for I/O-bound work such as HTTP or independent file operations. Use multiple robots with queue distribution for UI parallelism.

## Deployment Issues

### NuGet Feed Unreachable in Production (Offline Robots)

**Symptom:** Production robots cannot reach required NuGet feeds.

**Impact:** Package restore fails at process start. **Severity: Warning.**

**Detection:** Inspect `project.json` custom feed references. Verify network access to every feed, OR verify `NUGET_FALLBACK_PACKAGES` points to pre-downloaded packages.

**Fix:** Configure fallback packages or make the Orchestrator feed reachable from all robots.

### NuGet NU1107 Assembly Version Conflict

**Symptom:** Transitive dependencies require conflicting assembly versions, producing `NU1107: Version conflict detected` on a clean robot restore.

**Impact:** Studio cache hides the issue; production and CI/CD fail. **Severity: Warning.**

**Detection:** Projects with >15 direct dependencies are high risk. Run a clean package restore.

**Fix:** Pin the conflicting transitive dependency to a compatible version or remove the causing package.

### Invoke Workflow Argument Drift

**Symptom:** Workflow arguments changed but `Invoke Workflow File` call sites retain stale bindings.

**Impact:** No XAML compile-time error; runtime null or missing-argument errors occur. **Severity: Warning.**

**Detection:** Extract each workflow's arguments and compare them with every `InvokeWorkflowFile` binding. Flag missing or extra names.

**Fix:** Re-import arguments in Studio after every argument change.

### Get Asset Used for Credential Type (Wrong Activity)

**Symptom:** `Get Asset` retrieves a Credential-type Orchestrator asset instead of `Get Credential`.

**Impact:** Runtime failure or unusable password. **Severity: Warning.**

**Detection:** Identify credential assets in Config.xlsx and inspect XAML `GetAsset` use for those names.

**Fix:** Replace with `Get Credential`. In REFramework, put credential asset names in the Settings sheet for `Get Credential`, not the Assets sheet for `Get Asset`.

### Per-Robot Asset Values Missing for Production Robots

**Symptom:** Per-robot/per-user assets lack values for one or more production robots.

**Impact:** Robots receive a global fallback or Nothing and fail with “asset does not have a value associated with this robot.” **Severity: Warning.**

**Detection:** Verify every per-robot asset has values for all robots/machines assigned to the deployment folder.

**Fix:** Assign all production values or use a global asset when every robot needs the same value.