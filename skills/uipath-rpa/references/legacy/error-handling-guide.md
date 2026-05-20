# Error Handling Guide

Structured error handling patterns for legacy UiPath RPA workflows. Use this guide when designing exception handling strategy for any workflow.

For TryCatch XAML syntax, see [activity-docs/_BUILT-IN-ACTIVITIES.md](./activity-docs/_BUILT-IN-ACTIVITIES.md).
For REFramework exception flow, see [activity-docs/_REFRAMEWORK.md](./activity-docs/_REFRAMEWORK.md).
For Throw expression escaping, see [common-pitfalls.md](./common-pitfalls.md).

---

## 1. Exception Classification

Every exception in UiPath falls into one of two categories. Classify correctly — the wrong choice causes either wasted retries or skipped valid data.

| | Business Rule Exception | System Exception |
|---|---|---|
| **Class** | `UiPath.Core.BusinessRuleException` | `System.Exception` (or any subclass) |
| **Cause** | Invalid data, violated business rule, missing input | App crash, timeout, selector not found, network error |
| **Will retry fix it?** | **NO** — the data is bad, retrying produces the same result | **MAYBE** — transient issue may resolve on retry |
| **Action** | Skip transaction, log reason, mark Failed | Retry (up to limit), reinitialize apps, then escalate |
| **REFramework** | Caught → Failed status, no retry, next item | Caught → retry counter incremented, reinitialize apps |

### When to Throw BusinessRuleException

Throw `BusinessRuleException` when the input data is invalid and no amount of retrying will fix it:

1. Missing required fields: `If String.IsNullOrEmpty(invoiceNumber) Then Throw New BusinessRuleException("Invoice number is empty")`
2. Data format violations: negative amounts, invalid dates, unrecognized codes
3. Business rule failures: amount exceeds threshold, duplicate record, expired deadline
4. Missing dependencies: referenced record not found in target system

### When to Let System Exceptions Propagate

Do NOT catch these as BusinessRuleException — they are transient and may resolve on retry:

1. `SelectorNotFoundException` — UI element not found (app may not be ready)
2. `TimeoutException` — activity exceeded timeout (network lag, slow app)
3. `System.Net.WebException` — HTTP/network failure
4. `System.IO.IOException` — file locked by another process
5. `COMException` — Excel/Word COM automation failure

---

## 2. TryCatch Best Practices

### Rule: Order Catch Clauses from Specific to General

The first matching catch clause executes. If `System.Exception` is first, it catches everything — more specific clauses below it never execute.

```
Try
  ├── [Business logic activities]
Catch ex As BusinessRuleException          ← 1. Most specific
  ├── Log Message (Warning): "Business error: " + ex.Message
  ├── [Skip item, mark as business exception]
Catch ex As System.TimeoutException        ← 2. Specific system error
  ├── Log Message (Error): "Timeout: " + ex.Message
  ├── [Retry with longer timeout or escalate]
Catch ex As System.Exception               ← 3. Catch-all (ALWAYS last)
  ├── Log Message (Error): "System error: " + ex.Message
  ├── [Retry, reinitialize apps, or escalate]
Finally
  ├── [Cleanup: Kill Process for COM apps, close connections]
```

### Rules

1. **ALWAYS put `System.Exception` last** — it catches everything, so specific clauses must come first
2. **NEVER use empty catch blocks** — at minimum, log the exception. Silent failures are debugging nightmares.
3. **Use Finally for cleanup** — Kill Process for Excel/Word COM objects, close database connections, delete temp files
4. **Don't nest TryCatch more than 2 levels** — extract inner logic to sub-workflows with their own TryCatch

---

## 3. Retry Scope

The Retry Scope activity retries a block of activities when a condition is not met or an exception occurs.

### Configuration

| Property | Description | Recommended Value |
|---|---|---|
| `NumberOfRetries` | Max retry attempts | 2-3 for UI actions, 3-5 for network calls |
| `RetryInterval` | Wait between retries (TimeSpan) | `00:00:03` to `00:00:10` |

### Structure

```
Retry Scope (NumberOfRetries=3, RetryInterval=00:00:05)
  ├── Action: [Activities to retry]
  │   └── Click "Submit" button
  └── Condition: Element Exists "Success message"
```

### Rules

1. **ALWAYS add a Condition activity** — without it, Retry Scope only retries on exception. The Condition checks whether the action actually succeeded (e.g., Element Exists, text appeared, file was created).
2. **Keep actions idempotent** — the action block runs multiple times. Clicking "Submit" twice must not create duplicate records. If the action is not idempotent, check state before acting.
3. **Set reasonable intervals** — too short (< 1 second) wastes CPU; too long (> 30 seconds) wastes time. Match the interval to how long the system typically needs to recover.

### When to Use Which Retry Mechanism

| Mechanism | Use When | Scope |
|---|---|---|
| **Retry Scope** | Single action needs retry with success check (e.g., click button, wait for result) | One activity or small block |
| **REFramework retry** | Entire transaction needs retry after app reinitialization | Full transaction lifecycle |
| **Manual retry loop** | Custom retry logic with backoff, conditional retry, different strategies per attempt | Complex scenarios |

---

## 4. ContinueOnError Decision Matrix

`ContinueOnError` suppresses exceptions from an activity. When `True`, the activity fails silently and the workflow continues.

### Activities That Default to TRUE (Dangerous)

| Activity | Package | Risk |
|---|---|---|
| `HttpClient` (HTTP Request) | Web | HTTP 500/timeout → empty response, no error raised |
| `Data Scraping` output | UIAutomation | Extraction failure → empty DataTable, no error raised |

**ALWAYS set `ContinueOnError=False`** on these activities unless you explicitly handle empty results.

