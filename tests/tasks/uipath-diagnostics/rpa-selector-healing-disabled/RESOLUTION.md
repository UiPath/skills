# Final Resolution

---

**Root Cause: Benefits Enrollment Portal UI Change — Employee Name Input Field Selector Broken**

**What went wrong:** The Acme Benefits portal removed the `id='employeeName'` attribute from its employee name input field, causing the hardcoded "Type Employee Name" selector in Main.xaml to fail on every single enrollment transaction.

**Why:** The BenefitsEnrollment process navigates to the Acme Benefits portal in Chrome and uses a "Type Into" activity ("Type Employee Name") to enter each employee's name. That activity's selector targets the input field using a single attribute: `id='employeeName'`. At some point before 2026-04-28 (first observed occurrence), the portal's HTML changed — the employee name input field's `id` attribute was removed or replaced. The live portal now exposes INPUT elements with an empty `id` attribute (closest-match score: 50%), meaning the attribute the selector depends on no longer exists in the DOM. Because the selector has no fallback attributes (`name`, `class`, `placeholder`, etc.), it cannot recover from this change. Every one of the 11 employees failed at this first UI step. The process's transaction-level exception handling caught each failure and allowed the job to continue and report "Successful" to Orchestrator — **masking the total business-level failure.** Healing Agent was not enabled (`AutopilotForRobots.HealingEnabled: false`), so no automated selector recovery was attempted. This is a **recurrence**: the identical failure was seen on 2026-04-28 (job `7f453eb5-7906-42ee-8237-ef2071754e60`), and the selector was not fixed between then and now.

---

**Evidence:**

### UI Automation (Root Cause)

- Process: BenefitsEnrollment | Job Key: `777d35d4-26bc-49ad-bbdb-5243ba2947fc` | Machine: MOCK-HOST
- Job ran 2026-05-04 10:31:31Z – 10:39:28Z (~8 minutes) | Orchestrator-reported State: **Successful** — misleading; all enrollments failed
- Activity: "Type Employee Name" (TypeInto) in Main.xaml, line 191
- Failing selector: `<html app='chrome.exe' /><webctrl id='employeeName' tag='INPUT' />`
- 31 Error-level log entries, all identical: `"Could not find the UI element corresponding to this selector: [1] <html app='chrome.exe' /> [2] <webctrl id='employeeName' tag='INPUT' />"`
- Closest DOM matches returned: INPUT elements with **empty `id` attribute** — 50% match score — confirming `id='employeeName'` is absent from the live portal HTML
- All 11 employees affected (John Rivera, Sarah Kim, David Osei, Emma Thompson, Marcus Williams, Priya Patel, James O'Brien, Aisha Nkomo, Tyler Nguyen, Laura Sanchez, Kevin Park) — first failure at 10:31:50Z, last at 10:39:25Z
- Healing Agent: `AutopilotForRobots.Enabled: false`, `HealingEnabled: false` — no automated recovery attempted
- Source code confirmed: Main.xaml selector uses only `id='employeeName'` with no fallback attributes; all other form field selectors follow the same single-attribute pattern
- **Recurrence:** identical error on 2026-04-28, job `7f453eb5-7906-42ee-8237-ef2071754e60` — selector was not updated after first occurrence

---

**Immediate fix:**

### UI Automation (Root Cause)

1. **Re-capture the employee name input field selector in UiPath Studio against the live Acme Benefits portal**
   - Why: The portal HTML changed and `id='employeeName'` no longer exists in the DOM (confirmed by 50%-match empty-id closest match across 31 consecutive failures)
   - Where: Open `Main.xaml` in UiPath Studio → locate "Type Employee Name" (TypeInto) activity → open Selector Editor → with the portal open in Chrome, use "Indicate Element" to re-capture the current field and discover its current stable attributes (`name`, `class`, `placeholder`, `aaname`, or any fixed attribute the portal now exposes)
   - Who: RPA developer
   - Source: Playbook `selector-failure-healing-disabled.md` — Resolution section; `evidence/H1-source-code.json`

2. **Update the selector in Main.xaml, then rebuild and republish the BenefitsEnrollment package**
   - Why: The current selector has no fallback — once the portal attribute changes, the selector fails completely
   - Where: Main.xaml (TypeInto "Type Employee Name", line 191) → update Target selector → build → publish to Orchestrator → deploy to BenefitsEnrollment process in BenefitsEnrollment folder
   - Who: RPA developer
   - Source: Playbook `selector-failure-healing-disabled.md` — Resolution section

3. **(Recommended immediately — before or in parallel with steps 1–2) Enable Healing Agent on the BenefitsEnrollment process**
   - Why: Healing Agent was disabled during both the April 28 and May 4 occurrences. Enabling it now will capture automated diagnostic data if any remaining selector issues exist after the fix is deployed
   - Where: Orchestrator → BenefitsEnrollment folder → Processes → BenefitsEnrollment → Edit → Process Settings → set `AutopilotForRobots.Enabled: true` and `HealingEnabled: true`
   - Who: RPA developer or admin
   - Source: Playbook `selector-failure-healing-disabled.md` — Resolution section

---

**Preventive fix:**

1. **UI Automation — Add redundant fallback attributes to all form field selectors in Main.xaml**
   - Why: The same fragile single-attribute pattern applies to all other form fields (`id='department'`, `id='benefitPlanDropdown'`, `id='btnSubmit'`). One attribute change breaks each selector completely. Adding secondary attributes makes selectors resilient to partial DOM changes.
   - Where: Main.xaml — all TypeInto/Click/Select activities targeting portal form fields; use UiPath Studio Selector Editor to add additional attribute conditions for each
   - Who: RPA developer
   - Source: Playbook `selector-failure-healing-disabled.md` — Context section

2. **UI Automation — Enable Healing Agent permanently on BenefitsEnrollment**
   - Why: This failure recurred from 2026-04-28 without detection. With Healing Agent enabled, future selector drift is caught and recovered automatically, and healing diagnostics are available without manual investigation.
   - Where: Orchestrator → BenefitsEnrollment folder → Processes → BenefitsEnrollment → Process Settings → `AutopilotForRobots.Enabled: true`, `HealingEnabled: true`
   - Who: RPA developer or admin
   - Source: Playbook `selector-failure-healing-disabled.md` — Resolution section

3. **UI Automation — Fix job success/failure masking: surface failures when all enrollments fail**
   - Why: The job reported State=Successful despite 100% enrollment failure. Transaction-level exception handling catches failures without escalating, so Orchestrator monitoring sees a "green" job when the business process is entirely broken.
   - Where: Main.xaml — add a counter for failed transactions; throw or set a failure output when the failure rate hits a configurable threshold (e.g., all transactions failed)
   - Who: RPA developer
   - Source: `evidence/triage-initial.json` (execution path documented); **[Unverified]** — specific exception-handling pattern for transaction loops is not documented in the matched playbook; consult UiPath documentation or RPA best practices for dispatcher/performer patterns before implementing

---

**Investigation Summary**

| # | Hypothesis | Confidence | Status | Root Cause? | Key Evidence | Resolution |
|---|---|---|---|---|---|---|
| H1 | Portal UI change removed `id='employeeName'` from employee name input field; hardcoded single-attribute selector fails for every transaction | High | Confirmed | Yes | 31 identical SelectorNotFoundException errors; closest DOM match is INPUT with empty `id` (50%); Main.xaml line 191 confirmed; recurrence of 2026-04-28 failure | Re-capture selector in Studio; update Main.xaml; enable Healing Agent |

---

Would you like help implementing the selector fix in Main.xaml, or would you like to clean up the `.local/investigations/` folder?
