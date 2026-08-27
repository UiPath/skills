# Final Resolution

---

**Root Cause:** A `SelectorNotFoundException` on the **"Click
Submit"** activity is thrown on **every transaction** — the
order-portal UI element can no longer be found
(`<wnd app='orderportal.exe' title='Submit' />`, timeout reached).
After 5 consecutive System Exceptions the REFramework hit its
`MaxConsecutiveSystemExceptions` ceiling and aborted with `The
maximum number of consecutive system exceptions was reached.
Consecutive retry number: 5.` **The abort message is the symptom;
the recurring broken selector is the root cause** — this is the
`job-consecutive-system-exceptions` playbook.

**What went wrong:** Job `ccee6677-...-4455` (OrderReconciliation,
OpsAutomation) processed 0 transactions successfully. Every
transaction (1–5) failed with the same
`UiPath.UIAutomationNext.Exceptions.SelectorNotFoundException` on
"Click Submit", and after the 5th consecutive system exception the
framework aborted the job.

**Why:** The five error-log entries before the abort line are all
the identical exception on the same activity, and `jobs traces`
shows the "Click Submit" activity Faulted on every transaction — a
persistent, per-transaction UI failure, not a one-off. The
`MaxConsecutiveSystemExceptions` threshold only decided *when* to
give up; it did not cause the failure.

**Ruled out:**
- **Threshold too low** — raising `MaxConsecutiveSystemExceptions`
  would let the job burn more attempts and then abort anyway; it
  does not address the broken selector.
- **Business exception / bad data** — the exception is a
  UI-automation System Exception (selector not found), identical
  across transactions, not a per-item business-rule violation.

---

**Evidence:**

### Orchestrator
- Failing job `ccee6677-...-4455` — OrderReconciliation, Faulted at
  `2026-06-25T07:02:14.880Z`
- Job `Info`: `The maximum number of consecutive system exceptions
  was reached. Consecutive retry number: 5.`
- `jobs logs`: transactions 1–5 each failed with
  `UiPath.UIAutomationNext.Exceptions.SelectorNotFoundException:
  Could not find the UI element for 'Click Submit'. Selector:
  <wnd app='orderportal.exe' title='Submit' /> Timeout reached.` —
  then the max-consecutive abort line
- `jobs traces`: "Click Submit" Faulted on every transaction (txn
  1–5) with the same SelectorNotFoundException

---

**Immediate fix:**

1. **Repair the "Click Submit" selector** — this is the recurring
   System Exception the abort is reacting to.
   - **Why:** Every transaction fails at the same activity because
     the order-portal Submit element can no longer be matched (the
     app's UI changed). Fixing the selector stops the per-transaction
     failures, so the consecutive-exception counter never trips.
   - **Where:** Studio → OrderReconciliation → "Click Submit" —
     re-indicate the element, move the selector into the **Object
     Repository**, and/or add a stable anchor; add a `Check
     State` / wait-for-ready before the click so a slow render does
     not look like a missing element.
   - **Who:** Automation developer
   - **Source:**
     `products/orchestrator/playbooks/job-consecutive-system-exceptions.md`

2. **Rerun** after the selector is fixed; transactions should
   process instead of throwing.

---

**Do NOT do this:**

- **Do not just raise `MaxConsecutiveSystemExceptions`** (in
  REFramework `Config.xlsx` / the asset). A higher threshold only
  delays the same abort while wasting more attempts on a UI that is
  still broken. Fix the selector first.

---

**Preventive fix:**

1. **Robustness** — Use Object Repository selectors with anchors and
   `Check State` before critical UI actions so app changes degrade
   gracefully instead of throwing on every transaction.
2. **Exception hygiene** — Keep System vs Business exception
   classification correct so the consecutive-system-exception
   counter reflects real environmental failures, not data issues.
   - **Source:**
     `products/orchestrator/playbooks/job-consecutive-system-exceptions.md`
     (Prevention)

---

**Investigation Summary:**

| # | Hypothesis | Confidence | Status | Root Cause? | Key Evidence | Resolution |
|---|------------|------------|--------|-------------|--------------|------------|
| H1 | Recurring SelectorNotFoundException on "Click Submit" tripping the consecutive-system-exception ceiling (playbook) | High | Confirmed | Yes | 5 identical SelectorNotFoundException log entries before the abort; traces show "Click Submit" Faulted every transaction | Fix the selector (re-indicate / Object Repository / anchor + Check State); rerun |
| H2 | MaxConsecutiveSystemExceptions threshold too low | Low | Refuted | No | Threshold only sets when to give up; raising it does not fix the recurring UI failure | n/a |
| H3 | Business exception / bad transaction data | Low | Refuted | No | Error is a UI System Exception identical across all transactions, not a per-item business rule | n/a |

---

Would you like help applying the fix — re-indicating the "Click
Submit" element into the Object Repository and adding a Check State
guard?
