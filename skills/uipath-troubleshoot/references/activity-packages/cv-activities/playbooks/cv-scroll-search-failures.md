---
confidence: medium
---

# CV scroll-search failures (scrolled entire screen, scroll not reaching pane, silent scroll skip)

## Context

Scroll-search is the mode where a CV find activity (`ScrollDirection != None`) scrolls the target while re-analyzing, searching for the descriptor off-screen. One shared mechanism backs all the find activities; its terminal "covered the whole screen, no match" condition has its own hardcoded (non-localized) message. The same mechanism also fails in three quieter ways: it can throw a raw driver exception while sending scroll input, it can degrade silently to plain in-place retries when the scope root isn't a CV driver element, and (Get Text only) it can fault during scrollable OCR extraction.

What this looks like — the terminal scroll-exhausted message, verbatim:

- `Scrolled the entire screen, but element was not found` — thrown as `UiPath.CV.ElementNotFoundException`. Hardcoded English, no resource key, so it does **not** localize — match the literal regardless of Studio language. Trap: this is a different message from the plain not-found error (`cv-element-not-found.md`); the word `Scrolled` is the discriminator. If you only see a generic not-found message with no `Scrolled`, scroll-search was never engaged — that is a different playbook.

What activities can produce this:
- **CV Click** (`CvClickWithDescriptor`), **CV Type Into** (`CvTypeIntoWithDescriptor`), **CV Get Text** (`CvGetTextWithDescriptor`) — fault with the `Scrolled the entire screen...` exception, or with a raw driver exception during scroll input.
- **CV Element Exists** (`CvElementExistsWithDescriptor`) — catches `ElementNotFoundException` and converts it to `Result = false`. The `Scrolled the entire screen...` message is **swallowed** — it never surfaces. ElementExists returning `false` after a configured scroll search is the only symptom; there is no exception to match.

`ScrollDirection`, `NumberOfScrolls` (default 2), and `DelayScreenshotAfterScroll` (default 250 ms) are arguments on the activity. `ScrollOffset` is a property on the enclosing **CV Screen Scope** (`CVScope`), not on the activity.

What can cause it:
- **Element genuinely absent from the scrollable content.** It is not anywhere in the scrollable region for any scroll position. The mechanism scrolls until two consecutive screenshots produce an identical CV element set (compared via `SequenceEqual`), resets once (see below), confirms unchanged again, then throws. Genuine absence is the default conclusion only after the input-delivery and direction causes below are ruled out.
- **Wrong `ScrollDirection` for the layout.** Scrolling vertically when the element is reached by horizontal scroll (or vice versa). The covered axis never reveals the element.
- **Scroll input never reaches the scrollable pane.** The scroll point is computed from the scope center plus `CVScope.ScrollOffset`. If the center+offset lands on a non-scrollable region (a toolbar, a margin, a sibling pane), the mouse-wheel events go nowhere — the screen never changes, so the mechanism declares "entire screen covered" almost immediately. Common with an embedded scroll pane that is not under the scope center.
- **`NumberOfScrolls` too large.** Each pass scrolls `NumberOfScrolls` notches before re-screenshotting. Too many notches jump the element completely past the viewport between screenshots, so it is never captured in a frame.
- **`DelayScreenshotAfterScroll` too short for the app.** The screenshot is taken before the app finishes repainting after the scroll; the analyzed frame is stale/blank. Less common; suspect on slow or animated UIs.

What to look for:
- The activity has `ScrollDirection` set to something other than `None`. If it is `None`, scroll-search is not engaged — route to `cv-element-not-found.md`.
- Whether the failure is near-instant (screen never changed → input not reaching the pane / wrong scroll point) vs. after a visible scroll sweep (covered the area → genuine absence or wrong direction).

> **Different cause, do not apply this playbook:**
> - Generic not-found with no `Scrolled` in the message, or `ScrollDirection = None` — the descriptor never matched within timeout without scrolling. Use [cv-element-not-found.md](./cv-element-not-found.md).
> - Cell-targeting messages (`Could not find table...`, `Invalid row number...`, `Table only contains...`) — use [cv-cell-targeting-failures.md](./cv-cell-targeting-failures.md).
> - CV Get Text returns empty/stale/wrong text but the activity **succeeded** (no fault) — use [cv-get-text-empty-or-wrong-result.md](./cv-get-text-empty-or-wrong-result.md).
> - `Invalid Descriptor` / `Target must be set` — descriptor is malformed before any find runs. Use [cv-invalid-descriptor.md](./cv-invalid-descriptor.md).
> - 401/403/429/5xx, payload/word-limit, or network errors during analysis — the CV server failed, not scrolling. Use [cv-server-auth-throttling-network.md](./cv-server-auth-throttling-network.md).
> - CV Screen Scope itself failed to set up (target window, server/OCR config) — use [cv-scope-setup-failures.md](./cv-scope-setup-failures.md).
> - ElementExists false-negative/positive traps unrelated to scroll, or `InRegion` bypass and `ContinueOnError` swallow patterns — use [cv-silent-failures-and-false-results.md](./cv-silent-failures-and-false-results.md).

