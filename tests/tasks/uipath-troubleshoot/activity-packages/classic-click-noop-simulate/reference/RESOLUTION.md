# Final Resolution

Here is the investigation result.

---

**Root Cause:** The classic "Click 'Submit Claim'" activity (`UiPath.Core.Activities.Click`, `IdRef Click_1`) in `Main.xaml` has `SimulateClick=True`, but its target is a **Java** application (the full selector is `<wnd app='java.exe' cls='SunAwtFrame' title='Claims Entry System' /><java role='push button' name='Submit Claim' />`). The **SimulateClick** input method is **not supported for Java (nor SAP) targets** — the click event is posted at the message/API layer and the activity reports Successful as soon as the element is found and the event is dispatched, but the Java control never processes it. So the Submit button was never actuated even though the activity "succeeded". The classic `Click` has **no Verify Execution** feature, so nothing on the activity asserted the outcome and the miss never faulted: the job ended `Successful` with zero Error logs.

**What went wrong:** A click that produced no effect was reported as success because the input method (SimulateClick) cannot drive a Java control, and the classic Click has no post-action verification to catch the no-op.

**Why (causal chain):**

- **Confirmed (the no-op):** The runtime Info logs show `Click 'Submit Claim' execution ended` immediately followed by `Claim status after submit: Draft`. The status is still **Draft** after the submit click — a submitted claim would read `Submitted`. That is runtime proof the click had no effect, not a suspicion from source.
- **Confirmed (the cause):** The Click's `SimulateClick=True` and the target technology is Java (`app='java.exe'`, `<java role='push button' ... />`). Per UiPath documentation, SimulateClick / SendWindowMessages are unsupported for Java and SAP — the event is accepted at the OS/message layer but never actioned by the application, i.e. a silent no-op. This is exactly the observed behaviour.
- **Confirmed (why it was silent):** The classic `Click` has no Verify Execution property (that is a modern `NClick` feature), so nothing asserted the post-click state and the miss stayed silent.

**Evidence:**

### Classic UI Automation (Root Cause)
- `Main.xaml` → `Click_1` "Click 'Submit Claim'": `SimulateClick=True`, `SendWindowMessages` not set, no post-action check.
- Full selector `<wnd app='java.exe' cls='SunAwtFrame' title='Claims Entry System' /><java role='push button' name='Submit Claim' />` → Java technology.
- Project `ClassicClaimsSubmit`: classic `UiPath.UIAutomation.Activities` (23.10.x), `UiPath.Core.Activities.Click`.
- Documentation (docsai): SimulateClick / SendWindowMessages are not supported for Java/SAP; use Default (hardware events).

### Orchestrator (Runtime evidence)
- Job `ClassicClaimsSubmit` (folder Finance, key `3b9c2d1e-4f5a-4b6c-8d7e-9f0a1b2c3d4e`): `State = Successful`, Unattended, host MOCK-HOST.
- Error logs: **zero** entries. No `SelectorNotFound` / `ElementOperationException` / `ActivityTimeoutException`.
- Info logs: `Click 'Submit Claim' execution ended` then `Claim status after submit: Draft` (status unchanged → no effect).

**Immediate fix:**

### Classic UI Automation (Root Cause)
1. **Disable SimulateClick on the Click — set `SimulateClick=False` (and leave `SendWindowMessages=False`) so it uses Default (hardware events).**
   - *Why:* Default hardware events drive the physical cursor and work with Java (and SAP); SimulateClick does not actuate Java controls and silently no-ops.
   - *Where:* `Main.xaml`, activity `Click_1` "Click 'Submit Claim'", `SimulateClick` property.
   - *Note:* Do NOT set both `SimulateClick` and `SendWindowMessages` (that is a separate "only one option can be set" config error). Hardware events require an interactive session with the target in the foreground.
2. **Add explicit outcome detection after the Click** — classic Click cannot self-verify, so add an `Element Exists` / `Get Text` on a post-submit indicator (e.g. status = `Submitted`) and an `If` that throws/logs when it is missing.
   - *Why:* makes a future silent miss visible instead of passing as `Successful`.

**Preventive fix:**
1. Use **Default (hardware events)** for all interactions with the Java claims app; reserve SimulateClick/SendWindowMessages for web (HTML) and WPF/WinForms targets.
2. Since classic activities have no Verify Execution, always add explicit post-action checks on clicks/types whose effect matters (or migrate to modern `Use Application/Browser` + `NClick` with Verify Execution).

**Investigation summary:**

| # | Hypothesis | Confidence | Status | Root Cause? | Resolution |
|---|------------|------------|--------|-------------|------------|
| H1 | SimulateClick unsupported on Java target → silent no-op | High | **Confirmed** | **Yes** | Set SimulateClick=False (Default hardware events) |
| H2 | No Verify Execution on classic Click → miss undetected | High | **Confirmed** | Contributing (why silent) | Add explicit Element Exists / If check |
| H3 | Selector matched wrong/duplicate element | Low | Eliminated | No | Selector resolves the intended Java button |
| H4 | ElementOperationException / timeout | Low | Eliminated | No | Zero Error logs; activity reported Successful |

---

> The root cause is confirmed from runtime evidence (status still Draft after the click) plus source (`SimulateClick=True` on a Java target) and documentation. The fix is to disable SimulateClick (use Default hardware events); adding an explicit post-click check compensates for the classic Click's lack of Verify Execution.
