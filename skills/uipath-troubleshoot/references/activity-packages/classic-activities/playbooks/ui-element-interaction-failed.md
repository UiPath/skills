---
confidence: medium
---

# UI Element Interaction Failed — Found but Action Did Not Succeed

## Context

A classic UI activity located its target element but could not perform the action on it, throwing
`ElementOperationException`. Applies to `Click`, `Type Into`, `Send Hotkey`, and `Take Screenshot`.
This is distinct from "element not found" — the selector matched, but the operation against the
element failed.

What this looks like:
- `ElementOperationException` (the selector resolved, then the click/type/screenshot operation
  failed)
- The activity did not run for its full timeout — it found the element quickly, then failed on the
  action

What can cause it:
- The element is disabled / read-only, so it cannot receive the click or text
- The element is obscured by another window, a popup, a tooltip, or an overlay at the moment of the
  action
- The element (or its coordinate) is off-screen or scrolled out of view for hardware-event input
- Focus was lost between locating the element and acting on it (another app stole focus, a dialog
  appeared)
- The chosen input method does not work for this element/technology (e.g. background/window-message
  input on an element that only responds to hardware events, or vice versa)
- `Take Screenshot`: the target window could not be brought to the foreground or rendered

What to look for:
- Whether the element is enabled and interactable at the moment of the action (not just present)
- Whether a popup/overlay/another window covers the element
- The input mode configured on the activity (simulate / window messages / hardware events) vs. the
  target technology
- Whether focus is stable while the workflow runs (no other automation or user interaction competing)

## Investigation

1. Confirm from logs the failure is an interaction failure (element resolved) rather than a
   not-found/timeout.
2. Reproduce and observe the target at the moment of the action — is it enabled, fully visible, and
   on screen?
3. Check for overlays, modal dialogs, or another window covering or stealing focus from the target.
4. Review the activity's input method against the application technology; try the alternative input
   method to see if the action succeeds.
5. For `Take Screenshot`, verify the target window can be brought to the foreground (not minimized,
   not on a disconnected session).

## Resolution

- **If the element is disabled:** fix the upstream step so the element is enabled before the action
  (complete the prerequisite that activates it); do not force input on a disabled control.
- **If an overlay/dialog/another window covers or steals focus:** dismiss/handle the blocker in the
  workflow before the action.
- **If the input method is wrong for the technology:** switch the activity's input method to one the
  target supports.
- **If the element is off-screen:** ensure it is scrolled/brought into view before acting (or use an
  input method that does not require an on-screen coordinate).
- **If `Take Screenshot` cannot foreground the window:** run in an interactive session and ensure the
  window is restorable.
