---
name: uipath-interact
description: "[PREVIEW] Inspect and interact with live desktop/browser apps -- click buttons, type text, read values, take screenshots, inspect UI state, verify behavior, fill forms, navigate menus, and extract table data from running applications."
allowed-tools: Bash(uip:*), Read, Grep
---

# UI Interaction via "uip rpa uia"

Drive live desktop applications and browser tabs via the `uip rpa uia` CLI: discover applications and interact with elements using stable refs.

## When to use

- Probing a running application -- read values, inspect state, explore a UI tree.
- Driving a UI end-to-end (click, type, fill form, extract table).
- Verifying behavior after a change.

## When NOT to use

For anything else (building workflows, configuring Object Repository targets, fixing selectors, etc.) -- use the `uipath-rpa` skill. It is the entry point for all non-interactive UIA work and routes to the appropriate sub-skills.

## Entry procedure

Read and follow `$PROJECT_DIR/.local/docs/packages/UiPath.UIAutomation.Activities/skills/uia-interact/SKILL.md` **inline** in the main conversation. Do NOT delegate to a subagent -- the skill drives the live CLI and needs the main conversation's feedback loop (screenshots, captured output, user replies).

> **Trouble?** If something didn't work as expected, use `/uipath-feedback` to send a report.
