---
confidence: medium
---

# CV Get Text returns empty, stale, or wrong text (OCR mode and clipboard mode)

## Context

The activity **completed successfully** (no fault, `Result` is set) but the extracted text is empty, partial, outdated, or wrong. Symptom-driven: "the result is empty / null / old text but the activity did not throw." This is the defining signature — **CV Get Text** swallows the failures that produce it, so there is no exception to match on for most branches.

What activities can produce this:
- **CV Get Text** (`CvGetTextWithDescriptor`, namespace `UiPath.CV.Activities`) — the only activity here. Extracts text from a CV-detected element via OCR (`MethodType = OCR`) or via click + select + copy + clipboard read (`MethodType = ClipboardRow` / `ClipboardAll`).

What this looks like:
- `Result` is `""` / `null` / `Nothing` while every other activity in the run succeeded.
- `Result` holds text from a **previous** screen state (stale), not the screen as it is now.
- `Result` is partial — a few words missing, or words half-clipped at the edge of the read region.
- No error message in the logs for any of the above (silent). The two exception branches below are the exceptions.
- Design-time warning "The Select methods only work on editable text" — clipboard mode configured on a non-editable target.

What can cause it (ordered most → least common):
- **OCR scrape failed silently.** `MethodType = OCR`. The OCR engine threw; the failure is caught, traced, and swallowed, producing **zero** OCR words for the region. The activity then composes text from an empty word set → `Result = ""`. No fault is raised.
- **Stale OCR cache (`RefreshBefore = false`).** `MethodType = OCR`. With `RefreshBefore` unchecked, the activity reuses the OCR analysis cached from a **previous** screen state instead of re-scraping. If the screen changed since that analysis, the returned text is outdated. (When `RefreshBefore = true`, the activity issues a fresh OCR refresh of the session before reading.)
- **Region overlap clipping.** `MethodType = OCR`. Text is composed only from OCR words whose region **overlaps** the matched rectangle. Words sitting half-outside the matched area are dropped → partial result.
- **OCR language / accents mismatch.** `MethodType = OCR`. Engine recognised the glyphs as different characters (accents, non-Latin script, wrong configured language) → wrong text, not empty.
- **Clipboard read returned nothing (silent).** `MethodType = ClipboardRow` / `ClipboardAll`. The select-and-copy sequence relies on the target being **keyboard-selectable editable text**. The click/select/copy keystrokes and the clipboard read all swallow their failures — clicks return `false` and that value is ignored; the clipboard read has a **100ms** timeout and any exception (including timeout, or another process holding/overwriting the clipboard) is caught and returns `null`. Result: empty/wrong text with no error.

What to look for:
- `MethodType` of the activity — it cleanly splits the OCR branches from the clipboard branches. Read it from the XAML / activity properties before choosing a branch.
- `RefreshBefore` value (OCR branches only).
- The CV Screen Scope's `OCREngine` configuration (OCR branches only).
- Whether the target is genuinely selectable editable text (clipboard branches only) — a label, image caption, or read-only canvas is **not**.

> **Different cause, do not apply this playbook:**
> - The activity **threw** `ElementNotFoundException` and the descriptor never matched within `TimeoutMS` — the element was not found at all, not a text-extraction problem. Use [cv-element-not-found.md](./cv-element-not-found.md).
> - The activity **threw** with a server/OCR error message built by `ToErrorMessageWithCode()` (carries an HTTP/error code, mentions auth, an unreachable server, a 429, or an OCR word limit) — the CV/OCR server call itself failed and surfaced. Use [cv-server-auth-throttling-network.md](./cv-server-auth-throttling-network.md).
> - The CV Screen Scope itself faulted on setup, or no `OCREngine` is configured and the design-time error `Server or OCR engine is required.` appears — Use [cv-scope-setup-failures.md](./cv-scope-setup-failures.md).
> - The activity **threw** `Scrolled the entire screen, but element was not found` (`Scroll = true` + OCR, area never matched) — that is a scroll-search exhaustion, not an extraction-of-found-content problem. Use [cv-scroll-search-failures.md](./cv-scroll-search-failures.md).
> - The result is correct text but a downstream **CV Click / CV Type Into** then acted on the wrong place — Use [cv-action-failed-after-find.md](./cv-action-failed-after-find.md).
> - The target is a table cell and the row/column was misidentified — Use [cv-cell-targeting-failures.md](./cv-cell-targeting-failures.md).

