# Error Handling Guide

Production-grade error handling and resilience for modern UiPath projects (Windows / Cross-platform) — XAML and coded. Covers exception taxonomy, Try/Catch discipline, Retry Scope, ContinueOnError, Throw/Rethrow, screenshot-on-error, fail-fast validation, the Global Exception Handler, state recovery, transaction boundaries, idempotent/compensating writes, sensitive-data handling, and retry ownership across layers.

Scope boundary — this guide owns the **decision layer and resilience patterns**. For mechanics owned elsewhere, link out, don't restate:

- Raw `TryCatch` / `Throw` / `Rethrow` XAML shapes + the Rule 24 `Sequence`-wrap → [common-activity-card.md](common-activity-card.md).
- `ContinueOnError`-swallow gotcha, Studio Web `Throw.Exception` round-trip, `s:Exception` alias → [xaml/common-pitfalls.md](xaml/common-pitfalls.md).
- Per-activity property surfaces → `activity-docs/UiPath.System.Activities/<ver>/activities/{RetryScope,TryCatch,Throw,Rethrow}.md`.
- REFramework exception flow, queue retry, `MaxConsecutiveSystemExceptions` → [reframework-guide.md](reframework-guide.md).
- C# expression-binding mechanics (`CSharpValue`/`CSharpReference`) → [xaml/csharp-activity-binding-guide.md](xaml/csharp-activity-binding-guide.md).
- Long-running / persistence interplay → [xaml/long-running-workflow-guide.md](xaml/long-running-workflow-guide.md).

> Legacy (.NET 4.6.1) projects: use [legacy/error-handling-guide.md](legacy/error-handling-guide.md) instead.

VB primary; C# expression forms given inline. Coded (`.cs`) uses the C# forms directly — see [§ Coded](#coded-c).

---

## 1. Exception Taxonomy

Two families. Classify correctly — misclassification either wastes retries on bad data or skips recoverable failures.

| | Business exception | System / Application exception |
|---|---|---|
| **Type** | `UiPath.Core.BusinessRuleException` | `System.Exception` (and any other subclass) |
| **Cause** | Invalid / missing INPUT DATA (bad format, missing field, rule violated) | Transient TECHNICAL failure (app crash, timeout, selector not found, network, file lock) |
| **Retry fixes it?** | **No** — data won't change on retry; needs a human | **Maybe** — transient, may clear on retry |
| **Action** | Log, skip item, mark failed | Retry (limited), reset app state, then escalate |
| **Orchestrator queue Auto-Retry** | Not retried | Retried (when enabled) |

**Rules:**

1. `BusinessRuleException` and `System.ApplicationException` are **siblings** — both inherit directly from `System.Exception`, neither from the other. A `System.Exception` catch matches everything; a `BusinessRuleException` catch matches only business exceptions.
2. Business classification is **never automatic** — you must `Throw New BusinessRuleException(...)` explicitly. Any unhandled error that isn't an explicit business throw surfaces as a system exception.
3. Qualify as `UiPath.Core.BusinessRuleException` when ambiguous — the name also exists in other namespaces. `UiPath.Core` is imported by default in new projects, so the short name resolves; use the full name in coded files or on a compiler-ambiguity error.
4. `Check True` / `Check False` throw `CheckpointException`, **not** `BusinessRuleException`. For business validation use `If` + `Throw New BusinessRuleException(...)`.
5. **Isolated invoke keeps the type.** A workflow invoked with **Isolated** checked runs in its own executor process, and the caller still catches the exception it throws with its type and properties: a `BusinessRuleException` stays one, a `FileNotFoundException` keeps its `FileName`. Type-based `Catch` routing works across it. Never route on the human-readable `Message` (it changes, localizes, and carries variable data).

---

## 2. Choose the Mechanism

| Need | Use | Notes |
|------|-----|-------|
| Handle / classify a failure, run compensating logic | **Try/Catch** | Wrap each unit of external interaction (UI, file, network, DB) whose failure is handled differently — at the step, transaction or process level, not per activity; not assignments or control flow |
| Branch on whether a UI element is there | **Check App State** | Only when absence changes what happens next — typically a popup that may appear within some time (dismiss it if it shows, carry on if not). Not as a guard before acting on the same element, a page-load wait, or a check that only throws on an element a later activity acts on — that activity's own timeout and "element not found" do that (UIA package guide, *Unnecessary Check App State*) |
| Auto-retry a flaky action with a success check | **Retry Scope** | Add a Condition to verify the action landed; keep the body idempotent |
| Reject bad input before any work | **Fail-fast** + `Throw New BusinessRuleException` | Validate all inputs up front (§7) |
| Tolerate an expected, non-critical failure | **`ContinueOnError=True`** | Narrow set only (§6). Never on data/critical writes |
| Centralized last-line logging / screenshot across the whole process | **Global Exception Handler** | One per project; not a substitute for local Try/Catch (§8) |
| Per-transaction retry + system/business split at scale | **REFramework** | [reframework-guide.md](reframework-guide.md) |

