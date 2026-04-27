---
name: uipath-interact
description: "[PREVIEW] Inspect and interact with live desktop/browser apps using uip rpa uia only -- snapshot inspect, click, type, read values, take screenshots, inspect UI state, verify behavior, fill forms, navigate menus, and extract table data. Use for live-app exploration before UiPath RPA authoring and for post-build verification. Never use PowerShell/OS scripts, Playwright, or hand-written selectors as substitutes."
allowed-tools: Bash(uip:*), Read, Grep
---

# UI Interaction via "uip rpa uia"

Drive live desktop applications and browser tabs via the `uip rpa uia` CLI: discover applications and interact with elements using stable refs.

## Mandatory Entry Gate

Before inspecting or interacting with any live app:

1. Resolve `PROJECT_DIR` to the folder containing `project.json`.
2. Read `../uipath-rpa/references/uia-prerequisites.md`.
3. Ensure `UiPath.UIAutomation.Activities` is installed at the minimum version from that file. If it is absent or older and the user asked you to build/fix/explore UI automation, upgrade it before continuing unless the user explicitly forbids dependency changes.
4. Run `uip rpa restore "$PROJECT_DIR" --output json`.
5. Verify `{PROJECT_DIR}/.local/docs/packages/UiPath.UIAutomation.Activities/skills/uia-interact/SKILL.md` exists and read it inline.
6. Verify `uip rpa uia --help` exposes the interaction commands described by the package docs.

If any check fails after the prerequisite version and restore, stop and report the exact blocker. Do not use PowerShell UIAutomation, `Get-Process`, window-title scraping, Playwright, Selenium, browser devtools, or guessed selectors to compensate.

## When to use

- Probing a running application -- read values, inspect state, explore a UI tree.
- Driving a UI end-to-end (click, type, fill form, extract table).
- Verifying behavior after a change.

## When NOT to use

For anything else (building workflows, configuring Object Repository targets, fixing selectors, etc.) -- use the `uipath-rpa` skill. It is the entry point for all non-interactive UIA work and routes to the appropriate sub-skills.

## Prerequisites

See [uia-prerequisites.md](../uipath-rpa/references/uia-prerequisites.md).

## Entry procedure

Read and follow `$PROJECT_DIR/.local/docs/packages/UiPath.UIAutomation.Activities/skills/uia-interact/SKILL.md` **inline** in the main conversation. Do NOT delegate to a subagent -- the skill drives the live CLI and needs the main conversation's feedback loop (screenshots, captured output, user replies).

The first live-app discovery command must be `uia snapshot inspect`. Use `uia interact` commands only after a UIA snapshot/ref exists. Keep using UIA refs; do not switch to coordinates or OS-level scripts.

> **Trouble?** If something didn't work as expected, use `/uipath-feedback` to send a report.
