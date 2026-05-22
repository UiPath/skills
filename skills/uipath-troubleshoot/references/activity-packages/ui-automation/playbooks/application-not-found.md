---
confidence: high
---

# Application Not Found — Target Application Could Not Be Located

## Context

`ApplicationNotFoundException` is thrown by `NApplicationCard` (the runtime activity behind `Use Application`, `Use Browser`, and the standalone Application Card) when the target application cannot be located **and** the scope's `OpenMode` is set to `Never`. The exception is scope-level, not element-level — it fires before any inner `NClick` / `NTypeInto` / `NHover` runs, so the inner activities never get a chance to throw selector-level errors.

What this looks like:
- `ApplicationNotFoundException` (default message: `Could not find target application.`) in the job's error logs, sometimes with a closest-match diagnostic appended
- Stack frame originates inside `UiPath.UIAutomationNext.Activities.NApplicationCard` — `ProcessAppNotFoundAsync` → `GetAppNotFoundExceptionAsync`
- The faulted activity in XAML is a `Use Application` / `Use Browser` / `NApplicationCard` (or its alias), not an element-level activity
- The scope's `OpenMode` is `Never` in the XAML (`<NAppOpenMode>Never</NAppOpenMode>` or the matching `TargetApp` property)

What can cause it:
- App is closed and `OpenMode=Never` blocks the scope from launching it
- App is running but the application selector no longer matches (title drift, language change, version bump)
- App was running at job start but crashed or was closed between scopes
- Process is alive but has no visible window (minimized to tray, background-only, on another desktop)
- App is still launching (cold start) and the selector matches a splash screen window that disappears before the scope attaches

What this is NOT:
- If the app is missing AND `OpenMode != Never`, the scope throws `ApplicationOpenException` instead (launch was attempted and failed) — different playbook
- If the selector finds a window that belongs to a different process, the scope throws `WrongTargetApplicationException` — different playbook
- Element-level failures (`SelectorNotFoundException`, `UiElementNotFoundException`) inside the scope mean the scope attached fine — use the selector-failure playbooks

## Investigation

1. Locate the faulted activity in XAML — the `IdRef` in the exception's outer activity points at a `Use Application` / `Use Browser` / `NApplicationCard`, not at an inner element activity
2. Read the scope's `TargetApp` selector (and `TargetApp.OpenMode`) from XAML. Confirm `OpenMode=Never` — this is the gating condition for the exception. If `OpenMode != Never`, you're investigating the wrong playbook
3. Extract any closest-match diagnostic from the exception message — UIAutomationNext appends one via `GetSearchErrorMessageAsync` when `ShowClosestMatchesInSearchError` is on. It tells you which running window came closest to matching
4. Capture the application selector verbatim from XAML (decode `&amp;` → `&`, `&lt;` → `<`, etc.)
5. Check the job's environment context for the app's launch responsibility — does any earlier activity launch it (a previous scope with `OpenMode=Always`, an `NCheckAppState`, or an out-of-band launcher), or is the workflow assuming the app is already running?
6. If the app launches asynchronously (cold start, splash screen, license check), check whether an `NCheckAppState` or `Wait For Application` precedes the failing scope
7. Compare the closest-match diagnostic against the selector — if a window is reported with similar attributes, the selector has drifted (renaming, language, version). If no closest match, the app is genuinely absent

## Resolution

Walk the decision tree below. Each branch maps to a distinct fix; choose the first one whose evidence holds.

### Branch A — Workflow assumed the app was running but `OpenMode=Never` blocks the launch

Evidence: no earlier activity in the workflow launches the target app, the closest-match diagnostic reports no candidate window, and the job environment confirms the app was not pre-launched by an external trigger.

Fix: change the scope's `OpenMode` to `IfNotOpen` (preferred — only launches when needed) or `Always`, and set `FileName` / `Arguments` so the scope can launch the app itself. This is the most common root cause.

### Branch B — Selector drift on a running app (title / version / language)

Evidence: closest-match diagnostic reports a window from the expected process with similar but not identical attributes — title contains a new version string, the language changed, a sub-feature renamed the main window.

Fix: relax the application selector — use wildcards for volatile parts (`title='Invoice Portal*'`), prefer stable attributes (`app`, `automationid`, `cls`) over `title`, or migrate the scope to an Object Repository application target so the selector is centrally maintained.

### Branch C — App crashed mid-flow

Evidence: a previous scope or activity in the same job successfully interacted with the same app (look for earlier `NClick` / `NTypeInto` / `NCheckAppState` against the same selector). The app died between scopes.

Fix: add an `NCheckAppState` (Element Exists / App State) before the failing scope to detect that the app is gone, plus retry logic or a guarded re-launch. Investigate the crash separately — repeated `ApplicationNotFoundException` after this branch indicates an underlying app stability problem, not a workflow problem.

### Branch D — Process exists but no visible window

Evidence: the closest-match diagnostic returns nothing matching the selector, but the host process is known to be running (operator confirmation, prior log entries, telemetry). Common with apps minimized to system tray, second-monitor windows on an unattended robot, or background-only services.

Fix: ensure the app's main window is visible before the scope — call an OS-level activity to restore from tray, switch desktops, or pin the window. If the workflow is unattended, configure the app launcher to start visible (not minimized).

### Branch E — Cold-start race against a splash window

Evidence: the failure is intermittent and clusters with first-job-after-machine-restart runs. The closest-match diagnostic reports a window with `app='loader.exe'` or similar that doesn't match the main app's selector.

Fix: precede the scope with `NCheckAppState` waiting for the main-window selector (not the splash), or set the scope's `WaitForReady` to `Complete`. If the app's splash regularly outlives the scope's default timeout, raise the scope timeout.

## Post-presentation actions

This resolution path is **interactive** — every recommended fix above ends in a file edit (XAML property change, adding a new activity before the scope, adjusting timeouts). The orchestrator MUST call `AskUserQuestion` at the end of the troubleshooting to (a) print the exact property/file/line to be modified and the before → after value, and (b) ask the user whether to apply the fix. Do not write to the user's source files until that question is answered with explicit approval.

Rules the agent MUST follow:

1. **Sharing a file path is not approval.** If you previously asked the user for the project source location (e.g., "point me at the failing project") and they responded with a path, that consent covers reading the source only — not editing it. Issue a separate `AskUserQuestion` before any edit.
2. **Never bundle "gather input" with "apply fix" in a single option.** Any option that contains phrasing like "I'll … apply / edit / write the change" alongside an input request must be split into two steps: gather the input, then surface the specific diff and confirm separately.
3. **Surface the diff before asking.** The apply-fix question must include the file path, the activity `IdRef` or line number, the current value, and the proposed value. Vague approvals ("fix the scope") are not enough — show the concrete edit.
4. **One question per fix, not one for the whole branch.** If multiple files need editing (e.g., XAML plus an Object Repository `.content` file mirror), list every file in the question or ask file-by-file. Do not silently propagate the same substitution to side-channel files.
5. The presenter must emit a `## Post-presentation actions` block in its output declaring this interactive step; the orchestrator must execute it before closing the investigation. Do not collapse this into a generic "fix the OpenMode" recommendation — the apply-fix prompt is part of the documented resolution.
6. **If you cannot obtain interactive approval, do not edit.** When the approval prompt is unavailable or errors in the current environment, fall back to presenting the diff as a recommendation and stop — leave the apply step to the user. Never write to a source file without explicit approval, even when the approval mechanism is unavailable. A recommendation-only close is always acceptable; a silent edit is not.
