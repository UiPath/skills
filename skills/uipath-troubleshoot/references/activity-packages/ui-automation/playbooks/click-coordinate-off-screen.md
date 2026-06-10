---
confidence: high
---

# Click Coordinate Off-Screen — HardwareEvents

## Context

A UI Automation input activity (`NClick`, `NTypeInto`, `NHover`, or any descendant of `Activities.Workflow.Input.*`) faulted at the cursor-injection stage because the destination coordinate fell outside the runtime host's virtual-screen rectangle. The element was located successfully by selector; the OS rejected the absolute coordinate before any input was sent. This is **not** a selector-resolution failure — do not match against `selector-failure-*` playbooks.

What this looks like:

- Exception type: `UiPath.UIAutomationNext.Exceptions.UiAutomationException`
- Exception message: literally `"Cannot send input to UI element because it is outside of screen bounds."`
- Inner exception: `System.Runtime.InteropServices.COMException`, HRESULT `0x800402bd`
- Stack frame origin: `UiPath.UiNodeClass.Click` → `UiInputService.ClickAtPointAsync` → `UiInputService.ClickAsync` (the element was already located before the throw)
- Job runs only a few seconds before faulting — the failure is at first input, not after waiting for an element

What can cause it — four distinct mechanisms, each fits a different XAML pattern:

- **C1. Page-scroll mismatch (web targets only).** The page was scrolled at design time so the element was visible in the viewport; at runtime the page loads at scroll=0 and the element sits below the fold. The selector still resolves (DOM is unchanged) but the element's runtime screen Y is huge. Typical fingerprint: `NBrowser` / `NApplicationCard` (browser scope) AND no `Scroll`, `Scroll Into View`, `Hover`, or anchor-bearing `Navigate Browser` activity precedes the input. `Target.DesignTimeRectangle` and `TargetApp.Area` look fine in isolation — the geometry math against the host doesn't expose the cause.
- **C2. Window not normalized at runtime.** `AttachMode=ByInstance` reuses whatever window state the application already has — minimized, half-height, positioned off the visible monitor. The runtime viewport ends up smaller or differently positioned than the design-time canvas. Typical fingerprint: `AttachMode=ByInstance` AND no `Maximize Window` / `Set Browser Size` / `Set Window State` / `Move Window` precedes the input.
- **C3. Multi-monitor design canvas → single-monitor host.** The element's natural DOM/layout position genuinely doesn't fit any window the host can provide. Even maximized to the host's full virtual screen, the element renders past the host's MaxY (or MaxX). Typical fingerprint: `TargetApp.Area` extends past the runtime host's virtual-screen rectangle (e.g., `Area = -13, -13, 3866, 2330` on a single 1920×1080 host).
- **C4. Sticky chrome displacement.** A header, cookie banner, popup, modal, browser update notification, or Windows taskbar accumulated at runtime and pushed the element below the visible viewport even though the page is at the right scroll position and the window is correctly sized.

> **C1 vs C2 are indistinguishable from XAML alone.** A `ByInstance` browser scope with no preceding sizing AND no preceding scroll fits both. When both step 5b and step 5c fire, accept the ambiguity, recommend the universal fix, and present — do not loop trying to pick one. Asking the user "was the window maximized?" / "was the page scrolled?" almost always gets "I don't know" — accept that and present.

`InteractionMode=HardwareEvents` (or `WindowMessages`) is the necessary precondition for **all four** mechanisms — those modes drive the real OS cursor at an absolute screen coordinate. The viewport-independent modes (`DebuggerApi`, `Simulate`, or `SameAsCard` when the enclosing scope uses one of those) operate on the application's DOM / accessibility tree and bypass the screen-coordinate requirement entirely.

