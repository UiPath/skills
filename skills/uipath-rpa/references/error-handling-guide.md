# Error Handling Guide

Production-grade error handling and resilience for modern UiPath projects (Windows / Cross-platform), XAML and coded. Covers exception taxonomy, Try/Catch, Retry Scope, ContinueOnError, Throw/Rethrow, screenshots, validation, Global Exception Handler (GEH), state recovery, transaction boundaries, idempotent/compensating writes, sensitive data, and retry ownership.

This guide owns the **decision layer and resilience patterns**. For mechanics:

- Raw `TryCatch` / `Throw` / `Rethrow` XAML shapes + Rule 24 `Sequence` wrap → [common-activity-card.md](common-activity-card.md).
- `ContinueOnError`-swallow gotcha, Studio Web `Throw.Exception` round-trip, `s:Exception` alias → [xaml/common-pitfalls.md](xaml/common-pitfalls.md).
- Per-activity properties → `activity-docs/UiPath.System.Activities/<ver>/activities/{RetryScope,TryCatch,Throw,Rethrow}.md`.
- REFramework flow, queue retry, `MaxConsecutiveSystemExceptions` → [reframework-guide.md](reframework-guide.md).
- C# expression-binding mechanics → [xaml/csharp-activity-binding-guide.md](xaml/csharp-activity-binding-guide.md).
- Long-running / persistence interplay → [xaml/long-running-workflow-guide.md](xaml/long-running-workflow-guide.md).

Legacy (.NET 4.6.1): use [legacy/error-handling-guide.md](legacy/error-handling-guide.md). VB is primary; inline C# forms apply directly to `.cs` workflows; see [§ Coded](#coded-c).

## 1. Exception Taxonomy

Two families. Classify correctly — misclassification either wastes retries on bad data or skips recoverable failures.

| | Business exception | System / Application exception |
|---|---|---|
| **Type** | `UiPath.Core.BusinessRuleException` | `System.Exception` (and any other subclass) |
| **Cause** | Invalid / missing INPUT DATA (bad format, missing field, rule violated) | Transient TECHNICAL failure (app crash, timeout, selector not found, network, file lock) |
| **Retry fixes it?** | **No** — data won't change on retry; needs a human | **Maybe** — transient, may clear on retry |
| **Action** | Log, skip item, mark failed | Retry (limited), reset app state, then escalate |
| **Orchestrator queue Auto-Retry** | Not retried | Retried (when enabled) |

1. `BusinessRuleException` and `System.ApplicationException` are siblings directly derived from `System.Exception`; neither derives from the other. `System.Exception` catches everything; `BusinessRuleException` only business exceptions.
2. Classification is never automatic: explicitly `Throw New BusinessRuleException(...)`. Other unhandled errors are system exceptions.
3. Qualify `UiPath.Core.BusinessRuleException` when ambiguous. `UiPath.Core` is imported by default in new projects; use the full name in coded files or after compiler ambiguity.
4. `Check True` / `Check False` throw `CheckpointException`, not `BusinessRuleException`; validate business data with `If` + `Throw New BusinessRuleException(...)`.
5. **Isolated invoke preserves type and properties.** A workflow invoked with **Isolated** checked runs in its own executor, but the caller catches the original type and properties (`BusinessRuleException` remains one; `FileNotFoundException` retains `FileName`). Type-based Catch routing works across it; never route on human-readable `Message`, which can change, localize, and contain variable data.

## 2. Choose the Mechanism

