# RPA Common Issues

Catalog of frequently found issues in UiPath RPA projects, with detection methods and recommended fixes.

## Structural Issues

### Missing .cs.json Metadata Files

**Symptom:** Coded workflow `.cs` files exist without companion `.cs.json` files.

**Impact:** The workflow won't appear in Studio's entry points or be invocable from other workflows. Arguments won't be discoverable.

**Detection:**
```bash
# Find .cs files that should have .cs.json companions
# (files with [Workflow] or [TestCase] attributes)
grep -rl "\[Workflow\]\|\[TestCase\]" --include="*.cs" . | while read f; do
  [ ! -f "${f}.json" ] && echo "Missing: ${f}.json"
done
```

**Fix:** Use `uipath-rpa` skill to regenerate metadata, or run `uip rpa get-errors` which will flag missing metadata.

### Broken Entry Points

**Symptom:** `entryPoints` in project.json references files that don't exist or have been renamed.

**Detection:** Read project.json → `entryPoints` → verify each `filePath` exists on disk.

**Fix:** Update `entryPoints` array to match actual workflow files, or remove stale entries.

### Windows-Legacy Compatibility Lock-In

**Symptom:** Project uses Windows-Legacy compatibility (`expressionLanguage: "VisualBasic"` with no/Legacy `targetFramework`).

**Support status:** Legacy is supported **indefinitely** in Studio LTS (2024.10, 2025.10, 2026.10, and all future LTS releases). It is NOT a deployment blocker. It is NOT a mid-term support risk. Deprecation means "no new features in Legacy," not "Legacy will be removed."

**NEVER flag as Critical based on framework alone.** Severity is Warning if blocking desired modern features, Info if Studio LTS is the organizational standard.

**What you lose by staying on Legacy (ranked by developer-impact):**

