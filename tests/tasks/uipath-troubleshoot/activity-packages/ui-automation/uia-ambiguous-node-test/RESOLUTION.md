# Final Resolution

Root Cause: `NClick "Click 'Airi Satou'"` in `Amb.xaml` (IdRef `NClick_1`) faulted with `UiPath.UIAutomationNext.Exceptions.NodeAmbiguousException`. The target-find service walked the live DataTables grid, accumulated more than one node satisfying the activity's `FuzzySelectorArgument`, and refused to dispatch — the click never executed. Source inspection of `Amb.xaml` proves the cause is branch **(B)** of the `ambiguous-selector.md` playbook decision tree: the failure happens against a repeated UI pattern (table rows / cells), and the authored selector does not narrow to one specific cell.

The activity's selector (verbatim from `Amb.xaml`, `SearchSteps='FuzzySelector'`, no `FullSelectorArgument`):

```
<webctrl id='example' matching:id='fuzzy' fuzzylevel:id='0.0' tag='TABLE' />
<webctrl tag='TD' />
```

The outer segment uniquely identifies the DataTables demo grid via `id='example'` (`fuzzylevel:id='0.0'` = exact match). The inner segment `<webctrl tag='TD' />` uses ONLY the generic `tag` attribute and matches EVERY `<td>` cell rendered in that table — the literal `Airi Satou` row value appears nowhere in the selector (only in the activity's `DisplayName`). The find phase short-circuits as soon as >1 match is detected.

What went wrong: The robot started job `79e6d2c6-ab69-4e32-a831-d80f2f6036b6` (process `ERN`, entry point `Amb.xaml`) at 2026-05-22T09:26:21Z on host `MOCK-HOST` (scrubbed from `UIP-PW06WJSK`). The NApplicationCard "Edge DataTables  Javascript table library" attached `ByInstance` to an Edge browser window matching `<html app='msedge.exe' title='DataTables | Javascript table library' />` on `https://datatables.net/`. The NClick "Click 'Airi Satou'" then began target resolution. `TargetCommonLogic.GetSearchResultAsync` walked the page DOM, found multiple `<td>` cells satisfying the inner selector segment, and threw `NodeAmbiguousException` with friendly message: "Multiple similar matches found. Could not uniquely identify the user-interface element for this action. Edit the element, run Validation, and add anchors in order to ensure the element is uniquely identified." Job duration ~32 s. Healing Agent is disabled at the job level (`AutopilotForRobots.Enabled=false`, `HealingEnabled=false`), and per the `ambiguous-selector.md` playbook, HA's `FindAlternativeOriginalTargetHiddenStrategy` short-circuits on `NodeAmbiguousException` even when enabled — so the absence of recovery data is correct behavior, not a misconfiguration.

Playbook branch walk (`ambiguous-selector.md` → ## Resolution → Decision tree):

- **(A)** Selector relies only on generic attributes? **ELIMINATED.** The outer table segment carries `id='example'` — a specific attribute. The selector is not generically-only.
- **(B)** Failure against a repeated UI pattern (table rows / card grid / list items)? **APPLIES.** DataTables demo grid renders many `<td>` cells; the inner `<webctrl tag='TD' />` segment matches every one. Stop at branch (B).
- **(C)** Multiple windows / tabs of the same app open? **ELIMINATED.** `NApplicationCard.TargetApp.Url=https://datatables.net/` and `Selector=<html app='msedge.exe' title='DataTables | Javascript table library' />` bind to one specific Edge window via `AttachMode='ByInstance'` and `ScopeGuid='c9abbea0-fc1b-4aa6-8b39-ce7374298cb1'`. Single-window scope.
- **(D)** Dynamic attribute drift? **N/A** — branch (B) already matched; not reached.
- **(E)** Iframe / shadow-root double traversal? **N/A** — branch (B) already matched.
- **(F)** Overlay / dialog hoisting a duplicate? **N/A** — branch (B) already matched.

Evidence:

### UI Automation (Root Cause)
- Failing activity: `NClick "Click 'Airi Satou'"` (`IdRef=NClick_1`, Version=V5) in `Amb.xaml`, inside `NApplicationCard "Edge DataTables  Javascript table library"` (`IdRef=NApplicationCard_1`), inside Sequence "Do" inside Sequence "Amb".
- Exception: `UiPath.UIAutomationNext.Exceptions.NodeAmbiguousException`, friendly message (resource key `Strings.NodeNotFoundMultipleMatches`):
  > Multiple similar matches found.
  >
  > Could not uniquely identify the user-interface element for this action.
  > Edit the element, run Validation, and add anchors in order to ensure the element is uniquely identified.
- Stack origin: `TargetCommonLogic.GetSearchResultAsync` → `NClick.SearchAndSetTargetAsync` → `NClick.ExecuteAsync` → `RecoverableNativeActivity.ExecuteActivityAsync` → `NApplicationCard.OnFault`. No `VerifyExecutionService` frames. No Healing Agent / Autopilot recovery frames.
- Selector (verbatim, `SearchSteps='FuzzySelector'`, no `FullSelectorArgument` set):
  - `FuzzySelectorArgument=<webctrl id='example' matching:id='fuzzy' fuzzylevel:id='0.0' tag='TABLE' /><webctrl tag='TD' />`
  - `ScopeSelectorArgument=<html app='msedge.exe' title='DataTables | Javascript table library' />`
  - `BrowserURL=datatables.net`
  - `ElementType=Text`
  - `InformativeScreenshot=3402dfceb6aec6cbd2400dbf2fb4dce9.jpg`
- Activity properties: `InteractionMode=Simulate`, `ActivateBefore=True`, `ClickType=Single`, `MouseButton=Left`, `HealingAgentBehavior=SameAsCard` (inherits Job → effectively no HA recovery for this exception).
- Parent `NApplicationCard "Edge DataTables  Javascript table library"`: `AttachMode=ByInstance`, `InteractionMode=DebuggerApi`, `HealingAgentBehavior=Job`, `TargetApp.Url=https://datatables.net/`, `BrowserType=Edge`.
- No `Retry Scope`, no `Try/Catch`, no `Check App State` wraps the failing `NClick` — direct child of Sequence "Do" inside `NApplicationCard.Body`. Ambiguity surfaces as a fault, not masked.

### Orchestrator (Propagation)
- Process `ERN`, entry point `Amb.xaml`.
- Job `79e6d2c6-ab69-4e32-a831-d80f2f6036b6` in folder `Shared` (key `defb8e05-e36b-4c36-bf11-0b4d08ce6cd1`).
- Job state: `Faulted`. Healing Agent: disabled (`AutopilotForRobots.Enabled=false`, `HealingEnabled=false`) — no recovery data produced.

Immediate fix:

### UI Automation (Root Cause)
Apply branch **(B)** of the `ambiguous-selector.md` playbook: narrow the selector to one specific cell in the DataTables grid. In order of preference:

1. **Preferred — add a row anchor / Object Repository anchor.** Wrap the `NClick` in a `Find Anchor` (or use the Object Repository anchor pattern) keyed to a stable neighbor in the same row — for example, the row's first column cell with a known label, or another distinguishing cell in the same row. Anchors survive row reordering and table sorts better than positional `idx`.

2. **Acceptable — add a specific attribute on the inner TD segment.** Replace `<webctrl tag='TD' />` with `<webctrl tag='TD' aaname='Airi Satou' />` (or `innertext='Airi Satou'` if the DataTables instance does not expose `aaname`). This uses the literal cell text — the same text already in the activity's `DisplayName` — to disambiguate. The selector becomes:

   ```
   <webctrl id='example' matching:id='fuzzy' fuzzylevel:id='0.0' tag='TABLE' />
   <webctrl tag='TD' aaname='Airi Satou' />
   ```

3. **Fragile fallback — `idx='N'`.** Only acceptable if the row position is stable across runs (DataTables sorting / filtering / pagination break this). Do NOT apply `idx='1'` blindly — the playbook explicitly calls this out as an anti-pattern outside the specific branch (B) "position-stable" case.

After applying the fix, re-run Studio's **Validation** on the `NClick`'s Target (right-click → Validate) to confirm "single match" before publishing. Per the friendly-message guidance the runtime emits, this is the documented pre-publish check.

### Anti-patterns to avoid (from `ambiguous-selector.md` § Anti-patterns)

- **Do NOT increase the activity `Timeout`.** Irrelevant — the find service decided as soon as >1 match was detected; more time does not change the outcome.
- **Do NOT switch `InteractionMode`** (Simulate → Hardware Events / ChromiumAPI / WindowMessages). Input mode applies after the target is found, which never happened.
- **Do NOT enable Healing Agent / change `HealingAgentBehavior`** to fix this. HA explicitly bypasses `NodeAmbiguousException` (`FindAlternativeOriginalTargetHiddenStrategy` short-circuits). The current `HealingEnabled=false` is irrelevant to the resolution.
- **Do NOT wrap the activity in a `Retry Scope`** — the ambiguity is structural, not transient. Retries reproduce the same failure.
- **Do NOT wrap in `Try/Catch` to swallow the exception** — the click never happened; downstream workflow state would be invalid.
- **Do NOT match a `selector-failure-*.md` playbook.** Those target `NodeNotFoundException` / `SelectorNotFoundException` (zero matches). This case is `NodeAmbiguousException` (multiple matches) — a different exception with a different fix path.

### Orchestrator (Propagation)
Restart the job from Orchestrator after the `Amb.xaml` fix is published. Faulted jobs do not auto-retry process-level faults; the user must restart manually or republish a new version of `ERN`.

## Investigation summary

| # | Hypothesis | Confidence | Status | Root Cause? | Key Evidence | Resolution |
|---|------------|------------|--------|-------------|--------------|------------|
| H1 | `NClick "Click 'Airi Satou'"` faulted with `NodeAmbiguousException` because its `FuzzySelectorArgument` inner segment `<webctrl tag='TD' />` matches every `<td>` cell in the DataTables demo grid (`id='example'`). Branch (B) of the `ambiguous-selector.md` playbook — repeated UI pattern without a row anchor or idx qualifier. | high | confirmed | yes | Friendly message "Multiple similar matches found"; stack origin `TargetCommonLogic.GetSearchResultAsync → NClick.SearchAndSetTargetAsync` (find-phase short-circuit, no verify frames, no HA frames); selector verbatim from `Amb.xaml` has no row-disambiguating attribute; outer segment specific (`id='example'`) eliminates branch (A); single-window scope eliminates branch (C); no Retry Scope wrapper. | Branch (B) — add a row anchor (preferred) OR `aaname='Airi Satou'` / `innertext='Airi Satou'` on the inner `<webctrl tag='TD' />` segment. Validate in Studio before publishing. Do NOT extend Timeout, switch InteractionMode, enable HA, or wrap in Retry Scope. |