| Need | Use | Constraint |
|---|---|---|
| Handle/classify failure or compensate | **Try/Catch** | Wrap each externally interacting unit whose failure is handled differently, at step, transaction, or process level; not assignments/control flow. |
| Branch on UI presence | **Check App State** | Only when absence changes the next action, typically an optional popup. Not a guard before acting on the same element, page-load wait, or check that only throws for a later activity; use that activity's timeout and not-found failure (UIA package guide, *Unnecessary Check App State*). |
| Retry flaky action with success check | **Retry Scope** | Add a Condition verifying success; keep Action idempotent. |
| Reject bad input before work | **Fail-fast** + `Throw New BusinessRuleException` | Validate all inputs up front (§7). |
| Tolerate expected non-critical failure | **`ContinueOnError=True`** | Narrow use only (§6); never data/critical writes. |
| Centralized final logging/screenshot | **Global Exception Handler** | One per project; not a local Try/Catch replacement (§8). |
| Per-transaction retry and system/business split | **REFramework** | See [reframework-guide.md](reframework-guide.md). |

Default: fail fast on bad data; Try/Catch each differently handled external-interaction unit; Retry Scope for transient UI/network steps; GEH for centralized observability. Do not blanket-wrap pure logic or pre-check an element its activity will act on: its timeout waits and not-found error fails; handle that where behavior differs.

## 3. Try/Catch Discipline

Raw shapes and mandatory `Sequence` wrap: [common-activity-card.md § TryCatch](common-activity-card.md).

1. Catch specific types before general types; `System.Exception` last. Put `BusinessRuleException`, `TimeoutException`, and `SelectorNotFoundException` first; a preceding `System.Exception` makes them unreachable.
2. Never leave Catch empty: this violates `ST-DBP-003`. At minimum `Log Message` the exception in XAML and coded workflows.
3. Catch only failures you act on. Wrap external interactions, not an entire `Process.xaml` catch-all.
4. `Finally` is cleanup only: close/kill apps, dispose connections, delete temp files. No business logic. Use `ContinueOnError=True` for best-effort cleanup so missing resources do not mask the original error.
5. A `TryCatch` `Finally` runs only when the exception is caught inside the same workflow file. An exception leaving the file—rethrow, throw from Catch, or never caught—skips that file's Finally regardless of invoking Catch, Invoke Workflow File `ContinueOnError`, or `Isolated`. Invoke Workflow File runs as a separate workflow instance; its unhandled exception ends that instance without those Finally blocks. A rethrow caught by an outer Try/Catch in the same file does run the inner Finally. If exceptions can escape, put mandatory cleanup/end logging at the end of Try and in every Catch before Rethrow, with a `System.Exception` Catch, or in the caller.
6. Do not design recovery around process termination. Out-of-memory, killed host processes, and UiPath fatal faults can prevent Catch/Finally; treat them as unrecoverable.
7. `exception.Source` is the activity **type**, not DisplayName, when Try/Catch and the failing activity share a workflow. To capture the failing step name, put it in its own workflow and wrap `Invoke Workflow File`.

## 4. Throw & Rethrow

Raw shapes: [common-activity-card.md § Throw / § Rethrow](common-activity-card.md). `Throw.Exception` is a constructor expression, not a string.

```vb
' Throw a business exception (build the message in an Assign first for complex text)
New BusinessRuleException("Invoice " & invoiceId & " amount " & amount.ToString("F2") & " is negative")
```
```csharp
new BusinessRuleException($"Invoice {invoiceId} amount {amount:F2} is negative")
```

1. `Rethrow` preserves original type and stack trace. Use it inside Catch after logging/screenshot to propagate unchanged. It is Catch-only; outside `Catch.Action` it throws `InvalidOperationException`.
2. Never use `Throw New Exception(ex.Message)` to resurface an error: it resets the stack and drops the type (`CA2200`). Use `Rethrow`; use `Throw New <Type>(...)` only to translate types, such as wrapping a system error as business.
3. Put `Rethrow` last in Catch; later activities are unreachable.
4. **Throwing a caught exception object** (`Throw` with `[storedException]`) outside its Catch keeps its type, message, `Source` and `Data`, but restarts its stack trace; no analyzer rule flags it. It is the only way to raise the original exception once the handler has left the Catch, as a Flowchart's handler on the canvas does ([xaml/canvas-layout-guide.md § Exception Handling Across Nodes](xaml/canvas-layout-guide.md#exception-handling-across-nodes)). Set `Source` (or a `Data` entry) to the failing step first when a later handler reads it (§ 3 rule 7). Inside a Catch, `Rethrow` stays the rule.