Default posture: **fail-fast on bad data, Try/Catch around each unit of external interaction whose failure you handle differently, Retry Scope for transient UI/network steps, GEH for centralized observability.** Don't blanket-wrap pure logic, and don't pre-check UI elements an activity is about to act on: its timeout is the wait and its "element not found" is the failure — handle that where the behaviour differs (stop, skip the item, recover and retry, report a business message).

---

## 3. Try/Catch Discipline

Raw XAML shape and the mandatory `Sequence` wrap: [common-activity-card.md § TryCatch](common-activity-card.md). Rules that matter for correctness:

1. **Order catches specific → general; `System.Exception` last.** The designer/readers rely on this; a `System.Exception` clause above specific ones makes them unreachable. (Place `BusinessRuleException`, `TimeoutException`, `SelectorNotFoundException` first.)
2. **Never leave a Catch empty** — violates Workflow Analyzer `ST-DBP-003`. At minimum `Log Message` the exception. Applies to XAML and coded alike.
3. **Catch only what you'll act on.** Wrap external interactions; don't wrap a whole `Process.xaml` in a catch-all that hides where the failure was.
4. **`Finally` is cleanup only** — close/kill apps, dispose connections, delete temp files. No business logic. Use `ContinueOnError=True` on best-effort cleanup so a missing resource doesn't mask the original error.
5. **A `TryCatch` `Finally` runs only when the exception is caught inside the same workflow file.** An exception that leaves the file — rethrown, thrown from a Catch, or never caught — skips that file's Finally blocks, whatever the invoke does with it: the invoking workflow's Catch, `ContinueOnError` on the Invoke Workflow File, `Isolated`. Invoke Workflow File runs the file as its own workflow instance, the exception is unhandled there, and the instance ends without running them. A rethrow that an outer Try/Catch in the same file catches still runs the inner Finally. In a workflow that lets exceptions out to its caller, put what must run on every path (cleanup, a phase's end log) at the end of the Try and in each Catch before its Rethrow, with a `System.Exception` Catch so nothing leaves without it — or in the caller.
6. **Don't design business recovery around runtime/process termination.** Out-of-memory, a killed host process, and UiPath fatal faults can tear the job down without your Catch/Finally running — treat them as unrecoverable, not as something to handle.
7. **`exception.Source` returns the activity TYPE, not its DisplayName**, when the Try/Catch and the failing activity are in the same workflow. To capture the failing step's name, move the risky step into its own workflow and wrap the `Invoke Workflow File`.

---

## 4. Throw & Rethrow

Raw XAML shapes: [common-activity-card.md § Throw / § Rethrow](common-activity-card.md). `Throw.Exception` is a **constructor expression**, not a string.

```vb
' Throw a business exception (build the message in an Assign first for complex text)
New BusinessRuleException("Invoice " & invoiceId & " amount " & amount.ToString("F2") & " is negative")
```
```csharp
new BusinessRuleException($"Invoice {invoiceId} amount {amount:F2} is negative")
```

1. **`Rethrow` preserves the original exception type AND stack trace** (verified). Use it inside a `Catch` to log / screenshot, then propagate unchanged. `Rethrow` is Catch-only — outside a `Catch.Action` it throws `InvalidOperationException`.
2. **Never `Throw New Exception(ex.Message)` to re-surface** — it resets the stack trace to the throw site and drops the type (.NET `CA2200` anti-pattern). Use `Rethrow`. Use `Throw New <Type>(...)` only to *translate* to a different exception type (e.g. wrap a system error as a business one).
3. Place `Rethrow` last in the `Catch` body — anything after is unreachable.

---

## 5. Retry Scope

Property surface (`NumberOfRetries`, `RetryInterval`, `ContinueOnError`, `LogRetriedExceptions`): [activity-docs/UiPath.System.Activities/26.4/activities/RetryScope.md](activity-docs/UiPath.System.Activities/26.4/activities/RetryScope.md). Two bodies: **Action** (`ActivityBody` — activities to attempt) and an optional **Condition** (`ActivityFunc(Of Boolean)` — a check that the action landed). A retry fires when the Action throws **or** the Condition returns `False`. Verified XAML shape (the property-element names aren't in the activity doc):

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

`xmlns:ui="http://schemas.uipath.com/workflow/activities"` — the same schema provides `ui:LogMessage` and the `ui:BusinessRuleException` type used in a `Catch`: `<Catch x:TypeArguments="ui:BusinessRuleException">` (verified — the specific catch loads and matches `BusinessRuleException` ahead of `s:Exception`, in both VB and C# expression XAML). The CLR-namespace form `xmlns:uic="clr-namespace:UiPath.Core;assembly=UiPath.System.Activities"` + `uic:BusinessRuleException` is equivalent and is what some bundled samples use — either resolves.

**Verified count semantics — total executions equals `NumberOfRetries` (NOT 1 + retries):**

| `NumberOfRetries` | Action executions |
|---|---|
| `0` | **0 — the Action never runs (no-op).** Use `1` for a single guaranteed run. |
| `1` | 1 (0 retries) |
| `3` (default) | 3 (1 initial + 2 retries) |

> Verified by run: `=3` runs the Action exactly 3 times then throws the last error; `=0` runs it zero times.

1. **`RetryInterval` is a `TimeSpan`, not a number of seconds.** The literal `3` is parsed as a TimeSpan = **3 days**. Write `00:00:05` for 5 seconds (default `00:00:05`).
2. **Condition logic is inverted vs a while-loop:** Condition `True` **exits**; `False` triggers another attempt. With no Condition the scope is exception-driven only (retries on throw, succeeds on the first error-free run).
3. **Keep the Action idempotent** — it re-runs in full on every attempt. `Add Queue Item`, `Append Range`, `Write Range`, `Insert Rows`, and payment/order POSTs **duplicate** on retry. Retry Scope has no built-in dedup; guard mutations with an existence check or idempotency key.
4. **Nest Retry Scope INSIDE Try/Catch** (retry innermost). After exhausting attempts it rethrows the last error to the outer Catch.
5. **Modern UI Automation `Click` / `Type Into` have built-in "Verify execution" retry** — prefer it for single UI steps; reach for Retry Scope for multi-step blocks. In modern design, `Check App State` can't sit directly in the Condition — store its `State` to a Boolean and reference that.
6. **Orchestration Processes:** Retry Scope (and `Delay`) are unsupported in `Main` — wrap in a `No Persist Scope`.
7. **Retry attempts are near-invisible by default** — `LogRetriedExceptions=False`, and when enabled `RetriedExceptionsLogLevel` defaults to `Trace`, below the usual Orchestrator log level, so retry evidence disappears. Enable it and set the level intentionally, or log the attempt count yourself.

---

## 6. ContinueOnError

`ContinueOnError=True` tells an activity to **suppress its fault and continue** — for activities and error types that honor it, the activity doesn't throw, so an enclosing `Catch` never fires and the failure is silent. It is **not a universal shield**: some activities/exceptions ignore it (e.g. a `NetHttpRequest` timeout still throws — rule 3 below). Default `False`. Workflow Analyzer `UI-ANA-017` flags every `True`. Background: [xaml/common-pitfalls.md](xaml/common-pitfalls.md).

1. **First thing to check when "my Try/Catch isn't catching"** — a `ContinueOnError=True` on the activity (or its scope) ate the error.
2. **On a scope activity** (`Use Application/Browser`, `Attach`, `Retry Scope`, `On Element Appear`, `Trigger Scope`) `True` **cascades** — it suppresses errors from every nested child, including intentional business throws. Set it on the specific child, never the scope, unless you mean to silence the whole block.
3. **HTTP failure behavior differs by activity — handle the one you use:**
   - **Modern HTTP Request (`NetHttpRequest`)** — `ContinueOnError=True` by default. A network failure (`HttpRequestException` — DNS / SSL / refused) becomes a synthetic **`503`** response (message in `TextContent`), so it does **not** throw — check `StatusCode`. But a **timeout (`TaskCanceledException`) is NOT caught — it throws even with `ContinueOnError=True`.** For critical calls set `ContinueOnError=False` (network errors then propagate as `HttpRequestException`) and handle timeouts explicitly. ([NetHttpRequest.md § ContinueOnError Behavior](activity-docs/UiPath.Web.Activities/2.5/activities/NetHttpRequest.md))
   - **Classic `HttpClient`** — with `ContinueOnError=True` the error is swallowed and execution continues with an **unpopulated response and `StatusCode` left at `0`**; a downstream parse of the empty body then crashes. Set `ContinueOnError=False`, or check `StatusCode` before using the body. ([HttpClient.md](activity-docs/UiPath.Web.Activities/2.5/activities/HttpClient.md))

| `ContinueOnError=True` | Verdict |
|---|---|
| `Element Exists` / `Check App State` (returns Boolean, never throws) | Fine |
| Best-effort cleanup in `Finally` (close a maybe-open dialog) | Fine |
| Data-scrape "next page" selector that vanishes on the last page | OK, paired with an existence check |
| HTTP / DB write / file write / any output used downstream | **Never** — silent failure → corrupt/empty data |
| `Invoke Workflow File` | **Never** for a callee whose work or outputs matter — the caller continues as if it completed, with the output values the callee set before it failed ([xaml/common-pitfalls.md § Out and InOut Arguments When the Callee Faults](xaml/common-pitfalls.md#out-and-inout-arguments-when-the-callee-faults)), and the callee's Finally blocks did not run (§3 rule 5) |

---

## 7. Fail-Fast Input Validation

Validate **all** required inputs in one `Sequence` at the start, before any business logic. Throw `BusinessRuleException` immediately with the offending value in the message.

```vb
If String.IsNullOrWhiteSpace(in_InvoiceNumber) Then Throw New BusinessRuleException("Invoice number is empty")
If in_Amount <= 0 Then Throw New BusinessRuleException("Amount must be positive: " & in_Amount.ToString())
```

Catch every problem up front, not one run at a time. Don't validate inside loops — validate once before the loop. Guiding principle: **fail fast, fail loud** — surface bad data immediately with context; never let an invalid value flow into business logic and fail obscurely later.

---

## 8. Global Exception Handler (GEH)

A project-wide handler the runtime invokes when an activity faults. **One per project.** Use it for centralized logging / screenshots and a global retry/abort verdict — not as a replacement for local Try/Catch.

### Scaffold

A dedicated workflow with exactly two non-removable, case-sensitive arguments: `errorInfo` (In, `ExceptionHandlerArgs`) and `result` (Out, `ErrorAction`). Both types live in `UiPath.Activities.Contracts` (XAML alias `xmlns:uico="http://schemas.uipath.com/workflow/activities/contracts"`). Verified scaffold:

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

The verdict expression is the imported enum name — `ErrorAction.Abort` — **not** `uico:ErrorAction.Abort` (the `uico:` prefix is XML-only; inside a VB/C# expression it's invalid). `ErrorAction` resolves only if `UiPath.Activities.Contracts` is in `NamespacesForImplementation`.

`errorInfo` exposes: `Exception` (the `System.Exception`), `ActivityInfo` (`.Name`, `.TypeName` of the faulting activity), `RetryCount`, `Variables("name")`, `Arguments("name")`, `WorkflowArguments("name")`.

### Registration

Register the file in `project.json` under `runtimeOptions` (verified — build clean):

```json
"runtimeOptions": {
  "exceptionHandlerWorkflow": "GlobalHandlerX.xaml"
}
```

1. **One per project.** Cannot be `Main.xaml`. **Not available for Library projects** — libraries must rely on Try/Catch and propagation.
2. **Removing a GEH is two edits, both required:** delete the handler `.xaml` AND remove the `exceptionHandlerWorkflow` key from `project.json`. Deleting only the file leaves a stale registration pointing at a missing workflow.

### Verdicts — `ErrorAction`

Set `result` to one of (enum `UiPath.Activities.Contracts.ErrorAction`):

| Verdict | Effect |
|---|---|
| `Continue` | **Re-throw** the exception (let normal propagation / local Catch handle it). *Not* "skip" — a common community misreading. |
| `Ignore` | Suppress the error, continue from the **next** activity. |
| `Retry` | Re-execute the **failed activity**. |
| `Abort` | Stop the job after the handler finishes. |

### Verdict logic — avoid the runaway loop

The GEH re-enters at **every** call-stack level a fault propagates through, so an unconditional `result = ErrorAction.Retry` compounds — an always-failing activity is retried far more than intended and can loop without end. Always gate the verdict. XAML `If.Condition` expression forms (VB):

1. **Classify first** — business data won't fix itself, so abort: `[TypeOf errorInfo.Exception Is BusinessRuleException]` → set `result = ErrorAction.Abort`.
2. **Filter the faulting activity type** — don't "retry" scaffolding: `[New HashSet(Of String)({"Throw","Rethrow","TryCatch","RetryScope","Sequence"}).Contains(errorInfo.ActivityInfo.TypeName)]` → `Continue` (re-throw), don't retry.
3. **Gate retries on `RetryCount`** — `[errorInfo.RetryCount < 2]` → `Retry`, else `Abort`.

### Interplay and limits

- **When the GEH fires — three cases:**
  1. **Caught and handled** — the faulting activity's own Try/Catch catches it (no rethrow): GEH does **not** fire.
  2. **Fully unhandled** — nothing up the call stack catches it: GEH fires, then its verdict applies. Verified under `uip rpa run`.
  3. **Nested / call-stack** — version-sensitive: some Studio versions invoke the GEH *first-chance*, before a local `Catch`, for an activity nested in a `Sequence` inside `Try` (reported in 25.0.157). Don't assume a local Try/Catch always shields the GEH in deeply-nested code. See [UiPath Global Exception Handler docs](https://docs.uipath.com/studio/latest/user-guide/global-exception-handler).
- **Retries activities, not workflows.** To retry a whole workflow, wrap it in your own loop / Retry Scope.
- **Don't combine with REFramework** — REFramework's per-state Try/Catch and the GEH fight; business exceptions get caught/retried and can loop. Pick one strategy.
- **Debugging:** on a fault Studio pauses, highlights the activity, shows the exception in **Locals** / **Call Stack**; the ribbon offers Continue / Retry / Ignore / Abort. The debug **Retry** button does **not** invoke the GEH; only Continue does.

**Verifying the GEH:** to fire it, run a workflow that throws an **unhandled** error — a `Throw` not wrapped in a local Try/Catch. Verified by run: with the handler registered, `uip rpa run` executes the handler (its logs appear) and honors the verdict — e.g. returning `Ignore` skips the faulting activity and the run completes with `hasErrors:false`. An agent that needs to exercise GEH logic just triggers an unhandled error.

---

## 9. Screenshot-on-Error

For unattended post-mortem, capture a screenshot in the Catch (or GEH) before propagating. Modern activity: **Take Screenshot** (`UiPath.UIAutomationNext.Activities.NTakeScreenshot`, package `UiPath.UIAutomation.Activities`).

1. **Use an absolute path** including folder + `.png` — relative paths resolve into the NuGet cache. Create the directory first.
2. **Set `ContinueOnError=True` on the capture** so a failed screenshot doesn't abort the handler.
3. **Take Screenshot needs an interactive session** — under unattended Robots with no display it fails (`Win32Exception 0x80004005`) or silently writes nothing. For reliable unattended post-mortem prefer **Orchestrator session recording** (Robot 2023.2+) over the activity.
4. **Treat screenshots as sensitive data** — they routinely capture PII, credentials, invoices, and open sessions. Write to an access-controlled folder / storage bucket (not a world-readable temp), name files by job/transaction id + timestamp, set a retention + cleanup policy, and don't attach raw screenshots to logs that ship to a broad audience.

---

## 10. Logging Exceptions

1. **Log `exception.ToString()`** (type + message + full stack), not just `.Message` — `.Message` alone loses the root cause. Guard null: `If(exception IsNot Nothing, exception.ToString(), "<missing>")`.
2. **Level:** `Error` for caught system exceptions; `Warn` for recoverable business exceptions; `Fatal` for unrecoverable. Only `Trace`/`Verbose` capture argument values (PII risk) — don't log secrets.
3. **Log before you handle** — emit the exception detail before the Catch swallows or rethrows it.
4. **Limits:** `Log Message` truncates at 10,000 chars; Automation Cloud drops robot logs > 50 KB. The Orchestrator robot log level overrides local config (default `Information`).

---

## 11. Recover to a Known State Before Retrying

Retrying a UI or system action without resetting state usually repeats the failure or corrupts data. After a system exception, **before the next attempt**:

1. Dismiss blocking popups / modal dialogs.
2. Return the app or browser to a known anchor (home / search page); reattach, or close and reopen if the window is gone.
3. Clear partially-entered form data; discard half-built records.
4. Re-login if the session expired or timed out.
5. Clean up partial artifacts (temp files, interrupted downloads).
6. **Verify the expected screen is present** (`Check App State` / `Element Exists`) before re-running the action.

Wire this reset into the Retry Scope Action (run it first, ahead of the real step) or into the Catch before a manual retry. Rule: **a retry that skips state recovery is usually a bug.**

## 12. Transaction Boundary (outside REFramework)

Scope error handling to **one item**, not the whole loop, so a single bad item can't abort the batch. Two recipes by source:

**Queue-backed — let Orchestrator own retry.** Get a queue item, process, then set its status with `Set Transaction Status`:
- **Success** on completion.
- **BusinessException** on bad data → Orchestrator does **not** retry; flagged for human review.
- **ApplicationException** on a transient/system failure → Orchestrator retries per the queue's `Max # of retries`.

Don't wrap your own per-item retry loop on top — the queue owns transaction retry (§15). Carry the item `Reference` / id in every log line.

**DataTable / list — own a status column + bounded in-workflow retry.** No queue, so you own status and retry:

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

1. **One Try/Catch per item** — a single bad item must not abort the batch.
2. `BusinessRuleException` → mark failed/skipped, continue. System exception → bounded retry of the **same** item, then escalate.
3. Persist per-item status and release resources in `Finally`; include an **item id / correlation id** in every log line.

## 13. Compensation & Resume-Safe Writes

A failure partway through external writes leaves partial side effects. Make writes safe to re-run:

1. **Idempotency key** on API creates (client-generated id or `Idempotency-Key` header) so a retried create doesn't duplicate.
2. **Check-before-create** when no key is available — query by natural key first. **Not concurrency-safe on its own:** two robots can both check, see nothing, and both create. Back it with a server-side unique constraint / upsert, a lock or reservation record, or a downstream reconciliation pass — don't rely on the check alone.
3. **Record the external id immediately** after creation (persist before the next step) so a resumed run continues from it instead of re-creating.
4. **Never blindly retry a non-idempotent write** (payment, append, keyless POST) — see §5 rule 3.
5. **Define compensation** for partial work: delete the created draft, void the transaction, or mark the record for manual reconciliation.

## 14. Sensitive Data in Logs & Screenshots

Error paths are where secrets leak — exceptions and screenshots capture live data.

1. **Never log** credentials, auth headers/tokens, full request/response bodies, bank/card numbers, full customer identifiers, or document images unless explicitly approved. Redact or hash first.
2. `exception.ToString()` is right for the stack trace (§10), but the **message may still contain secrets or input values** — sanitize messages you build; don't echo raw input.
3. Treat screenshots as sensitive data — restricted storage, id+timestamp naming, retention/cleanup, access control (§9).
4. `Trace` / `Verbose` capture argument values (PII) — keep them out of production, and don't defeat the project's excluded-logged-data settings (`Private:*`, `*password*`).

## 15. Who Owns the Retry — Pick One Layer

Retries **stack multiplicatively**: 3 local × 3 queue × 3 job = up to 27 executions of the same work, with duplicate side effects. Assign one owner per concern.

| Layer | Owns | Don't use it for |
|---|---|---|
| **Orchestrator queue retry** (`Max # of retries`) | Business-transaction retry, when queues are used | short transient UI blips |
| **Retry Scope** | Short transient retry around **one** flaky action | whole-transaction retry |
| **Global Exception Handler** | Centralized logging/screenshot + a global verdict | business-transaction retry (§8) |
| **Orchestrator job/process retry** | Whole-job restart (use sparingly) | per-item or per-action retry |

1. Queues present → queue retry owns transaction retry; keep Retry Scope for sub-second UI flakiness only.
2. **Don't enable retry at every layer** — pick the lowest layer that fully resets state (§11) and disable the rest.

---

## Coded (C#)

Coded workflows use the same types and rules:

```csharp
if (string.IsNullOrWhiteSpace(invoiceNumber))
    throw new BusinessRuleException($"Invoice number is empty");   // using UiPath.Core;
try { /* external interaction */ }
catch (BusinessRuleException) { Log("business error", LogLevel.Warn); throw; }  // bare throw = preserve stack
catch (Exception ex)         { Log(ex.ToString(), LogLevel.Error); throw; }
```

- `throw;` (bare) preserves the stack trace; `throw ex;` resets it — same `CA2200` rule as Rethrow vs Throw-new.
- Workflow Analyzer rules (`ST-DBP-003`, etc.) apply to `.cs` workflows too.
- Retry: a plain `for` loop with `try/catch` and a delay, or call a Retry Scope from XAML. C# expression-binding mechanics for XAML activities: [xaml/csharp-activity-binding-guide.md](xaml/csharp-activity-binding-guide.md); coded `using` directives: [coded/operations-guide.md § Using Statements Rules](coded/operations-guide.md#using-statements-rules).

---

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
