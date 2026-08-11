---
confidence: medium
---

# CV — Element Not Found (descriptor match failed within timeout)

## Context

What this looks like — the job faults with `UiPath.CV.ElementNotFoundException`. The message is almost always the parameterless literal:

- `Element not found` — the canonical not-found signal. Emitted by `RuntimeFindService.FindWithRetry` after the retry loop exhausts `TimeoutMS` without a descriptor match. **Timeout expiry surfaces as `ElementNotFoundException`, NOT a `TimeoutException`** — there is no separate timeout exception type. Do not look for `TimeoutException`; do not conclude "this is not a timeout" from its absence.

The same `Element not found` text covers three structurally different root causes (genuine mismatch, scope-refresh failure, OCR degradation). The Resolution decision tree below keys on observable evidence to tell them apart.

> Trace-only message variant: the scope-refresh path additionally traces `Could not get screenshot` before the `ElementNotFoundException`. This line appears in the execution trace/log, not in the activity fault message. Its presence routes to Branch B.

What activities can produce this error:

- **CV Click** (`CvClickWithDescriptor`) — `Descriptor` argument; faults when the target/anchors never match.
- **CV Type Into** (`CvTypeIntoWithDescriptor`) — `Descriptor` argument; same find pipeline before typing.
- **CV Get Text** (`CvGetTextWithDescriptor`) — `Descriptor` argument; same find pipeline before reading text.
- **CV Element Exists** (`CvElementExistsWithDescriptor`) — does NOT fault. It catches `ElementNotFoundException` internally and returns `Result = false`. Every cause below becomes a `false` Result here, with `OutRegion` left unset. The error message is visible only in the trace / CV dump, never at the workflow level.
- **CV Screen Scope** (`CVScope`) — produces this indirectly: the scope's session refresh (root re-resolution / screenshot) throws `ElementNotFoundException` that surfaces through the child find activity (Branch B).

What can cause it (ordered most → least common):

- **UI changed since design time.** Target text/label/icon differs, element moved or was removed, layout shifted, theme/DPI change. The descriptor's target (or an anchor) no longer matches any region in the CV + OCR analysis of the screen.
- **Wrong screen state at run time.** App window not foreground/visible, page not loaded yet, a dialog covering the target, or the workflow reached the activity before the expected content rendered.
- **Anchor geometry broke.** Descriptor has anchors that are no longer co-located with the target — `Anchor2Service` finds the target and anchors individually but the geometric relationship no longer holds, so no match is returned.
- **Scale / DPI mismatch.** `DesignTimeScaleFactor` differs from `RootElementScaleFactor` (different monitor scaling between design and run machine), shifting matched geometry.
- **Timeout too short.** Slow-rendering screen never finishes within `TimeoutMS` — surfaces as `ElementNotFoundException`, not a timeout error.
- **Scope root lost / screenshot failed during refresh.** Target window closed, minimized, navigated away, or the session is locked/disconnected so the screenshot is null. The scope cannot produce a screen to analyze (Branch B).
- **OCR engine silently degraded.** The configured OCR engine threw or returned null during refresh; the failure is swallowed and OCR returns zero text elements, so every text-based target/anchor has no candidate region and never matches (Branch C).

What to look for:

- **The pre-throw runtime dump JSON is the primary forensic artifact.** Before throwing, `RuntimeFindService` writes a timestamped `*_ComputerVision` dump file via `RuntimeDumpInfoService`. It captures the descriptor, the scraped text, the detected elements, detected tables, the selector, and the screenshot at failure time. Locate and read this file first — it tells you what the CV server actually saw at the moment of failure (which distinguishes "UI changed" from "screen was empty/blank").