> **Valid `InteractionMode` values for input activities in UIAutomationNext:** `SameAsCard`, `HardwareEvents`, `Simulate`, `DebuggerApi`, `WindowMessages`. Do NOT recommend or write any value outside this list — XAML deserialization will fail on unknown values (the activity won't load in Studio or at runtime). In particular, `ChromiumAPI` is **not** a valid value in this enum; recommend `DebuggerApi` instead for Chromium browser scopes.

## Investigation

1. **Confirm the exception signature.** Read the job's error log via `uip or jobs logs <job-key> --level Error --output json`. The combination of exception class `UiAutomationException`, message containing "outside of screen bounds", and inner `COMException` `0x800402bd` is definitive — no other playbook in this folder matches this signature, do not branch to `selector-failure-*`.

2. **Identify the faulted activity and its scope container.** From the job's traces (`uip or traces spans get --job-key <job-key> --output json`) and/or workflow source, locate the input activity by `IdRef` and walk up to its enclosing scope container (`NApplicationCard`, `NBrowser`, `Use Application/Browser`, `NWindow`).

3. **Extract the geometry signals from the XAML.** From the input activity element:
   - `InteractionMode` — confirm it is `HardwareEvents` (or `WindowMessages`). If it is `DebuggerApi`, `Simulate`, or `SameAsCard` chained to a non-OS-cursor mode, this playbook does not apply (those modes don't dispatch OS cursor input).
   - `Target.DesignTimeRectangle` (format: `X, Y, Width, Height`) — the captured rectangle of the resolved element. Treat as a hint, **not** the runtime click target.
   - `HealingAgentBehavior` on the activity, and on the scope container.

   From the enclosing scope container:
   - `TargetApp.Area` (format: `X, Y, Width, Height`) — the design-time canvas. Compute `MaxX = X + Width`, `MaxY = Y + Height`.
   - `TargetApp.Selector` / `TargetApp.Url` — used to decide whether the target is web (C1 candidate) or desktop.
   - `AttachMode` (`ByInstance` / `SingleWindow` / `ByProcessName`).

4. **Walk preceding siblings of the input activity inside the scope body.** Record presence/absence of each of these in order:
   - Scroll-class activities — `Scroll`, `Scroll Into View`, `Hover` targeting the failing element, or `Navigate Browser` / `Go To URL` with an in-page anchor (`#fragment`). Absence is the C1 fingerprint.
   - Sizing-class activities — `Maximize Window`, `Set Window State`, `Set Browser Size`, `Move Window`, `Restore Window`. Absence (combined with `AttachMode=ByInstance`) is the C2 fingerprint.
   - Project-wide grep these too — gaps that are structural across the codebase (no sizing activity in ANY workflow) are stronger evidence than a local omission.

5. **Pick the sub-cause via this decision tree.** Apply in order; stop at the first match:

   ```
   5a. Is the target a browser (TargetApp.Url is set, BrowserType is Edge/Chrome/Firefox,
       or scope is NBrowser)?

       YES → 5b.
       NO  → skip to 5c.

   5b. Preceding-scroll check (web targets):
       - No Scroll / Scroll Into View / Hover / anchor-navigation activity before the
         input AND the failing element is likely below the fold on a fresh page-load
         (deep in the document, common for "Learn More", "Footer", "Submit" controls
         on long pages) → C1 (page-scroll mismatch). This is the most common web case.
       - A preceding scroll exists but the element is still off-screen → proceed to 5c
         (window-state or chrome).

   5c. Window-state check:
       - AttachMode=ByInstance AND no preceding Maximize Window / Set Browser Size /
         Set Window State / Move Window → C2 (window not normalized).
       - Otherwise → 5d.

   5d. Geometry check:
       - From job-get, read HostMachineName. The runtime virtual-screen rectangle of
         that host is the failure boundary. Compare element-center (X+W/2, Y+H/2)
         from DesignTimeRectangle against the host rectangle.
       - Element-center fits inside host's screen → C3 ELIMINATED. The element would
         render on-screen if the window were maximized and the page were scrolled —
         loop back to 5b/5c.
       - Element-center exceeds host's screen even when fully maximized → C3 confirmed
         (multi-monitor design → smaller host).

   5e. Chrome / overlay check:
       - User reports a banner, popup, modal, cookie prompt, or browser-update overlay
         appearing on the affected page → C4 (sticky chrome).
       - Otherwise the cause is undetermined — recommend the universal fix from
         Resolution and surface the ambiguity to the user.
   ```

   **Host-geometry data.** Do NOT fabricate or assume the host's display geometry. The `uip` CLI does not currently expose monitor/resolution metadata for a robot host (`or machines list` returns registration metadata only — no `Resolution`, `VirtualScreenRectangle`, or `Monitors` fields). If you cannot derive the runtime virtual-screen rectangle from a verified source (job logs, traces, an attached screenshot, a Healing-Agent capture), STOP and write `.local/investigations/needs_input.json` per `agents/shared.md` § "Requesting User Input". Ask for the host's display configuration with concrete option ranges (e.g., `1920x1080`, `2560x1440`, `3840x2160`, `multi-monitor with primary <X>x<Y>`). Do NOT default to any "typical" value — choosing the wrong sub-cause picks the wrong fix.

   **When the orchestrator re-spawns you with the user's answer**, continue from this step: re-run the decision tree using the new data and pick the matching sub-cause. Do NOT stop at "answer received" — the answer is an input to *complete* your verdict, not the verdict itself. Record the diff in your evidence file and set the hypothesis status before returning to the orchestrator.

6. **Confirm Healing could not relocate.** Read job-get → `JobInputArguments` / process settings for `AutopilotForRobots.HealingEnabled`. Confirm the job-error log contains `Healing agent is disabled for the current job.` or the equivalent. If Healing was enabled but produced no fix, switch to `no-recovery-data.md`.

## Causes

Name the confirmed sub-cause exactly:

- **C1.** Page-scroll mismatch — design-time captured the element at a scrolled viewport position; runtime opens at scroll=0; the element sits below the fold. Web targets only.
- **C2.** Window not normalized at runtime — `AttachMode=ByInstance` inherits whatever window state the application already has, and no preceding activity sizes/positions it before the click.
- **C3.** Multi-monitor design canvas → smaller host — the element's natural layout position exceeds the host's virtual screen even with the window maximized.
- **C4.** Sticky chrome — header/banner/modal/popup displaced the element below the viewport.

Do NOT assert a sub-cause unless step 5's decision tree actually arrived at it.

## Resolution

Pick the fix that matches the identified sub-cause. The interaction-mode switch is the **universal fix** — it covers all four sub-causes and is the safest recommendation when the cause is ambiguous.

- **Universal fix — switch the interaction mode** (covers C1, C2, C3, C4). Change the activity's `InteractionMode` to a viewport-independent value from the **valid enum**: `SameAsCard`, `HardwareEvents`, `Simulate`, `DebuggerApi`, `WindowMessages`. For a browser scope, recommend `DebuggerApi` (drives input through the Chromium debugger / DOM); for a desktop application, recommend `Simulate` (drives input through the UI accessibility tree). If the enclosing `NApplicationCard` / `NBrowser` already runs `InteractionMode=DebuggerApi` or `Simulate`, recommend `SameAsCard` so the activity inherits that mode without re-stating it. These modes do not require an on-screen coordinate. **Never recommend `ChromiumAPI` — it is not a valid enum value and XAML deserialization will fail on it.** Recommended unless `HardwareEvents` is mandatory (e.g., the target application doesn't expose a scripting surface and only accepts real input events).
- **C1-specific fix — scroll the element into view.** Insert a `Scroll Into View` activity targeting the failing element as the first child of the scope's body (or immediately before the input). For pages with a static anchor, `Navigate Browser` with the `#fragment` URL also works. Use when staying on `HardwareEvents` is required and the cause is the page-scroll mismatch.
- **C2-specific fix — normalize the application window.** Insert a `Maximize Window`, `Set Window State`, or `Set Browser Size` activity before the input. Use when the cause is window-state inheritance and the workflow must remain on `HardwareEvents`.
- **C3-specific fix — re-capture on a single-monitor canvas.** Re-record the scope container and the input activity on a display configuration matching production. The new `TargetApp.Area` and `DesignTimeRectangle` will fit the runtime host. Use when the project was authored on a wider canvas than production hosts can ever provide.
- **C4-specific fix — dismiss the chrome.** Insert an activity to close the banner / popup / modal before the input (`Click` on the close button, `Send Hotkey Esc`, or a CSS-rule injection through a script step).
- **Enable Healing Agent on the process** — set `AutopilotForRobots.HealingEnabled=true` in the release's `ProcessSettings`. Healing can relocate an off-screen coordinate on retry. Use as defense-in-depth; it does not fix the underlying authoring gap.

Do NOT "fix" the selector (adding wildcards, switching to `automationId`, tightening attributes). The selector resolved correctly — selector hardening is wrong for this fault class and masks the real defect.