1. **Healing Agent** — AI-powered selector self-healing at runtime. When selectors drift from app updates, DOM changes, or resolution shifts, Healing Agent recovers automatically. Legacy has no self-healing — every broken selector becomes a ticket + redeploy.
2. **Unified Target Method** (Strict + Fuzzy + Image + Anchor) — modern multi-strategy UI targeting. Legacy uses single-strategy classic selectors that break on minor UI changes.
3. **Object Repository + shared UI Libraries** — centralized, hierarchical, versioned UI descriptors. Legacy has limited OR support.
4. **Coded test cases (C#)** + Test Manager integration — real testing rigor (mocks, assertions, CI-runnable). Legacy testing is Studio Test Activity only.
5. **Autopilot™** — AI-assisted Studio development (generate, fix, explain workflows).
6. **ScreenPlay** — modern scripted UI interaction experience.
7. **AI Agents + Maestro + Agentic Automation** — participate as actors in multi-agent BPMN processes.
8. **Coded workflows (C#)** — type safety, unit testability, IDE refactoring for complex logic.
9. **Modern .NET (JIT)** — compiled performance + modern encryption/TLS. Legacy runs on .NET Framework 4.6.1.
10. **Cross-platform execution** (Linux robots).
11. **Studio STS** (2-month cadence) — locked to annual LTS on Legacy.

**When recommending migration, lead with the 2-3 features most relevant to the project's actual pain points** — heavy UI maintenance → Healing Agent + Unified Target + Object Repository; weak testing → coded tests + Test Manager; AI use cases → Autopilot + Agents.

**Valid reason to stay on Legacy:** SOAP web services (only supported in Legacy).

**Migration paths:**
1. **Studio's built-in Converter** — single project, framework-only (W-L → W)
2. **Activity Migrator Tool** (`UiPath.Upgrade.exe`) — bulk, activity-level. Handles:
   - W-L → Windows framework
   - Classic → Modern UI Automation (needed for Unified Target/Healing Agent)
   - Classic Outlook → Microsoft 365 Mail

For most real-world migrations (projects with Classic UIA), **Activity Migrator is the right tool**.

**Migration blockers** (manual rework required — Activity Migrator cannot convert these):
- All CV activities, all Trigger activities
- Anchor Base, Element Scope, Double Click variants
- Classic OCR engines, Callout, Set Clipping Region
- `Outlook Desktop Mail Messages Trigger` (no M365 folder-monitoring equivalent)
- `Get Outlook Desktop Mail Messages` filter options

**Pre-flight order:**
1. Run `UiPath.Upgrade.exe analyze` first (dry-run) — review SARIF report
2. Migrate libraries BEFORE consumer projects
3. Pilot on one project before `bulk`
4. Prepare ConnectionId config file for M365 mail migration

**Route Legacy-specific deep validation to the `uipath-rpa-legacy` skill.** The standard `uip rpa` tooling targets Windows/Cross-platform projects.

For full severity matrix and post-migration checks, see rpa-review-checklist.md §10 "Windows-Legacy Compatibility".

### Wrong Expression Language

**Symptom:** XAML files contain expressions in a language that doesn't match the project's `expressionLanguage` setting.

**Impact:** Expressions fail to compile. VB.NET expressions in a CSharp project (or vice versa) cause validation errors.

**Detection:** Read project.json `expressionLanguage`, then check XAML files for mismatched expression syntax.

**Fix:** Rewrite expressions in the correct language, or change the project setting (requires rewriting all expressions).

## Performance Issues

### Oversized XAML Files

**Symptom:** XAML workflow files exceeding 500KB, with critical issues above 5MB.

**Impact:** Studio becomes slow to open, edit, and save. Files >7MB can hang Studio entirely.

**Detection:**
```bash
find . -name "*.xaml" -size +500k -exec ls -lh {} \;
```

**Fix:** Break large workflows into smaller sub-workflows using Invoke Workflow File. Extract reusable sequences into separate files.

### Hardcoded Delay Activities

**Symptom:** `Delay` activities with fixed time values instead of element-based waits.

**Impact:** Wastes execution time on fast systems, causes timeout failures on slow systems. Non-deterministic behavior.

**Detection:** Workflow Analyzer rules ST-DBP-026 and ST-PRR-004. Also grep XAML for `Delay` activities.

**Fix:** Replace with `Element Exists`, `Check App State`, `On Element Appear`, or `Retry Scope` with element-based conditions.

### Progressive Slowdown in Long-Running Processes

**Symptom:** Automation starts fast (30 sec/item) and progressively slows to minutes per item after 1+ hours. No crash — just gets slower.

**Impact:** Jobs that should take 1 hour take 8. Timeouts, missed SLAs, wasted robot licenses. The most consistently reported performance issue on the UiPath Forum.

**Root causes:** Excel processes not killed between iterations (dozens of orphaned EXCEL.EXE accumulate), browser DOM growth in web loops, DataTable variables growing with uncleared temp data, Log Message flooding inside tight loops.

**Detection:** For processes looping >50 times: verify `KillAllProcesses.xaml` kills Excel/browser processes; check that browser is closed/reopened every 50-100 iterations for web loops; verify no growing DataTable variables inside loops; check for Log Message inside tight loops.

**Fix:** Add periodic resource cleanup. Kill Excel in Finally blocks. Close/reopen browser every N iterations. Clear temp variables between iterations. Log summaries before/after loops instead of per-iteration.

### Nested Loops Over Large DataTables

**Symptom:** `For Each Row` nested inside another `For Each Row`, processing large datasets.

**Impact:** O(n^2) complexity. A 1000-row table with nested loops executes 1,000,000 iterations.

**Detection:** Search XAML for nested `ForEachRow` or `ForEach` activities.

**Fix:** Use LINQ queries, `Filter Data Table`, `Join Data Table`, or `Dictionary`/`HashSet` lookups instead.

### Excessive Logging in Loops

**Symptom:** `Log Message` activities inside tight loops logging every iteration.

**Impact:** Floods Orchestrator logs, degrades performance, increases storage costs.

**Detection:** Check for Log Message activities inside For Each / While loops.

**Fix:** Log summary before/after the loop. Use counters and log at intervals (every 100 items). Set production log level to Info.

### Unoptimized Selectors

**Symptom:** Selectors using unstable attributes (`idx`, dynamic IDs, session-specific values).

**Impact:** Intermittent failures, flaky automation runs.

**Detection:**
```bash
grep -r 'idx=' --include="*.xaml" .
```

**Fix:** Use stable attributes (`id`, `name`, `automationid`). Use wildcards for dynamic portions. Use Anchor Base for elements near stable anchors. Use Object Repository for centralized selector management.

## Security Issues

### Hardcoded Credentials

**Symptom:** Passwords, API keys, or connection strings embedded directly in workflow files, Config.xlsx, or source code.

**Impact:** Credentials exposed in source control, logs, and package files. Critical security vulnerability.

**Detection:**
```bash
# Check for common credential patterns in all project files
grep -ri "password\s*=" --include="*.xaml" --include="*.cs" --include="*.json" .
grep -ri "apikey\|api_key\|secret\|token" --include="*.xaml" --include="*.cs" --include="*.json" .
```

**Fix:** Use Orchestrator Credential Assets, external credential stores (CyberArk, Azure Key Vault, HashiCorp Vault), or Windows Credential Manager. Retrieve with `Get Credential` activity.

### SecureString Misuse

**Symptom:** `SecureString` values converted to plain `String` via `.ToString()` or `new NetworkCredential("", secureString).Password`.

**Impact:** Defeats the purpose of SecureString protection. Password visible in memory and potentially in logs.

**Detection:** Workflow Analyzer rule ST-SEC-009. Grep for `NetworkCredential` or `SecureStringToString` patterns.

**Fix:** Keep passwords as `SecureString` throughout the workflow. Use `Type Secure Text` for UI entry. Pass as `SecureString` arguments.

### Sensitive Data in Logs

**Symptom:** Log messages containing PII, credentials, or business-sensitive data.

**Impact:** Sensitive data visible in Orchestrator logs, potentially accessible to unauthorized users.

**Detection:** Review all Log Message activities for variable interpolation that includes sensitive fields.

**Fix:** Redact or mask sensitive values before logging. Use Add Log Fields selectively. Review log output in Orchestrator after test runs.

## Maintainability Issues

### God Workflows

**Symptom:** Single workflow file containing 50+ activities with deeply nested logic.

**Impact:** Difficult to understand, debug, test, and modify. High risk of regression when changing anything.

**Detection:** Check XAML file size (>200KB is suspicious). Count activities in each workflow. Check nesting depth (Workflow Analyzer rule ST-MRD-009).

**Fix:** Extract logical sections into sub-workflows. Each workflow should have a single responsibility. Target 15-30 activities per workflow.

### Default Activity Names

**Symptom:** Activities with names like "Sequence", "Assign", "If", "Click", "Type Into".

**Impact:** Impossible to understand workflow logic without reading each activity's properties. Debugging becomes a guessing game.

**Detection:** Workflow Analyzer rule ST-MRD-002.

**Fix:** Rename every activity to describe its purpose: "Click 'Login' Button", "Assign Invoice Total", "Check if Customer Exists".

### Magic Strings and Numbers

**Symptom:** Hardcoded string values and numbers scattered throughout workflows (column indices, status codes, file paths, email addresses).

**Impact:** Changes require finding and updating every occurrence. Easy to miss one, causing bugs.

**Detection:** Workflow Analyzer rule ST-USG-005 (hardcoded activity arguments). Manual review for repeated literal values.

**Fix:** Extract to variables, Config.xlsx settings, or Orchestrator assets. Use named constants for status codes and column names.

### Unused Variables and Dependencies

**Symptom:** Variables declared but never referenced. NuGet packages in dependencies but no activities from them used.

**Impact:** Clutters the project, causes confusion, increases package restore time.

**Detection:** Workflow Analyzer rules ST-USG-009 (unused variables) and ST-USG-010 (unused dependencies).

**Fix:** Remove unused variables and uninstall unused packages.

### Deep Nesting

**Symptom:** If-Else inside If-Else inside If-Else (>3 levels). For Each inside For Each inside For Each.

**Impact:** Extremely difficult to follow logic flow. Error-prone modifications.

**Detection:** Workflow Analyzer rules ST-MRD-007 (nested If) and ST-MRD-009 (deeply nested activities).

**Fix:** Extract nested logic into separate workflows. Use Switch/Flowchart instead of deeply nested If-Else. Use early returns (Flowchart decision nodes) to reduce nesting.

## Error Handling Issues

### Throw Used Instead of Rethrow (Stack Trace Lost)

**Symptom:** Catch block uses `Throw` activity with `New Exception(exception.Message)` instead of `Rethrow`.

**Impact:** Original stack trace destroyed. Exception appears to originate at the Throw activity's location, not the real failure point. Production debugging becomes guesswork. .NET equivalent of `throw ex` vs `throw`.

**Detection:** Grep XAML for `<Throw>` activities inside `<Catch>` blocks creating new exception objects. Should use `Rethrow` activity (no arguments) to preserve stack trace.

**Fix:** Replace `Throw New Exception(...)` with `Rethrow`. If you must wrap the exception, pass the original as `InnerException`: `Throw New Exception("context", exception)`.

**Severity:** Warning

### Global Exception Handler Causing Cascading Retry Storms

**Symptom:** Project has `GlobalHandler.xaml` that sets `result = Retry` without filtering which activities should retry.

**Impact:** Nested activity failures trigger the Global Handler at every parent level. A 3-retry configuration actually produces dozens of retries (6 inner × 3 outer = 18 total). Documented cases of infinite loops.

**Detection:** Read `GlobalHandler.xaml`. If `result` is set to `Retry` unconditionally (no filtering by activity type / exception type), flag.

**Fix:** Conditionalize retry by activity type — exclude Throw, Rethrow, Try-Catch, and Retry Scope. Only retry specific transient-failure-prone activities (HTTP, UI actions).

**Severity:** Warning

### Global Exception Handler + REFramework (Redundant and Conflicting)

**Symptom:** Project has both `Framework/` folder (REFramework) AND `GlobalHandler.xaml`.

**Impact:** REFramework already has comprehensive Try-Catch in every state and uses specific exceptions for state transitions. The Global Handler catches exceptions REFramework needs to propagate, interfering with retry/recovery logic.

**Detection:** Check for both `Framework/` directory and `GlobalHandler.xaml` in the project.

**Fix:** Remove `GlobalHandler.xaml` in REFramework projects. Use REFramework's built-in error handling (`SetTransactionStatus`, `RetryCurrentTransaction`).

**Severity:** Warning

### Empty Catch Blocks

**Symptom:** Try-Catch with empty Catch body — exception is silently swallowed.

**Impact:** Errors go undetected. Process appears to succeed but produces incorrect results.

**Detection:** Workflow Analyzer rule ST-DBP-003.

**Fix:** At minimum, log the exception. Decide whether to re-throw, handle, or escalate.

### No Business vs System Exception Distinction

**Symptom:** All exceptions treated identically — either all retried or all failed.

**Impact:** Business exceptions (data issues) get retried unnecessarily. System exceptions (transient failures) don't get retried.

**Detection:** Check exception handling in REFramework's SetTransactionStatus or equivalent logic.

**Fix:** Throw `BusinessRuleException` for data/validation issues (no retry). Let `System.Exception` propagate for transient failures (auto-retry).

### ContinueOnError Overuse

**Symptom:** `ContinueOnError=True` set on multiple activities as a blanket error suppression.

**Impact:** Errors silently ignored. Process continues with invalid state, producing incorrect results downstream.

**Detection:** Grep XAML for `ContinueOnError="True"` or `ContinueOnError="{x:Null}"`.

**Fix:** Remove ContinueOnError. Use proper Try-Catch blocks. Only use ContinueOnError with explicit annotation explaining why.

### Missing Finally Blocks for Resource Cleanup

**Symptom:** Try-Catch blocks without Finally blocks when using external resources (file handles, database connections, application scopes).

**Impact:** Resource leaks. Files remain locked, database connections remain open, applications accumulate across retries and Init cycles.

**Detection:** Check Try-Catch activities that wrap file I/O, database, or application scope activities — verify Finally section exists and contains cleanup logic.

**Fix:** Add Finally blocks to close/dispose resources. Use `Close Application` or `Kill Process` in Finally for UI scopes. Use `Close Workbook` in Finally for Excel. Critical in REFramework Process.xaml and SetTransactionStatus workflows.

### Generic Exception Catching

**Symptom:** All Catch blocks catch only `System.Exception` instead of specific exception types.

**Impact:** All exceptions treated identically. Cannot distinguish between transient network failures (should retry), data validation errors (should not retry), and application crashes (should recover). Leads to inappropriate retry behavior and missed root causes.

**Detection:** Check Catch blocks for exception type. All catching `System.Exception` without any specific type catches is a code smell.

**Fix:** Catch specific exception types first with targeted handling: `TimeoutException` for transient waits, `SelectorNotFoundException` for UI issues, `BusinessRuleException` for data problems. Add a generic `System.Exception` catch last as a safety net that logs full details and re-throws.

### Missing Retry Logic for External Calls

**Symptom:** HTTP requests, API calls, or database operations with no retry mechanism.

**Impact:** Transient network failures or service unavailability causes permanent failure.

**Detection:** Check for HTTP Request, Invoke Method, and database activities outside Retry Scope.

**Fix:** Wrap transient-failure-prone activities in Retry Scope with appropriate retry count and interval. Use exponential backoff for API rate limiting.

## Queue and Transaction Issues

### No Queue for High-Volume Processing

**Symptom:** Process reads all items from a source and processes them sequentially in a single run, with no queue.

**Impact:** No per-item retry, no audit trail per item, no distributed processing, single point of failure.

**Detection:** Check if process reads a dataset and loops through it without using Orchestrator queues.

**Recommendation:** If volume >50 items/run AND items are independent, recommend Dispatcher-Performer with queues. Flag as **Info** — the current approach may be intentional for low-volume scenarios.

### Hardcoded Queue Names

**Symptom:** Queue name embedded as a string literal in workflows instead of using Config.xlsx or assets.

**Impact:** Queue name change requires modifying and republishing the process. Different environments can't use different queues.

**Detection:** Grep for `Add Queue Item` and `Get Transaction Item` activities with literal queue names.

**Fix:** Store queue name in Config.xlsx or Orchestrator asset. Reference via `Config("QueueName")`.

### Missing Transaction Status Updates

**Symptom:** Queue items processed but `Set Transaction Status` not called on all paths (especially failure paths).

**Impact:** Items remain "In Progress" for ~24 hours before being marked "Abandoned". No proper audit trail.

**Detection:** Check all code paths in ProcessTransaction for Set Transaction Status calls.

**Fix:** Ensure Set Transaction Status is called in both success and failure/catch paths. Use Finally blocks.

### Queue Items Stuck "In Progress" After Bot Crash

**Symptom:** Bot crashes mid-transaction (network failure, VM restart, Robot Service stop). The queue item remains "In Progress" for 24 hours before auto-abandonment.

**Impact:** During the 24-hour window, the item cannot be retried. No built-in auto-reset mechanism. For HITL workflows, this is worse — if the human takes >24 hours, the item is abandoned even though the workflow is legitimately waiting.

**Detection:** Check if the Init state includes orphan cleanup logic — querying for In Progress items older than a threshold and resetting them. Check if long-running/HITL workflows use the long-running workflow template.

**Fix:** Build an orphan cleanup step in Init: `Get Queue Items` filtered by `InProgress` status and age >2 hours, then set them to Failed for retry. For HITL, use the long-running workflow framework template.

## REFramework-Specific Issues

### Double-Retry Configuration

**Symptom:** Both `MaxRetryNumber > 0` in Config.xlsx AND `Max # of Retries > 0` on the Orchestrator Queue.

**Impact:** Retries multiply. With MaxRetryNumber=3 and Queue MaxRetries=3, a single failed item gets up to 9 attempts. Confuses error tracking and wastes processing time.

**Detection:** Read Config.xlsx Constants sheet for MaxRetryNumber. Check Orchestrator Queue configuration for max retries.

**Fix:** Use one mechanism, not both. For queue-based: set MaxRetryNumber=0 and configure retries on the queue. For non-queue: use MaxRetryNumber only.

### Transaction Shape: One-to-Many (Bulk-in-Transaction / Thick Transaction)

**What it is:** The declared contract (queue schema, input args, flow input, agent input schema) says one invocation represents ONE entity, but the execution body iterates over a sub-collection of that entity and performs external effects per sub-item. One declared transaction actually performs many units of external work.

This shape applies to **any project type**:
- **RPA queue:** queue item = company, execution body loops employees
- **Flow:** flow input = one request, body fans out to N downstream calls
- **Agent:** one agent invocation produces N tool calls that should be separate sessions
- **API workflow:** one request triggers N writes

**Shape detection (mechanical — this is classification, not a verdict):**

The shape is one-to-many when BOTH:
1. The execution body iterates (`ForEach` / `While` / `for` / `foreach`) over a field of the declared input that is a collection of business entities, AND
2. The loop body performs at least one external effect (workflow invocation with side effects, HTTP call, queue op, DB write, persistent UI action, file write outside Temp, email send)

Session scope, shared credentials, "one portal" / "one browser" framing, or PDD wording do NOT change the shape. Only the loop body's actual external effects determine it.

**Remediation depends on two independent questions:**

**Question A — Are sub-units independently splittable?**

- **Yes** (invoices, orders, records, files — each sub-unit is a free-standing transaction): the correct architectural fix is dispatcher/performer. Split the queue so each sub-unit is one atomic item.
- **No** (carrier group-plan enrollment, SAP multi-step transaction, bank wire setup — the domain forces one sequential session): queue splitting is infeasible. The fix shifts to hardening partial-failure recovery in place.

Answering "splittable?" requires understanding the domain. When unclear, default to "yes, probably splittable" and recommend investigation.

**Question B — What partial-failure recovery exists today?**

Look semantically, not by filename. Any of these counts as an idempotency guard:

| Pattern | What to look for |
|---|---|
| Read-check-before-write | `Get X` / SELECT / HTTP GET / `File Exists` immediately before each write for the same entity |
| Conditional skip | `If` / `Switch` skipping the write based on "already exists / processed" |
| Queue dedup | `Add Queue Item` with `UniqueReference` populated |
| SQL idempotency | `MERGE`, `INSERT ... ON CONFLICT`, `UPSERT`, `INSERT ... WHERE NOT EXISTS` |
| HTTP idempotency | `Idempotency-Key` header, `If-Match` / `If-None-Match` ETag |
| Status filter on reads | `WHERE Status != 'Processed'` |
| Pre-check workflow invocation | Workflow invoked before writes whose display name or purpose contains (case-insensitive) `check`, `verify`, `exists`, `processed`, `already`, `idempoten`, `skip` — one common form, not the only form |
| Per-sub-item progress writes | Writing to queue `Output` / Data Service / external state after each sub-unit |

Filenames like `CheckIfEmployeeExists.xaml` are one manifestation. Inline checks, SQL patterns, HTTP headers, queue UniqueReferences, and conditional branches all count.

**Severity and finding framing (combines Questions A and B):**

| A: Splittable? | B: Recovery posture | Severity | Finding framing |
|---|---|---|---|
| Yes | No guards + `MaxRetryNumber` < 2 | **Critical** | "Split into dispatcher/performer. Current architecture risks partial-state corruption on transient failure." |
| Yes | Guards exist + weak progress output | **Warning** | "Consider dispatcher/performer split for better analytics and retry isolation." |
| No | No guards, no progress tracking | **Warning** | "Sub-units cannot be queued independently, but current code has no idempotency or progress tracking — one failure at item N forces replaying items 1..N−1. Add idempotency guards and per-sub-item progress markers." |
| No | Guards + adequate retry but no per-sub-item progress output | **Info** | "Partial-failure recovery could be improved with per-sub-item progress markers written to queue Output for observability." |
| Yes | Guards + retry + per-sub-item output | **Info** | "Working with compensation; consider dispatcher/performer if volume grows." |

**When it cannot be split — hardening checklist:**

If the domain forces a one-to-many shape that cannot be decomposed into separate queue items (e.g., SAP multi-step enrollment, carrier portal group submission, bank wire requiring sequential steps in one session), the reviewer MUST verify ALL of these safeguards. Each missing safeguard is a separate finding.

| # | Safeguard | What to verify | Severity if missing |
|---|---|---|---|
| 1 | **Per-sub-item try-catch** | Every sub-item write inside the loop is wrapped in its own Try-Catch (not one Try-Catch around the entire loop) | Critical — one failure kills the entire batch |
| 2 | **Per-sub-item status tracking** | After each sub-item succeeds or fails, the result is recorded somewhere persistent (queue Output field, Data Service, database, status column in Excel/DataTable) | Warning — no visibility into partial progress |
| 3 | **Resumability after crash** | If the robot crashes mid-loop (power failure, session drop, OOM), the process can resume from the last completed sub-item on retry, not from the beginning | Warning — crash forces full replay |
| 4 | **Idempotency on each sub-item write** | Re-executing a sub-item that already succeeded does not create duplicates (check-before-write, UPSERT, UniqueReference, conditional skip) | Critical — retry creates duplicate records |
| 5 | **Error classification per sub-item** | Each sub-item failure is classified as Business (skip, move to next) or System (retry sub-item or abort loop) — not all treated the same | Warning — business errors trigger unnecessary retries |
| 6 | **Bounded retry per sub-item** | Failed sub-items have a max retry count (not infinite retry inside the loop) | Warning — infinite retry hangs the robot |
| 7 | **Screenshot/evidence on sub-item failure** | When a sub-item fails, screenshot and error details are captured before moving to the next | Info — debugging production failures without evidence |
| 8 | **Summary logging after loop** | After the loop completes, a log entry reports: total sub-items, succeeded count, failed count, skipped count | Warning — Orchestrator shows "1 transaction succeeded" when 47/50 sub-items actually succeeded |
| 9 | **Application state recovery between sub-items** | After a sub-item failure, the application is returned to a known state before processing the next sub-item (e.g., navigate back to list view, close dialog, clear form) | Critical — failed sub-item leaves app in corrupt state, next sub-item fails on stale UI |
| 10 | **Timeout per sub-item** | Each sub-item has a reasonable timeout (not relying only on the global job timeout) | Info — one hanging sub-item blocks all remaining items |

Report each missing safeguard as a numbered finding. Example:
- `[W-005] One-to-many loop in Process.xaml (line 47): no per-sub-item status tracking — partial progress invisible after crash`
- `[C-003] One-to-many loop in Process.xaml (line 47): no idempotency guard on sub-item write — retry creates duplicate records`

**Why this shape is a real problem (when remediation is weak):**

1. Non-atomic — sub-item #15 of 50 fails and the whole invocation is marked failed despite 14 succeeded
2. Retry replays everything — one transient failure re-executes every prior sub-item (wasted time, duplicate risk without guards)
3. Analytics lie — Orchestrator reports "1 processed" when N sub-operations ran
4. Partial-success invisibility — `SetTransactionStatus` captures only the first inner failure
5. Blocking runtime — long single transactions tie up a robot; host crash loses in-progress work

**Common misreadings that do NOT change the shape:**

- "The portal models this as one transaction" — UX framing ≠ atomicity
- "It's all in one `Use Application/Browser`" — session ≠ atomicity
- "They share one credential / connection" — auth reuse ≠ atomicity
- "The PDD calls this one transaction" — declared intent ≠ execution reality
- "Guards exist, so it's fine" — guards are a *remediation* signal (affect severity); they do not re-shape a one-to-many into a one-to-one

The shape is what the execution body does. Remediation posture and business constraints govern severity and the recommended fix — not the shape label.

### System Exception Swallowed by Try-Catch in ProcessTransaction

**Symptom:** System exceptions in ProcessTransaction are caught by a Try-Catch block inside the workflow that does NOT re-throw. The exception never reaches the state machine, so the framework marks the transaction as Success instead of retrying.

**Impact:** The single most common REFramework production failure. Transactions that should retry are silently marked successful. Data goes unprocessed with no error trail.

**Detection:** Read Process.xaml — check every Catch block. If a Catch handles `System.Exception` without a Rethrow, the framework's retry mechanism is bypassed. Only `BusinessRuleException` should be caught and NOT rethrown.

**Fix:** Ensure all Catch blocks in ProcessTransaction either (a) rethrow system exceptions so they propagate to the state machine, or (b) only catch `BusinessRuleException`. The REFramework only retries when the exception reaches the state machine transition level.

### Config.xlsx Environment-Specific Values in Wrong Sheet

**Symptom:** Environment-specific values (URLs, paths, queue names) stored in Config.xlsx Settings or Constants sheets instead of the Assets sheet.

**Impact:** Deploying to a new environment requires manually editing Config.xlsx and republishing. Secrets leak into version control. The most debated configuration issue on the UiPath Forum.

**Detection:** Read Config.xlsx — verify: Constants sheet contains only truly constant values (MaxRetryNumber, timeouts). Settings sheet contains only environment-agnostic settings. All environment-specific values (URLs, paths, credentials, queue names) are in the Assets sheet, referencing Orchestrator Asset names.

**Fix:** Move environment-specific values to the Assets sheet. Create corresponding Orchestrator Assets in each environment folder. Reference via `Config("AssetName")`.

### MaxConsecutiveSystemExceptions Disabled

**Symptom:** `MaxConsecutiveSystemExceptions` set to 0 (disabled) in Config.xlsx Constants sheet.

**Impact:** The bot continues processing even when every single transaction fails with System Exceptions. Can run indefinitely, consuming resources and generating noise.

**Detection:** Read Config.xlsx Constants sheet.

**Fix:** Set to a reasonable value (typically 3-5). This acts as a circuit breaker — if N consecutive transactions fail with System Exceptions, the process stops entirely.

### Empty CloseAllApplications and KillAllProcesses

**Symptom:** These scaffolding files shipped empty and were never implemented.

**Impact:** Applications accumulate across retries and Init cycles. Causes memory leaks, session conflicts, selector mismatches from stale windows.

**Detection:** Read `Framework/CloseAllApplications.xaml` and `Framework/KillAllProcesses.xaml` — check if they contain only the default empty Sequence.

**Fix:** Implement CloseAllApplications with graceful Close Application activities for each app. Implement KillAllProcesses with Kill Process for each app process name.

### All Exceptions Treated as System Exceptions

**Symptom:** No `BusinessRuleException` thrown anywhere. All failures trigger retry logic.

**Impact:** Data validation failures (missing fields, invalid formats, duplicate records) get retried and will never succeed. Wastes queue retry capacity and processing time.

**Detection:** Grep for `BusinessRuleException` in all .xaml and .cs files. If not found, business exception handling is likely missing.

**Fix:** Throw `BusinessRuleException` for data issues: `Throw New BusinessRuleException("Invoice amount is negative")`. These get marked as Failed-Business and are not retried.

### Business Logic in Framework Folder

**Symptom:** Custom code added to files in the `Framework/` folder (InitAllSettings.xaml, framework-level GetTransactionData.xaml, etc.).

**Impact:** Upgrading the REFramework template overwrites customizations. Makes the project non-standard and harder for other developers to understand.

**Detection:** Compare Framework/ files against the original REFramework template on GitHub.

**Fix:** Move customizations to root-level files (Process.xaml, root GetTransactionData.xaml, root SetTransactionStatus.xaml).

## Production Environment Issues

### Unattended Robot Session Failures

**Symptom:** Automation works in development but fails in production with "Desktop disconnected", selector not found, or "Cannot bring target application in foreground" errors.

**Common causes:**
- Different screen resolution or DPI scaling between dev and production machines
- RDP session disconnect due to network issues or Group Policy timeouts
- UAC prompts blocking robot UI interaction
- Windows "Display information about previous logons" policy preventing session creation

**Detection:** Check production robot logs for session-related errors. Compare dev and prod machine resolution/DPI settings.

**Fix:** Develop at the same resolution as production. Disable idle session timeouts via Group Policy. Disable UAC prompt-triggering auto-start programs. Ensure RDP session settings match.

### Excel Process Hanging

**Symptom:** Excel Application Scope completes but Excel process stays alive in background. Robot hangs indefinitely waiting for Excel. Occurs in 10-20% of executions.

**Detection:** Check for orphaned EXCEL.EXE processes after automation runs. Check for timeout errors in Excel activities.

**Fix:** Add Kill Process for EXCEL.EXE in KillAllProcesses.xaml AND in Finally blocks. Use `System.Diagnostics.Process.GetProcessesByName("EXCEL")` in coded workflows to force-kill.

### Selector Breakage After Deployment

**Symptom:** Selectors built on dev machine fail on production machines.

**Common causes:**
- Browser version differences (Chrome upgrades frequently break selectors)
- Screen resolution / DPI scaling differences
- OS version differences (Windows Server vs Windows 10/11)
- Application version differences (SAP GUI versions, web app deployments)

**Detection:** Compare browser versions, OS versions, resolution, and DPI between dev and prod environments.

**Fix:** Validate selectors on production machines. Use stable attributes (automationId, name, role). Avoid idx-based selectors. Use Object Repository for centralized selector management. Consider Healing Agent for self-healing selectors.

### Large Output Data Failures

**Symptom:** Automations processing large volumes fail with message size errors.

**Impact:** Output arguments exceeding the `maxMessageSizeInMegabytes` parameter cause job failures.

**Detection:** Check for large DataTables or JSON objects being passed as output arguments.

**Fix:** Store large outputs in Storage Buckets or Data Service instead of output arguments. Process data in batches.

### Browser Auto-Update Breaking Selectors

**Symptom:** Chrome/Edge auto-update breaks all Active Accessibility (AA) mode selectors overnight. Chrome v114 and v117 broke AA selectors for iFrames and PDFs specifically.

**Impact:** Mass production failure with no code change. All web automations fail simultaneously.

**Detection:** Check if browser auto-update is controlled in production environment. Check for AA-mode selectors on browser targets (most vulnerable). Grep for `aaname` or `role` attributes in selectors — these are AA-dependent.

**Fix:** Pin browser versions in production (disable auto-update). Use UIA mode instead of AA where possible. Consider `--force-renderer-accessibility=complete` browser flag as workaround. Configure Unified Target Method (Strict + Fuzzy + Image + Anchor) for resilience.

## Silent Failure Patterns

Issues where the bot reports success but the outcome is wrong. These are the costliest production issues because they are discovered hours or days later.

### No Output Verification After Data Writes

**Symptom:** Bot writes data (Excel, database, web form, API POST) but does not verify the write succeeded. The target system may accept the command but fail to save.

**Impact:** Bot reports success. The next morning someone discovers blank reports, missing records, or duplicate entries. Occurs ~1% of executions but extremely costly.

**Detection:** After every write operation (`Write Range`, `Submit Form`, HTTP POST, database INSERT), check for a verification step — read-back, count check, or status code validation.

**Fix:** Add verification after critical writes. For Excel: read back and compare row count. For APIs: validate HTTP response status code (not just 2xx — check for specific success codes). For databases: verify affected row count.

### No Record Count Validation After Data Processing

**Symptom:** Bot filters or transforms a DataTable but does not compare input count to output count.

**Impact:** Rows silently dropped during filtering or LINQ operations go undetected. Partial processing reported as complete.

**Detection:** After `Filter Data Table`, LINQ `.Where()`, or any DataTable transformation, check for row count comparison logging (e.g., `Log Message: "Processed {output.Rows.Count} of {input.Rows.Count} rows"`).

**Fix:** Log input and output counts after every data transformation. Flag if output < input without explanation.

## Coded Workflow Pitfalls (C#)

Issues specific to coded workflows that differ from XAML patterns.

### Namespace Clashes with Activity Packages

**Symptom:** Coded workflow class named `Mail`, `Excel`, `Http`, or other common name conflicts with UiPath activity package namespaces.

**Impact:** Cryptic compilation errors that do not point to the real problem. Build fails with unhelpful messages.

**Detection:** Check `.cs` file class names against common UiPath namespace names. Grep for `class (Mail|Excel|Http|Browser|SAP|PDF)[\s{]` patterns.

**Fix:** Use project-specific prefixes for class names. Avoid single-word names that match activity package names.

### Global Using Directives Break Publishing

**Symptom:** C# 10 global using directives with non-primitive types cause compilation errors when publishing coded workflow libraries.

**Impact:** Code compiles locally but fails during NuGet packaging for Orchestrator publishing.

**Detection:** Grep `*.cs` files for `global using` statements that reference complex types (not `System`, `System.Linq`, etc.).

**Fix:** Remove global using directives for non-primitive types. Use regular `using` statements in each file instead.

### Library Invocation NullReferenceException

**Symptom:** Invoking a coded workflow from a library in an external project throws `NullReferenceException` because `CodedWorkflow` service accessors (`system`, `uiAutomation`) are not initialized.

**Impact:** Library works in its own project but fails when consumed by another project.

**Detection:** Check if coded library workflows use service accessors. Test library invocation from an external project.

**Fix:** Ensure library workflows are properly bootstrapped. Use `RunWorkflow` with strongly-typed invocation instead of direct class instantiation.

## Concurrency Issues

### Parallel Activity With Shared UI Resources

**Symptom:** `Parallel` activity with child branches that interact with the same UI application, keyboard, or mouse.

**Impact:** UiPath's Parallel activity executes branches cooperatively on the same thread, but branches share the same desktop session. Clicks land on wrong elements, Type Into targets wrong fields. One branch can monopolize the UI while others block. `Isolated = True` does not fix this.

**Detection:** Grep XAML for `Parallel` activities whose child branches contain UI activities (`Click`, `TypeInto`, `UseApplicationBrowser`) targeting the same application.

**Fix:** Use `Parallel` only for I/O-bound work (HTTP calls, file writes, independent sub-processes). For UI parallelism, use multiple robots with queue work distribution.

**Severity:** Warning

## Deployment Issues

### NuGet Feed Unreachable in Production (Offline Robots)

**Symptom:** Production robot machines cannot reach the NuGet feed (no internet, no Orchestrator feed, custom feed unreachable).

**Impact:** Robot fails at process start with package restore errors. Cannot run any process if even one dependency is missing. Common in air-gapped enterprise environments.

**Detection:** Check `project.json` for custom NuGet feed references. Verify target environment has network access to all feeds, OR that `NUGET_FALLBACK_PACKAGES` environment variable is configured with pre-downloaded packages.

**Fix:** Configure fallback package location with required packages pre-downloaded, or ensure Orchestrator feed is accessible from all robot machines.

**Severity:** Warning

### NuGet NU1107 Assembly Version Conflict

**Symptom:** Project depends on multiple activity packages that transitively depend on conflicting versions of the same assembly (e.g., `Microsoft.CodeAnalysis.Common`). Works in Studio but fails on robot with `NU1107: Version conflict detected`.

**Impact:** Silent in development (Studio's cache masks it), breaks in production. CI/CD pipelines without full package restore don't catch it.

**Detection:** Check for projects with >15 direct dependencies (high risk). Run a clean package restore — NU1107 errors surface immediately.

**Fix:** Explicitly pin the conflicting transitive dependency to a compatible version, or remove one of the packages causing the conflict.

**Severity:** Warning

### Invoke Workflow Argument Drift

**Symptom:** Workflow arguments added, renamed, or removed over time, but existing `Invoke Workflow File` call sites still reference stale argument names. Caller sends outdated arguments; callee receives nulls for new required arguments.

**Impact:** No XAML compile-time error. Surfaces only at runtime with NullReferenceException or missing-argument errors. In mature projects with many maintainers, drift accumulates silently.

**Detection:** For each workflow, extract argument list. For each `InvokeWorkflowFile` call of that workflow, extract the argument bindings. Flag any arg name in the definition that's missing from the call site, or vice versa.

**Fix:** Re-import each invocation in Studio (right-click → Import Arguments). Better: organizational discipline to re-import after every argument change.

**Severity:** Warning

### Get Asset Used for Credential Type (Wrong Activity)

**Symptom:** `Get Asset` activity used to retrieve a Credential-type Orchestrator asset (instead of `Get Credential`).

**Impact:** `Get Asset` cannot retrieve credential-type assets — it returns only username as a string, password is null. Automation appears to work but login fails silently downstream.

**Detection:** In Config.xlsx Assets sheet, identify credential assets (by name convention or known usage). Grep XAML for `GetAsset` activities retrieving those names — should be `GetCredential`.

**Fix:** Replace `Get Asset` with `Get Credential` for credential-type assets. In REFramework, put credential asset names in the Settings sheet (retrieved via `Get Credential`), not the Assets sheet (retrieved via `Get Asset`).

**Severity:** Warning

### Per-Robot Asset Values Missing for Production Robots

**Symptom:** Orchestrator asset configured as per-robot/per-user but values not set for all robots that execute the process.

**Impact:** Robots without a per-robot value either fall back to the global default (if defined) or get Nothing — surfacing as "asset does not have a value associated with this robot" errors. Works in dev (developer's robot has value), fails in production.

**Detection:** For each per-robot asset, verify values are set for all production robots/machines assigned to the deployment folder.

**Fix:** Assign values for all production robots, or reconsider whether per-robot scoping is necessary (global with a single value is simpler when all robots need the same value).

**Severity:** Warning
