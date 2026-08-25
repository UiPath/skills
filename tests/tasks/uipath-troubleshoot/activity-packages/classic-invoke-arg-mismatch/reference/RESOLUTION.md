# Final Resolution

Investigation complete. Here is the resolution:

---

**Root Cause:** **Argument-name drift between the invoke and the invoked workflow.** `Main.xaml`'s
`Invoke Workflow File` passes an argument keyed `in_Amount`, but `ValidatePayment.xaml` no longer
declares `in_Amount` — its input was renamed to `in_GrossAmount`. At run time the workflow runtime
rejects the stale key, raising `System.ArgumentException` ("the following keys from the input dictionary
do not map to arguments and must be removed: **in_Amount**").

**What went wrong:** Job `4e9d2a71-6c05-4f38-9b12-8a3f0e7c1d59` (process **PaymentValidation**, folder
**Shared**, machine **MOCK-HOST**) faulted the moment the invoke tried to bind arguments. The invoked
workflow's argument list changed (an input was renamed) while the parent's `Invoke Workflow File` kept
the old argument mapping, so the parent supplies a key the child does not have.

**Why:**
- Job Info/logs: `System.ArgumentException: ... The following keys from the input dictionary do not map
  to arguments and must be removed: in_Amount. ... Parameter name: rootArgumentValues`. The stack
  localizes to `Main.xaml` → `InvokeWorkflowFile "Invoke ValidatePayment"` — the invoke fails at
  argument binding, before the child body runs.
- `process/Main.xaml` — the `Invoke Workflow File` (DisplayName "Invoke ValidatePayment") `Arguments`
  dictionary maps `in_Amount` (`InArgument(x:Double)`) and `out_IsValid`.
- `process/ValidatePayment.xaml` — `<x:Members>` declares `in_GrossAmount` (`InArgument(x:Double)`) and
  `out_IsValid`. There is **no** `in_Amount` argument; the input was renamed to `in_GrossAmount`.
- The mismatch is the stale key `in_Amount` on the parent vs the child's current `in_GrossAmount` — the
  exact key named in the error. `out_IsValid` matches on both sides and is not the problem.

**Evidence:**
- Error: `System.ArgumentException` — "keys ... do not map to arguments and must be removed: in_Amount".
- Parent invoke passes `in_Amount`; child declares `in_GrossAmount` (no `in_Amount`).
- Fault localizes to the InvokeWorkflowFile in `Main.xaml` at argument binding (child body never ran).
- Job identity: Key `4e9d2a71-…`, `ReleaseName` PaymentValidation, `EntryPointPath` Main.xaml, `State`
  Faulted, `ErrorCode` Robot, folder **Shared** (`a2f18c53-…`), machine **MOCK-HOST**. History: Running
  14:41:08 → Faulted 14:41:09. A prior run of the same process succeeded, consistent with the child's
  argument being renamed after that run.

**Immediate fix:**
1. Open the `Invoke Workflow File` ("Invoke ValidatePayment") in `Main.xaml` and click **Import
   Arguments** to pull in the invoked workflow's current argument list.
2. Map the value currently passed as `in_Amount` to the child's renamed input **`in_GrossAmount`**, and
   remove the stale `in_Amount` mapping.
   - Where: `Main.xaml` InvokeWorkflowFile_1 `Arguments` — replace the `in_Amount` key with
     `in_GrossAmount`.
   - (Alternatively, if the rename was unintended, restore the argument name `in_Amount` in
     `ValidatePayment.xaml` — but align both sides on one name.)

**Preventive fix:**
- After renaming/retyping an argument on any invoked workflow, re-open every caller's `Invoke Workflow
  File` and **Import Arguments** so the mappings track the child. `Find References` on the changed
  workflow locates all invocations to update.

| # | Hypothesis | Confidence | Status | Root Cause? | Key Evidence | Resolution |
|---|------------|------------|--------|-------------|--------------|------------|
| H1 | The invoke passes `in_Amount`, but `ValidatePayment.xaml` renamed that input to `in_GrossAmount`; the runtime rejects the stale key with `ArgumentException` at argument binding. | high | confirmed | Yes | Error names key `in_Amount` "must be removed"; parent maps `in_Amount`, child declares `in_GrossAmount` only; fault at the InvokeWorkflowFile before the child ran. | Import Arguments on the invoke and remap `in_Amount` → `in_GrossAmount`. |
| H2 | The child workflow threw its own exception during execution. | low | eliminated | No | The `ArgumentException` occurs at argument binding (`rootArgumentValues`), before the child body executes; no child activity appears in the stack. | N/A — the invoke never entered the child. |
