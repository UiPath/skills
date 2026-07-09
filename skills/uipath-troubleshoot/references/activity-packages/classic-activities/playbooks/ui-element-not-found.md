---
confidence: medium
---

# UI Element Not Found — Classic UI Activity

## Context

A classic UI Automation activity could not locate its target element within the timeout. Applies to
`Click`, `Type Into`, `Send Hotkey`, `Take Screenshot`, `Wait UI Element Appear`, `Attach Browser`
(Browser Scope), `Attach Window` (Window Scope), and `Close Tab`.

What this looks like:
- `SelectorNotFoundException`, or an error message such as "Cannot find the UI element corresponding
  to this selector"
- The activity ran roughly for its full timeout before failing
- The failing activity carries a `Selector` / `Target.Selector` property

What can cause it:
- The application or window the selector points to is not open, or is on a different
  screen/session/desktop than the robot
- Selector drift — the application changed (a UI update, a different version, a different language)
  so one or more selector attributes no longer match
- The selector depends on dynamic attributes (auto-generated `id`, `idx`, title text with a counter)
  that differ at run time
- The activity is inside the wrong scope — an `Attach Browser`/`Attach Window` (or `Open ...`) that
  attached to a different window than the inner selector expects
- The element exists but only appears after a delay, and the activity's timeout is shorter than that
  delay
- An earlier step in the workflow failed silently (navigation didn't happen, login wasn't completed)
  so the expected screen is not showing

What to look for:
- The exact selector on the failing activity (from the XAML or the job's verbose logs)
- Whether the target application was actually open and focused at the moment of failure
- Whether the failure is consistent or intermittent (intermittent → timing/readiness; consistent →
  selector or scope)

## Investigation

1. Identify the failing activity and read its full selector from the XAML or the verbose execution
   log.
2. Confirm the target application/window was open and reachable when the activity ran — check earlier
   steps in the same execution that should have launched or navigated to it.
3. Compare the selector against the live application (UI Explorer / Selector Editor against the
   running app). Identify which attribute(s) no longer match.
4. Check whether any matched attribute looks dynamic (numeric suffixes, GUIDs, full title strings)
   that would differ between runs.
5. If the activity is inside a scope (`Attach Browser`/`Attach Window`/`Open ...`), verify that scope
   attached to the intended window, not a different instance or a stale handle.
6. Re-check whether the element appears only after a delay relative to the activity's timeout.

## Resolution

- **If the application/window was not open or not on the right screen:** fix the upstream step that
  should have opened or navigated to it; do not point the activity at a window that isn't there.
- **If a selector attribute no longer matches (selector drift):** repair the selector to match the
  current application, preferring stable attributes over volatile ones.
- **If the selector relies on dynamic attributes:** replace them with stable attributes or wildcards
  so the selector survives across runs.
- **If the scope attached to the wrong window:** correct the scope's selector so it attaches to the
  intended window; the inner selector is fine.
- **If the element appears only after a delay:** wait for the real readiness signal (the element/the
  expected state) rather than padding the timeout blindly, and find why it is slow.
