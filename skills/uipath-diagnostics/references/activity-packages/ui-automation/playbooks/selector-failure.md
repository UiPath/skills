---
confidence: high
---

# Selector Failure

## Context

A UI automation activity failed because it could not find or interact with the target element. The selector didn't match any element in the live UI tree, or the element was found but can't be interacted with.

What this looks like:
- SelectorNotFoundException, UiElementNotFoundException, ElementNotInteractableException, or NodeNotFoundException during activity execution

What can cause it:
- Target application UI changed (redesign, update, dynamic content)
- Element attribute became dynamic (index shifted, name changed per session)
- Element hidden behind an overlay, popup, or dialog
- Timing issue — element not loaded yet when activity executed
- Wrong application window targeted

What to look for:
- Get the faulted activity name and selector from job traces
- Check if Healing Agent was enabled on the process (AutopilotForRobots field in job info)
- If HA was enabled, check for `healing-fixes.json` — HA may have already identified the fix
- Download the video recording for the job if available
- Check if the target application changed recently (version update, UI redesign)

### Scenario: healing-agent-fix-available

When `healing-fixes.json` exists and contains a matching entry for the faulted activity.

**Investigation:**
1. Match entry by `ActivityRefId` (preferred) or `activityName` + `workflowFile` (fallback)
2. Extract the `enhancedTarget` (for `update-target` fixes) or `clickTarget` (for `dismiss-popup` fixes)
3. Compare failed selector vs recommended selector
4. Check confidence score and strategy name

**Resolution:**
- For `update-target`: update the activity's selector in XAML with the HA-recommended selector
- For `dismiss-popup`: add a Click activity before the failing activity to dismiss the popup
- Match XAML activity by `ActivityRefId` -> `IdRef` attribute (unique within workflow)
- Apply proper XML encoding when editing selectors: encode `&` first, then `<`, `>`, `'`, `"`

### Scenario: healing-agent-disabled

When the job failed but Healing Agent was not enabled.

**Investigation:**
1. Confirm UIAutomation failure via trace spans (activity types: `UiPath.UIAutomationNext.*`, `UiPath.UIAutomation.*`, `UiPath.Core.Activities.Click`, etc.)
2. If trace unavailable, infer from exception type (SelectorNotFoundException is definitively UI)
3. TimeoutException is ambiguous — only classify as UI if trace confirms UI activity type

**Resolution:**
- Enable Healing Agent on the process: update release ProcessSettings with `{"AutopilotForRobots":{"Enabled":true,"HealingEnabled":true}}`
- Optionally restart the job — if it fails again, HA will capture full diagnostic data for a more detailed analysis
- Root cause still needs investigation via source code analysis or manual selector comparison

### Scenario: no-healing-data-manual-investigation

When HA was enabled but didn't produce fixes, or source code is available for manual analysis.

**Investigation:**
1. Locate the faulted activity in XAML by `IdRef`
2. Extract the selector from the XAML (decode XML encoding: `&amp;` -> `&`, `&lt;` -> `<`, etc.)
3. Analyze the selector: which attributes are used? Are any dynamic (idx, tableRow, etc.)?
4. Check selector attributes — fragile selectors use title/name, robust selectors use automationId/className
5. Check if the target application has changed recently
6. Compare against Object Repository if available
7. If HA data exists but no fix was produced: check eligibility and confidence threshold

**Resolution:**
- Update the selector to use more stable attributes (aaname, automationid, role) instead of volatile ones (idx, tableCol, tableRow)
- Add wildcard matching for dynamic portions: `name='Invoice*'` instead of `name='Invoice_20250319'`
- Consider adding a Check App State activity before the failing activity to wait for the element