## Investigation

1. **Confirm scroll-search was engaged.** Read the faulted activity's `ScrollDirection` from XAML. If `None`, stop — this is not a scroll failure; use `cv-element-not-found.md`. If non-`None`, continue.
2. **Classify by the observable evidence** and route to the matching Resolution branch:
   - Fault message contains `Scrolled the entire screen, but element was not found` → Branch A.
   - A faulted CV activity with **no** CV-level message — a raw driver/COM exception (or `NullReferenceException`) whose stack passes through scroll input (`WriteText` / `MouseScroll`) → Branch B.
   - No scroll motion observed at all and the failure is a plain not-found despite `ScrollDirection != None` — scroll-search degraded to in-place retries → Branch C.
   - CV Get Text faulting from scrollable content extraction (`Scroll = true` + OCR method) with an externally-originated exception → Branch D.
   - CV Element Exists returns `Result = false` after a configured scroll search, no exception → Branch E.
3. **Read the scroll knobs.** Capture `ScrollDirection`, `NumberOfScrolls`, `DelayScreenshotAfterScroll` from the activity and `ScrollOffset` from the enclosing CV Screen Scope. These feed the Branch A decision.
4. **Establish whether the screen changed during the search.** A near-instant `Scrolled the entire screen...` (no visible scroll motion in any screenshot/recording) means the screen content never changed → input not reaching the pane. A failure after a visible top-to-bottom sweep means the area was genuinely covered.

## Resolution

Walk the branches in order; pick the first whose evidence holds. Branch A is itself a decision tree because one message masks several root causes.

### Branch A — `Scrolled the entire screen, but element was not found`

The mechanism declares the scrollable area fully covered. Sub-cause keyed on observable evidence:

- **A1 — Screen never changed during the search (input not reaching the pane).** Evidence: the failure is near-instant; no scroll motion appears in any captured frame; the scrollable content is an embedded pane not centered under the scope. **Cause.** Scroll point = scope center + `CVScope.ScrollOffset` landed on a non-scrollable region. **Fix:** set/tune `CVScope.ScrollOffset` so the computed point falls inside the scrollable pane, or tighten the CV Screen Scope so its center sits over the pane. Do **not** raise `NumberOfScrolls` here — the wheel events are not landing at all.
- **A2 — Wrong axis.** Evidence: the element is reached by the opposite scroll axis in the live app (horizontal vs. vertical). **Fix:** set `ScrollDirection` to the axis that actually reveals the element.
- **A3 — Element skipped between screenshots.** Evidence: a visible scroll sweep occurred, the element is known to exist, and `NumberOfScrolls` is high (well above the default 2). **Cause.** Each pass scrolls too far; the element flashes past the viewport between captures. **Fix:** lower `NumberOfScrolls` (start at the default 2). If the app repaints slowly, also raise `DelayScreenshotAfterScroll` above the 250 ms default so each frame is fully rendered before analysis.
- **A4 — Element genuinely absent.** Evidence: a full visible sweep occurred, `ScrollOffset`/direction are correct, `NumberOfScrolls`/`DelayScreenshotAfterScroll` are sane, and the element is not present at any scroll position when checked manually. **Cause.** The element is not in the scrollable content (filtered out, wrong record set, not yet loaded). **Fix:** this is not a scroll-tuning problem — verify upstream data/state that should have produced the element. Do not keep adjusting scroll knobs.

> **Reset side effect — confirm before recommending a knob change.** When the screen stops changing, the mechanism resets scroll position once before giving up: it **types `Ctrl+Home` / `Ctrl+End` into the target application** (and may issue up to 500 reverse-scroll notches). On apps where `Ctrl+Home` / `Ctrl+End` do something other than scroll-to-edge (a custom editor, a shortcut binding), this is a real, observable side effect of the failing run — note it to the user. It is not the cause of the not-found, but it explains unexpected app state after the fault.

### Branch B — Scroll input simulation failure (raw driver exception)

Evidence: the CV activity faulted with a driver/COM exception (type depends on the UI driver) or a `NullReferenceException`, and the stack passes through scroll input — the reset `WriteText` (`Ctrl+Home`/`Ctrl+End`) or `MouseScroll`. There is **no** CV-level message; the raw driver exception propagates. This is thrown outside the find try/catch and is not an `ElementNotFoundException`, so the activity faults rather than retrying.

**Cause.** The driver could not deliver synthesized scroll/keyboard input to the target, or the top-parent element had no resolvable absolute position (null `TopParent`) when the scroll point was computed.

**Fix:** confirm the target window is foreground, visible, and not blocked (locked session, secure desktop, UAC prompt, RDP/console mismatch) — the same input-delivery prerequisites as [cv-action-failed-after-find.md](./cv-action-failed-after-find.md). If the `NullReferenceException` recurs on a scope whose target window resolution is unstable, treat it as a scope-setup problem ([cv-scope-setup-failures.md](./cv-scope-setup-failures.md)). Do not retry blindly.