## Investigation

1. **Confirm the no-fault signature.** Verify the activity did **not** throw — `Result` is set but empty/stale/partial/wrong, and the run continued. If an exception was thrown, route to the sibling playbook matching its message/type (see the block above) — do not proceed here. The two exception branches below (Branch E, Branch F) are the only in-playbook faults.
2. **Read `MethodType`** from the faulted activity's properties in XAML. `OCR` → Branches A–D. `ClipboardRow` / `ClipboardAll` → Branch E and Branch G.
3. **For OCR**, read `RefreshBefore` and the parent CV Screen Scope's `OCREngine`. Capture the screen state at the time of the run (screenshot / video / logged region if available) and compare against the expected text.
4. **For clipboard**, identify what the target actually is: selectable editable text vs a label / image / read-only region. Check whether another process or the robot itself touches the clipboard around the same time.
5. **For partial OCR results**, compare the matched `OutRegion` rectangle against the position of the missing words — words outside the rectangle are expected to be dropped.

## Resolution

Choose the first branch whose evidence holds. Do not apply a fix the evidence does not support — e.g. do not change `OCREngine` when the result is a clipboard-mode empty (no OCR runs in clipboard mode).

### Branch A — OCR scrape failed silently (empty result, `MethodType = OCR`)

Evidence: `MethodType = OCR`, `Result` is empty, the screen visibly contains text in the matched region, and there is **no** server error message in the logs (a real server error would route to [cv-server-auth-throttling-network.md](./cv-server-auth-throttling-network.md)). The OCR engine exception is swallowed, so absence of a message does not mean OCR succeeded.

Fix: verify the CV Screen Scope's `OCREngine` is configured and reachable (endpoint/key for a server engine, or the local engine's dependencies present). Re-run with OCR engine tracing if available to surface the swallowed exception. If the engine is healthy but still returns nothing, the screen may be too dense (word limit) — that surfaces as a server error, route accordingly.

### Branch B — Stale text from a cached OCR analysis (`RefreshBefore = false`)

Evidence: `MethodType = OCR`, `RefreshBefore = false` (or unchecked), `Result` matches the screen as it was **before** the most recent screen change rather than the current state. Common after a navigation/click earlier in the workflow changed the screen without a scope refresh.

Fix: set `RefreshBefore = true` on the activity so it re-scrapes OCR against the current screen before reading. This is the single most common stale-text cause.

### Branch C — Partial result, words clipped at the region edge (`MethodType = OCR`)

Evidence: `MethodType = OCR`, `Result` contains most but not all expected text, and the missing words sit at or beyond the boundary of the matched `OutRegion` rectangle. Only OCR words overlapping the matched area are composed into the result.

Fix: broaden the matched area so the full text falls inside it — adjust the descriptor / `InRegion` to cover the whole text block, or target a container element rather than a tight sub-element. Do not raise `TimeoutMS` — timeout is not the issue.

### Branch D — Wrong characters / accents (`MethodType = OCR`)

Evidence: `MethodType = OCR`, `Result` is non-empty but characters are wrong — accents stripped or mangled, non-Latin script garbled.

Fix: configure the OCR engine in the CV Screen Scope for the correct language/character set. This is an OCR-engine configuration change, not a CV Get Text property change.

### Branch E — Clipboard mode returned empty/wrong, no fault (`MethodType = ClipboardRow` / `ClipboardAll`)

Evidence: `MethodType = ClipboardRow` or `ClipboardAll`, `Result` is empty/wrong, **no** exception thrown. The click, the select keystrokes, and the clipboard read each swallow their own failures (clicks return `false`, ignored; clipboard read times out at 100ms and returns `null` on any exception).

Fix — decision by what the target is:
- **Target is not selectable editable text** (a label, image caption, static/read-only field, canvas): clipboard mode cannot work — the select-all/copy sequence (`End` / `Shift+Home`, or `Ctrl+End` / `Ctrl+Shift+Home`) only selects in keyboard-editable text. Switch `MethodType` to `OCR`. This is the most common clipboard-mode failure.
- **Another process touches the clipboard** (a clipboard manager, a concurrent robot, the operator) around the same time: isolate the run so nothing else writes the clipboard during the activity.
- **The read raced the 100ms clipboard timeout** on a slow machine: the read window is fixed; retry the activity, or switch to `OCR` mode which does not depend on the clipboard.

