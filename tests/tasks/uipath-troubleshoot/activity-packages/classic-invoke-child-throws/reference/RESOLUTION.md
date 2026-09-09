# Final Resolution

Investigation complete. Here is the resolution:

---

**Root Cause:** The **invoked child workflow threw** — the `Invoke Workflow File` in `Main.xaml` is only
the propagation point, not the fault. Inside `ProcessPayments.xaml`, the `Sum line items` **Assign**
dereferences the `lineItems` variable (`List<Double>`) while it is **null** — the variable is declared
with no default and nothing populates it before the Assign — so `lineItems.Sum()` raises
`System.NullReferenceException`, which unwinds up through the invoke and faults the job.

**What went wrong:** Job `7a3f1e08-2b9c-4d51-8e6a-1f0c4b2d9e33` (process **PaymentRun**, folder
**Shared**, machine **MOCK-HOST**) faulted with `System.NullReferenceException`. The job Info/Error
stack localizes the fault to `ProcessPayments.xaml` at the `Sum line items` Assign, reached through
`InvokeWorkflowFile "Invoke ProcessPayments"` in `Main.xaml`. The error is **inside the child**, so the
fix belongs in `ProcessPayments.xaml`, not in the invoke.

**Why (one hop into the child):**
- The job stack (from `job-get` Info and `job-logs`) reads, top-down:
  `in ProcessPayments.xaml → at Assign "Sum line items" → at Sequence "ProcessPayments" → at
  InvokeWorkflowFile "Invoke ProcessPayments" → at Sequence "Main"`. The innermost frame is the child's
  Assign — that is where the exception originates.
- `process/ProcessPayments.xaml` — declares `<Variable x:TypeArguments="scg:List(x:Double)"
  Name="lineItems" />` with **no `Default`**, so `lineItems` is `null` at run time. The `Sum line items`
  Assign sets `out_GrandTotal = lineItems.Sum()`; calling `.Sum()` on a null list throws
  `NullReferenceException`.
- `process/Main.xaml` — the `Invoke Workflow File` (DisplayName "Invoke ProcessPayments") only maps
  `out_GrandTotal` and relays the child's exception. Nothing about the invoke itself (path, arguments,
  session) is wrong.

**Evidence:**
- Exception: `System.NullReferenceException: Object reference not set to an instance of an object`.
- Stack innermost frame: `ProcessPayments.xaml` / Assign `Sum line items` (below the InvokeWorkflowFile
  frame) — the fault is in the child, propagated through the invoke.
- Source: `lineItems` (`List<Double>`) declared with no initializer in `ProcessPayments.xaml`; used as
  `lineItems.Sum()` in the `Sum line items` Assign.
- Job identity: Key `7a3f1e08-…`, `ReleaseName` PaymentRun, `EntryPointPath` Main.xaml, `State` Faulted,
  `ErrorCode` Robot, folder **Shared** (`b7c93a10-…`), machine **MOCK-HOST**. History: Running
  09:14:22 → Faulted 09:14:23.

**Immediate fix (in the child workflow):**
1. In `ProcessPayments.xaml`, initialize `lineItems` before it is used — give the `List<Double>`
   variable a default (`new List<double>()`) and populate it with the actual line-item values, or fix
   the upstream step that was supposed to build the list.
   - Where: `ProcessPayments.xaml` — `lineItems` variable default / the logic that fills it, ahead of
     the `Sum line items` Assign.
   - Why: `.Sum()` on a null list throws `NullReferenceException`; the list must be a non-null
     collection (empty or populated) before the Assign runs.
2. Do **not** change the `Invoke Workflow File` in `Main.xaml` — it is correct and only relays the
   child's exception.

**Preventive fix:**
- Initialize collection variables at declaration (`new List<double>()`) so a not-yet-populated list is
  empty rather than null; add a guard before aggregation if the list can legitimately be empty/absent.

| # | Hypothesis | Confidence | Status | Root Cause? | Key Evidence | Resolution |
|---|------------|------------|--------|-------------|--------------|------------|
| H1 | The invoked child `ProcessPayments.xaml` throws `NullReferenceException` at the `Sum line items` Assign because `lineItems` (`List<Double>`) is null (declared without a default, never populated); the fault propagates up through the Invoke Workflow File. | high | confirmed | Yes | Stack innermost frame is `ProcessPayments.xaml` Assign `Sum line items` below the InvokeWorkflowFile frame; `lineItems` declared with no initializer and used as `lineItems.Sum()`. | Initialize/populate `lineItems` in the child before the Assign; leave the invoke unchanged. |
| H2 | The Invoke Workflow File itself is misconfigured (bad path, wrong arguments, session settings). | low | eliminated | No | The invoke resolves `ProcessPayments.xaml`, maps only `out_GrandTotal`, and the exception originates below its frame — inside the child, not at the invoke. | N/A — the invoke only relays the child's exception. |
