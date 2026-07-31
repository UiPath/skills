---
confidence: medium
---

# Click Silent No-Op — Activity Reported Success But Did Nothing

## Context

A UIAutomationNext interaction activity — most often `NClick` — reported **Successful** but its effect never landed: the button was never actuated, the field never changed, the downstream step ran against the pre-action state. No exception, no Error log, no fault. The job ended `Successful`.

This is the **no-signature** counterpart to [verify-execution-failure.md](./verify-execution-failure.md):

- **Verify Execution WAS configured and threw** `VerifyActivityExecutionException` → that playbook. The miss produced a signal.
- **Nothing threw** (Verify Execution absent, or present but inert — a `Mode` with no verification target and empty `Retry`/`Timeout`) → **this playbook**. The miss is silent. Route here via `summary.md` § No-signature routing ("Job/run Successful but the action had no effect").

Applies to the input activities whose driver posts an event without asserting the outcome: `NClick`, `NTypeInto`, `NSetText`, `NCheck`, `NSelectItem`, `NHover`, `NKeyboardShortcuts`.

**Classic input activities (`UiPath.Core.Activities` — `Click`, `Type Into`, `Send Hotkey`) are a different playbook** — they have no Verify Execution feature at all, so a missed classic click is silent by design: [classic-activities/click-silent-no-op.md](../../classic-activities/playbooks/click-silent-no-op.md). This playbook covers UIAutomationNext (`N*`) activities only.

What this looks like:

- Job/instance `State = Successful`; **zero** Error-level logs for the run.
- No `NodeNotFoundException` / `SelectorNotFoundException` / `UiElementNotFoundException` / `UiNodeDisabledElementException` / `VerifyActivityExecutionException` anywhere in the trace — the target WAS found and the event WAS posted.
- Downstream evidence that the action had no effect: a later Get Text / Element Exists / business output showing the pre-action value (empty confirmation number, unchanged status field, missing record).
- Healing Agent, if enabled, produced no recovery data (empty ~22-byte archive) — it engages only on a faulting/timing-out modern UI activity, and a silent success never faults.

What can cause it:

- **Input method did not actuate the control.** `InteractionMode = Simulate` acts through the element's control/accessibility API and IS supported for browsers, Java and SAP - it is the product's *recommended* mode for those technologies, and `Background` resolves to it - but only when the specific control implements the action. A control that accepts the API call without acting produces a silent miss. This is **per-element, not per-technology**: do NOT conclude it from `app='java.exe'` (or SAP) alone. A node that cannot take the control API at all fails loudly with `Cannot use UI_CONTROL_API on this UI node. Please use UI_HARDWARE_EVENTS method.` - that is an Error log, so it is not this family. Two Simulate limits independent of technology: only a **single left click with no key modifiers** is honored, and a click **offset** is honored only on Java targets (silently ignored elsewhere under Simulate, which is its own miss cause).
- **Click intercepted by a covering element** — a transparent overlay, cookie/consent banner, modal, or tooltip sat on top of the target at action time; the event hit the overlay, not the control.
- **Wrong target resolved** — the selector matched a duplicate / off-screen / ARIA-hidden / shadow-DOM element that looks right but is inert.
- **Focus / activation lost** between activities — a prior step left focus on another window/tab, so the posted input went nowhere.
- **Timing / DOM race** — the element was re-rendered or replaced between find and action; the event landed on a stale node.
- **Absent or inert Verify Execution** — this does not *cause* the miss, but it is why the miss went undetected. An action-level activity with no real Verify target cannot fault on a no-op.

What to look for:

- The activity's `InteractionMode`, the click shape (`ClickType`, `MouseButton`, `KeyModifiers`, `PointOffset`), and the enclosing scope's **target technology** — these live only in the workflow source. Source-required. Technology alone does not confirm or eliminate the input-method branch.
- Whether Verify Execution is configured with a **real verification target** (not just a `Mode`).
- Runtime proof of no-effect in the Info-level logs or business output — needed to separate "silently did nothing" from "did the right thing and the user is mistaken".

## Investigation

Source-required — resolve the project per SKILL.md §5.4 before concluding.