> **Different cause, do not apply this playbook:**
> - Message is `Scrolled the entire screen, but element was not found` — scroll-search exhausted, not a plain find timeout. Use [cv-scroll-search-failures.md](./cv-scroll-search-failures.md).
> - Message is a cell-targeting sentence (`Could not find table. Cell targeting supports only tables as target`, `Invalid column number <n>`, `Table only contains <n> columns and column number is <m>`, `No row in column <c> had a text containing <v>`, etc.) — descriptor targets a table cell. Although the type is still `ElementNotFoundException`, the *last* cell error is rethrown verbatim, so you will see the cell sentence, not `Element not found`. Use [cv-cell-targeting-failures.md](./cv-cell-targeting-failures.md).
> - Message is `Invalid Descriptor` / `Reason: Target must be set` / `Reason: Invalid image reference or value` — `InvalidDescriptorException`, thrown before any find attempt (descriptor evaluation/validation), not after a timeout. Use [cv-invalid-descriptor.md](./cv-invalid-descriptor.md).
> - The activity did NOT fault but a click/type landed on the wrong spot, or `CvElementExistsWithDescriptor` returned an unexpected `true`/`false` — the element was found (or `InRegion`/`ContinueOnError` bypassed the find). Use [cv-silent-failures-and-false-results.md](./cv-silent-failures-and-false-results.md).
> - The fault is a CV **server** error — `401`/`403`/`5xx`, `429`/`TooManyRequests`, payload/word-limit, or a network error during analysis. The find never completed because the analysis call failed. Use [cv-server-auth-throttling-network.md](./cv-server-auth-throttling-network.md).
> - The CV Screen Scope itself failed to set up (target window never resolved, missing local-server prerequisite, missing server/OCR config) — the scope never produced a session. Use [cv-scope-setup-failures.md](./cv-scope-setup-failures.md).
> - A click/type fault that occurred *after* the element was found (focus loss, stale coordinates, blocked input, SecureString) — find succeeded, action failed. Use [cv-action-failed-after-find.md](./cv-action-failed-after-find.md).
> - `CV Get Text` returned empty/stale/wrong text without faulting — find succeeded, extraction misbehaved. Use [cv-get-text-empty-or-wrong-result.md](./cv-get-text-empty-or-wrong-result.md).

## Investigation

1. **Confirm the message and type.** `UiPath.CV.ElementNotFoundException` with message `Element not found`. If the message is a scroll, cell, or invalid-descriptor sentence, stop and route via the negative-match block above. For `CvElementExistsWithDescriptor`, there is no fault — the symptom is `Result = false`; proceed using the dump and trace.
2. **Locate the `*_ComputerVision` runtime dump JSON** written just before the throw (timestamped, matching the failed run). Read the descriptor, the scraped/detected text, the detected elements, and the screenshot.
3. **Inspect the dump screenshot.** Decide which branch the evidence supports:
   - Screenshot shows the expected application screen, but the target is absent / different / moved → Branch A (genuine mismatch).
   - Screenshot is blank, black, truncated, shows the desktop/lock screen, or is missing, and/or the trace shows `Could not get screenshot` → Branch B (scope refresh failed).
   - Screenshot shows the correct screen with the target text clearly visible, but the dump's detected/scraped text is empty or missing that text → Branch C (OCR degraded).
4. **Read the trace** around the failure for `Could not get screenshot` (Branch B signal) and for any OCR-engine error/warning that was logged before degradation (Branch C corroboration).
5. **Capture the activity's `Descriptor` and key properties** from the workflow: `TimeoutMS`, `ScrollDirection` (if set, the negative-match scroll playbook applies once it actually scrolls), `InRegion` (if bound, the descriptor is bypassed — different playbook), and the `Version` / `FeatureVersion`.
6. **Capture scope/environment context.** The `CVScope` `Target` selector and `WaitForReady`, whether the run is unattended, whether the session could be locked/minimized, and the CV method / OCR engine configured on the scope.

## Resolution

Walk the decision tree. Choose the first branch whose evidence holds. Do not apply a branch whose ruling-out evidence is present.

> **Not applicable — do NOT recommend:** the **Healing Agent** and selector-improvement remedies (`selector-failure-*` playbooks) are **UIA-selector** features. They do NOT apply to CV `Cv*WithDescriptor` activities, which match a visual **descriptor**, not a UIA selector. The fix for a CV find failure is descriptor **re-indication** (Branch A) / scope or OCR correction (Branches B/C) — never selector healing. Recommending Healing Agent here is a misattribution.

### Branch A — Genuine descriptor mismatch (UI changed, anchors moved, DPI scale mismatch)

**Evidence (required to apply):** the dump screenshot shows the expected application screen rendered normally, AND the target is absent, visually changed, or relocated relative to its anchors. OCR/detected text in the dump is populated (rules out Branch C). No `Could not get screenshot` trace (rules out Branch B).

**Fixes:**
- **UI changed.** Re-indicate the target against the current screen to regenerate the descriptor. If only a label/text drifted, loosen the descriptor's text/fuzzy matching for the volatile part.
- **Anchor geometry broke.** Re-pick anchors that remain stable relative to the target, or reduce reliance on anchors if the target alone is now distinctive.
- **Scale/DPI mismatch.** Make the run-machine display scaling match design time, or re-indicate on the run-machine resolution. Do NOT just raise `TimeoutMS` — geometry, not time, is the problem.
- **Wrong screen state.** Add an explicit readiness gate before the activity (wait for a stable anchor element / page-loaded indicator) so the target is present when the find runs.
- **Timeout too short — only if the screen is slow-rendering.** Raise `TimeoutMS`. Apply this ONLY when the dump shows the screen still mid-render (partial content) at failure; raising the timeout when the UI genuinely changed wastes the whole window and still fails.

