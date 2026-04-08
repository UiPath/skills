---
confidence: high
---

# Selector Failure — Healing Agent Fix Available

## Context

A UI automation activity failed because its selector didn't match any element in the live UI tree. Healing Agent was enabled and has produced a fix in `healing-fixes.json`.

What this looks like:
- SelectorNotFoundException, UiElementNotFoundException, ElementNotInteractableException, or NodeNotFoundException during activity execution
- `healing-fixes.json` exists and contains a matching entry for the faulted activity

What can cause it:
- Target application UI changed (redesign, update, dynamic content)
- Element attribute became dynamic (index shifted, name changed per session)

## Investigation

1. Match entry by `ActivityRefId` (preferred) or `activityName` + `workflowFile` (fallback)
2. Extract the `enhancedTarget` (for `update-target` fixes) or `clickTarget` (for `dismiss-popup` fixes)
3. Compare failed selector vs recommended selector
4. Check confidence score and strategy name

## Resolution

Follow the fix-application procedures in [interpretations/healing-agent-data.md](../interpretations/healing-agent-data.md) (section "Applying HA Fixes"):
- For `update-target`: see "Applying `update-target` Fixes" — uses `uia-improve-selector` skill if available, falls back to direct XAML edit
- For `dismiss-popup`: see "Applying `dismiss-popup` Fixes" — creates a Click activity before the failing activity, validates the workflow compiles
