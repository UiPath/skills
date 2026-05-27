---
confidence: medium
---

# Selector Failure — Manual Investigation

## Context

A UI automation activity failed because its selector didn't match any element in the live UI tree. Either Healing Agent was enabled but didn't produce fixes, or source code is available for manual selector analysis.

What this looks like:
- SelectorNotFoundException, UiElementNotFoundException, ElementNotInteractableException, or NodeNotFoundException during activity execution
- Healing Agent data exists but no fix was produced, OR source code is available for direct analysis

What can cause it:
- Target application UI changed (redesign, update, dynamic content)
- Element attribute became dynamic (index shifted, name changed per session)
- Element hidden behind an overlay, popup, or dialog
- Timing issue — element not loaded yet when activity executed
- Wrong application window targeted
- Scope container (`NApplicationCard`, `NBrowser`, `Use Application/Browser`, `NWindow`) attached to a different page/window than the selector expects — see [scope-container-wrong-page.md](./scope-container-wrong-page.md)

What to look for:
- Get the faulted activity name and selector from job traces or XAML source
- Check if the target application changed recently (version update, UI redesign)
- Check selector attributes — fragile selectors use title/name, robust selectors use automationId/className
- If HA data exists but no fix was produced: check eligibility and confidence threshold

## Investigation

1. **Read the enclosing scope container** (`NApplicationCard`, `NBrowser`, `Use Application/Browser`, `NWindow`, `Attach Browser`, `Attach Window`) from the XAML — record `AttachMode`, `OpenMode` (defaults to `IfNotOpen` when absent), and `TargetApp.{Selector,Url}`. If the scope is permissive enough to attach to an unintended tab/window (`AttachMode=ByInstance` + `OpenMode=IfNotOpen` + loose `TargetApp.Selector`, or `TargetApp.Url` not matching the inner selector's intended page), the defect is the scope, not the selector — switch to [scope-container-wrong-page.md](./scope-container-wrong-page.md) before proceeding.
2. Locate the faulted activity in XAML by `IdRef`
3. Extract the selector from the XAML (decode XML encoding: `&amp;` -> `&`, `&lt;` -> `<`, etc.)
4. Analyze the selector: which attributes are used? Are any dynamic (idx, tableRow, etc.)?
5. Check selector attributes — fragile selectors use title/name, robust selectors use automationId/className
6. Check if the target application has changed recently
7. Compare against Object Repository if available
8. If HA data exists but no fix was produced: check eligibility and confidence threshold

## Resolution

- Update the selector to use more stable attributes (aaname, automationid, role) instead of volatile ones (idx, tableCol, tableRow)
- Add wildcard matching for dynamic portions: `name='Invoice*'` instead of `name='Invoice_20250319'`
- Consider adding a Check App State activity before the failing activity to wait for the element
