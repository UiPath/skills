# Final Resolution

---

**Root Cause:** The UI Automation **Check App State 'Welcome'** activity in
`AcmeTest_Login.xaml` timed out — after login, the ACME portal did not return the
expected post-login state (neither the welcome dashboard nor the credential-error
page appeared within the activity's `Timeout = 10s`). The workflow's explicit
`IfNotExists → "Target does not appear" → Throw` branch then raised
`System.SystemException: "It was not possible to access the portal"`, faulting job
`3735ac5a-86b8-4b6c-821b-cd4df71831f7` (`HealingAgent_GetEmployeeInformation`,
"Healing Agent" folder).

**What went wrong:** Post-login the portal never reached the expected state. The
outer `Check App State 'Welcome…'` ran its full ~10 s window (≈20:34:07–20:34:17)
without finding the dashboard element; the inner `Check App State 'These
credentials'` also found nothing (≈20:34:17–20:34:22); the `Target does not appear`
sequence executed the explicit `Throw`, and the job faulted at 20:34:29.

**Why (Medium confidence):** The proximate, actionable root cause is the
**Welcome Check App State timeout**. The deeper sub-cause — whether the portal was
genuinely **slow**, showed the **wrong/blank page**, or the target's hardcoded
welcome text no longer **matched** the logged-in user — **cannot be pinned from
Orchestrator CLI evidence alone.** That distinction requires the healing-data
**screenshot** of what was on screen at timeout, which is **not retrievable via the
`uip` CLI** (the `or jobs healing-data` archive was unavailable). This is a genuine
evidence ceiling, not a missing investigation step.

Causes **eliminated** from the available evidence:
- **Robot session lock / RDP disconnect** — job history is a clean `Pending → Running → Faulted` with no session-interruption events.
- **Picture-in-Picture (PiP) involvement** — no PiP signals present.
- The **"Healing agent configuration."** Info log at 20:33:54 is a benign robot
  startup config read — expected, non-blocking, **not a fault contributor**.

---

**Evidence:**

### UI Automation (Root Cause)
- Faulting workflow: `AcmeTest_Login.xaml`, activity `Check App State 'Welcome…'` (`UiPath.UIAutomationNext.Activities.NCheckState`), `Timeout = 10`.
- Activity duration (~10 s, 20:34:07→20:34:17) matches `Timeout = 10` exactly — the check exhausted its window.
- Enclosing scope: `AttachMode = ByInstance`, `InteractionMode = Simulate`, target `https://acme-test.uipath.com/`.
- Error: `System.SystemException: "It was not possible to access the portal"` thrown by the explicit `Target does not appear` branch.
- Package: `UiPath.UIAutomation.Activities 25.2.1-preview`.

### Orchestrator
- Job `3735ac5a-…` — **Faulted**; history `Pending → Running → Faulted` (no session interruption).
- Healing Agent enabled (`AutopilotForRobots.Enabled = true`, `HealingEnabled = true`); benign config Info log at 20:33:54.

---

**Immediate fix:**
1. Increase the **`Timeout`** on `Check App State 'Welcome…'` and/or add a **Retry Scope** (or a preceding `Check App State` / `Element Exists`) around the post-login state check — give the portal more time to render before the throw.
2. Do **NOT** blindly increase the timeout: retrieve the **healing-data screenshot** from a live run to confirm *why* the state was missing (slow render vs. wrong page vs. stale target text), then pick the fix branch:
   - genuinely slow → larger timeout / explicit wait;
   - wrong/blank page → fix the upstream navigation/login step;
   - target text no longer matches the logged-in user → make the welcome target less text-sensitive.

**Preventive fix:** Add explicit wait/retry around post-login state checks; avoid hardcoded, user-specific welcome-text targets when the signed-in user can vary.

**Out-of-band confirmation (evidence ceiling):** Pull the `or jobs healing-data`
screenshot from a live environment to distinguish the sub-cause, and check sibling
job recurrence to confirm transient vs. systematic. Neither is available through the
CLI evidence captured here — the diagnosis is correct at the **timeout-root-cause**
altitude; the sub-cause and exact fix branch remain open pending that screenshot.