## 5. Retry Scope

Properties (`NumberOfRetries`, `RetryInterval`, `ContinueOnError`, `LogRetriedExceptions`): [activity-docs/UiPath.System.Activities/26.4/activities/RetryScope.md](activity-docs/UiPath.System.Activities/26.4/activities/RetryScope.md). It has an Action (`ActivityBody`) and optional Condition (`ActivityFunc(Of Boolean)`); retry occurs when Action throws or Condition returns `False`. Verified XAML shape (the property-element names aren't in the activity doc):

```xml
<ui:RetryScope NumberOfRetries="3" RetryInterval="00:00:05" DisplayName="Retry Scope">
  <ui:RetryScope.ActivityBody>
    <ActivityAction>
      <Sequence><!-- activities to attempt (keep idempotent) --></Sequence>
    </ActivityAction>
  </ui:RetryScope.ActivityBody>
  <ui:RetryScope.Condition>
    <ActivityFunc x:TypeArguments="x:Boolean">
      <!-- a Boolean-returning check (Element Exists, or Check True on a stored State).
           Omit this whole block for exception-only retry. -->
    </ActivityFunc>
  </ui:RetryScope.Condition>
</ui:RetryScope>
```

`xmlns:ui="http://schemas.uipath.com/workflow/activities"` also supplies `ui:LogMessage` and `ui:BusinessRuleException`; a verified specific Catch is `<Catch x:TypeArguments="ui:BusinessRuleException">`. Equivalent CLR form: `xmlns:uic="clr-namespace:UiPath.Core;assembly=UiPath.System.Activities"` + `uic:BusinessRuleException`; either resolves.

**Total executions equal `NumberOfRetries`, not 1 + retries:** `0` = 0 (Action never runs; use `1` for one guaranteed run), `1` = 1, `3` (default) = 3 (one initial + two retries). `=3` runs exactly three times then throws the last error; `=0` is a no-op.

1. `RetryInterval` is a `TimeSpan`, not seconds. `3` means **3 days**; use `00:00:05` for five seconds (default `00:00:05`).
2. Condition semantics are inverse of a while loop: `True` exits; `False` retries. Without Condition, retry is exception-driven and succeeds on the first error-free run.
3. Action reruns fully, so keep it idempotent. `Add Queue Item`, `Append Range`, `Write Range`, `Insert Rows`, and payment/order POSTs can duplicate. Retry Scope has no deduplication; use an existence check or idempotency key.
4. Nest Retry Scope **inside Try/Catch**; after exhaustion it rethrows the last error to the outer Catch.
5. Modern UI Automation `Click` / `Type Into` have built-in **Verify execution** retry; prefer it for one UI step and Retry Scope for multi-step blocks. In modern design, `Check App State` cannot be directly in Condition; store its `State` to a Boolean and reference it.
6. In Orchestration Processes, Retry Scope and `Delay` are unsupported in `Main`; wrap them in `No Persist Scope`.
7. Attempts are nearly invisible by default: `LogRetriedExceptions=False`, and enabled `RetriedExceptionsLogLevel` defaults to `Trace`, below usual Orchestrator logging. Enable it and choose the level intentionally, or log attempt count yourself.

## 6. ContinueOnError

`ContinueOnError=True` suppresses a fault and continues where honored; the activity does not throw, so an enclosing Catch does not fire and failure is silent. It is not universal: some activities/exceptions ignore it; `NetHttpRequest` timeout is one example. Default is `False`; Workflow Analyzer `UI-ANA-017` flags every `True`. See [xaml/common-pitfalls.md](xaml/common-pitfalls.md).

1. When Try/Catch is not catching, first inspect the activity or scope for `ContinueOnError=True`.
2. On `Use Application/Browser`, `Attach`, `Retry Scope`, `On Element Appear`, and `Trigger Scope`, `True` cascades to all nested children, including intentional business throws. Set it on a specific child, never the scope, unless silencing the whole block is intended.
3. HTTP behavior:
   - **Modern HTTP Request (`NetHttpRequest`)**: default `ContinueOnError=True`. Network failure (`HttpRequestException`, including DNS/SSL/refused) becomes synthetic **`503`** in `TextContent` and does not throw; check `StatusCode`. Timeout (`TaskCanceledException`) still throws. For critical calls set `ContinueOnError=False`; network errors then propagate as `HttpRequestException`, and handle timeouts explicitly. ([NetHttpRequest.md § ContinueOnError Behavior](activity-docs/UiPath.Web.Activities/2.5/activities/NetHttpRequest.md))
   - **Classic `HttpClient`**: with `True`, errors are swallowed, response is unpopulated, and `StatusCode` remains `0`; parsing the empty body can crash. Set `False`, or check `StatusCode` before using the body. ([HttpClient.md](activity-docs/UiPath.Web.Activities/2.5/activities/HttpClient.md))

Allowed uses: `Element Exists` / `Check App State` (Boolean, no throw), best-effort cleanup in Finally, and a data-scrape next-page selector that disappears on the last page when paired with an existence check. Never use it on HTTP / DB write / file write / any output used downstream — silent failure → corrupt/empty data. Never use it on `Invoke Workflow File` when callee work or outputs matter: the caller continues as if complete with values set before failure, and callee Finally blocks did not run (§3 rule 5; see [xaml/common-pitfalls.md § Out and InOut Arguments When the Callee Faults](xaml/common-pitfalls.md#out-and-inout-arguments-when-the-callee-faults)).

## 7. Fail-Fast Input Validation

Validate **all** required inputs in one `Sequence` at the start, before business logic. Catch every problem up front, not one run at a time. Don't validate inside loops — validate once before the loop. Immediately throw `BusinessRuleException` with the offending value; fail fast, fail loud, and do not let invalid data reach business logic.

```vb
If String.IsNullOrWhiteSpace(in_InvoiceNumber) Then Throw New BusinessRuleException("Invoice number is empty")
If in_Amount <= 0 Then Throw New BusinessRuleException("Amount must be positive: " & in_Amount.ToString())
```

## 8. Global Exception Handler (GEH)

The runtime invokes one project-wide handler when an activity faults. Use it for centralized logging/screenshots and a global retry/abort verdict, not instead of local Try/Catch.

### Scaffold

Create a dedicated workflow with exactly two non-removable, case-sensitive arguments: `errorInfo` (In, `ExceptionHandlerArgs`) and `result` (Out, `ErrorAction`). Both types are in `UiPath.Activities.Contracts`; XAML alias: `xmlns:uico="http://schemas.uipath.com/workflow/activities/contracts"`.

Verified scaffold:

```xml
<Activity x:Class="GlobalHandlerX"
 xmlns="http://schemas.microsoft.com/netfx/2009/xaml/activities"
 xmlns:ui="http://schemas.uipath.com/workflow/activities"
 xmlns:uico="http://schemas.uipath.com/workflow/activities/contracts"
 xmlns:x="http://schemas.microsoft.com/winfx/2006/xaml">
  <x:Members>
    <x:Property Name="errorInfo" Type="InArgument(uico:ExceptionHandlerArgs)">
      <x:Property.Attributes><RequiredArgumentAttribute /></x:Property.Attributes>
    </x:Property>
    <x:Property Name="result" Type="OutArgument(uico:ErrorAction)">
      <x:Property.Attributes><RequiredArgumentAttribute /></x:Property.Attributes>
    </x:Property>
  </x:Members>
  <!-- Include standard TextExpression.NamespacesForImplementation / ReferencesForImplementation
       (copy from any project .xaml) AND add UiPath.Activities.Contracts to the namespace list so
       the ErrorAction enum resolves in expressions. -->
  <Sequence>
    <!-- log errorInfo.Exception, optionally screenshot, then set the verdict (verified Assign form): -->
    <Assign>
      <Assign.To><OutArgument x:TypeArguments="uico:ErrorAction">[result]</OutArgument></Assign.To>
      <Assign.Value><InArgument x:TypeArguments="uico:ErrorAction">[ErrorAction.Abort]</InArgument></Assign.Value>
    </Assign>
  </Sequence>
</Activity>
```

The expression is imported `ErrorAction.Abort`, not `uico:ErrorAction.Abort`; `uico:` is XML-only and invalid in VB/C# expressions. `ErrorAction` resolves only when `UiPath.Activities.Contracts` is in `NamespacesForImplementation`.

`errorInfo` exposes `Exception`, `ActivityInfo` (`.Name`, `.TypeName`), `RetryCount`, `Variables("name")`, `Arguments("name")`, and `WorkflowArguments("name")`.

### Registration

Register in `project.json` under `runtimeOptions`:

```json
"runtimeOptions": {
  "exceptionHandlerWorkflow": "GlobalHandlerX.xaml"
}
```

1. One per project; it cannot be `Main.xaml` and is unavailable for Library projects, which must use Try/Catch and propagation.
2. Removing it requires deleting the handler `.xaml` and removing `exceptionHandlerWorkflow` from `project.json`; otherwise registration points to a missing workflow.

### Verdicts — `ErrorAction`

| Verdict | Effect |
|---|---|
| `Continue` | **Re-throw**; normal propagation/local Catch handles it. It does not mean skip. |
| `Ignore` | Suppress error and continue from the next activity. |
| `Retry` | Re-execute the failed activity. |
| `Abort` | Stop the job after the handler; the remaining Catch and Finally blocks do not run. |

### Verdict logic — avoid the runaway loop

GEH re-enters at every call-stack level. Unconditional `Retry` can retry an always-failing activity indefinitely. Always gate it:

1. Business data does not self-correct: `[TypeOf errorInfo.Exception Is BusinessRuleException]` → `result = ErrorAction.Abort`.
2. Do not retry scaffolding: `[New HashSet(Of String)({"Throw","Rethrow","TryCatch","RetryScope","Sequence"}).Contains(errorInfo.ActivityInfo.TypeName)]` → `Continue` (re-throw).
3. `[errorInfo.RetryCount < 2]` → `Retry`; otherwise `Abort`.

### Interplay and limits

- GEH runs first-chance: before any local Catch — a Try/Catch around the faulted activity in the same workflow included — then again for every enclosing activity while the exception propagates. A local Try/Catch does not shield it, so a fault the workflow catches as normal flow still reaches the GEH first. Verified under `uip rpa run`; see [UiPath Global Exception Handler docs](https://docs.uipath.com/studio/standalone/latest/user-guide/global-exception-handler).
- Fully unhandled: GEH fires and verdict applies; verified under `uip rpa run`.
- Activities with `ContinueOnError=True` never reach the GEH.
- GEH retries activities, not workflows; retry a whole workflow with your own loop / Retry Scope.
- Do not combine GEH with REFramework: their Try/Catch/retry strategies can fight and loop on business exceptions; choose one.
- During debugging, Studio pauses/highlights the activity and shows exception in Locals/Call Stack; ribbon offers Continue / Retry / Ignore / Abort. Debug **Retry** does not invoke GEH; only Continue does.

To verify GEH, run a workflow with an **unhandled** error—a `Throw` outside local Try/Catch. With registration, `uip rpa run` runs the handler, logs it, and honors verdict; e.g. returning `Ignore` skips the faulting activity and the run completes with `hasErrors:false`.

## 9. Screenshot-on-Error

Capture in Catch or GEH before propagating. Use **Take Screenshot** (`UiPath.UIAutomationNext.Activities.NTakeScreenshot`, package `UiPath.UIAutomation.Activities`).

1. Use an absolute folder path ending `.png`; relative paths resolve to the NuGet cache. Create the directory first.
2. Set capture `ContinueOnError=True` so screenshot failure cannot abort the handler.
3. It requires an interactive session; unattended Robots without a display may fail (`Win32Exception 0x80004005`) or write nothing. Prefer **Orchestrator session recording** (Robot 2023.2+) for reliable unattended post-mortems.
4. Screenshots routinely contain PII, credentials, invoices, and sessions. Use access-controlled storage, job/transaction id + timestamp names, retention/cleanup, and do not attach raw screenshots to broadly distributed logs.

## 10. Logging Exceptions

1. Log `exception.ToString()` (type, message, full stack), not only `.Message`; guard null: `If(exception IsNot Nothing, exception.ToString(), "<missing>")`.
2. Severity: `Error` for caught system exceptions, `Warn` for recoverable business exceptions, `Fatal` for unrecoverable. `Trace`/`Verbose` capture argument values and risk PII; do not log secrets.
3. Log before handling, including before Catch swallows or rethrows.
4. `Log Message` truncates at 10,000 chars; Automation Cloud drops robot logs over 50 KB. Orchestrator robot log level overrides local configuration; default is `Information`.

## 11. Recover to a Known State Before Retrying

Before the next attempt after a system exception:

1. Dismiss blocking popups/modal dialogs.
2. Return app/browser to a known anchor (home/search); reattach, or close/reopen if gone.
3. Clear partial form data and discard half-built records.
4. Re-login after session expiry/timeout.
5. Remove partial artifacts such as temp files and interrupted downloads.
6. Verify the expected screen with `Check App State` / `Element Exists`.

Put reset first in Retry Scope Action or in Catch before manual retry. A retry without state recovery is usually a bug.

## 12. Transaction Boundary (outside REFramework)

Handle one item, not the entire loop, so one bad item cannot abort the batch.

**Queue-backed — Orchestrator owns retry:** get item, process, then `Set Transaction Status`: **Success** on completion; **BusinessException** for bad data (no retry, human review); **ApplicationException** for transient/system failure (queue `Max # of retries`). Do not add a per-item retry loop; carry item `Reference` / id in every log line.

**DataTable/list — own status and bounded retry:**

```
For each row/item:
  Try
    Validate                  ' Throw BusinessRuleException on bad data
    Process                   ' external interactions
    Status column = "Success"
  Catch BusinessRuleException  ' bad data — do NOT retry
    Status = "Failed: business"; log; continue to next item
  Catch Exception              ' transient — bounded retry of the SAME item, then escalate
    Status = "Failed: system"; log
  Finally
    Persist the status column; release per-item resources
```

1. One Try/Catch per item; one bad item must not abort the batch.
2. Business exception: mark failed/skipped and continue. System exception: bounded retry of the same item, then escalate.
3. Persist item status and release resources in Finally; include item id/correlation id in every log line.

## 13. Compensation & Resume-Safe Writes

1. Use an idempotency key on API creates (client-generated id or `Idempotency-Key` header).
2. Without one, check natural key before create. This is not concurrency-safe: two robots can both see nothing and create. Add server unique constraint/upsert, lock/reservation, or reconciliation; never rely on the check alone.
3. Persist external id immediately after creation, before the next step, so resume continues instead of recreating.
4. Never blindly retry non-idempotent writes (payment, append, keyless POST); see §5 rule 3.
5. Define compensation for partial work: delete created draft, void transaction, or mark for manual reconciliation.

## 14. Sensitive Data in Logs & Screenshots

1. Never log credentials, auth headers/tokens, full request/response bodies, bank/card numbers, full customer identifiers, or document images unless explicitly approved; redact or hash first.
2. `exception.ToString()` preserves stack detail, but its message may contain secrets/input values. Sanitize constructed messages; do not echo raw input.
3. Restrict screenshots, use id+timestamp names, retention/cleanup, and access control (§9).
4. `Trace` / `Verbose` capture argument values; keep them out of production and preserve excluded-logged-data settings (`Private:*`, `*password*`).

## 15. Who Owns the Retry — Pick One Layer

Retries multiply: 3 local × 3 queue × 3 job can execute the same work up to 27 times and duplicate side effects. Assign one owner per concern.

| Layer | Owns | Not for |
|---|---|---|
| **Orchestrator queue retry** (`Max # of retries`) | Business-transaction retry with queues | Short UI blips |
| **Retry Scope** | Short transient retry around one flaky action | Whole transaction |
| **Global Exception Handler** | Central logging/screenshot and global verdict | Business-transaction retry (§8) |
| **Orchestrator job/process retry** | Whole-job restart, sparingly | Per-item/action retry |

1. With queues, queue retry owns transaction retry; keep Retry Scope only for sub-second UI flakiness.
2. Do not enable every layer; choose the lowest layer that fully resets state (§11) and disable the others.

## Coded (C#)

Coded workflows use the same types and rules:

```csharp
if (string.IsNullOrWhiteSpace(invoiceNumber))
    throw new BusinessRuleException($"Invoice number is empty");   // using UiPath.Core;
try { /* external interaction */ }
catch (BusinessRuleException) { Log("business error", LogLevel.Warn); throw; }  // bare throw = preserve stack
catch (Exception ex)         { Log(ex.ToString(), LogLevel.Error); throw; }
```

Bare `throw;` preserves stack; `throw ex;` resets it—the same `CA2200` rule as Rethrow versus Throw-new. Workflow Analyzer rules including `ST-DBP-003` apply to `.cs`. For retry, use a plain `for` loop with `try/catch` and delay, or call Retry Scope from XAML. C# XAML binding: [xaml/csharp-activity-binding-guide.md](xaml/csharp-activity-binding-guide.md); coded `using` directives: [coded/operations-guide.md § Using Statements Rules](coded/operations-guide.md#using-statements-rules).

## Anti-patterns

| Symptom | Cause | Fix |
|---|---|---|
| "Try/Catch isn't catching" | `ContinueOnError=True` on the activity/scope swallowed it | Set `False`; check the enclosing scope too (§6) |
| "GEH isn't firing" | a local Try/Catch handled the exception (handled errors don't reach it; nested cases vary by version) | throw outside any local Catch to fire it (§8) |
| "Global handler infinite loop / runaway retries" | unconditional `result = Retry` | Gate `RetryCount`, filter `TypeName`, `Abort` on `BusinessRuleException` (§8) |
| "Retry ran fewer times than expected" / "ran N, not N+1" | `NumberOfRetries` is TOTAL executions, not extra retries; `0` = no-op | Set N = total runs wanted; `1` = one run (§5) |
| "RetryInterval waited days" | `3` parsed as 3 days | Use `00:00:05` (§5) |
| "Duplicate rows / queue items after retry" | non-idempotent Action in Retry Scope | Existence check / idempotency key (§5) |
| "BusinessRuleException caught as system error" | not thrown explicitly, or namespace ambiguity | Explicit `Throw New BusinessRuleException`, qualify `UiPath.Core` (§1) |
| Empty `Catch` | silent failure, `ST-DBP-003` | Log at minimum (§3) |
| `Throw New Exception(ex.Message)` to re-surface | resets stack, drops type | `Rethrow` (§4) |
| Screenshot works attended, nothing unattended | no interactive session | Orchestrator recording + absolute path (§9) |
| Same work runs many times / duplicate side effects | retries stacked at multiple layers (local × queue × job) | one retry owner per concern (§15); idempotency on writes (§13) |
| Retry repeats the failure or corrupts data | action retried without resetting app/data state | recover to a known state first (§11) |
| Secrets/PII in logs or screenshots | logging raw messages/bodies; unprotected screenshot store | redact; restricted storage (§14) |
