---
confidence: high
---

# Identified Element Belongs to a Different Application

## Context

The activity resolved an element, but that element does not belong to the application/browser the enclosing scope is bound to. The runtime rejects it rather than acting on an element outside the target application.

What this looks like:
- Exception class: `WrongTargetApplicationException`
- Friendly message: `The identified element does not belong to the target application/browser.`
- The scope (`Use Application/Browser`) attached successfully, but the element acted on (often the focused element or active window) is owned by a different process.

What can cause it:
- A different window came to the foreground between scope attach and the action (a notification, a popup from another app, the OS stealing focus), and the activity resolves against whatever is focused/active.
- The scope's application selector is permissive enough to attach to one app while the element the activity finds lives in another (similar titles across apps).
- Two instances/processes present similar windows and the activity reached the wrong one.
- On multi-monitor / multi-session machines, a window from another app overlaps or is focused at action time.

What to look for:
- Confirm the exception is `WrongTargetApplicationException` (the element WAS identified — this is not `NodeNotFound`, and the scope did attach — this is not `ApplicationNotFound` / `ApplicationOpenException`).
- Identify which activity faulted and whether it operates on the focused element / active window.
- Read the scope's application selector and how specific it is.

## Investigation

1. From the failed job, capture the exception class, the faulting activity, and the enclosing scope.
2. Read the scope's `Target application` selector — note whether it is specific to the intended process or loose enough to match another app's window.
3. Determine whether the failing activity acts on the focused element / active window (these are most exposed to a foreground change at action time).
4. Check what else runs on the robot at that moment: a popup, notification, or another automation that could steal focus right before the action.
5. Confirm the intended application was actually in the foreground/owning the element when the activity ran.

## Resolution

- **Foreground/focus stolen by another app:** the originating fault is that the wrong window was active. Trace and remove the focus thief, or ensure the target window is foreground before the action (bring the target to front as part of the legitimate flow, not as a mask). If a popup from another app intrudes, dismiss it deterministically.
- **Loose application selector:** tighten the scope's application selector to the intended process (use the process/`app` attribute, not just title), or attach via an Object Repository application target so the binding is unambiguous.
- **Multiple instances:** make the scope attach to the specific intended instance rather than any matching window.

Do not relax the activity to "act on whatever is focused" to make the error disappear — that hides the real foreground/selector problem and lets the robot act on the wrong application.