1. From the job, confirm `State = Successful` and capture the full Info-level logs (`uip or jobs logs <jobKey> --output json`). Confirm **zero** Error logs (`--level Error`). No exception class anywhere = this family.
2. Identify the acting activity (display name + `IdRef`) and its workflow file from the Info trace.
3. Establish **runtime proof the action had no effect** — a downstream Info log line, a captured output argument, or a business record showing the pre-action state (e.g. an empty confirmation number logged after a "Submit" click). Without this, the "did nothing" claim is unconfirmed (§6 runtime-evidence gate) — say so rather than asserting a defect from source alone.
4. Open the workflow source. On the acting activity read:
   - `InteractionMode` (`Simulate` / `SendWindowMessages` / `HardwareEvents` / `ChromiumAPI` / `Background`).
   - `VerifyOptions` — is a verification `Target` set, or is it inert (`Mode` only, empty `Retry`/`Timeout`)?
5. Open the enclosing scope (`NApplicationCard` / Use Application/Browser) and read its `TargetApp` **technology**: `app='java.exe'` / a `javastate` selector = Java; `app='saplogon.exe'` / `sapwnd` = SAP; a Chromium `app='chrome.exe'`/`'msedge.exe'` with an HTML selector = browser.
6. Do NOT ask docs whether the input method is supported for the target technology - `Simulate` is documented as supported and recommended for browsers, Java and SAP, so a technology-level answer neither confirms nor eliminates branch **(A)**. What decides it is element-level: runtime proof of no-effect (step 3) plus a re-run on `HardwareEvents`.
7. If HA was enabled, confirm the empty recovery archive — it is the expected "no fault, no trigger" state, not a separate defect to fix.

## Resolution

### Decision tree

Walk from the top; stop at the first branch that matches.

1. **Is `InteractionMode = Simulate` / `SendWindowMessages` / `Background`, with runtime proof the control never acted and no `UI_CONTROL_API` Error log?** → branch **(A)**. The control accepted the API-level event without performing the action. Report it as the *likely* cause, confirmed only by a re-run on `HardwareEvents` - the target technology is not evidence either way.
2. **Was a covering element present** (overlay / banner / modal detected in HA data or visible in the informative screenshot)? → branch **(B)**.
3. **Did the selector resolve a duplicate / off-screen / hidden element** (multiple matches, `idx=`-positional, shadow/iframe)? → branch **(C)**.
4. **Was focus/activation on the wrong window** at action time (prior activity left another app foreground; `ActivateBefore` not set)? → branch **(D)**.
5. **Default — effect landed on a stale/re-rendered node** (DOM race) → branch **(E)**.

In every branch, **also** close the detection gap (branch **(F)**) so a future miss faults instead of passing silently.

### Branches

- **(A) Control did not act on the API-level event.** Set the acting activity's `InteractionMode` to **`HardwareEvents`** (drives the physical cursor/keyboard — works regardless of framework; requires an interactive session and the foreground). This is the same remedy the driver itself names when a node rejects the control API. `ChromiumAPI` is browser-only. Re-run and confirm the effect lands; if it still misses, the cause is elsewhere (B)-(E). Note `HardwareEvents` gives up Simulate's background/out-of-focus execution, so state that trade-off when proposing it.
- **(B) Covering element intercepted the event.** Add a deterministic dismiss/wait step before the action (close the banner, dismiss the modal, Check App State for the overlay to disappear). Inspect HA data / the informative screenshot for the intercepting element. See [interpretations/healing-agent-data.md](../interpretations/healing-agent-data.md).
- **(C) Wrong element resolved.** Tighten the activity's `Target` selector to a stable, unique attribute; remove positional `idx=`; for shadow-DOM/iframe, scope to the correct frame. Do not loosen — the current selector matched something inert.
- **(D) Focus/activation lost.** Set `ActivateBefore = True` on the activity, or add a Use Application / Activate step before it so the target window is foreground when the input is posted.
- **(E) Timing / DOM race.** Add a Check App State (element appears / is interactive) before the action, or set `WaitForReady = COMPLETE` on the target, so the action runs against a settled node.
- **(F) Close the detection gap (do this in addition to the cause fix).** Configure a **real Verify Execution target** on the action — an element/state that exists ONLY after the action succeeds (e.g. the confirmation element after a submit), with a non-trivial `Timeout`. This converts a future silent no-op into a `VerifyActivityExecutionException` (→ [verify-execution-failure.md](./verify-execution-failure.md)) and, when HA is enabled, gives Healing Agent a fault to engage on. Do NOT treat adding Verify as the whole fix — it surfaces future misses; the cause fix (A–E) is what stops this one.

> Approval gate (SKILL.md §1.10): these are edits to the user's workflow. Present the concrete change (file, activity, current vs proposed `InteractionMode` / Verify target) and get explicit approval before editing.