### Branch F — Clipboard mode: `ElementNotFoundException` thrown (`MethodType = ClipboardRow` / `ClipboardAll`)

Evidence: `MethodType = ClipboardRow` or `ClipboardAll`, the activity **threw** `ElementNotFoundException`, and the descriptor *did* match (the area was found — distinguish from [cv-element-not-found.md](./cv-element-not-found.md) where the descriptor never matched). This fires when the activity could not create a UI element from the matched area before clicking it. In practice this element is cloned from the scope's root, so this is a defensive guard that is near-dead unless the scope root element is null.

Fix: this points to a degraded CV Screen Scope root element, not to the text target. Verify the scope resolved its target window/element correctly. Use [cv-scope-setup-failures.md](./cv-scope-setup-failures.md) if the scope's target resolution is the actual problem.

### Branch G — Scrollable content extraction failure (`Scroll = true` + `MethodType = OCR`)

Evidence: `Scroll = true` **and** `MethodType = OCR`. The area was found, but the scroll-capture-and-stitch phase that gathers OCR across the scrollable content returned wrong/empty text or hung. Two distinct facts matter here:
- **`TimeoutMS` does NOT bound this phase.** The scroll-extraction phase receives the raw workflow cancellation token, not the `TimeoutMS`-bound token. If the activity appears to hang here, raising or lowering `TimeoutMS` has no effect — do not recommend it. Only job-level cancellation stops it.
- The extraction service is resolved when the activity is constructed; a missing service registration faults at activity instantiation (before execution), not as an empty result.

Fix:
- **Hang / no progress:** the content is likely not actually scrollable, or the scroll point lands off-target. Tune `ScrollOffset` (on the CV Screen Scope) so the scroll lands on the right pane, and `DelayScreenshotAfterScroll` so each captured frame is settled. Do not adjust `TimeoutMS` — it does not apply.
- **Empty/partial stitched text:** server/OCR errors during the per-scroll analysis degrade the stitch; verify the OCR engine health as in Branch A.
- **Note:** `Scroll = true` combined with a **clipboard** `MethodType` is invalid and is flagged at design time — it is not a runtime branch here.

## Post-presentation actions

Branches B, C, E (the switch-to-OCR fix), and G edit user workflow files (the `RefreshBefore` / `MethodType` / `Scroll`-related properties of the CV Get Text activity, or `ScrollOffset` / `DelayScreenshotAfterScroll` / `OCREngine` on the CV Screen Scope). This resolution path is **interactive**. Before any edit, you MUST call `AskUserQuestion` (approval gate).

Rules the agent MUST follow:

1. **Sharing a file path is not approval.** A path the user gave for reading the project does not authorize editing it. Issue a separate `AskUserQuestion` before any edit.
2. **Never bundle "gather input" with "apply fix" in one option.** Split into two steps: gather input, then surface the diff and confirm.
3. **Surface the diff before asking.** The question must name the file path, the activity `IdRef` or line, the current value, and the proposed value (e.g. `RefreshBefore: false → true`, or `MethodType: ClipboardRow → OCR`).
4. **One question per fix, listing every file touched.** If a fix changes both the CV Get Text activity and its parent CV Screen Scope, list both.
5. **If interactive approval is unavailable or errors, do not edit.** Present the diff as a recommendation and stop. A recommendation-only close is acceptable; a silent edit is never acceptable.

## Stop / escalate

If `MethodType = OCR` with `RefreshBefore = true`, the `OCREngine` is confirmed configured/reachable and healthy, the matched region covers the full expected text, and the result is still empty/wrong — the OCR engine is failing for this content; escalate to the OCR engine owner with the captured screen and region rather than continue under this playbook. If `MethodType` is a clipboard mode, the target is confirmed selectable editable text, and nothing else touches the clipboard, yet the result is still empty — switch to `OCR` mode per Branch E and escalate the clipboard path separately. Do not recommend changing `OCREngine` for a clipboard-mode failure or raising `TimeoutMS` for a `Scroll = true` extraction — the evidence rules both out.
