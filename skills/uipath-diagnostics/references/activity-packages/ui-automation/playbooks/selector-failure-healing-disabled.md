---
confidence: high
---

# Selector Failure — Healing Agent Disabled

## Context

A UI automation activity failed because its selector didn't match any element in the live UI tree. Healing Agent was not enabled on the process, so no automated recovery data is available.

What this looks like:
- SelectorNotFoundException, UiElementNotFoundException, ElementNotInteractableException, or NodeNotFoundException during activity execution
- AutopilotForRobots shows Enabled: false or HealingEnabled: false (or field absent)

What can cause it:
- Target application UI changed (redesign, update, dynamic content)
- Element attribute became dynamic (index shifted, name changed per session)
- Element hidden behind an overlay, popup, or dialog
- Wrong application window targeted

## Investigation

1. Confirm UIAutomation failure via trace spans (activity types: `UiPath.UIAutomationNext.*`, `UiPath.UIAutomation.*`, `UiPath.Core.Activities.Click`, etc.)
2. If trace unavailable, infer from exception type (SelectorNotFoundException is definitively UI)
3. TimeoutException is ambiguous — only classify as UI if trace confirms UI activity type

## Resolution

- Enable Healing Agent on the process: update release ProcessSettings with `{"AutopilotForRobots":{"Enabled":true,"HealingEnabled":true}}`
- Optionally restart the job — if it fails again, HA will capture full diagnostic data for a more detailed analysis
- Root cause still needs investigation via source code analysis or manual selector comparison
