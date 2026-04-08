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

What to look for:
- Get the faulted activity name and selector from job traces or XAML source
- Check if the target application changed recently (version update, UI redesign)
- Check selector attributes — fragile selectors use title/name, robust selectors use automationId/className
- If HA data exists but no fix was produced: check eligibility and confidence threshold

## Investigation

1. Locate the faulted activity in XAML by `IdRef`
2. Extract the selector from the XAML (decode XML encoding: `&amp;` -> `&`, `&lt;` -> `<`, etc.)
3. Analyze the selector: which attributes are used? Are any dynamic (idx, tableRow, etc.)?
4. Check selector attributes — fragile selectors use title/name, robust selectors use automationId/className
5. Check if the target application has changed recently
6. Compare against Object Repository if available
7. If HA data exists but no fix was produced: check eligibility and confidence threshold

## Resolution

- Update the selector to use more stable attributes (aaname, automationid, role) instead of volatile ones (idx, tableCol, tableRow)
- Add wildcard matching for dynamic portions: `name='Invoice*'` instead of `name='Invoice_20250319'`
- Consider adding a Check App State activity before the failing activity to wait for the element