### When ContinueOnError=True Is Acceptable

| Scenario | Why It's OK |
|---|---|
| `Element Exists` / `Image Exists` | Activity returns Boolean — it never throws, ContinueOnError is irrelevant |
| Non-critical Log Message | Logging failure should not stop the automation |
| Optional cleanup in Finally block | Best-effort cleanup (e.g., close dialog that may not exist) |

### When ContinueOnError=True Is NEVER Acceptable

1. **HTTP Request** — you MUST know if the API call failed
2. **Database operations** — silent SQL failures corrupt data
3. **File write operations** — silent write failures mean data loss
4. **Any activity whose output you use downstream** — silent failure → null/empty → downstream crash
5. **Library workflows** — consumers cannot know which errors are swallowed. ALWAYS let exceptions propagate from libraries.

---

## 5. Throw and Rethrow Patterns

### Throw — Create a New Exception

Use `Throw` to signal a business rule violation or intentional failure:

```xml
<!-- Simple message -->
<Throw Exception="[New BusinessRuleException(&quot;Invoice amount is negative&quot;)]" />

<!-- With variable (recommended for complex messages) -->
<!-- Step 1: Assign errorMsg = "Invalid: " & amount.ToString("F2") & " for " & txId -->
<!-- Step 2: Throw with variable -->
<Throw Exception="[New BusinessRuleException(errorMsg)]" />
```

**Rules:**
1. **Use short-form class names** — `BusinessRuleException` not `UiPath.Core.Activities.BusinessRuleException`
2. **Build complex messages in a variable first** — avoids VB.NET compiler issues with `&quot;` in `Throw.Exception`
3. **Include context in the message** — "Invoice INV-12345 amount -500.00 is negative" not "Invalid amount"

See [common-pitfalls.md](./common-pitfalls.md) for the full Throw expression escaping reference.

### Rethrow — Preserve Original Stack Trace

Use `Rethrow` inside a Catch block when you want to log/handle but still propagate the exception:

```
Catch ex As System.Exception
  ├── Log Message: "Error in ProcessInvoice: " + ex.Message
  ├── Take Screenshot
  └── Rethrow   ← preserves original exception type and stack trace
```

**When to Rethrow:**
- You need to log or screenshot before propagating
- You're in a sub-workflow and the caller handles the exception
- You want to add cleanup but still fail the transaction

**When NOT to Rethrow:**
- You've fully handled the exception (e.g., used a fallback value)
- You're wrapping in a different exception type (use Throw instead)

---

## 6. Finally Block Patterns

The Finally block runs regardless of whether an exception occurred. Use it for mandatory cleanup.

### Common Cleanup Patterns

| Scenario | Finally Action |
|---|---|
| Excel COM automation | Kill Process "EXCEL" — prevents zombie EXCEL.EXE processes after crashes |
| Word COM automation | Kill Process "WINWORD" |
| Database connection | Close connection activity or Dispose in InvokeCode |
| Temp files created | Delete File for each temp file |
| Browser opened | Close Tab / Close Browser |
| Application opened | Close Application |

### Rules

1. **Kill Process in Finally for COM apps** — Excel Application Scope and Word Application Scope can leave zombie processes if the workflow crashes mid-execution
2. **Don't put business logic in Finally** — Finally is for cleanup only
3. **Use ContinueOnError=True in Finally cleanup** — if the process is already dead, Kill Process throws; this is acceptable to ignore

---

## 7. Fail-Fast Principle

Validate inputs at the beginning of a workflow. Throw `BusinessRuleException` immediately when data is invalid — don't process halfway then fail.

### Input Validation Pattern

Place this at the START of `Process.xaml` (or any workflow that receives arguments):

```
Sequence "Validate Inputs"
  ├── If String.IsNullOrWhiteSpace(in_InvoiceNumber)
  │   └── Throw New BusinessRuleException("Invoice number is empty")
  ├── If in_Amount <= 0
  │   └── Throw New BusinessRuleException("Amount must be positive: " & in_Amount.ToString())
  ├── If Not DateTime.TryParse(in_DateString, Nothing)
  │   └── Throw New BusinessRuleException("Invalid date format: " & in_DateString)
  └── [Continue with validated data]
```

### Rules

1. **Validate ALL required inputs before processing** — catch all problems upfront, not one at a time
2. **Include the invalid value in the error message** — "Amount -500.00 is negative" not "Invalid amount"
3. **Use BusinessRuleException for validation failures** — the data is bad, retrying won't help
4. **Don't validate inside loops** — validate once before the loop starts

---

## 8. State Machine Exit Conditions

When building State Machine workflows (including REFramework customizations):

1. **Every state machine MUST have a reachable Final State** — a state with no outgoing transitions that ends execution
2. **Every state MUST have at least one outgoing transition** (except the Final State) — orphan states cause infinite hangs
3. **Add a default/fallback transition** from every decision state — handles unexpected conditions
4. **Limit transitions per state to 3-4** — more indicates the state is doing too much; split it
5. **Set max-retry counters** — any retry loop must have a counter that eventually routes to the Final State
6. **Test the "all failures" path** — verify that if every transaction fails, the robot reaches End Process (not infinite loop)

### REFramework-Specific

The REFramework already handles exit conditions via `MaxRetryNumber` and `MaxConsecutiveSystemExceptions`. When customizing:

- **Do NOT remove the ConsecutiveSystemExceptions check** — it's the safety net that prevents infinite retries when the environment is broken
- **Do NOT set MaxRetryNumber to 0** — this disables retry entirely; use 1 if you want minimal retry
- **Do NOT add states without transitions to End Process** — every custom state needs a failure path that reaches the Final State
