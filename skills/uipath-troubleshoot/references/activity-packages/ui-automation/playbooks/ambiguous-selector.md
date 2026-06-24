---
confidence: high
---

# Ambiguous Selector — Target Matched Multiple Elements

## Context

A UI Automation Next activity threw `NodeAmbiguousException` because its target selector matched more than one element in the live UI tree. The target-find service walks the tree, accumulates every node satisfying the selector, and refuses to act when the result set has more than one. The activity never dispatches — no click, no key, no read.

Applies to every UIAutomationNext activity that resolves a target before acting:

- `NClick`, `NTypeInto`, `NCheck`, `NHover`, `NHighlight`, `NSetFocus`
- `NGetText`, `NSetText`, `NGetAttribute`
- `NSelectItem`
- `NCheckElement`, `NCheckState`

What this looks like:

- Exception class: `UiPath.UIAutomationNext.Exceptions.NodeAmbiguousException`
- Friendly message (the only one — this exception carries a static resource string with no placeholders):
  > Multiple similar matches found.
  >
  > Could not uniquely identify the user-interface element for this action.
  > Edit the element, run Validation, and add anchors in order to ensure the element is uniquely identified.
- Resource key: `Strings.NodeNotFoundMultipleMatches`
- Stack origin: the find phase of the activity (no `VerifyExecutionService` frames, no Healing Agent recovery frames — the find phase short-circuits before either runs).
- Fault duration is short (typically under the activity `Timeout` — once the ambiguity is detected the find service does not retry).
- The exception message does NOT include the offending selector — you must read the workflow source to recover it.

What can cause it:

- Selector is too generic — no anchor, no parent context, no `idx=`. Common authoring mistakes: `<webctrl tag='BUTTON' />`, `<webctrl tag='INPUT' type='submit' />`, `<wnd cls='Button' />`.
- The UI legitimately has repeated controls (table rows, card grid, list items, paginated wizard steps) and the selector does not narrow to one row/card/page.
- Multiple windows or tabs of the same application are open and the selector does not include a window-scope qualifier (`<html app='msedge.exe' title='Specific Title' />`).
- Dynamic attributes drifted — the attribute that was unique at design time is no longer unique at runtime (regenerated id, A/B-tested layout duplicated a control).
- Iframe / shadow-root traversal that pulls the same logical DOM tree into the search twice.
- A previous activity (e.g., an opened dialog) introduced a duplicate of the target element on top of the existing one.

What to look for:

- Confirm the exception class is `NodeAmbiguousException`. If it is `NodeNotFoundException` / `SelectorNotFoundException` / `UiElementNotFoundException`, the selector matched ZERO elements — use the `selector-failure-*.md` playbooks instead. Ambiguous = multiple matches; failure = no matches.
- Healing Agent **explicitly bypasses** this exception. Its recovery pipeline (`FindAlternativeOriginalTargetHiddenStrategy`) checks for `NodeAmbiguousException` and returns immediately, producing no recovery data. If you see `HealingAgentBehavior=Job` or `=Card` on the activity and no recovery payload for this fault, that is correct behavior — not an HA misconfiguration. Do NOT treat this as a `no-recovery-data.md` case.
- The exception message ALONE does not identify the duplicate. To diagnose you must:
  - Read the workflow source to get the selector
  - Open the target page at the time of failure (or its `InformativeScreenshot` if attached to the `TargetAnchorable`) and count how many elements satisfy the selector
- The activity `Timeout` is irrelevant. Extending it does not give the find service more time to disambiguate — the service has already decided as soon as >1 match is found.

## Investigation

