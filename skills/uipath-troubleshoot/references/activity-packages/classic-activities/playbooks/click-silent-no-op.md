---
confidence: medium
---

# Classic Click Silent No-Op — Reported Success But Did Nothing

## Context

A classic UI activity — most often `Click` (`UiPath.Core.Activities.Click`) — reported **Successful** but its effect never landed: the button was never actuated, the downstream step ran against the pre-action state. No exception, no Error log, no fault. The job ended `Successful`.

Distinct from the classic exception paths:
- **`ElementOperationException` thrown** (element found, action failed) → [ui-element-interaction-failed.md](./ui-element-interaction-failed.md).
- **`SelectorNotFoundException` / `ActivityTimeoutException`** (target never located) → [ui-element-not-found.md](./ui-element-not-found.md) / [ui-activity-timeout.md](./ui-activity-timeout.md).
- **`"Only one of the {0} and {1} options can be set"`** (both `SimulateClick` and `SendWindowMessages` set) → [ui-activity-configuration-error.md](./ui-activity-configuration-error.md).
- **Nothing threw** → **this playbook**. Route here via `summary.md` (top level) § No-signature routing ("Job/run Successful but the action had no effect").

Classic Click, unlike the modern `NClick`, has **no Verify Execution feature** — there is nothing on the activity to assert the outcome, so a missed classic click is silent *by design*. (For the modern `NClick` silent no-op see the **ui-automation** package.)

Applies to the classic input activities whose driver posts an event without asserting the outcome: `Click`, `Type Into`, `Send Hotkey`.

What this looks like:

- Job/instance `State = Successful`; **zero** Error-level logs for the run.
- No `SelectorNotFoundException` / `ElementOperationException` / `ActivityTimeoutException` anywhere in the trace — the target WAS found and the event WAS posted.
- Downstream evidence the action had no effect: a later Get Text / Element Exists / business output showing the pre-action value.

What can cause it:

- **Input method not honored by the target technology.** Classic Click exposes two mutually-exclusive booleans: `SimulateClick` and `SendWindowMessages`; both unset = **Default** (hardware events). **`SimulateClick` and `SendWindowMessages` are not supported for Java, SAP, and some legacy Win32 / Citrix targets** — the event is posted, the activity reports success, and the control never reacts. Primary cause when the target app is Java/SAP. (Both booleans unset — hardware events — does drive these technologies.)
- **Click intercepted by a covering element** — an overlay, modal, tooltip, or another window sat over the target; the event hit the cover.
- **Wrong target resolved** — a loose/positional selector matched a duplicate / off-screen / inert element that looks right.
- **`ClippingRegion` / `CursorPosition` offset** places the click at a point outside the element or on empty space.
- **Focus / activation lost** between activities so the posted input went nowhere.

What to look for:

- The classic Click's `SimulateClick` / `SendWindowMessages` flags and the target **technology** (from the full selector). Source-required.
- Runtime proof of no-effect in Info-level logs or business output — needed to separate "silently did nothing" from "did the right thing and the user is mistaken".

## Investigation

Source-required — resolve the project per SKILL.md §5.4 before concluding.

1. From the job, confirm `State = Successful` and capture the full Info-level logs (`uip or jobs logs <jobKey> --output json`). Confirm **zero** Error logs (`--level Error`). No exception class anywhere = this family.
2. Identify the acting activity (display name) and its workflow file from the Info trace.
3. Establish **runtime proof the action had no effect** — a downstream Info log line, an output argument, or a business record showing the pre-action state. Without it, the "did nothing" claim is unconfirmed (§6 runtime-evidence gate) — say so rather than asserting a defect from source alone.
4. Open the workflow source. On the classic `Click` read:
   - `SimulateClick` (`True`/`False`) and `SendWindowMessages` (`True`/`False`). Both `False` = Default / hardware events.
   - `ClippingRegion` / `CursorPosition` / `OffsetX` / `OffsetY` if set.
5. Read the activity's full `Selector` and identify the **target technology**: `app='java.exe'` / a `javastate`/`java` attribute = Java; `app='saplogon.exe'` / `sapwnd` = SAP; a browser or plain `wnd`/`ctrl` for Win32/WPF.
6. Cross-check the input-method × target-technology support with docs when the pairing looks unsupported: `uip docsai ask "Is the SimulateClick / SendWindowMessages input method supported for Java (or SAP) applications in UiPath UI Automation?" --source docs`.

## Resolution

### Decision tree

Walk from the top; stop at the first branch that matches.

1. **Is `SimulateClick=True` or `SendWindowMessages=True` AND the target technology is Java, SAP, or legacy Win32/Citrix?** → branch **(A)**. Documented-unsupported pairing — the event is never processed.
2. **Was a covering element present** (overlay / modal / another window over the target)? → branch **(B)**.
3. **Did the selector resolve a duplicate / off-screen / inert element** (loose/positional `idx=`)? → branch **(C)**.
4. **Is a `ClippingRegion` / `CursorPosition` offset set** that lands off the element? → branch **(D)**.
5. **Default — focus/activation lost or a timing race** → branch **(E)**.

In every branch, **also** add explicit outcome detection (branch **(F)**) — classic Click has no Verify Execution, so the workflow must check the result itself.

### Branches

- **(A) Input method unsupported for the target technology.** Set `SimulateClick=False` AND `SendWindowMessages=False` so the Click uses **Default (hardware events)**, which drives Java/SAP/legacy Win32 (requires an interactive session with the target in the foreground). Do NOT set both flags together — that is a separate config error. Re-run and confirm the effect lands.
- **(B) Covering element intercepted the event.** Add a deterministic dismiss/wait step before the Click (close the banner/modal; `Wait UI Element Appear`/`Element Exists` on the blocker's absence).
- **(C) Wrong element resolved.** Tighten the `Selector` to a stable, unique attribute; remove positional `idx=`.
- **(D) Offset lands off the element.** Clear or correct `ClippingRegion` / `CursorPosition` (`OffsetX`/`OffsetY`) so the click point falls inside the target.
- **(E) Focus/activation lost or timing race.** Add an `Attach Window` / activation step (or `Wait UI Element Appear`) before the Click so the target is foreground and settled.
- **(F) Add outcome detection (do this in addition to the cause fix).** Classic Click cannot self-verify. After the action, add an `Element Exists` / `Get Text` on an element/state that exists ONLY after success, and branch (`If`) to throw or log when it is missing — so a future silent miss becomes visible instead of passing as `Successful`. (The modern `NClick` bakes this in via Verify Execution; classic must do it explicitly.)

> Approval gate (SKILL.md §1.10): these are edits to the user's workflow. Present the concrete change (file, activity, current vs proposed `SimulateClick`/`SendWindowMessages`) and get explicit approval before editing.