### Branch C — Scroll silently skipped (scope root is not a CV driver element)

Evidence: `ScrollDirection != None`, but **no scroll motion ever occurs**, and the activity ends in a plain not-found at timeout. Common in non-standard sessions — image-based or remote/test sessions where the scope root is not a live CV driver element.

**Cause.** The scroll routine returns immediately when the scope root is not a CV driver element (or when the direction resolves to `None`). Scroll-search degenerates into plain in-place retries until `TimeoutMS`, then reports not found. The element is never searched off-screen.

**Fix:** scroll-search is not available against this scope root. Either run against a live (driver-backed) target window so scrolling works, or stop relying on scroll-search and ensure the element is on-screen before the find (scroll the app via a separate step). Confirm `ScrollDirection` is genuinely non-`None` and not being overridden to `None` at runtime. Do **not** tune `NumberOfScrolls`/`ScrollOffset` — they are never read on this path.

### Branch D — Scrollable content extraction failure (CV Get Text, `Scroll = true` + OCR)

Evidence: `CvGetTextWithDescriptor` with `Scroll = true` and an OCR method type, faulting during the scroll-capture/stitch phase with an exception that originates outside the CV package.

**Cause.** Scrollable extraction is delegated to an external extraction service. Two distinct failure points: (1) the service throws during scroll-capture/stitch and the exception propagates verbatim; (2) the service is resolved at activity construction — a missing registration faults at instantiation, before find. Also note: this extraction phase receives the raw workflow cancellation token, **not** the `TimeoutMS`-bound token — so `TimeoutMS` does **not** bound it. A hang here will not time out via `TimeoutMS`; rule out "raise TimeoutMS" as a fix.

**Fix:** the failing code is in the external extraction/UIAutomationNext service, not the CV activity. Confirm the UIAutomationNext/extraction dependency is present and the package versions are compatible; capture the propagated exception text for the underlying service. If the activity faults at instantiation (before any find), it is a missing service registration — a packaging/dependency problem, not a configuration one.

### Branch E — CV Element Exists returns `false` after a scroll search (swallowed)

Evidence: `CvElementExistsWithDescriptor` with `ScrollDirection != None` returns `Result = false`; no exception in logs.

**Cause.** ElementExists catches `ElementNotFoundException` — including the `Scrolled the entire screen...` case — and converts it to `Result = false`. You cannot distinguish "genuinely absent" from "wrong direction / scroll point / skipped" from the boolean alone; the diagnostic message is gone.

**Fix:** the boolean is not enough evidence to conclude the element is absent. To diagnose, temporarily reproduce the same descriptor and `ScrollDirection`/`ScrollOffset`/`NumberOfScrolls` with a CV Click or CV Get Text (which surface the exception), then apply Branch A. Do not assert "element does not exist" from a `false` ElementExists result when scroll-search is configured — the silent swallow makes a false-negative indistinguishable from a true negative.

## Post-presentation actions

Branches A, B, C, and E may end in edits to the user's workflow files (changing `ScrollDirection` / `NumberOfScrolls` / `DelayScreenshotAfterScroll` on the activity, `ScrollOffset` on the CV Screen Scope, or restructuring the scope). When a recommended fix edits a source file, the resolution is **interactive**. You MUST call `AskUserQuestion` before any edit (approval gate).

1. **Sharing a file path is not approval.** A path the user gave for reading the project does not authorize editing it. Issue a separate `AskUserQuestion` before any edit.
2. **Never bundle "gather input" with "apply fix" in one option.** Split into two steps: gather input, then surface the concrete diff and confirm separately.
3. **Surface the diff before asking.** Include the file path, the activity `IdRef` (or CV Screen Scope `IdRef`), the property name (`ScrollDirection` / `NumberOfScrolls` / `DelayScreenshotAfterScroll` / `ScrollOffset`), the current value, and the proposed value.
4. **One question per file/fix.** If both the activity and its enclosing CV Screen Scope change, list both files or ask file-by-file.
5. **If interactive approval is unavailable or errors, do not edit.** Present the diff as a recommendation and stop. A recommendation-only close is acceptable; a silent edit is never acceptable.

Branch A4 (genuine absence) and Branch D (external extraction/dependency) prescribe no source edit — present the finding without an apply-fix prompt.

## Stop / escalate

If `ScrollDirection` is non-`None`, the scroll point (`CVScope.ScrollOffset`) lands inside the scrollable pane, the direction matches the layout, `NumberOfScrolls`/`DelayScreenshotAfterScroll` are at sane values, the screen visibly changes through a full sweep, and the element still is not captured — the element is genuinely absent from the scrollable content (Branch A4). Stop tuning scroll parameters and investigate the upstream data/state that should have produced it. If Branch B's driver exception or Branch D's external extraction failure persists after the input-delivery and dependency checks above, the fault is outside the CV activity — escalate (UI driver, UIAutomationNext/extraction package, or target-application stability) rather than continue under this playbook.