1. From the failed job, capture the exception class, faulting activity, and workflow file.
2. Open the workflow source. Locate the failing activity by `DisplayName` or `IdRef`. Read its `Target` block:
   - The active selector — check the `SearchSteps` attribute on the `TargetAnchorable` and read whichever selector matches: `SearchSteps='FullSelector'` → `FullSelectorArgument`; `SearchSteps='FuzzySelector'` → `FuzzySelectorArgument`. One of these will be set, the other typically empty. Do not assume `FullSelectorArgument` is always populated.
   - `ScopeSelectorArgument` — the window/scope wrapper (often just the app + window title)
   - `BrowserURL` — for web targets, the URL the target lives on
   - `InformativeScreenshot` — design-time screenshot of the intended element (filename only — file may not be in the repo)
3. Inspect the selector specificity. Decompose attributes into "specific" (`aaname`, `aria-label`, stable `id`, `name`, `data-testid`, application-owned `data-*`) vs. "generic" (`tag`, `type`, `cls`, `role`). A selector with only generic attributes against a page that has repeated patterns is the canonical ambiguous case.
4. Determine the duplication source. Classify the failure:
   - Repeated UI pattern (multiple rows / cards / list items)
   - Multiple windows / tabs of the same app open simultaneously
   - Dynamic attribute drift (id was stable at design time, regenerated at runtime)
   - Iframe / shadow-root double traversal
   - Overlay / dialog opening a duplicate of the underlying control
5. Confirm the duplication is reachable from the activity's scope at runtime. If a sibling activity opens a dialog before the failing activity runs, the duplicate may only exist transiently — the fix is to gate on the dialog being closed, not to narrow the selector.
6. Confirm the activity is NOT wrapped in a Retry Scope on `NodeAmbiguousException`. If it is, retrying does not help — the ambiguity is structural, not transient. The retry block must be removed and the selector fixed at source.

## Resolution

### Decision tree

Walk this tree from the top. Stop at the first branch that matches.

1. **Is the selector relying only on generic attributes** (`tag`, `type`, `cls`, `role`) with no specific identifier?
   - YES → branch **(A)**. Selector is too generic — add a specific attribute.
   - NO → continue.

2. **Does the failure happen against a repeated UI pattern** (table rows, card grid, list items, paginated forms)?
   - YES → branch **(B)**. The selector matches the pattern but not a specific instance — narrow by anchor or index.
   - NO → continue.

3. **Are multiple windows / tabs of the same application open** when the activity runs?
   - YES → branch **(C)**. Narrow the `ScopeSelectorArgument` to the specific window — or attach to the scope explicitly via `NApplicationCard`.
   - NO → continue.

4. **Was the unique attribute stable at design time but drifts at runtime** (regenerated id, dynamic GUID, A/B-tested attribute)?
   - YES → branch **(D)**. Replace the drifting attribute with a stable one — or use a wildcard / regex match.
   - NO → continue.

5. **Does the page contain iframes or shadow-roots that traverse the same logical DOM twice**?
   - YES → branch **(E)**. Anchor the selector inside the correct frame.
   - NO → continue.

6. **Default — an overlay / dialog opened a duplicate of the target** → branch **(F)**. Gate the activity on the dialog being closed before the action runs.

### Branches

- **(A) Selector too generic — add a specific attribute.** The selector uses only generic attributes (`tag`, `type`, `cls`, `role`) that match many sibling controls. Open the target in Studio's Selector Editor or Object Repository. Add the first stable, specific attribute the target exposes: `aaname` / `aria-label`, `name`, `id` (only if it does not drift), `data-testid`, application-owned `data-*`. Re-run Validation in Studio to confirm "single match". Example: change `<webctrl tag='INPUT' type='submit' />` to `<webctrl tag='INPUT' type='submit' name='btnK' />` (Google Search) to disambiguate from the "I'm Feeling Lucky" submit on the same page.

- **(B) Repeated UI pattern — narrow by anchor or index.** The selector matches a pattern that legitimately repeats (rows, cards, list items). Two viable fixes:
  - **Use an anchor**: wrap the target with a `Find Anchor` (or Object Repository anchor) that locks the search to a specific neighbor (the row's first cell with a known label, the card's title, the section header above the action button). Anchors are the preferred Object Repository pattern because they survive row reordering.
  - **Use `idx='N'`** in the selector if the position is stable across runs (e.g., always the first row). Fragile under list reordering.

  Do NOT loop over every match and act on each — that is a different operation, surfaced via `NForEachUiElement`, not a fix for `NodeAmbiguousException`.

