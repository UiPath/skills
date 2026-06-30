# Final Resolution

Root Cause: **Click activity drove an OS-cursor coordinate outside the host's screen bounds** on a browser target — playbook `click-coordinate-off-screen.md`, sub-cause **C1 (page-scroll mismatch)** with **C2 (window-not-normalized)** as an indistinguishable co-candidate.

What went wrong: The "Click 'Learn More About Editor'" activity in `Ofsb.xaml` ran with `InteractionMode=HardwareEvents`, which dispatches a real OS cursor click at an absolute screen coordinate; the resolved element's runtime Y position sat below the visible viewport (likely because the DataTables page loaded at scroll=0 and no `Scroll Into View` precedes the click), so Windows rejected the input with `HRESULT 0x800402bd` before the click was sent.

Why: At design time the click was recorded against the element 'Learn More About Editor' on `https://datatables.net/` while the page was scrolled to bring the element into the viewport (`Target.DesignTimeRectangle` Y=1090, well below the fold of a fresh page-load). At runtime the `NApplicationCard` scope reuses an existing Edge window (`AttachMode=ByInstance`) and the click sequence's body has **zero preceding siblings** — no `Scroll Into View`, `Hover`, `Navigate Browser` with `#fragment`, `Maximize Window`, `Set Browser Size`, or `Set Window State`. So either the page is at scroll=0 (C1) or the window is in an inherited non-maximized state (C2), or both. The fault originates inside `UiPath.UIAutomationNext.Services.UiInputService.ClickAtPointAsync` (`UiNodeClass.Click` stack frame) — this is the cursor-injection stage, not selector resolution. C3 (multi-monitor canvas) is eliminated: element-center (1736.5, 1137) fits inside the host's single-monitor 4K screen (3840x2160). C4 (sticky chrome) is plausible but unsupported by evidence (no Healing screenshot — Healing was disabled; ~4.75s runtime is too short for a typical cookie/update banner to accumulate). The Orchestrator layer surfaced the fault but did not cause it — `ErrorCode=Robot`, Source=Manual, and `AutopilotForRobots.HealingEnabled=false` meant nothing intercepted the fault and the job moved straight to Faulted.

Evidence:

### UI Automation (Root Cause)
- Job error message: `Cannot send input to UI element because it is outside of screen bounds.`
- Exception: `UiPath.UIAutomationNext.Exceptions.UiAutomationException` → inner `System.Runtime.InteropServices.COMException` HRESULT `0x800402bd`
- Originating stack frame: `UiPath.UiNodeClass.Click` → `UiPath.UIAutomationNext.Services.UiInputService.ClickAtPointAsync`
- Faulted activity: Click "Learn More About Editor" (`NClick_1` in `Ofsb.xaml`), `InteractionMode=HardwareEvents`, `ActivateBefore=False`, target selector `<webctrl aaname='Learn More About Editor' class='site-btn' tag='A' />`, `DesignTimeRectangle=1333, 1090, 807, 94` (element-center 1736.5, 1137)
- Enclosing scope: Use Application/Browser "Edge DataTables Javascript table library" (`NApplicationCard_1`), `AttachMode=ByInstance`, scope `InteractionMode=DebuggerApi`, `TargetApp.BrowserType=Edge`, `TargetApp.Url=https://datatables.net/`, `TargetApp.Area=-13, -13, 3866, 2330`
- Preceding-sibling walk inside the scope's "Do" sequence: **zero** activities before the click. No `Scroll`, `Scroll Into View`, `Hover`, `Navigate Browser`, `Maximize Window`, `Set Browser Size`, `Set Window State`, or `Move Window`. The only other body activity is a disabled (CommentOut) `Keyboard Shortcuts` block that does not execute.
- Host display: MOCK-HOST is single-monitor 4K (3840x2160, user-confirmed) — element fits inside host screen, so C3 (multi-monitor canvas → smaller host) is eliminated.
- Job runtime ~4.75s (Start 2026-05-25T17:56:44.133Z → End 2026-05-25T17:56:48.883Z), consistent with failure at first input rather than after element-wait.
- `UiPath.UIAutomation.Activities` package version `26.5.0-alpha.11984665`.

