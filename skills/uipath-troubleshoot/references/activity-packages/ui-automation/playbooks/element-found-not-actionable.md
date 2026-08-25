---
confidence: medium
---

# Element Found But Not Actionable — Stale, Not Visible, or Blocked

## Context

The selector resolved (or the search reached the right place), but the activity could not act on the element: it went invalid between find and action, it is not visible, or a dialog is blocking access to it. This is distinct from a genuine selector mismatch and from a disabled element.

What this looks like — one of these signatures:
- `The UI element is invalid. Make sure the target application is open and the element is on the screen.` (`InvalidNodeException`)
- `The selected UI element seems to have become invalid. Please make sure the UI element is still on the screen.` (`UiNodeUninitializedElementException`)
- `Cannot get the screen rectangle of this UI node. A possible reason might be that the element is not visible.` — the element exists but has no usable on-screen rectangle (minimized, collapsed, scrolled out, zero-size).
- `The element was found but its visibility was not as expected (Visible). ...` (`TargetFoundButNotVisibleException`) — the target's configured visibility didn't match at runtime.
- `The element was not found, and it might be due to the dialog blocking the browser.` (`TargetNotFoundBrowserBlockedException`) — a modal/JS dialog blocked the browser, so the element couldn't be reached.

What can cause it:
- The window closed, navigated, or re-rendered between locating the element and acting on it (the element handle went stale). Usually an upstream step left the page changing under the activity, or a timing gap.
- The element is present but hidden/collapsed/scrolled away, so it has no actionable rectangle.
- The target was authored expecting a different visibility state than it has at runtime.
- A browser dialog (alert/confirm/print/auth) is up, freezing the page so the element cannot be located or acted on.

What to look for:
- Confirm the exception is one of the above — the element was located/expected, so this is NOT a plain `selector-failure-*` (genuine not-found) and NOT `disabled-element` (target found but disabled).
- The "outside of screen bounds" coordinate-injection failure on Hardware Events is a different signature, covered by its own dedicated playbook — not this one.
- Check whether the page/window was changing, hidden, or had a dialog open at action time.

## Investigation

1. From the failed job, capture the exact message and the faulting activity + workflow.
2. Determine which state applies: stale (invalid/uninitialized), not-visible (no rectangle / visibility mismatch), or browser-blocked (dialog).
3. For stale elements, look at what runs just before: an upstream click/navigation that keeps the page reloading, or a too-short gap before the action.
4. For not-visible, check whether the element is hidden until a prior step reveals it (expand/scroll/tab switch) and whether the target's expected visibility matches reality.
5. For browser-blocked, check whether a JavaScript dialog or native browser prompt appears around that step.

## Resolution

- **Stale (invalid/uninitialized):** the element changed under the activity. Re-establish the element right before acting — add a `Check App State` (Element Exists) gate so the action runs only once the element is present and stable; and trace the upstream step that keeps the page changing and fix that.
- **Not visible / no rectangle:** make the element actually visible before acting — bring it into view via the legitimate flow (expand the section, switch the tab, scroll), or correct the target's expected visibility if it was authored wrong. Do not work around it by acting on a hidden element.
- **Browser blocked by a dialog:** the dialog is the originating fault. Handle it deterministically — dismiss/accept the dialog as a real step in the flow (or prevent it) before the activity. 

Do not harden the selector (wildcards, switching attributes) for this class — the element was found/expected; selector changes don't address staleness, visibility, or a blocking dialog.