- **(C) Multiple windows / tabs open — narrow window scope.** The selector's `ScopeSelectorArgument` was too generic — e.g., `<html app='msedge.exe' title='Google' />` matches every Edge window currently titled "Google". Fix one of:
  - Narrow the `ScopeSelectorArgument` to a title pattern unique to the intended window.
  - Attach to the application explicitly via an `NApplicationCard` opened on the intended window — actions inside the card inherit the card's scope and ignore other windows.
  - If multiple windows of the same app are an expected and legitimate workflow state, surface that to the workflow author — the workflow needs an explicit "switch to window N" step before the action, not a tighter selector.

- **(D) Dynamic attribute drift — use a stable attribute or wildcard.** The attribute that disambiguated at design time was regenerated, A/B-tested, or replaced at runtime. Symptom: a previously-working workflow starts failing with `NodeAmbiguousException` without any workflow change. Fix:
  - Replace the drifting attribute with a stable one (`name`, `data-testid`, application-owned `data-*`).
  - If no fully-stable attribute exists, use wildcard matching: `id='button_*'` or regex on the drifting portion. Validate that the wildcard still uniquely matches the intended element.
  - Coordinate with the application team to add a stable test-id if the application is internal. UI automation against an app whose every attribute is generated is the actual problem.

- **(E) Iframe / shadow-root double traversal.** The selector traverses into an iframe or shadow root that hosts the same logical DOM as the parent — the find service then matches both the original element and the duplicate inside the frame. Open the target page's DOM and identify which frame the intended element lives in. Anchor the selector explicitly: prepend an iframe selector segment (e.g., `<webctrl tag='IFRAME' aaname='specific-frame-name' />`) for iframe, or use the application's shadow-root selector. If the duplication is unintentional (the application's bug), report it — UI automation cannot reliably target an application that duplicates its own DOM into ambient frames.

- **(F) Overlay / dialog duplicated the target — gate on dialog state.** A dialog, modal, or popup opened between a prior activity and the failing one, and the dialog hoists a copy of the underlying control. Symptom: ambiguity that only fires when a specific sibling activity ran just before. Fix:
  - Add an `NCheckAppState` before the failing activity to wait for the dialog to close (`Disappears` mode).
  - If the dialog is expected to stay open, narrow the selector to scope into the dialog's container only (the dialog's root has a distinguishing attribute — `role='dialog'`, `aria-modal='true'`, a specific class).
  - Do NOT add a fixed `Delay` and hope the dialog dismisses on its own — race conditions reappear under load.

### Anti-patterns

The following are NOT valid fixes for `NodeAmbiguousException`:

- **Increase the activity `Timeout`** — irrelevant. The find service has already decided as soon as >1 match is found; more time does not change the outcome.
- **Switch `InteractionMode`** (Simulate / Hardware Events / ChromiumAPI / WindowMessages) — input mode applies to the action after the target is found. The target was never found uniquely; input mode does not enter.
- **Enable Healing Agent on the activity / card / process** — Healing Agent explicitly bypasses `NodeAmbiguousException` (`FindAlternativeOriginalTargetHiddenStrategy` short-circuits when the exception type is detected). Turning HA on produces no recovery data and no fix.
- **Wrap the activity in a try / catch and ignore the exception** — the action never happened; downstream workflow state is invalid.
- **Wrap the activity in a Retry Scope** — ambiguity is structural, not transient. Retrying the same selector returns the same multiple matches every time.
- **Add `idx='1'` unconditionally** — only valid in branch (B) when position is stable across runs. Doing it blindly hides selector drift and masks future regressions.