### Orchestrator (Propagation)
- Job 'ERN' (key `8c994220-a19a-4c62-9868-6df7b61c97e3`, Id 65135970) in folder **Shared**, Unattended, Source=Manual, finished in `Faulted` state with `ErrorCode=Robot`.
- Host machine: **MOCK-HOST**. Robot identity: `newrobot` (Windows account `UIPATH\REPLACEMENT_USER`).
- `AutopilotForRobots.Enabled=false` and `AutopilotForRobots.HealingEnabled=false` in `JobInputArguments` — Healing Agent did not engage (process-level kill switch supersedes the per-activity `HealingAgentBehavior=SameAsCard` and scope-level `HealingAgentBehavior=Job`), so there was no in-flight relocation attempt.
- Job source is Manual (not queue/trigger-driven), so queue Auto-Retry and trigger-level retry do not apply — the fault propagated straight to a terminal Faulted state with no automatic retry.

Immediate fix:

### UI Automation (Root Cause)
1. Switch the click activity off `HardwareEvents`. Change the "Click 'Learn More About Editor'" activity's **Input mode** from `HardwareEvents` to `SameAsCard` (preferred — inherits the scope's already-correct `DebuggerApi`) or explicitly to `DebuggerApi`.
  - Why: The scope `NApplicationCard_1` already runs `InteractionMode=DebuggerApi` (the Chromium debugger / DOM-driven input pipeline). Inheriting it via `SameAsCard`, or naming `DebuggerApi` explicitly, dispatches the click through the browser's DOM rather than at an OS screen coordinate, so the `0x800402bd` screen-bounds check disappears. This is the playbook's **universal fix** and covers both C1 and C2 — disambiguation isn't required.

    **Valid `InteractionMode` enum values:** `SameAsCard`, `HardwareEvents`, `Simulate`, `DebuggerApi`, `WindowMessages`. **Do NOT use `ChromiumAPI`** — it is not a valid enum value and XAML deserialization will fail on it (the activity won't load in Studio or at runtime).
  - Where: `Ofsb.xaml`, activity `NClick_1` ("Click 'Learn More About Editor'") inside `NApplicationCard_1`. In Studio: open the activity properties → **Input** section → **Input mode** = `SameAsCard` (or `DebuggerApi`). In XAML: change `InteractionMode="HardwareEvents"` to `InteractionMode="SameAsCard"` (or `InteractionMode="DebuggerApi"`) on the `<uix:NClick ... />` element.
  - Who: RPA developer
  - Source: `references/activity-packages/ui-automation/playbooks/click-coordinate-off-screen.md` § Resolution → "Universal fix — switch the interaction mode"

### Orchestrator (Propagation)
1. Manually restart the job once the UI Automation fix is applied. Use **Jobs** → locate job `8c994220-a19a-4c62-9868-6df7b61c97e3` → **More Actions > Restart** (or start a new run of process 'ERN' in folder 'Shared').
  - Why: Per UiPath docs, faulted Unattended jobs from a Manual source are not retried automatically — they must be restarted from the Jobs list. There is no built-in Orchestrator-side retry policy for Manual/child jobs that would have recovered this fault.
  - Where: Orchestrator → folder 'Shared' → Jobs → job `8c994220-a19a-4c62-9868-6df7b61c97e3` → More Actions → Restart.
  - Who: RPA developer or process owner
  - Source: https://docs-staging.uipath.com/orchestrator/automation-cloud/latest/user-guide/job-states ; https://docs-staging.uipath.com/orchestrator/standalone/2020.10/user-guide/managing-jobs

Preventive fix:

1. **UI Automation** — As a C1-specific alternative if the team prefers to stay on `HardwareEvents` (e.g., the click must drive a real OS cursor): insert a `Scroll Into View` activity targeting "Learn More About Editor" as the first child of the `NApplicationCard_1` "Do" sequence, immediately before the click. For a static page anchor, a `Navigate Browser` with the in-page `#fragment` URL works equivalently.
  - Why: Walk of preceding siblings shows **zero** scroll-class activities in the scope body — at runtime the page loads at scroll=0 and the design-time-captured Y=1090 element sits below the fold. `Scroll Into View` brings the element into the viewport before the click resolves its screen coordinate, eliminating C1.
  - Where: `Ofsb.xaml`, inside `Sequence_5` ("Do") inside `NApplicationCard_1`, before `NClick_1`.
  - Who: RPA developer
  - Source: `references/activity-packages/ui-automation/playbooks/click-coordinate-off-screen.md` § Resolution → "C1-specific fix — scroll the element into view"

2. **UI Automation** — Add a window normalization step as defense-in-depth for the C2 co-candidate: insert a `Maximize Window` (or `Set Browser Size` / `Set Window State`) activity before the click, or change `AttachMode` on `NApplicationCard_1` from `ByInstance` to `SingleWindow` so the scope opens/sizes a window rather than reusing whatever state the existing Edge window has.
  - Why: `AttachMode=ByInstance` combined with no preceding sizing activity is the exact C2 fingerprint per the playbook — the runtime window can inherit an arbitrary size/position from the existing Edge instance. The playbook explicitly notes C1 and C2 are indistinguishable from the XAML alone for this scope shape.
  - Where: `Ofsb.xaml`, `NApplicationCard_1` (change `AttachMode`) and/or inside `Sequence_5` "Do" (insert a sizing activity before `NClick_1`).
  - Who: RPA developer
  - Source: `references/activity-packages/ui-automation/playbooks/click-coordinate-off-screen.md` § Resolution → "C2-specific fix — normalize the application window"

3. **Orchestrator** — Enable Healing Agent on the ERN release: set `AutopilotForRobots.HealingEnabled=true` in the release's **Process settings** for folder 'Shared'.
  - Why: `JobInputArguments` shows `AutopilotForRobots.HealingEnabled=false` at job time, so Healing did not engage on the faulted click (the per-activity `HealingAgentBehavior=SameAsCard` and scope `HealingAgentBehavior=Job` were moot under the process-level kill switch). The Healing Agent can relocate an off-screen coordinate on retry. Defense-in-depth only — it does not replace the InteractionMode fix.
  - Where: Orchestrator → folder 'Shared' → Processes → ERN → Edit → Process settings → enable Healing Agent.
  - Who: Admin or process owner
  - Source: `references/activity-packages/ui-automation/playbooks/click-coordinate-off-screen.md` § Resolution → "Enable Healing Agent on the process"

## Investigation summary

| # | Hypothesis | Confidence | Status | Root Cause? | Key Evidence | Resolution |
|---|------------|------------|--------|-------------|--------------|------------|
| H1 | NClick "Click 'Learn More About Editor'" faulted at cursor-injection because the runtime click coordinate fell outside the host's screen bounds (HardwareEvents path, browser scope, sub-cause C1 page-scroll mismatch with C2 window-not-normalized as co-candidate; C3 eliminated, C4 unsupported) | high | confirmed | yes | `triage-initial.json` (exception signature, stack frame, healing disabled); `H1-xaml.json` (`InteractionMode=HardwareEvents`, scope `AttachMode=ByInstance`, browser scope on datatables.net, zero preceding scroll/sizing siblings, element-center inside host's 4K screen) | Universal fix: switch click `InteractionMode` from `HardwareEvents` to `SameAsCard` (inherits scope's `DebuggerApi`) or `DebuggerApi` explicitly — covers C1 + C2 + C3 + C4; preventive: add `Scroll Into View` before click and/or normalize window, enable Healing Agent on ERN release |

---

Now executing Post-presentation actions in order.

**Action 1 — Apply universal fix: switch NClick_1 InteractionMode from HardwareEvents to SameAsCard (or DebuggerApi)**

Source: `references/activity-packages/ui-automation/playbooks/click-coordinate-off-screen.md` § Resolution → "Universal fix — switch the interaction mode"

```
File:      Ofsb.xaml
Activity:  Click "Learn More About Editor"  (IdRef = NClick_1)
Scope:     Use Application/Browser "Edge DataTables  Javascript table library"  (IdRef = NApplicationCard_1, AttachMode=ByInstance, scope InteractionMode=DebuggerApi)

Proposed edit on NClick_1 (pick one):
  InteractionMode="HardwareEvents"  ->  InteractionMode="SameAsCard"     (preferred — inherits scope's DebuggerApi)
  InteractionMode="HardwareEvents"  ->  InteractionMode="DebuggerApi"    (explicit)

Valid InteractionMode enum: SameAsCard, HardwareEvents, Simulate, DebuggerApi, WindowMessages.
Do NOT use "ChromiumAPI" — not a valid enum value; XAML will fail to deserialize.

Why this is safe:
  - The scope already runs InteractionMode=DebuggerApi (Chromium debugger / DOM-driven input).
    SameAsCard inherits that; DebuggerApi names it explicitly.
  - Both drive input through the browser's DOM, not the OS cursor,
    so the HRESULT 0x800402bd "outside of screen bounds" check no longer applies.
  - Covers both C1 (page-scroll mismatch) and C2 (window-not-normalized) without
    requiring runtime disambiguation.

What this does NOT fix:
  - The underlying authoring gap (no Scroll Into View, no window normalization,
    AttachMode=ByInstance). Consider the preventive fixes above if the workflow
    ever needs to stay on HardwareEvents.
```
