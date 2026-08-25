# Final Resolution

Investigation complete. Here is the resolution:

---

**Root Cause:** **The `If` condition uses a case-sensitive string comparison, so an approved record
takes the wrong branch.** The `If` activity "Check approval decision" has the Condition
`decision = "Approved"`. VB string `=` is case-sensitive by default (`Option Compare Binary`). The
source system supplied `decision = "APPROVED"` (upper-case), so `"APPROVED" = "Approved"` evaluates to
`False` and the workflow runs the **Else** branch — routing the order to the manual review queue even
though it was already approved. The job completes **Successful**; nothing faults. This is a **silent
logic fault**, not an exception.

**What went wrong:** The comparison expected an exact-case match but the incoming value differs only in
case. Because there is no exception, the job reports success while producing the wrong business
outcome (approved orders sent to manual review).

**Why:**
- `process/Main.xaml` — the `If` "Check approval decision" (`If_CheckDecision`) has
  `Condition="[decision = "Approved"]"` with an `Else` branch that logs "Routing to manual review
  queue".
- Job log evidence: `Decision from source system: APPROVED` immediately followed by `Routing to manual
  review queue` — the value was `APPROVED` (an approval) yet the Else branch ran.
- VB `=` on `String` is case-sensitive, so `"APPROVED" = "Approved"` is `False`; the Condition does no
  `.Trim()` or case normalization.

**Evidence:**
- Job `c9a4e2f1-7b53-4d81-a260-3f8e1c6d0b49` (process **OrderApprovalRouter**, folder **Shared**, host
  **MOCK-HOST**) ended **Successful** — no fault, no error code.
- Logs show the compared value (`APPROVED`) and the branch actually taken (`manual review`), which
  contradicts the intent (an approved order should auto-approve).
- The `If` Condition compares against the literal `"Approved"` with no normalization — the case
  mismatch is the sole reason the wrong branch ran.

**Immediate fix:**
1. Make the comparison case-insensitive (and whitespace-tolerant). Change the `If` Condition to:
   - `decision.Trim().Equals("approved", StringComparison.OrdinalIgnoreCase)`, or
   - `decision.Trim().ToLower() = "approved"`.
2. Re-run — an `APPROVED` (or `Approved`, `approved`) value now takes the auto-approve branch.

**Do NOT** set `ContinueOnError = True` or otherwise mask this — the job already "succeeds"; the
problem is the branch logic, and hiding it makes the wrong routing harder to catch.

**Preventive fix:**
- Normalize external string values before comparing — `.Trim()` and a case-insensitive compare
  (`StringComparison.OrdinalIgnoreCase`) — since upstream systems, scrapes, and spreadsheets vary in
  case and whitespace.
- For volatile checks (UI state, external calls) wrap the logic in a `Try Catch`
  (`System.Activities.Statements.TryCatch`) so genuine runtime errors surface instead of being
  swallowed, rather than relying on `ContinueOnError`.

| # | Hypothesis | Confidence | Status | Root Cause? | Key Evidence | Resolution |
|---|------------|------------|--------|-------------|--------------|------------|
| H1 | The `If` Condition `decision = "Approved"` is case-sensitive, so `"APPROVED"` fails the match and the Else (manual review) branch runs on approved orders. | high | confirmed | Yes | Logs: `Decision from source system: APPROVED` → `Routing to manual review queue`; source Condition compares to `"Approved"` with no case/whitespace normalization; job Successful (no fault). | Compare case-insensitively + trim: `decision.Trim().Equals("approved", StringComparison.OrdinalIgnoreCase)`. |
| H2 | A robot job faulted and the routing failed with an exception. | low | eliminated | No | Job state is Successful, ErrorCode null, no exception in logs — the fault is silent, not an exception. | N/A — fix the branch logic. |
| H3 | The source system sent the wrong decision value. | low | eliminated | No | The source correctly sent `APPROVED` (an approval); the workflow mis-compared it. The defect is in the `If`, not the input. | N/A — the input is valid; normalize the comparison. |
