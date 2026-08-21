# Final Resolution

Here is the investigation result.

---

**Root Cause:** The "Click 'Submit Claim'" activity (modern `NClick`, `IdRef NClick_1`) in `Main.xaml` is configured with `InteractionMode = Simulate`, but its target is a **Java** application (the enclosing `Use Application` scope and the Click both target `<wnd app='java.exe' cls='SunAwtFrame' title='Claims Entry System' />` with a `<java ... />` element selector). The **Simulate** input method is **not supported for Java (nor SAP) targets** — the click event is posted at the message/accessibility layer, the activity reports Successful as soon as the element is found and the event is dispatched, but the Java control never processes it. So the Submit button was never actuated even though the activity "succeeded". Because there is **no Verify Execution** on the activity, nothing asserted the outcome, so the miss never faulted: the job ended `Successful` with zero Error logs.

**What went wrong:** A click that produced no effect was reported as success because the input method (Simulate) cannot drive a Java control, and no Verify Execution was configured to catch the no-op.

**Why (causal chain):**

- **Confirmed (the no-op):** The runtime Info logs show `Click 'Submit Claim' execution ended` immediately followed by `Claim status after submit: Draft`. The status is still **Draft** after the submit click — a submitted claim would read `Submitted`. That is runtime proof the click had no effect, not merely a suspicion from source.
- **Confirmed (the cause):** The Click's `InteractionMode = Simulate` and the target technology is Java (`app='java.exe'`, `<java role='push button' name='Submit Claim' />`). Per UiPath documentation, Simulate / Send Window Messages are unsupported for Java and SAP — the event is accepted at the OS/message layer but never actioned by the application, i.e. a silent no-op. This is exactly the observed behaviour.
- **Confirmed (why it was silent):** The activity has no `VerifyOptions` block at all, so there was nothing to assert the post-click state and turn the miss into a fault.
- **Confirmed (HA not involved):** Healing Agent is disabled on this job (`AutopilotForRobots.Enabled = false`); it plays no part and needs no change.

**Evidence:**

### UI Automation (Root Cause)
- `Main.xaml` → `NClick_1` "Click 'Submit Claim'": `InteractionMode = Simulate`, no `VerifyOptions`.
- Target selector `<java role='push button' name='Submit Claim' />`; scope `Claims - Java` (`NApplicationCard_1`) `TargetApp.Selector = <wnd app='java.exe' cls='SunAwtFrame' title='Claims Entry System' />` → Java technology.
- Project `ClaimsSubmit`: UiPath.UIAutomation.Activities 26.5.0-alpha.12216680 (modern UIAutomationNext).
- Documentation (docsai): Simulate / Send Window Messages are not supported for Java/SAP; use Hardware Events.

### Orchestrator (Runtime evidence)
- Job `ClaimsSubmit` (folder Finance, key `7c4e1a9b-2d6f-4a81-b3e0-9f5c1d8a2e44`): `State = Successful`, Unattended, host MOCK-HOST.
- Error logs: **zero** entries. No `SelectorNotFound` / `NodeNotFound` / `UiElementNotFound` / `VerifyActivityExecutionException`.
- Info logs: `Click 'Submit Claim' execution ended` then `Claim status after submit: Draft` (status unchanged → no effect).
- `AutopilotForRobots.Enabled = false` (Healing Agent not involved).

**Immediate fix:**

### UI Automation (Root Cause)
1. **Change the Click's input method from Simulate to Hardware Events.**
   - *Why:* Hardware Events drives the physical cursor/keyboard and works with Java (and SAP); Simulate does not actuate Java controls and silently no-ops.
   - *Where:* `Main.xaml`, activity `NClick_1` "Click 'Submit Claim'", `InteractionMode` property.
   - *Note:* Hardware Events requires an interactive session with the target in the foreground (unattended is fine on an interactive robot session).
2. **Add a real Verify Execution target** to the Click — an element/state that exists only after a successful submit (e.g. status = `Submitted`, or a confirmation element) with a non-trivial Timeout.
   - *Why:* today nothing asserts the outcome, so a future miss would again pass silently; a real Verify target makes it FAULT instead.

**Preventive fix:**
1. Use **Hardware Events** for all interactions with the Java claims app; reserve Simulate/Send Window Messages for HTML and WPF/WinForms targets.
2. Never leave Verify Execution unset on action activities whose effect matters.

**Investigation summary:**

| # | Hypothesis | Confidence | Status | Root Cause? | Resolution |
|---|------------|------------|--------|-------------|------------|
| H1 | Simulate input unsupported on Java target → silent no-op | High | **Confirmed** | **Yes** | Switch input method to Hardware Events |
| H2 | Missing Verify Execution → miss undetected | High | **Confirmed** | Contributing (why silent) | Add real Verify target |
| H3 | Selector matched wrong/duplicate element | Low | Eliminated | No | Selector resolves the intended Java button |
| H4 | Healing Agent gated off | Low | Eliminated | No | HA disabled on job; not involved |

---

> The root cause is confirmed from runtime evidence (status still Draft after the click) plus source (`InteractionMode=Simulate` on a Java target) and documentation. The fix is to switch the Click to Hardware Events; adding a Verify target hardens against future silent misses.