### Branch B — Scope root lost / screenshot failed during refresh

**Evidence (required to apply):** the dump screenshot is blank/black/desktop/lock-screen or missing, AND/OR the trace contains `Could not get screenshot` before the `ElementNotFoundException`. The scope could not produce a valid screen to analyze, so the find could never match.

**Root cause is one of:**
- **Target application/window closed or navigated away** mid-scope (between scope setup and this activity).
- **Window minimized** — the element region is empty, so the screenshot is null.
- **Scope root selector no longer matches** (window title changed), so the root element could not be re-created from its cached selector within the timeout.
- **Locked/disconnected session** preventing screen capture (common on unattended robots where the session locks).

**Fixes:**
- Ensure the target window stays open, foreground, and non-minimized for the duration of the CV Screen Scope — add a check/restore step before the failing activity if an earlier step may close or background it.
- If the scope-window title drifts, relax the `CVScope` `Target` selector (wildcard the volatile part) so its root re-resolves.
- For unattended runs, keep the session interactive (do not let it lock/disconnect); CV screenshot capture needs a live, unlocked desktop.

> Anti-fabrication: for `CvElementExistsWithDescriptor`, a closed/minimized/locked target silently returns `Result = false` — indistinguishable at the workflow level from a genuine "element does not exist." Do NOT report `Result = false` as "element confirmed absent" until the dump screenshot proves the screen was actually captured. A blank screenshot means the check is meaningless, not negative.

### Branch C — OCR engine silently degraded (text-based descriptors fail as not-found)

**Evidence (required to apply):** the descriptor's target or anchors are text-based, the dump screenshot clearly shows that text on screen, BUT the dump's detected/scraped text is empty or missing it. Optionally an OCR-engine error/warning was logged before the find timed out. The OCR failure is swallowed (returns null → zero text elements), so text matches never find a candidate.

**Root cause is one of:**
- **OCR engine misconfiguration** — wrong `ApiKey`/endpoint for the configured engine (e.g. UiPath Screen OCR), or the engine package missing at runtime.
- **CV method excludes OCR** — `CVScope.CvMethod` not set to a mode that runs OCR, so no text elements are produced.
- **Language/accents mismatch** producing zero recognized words.

**Fixes:**
- Verify and correct the `CVScope.OCREngine` configuration (engine selected, `ApiKey`/endpoint valid; Screen OCR inherits the scope `ApiKey` only when its own key is empty). Confirm the engine package is present on the run machine.
- Ensure `CVScope.CvMethod` includes OCR when the descriptor relies on text targets/anchors.
- If text recognition is unreliable for the content's language/font, switch the descriptor to image- or control-based targeting instead of text.

## Post-presentation actions

This resolution is **interactive** — every applicable fix edits user source files (the activity `Descriptor`, `TimeoutMS`, `CVScope` `Target`/`OCREngine`/`CvMethod` properties, or adds a readiness/check activity). Before any edit, you MUST call `AskUserQuestion` (approval gate). Rules:

1. **Sharing a file path is not approval.** A path the user gave for reading the workflow does not authorize editing it. Issue a separate `AskUserQuestion` before any write.
2. **Never bundle "gather input" with "apply fix" in one option.** Split into two steps: gather the input, then surface the concrete diff and confirm separately.
3. **Surface the diff before asking.** Include the file path, the activity `IdRef`/line, the current value, and the proposed value (e.g. the `Descriptor` re-indication, the `TimeoutMS` change, the `CVScope.OCREngine` correction).
4. **One question per file/fix.** If multiple files are touched (workflow plus an Object Repository mirror), list every file or ask file-by-file. Do not silently propagate the change to side-channel files.
5. **If interactive approval is unavailable or errors, do not edit.** Present the diff as a recommendation and stop. A recommendation-only close is acceptable; a silent edit is never.

## Stop / escalate

Escalate (do not continue under this playbook) when:

- The dump screenshot shows the expected screen with the target plainly present and unchanged, OCR text is populated, the descriptor still matches at design time against the same screen, scaling matches, and the timeout was ample — the failure is then outside the descriptor/find path (CV server model regression or driver issue); escalate with the `*_ComputerVision` dump attached.
- Branch B evidence holds but the window is confirmed open, foreground, non-minimized, the session is live, and the scope selector resolves — the screenshot failure is environmental/driver-level; escalate rather than keep editing the workflow.
- Branch C evidence holds but the OCR engine is correctly configured, packaged, and `CvMethod` includes OCR — escalate the OCR engine/runtime, do not keep changing the descriptor.
